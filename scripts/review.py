#!/usr/bin/env python3
"""Versioned assessment records. Checks structure/evidence flags/freshness, not legal truth."""
import argparse
import copy
import json
import re
from pathlib import Path

from state import UsageError, FILING_COMPUTED_FIELDS, sha256_path, utc_now, write_json

PHASES = ("clarify", "lite", "deep", "draft")
TEXT_FIELDS = ("scope", "bottom_line", "examiner_objection", "applicant_response",
               "resolution", "next_action", "uncertainty", "inventor_fidelity")
OUTCOMES = {
    "clarify": {"ready_to_search", "needs_clarification", "eligibility_concern",
                "disclosure_concern", "bar_concern"},
    "lite": {"likely_unpatentable", "no_blocker_found", "inconclusive"},
    "deep": {"likely_patentable", "likely_unpatentable", "inconclusive"},
    "draft": {"likely_patentable", "likely_unpatentable", "inconclusive"},
}


def read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise UsageError("Cannot read %s: %s" % (path, e)) from e


def inputs(phase):
    paths = ["invention-disclosure.md"]
    if phase != "clarify":
        paths += ["prior-art.json"]
    if phase == "draft":
        paths += ["draft/claims.md", "draft/spec.md", "draft/figures.json",
                  "draft/filing.json", "draft/support-map.md"]
    return paths


def snapshot(directory, phase):
    import hashlib
    result = {}
    base = Path(directory).resolve()
    for rel in inputs(phase):
        path = base / rel
        if base not in path.resolve().parents:
            raise UsageError("Review inputs must stay inside the matter: " + rel)
        if not path.is_file():
            raise UsageError("Missing review input: " + rel)
        if rel == "draft/filing.json":
            obj = read(path)
            if not isinstance(obj, dict):
                raise UsageError("filing.json must be an object")
            obj = {k: v for k, v in obj.items() if k not in FILING_COMPUTED_FIELDS}
            digest = hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()
        else:
            digest = sha256_path(str(path))
        result[rel] = digest
    return result


def validate(assessment, phase, directory):
    if phase not in PHASES or not isinstance(assessment, dict):
        raise UsageError("Expected a review object and a supported phase")
    for field in TEXT_FIELDS:
        value = assessment.get(field)
        if not isinstance(value, str) or not value.strip():
            raise UsageError("Review requires " + field)
        if value.startswith(("Replace with", "Identify the strongest", "State the strongest",
                             "Explain which argument", "Identify the consequential",
                             "State the specific", "Explain how material")):
            raise UsageError("Replace the template instruction in " + field)
    purpose = assessment.get("purpose")
    if purpose not in ("patentability", "fto", "invalidity", "landscape"):
        raise UsageError("Specify patentability, fto, invalidity or landscape purpose")
    allowed = OUTCOMES[phase] if purpose == "patentability" else {"assessed_risks", "inconclusive"}
    if purpose != "patentability" and phase != "deep":
        raise UsageError("Other purposes use the separate deep-analysis mode")
    outcome = assessment.get("outcome")
    if outcome not in allowed:
        raise UsageError("Outcome is not allowed for this phase/purpose")
    if not isinstance(assessment.get("scope_confirmed"), bool):
        raise UsageError("scope_confirmed must record an actual boolean")
    if (outcome in ("ready_to_search", "likely_patentable") or phase == "draft") and not assessment["scope_confirmed"]:
        raise UsageError("Confirm actual inventor/claim scope before this assessment")
    coverage = assessment.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("search") not in ("none", "limited", "substantial"):
        raise UsageError("coverage.search must be none, limited or substantial")
    limits = coverage.get("limits")
    if not isinstance(limits, list) or not limits or not all(isinstance(x, str) and x.strip() for x in limits):
        raise UsageError("Record specific coverage limits (even a substantial search has limits)")
    grounds = assessment.get("grounds")
    if not isinstance(grounds, list) or not all(isinstance(x, str) and x in ("101", "102", "103", "112", "bar") for x in grounds):
        raise UsageError("grounds must be a list using 101, 102, 103, 112, bar")
    ids = assessment.get("reference_ids")
    if not isinstance(ids, list) or not all(isinstance(x, str) and x for x in ids):
        raise UsageError("reference_ids must be a list of identifiers")
    if phase == "clarify" and (coverage["search"] != "none" or set(grounds) & {"102", "103"} or ids):
        raise UsageError("Phase 0 does not assess novelty/obviousness or search prior art")
    if outcome == "likely_patentable" and coverage["search"] != "substantial":
        raise UsageError("A favorable patentability assessment needs substantial recorded review")
    if outcome == "no_blocker_found" and coverage["search"] == "none":
        raise UsageError("No-blocker-found requires an actual search")
    if outcome == "likely_unpatentable" and not grounds:
        raise UsageError("An adverse assessment needs a stated legal ground")
    if phase == "draft" and outcome != "likely_patentable":
        if not isinstance(assessment.get("proceed_basis"), str) or not assessment["proceed_basis"].strip():
            raise UsageError("Record the user's basis for drafting despite unresolved/adverse assessment")
    if set(grounds) & {"102", "103"}:
        if not ids or coverage["search"] == "none":
            raise UsageError("Prior-art assessment needs reviewed references and search coverage")
    if ids:
        art = read(Path(directory) / "prior-art.json")
        refs = {r.get("id"): r for r in art.get("references", [])}
        for ident in ids:
            ref = refs.get(ident, {})
            if ref.get("verified") is not True or not ref.get("verified_how") or not ref.get("verified_on"):
                raise UsageError("Reference %s lacks a recorded source verification" % ident)
    return assessment


