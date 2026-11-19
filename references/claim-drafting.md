---
title: Claim drafting rules and patterns (US utility)
last_verified: 2026-11-18
sources:
  - url: https://www.ecfr.gov/current/title-37/section-1.75
    supports: 37 CFR 1.75 (claims; dependent and multiple dependent form; Jepson form at 1.75(e); broadest claim first 1.75(g); one indentation per element 1.75(i)). Text read from eCFR, title 37 up to date as of 2026-11-16.
  - url: https://www.ecfr.gov/current/title-37/section-1.16
    supports: 37 CFR 1.16(h) fee per independent claim over three, 1.16(i) per claim over 20, 1.16(j) multiple dependent claim fee.
  - url: https://www.ecfr.gov/current/title-37/section-1.102
    supports: 37 CFR 1.102(e) Track One limits (4 independent, 30 total, no multiple dependent claims).
  - url: https://www.law.cornell.edu/uscode/text/35/112
    supports: 35 U.S.C. 112(b) definiteness, 112(d) dependent claims, 112(e) multiple dependent claims, 112(f) means-plus-function text.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2111.html
    supports: MPEP 2111.02 (effect of preamble), 2111.03 (comprising / consisting essentially of / consisting of; "composed of" can vary), 2111.04 (adapted to, wherein, whereby; In re Giannelli, 739 F.3d 1375 (Fed. Cir. 2014)).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2113.html
    supports: MPEP 2113 product-by-process judged on the product itself.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2114.html
    supports: MPEP 2114 functional language in apparatus claims covers devices capable of the function.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2117.html
    supports: MPEP 2117 Markush claims.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2129.html
    supports: MPEP 2129(III) Jepson preamble is an implied admission of prior art (In re Fout).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2173.html
    supports: MPEP 2173.05(b) relative terms, 2173.05(d) "such as"/"for example", 2173.05(e) antecedent basis, 2173.05(g) functional limitations, 2173.05(h) Markush and alternatives, 2173.05(i) negative limitations need basis in the original disclosure, 2173.05(p) product-by-process and product-and-process in one claim (IPXL Holdings v. Amazon.com, 430 F.3d 1377 (Fed. Cir. 2005)), 2173.05(q) use claims.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2181.html
    supports: MPEP 2181 112(f) three-prong test, Williamson v. Citrix Online, 792 F.3d 1339 (Fed. Cir. 2015), list of generic placeholders, algorithm requirement for computer-implemented 112(f) limitations.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2106.html
    supports: MPEP 2106.03 transitory signals are not a statutory category (In re Nuijten, 500 F.3d 1346 (Fed. Cir. 2007); Mentor Graphics v. EVE-USA, 851 F.3d 1275 (Fed. Cir. 2017)).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s608.html
    supports: MPEP 608.01(m) form of claims (one sentence); 608.01(n) dependent and multiple dependent claims, including that a claim in a different statutory class can be a proper dependent claim.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2131.html
    supports: MPEP 2131.03 anticipation of ranges.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2144.html
    supports: MPEP 2144.05 obviousness of overlapping ranges.
  - url: scripts/check_claims.py
    supports: Finding codes CLAIM_NUMBERING, DEP_FORWARD, DEP_MISSING, MULTI_DEP, MULTI_DEP_FORM, MULTI_ON_MULTI, ONE_SENTENCE, ANTECEDENT, DOUBLE_INTRO, NONCE_112F, INDEFINITE, TERM_SUPPORT, COUNTS and their levels.
---

# Claim drafting

Load this at Phase 3, Step 2, and in the office-action tool when amending claims. Doctrine behind these rules: `disclosure-112.md`, `eligibility-101.md`, `case-law/claims-and-construction.md`, `case-law/infringement.md`. Format of the claims file: `state-files.md` (`draft/claims.md`).

Claims define the right. Everything else in the application exists to support them. Write claims first.

