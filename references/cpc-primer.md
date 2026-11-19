---
title: CPC primer for searching
last_verified: 2026-11-18
sources:
  - url: https://www.uspto.gov/web/patents/classification/cpc/html/cpc.html
    supports: CPC section titles A-H and Y.
  - url: https://www.uspto.gov/web/patents/classification/cpc/html/cpc-G06N.html
    supports: Scheme page format (code, dots, title, [YYYY-MM] revision date, warnings). Every code in the starter table was checked on its subclass page at https://www.uspto.gov/web/patents/classification/cpc/html/cpc-<SUBCLASS>.html on 2026-11-18.
  - url: https://www.uspto.gov/web/patents/classification/cpc/html/defG06N.html
    supports: Definition page format (definition statement, references, glossary); definitions version 2026.01 shown on that page.
  - url: https://www.cooperativepatentclassification.org/cpcSchemeAndDefinitions
    supports: Official CPC scheme and definitions site (managed by the EPO); notices of change.
  - url: https://www.cooperativepatentclassification.org/about
    supports: CPC is a joint EPO-USPTO scheme built from ECLA and kept compatible with the IPC.
  - url: https://www.uspto.gov/web/patents/classification/cpc/html/cpc-Y.html
    supports: Section Y title; Y02 (climate change mitigation or adaptation), Y04, Y10S, Y10T class and subclass titles.
---

# CPC primer

The Cooperative Patent Classification (CPC) is the shared EPO–USPTO scheme, built from the old European scheme and kept compatible with the International Patent Classification (IPC). Examiners search by it. You should too. Load this at Phase 2, Step 2 (and Phase 1 for CPC-anchored queries).

## 1. How a code is built

```
A61B 5/024
│││  │ └── subgroup (after the slash)
│││  └──── main group (number before the slash; main groups end in /00)
││└─────── subclass letter (A61B)
│└──────── class (A61)
└───────── section (A)
```

| Level | Example | Meaning |
|---|---|---|
| Section | A | Human necessities |
| Class | A61 | Medical or veterinary science; hygiene |
| Subclass | A61B | Diagnosis; surgery; identification |
| Main group | A61B 5/00 | Measuring for diagnostic purposes; identification of persons |
| Subgroup | A61B 5/02 | (1 dot) evaluating the cardiovascular system |

**Sections:**

| | Title |
|---|---|
| A | Human necessities |
| B | Performing operations; transporting |
| C | Chemistry; metallurgy |
| D | Textiles; paper |
| E | Fixed constructions |
| F | Mechanical engineering; lighting; heating; weapons; blasting |
| G | Physics |
| H | Electricity |
| Y | General tagging of new technologies and cross-sectional technologies; former USPC collections |

## 2. Read the dots, not the digits

- The number after the slash does **not** show the hierarchy. `G06F 9/50` is not a child of `G06F 9/5` in any decimal sense.
- The **dots** on the scheme page show the hierarchy. One dot is a child of the nearest line above with no dot; two dots is a child of the nearest one-dot line above, and so on.
- A dotted title reads as a continuation of its parent. Example: `G06V 10/00` "Arrangements for image or video recognition or understanding" → `G06V 10/70` (1 dot) "using pattern recognition or machine learning." Together: image recognition using machine learning.
- Text in curly brackets `{ }` is CPC-only detail that the IPC does not have. Example: `G06F 1/163` "{Wearable computers, e.g. on a belt}."
- Codes in the 2000 series (`C12N 2310/20`) are indexing codes. They add facets to a main classification and are never the only code on a document.
- Section Y codes are tags added on top of the normal codes:
  - `Y02` climate change mitigation or adaptation technologies (for example `Y02E 60/10` energy storage using batteries).
  - `Y04S` systems integrating power-network operation with communication or IT (smart grids).
  - `Y10S` and `Y10T` hold subjects from the former US classification (USPC). Useful for older US documents.

## 3. How to find the right codes

Work in this order:

