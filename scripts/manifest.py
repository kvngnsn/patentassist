#!/usr/bin/env python3
"""Filing package manifest: every file in draft/out with its sha256, size, and Patent Center upload
document description, marked required / conditional / optional by filing type.

    python3 scripts/manifest.py [--dir patent] [--type provisional|nonprovisional] [--json] [--no-audit]

Writes <dir>/draft/out/manifest.md and manifest.json (patentassist/manifest@1) and logs one `export`
line per written file to <dir>/audit.jsonl. The document descriptions come from the
```json manifest-descriptions block in references/forms-and-filing.md, section 4 (one source; confirm
each description in Patent Center's upload screen before submitting).

Files are recognized by name (case-insensitive):
  spec.docx (spec + claims + abstract in one DOCX), specification.docx, claims.docx, abstract.docx,
  drawings.pdf, sb16*.pdf (cover sheet), aia14*.pdf / ads*.pdf, aia01*.pdf / declaration*.pdf,
  sb15a*.pdf, sb15b*.pdf, aia82*.pdf / poa*.pdf, sb08*.pdf / ids*.pdf, sb06*.pdf, aia15*.pdf.
Everything else (worksheets, fees.md, ids.json, SVGs, the drawings manifest) is a working file: listed
with its hash, marked "not uploaded".

Findings: BLOCK when the specification (or, for a nonprovisional, the claims or abstract) is missing, or
an IDS is in a provisional; WARN for a missing cover sheet / ADS, declaration, micro entity certification,
or drawings PDF when figures.json exists.

Exit codes: 0 no blocking findings, 1 blocking findings, 2 usage or input error.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from state import UsageError, audit, finding, to_namespace  # noqa: E402

SCRIPT = "manifest.py"
SCHEMA = "patentassist/manifest@1"
FORMS_MD = os.path.join(os.path.dirname(HERE), "references", "forms-and-filing.md")

# (document key, filename pattern) - first match wins
PATTERNS = [
    ("spec_combined", r"^spec\.docx$"),
    ("spec", r"^spec(ification)?\b.*\.(docx|pdf)$"),
    ("claims", r"^claims?\b.*\.(docx|pdf)$"),
    ("abstract", r"^abstract\b.*\.(docx|pdf)$"),
    ("drawings", r"^(drawings?|drw)\b.*\.pdf$"),
    ("cover_sheet", r"^sb0?0?16\b.*\.pdf$|^cover[-_ ]?sheet.*\.pdf$"),
    ("ads", r"^(aia0?0?14|ads)\b.*\.pdf$"),
    ("declaration", r"^(aia0?0?01|declaration)\b.*\.pdf$"),
    ("micro_gross_income", r"^sb0?0?15a\b.*\.pdf$"),
    ("micro_education", r"^sb0?0?15b\b.*\.pdf$"),
    ("power_of_attorney", r"^(aia0?0?82|poa|power[-_ ]of[-_ ]attorney)\b.*\.pdf$"),
    ("ids", r"^(sb0?0?08|ids)\b.*\.pdf$"),
    ("fee_worksheet", r"^(sb0?0?06|fee[-_ ]worksheet)\b.*\.pdf$"),
    ("transmittal", r"^(aia0?0?15|transmittal)\b.*\.pdf$"),
]
OWN_FILES = ("manifest.md", "manifest.json")


def load_descriptions(path=FORMS_MD):
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        raise UsageError("cannot read %s: %s" % (path, e))
    m = re.search(r"```json manifest-descriptions\n(.*?)```", text, re.S)
    if not m:
        raise UsageError("%s has no ```json manifest-descriptions block (section 4)" % path)
    try:
        obj = json.loads(m.group(1))
    except ValueError as e:
        raise UsageError("manifest-descriptions block is not valid JSON: %s" % e)
    return obj


def classify(name):
    low = name.lower()
    for key, pat in PATTERNS:
        if re.search(pat, low):
            return key
    return None


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _filing(d):
    for p in (os.path.join(d, "draft", "filing.json"),):
        try:
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            pass
    return {}


def _filing_type(a, filing, d):
    if a.type:
        return a.type
    v = (filing or {}).get("filing_type")
    if isinstance(v, str) and v:
        return "provisional" if v.lower() == "provisional" else "nonprovisional"
    try:
        with open(os.path.join(d, "state.json"), encoding="utf-8") as fh:
            v = ((json.load(fh).get("phases") or {}).get("draft") or {}).get("filing_type")
        if v:
            return "provisional" if v == "provisional" else "nonprovisional"
    except (OSError, ValueError):
        pass
    return None


DEFAULTS = {"dir": "patent", "type": None, "json": False, "no_audit": False, "forms_md": None}


def run(args):
    a = to_namespace(args, DEFAULTS)
    d = a.dir
    out = os.path.join(d, "draft", "out")
    if not os.path.isdir(out):
        raise UsageError("no %s folder: build the package first (build_docx.py, drawings.py, fill_forms.py)" % out)
    filing = _filing(d)
    ftype = _filing_type(a, filing, d)
    if ftype not in ("provisional", "nonprovisional"):
        raise UsageError("filing type unknown: pass --type provisional|nonprovisional or set filing.json filing_type")
    desc = load_descriptions(a.forms_md or FORMS_MD)
    docs = desc["documents"]
    files, findings = [], []
    present = {}
    for root, dirs, names in os.walk(out):
        dirs.sort()
        for name in sorted(names):
            if name in OWN_FILES or name.startswith("."):
                continue
            p = os.path.join(root, name)
            rel = os.path.relpath(p, out)
            key = classify(name) if root == out else None
            row = {"file": rel, "sha256": _sha256(p), "size": os.path.getsize(p), "document": key}
            if key:
                description, code, requirement, note = docs[key][ftype]
                row.update({"upload": requirement not in ("not_allowed", "n/a"), "description": description,
                            "doc_code": code, "requirement": requirement, "note": note})
                present.setdefault(key, []).append(rel)
            else:
                row.update({"upload": False, "description": None, "doc_code": None, "requirement": "not uploaded",
                            "note": "working file"})
            files.append(row)

    def has(*keys):
        return any(k in present for k in keys)
    if not has("spec_combined", "spec"):
        findings.append(finding("BLOCK", "MISSING", "draft/out", "no specification (spec.docx or specification.docx); "
                                "build it with build_docx.py (35 USC 111, 112(a))."))
    if ftype == "nonprovisional" and not has("spec_combined"):
        for k, label in (("claims", "claims"), ("abstract", "abstract")):
            if not has(k):
                findings.append(finding("BLOCK", "MISSING", "draft/out", "no %s file; a split DOCX upload needs "
                                        "%s.docx (37 CFR 1.75, 1.72(b))." % (label, label)))
    if ftype == "provisional":
        if has("ids"):
            findings.append(finding("BLOCK", "NOT_ALLOWED", ", ".join(present["ids"]),
                                    "no IDS may be filed in a provisional (37 CFR 1.51(d)); remove it from the package."))
        if not has("cover_sheet", "ads"):
            findings.append(finding("WARN", "MISSING", "cover sheet",
                                    "no SB/16 or ADS PDF: fill the SB/16 (fill_forms.py fill SB16 --pdf sb0016.pdf) or "
                                    "complete Patent Center's Web ADS; one is required (37 CFR 1.51(c)(1))."))
    else:
        if not has("declaration"):
            findings.append(finding("WARN", "MISSING", "declaration",
                                    "no inventor declaration (AIA/01); it may be postponed if the ADS names every "
                                    "inventor (37 CFR 1.53(f)(3)), with the 1.16(f) surcharge."))
        if not has("ads"):
            findings.append(finding("INFO", "MISSING", "ADS", "no ADS PDF; use the Patent Center Web ADS (no upload) or "
                                    "fill AIA/14."))
    ent = (filing or {}).get("entity_status")
    if ent == "micro" and not has("micro_gross_income", "micro_education"):
        findings.append(finding("WARN", "MISSING", "micro entity certification",
                                "entity_status is micro but no SB/15A or SB/15B PDF; file it with the first micro fee "
                                "(37 CFR 1.29)."))
    if os.path.exists(os.path.join(d, "draft", "figures.json")) and not has("drawings"):
        findings.append(finding("WARN", "MISSING", "drawings", "figures.json exists but there is no drawings.pdf "
                                "(drawings.py build)."))
    generated = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    obj = {"schema": SCHEMA, "generated": generated, "filing_type": ftype,
           "title": (filing or {}).get("title"), "attorney_docket": (filing or {}).get("attorney_docket"),
           "descriptions_last_verified": desc.get("last_verified"),
           "descriptions_source": "references/forms-and-filing.md section 4", "files": files,
           "findings": findings}
    jp = os.path.join(out, "manifest.json")
    with open(jp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    mp = os.path.join(out, "manifest.md")
    with open(mp, "w", encoding="utf-8") as fh:
        fh.write(render_md(obj))
    for p in (mp, jp):
        audit(d, "export", no_audit=a.no_audit, script=SCRIPT, path=os.path.relpath(p, d), sha256=_sha256(p),
              files=len(files))
    blocks = sum(1 for f in findings if f["level"] == "BLOCK")
    warns = sum(1 for f in findings if f["level"] == "WARN")
    return {"ok": blocks == 0, "exit_code": 1 if blocks else 0, "findings": findings,
            "checks_run": ["MANIFEST"], "checks_skipped": [], "written": [mp, jp], "manifest": obj,
            "summary": {"blocking": blocks, "warnings": warns, "files": len(files),
                        "uploads": sum(1 for f in files if f["upload"]), "filing_type": ftype}}


def _md(s):
    return str(s if s is not None else "").replace("|", "\\|")


def render_md(obj):
    lines = ["# Filing package manifest%s (%s)" % ((": " + obj["attorney_docket"]) if obj.get("attorney_docket") else "",
                                                  obj["filing_type"]), "",
             "Generated %s by `manifest.py`. Document descriptions from references/forms-and-filing.md section 4 "
             "(last verified %s); confirm each one in Patent Center's upload screen (\"Help with document "
             "description\") before submitting." % (obj["generated"][:10], obj.get("descriptions_last_verified")), "",
             "## Upload", "",
             "| File | Patent Center document description | Doc code | Requirement | sha256 | Size |",
             "|---|---|---|---|---|---|"]
    ups = [f for f in obj["files"] if f["upload"]]
    for f in ups:
        req = f["requirement"] + ((": " + f["note"]) if f.get("note") else "")
        lines.append("| %s | %s | %s | %s | `%s` | %d |" % (_md(f["file"]), _md(f["description"]), _md(f["doc_code"]),
                                                          _md(req), f["sha256"], f["size"]))
    if not ups:
        lines.append("| (none) | | | | | |")
    lines += ["", "## Not uploaded", "", "| File | Why | sha256 |", "|---|---|---|"]
    for f in obj["files"]:
        if not f["upload"]:
            why = f.get("note") or ""
            if f["requirement"] in ("not_allowed", "n/a"):
                why = "%s: %s" % (f["requirement"].replace("_", " "), why)
            lines.append("| %s | %s | `%s` |" % (_md(f["file"]), _md(why), f["sha256"]))
    if obj["findings"]:
        lines += ["", "## Open items", ""]
        for f in obj["findings"]:
            lines.append("- %s %s: %s" % (f["level"], f["where"], f["message"]))
    lines.append("")
    return "\n".join(lines)


def render_text(res):
    s = res["summary"]
    out = ["manifest.py  %s files (%d to upload), %s" % (s["files"], s["uploads"], s["filing_type"])]
    for f in res["manifest"]["files"]:
        out.append("  %-34s %s" % (f["file"], ("upload as \"%s\" (%s)" % (f["description"], f["requirement"]))
                                   if f["upload"] else "not uploaded (%s)" % (f.get("note") or f["requirement"])))
    for f in res["findings"]:
        out.append("%-5s  %s  %s  %s" % (f["level"], f["code"], f["where"], f["message"]))
    out.append("Wrote: %s" % ", ".join(res["written"]))
    return "\n".join(out)


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", default="patent", help="matter folder (default: patent)")
    p.add_argument("--type", choices=["provisional", "nonprovisional"], help="override the filing type")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--no-audit", action="store_true", help="do not append to audit.jsonl")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        res = run(args)
    except UsageError as e:
        if args.json:
            print(json.dumps({"ok": False, "exit_code": 2, "error": str(e), "findings": []}, indent=2))
        else:
            print("ERROR: %s" % e, file=sys.stderr)
        return 2
    print(json.dumps({k: v for k, v in res.items()}, indent=2, ensure_ascii=False) if args.json else render_text(res))
    return res["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