## 1. Anatomy

```
1. A clip comprising:          ← preamble + transition
   a base;                     ← body: elements, one per indented line
   a first jaw extending from the base; and
   a second jaw connected to the base by a hinge.
```

| Part | Rule |
|---|---|
| Preamble | Name the thing claimed in plain category words ("A method of…", "A system comprising…"). Keep it short. A preamble may or may not limit the claim (MPEP 2111.02). Do not hide a key limitation there; put it in the body. |
| Transition | Default `comprising`. See the table below. |
| Body | Each element or step on its own indented line (37 CFR 1.75(i)), separated by semicolons, with "and" before the last one. Recite how elements connect or interact, not just a parts list. |

**Transitions (MPEP 2111.03):**

| Phrase | Scope | Use when |
|---|---|---|
| comprising (also "including", "containing") | open: other unrecited parts or steps allowed | almost always |
| consisting of | closed: nothing else (except impurities normally present) | rare; mainly chemistry when the closed set is the point |
| consisting essentially of | partly closed: other things allowed only if they do not materially affect the basic and novel characteristics | chemistry, when you must exclude something but want some room; define the basic and novel characteristics in the spec |
| having, composed of | unclear: read in context | avoid as the main transition |

## 2. Antecedent basis (MPEP 2173.05(e))

- Introduce each element once with "a" or "an." Refer back with "the" (or "said"; pick one word and use it everywhere).
- Repeat the exact noun phrase. "a first sensor" → "the first sensor", never "the sensor" if there are two.
- `at least one X` → `the at least one X`. `a plurality of X` → `the plurality of X`, or `each X of the plurality of X`.
- Inherent parts need no introduction when they obviously exist: "the outer surface of the shell" is fine once "a shell" is introduced. Use this sparingly.
- A dependent claim may rely on terms introduced in its parent chain only. It cannot use a term from a sibling claim.
- A multiple dependent claim needs antecedent basis through every claim it refers to.
- Never introduce the same element twice with "a." It reads as two different elements.

## 3. One sentence per claim

- Each claim is one sentence: capital letter at the start, one period at the end (MPEP 608.01(m)).
- No periods inside the claim except in abbreviations. Use semicolons and colons for structure.
- Number claims consecutively from 1 (37 CFR 1.75(f)). Put the broadest claim first and group dependents with their parents (37 CFR 1.75(g)).

## 4. Independent and dependent strategy

**Independent claims**
- Each one carries the core that is absent from every X reference in `prior-art.json` (Phase 3, Step 2.1).
- Keep only what is needed for novelty and non-obviousness, plus what is needed for 101 (`eligibility-101.md`). Every extra word is a design-around.
- Default budget: 3 independents (one per category you need) within 20 total claims.

**Dependent claims**
- Each one adds one meaningful limitation that could matter in a fight: a fallback against the closest art, a commercially important feature, or a catch for a design-around.
- Order them from most to least commercially relevant.
- Build ladders: broad range → narrower range → specific value; genus → species.
- A dependent claim must refer to an earlier claim and further limit it (35 U.S.C. 112(d); 37 CFR 1.75(c)).
- **Claim differentiation:** a dependent that adds X suggests the independent does not require X. Use this on purpose: add a dependent for any feature you want the independent read without. Do not add a dependent that repeats what the independent already says.
- A dependent claim may be in a different category from its parent ("A method of making the product of claim 1, …") if it includes every limitation of the parent (MPEP 608.01(n)).

**Claim tree example**

```
1 (method, broad core)
├─ 2 fallback feature A
│  └─ 3 narrower A
├─ 4 fallback feature B (catches design-around)
└─ 5 detectable output limitation
6 (system, parallel to 1) ─ 7, 8 mirror 2, 4
11 (CRM, parallel to 1) ─ 12 mirrors 2
```

## 5. Claim categories

