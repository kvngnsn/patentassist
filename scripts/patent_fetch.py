#!/usr/bin/env python3
"""Fetch patents and publications into <dir>/cache/<CANONICAL>.json (patentassist/patent@1).

Examples:
    python3 scripts/patent_fetch.py fetch US9457709B2 "US 2016/0144773 A1"
    python3 scripts/patent_fetch.py fetch 9457709            # kind-less: Google reports the kind
    python3 scripts/patent_fetch.py fetch --from patent/prior-art.json
    python3 scripts/patent_fetch.py fetch US9457709B2 --offline   # cache only
    python3 scripts/patent_fetch.py parse page.html --json        # parse a saved Google Patents page
    python3 scripts/patent_fetch.py similar US9457709B2           # Google's "Similar Documents" list

Source chain:
  1. Google Patents HTML  https://patents.google.com/patent/<CANONICAL>/en  (keyless; /patent/ is
     allowed by robots.txt). Parsed with html.parser: itemprop/meta tags.
  2. USPTO ODP (only if USPTO_ODP_API_KEY is set; US documents): applications/{appNo}/meta-data.
     EXPERIMENTAL: response field names are not confirmed (see references/sources-and-apis.md),
     so the result is stored under enrichment.uspto_odp and never overwrites Google fields.
  3. EPO OPS (only if EPO_OPS_KEY and EPO_OPS_SECRET are set): docdb biblio. EXPERIMENTAL, same rule.

Network rules: generic User-Agent, >=1 s between requests to one host, 2 retries with backoff,
raw responses cached under cache/raw/, --offline uses the cache only.

Parse limits:
  - US grants print column:line, not paragraph numbers. Google's text for a grant has no printed
    paragraph labels, so grant paragraphs get synthesized labels p1..pN (paragraph_labels =
    "synthesized"). Published applications get their printed [0001] labels; EP B/A documents
    get [0001] from the paragraph ids.
  - Text for non-English documents is usually Google's machine translation.
  - A claim whose text is only "deleted", "delete", "canceled", "cancelled" (or Google's wording of
    that in a translated page) is kept with "canceled": true and is never independent.

Similar documents: Google's page lists "Similar Documents"; they are cached as
`similar: [{number, title, date}]`. `similar NUMBER` prints them (from the cache, re-parsing the saved
raw page if an older record lacks the list; it fetches the page only when neither exists and
--offline is not set). It is a keyless way to grow the candidate pool when web search is unavailable.

Exit codes: 0 ok, 1 a number was not found, 2 bad input, 3 network/source failure.
"""

import argparse
import base64
import glob
import gzip
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from normalize_number import fetch_candidates, kindless, normalize  # noqa: E402
from state import (SCHEMA_PATENT, SourceError, UsageError, add_common, audit, check_schema,  # noqa: E402
                   cli_main, finalize, finding, load_prior_art, new_result, read_json, to_namespace,
                   utc_now, write_json)

USER_AGENT = "patentassist/1.0 (+https://github.com/)"
MIN_SPACING = 1.0
RETRIES = 2
TIMEOUT = 30
_LAST_HIT = {}

ODP_BASE = "https://api.uspto.gov/api/v1/patent/applications/"
EPO_TOKEN_URL = "https://ops.epo.org/3.2/auth/accesstoken"
EPO_BASE = "https://ops.epo.org/3.2/rest-services/"

ENGLISH_OFFICES = {"US", "GB", "CA", "AU", "IE", "NZ", "IN", "SG", "ZA", "PH", "MY", "HK", "IL"}


# --------------------------------------------------------------------------- HTTP


def http_request(url, headers=None, data=None, method=None, timeout=TIMEOUT, retries=RETRIES,
                 spacing=MIN_SPACING):
    """GET/POST with polite spacing per host and retries.

    Returns (status, body_bytes, headers_dict). 4xx other than 429 return immediately.
    Raises SourceError when the host cannot be reached after retries."""
    host = urllib.parse.urlparse(url).netloc
    hdrs = {"User-Agent": USER_AGENT, "Accept-Language": "en"}
    hdrs.update(headers or {})
    last_err = None
    for attempt in range(retries + 1):
        wait = spacing - (time.time() - _LAST_HIT.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            _LAST_HIT[host] = time.time()
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return resp.status, body, dict(resp.headers)
        except urllib.error.HTTPError as e:
            body = e.read() if hasattr(e, "read") else b""
            if e.code == 429 or e.code >= 500:
                last_err = "HTTP %d" % e.code
                time.sleep(2 * (attempt + 1) + (3 if e.code == 429 else 0))
                continue
            return e.code, body, dict(e.headers or {})
        except (urllib.error.URLError, OSError) as e:
            last_err = str(getattr(e, "reason", e))
            time.sleep(1.5 * (attempt + 1))
    raise SourceError("%s: %s" % (host, last_err))


# --------------------------------------------------------------------------- tiny DOM

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
        "track", "wbr"}
SKIP_TEXT_TAGS = {"script", "style", "template"}


