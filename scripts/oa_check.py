#!/usr/bin/env python3
"""Office-action reply checks: completeness, 37 CFR 1.121(c) claim markup, new matter, clean claims.

    python3 scripts/oa_check.py inventory --inventory inventory.json --response response.md
    python3 scripts/oa_check.py markup    --response response.md [--previous-claims prev.md] [--inventory inventory.json]
    python3 scripts/oa_check.py newmatter --claims response.md --spec spec.md [--previous-claims prev.md]
    python3 scripts/oa_check.py clean     --response response.md --out clean_claims.md
    python3 scripts/oa_check.py all       --inventory inventory.json --response response.md --spec spec.md [--out clean.md]

Markup syntax (Markdown source): additions <u>added</u> (or <ins>); deletions ~~deleted~~
(or <s>/<del>/<strike>) or [[abc]] for five or fewer characters.

Rules checked (37 CFR 1.121(c), text from eCFR; 1.126 for numbering):
  LISTING_*        a complete listing of all claims ever presented, ascending, no gaps or duplicates (1.121(c), (c)(1))
  STATUS_*         exactly one status identifier per claim: (Original), (Currently Amended), (Canceled),
                   (Withdrawn), (Previously Presented), (New), (Not Entered), (Withdrawn - Currently Amended)
  MARKUP_*         only Currently Amended (or Withdrawn - Currently Amended) claims carry markup (1.121(c)(2)-(3));
                   [[...]] only for deletions of five or fewer characters (WARN otherwise; allowed when strike-through
                   "cannot be easily perceived"); markup must be balanced
  CANCELED_TEXT    canceled / not entered claims have no text (1.121(c)(4)(i))
  NEW_*            new claims have no markup (1.121(c)(3)); new numbers continue after the highest number ever
                   presented and never reuse a canceled number (1.121(c)(5); 1.126). Full check needs --previous-claims.
  UNCHANGED_DIFFERS  a clean (Original / Previously Presented / Withdrawn) claim must match its prior text (1.121(c)(3))
  DEP_CANCELED     a pending claim depends on a canceled claim
  NEWMATTER_WORD   an added word not found in the as-filed spec (BLOCK candidate; 35 USC 132)
  NEWMATTER_PHRASE an added 2-3 word phrase whose words appear but not together (WARN: confirm support)

Exit codes: 0 no blocking findings, 1 blocking findings, 2 usage or input error.
"""

import argparse
import difflib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from state import UsageError, add_common, audit, check_schema, cli_main, finalize, finding, new_result, read_json, \
    to_namespace  # noqa: E402

SCRIPT = "oa_check.py"
SCHEMA_INV = "patentassist/oa-inventory@1"

STATUSES = ["Original", "Currently Amended", "Canceled", "Withdrawn", "Previously Presented", "New", "Not Entered",
            "Withdrawn – Currently Amended"]
_STATUS_KEYS = {
    "original": "Original", "currently amended": "Currently Amended", "canceled": "Canceled",
    "cancelled": "Canceled", "withdrawn": "Withdrawn", "previously presented": "Previously Presented",
    "new": "New", "not entered": "Not Entered", "withdrawn - currently amended": "Withdrawn – Currently Amended",
}
MARKED_OK = ("Currently Amended", "Withdrawn – Currently Amended")
NO_TEXT = ("Canceled", "Not Entered")
PENDING = ("Original", "Currently Amended", "Withdrawn", "Previously Presented", "New", "Withdrawn – Currently Amended")

ADD_RE = re.compile(r"<u>(.*?)</u>|<ins>(.*?)</ins>", re.S | re.I)
DEL_RE = re.compile(r"~~(.*?)~~|\[\[(.*?)\]\]|<s>(.*?)</s>|<del>(.*?)</del>|<strike>(.*?)</strike>", re.S | re.I)
ANY_MARK_RE = re.compile(r"</?u>|</?ins>|~~|\[\[|\]\]|</?s>|</?del>|</?strike>", re.I)
CLAIM_LINE_RE = re.compile(r"^\s{0,3}(?:\*\*)?(?:Claims?\s+)?(\d+)(?:\s*(?:-|–|—|through|to)\s*(\d+))?\s*[.)]?\s*"
                           r"(?:\*\*)?\s*(.*)$", re.I)
STATUS_RE = re.compile(r"^\(\s*([^()]{2,40}?)\s*\)\s*", re.S)
LISTING_HEAD_RE = re.compile(r"^#{1,6}\s*(?:amendments?\s+to\s+the\s+claims|listing\s+of\s+claims|claim\s+listing|"
                             r"in\s+the\s+claims)\b", re.I)
CLAIMLIST = (r"\d+(?:\s*(?:-|–|—|through|to)\s*\d+)?"
             r"(?:\s*(?:,\s*(?:and\s+|or\s+)?|and\s+|or\s+|&\s*)\d+(?:\s*(?:-|–|—|through|to)\s*\d+)?)*")


# --------------------------------------------------------------------------- helpers


def expand_claims(s):
    if not s:
        return []
    s = re.sub(r"\b(?:and|or)\b|&", ",", s)
    s = re.sub(r"\s*(?:through|to|–|—)\s*", "-", s)
    out = []
    for p in s.split(","):
        p = p.strip()
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", p)
        if m and int(m.group(2)) >= int(m.group(1)) and int(m.group(2)) - int(m.group(1)) < 1000:
            out.extend(range(int(m.group(1)), int(m.group(2)) + 1))
        elif re.fullmatch(r"\d+", p):
            out.append(int(p))
    return sorted(set(out))