| Category | Form | Use when | Watch for |
|---|---|---|---|
| Method / process | "A method of [doing X], comprising: [verb-ing] …" | software, processes, methods of use or treatment | single actor (Section 7); step order only if required |
| System / apparatus / device | "A system comprising: a processor; and memory storing instructions that, when executed, cause …" or structural elements | products, hardware, software systems | 112(f) nonce words (Section 9) |
| Computer-readable medium (Beauregard) | "One or more non-transitory computer-readable media storing instructions that, when executed by a processor, cause …" | software sold or distributed as code | Must say **non-transitory**. A medium that could be a signal is not a statutory category (MPEP 2106.03; In re Nuijten). |
| Composition / article of manufacture | "A composition comprising: …" | chemistry, materials, formulations | ranges, Markush, consisting-essentially-of |
| Method of making | "A method of making a [product], comprising: …" | new manufacturing routes | separate from product claims |
| Method of use / treatment | "A method of treating [condition] in a subject, comprising administering …" | new uses of known things | medical-procedure immunity (`field-guides/medical-device.md`) |
| Kit | "A kit comprising: [items]; and instructions …" | multi-part products | instructions alone add little weight |

Never:
- a "use" claim with no steps ("The use of X for Y"); indefinite (MPEP 2173.05(q)).
- an apparatus claim that also requires a user to perform a method step; indefinite (MPEP 2173.05(p); IPXL Holdings v. Amazon.com).

## 6. Parallel scope across categories (software and AI)

- Method, system, and CRM claims should cover the same inventive core, step for step.
- System: processor + memory storing instructions that cause the processor to perform the method's steps (verb forms change: "receiving" → "receive").
- CRM: the same steps as "operations comprising."
- Check that no category is accidentally narrower (an extra element in the system claim) or broader (a missing step in the CRM claim) unless you meant it.
- Put the technical improvement in all three (`eligibility-101.md`).

## 7. One actor per method claim (divided infringement)

Direct infringement of a method needs every step performed by, or attributable to, one entity. Attribution exists when that entity directs or controls the others' performance, or when they form a joint enterprise (Akamai Techs. v. Limelight Networks, 797 F.3d 1020 (Fed. Cir. 2015) (en banc)). Without a direct infringer there is no induced infringement (Limelight Networks v. Akamai Techs., 572 U.S. 915 (2014)). Details: `case-law/infringement.md`.

Draft accordingly:
- Write each method claim from one actor's point of view: the server, or the client device, or the vehicle.
- Name the actor in each step when it helps: "receiving, by a server, …"
- Turn the other party's acts into inputs: "receiving a request from a user device" instead of "a user sending a request."
- If both sides are valuable, write two independent claims: a server-side method and a device-side method.

| Divided (avoid) | Single actor (use) |
|---|---|
| a user selecting an item on a phone; a server storing the selection; the server sending a confirmation | receiving, by a server from a user device, a selection of an item; storing, by the server, the selection; and sending, by the server to the user device, a confirmation |

## 8. Claim the side you can detect

- Ask: could the user tell from a competitor's product that this claim is practiced?
- Prefer limitations that show up in a product's visible behavior, structure, output, or network traffic.
- Server-side internals, training recipes, and internal data structures are hard to prove. If they are the invention, also claim a detectable consequence (the output format, the device behavior), or weigh trade secret (Phase 1 detectability note).

## 9. Functional language and 112(f)

35 U.S.C. 112(f) lets an element be stated "as a means or step for performing a specified function without the recital of structure." The cost: the claim then covers only the structure in the spec that does the function, and its equivalents.

**When it is triggered (MPEP 2181):**
- "means for" or "step for" plus a function: presumed 112(f).
- No "means," but a generic placeholder plus a function, with no structure that the field understands: 112(f) can still apply (Williamson v. Citrix Online). Placeholders the MPEP lists include "mechanism for," "module for," "device for," "unit for," "component for," "element for," "member for," "apparatus for," "machine for," and "system for."

