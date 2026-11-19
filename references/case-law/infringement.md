---
title: Infringement (literal, equivalents, indirect, extraterritorial, divided, venue) — case law and edge cases
last_verified: 2026-11-18
sources:
  - Adelman et al., Patent Law — Cases and Materials (5th ed.), ch. 12 (used for case selection only; digests are original)
  - Akeva L.L.C. v. Nike, Inc., 817 F. App'x 1005 (Fed. Cir. 2020) (nonprecedential), course PDF read in full
  - TC Heartland LLC v. Kraft Foods Group Brands LLC, 581 U.S. 258 (2017), course PDF read in full
  - https://www.supremecourt.gov/opinions/25pdf/608us2r45_i4dk.pdf (Hikma v. Amarin, 608 U.S. 580 (2026), official preliminary print)
  - https://www.law.cornell.edu/supremecourt/text/24-889 (Hikma v. Amarin, 2026)
  - https://www.supremecourt.gov/orders/26grantednotedlist.pdf (October Term 2026 granted list, as of Nov. 6, 2026)
  - https://www.law.cornell.edu/supremecourt/text/12-786 (Limelight v. Akamai, 2014)
  - https://www.law.cornell.edu/supremecourt/text/05-1056 (Microsoft v. AT&T, 2007)
  - https://www.law.cornell.edu/uscode/text/35/298
  - https://cases.justia.com/federal/appellate-courts/cafc/11-1629/11-1629-2012-12-04.pdf (Deere v. Bush Hog)
  - https://cases.justia.com/federal/appellate-courts/cafc/16-1275/16-1275-2017-09-29.pdf (Jang v. Boston Scientific)
  - https://cases.justia.com/federal/appellate-courts/cafc/17-129/17-129-2017-09-21.pdf (In re Cray)
  - full list in "Verification sources" at the end of this file
---

# How to use this file

Load it for FTO screens (Phase 2, FTO mode), infringement claim charts (`modules/analyze.md`), file-wrapper summaries (estoppel), and claim drafting (Phase 3), where claim wording decides later infringement reach. Give a supported, scope-specific infringement-risk assessment, not an unqualified clearance guarantee. Report element states (`literal`, `doe`, `partial`, `absent`, `unknown`) and name the doctrine that limits each `doe` cell.

Order of analysis the cases below enforce:
1. Construe the claim (Phillips is in the claims file; disclaimer cases are here).
2. Literal infringement: every limitation present in one accused product or one actor's method (all-elements rule).
3. Equivalents, limitation by limitation, and only after the four legal limits: vitiation/all-elements, prosecution history estoppel, dedication-disclosure, ensnarement.
4. Who is liable: direct (271(a)), induced (271(b)), contributory (271(c)), divided (attribution), export (271(f)), import of process products (271(g)), ANDA (271(e)(2)).
5. Where suit can be brought (venue) and what defenses apply (see `defenses.md`).

---

## 1. Literal infringement and claim scope

