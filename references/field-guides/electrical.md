---
title: Field guide - electrical, electronics, and semiconductors
last_verified: 2026-11-18
sources:
  - url: https://www.ecfr.gov/current/title-37/section-1.84
    supports: 37 CFR 1.84 drawing standards, including conventional graphical symbols and graphs.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2106.html
    supports: MPEP 2106.03 transitory signals are not a statutory category (In re Nuijten).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2181.html
    supports: MPEP 2181 placeholders such as "unit for" or "device for" may invoke 112(f).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2114.html
    supports: MPEP 2114 functional language in apparatus claims.
---

# Field guide: electrical, electronics, semiconductors

Load at Phase 3, Round 4 and Step 3. General rules: `claim-drafting.md`, `specification-drafting.md`. Firmware-heavy inventions also use `field-guides/software.md`.

## Default claim categories

| Claim | Default | Notes |
|---|---|---|
| Circuit / apparatus | yes | components and their electrical connections |
| Method of operating | yes | control steps performed by the circuit or controller (one actor) |
| System | when several devices interact | e.g., charger plus battery pack |
| Method of making | semiconductors, packaging | process steps and structures |
| Non-transitory medium | when firmware is the point | parallel to the method |

## What examiners in this field focus on

- **103 combinations of known blocks.** Examiners combine a known topology with a known control scheme. Point the claims at the specific connection, timing, or control that produces the effect.
- **Functional circuit language.** "a circuit configured to…" is usually treated as structure, but "a unit for," "a device for," or "logic for" can trigger 112(f) (MPEP 2181). Recite components or the controller-plus-instructions form.
- **Signals.** A signal itself is not patentable subject matter (In re Nuijten; MPEP 2106.03). Claim the transmitter, receiver, method, or medium.
- **Standards.** If the invention touches a standard (wireless, video, power delivery), standard contributions and drafts are prior art once public. Pharma and standard-essential issues: `case-law/pharma-and-sep.md`.

## Typical 112 risks and fixes

| Risk | Fix |
|---|---|
| "a control unit configured to…" with no structure | "a controller comprising a processor and memory storing instructions that cause…", or recite the circuit elements |
| Values only in a schematic | Write component values and ranges in the text |
| Undefined signal terms ("high," "low," "fast") | Define thresholds, voltages, frequencies, or timing in the spec |
| Relative terms ("substantially equal voltage") | Give a tolerance in the spec |

## Figures to include

| Figure | Shows |
|---|---|
| Block diagram | functional blocks and signal paths |
| Circuit schematic | components, values (or ranges), connections; conventional symbols |
| Timing or waveform diagram | signals over time, thresholds, phases |
| State diagram | controller states and transitions |
| Flowchart | control method steps |
| Graph | measured or simulated performance (label simulated as simulated) |
| Cross-section or layout | semiconductor or package structures |

`drawings.py` makes block, flowchart, sequence, and graph figures. Schematics and layouts usually need the user's EDA export converted to line art (`image` type) or a draftsperson.

## Specification must-haves

- [ ] Topology and alternatives (for example buck, boost, or buck-boost; discrete, IC, FPGA, or microcontroller).
- [ ] Component types, values, and ranges with preferred sub-ranges (resistance, capacitance, frequency, voltage, current).
- [ ] Signal definitions: levels, thresholds, timing, frequency, duty cycle.
- [ ] Control algorithm for any controller or firmware function (steps, conditions, order).
- [ ] Operating modes and transitions (startup, fault, sleep).
- [ ] Performance numbers (efficiency, noise, latency, power) if measured, past tense; simulations labeled as simulations.
- [ ] Definitions for terms with field synonyms (terminal, contact, pad, pin; node, net; module, unit).
- [ ] Manufacturing process steps and materials for semiconductor or package inventions.

## Disclosure traps

- Datasheets, application notes, FCC filings, conference papers, and standards contributions are often public before a patent is filed. Check what was released and when (`bars-and-eligibility.md`).
