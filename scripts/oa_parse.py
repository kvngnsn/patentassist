#!/usr/bin/env python3
"""First-pass parser: USPTO office action text (pdftotext -layout) -> inventory.json.

    python3 scripts/oa_parse.py patent/prosecution/oa-2026-05-06/oa.txt \
        --out patent/prosecution/oa-2026-05-06/inventory.json

Finds: application number, mailing (notification) date, action type (nonfinal / final /
restriction), Office Action Summary dispositions (pending, rejected, objected, allowed,
withdrawn), every rejection ("Claim(s) ... is/are rejected under 35 U.S.C. ...") with
statute, basis, expanded claims, and references (numbers normalized by
normalize_number.py), the examiner's per-element mapping where it follows the common
"Smith discloses X (col. 3, ll. 5-10; FIG. 2)" pattern, objections (drawings,
specification, claims, allowable-if-rewritten), 112(f) interpretation notices, double
patenting, restriction groups, withdrawn rejections, and the Response to Arguments.

This is a first pass. Every item carries confidence high|low; read the action and
correct the inventory before relying on it.

Output: {"schema": "patentassist/oa-inventory@1", app_no, mailed, type, claims:
{pending, rejected, objected, allowed, withdrawn}, rejections: [{id, statute, basis,
claims, refs, mapping: [{claim, element_text, ref, pinpoint, confidence}], decision:
null, confidence}], objections: [...], notes: [...], ...}

Exit codes: 0 parsed (low-confidence items are WARN findings), 2 usage/input error.
"""

import argparse
import datetime as _dt
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from state import UsageError, add_common, audit, cli_main, finalize, finding, new_result, sha256_path, \
    to_namespace, utc_now, write_json  # noqa: E402

try:
    import normalize_number as _nn  # noqa: E402
except Exception:  # pragma: no cover - normalize_number is part of the skill
    _nn = None

SCRIPT = "oa_parse.py"
SCHEMA = "patentassist/oa-inventory@1"

CLAIMLIST = (r"\d+(?:\s*(?:-|–|—|through|to)\s*\d+)?"
             r"(?:\s*(?:,\s*(?:and\s+|or\s+)?|and\s+|or\s+|&\s*)\d+(?:\s*(?:-|–|—|through|to)\s*\d+)?)*")
CHECKED = set("☒☑■⊠✔✓◼▪xX")
UNCHECKED = set("☐□◻○")

HEADINGS = [
    r"notice of pre-aia or aia status", r"response to amendments?", r"response to arguments",
    r"drawings", r"specification", r"the disclosure", r"abstract", r"title", r"claim objections",
    r"claim interpretation", r"double patenting", r"claim rejections?\s*[-–—]\s*35\s*u\.?s\.?c\.?\s*§*\s*\d+.*",
    r"claim rejections?\s*[-–—].*", r"allowable subject matter", r"conclusion", r"election\s*/\s*restrictions?",
    r"restriction\s*/\s*election", r"information disclosure statement", r"priority", r"status of claims",
    r"examiner'?s amendment", r"reasons for allowance", r"continued examination under 37 cfr 1\.114",
    r"terminal disclaimer", r"oath\s*/\s*declaration", r"interview summary", r"applicant'?s reply",
    r"response to remarks", r"claim status", r"detailed action",
]
HEADING_RE = re.compile(r"^(?:%s)\s*:?$" % "|".join(HEADINGS), re.I)
NO_REJECTION_SECTIONS = ("response to arguments", "response to amendment", "response to amendments", "conclusion",
                         "allowable subject matter", "claim interpretation", "response to remarks")

ABBREV = {"no", "nos", "pat", "pub", "al", "col", "cols", "ll", "l", "para", "paras", "p", "pp", "fig", "figs",
          "ser", "appl", "app", "et", "vs", "inc", "corp", "co", "ltd", "e", "i", "eg", "ie", "sec", "ch", "approx",
          "ref", "refs", "u", "s", "c", "ex", "nos", "pg", "pgs", "ed", "vol"}

VERBS = (r"discloses|disclose|disclosed|teaches|teach|taught|shows|show|describes|describe|suggests|suggest|"
         r"recites|provides|illustrates|depicts|includes|has")
PIN_RE = re.compile(
    r"\((?P<pin>[^()]*?(?:\bcol(?:umn)?s?\.?\s*\d|\bll?\.\s*\d|\blines?\s+\d|\bpara(?:graph)?s?\.?\s*\[?\d|¶+\s*\[?\d|"
    r"\[\d{3,5}\]|\bFIGS?\.\s*\d|\bFig(?:ure)?s?\.?\s*\d|\bpages?\s+\d|\bp\.\s*\d|\bpp\.\s*\d|\babstract\b|"
    r"\bclaims?\s+\d|\belement\s+\d)[^()]*)\)", re.I)
CLAIM_CTX_RE = re.compile(r"\b(?:Regarding|As to|As per|With respect to|Re:?|For|Referring to|Considering)\s+"
                          r"(?:independent\s+|dependent\s+)?claims?\s+(\d+)", re.I)
NAMEPAREN_RE = re.compile(
    r"(?P<name>[A-Z][A-Za-z'’\-]+(?:\s+(?:et\s+al\.?|[A-Z][A-Za-z'’\-]+(?=\s*\()))?)\s*"
    r"\((?P<num>[^()]{4,70})\)")
