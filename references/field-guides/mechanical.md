---
title: Field guide - mechanical devices and consumer products
last_verified: 2026-11-18
sources:
  - url: https://www.ecfr.gov/current/title-37/section-1.84
    supports: 37 CFR 1.84 drawing standards, including permitted views (perspective, exploded, sectional, partial, enlarged) and black-and-white line drawings.
  - url: https://www.ecfr.gov/current/title-37/section-1.83
    supports: 37 CFR 1.83(a) drawings must show every claimed feature.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2114.html
    supports: MPEP 2114 functional language in apparatus claims; a prior device capable of the function can anticipate.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2125.html
    supports: MPEP 2125 drawings as prior art; proportions are not evidence unless stated to scale.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2173.html
    supports: MPEP 2173.05(b) relative terms, 2173.05(g) functional limitations.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2144.html
    supports: MPEP 2144.04 legal precedent as a source of obviousness rationales (for example changes in size, shape, or making parts integral or separable) and 2144.05 ranges.
---

# Field guide: mechanical devices and consumer products

Load at Phase 3, Round 4 and Step 3. General rules: `claim-drafting.md`, `specification-drafting.md`.

## Default claim categories

| Claim | Default | Notes |
|---|---|---|
| Apparatus / device | yes | structure and how parts connect and move |
| Method of use | often | if the way it is used is new; one actor |
| Method of making | when manufacturing is new | molding, forming, assembly steps |
| System or kit | sometimes | device plus accessory or consumable |

## What examiners in this field focus on

- **102/103 on structure.** Examiners read structural claims broadly and look for any device with the same parts arranged the same way.
- **Functional language.** "configured to hold a tube" is met by any prior device capable of holding a tube (MPEP 2114). The novel feature should be structure, not function.
- **Routine changes.** Changes in size, shape, proportion, material, or making parts one piece or separate are often argued as obvious (MPEP 2144.04). Tie such features to a real effect the inventor can show.
- **Relative terms.** "substantially parallel," "thin," "rigid" need a standard in the spec (MPEP 2173.05(b)).
- **Drawings.** Every claimed feature must be shown (37 CFR 1.83(a)); missing views draw objections.
- **101 is rarely an issue,** but a claim that recites only a natural law applied to a mechanism, with no specific structure, can be at risk (see `eligibility-101.md`).

## Typical 112 risks and fixes

| Risk | Fix |
|---|---|
| Nonce words: "a locking member configured to…", "an attachment mechanism" | Name the structure: latch, hook and catch, detent, pin, spring, threads, magnet |
| Relative terms in independents | Define in the spec, or use numbers with ranges |
| Dimensions only in drawings | Write dimensions and ranges in the text; drawings not to scale prove nothing (MPEP 2125) |
| Parts list without relationships | Recite how each part attaches, moves, or engages another |

## Figures to include

The skill cannot invent accurate mechanical views. Use the user's CAD exports, sketches, or photos converted to line art (`image` figure type), or recommend a patent draftsperson.

| View | Use |
|---|---|
| Perspective | overall shape; usually FIG. 1 |
| Front, side, top, bottom | exact layout of parts |
| Exploded | how parts assemble; every part numbered |
| Sectional | internal structure; mark the section line on another view |
| Detail (enlarged) | small features such as ribs, teeth, hinges |
| Operating positions | open and closed, extended and retracted (FIGS. 3A, 3B) |
| Alternative embodiments | each variant you may claim |
| Method of use | flowchart, or a sequence of views |

## Specification must-haves

- [ ] Every part named with a numeral, its shape, its material, and what it connects to.
- [ ] How it moves: pivot axes, sliding directions, ranges of motion, positions.
- [ ] Materials and alternatives (for example: thermoplastic such as polypropylene or nylon; metal such as aluminum or steel; elastomer for grips).
- [ ] Dimensions, tolerances, and ratios as ranges with preferred sub-ranges, with units. Write the ones you may claim.
- [ ] Forces, torques, stiffness, or other performance numbers if the inventor has them (past tense only if measured).
- [ ] Mechanism alternatives for each function: living hinge or pin hinge; snap fit, screw, or adhesive; spring, magnet, or detent.
- [ ] Manufacturing methods and alternatives (molding, machining, additive manufacturing, stamping).
- [ ] Definitions for structural nouns with field synonyms (channel, slot, groove; rib, ridge, barb; jaw, arm, finger).
- [ ] The "figures not necessarily to scale" sentence, and the real dimensions written out.

## Consumer-product notes

- Trade shows, crowdfunding pages, retail listings, and sample shipments start the clock. Offers count, not only sales (`bars-and-eligibility.md`).
- Appearance is protected by design patents, not utility patents. Mention design protection in one line if the look matters; this skill covers utility only.