class Node(object):
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs, parent=None):
        self.tag = tag
        self.attrs = attrs
        self.children = []
        self.parent = parent

    def get(self, key, default=None):
        return self.attrs.get(key, default)

    def has_class(self, name):
        return name in (self.attrs.get("class") or "").split()

    def iter(self):
        stack = [self]
        while stack:
            n = stack.pop()
            yield n
            for c in reversed(n.children):
                if isinstance(c, Node):
                    stack.append(c)

    def find_all(self, pred):
        return [n for n in self.iter() if pred(n)]

    def find(self, pred):
        for n in self.iter():
            if pred(n):
                return n
        return None

    def text(self):
        out = []
        self._text(out)
        return "".join(out)

    def _text(self, out):
        for c in self.children:
            if isinstance(c, Node):
                if c.tag in SKIP_TEXT_TAGS or c.has_class("google-src-text"):
                    continue
                if c.tag == "br":
                    out.append("\n")
                    continue
                c._text(out)
            else:
                out.append(c)


class _Builder(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = Node("#root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse_html(html):
    b = _Builder()
    b.feed(html)
    b.close()
    return b.root


def clean(s):
    if s is None:
        return None
    s = s.replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def _ip(name):
    return lambda n: name in (n.attrs.get("itemprop") or "").split()


def _date(s):
    s = clean(s or "")
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", s)
    return m.group(1) if m else None


def _first_text(root, name, tag=None):
    n = root.find(lambda x: _ip(name)(x) and (tag is None or x.tag == tag))
    return clean(n.text()) if n is not None else None


def _first_time(root, name):
    n = root.find(lambda x: _ip(name)(x) and x.tag == "time")
    if n is None:
        return None
    return _date(n.get("datetime") or n.text())


def _uniq(seq):
    out, seen = [], set()
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


# --------------------------------------------------------------------------- Google Patents parser


_DEP_RE = re.compile(
    r"\bclaims?\s+(\d+)((?:\s*(?:,|-|–|to|through|or|and|and/or)\s*(?:claims?\s+)?\d+)*)", re.I)


def deps_from_text(text, num):
    """Claim numbers a claim refers to, read from its text (used when no claim-ref markup)."""
    head = text[:400]
    if re.search(r"\b(?:any|one) of the (?:preceding|previous|foregoing) claims\b", head, re.I):
        return list(range(1, num))
    deps = []
    for m in _DEP_RE.finditer(head):
        nums = [int(m.group(1))]
        tail = m.group(2) or ""
        parts = re.findall(r"(,|-|–|to|through|or|and/or|and)\s*(?:claims?\s+)?(\d+)", tail, re.I)
        prev = nums[0]
        for sep, n in parts:
            n = int(n)
            if sep.lower() in ("-", "–", "to", "through") and n > prev:
                nums.extend(range(prev + 1, n + 1))
            else:
                nums.append(n)
            prev = n
        deps.extend(x for x in nums if 0 < x < num)
    return sorted(set(deps))


# A claim that only says it was deleted/canceled (KR "delete", JP "(Deleted)", US "(Canceled)", DE "(gestrichen)").
CANCELED_RE = re.compile(
    r"^[\s(\[]*(?:claim\s+\d+\s*(?:is|was|has been)?\s*)?(?:deleted?|cancel(?:l)?ed|cancel|canceled|withdrawn|"
    r"omitted|gestrichen|entf[äa]llt|supprim[ée]e?s?|annul[ée]e?|삭제|削除|删除|취소)[\s)\].:;]*$", re.I)


def is_canceled_text(text):
    body = re.sub(r"^\s*\d+\s*\.\s*", "", text or "")
    return bool(CANCELED_RE.match(body.strip()))


def _parse_claims(root):
    sec = root.find(lambda n: n.tag == "section" and _ip("claims")(n))
    if sec is None:
        return [], None
    count = None
    cn = sec.find(_ip("count"))
    if cn is not None and clean(cn.text()).isdigit():
        count = int(clean(cn.text()))
    # English originals mark claims <div class="claim" num=..>; Google's translated pages use a bare
    # <claim num="0001"> element (no class), so accept either.
    nodes = sec.find_all(lambda n: (n.has_class("claim") or n.tag == "claim") and "num" in n.attrs)
    id_to_num = {}
    raw = []
    for i, n in enumerate(nodes):
        num_attr = re.sub(r"\D", "", n.get("num") or "")
        text = clean(n.text()) or ""
        m = re.match(r"^(\d+)\s*\.\s*", text)
        num = int(m.group(1)) if m else (int(num_attr) if num_attr else i + 1)
        if n.get("id"):
            id_to_num[n.get("id")] = num
        refs = [r.get("idref") for r in n.find_all(lambda x: x.tag == "claim-ref") if r.get("idref")]
        raw.append((num, text, refs))
    claims = []
    for num, text, refs in raw:
        if refs:
            deps = sorted(set(id_to_num[r] for r in refs if r in id_to_num and id_to_num[r] != num))
        else:
            deps = deps_from_text(re.sub(r"^\d+\s*\.\s*", "", text), num)
        if not re.match(r"^\d+\s*\.", text):
            text = "%d. %s" % (num, text)
        else:
            text = re.sub(r"^(\d+)\s*\.\s*", r"\1. ", text)
        if is_canceled_text(text):
            claims.append({"num": num, "text": text, "depends_on": [], "independent": False, "canceled": True})
            continue
        claims.append({"num": num, "text": text, "depends_on": deps, "independent": not deps})
    return claims, count


def parse_similar(root):
    """Google's "Similar Documents" table: [{number, title, date}] (patent rows only)."""
    out, seen = [], set()
    for tr in root.find_all(lambda n: n.tag == "tr" and _ip("similarDocuments")(n)):
        is_pat = tr.find(lambda n: n.tag == "meta" and _ip("isPatent")(n))
        if is_pat is not None and (is_pat.get("content") or "").lower() == "false":
            continue
        num = _first_text(tr, "publicationNumber")
        if not num or num in seen:
            continue
        seen.add(num)
        out.append({"number": num, "title": _first_text(tr, "title"), "date": _first_time(tr, "publicationDate")})
    return out


def _parse_description(root, country, kind):
    sec = root.find(lambda n: n.tag == "section" and _ip("description")(n))
    if sec is None:
        return [], None
    content = sec.find(_ip("content")) or sec
    paras = []
    heading = None
    pending_label = None
    style = None

    def walk(node):
        nonlocal heading, pending_label
        for c in node.children:
            if not isinstance(c, Node):
                continue
            if c.tag in SKIP_TEXT_TAGS or c.has_class("google-src-text"):
                continue
            if c.tag == "heading":
                heading = clean(c.text()) or heading
                continue
            if c.tag == "para-num":
                pending_label = c.get("num")
                continue
            if c.has_class("description-paragraph") or c.has_class("description-line"):
                t = clean(c.text())
                if t:
                    paras.append({"text": t, "printed": pending_label, "id": c.get("id"), "heading": heading})
                pending_label = None
                continue
            walk(c)

    walk(content)
    if not paras:
        # Fallback: plain text description (older OCR'd documents)
        txt = content.text()
        chunks = [clean(x) for x in re.split(r"\n\s*\n|(?<=\.)\s*\n(?=[A-Z])", txt)]
        paras = [{"text": x, "printed": None, "id": None, "heading": None} for x in chunks if x]
    out = []
    if paras and all(p["printed"] for p in paras):
        style = "printed"
        for p in paras:
            lab = p["printed"].strip()
            if not lab.startswith("["):
                lab = "[%s]" % lab
            digits = re.sub(r"\D", "", lab)
            out.append({"pid": "p" + digits, "label": lab, "text": p["text"]})
    elif paras and country != "US" and all(p["id"] and re.match(r"^\d{4,5}$", p["id"]) for p in paras):
        style = "printed"
        for p in paras:
            out.append({"pid": "p" + p["id"], "label": "[%s]" % p["id"], "text": p["text"]})
    else:
        style = "synthesized"
        for i, p in enumerate(paras, 1):
            out.append({"pid": "p%d" % i, "label": "p%d" % i, "text": p["text"]})
    for o, p in zip(out, paras):
        if p.get("heading"):
            o["heading"] = p["heading"]
    return out, style


def _ref_rows(root, name):
    rows = []
    for tr in root.find_all(lambda n: n.tag == "tr" and _ip(name)(n)):
        num = _first_text(tr, "publicationNumber")
        if not num:
            continue
        third = tr.find(lambda n: "thirdParty" in (n.get("itemprop") or "")) is not None
        assignee = _first_text(tr, "assigneeOriginal")
        rows.append({
            "number": num,
            "examiner": tr.find(_ip("examinerCited")) is not None,
            "third_party": third,
            "priority_date": _date(_first_text(tr, "priorityDate")),
            "date": _date(_first_text(tr, "publicationDate")),
            "assignee": assignee,
            "title": _first_text(tr, "title"),
        })
    return rows


def _merge_rows(*lists):
    out, seen = [], {}
    for lst in lists:
        for r in lst:
            if r["number"] in seen:
                prev = seen[r["number"]]
                prev["examiner"] = prev["examiner"] or r["examiner"]
                prev["third_party"] = prev["third_party"] or r["third_party"]
                continue
            seen[r["number"]] = r
            out.append(r)
    return out


def parse_google_html(html, requested=None, url=None):
    """Parse a Google Patents patent page into a patentassist/patent@1 record (no I/O)."""
    root = parse_html(html)
    metas = root.find_all(lambda n: n.tag == "meta" and n.get("name"))

    def meta(name, scheme=None):
        return [m.get("content") for m in metas
                if m.get("name") == name and (scheme is None or m.get("scheme") == scheme)]

    number = _first_text(root, "publicationNumber")
    kind_meta = root.find(lambda n: n.tag == "meta" and _ip("kindCode")(n))
    kind = kind_meta.get("content") if kind_meta is not None else None
    country = _first_text(root, "countryCode")
    if not number:
        tn = root.find(lambda n: n.tag == "title")
        m = re.match(r"^\s*([A-Z]{2}[A-Z]{0,2}\d+[A-Z]\d?)\s*-", tn.text() if tn else "")
        number = m.group(1) if m else requested
    norm = normalize(number) if number else {"ok": False}
    if not country and norm.get("ok"):
        country = norm["country"]
    if not kind and norm.get("ok"):
        kind = norm.get("kind")

    title = _first_text(root, "title")
    if not title:
        tn = root.find(lambda n: n.tag == "title")
        if tn is not None:
            t = clean(tn.text())
            t = re.sub(r"\s*-\s*Google Patents\s*$", "", t)
            t = re.sub(r"^[A-Z]{2}\S*\s*-\s*", "", t)
            title = t

    abs_sec = root.find(lambda n: n.tag == "section" and _ip("abstract")(n))
    abstract = None
    if abs_sec is not None:
        c = abs_sec.find(_ip("content")) or abs_sec
        abstract = clean(c.text())

    header_dd = lambda name: [clean(n.text()) for n in root.find_all(lambda x: x.tag == "dd" and _ip(name)(x))]
    inventors = _uniq(header_dd("inventor")) or _uniq(meta("DC.contributor", "inventor"))
    assignees = _uniq(header_dd("assigneeOriginal")) or _uniq(meta("DC.contributor", "assignee"))
    assignees_current = _uniq(header_dd("assigneeCurrent"))

    priority_date = _first_time(root, "priorityDate")
    filing_date = _first_time(root, "filingDate") or _date((meta("DC.date", "dateSubmitted") or [None])[0])
    publication_date = _first_time(root, "publicationDate")
    issue = meta("DC.date", "issue")
    events = []
    for ev in root.find_all(lambda n: n.tag == "dd" and _ip("events")(n)):
        t = ev.find(lambda x: x.tag == "time" and _ip("date")(x))
        events.append({
            "date": _date(t.get("datetime")) if t is not None and t.get("datetime") else None,
            "title": _first_text(ev, "title"),
            "type": _first_text(ev, "type"),
            "document": (_first_text(ev, "documentId") or "").replace("patent/", "").replace("/en", "") or None,
        })
    doc_type = norm.get("doc_type") if norm.get("ok") else None
    is_grant = bool(issue) or (doc_type in ("patent", "design", "plant", "reissue"))
    grant_date = None
    if is_grant:
        grant_date = _date(issue[0]) if issue else publication_date
        if not grant_date:
            g = [e["date"] for e in events if e["type"] == "granted" and e["date"]]
            grant_date = g[0] if g else None

    app_no = _first_text(root, "applicationNumber", tag="dd")
    if not app_no:
        a = meta("citation_patent_application_number")
        app_no = a[0].replace(":", "") if a else None

    # family
    fam = []
    for dd in root.find_all(lambda n: _ip("directAssociations")(n)):
        fam.append(_first_text(dd, "publicationNumber"))
    for tr in root.find_all(lambda n: n.tag == "tr" and (_ip("pubs")(n) or _ip("docdbFamily")(n))):
        fam.append(_first_text(tr, "publicationNumber"))
    family = [f for f in _uniq(fam) if f != number]
    fam_h2 = root.find(lambda n: n.tag == "h2" and clean(n.text() or "").startswith("ID="))
    family_id = clean(fam_h2.text())[3:] if fam_h2 is not None else None

    # priority applications
    prio_apps = []
    for tr in root.find_all(lambda n: n.tag == "tr" and _ip("priorityApps")(n)):
        prio_apps.append({"application_number": _first_text(tr, "applicationNumber"),
                          "publication": _first_text(tr, "representativePublication"),
                          "priority_date": _date(_first_text(tr, "priorityDate")),
                          "filing_date": _date(_first_text(tr, "filingDate"))})

    # CPC leaves (first code first)
    cpc_first, cpc = [], []
    for li in root.find_all(lambda n: n.tag == "li" and _ip("classifications")(n)):
        own = [c for c in li.children if isinstance(c, Node)]
        code_n = next((c for c in own if _ip("Code")(c)), None)
        props = {c.get("itemprop"): c.get("content") for c in own if c.tag == "meta"}
        if code_n is None or props.get("Leaf") != "true":
            continue
        if props.get("IsCPC") not in (None, "true"):
            continue
        code = clean(code_n.text())
        (cpc_first if props.get("FirstCode") == "true" else cpc).append(code)
    cpc = _uniq(cpc_first + cpc)

    claims, claim_count = _parse_claims(root)
    description, label_style = _parse_description(root, country, kind)

    backward = _merge_rows(_ref_rows(root, "backwardReferences"), _ref_rows(root, "backwardReferencesOrig"))
    forward = _merge_rows(_ref_rows(root, "forwardReferences"), _ref_rows(root, "forwardReferencesOrig"))
    npl = []
    for tr in root.find_all(lambda n: n.tag == "tr" and _ip("detailedNonPatentLiterature")(n)):
        t = _first_text(tr, "title")
        if t:
            npl.append({"citation": t, "examiner": tr.find(_ip("examinerCited")) is not None})

    status_n = root.find(_ip("legalStatusIfi"))
    legal_status = _first_text(status_n, "status") if status_n is not None else None
    expiration = None
    if status_n is not None:
        expiration = _first_time(status_n, "expiration")
    if not expiration:
        for e in events:
            if e["title"] and "expiration" in e["title"].lower() and e["date"]:
                expiration = e["date"]
    pdf = root.find(lambda n: n.tag == "a" and _ip("pdfLink")(n))

    notes = []
    if label_style == "synthesized":
        if country == "US" and is_grant:
            notes.append("US grant: printed patent uses column:line; paragraph labels pN are synthesized "
                         "from Google's text order, cite col:line from the PDF for filings.")
        else:
            notes.append("No printed paragraph numbers in the source text; labels pN are synthesized.")
    translated_from = _first_text(root, "translatedLanguage")
    if translated_from:
        notes.append("Text is Google machine translation from %s; quote it as machine-translated and mark "
                     "the cell [review]." % translated_from)
    elif country and country not in ENGLISH_OFFICES and country not in ("EP", "WO"):
        notes.append("Text is likely Google machine translation of a %s document." % country)
    if claim_count is not None and claim_count != len(claims):
        notes.append("Google lists %d claims; parsed %d." % (claim_count, len(claims)))
    canceled = [c["num"] for c in claims if c.get("canceled")]
    if canceled:
        notes.append("Claims %s are deleted/canceled in this publication (kept with canceled: true)."
                     % ", ".join(str(n) for n in canceled))

    rec = {
        "schema": SCHEMA_PATENT,
        "number": number,
        "country": country,
        "kind": kind,
        "doc_type": doc_type,
        "title": title,
        "abstract": abstract,
        "assignees": assignees,
        "assignees_current": assignees_current,
        "inventors": inventors,
        "priority_date": priority_date,
        "filing_date": filing_date,
        "publication_date": publication_date,
        "grant_date": grant_date,
        "application_number": app_no,
        "family": family,
        "family_id": family_id,
        "priority_applications": prio_apps,
        "cpc": cpc,
        "claims": claims,
        "claim_count": claim_count,
        "description": description,
        "paragraph_labels": label_style,
        "citations": {"backward": backward, "forward": forward, "npl": npl,
                      "backward_family": _ref_rows(root, "backwardReferencesFamily"),
                      "forward_family": _ref_rows(root, "forwardReferencesFamily")},
        "similar": parse_similar(root),
        "legal_status": legal_status,
        "expiration": expiration,
        "events": events,
        "pdf_url": pdf.get("href") if pdf is not None else None,
        "source": "google_patents",
        "url": url or ("https://patents.google.com/patent/%s/en" % number if number else None),
        "requested": requested,
        "fetched": utc_now(),
        "notes": notes,
        "enrichment": {},
    }
    return rec


# --------------------------------------------------------------------------- cache


def cache_dir(dirpath):
    return os.path.join(dirpath, "cache")


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)


def cache_path(dirpath, canonical):
    return os.path.join(cache_dir(dirpath), safe_name(canonical) + ".json")


def find_cached(dirpath, number, any_kind=False):
    """Return (path, record) for a cached patent record matching `number`, else (None, None).

    A kind-less number matches any cached kind. With any_kind=True a number WITH a kind also
    falls back to another kind of the same document number (the caller must compare kinds)."""
    norm = normalize(number)
    names = []
    if norm.get("ok"):
        names.extend(fetch_candidates(norm))
        names.append(norm["canonical"])
    else:
        names.append(str(number))
    for n in names:
        p = cache_path(dirpath, n)
        if os.path.exists(p):
            return p, _load_record(p)
    if norm.get("ok") and (not norm.get("kind") or any_kind):
        base = kindless(norm["canonical"])
        for p in sorted(glob.glob(os.path.join(cache_dir(dirpath), safe_name(base) + "*.json"))):
            stem = os.path.basename(p)[:-5]
            if re.match(r"^%s[A-Z]\d?$" % re.escape(base), stem):
                return p, _load_record(p)
    return None, None


def _load_record(path):
    rec = read_json(path)
    check_schema(rec, SCHEMA_PATENT, path)
    return rec


def save_raw(dirpath, source, name, body):
    d = os.path.join(cache_dir(dirpath), "raw", source)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, safe_name(name) + ".gz")
    with gzip.open(p, "wb") as fh:
        fh.write(body if isinstance(body, bytes) else body.encode("utf-8"))
    return p