PATNO_RE = re.compile(r"(?:U\.?\s?S\.?\s+)?(?:Patent|Pat\.)\s+(?:No\.|Number)\s*(?:RE)?\s*[\d,]{6,12}", re.I)
APPNO_RE = re.compile(r"(?:copending\s+)?(?:U\.?\s?S\.?\s+)?(?:Patent\s+)?Application\s+(?:Serial\s+)?No\.\s*\d{2}/[\d,]{6,7}",
                      re.I)
DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
APP_NO_RE = re.compile(r"\b(\d{2})/(\d{3}),?(\d{3})\b")


# --------------------------------------------------------------------------- small helpers


def expand_claims(s):
    """'1-12,19 and 20' -> [1..12, 19, 20]; '____' -> []."""
    if not s:
        return []
    s = re.sub(r"\b(?:and|or|&)\b|&", ",", s)
    s = re.sub(r"\s*(?:through|to|–|—)\s*", "-", s)
    out = []
    for piece in s.split(","):
        piece = piece.strip()
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", piece)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if b >= a and b - a < 1000:
                out.extend(range(a, b + 1))
            continue
        if re.fullmatch(r"\d+", piece):
            out.append(int(piece))
    return sorted(set(out))


def collapse(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"(\d)\s*-\s+(\[?\d)", r"\1-\2", s)      # "[0052]- [0055]" from line wraps
    s = re.sub(r"\]\s*-\s+\[", "]-[", s)
    return s


def iso(m):
    try:
        return _dt.date(int(m.group(3)), int(m.group(1)), int(m.group(2))).isoformat()
    except ValueError:
        return None


def sentence_end(text, start):
    """Index just past the sentence that begins at `start` (abbreviation- and paren-aware)."""
    depth = 0
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c in "([":
            depth += 1
        elif c in ")]":
            depth = max(0, depth - 1)
        elif c == "." and depth == 0:
            nxt = text[i + 1:i + 3]
            if i + 1 >= n or (nxt[:1] == " " and (nxt[1:2].isupper() or nxt[1:2] in "\"“(")):
                j = i - 1
                while j >= 0 and (text[j].isalnum() or text[j] in ".-"):
                    j -= 1
                tok = text[j + 1:i]
                if "." in tok or tok.lower() in ABBREV or (len(tok) == 1 and tok.isalpha()):
                    i += 1
                    continue
                return i + 1
        i += 1
    return n


def normalize_ref(raw):
    if _nn is None:
        return None
    try:
        r = _nn.normalize(raw)
    except Exception:
        return None
    if not r.get("ok"):
        return None
    return r


# --------------------------------------------------------------------------- header + summary


def _labelled_value(lines, label_re, value_re, max_ahead=3, max_dist=30):
    """Value printed under a column label in pdftotext -layout output."""
    for i, line in enumerate(lines):
        m = re.search(label_re, line)
        if not m:
            continue
        col = m.start()
        best = None
        for j in range(i, min(len(lines), i + max_ahead + 1)):
            for v in re.finditer(value_re, lines[j]):
                if j == i and v.start() < m.end():
                    continue
                dist = abs(v.start() - col)
                if dist <= max_dist and (best is None or (j - i, dist) < best[0]):
                    best = ((j - i, dist), v)
        if best:
            return best[1]
    return None


def parse_header(text, lines, inv, warn):
    m = re.search(r"(?:APPLICATION NO\.|Application No\.|Application/Control Number:?|Application Number:?)", text)
    app = None
    if m:
        app = APP_NO_RE.search(text, m.end(), m.end() + 400)
    conf = "high" if app else "low"
    if not app:
        app = APP_NO_RE.search(text)
    if app:
        raw = "%s/%s,%s" % app.groups()
        inv["app_no"] = raw
        r = normalize_ref(raw)
        inv["app_no_canonical"] = r["canonical"] if r else None
        inv["app_no_confidence"] = conf
    else:
        inv["app_no"] = None
        inv["app_no_confidence"] = "low"
        warn("app_no", "application number not found")

    mv = _labelled_value(lines, r"NOTIFICATION DATE|MAIL DATE", DATE_RE.pattern)
    if mv:
        inv["mailed"] = iso(re.match(DATE_RE.pattern, mv.group(0)))
        inv["mailed_confidence"] = "high"
        inv["mailed_source"] = "cover sheet date column"
    else:
        m2 = re.search(r"^\s*\d+\s+7590\s+(\d{1,2}/\d{1,2}/\d{4})", text, re.M)
        if m2:
            inv["mailed"] = iso(DATE_RE.match(m2.group(1)))
            inv["mailed_confidence"] = "low"
            inv["mailed_source"] = "customer-number line (7590)"
            warn("mailed", "mailing date taken from the customer-number line; confirm on the cover sheet")
        else:
            inv["mailed"] = None
            inv["mailed_confidence"] = "low"
            warn("mailed", "mailing/notification date not found; enter it from the cover sheet")

    ex = _labelled_value(lines, r"\bEXAMINER\b", r"[A-Z][A-Z'\-]+,\s+[A-Z][A-Z .'\-]+", max_dist=20)
    inv["examiner"] = ex.group(0).strip() if ex else None
    au = re.search(r"Art Unit:?\s*(\d{4})", text) or _labelled_value(lines, r"ART UNIT", r"\b\d{4}\b", max_dist=12)
    inv["art_unit"] = (au.group(1) if au and au.re.groups else au.group(0)) if au else None