**Software trap:** a computer-implemented 112(f) element needs an algorithm in the spec for the function. A general-purpose computer alone is not enough. Without it the claim is indefinite (MPEP 2181).

**Fixes:**
- Recite structure the field knows: "a spring," "a latch," "a hinge," "a processor," "a circuit," "a memory storing instructions that cause the processor to…"
- Replace "a [nonce word] configured to [function]" with the actual parts or the processor-plus-instructions form.
- Even with structural words, describe the algorithm in the spec for every software function (`specification-drafting.md`). Courts do not always treat "processor configured to" as enough structure.
- If you want 112(f) on purpose, say "means for" and disclose every structure and its equivalents in the spec.

## 10. Special formats and word choices

### Markush groups (MPEP 2117, 2173.05(h))
- Form: "selected from the group consisting of A, B, and C." Closed language inside the group.
- Members should share a common property or use.
- "A, B, or C" in plain alternative form is also acceptable.
- Never "selected from the group comprising." Avoid "and/or"; write "A, B, or a combination thereof" instead.

### Ranges and numbers
- Give units and the basis: "from 5 wt% to 10 wt%, based on a total weight of the composition."
- Use "from X to Y" (endpoints included). Avoid "between" unless the spec says whether endpoints count.
- Ladder ranges in dependents: broad → preferred → most preferred, each with spec support.
- Prior art inside a claimed range can anticipate it (MPEP 2131.03). Overlapping ranges are usually treated as obvious unless there is evidence that the range matters, such as unexpected results (MPEP 2144.05). Support any key range with data in the examples.
- "About" is a relative term. Define it in the spec (for example, ±10%) or leave it out of independents.

### Negative limitations (MPEP 2173.05(i))
- "free of X," "does not comprise X," "without X" are allowed if definite.
- Each one needs basis in the original disclosure. Without it, the claim fails written description. Put the support in the spec now: say embodiments may lack X and why.

### Product-by-process (MPEP 2113, 2173.05(p))
- "A film made by the process of claim 1." Patentability is judged on the product itself: if the product is old, a new process does not save it.
- For infringement, the process steps limit the claim (Abbott Labs. v. Sandoz, 566 F.3d 1282 (Fed. Cir. 2009) (en banc in part)).
- Use only when the product cannot be described by structure or properties. Prefer a structural product claim plus a method-of-making claim.

### Jepson claims (37 CFR 1.75(e); MPEP 2129)
- Form: "In a [known device], the improvement comprising…"
- The preamble is treated as an implied admission that it is prior art. Avoid this form.

### Relative terms (MPEP 2173.05(b))
- "substantially," "about," "approximately," "generally," "thin," "large," "near."
- Allowed only if the spec gives a standard so a skilled reader knows the scope with reasonable certainty (Nautilus v. Biosig Instruments, 572 U.S. 898 (2014)).
- Keep them out of independents unless defined. Define each one used.

### "Such as," "for example," "preferably," "optionally," "may"
- These make scope unclear in a claim (MPEP 2173.05(d)). Move examples and preferences to the spec or to dependents.

### Ordinal terms
- "first" and "second" distinguish elements. They do not, by themselves, mean order in time, position, or importance.
- If order matters, say it: "after receiving the first signal."

### "Wherein" vs "whereby" (MPEP 2111.04)
- "wherein" introduces a limitation. Use it for real features.
- A "whereby" clause that only states the result of elements already recited may get no weight. Never rely on a whereby clause for novelty. Turn the needed feature into a positive element or step.

### "Configured to" vs "adapted to" vs "capable of"
- "configured to" is usually read as designed, programmed, or built to do the function. Use it as the default, and define it in the spec.
- "adapted to" can be read either as "designed to" or as "suitable for." The spec decides (MPEP 2111.04; In re Giannelli).
- "capable of" is the broadest. In apparatus claims, functional language covers any prior device able to do the function (MPEP 2114), so "capable of" invites anticipation. Avoid it for the novel feature.

