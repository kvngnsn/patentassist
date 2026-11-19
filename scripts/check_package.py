#!/usr/bin/env python3
"""Whole-package check before export: runs every draft checker and the cross-file checks.

    python3 scripts/check_package.py [--dir patent] [--json] [--no-audit]

Reads <dir>/state.json and <dir>/draft/{claims.md, spec.md, figures.json, filing.json, out/}.

Runs:
  check_claims.py, check_spec.py, check_drawings.py (if present), fees.py (if present)
  STALE        a built output is older than its inputs (state.json depends + sha256)
  MARKERS      leftover notes in filing copies: [review], TODO, TK, {{, [[, UNVERIFIED, [verify], TBD,
               bracketed notes
  CLAIMS_MATCH claims in spec.md match claims.md
  TITLE_MATCH  spec title == filing.json title (37 CFR 1.72(a), 1.76(b)(3))
  INVENTORS    at least one inventor with a legal name; residence and mailing address (35 USC 115; 1.63, 1.76)
  ENTITY       entity status set: large / small / micro (37 CFR 1.27, 1.29)
  FEE_COUNTS   a fee sheet in draft/out uses the current claim counts (nonprovisional only)
  CLAIMED_NOT_SHOWN (WARN) the head noun of each claimed element appears in a figure label or in
               the name of a numbered element in the spec (37 CFR 1.83(a)); lists the features not shown

Worksheets (*-worksheet.md) are typing aids, not uploads, so MARKERS skips them.

Prints the blocker list and "Ready to export: yes / yes, with warnings / no". Ready means no BLOCK
findings and every required check ran.

Exit codes: 0 ready, 1 blocking findings or a required check skipped, 2 usage or input error.
"""

import argparse
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from state import UsageError, audit, finding, to_namespace  # noqa: E402

SCRIPT = "check_package.py"
TEXT_EXT = (".md", ".txt", ".html", ".htm", ".csv", ".xml", ".docx")
HARD_MARKERS = [
    (re.compile(r"\[review\]", re.I), "[review]"),
    (re.compile(r"\bTODO\b"), "TODO"),
    (re.compile(r"\bTK\b"), "TK"),
    (re.compile(r"\bTBD\b"), "TBD"),
    (re.compile(r"\{\{"), "{{"),
    (re.compile(r"\[\["), "[["),
    (re.compile(r"\bUNVERIFIED\b"), "UNVERIFIED"),
    (re.compile(r"\[verify\]", re.I), "[verify]"),
    (re.compile(r"\bXXX\b"), "XXX"),
    (re.compile(r"\[(?:insert|placeholder|note|comment|inventor|attorney|confirm|check|fill)[^\]\n]*\]", re.I),
     "bracketed note"),
]
SOFT_BRACKET = re.compile(r"\[(?!\d{3,5}\])(?![ xX]\])([^\]\n]*[A-Za-z]{3,}[^\]\n]*)\](?!\()")