# --------------------------------------------------------------------------- enrichment (experimental)


def _walk_find(obj, keys):
    """Depth-first search for the first value under any of `keys` (case-insensitive)."""
    lk = {k.lower() for k in keys}
    stack = [obj]
    while stack:
        cur = stack.pop(0)
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k.lower() in lk and v not in (None, "", [], {}):
                    return v
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def enrich_odp(rec, dirpath, key):
    """US only. Experimental: ODP field names are discovered at runtime."""
    app = rec.get("application_number") or ""
    digits = re.sub(r"\D", "", app)
    if rec.get("country") != "US" or not digits:
        return {"ok": False, "skipped": "not a US document with an application number"}
    url = ODP_BASE + digits + "/meta-data"
    status, body, _ = http_request(url, headers={"X-API-KEY": key, "Accept": "application/json"})
    save_raw(dirpath, "uspto_odp", digits + "-meta-data.json", body)
    out = {"ok": status == 200, "status": status, "experimental": True, "url": url}
    if status != 200:
        out["error"] = body[:300].decode("utf-8", "replace")
        return out
    try:
        data = json.loads(body.decode("utf-8"))
    except ValueError:
        out.update({"ok": False, "error": "non-JSON response"})
        return out
    fields = {
        "title": _walk_find(data, ["inventionTitle"]),
        "filing_date": _walk_find(data, ["filingDate"]),
        "grant_date": _walk_find(data, ["grantDate", "patentIssueDate"]),
        "patent_number": _walk_find(data, ["patentNumber"]),
        "publication_number": _walk_find(data, ["earliestPublicationNumber", "publicationNumber"]),
        "publication_date": _walk_find(data, ["earliestPublicationDate", "publicationDate"]),
        "applicant": _walk_find(data, ["firstApplicantName", "applicantNameText"]),
        "status": _walk_find(data, ["applicationStatusDescriptionText", "applicationStatusCode"]),
    }
    out["fields"] = {k: v for k, v in fields.items() if v is not None}
    out["top_keys"] = sorted(data.keys())[:30] if isinstance(data, dict) else None
    return out