### Singular, plural, "at least one"
- In an open claim, "a" or "an" generally means one or more. "a plurality of" means two or more.
- "at least one of A and B" may be read as at least one A **and** at least one B. If you mean either, write "at least one of A or B" or "one or more of A, B, or C," and define it in the spec.
- "each" means every one. "each sensor" in a claim requires all sensors to meet the limitation.

## 11. Claim fee economics

| Item | Rule | Where the numbers are |
|---|---|---|
| Included claims | 3 independent and 20 total with no excess fees (37 CFR 1.16(h), (i)) | `fees.md`, `python3 scripts/fees.py` |
| Excess independent | fee per independent claim over 3 | `fees.md` |
| Excess total | fee per claim over 20 | `fees.md` |
| Multiple dependent claim | one fee per application (1.16(j)); each multiple dependent claim also counts as the number of claims it refers to (1.75(c)) | `fees.md` |
| Track One | at most 4 independent, 30 total, no multiple dependent claims (37 CFR 1.102(e)) | `fees.md` |
| Provisional | no claims required, no claim fees | `filing-paths.md` |

Rules of thumb:
- Avoid multiple dependent claims in US filings. They cost more and count as several claims.
- Adding claims later (by amendment) triggers the same excess fees.
- Show the cost of a bigger claim set with `fees.py` before the user decides.

## 12. Common mistakes checklist

Run this by eye after `check_claims.py`.

- [ ] Every independent claim has a feature absent from every X reference.
- [ ] No independent claim needs more than one actor to infringe.
- [ ] Method, system, and CRM claims have parallel scope.
- [ ] CRM claims say "non-transitory."
- [ ] No nonce word plus function without structure (or 112(f) is intended and supported).
- [ ] Every software function in a claim has an algorithm in the spec.
- [ ] No relative term in an independent claim unless defined in the spec.
- [ ] No "such as," "preferably," "optionally," "may," or "and/or."
- [ ] No "whereby" clause doing the work of a limitation.
- [ ] No Jepson form, no use claim, no apparatus-plus-user-step claim.
- [ ] Every negative limitation has written support.
- [ ] Every claim term appears word for word in the spec at least once.
- [ ] Every claimed feature appears in a figure (37 CFR 1.83(a)).
- [ ] Every dependent adds one real limitation; none repeats its parent.
- [ ] Construction-dependent nouns (channel/lumen, module/engine) are defined in the spec or claimed generically.
- [ ] Claim counts fit the budget, or the user approved the extra fees.
- [ ] Reference numerals, if used in claims at all, are in parentheses and match the spec. (Many drafters leave them out.)

## 13. `check_claims.py` findings and fixes

Run: `python3 scripts/check_claims.py patent/draft/claims.md --spec patent/draft/spec.md --entity <status>`. Fix every BLOCK. Fix or justify every WARN in the package notes. If the script's `--help` lists codes not in this table, the script wins; update this table.

