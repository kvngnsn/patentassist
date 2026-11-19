#!/usr/bin/env python3
"""Check a US patent claim set: numbering, dependencies, one-sentence form,
antecedent basis, 112(f) triggers, indefinite terms, term support, and counts.

    python3 scripts/check_claims.py [claims.md] [--spec spec.md] [--entity large|small|micro]
                                    [--dir patent] [--json] [--no-audit]

claims.md defaults to <dir>/draft/claims.md. The file may be the claims.md format
in references/state-files.md or plain text with the same "1. A ..." numbering.

Checks (code: rule):
  CLAIM_NUMBERING  consecutive arabic numbering from 1 (37 CFR 1.126)
  DEP_FORWARD      a dependent claim must refer to a preceding claim (37 CFR 1.75(c); MPEP 608.01(n))
  DEP_MISSING      the referenced claim does not exist or is canceled
  MULTI_DEP        multiple dependent claim (35 USC 112(e); 37 CFR 1.75(c); fee 37 CFR 1.16(j))
  MULTI_DEP_FORM   multiple dependent claim must refer in the alternative only (1.75(c))
  MULTI_ON_MULTI   a multiple dependent claim may not serve as a basis for another (1.75(c))
  ONE_SENTENCE     one sentence, capital letter, one period at the end (MPEP 608.01(m))
  ANTECEDENT       "the/said X" needs an earlier "a/an X" in the claim or its chain (MPEP 2173.05(e))
  DOUBLE_INTRO     the same element introduced twice with "a/an" in one chain
  NONCE_112F       "means for", "step for", nonce word + function (35 USC 112(f); Williamson)
  INDEFINITE       relative, optional, exemplary, or trademark language (35 USC 112(b); MPEP 2173.05)
  TERM_SUPPORT     claim terms found in the description (35 USC 112(a)/(b); 37 CFR 1.75(d)(1))
  COUNTS           independent / total / multiple-dependent counts for fees (37 CFR 1.16(h)-(j), 1.75(c))

The antecedent checker is a heuristic. It prefers WARN over BLOCK whenever the
parse is uncertain; a BLOCK means the term (or its head noun) is not introduced
anywhere the claim can draw on.

Exit codes: 0 no blocking findings, 1 blocking findings, 2 usage or input error.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import UsageError, audit, finding, to_namespace  # noqa: E402

SCRIPT = "check_claims.py"
HERE = os.path.dirname(os.path.abspath(__file__))
FEES_MD = os.path.join(os.path.dirname(HERE), "references", "fees.md")

ALL_CHECKS = ["CLAIM_NUMBERING", "DEPENDENCIES", "MULTI_DEP", "ONE_SENTENCE", "ANTECEDENT",
              "DOUBLE_INTRO", "NONCE_112F", "INDEFINITE", "TERM_SUPPORT", "COUNTS"]

# --------------------------------------------------------------------------- word lists

ORDINALS = {"first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth",
            "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "nth"}
NUMBER_WORDS = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                "eleven", "twelve", "twenty", "hundred", "thousand"}
DEF_DETS = {"the", "said"}
NEUTRAL_DETS = {"each", "every", "any", "another", "some", "all", "both", "either", "neither", "no",
                "its", "their", "his", "her", "this", "these", "those", "such", "several",
                "multiple", "various", "many", "few", "certain", "none"}
PREPS = {"of", "in", "on", "at", "to", "for", "from", "with", "by", "into", "onto", "over", "under",
         "between", "among", "amongst", "through", "throughout", "via", "within", "without",
         "about", "against", "along", "alongside", "around", "behind", "below", "above", "beneath",
         "beside", "besides", "beyond", "near", "upon", "across", "after", "before", "during",
         "toward", "towards", "inside", "outside", "per", "than", "like", "as", "past", "since",
         "until", "till", "up", "down", "off", "out", "underneath", "versus", "vs", "except",
         "regarding", "concerning", "plus", "minus", "atop", "amid"}
CONJ_ETC = {"and", "or", "but", "nor", "and/or", "wherein", "whereby", "whereas", "which", "that",
            "who", "whom", "whose", "when", "whenever", "where", "wherever", "while", "whether",
            "if", "unless", "so", "thereby", "therein", "thereof", "thereto", "therefrom",
            "therewith", "thereon", "therebetween", "thereafter", "then", "thus", "hence", "also",
            "further", "furthermore", "not", "only", "it", "they", "them", "itself", "themselves",
            "there", "here", "herein", "hereof", "how", "what", "why", "least", "most", "more",
            "less", "fewer", "very", "too", "just", "even", "still", "yet", "again", "once",
            "twice", "claim", "claims", "same", "otherwise", "instead", "rather", "because",
            "although", "though", "upon", "whereupon", "being", "been", "be", "is", "are", "was",
            "were", "has", "have", "had", "does", "do", "did", "can", "may", "might", "must",
            "shall", "should", "will", "would", "could", "comprising", "comprises", "comprise",
            "including", "includes", "include", "having", "consisting", "consists", "consist",
            "containing", "contains", "contain", "essentially", "'s", "s"}
MODALS = {"can", "may", "might", "must", "shall", "should", "will", "would", "could", "does", "do",
          "did", "to"}
POSTADJ = {"relative", "adjacent", "proximate", "proximal", "distal", "remote", "parallel",
           "perpendicular", "orthogonal", "opposite", "close", "next", "due", "prior",
           "subsequent", "responsive", "corresponding", "equal", "similar", "identical",
           "different", "independent", "separate", "apart", "away", "together", "outward",
           "inward", "upward", "downward", "forward", "rearward", "backward", "capable", "able",
           "configured", "adapted", "operable", "operative", "arranged", "programmed",
           "sufficient", "suitable", "effective", "associated", "coupled", "connected",
           "attached", "mounted", "disposed", "positioned", "located", "coextensive",
           "concentric", "coaxial", "aligned", "spaced", "based", "related", "dependent",
           "indicative", "representative", "available", "accessible", "present", "absent",
           "free", "integral", "unitary", "flush", "transverse", "selected", "chosen", "known",
           "greater", "smaller", "larger", "higher", "lower", "longer", "shorter", "wider",
           "narrower", "thicker", "thinner", "closer", "farther", "further"}
VERB_PURE = {"receive", "transmit", "send", "generate", "determine", "store", "provide", "cause",
             "detect", "indicate", "define", "extend", "rotate", "move", "execute", "perform",
             "carry", "engage", "couple", "connect", "surround", "enclose", "abut", "emit",
             "illuminate", "activate", "deactivate", "compare", "calculate", "compute", "select",
             "identify", "adjust", "apply", "produce", "convert", "communicate", "operate",
             "respond", "exceed", "correspond", "represent", "retrieve", "notify", "prevent",
             "allow", "enable", "reduce", "increase", "decrease", "maintain", "hold", "secure",
             "attach", "translate", "vary", "depend", "overlap", "protrude", "satisfy", "meet",
             "obtain", "modify", "create", "delete", "render", "encode", "decode", "encrypt",
             "decrypt", "authenticate", "verify", "validate", "estimate", "predict", "classify",
             "sense", "actuate", "urge", "align", "locate", "reside", "span", "separate",
             "divide", "combine", "join", "assign", "allocate", "invoke", "launch", "inject",
             "dissolve", "bind", "inhibit", "become", "remain", "appear", "occur", "exist",
             "begin", "continue", "get", "make", "take", "give", "keep", "let", "put", "show",
             "travel", "lie", "sit", "require", "permit", "facilitate", "ensure", "establish",
             "initiate", "terminate", "transfer", "use", "measure", "form", "emit", "blink",
             "flash", "turn", "wirelessly", "pair"}
# Third-person verb forms that end a noun phrase wherever they follow a noun ("whose fingerprint matches
# the spectrum", "the energy exceeds a threshold"). The -s/-es forms of VERB_PURE are handled by rule.
VERB_3P = {"matches", "exceeds", "includes", "comprises", "indicates", "contains", "defines", "receives",
           "transmits", "determines", "equals", "exhibits", "differs", "lacks", "surpasses", "satisfies",
           "outputs", "emits", "reaches", "crosses", "drops", "rises", "falls", "remains", "becomes",
           "corresponds", "represents", "generates", "detects", "stores", "provides", "causes", "computes",
           "calculates", "compares", "selects", "identifies", "produces", "performs", "executes", "instructs",
           "informs", "prompts"}
# Stems that are nouns as often as verbs ("signal", "control", "record"). Their -s/-es forms end a noun
# phrase only when a determiner, a number, or a plain noun follows ("the controller signals a fault",
# "the timer counts pulses"), never before a verb, a preposition, punctuation, or the end of the claim.
AMBIG_VERBS = {"match", "signal", "control", "record", "process", "drive", "power", "change", "shift",
               "limit", "trigger", "report", "fit", "contact", "support", "cover", "face", "border", "house",
               "lead", "feed", "test", "count", "sample", "filter", "pass", "touch", "press", "push", "pull",
               "lift", "flow", "pump", "switch", "display", "link", "mark", "map", "load", "charge", "heat",
               "cool", "command", "request", "return", "set", "reset", "update", "alert", "warn", "wait",
               "lock", "seal", "mount", "monitor", "scan", "track", "view", "list", "sort", "rank", "score",
               "input", "query", "access", "release", "start", "stop", "end", "exit", "enter", "close", "open",
               "toggle", "rest", "need", "lack", "fill", "drain", "act"}
NP_FOLLOWERS = {"a", "an", "the", "said", "none", "no", "one", "any", "all", "its", "their", "this", "these",
                "those", "both", "either", "every", "at", "another", "nothing", "only"}
# An -ing word mid-phrase modifies the next noun when an adjective comes before it ("an initial heating
# period", "a central processing unit", "a signal processing unit"); after a noun it is a verb and ends
# the phrase ("a sensor detecting vibration").
ADJ_WORDS = {"initial", "final", "main", "primary", "secondary", "normal", "low", "high", "full", "partial",
             "rapid", "slow", "fast", "new", "current", "standard", "ambient", "constant", "dominant",
             "transient", "resonant", "maximum", "minimum", "upper", "lower", "inner", "outer", "front", "rear",
             "short", "long", "early", "late", "steady", "low-power", "high-power"}
ADJ_SUFFIXES = ("al", "ic", "ive", "ous", "ary", "ible", "able", "less", "ful")
LY_NOUNS = {"assembly", "supply", "family", "anomaly", "reply", "poly", "butterfly", "fly", "ally",
            "rally", "jelly", "belly", "gully", "lily", "holly", "firefly", "monopoly", "italy",
            "july", "apply", "comply", "multiply", "rely", "imply", "ply", "doily", "panoply",
            "subassembly", "early", "daily", "weekly", "monthly", "hourly", "yearly", "friendly",
            "elderly", "likely", "costly", "orderly"}
ING_NOUNS = {"housing", "bearing", "ring", "string", "spring", "fitting", "coupling", "opening",
             "setting", "casing", "wing", "building", "ceiling", "drawing", "lining", "padding",
             "thing", "something", "nothing", "anything", "everything", "king", "bushing",
             "tubing", "piping", "wiring", "seating", "bedding", "clothing", "sling", "earring",
             "o-ring", "swing", "morning", "evening", "lightning", "railing", "siding",
             "flooring", "roofing", "molding", "moulding", "packaging", "recording", "reading",
             "mounting", "fastening", "fixing", "filling", "coating", "plating", "sealing",
             "binding", "timing", "spacing", "winding", "cladding", "shielding", "heading",
             "ending", "landing", "crossing", "sibling", "warning", "listing", "posting",
             "meeting", "offering", "painting", "embedding", "encoding", "mapping", "rating",
             "ranking", "spring", "bracketing", "fairing", "flashing", "grating", "lacing",
             "webbing", "netting", "ceiling", "awning", "dwelling"}
ED_NOUNS = {"speed", "bleed", "breed", "creed", "greed", "steed", "tweed", "embed", "hundred",
            "shred", "seabed", "airspeed", "flatbed", "hotbed", "seaweed", "proceed", "exceed"}
ABLE_NOUNS = {"cable", "table", "variable", "wearable", "consumable", "deliverable", "timetable",
              "turntable", "vegetable", "syllable", "receivable", "collectible", "convertible",
              "stable", "fable", "gable", "sable", "constable", "notable", "disposable"}
IRREGULAR = {"media": "medium", "criteria": "criterion", "phenomena": "phenomenon",
             "indices": "index", "vertices": "vertex", "matrices": "matrix",
             "appendices": "appendix", "apices": "apex", "radii": "radius", "nuclei": "nucleus",
             "stimuli": "stimulus", "foci": "focus", "fungi": "fungus", "teeth": "tooth",
             "feet": "foot", "geese": "goose", "mice": "mouse", "men": "man", "women": "woman",
             "children": "child", "people": "person", "oxen": "ox", "axes": "axis",
             "analyses": "analysis", "bases": "base", "theses": "thesis", "crises": "crisis",
             "halves": "half", "knives": "knife", "shelves": "shelf", "leaves": "leaf",
             "wolves": "wolf", "loaves": "loaf", "calves": "calf", "lives": "life",
             "wives": "wife", "selves": "self", "lenses": "lens", "buses": "bus",
             "busses": "bus", "gases": "gas", "biases": "bias", "aliases": "alias",
             "statuses": "status", "viruses": "virus", "focuses": "focus", "campuses": "campus",
             "canvases": "canvas", "atlases": "atlas", "corpuses": "corpus", "caches": "cache",
             "niches": "niche", "headaches": "headache", "cookies": "cookie", "movies": "movie",
             "calories": "calorie", "selfies": "selfie", "zombies": "zombie", "hoodies": "hoodie",
             "dies": "die", "ties": "tie", "lies": "lie", "pies": "pie", "data": "data",
             "schemata": "schema", "automata": "automaton", "quanta": "quantum",
             "spectra": "spectrum", "maxima": "maximum", "minima": "minimum",
             "optima": "optimum", "strata": "stratum", "bacteria": "bacterium"}
INVARIANT = {"series", "species", "apparatus", "chassis", "means", "headquarters", "aircraft",
             "spacecraft", "sheep", "fish", "deer", "news", "physics", "electronics", "optics",
             "mathematics", "analytics", "dynamics", "kinetics", "logistics", "graphics",
             "lens", "bias", "gas", "atlas", "canvas", "alias", "plus", "corpus", "status",
             "bus", "virus", "campus", "census", "focus", "radius", "stimulus", "nucleus",
             "thus", "yes", "its", "always", "perhaps", "whereas", "sometimes", "various",
             "previous", "wireless", "unless", "this", "his", "is", "was", "has", "does",
             "diabetes", "mumps", "measles", "pants", "scissors", "pliers", "tongs", "glasses",
             "goods", "premises", "thanks", "odds", "ethics", "statistics", "acoustics",
             "biomechanics", "mechanics", "haptics", "robotics", "genomics", "proteomics",
             "economics", "politics", "cross-hairs", "crosshairs", "alms", "outskirts"}

INHERENT_OF = {"number", "amount", "size", "length", "width", "height", "depth", "thickness",
               "weight", "mass", "volume", "area", "temperature", "pressure", "speed",
               "velocity", "position", "location", "orientation", "direction", "shape", "color",
               "colour", "surface", "edge", "end", "top", "bottom", "side", "center", "centre",
               "interior", "exterior", "periphery", "perimeter", "axis", "value", "magnitude",
               "level", "duration", "frequency", "rate", "time", "intensity", "brightness",
               "diameter", "radius", "circumference", "outer surface", "inner surface",
               "presence", "absence", "range", "sum", "total", "average", "mean", "rest",
               "remainder", "state", "status", "identity", "type", "content", "contents",
               "front", "back", "rear", "base", "tip", "middle", "portion", "part", "half",
               "outside", "inside", "form", "order", "basis", "purpose", "extent", "case",
               "event", "group", "start", "beginning", "output", "input"}
UNIQUE_THINGS = {"ground", "air", "atmosphere", "earth", "internet", "sun", "world", "sky",
                 "gravity", "environment", "art", "user"}
SKIP_FIRST = {"other", "same", "following", "foregoing", "like", "contrary", "preceding", "previous",
              "above", "aforementioned", "aforesaid", "latter", "former", "art"}
SOFT_MODS = {"other", "remaining", "respective", "corresponding", "entire", "whole", "same",
             "aforementioned", "aforesaid", "above-mentioned", "particular", "specific",
             "current", "given", "individual", "overall", "full", "complete", "selected",
             "previous", "new"}
# Mixed-case scientific terms and units that are not trademarks.
SCI_TERMS = {"pH", "pKa", "mRNA", "siRNA", "tRNA", "rRNA", "miRNA", "cDNA", "gRNA", "sgRNA", "dsDNA",
             "ssDNA", "dB", "dBm", "kHz", "MHz", "GHz", "mAh", "kWh", "mW", "kW", "eV", "keV", "MeV",
             "nm", "mL", "uL", "mM", "uM", "nM", "kDa", "kPa", "MPa", "GPa", "IoT", "SoC", "FinFET",
             "eNB", "gNB", "iOS", "macOS", "LiDAR", "CubeSat"}
NONCE = {"module", "modules", "mechanism", "mechanisms", "element", "elements", "device",
         "devices", "unit", "units", "component", "components", "member", "members",
         "apparatus", "system", "systems", "circuit", "circuits", "circuitry", "logic",
         "engine", "engines"}

# --------------------------------------------------------------------------- words


def lemma(w):
    """Singular form of one lowercase word (rule-based; consistent on both sides of a match)."""
    w = w.lower()
    if "-" in w:
        head, _, last = w.rpartition("-")
        return head + "-" + lemma(last) if last else w
    if w in IRREGULAR:
        return IRREGULAR[w]
    if w in INVARIANT or len(w) <= 3:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("sses", "xes", "ches", "shes", "zzes")):
        return w[:-2]
    if w.endswith(("ss", "us", "is", "ics", "ous", "sis", "'s")):
        return w
    if w.endswith("s"):
        return w[:-1]
    return w


def is_plural_word(w):
    w = w.lower()
    return lemma(w) != w and w not in ("data",)


def norm_words(words):
    """Normalize a noun phrase: lowercase, head noun singular."""
    ws = [w.lower() for w in words]
    if not ws:
        return ()
    return tuple(ws[:-1] + [lemma(ws[-1])])


def norm_text_for_match(text):
    """Lowercase, hyphens to spaces, every word singular; padded with spaces."""
    text = re.sub(r"[*_`#>|]", " ", text.lower())
    words = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.replace("-", " ").replace("/", " "))
    return " " + " ".join(lemma(w) for w in words) + " "


def term_in_text(term_words, norm_text):
    phrase = " ".join(lemma(w) for w in " ".join(term_words).replace("-", " ").replace("/", " ").split())
    return (" " + phrase + " ") in norm_text


def verbish(w):
    w = w.lower()
    if w in VERB_PURE or w in CONJ_ETC or w in PREPS or w in POSTADJ:
        return True
    if w.endswith("ly") and w not in LY_NOUNS and len(w) > 4:
        return True
    if w.endswith("ing") and w not in ING_NOUNS and len(w) > 4:
        return True
    if w.endswith("ed") and w not in ED_NOUNS and len(w) > 4:
        return True
    if w.endswith("es") and w[:-2] in VERB_PURE:
        return True
    if w.endswith("s") and w[:-1] in VERB_PURE:
        return True
    if w.endswith("ies") and (w[:-3] + "y") in VERB_PURE:
        return True
    return False


# --------------------------------------------------------------------------- parsing

CLAIM_START = re.compile(r"^\s{0,3}(\d+)\s*(?:[-–—]\s*(\d+)\s*)?[.)]\s*(.*)$")
STATUS_RE = re.compile(
    r"^\(\s*(canceled|cancelled|withdrawn(?:[- ]currently amended)?|original|currently amended|"
    r"previously presented|new|amended|rejected|allowed|objected to)\s*\)\s*", re.I)
PRECEDING_RE = re.compile(
    r"\bany\s+(?:one\s+)?(?:of\s+)?(?:the\s+)?(?:preceding|previous|foregoing|prior|above|"
    r"aforementioned)\s+claims?\b", re.I)


def _clean_md(line):
    line = re.sub(r"(\*\*|__)", "", line)
    line = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)\*(?!\w)", r"\1", line)
    return line


def parse_claims(text):
    """Parse claims text into a list of dicts:
    {num, text, status, line, deps, dep_kind, conj, any_preceding, ref_spans}."""
    claims = []
    cur = None
    in_code = False
    for ln, raw in enumerate(text.splitlines(), 1):
        if raw.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        line = _clean_md(raw.rstrip())
        stripped = line.strip()
        if stripped.startswith("#") or re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped or "x"):
            continue
        if stripped.startswith(">"):
            continue
        m = CLAIM_START.match(line)
        if m and (cur is None or not cur["text"] or len(line) - len(line.lstrip()) <= 3):
            body = m.group(3).strip()
            status = None
            sm = STATUS_RE.match(body)
            if sm:
                status = sm.group(1).lower().replace("cancelled", "canceled")
                body = body[sm.end():].strip()
            first, last = int(m.group(1)), int(m.group(2)) if m.group(2) else None
            if last is not None and last >= first and status == "canceled":
                for n in range(first, last + 1):
                    claims.append({"num": n, "text": "", "status": "canceled", "line": ln})
                cur = None
                continue
            cur = {"num": first, "text": body, "status": status, "line": ln}
            claims.append(cur)
            continue
        if cur is not None and stripped:
            if stripped.lower().startswith(("what is claimed", "i claim", "we claim", "claims:")):
                continue
            cur["text"] = (cur["text"] + " " + stripped).strip()
    for c in claims:
        c["text"] = re.sub(r"\s+", " ", c["text"]).strip()
        if c["status"] and c["status"].startswith("withdrawn"):
            c["status"] = "withdrawn"
        refs = find_claim_refs(c["text"])
        nums, conj, spans = [], set(), []
        for r in refs:
            for n in r["nums"]:
                if n not in nums:
                    nums.append(n)
            conj |= r["conj"]
            spans.append((r["start"], r["end"]))
        anyp = bool(PRECEDING_RE.search(c["text"]))
        if anyp:
            for o in claims:
                if o["num"] < c["num"] and o.get("status") != "canceled" and o["num"] not in nums:
                    nums.append(o["num"])
            conj.add("or")
        c["deps"] = nums
        c["conj"] = sorted(conj)
        c["any_preceding"] = anyp
        c["ref_spans"] = spans
        if c["status"] == "canceled" and not c["text"]:
            c["dep_kind"] = "canceled"
        elif not nums:
            c["dep_kind"] = "independent"
        elif len(nums) == 1:
            c["dep_kind"] = "single"
        else:
            c["dep_kind"] = "multiple"
    return claims


_NUM_AT = re.compile(r"\s*(\d+)")
_SEP_AT = re.compile(r"\s*(,\s*(?:or|and)\b|,|or\b|and\b|to\b|through\b|-|–|—)\s*(?:claims?\b)?",
                     re.I)


def find_claim_refs(text):
    out = []
    for m in re.finditer(r"\bclaims?\b", text, re.I):
        pos = m.end()
        nums, conj = [], set()
        pending_range = False
        expect_num = True
        while True:
            if expect_num:
                mm = _NUM_AT.match(text, pos)
                if not mm:
                    break
                n = int(mm.group(1))
                if pending_range and nums and n > nums[-1]:
                    nums.extend(range(nums[-1] + 1, n + 1))
                elif n not in nums:
                    nums.append(n)
                pending_range = False
                pos = mm.end()
                expect_num = False
            else:
                mm = _SEP_AT.match(text, pos)
                if not mm or not re.match(r"\s*\d", text[mm.end():]):
                    break
                sep = mm.group(1).lower()
                if sep in ("to", "through", "-", "–", "—"):
                    pending_range = True
                    conj.add("or")
                if "and" in sep:
                    conj.add("and")
                if "or" in sep:
                    conj.add("or")
                pos = mm.end()
                expect_num = True
        if nums:
            out.append({"start": m.start(), "end": pos, "nums": nums, "conj": conj})
    return out


def category(text):
    t = text.lower()[:160]
    if re.match(r"^(?:an?|one or more|at least one)\s+(?:[\w-]+\s+){0,4}?(?:method|process)\b", t):
        return "method"
    if re.search(r"\b(?:medium|media|storage device|memory device|program product|storage)\b",
                 t.split(" storing ")[0].split(" having ")[0]) and \
            re.search(r"\b(?:computer[- ]readable|machine[- ]readable|storage|program product)", t):
        return "crm"
    if re.match(r"^(?:an?|one or more)\s+(?:[\w-]+\s+){0,4}?(?:system|apparatus|device|machine|kit)\b", t):
        return "system/apparatus"
    if re.match(r"^(?:an?)\s+(?:[\w-]+\s+){0,4}?(?:composition|compound|formulation)\b", t):
        return "composition"
    return "other"


# --------------------------------------------------------------------------- noun-phrase chunker

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-/]*[A-Za-z0-9]|[A-Za-z0-9]|'s\b|[^\sA-Za-z0-9]")


def tokenize(text):
    text = re.sub(r"\(\s*\d+[a-zA-Z]?'?(?:\s*,\s*\d+[a-zA-Z]?'?)*\s*\)", " ", text)
    text = text.replace("’", "'")
    return TOKEN_RE.findall(text)


def _is_word(t):
    return bool(re.match(r"[A-Za-z0-9]", t))


def _content_ok(w, first, prev_ordinal):
    """May word w (lowercase) continue / start a noun phrase?"""
    if w in DEF_DETS or w in NEUTRAL_DETS or w in ("a", "an"):
        return False
    if w in PREPS or w in CONJ_ETC:
        return False
    if w.isdigit():
        return False
    if first or prev_ordinal:
        return True
    if "-" in w and not w.endswith("-"):
        return True  # hyphenated compounds are prenominal modifiers ("computer-readable")
    if w in POSTADJ:
        return False
    if w.endswith("ly") and len(w) > 4 and w not in LY_NOUNS:
        return False
    if w.endswith("ing") and len(w) > 4 and w not in ING_NOUNS:
        return False
    if w.endswith("ed") and len(w) > 4 and w not in ED_NOUNS:
        return False
    if (w.endswith("able") or w.endswith("ible")) and w not in ABLE_NOUNS:
        return False
    if w in VERB_PURE:
        return False
    if (w.endswith("s") and w[:-1] in VERB_PURE) or (w.endswith("es") and w[:-2] in VERB_PURE) or \
            (w.endswith("ies") and w[:-3] + "y" in VERB_PURE):
        return False
    return True


def _bare_start_ok(w):
    if not _content_ok(w, False, False):
        return False
    if w in NUMBER_WORDS or w in VERB_3P:
        return False
    return True


def _ambig_stem(w):
    """The AMBIG_VERBS stem of a third-person form ("matches" -> "match"), else None."""
    if w.endswith("ies") and (w[:-3] + "y") in AMBIG_VERBS:
        return w[:-3] + "y"
    if w.endswith("es") and w[:-2] in AMBIG_VERBS:
        return w[:-2]
    if w.endswith("s") and w[:-1] in AMBIG_VERBS:
        return w[:-1]
    return None


def _verb_break(low, k):
    """True when token k, inside a noun phrase that already has a word, is a third-person verb that
    ends the phrase ("the fingerprint matches the spectrum", "the controller signals a fault")."""
    w = low[k]
    if w in VERB_3P:
        return True
    if _ambig_stem(w) is None:
        return False
    nxt = low[k + 1] if k + 1 < len(low) else ""
    if nxt in NP_FOLLOWERS or nxt.isdigit() or nxt in NUMBER_WORDS:
        return True
    # a plain noun follows ("the timer counts pulses"): not a verb, preposition, conjunction, or punctuation
    return bool(re.match(r"[a-z]", nxt)) and not verbish(nxt) and nxt not in DEF_DETS and \
        _ambig_stem(nxt) is None and nxt not in VERB_3P


def _gerund_mod(low, k, words):
    """True when an -ing word mid-phrase modifies the noun after it ("an initial heating period")."""
    w = low[k]
    if not words or not w.endswith("ing") or k + 1 >= len(low):
        return False
    prev = words[-1].lower()
    if not (prev in ADJ_WORDS or prev in ORDINALS or (prev.endswith(ADJ_SUFFIXES) and len(prev) > 4)):
        return False
    nxt = low[k + 1]
    return bool(re.match(r"[a-z]", nxt)) and _content_ok(nxt, False, False) and not _verb_break(low, k + 1)


def chunk(text):
    """Split claim text into noun-phrase chunks.
    Each chunk: {det, words, start, end, number, next, prev}. det is
    'the' (definite reference), 'a' (explicit introduction), 'quant' (plural
    introduction), 'any' (at least one / one or more), 'neutral', or 'bare'."""
    toks = tokenize(text)
    low = [t.lower() for t in toks]
    n = len(toks)
    chunks = []
    i = 0
    prev_tok = ""
    while i < n:
        t = low[i]
        # claim references: skip "claim 3", "claims 1-3", "claim 1 or 2"
        if t in ("claim", "claims"):
            j = i + 1
            while j < n and (low[j].isdigit() or low[j] in (",", "or", "and", "to", "through", "-",
                                                             "–", "claim", "claims")):
                if low[j] in (",", "or", "and") and not (j + 1 < n and (low[j + 1].isdigit() or
                                                                         low[j + 1].startswith("claim"))):
                    break
                j += 1
            i = j
            prev_tok = "claim"
            continue
        det, number, j = None, None, i
        seq3 = " ".join(low[i:i + 3])
        seq4 = " ".join(low[i:i + 4])
        if t in DEF_DETS or t in ("these", "those"):
            det, j = "the", i + 1
            nxt3 = " ".join(low[j:j + 3])
            if nxt3 in ("at least one", "one or more", "two or more") or \
                    " ".join(low[j:j + 3]) == "at least two":
                number, j = "any", j + 3
            elif " ".join(low[j:j + 2]) == "plurality of":
                number, j = "pl", j + 2
        elif seq3 in ("at least one", "one or more"):
            det, number, j = "any", "any", i + 3
        elif seq3 in ("at least two", "two or more") or seq4 in ("a plurality of",):
            det, number, j = "quant", "pl", i + (4 if seq4 == "a plurality of" else 3)
        elif " ".join(low[i:i + 2]) == "plurality of":
            det, number, j = "quant", "pl", i + 2
        elif t in ("a", "an"):
            det, j = "a", i + 1
        elif t == "one" and not (i + 1 < n and low[i + 1] in ("of", "or")):
            det, j = "a", i + 1
        elif (t in NUMBER_WORDS or t.isdigit()) and t != "one" and prev_tok != "claim":
            det, number, j = "quant", "pl", i + 1
        elif t in NEUTRAL_DETS:
            det, j = "neutral", i + 1
        if det is not None:
            words, k, start = [], j, i
            verb_end = False
            while k < n and _is_word(toks[k]):
                w = low[k]
                if words and _verb_break(low, k):
                    verb_end = True
                    break
                if not _content_ok(w, not words, bool(words) and words[-1].lower() in ORDINALS) and \
                        not _gerund_mod(low, k, words):
                    break
                if words and low[k - 1] in MODALS:
                    break
                words.append(toks[k])
                k += 1
            if words:
                chunks.append({"det": det, "words": words, "start": start, "end": k,
                               "number": number, "prev": prev_tok,
                               "next": low[k] if k < n else ""})
                prev_tok = low[k - 1]
                i = k
                if verb_end:   # the verb is not the start of a new noun phrase
                    prev_tok, i = low[k], k + 1
                continue
            prev_tok = t
            i = j if j > i else i + 1
            continue
        if _is_word(toks[i]) and prev_tok not in MODALS and _bare_start_ok(t):
            words, k = [], i
            verb_end = False
            while k < n and _is_word(toks[k]):
                w = low[k]
                if words and _verb_break(low, k):
                    verb_end = True
                    break
                if not _content_ok(w, False, bool(words) and words[-1].lower() in ORDINALS) and \
                        not _gerund_mod(low, k, words):
                    break
                words.append(toks[k])
                k += 1
            if words:
                chunks.append({"det": "bare", "words": words, "start": i, "end": k,
                               "number": None, "prev": prev_tok,
                               "next": low[k] if k < n else ""})
                prev_tok = low[k - 1]
                i = k
                if verb_end:
                    prev_tok, i = low[k], k + 1
                continue
        prev_tok = t
        i += 1
    # distribute "a first and a second light", "first, second, and third sensors"
    for idx, c in enumerate(chunks):
        if not all(w.lower() in ORDINALS for w in c["words"]):
            continue
        for nxt in chunks[idx + 1:idx + 6]:
            gap = low[c["end"]:nxt["start"]]
            if not gap or any(g not in (",", "and", "or", "a", "an", "the", "said") for g in gap):
                break
            if nxt["words"] and nxt["words"][0].lower() in ORDINALS:
                if len(nxt["words"]) > 1 and not all(w.lower() in ORDINALS for w in nxt["words"]):
                    tail = [w for w in nxt["words"] if w.lower() not in ORDINALS]
                    c["words"] = c["words"] + tail
                    c["distributed"] = True
                    nxt["distributed"] = True
                    if nxt["det"] == "bare" and c["det"] != "bare" and \
                            not any(g in ("a", "an", "the", "said") for g in gap):
                        nxt["det"] = c["det"]
                    break
                continue
            break
    # coordinated modifier: "the top and bottom surfaces" -> also try "top surface"
    for idx, c in enumerate(chunks[:-1]):
        nxt = chunks[idx + 1]
        gap = low[c["end"]:nxt["start"]]
        if len(c["words"]) == 1 and len(nxt["words"]) >= 2 and gap and \
                all(g in (",", "and", "or") for g in gap) and not c.get("distributed"):
            c["coord_words"] = c["words"] + [nxt["words"][-1]]
    for c in chunks:
        j = c["start"] - 1
        c["in_each"] = False
        while j >= 0 and low[j] not in (";", ":"):
            if low[j] in ("each", "every"):
                c["in_each"] = True
                break
            j -= 1
        # "each X comprising a Y": a Y per X (distributive), not a second introduction of one Y. The scope
        # ends at ";" or ":" or at a comma that starts a new clause (", the ...", ", wherein ...").
        c["distributive"] = False
        if c["det"] == "a":
            j = c["start"] - 1
            while j >= 0 and low[j] not in (";", ":"):
                if low[j] == "," and j + 1 < n and low[j + 1] in ("the", "said", "wherein", "whereby", "where"):
                    break
                if low[j] in ("each", "every") and j + 1 < len(low) and _is_word(toks[j + 1]):
                    c["distributive"] = True
                    break
                j -= 1
        c["key"] = norm_words(c["words"])
        c["text"] = " ".join(c["words"])
        if c["number"] is None:
            c["number"] = "pl" if is_plural_word(c["words"][-1]) else "sg"
        elif c["number"] == "any":
            pass
        c["plural_form"] = is_plural_word(c["words"][-1])
        if c.get("distributed"):
            c["number"], c["plural_form"] = "sg", False  # each ordinal names one item
    return chunks


# --------------------------------------------------------------------------- antecedent engine


def _intro_events(chunks):
    out = []
    for c in chunks:
        if c["det"] == "the":
            continue
        out.append(c)
        if c.get("coord_words"):
            extra = dict(c)
            extra["words"] = c["coord_words"]
            extra["key"] = norm_words(c["coord_words"])
            extra["text"] = " ".join(c["coord_words"])
            extra["synthetic"] = True
            out.append(extra)
    return out


def _match(ref_key, intros):
    exact = [e for e in intros if e["key"] == ref_key]
    if exact:
        return "exact", exact
    L = len(ref_key)
    suffix = [e for e in intros if len(e["key"]) > L and e["key"][-L:] == ref_key]
    if suffix:
        keys = set(e["key"] for e in suffix)
        # ordinal-qualified intros (first light / second light) make "the light" ambiguous
        if len(keys) == 1:
            return "suffix", suffix
        return "ambiguous", suffix
    return None, []


def _candidates(words, coord=None):
    """Reference word lists to try: full, verbs trimmed, soft modifiers stripped."""
    ws = list(words)
    cands = [("full", ws)]
    if coord:
        cands.append(("coord", list(coord)))
    t = list(ws)
    while len(t) > 1 and verbish(t[-1]):
        t = t[:-1]
    if t != ws:
        cands.append(("trim", t))
    s = list(t)
    while len(s) > 1 and s[0].lower() in SOFT_MODS:
        s = s[1:]
    if s != t:
        cands.append(("soft", s))
    p = list(s)
    while len(p) > 1 and (p[0].lower().endswith("ed") or p[0].lower().endswith("ing")) and \
            p[0].lower() not in ING_NOUNS and p[0].lower() not in ED_NOUNS:
        p = p[1:]
    if p != s:
        cands.append(("participle", p))
    return cands


def _head(words):
    t = list(words)
    while len(t) > 1 and verbish(t[-1]):
        t = t[:-1]
    return lemma(t[-1].lower()), t


def ancestors(num, by_num, seen=None):
    seen = set() if seen is None else seen
    c = by_num.get(num)
    if c is None:
        return seen
    for d in c.get("deps", []):
        if d in seen or d == num or d not in by_num or d >= num:
            continue
        seen.add(d)
        ancestors(d, by_num, seen)
    return seen


def chain_alternatives(c, by_num):
    """List of (label, set of ancestor claim numbers), one per alternative parent."""
    deps = [d for d in c.get("deps", []) if d in by_num and d < c["num"]]
    if not deps:
        return [("self", set())]
    alts = []
    for d in deps:
        s = {d} | ancestors(d, by_num)
        alts.append(("claim %d" % d, s))
    return alts


def check_antecedents(claims, findings):
    by_num = {c["num"]: c for c in claims if c.get("dep_kind") != "canceled"}
    chunks_by = {}
    for c in by_num.values():
        chunks_by[c["num"]] = chunk(c["text"])
    terms = {}
    intro_by = {n: _intro_events(ch) for n, ch in chunks_by.items()}
    for num in sorted(by_num):
        c = by_num[num]
        chs = chunks_by[num]
        alts = chain_alternatives(c, by_num)
        intro_terms, ref_terms = [], []
        for ch in chs:
            (ref_terms if ch["det"] == "the" else intro_terms).append(ch["text"])
        terms[num] = {"introduces": _dedupe(intro_terms), "refers": _dedupe(ref_terms)}
        reported = set()
        bad = [d for d in c.get("deps", []) if d not in by_num or d >= num]
        if bad:
            findings.append(finding("INFO", "ANTECEDENT", "claim %d" % num,
                                    "antecedent check skipped: fix the dependency on claim %s first."
                                    % ", ".join(str(d) for d in bad)))
            continue
        for ch in chs:
            if ch["det"] != "the":
                continue
            res = _check_one_ref(ch, c, chs, alts, intro_by, by_num)
            if res is None:
                continue
            level, msg, term = res
            if (term, level) in reported:
                continue
            reported.add((term, level))
            findings.append(finding(level, "ANTECEDENT", "claim %d" % num, msg))
        _check_double_intro(c, chs, alts, intro_by, findings)
    return terms, chunks_by


def art(phrase):
    """'a' or 'an' + phrase (vowel-sound heuristic)."""
    w = phrase.strip().lower()
    an = bool(re.match(r"(?:[aeio]|u(?!s[eiu]|ni|r[aeiou]|tens)|hour|honest|led\b|mri|fpga|rf\b|x-)", w))
    return ("an " if an else "a ") + phrase


def _dedupe(xs):
    out = []
    for x in xs:
        if x not in out:
            out.append(x)
    return out


def _check_one_ref(ch, c, chs, alts, intro_by, by_num):
    words = ch["words"]
    lw = [w.lower() for w in words]
    num = c["num"]
    if lw[0] in SKIP_FIRST:
        return None
    if all(w in ORDINALS or w in NUMBER_WORDS for w in lw):
        return None
    if lw[0] in ("step", "steps") and ch["next"] == "of":
        return None
    if lw[-1] == "group" and ch["next"] in ("consisting", "comprising"):
        return None
    term = " ".join(words)
    own_before = [e for e in intro_by[num] if e["end"] <= ch["start"]]
    own_after = [e for e in intro_by[num] if e["start"] >= ch["end"]]
    cands = _candidates(words, ch.get("coord_words"))
    alt_results = []
    for label, anc in alts:
        pool = list(own_before)
        for a in sorted(anc):
            pool.extend(intro_by.get(a, []))
        best = None
        for kind, cw in cands:
            mk, hits = _match(norm_words(cw), pool)
            if mk in ("exact", "suffix"):
                best = ("ok", kind, hits, cw)
                break
            if mk == "ambiguous" and (ch["plural_form"] or ch["number"] in ("pl", "any")):
                best = ("ok", "collective", hits, cw)  # "the sensors" -> first and second sensors
                break
            if mk == "ambiguous" and best is None:
                best = ("ambiguous", kind, hits, cw)
        alt_results.append((label, best))
    oks = [(lab, b) for lab, b in alt_results if b and b[0] == "ok"]
    if oks and len(oks) == len(alt_results):
        # number agreement
        lab, b = oks[0]
        kind, hits, cw = b[1], b[2], b[3]
        if kind == "participle":
            return ("WARN", '"the %s": only "%s" is introduced; the modifier "%s" has no antecedent. '
                    'Suggest "the %s" or introduce "%s" (MPEP 2173.05(e)).'
                    % (term, " ".join(cw), words[0], " ".join(cw), art(term)), term)
        ref_pl = ch["plural_form"] or ch["number"] == "pl"
        if ch["number"] == "any" or kind in ("coord", "collective") or ch.get("distributed"):
            return None
        nums = set(h["number"] for h in hits)
        if ref_pl and nums == {"sg"} and not any(h["plural_form"] or h.get("in_each") for h in hits):
            return ("WARN", '"the %s" (plural) refers back to a single introduced "%s" (MPEP 2173.05(e)). '
                    'Introduce "a plurality of %s" or use the singular.' % (term, hits[0]["text"], term), term)
        if not ref_pl and nums <= {"pl"} and all(h["plural_form"] or h["number"] == "pl" for h in hits):
            return ("WARN", '"the %s" (singular) refers to a plurality ("%s"); which one is unclear '
                    '(MPEP 2173.05(e)). Suggest "each %s" or "a %s of the plurality of %s".'
                    % (term, hits[0]["text"], term, term, hits[0]["text"]), term)
        if not ref_pl and nums <= {"any"} and all(h["number"] == "any" for h in hits):
            return ("WARN", '"the %s" refers to "at least one / one or more %s"; suggest "the at least '
                    'one %s" (or "the one or more %s") to match (MPEP 2173.05(e)).'
                    % (term, hits[0]["text"], term, term), term)
        return None
    if oks:
        missing = [lab for lab, b in alt_results if not (b and b[0] == "ok")]
        return ("WARN", '"the %s" has antecedent basis through %s but not through %s of this multiple '
                'dependent claim (MPEP 2173.05(e); 608.01(n)).'
                % (term, ", ".join(l for l, _ in oks), ", ".join(missing)), term)
    ambs = [b for _, b in alt_results if b and b[0] == "ambiguous"]
    if ambs:
        opts = sorted(set(h["text"] for h in ambs[0][2]))
        return ("WARN", '"the %s" could refer to more than one introduced term (%s); name it fully '
                '(MPEP 2173.05(e)).' % (term, "; ".join('"%s"' % o for o in opts[:4])), term)
    # nothing in the chain matches
    head, trimmed = _head(words)
    tterm = " ".join(trimmed)
    if ch["start"] <= 1 and c.get("dep_kind") in ("single", "multiple"):
        parents = ", ".join(str(d) for d in c.get("deps", []))
        return ("BLOCK", 'dependent claim preamble "The %s" does not match the subject of claim %s; a dependent '
                'claim must refer back to the same claimed subject (35 USC 112(d); MPEP 608.01(n)).'
                % (tterm, parents), tterm)
    if len(lw) == 1 and lw[0].endswith("ing"):
        chain_txt = " ".join(by_num[a]["text"] for _, anc in alts for a in anc if a in by_num)
        if re.search(r"\b%s\b" % re.escape(lw[0]), (chain_txt + " " + c["text"][:0]).lower()) or \
                re.search(r"\b%s\b" % re.escape(lw[0]), " ".join(
                    t for t in tokenize(c["text"])[:ch["start"]]).lower()):
            return None  # "the forming" refers to the recited step
    for kind, cw in cands:
        mk, _ = _match(norm_words(cw), own_after)
        if mk in ("exact", "suffix", "ambiguous"):
            return ("BLOCK", '"the %s" is used before it is introduced later in the same claim; move '
                    '"%s" ahead of this use (MPEP 2173.05(e)).' % (tterm, art(tterm)), tterm)
    elsewhere = []
    for other, evs in intro_by.items():
        if other == num:
            continue
        for kind, cw in cands:
            mk, _ = _match(norm_words(cw), evs)
            if mk in ("exact", "suffix"):
                elsewhere.append(other)
                break
    if ch["next"] == "of" and (head in INHERENT_OF or " ".join(w.lower() for w in trimmed) in INHERENT_OF):
        return ("INFO", '"the %s of ..." treated as an inherent property (MPEP 2173.05(e)); '
                'confirm it is inherent to the object named.' % tterm, tterm)
    if head in UNIQUE_THINGS and len(trimmed) == 1:
        if head == "user":
            return ("WARN", '"the user" has no antecedent; introduce "a user" (MPEP 2173.05(e)).',
                    tterm)
        return ("INFO", '"the %s" treated as a unique or well-known thing; no antecedent needed.'
                % tterm, tterm)
    chain = set()
    for _, anc in alts:
        chain |= anc
    pools = []
    for _, anc in alts:
        pool = list(own_before)
        for a2 in sorted(anc):
            pool.extend(intro_by.get(a2, []))
        pools.append(pool)
    # a proper prefix matches: the rest is probably a verb absorbed by the chunker ("the processor tracks")
    for k in range(len(words) - 1, 0, -1):
        pre = words[:k]
        rest = [w.lower() for w in words[k:]]
        if all(_match(norm_words(pre), pl)[0] in ("exact", "suffix") for pl in pools):
            if len(rest) == 1 and rest[0].endswith("s") and not rest[0].endswith("ss") and \
                    not is_plural_word(pre[-1]):
                return None
            return ("WARN", '"the %s": "%s" is introduced but "%s" is not; if "%s" is a verb this is a '
                    'parsing artifact, otherwise introduce "%s" (MPEP 2173.05(e)).'
                    % (term, " ".join(pre), term, " ".join(words[k:]), art(term)), term)
    verb = _nominal_source(head, c, chain, by_num)
    if verb:
        return ("WARN", '"the %s" has only an implicit antecedent ("%s"); examiners often object. Consider '
                '"%s" at first use or rewording (MPEP 2173.05(e)).' % (tterm, verb, art(tterm)), tterm)
    head_pool = list(own_before) + list(own_after)
    for a in chain:
        head_pool.extend(intro_by.get(a, []))
    head_seen = [e for e in head_pool if e["key"] and e["key"][-1] == head]
    if elsewhere:
        others = sorted(set(elsewhere) - chain)
        if others:
            return ("BLOCK", '"the %s" lacks antecedent basis: it is introduced in claim %s, which is not '
                    'in claim %d\'s dependency chain. Change the dependency or introduce "%s" '
                    '(MPEP 2173.05(e)).' % (tterm, ", ".join(str(o) for o in others[:3]), num, art(tterm)),
                    tterm)
    if head_seen:
        intro_txt = sorted(set(e["text"] for e in head_seen))[:3]
        return ("WARN", '"the %s" does not match an introduced term exactly (introduced: %s). Use the '
                'same words or introduce "%s" (MPEP 2173.05(e)).'
                % (tterm, ", ".join('"%s"' % x for x in intro_txt), art(tterm)), tterm)
    if ch["next"] == "of":
        return ("WARN", '"the %s of ..." has no antecedent; acceptable only if it is an inherent part or '
                'property of the following object (MPEP 2173.05(e)); otherwise introduce "%s".'
                % (tterm, art(tterm)), tterm)
    if words[0].lower() in SOFT_MODS or len(cands) > 2:
        return ("WARN", '"the %s" has no clear antecedent (MPEP 2173.05(e)); introduce "%s" or reword.'
                % (tterm, art(tterm)), tterm)
    return ("BLOCK", '"the %s" lacks antecedent basis: no "a/an %s" earlier in claim %d or in the claims '
            'it depends on (35 USC 112(b); MPEP 2173.05(e)). Suggest introducing "%s".'
            % (tterm, tterm, num, art(tterm)), tterm)


NOMINAL_SUFFIXES = ("isation", "ization", "ation", "ition", "ssion", "ison", "ion", "ment", "ance",
                    "ence", "al", "ure", "ing")


def _nominal_source(head, c, chain, by_num):
    """If head is a nominalization of a verb used earlier ("comparison" <- "compare"), return that word."""
    stems = []
    for suf in NOMINAL_SUFFIXES:
        if head.endswith(suf) and len(head) - len(suf) >= 4:
            stems.append(head[:-len(suf)])
    if not stems:
        return None
    texts = [by_num[a]["text"] for a in sorted(chain) if a in by_num] + [c["text"]]
    words = set(re.findall(r"[a-z]+", " ".join(texts).lower()))
    words.discard(head)
    words.discard(head + "s")
    for st in sorted(stems, key=len, reverse=True):
        for w in sorted(words):
            if w.startswith(st) and w != head and not w.startswith(head):
                return w
    return None


def _check_double_intro(c, chs, alts, intro_by, findings):
    num = c["num"]
    explicit = [e for e in chs if e["det"] == "a" and e["next"] != "of" and not e.get("distributed")
                and not e.get("distributive")]
    seen = set()
    # within this claim
    for i, e in enumerate(explicit):
        for f in explicit[i + 1:]:
            if f["key"] == e["key"] and e["key"] not in seen:
                later_ref = [r for r in chs if r["det"] == "the" and r["start"] > f["end"] and
                             (r["key"] == e["key"] or (len(r["key"]) < len(e["key"]) and
                                                       e["key"][-len(r["key"]):] == r["key"]))]
                seen.add(e["key"])
                lvl = "WARN" if later_ref else "INFO"
                findings.append(finding(lvl, "DOUBLE_INTRO", "claim %d" % num,
                                        '"%s" is introduced twice in claim %d%s; if the same element, '
                                        'use "the %s"; if different, use "a first/second %s".'
                                        % (art(e["text"]), num, " and later referred to as \"the ...\"" if later_ref
                                           else "", e["text"], e["text"])))
    # against the chain
    chain = set()
    for _, anc in alts:
        chain |= anc
    for e in explicit:
        if e["key"] in seen:
            continue
        for a in sorted(chain):
            prev = [p for p in intro_by.get(a, []) if p["det"] in ("a", "quant", "any") and p["key"] == e["key"]
                    and not p.get("distributive")]
            if prev:
                seen.add(e["key"])
                findings.append(finding("WARN", "DOUBLE_INTRO", "claim %d" % num,
                                        '"%s" was already introduced in claim %d; use "the %s" if it is '
                                        'the same element, or "a second %s" if it is another one.'
                                        % (art(e["text"]), a, e["text"], e["text"])))
                break


# --------------------------------------------------------------------------- other checks

ABBREV = {"fig", "figs", "e.g", "i.e", "etc", "approx", "no", "nos", "vs", "inc", "co", "ltd",
          "wt", "mol", "ca", "cf", "al", "u.s", "ser", "dr", "st", "deg", "min", "max", "sec",
          "hr", "ml", "mg", "mm", "cm", "nm", "kg", "pat", "pub", "corp", "jr", "sr", "eq",
          "ref", "vol", "pp", "ph", "temp", "avg", "std", "dia", "ft", "lb", "lbs", "oz", "in",
          "mt", "rev", "ver", "v"}


def check_one_sentence(c, findings):
    text = c["text"]
    num = c["num"]
    where = "claim %d" % num
    if not text:
        findings.append(finding("BLOCK", "ONE_SENTENCE", where, "claim has no text (37 CFR 1.75(a))."))
        return
    if not re.match(r"^[\"'(]?[A-Z0-9]", text):
        findings.append(finding("WARN", "ONE_SENTENCE", where,
                                "claim should begin with a capital letter (MPEP 608.01(m))."))
    t = text.rstrip()
    if t.endswith(".."):
        findings.append(finding("BLOCK", "ONE_SENTENCE", where,
                                "claim ends with more than one period (MPEP 608.01(m))."))
    elif not t.endswith("."):
        findings.append(finding("BLOCK", "ONE_SENTENCE", where,
                                'claim must end with a single period; it ends with "%s" (MPEP 608.01(m)).'
                                % t[-1:]))
    body = t[:-1] if t.endswith(".") else t
    for m in re.finditer(r"([A-Za-z0-9.\-]*)\.(?=\s+(\S))", body):
        tok = m.group(1).lower().strip(".")
        nxt = m.group(2)
        if tok in ABBREV or len(tok) == 1 or re.fullmatch(r"(?:[a-z]\.)+[a-z]?", tok or "x"):
            continue
        lvl = "BLOCK" if nxt[:1].isupper() else "WARN"
        findings.append(finding(lvl, "ONE_SENTENCE", where,
                                'internal period after "%s." -- a claim is one sentence; periods only in '
                                'abbreviations (MPEP 608.01(m); Fressola v. Manbeck).' % m.group(1)))
    if re.search(r"[?!]", body):
        findings.append(finding("WARN", "ONE_SENTENCE", where, 'claim contains "?" or "!" (MPEP 608.01(m)).'))


def _subject_span(c):
    """Character span of the claim subject (preamble up to the transition)."""
    t = c["text"]
    m = re.search(r"\b(comprising|comprises|consisting|including|includes|having|wherein|"
                  r"characterized|the improvement)\b|[:;]", t, re.I)
    end = m.start() if m else min(len(t), 80)
    return 0, end


def check_nonce(c, findings):
    text = c["text"]
    num = c["num"]
    where = "claim %d" % num
    seen = set()
    for m in re.finditer(r"\b(means|step)\s+(for|to)\b", text, re.I):
        pre = text[max(0, m.start() - 9):m.start()].lower()
        if "by " in pre[-4:] or "by means" in (pre + m.group(1).lower()):
            continue
        if m.group(1).lower() == "step" and m.group(2).lower() == "to":
            continue
        key = m.group(0).lower()
        if key in seen:
            continue
        seen.add(key)
        kind = "means-plus-function" if m.group(1).lower() == "means" else "step-plus-function"
        findings.append(finding("WARN", "NONCE_112F", where,
                                '"%s" presumptively invokes 35 USC 112(f) (%s): the claim covers only the '
                                'structure (or acts) in the spec and equivalents; computer functions need a '
                                'disclosed algorithm (MPEP 2181; Williamson v. Citrix, 792 F.3d 1339 (Fed. '
                                'Cir. 2015) (en banc); Aristocrat).' % (m.group(0), kind)))
    s0, s1 = _subject_span(c)
    pat = re.compile(r"\b((?:[\w-]+\s+){0,2}?)(%s)\b(\s*\(\s*\d+[a-z]?\s*\))?\s+(for|configured\s+to|"
                     r"operable\s+to|adapted\s+to|programmed\s+to|arranged\s+to|that\s+is\s+configured\s+to|"
                     r"being\s+configured\s+to)\b" % "|".join(sorted(NONCE, key=len, reverse=True)), re.I)
    for m in pat.finditer(text):
        if m.start(2) < s1 and c.get("dep_kind") == "independent":
            continue  # claim subject ("A system for ...") is not a claim element
        if c.get("dep_kind") in ("single", "multiple") and m.start(2) < s1 and \
                re.match(r"^(the|an?)\s+", text, re.I) and m.start(2) < 60:
            continue
        if m.group(4).lower() == "for" and re.match(r"\s*example\b", text[m.end():], re.I):
            continue
        mods = m.group(1).strip().lower().split()
        mods = [x for x in mods if x not in ("a", "an", "the", "said", "each", "one", "at", "least")]
        word = m.group(2).lower()
        phrase = (" ".join(mods + [word]) + " " + re.sub(r"\s+", " ", m.group(4).lower())).strip()
        if phrase in seen:
            continue
        seen.add(phrase)
        if word.startswith("circuit"):
            note = ("lower risk: courts often treat \"circuit\" as connoting structure (MPEP 2181(I)(A)), "
                    "but check that the claim or spec gives its structure")
        else:
            note = ("a nonce word plus a function may invoke 35 USC 112(f) (Williamson v. Citrix, 792 F.3d "
                    "1339 (Fed. Cir. 2015) (en banc); MPEP 2181(I)(A)); recite structure (for example "
                    "\"a processor configured to\") or make sure the spec discloses the corresponding "
                    "structure or algorithm")
        findings.append(finding("WARN", "NONCE_112F", where, '"%s": %s.' % (phrase, note)))


INDEF_TERMS = [
    (r"\bsubstantially\b", "relative term of degree; the spec needs a standard for measuring it (MPEP 2173.05(b))"),
    (r"\babout\s+[\d.]", "\"about\" + number; give the tolerance in the spec (MPEP 2173.05(b)(III))"),
    (r"\bapproximately\b", "relative term of degree; give the tolerance in the spec (MPEP 2173.05(b))"),
    (r"\bgenerally\b", "relative term; may be indefinite without a standard in the spec (MPEP 2173.05(b))"),
    (r"\brelatively\b", "relative term; needs a reference point (MPEP 2173.05(b))"),
    (r"\bsufficient(?:ly)?\b", "subjective term; state the threshold (MPEP 2173.05(b))"),
    (r"\b(?:large|small|thin)\b", "relative size term; give a measure or a comparison (MPEP 2173.05(b))"),
    (r"\boptimal(?:ly)?\b|\boptimum\b", "subjective term (MPEP 2173.05(b)(IV))"),
    (r"\buser[- ]friendly\b", "subjective term (MPEP 2173.05(b)(IV))"),
    (r"\baesthetic(?:ally)?\b", "subjective term (MPEP 2173.05(b)(IV))"),
    (r"\b(?:significantly|slightly|considerably)\b", "relative term of degree (MPEP 2173.05(b))"),
    (r"\boptional(?:ly)?\b", "optional language does not limit the claim and can make scope unclear "
                             "(MPEP 2173.05(h); 2111.04)"),
    (r"\bmay\b", "\"may\" is permissive; the limitation may not limit the claim (MPEP 2111.04)"),
    (r"\bcan\b", "\"can\" is permissive; say what the element does (MPEP 2111.04)"),
    (r"\bpreferabl[ye]\b", "preferred language makes scope unclear (MPEP 2173.05(d))"),
    (r"\bsuch as\b", "exemplary language makes scope unclear (MPEP 2173.05(d))"),
    (r"\bfor example\b|\be\.g\.", "exemplary language makes scope unclear (MPEP 2173.05(d))"),
    (r"\bi\.e\.", "\"i.e.\" can be read as limiting or as an example; restate plainly (MPEP 2173.05(d))"),
    (r"\band/or\b", "\"and/or\" may be read as indefinite; recite \"at least one of A or B\" or list "
                    "alternatives (MPEP 2173.05(h))"),
    (r"\b(?:and|or) the like\b|\betc\.?", "open-ended list is indefinite (MPEP 2173.05(d))"),
]
EPONYMS = {"hall", "celsius", "fahrenheit", "kelvin", "gaussian", "gauss", "fourier", "bayesian",
           "euclidean", "newton", "newtonian", "doppler", "peltier", "wheatstone", "bragg", "raman",
           "fresnel", "joule", "ohm", "volt", "ampere", "hertz", "pascal", "coulomb", "faraday", "weber",
           "boolean", "cartesian", "laplace", "laplacian", "kalman", "markov", "poisson", "lorentz",
           "hilbert", "riemann", "monte", "carlo", "levenshtein", "huffman", "hamming", "reed-solomon",
           "ethernet", "internet", "petri", "turing", "venturi", "pitot", "coriolis", "hall-effect",
           "bernoulli", "reynolds", "nyquist", "shannon", "viterbi", "dijkstra", "voronoi", "delaunay",
           "bezier", "phillips", "allen", "luer", "luer-lock", "schottky", "zener", "darlington",
           "cmos", "english", "american", "european", "latin", "roman", "arabic", "gregorian"}
TM_WORDS = {"bluetooth", "wi-fi", "wifi", "velcro", "teflon", "kevlar", "lycra", "plexiglas",
            "plexiglass", "styrofoam", "gore-tex", "lucite", "zigbee", "android", "iphone", "ipad",
            "windows", "excel", "powerpoint", "thunderbolt", "lightning", "post-it", "spandex"}


def check_indefinite(c, findings):
    text = c["text"]
    where = "claim %d" % c["num"]
    seen = set()
    for pat, why in INDEF_TERMS:
        for m in re.finditer(pat, text, re.I):
            k = m.group(0).lower().strip()
            if k in seen:
                continue
            seen.add(k)
            findings.append(finding("WARN", "INDEFINITE", where, '"%s": %s.' % (m.group(0).strip(), why)))
            break
    if re.search("[™®℠]", text):
        findings.append(finding("WARN", "INDEFINITE", where,
                                "trademark symbol in a claim; a trademark identifies a source, not a "
                                "product, and makes the claim indefinite (MPEP 2173.05(u))."))
    flagged = set()
    run = None
    for i, m in enumerate(re.finditer(r"[A-Za-z][A-Za-z0-9\-]*", text)):
        w = m.group(0)
        if i == 0 or re.search(r"[.:;(\"']\s*$", text[:m.start()]):
            continue
        lw = w.lower()
        if lw in DEF_DETS or lw in NEUTRAL_DETS or lw in CONJ_ETC or lw in PREPS or lw in ("a", "an"):
            continue
        brand = lw in TM_WORDS
        camel = bool(re.search(r"[a-z][A-Z]", w)) and not w.isupper() and w not in SCI_TERMS
        capword = bool(re.fullmatch(r"[A-Z][a-z]{2,}(?:-[A-Za-z]+)*", w)) and lw not in ("fig", "figs")
        if lw in EPONYMS or lw.split("-")[0] in EPONYMS:
            continue
        if (brand or camel or capword) and lw not in flagged:
            flagged.add(lw)
            # A run of capitalized words ("Bluetooth Low Energy") is one trade name, not three.
            if run is not None and not text[run["end"]:m.start()].strip():
                run["phrase"] += text[run["end"]:m.end()]
                run["end"] = m.end()
                run["finding"]["message"] = ('"%s" looks like a trademark or trade name; use the generic term '
                                             '(MPEP 2173.05(u)).' % run["phrase"])
                continue
            f = finding("WARN", "INDEFINITE", where,
                        '"%s" looks like a trademark or trade name; use the generic term '
                        '(MPEP 2173.05(u)).' % w)
            findings.append(f)
            run = {"phrase": w, "end": m.end(), "finding": f}
        else:
            run = None


# --------------------------------------------------------------------------- counts & fees


def fee_counts(claims):
    by_num = {c["num"]: c for c in claims}
    active = [c for c in claims if c.get("dep_kind") not in ("canceled",) and c.get("status") != "withdrawn"]
    weights = {}

    def weight(c, depth=0):
        if c["num"] in weights:
            return weights[c["num"]]
        if depth > 50:
            return 1
        if c["dep_kind"] == "independent":
            w = 1
        elif c["dep_kind"] == "multiple":
            w = len([d for d in c["deps"] if d in by_num])  # 37 CFR 1.75(c)
        else:
            p = by_num.get(c["deps"][0]) if c["deps"] else None
            if p is not None and p.get("dep_kind") in ("multiple", "single") and p["num"] < c["num"] \
                    and _depends_on_multiple(p, by_num):
                w = weight(p, depth + 1)
            else:
                w = 1
        weights[c["num"]] = max(1, w)
        return weights[c["num"]]

    total = 0
    for c in active:
        total += weight(c)
    indep = len([c for c in active if c["dep_kind"] == "independent"])
    multi = [c["num"] for c in active if c["dep_kind"] == "multiple"]
    return {"claims_listed": len(claims), "active": len(active), "independent": indep,
            "total_for_fees": total, "multiple_dependent": multi,
            "excess_independent": max(0, indep - 3), "excess_total": max(0, total - 20),
            "canceled": [c["num"] for c in claims if c.get("dep_kind") == "canceled"],
            "withdrawn": [c["num"] for c in claims if c.get("status") == "withdrawn"],
            "weights": {str(k): v for k, v in sorted(weights.items())}}


def _depends_on_multiple(c, by_num, depth=0):
    if depth > 50:
        return False
    if c.get("dep_kind") == "multiple":
        return True
    if c.get("dep_kind") == "single" and c["deps"]:
        p = by_num.get(c["deps"][0])
        if p is not None and p["num"] < c["num"]:
            return _depends_on_multiple(p, by_num, depth + 1)
    return False


def load_fee_table(path=FEES_MD):
    """Read the ```json block holding {"fees": {...}} from references/fees.md, if present."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    for m in re.finditer(r"```json[^\n]*\n(.*?)```", text, re.S):
        info = text[m.start():text.find("\n", m.start())]
        try:
            obj = json.loads(m.group(1))
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("fees"), dict):
            return obj["fees"]
        if "fees" in info and isinstance(obj, dict):
            return obj
    return None


def fee_estimate(counts, entity, table):
    if not table or entity not in ("large", "small", "micro"):
        return None

    def amt(key):
        row = table.get(key)
        if isinstance(row, dict) and isinstance(row.get(entity), (int, float)):
            return row[entity], row.get("cfr")
        return None, None

    out = {"entity": entity, "items": []}
    a, cfr = amt("excess_independent_claim")
    if a is not None and counts["excess_independent"]:
        out["items"].append({"fee": "excess independent claims", "count": counts["excess_independent"],
                             "each": a, "amount": a * counts["excess_independent"], "cfr": cfr})
    a, cfr = amt("excess_total_claim")
    if a is not None and counts["excess_total"]:
        out["items"].append({"fee": "excess total claims", "count": counts["excess_total"], "each": a,
                             "amount": a * counts["excess_total"], "cfr": cfr})
    a, cfr = amt("multiple_dependent_claim")
    if a is not None and counts["multiple_dependent"]:
        out["items"].append({"fee": "multiple dependent claim (once per application)", "count": 1,
                             "each": a, "amount": a, "cfr": cfr})
    out["total"] = sum(i["amount"] for i in out["items"])
    meta = table.get("_meta") or {}
    out["last_verified"] = meta.get("last_verified")
    return out


# --------------------------------------------------------------------------- tree


def dep_tree(claims):
    by_num = {c["num"]: c for c in claims}
    children = {}
    for c in claims:
        for d in c.get("deps", []):
            if d in by_num and d < c["num"]:
                children.setdefault(d, []).append(c["num"])
    lines = []

    def label(c, parent=None):
        s = str(c["num"])
        if c.get("dep_kind") == "independent":
            s += " (independent, %s)" % category(c["text"])
        if c.get("dep_kind") == "multiple":
            s += " [multiple: %s]" % ", ".join(str(d) for d in c["deps"])
        if c.get("status") in ("withdrawn",):
            s += " (withdrawn)"
        bad = [d for d in c.get("deps", []) if d not in by_num or d >= c["num"]]
        if bad:
            s += " !-> %s" % ", ".join(str(d) for d in bad)
        return s

    def walk(num, prefix, last, depth):
        c = by_num[num]
        conn = "`-- " if last else "|-- "
        lines.append(prefix + conn + label(c))
        if depth > 40:
            return
        kids = children.get(num, [])
        for i, k in enumerate(kids):
            walk(k, prefix + ("    " if last else "|   "), i == len(kids) - 1, depth + 1)

    for c in claims:
        if c.get("dep_kind") == "canceled":
            lines.append("%d (canceled)" % c["num"])
            continue
        valid = [d for d in c.get("deps", []) if d in by_num and d < c["num"]]
        if not valid:
            lines.append(label(c))
            kids = children.get(c["num"], [])
            for i, k in enumerate(kids):
                walk(k, "", i == len(kids) - 1, 1)
    return lines