_EPO_TOKEN = {}


def _epo_token(key, secret):
    if _EPO_TOKEN.get("exp", 0) > time.time() + 30:
        return _EPO_TOKEN["token"]
    auth = base64.b64encode(("%s:%s" % (key, secret)).encode("utf-8")).decode("ascii")
    status, body, _ = http_request(EPO_TOKEN_URL, headers={
        "Authorization": "Basic " + auth, "Content-Type": "application/x-www-form-urlencoded"},
        data=b"grant_type=client_credentials", method="POST")
    if status != 200:
        raise SourceError("EPO OPS token request failed: HTTP %d" % status)
    data = json.loads(body.decode("utf-8"))
    _EPO_TOKEN["token"] = data.get("access_token")
    _EPO_TOKEN["exp"] = time.time() + int(data.get("expires_in", 1200))
    return _EPO_TOKEN["token"]


def enrich_epo(rec, dirpath, key, secret):
    """Experimental: docdb biblio, JSON. Field paths follow OPS 3.2 conventions, read defensively."""
    m = re.match(r"^([A-Z]{2})(.+?)([A-Z]\d?)?$", rec.get("number") or "")
    if not m:
        return {"ok": False, "skipped": "no number"}
    cc, num, kind = m.groups()
    ref = "%s.%s%s" % (cc, num, ("." + kind) if kind else "")
    url = EPO_BASE + "published-data/publication/docdb/%s/biblio" % urllib.parse.quote(ref)
    token = _epo_token(key, secret)
    status, body, _ = http_request(url, headers={"Authorization": "Bearer " + token,
                                                 "Accept": "application/json"})
    save_raw(dirpath, "epo_ops", ref + "-biblio.json", body)
    out = {"ok": status == 200, "status": status, "experimental": True, "url": url}
    if status != 200:
        out["error"] = body[:300].decode("utf-8", "replace")
        return out
    try:
        data = json.loads(body.decode("utf-8"))
    except ValueError:
        out.update({"ok": False, "error": "non-JSON response"})
        return out
    titles = []
    t = _walk_find(data, ["invention-title"])
    for item in (t if isinstance(t, list) else [t] if t else []):
        if isinstance(item, dict):
            titles.append({"lang": item.get("@lang"), "text": item.get("$")})
    applicants = []
    ap = _walk_find(data, ["applicant"])
    for item in (ap if isinstance(ap, list) else [ap] if ap else []):
        if isinstance(item, dict):
            name = _walk_find(item, ["name"])
            if isinstance(name, dict):
                name = name.get("$")
            if name:
                applicants.append(name)
    date = _walk_find(data, ["date"])
    out["fields"] = {"titles": titles, "applicants": _uniq(applicants),
                     "date": date.get("$") if isinstance(date, dict) else date}
    return out