| Code | Level | Meaning | Fix |
|---|---|---|---|
| `CLAIM_NUMBERING` | BLOCK | Claims not numbered 1, 2, 3… consecutively | Renumber; update every dependency reference |
| `DEP_FORWARD` | BLOCK | A dependent refers to itself or a later claim | Move the dependent after its parent, or change the reference |
| `DEP_MISSING` | BLOCK | Refers to a claim that does not exist or is canceled | Point to the right claim, or delete the dependent |
| `MULTI_DEP` | WARN | Multiple dependent claim present (extra fee; counts as several claims) | Split into separate single dependents unless the user accepts the fee |
| `MULTI_DEP_FORM` | BLOCK | Multiple dependent not in the alternative ("claim 1 and 2") | Write "any one of claims 1 to 3" or "claim 1 or 2" |
| `MULTI_ON_MULTI` | BLOCK | A multiple dependent depends on another multiple dependent | Point it at single claims only |
| `ONE_SENTENCE` | BLOCK/WARN | Missing final period, internal period, empty claim, or "?" / "!" | Rewrite as one sentence; use semicolons |
| `ANTECEDENT` | BLOCK | "the X" with no earlier "a X" anywhere in the claim's chain, or used before it is introduced | Introduce "a X" first, or fix the noun to match the introduced term exactly |
| `ANTECEDENT` | WARN | Partial match, singular/plural mismatch, more than one possible referent, "at least one" not carried | Repeat the full introduced phrase ("the first sensor"; "the at least one sensor") |
| `ANTECEDENT` | INFO | Treated as an inherent property or a unique thing | Confirm it really is inherent; otherwise introduce it |
| `DOUBLE_INTRO` | WARN/INFO | The same element introduced twice with "a" in one chain | Use "the" the second time, or name them "first" and "second" |
| `NONCE_112F` | WARN | "means for," "step for," or a nonce word plus a function | Recite structure (Section 9), or keep 112(f) on purpose and confirm the spec discloses the structure or algorithm |
| `INDEFINITE` | WARN | Relative, optional, exemplary, or trademark language | Define the term in the spec, move it to a dependent, or delete it. Replace trademarks with generic names |
| `TERM_SUPPORT` | WARN | A claim term is not found in the description | Add the exact term to the detailed description, or change the claim to a term the spec uses |
| `COUNTS` | INFO | Independent, total, and multiple-dependent counts, with fee note | Compare with the budget; run `fees.py` if over 3/20 |

**Checks the script does not run** (do them by hand with Section 12): category choice, single-actor drafting, CRM "non-transitory," parallel scope, negative-limitation support, Jepson or use claims, apparatus-plus-method-step claims, whereby clauses, figure coverage (that one is `check_drawings.py` and `check_spec.py`).

## 14. Example claim sets (fictional)

These are teaching examples written for this file. They describe no real product and were not searched.

### A. Software: method, system, CRM (parallel scope)

Fictional invention: a phone holds sensor readings in a buffer and sends them only when the cellular radio is already awake for some other reason, which saves battery.

```
1. A method comprising:
   receiving, by a processor of a mobile device, a plurality of sensor readings from a sensor of the mobile device;
   storing, by the processor, the plurality of sensor readings in a buffer in a memory of the mobile device;
   determining, by the processor, that a cellular radio of the mobile device has entered a connected state for a purpose other than transmitting the plurality of sensor readings; and
   in response to the determining, transmitting, by the processor via the cellular radio while the cellular radio remains in the connected state, the plurality of sensor readings stored in the buffer to a remote server.

2. The method of claim 1, further comprising:
   determining, by the processor, that a count of sensor readings stored in the buffer exceeds a threshold; and
   in response to determining that the count exceeds the threshold, transmitting the sensor readings stored in the buffer to the remote server.

3. The method of claim 1, wherein the purpose other than transmitting the plurality of sensor readings comprises a voice call, a message, or a data request by an application executing on the mobile device.

4. The method of claim 1, further comprising compressing, by the processor, the plurality of sensor readings stored in the buffer before the transmitting.

5. A mobile device comprising:
   a sensor;
   a cellular radio;
   a memory comprising a buffer; and
   a processor coupled to the sensor, the cellular radio, and the memory, the memory storing instructions that, when executed by the processor, cause the processor to:
      receive a plurality of sensor readings from the sensor;
      store the plurality of sensor readings in the buffer;
      determine that the cellular radio has entered a connected state for a purpose other than transmitting the plurality of sensor readings; and
      in response to determining that the cellular radio has entered the connected state, transmit, via the cellular radio while the cellular radio remains in the connected state, the plurality of sensor readings stored in the buffer to a remote server.

6. One or more non-transitory computer-readable media storing instructions that, when executed by a processor of a mobile device, cause the processor to perform operations comprising:
   receiving a plurality of sensor readings from a sensor of the mobile device;
   storing the plurality of sensor readings in a buffer in a memory of the mobile device;
   determining that a cellular radio of the mobile device has entered a connected state for a purpose other than transmitting the plurality of sensor readings; and
   in response to the determining, transmitting, via the cellular radio while the cellular radio remains in the connected state, the plurality of sensor readings stored in the buffer to a remote server.
```