# --------------------------------------------------------------------------- main checks


def check_structure(claims, findings):
    nums = [c["num"] for c in claims]
    by_num = {}
    for c in claims:
        if c["num"] in by_num:
            findings.append(finding("BLOCK", "CLAIM_NUMBERING", "claim %d" % c["num"],
                                    "claim number %d is used twice (37 CFR 1.126)." % c["num"]))
        by_num.setdefault(c["num"], c)
    expected = 1
    for i, n in enumerate(nums):
        if n != expected:
            if i == 0:
                msg = "claims must be numbered from 1; first claim is %d (37 CFR 1.126)." % n
            elif n > expected:
                msg = ("claim numbering skips from %d to %d; number consecutively and list canceled "
                       "claims (37 CFR 1.126, 1.121(c))." % (expected - 1, n))
            else:
                msg = "claim %d is out of order after claim %d (37 CFR 1.126)." % (n, nums[i - 1])
            findings.append(finding("BLOCK", "CLAIM_NUMBERING", "claim %d" % n, msg))
            expected = max(expected, n) + 1
        else:
            expected += 1
    for c in claims:
        if c.get("dep_kind") in ("canceled",):
            continue
        where = "claim %d" % c["num"]
        for d in c.get("deps", []):
            if d >= c["num"]:
                findings.append(finding("BLOCK", "DEP_FORWARD", where,
                                        "claim %d depends on claim %d, which is not a preceding claim "
                                        "(37 CFR 1.75(c); MPEP 608.01(n)(IV))." % (c["num"], d)))
            elif d not in by_num:
                findings.append(finding("BLOCK", "DEP_MISSING", where,
                                        "claim %d depends on claim %d, which does not exist "
                                        "(35 USC 112(d); 37 CFR 1.75(c))." % (c["num"], d)))
            elif by_num[d].get("dep_kind") == "canceled":
                findings.append(finding("BLOCK", "DEP_MISSING", where,
                                        "claim %d depends on canceled claim %d (35 USC 112(d))." % (c["num"], d)))
        if c.get("dep_kind") == "multiple":
            msg = ("multiple dependent claim (refers to claims %s). Each counts as %d claims for fees "
                   "and adds the one-time multiple dependent claim fee (35 USC 112(e); 37 CFR 1.75(c), "
                   "1.16(j)). Consider separate single-dependent claims."
                   % (", ".join(str(d) for d in c["deps"]), len(c["deps"])))
            findings.append(finding("WARN", "MULTI_DEP", where, msg))
            if "and" in c.get("conj", []) and "or" not in c.get("conj", []):
                findings.append(finding("BLOCK", "MULTI_DEP_FORM", where,
                                        'a multiple dependent claim must refer to the other claims in the '
                                        'alternative only ("claim 1 or 2"), not "and" (37 CFR 1.75(c); '
                                        'MPEP 608.01(n)(I)).'))
            for d in c["deps"]:
                p = by_num.get(d)
                if p is None or d >= c["num"]:
                    continue
                if p.get("dep_kind") == "multiple":
                    findings.append(finding("BLOCK", "MULTI_ON_MULTI", where,
                                            "multiple dependent claim %d depends on claim %d, which is itself "
                                            "a multiple dependent claim (35 USC 112(e); 37 CFR 1.75(c))."
                                            % (c["num"], d)))
                elif _depends_on_multiple(p, by_num):
                    findings.append(finding("BLOCK", "MULTI_ON_MULTI", where,
                                            "multiple dependent claim %d depends on claim %d, which depends "
                                            "from a multiple dependent claim; a multiple dependent claim may "
                                            "not serve as a basis for another, directly or indirectly "
                                            "(37 CFR 1.75(c); MPEP 608.01(n))." % (c["num"], d)))