# --------------------------------------------------------------------------- fetch


def fetch_one(number, dirpath, offline=False, force=False, no_audit=False, enrich=True):
    """Fetch one number (cache-first). Returns a status dict; never raises for normal failures."""
    out = {"input": number, "status": None, "canonical": None, "path": None, "source": None,
           "tried": [], "message": None}
    norm = normalize(number)
    if not norm.get("ok"):
        out.update({"status": "bad_input", "message": "cannot parse number: %s" % "; ".join(norm["notes"])})
        return out
    if norm["doc_type"] == "application_no":
        out.update({"status": "bad_input", "canonical": norm["canonical"],
                    "message": "application numbers have no Google Patents page; give the publication "
                               "or patent number"})
        return out
    if not force:
        p, rec = find_cached(dirpath, number)
        if p:
            out.update({"status": "cached", "canonical": rec.get("number"), "path": p,
                        "source": rec.get("source"), "record": rec})
            return out
    want = kindless(norm["canonical"])
    if offline:
        p, rec = (None, None) if force else find_cached(dirpath, number, any_kind=True)
        if p:
            out.update({"status": "cached", "canonical": rec.get("number"), "path": p,
                        "source": rec.get("source"), "record": rec,
                        "message": "requested %s; cached document is %s" % (norm["canonical"], rec.get("number"))})
            return out
        out.update({"status": "not_cached", "message": "offline and not in cache"})
        return out
    cands = fetch_candidates(norm)
    if norm.get("kind") and want not in cands:
        cands.append(want)  # learn the real kind if the given kind does not exist
    for cand in cands:
        url = "https://patents.google.com/patent/%s/en" % cand
        out["tried"].append(cand)
        try:
            status, body, _ = http_request(url)
        except SourceError as e:
            out.update({"status": "network_error", "message": str(e)})
            audit(dirpath, "fetch", no_audit, number=cand, source="google_patents", ok=False, error=str(e))
            return out
        if status == 404:
            continue
        if status != 200:
            out.update({"status": "network_error", "message": "HTTP %d from Google Patents" % status})
            audit(dirpath, "fetch", no_audit, number=cand, source="google_patents", ok=False,
                  error="HTTP %d" % status)
            return out
        html = body.decode("utf-8", "replace")
        rec = parse_google_html(html, requested=number, url=url)
        got = rec.get("number") or cand
        if kindless(got) != want and kindless(got).lstrip("US") != want.lstrip("US"):
            rec["notes"].append("Google returned %s for request %s." % (got, cand))
        save_raw(dirpath, "google_patents", got + ".html", body)
        rec["url"] = "https://patents.google.com/patent/%s/en" % got
        if enrich:
            key = os.environ.get("USPTO_ODP_API_KEY")
            if key and rec.get("country") == "US":
                try:
                    rec["enrichment"]["uspto_odp"] = enrich_odp(rec, dirpath, key)
                except SourceError as e:
                    rec["enrichment"]["uspto_odp"] = {"ok": False, "error": str(e), "experimental": True}
            ek, es = os.environ.get("EPO_OPS_KEY"), os.environ.get("EPO_OPS_SECRET")
            if ek and es:
                try:
                    rec["enrichment"]["epo_ops"] = enrich_epo(rec, dirpath, ek, es)
                except (SourceError, ValueError) as e:
                    rec["enrichment"]["epo_ops"] = {"ok": False, "error": str(e), "experimental": True}
        path = cache_path(dirpath, got)
        write_json(path, rec)
        audit(dirpath, "fetch", no_audit, number=got, requested=number, source="google_patents", ok=True)
        out.update({"status": "fetched", "canonical": got, "path": path, "source": "google_patents",
                    "record": rec})
        if norm.get("kind") and rec.get("kind") and rec["kind"] != norm["kind"]:
            out["message"] = "requested %s; Google Patents has %s" % (norm["canonical"], got)
        return out
    audit(dirpath, "fetch", no_audit, number=norm["canonical"], source="google_patents", ok=False,
          error="not found", tried=out["tried"])
    out.update({"status": "not_found", "message": "Google Patents has no page for %s" % ", ".join(out["tried"])})
    return out


