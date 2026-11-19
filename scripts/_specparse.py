"""Shared spec.md parsing for check_spec.py and check_drawings.py (one rule set, so they cannot drift).

- parse_spec(text): '## ' headings are the 37 CFR 1.77(b) sections (references/state-files.md); a first
  '# ' heading before any section is the H1 title; '###' and deeper stay inside their section.
- figure references: fig_ids_in(text) -> [(id, pos)] with ranges and lists expanded ("FIGS. 2A-2C").
- reference numerals: numerals_in(text, line_of) -> [(numeral, name_key, display_name, line)] from
  "name 102" patterns, skipping units, counts, dates, claim and FIG. numbers, patent and application
  numbers, and decimals; "elements 102 and 104" and "strap 104, 106" count every numeral.

Word lists live here once: GENERIC_NAMES, STOP_BEFORE, COUNT_VERBS, UNITS.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_claims as cc  # noqa: E402  (shared claim-language word lists)

# --------------------------------------------------------------------------- sections

# 37 CFR 1.77(b) order: (key, position, heading pattern)
SECTIONS = [
    ("TITLE", 1, r"^TITLE\b"),
    ("CROSS_REFERENCE", 2, r"CROSS[- ]?REFERENCE|RELATED APPLICATIONS?$|PRIORITY CLAIM"),
    ("FEDERAL_FUNDING", 3, r"FEDERALLY[- ]SPONSORED|GOVERNMENT (?:INTEREST|SUPPORT|RIGHTS|LICENSE)|"
                           r"STATEMENT REGARDING FEDERAL"),
    ("JOINT_RESEARCH", 4, r"JOINT RESEARCH"),
    ("SEQUENCE_REFERENCE", 5, r"SEQUENCE LISTING|COMPUTER PROGRAM LISTING|TABLE APPENDIX"),
    ("PRIOR_DISCLOSURE", 6, r"PRIOR DISCLOSURES?|DISCLOSURES? BY THE INVENTOR"),
    ("BACKGROUND", 7, r"BACKGROUND|^(?:TECHNICAL )?FIELD\b|DESCRIPTION OF (?:THE )?RELATED ART"),
    ("SUMMARY", 8, r"SUMMARY"),
    ("BRIEF_DRAWINGS", 9, r"BRIEF DESCRIPTION OF (?:THE )?(?:SEVERAL VIEWS OF (?:THE )?)?(?:DRAWINGS?|FIGURES)|"
                          r"DESCRIPTION OF (?:THE )?(?:DRAWINGS|FIGURES)"),
    ("DETAILED_DESCRIPTION", 10, r"DETAILED DESCRIPTION|DESCRIPTION OF (?:THE )?(?:PREFERRED |EXAMPLE |ILLUSTRATIVE )?"
                                 r"EMBODIMENTS?|^DESCRIPTION$|^DETAILED\b"),
    ("CLAIMS", 11, r"^CLAIMS?\b|WHAT IS CLAIMED|^I CLAIM|^WE CLAIM"),
    ("ABSTRACT", 12, r"ABSTRACT"),
]
SECTION_INDEX = {k: i for k, i, _ in SECTIONS}
# sections whose numbers are not reference numerals (titles, cross-references, statements, claims, abstract)
NON_DESCRIPTION = {"TITLE", "CROSS_REFERENCE", "FEDERAL_FUNDING", "JOINT_RESEARCH", "SEQUENCE_REFERENCE",
                   "PRIOR_DISCLOSURE", "CLAIMS", "ABSTRACT"}
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")


def classify_heading(h):
    u = re.sub(r"\s+", " ", h.strip().upper().strip("#: "))
    for key, _idx, pat in SECTIONS:
        if re.search(pat, u):
            return key
    return None


def parse_spec(text):
    """Return {sections: [{key, heading, line, body:[(line_no, text)]}], h1: str|None}."""
    sections, cur, h1 = [], None, None
    in_code = False
    for ln, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            if cur is not None:
                cur["body"].append((ln, line))
            continue
        m = _HEADING.match(line)
        if m and len(m.group(1)) == 1 and h1 is None and not sections:
            h1 = m.group(2).strip()
            continue
        if m and len(m.group(1)) <= 2:
            cur = {"key": classify_heading(m.group(2)), "heading": m.group(2).strip(), "line": ln, "body": []}
            sections.append(cur)
            continue
        if cur is not None:
            cur["body"].append((ln, line))
    return {"sections": sections, "h1": h1}


def section(spec, key):
    for s in spec["sections"]:
        if s["key"] == key:
            return s
    return None


def body_text(sec):
    if not sec:
        return ""
    return "\n".join(t for _, t in sec["body"] if not _HEADING.match(t))


def description_sections(spec):
    """Sections that may carry reference numerals (everything but NON_DESCRIPTION)."""
    return [s for s in spec["sections"] if s["key"] not in NON_DESCRIPTION]


def description_text(spec):
    return "\n".join(body_text(s) for s in description_sections(spec))


# --------------------------------------------------------------------------- figure references

_ITEM = r"\d+[A-Za-z]?(?:\(\w\))?"
_RANGE = r"(?:\s*(?:-|–|through|to)\s*(?:(?i:FIGS?)\.?\s*)?(?:\d+[A-Za-z]?|[A-Z]\b))"
_SEP = r"\s*(?:,\s*and|,\s*or|,|and|or|&)\s*(?:(?i:FIGS?)\.?\s*)?"
FIG_RE = re.compile(r"(?i:\bFIG(?:URE)?S?)\.?\s*(%s%s?(?:%s%s%s?)*)" % (_ITEM, _RANGE, _SEP, _ITEM, _RANGE))


def _expand(a, b):
    ma = re.match(r"(\d+)([A-Za-z]?)", a)
    mb = re.match(r"(\d*)([A-Za-z]?)", b)
    if not ma or not mb:
        return [a.upper(), b.upper()]
    n1, l1 = ma.group(1), ma.group(2).upper()
    n2, l2 = (mb.group(1) or n1), mb.group(2).upper()
    if l1 and l2 and n1 == n2 and ord(l2) >= ord(l1):
        return ["%s%s" % (n1, chr(c)) for c in range(ord(l1), ord(l2) + 1)]
    if not l1 and not l2 and int(n2) >= int(n1) and int(n2) - int(n1) < 50:
        return [str(k) for k in range(int(n1), int(n2) + 1)]
    return ["%s%s" % (n1, l1), "%s%s" % (n2, l2)]


def fig_ids_in(text):
    """Ordered [(id, char_pos)] for every figure cited: 'FIGS. 2A-2C and 4' -> 2A, 2B, 2C, 4."""
    out = []
    for m in FIG_RE.finditer(text):
        body = re.sub(r"\(\w\)", "", m.group(1))
        for part in re.split(_SEP, body):
            part = part.strip()
            r = re.match(r"^(\d+[A-Za-z]?)\s*(?:-|–|through|to)\s*(?:(?i:FIGS?)\.?\s*)?(\d*[A-Za-z]?)$", part)
            if r:
                ids = _expand(r.group(1), r.group(2))
            else:
                ids = [part.upper()] if re.match(r"^\d+[A-Za-z]?$", part) else []
            for i in ids:
                out.append((i.upper(), m.start()))
    return out


def norm_fig_id(fid):
    """'FIG. 2a' / 'Figure 2A' / '2A' -> '2A'."""
    s = str(fid).strip().upper()
    s = re.sub(r"^FIG(?:URE)?S?\.?\s*", "", s)
    return s.strip()


# --------------------------------------------------------------------------- reference numerals

UNITS = set("""mm cm m km nm um µm μm mil mils in inch inches ft feet foot yd mi mg g kg lb lbs oz ml l
 s sec secs second seconds ms us µs min mins minute minutes h hr hrs hour hours day days week weeks month months
 year years hz khz mhz ghz v volt volts mv kv a amp amps ma µa w watt watts mw kw j kj cal kcal n kn pa kpa mpa
 gpa psi bar atm k °c °f c f % percent degrees degree deg rpm dpi ppi fps px pixels pixel bit bits byte bytes kb
 mb gb tb kbps mbps gbps db dbm times x fold lux lm cd ohm ohms Ω mah wh kwh mph kph nit nits lumen lumens
 word words character characters meters meter millimeters centimeters micrometers microns milliseconds
 trials trial samples sample cycles cycle runs run""".split())
# a number right after one of these words is not a reference numeral
STOP_BEFORE = set("""about approximately approx than to from between least most by of over under within up at
 the a an these those before after remaining another and or
 claim claims fig figs figure figures paragraph paragraphs para no nos number numbers ser serial pat patent
 pub publication application appl section sections cfr usc u.s.c rule rules chapter page pages col column
 columns line lines item items in on since circa year years version model type class v table tables
 example examples embodiment equation eq formula until top bottom
 every per each only exactly nearly roughly around some all any first second third last next
 iso ieee astm ansi sae din iec rfc us wo ep jp cn kr de gb
 january february march april may june july august september october november december
 jan feb mar apr jun jul aug sep sept oct nov dec""".split())
# a number right after one of these verbs is a count ("includes 12 LEDs"), not a reference numeral
COUNT_VERBS = set("""includes include including has have having comprises comprise comprising contains
 contain containing with uses use using holds hold carries carry totals total is are be was were""".split())
# words that name a step, a message, or a flowchart shape rather than a part: names using them are not
# compared, and one of them may carry several numerals ("step 202 ... step 204", "decision 312")
GENERIC_NAMES = set("""step steps decision decisions operation operations block blocks act acts action actions
 stage stages box phase routine subroutine message messages request command signal""".split())
# verbs that follow a figure reference ("FIG. 2 shows ...") and never end an element name
FIG_VERBS = {"show", "shows", "illustrate", "illustrates", "depict", "depicts", "include", "includes",
             "comprise", "comprises", "contain", "contains", "has", "have", "is", "are", "describe",
             "describes", "represent", "represents", "present", "presents", "provide", "provides"}
CONNECTORS = {"and", "or", ",", "through", "to", "-", "–", "&"}

NUM_TOKEN = re.compile(r"[A-Za-z][A-Za-z\-']*|\d+(?:[.,]\d+)*[a-z]?(?:'{1,2}|′)?|[^\sA-Za-z\d]")
_NUMERAL = re.compile(r"^\d{2,4}[a-z]?(?:'{1,2}|′)?$")


def strip_noise(text):
    """Blank out things whose digits are not reference numerals (keeps character positions)."""
    def blank(m):
        return " " * len(m.group(0))
    t = re.sub(r"`[^`]*`", blank, text)                                           # code spans
    t = re.sub(r"\[\d{3,5}\]", blank, t)                                           # paragraph numbers
    t = FIG_RE.sub(blank, t)                                                       # FIG. refs
    t = re.sub(r"\b(?:claims?)\s+\d+(?:\s*(?:-|–|,|and|or|to|through)\s*\d+)*", blank, t, flags=re.I)
    t = re.sub(r"\b\d{1,3}(?:,\d{3})+\b", blank, t)                                # 9,457,709
    t = re.sub(r"\b\d+/\d[\d,]*\b", blank, t)                                      # 63/123,456
    t = re.sub(r"\b\d+\.\d+\b", blank, t)                                          # decimals, 1.84
    t = re.sub(r"\b(?:U\.S\.C\.|C\.F\.R\.|CFR|USC)\b", blank, t)
    return t


def name_stop(w):
    """True when w cannot be part of an element name ("the", "of", "shows", "quickly")."""
    lw = w.lower()
    if lw in cc.DEF_DETS or lw in cc.NEUTRAL_DETS or lw in ("a", "an") or lw in cc.PREPS or \
            lw in cc.CONJ_ETC or lw in FIG_VERBS:
        return True
    if lw in cc.VERB_PURE or (lw.endswith("s") and lw[:-1] in cc.VERB_PURE) or \
            (lw.endswith("es") and lw[:-2] in cc.VERB_PURE) or lw in cc.VERB_3P:
        return True
    if lw.endswith("ly") and len(lw) > 4 and lw not in cc.LY_NOUNS:
        return True
    return False


def numerals_in(text, line_of=None):
    """[(numeral, name_key, display_name, line)] from "name 102" patterns.

    name_key is the normalized element name (tuple of words, head noun singular), or () for a numeral
    that continues a list ("strap 104, 106"): it counts as mentioned but carries no name of its own."""
    line_of = line_of or (lambda pos: None)
    clean = strip_noise(text)
    toks = [(m.group(0), m.start()) for m in NUM_TOKEN.finditer(clean)]
    out = []
    last_ok = False
    for i, (t, pos) in enumerate(toks):
        if not _NUMERAL.match(t):
            if t.lower() not in CONNECTORS and t not in ("(", ")"):
                last_ok = False if not t[:1].isdigit() else last_ok
            continue
        num = t.rstrip("'′") + ("'" * t.count("'"))
        nxt = toks[i + 1][0].lower() if i + 1 < len(toks) else ""
        if nxt in UNITS or nxt in ("°", "%"):
            last_ok = False
            continue
        if nxt == "." and i + 2 < len(toks) and toks[i + 2][0][:1].isdigit():
            last_ok = False
            continue
        j = i - 1
        if j >= 0 and toks[j][0] == "(":
            j -= 1
        if j < 0:
            last_ok = False
            continue
        pw = toks[j][0]
        lpw = pw.lower().rstrip(".")
        if lpw in CONNECTORS and last_ok:
            out.append((num, (), "", line_of(pos)))
            continue
        if not re.match(r"[A-Za-z]", pw) or lpw in STOP_BEFORE or lpw in COUNT_VERBS or name_stop(pw):
            last_ok = False
            continue
        name = []
        k = j
        while k >= 0 and len(name) < 4:
            w = toks[k][0]
            if not re.match(r"[A-Za-z]", w) or name_stop(w):
                break
            name.insert(0, w)
            k -= 1
        if not name:
            last_ok = False
            continue
        out.append((num, cc.norm_words(name), " ".join(name), line_of(pos)))
        last_ok = True
    return out


def numeral_names(text):
    """numeral -> [display names] (empty list for list continuations) for a block of description text."""
    found = {}
    for num, key, disp, _ in numerals_in(text):
        found.setdefault(num, [])
        if disp:
            found[num].append(disp.lower())
    return found