def summary_region(text):
    s = re.search(r"Office Action Summary", text)
    if not s:
        return None
    e = re.search(r"DETAILED ACTION", text[s.end():])
    return text[s.start(): s.end() + (e.start() if e else 6000)]


def parse_summary(summary, inv, warn):
    claims = {"pending": [], "rejected": [], "objected": [], "allowed": [], "withdrawn": [], "restricted": []}
    if summary is None:
        inv["claims"] = dict(claims, confidence="low", source="none")
        return False
    flat = collapse(summary)
    found = False
    for m in re.finditer(r"Claim\(s\)\s+(?P<list>.*?)\s*(?:is/are|are|is)\s+(?P<what>pending|allowed|rejected|"
                         r"objected to|subject to restriction)", flat):
        what = m.group("what").split()[0]
        key = {"pending": "pending", "allowed": "allowed", "rejected": "rejected", "objected": "objected",
               "subject": "restricted"}[what]
        claims[key] = expand_claims(m.group("list"))
        found = True
    m = re.search(r"Of the above claim\(s\)\s+(?P<list>.*?)\s*is/are\s+withdrawn", flat)
    if m:
        claims["withdrawn"] = expand_claims(m.group("list"))
    rs = re.search(r"Responsive to communication\(s\) filed on\s+(\d{1,2}/\d{1,2}/\d{4})", flat)
    if rs:
        inv["responsive_to"] = iso(DATE_RE.match(rs.group(1)))
    p = re.search(r"SHORTENED STATUTORY PERIOD FOR REPLY IS SET TO EXPIRE\s+(\w+)\s+MONTHS?", flat, re.I)
    if p:
        words = {"one": 1, "two": 2, "three": 3, "1": 1, "2": 2, "3": 3, "four": 4, "six": 6}
        inv["ssp_months"] = words.get(p.group(1).lower())
    inv["claims"] = dict(claims, confidence="high" if found else "low", source="office action summary")
    if not found:
        warn("claims", "Office Action Summary found but no claim dispositions parsed")
    # checkbox reading for the action type
    t = None
    a = re.search(r"2a\)\s*(\S)\s*This action is FINAL", flat)
    b = re.search(r"2b\)\s*(\S)\s*This action is non-final", flat)
    if a and b:
        ca, cb = a.group(1) in CHECKED, b.group(1) in CHECKED
        if ca and not cb:
            t = "final"
        elif cb and not ca:
            t = "nonfinal"
    inv["_checkbox_type"] = t
    dr = re.search(r"drawing\(s\) filed on .*?is/are:\s*a\)\s*(\S)\s*accepted or b\)\s*(\S)\s*objected", flat)
    inv["_drawings_objected_box"] = bool(dr and dr.group(2) in CHECKED)
    sp = re.search(r"10\)\s*(\S)\s*The specification is objected to", flat)
    inv["_spec_objected_box"] = bool(sp and sp.group(1) in CHECKED)
    return found


# --------------------------------------------------------------------------- detailed action


def detailed_paragraphs(text):
    """[(section, paragraph_number_or_None, joined_text)] for the DETAILED ACTION."""
    m = re.search(r"DETAILED ACTION", text)
    body = text[m.end():] if m else text
    raw = body.replace("\f", "\n").splitlines()
    lines = []
    for l in raw:
        s = l.strip()
        if re.match(r"^Application/Control Number:", s) or re.match(r"^Art Unit:\s*\d{4}\s*(Page\s+\d+)?$", s) \
                or re.match(r"^Page\s+\d+$", s):
            continue
        lines.append(l.rstrip())
    numbered = sum(1 for l in lines if re.match(r"^\s{0,8}\d{1,3}\.\s+\S", l))
    use_numbers = numbered >= 3
    paras, cur, section, num = [], [], None, None

    def flush():
        if cur:
            paras.append((section, num, collapse(" ".join(cur))))

    for l in lines:
        s = l.strip()
        if s and HEADING_RE.match(s) and len(s) < 90:
            flush()
            cur, num = [], None
            section = s.rstrip(":").lower()
            continue
        nm = re.match(r"^\s{0,8}(\d{1,3})\.\s+(\S.*)$", l)
        if nm and (use_numbers or not cur):
            flush()
            cur, num = [nm.group(2)], int(nm.group(1))
            continue
        if not s:
            if not use_numbers:
                flush()
                cur, num = [], None
            continue
        cur.append(s)
    flush()
    return paras, bool(m)


REJ_RE = re.compile(r"\bClaims?\s+(?P<claims>%s)\s+(?:is|are|is/are|stands?)\s+(?:(?:also|further|again|"
                    r"provisionally|now|hereby)\s+)*rejected\b" % CLAIMLIST, re.I)