def numbers_from_prior_art(path_or_dir):
    if os.path.isdir(path_or_dir):
        pa = load_prior_art(path_or_dir)
    else:
        pa = check_schema(read_json(path_or_dir), "patentassist/prior-art@1", path_or_dir)
    nums = []
    for r in pa.get("references", []):
        if r.get("type") in ("npl", "web", "product"):
            continue
        if r.get("number"):
            nums.append(r["number"])
    return nums


def _summ(rec):
    return "claims=%d paras=%d (%s labels) cites=%d/%d" % (
        len(rec.get("claims") or []), len(rec.get("description") or []), rec.get("paragraph_labels"),
        len((rec.get("citations") or {}).get("backward") or []),
        len((rec.get("citations") or {}).get("forward") or []))


def raw_html_path(dirpath, number):
    return os.path.join(cache_dir(dirpath), "raw", "google_patents", safe_name(number + ".html") + ".gz")


def _known_numbers(dirpath):
    """Kind-less keys of references and read_not_cited in prior-art.json (empty if none)."""
    try:
        pa = load_prior_art(dirpath, required=False)
    except UsageError:
        pa = None
    keys = {}
    for r in (pa or {}).get("references") or []:
        for n in [r.get("number")] + list(r.get("family") or []):
            if n:
                keys[kindless(normalize(n).get("canonical") or n)] = r.get("id")
    for r in (pa or {}).get("read_not_cited") or []:
        if r.get("number"):
            keys.setdefault(kindless(normalize(r["number"]).get("canonical") or r["number"]), "read_not_cited")
    return keys