def check_term_support(claims, chunks_by, spec_text, findings):
    norm = norm_text_for_match(spec_text)
    missing = {}
    for c in claims:
        if c["num"] not in chunks_by:
            continue
        for ch in chunks_by[c["num"]]:
            if ch["det"] == "the":
                continue
            if ch["det"] == "bare" and ch["prev"] not in (
                    "comprising", "including", "having", "storing", "containing", "of", "from", "with",
                    "by", "on", ":", ";", "include", "includes", "comprises", "comprise", "store",
                    "stores", "for", "in"):
                continue
            words = [w for w in ch["words"] if w.lower() not in ORDINALS] or ch["words"]
            if term_in_text(words, norm):
                continue
            _, trimmed = _head(words)
            if term_in_text(trimmed, norm):
                continue
            k = " ".join(w.lower() for w in trimmed)
            missing.setdefault(k, []).append(c["num"])
    for term, nums in missing.items():
        findings.append(finding("WARN", "TERM_SUPPORT", "claim %d" % nums[0],
                                '"%s" (claims %s) does not appear in the specification; claim terms need '
                                'clear support or antecedent basis in the description (35 USC 112(a)/(b); '
                                '37 CFR 1.75(d)(1); MPEP 608.01(o)).'
                                % (term, ", ".join(str(n) for n in sorted(set(nums))[:6]))))
    return sorted(missing)