def record(directory, phase, assessment):
    validate(assessment, phase, directory)
    hashes = snapshot(directory, phase)
    dest = Path(directory) / "reviews"
    dest.mkdir(exist_ok=True)
    if dest.is_symlink():
        raise UsageError("reviews must not be a symlink")
    index_path = dest / "index.json"
    if index_path.is_symlink():
        raise UsageError("review index must not be a symlink")
    index = read(index_path) if index_path.exists() else {}
    if not isinstance(index, dict):
        raise UsageError("Invalid review index")
    numbers = [int(f.name.split("-")[0]) for f in dest.glob("*.json")
               if re.fullmatch(r"\d{6,}-[a-z]+\.json", f.name)]
    number = max(numbers, default=0) + 1
    filename = "%06d-%s.json" % (number, phase)
    obj = copy.deepcopy(assessment)
    obj.update(schema="patentassist/review@1", phase=phase, recorded=utc_now(), input_hashes=hashes)
    # Exclusive creation preserves earlier records, including when a name is occupied.
    with (dest / filename).open("x", encoding="utf-8") as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    index[phase] = filename
    write_json(str(index_path), index)
    return filename


def check(directory, phase):
    dest = Path(directory) / "reviews"
    if dest.is_symlink() or (dest / "index.json").is_symlink():
        raise UsageError("Review history must stay inside the matter")
    index = read(dest / "index.json")
    if not isinstance(index, dict):
        raise UsageError("Invalid review index")
    filename = index.get(phase, "")
    if not isinstance(filename, str) or not re.fullmatch(r"\d{6,}-" + re.escape(phase) + r"\.json", filename):
        raise UsageError("No valid latest %s review" % phase)
    if (dest / filename).is_symlink():
        raise UsageError("Review history must stay inside the matter")
    obj = read(dest / filename)
    if not isinstance(obj, dict) or obj.get("schema") != "patentassist/review@1" or obj.get("phase") != phase:
        raise UsageError("Unsupported review schema/phase")
    validate(obj, phase, directory)
    current = snapshot(directory, phase)
    if obj.get("input_hashes") != current:
        raise UsageError("Stale %s assessment: inputs changed; reassess and record a new version" % phase)
    return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("record", "check"))
    parser.add_argument("--phase", choices=PHASES, required=True)
    parser.add_argument("--dir", required=True)
    parser.add_argument("--input")
    args = parser.parse_args()
    try:
        if args.command == "record":
            if not args.input:
                raise UsageError("record requires --input")
            print(record(args.dir, args.phase, read(args.input)))
        else:
            obj = check(args.dir, args.phase)
            print("Current %s review: %s (mechanical checks only)" % (args.phase, obj["outcome"]))
        return 0
    except (UsageError, OSError, ValueError) as exc:
        print("Review check failed: " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