1. **From your closest references.** Each cached record has `cpc` (`cache/<NUMBER>.json`). Count the codes across the top 5 references. Codes that repeat are the field's home. A single document's codes can be noisy.
2. **Confirm on the scheme page.** `https://www.uspto.gov/web/patents/classification/cpc/html/cpc-<SUBCLASS>.html` (for example `cpc-A61B.html`). Read the code's line, its parent lines, and any WARNING about reclassification.
3. **Read the definition.** `https://www.uspto.gov/web/patents/classification/cpc/html/def<SUBCLASS>.html`. It says what the group covers, which other groups take precedence, and the glossary. Check it before relying on a group for a "no art found" conclusion.
4. **Browse from the top.** If you have no references yet, start at the subclass page for the obvious field and walk down by title. The official site is `cooperativepatentclassification.org` (scheme, definitions, notices of change).
5. **Write down 2–4 groups** in the search plan with their titles. Never use a code whose meaning you did not confirm.

## 4. Using codes in queries

| Where | How | Notes |
|---|---|---|
| available web search on Google Patents | `site:patents.google.com "A61B5/02" "photoplethysmography" wrist` | Google Patents prints codes without the space (`A61B5/02`). Quote the code string and add 1–2 keywords. A code alone returns too much. |
| Breadth | run separate queries for the 2–3 most relevant subgroups, plus the parent | Whether a quoted code also matches its children depends on the search engine. Do not count on it. |
| Too few hits | move up one level (fewer dots), or to the main group | Check that the parent still fits the element. |
| Too many hits | move down one level, or add one more keyword | |
| Reclassification warning | search both the old group and each new group named | Older documents may not be moved yet. |
| Older and foreign art | use the IPC main group, which usually matches CPC at that level | Many older documents carry IPC only. |
| ODP or EPO OPS (keys) | use their CPC search fields per `sources-and-apis.md` | Field names there are partly unverified; handle failures. |

Record each CPC query in `prior-art.json → queries` like any other query, with the code and its title in the plan.

## 5. Starter table

Checked on the USPTO scheme pages on 2026-11-18. Dots show the level under the main group. Titles are shortened where long; read the full line on the scheme page before use. This list is a starting point, not a substitute for codes taken from your own closest references.

### Software, AI, networks

| Code | Dots | Title (short) | Typical use |
|---|---|---|---|
| G06N 20/00 | 0 | Machine learning | ML methods not tied to neural networks |
| G06N 3/02 | 1 | Neural networks | NN architectures |
| G06N 3/08 | 2 | Learning methods (under neural networks) | training procedures |
| G06N 5/04 | 1 | Inference or reasoning models | rule engines, inference |
| G06F 16/00 | 0 | Information retrieval; database and file system structures | search, indexing, databases |
| G06F 21/00 | 0 | Security arrangements protecting computers, programs or data | access control, malware defense |
| G06F 3/048 | 2 | Interaction techniques based on GUIs | UI interaction features |
| G06F 9/50 | 3 | Allocation of resources, e.g. CPU | schedulers, cloud resource allocation |
| G06F 40/00 | 0 | Handling natural language data | NLP, text processing |
| G06Q 10/00 | 0 | Administration; management | workflow, logistics, scheduling (high 101 risk) |
| G06Q 20/00 | 0 | Payment architectures, schemes or protocols | payments (high 101 risk) |
| G06Q 50/00 | 0 | ICT for business processes of specific sectors | sector-specific business systems |
| G06T 7/00 | 0 | Image analysis | image processing pipelines |
| G06V 10/70 | 1 | Image or video recognition using pattern recognition or ML | vision models |
| G06V 40/16 | 2 | Human faces | face detection or recognition |
| G10L 15/00 | 0 | Speech recognition | ASR |
| H04L 9/00 | 0 | Cryptographic mechanisms; network security protocols | encryption, signatures, blockchain (see H04L 9/50) |
| H04L 63/00 | 0 | Network architectures or protocols for network security | firewalls, authentication over networks |
| H04L 67/10 | 2 | Applications distributed across network nodes | distributed and cloud services |
| H04W 4/02 | 1 | Services making use of location information | location-based services |
| G16H 50/20 | 1 | ICT for computer-aided diagnosis | clinical decision support |
| G16H 40/67 | 2 | ICT for remote operation of medical equipment | telemedicine devices |