def cmd_similar(a, res):
    number = a.number or (a.numbers[0] if a.numbers else None)
    if not number:
        raise UsageError("similar needs a patent or publication number")
    path, rec = find_cached(a.dir, number)
    how = "cache"
    if rec is not None and "similar" not in rec:
        raw = raw_html_path(a.dir, rec.get("number") or number)
        if os.path.exists(raw):
            with gzip.open(raw, "rb") as fh:
                rec["similar"] = parse_similar(parse_html(fh.read().decode("utf-8", "replace")))
            write_json(path, rec)
            how = "re-parsed saved page"
    if rec is None or "similar" not in rec:
        if a.offline:
            res["findings"].append(finding("WARN", "not_cached", number, "offline and no cached page with a "
                                           "similar-documents list; fetch it first"))
            res["exit_code"] = 3
            return
        r = fetch_one(number, a.dir, force=rec is not None, no_audit=a.no_audit, enrich=False)
        rec = r.get("record")
        if rec is None:
            level = "BLOCK" if r["status"] == "not_found" else "WARN"
            res["findings"].append(finding(level, r["status"], number, r.get("message") or r["status"]))
            if r["status"] in ("network_error", "not_cached"):
                res["exit_code"] = 3
            return
        how = "fetched"
    sim = rec.get("similar") or []
    known = _known_numbers(a.dir)
    rows = []
    for s_ in sim:
        key = kindless(normalize(s_["number"]).get("canonical") or s_["number"])
        row = dict(s_)
        if key in known:
            row["known_as"] = known[key]
        cached, _ = find_cached(a.dir, s_["number"])
        row["cached"] = bool(cached)
        rows.append(row)
    res["number"] = rec.get("number")
    res["similar"] = rows
    res["checks_run"].append("similar (%s)" % how)
    res["text"].append("Similar documents for %s (%d, from %s):" % (rec.get("number"), len(rows), how))
    for r in rows:
        tag = ("  [%s]" % r["known_as"]) if r.get("known_as") else ("  [cached]" if r.get("cached") else "")
        res["text"].append("  %-20s %-10s %s%s" % (r["number"], r.get("date") or "-", r.get("title") or "", tag))
    new = [r["number"] for r in rows if not r.get("known_as") and not r.get("cached")]
    if new:
        res["text"].append("Screen titles first, then fetch the promising ones: patent_fetch.py fetch %s"
                           % " ".join(new[:10]))
    elif not rows:
        res["text"].append("Google lists no similar documents for this page.")
    res["summary"] = {"similar": len(rows), "new": len(new)}