def claim_terms(claims):
    """Public helper for check_spec / check_package: list of (claim, term words) introduced."""
    out = []
    for c in claims:
        if c.get("dep_kind") == "canceled":
            continue
        for ch in chunk(c["text"]):
            if ch["det"] in ("a", "quant", "any") or (ch["det"] == "bare" and ch["prev"] in (
                    "comprising", "including", "having", "storing", ":", ";", "of")):
                words = [w for w in ch["words"] if w.lower() not in ORDINALS] or ch["words"]
                _, trimmed = _head(words)
                out.append((c["num"], trimmed))
    return out


def extract_spec_text(spec_text):
    """Drop CLAIMS and ABSTRACT sections when checking claim support in the description."""
    out, skip = [], False
    for line in spec_text.splitlines():
        m = re.match(r"^\s{0,3}#{1,6}\s+(.*)$", line)
        if m:
            h = m.group(1).strip().upper()
            skip = h.startswith("CLAIM") or h.startswith("WHAT IS CLAIMED") or h.startswith("ABSTRACT")
            continue
        if not skip:
            out.append(line)
    return "\n".join(out)


DEFAULTS = {"claims": None, "spec": None, "entity": None, "dir": "patent", "json": False,
            "no_audit": False, "text": None}


def run(args):
    a = to_namespace(args, DEFAULTS)
    if a.text is not None:
        text, path = a.text, "<text>"
    else:
        path = a.claims or os.path.join(a.dir, "draft", "claims.md")
        if not os.path.exists(path):
            raise UsageError("claims file not found: %s" % path)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    claims = parse_claims(text)
    if not claims:
        raise UsageError("no numbered claims found in %s" % path)
    findings, run_list, skipped = [], [], []
    check_structure(claims, findings)
    run_list += ["CLAIM_NUMBERING", "DEPENDENCIES", "MULTI_DEP"]
    active = [c for c in claims if c.get("dep_kind") != "canceled"]
    for c in active:
        check_one_sentence(c, findings)
    run_list.append("ONE_SENTENCE")
    terms, chunks_by = check_antecedents(claims, findings)
    run_list += ["ANTECEDENT", "DOUBLE_INTRO"]
    for c in active:
        check_nonce(c, findings)
    run_list.append("NONCE_112F")
    for c in active:
        check_indefinite(c, findings)
    run_list.append("INDEFINITE")
    unsupported = None
    if a.spec:
        if not os.path.exists(a.spec):
            raise UsageError("spec file not found: %s" % a.spec)
        with open(a.spec, encoding="utf-8") as fh:
            spec_text = extract_spec_text(fh.read())
        unsupported = check_term_support(active, chunks_by, spec_text, findings)
        run_list.append("TERM_SUPPORT")
    else:
        skipped.append({"check": "TERM_SUPPORT", "reason": "no --spec given"})
    counts = fee_counts(claims)
    run_list.append("COUNTS")
    table = load_fee_table()
    fees = fee_estimate(counts, a.entity, table) if a.entity else None
    if a.entity and fees is None:
        skipped.append({"check": "FEE_AMOUNTS", "reason": "references/fees.md fee table not readable"})
    elif not a.entity:
        skipped.append({"check": "FEE_AMOUNTS", "reason": "no --entity given (counts only)"})
    if counts["excess_independent"] or counts["excess_total"]:
        findings.append(finding("INFO", "COUNTS", "claims",
                                "%d independent (excess %d over 3) and %d total for fees (excess %d over 20) "
                                "(37 CFR 1.16(h), (i))." % (counts["independent"], counts["excess_independent"],
                                                            counts["total_for_fees"], counts["excess_total"])))
    order = {"BLOCK": 0, "WARN": 1, "INFO": 2}

    def sort_key(f):
        m = re.search(r"\d+", f["where"])
        return (int(m.group()) if m else 0, order.get(f["level"], 3))

    findings.sort(key=sort_key)
    blocks = sum(1 for f in findings if f["level"] == "BLOCK")
    warns = sum(1 for f in findings if f["level"] == "WARN")
    tree = dep_tree(claims)
    res = {
        "ok": blocks == 0, "exit_code": 1 if blocks else 0, "file": path,
        "findings": findings, "checks_run": run_list, "checks_skipped": skipped,
        "summary": {"blocking": blocks, "warnings": warns,
                    "info": sum(1 for f in findings if f["level"] == "INFO"),
                    "counts": counts, "fees": fees,
                    "categories": sorted(set(category(c["text"]) for c in active if c["dep_kind"] == "independent")),
                    "unsupported_terms": unsupported},
        "claims": [{"num": c["num"], "status": c.get("status"), "dep_kind": c.get("dep_kind"),
                    "deps": c.get("deps", []), "line": c.get("line")} for c in claims],
        "tree": tree,
        "terms": {str(k): v for k, v in terms.items()},
    }
    if a.text is None:
        audit(a.dir, "check", no_audit=a.no_audit or not os.path.isdir(a.dir), script=SCRIPT,
              file=path, blocking=blocks, warnings=warns)
    return res