def claims_mentioned(text):
    out = set()
    for m in re.finditer(r"\bclaims?\s+(%s)" % CLAIMLIST, text, re.I):
        out.update(expand_claims(m.group(1)))
    return out


def canon_status(raw):
    k = re.sub(r"\s*[-–—]\s*", " - ", raw.strip().lower())
    k = re.sub(r"\s+", " ", k)
    return _STATUS_KEYS.get(k)


def read_text(path, what):
    if not path:
        raise UsageError("give --%s" % what)
    if not os.path.exists(path):
        raise UsageError("%s file not found: %s" % (what, path))
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def clean_text(t):
    """Apply markup: drop deletions, keep additions."""
    t = DEL_RE.sub("", t)
    t = ADD_RE.sub(lambda m: m.group(1) if m.group(1) is not None else m.group(2), t)
    return _tidy(t)


def prior_text(t):
    """Undo markup: drop additions, keep deletions (the immediate prior version)."""
    t = ADD_RE.sub("", t)
    t = DEL_RE.sub(lambda m: next(g for g in m.groups() if g is not None), t)
    return _tidy(t)


def _tidy(t):
    t = re.sub(r"(?<=\S)[ \t]{2,}", " ", t)
    t = re.sub(r"[ \t]+([,;.:])", r"\1", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    return t.strip()


def flat(t):
    return re.sub(r"\s+", " ", t or "").strip()


def additions(t):
    return [m.group(1) if m.group(1) is not None else m.group(2) for m in ADD_RE.finditer(t)]


# --------------------------------------------------------------------------- listing parser


def split_listing(text):
    """(listing_text, remarks_text, found_heading). The listing runs from an 'Amendments to the
    Claims' style heading to the next heading of the same or higher level."""
    lines = text.splitlines()
    start = None
    level = 2
    for i, l in enumerate(lines):
        if LISTING_HEAD_RE.match(l.strip()):
            start = i
            level = len(l.strip()) - len(l.strip().lstrip("#"))
            break
    if start is None:
        return text, text, False
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        m = re.match(r"^(#{1,6})\s", s)
        if m and len(m.group(1)) <= level and not LISTING_HEAD_RE.match(s):
            end = j
            break
    listing = "\n".join(lines[start + 1:end])
    rest = "\n".join(lines[:start] + lines[end:])
    return listing, rest, True


def parse_listing(text):
    """Claims with status identifiers. Each: {num, status, raw_status, statuses, text, line, aggregated}."""
    claims = []
    cur = None
    in_code = False
    for ln, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not s:
            if cur is not None and not s:
                cur["lines"].append("")
            continue
        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", s) or s.startswith(("{{", "#", ">")) or \
                re.fullmatch(r"\*\*[^*]+\*\*:?", s) or re.match(r"^this listing of claims", s, re.I):
            cur = None if (s.startswith("#") or re.fullmatch(r"-{3,}", s)) else cur
            continue
        m = CLAIM_LINE_RE.match(raw)
        indent = len(raw) - len(raw.lstrip())
        if m and indent <= 3 and (m.group(3).startswith("(") or cur is None or not raw.startswith(" ")):
            body = m.group(3)
            statuses = []
            raw_statuses = []
            while True:
                sm = STATUS_RE.match(body)
                if not sm:
                    break
                cs = canon_status(sm.group(1))
                if cs is None and statuses:
                    break
                raw_statuses.append(sm.group(1))
                statuses.append(cs)
                body = body[sm.end():]
                if cs is None:
                    break
            first = int(m.group(1))
            last = int(m.group(2)) if m.group(2) else first
            if m.group(2) and last < first:
                last = first
            nums = list(range(first, last + 1)) if (last - first) < 500 else [first]
            for n in nums:
                cur = {"num": n, "status": statuses[0] if statuses else None, "statuses": statuses,
                       "raw_status": raw_statuses[0] if raw_statuses else None, "raw_statuses": raw_statuses,
                       "lines": [body] if body.strip() else [], "line": ln, "aggregated": len(nums) > 1}
                claims.append(cur)
            if len(nums) > 1:
                cur = None
            continue
        if cur is not None:
            cur["lines"].append(raw.rstrip())
    for c in claims:
        while c["lines"] and not c["lines"][-1].strip():
            c["lines"].pop()
        c["text"] = "\n".join(c["lines"]).strip()
        del c["lines"]
    return claims


def has_status_markers(text):
    return bool(re.search(r"^\s{0,3}(?:\*\*)?\d+\s*[.)]?\s*(?:\*\*)?\s*\(\s*(?:original|currently amended|canceled|"
                          r"cancelled|withdrawn|previously presented|new|not entered)", text, re.I | re.M))


def parse_plain_claims(text):
    """Plain claims file (claims.md): {num: text}."""
    out = {}
    cur = None
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^\s{0,3}(\d+)\s*[.)]\s*(.*)$", raw)
        if m:
            cur = int(m.group(1))
            out[cur] = m.group(2)
        elif cur is not None:
            out[cur] += "\n" + raw.rstrip()
    return {k: v.strip() for k, v in out.items()}


def load_claim_versions(path):
    """Previous claims: a listing (with statuses) or a plain claims file.
    Returns {num: {"status": str|None, "text": clean text}} and the highest number presented."""
    text = read_text(path, "previous-claims")
    listing, _, _ = split_listing(text)
    out = {}
    if has_status_markers(listing):
        for c in parse_listing(listing):
            st = c["status"]
            t = clean_text(c["text"]) if st in MARKED_OK else c["text"]
            out[c["num"]] = {"status": st, "text": t}
    else:
        for n, t in parse_plain_claims(text).items():
            canceled = bool(re.match(r"^\(\s*(canceled|cancelled)\s*\)", t, re.I))
            out[n] = {"status": "Canceled" if canceled else None, "text": "" if canceled else t}
    return out, (max(out) if out else 0)


def _deps(text):
    out = []
    for m in re.finditer(r"\bclaims?\s+(%s)" % CLAIMLIST, text, re.I):
        out.extend(expand_claims(m.group(1)))
    return sorted(set(out))


# --------------------------------------------------------------------------- checks


def check_markup(response_text, findings, ran, skipped, previous=None, inventory=None):
    listing_text, _, found = split_listing(response_text)
    claims = parse_listing(listing_text) if (found or has_status_markers(response_text)) else []
    ran.append("markup:listing_found")
    if not claims:
        findings.append(finding("BLOCK", "LISTING_MISSING", "response", "no claim listing with status identifiers found "
                                "(expected an 'Amendments to the Claims' section; 37 CFR 1.121(c))"))
        return claims
    # statuses
    ran.append("markup:status_identifiers")
    for c in claims:
        w = "claim %d" % c["num"]
        if not c["raw_statuses"]:
            findings.append(finding("BLOCK", "STATUS_MISSING", w, "no status identifier after the claim number "
                                    "(1.121(c))"))
            continue
        if c["status"] is None:
            findings.append(finding("BLOCK", "STATUS_UNKNOWN", w, "'(%s)' is not a 1.121(c) status identifier; use one "
                                    "of: %s" % (c["raw_status"], ", ".join("(%s)" % s for s in STATUSES))))
            continue
        if len(c["statuses"]) > 1:
            findings.append(finding("BLOCK", "STATUS_MULTIPLE", w, "more than one status identifier (%s); use exactly one"
                                    % ", ".join("(%s)" % s for s in c["raw_statuses"])))
        if c["raw_status"].strip().lower() == "cancelled":
            findings.append(finding("WARN", "STATUS_SPELLING", w, "rule spelling is '(Canceled)'"))
    # order, duplicates, gaps
    ran.append("markup:listing_order")
    nums = [c["num"] for c in claims]
    for a, b in zip(nums, nums[1:]):
        if b < a:
            findings.append(finding("BLOCK", "LISTING_ORDER", "claim %d" % b, "claim %d appears after claim %d; the "
                                    "listing must be in ascending order (1.121(c)(1))" % (b, a)))
    seen = set()
    for n in nums:
        if n in seen:
            findings.append(finding("BLOCK", "LISTING_DUPLICATE", "claim %d" % n, "claim number listed more than once"))
        seen.add(n)
    expected_max = max(nums)
    if previous:
        expected_max = max(expected_max, max(previous[0]) if previous[0] else 0)
    if inventory:
        pend = inventory.get("claims", {}).get("pending") or []
        if pend:
            expected_max = max(expected_max, max(pend))
    missing = [n for n in range(1, expected_max + 1) if n not in seen]
    if missing:
        findings.append(finding("BLOCK", "LISTING_INCOMPLETE", "listing", "claim(s) %s missing: the listing must include "
                                "every claim ever presented (1.121(c)); canceled claims may be grouped, e.g. 'Claims "
                                "5-7 (Canceled)'" % _rng(missing)))
    # markup rules
    ran.append("markup:markup_rules")
    for c in claims:
        w = "claim %d" % c["num"]
        st = c["status"]
        t = c["text"]
        marks = bool(ANY_MARK_RE.search(t))
        if st in NO_TEXT:
            if t.strip():
                findings.append(finding("BLOCK", "CANCELED_TEXT", w, "(%s) claim must show no claim text "
                                        "(1.121(c)(4)(i))" % st))
            continue
        if st and not t.strip():
            findings.append(finding("BLOCK", "CLAIM_TEXT_MISSING", w, "(%s) claim has no text; pending and withdrawn "
                                    "claims must be listed with their full text (1.121(c))" % st))
            continue
        bal = []
        if len(re.findall(r"<u>", t, re.I)) != len(re.findall(r"</u>", t, re.I)):
            bal.append("<u>…</u>")
        if t.count("~~") % 2:
            bal.append("~~…~~")
        if t.count("[[") != t.count("]]"):
            bal.append("[[…]]")
        if bal:
            findings.append(finding("BLOCK", "MARKUP_UNBALANCED", w, "unbalanced markup: %s" % ", ".join(bal)))
        if st == "New" and marks:
            findings.append(finding("BLOCK", "NEW_HAS_MARKUP", w, "a (New) claim must be presented in clean text, "
                                    "without underlining (1.121(c)(3))"))
        elif st in ("Original", "Previously Presented", "Withdrawn") and marks:
            findings.append(finding("BLOCK", "MARKUP_NOT_ALLOWED", w, "only (Currently Amended) claims may show markup; "
                                    "a (%s) claim must be clean (1.121(c)(2), (3))" % st))
        if st in MARKED_OK:
            if not marks:
                findings.append(finding("WARN", "AMENDED_NO_MARKUP", w, "status is (%s) but no changes are marked" % st))
            for m in re.finditer(r"\[\[(.*?)\]\]", t, re.S):
                if len(m.group(1)) > 5:
                    findings.append(finding("WARN", "DOUBLE_BRACKET_LONG", w, "[[%s]] deletes %d characters; double "
                                            "brackets are for five or fewer characters, or where strike-through cannot "
                                            "be easily perceived (1.121(c)(2)); use ~~…~~" % (m.group(1)[:30],
                                                                                              len(m.group(1)))))
    # dependencies on canceled claims
    ran.append("markup:dependencies")
    by_num = {c["num"]: c for c in claims}
    for c in claims:
        if c["status"] in PENDING and c["text"]:
            for d in _deps(clean_text(c["text"]) if c["status"] in MARKED_OK else c["text"]):
                if d in by_num and by_num[d]["status"] in NO_TEXT:
                    findings.append(finding("BLOCK", "DEP_CANCELED", "claim %d" % c["num"], "depends on claim %d, "
                                            "which is (%s)" % (d, by_num[d]["status"])))
    # new-claim numbering
    news = [c for c in claims if c["status"] == "New"]
    if previous is None:
        skipped.append({"check": "markup:new_numbering_full", "reason": "no --previous-claims: cannot know the highest "
                        "number ever presented or which numbers were canceled"})
        ran.append("markup:new_numbering_basic")
        old = [c["num"] for c in claims if c["status"] not in ("New",) and c["status"] is not None]
        if news and old:
            hi = max(old)
            for c in news:
                if c["num"] < hi:
                    findings.append(finding("BLOCK", "NEW_NUMBERING", "claim %d" % c["num"], "(New) claim numbered below "
                                            "previously presented claim %d; new claims continue after the highest "
                                            "number ever presented (1.126)" % hi))
        if news:
            findings.append(finding("WARN", "NEW_NUMBERING_UNVERIFIED", "listing", "new claims %s: pass "
                                    "--previous-claims to confirm they continue from the highest number ever presented "
                                    "and reuse no canceled number (1.121(c)(5); 1.126)" % _rng([c["num"] for c in news])))
    else:
        ran.append("markup:new_numbering_full")
        ran.append("markup:previous_versions")
        prev, prev_hi = previous
        expect = prev_hi + 1
        for c in sorted(news, key=lambda x: x["num"]):
            if c["num"] in prev:
                was = prev[c["num"]]["status"] or "presented"
                findings.append(finding("BLOCK", "NEW_REUSES_NUMBER", "claim %d" % c["num"], "claim %d was already "
                                        "presented (%s); a new or reinstated claim takes the next number after %d "
                                        "(1.121(c)(5); 1.126)" % (c["num"], was, prev_hi)))
            elif c["num"] != expect:
                findings.append(finding("BLOCK", "NEW_NUMBERING", "claim %d" % c["num"], "new claims must be numbered "
                                        "consecutively from %d (1.126)" % expect))
                expect = c["num"] + 1
            else:
                expect += 1
        for c in claims:
            p = prev.get(c["num"])
            w = "claim %d" % c["num"]
            if p is None:
                if c["status"] not in ("New", None):
                    findings.append(finding("BLOCK", "STATUS_NOT_NEW", w, "claim %d was not presented before but is "
                                            "marked (%s); it should be (New)" % (c["num"], c["status"])))
                continue
            if p["status"] in NO_TEXT and c["status"] not in NO_TEXT:
                findings.append(finding("BLOCK", "CANCELED_REINSTATED", w, "claim %d was canceled; reinstate it only as "
                                        "a (New) claim with a new number (1.121(c)(5))" % c["num"]))
                continue
            if c["status"] in ("Original", "Previously Presented", "Withdrawn"):
                if flat(c["text"]) != flat(p["text"]):
                    findings.append(finding("BLOCK", "UNCHANGED_DIFFERS", w, "(%s) asserts no change, but the text differs "
                                            "from the prior version (1.121(c)(3)); mark it (Currently Amended) with "
                                            "markup" % c["status"]))
                if c["status"] == "Original" and p["status"] in ("Currently Amended", "Previously Presented", "New",
                                                                  "Withdrawn – Currently Amended"):
                    findings.append(finding("BLOCK", "STATUS_STALE", w, "claim was %s in the prior listing; it is now "
                                            "(Previously Presented), not (Original)" % p["status"]))
            if c["status"] in MARKED_OK and flat(prior_text(c["text"])) != flat(p["text"]):
                findings.append(finding("WARN", "AMENDED_BASE_MISMATCH", w, "removing the additions and restoring the "
                                        "deletions does not reproduce the prior version; markup must be relative to "
                                        "the immediate prior version (1.121(c)(2))"))
    if inventory:
        ran.append("markup:inventory_withdrawn")
        for n in inventory.get("claims", {}).get("withdrawn") or []:
            c = by_num.get(n)
            if c and c["status"] not in ("Withdrawn", "Withdrawn – Currently Amended", "Canceled"):
                findings.append(finding("WARN", "WITHDRAWN_STATUS", "claim %d" % n, "the action lists claim %d as withdrawn "
                                        "but the listing says (%s)" % (n, c["status"])))
    return claims


def _remarks_sections(text):
    """[(heading, body)] for the remarks part of a response."""
    out = []
    head, body = "", []
    for l in text.splitlines():
        s = l.strip()
        m = re.match(r"^#{1,6}\s+(.*)$", s) or re.match(r"^\*\*([^*]{3,200})\*\*\s*$", s)
        if m:
            out.append((head, "\n".join(body)))
            head, body = m.group(1).strip(), []
        else:
            body.append(l)
    out.append((head, "\n".join(body)))
    return [(h, b) for h, b in out if h or b.strip()]


BASIS_PAT = {
    "102": r"\b102\b|anticipat",
    "103": r"\b103\b|obvious(?!ness[- ]type)",
    "101": r"\b101\b|eligib|subject matter",
    "112(a)": r"112\s*\(a\)|112,?\s*first paragraph|written description|enablement",
    "112(b)": r"112\s*\(b\)|112,?\s*second paragraph|indefinite",
    "112(d)": r"112\s*\(d\)|112,?\s*fourth paragraph",
    "ODP": r"double patenting|terminal disclaimer",
}


def check_inventory(inv, response_text, findings, ran, skipped, listing_check=True):
    check_schema(inv, SCHEMA_INV, "inventory")
    listing_text, remarks, found = split_listing(response_text)
    claims = parse_listing(listing_text) if (found or has_status_markers(response_text)) else []
    canceled = set(c["num"] for c in claims if c["status"] in NO_TEXT)
    amended = set(c["num"] for c in claims if c["status"] in MARKED_OK)
    listed = set(c["num"] for c in claims)
    sections = _remarks_sections(remarks)
    # claims named anywhere in the substantive remarks (not the status-of-claims summary)
    all_mentioned = set()
    for h, b in sections:
        if not re.search(r"status of (?:the )?claims|claim status|introduct|conclusion|interview|listing of claims",
                         h, re.I) and h:
            all_mentioned |= claims_mentioned(h + "\n" + b)
    ran.append("inventory:rejections")
    covered_claims = set()
    for r in inv.get("rejections") or []:
        rid = r.get("id") or "?"
        rclaims = set(r.get("claims") or [])
        basis = r.get("basis") or ""
        where = "%s (%s, claims %s)" % (rid, basis or "?", _rng(sorted(rclaims)))
        if r.get("decision"):
            covered_claims |= rclaims
            findings.append(finding("INFO", "DECISION", where, "explicit decision: %s" % r["decision"]))
            continue
        if rclaims and rclaims <= canceled:
            covered_claims |= rclaims
            findings.append(finding("INFO", "MOOT", where, "every rejected claim is canceled"))
            continue
        hits = []
        for h, b in sections:
            hb = h + "\n" + b[:200]
            if re.search(r"\b%s\b" % re.escape(rid), h) or re.search(r"\[%s\]" % re.escape(rid), b[:300]):
                hits.append((h, b))
                continue
            pat = BASIS_PAT.get(basis)
            if pat and re.search(pat, h, re.I) and (claims_mentioned(h) & rclaims or not claims_mentioned(h)):
                if basis in ("102", "103") and re.search(r"\brejection", hb, re.I) is None and "§" not in h:
                    continue
                hits.append((h, b))
        if not hits:
            findings.append(finding("BLOCK", "REJECTION_UNANSWERED", where, "no remarks section answers this rejection "
                                    "(heading naming the statute and claims, or '[%s]'), and no decision is recorded "
                                    "in the inventory" % rid))
            continue
        sec_claims, head_claims = set(), False
        for h, b in hits:
            hc = claims_mentioned(h)
            head_claims = head_claims or bool(hc)
            sec_claims |= hc | claims_mentioned(b)
        if head_claims:
            covered_claims |= rclaims & (sec_claims | canceled)
        else:
            covered_claims |= rclaims  # e.g. a "Double Patenting" heading that names no claims
    ran.append("inventory:objections")
    for o in inv.get("objections") or []:
        oid = o.get("id") or "?"
        typ = o.get("type")
        oclaims = set(o.get("claims") or [])
        where = "%s (%s%s)" % (oid, typ, (", claims %s" % _rng(sorted(oclaims))) if oclaims else "")
        if o.get("decision"):
            covered_claims |= oclaims
            findings.append(finding("INFO", "DECISION", where, "explicit decision: %s" % o["decision"]))
            continue
        ok = False
        if typ == "drawings":
            ok = any(re.search(r"drawing|replacement sheet|figure|\bFIG", h + "\n" + b, re.I) and
                     re.search(r"drawing|objection|replacement", h, re.I) for h, b in sections) or \
                bool(re.search(r"replacement sheet", response_text, re.I))
        elif typ in ("specification", "abstract", "title"):
            ok = any(re.search(typ if typ != "specification" else r"specification|disclosure", h, re.I)
                     for h, b in sections) or bool(re.search(r"^#{1,6}\s*amendments?\s+to\s+the\s+(?:specification|"
                                                             r"abstract|title)", response_text, re.I | re.M))
        elif typ == "oath_declaration":
            ok = any(re.search(r"oath|declaration", h, re.I) for h, b in sections)
        else:
            obj_secs = [(h, b) for h, b in sections if re.search(r"objection|informalit|allowable", h, re.I)]
            in_obj = set()
            for h, b in obj_secs:
                in_obj |= claims_mentioned(h + "\n" + b)
            pool = canceled | amended | (all_mentioned if o.get("subtype") == "allowable_if_rewritten" else in_obj)
            if oclaims and oclaims <= pool:
                ok = True
            elif not oclaims:
                ok = bool(obj_secs)
        if ok:
            covered_claims |= oclaims
        else:
            findings.append(finding("BLOCK", "OBJECTION_UNANSWERED", where, "no remarks section, amendment, or decision "
                                    "answers this objection"))
    ran.append("inventory:claims")
    invc = inv.get("claims") or {}
    targets = {}
    for n in invc.get("rejected") or []:
        targets.setdefault(n, "rejected")
    for n in invc.get("objected") or []:
        targets.setdefault(n, "objected")
    for r in inv.get("rejections") or []:
        for n in r.get("claims") or []:
            targets.setdefault(n, "rejected (%s)" % r.get("id"))
    for n in sorted(targets):
        if n in canceled or n in all_mentioned or n in covered_claims:
            continue
        findings.append(finding("BLOCK", "CLAIM_UNANSWERED", "claim %d" % n, "%s claim is neither canceled, addressed "
                                "in the remarks, nor covered by a recorded decision" % targets[n]))
    pend = invc.get("pending") or []
    if claims and not listing_check:
        pass  # the markup check reports listing gaps
    elif claims:
        ran.append("inventory:listing_covers_pending")
        miss = [n for n in pend if n not in listed]
        if miss:
            findings.append(finding("BLOCK", "LISTING_INCOMPLETE", "listing", "pending claim(s) %s from the action are not "
                                    "in the claim listing" % _rng(miss)))
    else:
        skipped.append({"check": "inventory:listing_covers_pending", "reason": "no claim listing in the response"})
    for n in inv.get("notes") or []:
        if n.get("type") == "112f_interpretation":
            for lim in n.get("limitations") or []:
                findings.append(finding("INFO", "NOTE_112F", "claims %s" % _rng(lim.get("claims") or []),
                                        "examiner reads \"%s\" under 112(f); decide whether to address it"
                                        % lim.get("text")))
    return claims


# --------------------------------------------------------------------------- new matter


STOP = set("""a an the of to in on at by for with from into onto via and or nor but if then than that which who whom whose
where wherein whereby whereas when while as is are was were be been being has have having had do does did can may
might must shall should will would could said such same each every any all some both either neither other another
one ones first second third fourth fifth plurality least more less further also thereof therein thereto thereby
therewith herein claim claims comprising comprises comprise comprised including includes include consisting consists
having it its this these those not no so about configured adapted operable respectively respective wherein
based upon over under between among within without along made make use used using being""".split())


def _stem(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if w.endswith("sses"):
        return w[:-2]
    if len(w) > 4 and (w.endswith(("ches", "shes", "xes", "zes"))):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def norm_tokens(text):
    t = text.lower()
    t = re.sub(r"[-‐‑–—/_]", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return [_stem(w) for w in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", t)]


def _terms(segment):
    """Content words and 2-3 word content phrases from added text."""
    raw = re.findall(r"[A-Za-z0-9]+(?:\.[0-9]+)?", re.sub(r"[-‐‑–—/_]", " ", re.sub(r"<[^>]+>", " ", segment)))
    toks = [_stem(r.lower()) for r in raw]
    words, phrases, run = [], [], []
    for tok, rw in zip(toks, raw):
        if tok in STOP or (len(tok) < 2 and not tok.isdigit()):
            if len(run) >= 2:
                phrases.extend(_ngrams(run))
            run = []
            continue
        words.append((tok, rw))
        run.append((tok, rw))
    if len(run) >= 2:
        phrases.extend(_ngrams(run))
    return words, phrases


def _ngrams(run):
    out = []
    for n in (2, 3):
        for i in range(len(run) - n + 1):
            seg = run[i:i + n]
            out.append((" ".join(t for t, _ in seg), " ".join(r for _, r in seg)))
    return out


def added_segments(claims_text, previous_path, findings, ran, skipped):
    """{claim_num: [added text segments]} from markup, New claims, or a diff with --previous-claims."""
    listing_text, _, found = split_listing(claims_text)
    prev = None
    if previous_path:
        prev, _ = load_claim_versions(previous_path)
    out = {}
    if found or has_status_markers(claims_text):
        claims = parse_listing(listing_text)
        for c in claims:
            if c["status"] == "New":
                out[c["num"]] = [clean_text(c["text"])]
            elif c["status"] not in NO_TEXT:
                adds = additions(c["text"])  # underlined text counts as added whatever the status says
                if adds:
                    out[c["num"]] = adds
                elif c["status"] in MARKED_OK and not ANY_MARK_RE.search(c["text"]) and prev and c["num"] in prev:
                    out[c["num"]] = _diff_added(prev[c["num"]]["text"], c["text"])  # amended but unmarked
        ran.append("newmatter:added_text_from_markup")
        return out
    plain = parse_plain_claims(claims_text)
    if not plain:
        raise UsageError("no claims found in the --claims file")
    if prev is None:
        skipped.append({"check": "newmatter:added_text", "reason": "claims have no markup or status identifiers and no "
                        "--previous-claims was given, so the added words cannot be identified"})
        return None
    for n, t in plain.items():
        if n not in prev or prev[n]["status"] in NO_TEXT:
            out[n] = [t]
        else:
            segs = _diff_added(prev[n]["text"], t)
            if segs:
                out[n] = segs
    ran.append("newmatter:added_text_from_diff")
    return out


def _diff_added(old, new):
    a, b = old.split(), new.split()
    segs = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("insert", "replace"):
            segs.append(" ".join(b[j1:j2]))
    return segs


def check_newmatter(claims_text, spec_text, findings, ran, skipped, previous_path=None, extra_support=None):
    segs = added_segments(claims_text, previous_path, findings, ran, skipped)
    if segs is None:
        return {}
    support = spec_text + "\n" + (extra_support or "")
    stoks = norm_tokens(support)
    vocab = set(stoks)
    joined = set(a + b for a, b in zip(stoks, stoks[1:]))
    sflat = " " + " ".join(stoks) + " "
    ran.append("newmatter:words")
    ran.append("newmatter:phrases")
    report = {}
    vocab_list = sorted(vocab)
    for num in sorted(segs):
        bad_words, bad_phrases = [], []
        seen = set()
        for seg in segs[num]:
            words, phrases = _terms(seg)
            for tok, raww in words:
                if tok in seen:
                    continue
                seen.add(tok)
                if tok in vocab or tok in joined:
                    continue
                near = difflib.get_close_matches(tok, vocab_list, n=3, cutoff=0.75)
                bad_words.append(raww)
                findings.append(finding("BLOCK", "NEWMATTER_WORD", "claim %d" % num, "added word '%s' does not appear in "
                                        "the as-filed specification%s; cite support or drop it (35 USC 132)"
                                        % (raww, (" (nearest: %s)" % ", ".join(near)) if near else "")))
            for ph, rawp in phrases:
                if ph in seen:
                    continue
                seen.add(ph)
                parts = ph.split()
                if any(p not in vocab and p not in joined for p in parts):
                    continue  # already reported as a word
                if (" %s " % ph) in sflat or ph.replace(" ", "") in vocab:
                    continue
                n = len(parts)
                grams = set(" ".join(stoks[i:i + n]) for i in range(len(stoks) - n + 1) if parts[0] in stoks[i:i + n]
                            or parts[-1] in stoks[i:i + n])
                near = difflib.get_close_matches(ph, sorted(grams), n=2, cutoff=0.6)
                bad_phrases.append(rawp)
                findings.append(finding("WARN", "NEWMATTER_PHRASE", "claim %d" % num, "added phrase '%s' is not in the "
                                        "specification as a phrase (its words are)%s; confirm the combination is "
                                        "supported" % (rawp, (" (nearest: %s)" % "; ".join(near)) if near else "")))
        report[num] = {"segments": segs[num], "unsupported_words": bad_words, "unsupported_phrases": bad_phrases}
    return report


# --------------------------------------------------------------------------- clean


def clean_claims(claims, include_withdrawn=True):
    """Clean claims.md for check_claims.py: markup applied; canceled and not-entered claims kept as
    'N. (Canceled)' so numbering checks see every number (1.126); withdrawn claims keep '(Withdrawn)'
    so check_claims.py leaves them out of fee counts."""
    lines = ["# Claims", ""]
    kept = []
    for c in claims:
        if c["status"] in NO_TEXT or (c["status"] is None and not c["text"]):
            lines.append("%d. (Canceled)" % c["num"])
            lines.append("")
            continue
        withdrawn = c["status"] in ("Withdrawn", "Withdrawn – Currently Amended")
        if withdrawn and not include_withdrawn:
            continue
        t = clean_text(c["text"])
        first, _, rest = t.partition("\n")
        lines.append("%d. %s%s" % (c["num"], "(Withdrawn) " if withdrawn else "", first.strip()))
        if rest.strip():
            lines.extend(rest.splitlines())
        lines.append("")
        kept.append(c["num"])
    return "\n".join(lines).rstrip() + "\n", kept


# --------------------------------------------------------------------------- commands


def _prev(a):
    return load_claim_versions(a.previous_claims) if a.previous_claims else None


def _inv(a, required):
    if not a.inventory:
        if required:
            raise UsageError("give --inventory inventory.json")
        return None
    if not os.path.exists(a.inventory):
        raise UsageError("inventory not found: %s" % a.inventory)
    try:
        inv = read_json(a.inventory)
    except ValueError as e:
        raise UsageError("inventory is not valid JSON: %s" % e)
    return check_schema(inv, SCHEMA_INV, a.inventory)


def cmd_inventory(a, res):
    inv = _inv(a, True)
    check_inventory(inv, read_text(a.response, "response"), res["findings"], res["checks_run"], res["checks_skipped"])


def cmd_markup(a, res):
    claims = check_markup(read_text(a.response, "response"), res["findings"], res["checks_run"], res["checks_skipped"],
                          _prev(a), _inv(a, False))
    res["claims"] = [{"num": c["num"], "status": c["status"]} for c in claims]


def cmd_newmatter(a, res):
    src = a.claims or a.response
    if not src:
        raise UsageError("give --claims (amended claims or the response) and --spec")
    extra = read_text(a.original_claims, "original-claims") if a.original_claims else None
    res["newmatter"] = check_newmatter(read_text(src, "claims"), read_text(a.spec, "spec"), res["findings"],
                                       res["checks_run"], res["checks_skipped"], a.previous_claims, extra)


def cmd_clean(a, res):
    text = read_text(a.response, "response")
    listing, _, found = split_listing(text)
    claims = parse_listing(listing) if (found or has_status_markers(text)) else []
    if not claims:
        raise UsageError("no claim listing with status identifiers found in %s" % a.response)
    out, kept = clean_claims(claims, include_withdrawn=not a.exclude_withdrawn)
    res["clean_claims"] = out
    res["kept"] = kept
    res["checks_run"].append("clean")
    if a.out:
        d = os.path.dirname(a.out)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(out)
        res["out"] = a.out
        res["text"].append("Wrote %s (%d claims: %s). Next: python3 scripts/check_claims.py %s --spec <spec.md>"
                           % (a.out, len(kept), _rng(kept), a.out))
    else:
        res["text"].append(out.rstrip())


def cmd_all(a, res):
    f, ran, skipped = res["findings"], res["checks_run"], res["checks_skipped"]
    if not a.response and not (a.claims and a.spec):
        raise UsageError("all needs --response (and --inventory, --spec for the full set)")
    resp = read_text(a.response, "response") if a.response else None
    if a.inventory and resp is not None:
        check_inventory(_inv(a, True), resp, f, ran, skipped, listing_check=False)
    else:
        skipped.append({"check": "inventory", "reason": "needs --inventory and --response"})
    if resp is not None:
        check_markup(resp, f, ran, skipped, _prev(a), _inv(a, False))
    else:
        skipped.append({"check": "markup", "reason": "needs --response"})
    src = a.claims or a.response
    if src and a.spec:
        extra = read_text(a.original_claims, "original-claims") if a.original_claims else None
        res["newmatter"] = check_newmatter(read_text(src, "claims"), read_text(a.spec, "spec"), f, ran, skipped,
                                           a.previous_claims, extra)
    else:
        skipped.append({"check": "newmatter", "reason": "needs --spec and --claims or --response"})
    if a.out and resp is not None:
        cmd_clean(a, res)
    else:
        skipped.append({"check": "clean", "reason": "no --out given"})


COMMANDS = {"inventory": cmd_inventory, "markup": cmd_markup, "newmatter": cmd_newmatter, "clean": cmd_clean,
            "all": cmd_all}
DEFAULTS = {"command": None, "dir": "patent", "json": False, "no_audit": False, "inventory": None, "response": None,
            "claims": None, "spec": None, "previous_claims": None, "original_claims": None, "out": None,
            "exclude_withdrawn": False}


def _rng(nums):
    nums = sorted(set(nums))
    if not nums:
        return "-"
    out, start, prev = [], nums[0], nums[0]
    for n in nums[1:] + [None]:
        if n is not None and n == prev + 1:
            prev = n
            continue
        out.append(str(start) if start == prev else "%d-%d" % (start, prev))
        if n is not None:
            start = prev = n
    return ",".join(out)


def run(args):
    a = to_namespace(args, DEFAULTS)
    if a.command not in COMMANDS:
        raise UsageError("command must be one of %s" % ", ".join(COMMANDS))
    res = new_result()
    res["command"] = a.command
    COMMANDS[a.command](a, res)
    res = finalize(res)
    blocks = res["summary"]["blocking"]
    if a.command != "clean":
        required_skipped = [s for s in res["checks_skipped"] if s["check"] not in ("clean",)]
        if blocks:
            res["text"].append("%d blocking finding(s)." % blocks)
        elif required_skipped:
            res["text"].append("No blocking findings in the checks that ran; some checks were skipped (see below), so "
                               "this is not a clean bill.")
        else:
            res["text"].append("No blocking findings; every check ran.")
    if not a.no_audit and os.path.isdir(a.dir):
        audit(a.dir, "check", False, script=SCRIPT, command=a.command, blocking=blocks,
              warnings=res["summary"]["warnings"])
    return res


def build_parser():
    p = argparse.ArgumentParser(prog="oa_check.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    add_common(p)
    sp = p.add_subparsers(dest="command")

    def sub(name, help_, opts):
        s = sp.add_parser(name, help=help_)
        add_common(s, sub=True)
        for o in opts:
            if o == "exclude-withdrawn":
                s.add_argument("--exclude-withdrawn", action="store_true", help="omit withdrawn claims from clean output")
            else:
                s.add_argument("--" + o, default=None)
        return s

    sub("inventory", "every rejection, objection, and rejected/objected claim is answered",
        ["inventory", "response"])
    sub("markup", "37 CFR 1.121(c) claim listing and markup", ["response", "previous-claims", "inventory"])
    sub("newmatter", "added words/phrases must appear in the as-filed spec",
        ["claims", "response", "spec", "previous-claims", "original-claims"])
    sub("clean", "apply markup and write clean claims for check_claims.py (canceled kept as 'N. (Canceled)')",
        ["response", "out", "exclude-withdrawn"])
    sub("all", "inventory + markup + newmatter (+ clean with --out)",
        ["inventory", "response", "claims", "spec", "previous-claims", "original-claims", "out", "exclude-withdrawn"])
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