def statute_of(sentence):
    s = sentence
    low = s.lower()
    info = {"statute": None, "basis": None, "double_patenting": None, "subtype": None, "provisional": False}
    if "double patenting" in low:
        info["provisional"] = "provisionally" in low
        if "nonstatutory" in low or "non-statutory" in low or "obviousness-type" in low or "obviousness type" in low:
            info.update(statute="nonstatutory (obviousness-type) double patenting", basis="ODP",
                        double_patenting="nonstatutory")
        else:
            info.update(statute="35 U.S.C. 101 (statutory double patenting)", basis="101", double_patenting="statutory")
        return info
    m = re.search(r"35\s*U\.?\s*S\.?\s*C\.?\s*§*\s*(\d{3})((?:\s*\([a-z0-9]+\))*)(?:\s*\(pre-AIA\))?"
                  r"(?:,?\s*(first|second|fourth|sixth)\s+paragraph)?", s, re.I)
    if m:
        sec, sub, para = m.group(1), re.sub(r"\s+", "", m.group(2) or ""), (m.group(3) or "").lower()
        if not sub and para:
            sub = {"first": "(a)", "second": "(b)", "fourth": "(d)", "sixth": "(f)"}[para]
        info["statute"] = "35 U.S.C. %s%s" % (sec, sub)
        if sec in ("102", "103", "101"):
            info["basis"] = sec
        elif sec == "112":
            info["basis"] = "112" + (sub[:3] if sub else "")
        else:
            info["basis"] = "other"
    elif re.search(r"anticipated by", low):
        info.update(statute="35 U.S.C. 102 (inferred)", basis="102")
    elif re.search(r"unpatentable over|obvious over", low):
        info.update(statute="35 U.S.C. 103 (inferred)", basis="103")
    elif "indefinite" in low:
        info.update(statute="35 U.S.C. 112(b) (inferred)", basis="112(b)")
    if info["basis"] == "112(a)" or info["basis"] == "112":
        if "written description" in low:
            info["subtype"] = "written description"
            info["basis"] = "112(a)"
        elif "enablement" in low or "enable" in low:
            info["subtype"] = "enablement"
            info["basis"] = "112(a)"
    if info["basis"] == "112" and "indefinite" in low:
        info["basis"] = "112(b)"
    if info["basis"] == "101" and re.search(r"abstract idea|judicial exception|natural phenomen|law of nature", low):
        info["subtype"] = "eligibility"
    if info["basis"] == "102" and re.search(r"in the alternative.*103|or,? in the alternative", low):
        info["subtype"] = "102/103 alternative"
    return info


def _ref_record(name, raw, how):
    r = normalize_ref(raw) if raw else None
    rec = {"name": name, "number": raw, "canonical": r["canonical"] if r else None,
           "display": r["display"] if r else None, "doc_type": r["doc_type"] if r else None,
           "confidence": "high" if r and not r.get("ambiguous") else "low", "found_by": how}
    if r and r.get("ambiguous"):
        rec["note"] = "number has no kind code; resolve on fetch"
    return rec


def build_ref_map(paras):
    """name -> (raw number) from every 'Name (number)' anywhere in the action."""
    out = {}
    for _, _, t in paras:
        for m in NAMEPAREN_RE.finditer(t):
            num = m.group("num").strip()
            if len(re.findall(r"\d", num)) < 5 or PIN_RE.fullmatch("(" + num + ")"):
                continue
            if normalize_ref(num) is None:
                continue
            key = re.sub(r"\s+et\s+al\.?$", "", m.group("name")).strip()
            out.setdefault(key, num)
    return out


SKIP_NAMES = {"Applicant", "Applicants", "The", "Examiner", "Office", "Claim", "Claims", "However", "Regarding",
              "Specifically", "Further", "See", "Also", "In", "As", "It", "This"}


def refs_in(sentence, refmap):
    found = []
    m = re.search(r"\b(?:over|by)\s+", sentence)
    tail_start = m.end() if m else len(sentence)
    tail = sentence[tail_start:]
    for pm in NAMEPAREN_RE.finditer(tail):
        num = pm.group("num").strip()
        if normalize_ref(num) is None:
            continue
        nm = re.sub(r"\s+et\s+al\.?$", "", pm.group("name")).strip()
        found.append((pm.start(), _ref_record(nm, num, "name (number)")))
    for rx in (PATNO_RE, APPNO_RE):
        for pm in rx.finditer(sentence):
            raw = re.sub(r"^copending\s+", "", pm.group(0), flags=re.I)
            num = re.sub(r"^(?:U\.?\s?S\.?\s+)?(?:Patent|Pat\.)\s+(?:No\.|Number)\s*", "US ", raw, flags=re.I)
            num = re.sub(r"^(?:U\.?\s?S\.?\s+)?(?:Patent\s+)?Application\s+(?:Serial\s+)?No\.\s*", "", num, flags=re.I)
            pos = pm.start() - tail_start
            if not any(r["number"] and normalize_ref(r["number"]) and normalize_ref(num) and
                       normalize_ref(r["number"])["canonical"] == normalize_ref(num)["canonical"] for _, r in found):
                found.append((pos, _ref_record(None, num, "patent/application number")))
    # bare names: "over Smith in view of Jones, and further in view of Park"
    bare = re.sub(r"\([^()]*\)", " ", tail)
    for piece in re.split(r",?\s*(?:and\s+)?(?:further\s+)?(?:in\s+view\s+of|in\s+combination\s+with|as\s+evidenced\s+by|"
                          r"as\s+modified\s+by)\s+|,\s*and\s+|\s+and\s+|,\s*", bare):
        nm = re.match(r"\s*(?:the\s+)?([A-Z][A-Za-z'’\-]+(?:\s+et\s+al\.?)?)", piece)
        if not nm:
            continue
        name = re.sub(r"\s+et\s+al\.?$", "", nm.group(1)).strip()
        if name in SKIP_NAMES or name.upper() == name and len(name) > 1 and name not in ("AAPA",):
            continue
        if any(r["name"] == name for _, r in found):
            continue
        pos = tail.find(name)
        if name in refmap:
            found.append((pos, _ref_record(name, refmap[name], "name resolved from earlier citation")))
        elif name in ("AAPA",) or "admitted" in piece.lower():
            found.append((pos, {"name": "Applicant Admitted Prior Art", "number": None, "canonical": None,
                                "display": None, "doc_type": "aapa", "confidence": "low", "found_by": "name"}))
        else:
            rec = _ref_record(name, None, "name only (no number found)")
            rec["confidence"] = "low"
            found.append((pos, rec))
    found.sort(key=lambda x: x[0])
    out = []
    for i, (_, r) in enumerate(found):
        r["role"] = "primary" if i == 0 else "secondary"
        out.append(r)
    return out