def render_text(res):
    out = ["check_claims.py  %s" % res.get("file", "")]
    for f in res["findings"]:
        out.append("%-5s  %s  %s  %s" % (f["level"], f["code"], f["where"], f["message"]))
    out.append("")
    out.append("Checks run: %s" % ", ".join(res["checks_run"]))
    for s in res["checks_skipped"]:
        out.append("Check skipped: %s (%s)" % (s["check"], s["reason"]))
    c = res["summary"]["counts"]
    out.append("")
    out.append("Counts: %d independent, %d total for fees (%d active claims listed)%s"
               % (c["independent"], c["total_for_fees"], c["active"],
                  "; multiple dependent: %s" % ", ".join(map(str, c["multiple_dependent"]))
                  if c["multiple_dependent"] else ""))
    out.append("Excess: %d independent over 3, %d total over 20" % (c["excess_independent"], c["excess_total"]))
    fees = res["summary"].get("fees")
    if fees:
        for it in fees["items"]:
            out.append("  fee: %s x%d @ $%s = $%s (%s)" % (it["fee"], it["count"], it["each"], it["amount"],
                                                       it.get("cfr")))
        out.append("  excess-claim fees (%s entity): $%s (fees.md last_verified %s)"
                   % (fees["entity"], fees["total"], fees.get("last_verified")))
    out.append("")
    out.append("Dependency tree:")
    out.extend("  " + ln for ln in res["tree"])
    out.append("")
    out.append("Terms per claim:")
    for k, v in res["terms"].items():
        out.append("  %s  introduces: %s" % (k, "; ".join(v["introduces"]) or "-"))
        if v["refers"]:
            out.append("  %s  refers to:  %s" % (" " * len(k), "; ".join(v["refers"])))
    s = res["summary"]
    out.append("")
    out.append("Summary: %d BLOCK, %d WARN, %d INFO" % (s["blocking"], s["warnings"], s["info"]))
    if res.get("error"):
        out.append("ERROR: %s" % res["error"])
    return "\n".join(out)


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("claims", nargs="?", help="claims file (default <dir>/draft/claims.md)")
    p.add_argument("--spec", help="spec.md for TERM_SUPPORT")
    p.add_argument("--entity", choices=["large", "small", "micro"], help="fee entity status for excess-claim fees")
    p.add_argument("--dir", default="patent", help="matter folder (default: patent)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--no-audit", action="store_true", help="do not append to audit.jsonl")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        res = run(args)
    except UsageError as e:
        res = {"ok": False, "exit_code": 2, "error": str(e), "findings": [], "checks_run": [],
               "checks_skipped": [], "summary": {}}
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("ERROR: %s" % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(render_text(res))
    return res["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