### Computer Docking Station Corp. v. Dell, Inc., 519 F.3d 1366 (Fed. Cir. 2008) · CB p. 770
- **Facts:** Claims recited a "portable computer" with a single docking connector. To get around a laptop reference (Herron), the applicants told the examiner their system left the display and keyboard as separate peripherals and contrasted it with laptops several ways. Every accused product was a laptop with a built-in screen or keyboard.
- **Holding / rule:** Prosecution disclaimer. A clear and unmistakable disavowal made to overcome art narrows the ordinary meaning of a claim term, here "portable computer" excludes machines with a built-in display or keyboard. Summary judgment of no literal infringement affirmed. The court refused to let the patentee construe claims "one way in order to obtain their allowance and in a different way against accused infringers."
- **Nuance:** Disclaimer must be unambiguous. Merely describing prior-art features without distinguishing on them is not enough. The court also said one clear distinction can be a disclaimer even when the applicant argued many distinctions, though piling on distinctions can make any single one less clear. The spec here reinforced the disclaimer (it called the invention a microcomputer, never a laptop). A spec with an express broad definition could have made the file-wrapper statements ambiguous and flipped the result.
- **Status:** Good law as of 2026-11-18; the clear-and-unmistakable disclaimer standard is applied routinely (Omega Eng'g v. Raytek, 334 F.3d 1314 (Fed. Cir. 2003)).
- **Skill rule:** FTO / claim charts: before charting, read every applicant argument in the file wrapper and list each statement that distinguishes the art on a feature the product has or lacks; a clear one narrows literal scope, not only equivalents. Prosecution: when distinguishing art, argue the one limitation that matters and avoid characterizing "the invention" globally.

### Akeva L.L.C. v. Nike, Inc., 817 F. App'x 1005 (Fed. Cir. 2020) (nonprecedential) · supplemental opinion
- **Facts:** Parent '126 patent addressed fast-wearing heels. Its abstract, summary, and every one of many embodiments used a detachable or rotatable rear sole and disparaged conventional one-piece soles. Accused Nike/adidas shoes had conventional fixed rear soles. In later continuations Akeva rewrote the specification to "rescind" a disclaimer that the court had found in an earlier family member (Akeva I, 2006), and told the examiner so in an IDS.
- **Holding / rule:** (1) Specification disclaimer: "rear sole secured" means fastened but not permanently fixed in position, so fixed soles are outside the claim. Disparaging the conventional design plus describing the invention uniformly with the feature excludes the conventional design, even when the claim word itself is generic. Claim differentiation did not help because the construed independent claim was still broader than the "detachably secured" dependents (it also covered rotatable, non-detachable soles). (2) A specification disclaimer cannot be undone in a continuation by amending the text. The rewrite adds new matter, so the continuation claims lose the parent's date. Nike's own earlier sales then anticipated them (on-sale bar).
- **Nuance:** The court distinguished prosecution disclaimers, which a patentee can rescind in a later application (Hakim v. Cannon Avent, 479 F.3d 1313 (Fed. Cir. 2007)) because the written-description support always existed. A specification disclaimer is different: it removes subject matter from what was disclosed, so priority continuity breaks. Nonprecedential, but it applies precedential rules (SciMed, Anascape, Lockwood). Note: this is not a repair/reconstruction case, although the patented feature was a replaceable sole.
- **Status:** Nonprecedential; principles drawn from precedential cases that remain good law as of 2026-11-18.
- **Skill rule:** FTO: when a continuation's claims read on the product but the family's earlier specification disparaged or excluded the product's design, flag the continuation's priority and anticipation risk (`[review]`) instead of treating it as a clean hit. Drafting spec: never disparage a conventional alternative or call one feature "the invention" unless you are willing to lose it from every claim in the family; describe benefits as advantages of some embodiments.

### Note cases on claim scope (compact)
- **Chef America, Inc. v. Lamb-Weston, Inc., 358 F.3d 1371 (Fed. Cir. 2004) · CB p. 768.** Claim said heat "the dough to" 400–850°F, which would burn it; the court enforced the words as written because only one reasonable reading existed. **Skill rule:** Drafting: read every process limitation literally for what object it modifies (dough vs. oven); courts will not redraft an obvious error.
- **North American Vaccine v. American Cyanamid, 7 F.3d 1571 (Fed. Cir. 1993); KCJ Corp. v. Kinetic Concepts, 223 F.3d 1351 (Fed. Cir. 2000) · CB p. 768–69.** "A"/"an" in a comprising claim normally means one or more (KCJ); North American Vaccine read "a" as singular from context and is treated as an outlier. **Skill rule:** Claim charts: treat "a" as "one or more" unless the spec or prosecution clearly limits it; flag any singular reading `[review]`.
- **Vitronics v. Conceptronic, 90 F.3d 1576 (Fed. Cir. 1996); Pitney Bowes v. Hewlett-Packard, 182 F.3d 1298 (Fed. Cir. 1999) · CB p. 769.** Intrinsic record first; expert testimony may explain technology but cannot contradict the intrinsic record. Phillips v. AWH (en banc 2005) is digested in the claims file. **Skill rule:** Analysis: rank sources claim → spec → file history → extrinsic, and never let a dictionary or expert override the spec.
- **SRI Int'l v. Matsushita, 775 F.2d 1107 (Fed. Cir. 1985) (en banc) · cited CB p. 818.** Infringement compares the accused product to the construed claims, not to the patentee's preferred embodiment or commercial product. **Skill rule:** FTO / claim charts: never chart the product against the patentee's product or figures; chart against claim language only.

### All-elements rule (literal)
- **Pennwalt Corp. v. Durand-Wayland, Inc., 833 F.2d 931 (Fed. Cir. 1987) (en banc) · CB p. 798.** Every limitation, or its substantial equivalent, must be in the accused device; equivalence is judged in the context of the whole claim, not against the invention "as a whole." **Skill rule:** FTO chart: one `absent` cell ends literal infringement of that claim; record it and move to the separate DOE pass, never round it up.

---

## 2. Doctrine of equivalents (DOE)

### Graver Tank & Mfg. Co. v. Linde Air Products Co., 339 U.S. 605 (1950) · CB p. 779
- **Facts:** Claimed welding flux required alkaline-earth-metal silicates. The accused flux swapped manganese silicate (not an alkaline earth metal) for magnesium silicate. Experts and literature showed the two were known substitutes for this purpose.
- **Holding / rule:** A product that does not literally infringe can still infringe if it performs substantially the same function in substantially the same way to obtain the same result. Equivalence is a question of fact, judged against the patent, the prior art, and the circumstances. Known interchangeability to persons skilled in the art is "an important factor."
- **Nuance:** The opinion stresses piracy and copying; Warner-Jenkinson later held that intent is irrelevant. Black and Douglas dissented. Unusual facts: a broader claim that literally covered manganese had been held invalid in Graver I (1949) for claiming inoperative species, so the patentee had in fact claimed the subject matter (J&J v. R.E. Service relies on this to reconcile Graver with the dedication rule). Graver also recognizes the reverse use of equivalence: a device so changed in principle that it works in a substantially different way can escape a claim that literally reads on it (339 U.S. at 608–09; see § 6).
- **Status:** Good law; reaffirmed in Warner-Jenkinson (1997) and Festo (2002).
- **Skill rule:** FTO DOE pass: for each non-literal limitation, record function, way, and result of the claimed element and of the substitute, plus evidence of known interchangeability (textbooks, prior art, the product's own literature); without element-level evidence mark the cell `unknown`, not `doe`.

### Warner-Jenkinson Co. v. Hilton Davis Chemical Co., 520 U.S. 17 (1997) · CB p. 783
- **Facts:** Ultrafiltration claim required pH "from approximately 6.0 to 9.0." The upper limit was added during prosecution to avoid a reference (Booth) operating above 9.0; the reason for the 6.0 floor was unclear. Accused process ran at pH 5.0.
- **Holding / rule:** (1) DOE survived the 1952 Act. (2) DOE applies element by element, never to the invention as a whole, and may not eliminate an element entirely. (3) Prosecution history estoppel applies to amendments made for a substantial reason related to patentability; the patentee bears the burden of showing a different reason, and if none is established the court presumes a patentability reason and estoppel bars equivalents for that element. (4) Intent and copying play no role. (5) Equivalence is measured at the time of infringement, so after-arising equivalents count. (6) Function-way-result and insubstantial differences are both acceptable frameworks; the question is whether each claimed element has an identical or equivalent counterpart.
- **Nuance:** The Court left to the Federal Circuit whether DOE goes to the jury (it does) and said legal limits (estoppel, vitiation) are for the court on summary judgment or JMOL. On remand the Federal Circuit reaffirmed that 5.0 could be equivalent to "approximately 6.0" without vitiating the limitation because the process worked as low as pH 2, and sent estoppel back for the patentee to try to explain the 6.0 floor (Hilton Davis v. Warner-Jenkinson, 114 F.3d 1161 (Fed. Cir. 1997), CB p. 794). An unexplained amendment is the worst fact for the patentee.
- **Status:** Good law; its estoppel framework was extended (not displaced) by Festo (2002).
- **Skill rule:** File-wrapper summaries: for every amended limitation record the stated reason for the amendment; if the record gives none, flag "presumed patentability reason, Warner-Jenkinson/Festo presumption applies." FTO: evaluate equivalence as of today's technology, not the filing date.

### Corning Glass Works v. Sumitomo Electric U.S.A., Inc., 868 F.2d 1251 (Fed. Cir. 1989) · CB p. 798
- **Facts:** Claim required a fused-silica core doped to raise its refractive index above the cladding. Sumitomo's S-3 fiber had an undoped core and lowered the cladding's index with fluorine, producing the same index differential.
- **Holding / rule:** No element was "missing." The equivalent of a limitation must exist somewhere in the accused device, but not necessarily in the corresponding component. Negative dopant in the cladding was held equivalent to positive dopant in the core; DOE infringement affirmed. "Element" can mean a single limitation or a group of limitations forming one component.
- **Nuance:** The all-elements rule is not a component-to-component matching test. The result depends on how the court parses the limitation: parse "core doped to exceed cladding" as one functional unit and the swap survives; parse "dopant in core" as its own element and it is missing. Pioneer status (the court called this a pioneering invention) may have helped.
- **Status:** Good law on its narrow point; later Federal Circuit cases frame vitiation as a conclusion that no reasonable jury could find equivalence rather than a free-standing exception (see Post-casebook, Deere v. Bush Hog).
- **Skill rule:** FTO DOE pass: when the accused product achieves a claimed relationship by moving the feature to a different part, do not mark the limitation `absent` automatically; mark `doe` with `construction_dependent` and give both parsings of the limitation.

### Note cases on DOE and vitiation (compact)
- **Moore U.S.A., Inc. v. Standard Register Co., 229 F.3d 1091 (Fed. Cir. 2000) · CB p. 795.** Claim required adhesive along "the majority" of the length; 47.8% could not be equivalent because a minority is the opposite of a majority. **Skill rule:** FTO: binary or antonym limitations (majority/minority, inside/outside, attached/detached) defeat DOE as a matter of law; mark `absent`, not `doe`.
- **Sage Products, Inc. v. Devon Industries, Inc., 126 F.3d 1420 (Fed. Cir. 1997) · CB p. 782, 814.** For a simple structural claim, a patentee who could have foreseen and claimed the variation bears the cost of not doing so; DOE denied. **Skill rule:** Drafting: for every structural limitation, list the obvious alternative placements and shapes and claim them generically or in dependents; DOE will not rescue foreseeable variants.
- **Festo panel opinion, 172 F.3d 1361 (Fed. Cir. 1999) (vacated on other grounds) · CB p. 803.** One two-way sealing ring could stand in for a claimed pair of one-way rings because it fully performed the claimed role; that all-elements point survived. **Skill rule:** FTO: a one-for-two (or two-for-one) structural swap is not automatically vitiation; analyze the limitation's role in the claim.
- **Actavis UK v. Eli Lilly, [2017] UKSC 48 · CB p. 796.** UK three-question equivalence test found infringement by other pemetrexed salts. **Skill rule:** All phases: never apply UK or EPO equivalence tests to US claims or vice versa (SKILL.md US-utility scope); note that a design-around valid in the US may not be valid in the UK.

---

## 3. Prosecution history estoppel (PHE)

### Festo Corp. v. Shoketsu Kinzoku Kogyo Kabushiki Co., 535 U.S. 722 (2002) · CB p. 804
- **Facts:** Festo's claims were narrowed in prosecution and reexamination to require a pair of one-way sealing rings and a magnetizable sleeve. SMC used one two-way ring and a non-magnetizable aluminum-alloy sleeve. The en banc Federal Circuit had made any narrowing amendment a complete bar to equivalents.
- **Holding / rule:** (1) Any narrowing amendment made to satisfy a Patent Act requirement, including § 112, can create estoppel; a purely cosmetic amendment that does not narrow does not. (2) Estoppel is not a complete bar. A narrowing amendment raises a presumption that the patentee surrendered all territory between the original and amended claim. (3) The patentee can rebut by showing that, at the time of amendment, one skilled in the art could not reasonably have been expected to draft a claim literally covering the equivalent: the equivalent was unforeseeable, the amendment's rationale bears no more than a tangential relation to it, or "some other reason" prevented describing it.
- **Nuance:** The burden is on the patentee at each step (reason for amendment under Warner-Jenkinson, then rebuttal under Festo). On remand Festo lost: the Federal Circuit (en banc) held the rebuttal questions are for the court, tangentiality is judged from the prosecution record, and a ring/sleeve equivalent noted in the record was not tangential (344 F.3d 1359 (Fed. Cir. 2003)); then both equivalents were held foreseeable, because an alternative is foreseeable if known in the field defined by the original claim scope even if its suitability for the amended purpose was unknown (493 F.3d 1368 (Fed. Cir. 2007)) · CB p. 813–14.
- **Status:** Good law as of 2026-11-18 (see Post-casebook for applications).
- **Skill rule:** File-wrapper summaries and FTO: for each narrowed limitation, record original text, amended text, the rejection it answered, and whether the accused substitute falls in the surrendered gap; a substitute that was known in the field at amendment time is presumptively barred, so mark the DOE cell `doe` only with a stated rebuttal theory (unforeseeable / tangential / other) and `[review]`.

### Note cases on PHE (compact)
- **Honeywell Int'l v. Hamilton Sundstrand, 370 F.3d 1131 (Fed. Cir. 2004) (en banc); 523 F.3d 1304 (Fed. Cir. 2008) · CB p. 814.** Rewriting a dependent claim in independent form and canceling the broader independent claim is a narrowing amendment that triggers the Festo presumption for the added limitation; the later panel barred DOE because the equivalent was foreseeable at the time. **Skill rule:** Prosecution / office-action response: warn the user that accepting an "allowable if rewritten in independent form" objection by canceling the parent creates estoppel as to the dependent's limitations; consider keeping or appealing the broad claim, or pursuing it in a continuation.
- **Argument-based estoppel (KCJ Corp. v. Kinetic Concepts, 223 F.3d 1351 (Fed. Cir. 2000); Festo en banc, 234 F.3d 558, 569 (Fed. Cir. 2000)) · CB p. 813.** Arguments alone, without amendment, can estop equivalents if they show a clear and unmistakable surrender. **Skill rule:** File-wrapper summaries: chart arguments as well as amendments; a clear "unlike the reference, our claim requires X" statement surrenders equivalents near X.

---

## 4. Dedication-disclosure rule

### Johnson & Johnston Assocs. v. R.E. Service Co., 285 F.3d 1046 (Fed. Cir. 2002) (en banc) · CB p. 815
- **Facts:** Claims recited "a sheet of aluminum" as the discardable substrate for copper foil. The spec said aluminum was preferred but stainless steel or nickel alloys "may be used." RES used steel; a jury found willful DOE infringement.
- **Holding / rule:** Subject matter disclosed in the specification but not claimed is dedicated to the public and cannot be recaptured through DOE. Reversed as a matter of law. YBM Magnex, to the extent inconsistent, overruled. The patentee's remedy is a broadening reissue within two years (§ 251) or a continuation claiming the disclosed alternative (§ 120), which Johnston had in fact filed.
- **Nuance:** Concurrences: Rader would have rested on foreseeability (a drafter who could foresee and claim a variant must claim it); Lourie doubted foreseeability would simplify anything. The aluminum limitation was never amended, so this is a limit on DOE independent of estoppel. Paradox: a patentee who discloses the alternative loses DOE for it, while one who stays silent about a known alternative may keep DOE. Maxwell v. J. Baker, 86 F.3d 1098 (Fed. Cir. 1996) (disclosed but unclaimed shoe-tab placement dedicated) is the rule's origin.
- **Status:** Good law; later cases require the disclosure to be specific enough that a skilled reader can identify the dedicated subject matter (see Post-casebook, PSC Computer; Eagle v. Slayback).
- **Skill rule:** FTO DOE pass: search the target patent's spec for the accused substitute (its name, genus, or synonyms); if the spec names it as an alternative and no claim covers it literally, mark DOE `barred — dedicated` and check pending continuations, which may still claim it literally. Drafting: every alternative named in the spec needs a claim (at least a dependent or a pending continuation) or it is given away.

### Note cases (compact)
- **YBM Magnex v. ITC, 145 F.3d 1317 (Fed. Cir. 1998) · CB p. 818.** Had limited Maxwell to distinct disclosed alternatives; overruled in relevant part by Johnson & Johnston. **Skill rule:** Analysis: never cite YBM Magnex for DOE coverage of disclosed-unclaimed matter.

---

## 5. Prior-art limit on equivalents: hypothetical claim and ensnarement

### Wilson Sporting Goods Co. v. David Geoffrey & Assocs., 904 F.2d 677 (Fed. Cir. 1990) · CB p. 824
- **Facts:** Claims required golf-ball dimples arranged so none intersect any great circle. Dunlop's balls had 60 dimples nicking great circles by thousandths of an inch; the jury found DOE infringement. A prior-art Uniroyal ball intersected great circles at a rate with no principled difference from Dunlop's.
- **Holding / rule:** A patentee cannot obtain through DOE coverage it could not lawfully have obtained from the USPTO by literal claims. Method: draft a hypothetical claim broad enough to literally cover the accused product; if that claim would have been unpatentable over the prior art (anticipated or obvious), the asserted range of equivalents is too broad. Judgment reversed.
- **Nuance:** The hypothetical claim is a tool, not a mandatory step (Key Mfg. v. Microdot, 925 F.2d 1444 (Fed. Cir. 1991)); it may broaden the claimed limitations only enough to reach the accused product and may not narrow any original limitation to dodge the art (Streamfeeder v. Sure-Feed, 175 F.3d 974 (Fed. Cir. 1999)) · CB p. 825–26. The defense matters only in crowded art where the slight expansion would capture an actual reference. Ensnarement limits DOE only; it says nothing about literal infringement or validity of the actual claim.
- **Status:** Good law; ensnarement is decided by the court (see Post-casebook, Jang v. Boston Scientific).
- **Skill rule:** FTO DOE pass: for each `doe` cell, write the hypothetical claim that would literally read on the product and test it against the closest art found in the screen; if a reference (or an obvious combination) falls inside it, mark DOE `ensnarement risk — likely barred` and cite the reference. Also run the "practicing the prior art" check: if the product does what an old reference does, DOE is very weak even though "practicing the prior art" is not itself a defense to literal infringement.

---

## 6. Reverse doctrine of equivalents (not excerpted in the casebook)

### Graver Tank, 339 U.S. 605, 608–09 (1950); SRI Int'l v. Matsushita, 775 F.2d 1107 (Fed. Cir. 1985) (en banc)
- **Rule:** A product that falls within the literal words of a claim may still escape infringement if it is so far changed in principle that it performs the same or a similar function in a substantially different way. It is a fact question. Under SRI, once literal infringement is shown the accused infringer must come forward with a prima facie case, while the patentee keeps the burden of persuasion.
- **Nuance:** A near-dead letter. The Federal Circuit has never affirmed a noninfringement judgment on reverse DOE: Tate Access Floors v. Interface Architectural Res., 279 F.3d 1357, 1368 (Fed. Cir. 2002) (calling it an "anachronistic exception, long mentioned but rarely applied"); Roche Palo Alto LLC v. Apotex, Inc., 531 F.3d 1372 (Fed. Cir. 2008) (same). Amgen v. Hoechst Marion Roussel, 314 F.3d 1313 (Fed. Cir. 2003), treated it as an available equitable fact question and rejected it on the merits. It is most plausible where a broad genus or functional claim literally reads on a later, fundamentally different technology; modern § 112 enablement and written-description limits (Amgen v. Sanofi, 2023, in the disclosure file) usually do that work at the validity stage instead.
- **Status:** Available in theory, never successful on appeal, as of 2026-11-18.
- **Skill rule:** FTO: never clear a literal hit on reverse-DOE grounds; at most note "reverse DOE argument conceivable (rarely successful)" and pair it with the stronger 112 invalidity attack on the over-broad claim.

---

## 7. Indirect infringement: inducement (271(b)) and contributory infringement (271(c))

Statutory frame (CB p. 826–27): 271(b) reaches whoever "actively induces infringement"; 271(c) reaches sale, offer, or import of a component or material that is a material part of the invention, known to be especially made or adapted for infringement, and not a staple article suitable for substantial noninfringing use. Both require an underlying direct infringement by someone. 271(d) says conduct that would be contributory infringement, and enforcing against it, is not misuse (see `defenses.md`).

### Global-Tech Appliances, Inc. v. SEB S.A., 563 U.S. 754 (2011) · CB p. 827
- **Facts:** Pentalpha bought SEB's cool-touch fryer abroad (an overseas model without US patent marking), copied all but its cosmetics, and got a right-to-use opinion from a lawyer it did not tell about the copying. The lawyer found no relevant patent. Pentalpha sold the fryers to Sunbeam and others for resale in the US.
- **Holding / rule:** Inducement under 271(b) requires knowledge that the induced acts constitute patent infringement (borrowing Aro II's knowledge requirement under 271(c)). Willful blindness satisfies the knowledge element: (1) the defendant subjectively believes there is a high probability that a fact exists, and (2) takes deliberate actions to avoid learning it. Deliberate indifference to a known risk (the Federal Circuit's test) is not enough. Affirmed on willful-blindness grounds.
- **Nuance:** Willful blindness is more than recklessness or negligence; the defendant must almost have known. The damning facts: copying an unmarked foreign model of a market-leading product, plus withholding the copying from opinion counsel. Kennedy dissented (willful blindness is not knowledge). An honest, fully informed clearance search that misses a patent is the opposite fact pattern.
- **Status:** Good law as of 2026-11-18. Knowledge requirement reaffirmed in Commil (2015). The "active steps" element was clarified in Hikma v. Amarin (2026) (see Post-casebook). 35 U.S.C. § 298 (AIA) bars using failure to obtain, or to present, advice of counsel to prove willfulness or intent to induce (civil actions filed on or after Jan. 14, 2013).
- **Skill rule:** FTO: when the user copied or benchmarked a competitor's product, tell them the screen must search that competitor's patents by assignee and by the product's features, and that hiding the copying from counsel or the search is evidence of willful blindness. Never suggest avoiding patent searches to preserve deniability.

### Commil USA, LLC v. Cisco Systems, Inc., 575 U.S. 632 (2015) · CB p. 837
- **Facts:** Cisco was found liable for inducing infringement of Commil's wireless-network method patent. It sought to show it believed in good faith that the patent was invalid.
- **Holding / rule:** A good-faith belief that the patent is invalid is not a defense to induced infringement. The scienter element concerns infringement, and infringement and validity are separate issues; letting belief in invalidity negate intent would undercut the presumption of validity and its clear-and-convincing standard. The Court reaffirmed Global-Tech: inducement requires knowledge of the patent and knowledge that the induced acts infringe (rejecting the Government's and Commil's argument that knowledge of the patent alone suffices).
- **Nuance:** A reasonable good-faith belief of non-infringement (for example, based on a claim construction) remains relevant to intent. The Court pointed accused inducers to proper channels: declaratory judgment, IPR, ex parte reexamination, or the invalidity defense. Scalia and Roberts dissented ("only valid patents can be infringed"). Invalidity, if proved, still defeats liability; it is a defense to liability, not to the intent element.
- **Status:** Good law as of 2026-11-18.
- **Skill rule:** FTO: when a screened patent looks invalid, report invalidity and non-infringement in separate sections and tell the user that an invalidity belief does not shield inducement exposure; recommend counsel weigh an IPR or declaratory judgment if the patent matters commercially.

### Note cases on indirect infringement (compact)
- **Aro Mfg. Co. v. Convertible Top Replacement Co., 377 U.S. 476 (1964) (Aro II) · CB p. 830, 928.** 271(c) requires knowledge that the combination is both patented and infringing; sellers of replacement tops for licensed GM cars were not liable (repair by licensed owners is not infringement), but were liable for tops sold for unlicensed Ford cars. **Skill rule:** FTO for component suppliers: trace each customer's authority (license, exhaustion) before assessing contributory exposure; no direct infringement means no indirect liability.
- **Distinguishing (b) and (c) · CB p. 835.** Inducement fits multi-use technology promoted for an infringing use; contributory infringement fits a component whose only substantial use infringes; anything under (c) could also be inducement. **Skill rule:** FTO: for a component with substantial noninfringing uses, contributory risk is low, so focus the inducement analysis on instructions, marketing, and configuration defaults.
- **Officer liability: Orthokinetics v. Safety Travel Chairs, 806 F.2d 1565 (Fed. Cir. 1986); Sensonics v. Aerosonic, 81 F.3d 1566 (Fed. Cir. 1996) (liability affirmed); Hoover Group v. Custom Metalcraft, 84 F.3d 1408 (Fed. Cir. 1996) (reversed) · CB p. 835–37.** Officers who personally and actively induce infringement can be liable under 271(b) without veil piercing; outcomes are fact-dependent. **Skill rule:** FTO report: note that individuals directing an infringing program can be named personally; keep the screen privileged.
- **Joy Technologies v. Flakt, 6 F.3d 770 (Fed. Cir. 1993) · CB p. 835.** Indirect liability is "dependent" on direct infringement. **Skill rule:** Claim charts: an inducement chart must identify the direct infringer and chart that party's acts.
- **Limelight Networks v. Akamai Techs., 572 U.S. 915 (2014) · CB p. 853.** No inducement of a method claim unless some single entity directly infringes under 271(a) (all steps performed by or attributable to one entity). See § 9.

---

## 8. Extraterritorial reach: 271(f), 271(g), and foreign activity

Baseline: US patents reach only making, using, selling, offering, or importing in or into the US (271(a)). Deepsouth Packing Co. v. Laitram Corp., 406 U.S. 518 (1972) · CB p. 841, held that making all parts of a shrimp deveiner in the US and shipping them unassembled abroad was not infringement; Congress answered with 271(f) (1984). 271(f)(1) parallels inducement; 271(f)(2) parallels contributory infringement (T.D. Williamson v. Laymon, 723 F. Supp. 587 (N.D. Okla. 1989), aff'd, 923 F.2d 871 (Fed. Cir. 1990)) · CB p. 841.

### Life Technologies Corp. v. Promega Corp., 580 U.S. 140 (2017) · CB p. 842
- **Facts:** Patented genetic-testing kit had five components. Life Technologies made one (Taq polymerase, a commodity enzyme) in the US and shipped it to its UK plant, which made the other four and assembled the kits.
- **Holding / rule:** "Substantial portion" in 271(f)(1) is quantitative, not qualitative, and a single component can never be "all or a substantial portion" of the components of a multicomponent invention. No 271(f)(1) liability.
- **Nuance:** The Court did not say how many components suffice. A single component can still trigger 271(f)(2) if it is especially made or adapted for the invention and not a staple. The Court called Taq "a single commodity article," which would keep it outside (f)(2) too, but (f)(2) was not the theory on appeal. The Federal Circuit had also held that a company can "actively induce" combination by its own foreign affiliate; the Supreme Court did not reach that question.
- **Status:** Good law as of 2026-11-18. Related: Microsoft v. AT&T (2007) and WesternGeco (2018), see Post-casebook. WesternGeco's damages holding is also in the remedies file.
- **Skill rule:** FTO for export supply chains: list every claim component, mark which ship from the US, and flag (f)(1) only when more than one component is supplied from the US and (f)(2) when any single custom (non-staple) component is supplied for overseas assembly.

---

## 9. Divided (joint) infringement

### Akamai Technologies, Inc. v. Limelight Networks, Inc., 797 F.3d 1020 (Fed. Cir. 2015) (en banc) · CB p. 849
- **Facts:** Content-delivery method claims. Limelight performed every step except "tagging" (and some "serving") of content, which its customers performed under Limelight's standard contract, welcome letter, hostname assignment, and step-by-step instructions, with Limelight engineers assisting.
- **Holding / rule:** Direct infringement of a method claim under 271(a) occurs when all steps are performed by or attributable to a single entity. Others' steps are attributable when the entity (1) directs or controls their performance, including by agency or contract, or by conditioning participation in an activity or receipt of a benefit on performance of a step and establishing the manner or timing of that performance; or (2) forms a joint enterprise with them (agreement, common purpose, community of pecuniary interest, equal right of control). Jury verdict against Limelight reinstated.
- **Nuance:** Attribution is a fact question. The "conditioning plus manner or timing" test was new; the court said other fact patterns may justify attribution. Background: the 2012 en banc court had allowed inducement without a single direct infringer; the Supreme Court reversed (Limelight, 2014). Earlier cases (BMC Resources v. Paymentech, 498 F.3d 1373 (Fed. Cir. 2007); Muniauction v. Thomson, 532 F.3d 1318 (Fed. Cir. 2008)) required agency or contractual obligation. System claims are analyzed differently: a party "uses" a system by putting it into service, controlling it as a whole and obtaining benefit, even if others possess components (Centillion Data Sys. v. Qwest, 631 F.3d 1279 (Fed. Cir. 2011)) · CB p. 853–54.
- **Status:** Good law as of 2026-11-18 (later applications in Post-casebook).
- **Skill rule:** Drafting claims: for any method that involves a user, customer, server, and third party, write at least one claim set whose every step one actor performs (server-side or user-side), plus a system claim; flag multi-actor method claims as weak. FTO: for a multi-actor method, identify who performs each step and whether the product conditions use on the customer's steps and sets their manner or timing (contracts, onboarding docs, required configuration).

---

## 10. Venue

### TC Heartland LLC v. Kraft Foods Group Brands LLC, 581 U.S. 258 (2017) · supplemental opinion
- **Facts:** Kraft sued TC Heartland, an Indiana entity headquartered in Indiana with no meaningful Delaware presence, in Delaware because it shipped accused drink-mix products there. The Federal Circuit, following VE Holding (1990), read § 1400(b)'s "resides" through the general venue statute's personal-jurisdiction definition (§ 1391(c)).
- **Holding / rule:** For purposes of the patent venue statute, 28 U.S.C. § 1400(b), a domestic corporation "resides" only in its State of incorporation. The 1988 and 2011 amendments to § 1391 did not change Fourco Glass v. Transmirra, 353 U.S. 222 (1957). VE Holding abrogated. Otherwise venue lies only where the defendant has committed acts of infringement and has a regular and established place of business. Unanimous (Gorsuch not participating).
- **Nuance:** Footnotes left open (i) how the rule applies to unincorporated entities (the parties suggested TC Heartland was actually an LLC; the Court decided on the pleaded corporate status) and (ii) foreign corporations (no opinion on Brunette Machine Works v. Kockum, 406 U.S. 706 (1972)). The Federal Circuit later filled these gaps (see Post-casebook: In re Cray, In re HTC, In re Google, In re Micron). § 1400(b) governs infringement suits against defendants; it does not govern declaratory-judgment actions by accused infringers, which use § 1391 (not addressed in the opinion; stated here as general background).
- **Status:** Good law as of 2026-11-18.
- **Skill rule:** FTO / litigation-risk notes: when profiling where a patentee could sue the user, list the user's state of incorporation plus each district with a physical, regular, established place of business of the user (not just sales); do not assume "anywhere the product is sold." Portfolio: note that a foreign entity can generally be sued in any district.

---

## 11. Hatch-Waxman and 271(e) (cross-reference)

- **271(e)(2):** Filing an ANDA or 505(b)(2) application (or a biosimilar application) for a drug claimed in a patent is an artificial act of infringement that lets the brand sue before launch. Digested in the Hatch-Waxman/BPCIA file (ch. 16).
- **271(e)(1) safe harbor:** uses reasonably related to developing and submitting information to the FDA are not infringement; digested in `defenses.md` (Roche v. Bolar and Merck v. Integra).
- **Skill rule:** FTO for drugs, biologics, and regulated devices: separate pre-approval development (often safe-harbored) from commercial manufacture, stockpiling, and launch (not safe-harbored), and route ANDA/Paragraph IV questions to the ch. 16 file.

### Also cited in ch. 12 (string cites; no separate digest)
Lemelson v. United States, 752 F.2d 1538 (Fed. Cir. 1985) (every element material); Dolly, Inc. v. Spalding & Evenflo, 16 F.3d 394 (Fed. Cir. 1994) and Athletic Alternatives v. Prince Mfg., 73 F.3d 1573 (Fed. Cir. 1996) (missing-limitation cases); International Visual Corp. v. Crown Metal Mfg., 991 F.2d 768 (Fed. Cir. 1993) (prior-art limit on equivalents); Kinzenbaw v. Deere & Co., 741 F.2d 383 (Fed. Cir. 1984) (DOE protects against unanticipated equivalents); Exhibit Supply Co. v. Ace Patents Corp., 315 U.S. 126 (1942) and Keystone Driller Co. v. Northwest Eng'g, 294 U.S. 42 (1935) (early file-wrapper estoppel); Graver Tank I, 336 U.S. 271 (1949) (broader claims invalid).

---

# Edge-case playbook (FTO-focused)

Each pattern: the trap, the correct analysis, the controlling case(s). These are the places a naive screen (or a non-lawyer) goes wrong.

1. **"Our product adds features the claim doesn't mention, so we're outside it."** Trap: extra features avoid infringement. Analysis: under an open "comprising" claim, extra structure is irrelevant; the only question is whether every recited limitation is present. Only a closed "consisting of" claim is avoided by additions. Controlling: all-elements rule (Pennwalt); Warner-Jenkinson (element-by-element).

2. **A claimed step happens "by itself."** The claim requires "drying" after painting. The user never runs a drying step, but residual heat dries the part in minutes. Trap: the step is missing, so there is no infringement. Analysis: first construe whether the step requires a deliberate act or only the result. If the result is enough, the step may be met literally. Otherwise test DOE for that step, and do not call it vitiation unless reading the step out would erase it. Mark the cell `construction_dependent`. Controlling: Warner-Jenkinson; Corning Glass.

3. **Same steps, different order.** Trap: reordering a method's steps avoids the claim. Analysis: steps are not limited to the order written unless the claim's logic or grammar requires it (e.g., a step acts on the product of an earlier one) or the spec clearly requires it. If order is not required, reordering is literal infringement. If it is required, the reordered process may still be a DOE equivalent when the order does not change function, way, or result (expert evidence needed). Controlling: Altiris, Inc. v. Symantec Corp., 318 F.3d 1363 (Fed. Cir. 2003) (order not implied absent logic or grammar); Warner-Jenkinson.

4. **A substitute became practical only after the patent issued.** Trap: the patentee could not have meant it, so it is outside the patent. Analysis: equivalence is judged at the time of infringement, so after-arising substitutes can be equivalents. If the limitation was narrowed by amendment, a substitute that was unforeseeable at amendment time can rebut the Festo presumption. Two separate checks can still bar DOE: (a) the spec names the substitute (dedication), and (b) the prior art already shows the combination with the substitute (ensnarement). Controlling: Warner-Jenkinson; Festo; Johnson & Johnston; Wilson Sporting Goods.

5. **The spec lists the user's material as an alternative, but the claims recite only the preferred one.** Trap: the patentee obviously contemplated it, so DOE covers it. Analysis: the reverse. Disclosed but unclaimed alternatives are dedicated to the public, so there is no DOE. But check every pending continuation and the two-year broadening-reissue window. The patentee can still claim the alternative literally there, subject to written description and intervening rights for reissues. Controlling: Johnson & Johnston (en banc); 35 U.S.C. §§ 120, 251, 252.

6. **The limitation the product avoids was added to get allowance.** Trap: the product is "close enough" for DOE. Analysis: a narrowing amendment for any patentability reason, including § 112 clarity, presumptively surrenders everything between the original and amended language. The patentee must prove the substitute was unforeseeable, tangential to the amendment's reason, or indescribable for some other reason. A substitute that was known in the field at amendment time is presumptively surrendered. Controlling: Festo (2002); Festo remand decisions (2003, 2007); Warner-Jenkinson (unexplained amendment presumed).

7. **"Allowable if rewritten in independent form."** The applicant canceled the broad claim and rewrote the dependent claim as independent. Trap: no words were narrowed, so there is no estoppel. Analysis: rewriting plus canceling the broader claim counts as a narrowing amendment. It triggers the Festo presumption for the dependent's added limitation. Controlling: Honeywell v. Hamilton Sundstrand (en banc 2004; 2008).

8. **Allowed on first action with no amendments or arguments.** Trap: no estoppel, so DOE is wide open. Analysis: no amendment-based estoppel is right. But DOE is still limited by the all-elements rule, dedication, and ensnarement. An examiner's unilateral statement in reasons for allowance generally does not narrow the claim by itself. Prosecution disclaimer and estoppel come from the applicant's statements. Controlling: Warner-Jenkinson; Johnson & Johnston; Wilson; Salazar v. Procter & Gamble Co., 414 F.3d 1342 (Fed. Cir. 2005) (examiner's unilateral remarks).

9. **Applicant arguments (no amendment) distinguished the art on a feature the product shares.** Trap: estoppel needs an amendment. Analysis: clear and unmistakable arguments can narrow literal scope (prosecution disclaimer) and can surrender equivalents (argument-based estoppel). Controlling: Computer Docking Station v. Dell; KCJ v. Kinetic Concepts; Festo en banc (2000).

10. **The product does exactly what an old reference does.** Trap: "practicing the prior art" is a defense to literal infringement. Analysis: it is not a defense to literal infringement. If the claim literally reads on the product, the remedy is to prove invalidity by clear and convincing evidence (anticipation if the old reference has every element). For DOE, the hypothetical-claim test bars any range of equivalents that would capture the reference. Controlling: Wilson Sporting Goods; Tate Access Floors (§ 6); Commil (validity is a separate issue).

11. **Numeric limits and words like "majority."** Trap: 47.8% is close to "a majority," and pH 5 is close to "about 6." Analysis: antonym-type limits (majority/minority) defeat DOE as a matter of law. Approximate ranges can stretch through DOE when evidence shows the process works the same way outside the range. That is what happened on remand in Hilton Davis. Controlling: Moore v. Standard Register; Warner-Jenkinson and its 1997 remand.

12. **The user moved the feature to a different part.** For example, the claim dopes the core, and the product dopes the cladding to get the same index difference. Trap: the claimed element is "missing," so no DOE. Analysis: an equivalent can sit in a different component if it serves the limitation's role. Analyze the limitation as a functional unit and give both parsings. Controlling: Corning Glass; Festo panel (1999) on the role of a two-for-one swap.

13. **The patentee's own product differs from its claims.** Trap: the screen compares the user's product with the patentee's product or figures. Analysis: infringement compares the accused product with the construed claims only. Controlling: SRI v. Matsushita (en banc); Johnson & Johnston.

14. **The spec disparages the conventional design the user uses, but the claim word is generic.** Trap: the plain claim term covers the conventional design. Analysis: uniform description of the invention with a feature, plus disparagement of the alternative, can be a specification disclaimer that narrows even a generic term. The patentee cannot rescind it in a continuation without adding new matter and losing priority. Controlling: Akeva v. Nike (nonprecedential, applying SciMed); Computer Docking (prosecution counterpart).

15. **A supplier sells only general-purpose (staple) materials plus instructions.** Trap: the materials have other uses, so the supplier is safe. Analysis: staple status defeats contributory infringement under 271(c), not inducement. Beyond someone's direct infringement, inducement still needs two things. First, knowledge of the patent and of the infringing nature of the acts (willful blindness counts; a charge letter sent to the customer may supply it once the supplier learns of it). Second, the supplier's own statements must actively encourage the infringing use. Instructions that step through the patented method can do that. Omissions, vague language, and statements that merely track legal requirements or standard industry practice cannot. Controlling: Global-Tech; Hikma v. Amarin (2026); Aro II; 35 U.S.C. § 271(b)–(c).

16. **The user copied a competitor and then got a clean opinion from counsel who wasn't told.** Trap: the opinion shields the user. Analysis: withholding the copying from counsel is classic evidence of willful blindness, so it supports both inducement and willfulness. Controlling: Global-Tech.

17. **"We think the patent is invalid, so we can keep selling and instructing customers."** Trap: a good-faith invalidity belief negates inducement intent. Analysis: it does not. Only a good-faith non-infringement belief bears on intent. Invalidity must be proved by clear and convincing evidence in court, or decided by the PTAB. Controlling: Commil.

18. **Steps are split between the user and its customers or cloud provider.** Trap: no single actor performs every step, so there is no infringement and no inducement. Analysis: steps are attributed to one entity that directs or controls the others. That includes conditioning use of the service on the customers' steps while setting their manner or timing through contracts, onboarding instructions, or required configuration. It also includes a joint enterprise. System claims are "used" by whoever puts the whole system into service and benefits from it. Controlling: Akamai (en banc 2015); Limelight (2014); Centillion.

19. **The user exports one component for assembly abroad.** Trap: any US-made component triggers 271(f). Analysis: one component can never be a "substantial portion" under (f)(1). A single component triggers (f)(2) only if it is especially made for the invention and not a staple. Shipping a software master that is copied abroad is analyzed separately (see Post-casebook, Microsoft v. AT&T). Controlling: Life Technologies v. Promega; Deepsouth (pre-271(f) baseline).

20. **"They can sue us anywhere we sell."** Trap: patent venue follows personal jurisdiction. Analysis: a domestic corporation can be sued only in its state of incorporation, or where it committed acts of infringement and has a regular and established place of business. Foreign defendants are treated differently. Controlling: TC Heartland; In re Cray and In re HTC (see Post-casebook).

21. **A pending continuation was amended after the patentee saw the user's product.** Trap: claims drafted to target a competitor are improper. Analysis: amending or adding claims to cover a competitor's product the applicant learned of is legitimate if the original disclosure supports the claims. Watch written description and any specification disclaimer (Akeva). Controlling: Kingsdown Medical Consultants v. Hollister Inc., 863 F.2d 867 (Fed. Cir. 1988) (nothing improper in amending or adding claims to cover a competitor's product learned of during prosecution, if the claims comply with the statute); Akeva.

22. **A broad functional claim literally reads on a fundamentally different later technology.** Trap: the user clears it under the reverse doctrine of equivalents. Analysis: reverse DOE is formally available but almost never succeeds. The realistic attack is § 112 (enablement or written description) on the over-broad claim. Controlling: Graver Tank (339 U.S. at 608–09); SRI v. Matsushita; Tate Access Floors.

23. **A generic or "skinny label" product, or any multi-use product whose marketing never mentions the patented use.** Trap: customers will foreseeably use it the patented way, and generic marketing ("equivalent to Brand X") reads as an instruction, so inducement is likely. Analysis: the question is whether the seller's own statements actively encouraged the infringing use, not how customers might read them. Carving the patented use out of the label, calling the product a generic equivalent, and citing total brand sales are not enough without statements that encourage the patented use. FTO screens must still read every label, website, sales deck, and press release for language that steps through the patented use. Controlling: Hikma v. Amarin (2026), rejecting the Federal Circuit's "could be read as instructions" trend it traced to GSK v. Teva (2021); Global-Tech.

---

# Post-casebook developments (verified 2026-11-18)

Entries marked "pre-edition" are older than the casebook but appear in it only as passing mentions or not at all. They are included because the skill needs them.

### Hikma Pharmaceuticals USA Inc. v. Amarin Pharma, Inc., 608 U.S. 580 (2026), No. 24-889 (argued Apr. 29, 2026; decided June 4, 2026; unanimous; Jackson, J.)
- **Facts:** Hikma launched a generic icosapent ethyl with a label carved out of Amarin's patented cardiovascular-risk indication (a "skinny label"). Amarin alleged inducement based on Hikma's label, website, and press releases (generic-equivalence statements and brand sales figures). The Federal Circuit had reinstated the complaint (Amarin Pharma v. Hikma Pharms., 104 F.4th 1370 (Fed. Cir. 2024)).
- **Holding / rule:** Reversed and remanded; no plausible claim of active inducement under 271(b). The question is whether the defendant's own statements actively encouraged infringing use, "not merely how others may understand those statements." Omissions, vague language, and statements that reflect legal requirements or standard industry practice do not suffice, nor does speculation about how providers will act.
- **Nuance:** The Court expressly rejected a Federal Circuit trend, citing GSK v. Teva, of asking whether statements could be read as instructions to infringe. It decided a pleading-stage case, and Hikma did not dispute direct infringement or intent before the Court (n. 2); statements that do encourage the patented use (instructions, promotion of the carved-out indication) can still support inducement.
- **Status:** Good law; rejects the "could be read" approach that GlaxoSmithKline v. Teva, 7 F.4th 1320 (Fed. Cir. 2021) (per curiam) (cert denied 2023), exemplifies, without expressly overruling GSK (n. 3), and reverses Amarin v. Hikma (2024), which the Federal Circuit then vacated on remand (No. 2023-1169, order of July 15, 2026); do not cite the 2024 opinion.
- **Skill rule:** FTO for generics and multi-use products: chart the seller's own statements (label, site, decks, press, sales scripts) for affirmative encouragement of the patented use; don't treat foreseeable customer use, generic-equivalence claims, or a carved-out label as inducement by themselves, and flag any statement that steps through the patented use.

### Deere & Co. v. Bush Hog, LLC, 703 F.3d 1349 (Fed. Cir. 2012)
- **Rule:** Vitiation is "not an exception to the doctrine of equivalents" but a legal conclusion that no reasonable jury could find the element equivalent. Saying an element is "missing" proves nothing by itself. Followed in Brilliant Instruments v. GuideTech, 707 F.3d 1342 (Fed. Cir. 2013).
- **Skill rule:** FTO DOE pass: never write "vitiated" as a label; explain why no reasonable factfinder could find the substitute equivalent (antonym, opposite structure, or the limitation read out entirely), or leave the cell `doe`/`unknown`.

### VLSI Technology LLC v. Intel Corp., 87 F.4th 1332 (Fed. Cir. 2023)
- **Rule:** A DOE verdict was reversed because the expert gave no particularized testimony and linking argument on "way." Calling a difference a mere "design choice" does not prove equivalence.
- **Skill rule:** Claim charts: a `doe` cell needs separate function, way, and result statements for that limitation, each tied to evidence; generic "performs the same function" text is a `[review]` defect.

### Ajinomoto Co. v. ITC, 932 F.3d 1342 (Fed. Cir. 2019) (cert denied 2020)
- **Rule:** The patentee rebutted the Festo presumption under the tangential-relation exception. The way the accused equivalent departed from the literal claim was tangential to the objectively apparent reason for the narrowing amendment. Dyk, J., dissented on that point.
- **Skill rule:** File-wrapper analysis: for each narrowing amendment, state the objectively apparent reason from the record (the specific art or 112 problem addressed); if the accused substitute differs on an axis unrelated to that reason, record tangentiality as a live rebuttal and downgrade estoppel from "barred" to "contested."

### Amgen Inc. v. Coherus BioSciences Inc., 931 F.3d 1154 (Fed. Cir. 2019)
- **Rule:** Argument-based estoppel barred DOE. Amgen clearly and unmistakably surrendered unclaimed salt combinations by arguing that its specific salt combinations distinguished the art. Estoppel can attach to each argument separately even when other arguments were also made.
- **Skill rule:** File-wrapper summaries: chart each separate argument; one clear argument surrenders equivalents even if the examiner relied on a different one.

### PSC Computer Prods. v. Foxconn Int'l, 355 F.3d 1353 (Fed. Cir. 2004); Eagle Pharms. v. Slayback Pharma, 958 F.3d 1171 (Fed. Cir. 2020)
- **Rule:** Dedication requires disclosure specific enough that a skilled reader could identify the subject matter disclosed but not claimed. A generic reference does not dedicate every member of the genus (PSC). Dedication is a question of law and can be decided on the pleadings without expert testimony (Eagle).
- **Skill rule:** FTO: quote the spec passage that names the accused substitute; a passing genus mention is `[review]`, a specific named alternative supports `barred — dedicated`.

### Jang v. Boston Scientific Corp., 872 F.3d 1275 (Fed. Cir. 2017)
- **Rule:** Ensnarement is a legal question for the court. The accused infringer must produce the prior art; the patentee bears the burden of persuading that the hypothetical claim would have been patentable. The hypothetical claim may not add narrowing limitations (reaffirming Streamfeeder: "Slight broadening is permitted at that point, but not narrowing").
- **Skill rule:** FTO: when building the hypothetical claim, broaden only the limitation at issue, never narrow another, and note that the patentee carries the persuasion burden.

### Eli Lilly & Co. v. Teva Parenteral Medicines, Inc., 845 F.3d 1357 (Fed. Cir. 2017)
- **Rule:** Applying Akamai, physicians direct or control patients' performance of a folic-acid pretreatment step because they condition the patented drug treatment on it. Generic makers whose labels instruct that regimen were liable for inducement.
- **Skill rule:** FTO for treatment-method claims: map physician and patient steps, and check whether the label makes one actor's step a condition of the other's treatment (attribution), then whether the label actively encourages it (Hikma).

### Microsoft Corp. v. AT&T Corp., 550 U.S. 437 (2007) (pre-edition)
- **Rule:** "Abstract software code is an idea without physical embodiment," so software in the abstract is not a 271(f) "component." Copies made abroad from a master shipped from the US are not "supplied from" the US.
- **Skill rule:** FTO for software exports: distinguish physical copies shipped from the US (possible 271(f)) from foreign-made copies of a US master (not 271(f)); check 271(a) for any US use or sale instead.

### WesternGeco LLC v. ION Geophysical Corp., 585 U.S. 407 (2018); Brumfield v. IBG LLC, 97 F.4th 854 (Fed. Cir. 2024)
- **Rule:** Lost foreign profits are recoverable for 271(f)(2) infringement because the statute's focus is domestic supply (WesternGeco). Brumfield extended the WesternGeco focus analysis to 271(a) and reasonable royalties, displacing Power Integrations. It still affirmed exclusion of the expert's foreign-damages testimony for failing to tie foreign sales to domestic infringing acts.
- **Skill rule:** FTO risk ranking: when a US act of infringement (a domestic sale, use, or supply) drives foreign revenue, flag that damages may reach that foreign revenue; do not assume exposure stops at US sales.

### Venue after TC Heartland
- **In re Cray Inc., 871 F.3d 1355 (Fed. Cir. 2017):** A "regular and established place of business" requires "(1) a physical place in the district; (2) … a regular and established place of business; and (3) … the place of the defendant." An employee's home office alone was not enough on those facts.
- **In re Micron Tech., 875 F.3d 1091 (Fed. Cir. 2017):** The TC Heartland venue objection was not "available" earlier, so Rule 12(h)(1) waiver did not apply; district courts keep discretion to find forfeiture.
- **In re HTC Corp., 889 F.3d 1349 (Fed. Cir. 2018):** Brunette reaffirmed; foreign defendants may be sued in any district.
- **In re Google LLC, 949 F.3d 1338 (Fed. Cir. 2020):** A place of business requires the regular, physical presence of an employee or other agent conducting the defendant's business. Servers alone, without such a person, are not enough.
- **Skill rule:** Litigation-risk notes: list the user's state of incorporation and each district where it has a physical place with employees or agents conducting its business; treat foreign affiliates as suable anywhere.

### Halo Electronics, Inc. v. Pulse Electronics, Inc., 579 U.S. 93 (2016); 35 U.S.C. § 298
- **Rule:** Enhanced damages are discretionary, reserved for egregious conduct, proved by a preponderance (Seagate test rejected). Under § 298, failure to obtain or present advice of counsel "may not be used to prove" willfulness or intent to induce (civil actions filed on or after Jan. 14, 2013).
- **Skill rule:** FTO report: tell the user that knowledge of a specific patent can later matter for willfulness and inducement, that the screen is not an opinion of counsel, and that § 298 means not getting an opinion cannot itself be used against them.

### Search result for January 2023 to November 2026
Hikma v. Amarin (2026) is the only Supreme Court or en banc Federal Circuit decision found in this file's topics: DOE, prosecution history estoppel, inducement or contributory infringement, 271(f), divided infringement, and venue. En banc decisions in the window, LKQ v. GM (2024, design-patent obviousness) and EcoFactor v. Google (2025, damages experts), belong to other files. The Supreme Court's granted-and-noted lists for October Terms 2022–2025 show no other Federal Circuit patent case in these topics (Amgen v. Sanofi, 2023, is enablement), and the October Term 2026 list (as of Nov. 6, 2026) shows no Federal Circuit case at all. Search confidence: the Supreme Court check is from those primary lists; the en banc check is from secondary sources and opinion downloads, so treat "none found" for en banc decisions as not exhaustive.

---

# Checklist for the skill (infringement)

- Construe first. Pull the claim, the full spec, and the file wrapper before charting. List every applicant argument and amendment that touches a limitation the product arguably lacks.
- Chart claim against product only, never product against the patentee's product or figures.
- Treat "comprising" as open. Treat "a/an" as one or more unless the record clearly says otherwise.
- Mark each limitation `literal`, `doe`, `partial`, `absent`, or `unknown`. One `absent` means no literal infringement of that claim. Never round it up.
- Method claims: check whether step order is required by logic, grammar, or spec before treating reordering as a design-around.
- Run DOE only after literal, and only limitation by limitation. Every `doe` cell needs function-way-result (or insubstantial-difference) evidence specific to that limitation. Without it, mark `unknown`.
- For every `doe` cell, run all four bars in order and record the result of each:
  1. Vitiation or all-elements (antonym limits, a limitation read out entirely).
  2. Prosecution history estoppel (amendment or argument; Festo presumption; rebuttal theory named).
  3. Dedication (substitute named in the spec but not claimed).
  4. Ensnarement (hypothetical claim versus the closest art found).
- For amended limitations with no stated reason in the record, apply the Warner-Jenkinson/Festo presumption.
- Check pending continuations, reissue windows (two years for broadening), and terminal disclaimers for every patent that shows a near miss. Those are where a near miss becomes literal coverage.
- Check specification disclaimers: disparaged alternatives and features described as "the invention." Check whether a continuation's spec was rewritten, which raises a priority-break risk (Akeva).
- Identify the direct infringer for every theory. For inducement, collect evidence of knowledge of the patent (letters, citations, marking, copying) and of the instructions or marketing. For contributory infringement, decide staple versus nonstaple.
- Never treat an invalidity belief as a shield against inducement. Report invalidity and infringement in separate sections.
- Multi-actor methods: map each step to an actor. Test attribution (direction or control, conditioning plus manner or timing, joint enterprise). Test system claims separately ("use" equals putting into service and benefiting).
- Supply chains: list where each component is made and assembled. Test 271(f)(1) (more than one component) and (f)(2) (custom non-staple component). Test 271(g) for imported products of a patented process (statute; not digested here).
- Venue: note state of incorporation and regular, established places of business. Never assume nationwide exposure for a domestic corporation.
- Willfulness hygiene: keep FTO screens confidential or privileged. Never advise avoiding searches. Never advise withholding facts (copying, benchmarking) from counsel.
- Never write "infringes," "does not infringe," or "clear." Use traffic lights per patent and the required banner (Phase 2, FTO mode).

---

## Verification sources (infringement)
- Hikma v. Amarin (2026): opinion (608 U.S. 580) https://www.supremecourt.gov/opinions/25pdf/608us2r45_i4dk.pdf ; https://www.law.cornell.edu/supremecourt/text/24-889 ; docket https://www.supremecourt.gov/search.aspx?filename=/docket/docketfiles/html/public/24-889.html
- Limelight v. Akamai (2014): https://www.law.cornell.edu/supremecourt/text/12-786
- Microsoft v. AT&T (2007): https://www.law.cornell.edu/supremecourt/text/05-1056
- WesternGeco (2018): https://www.law.cornell.edu/supremecourt/text/16-1011
- Halo (2016): https://www.law.cornell.edu/supremecourt/text/14-1513 ; 35 U.S.C. § 298: https://www.law.cornell.edu/uscode/text/35/298
- Deere v. Bush Hog: https://cases.justia.com/federal/appellate-courts/cafc/11-1629/11-1629-2012-12-04.pdf
- VLSI v. Intel: https://cases.justia.com/federal/appellate-courts/cafc/22-1906/22-1906-2023-12-04.pdf
- Festo remand (2003): https://www.law.berkeley.edu/files/Festo_(on_remand_from_S_Ct).pdf ; Festo (2007): https://cases.justia.com/federal/appellate-courts/cafc/05-1492/05-1492-2011-03-27.pdf
- Honeywell (en banc 2004): https://law.resource.org/pub/us/case/reporter/F3/370/370.F3d.1131.02-1082.02-1005.html
- Ajinomoto v. ITC: https://cases.justia.com/federal/appellate-courts/cafc/18-1590/18-1590-2019-08-06.pdf
- Amgen v. Coherus: https://cases.justia.com/federal/appellate-courts/cafc/18-1993/18-1993-2019-07-29.pdf
- PSC v. Foxconn: https://law.resource.org/pub/us/case/reporter/F3/355/355.F3d.1353.03-1089.html ; Eagle v. Slayback: https://cases.justia.com/federal/appellate-courts/cafc/19-1924/19-1924-2020-05-08.pdf
- Jang v. Boston Scientific: https://cases.justia.com/federal/appellate-courts/cafc/16-1275/16-1275-2017-09-29.pdf ; Streamfeeder: https://law.resource.org/pub/us/case/reporter/F3/175/175.F3d.974.98-1521.html
- Tate Access Floors: https://law.resource.org/pub/us/case/reporter/F3/279/279.F3d.1357.01-1275.html ; SRI v. Matsushita: https://law.resource.org/pub/us/case/reporter/F2/775/775.F2d.1107.84-1637.html ; Amgen v. HMR: https://law.resource.org/pub/us/case/reporter/F3/314/314.F3d.1313.01-1218.01-1191.html ; Roche Palo Alto v. Apotex: https://cases.justia.com/federal/appellate-courts/cafc/08-1021/08-1021-2011-03-27.pdf
- Eli Lilly v. Teva Parenteral: https://cases.justia.com/federal/appellate-courts/cafc/15-2067/15-2067-2017-01-12.pdf
- GSK v. Teva (2021): https://cases.justia.com/federal/appellate-courts/cafc/18-1976/18-1976-2021-08-05.pdf
- Brumfield v. IBG: https://cases.justia.com/federal/appellate-courts/cafc/22-1630/22-1630-2024-03-27.pdf
- In re Cray: https://cases.justia.com/federal/appellate-courts/cafc/17-129/17-129-2017-09-21.pdf ; In re HTC: https://cases.justia.com/federal/appellate-courts/cafc/18-130/18-130-2018-05-09.pdf ; In re Google: https://cases.justia.com/federal/appellate-courts/cafc/19-126/19-126-2020-02-13.pdf ; In re Micron: https://cases.justia.com/federal/appellate-courts/cafc/17-138/17-138-2017-11-15.pdf
- Altiris v. Symantec: https://law.justia.com/cases/federal/appellate-courts/F3/318/1363/608365/ ; Salazar v. P&G: https://law.justia.com/cases/federal/appellate-courts/F3/414/1342/622182 ; Omega v. Raytek: https://openjurist.org/334/f3d/1314
- Cert denials: Ajinomoto (CJ CheilJedang v. ITC, No. 19-1062, denied June 22, 2020) https://www.supremecourt.gov/docket/docketfiles/html/public/19-1062.html ; GSK v. Teva (Teva v. GlaxoSmithKline, No. 22-37, denied May 15, 2023) https://www.supremecourt.gov/docket/docketfiles/html/public/22-37.html
- EcoFactor v. Google (en banc, May 21, 2025): https://cases.justia.com/federal/appellate-courts/cafc/23-1101/23-1101-2025-05-21.pdf ; Supreme Court granted lists: https://www.supremecourt.gov/orders/grantednotedlists.aspx
- Kingsdown v. Hollister, 863 F.2d 867: https://static.case.law/f2d/863/cases/0867-01.json (competitor-claims passage read)
- Not verified this session (well-established, cited from the casebook or general knowledge): Honeywell cert petition outcome; GSK en banc-denial reporter cite.
