#!/usr/bin/env python3
"""Parse messy patent / publication / application numbers into canonical forms.

Examples:
    python3 scripts/normalize_number.py "US 9,457,709 B2" "US 2016/0144773 A1" 16/123,456
    printf 'EP1234567B1\\nWO2019/123456\\n' | python3 scripts/normalize_number.py --json

Each result: {input, country, number, kind, doc_type, canonical, display,
google_patents_url, ambiguous, candidates, notes, ok}.
doc_type: patent | application_pub | application_no | design | plant | reissue | null.

A bare US number without a kind code is marked ambiguous and lists candidates
(B2 then B1; plus an application-number reading for 8-digit numbers that could be
either). Kind-less canonical forms still resolve on Google Patents, which reports
the real kind; patent_fetch.py uses that.

Exit codes: 0 all parsed, 2 at least one input could not be parsed.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import UsageError, add_common, cli_main, finalize, new_result, to_namespace  # noqa: E402

GOOGLE = "https://patents.google.com/patent/%s/en"

# First US utility patent issued under the 2001 kind-code system (Jan 2, 2001).
US_FIRST_2001_PATENT = 6167130
# US utility patent numbers had not reached this value by late 2026 (12,000,000 issued June 2024).
US_PATENT_NUMBER_CEILING = 13500000

_PREFIX_RE = re.compile(
    r"^\s*(?:U\.?\s*S\.?\s*)?(?:"
    r"(?P<pub>(?:patent\s+)?(?:application\s+)?pub(?:lication|\.)?\s*(?:no\.?|number|#)?)"
    r"|(?P<app>(?:patent\s+)?(?:application|appl?n?\.?|ser(?:ial)?\.?)\s*(?:ser(?:ial)?\.?\s*)?(?:no\.?|number|#)?)"
    r"|(?P<pat>(?:design\s+|plant\s+|reissue\s+)?pat(?:ent|\.)?\s*(?:no\.?|number|#)?)"
    r")\s*[:#]?\s*",
    re.I,
)


def _strip_prefix(s):
    """Remove 'U.S. Pat. No.', 'Publication No.', 'Application Ser. No.' style prefixes."""
    m = _PREFIX_RE.match(s)
    if not m or not m.group(0).strip():
        return s.strip(), None, False
    rest = s[m.end():].strip()
    us = bool(re.match(r"^\s*U\.?\s*S\.?", s, re.I))
    hint = "application_no" if m.group("app") else "application_pub" if m.group("pub") else "patent"
    return rest, hint, us


def _group3(n):
    return "{:,}".format(int(n))


def _url(canonical):
    return GOOGLE % canonical


def _cand(country, number, kind, doc_type, prefix=""):
    canon = "%s%s%s%s" % (country, prefix, number, kind or "")
    return {"canonical": canon, "kind": kind, "doc_type": doc_type, "google_patents_url": _url(canon)}


def _base(raw):
    return {"input": raw, "ok": False, "country": None, "number": None, "kind": None, "doc_type": None,
            "canonical": None, "display": None, "google_patents_url": None, "ambiguous": False,
            "candidates": [], "notes": []}


def _finish(r, ambiguous=None):
    r["ok"] = r["canonical"] is not None
    if ambiguous is not None:
        r["ambiguous"] = ambiguous
    elif r["kind"] is None and r["candidates"]:
        types = set(c["doc_type"] for c in r["candidates"])
        r["ambiguous"] = len(types) > 1
    return r


# ----------------------------------------------------------------- per-format parsers


def _us_app(r, series, rest6, note_extra=None):
    series = series.zfill(2)
    digits = series + rest6
    r.update({"country": "US", "number": digits, "kind": None, "doc_type": "application_no",
              "canonical": "US%s/%s,%s" % (series, rest6[:3], rest6[3:]),
              "display": "%s/%s,%s" % (series, rest6[:3], rest6[3:]),
              "google_patents_url": None, "odp_application_digits": digits})
    s = int(series)
    if 60 <= s <= 63:
        r["notes"].append("US provisional application number; provisionals are never published.")
    elif s == 29:
        r["notes"].append("US design application number.")
    elif s in (90, 95, 96):
        r["notes"].append("US reexamination / supplemental examination control number.")
    elif s == 35:
        r["notes"].append("International design application (Hague) designating the US.")
    else:
        r["notes"].append("US application number; look up its publication or patent before citing.")
    if note_extra:
        r["notes"].append(note_extra)
    return _finish(r, ambiguous=False)


def _us_pub(r, year, serial, kind):
    serial = serial.zfill(7)
    num = "%s%s" % (year, serial)
    kind = kind or None
    r.update({"country": "US", "number": num, "kind": kind, "doc_type": "application_pub"})
    if kind and kind not in ("A1", "A2", "A9", "P1", "P4", "P9"):
        r["notes"].append("Unusual kind %s for a US pre-grant publication." % kind)
    if kind == "P1":
        r["notes"].append("Plant patent application publication.")
    if kind is None:
        r["candidates"] = [_cand("US", num, k, "application_pub") for k in ("A1", "A2", "A9")]
        r["notes"].append("No kind code given; A1 is the usual US publication kind.")
    canon = "US%s%s" % (num, kind or "")
    r.update({"canonical": canon, "display": "US %s/%s%s" % (year, serial, (" " + kind) if kind else ""),
              "google_patents_url": _url(canon)})
    return _finish(r, ambiguous=False)


def _us_numbered(r, prefix, digits, kind, hint):
    """US grants: utility (no prefix), RE, D, PP, H, T."""
    n = int(digits)
    r["country"] = "US"
    if prefix == "RE":
        r.update({"number": "RE%d" % n, "kind": kind, "doc_type": "reissue"})
        if not kind:
            r["candidates"] = [_cand("US", "RE%d" % n, k, "reissue") for k in ("E1", "E")]
            r["notes"].append("No kind code; Google lists post-2001 reissues as E1, older ones as E.")
        canon = "USRE%d%s" % (n, kind or "")
        disp = "US RE%s%s" % (_group3(n), (" " + kind) if kind else "")
    elif prefix == "D":
        r.update({"number": "D%d" % n, "kind": kind, "doc_type": "design"})
        if not kind:
            r["candidates"] = [_cand("US", "D%d" % n, k, "design") for k in ("S1", "S")]
            r["notes"].append("No kind code; Google lists design patents as S1 (older: S).")
        canon = "USD%d%s" % (n, kind or "")
        disp = "US D%s%s" % (_group3(n), (" " + kind) if kind else "")
    elif prefix == "PP":
        r.update({"number": "PP%d" % n, "kind": kind, "doc_type": "plant"})
        if not kind:
            r["candidates"] = [_cand("US", "PP%d" % n, k, "plant") for k in ("P2", "P3", "P")]
            r["notes"].append("No kind code; plant patents are P2 (no prior publication) or P3 (with one).")
        canon = "USPP%d%s" % (n, kind or "")
        disp = "US PP%s%s" % (_group3(n), (" " + kind) if kind else "")
    elif prefix == "H":
        r.update({"number": "H%d" % n, "kind": kind or "H", "doc_type": "patent"})
        r["notes"].append("Statutory invention registration (SIR): prior art, not an enforceable patent.")
        canon = "USH%d%s" % (n, kind or "H")
        disp = "US H%s %s" % (_group3(n), kind or "H")
    elif prefix == "T":
        r.update({"number": "T%d" % n, "kind": kind or "I4", "doc_type": "patent"})
        r["notes"].append("Defensive publication: prior art, not a patent.")
        canon = "UST%d%s" % (n, kind or "I4")
        disp = "US T%d %s" % (n, kind or "I4")
    else:
        return _us_utility(r, digits, kind, hint)
    r.update({"canonical": canon, "display": disp, "google_patents_url": _url(canon)})
    return _finish(r, ambiguous=False)


def _us_utility(r, digits, kind, hint):
    n = int(digits)
    nd = len(str(n))
    if kind:
        if kind.startswith("A") and len(digits) == 11:
            return _us_pub(r, digits[:4], digits[4:], kind)
        doc = "patent"
        if kind not in ("B1", "B2", "A", "E", "E1"):
            r["notes"].append("Unusual kind %s for a US patent." % kind)
        r.update({"number": str(n), "kind": kind, "doc_type": doc, "canonical": "US%d%s" % (n, kind),
                  "display": "US %s %s" % (_group3(n), kind), "google_patents_url": _url("US%d%s" % (n, kind))})
        return _finish(r, ambiguous=False)
    # no kind code
    if nd < 7 and n < US_FIRST_2001_PATENT and hint != "application_no":
        r.update({"number": str(n), "kind": "A", "doc_type": "patent", "canonical": "US%dA" % n,
                  "display": "US %s A" % _group3(n), "google_patents_url": _url("US%dA" % n)})
        r["notes"].append("Pre-2001 US grant: kind A inferred (no kind code given).")
        return _finish(r, ambiguous=False)
    if nd == 7 and n < US_FIRST_2001_PATENT:
        r.update({"number": str(n), "kind": "A", "doc_type": "patent", "canonical": "US%dA" % n,
                  "display": "US %s A" % _group3(n), "google_patents_url": _url("US%dA" % n)})
        r["notes"].append("Pre-2001 US grant: kind A inferred (no kind code given).")
        return _finish(r, ambiguous=False)
    if nd in (7, 8):
        cands = []
        could_be_patent = n < US_PATENT_NUMBER_CEILING and hint != "application_no"
        could_be_app = nd == 8 and hint not in ("patent", "application_pub")
        if hint == "application_no" and nd == 8:
            return _us_app(r, digits[:2], digits[2:])
        if could_be_patent:
            cands += [_cand("US", str(n), "B2", "patent"), _cand("US", str(n), "B1", "patent")]
        if could_be_app:
            series, rest = digits[:2], digits[2:]
            cands.append({"canonical": "US%s/%s,%s" % (series, rest[:3], rest[3:]), "kind": None,
                          "doc_type": "application_no", "google_patents_url": None})
        if not cands:
            r["notes"].append("Number too large for a US patent and no application context.")
            return _finish(r)
        if not could_be_patent and could_be_app:
            return _us_app(r, digits[:2], digits[2:],
                           "Bare 8-digit number above the US patent number range: read as an application number.")
        canon = "US%d" % n
        r.update({"number": str(n), "kind": None, "doc_type": cands[0]["doc_type"], "canonical": canon,
                  "display": "US %s" % _group3(n), "google_patents_url": _url(canon) if could_be_patent else None,
                  "candidates": cands})
        r["notes"].append("No kind code: a US patent number may be B1 (no earlier publication) or B2 "
                          "(earlier publication). The fetch reads the real kind from Google Patents.")
        if could_be_app:
            r["notes"].append("An 8-digit number can also be an application number (%s/%s,%s)." % (
                digits[:2], digits[2:5], digits[5:]))
        return _finish(r, ambiguous=True)
    if nd == 11 and str(n).startswith("20"):
        return _us_pub(r, digits[:4], digits[4:], None)
    if nd == 10 and str(n).startswith("20"):
        r["notes"].append("10-digit publication number padded to the 11-digit form.")
        return _us_pub(r, digits[:4], digits[4:], None)
    r["notes"].append("Cannot tell what kind of US number this is (%d digits)." % nd)
    return _finish(r)


_GENERIC_DOC = {"A": "application_pub", "B": "patent", "C": "patent", "U": "patent", "Y": "patent",
                "S": "design", "E": "reissue"}


def _foreign(r, cc, digits, kind):
    r["country"] = cc
    if cc == "EP":
        num = digits.zfill(7) if len(digits) <= 7 else digits
        if kind:
            doc = "patent" if kind.startswith("B") else "application_pub" if kind.startswith("A") else None
        else:
            doc = None
            r["candidates"] = [_cand("EP", num, "B1", "patent"), _cand("EP", num, "A1", "application_pub"),
                               _cand("EP", num, "A2", "application_pub")]
            r["notes"].append("No kind code: EP A1/A2 are publications, B1 is the granted patent.")
        disp = "EP %s %s %s%s" % (num[0], num[1:4], num[4:], (" " + kind) if kind else "") if len(num) == 7 \
            else "EP %s%s" % (num, (" " + kind) if kind else "")
        r.update({"number": num, "kind": kind, "doc_type": doc, "display": disp})
    elif cc == "WO":
        if len(digits) == 12:
            num = digits
        elif len(digits) == 10:  # 4-digit year + 6? or YYYY + 6 missing; treat as year+serial
            num = digits[:4] + digits[4:].zfill(6)
        elif len(digits) == 7:  # old compact YY + 5 digits
            yy = int(digits[:2])
            num = ("19" if yy >= 70 else "20") + digits[:2] + digits[2:].zfill(6)
            r["notes"].append("Old two-digit-year WO number expanded to WO%s." % num)
        elif len(digits) in (8, 9, 11):
            num = digits[:4] + digits[4:].zfill(6)
        else:
            r["notes"].append("Cannot read WO number.")
            return _finish(r)
        if not kind:
            r["candidates"] = [_cand("WO", num, k, "application_pub") for k in ("A1", "A2", "A3")]
            r["notes"].append("No kind code: WO publications are A1 (with search report), A2, or A3.")
        r.update({"number": num, "kind": kind, "doc_type": "application_pub",
                  "display": "WO %s/%s%s" % (num[:4], num[4:], (" " + kind) if kind else "")})
    elif cc == "CN":
        if kind:
            doc = _GENERIC_DOC.get(kind[0])
            if kind[0] in ("U", "Y"):
                r["notes"].append("Chinese utility model.")
        else:
            doc = None
            r["candidates"] = [_cand("CN", digits, "A", "application_pub"), _cand("CN", digits, "B", "patent"),
                               _cand("CN", digits, "U", "patent")]
            r["notes"].append("No kind code: CN A = published application, B = granted invention, U = utility model.")
        r.update({"number": digits, "kind": kind, "doc_type": doc,
                  "display": "CN %s%s" % (digits, (" " + kind) if kind else "")})
    elif cc == "JP":
        if kind:
            doc = _GENERIC_DOC.get(kind[0])
        elif len(digits) == 10:
            doc = None
            r["candidates"] = [_cand("JP", digits, "A", "application_pub"),
                               {"canonical": "JP%s-%s" % (digits[:4], digits[4:]), "kind": None,
                                "doc_type": "application_no", "google_patents_url": None}]
            r["notes"].append("No kind code: JP year+6 digits is usually a publication (A) but can be an "
                              "application number (Tokugan).")
        else:
            doc = "patent"
            r["candidates"] = [_cand("JP", digits, k, "patent") for k in ("B2", "B1")]
        disp = "JP %s%s" % (("%s-%s" % (digits[:4], digits[4:])) if len(digits) == 10 else digits,
                            (" " + kind) if kind else "")
        r.update({"number": digits, "kind": kind, "doc_type": doc, "display": disp})
    elif cc == "KR":
        if kind:
            doc = _GENERIC_DOC.get(kind[0])
        elif len(digits) == 13:
            doc = None
            r["candidates"] = [_cand("KR", digits, "A", "application_pub"),
                               {"canonical": "KR%s-%s-%s" % (digits[:2], digits[2:6], digits[6:]), "kind": None,
                                "doc_type": "application_no", "google_patents_url": None}]
            r["notes"].append("No kind code: 13 digits is a KR publication (A) or application number.")
        else:
            doc = "patent"
            r["candidates"] = [_cand("KR", digits, k, "patent") for k in ("B1", "B2")]
        disp = "KR %s%s" % (("%s-%s-%s" % (digits[:2], digits[2:6], digits[6:])) if len(digits) == 13 else digits,
                            (" " + kind) if kind else "")
        r.update({"number": digits, "kind": kind, "doc_type": doc, "display": disp})
    else:
        doc = _GENERIC_DOC.get(kind[0]) if kind else None
        if kind is None:
            r["notes"].append("No kind code; document type unknown for %s." % cc)
        elif doc and cc in ("DE", "GB", "FR", "CA", "AU", "TW", "ES", "IT", "NL", "SE", "CH", "AT", "DK",
                            "FI", "NO", "BR", "MX", "IN", "RU", "IL", "SG", "NZ", "ZA", "HK", "BE", "PL"):
            r["notes"].append("Kind %s read with the usual A=publication / B,C=grant convention; "
                              "check the office's kind-code table." % kind)
        r.update({"number": digits, "kind": kind, "doc_type": doc,
                  "display": "%s %s%s" % (cc, digits, (" " + kind) if kind else "")})
    canon = "%s%s%s" % (cc, r["number"], kind or "")
    r.update({"canonical": canon, "google_patents_url": _url(canon)})
    return _finish(r)


# ----------------------------------------------------------------- main entry


def normalize(raw):
    """Normalize one number. Never raises; check result['ok']."""
    r = _base(raw)
    if raw is None or not str(raw).strip():
        r["notes"].append("empty input")
        return r
    s, hint, us_prefix = _strip_prefix(str(raw))
    S = s.upper().strip().rstrip(".;")
    S = S.replace(" ", " ").replace(" ", " ")
    if us_prefix and not re.match(r"^(US|RE|D|PP|H|T|\d)", S.replace(" ", "")):
        r["notes"].append("unrecognized after U.S. prefix")
    if hint:
        r["notes"].append("context: %s" % hint.replace("_", " "))

    # PCT international application
    m = re.match(r"^PCT\s*/?\s*([A-Z]{2})\s*/?\s*(\d{2}|\d{4})\s*/?\s*(\d{4,6})$", S)
    if m:
        cc, yr, ser = m.groups()
        year = yr if len(yr) == 4 else (("19" if int(yr) >= 70 else "20") + yr)
        canon = "PCT/%s%s/%s" % (cc, year, ser.zfill(6))
        r.update({"country": "WO", "number": "%s%s%s" % (cc, year, ser.zfill(6)), "kind": None,
                  "doc_type": "application_no", "canonical": canon, "display": canon})
        r["notes"].append("PCT application number; cite its WO publication.")
        return _finish(r, ambiguous=False)

    # US application number: 16/123,456 or 16/123456 (optionally US prefix)
    m = re.match(r"^(?:US\s*)?(\d{2})\s*/\s*(\d{3}),?\s*(\d{3})$", S)
    if m:
        return _us_app(r, m.group(1), m.group(2) + m.group(3))

    # JP application with hyphen: JP2019-123456 / 特願 style
    m = re.match(r"^JP\s*(\d{4})\s*-\s*(\d{6})$", S)
    if m:
        num = m.group(1) + m.group(2)
        r.update({"country": "JP", "number": num, "doc_type": "application_no",
                  "canonical": "JP%s-%s" % m.groups(), "display": "JP %s-%s" % m.groups()})
        r["notes"].append("JP application number (Tokugan); cite its publication.")
        return _finish(r, ambiguous=False)

    # JP pre-2000 era numbers as Google Patents prints them: JPS62195890A (Showa), JPH0570913B2 (Heisei)
    m = re.match(r"^JP\s*([SH])\s*(\d{2})\s*-?\s*(\d{4,7})\s*([A-Z]\d?)?$", S)
    if m:
        era, yy, ser, kind = m.groups()
        num = era + yy + ser
        canon = "JP%s%s" % (num, kind or "")
        doc = _GENERIC_DOC.get(kind[0]) if kind else None
        r.update({"country": "JP", "number": num, "kind": kind, "doc_type": doc, "canonical": canon,
                  "display": "JP %s%s-%s%s" % (era, yy, ser, (" " + kind) if kind else ""),
                  "google_patents_url": _url(canon) if kind else None})
        r["notes"].append("JP %s-era number (%s %s); the text on Google Patents is usually a machine translation."
                          % ("Showa" if era == "S" else "Heisei", "Showa" if era == "S" else "Heisei", yy))
        if not kind:
            r["notes"].append("No kind code: add A (unexamined publication) or B2 (examined) before fetching.")
        return _finish(r, ambiguous=False)

    # KR application: KR10-2019-0012345
    m = re.match(r"^KR\s*(\d{2})\s*-\s*(\d{4})\s*-\s*(\d{7})$", S)
    if m:
        r.update({"country": "KR", "number": "".join(m.groups()), "doc_type": "application_no",
                  "canonical": "KR%s-%s-%s" % m.groups(), "display": "KR %s-%s-%s" % m.groups()})
        r["notes"].append("KR application number; cite its publication.")
        return _finish(r, ambiguous=False)

    # EP application with check digit: EP19123456.7 / EP 19 123 456.7
    m = re.match(r"^EP\s*(\d{2})\s*(\d{3})\s*(\d{3})\s*\.\s*(\d)$", S)
    if m:
        num = "".join(m.groups()[:3])
        r.update({"country": "EP", "number": num, "doc_type": "application_no",
                  "canonical": "EP%s.%s" % (num, m.group(4)), "display": "EP %s.%s" % (num, m.group(4))})
        r["notes"].append("EP application number; cite the EP publication (A1/B1).")
        return _finish(r, ambiguous=False)

    # CN application: CN201910123456.7
    m = re.match(r"^CN\s*(\d{12}|\d{8})\s*\.\s*([\dX])$", S)
    if m:
        r.update({"country": "CN", "number": m.group(1), "doc_type": "application_no",
                  "canonical": "CN%s.%s" % m.groups(), "display": "CN %s.%s" % m.groups()})
        r["notes"].append("CN application number; cite the CN publication.")
        return _finish(r, ambiguous=False)

    # WO with slash: WO2019/123456, WO 99/12345
    m = re.match(r"^WO\s*(\d{2}|\d{4})\s*/\s*(\d{4,6})\s*([A-Z]\d?)?$", S)
    if m:
        yr, ser, kind = m.groups()
        year = yr if len(yr) == 4 else (("19" if int(yr) >= 70 else "20") + yr)
        return _foreign(r, "WO", year + ser.zfill(6), kind)

    # US publication with slash or dash: US 2016/0144773 A1, 2016/144773, US-2016-0144773-A1
    m = re.match(r"^(?:US\s*-?\s*)?(20\d{2})\s*[/-]\s*(\d{5,7})\s*-?\s*([A-Z]\d?)?$", S)
    if m:
        return _us_pub(r, m.group(1), m.group(2), m.group(3))

    compact = re.sub(r"[\s,./\-]", "", S)
    m = re.match(r"^([A-Z]{2})?(RE|PP|D|H|T)?(\d+)([A-Z]\d?)?$", compact)
    if not m:
        r["notes"].append("unrecognized number format")
        return r
    cc, pre, digits, kind = m.groups()
    if cc is None and pre is None and compact[:2].isalpha():
        r["notes"].append("unrecognized number format")
        return r
    # 'RE', 'PP' etc. could also be read as a country code by the regex; fix that.
    if cc in ("RE", "PP") and pre is None:
        pre, cc = cc, None
    if cc is None or cc == "US":
        if pre is None and cc is None and hint == "application_no" and len(digits) == 8:
            return _us_app(r, digits[:2], digits[2:])
        return _us_numbered(r, pre, digits, kind, hint)
    if pre:
        r["notes"].append("prefix %s is only used for US documents" % pre)
        return r
    return _foreign(r, cc, digits, kind)


def fetch_candidates(norm):
    """Canonical strings to try on Google Patents, best first. Kind-less input first
    tries the kind-less canonical (Google resolves it and reports the kind)."""
    if not norm.get("ok") or norm.get("doc_type") == "application_no":
        return []
    out = []
    if norm.get("kind"):
        out.append(norm["canonical"])
    else:
        if norm.get("google_patents_url"):
            out.append(norm["canonical"])
        for c in norm.get("candidates") or []:
            if c.get("google_patents_url") and c["canonical"] not in out:
                out.append(c["canonical"])
    return out


def kindless(canonical):
    """'US9457709B2' -> 'US9457709'; 'US20160144773A1' -> 'US20160144773'."""
    m = re.match(r"^([A-Z]{2}(?:RE|PP|D|H|T)?\d+)([A-Z]\d?)?$", canonical or "")
    return m.group(1) if m else canonical


DEFAULTS = {"numbers": [], "json": False, "dir": "patent", "no_audit": True, "stdin_text": None}


def run(args):
    a = to_namespace(args, DEFAULTS)
    nums = list(a.numbers or [])
    if not nums or nums == ["-"]:
        text = a.stdin_text if a.stdin_text is not None else ("" if sys.stdin is None or sys.stdin.isatty()
                                                              else sys.stdin.read())
        nums = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if not nums:
        raise UsageError("give one or more numbers, or pipe them on stdin (one per line)")
    res = new_result()
    results = [normalize(n) for n in nums]
    res["results"] = results
    bad = [x for x in results if not x["ok"]]
    for x in results:
        if not x["ok"]:
            res["text"].append("%-28s  UNPARSED  %s" % (x["input"], "; ".join(x["notes"])))
            continue
        line = "%-28s  %-18s  %-15s  %s" % (x["input"], x["canonical"], x["doc_type"] or "?", x["display"])
        if x["ambiguous"]:
            line += "  AMBIGUOUS: " + ", ".join(c["canonical"] for c in x["candidates"])
        res["text"].append(line)
    res["summary"] = {"parsed": len(results) - len(bad), "unparsed": len(bad),
                      "ambiguous": sum(1 for x in results if x["ambiguous"])}
    if bad:
        res["exit_code"] = 2
    return finalize(res)


def build_parser():
    p = argparse.ArgumentParser(prog="normalize_number.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common(p)
    p.add_argument("numbers", nargs="*", help="numbers to parse; none or '-' reads stdin lines")
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