DEFAULTS = {"command": None, "dir": "patent", "json": False, "no_audit": False, "offline": False,
            "numbers": [], "from_file": None, "force": False, "no_enrich": False, "file": None, "number": None}


def run(args):
    a = to_namespace(args, DEFAULTS)
    res = new_result()
    res["command"] = a.command
    if a.command == "parse":
        if not a.file or not os.path.exists(a.file):
            raise UsageError("parse needs an existing HTML file")
        with open(a.file, "r", encoding="utf-8", errors="replace") as fh:
            rec = parse_google_html(fh.read(), requested=a.number)
        res["record"] = rec
        res["text"].append("%s  %s  %s" % (rec["number"], rec["title"], _summ(rec)))
        return finalize(res)
    if a.command == "similar":
        os.makedirs(cache_dir(a.dir), exist_ok=True)
        cmd_similar(a, res)
        return finalize(res)
    if a.command != "fetch":
        raise UsageError("command must be fetch, parse, or similar")
    nums = list(a.numbers or [])
    if a.from_file:
        nums.extend(numbers_from_prior_art(a.from_file))
    if not nums:
        raise UsageError("give numbers or --from prior-art.json")
    os.makedirs(cache_dir(a.dir), exist_ok=True)
    results = []
    res["checks_run"].append("google_patents")
    if os.environ.get("USPTO_ODP_API_KEY") and not a.no_enrich:
        res["checks_run"].append("uspto_odp (experimental)")
    else:
        res["checks_skipped"].append({"check": "uspto_odp", "reason": "USPTO_ODP_API_KEY not set" if not
                                      os.environ.get("USPTO_ODP_API_KEY") else "--no-enrich"})
    if os.environ.get("EPO_OPS_KEY") and os.environ.get("EPO_OPS_SECRET") and not a.no_enrich:
        res["checks_run"].append("epo_ops (experimental)")
    else:
        res["checks_skipped"].append({"check": "epo_ops", "reason": "EPO_OPS_KEY/EPO_OPS_SECRET not set"
                                      if not os.environ.get("EPO_OPS_KEY") else "--no-enrich"})
    for n in _uniq(nums):
        r = fetch_one(n, a.dir, offline=a.offline, force=a.force, no_audit=a.no_audit, enrich=not a.no_enrich)
        rec = r.pop("record", None)
        if rec:
            r["title"] = rec.get("title")
            r["summary"] = _summ(rec)
            res["text"].append("%-22s %-8s %s  %s  -> %s" % (r["canonical"], r["status"], rec.get("title"),
                                                            r["summary"], r["path"]))
            if r.get("message"):
                res["findings"].append(finding("WARN", "kind_differs", n, r["message"]))
        else:
            res["text"].append("%-22s %-12s %s" % (n, r["status"], r.get("message") or ""))
            level = "BLOCK" if r["status"] == "not_found" else "WARN"
            res["findings"].append(finding(level, r["status"], n, r.get("message") or r["status"]))
        results.append(r)
    res["results"] = results
    st = [r["status"] for r in results]
    res["summary"] = {"requested": len(results), "fetched": st.count("fetched"), "cached": st.count("cached"),
                      "not_found": st.count("not_found"), "failed": sum(1 for s in st if s in
                                                                         ("network_error", "not_cached"))}
    if "bad_input" in st:
        res["exit_code"] = 2
    elif "network_error" in st or "not_cached" in st:
        res["exit_code"] = 3
    return finalize(res)


def build_parser():
    p = argparse.ArgumentParser(prog="patent_fetch.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common(p, network=True)
    sp = p.add_subparsers(dest="command")
    f = sp.add_parser("fetch", help="fetch numbers into cache/")
    add_common(f, sub=True, network=True)
    f.add_argument("numbers", nargs="*")
    f.add_argument("--from", dest="from_file", default=None, help="prior-art.json (or matter dir)")
    f.add_argument("--force", action="store_true", help="re-fetch even if cached")
    f.add_argument("--no-enrich", action="store_true", help="skip ODP / EPO OPS even if keys are set")
    pr = sp.add_parser("parse", help="parse a saved Google Patents HTML page (no network)")
    add_common(pr, sub=True)
    pr.add_argument("file")
    pr.add_argument("--number", default=None)
    sm = sp.add_parser("similar", help="list Google's similar documents for a number (cache first)")
    add_common(sm, sub=True, network=True)
    sm.add_argument("number")
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
