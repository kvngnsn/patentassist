#!/usr/bin/env python3
"""Check a patent specification (draft/spec.md) before it is built into a DOCX.

    python3 scripts/check_spec.py [spec.md] [--claims claims.md] [--figures figures.json]
                                  [--filing filing.json] [--type provisional|nonprovisional]
                                  [--dir patent] [--json] [--no-audit]

spec.md defaults to <dir>/draft/spec.md; figures/filing default to <dir>/draft/*.json
when those files exist. Headings follow references/state-files.md (## TITLE ... ## ABSTRACT).

Checks (code: rule):
  SECTION_ORDER     sections in 37 CFR 1.77(b) order; required sections present
  TITLE_LEN         title <= 500 characters (37 CFR 1.72(a)); WARN over 15 words
  ABSTRACT          <= 150 words (37 CFR 1.72(b)); WARN under 50 words, legal phrasing, >1 paragraph
  FIG_COVERAGE      every FIG. in the Detailed Description is in the Brief Description and figures.json,
                    and vice versa (37 CFR 1.74, 1.84(u))
  FIG_SEQUENCE      figures introduced in numerical order, no gaps
  NUMERALS          one numeral = one element; spec numerals <-> figures.json numerals (37 CFR 1.84(p)(5))
  PARA_NUMBERING    explicit [0001] paragraph numbers are consecutive (37 CFR 1.52(b)(6))
  RISKY_WORDS       "the invention", "critical", "must", "always", "only" ... (claim-scope risk)
  FUNDING           federally sponsored research statement when filing.json shows government interest
                    (35 USC 202(c)(6); 37 CFR 1.77(b)(3))
  INCORP_BY_REF     essential material only from U.S. patents / published applications (37 CFR 1.57(d))
  CLAIM_SUPPORT     claim terms appear in the Detailed Description (35 USC 112(a); 37 CFR 1.75(d)(1))
  PROVISIONAL_THIN  thin provisional warning (35 USC 119(e)(1); New Railhead, 298 F.3d 1290)

Exit codes: 0 no blocking findings, 1 blocking findings, 2 usage or input error.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import UsageError, audit, finding, to_namespace  # noqa: E402
import check_claims as cc  # noqa: E402
import _specparse as sp  # noqa: E402  (section, figure and numeral parsing shared with check_drawings.py)
from _specparse import (SECTIONS, SECTION_INDEX, GENERIC_NAMES, UNITS, FIG_VERBS,  # noqa: E402,F401
                        classify_heading, parse_spec, section, body_text)

SCRIPT = "check_spec.py"


RISKY = [
    (r"\b(?:the|this|our) (?:present )?invention\b|\bpresent invention\b",
     "use \"the disclosure\", \"embodiments\" or \"some implementations\"; describing \"the invention\" "
     "invites a court to limit the claims to the features so described"),
    (r"\bcritical(?:ly)?\b", "drop or soften (\"in some embodiments\"); critical language can limit claim scope"),
    (r"\bcrucial\b", "drop or soften; it can be read as a required feature"),
    (r"\bessential(?:ly)?\b", "drop or soften; it can be read as a required feature"),
    (r"\bimportant\b", "drop or soften; it can be read as a required feature"),
    (r"\bkey (?:feature|aspect|element|component)s?\b", "drop or soften; it can be read as a required feature"),
    (r"\bnecessar(?:y|ily)\b", "use \"may\" or \"in some embodiments\" unless truly required"),
    (r"\brequired?\b|\brequires\b", "use \"may\" or \"in some embodiments\" unless truly required"),
    (r"\bmust\b", "use \"may\" or \"in some embodiments\"; \"must\" reads as a claim limitation"),
    (r"\balways\b", "use \"in some embodiments\" or \"typically\""),
    (r"\bnever\b", "use \"in some embodiments\" or \"typically\""),
    (r"(?<!\bnot )\bonly\b(?! if\b)", "check the scope; \"only\" can disclaim other embodiments"),
    (r"\ball embodiments\b", "use \"some embodiments\" unless every embodiment truly shares it"),
    (r"\bpreferred embodiment is the only\b|\bthe only embodiment\b", "never call one embodiment the only one"),
]
ALT_PHRASES = re.compile(r"\b(?:in (?:some|other|certain|another|alternative|further|various) "
                         r"(?:embodiments?|implementations?|examples?|aspects?)|alternatively|"
                         r"in an alternative|may also|as another example|in one (?:or more )?"
                         r"(?:embodiments?|implementations?|examples?)|for example|"
                         r"instead of|optionally)\b", re.I)


# --------------------------------------------------------------------------- parsing


def paragraphs(sec):
    """[(first_line, text)] blank-line separated, headings skipped."""
    out, buf, start = [], [], None
    for ln, t in (sec["body"] if sec else []):
        if not t.strip() or re.match(r"^\s{0,3}#{1,6}\s", t):
            if buf:
                out.append((start, " ".join(buf)))
            buf, start = [], None
            continue
        if start is None:
            start = ln
        buf.append(t.strip())
    if buf:
        out.append((start, " ".join(buf)))
    return out


def words(text):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", text)


# --------------------------------------------------------------------------- figures

def figs_in(text):
    """Ordered list of (fig_id, char_pos) for every figure cited ("FIG. 2A")."""
    return [("FIG. %s" % i, pos) for i, pos in sp.fig_ids_in(text)]


def norm_fig(s):
    r = figs_in(s if re.match(r"\s*fig", s, re.I) else "FIG. " + str(s))
    return r[0][0] if r else str(s).strip().upper()


def fig_sort_key(f):
    m = re.match(r"FIG\. (\d+)([A-Z]?)", f)
    return (int(m.group(1)), m.group(2)) if m else (9999, f)


def figures_json_ids(fj):
    ids = []
    for f in (fj or {}).get("figures", []) or []:
        fid = f.get("id") or f.get("label")
        if fid:
            ids.append(norm_fig(str(fid)))
    return ids


FIG_NUMERAL_KEYS = ("nodes", "steps", "regions", "numerals", "callouts", "participants", "messages", "series")


def figures_json_numerals(fj):
    """numeral -> set of figure ids. Same places check_drawings.py and drawings.py read numerals from."""
    found = {}

    def walk(o, fig):
        if isinstance(o, dict):
            if o.get("numeral") not in (None, ""):
                found.setdefault(str(o["numeral"]).strip(), set()).add(fig)
            for k in FIG_NUMERAL_KEYS:
                if isinstance(o.get(k), list):
                    walk(o[k], fig)
        elif isinstance(o, list):
            for x in o:
                if isinstance(x, (dict, list)):
                    walk(x, fig)
                elif x not in (None, ""):
                    found.setdefault(str(x).strip(), set()).add(fig)

    for f in (fj or {}).get("figures", []) or []:
        fid = str(f.get("id", "?"))
        for k in FIG_NUMERAL_KEYS:
            if isinstance(f.get(k), list):
                walk(f[k], fid)
    return found


# --------------------------------------------------------------------------- numerals

def numerals_in(text, line_of):
    """[(numeral, name_tuple, display_name, line)] from "name 102" patterns (shared parser)."""
    return sp.numerals_in(text, line_of)


def names_compatible(a, b):
    if a == b:
        return True
    if (a and a[-1] in GENERIC_NAMES) or (b and b[-1] in GENERIC_NAMES) or \
            (a and a[0] in GENERIC_NAMES) or (b and b[0] in GENERIC_NAMES):
        return True
    s, l = (a, b) if len(a) <= len(b) else (b, a)
    return l[-len(s):] == s


def _base(numeral):
    m = re.match(r"\d+", numeral)
    return m.group(0) if m else numeral


# --------------------------------------------------------------------------- checks


def _filing_type(a, filing, dirpath):
    if a.type:
        return a.type, "--type"
    for k in ("filing_type", "type", "application_type"):
        v = (filing or {}).get(k)
        if isinstance(v, str) and v:
            return ("provisional" if "provisional" == v.lower() else "nonprovisional"), "filing.json %s" % k
    try:
        with open(os.path.join(dirpath, "state.json"), encoding="utf-8") as fh:
            st = json.load(fh)
        v = ((st.get("phases") or {}).get("draft") or {}).get("filing_type")
        if v:
            return ("provisional" if v == "provisional" else "nonprovisional"), "state.json"
    except (OSError, ValueError):
        pass
    return None, None


def _gov_interest(filing):
    if not isinstance(filing, dict):
        return None
    for k, v in filing.items():
        lk = k.lower()
        if any(x in lk for x in ("government_interest", "gov_interest", "federal_funding",
                                 "federally_sponsored", "government_funding", "federal_support")):
            if isinstance(v, dict):
                if v.get("present") is False or v.get("funded") is False:
                    return False
                return any(bool(x) for x in v.values())
            if isinstance(v, str):
                return bool(v.strip()) and v.strip().lower() not in ("none", "no", "n/a", "false")
            return bool(v)
    return None


def check_sections(spec, ftype, has_figs, has_claims_file, filing, findings):
    keys = [s["key"] for s in spec["sections"]]
    last_idx, last_key = 0, None
    for s in spec["sections"]:
        if s["key"] is None:
            findings.append(finding("INFO", "SECTION_ORDER", "spec.md:L%d" % s["line"],
                                    'unrecognized heading "## %s" (not a 37 CFR 1.77(b) section).' % s["heading"]))
            continue
        idx = SECTION_INDEX[s["key"]]
        if idx < last_idx:
            findings.append(finding("WARN", "SECTION_ORDER", "spec.md:L%d" % s["line"],
                                    '"%s" comes after "%s"; 37 CFR 1.77(b) order is Title, Cross-Reference, '
                                    'Federal Funding, JRA, Sequence Listing, Prior Disclosures, Background, '
                                    'Summary, Brief Description of Drawings, Detailed Description, Claims, '
                                    'Abstract.' % (s["heading"], last_key)))
        if keys.count(s["key"]) > 1 and s is not section(spec, s["key"]):
            findings.append(finding("WARN", "SECTION_ORDER", "spec.md:L%d" % s["line"],
                                    'section "%s" appears more than once.' % s["heading"]))
        last_idx, last_key = max(last_idx, idx), s["heading"]
    nonprov = ftype != "provisional"
    title = section(spec, "TITLE")
    if not title:
        if spec.get("h1"):
            findings.append(finding("INFO", "SECTION_ORDER", "spec.md",
                                    'no "## TITLE" section; using the H1 heading "%s" as the title.' % spec["h1"]))
        elif (filing or {}).get("title"):
            findings.append(finding("WARN", "SECTION_ORDER", "spec.md",
                                    "no TITLE section; the title appears only in filing.json (37 CFR 1.72(a) "
                                    "allows the ADS title, but put it at the top of the spec too)."))
        else:
            findings.append(finding("BLOCK", "SECTION_ORDER", "spec.md",
                                    "no title (37 CFR 1.72(a), 1.77(b)(1))."))
    if not section(spec, "DETAILED_DESCRIPTION"):
        findings.append(finding("BLOCK", "SECTION_ORDER", "spec.md",
                                "no DETAILED DESCRIPTION section; the written description is required "
                                "(35 USC 112(a); 37 CFR 1.71, 1.77(b)(10))."))
    if not section(spec, "BACKGROUND"):
        findings.append(finding("INFO", "SECTION_ORDER", "spec.md",
                                "no BACKGROUND section (recommended, 37 CFR 1.77(b)(7)); keep it short, no admissions."))
    if not section(spec, "SUMMARY"):
        findings.append(finding("WARN" if nonprov else "INFO", "SECTION_ORDER", "spec.md",
                                "no SUMMARY section (37 CFR 1.73, 1.77(b)(8)); a summary tracking the claims "
                                "helps claim support."))
    if has_figs and not section(spec, "BRIEF_DRAWINGS"):
        findings.append(finding("BLOCK", "SECTION_ORDER", "spec.md",
                                "drawings exist but there is no BRIEF DESCRIPTION OF THE DRAWINGS (37 CFR 1.74)."))
    claims_sec = section(spec, "CLAIMS")
    if not claims_sec and not has_claims_file:
        findings.append(finding("BLOCK" if nonprov else "INFO", "SECTION_ORDER", "spec.md",
                                "no CLAIMS section and no claims.md; a nonprovisional needs at least one claim "
                                "(35 USC 112(b); 37 CFR 1.75(a))" if nonprov else
                                "no claims; optional for a provisional but recommended (claims show what the "
                                "provisional must support)."))
    if not section(spec, "ABSTRACT"):
        findings.append(finding("BLOCK" if nonprov else "INFO", "SECTION_ORDER", "spec.md",
                                "no ABSTRACT section (37 CFR 1.72(b))." if nonprov else
                                "no abstract (not required for a provisional)."))


def check_title(spec, findings):
    sec = section(spec, "TITLE")
    title = None
    where = "spec.md"
    if sec:
        for ln, t in sec["body"]:
            if t.strip():
                title, where = t.strip(), "spec.md:L%d" % ln
                break
    elif spec.get("h1"):
        title = spec["h1"]
    if not title:
        if sec:
            findings.append(finding("BLOCK", "TITLE_LEN", "spec.md:L%d" % sec["line"], "TITLE section is empty."))
        return None
    if len(title) > 500:
        findings.append(finding("BLOCK", "TITLE_LEN", where, "title is %d characters; limit is 500 "
                                "(37 CFR 1.72(a))." % len(title)))
    n = len(words(title))
    if n > 15:
        findings.append(finding("WARN", "TITLE_LEN", where, "title is %d words; keep it short and specific "
                                "(MPEP 606)." % n))
    if re.match(r"^(?:an?|the)\s|^(?:improved|new|novel)\b", title, re.I):
        findings.append(finding("INFO", "TITLE_LEN", where, 'title starts with an article or "improved/new"; '
                                "MPEP 606 prefers a plain technical title."))
    return title


def check_abstract(spec, findings):
    sec = section(spec, "ABSTRACT")
    if not sec:
        return None
    text = body_text(sec).strip()
    where = "spec.md:L%d" % sec["line"]
    n = len(words(text))
    if n == 0:
        findings.append(finding("BLOCK", "ABSTRACT", where, "ABSTRACT section is empty (37 CFR 1.72(b))."))
        return 0
    if n > 150:
        findings.append(finding("BLOCK", "ABSTRACT", where, "abstract is %d words; keep it to 150 words or fewer "
                                "(37 CFR 1.72(b); MPEP 608.01(b))." % n))
    elif n < 50:
        findings.append(finding("WARN", "ABSTRACT", where, "abstract is %d words; 50-150 is the target "
                                "(MPEP 608.01(b))." % n))
    for w in ("said", "means"):
        if re.search(r"\b%s\b" % w, text, re.I):
            findings.append(finding("WARN", "ABSTRACT", where, 'abstract uses the legal phrasing "%s"; avoid it '
                                    "(MPEP 608.01(b))." % w))
    if re.search(r"\b(?:this|the present) (?:disclosure|invention) (?:relates|concerns|is directed)|"
                 r"\bthe (?:present )?invention\b", text, re.I):
        findings.append(finding("WARN", "ABSTRACT", where, 'avoid phrases like "This disclosure relates to" or '
                                '"the invention" in the abstract (MPEP 608.01(b)).'))
    if len(paragraphs(sec)) > 1:
        findings.append(finding("WARN", "ABSTRACT", where, "abstract should be a single paragraph "
                                "(MPEP 608.01(b))."))
    return n


def check_figures(spec, fj, findings, run_list, skipped):
    brief = section(spec, "BRIEF_DRAWINGS")
    dd = section(spec, "DETAILED_DESCRIPTION")
    bt, dt = body_text(brief), body_text(dd)
    brief_figs = [f for f, _ in figs_in(bt)]
    dd_list = figs_in(dt)
    dd_figs = [f for f, _ in dd_list]
    json_ids = figures_json_ids(fj) if fj is not None else None
    bset, dset = set(brief_figs), set(dd_figs)
    for f in sorted(dset - bset, key=fig_sort_key):
        findings.append(finding("BLOCK", "FIG_COVERAGE", f,
                                "%s is cited in the Detailed Description but not listed in the Brief "
                                "Description of the Drawings (37 CFR 1.74)." % f))
    for f in sorted(bset - dset, key=fig_sort_key):
        findings.append(finding("WARN", "FIG_COVERAGE", f,
                                "%s is listed in the Brief Description but never discussed in the Detailed "
                                "Description." % f))
    if json_ids is not None:
        jset = set(json_ids)
        for f in sorted((bset | dset) - jset, key=fig_sort_key):
            findings.append(finding("BLOCK", "FIG_COVERAGE", f,
                                    "%s is cited in the spec but is not in figures.json (no drawing for it)." % f))
        for f in sorted(jset - bset, key=fig_sort_key):
            findings.append(finding("BLOCK", "FIG_COVERAGE", f,
                                    "%s is in figures.json but not in the Brief Description of the Drawings "
                                    "(37 CFR 1.74)." % f))
    else:
        skipped.append({"check": "FIG_COVERAGE (figures.json)", "reason": "no figures.json"})
    run_list.append("FIG_COVERAGE")
    # sequence: first mentions in ascending order, no gaps
    seen = []
    for f, _ in dd_list:
        if f not in seen:
            seen.append(f)
    for i in range(1, len(seen)):
        if fig_sort_key(seen[i]) < fig_sort_key(seen[i - 1]) and \
                fig_sort_key(seen[i]) < max(fig_sort_key(x) for x in seen[:i]):
            findings.append(finding("WARN", "FIG_SEQUENCE", seen[i],
                                    "%s is first discussed after %s; introduce figures in numerical order."
                                    % (seen[i], seen[i - 1])))
            break
    allf = sorted(set(brief_figs) | set(dd_figs) | set(json_ids or []), key=fig_sort_key)
    nums = sorted(set(fig_sort_key(f)[0] for f in allf if fig_sort_key(f)[0] != 9999))
    if nums:
        missing = [k for k in range(1, nums[-1] + 1) if k not in nums]
        if missing:
            findings.append(finding("WARN", "FIG_SEQUENCE", "figures",
                                    "figure numbering has gaps: no FIG. %s (37 CFR 1.84(u)(1): consecutive "
                                    "Arabic numerals)." % ", ".join(str(k) for k in missing)))
    run_list.append("FIG_SEQUENCE")
    return bool(allf)


def check_numerals(spec, text_lines, fj, findings, run_list, skipped):
    by_num = {}
    by_name = {}
    mentioned = {}   # numeral -> first line, including list continuations ("strap 104, 106")
    for s in sp.description_sections(spec):
        for ln, t in s["body"]:
            if re.match(r"^\s{0,3}#{1,6}\s", t):
                continue
            for num, key, disp, _ in numerals_in(t, lambda pos, ln=ln: ln):
                mentioned.setdefault(num, ln)
                if not key:
                    continue
                by_num.setdefault(num, []).append((key, disp, ln))
                by_name.setdefault(key, []).append((num, ln))
    for num, uses in sorted(by_num.items(), key=lambda kv: (len(kv[0]), kv[0])):
        groups = []
        for key, disp, ln in uses:
            for g in groups:
                if names_compatible(g[0][0], key):
                    g.append((key, disp, ln))
                    break
            else:
                groups.append([(key, disp, ln)])
        if len(groups) > 1:
            desc = "; ".join('"%s" (L%d)' % (g[0][1], g[0][2]) for g in groups[:4])
            findings.append(finding("BLOCK", "NUMERALS", "numeral %s" % num,
                                    "reference numeral %s is used for different elements: %s. One numeral must "
                                    "mean one element (37 CFR 1.84(p)(4))." % (num, desc)))
    for key, uses in by_name.items():
        if key and (key[-1] in GENERIC_NAMES or key[0] in GENERIC_NAMES):
            continue
        bases = sorted(set(_base(n) for n, _ in uses))
        if len(bases) > 1:
            findings.append(finding("WARN", "NUMERALS", '"%s"' % " ".join(key),
                                    '"%s" carries more than one numeral (%s); use one numeral per element '
                                    "unless these are different embodiments (37 CFR 1.84(p)(4))."
                                    % (" ".join(key), ", ".join(bases))))
    run_list.append("NUMERALS")
    if fj is None:
        skipped.append({"check": "NUMERALS (figures.json)", "reason": "no figures.json"})
        return sorted(mentioned)
    jn = figures_json_numerals(fj)
    spec_set = set(mentioned)
    for n in sorted(set(jn) - spec_set, key=lambda x: (len(x), x)):
        findings.append(finding("BLOCK", "NUMERALS", "numeral %s" % n,
                                "numeral %s appears in figures.json (%s) but not in the description "
                                "(37 CFR 1.84(p)(5))." % (n, ", ".join(sorted(jn[n])))))
    for n in sorted(spec_set - set(jn), key=lambda x: (len(x), x)):
        disp, ln = (by_num[n][0][1], by_num[n][0][2]) if n in by_num else ("listed with another numeral", mentioned[n])
        findings.append(finding("BLOCK", "NUMERALS", "numeral %s" % n,
                                'numeral %s ("%s", L%d) appears in the description but in no figure '
                                "(37 CFR 1.84(p)(5))." % (n, disp, ln)))
    return sorted(mentioned)


def check_para_numbering(spec, findings):
    nums = []
    for s in spec["sections"]:
        for ln, t in s["body"]:
            m = re.match(r"^\s*\[(\d{4,5})\]", t)
            if m:
                nums.append((int(m.group(1)), ln))
    if not nums:
        findings.append(finding("INFO", "PARA_NUMBERING", "spec.md",
                                "paragraphs are unnumbered; build_docx.py adds [0001]-style numbers "
                                "(37 CFR 1.52(b)(6))."))
        return
    exp = 1
    for n, ln in nums:
        if n != exp:
            findings.append(finding("WARN", "PARA_NUMBERING", "spec.md:L%d" % ln,
                                    "paragraph [%04d] where [%04d] was expected." % (n, exp)))
            exp = n
        exp += 1


def check_risky(spec, findings):
    hits = {}
    for s in spec["sections"]:
        if s["key"] in ("CLAIMS", "TITLE"):
            continue
        for ln, t in s["body"]:
            if re.match(r"^\s{0,3}#{1,6}\s", t):
                continue
            # The skill's own drawings boilerplate ("not necessarily to scale") is not a scope word.
            t = re.sub(r"\bnot\s+necessarily\s+(?:drawn\s+)?to\s+scale\b", "", t, flags=re.I)
            for pat, why in RISKY:
                for m in re.finditer(pat, t, re.I):
                    k = m.group(0).lower()
                    hits.setdefault((pat, why), {}).setdefault(k, []).append(ln)
    for (pat, why), forms in hits.items():
        lines = sorted(set(ln for v in forms.values() for ln in v))
        label = ", ".join('"%s"' % f for f in sorted(forms))
        findings.append(finding("WARN", "RISKY_WORDS", "spec.md:L%d" % lines[0],
                                "%s used %d time(s) (lines %s): %s." % (label, sum(len(v) for v in forms.values()),
                                                                      ", ".join(str(x) for x in lines[:8]), why)))


def check_funding(spec, filing, findings, run_list, skipped):
    gi = _gov_interest(filing)
    sec = section(spec, "FEDERAL_FUNDING")
    if filing is None:
        skipped.append({"check": "FUNDING", "reason": "no filing.json"})
        return
    run_list.append("FUNDING")
    if gi and (not sec or not body_text(sec).strip()):
        findings.append(finding("BLOCK", "FUNDING", "spec.md",
                                "filing.json shows a government interest but the spec has no federally sponsored "
                                "research statement (35 USC 202(c)(6); 37 CFR 401.14(f)(4); 1.77(b)(3))."))
    elif gi is None and sec is None:
        findings.append(finding("INFO", "FUNDING", "filing.json",
                                "filing.json does not say whether there is government funding; confirm with "
                                "the inventors."))
    elif sec is not None and not body_text(sec).strip():
        findings.append(finding("WARN", "FUNDING", "spec.md:L%d" % sec["line"],
                                "federally sponsored research section is empty; delete it or add the statement."))


US_PAT = re.compile(r"U\.\s?S\.\s+Pat(?:ent)?\.?\s+Nos?\.|U\.S\. Patent Nos?\.?|\bUS\s?\d{1,2},?\d{3},?\d{3}\s?B\d?\b|"
                    r"\bUS\d{7,8}\s?[AB]\d?\b|\bU\.S\. Pat\.", re.I)
US_PUB = re.compile(r"Pub(?:lication|l)?\.?\s+No\.?\s*(?:US\s*)?20\d{2}/?\d{7}|\bUS\s?20\d{2}/?\d{7}|"
                    r"Patent Application Publication", re.I)
US_APP = re.compile(r"(?:Application|Appl?\.)\s+(?:Ser(?:ial)?\.?\s+)?No\.?\s*\d{2}/\d{3},?\d{3}|"
                    r"Provisional (?:Patent )?Application", re.I)
FOREIGN = re.compile(r"\b(?:WO|EP|JP|CN|DE|KR|GB|FR)\s?\d")


def check_incorp(spec, findings):
    for s in spec["sections"]:
        for ln, para in paragraphs(s):
            for m in re.finditer(r"incorporat\w*\s+(?:herein\s+|in (?:its|their) entiret(?:y|ies)\s+)?by\s+reference",
                                 para, re.I):
                ctx = para[max(0, m.start() - 400):m.start()]
                if FOREIGN.search(ctx) or re.search(r"https?://|\bet al\.|journal|proceedings|vol\.|pp\.|"
                                                    r"\"[^\"]{8,}\"|standard|specification|manual|datasheet",
                                                    ctx, re.I):
                    lvl = "WARN"
                    why = "non-patent or foreign material"
                elif US_APP.search(ctx) and not (US_PAT.search(ctx) or US_PUB.search(ctx)):
                    lvl = "INFO" if s["key"] == "CROSS_REFERENCE" else "WARN"
                    why = "an application that may be unpublished"
                elif US_PAT.search(ctx) or US_PUB.search(ctx):
                    continue
                else:
                    lvl, why = "WARN", "a document that is not clearly a U.S. patent or published application"
                findings.append(finding(lvl, "INCORP_BY_REF", "spec.md:L%d" % ln,
                                        "incorporation by reference of %s: essential material (needed for "
                                        "112(a), 112(b), or 112(f) structure) may be incorporated only from a "
                                        "U.S. patent or U.S. patent application publication (37 CFR 1.57(d)); "
                                        "put essential text in the spec itself." % why))


def check_claim_support(spec, claims_text, findings):
    dd = section(spec, "DETAILED_DESCRIPTION")
    norm = cc.norm_text_for_match(body_text(dd))
    claims = cc.parse_claims(claims_text)
    missing = {}
    for num, tw in cc.claim_terms(claims):
        if cc.term_in_text(tw, norm):
            continue
        missing.setdefault(" ".join(w.lower() for w in tw), []).append(num)
    for term, nums in missing.items():
        findings.append(finding("WARN", "CLAIM_SUPPORT", "claim %d" % nums[0],
                                '"%s" (claims %s) is not found in the Detailed Description; add support using '
                                "the same words (35 USC 112(a); 37 CFR 1.75(d)(1))."
                                % (term, ", ".join(str(n) for n in sorted(set(nums))[:6]))))
    return sorted(missing)


def check_provisional(spec, findings):
    dd = section(spec, "DETAILED_DESCRIPTION")
    t = body_text(dd)
    n = len(words(t))
    alts = len(ALT_PHRASES.findall(t))
    if n < 1500 or alts == 0:
        why = []
        if n < 1500:
            why.append("Detailed Description is %d words" % n)
        if alts == 0:
            why.append("no alternative-embodiment language (\"in some embodiments\", \"alternatively\")")
        findings.append(finding("WARN", "PROVISIONAL_THIN", "spec.md",
                                "%s. A later nonprovisional gets the provisional date only for claims the "
                                "provisional fully supports (35 USC 119(e)(1); New Railhead Mfg. v. Vermeer, "
                                "298 F.3d 1290 (Fed. Cir. 2002)); describe every embodiment and alternative now."
                                % "; ".join(why)))


# --------------------------------------------------------------------------- run

DEFAULTS = {"spec": None, "claims": None, "figures": None, "filing": None, "type": None, "dir": "patent",
            "json": False, "no_audit": False}


def _load_json(path, label):
    if not path:
        return None
    if not os.path.exists(path):
        raise UsageError("%s not found: %s" % (label, path))
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as e:
        raise UsageError("%s is not valid JSON: %s" % (path, e))


def run(args):
    a = to_namespace(args, DEFAULTS)
    path = a.spec or os.path.join(a.dir, "draft", "spec.md")
    if not os.path.exists(path):
        raise UsageError("spec file not found: %s" % path)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    draft = os.path.join(a.dir, "draft")
    fig_path = a.figures or (os.path.join(draft, "figures.json") if os.path.exists(os.path.join(draft, "figures.json"))
                             else None)
    fil_path = a.filing or (os.path.join(draft, "filing.json") if os.path.exists(os.path.join(draft, "filing.json"))
                            else None)
    fj = _load_json(fig_path, "figures file")
    if fj is not None and isinstance(fj.get("schema"), str) and not fj["schema"].startswith("patentassist/figures@1"):
        raise UsageError("%s: schema %s is not supported (expected patentassist/figures@1)" % (fig_path, fj["schema"]))
    filing = _load_json(fil_path, "filing file")
    spec = parse_spec(text)
    if not spec["sections"]:
        raise UsageError("no '## ' section headings found in %s (see references/state-files.md)" % path)
    findings, run_list, skipped = [], [], []
    ftype, fsrc = _filing_type(a, filing, a.dir)
    if ftype is None:
        findings.append(finding("INFO", "SECTION_ORDER", "spec.md",
                                "filing type unknown (no --type, filing.json, or state.json); checked as a "
                                "nonprovisional."))
    claims_text = None
    if a.claims:
        if not os.path.exists(a.claims):
            raise UsageError("claims file not found: %s" % a.claims)
        with open(a.claims, encoding="utf-8") as fh:
            claims_text = fh.read()
    else:
        cs = section(spec, "CLAIMS")
        if cs and re.search(r"^\s{0,3}1\s*[.)]\s+\S", body_text(cs), re.M):
            claims_text = body_text(cs)
    has_figs_cited = bool(figs_in(text)) or bool(fj and fj.get("figures"))
    check_sections(spec, ftype, has_figs_cited, bool(a.claims), filing, findings)
    run_list.append("SECTION_ORDER")
    title = check_title(spec, findings)
    run_list.append("TITLE_LEN")
    abstract_words = check_abstract(spec, findings)
    if section(spec, "ABSTRACT"):
        run_list.append("ABSTRACT")
    else:
        skipped.append({"check": "ABSTRACT", "reason": "no ABSTRACT section"})
    check_figures(spec, fj, findings, run_list, skipped)
    numerals = check_numerals(spec, text.splitlines(), fj, findings, run_list, skipped)
    check_para_numbering(spec, findings)
    run_list.append("PARA_NUMBERING")
    check_risky(spec, findings)
    run_list.append("RISKY_WORDS")
    check_funding(spec, filing, findings, run_list, skipped)
    check_incorp(spec, findings)
    run_list.append("INCORP_BY_REF")
    unsupported = None
    if claims_text and section(spec, "DETAILED_DESCRIPTION"):
        unsupported = check_claim_support(spec, claims_text, findings)
        run_list.append("CLAIM_SUPPORT")
    else:
        skipped.append({"check": "CLAIM_SUPPORT", "reason": "no --claims and no numbered claims in the spec"
                        if not claims_text else "no DETAILED DESCRIPTION section"})
    if ftype == "provisional":
        check_provisional(spec, findings)
        run_list.append("PROVISIONAL_THIN")
    else:
        skipped.append({"check": "PROVISIONAL_THIN", "reason": "not a provisional"})
    order = {"BLOCK": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: order.get(f["level"], 3))
    blocks = sum(1 for f in findings if f["level"] == "BLOCK")
    warns = sum(1 for f in findings if f["level"] == "WARN")
    dd = section(spec, "DETAILED_DESCRIPTION")
    res = {"ok": blocks == 0, "exit_code": 1 if blocks else 0, "file": path, "findings": findings,
           "checks_run": run_list, "checks_skipped": skipped,
           "summary": {"blocking": blocks, "warnings": warns, "info": sum(1 for f in findings if f["level"] == "INFO"),
                       "filing_type": ftype or "unknown (checked as nonprovisional)", "filing_type_source": fsrc,
                       "title": title, "abstract_words": abstract_words,
                       "detailed_description_words": len(words(body_text(dd))),
                       "sections": [s["heading"] for s in spec["sections"]],
                       "numerals": numerals, "unsupported_claim_terms": unsupported,
                       "figures_json": fig_path, "filing_json": fil_path}}
    audit(a.dir, "check", no_audit=a.no_audit or not os.path.isdir(a.dir), script=SCRIPT, file=path,
          blocking=blocks, warnings=warns)
    return res


def render_text(res):
    out = ["check_spec.py  %s" % res.get("file", "")]
    for f in res["findings"]:
        out.append("%-5s  %s  %s  %s" % (f["level"], f["code"], f["where"], f["message"]))
    out.append("")
    out.append("Checks run: %s" % ", ".join(res["checks_run"]))
    for s in res["checks_skipped"]:
        out.append("Check skipped: %s (%s)" % (s["check"], s["reason"]))
    s = res["summary"]
    out.append("Filing type: %s; abstract %s words; Detailed Description %s words"
               % (s["filing_type"], s.get("abstract_words"), s.get("detailed_description_words")))
    out.append("Summary: %d BLOCK, %d WARN, %d INFO" % (s["blocking"], s["warnings"], s["info"]))
    return "\n".join(out)


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("spec", nargs="?", help="spec.md (default <dir>/draft/spec.md)")
    p.add_argument("--claims", help="claims.md for CLAIM_SUPPORT")
    p.add_argument("--figures", help="figures.json (default <dir>/draft/figures.json if present)")
    p.add_argument("--filing", help="filing.json (default <dir>/draft/filing.json if present)")
    p.add_argument("--type", choices=["provisional", "nonprovisional"], help="override the filing type")
    p.add_argument("--dir", default="patent", help="matter folder (default: patent)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--no-audit", action="store_true", help="do not append to audit.jsonl")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        res = run(args)
    except UsageError as e:
        if args.json:
            print(json.dumps({"ok": False, "exit_code": 2, "error": str(e), "findings": [],
                              "checks_run": [], "checks_skipped": [], "summary": {}}, indent=2))
        else:
            print("ERROR: %s" % e, file=sys.stderr)
        return 2
    print(json.dumps(res, indent=2, ensure_ascii=False) if args.json else render_text(res))
    return res["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