def mapping_in(body, refs, refmap, first_claim):
    """Per-element mapping from 'Ref discloses X (pinpoint)' patterns."""
    names = [r["name"] for r in refs if r.get("name")] + [n for n in refmap if n not in [r.get("name") for r in refs]]
    name_re = re.compile(r"\b(%s)\b" % "|".join(re.escape(n) for n in names)) if names else None
    verb_re = re.compile(r"(?:^|.*?\b)(?P<ref>[A-Z][A-Za-z'’\-]+)(?:\s+et\s+al\.?)?\s+(?:(?:also|further|explicitly|"
                         r"expressly|clearly|similarly)\s+)*(?:%s)\s+(?P<el>.*)$" % VERBS, re.S)
    out = []
    last = 0
    for pm in PIN_RE.finditer(body):
        seg = body[last:pm.start()]
        last = pm.end()
        pre = body[:pm.start()]
        cm = list(CLAIM_CTX_RE.finditer(pre))
        claim = int(cm[-1].group(1)) if cm else first_claim
        cut = max(seg.rfind(";"), seg.rfind(":"), seg.rfind(". "))
        el = seg[cut + 1:] if cut >= 0 else seg
        el = re.sub(r"^\s*(?:Regarding|As to|As per|With respect to)\s+claims?\s+\d+\s*,\s*", "", el, flags=re.I)
        ref = None
        vm = verb_re.match(el)
        if vm and vm.group("ref") not in SKIP_NAMES:
            ref = vm.group("ref")
            el = vm.group("el")
        elif name_re:
            prev = list(name_re.finditer(pre))
            ref = prev[-1].group(1) if prev else (refs[0]["name"] if refs and refs[0].get("name") else None)
        el = re.sub(r"^\s*(?:and|or|comprising|including|wherein:?)\s+", "", el.strip(), flags=re.I)
        el = el.strip(" ,;:")
        if not el or len(el) < 3:
            continue
        negative = bool(re.search(r"\b(?:does not|do not|fails? to|silent)\b", el, re.I))
        pin = re.sub(r"\s+", " ", pm.group("pin")).strip()
        rnum = None
        for r in refs:
            if r.get("name") == ref:
                rnum = r.get("canonical")
        if rnum is None and ref in refmap:
            n = normalize_ref(refmap[ref])
            rnum = n["canonical"] if n else None
        conf = "high" if ref and rnum and not negative and len(el) < 300 else "low"
        out.append({"claim": claim, "element_text": el, "ref": ref, "ref_number": rnum, "pinpoint": pin,
                    "negative": negative, "confidence": conf})
    return out


OBJ_RE = re.compile(r"\b(?P<what>(?:the\s+)?(?:drawings?|specification|disclosure|abstract|title(?:\s+of\s+the\s+invention)?|"
                    r"oath|declaration)|Claims?\s+(?P<claims>%s))\s+(?:is|are|is/are)\s+(?:also\s+)?objected\s+to\b"
                    % CLAIMLIST, re.I)


def objections_in(paras):
    out = []
    for section, num, t in paras:
        if section in ("response to arguments", "response to amendment", "response to amendments"):
            continue
        for m in OBJ_RE.finditer(t):
            what = m.group("what").lower()
            end = sentence_end(t, m.start())
            sent = t[m.start():end]
            claims = expand_claims(m.group("claims")) if m.group("claims") else []
            if "drawing" in what:
                typ = "drawings"
            elif "abstract" in what:
                typ = "abstract"
            elif "title" in what:
                typ = "title"
            elif "specification" in what or "disclosure" in what:
                typ = "specification"
            elif "oath" in what or "declaration" in what:
                typ = "oath_declaration"
            else:
                typ = "claims"
            sub = None
            if re.search(r"dependent upon a rejected base claim", sent, re.I):
                sub = "allowable_if_rewritten"
            elif re.search(r"informalit", sent, re.I):
                sub = "informalities"
            elif re.search(r"1\.75\(c\)|improper(?:ly)? (?:multiple )?dependent", sent, re.I):
                sub = "dependency_form"
            rule = re.search(r"37\s*C\.?F\.?R\.?\s*§*\s*1\.\d+(?:\([a-z0-9]+\))*", t)
            out.append({"type": typ, "subtype": sub, "claims": claims, "rule": rule.group(0) if rule else None,
                        "text": t[:700], "section": section, "para": num, "decision": None,
                        "confidence": "high" if (typ != "claims" or claims) else "low"})
    dedup, seen = [], set()
    for o in out:
        k = (o["type"], o["subtype"], tuple(o["claims"]), o["para"])
        if k not in seen:
            seen.add(k)
            dedup.append(o)
    for i, o in enumerate(dedup, 1):
        o["id"] = "O%d" % i
    return dedup