### Mechanical

| Code | Dots | Title (short) | Typical use |
|---|---|---|---|
| F16B (subclass) | – | Devices for fastening or securing parts together | fasteners, clips, joints |
| F16H 1/00 | 0 | Toothed gearings for conveying rotary motion | gear trains |
| F16K (subclass) | – | Valves; taps; cocks | valves |
| F16L 37/00 | 0 | Couplings of the quick-acting type | quick connectors for pipes and hoses |
| F16F 9/00 | 0 | Springs, dampers, shock absorbers using a fluid | fluid dampers |
| B25J 9/16 | 1 | Program controls (for programme-controlled manipulators) | robot control |
| B33Y 10/00 | 0 | Processes of additive manufacturing | 3D printing methods |
| B33Y 80/00 | 0 | Products made by additive manufacturing | 3D-printed articles |
| B64U (subclass) | – | Unmanned aerial vehicles [UAV]; equipment therefor | drones |
| A42B 3/04 | 1 | Parts, details or accessories of helmets | helmet add-ons |
| A42B 3/0433 | 3 | {Detecting, signalling or lighting devices} (helmets) | helmet lights and sensors |

### Medical devices

| Code | Dots | Title (short) | Typical use |
|---|---|---|---|
| A61B 5/00 | 0 | Measuring for diagnostic purposes; identification of persons | sensors, wearables, diagnostics |
| A61B 5/02 | 1 | Evaluating the cardiovascular system (pulse, heart rate, blood pressure) | heart monitoring |
| A61B 17/00 | 0 | Surgical instruments, devices or methods | surgical tools |
| A61B 34/30 | 1 | Surgical robots | robotic surgery |
| A61M 5/00 | 0 | Devices for subcutaneous, intravascular or intramuscular delivery | syringes, injectors, infusion |
| A61M 16/00 | 0 | Respiratory devices by gas treatment, e.g. ventilators; tracheal tubes | ventilation |
| A61M 25/00 | 0 | Catheters; hollow probes | catheters |
| A61F 2/82 | 1 | Devices keeping tubular body structures open, e.g. stents | stents |
| A61F 13/00 | 0 | Bandages or dressings; absorbent pads | wound care |
| A61N 1/00 | 0 | Electrotherapy; circuits therefor | stimulators |
| A61N 1/36 | 3 | (electrotherapy) for stimulation | nerve and muscle stimulation |

### Consumer products

| Code | Dots | Title (short) | Typical use |
|---|---|---|---|
| A47J 31/00 | 0 | Apparatus for making beverages | coffee and tea machines |
| A47L 9/00 | 0 | Details or accessories of suction cleaners | vacuum cleaners |
| A63B 21/00 | 0 | Exercising apparatus working against a counterforce | strength equipment |
| A63B 24/00 | 0 | Electric or electronic controls for exercising apparatus | connected fitness |
| B26B 21/00 | 0 | Razors; shaving implements | razors |
| A01K 15/02 | 1 | Training or exercising equipment for animals; animal toys | pet products |
| G06F 1/163 | 3 | {Wearable computers} | wearables (with A61B 5/00 for health sensing) |

### Electrical and electronics