def _read_text(path):
    if path.lower().endswith(".docx"):
        try:
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode("utf-8", "replace")
        except (zipfile.BadZipFile, KeyError, OSError):
            return None
        xml = re.sub(r"</w:p>", "\n", xml)
        txt = re.sub(r"<[^>]+>", "", xml)
        return (txt.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&apos;", "'"))
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def _load_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as e:
        raise UsageError("%s is not valid JSON: %s" % (path, e))


def _norm_title(t):
    return re.sub(r"\s+", " ", (t or "").strip().rstrip(".")).casefold()


def _prefix(findings, label):
    out = []
    for f in findings or []:
        g = dict(f)
        w = f.get("where") or ""
        g["where"] = w if w.startswith(label) else ("%s %s" % (label, w)).strip()
        g["source"] = label
        out.append(g)
    return out


def _filing_type(filing, st):
    for k in ("filing_type", "type", "application_type"):
        v = (filing or {}).get(k)
        if isinstance(v, str) and v:
            return "provisional" if v.lower() == "provisional" else "nonprovisional"
    v = (((st or {}).get("phases") or {}).get("draft") or {}).get("filing_type")
    if v:
        return "provisional" if v == "provisional" else "nonprovisional"
    return None


def _inventor_name(inv):
    if not isinstance(inv, dict):
        return inv if isinstance(inv, str) else None
    for k in ("legal_name", "name", "full_name"):
        if inv.get(k):
            return inv[k]
    # patentassist/filing@1 (references/state-files.md, fill_forms.py) uses given / middle / family;
    # the *_name spellings are kept for older files.
    parts = [inv.get(k) for k in ("given", "given_name", "first_name", "middle", "middle_name",
                                  "family", "family_name", "last_name") if inv.get(k)]
    return " ".join(parts) if parts else None


def _counts_from_sheet(path):
    """(independent, total, source) from a fee sheet file in draft/out, or (None, None, why)."""
    if path.endswith(".json"):
        try:
            with open(path, encoding="utf-8") as fh:
                obj = json.load(fh)
        except (OSError, ValueError):
            return None, None, "not valid JSON"
        found = {}

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    lk = k.lower()
                    if isinstance(v, int) and not isinstance(v, bool):
                        if lk in ("independent", "independent_claims", "claims_independent"):
                            found.setdefault("i", v)
                        elif lk in ("total_for_fees", "total_claims", "claims_total", "total_claims_for_fees"):
                            found.setdefault("t", v)
                    walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(obj)
        if "i" in found or "t" in found:
            return found.get("i"), found.get("t"), "json keys"
        return None, None, "no claim-count keys found"
    text = _read_text(path) or ""
    mi = re.search(r"(\d+)\s+independent|independent claims?\s*[:=]\s*(\d+)", text, re.I)
    mt = re.search(r"(\d+)\s+total for fees|total claims?(?: for fees)?\s*[:=]\s*(\d+)", text, re.I)
    gi = int(next(g for g in mi.groups() if g)) if mi else None
    gt = int(next(g for g in mt.groups() if g)) if mt else None
    if gi is None and gt is None:
        return None, None, "no claim counts found in text"
    return gi, gt, "text"


def _compute_stale(d, st):
    try:
        import state as _state
        if hasattr(_state, "compute_stale"):
            return _state.compute_stale(d, st), "state.compute_stale"
    except Exception:  # pragma: no cover - fall back below
        pass
    # fallback: compare recorded input hashes with current ones
    import hashlib
    out = []
    arts = st.get("artifacts") or {}
    for down, ins in (st.get("depends") or {}).items():
        if not os.path.exists(os.path.join(d, down)):
            continue
        snap = (arts.get(down) or {}).get("inputs") or {}
        changed = []
        for inp in ins:
            p = os.path.join(d, inp)
            if os.path.isfile(p):
                h = hashlib.sha256(open(p, "rb").read()).hexdigest()
                if snap.get(inp) and snap[inp] != h:
                    changed.append(inp)
        if changed:
            out.append({"downstream": down, "changed_inputs": changed, "reason": "input hash changed"})
    return out, "fallback"


# heads of claim terms that name a quantity, a time, or a category rather than a part to draw
NOT_DRAWN = set("""threshold time period value level number amount method process step response event condition
 information instruction percent hz khz mhz ghz db plurality way manner result basis state mode rate duration
 ratio difference range maximum minimum average sum total count set group use operation device system apparatus
 medium claim user session part portion kind type degree extent order presence absence fraction
 boil-over""".split())
FIG_LABEL_KEYS = ("label", "title_text", "x_label", "y_label")


def _figure_words(figs):
    """Lower-case, singular words of every label drawn in figures.json (boxes, steps, edges, regions...)."""
    import check_claims
    texts = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("label", "x_label", "y_label") and isinstance(v, str):
                    texts.append(v)
                elif k == "device" and isinstance(v, str):
                    texts.append(v)
                elif isinstance(v, (dict, list)) and k != "schema":
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk((figs or {}).get("figures") or [])
    return check_claims.norm_text_for_match(" . ".join(texts))


def claimed_not_shown(claims_text, figs, spec_text):
    """[(claim number, [terms])] for claimed elements whose words appear in no figure label and in no
    numbered element name of the spec (37 CFR 1.83(a)). A cheap head-noun check: it catches the usual
    case (a claimed part never drawn), not a part drawn under another name."""
    import check_claims
    import _specparse
    fig_text = _figure_words(figs)
    fig_nums = set()

    def nums(o):
        if isinstance(o, dict):
            if o.get("numeral") not in (None, ""):
                fig_nums.add(str(o["numeral"]).strip())
            for v in o.values():
                nums(v)
        elif isinstance(o, list):
            for x in o:
                nums(x)
    nums((figs or {}).get("figures") or [])
    names = []
    if spec_text:
        parsed = _specparse.parse_spec(spec_text)
        for num, _key, disp, _ln in _specparse.numerals_in(_specparse.description_text(parsed)):
            if disp and num in fig_nums:
                names.append(disp)
    name_text = check_claims.norm_text_for_match(" . ".join(names))
    claims = check_claims.parse_claims(claims_text)
    out, seen = [], set()
    for num, words in check_claims.claim_terms(claims):
        ws = [w for w in words if re.match(r"[A-Za-z]", w)]
        if not ws:
            continue
        term = " ".join(w.lower() for w in ws)
        head = check_claims.lemma(ws[-1].lower())
        if term in seen:
            continue
        if check_claims.term_in_text(ws, fig_text) or check_claims.term_in_text(ws, name_text) or \
                (" %s " % head) in fig_text or (" %s " % head) in name_text:
            continue
        if head in NOT_DRAWN or head.split("-")[-1] in NOT_DRAWN or len(head) < 3:
            continue
        seen.add(term)
        if out and out[-1][0] == num:
            out[-1][1].append(term)
        else:
            out.append((num, [term]))
    return out


DEFAULTS = {"dir": "patent", "json": False, "no_audit": False}


def run(args):
    a = to_namespace(args, DEFAULTS)
    d = a.dir
    if not os.path.isdir(d):
        raise UsageError("matter folder not found: %s" % d)
    draft = os.path.join(d, "draft")
    paths = {k: os.path.join(draft, v) for k, v in (("claims", "claims.md"), ("spec", "spec.md"),
                                                    ("figures", "figures.json"), ("filing", "filing.json"))}
    out_dir = os.path.join(draft, "out")
    st = _load_json(os.path.join(d, "state.json"))
    filing = _load_json(paths["filing"])
    ftype = _filing_type(filing, st)
    nonprov = ftype != "provisional"
    findings, run_list, skipped, required_missing = [], [], [], []
    sub = {}
    counts = None
    entity = None
    if isinstance(filing, dict):
        entity = filing.get("entity_status") or filing.get("entity")
        if isinstance(entity, dict):
            entity = entity.get("status")

    # ---- check_claims
    if os.path.exists(paths["claims"]):
        try:
            import check_claims
            r = check_claims.run({"claims": paths["claims"], "spec": paths["spec"] if os.path.exists(paths["spec"])
                                  else None, "entity": entity if entity in ("large", "small", "micro") else None,
                                  "dir": d, "no_audit": True})
            findings += _prefix(r["findings"], "claims.md")
            counts = r["summary"]["counts"]
            sub["check_claims"] = {"blocking": r["summary"]["blocking"], "warnings": r["summary"]["warnings"],
                                   "checks_skipped": r["checks_skipped"]}
            run_list.append("check_claims")
        except Exception as e:
            skipped.append({"check": "check_claims", "reason": "%s: %s" % (e.__class__.__name__, e)})
            required_missing.append("check_claims")
    else:
        if nonprov:
            findings.append(finding("BLOCK", "MISSING", "draft/claims.md",
                                    "no claims.md; a nonprovisional needs claims (35 USC 112(b); 37 CFR 1.75)."))
        skipped.append({"check": "check_claims", "reason": "no draft/claims.md"})

    # ---- check_spec
    if os.path.exists(paths["spec"]):
        try:
            import check_spec
            r = check_spec.run({"spec": paths["spec"],
                                "claims": paths["claims"] if os.path.exists(paths["claims"]) else None,
                                "figures": paths["figures"] if os.path.exists(paths["figures"]) else None,
                                "filing": paths["filing"] if os.path.exists(paths["filing"]) else None,
                                "type": ftype, "dir": d, "no_audit": True})
            findings += _prefix(r["findings"], "spec.md")
            sub["check_spec"] = {"blocking": r["summary"]["blocking"], "warnings": r["summary"]["warnings"],
                                 "checks_skipped": r["checks_skipped"]}
            spec_title = r["summary"].get("title")
            run_list.append("check_spec")
        except Exception as e:
            spec_title = None
            skipped.append({"check": "check_spec", "reason": "%s: %s" % (e.__class__.__name__, e)})
            required_missing.append("check_spec")
    else:
        spec_title = None
        findings.append(finding("BLOCK", "MISSING", "draft/spec.md", "no spec.md (35 USC 112(a))."))
        skipped.append({"check": "check_spec", "reason": "no draft/spec.md"})
        required_missing.append("check_spec")

    # ---- check_drawings (optional script, required when figures exist)
    if os.path.exists(paths["figures"]):
        if os.path.exists(os.path.join(HERE, "check_drawings.py")) and os.path.exists(paths["spec"]):
            try:
                import check_drawings
                args_d = {"figures": paths["figures"], "spec": paths["spec"], "dir": d, "no_audit": True}
                man = os.path.join(out_dir, "drawings-manifest.json")
                pdf = os.path.join(out_dir, "drawings.pdf")
                if os.path.exists(man):
                    args_d["manifest"] = man
                if os.path.exists(pdf):
                    args_d["pdf"] = pdf
                r = check_drawings.run(args_d)
                findings += _prefix(r.get("findings"), "drawings")
                sub["check_drawings"] = {"blocking": (r.get("summary") or {}).get("blocking"),
                                         "warnings": (r.get("summary") or {}).get("warnings"),
                                         "checks_skipped": r.get("checks_skipped", [])}
                run_list.append("check_drawings")
            except Exception as e:
                skipped.append({"check": "check_drawings", "reason": "%s: %s" % (e.__class__.__name__, e)})
                required_missing.append("check_drawings")
        else:
            skipped.append({"check": "check_drawings", "reason": "scripts/check_drawings.py not found"
                            if not os.path.exists(os.path.join(HERE, "check_drawings.py")) else "no spec.md"})
            required_missing.append("check_drawings")
    else:
        skipped.append({"check": "check_drawings", "reason": "no draft/figures.json"})

    # ---- fees (optional, informational)
    if os.path.exists(os.path.join(HERE, "fees.py")) and entity in ("large", "small", "micro") and ftype:
        try:
            import fees
            fa = {"command": "estimate", "type": ftype, "entity": entity, "dir": d, "no_audit": True}
            if os.path.exists(paths["claims"]) and nonprov:
                fa["claims"] = paths["claims"]
            r = fees.run(fa)
            est = r.get("estimate") or {}
            sub["fees"] = {"total": est.get("total"), "entity": entity, "type": ftype,
                           "last_verified": r.get("last_verified")}
            findings.append(finding("INFO", "FEES", "fees.py", "fee estimate %s entity, %s: $%s (fees.md "
                                    "last_verified %s); verify on uspto.gov before paying."
                                    % (entity, ftype, est.get("total"), r.get("last_verified"))))
            run_list.append("fees")
        except Exception as e:
            skipped.append({"check": "fees", "reason": "%s: %s" % (e.__class__.__name__, e)})
    else:
        skipped.append({"check": "fees", "reason": "scripts/fees.py not found" if not os.path.exists(
            os.path.join(HERE, "fees.py")) else "entity status or filing type unknown"})

    # ---- stale
    if st is not None:
        items, how = _compute_stale(d, st)
        for it in items:
            findings.append(finding("BLOCK", "STALE", it["downstream"],
                                    "built from older inputs (%s changed); rebuild it, then run `state.py hash %s`. "
                                    "(%s)" % (", ".join(it["changed_inputs"]), it["downstream"], it.get("reason"))))
        run_list.append("STALE")
    else:
        skipped.append({"check": "STALE", "reason": "no state.json"})
        required_missing.append("STALE")

    # ---- markers in filing copies
    targets = [p for p in (paths["spec"], paths["claims"]) if os.path.exists(p)]
    if os.path.isdir(out_dir):
        for root, _dirs, files in os.walk(out_dir):
            for name in sorted(files):
                if name.lower().endswith(TEXT_EXT):
                    targets.append(os.path.join(root, name))
                elif name.lower().endswith(".pdf"):
                    skipped.append({"check": "MARKERS %s" % os.path.relpath(os.path.join(root, name), d),
                                    "reason": "PDF text not scanned"})
    for p in targets:
        rel = os.path.relpath(p, d)
        if os.path.basename(p).lower().endswith("-worksheet.md"):
            skipped.append({"check": "MARKERS %s" % rel,
                            "reason": "worksheet: a typing aid for a USPTO form, not an upload"})
            continue
        txt = _read_text(p)
        if txt is None:
            skipped.append({"check": "MARKERS %s" % rel, "reason": "could not read"})
            continue
        lines = txt.splitlines()
        hard = {}
        soft = {}
        for ln, line in enumerate(lines, 1):
            for rx, label in HARD_MARKERS:
                if rx.search(line):
                    hard.setdefault(label, []).append(ln)
            for m in SOFT_BRACKET.finditer(line):
                if any(rx.search(m.group(0)) for rx, _ in HARD_MARKERS):
                    continue
                if re.fullmatch(r"\[\d{4,5}\]", m.group(0)):
                    continue
                soft.setdefault(m.group(0)[:40], []).append(ln)
        for label, lns in hard.items():
            findings.append(finding("BLOCK", "MARKERS", "%s:L%d" % (rel, lns[0]),
                                    'leftover marker "%s" (%d line(s): %s); remove it before export.'
                                    % (label, len(lns), ", ".join(str(x) for x in lns[:6]))))
        for label, lns in list(soft.items())[:10]:
            findings.append(finding("WARN", "MARKERS", "%s:L%d" % (rel, lns[0]),
                                    'bracketed text "%s" may be a drafting note; remove it if so.' % label))
    run_list.append("MARKERS")

    # ---- claims in spec vs claims.md
    if os.path.exists(paths["spec"]) and os.path.exists(paths["claims"]):
        import check_claims
        import check_spec
        spec_parsed = check_spec.parse_spec(_read_text(paths["spec"]) or "")
        cs = check_spec.section(spec_parsed, "CLAIMS")
        body = check_spec.body_text(cs) if cs else ""
        if cs and re.search(r"^\s{0,3}1\s*[.)]\s+\S", body, re.M):
            a_cl = {c["num"]: re.sub(r"\s+", " ", c["text"]).strip() for c in check_claims.parse_claims(body)}
            b_cl = {c["num"]: re.sub(r"\s+", " ", c["text"]).strip()
                    for c in check_claims.parse_claims(_read_text(paths["claims"]) or "")}
            diff = sorted(n for n in set(a_cl) | set(b_cl) if a_cl.get(n) != b_cl.get(n))
            if diff:
                findings.append(finding("BLOCK", "CLAIMS_MATCH", "spec.md CLAIMS",
                                        "claims in spec.md differ from claims.md (claims %s); keep one source "
                                        "(point the spec's CLAIMS section at claims.md)."
                                        % ", ".join(str(n) for n in diff[:10])))
            run_list.append("CLAIMS_MATCH")
        elif cs:
            skipped.append({"check": "CLAIMS_MATCH", "reason": "spec.md CLAIMS section has no numbered claims "
                                                             "(it points to claims.md)"})
        else:
            skipped.append({"check": "CLAIMS_MATCH", "reason": "spec.md has no CLAIMS section; claims.md is the "
                                                             "only claim set"})
    else:
        skipped.append({"check": "CLAIMS_MATCH", "reason": "spec.md or claims.md missing"})

    # ---- filing.json checks
    if filing is None:
        findings.append(finding("BLOCK", "MISSING", "draft/filing.json",
                                "no filing.json; ADS / cover-sheet data (inventors, entity status, title) is needed "
                                "(37 CFR 1.51(c), 1.76)."))
        required_missing += ["TITLE_MATCH", "INVENTORS", "ENTITY"]
        skipped += [{"check": c, "reason": "no filing.json"} for c in ("TITLE_MATCH", "INVENTORS", "ENTITY")]
    else:
        ft = filing.get("title")
        if spec_title and ft:
            if _norm_title(spec_title) != _norm_title(ft):
                findings.append(finding("BLOCK", "TITLE_MATCH", "filing.json title",
                                        'spec title "%s" differs from filing.json title "%s"; they must match '
                                        "(37 CFR 1.72(a), 1.76(b)(3))." % (spec_title, ft)))
        elif not ft:
            findings.append(finding("BLOCK", "TITLE_MATCH", "filing.json title",
                                    "filing.json has no title (ADS / cover sheet, 37 CFR 1.76(b)(3))."))
        run_list.append("TITLE_MATCH")
        invs = filing.get("inventors")
        if not isinstance(invs, list) or not invs:
            findings.append(finding("BLOCK", "INVENTORS", "filing.json inventors",
                                    "no inventors listed; every inventor must be named (35 USC 115; 37 CFR 1.41, "
                                    "1.63, 1.76(b)(1))."))
        else:
            for i, inv in enumerate(invs, 1):
                nm = _inventor_name(inv)
                if not nm:
                    findings.append(finding("BLOCK", "INVENTORS", "filing.json inventor %d" % i,
                                            "inventor %d has no legal name (37 CFR 1.63(a)(1))." % i))
                    continue
                if isinstance(inv, dict):
                    if not (inv.get("residence") or inv.get("city")):
                        findings.append(finding("WARN", "INVENTORS", "filing.json inventor %d" % i,
                                                "%s: residence (city, state/country) missing (37 CFR 1.63(b), "
                                                "1.76(b)(1))." % nm))
                    if not (inv.get("mailing") or inv.get("mailing_address") or inv.get("address")):
                        findings.append(finding("WARN", "INVENTORS", "filing.json inventor %d" % i,
                                                "%s: mailing address missing (37 CFR 1.63(b), 1.76(b)(1))." % nm))
        run_list.append("INVENTORS")
        if entity not in ("large", "small", "micro"):
            findings.append(finding("BLOCK", "ENTITY", "filing.json entity_status",
                                    "entity status not set (large / small / micro); it sets every fee (37 CFR 1.27, "
                                    "1.29)."))
        elif entity == "micro":
            findings.append(finding("INFO", "ENTITY", "filing.json entity_status",
                                    "micro entity needs a certification (PTO/SB/15A or 15B) filed with the first fee "
                                    "(37 CFR 1.29)."))
        run_list.append("ENTITY")

    # ---- fee sheet counts
    sheets = []
    if os.path.isdir(out_dir):
        for name in sorted(os.listdir(out_dir)):
            if re.match(r"fee", name, re.I) and name.lower().endswith((".json", ".md", ".txt", ".docx")):
                sheets.append(os.path.join(out_dir, name))
    if ftype == "provisional":
        skipped.append({"check": "FEE_COUNTS", "reason": "provisional: no claim fees (37 CFR 1.16(d))"})
    elif sheets and counts:
        for p in sheets:
            gi, gt, how = _counts_from_sheet(p)
            rel = os.path.relpath(p, d)
            if gi is None and gt is None:
                findings.append(finding("WARN", "FEE_COUNTS", rel, "could not read claim counts (%s)." % how))
                continue
            bad = []
            if gi is not None and gi != counts["independent"]:
                bad.append("independent %d vs current %d" % (gi, counts["independent"]))
            if gt is not None and gt != counts["total_for_fees"]:
                bad.append("total %d vs current %d" % (gt, counts["total_for_fees"]))
            if bad:
                findings.append(finding("BLOCK", "FEE_COUNTS", rel,
                                        "fee sheet claim counts are out of date (%s); rerun fees.py." % "; ".join(bad)))
        run_list.append("FEE_COUNTS")
    else:
        skipped.append({"check": "FEE_COUNTS", "reason": "no fee sheet in draft/out" if not sheets else
                        "no claim counts"})

    # ---- claimed features shown in the drawings (37 CFR 1.83(a))
    if os.path.exists(paths["claims"]) and os.path.exists(paths["figures"]):
        try:
            figs = _load_json(paths["figures"]) or {}
            missing = claimed_not_shown(_read_text(paths["claims"]) or "", figs,
                                        _read_text(paths["spec"]) or "" if os.path.exists(paths["spec"]) else "")
            for num, terms in missing:
                findings.append(finding("WARN", "CLAIMED_NOT_SHOWN", "claims.md claim %d" % num,
                                        "claimed feature(s) with no figure label or numbered element: %s. Every "
                                        "claimed feature must be shown in a drawing (37 CFR 1.83(a)); add a view or "
                                        "a labeled element, or confirm it is shown under another name."
                                        % ", ".join('"%s"' % t for t in terms)))
            run_list.append("CLAIMED_NOT_SHOWN")
        except Exception as e:  # heuristic check: never fatal
            skipped.append({"check": "CLAIMED_NOT_SHOWN", "reason": "%s: %s" % (e.__class__.__name__, e)})
    else:
        skipped.append({"check": "CLAIMED_NOT_SHOWN", "reason": "no claims.md or no figures.json"})

    # A format pass cannot substitute for an assessment of the current scope.
    try:
        import review
        assessment = review.check(d, "draft")
        run_list.append("ASSESSMENT")
        if assessment["outcome"] != "likely_patentable":
            findings.append(finding("WARN", "ASSESSMENT_RISK", "reviews/",
                                    "Current assessment: %s. Export is a draft, not a favorable legal opinion. %s"
                                    % (assessment["outcome"], assessment.get("proceed_basis", ""))))
    except (UsageError, OSError, ValueError, TypeError) as e:
        run_list.append("ASSESSMENT")
        findings.append(finding("BLOCK", "ASSESSMENT", "reviews/", str(e)))

    order = {"BLOCK": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: order.get(f["level"], 3))
    blocks = [f for f in findings if f["level"] == "BLOCK"]
    warns = [f for f in findings if f["level"] == "WARN"]
    reasons = []
    if blocks:
        reasons.append("%d blocking finding(s)" % len(blocks))
    if required_missing:
        reasons.append("required check(s) did not run: %s" % ", ".join(sorted(set(required_missing))))
    ready = not reasons
    res = {"ok": ready, "exit_code": 0 if ready else 1, "dir": d, "findings": findings, "checks_run": run_list,
           "checks_skipped": skipped,
           "summary": {"blocking": len(blocks), "warnings": len(warns),
                       "info": sum(1 for f in findings if f["level"] == "INFO"),
                       "ready_to_export": ready, "not_ready_reasons": reasons, "filing_type": ftype or "unknown",
                       "ready_label": ("yes, with warnings" if warns else "yes") if ready else "no",
                       "entity": entity, "counts": counts, "subchecks": sub}}
    audit(d, "check", no_audit=a.no_audit, script=SCRIPT, blocking=len(blocks), warnings=len(warns), ready=ready)
    return res


def render_text(res):
    out = ["check_package.py  %s  (filing type: %s)" % (res["dir"], res["summary"]["filing_type"])]
    blocks = [f for f in res["findings"] if f["level"] == "BLOCK"]
    others = [f for f in res["findings"] if f["level"] != "BLOCK"]
    out.append("")
    out.append("Blockers (%d):" % len(blocks))
    for f in blocks:
        out.append("%-5s  %s  %s  %s" % (f["level"], f["code"], f["where"], f["message"]))
    if not blocks:
        out.append("  none")
    out.append("")
    out.append("Warnings and notes (%d):" % len(others))
    for f in others:
        out.append("%-5s  %s  %s  %s" % (f["level"], f["code"], f["where"], f["message"]))
    out.append("")
    out.append("Checks run: %s" % ", ".join(res["checks_run"]))
    for s in res["checks_skipped"]:
        out.append("Check skipped: %s (%s)" % (s["check"], s["reason"]))
    s = res["summary"]
    out.append("")
    if s["ready_to_export"]:
        out.append("Ready to export: %s" % ("yes, with warnings (%d): review them before filing" % s["warnings"]
                                            if s["warnings"] else "yes"))
    else:
        out.append("Ready to export: no (%s)" % "; ".join(s["not_ready_reasons"]))
    return "\n".join(out)


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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
            print(json.dumps({"ok": False, "exit_code": 2, "error": str(e), "findings": [], "checks_run": [],
                              "checks_skipped": [], "summary": {}}, indent=2))
        else:
            print("ERROR: %s" % e, file=sys.stderr)
        return 2
    print(json.dumps(res, indent=2, ensure_ascii=False) if args.json else render_text(res))
    return res["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
