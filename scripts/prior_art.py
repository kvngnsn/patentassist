#!/usr/bin/env python3
"""Edit prior-art.json without hand-editing JSON: elements, cutoff, vocabulary, references, cells.

Examples:
    python3 scripts/prior_art.py elements add "a vibration sensor coupled to the pot" \\
        --test "a sensor that measures vibration of the vessel"
    python3 scripts/prior_art.py elements set E3 --test "dominant frequency band shifts and total level \\
        rises above a limit, held for N intervals"          # purpose-free restatement (phase 2 Step 4.0)
    python3 scripts/prior_art.py elements set E4 --essential false
    python3 scripts/prior_art.py elements list
    python3 scripts/prior_art.py cutoff --date 2026-11-18 --basis "no disclosure yet; today's date used"
    python3 scripts/prior_art.py vocabulary set E1 "vibration|acoustic|accelerometer|piezo" --confirmed
    python3 scripts/prior_art.py ref add US9457709B2 --category X
    python3 scripts/prior_art.py ref add 10.1121/1.1566333 --type npl
    python3 scripts/prior_art.py cell set R1 E2 --state partial --pinpoint "[0021]" \\
        --quote "exact words from the fetched text" --note "lights not said to be LEDs"
    python3 scripts/prior_art.py combo add --refs R1,R3 --covers E1,E2,E3 \\
        --rationale "KSR (G): known technique to improve a similar device" --strength strong
    python3 scripts/prior_art.py read-not-cited add US8803674B2 --why "lights on the bicycle, not the helmet"
    python3 scripts/prior_art.py not-searched add "non-English full text"

Fields (references/state-files.md, prior-art.json):
  elements[]    {id, text, essential, test}. `test` restates the element as a structural or functional
                test with no purpose words; chart against the test and note the purpose separately.
  vocabulary    {E1: {terms: [...], confirmed_by_user: bool}}: the synonym families shown to the user.
  references[]  `ref add` writes a stub {id, type, number|doi|arxiv_id|url, category, verified: false,
                element_map: {}}; verify_refs.py fills title, dates, assignee, and prior_art_basis.
  element_map   `cell set` validates the state (explicit | inherent | partial | absent | unknown) and
                replaces the cell. quote_check.py later confirms the quote is verbatim and rewrites the
                pinpoint from the cache.

Every write appends a `note` line to audit.jsonl (unless --no-audit). This script never touches the
network. Exit codes: 0 ok, 2 bad input.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _dates import parse_date  # noqa: E402
from normalize_number import normalize  # noqa: E402
from state import (UsageError, add_common, audit, cli_main, finalize, finding, load_prior_art,  # noqa: E402
                   new_result, save_prior_art, to_namespace)

REF_TYPES = ("patent", "application", "npl", "product", "web")
CATEGORIES = ("X", "Y", "A", "P", "E")
STATES = ("explicit", "inherent", "partial", "absent", "unknown")
POSITIVE = ("explicit", "inherent", "partial")
STRENGTHS = ("strong", "moderate", "weak")
# fields other scripts derive from the quote; kept by `cell set` while the quote is unchanged
DERIVED_CELL_FIELDS = ("pinpoint_colline", "pinpoint_colline_candidate", "pinpoint_also", "source_number")
PINPOINT_RE = re.compile(
    r"^(\[\d{4,5}\](\s*-\s*\[\d{4,5}\])?|p\d+|text p\d+|claims? \d+([-,] ?\d+)*|abstract|title|"
    r"col(?:s|umns?)?\.? \d+.*|page \d+.*|p(?:p)?\. \d+.*|fig(?:ure)?s?\.? \d+.*|section .+|table \d+.*)$", re.I)
PURPOSE_RE = re.compile(r"\b(in order to|so as to|so that|for the purpose of|intended to|to prevent|to avoid|"
                        r"to warn|pre-(?!determined|defined|set|selected|stored|amp|programmed|configured|loaded)"
                        r"[a-z]+)\b", re.I)
DOI_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)?(10\.\d{4,9}/\S+)$", re.I)
ARXIV_RE = re.compile(r"^(?:arxiv:)?(\d{4}\.\d{4,5}(?:v\d+)?)$", re.I)
URL_RE = re.compile(r"^https?://\S+$", re.I)


def _split(s, sep=","):
    if s is None:
        return []
    if isinstance(s, list):
        return [str(x).strip() for x in s if str(x).strip()]
    return [x.strip() for x in str(s).split(sep) if x.strip()]


def _bool(v, name):
    if isinstance(v, bool):
        return v
    t = str(v).strip().lower()
    if t in ("true", "yes", "y", "1"):
        return True
    if t in ("false", "no", "n", "0"):
        return False
    raise UsageError("%s must be true or false (got %r)" % (name, v))


def _family_key(n):
    r = normalize(n or "")
    if r.get("ok") and r.get("number"):
        return "%s%s" % (r["country"], r["number"])
    return (n or "").strip().upper()


def _elements(pa):
    return pa.setdefault("elements", [])


def _element(pa, eid):
    return next((e for e in _elements(pa) if str(e.get("id")) == eid), None)


def _need_element(pa, eid):
    e = _element(pa, eid)
    if e is None:
        known = ", ".join(str(x.get("id")) for x in _elements(pa)) or "none defined"
        raise UsageError("element %s is not in prior-art.json elements (%s); add it with: prior_art.py elements add"
                         % (eid, known))
    return e


def _ref(pa, rid):
    return next((r for r in pa.get("references") or [] if str(r.get("id")) == rid), None)


def _need_ref(pa, rid):
    r = _ref(pa, rid)
    if r is None:
        known = ", ".join(str(x.get("id")) for x in pa.get("references") or []) or "none"
        raise UsageError("reference %s is not in prior-art.json (%s); add it with: prior_art.py ref add NUMBER"
                         % (rid, known))
    return r


def _next_id(prefix, ids):
    nums = [int(m.group(1)) for m in (re.match(r"^%s(\d+)$" % prefix, str(i) or "") for i in ids) if m]
    return "%s%d" % (prefix, (max(nums) if nums else 0) + 1)


def _purpose_check(text, eid, res):
    m = PURPOSE_RE.search(text or "")
    if m:
        res["findings"].append(finding("WARN", "purpose_words", eid,
                                       "test contains purpose wording %r; restate it as structure or function only "
                                       "and keep the purpose in text or a note" % m.group(0)))


def _ref_label(r):
    return r.get("number") or r.get("doi") or r.get("arxiv_id") or r.get("url") or r.get("title") or "?"


# --------------------------------------------------------------------------- elements


def cmd_elements(a, pa, res):
    act = a.action
    if act == "list":
        els = _elements(pa)
        vocab = pa.get("vocabulary") or {}
        res["elements"] = els
        res["vocabulary"] = vocab
        if not els:
            res["text"].append("No elements defined (prior_art.py elements add \"...\").")
        for e in els:
            eid = str(e.get("id"))
            res["text"].append("%-4s %s  %s" % (eid, "essential" if e.get("essential", True) else "optional ",
                                                e.get("text")))
            if e.get("test"):
                res["text"].append("     test: %s" % e["test"])
            else:
                res["findings"].append(finding("INFO", "no_test", eid, "no purpose-free test yet; add one with "
                                               "elements set %s --test \"...\" before charting" % eid))
            v = vocab.get(eid)
            if v:
                res["text"].append("     vocabulary: %s%s" % (" | ".join(v.get("terms") or []),
                                                             "" if v.get("confirmed_by_user") else
                                                             "  (not confirmed by user)"))
        res["summary"] = {"elements": len(els), "with_test": sum(1 for e in els if e.get("test")),
                          "vocabulary": len(vocab), "vocabulary_confirmed":
                          sum(1 for v in vocab.values() if (v or {}).get("confirmed_by_user"))}
        return False
    if act == "add":
        text = (a.text or "").strip()
        if not text:
            raise UsageError("elements add needs the element text")
        eid = (a.id or "").strip() or _next_id("E", [e.get("id") for e in _elements(pa)])
        if re.search(r"\s", eid):
            raise UsageError("element id must not contain spaces: %r" % eid)
        if _element(pa, eid):
            raise UsageError("element %s already exists; change it with: elements set %s" % (eid, eid))
        e = {"id": eid, "text": text, "essential": True if a.essential is None else _bool(a.essential, "--essential")}
        if a.test and a.test.strip():
            e["test"] = a.test.strip()
            _purpose_check(e["test"], eid, res)
        _elements(pa).append(e)
        res["element"] = e
        res["text"].append("%s added: %s%s" % (eid, text, "" if e["essential"] else " (optional)"))
        if "test" not in e:
            res["text"].append("Add a purpose-free test before charting: elements set %s --test \"...\"" % eid)
        return {"action": "elements.add", "id": eid}
    if act == "set":
        eid = (a.id or "").strip()
        e = _need_element(pa, eid)
        if a.text is None and a.test is None and a.essential is None:
            raise UsageError("elements set needs --text, --test, or --essential")
        changed = []
        if a.text is not None:
            if not a.text.strip():
                raise UsageError("--text must not be empty")
            e["text"] = a.text.strip()
            changed.append("text")
        if a.test is not None:
            if a.test.strip():
                e["test"] = a.test.strip()
                _purpose_check(e["test"], eid, res)
            else:
                e.pop("test", None)
            changed.append("test")
        if a.essential is not None:
            e["essential"] = _bool(a.essential, "--essential")
            changed.append("essential")
        res["element"] = e
        res["text"].append("%s updated (%s)" % (eid, ", ".join(changed)))
        return {"action": "elements.set", "id": eid, "fields": changed}
    raise UsageError("elements action must be add, set, or list")


# --------------------------------------------------------------------------- cutoff


def cmd_cutoff(a, pa, res):
    if not a.date:
        raise UsageError("cutoff needs --date YYYY-MM-DD")
    try:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(a.date).strip()):
            raise ValueError
        d = parse_date(a.date).isoformat()
    except ValueError:
        raise UsageError("--date must be an ISO date YYYY-MM-DD (got %r)" % a.date)
    if not a.basis or not a.basis.strip():
        raise UsageError("cutoff needs --basis (why this date: e.g. earliest effective filing date, or today's "
                         "date when nothing is filed)")
    old = pa.get("cutoff_date")
    pa["cutoff_date"] = d
    pa["cutoff_basis"] = a.basis.strip()
    res["cutoff"] = {"cutoff_date": d, "cutoff_basis": pa["cutoff_basis"]}
    res["text"].append("cutoff_date = %s (%s)" % (d, pa["cutoff_basis"]))
    if old and old != d and pa.get("references"):
        res["findings"].append(finding("INFO", "rerun_verify", "cutoff", "cutoff changed %s -> %s: re-run "
                                       "verify_refs.py to recompute prior_art_basis" % (old, d)))
    return {"action": "cutoff", "cutoff_date": d, "previous": old}


# --------------------------------------------------------------------------- vocabulary


def cmd_vocabulary(a, pa, res):
    vocab = pa.setdefault("vocabulary", {})
    if a.action == "list":
        res["vocabulary"] = vocab
        if not vocab:
            res["text"].append("No vocabulary recorded.")
        for eid, v in vocab.items():
            res["text"].append("%-4s %s%s" % (eid, " | ".join((v or {}).get("terms") or []),
                                              "" if (v or {}).get("confirmed_by_user") else "  (not confirmed)"))
        return False
    if a.action != "set":
        raise UsageError("vocabulary action must be set or list")
    if not _elements(pa):
        raise UsageError("define elements first (prior_art.py elements add)")
    eid = (a.id or "").strip()
    _need_element(pa, eid)
    terms = []
    for t in _split(a.terms, "|"):
        if t.lower() not in [x.lower() for x in terms]:
            terms.append(t)
    if not terms:
        raise UsageError("give the terms separated by |, e.g. \"vibration|acoustic|piezo\"")
    old = vocab.get(eid) or {}
    same = [x.lower() for x in old.get("terms") or []] == [x.lower() for x in terms]
    confirmed = bool(a.confirmed) or (same and bool(old.get("confirmed_by_user")))
    vocab[eid] = {"terms": terms, "confirmed_by_user": confirmed}
    res["vocabulary"] = {eid: vocab[eid]}
    res["text"].append("%s vocabulary: %s%s" % (eid, " | ".join(terms),
                                                "  (confirmed by user)" if confirmed else
                                                "  (not confirmed: show it to the user, then add --confirmed)"))
    return {"action": "vocabulary.set", "id": eid, "terms": terms, "confirmed_by_user": confirmed}


# --------------------------------------------------------------------------- references


def _ident(raw, rtype):
    """Return (fields, inferred_type) for a reference identifier."""
    raw = raw.strip()
    m = DOI_RE.match(raw)
    if m and rtype in (None, "npl"):
        return {"doi": m.group(1)}, "npl"
    m = ARXIV_RE.match(raw)
    if m and rtype in (None, "npl"):
        return {"arxiv_id": m.group(1)}, "npl"
    if URL_RE.match(raw) and rtype in (None, "web", "product", "npl"):
        return {"url": raw}, rtype or "web"
    if rtype in ("npl", "product", "web"):
        return {"title": raw}, rtype
    norm = normalize(raw)
    if not norm.get("ok"):
        raise UsageError("cannot parse %r as a patent number, DOI, arXiv id, or URL: %s (use --type npl|product|web "
                         "for other references)" % (raw, "; ".join(norm.get("notes") or [])))
    if norm["doc_type"] == "application_no":
        raise UsageError("%s is an application number; add its publication or patent number" % norm["canonical"])
    inferred = "application" if norm["doc_type"] == "application_pub" else "patent"
    return {"number": norm["canonical"]}, inferred


def cmd_ref(a, pa, res):
    if a.action != "add":
        raise UsageError("ref action must be add")
    if not a.number or not str(a.number).strip():
        raise UsageError("ref add needs a number (or DOI / arXiv id / URL)")
    if a.type is not None and a.type not in REF_TYPES:
        raise UsageError("--type must be one of %s" % ", ".join(REF_TYPES))
    cat = a.category.strip().upper() if a.category else None
    if cat is not None and cat not in CATEGORIES:
        raise UsageError("--category must be one of %s" % ", ".join(CATEGORIES))
    fields, inferred = _ident(str(a.number), a.type)
    rtype = inferred
    if a.type and a.type != inferred:
        if "number" in fields and a.type in ("patent", "application"):
            res["findings"].append(finding("WARN", "type_inferred", fields["number"],
                                           "%s is a %s by its number; recorded as %s" % (fields["number"], inferred,
                                                                                        inferred)))
        else:
            rtype = a.type
    refs = pa.setdefault("references", [])
    key = None
    if "number" in fields:
        key = _family_key(fields["number"])
        for r in refs:
            for n in [r.get("number")] + list(r.get("family") or []):
                if n and _family_key(n) == key:
                    raise UsageError("%s is already %s (%s)" % (fields["number"], r.get("id"), r.get("number")))
    else:
        k, v = next(iter(fields.items()))
        if k != "title":
            for r in refs:
                if (r.get(k) or "").strip().lower() == v.lower():
                    raise UsageError("%s is already %s" % (v, r.get("id")))
    rid = (a.id or "").strip() or _next_id("R", [r.get("id") for r in refs])
    if _ref(pa, rid):
        raise UsageError("reference id %s already exists" % rid)
    stub = {"id": rid, "type": rtype}
    stub.update(fields)
    stub.update({"category": cat, "verified": False, "element_map": {}})
    refs.append(stub)
    if key:
        rnc = pa.get("read_not_cited") or []
        moved = [x for x in rnc if x.get("number") and _family_key(x["number"]) == key]
        if moved:
            pa["read_not_cited"] = [x for x in rnc if x not in moved]
            res["findings"].append(finding("INFO", "moved_from_read_not_cited", rid,
                                           "%s was in read_not_cited; removed there now that it is cited"
                                           % fields["number"]))
    res["reference"] = stub
    res["text"].append("%s added: %s (%s%s, UNVERIFIED)" % (rid, _ref_label(stub), rtype,
                                                           ", category %s" % cat if cat else ""))
    res["text"].append("Next: verify_refs.py --only %s (fills title, dates, assignee, prior_art_basis)" % rid)
    return {"action": "ref.add", "id": rid, "ref": _ref_label(stub), "type": rtype}


# --------------------------------------------------------------------------- cells


def cmd_cell(a, pa, res):
    if a.action != "set":
        raise UsageError("cell action must be set")
    rid, eid = (a.ref or "").strip(), (a.element or "").strip()
    ref = _need_ref(pa, rid)
    _need_element(pa, eid)
    state = (a.state or "").strip().lower()
    if state not in STATES:
        raise UsageError("--state must be one of %s (got %r); 'unknown' (could not read enough) never collapses "
                         "into 'absent'" % (", ".join(STATES), a.state))
    where = "%s.%s" % (rid, eid)
    quote = a.quote.strip() if a.quote and a.quote.strip() else None
    pin = a.pinpoint.strip() if a.pinpoint and a.pinpoint.strip() else None
    if state in POSITIVE and not quote:
        res["findings"].append(finding("WARN", "quote_missing", where,
                                       "state %s needs a verbatim quote from the fetched text" % state))
    if state == "inherent":
        res["findings"].append(finding("INFO", "inherent", where, "inherent needs evidence that the feature "
                                       "necessarily follows (probability is not enough); it stays on the "
                                       "needs-evidence list"))
    if pin and not PINPOINT_RE.match(pin):
        res["findings"].append(finding("WARN", "pinpoint_format", where,
                                       "unusual pinpoint %r (expected [0021], p17, claim 3, abstract, col. 4, "
                                       "ll. 10-22, page 3 ...); quote_check.py rewrites it from the cache" % pin))
    if state in ("absent", "unknown") and pin and not quote:
        res["findings"].append(finding("WARN", "pinpoint_without_quote", where,
                                       "a pinpoint without a quote cannot be checked"))
    em = ref.get("element_map")
    if not isinstance(em, dict):
        em = ref["element_map"] = {}
    old = em.get(eid) if isinstance(em.get(eid), dict) else {}
    cell = {"state": state, "pinpoint": pin, "quote": quote}
    if a.note and a.note.strip():
        cell["note"] = a.note.strip()
    if a.construction_dependent:
        cell["construction_dependent"] = True
    if quote and old.get("quote") == quote:
        for k in DERIVED_CELL_FIELDS:
            if k in old:
                cell[k] = old[k]
    em[eid] = cell
    res["cell"] = {"ref": rid, "element": eid, "entry": cell}
    res["text"].append("%s = %s%s%s" % (where, state, (" at %s" % pin) if pin else "",
                                        "  (construction-dependent)" if cell.get("construction_dependent") else ""))
    if quote:
        res["text"].append("Next: quote_check.py (confirms the quote is verbatim and fills the pinpoint)")
    return {"action": "cell.set", "ref": rid, "element": eid, "state": state}


# --------------------------------------------------------------------------- combinations, lists


def cmd_combo(a, pa, res):
    if a.action != "add":
        raise UsageError("combo action must be add")
    refs = _split(a.refs)
    if len(refs) < 2:
        raise UsageError("--refs needs at least two reference ids, e.g. R1,R3")
    for r in refs:
        _need_ref(pa, r)
    covers = _split(a.covers)
    if not covers:
        raise UsageError("--covers needs the element ids the combination teaches, e.g. E1,E2")
    for e in covers:
        _need_element(pa, e)
    if not a.rationale or not a.rationale.strip():
        raise UsageError("--rationale is required (e.g. \"KSR (G): known technique to improve a similar device\")")
    strength = (a.strength or "").strip().lower()
    if strength not in STRENGTHS:
        raise UsageError("--strength must be one of %s" % ", ".join(STRENGTHS))
    combos = pa.setdefault("combinations", [])
    if any(sorted(c.get("refs") or []) == sorted(refs) for c in combos):
        res["findings"].append(finding("WARN", "duplicate_combination", "+".join(refs),
                                       "this set of references already has a combination entry"))
    c = {"refs": refs, "covers": covers, "rationale": a.rationale.strip(), "strength": strength}
    combos.append(c)
    missing = [str(e.get("id")) for e in _elements(pa) if e.get("essential", True) and str(e.get("id")) not in covers]
    if missing:
        res["findings"].append(finding("INFO", "elements_not_covered", "+".join(refs),
                                       "essential elements not covered: %s" % ", ".join(missing)))
    res["combination"] = c
    res["text"].append("combination %s covers %s (%s)" % ("+".join(refs), ",".join(covers), strength))
    return {"action": "combo.add", "refs": refs, "covers": covers, "strength": strength}


def cmd_read_not_cited(a, pa, res):
    if a.action != "add":
        raise UsageError("read-not-cited action must be add")
    raw = (a.number or "").strip()
    if not raw:
        raise UsageError("read-not-cited add needs a number")
    if not a.why or not a.why.strip():
        raise UsageError("--why is required (one line: why it was read but not cited)")
    norm = normalize(raw)
    number = norm["canonical"] if norm.get("ok") else raw
    key = _family_key(number)
    for r in pa.get("references") or []:
        for n in [r.get("number")] + list(r.get("family") or []):
            if n and _family_key(n) == key:
                raise UsageError("%s is cited as %s; remove it there first if it should not be cited"
                                 % (number, r.get("id")))
    rnc = pa.setdefault("read_not_cited", [])
    cur = next((x for x in rnc if x.get("number") and _family_key(x["number"]) == key), None)
    if cur:
        cur["why"] = a.why.strip()
        res["findings"].append(finding("INFO", "already_listed", number, "already in read_not_cited; why updated"))
        entry = cur
    else:
        entry = {"number": number, "why": a.why.strip()}
        rnc.append(entry)
    res["entry"] = entry
    res["text"].append("read, not cited: %s (%s)" % (number, entry["why"]))
    return {"action": "read_not_cited.add", "number": number}


def cmd_not_searched(a, pa, res):
    if a.action != "add":
        raise UsageError("not-searched action must be add")
    text = (a.text or "").strip()
    if not text:
        raise UsageError("not-searched add needs the text, e.g. \"non-English full text\"")
    ns = pa.setdefault("not_searched", [])
    if text.lower() in [str(x).lower() for x in ns]:
        res["text"].append("already listed: %s" % text)
        return False
    ns.append(text)
    res["text"].append("not searched: %s" % text)
    return {"action": "not_searched.add", "text": text}


COMMANDS = {"elements": cmd_elements, "cutoff": cmd_cutoff, "vocabulary": cmd_vocabulary, "ref": cmd_ref,
            "cell": cmd_cell, "combo": cmd_combo, "read-not-cited": cmd_read_not_cited,
            "not-searched": cmd_not_searched}
DEFAULTS = {"command": None, "action": None, "dir": "patent", "json": False, "no_audit": False, "text": None,
            "id": None, "test": None, "essential": None, "date": None, "basis": None, "terms": None,
            "confirmed": False, "number": None, "type": None, "category": None, "ref": None, "element": None,
            "state": None, "pinpoint": None, "quote": None, "note": None, "construction_dependent": False,
            "refs": None, "covers": None, "rationale": None, "strength": None, "why": None}


def run(args):
    a = to_namespace(args, DEFAULTS)
    if a.command not in COMMANDS:
        raise UsageError("command must be one of %s" % ", ".join(COMMANDS))
    pa = load_prior_art(a.dir)
    res = new_result()
    res["command"] = a.command if not a.action else "%s %s" % (a.command, a.action)
    change = COMMANDS[a.command](a, pa, res)
    if change:
        save_prior_art(a.dir, pa)
        detail = dict(change)
        action = detail.pop("action")
        audit(a.dir, "note", a.no_audit, action="prior_art." + action, **detail)
        res["written"] = os.path.join(a.dir, "prior-art.json")
    return finalize(res)


def build_parser():
    p = argparse.ArgumentParser(prog="prior_art.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common(p)
    sp = p.add_subparsers(dest="command")

    def sub(parent, name, h):
        s = parent.add_parser(name, help=h)
        add_common(s, sub=True)
        return s

    g = sp.add_parser("elements", help="add / set / list claim elements")
    ga = g.add_subparsers(dest="action")
    s = sub(ga, "add", "add an element (next E-id unless --id)")
    s.add_argument("text")
    s.add_argument("--id", default=None)
    s.add_argument("--test", default=None, help="purpose-free structural/functional restatement")
    s.add_argument("--essential", default=None, help="true (default) or false")
    s = sub(ga, "set", "change an element's text, test, or essential flag")
    s.add_argument("id")
    s.add_argument("--text", default=None)
    s.add_argument("--test", default=None, help="purpose-free restatement (\"\" clears it)")
    s.add_argument("--essential", default=None, help="true or false")
    sub(ga, "list", "list elements with tests and vocabulary")

    s = sub(sp, "cutoff", "set cutoff_date and cutoff_basis")
    s.add_argument("--date", required=True)
    s.add_argument("--basis", required=True)

    g = sp.add_parser("vocabulary", help="record the synonym families per element")
    ga = g.add_subparsers(dest="action")
    s = sub(ga, "set", "set an element's terms, separated by |")
    s.add_argument("id")
    s.add_argument("terms")
    s.add_argument("--confirmed", action="store_true", help="the user confirmed this vocabulary")
    sub(ga, "list", "list vocabulary")

    g = sp.add_parser("ref", help="add a reference stub")
    ga = g.add_subparsers(dest="action")
    s = sub(ga, "add", "add a reference (verify_refs.py fills the metadata)")
    s.add_argument("number", help="patent/publication number, DOI, arXiv id, or URL")
    s.add_argument("--type", default=None, choices=REF_TYPES)
    s.add_argument("--category", default=None, help="X, Y, A, P, or E")
    s.add_argument("--id", default=None)

    g = sp.add_parser("cell", help="set one element_map cell")
    ga = g.add_subparsers(dest="action")
    s = sub(ga, "set", "set the state, pinpoint, and quote for a reference x element")
    s.add_argument("ref")
    s.add_argument("element")
    s.add_argument("--state", required=True, choices=STATES)
    s.add_argument("--pinpoint", default=None)
    s.add_argument("--quote", default=None, help="verbatim words from the fetched text")
    s.add_argument("--note", default=None)
    s.add_argument("--construction-dependent", action="store_true")

    g = sp.add_parser("combo", help="add an obviousness combination")
    ga = g.add_subparsers(dest="action")
    s = sub(ga, "add", "add a combination")
    s.add_argument("--refs", required=True)
    s.add_argument("--covers", required=True)
    s.add_argument("--rationale", required=True)
    s.add_argument("--strength", required=True, choices=STRENGTHS)

    g = sp.add_parser("read-not-cited", help="record a document read but not cited")
    ga = g.add_subparsers(dest="action")
    s = sub(ga, "add", "add a read-not-cited entry")
    s.add_argument("number")
    s.add_argument("--why", required=True)

    g = sp.add_parser("not-searched", help="record a coverage gap")
    ga = g.add_subparsers(dest="action")
    s = sub(ga, "add", "add a not-searched line")
    s.add_argument("text")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command and args.command != "cutoff" and getattr(args, "action", None) is None:
        sys.stderr.write("ERROR: %s needs an action (see prior_art.py %s --help)\n" % (args.command, args.command))
        return 2
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