| Code | Dots | Title (short) | Typical use |
|---|---|---|---|
| H01M 10/42 | 1 | Servicing or maintenance of secondary cells | battery management |
| H01M 10/052 | 2 | Li-accumulators | lithium batteries |
| H02J 7/00 | 0 | Circuit arrangements for charging or discharging batteries | chargers |
| H02J 50/10 | 1 | Wireless power using inductive coupling | wireless charging |
| H02M 3/00 | 0 | Conversion of DC power input into DC power output | DC-DC converters |
| H05K 7/20 | 1 | Modifications to facilitate cooling, ventilating, or heating | electronics cooling |
| H05B 45/00 | 0 | Circuit arrangements for operating LEDs | LED drivers |
| H05B 47/19 | 3 | Controlling the light source via wireless transmission | smart lighting |
| H04N 23/00 | 0 | Cameras or camera modules with electronic image sensors; control thereof | cameras |
| G01S 17/00 | 0 | Systems using reflection of non-radio EM waves, e.g. lidar | lidar |
| H01Q 1/00 | 0 | Details of, or arrangements associated with, antennas | antennas |
| H01L 21/00 | 0 | Processes or apparatus for making semiconductor devices | semiconductor fabrication |
| B60L 53/00 | 0 | Methods of charging batteries for electric vehicles; charging stations | EV charging |

### Chemistry and materials

| Code | Dots | Title (short) | Typical use |
|---|---|---|---|
| C08L (subclass) | – | Compositions of macromolecular compounds | polymer blends |
| C08K 3/00 | 0 | Use of inorganic substances as compounding ingredients | fillers, additives |
| C09D 5/00 | 0 | Coating compositions characterised by physical nature or effect | paints, coatings |
| C01B 32/182 | 2 | Graphene | graphene materials |
| B01J 23/00 | 0 | Catalysts comprising metals or metal oxides or hydroxides | catalysts |
| C02F 1/00 | 0 | Treatment of water, waste water, or sewage | water treatment |
| C07D (subclass) | – | Heterocyclic compounds | small-molecule chemistry |
| A61K 9/00 | 0 | Medicinal preparations characterised by special physical form | formulations, dosage forms |
| A61K 31/00 | 0 | Medicinal preparations containing organic active ingredients | small-molecule drugs |
| A61P 35/00 | 0 | Antineoplastic agents | anticancer activity (therapeutic-activity tag) |

### Biotech

| Code | Dots | Title (short) | Typical use |
|---|---|---|---|
| C12N 15/11 | 2 | DNA or RNA fragments; modified forms; {non-coding nucleic acids} | oligos, siRNA, guide RNA |
| C12N 9/22 | 3 | Ribonucleases; deoxyribonucleases | nucleases; CRISPR enzymes are being moved to C12N 9/222 (check the warning) |
| C12N 2310/20 | 2 | (indexing) nucleic acids involving CRISPR | CRISPR facet; scheme warns of reclassification into C12N 9/22x |
| C07K 16/00 | 0 | Immunoglobulins, e.g. monoclonal or polyclonal antibodies | antibodies |
| C12Q 1/68 | 1 | Measuring or testing involving nucleic acids | nucleic acid assays |
| C12Q 1/6883 | 3 | (nucleic acid assays) for diseases caused by alterations of genetic material | genetic diagnostics (high 101 risk) |
| G01N 33/53 | 3 | Immunoassay; biospecific binding assay | immunoassays |
| A61K 39/00 | 0 | Medicinal preparations containing antigens or antibodies | vaccines, antibody drugs |
| A61K 48/00 | 0 | Medicinal preparations containing genetic material inserted into cells; gene therapy | gene therapy |

### Y-section tags

| Code | Title (short) | Typical use |
|---|---|---|
| Y02E 60/10 | Energy storage using batteries | climate-tagged battery tech |
| Y02T 10/70 | Energy storage systems for electromobility | EV batteries |
| Y02P (subclass) | Climate change mitigation in production or processing of goods | green manufacturing |
| Y02A (subclass) | Technologies for adaptation to climate change | adaptation tech |
| Y10T (subclass) | Technical subjects covered by former US classification | older US mechanical art |
| Y10S (subclass) | Former USPC cross-reference art collections and digests | older US art collections |

## 6. Common mistakes

- Using a code from memory without opening the scheme page. Codes get split, moved, and retitled.
- Reading a subgroup title alone. A one-dot title ("using inductive coupling") is meaningless without its parent.
- Treating "no hits in this group" as "no art." Documents can sit in neighboring groups, in Y tags, or in IPC-only records.
- Ignoring the "takes precedence" notes in titles and definitions. They tell you where a document went instead.