def notes_in(paras, text):
    notes = []
    for section, num, t in paras:
        low = t.lower()
        if ("112(f)" in low or "sixth paragraph" in low) and not low.startswith("the following is a quotation") \
                and re.search(r"claim limitation|interpreted under|invok", low):
            lims = []
            for m in re.finditer(r"[\"“]([^\"”]{3,200})[\"”]\s+in\s+claims?\s+(%s)" % CLAIMLIST, t):
                lims.append({"text": m.group(1), "claims": expand_claims(m.group(2))})
            if not lims:
                for m in re.finditer(r"[\"“]([^\"”]{3,200})[\"”]", t):
                    lims.append({"text": m.group(1), "claims": []})
            notes.append({"type": "112f_interpretation", "limitations": lims, "text": t[:900], "para": num,
                          "confidence": "high" if lims and all(l["claims"] for l in lims) else "low"})
        for m in re.finditer(r"(?:The\s+)?rejections?\s+of\s+claims?\s+(%s)\s+under\s+(.{0,60}?)\s+(?:is|are|has been|"
                             r"have been)\s+withdrawn" % CLAIMLIST, t, re.I):
            notes.append({"type": "withdrawn_rejection", "claims": expand_claims(m.group(1)),
                          "statute": m.group(2).strip(" ,"), "para": num, "confidence": "high"})
        if section == "notice of pre-aia or aia status" or "first inventor to file provisions" in low:
            notes.append({"type": "aia_status", "text": t[:300], "para": num,
                          "value": "AIA" if "first inventor to file" in low else "pre-AIA" if "pre-aia" in low else None,
                          "confidence": "high"})
    for title, typ in (("response to arguments", "response_to_arguments"),
                       ("allowable subject matter", "allowable_subject_matter"),
                       ("response to amendment", "response_to_amendment")):
        body = [t for s, _, t in paras if s == title]
        if body:
            notes.append({"type": typ, "text": "\n\n".join(body), "confidence": "high"})
    concl = [t for s, _, t in paras if s == "conclusion"]
    if concl:
        refs = []
        for t in concl:
            for m in NAMEPAREN_RE.finditer(t):
                r = normalize_ref(m.group("num"))
                if r:
                    refs.append({"name": m.group("name"), "number": m.group("num"), "canonical": r["canonical"]})
        if refs:
            notes.append({"type": "art_of_record_not_relied_upon", "refs": refs, "confidence": "low"})
    if re.search(r"THIS ACTION IS MADE FINAL", text, re.I):
        notes.append({"type": "final_statement", "text": "THIS ACTION IS MADE FINAL", "confidence": "high"})
    return notes


def restriction_in(text, paras):
    has = re.search(r"Restriction to one of the following inventions is required|election of species|"
                    r"patentably distinct species|Election/Restrictions?|Restriction/Election", text, re.I)
    if not has:
        return None
    groups = []
    for m in re.finditer(r"(?m)^\s*([IVX]{1,5})\.\s+Claims?\s+(%s),?\s+(?:is\s+|are\s+)?drawn\s+to\s+(.+?)(?:,\s*classified\s+in\s+"
                         r"(.+?))?\.?\s*$" % CLAIMLIST, text):
        groups.append({"group": m.group(1), "claims": expand_claims(m.group(2)), "drawn_to": m.group(3).strip(),
                       "classified_in": (m.group(4) or "").strip() or None})
    species = []
    for m in re.finditer(r"(?m)^\s*Species\s+([A-Z0-9]{1,4})\s*[:,.\-–]\s*(.+)$", text):
        species.append({"species": m.group(1), "text": m.group(2).strip()})
    return {"groups": groups, "species": species, "confidence": "high" if groups or species else "low"}


# --------------------------------------------------------------------------- main parse