What it shows: one actor (the device) in every step; the technical effect (fewer radio wake-ups) lives in the claim's steps; claims 1, 5, and 6 match step for step; claim 2 catches a design-around that adds a size trigger; claim 3 is a plain alternative list.

### B. Mechanical device

Fictional invention: a molded clip that snaps around a tube, with ribs that grip.

```
1. A clip comprising:
   a base;
   a first jaw extending from the base;
   a second jaw connected to the base by a hinge, the second jaw being pivotable about the hinge between an open position and a closed position, the first jaw and the second jaw together defining a channel when the second jaw is in the closed position; and
   a latch comprising a hook on one of the first jaw and the second jaw and a catch on the other of the first jaw and the second jaw, the hook engaging the catch when the second jaw is in the closed position;
   wherein the first jaw comprises an inner surface facing the channel and a plurality of ribs projecting from the inner surface into the channel.

2. The clip of claim 1, wherein the hinge is a living hinge integrally formed with the base and the second jaw.

3. The clip of claim 2, wherein the base, the first jaw, the second jaw, and the living hinge are a single molded piece of a thermoplastic.

4. The clip of claim 1, wherein each rib of the plurality of ribs has a height of from 0.2 mm to 1.5 mm.

5. The clip of claim 4, wherein the height is from 0.4 mm to 0.8 mm.

6. The clip of claim 1, wherein each rib of the plurality of ribs comprises an elastomer.

7. The clip of claim 1, further comprising a fastener opening extending through the base.
```

What it shows: elements connected to each other, not a parts list; "one of… the other of" covers the latch either way round (`check_claims.py` may WARN on "the other of"; it is a standard idiom, so justify the WARN rather than rewrite); a range ladder (claims 4–5) with units; material and integral-forming fallbacks; each dependent is one limitation.

### C. Composition

Fictional invention: an edible coating that slows moisture loss in harvested fruit.

```
1. A coating composition comprising:
   from 2 wt% to 12 wt% of a film-forming polysaccharide selected from the group consisting of pullulan, alginate, and carboxymethyl cellulose;
   from 0.5 wt% to 4 wt% of a plasticizer;
   from 0.1 wt% to 1.0 wt% of a fatty acid ester emulsifier; and
   water,
   wherein each weight percentage is based on a total weight of the coating composition, and the coating composition has a pH of from 4.0 to 6.5.

2. The coating composition of claim 1, wherein the film-forming polysaccharide is pullulan.

3. The coating composition of claim 1, wherein the film-forming polysaccharide is present in an amount of from 4 wt% to 8 wt%.

4. The coating composition of claim 1, wherein the plasticizer is selected from the group consisting of glycerol, sorbitol, and propylene glycol.

5. The coating composition of claim 1, wherein the coating composition is free of wax.

6. A method of coating a harvested fruit, the method comprising:
   applying the coating composition of claim 1 to an outer surface of the harvested fruit; and
   drying the coating composition on the outer surface to form a film.
```

What it shows: a closed Markush group inside an open "comprising" claim; every range has units and a stated basis; claim 5 is a negative limitation, so the spec must say that wax-free embodiments exist and why; claim 6 is a method that depends from a composition claim, which can be a proper dependent because it includes every limitation of claim 1 (MPEP 608.01(n)). If `check_claims.py` flags "pH" as a trade name, that is a false positive; justify it.