def parse(text):
    inv = {"schema": SCHEMA, "parsed": utc_now(), "parser": SCRIPT}
    warns = []

    def warn(where, msg):
        warns.append({"where": where, "message": msg})

    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    lines = text.splitlines()
    parse_header(text, lines, inv, warn)
    parse_summary(summary_region(text), inv, warn)
    paras, has_detailed = detailed_paragraphs(text)
    if not has_detailed:
        warn("detailed_action", "no DETAILED ACTION heading; parsed the whole text")
    refmap = build_ref_map(paras)
    inv["reference_names"] = refmap

    rejections = []
    for idx, (section, num, t) in enumerate(paras):
        if section in NO_REJECTION_SECTIONS:
            continue
        matches = list(REJ_RE.finditer(t))
        for k, m in enumerate(matches):
            end = sentence_end(t, m.start())
            sent = t[m.start():end]
            body_end = matches[k + 1].start() if k + 1 < len(matches) else len(t)
            body = t[end:body_end]
            # unnumbered continuation paragraphs in the same section belong to this rejection
            j = idx + 1
            while k + 1 == len(matches) and j < len(paras) and paras[j][0] == section and paras[j][1] is None \
                    and not REJ_RE.search(paras[j][2]):
                body += " " + paras[j][2]
                j += 1
            st = statute_of(sent)
            claims = expand_claims(m.group("claims"))
            refs = refs_in(sent, refmap) if st["basis"] in ("102", "103", "ODP", "101", "other", None) else []
            if st["basis"] == "101" and not st["double_patenting"]:
                refs = []
            mapping = mapping_in(body, refs, refmap, claims[0] if claims else None) \
                if st["basis"] in ("102", "103") else []
            conf = "high"
            reasons = []
            if not claims:
                conf, reasons = "low", reasons + ["no claims parsed"]
            if not st["basis"]:
                conf, reasons = "low", reasons + ["statute not found"]
            if st["basis"] in ("102", "103") and (not refs or any(not r.get("canonical") for r in refs)):
                conf, reasons = "low", reasons + ["reference(s) without a normalized number"]
            if st["basis"] == "ODP" and not refs:
                conf, reasons = "low", reasons + ["conflicting patent/application not found"]
            rec = {"id": None, "statute": st["statute"], "basis": st["basis"], "subtype": st["subtype"],
                   "double_patenting": st["double_patenting"], "provisional": st["provisional"], "claims": claims,
                   "refs": refs, "mapping": mapping, "text": sent, "section": section, "para": num,
                   "decision": None, "confidence": conf}
            if reasons:
                rec["low_confidence_reasons"] = reasons
            rejections.append(rec)
    for i, r in enumerate(rejections, 1):
        r["id"] = "R%d" % i
    inv["rejections"] = rejections
    inv["objections"] = objections_in(paras)
    inv["notes"] = notes_in(paras, text)
    inv["restriction"] = restriction_in(text, paras)

    # action type
    final_stmt = bool(re.search(r"THIS ACTION IS MADE FINAL", text, re.I))
    cb = inv.pop("_checkbox_type", None)
    if final_stmt:
        typ, tconf = "final", "high"
    elif cb:
        typ, tconf = cb, "high"
    elif inv["restriction"] and not rejections:
        typ, tconf = "restriction", "high" if inv["restriction"]["groups"] or inv["restriction"]["species"] else "low"
    elif re.search(r"Notice of Allowability", text) and not rejections:
        typ, tconf = "notice_of_allowance", "low"
    elif re.search(r"Ex parte Quayle", text[text.find("DETAILED ACTION"):] if "DETAILED ACTION" in text else "") \
            and not rejections:
        typ, tconf = "quayle", "low"
    elif rejections:
        typ, tconf = "nonfinal", "low"
    else:
        typ, tconf = None, "low"
    inv["type"] = typ
    inv["type_label"] = {"final": "Final Rejection", "nonfinal": "Non-Final Rejection", "restriction":
                         "Restriction/Election Requirement", "notice_of_allowance": "Notice of Allowability",
                         "quayle": "Ex parte Quayle action"}.get(typ)
    inv["type_confidence"] = tconf
    if tconf == "low":
        warn("type", "action type %s inferred without a checkbox or 'made final' statement" % typ)
    if inv["type"] == "final" and cb == "nonfinal":
        warn("type", "summary box says non-final but the text says THIS ACTION IS MADE FINAL")

    # cross-checks against the summary
    drw = inv.pop("_drawings_objected_box", False)
    spc = inv.pop("_spec_objected_box", False)
    if drw and not any(o["type"] == "drawings" for o in inv["objections"]):
        inv["objections"].append({"id": "O%d" % (len(inv["objections"]) + 1), "type": "drawings", "subtype": None,
                                  "claims": [], "rule": None, "text": "Summary box: drawings objected to (no detail "
                                  "paragraph parsed)", "section": None, "para": None, "decision": None,
                                  "confidence": "low"})
    if spc and not any(o["type"] in ("specification", "abstract", "title") for o in inv["objections"]):
        inv["objections"].append({"id": "O%d" % (len(inv["objections"]) + 1), "type": "specification", "subtype": None,
                                  "claims": [], "rule": None, "text": "Summary box: specification objected to (no "
                                  "detail paragraph parsed)", "section": None, "para": None, "decision": None,
                                  "confidence": "low"})
    c = inv["claims"]
    union_rej = sorted(set(n for r in rejections for n in r["claims"]))
    union_obj = sorted(set(n for o in inv["objections"] if o["type"] == "claims" for n in o["claims"]))
    if c["source"] == "none":
        c["rejected"], c["objected"] = union_rej, union_obj
        warn("claims", "no Office Action Summary: rejected/objected claims derived from the paragraphs; pending unknown")
    else:
        if c["rejected"] and set(union_rej) != set(c["rejected"]):
            miss = sorted(set(c["rejected"]) - set(union_rej))
            extra = sorted(set(union_rej) - set(c["rejected"]))
            warn("claims", "summary rejected claims differ from rejection paragraphs (summary only: %s; paragraphs "
                           "only: %s)" % (miss or "-", extra or "-"))
            c["confidence"] = "low"
        if c["objected"] and not set(union_obj) >= set(c["objected"]):
            warn("claims", "objected claims in the summary without a parsed objection: %s"
                 % sorted(set(c["objected"]) - set(union_obj)))
    for r in rejections:
        if r["confidence"] == "low":
            warn(r["id"], "low confidence: %s" % "; ".join(r.get("low_confidence_reasons", [])))
        if not r["mapping"] and r["basis"] in ("102", "103"):
            warn(r["id"], "no element mapping parsed; chart it by hand")
    inv["parse_warnings"] = warns
    inv["summary"] = {"rejections": len(rejections), "objections": len(inv["objections"]),
                      "notes": len(inv["notes"]), "mapping_entries": sum(len(r["mapping"]) for r in rejections)}
    return inv


def looks_like_oa(text):
    return bool(re.search(r"Office Action Summary|DETAILED ACTION|rejected under|Application/Control Number|"
                          r"APPLICATION NO\.|Restriction", text))


DEFAULTS = {"input": None, "out": None, "dir": "patent", "json": False, "no_audit": False, "text": None}


def run(args):
    a = to_namespace(args, DEFAULTS)
    res = new_result()
    if a.text is not None:
        text = a.text
    else:
        if not a.input:
            raise UsageError("give the office action text file (pdftotext -layout oa.pdf oa.txt)")
        if not os.path.exists(a.input):
            raise UsageError("file not found: %s" % a.input)
        with open(a.input, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    if not text.strip():
        raise UsageError("office action text is empty (scanned PDF? run OCR first)")
    if not looks_like_oa(text):
        raise UsageError("this does not look like a USPTO office action (no summary, DETAILED ACTION, or rejections)")
    inv = parse(text)
    inv["source"] = a.input
    res["inventory"] = inv
    res["checks_run"] = ["header", "summary", "rejections", "mapping", "objections", "notes", "restriction"]
    if a.out:
        write_json(a.out, inv)
        res["out"] = a.out
        if not a.no_audit and os.path.isdir(a.dir):
            audit(a.dir, "export", False, script=SCRIPT, path=a.out, sha256=sha256_path(a.out),
                  rejections=len(inv["rejections"]))
    else:
        res["checks_skipped"].append({"check": "write", "reason": "no --out given (inventory printed only)"})
    for w in inv["parse_warnings"]:
        res["findings"].append(finding("WARN", "OA_PARSE", w["where"], w["message"]))
    t = res["text"]
    t.append("Application %s; mailed %s; type %s (%s confidence)" % (inv.get("app_no"), inv.get("mailed"),
                                                                     inv.get("type_label") or inv.get("type"),
                                                                     inv.get("type_confidence")))
    c = inv["claims"]
    t.append("Claims: pending %s; rejected %s; objected %s; allowed %s; withdrawn %s (%s)" % (
        _rng(c["pending"]), _rng(c["rejected"]), _rng(c["objected"]), _rng(c["allowed"]), _rng(c["withdrawn"]),
        c["confidence"]))
    for r in inv["rejections"]:
        t.append("  %s  %-6s claims %s  refs: %s  mapping: %d  [%s]" % (
            r["id"], r["basis"], _rng(r["claims"]),
            ", ".join("%s%s" % (x.get("name") or "", (" (%s)" % x["canonical"]) if x.get("canonical") else "")
                      for x in r["refs"]) or "-", len(r["mapping"]), r["confidence"]))
    for o in inv["objections"]:
        t.append("  %s  objection: %s%s%s [%s]" % (o["id"], o["type"], (" (%s)" % o["subtype"]) if o["subtype"] else "",
                                                 (" claims %s" % _rng(o["claims"])) if o["claims"] else "",
                                                 o["confidence"]))
    for n in inv["notes"]:
        if n["type"] in ("112f_interpretation", "withdrawn_rejection"):
            t.append("  note: %s %s" % (n["type"], n.get("limitations") or n.get("claims")))
    if inv.get("mailed") and inv.get("type") in ("nonfinal", "final", "restriction"):
        t.append("Deadline: python3 scripts/deadlines.py oa --mailed %s --type %s" % (inv["mailed"], inv["type"]))
    t.append("First pass only: read the action and correct inventory.json (set each 'decision') before drafting.")
    res["summary"] = dict(inv["summary"], type=inv.get("type"), app_no=inv.get("app_no"), mailed=inv.get("mailed"))
    return finalize(res)


def _rng(nums):
    if not nums:
        return "-"
    nums = sorted(nums)
    out, start, prev = [], nums[0], nums[0]
    for n in nums[1:] + [None]:
        if n is not None and n == prev + 1:
            prev = n
            continue
        out.append(str(start) if start == prev else "%d-%d" % (start, prev))
        if n is not None:
            start = prev = n
    return ",".join(out)


def build_parser():
    p = argparse.ArgumentParser(prog="oa_parse.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    add_common(p)
    p.add_argument("input", help="office action text (pdftotext -layout)")
    p.add_argument("--out", default=None, help="write inventory.json here")
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
