---
title: Nonobviousness (35 U.S.C. 103) — case law and edge cases
last_verified: 2026-11-18
sources:
  - Adelman et al., Patent Law — Cases and Materials (5th ed.), ch. 7 (used for case selection only; digests are original)
  - https://www.uspto.gov/web/offices/pac/mpep/s2141.html (MPEP 2141-2141.03, R-01.2024: Graham, KSR, Bigio, Clay, Airbus, Donner, Wyers, Environmental Designs still cited)
  - https://www.uspto.gov/web/offices/pac/mpep/s2143.html (MPEP 2143, R-01.2024: Kubin, Ortho-McNeil, Takeda, Eisai cited for obvious-to-try and lead-compound examples)
  - https://www.uspto.gov/web/offices/pac/mpep/s2144.html (MPEP 2144-2144.09, R-01.2024: Dillon, Papesch, Stemniski still cited)
  - https://www.govinfo.gov/content/pkg/FR-2024-02-27/html/2024-03967.htm (USPTO, Updated Guidance for Making a Proper Determination of Obviousness, 89 FR 14449 (Feb. 27, 2024))
  - https://www.govinfo.gov/content/pkg/USCOURTS-ca13-17-01333/pdf/USCOURTS-ca13-17-01333-0.pdf (Orexo AB v. Actavis Elizabeth LLC, 903 F.3d 1265 (Fed. Cir. 2018))
  - https://www.knobbe.com/blog/presumption-nexus-secondary-considerations-improper-when-commercial-product-includes-unclaimed (Fox Factory v. SRAM, 944 F.3d 1366 (Fed. Cir. 2019))
  - https://www.knobbe.com/blog/acorda-therapeutics-inc-v-roxane-laboratories-inc/ (Acorda v. Roxane, 903 F.3d 1310 (Fed. Cir. 2018))
  - https://www.sternekessler.com/news-insights/insights/raytheon-technologies-corp-v-general-electric-co-993-f3d-1374-fed-cir/ (Raytheon v. GE, 993 F.3d 1374 (Fed. Cir. 2021))
  - https://www.govinfo.gov/content/pkg/USCOURTS-ca13-21-01360/pdf/USCOURTS-ca13-21-01360-0.pdf (Teva v. Corcept, 18 F.4th 1377 (Fed. Cir. 2021), No. 21-1360, decided Dec. 7, 2021)
  - https://www.sternekessler.com/news-insights/insights/2024-federal-circuit-ip-appeals-lkq-corporation-v-gm-global-technology-operations-llc-102-f-4th-1280-fed-cir-2024-en-banc-stoll/ (LKQ v. GM, 102 F.4th 1280 (Fed. Cir. 2024) (en banc))
  - https://www.govinfo.gov/content/pkg/USCOURTS-ca13-23-02186/pdf/USCOURTS-ca13-23-02186-0.pdf (Agilent v. Synthego, No. 23-2186 (Fed. Cir. June 11, 2025))
  - https://cases.justia.com/federal/appellate-courts/cafc/23-1208/23-1208-2025-04-23.pdf (Qualcomm v. Apple, Nos. 23-1208, -1209 (Fed. Cir. Apr. 23, 2025))
  - https://www.cooley.com/news/insight/2025/2025-01-21-precedential-federal-circuit-decision-overturns-lack-of-written-description-based-on-later-discovered-technology (In re Entresto, 125 F.4th 1090 (Fed. Cir. 2025), obviousness affirmed)
---

# How to use this file

Doctrine, MPEP rationales A–G, chart templates, and 2024–2026 rule changes live in `../novelty-and-obviousness.md` (sections 5–7). This file adds what the cases teach: where each rule stops, the losing argument, and the fact that flips the result. Load it for Phase 2 103 analysis, invalidity mode, Phase 3 self-attack on draft claims, and any office action with a 103 rejection. Enablement and written description cases are in `specification-112.md`; anticipation is in `anticipation.md`.

Order the cases enforce for every 103 question:
1. Fix the date. AIA patents: obviousness "before the effective filing date." Pre-AIA patents: "at the time the invention was made."
2. Graham facts: scope and content of the (analogous) art, differences, level of ordinary skill, objective indicia. Find all four before concluding.
3. A reason a skilled person would have combined or modified the art as claimed, with a reasonable expectation of success, articulated from the pre-filing record (KSR, Orexo).
4. Objective indicia with nexus, weighed with everything else, never as an afterthought (Transocean).
5. Assess the claim combination as a whole. Give the strongest supported objection, applicant response and resolution. State a conditional likely-obvious or likely-nonobvious assessment when justified; identify the actual evidentiary limits. See `../examiner-review.md`.

---

## 1. The historical "invention" standard (pre-1952)

### Hotchkiss v. Greenwood, 52 U.S. (11 How.) 248 (1851) · CB p. 314
- **Facts:** Patent on door knobs made of clay or porcelain, attached by a known dovetail shank. The knob material was the only change; knobs of metal and wood with the same shank were old.
- **Holding / rule:** Substituting a known, better material in a known article, with no new mode of operation, is the work of a skilled mechanic, not an inventor. The patent was invalid even though the clay knob was cheaper and better.
- **Nuance:** The defect was not novelty but too small a step. Better or cheaper results alone did not save it. A material swap that needed a new construction, or that produced an unexpected property, would have changed the analysis (compare Adams, below).
- **Status:** Codified and replaced by § 103 (1952). Graham says § 103 codified the Hotchkiss principle; the word "invention" as a test is gone. Good law only as background, as of 2026-11-18.
- **Skill rule:** Invalidity and lite search: when the only difference over the art is a known material or a known substitute doing its known job, flag high 103 exposure and look for an unexpected property before treating the difference as meaningful.

### Great A. & P. Tea Co. v. Supermarket Equipment Corp., 340 U.S. 147 (1950) · CB p. 318
- **Facts:** Grocery checkout counter with a bottomless three-sided rack that pushes groceries to the cashier. The trial court found every element old but held the combination patentable.
- **Holding / rule:** A combination of old elements that each perform their old function, with nothing more than the sum of their parts, is unpatentable. Commercial success and adoption could not save it. Justice Douglas's concurrence (with Black) treated "invention" as a constitutional standard.
- **Nuance:** The "synergy" or "exceeds the sum of its parts" idea was rejected as a test by the early Federal Circuit (Chore-Time, Medtronic, CB p. 346), then partly revived when KSR cited A&P, Anderson's-Black Rock, and Sakraida. Use it as a way to ask whether the elements interact, not as a required "synergy" showing.
- **Status:** Pre-1952-Act standard superseded by § 103 (Graham). Its combination reasoning survives through KSR. As of 2026-11-18.
- **Skill rule:** Analysis: for a combination claim, chart whether any element changes how another works; if each element just does its own job, expect a KSR "predictable results" rejection (rationale A) and plan the response around interaction or unexpected results.

### Note cases (historical)
- Cuno Eng'g Corp. v. Automatic Devices Corp., 314 U.S. 84 (1941) (CB p. 317): "flash of creative genius" test. Abolished by § 103's last sentence: patentability is not negated by the manner in which the invention was made (Graham). **Skill rule:** never discount an invention because it came from routine testing, accident, or brute-force iteration; ask only whether the result would have been obvious.
- Atlantic Works v. Brady, 107 U.S. 192 (1883) and the other "inventive genius" formulations (CB pp. 317, 320): show why the 1952 Act replaced "invention" with obviousness. Do not use "inventive" or "genius" language in reports.
- String cites, same point (CB pp. 316–317): Smith v. Goodyear Dental Vulcanite, 93 U.S. 486 (1876); Hollister v. Benedict & Burnham, 113 U.S. 59 (1885); McClain v. Ortmayer, 141 U.S. 419 (1891); Ansonia Brass & Copper v. Electrical Supply, 144 U.S. 11 (1892); Jungersen v. Ostby & Barton, 335 U.S. 560 (1949) (Jackson, J., dissenting); Harries v. Air King Prods., 183 F.2d 158 (2d Cir. 1950) (L. Hand, J.); Thurber Corp. v. Fairchild Motor, 269 F.2d 841 (5th Cir. 1959).

---

## 2. The modern framework: Graham and KSR

### Graham v. John Deere Co., 383 U.S. 1 (1966) · CB p. 322
- **Facts:** Spring clamp for chisel plows. The claimed change over Graham's own earlier '811 patent and the Glencoe device was inverting the shank and hinge plate. In court, Graham argued a "free-flexing" advantage he never mentioned in the spec or to the examiner.
- **Holding / rule:** § 103 codified Hotchkiss without changing the level of innovation required. Obviousness is a legal question built on factual inquiries: "the scope and content of the prior art are to be determined," the differences ascertained, and the level of ordinary skill resolved. Secondary considerations (commercial success, long-felt need, failure of others) "may have relevancy." The plow claim was obvious.
- **Nuance:** (1) The flexing argument failed as an "afterthought": no hint of it in the spec, not argued to the PTO, and undercut by the patentee's own experts. (2) Glencoe was not before the examiner, which weakened the deference owed to the grant. (3) The companion cases split: Adams (wet battery) was nonobvious; Calmar/Cook Chemical (sprayer) was obvious because the narrow difference over prior art could not be saved by commercial success.
- **Status:** Good law; the four-factor framework is applied in every 103 case and in MPEP 2141 (R-01.2024). LKQ (2024) extended it to design patents. As of 2026-11-18.
- **Skill rule:** Drafting spec: state every functional advantage of each key structural choice in the spec itself, so it can be argued later without the "afterthought" label. Invalidity: search for art the examiner never saw; an uncited reference stronger than the cited art is the best attack.

### United States v. Adams, 383 U.S. 39 (1966) · discussed in KSR, CB p. 340
- **Rule:** A wet battery using water and magnesium/cuprous chloride electrodes was nonobvious. Known elements worked together in an unexpected and fruitful way, and the art taught away (water-activated batteries were thought impractical). **Skill rule:** Office actions: when the art discouraged the substituted element, argue teaching away with quotes, and pair it with test data on the unexpected result.

### Anderson's-Black Rock, Inc. v. Pavement Salvage Co., 396 U.S. 57 (1969); Sakraida v. Ag Pro, Inc., 425 U.S. 273 (1976) · discussed in KSR, CB p. 340
- **Rule:** A radiant heater on a paving machine (Anderson's) and a water-flush barn floor (Sakraida) were obvious: old elements each did what they always did, with no new interaction. **Skill rule:** Invalidity: cite these with KSR when the claimed elements operate independently, sequentially, and as expected.

### KSR International Co. v. Teleflex Inc., 550 U.S. 398 (2007) · CB p. 332
- **Facts:** Claim to an adjustable gas pedal (Asano) with an electronic sensor on a fixed pivot point. Sensors on pedals were known (Smith, Rixon, '936 patent); wire chafing taught putting the sensor on a nonmoving part. The Federal Circuit had reversed summary judgment of obviousness under a rigid teaching-suggestion-motivation (TSM) test.
- **Holding / rule:** Reversed. TSM is a helpful insight, not a mandatory formula. The analysis may consider the inferences and creative steps of a skilled person, design needs, market pressure, and common sense. A combination of familiar elements by known methods is likely obvious when it yields predictable results; the question is whether the improvement is more than "the predictable use of prior art elements according to their established functions." The skilled person is "a person of ordinary creativity, not an automaton." Obvious to try can be obvious where there is a design need and a "finite number of identified, predictable solutions." Summary judgment is proper when Graham facts are not materially disputed, even against a conclusory expert affidavit.
- **Nuance:** (1) Any need or problem known in the field can supply the reason to combine, not only the problem the patentee was solving. (2) Teaching away needs more than showing the base reference was inferior to the patentee's preferred embodiment; judging Asano against Engelgau's design would itself be hindsight. (3) The Court still requires an explicit, articulated reason; conclusory statements do not suffice. (4) The Court noted, without deciding, that the presumption of validity's rationale is "much diminished" when the key art was never before the examiner. (5) Hindsight remains forbidden.
- **Status:** Good law; the controlling 103 framework. USPTO restated it in the Feb. 27, 2024 guidance (89 FR 14449), and MPEP 2143 rationales A–G derive from it. As of 2026-11-18.
- **Skill rule:** Every 103 chart: name the KSR rationale for each gap and write the reason to combine in one sentence tied to a cited passage or a documented design need; if you cannot write that sentence from the pre-filing record, mark the combination "weak" rather than reaching for common sense.

### In re Translogic Technology, Inc., 504 F.3d 1249 (Fed. Cir. 2007) · CB p. 349
- **Facts:** Reexamination of claims to a series of 2:1 multiplexers built from transmission-gate multiplexers (TGMs). Gorai (a logic-synthesis paper) showed series 2:1 multiplexers; Weste (a 1985 textbook) showed the TGM circuit.
- **Holding / rule:** Obvious. A skilled designer needing a 2:1 multiplexer for each Gorai stage would pick a well-known circuit such as the TGM, "pursu[ing] known options within his or her technical grasp." A reference addressing a different problem (logic design rather than improving a multiplexer) is still prior art and still relevant; it does not "teach away" by focusing elsewhere.
- **Nuance:** The patentee's argument (Gorai solved a different problem, so it is irrelevant) is the exact error KSR corrected. Textbooks count as strong evidence of what was conventional. The flexible TSM test still operates after KSR.
- **Status:** Good law; frequently cited post-KSR application. No negative history found. As of 2026-11-18.
- **Skill rule:** Deep search: include textbooks, handbooks, and standard references (NPL) to prove an element was a conventional building block; Office actions: do not argue that a reference is irrelevant because it addresses a different problem unless you can also show non-analogous art or teaching away.

### Orexo AB v. Actavis Elizabeth LLC, 903 F.3d 1265 (Fed. Cir. 2018) · CB p. 354
- **Facts:** Zubsolv sublingual tablet: buprenorphine microparticles on citric-acid carrier particles, plus naloxone in the known 4:1 ratio. Each ingredient was known; no reference used citric acid as a carrier. The patent showed 66% higher bioavailability and bioequivalence at 29% less drug.
- **Holding / rule:** Reversed the district court's obviousness judgment. The question is "whether the prior art suggested the selection and combination achieved by the [patent's] inventors," not whether references separately taught components. An expert's view that citric acid would work if chosen, or that a skilled person "would not have excluded" it, is not a reason to choose it (In re Gordon). Also: "recognizing a need does not render the solution obvious."
- **Nuance:** (1) The trial court wrongly treated the 66% bioavailability gain as a mere "difference in degree." (2) An unclaimed benefit (keeping the 4:1 ratio) still mattered to motivation. (3) Objective indicia are part of the whole analysis, not an afterthought (Leo Pharm. v. Rea). (4) Actavis conceded at argument that no reference taught citric acid as a carrier; without that concession the case is closer. Use Orexo as a patentee-side anchor, and expect challengers to cite KSR's flexibility against it.
- **Status:** Good law (precedential). No negative history found. As of 2026-11-18.
- **Skill rule:** Analysis and office actions: separate "could" from "would"; for each missing element, demand a reason to select it from among the alternatives, and treat "it would work" or "nothing excludes it" as no motivation at all.

### Note cases (framework)
- Environmental Designs, Ltd. v. Union Oil Co., 713 F.2d 693 (Fed. Cir. 1983) (CB p. 330): six factors for the level of ordinary skill (inventor's education, problems in the art, prior solutions, pace of innovation, sophistication, education of active workers). Still cited in MPEP 2141.03 with In re GPAC. **Skill rule:** state the level of skill explicitly in every 103 analysis, with the factors that support it.
- Pro-Mold & Tool Co. v. Great Lakes Plastics, 75 F.3d 1568 (Fed. Cir. 1996); Motorola v. Interdigital, 121 F.3d 1461 (Fed. Cir. 1997) (CB p. 331): pre-KSR TSM sources (the references, skilled knowledge, the nature of the problem); the suggestion may be implicit. Still consistent with KSR.
- In re Lee, 277 F.3d 1338 (Fed. Cir. 2002) (CB p. 347): required record support rather than "common sense." KSR allows common sense, but later cases (Arendi v. Apple, 832 F.3d 1355 (Fed. Cir. 2016)) limit common sense to filling a minor gap with reasoned explanation. **Skill rule:** never rely on common sense to supply a missing claim limitation that matters; find a reference.
- Chore-Time Equip. v. Cumberland Corp., 713 F.2d 774 (Fed. Cir. 1983); Medtronic v. Cardiac Pacemakers, 721 F.2d 1563 (Fed. Cir. 1983) (CB p. 346): no separate "combination patent" standard and no synergy requirement. Still true; synergy is evidence, not a requirement.
- Apple Inc. v. Samsung Elecs. Co., 839 F.3d 1034 (Fed. Cir. 2016) (en banc) (CB pp. 353, 382): motivation to combine and what a reference teaches are fact questions; the appellate court cannot reweigh a jury's supported findings; strong objective indicia (copying, praise, commercial success, long-felt need) can tip the balance. **Skill rule:** in litigation-oriented analysis, separate fact findings from the legal conclusion and note which side has the burden.
- In re Gordon, 733 F.2d 900 (Fed. Cir. 1984) (cited in Orexo, CB p. 362): that the art "could be so modified" is not enough without a suggestion that the change is desirable. Also: a change that makes the primary reference unsatisfactory for its intended purpose undercuts motivation (MPEP 2143.01). **Skill rule:** Office actions: check whether the examiner's modification breaks the primary reference's purpose or principle of operation.
- Interconnect Planning Corp. v. Feil, 774 F.2d 1132 (Fed. Cir. 1985) (CB p. 360): the inventor's blueprint cannot be the roadmap for combining references. **Skill rule:** invalidity: build the combination from the art's own teachings in time order; never cite the patent under attack as the source of the reason to combine.

---

## 3. Objective indicia (secondary considerations) and nexus

### Transocean Offshore Deepwater Drilling, Inc. v. Maersk Drilling USA, Inc., 699 F.3d 1340 (Fed. Cir. 2012) · CB p. 365
- **Facts:** Dual-activity drilling rig: two tubular advancing stations under one derrick plus a pipe-transfer assembly. An earlier appeal (Transocean I, 617 F.3d 1296 (Fed. Cir. 2010)) held that Horn plus Lund taught every element and gave a motivation, a prima facie case. On remand a jury found seven objective indicia; the district court granted JMOL of obviousness.
- **Holding / rule:** Reversed. A prima facie case is not the conclusion; the factfinder must weigh it with the objective evidence. Objective indicia "must always when present be considered" (Stratoflex) and can be the most probative evidence. Substantial evidence supported commercial success, praise, unexpected results, copying, skepticism, licensing, and long-felt need, each tied to the claimed dual-activity feature.
- **Nuance:** How nexus was proven is the lesson: (1) a 12% price premium for the dual-activity rig over a single-activity rig in contracts signed the same day, and rate cuts when the feature was unavailable; (2) praise and copying documents that named the claimed dual-activity feature and distinguished the prior art's "dual drilling"; (3) licenses with royalties above litigation cost and from companies under no threat; (4) skepticism from industry fears of string "clashing." A foreign office's rejection is irrelevant to commercial success. Copying counted even though Maersk copied because it believed the patents invalid. The court admitted that it has "rarely held" objective evidence enough to overcome a prima facie case; a dissent in Apple v. Samsung called Transocean the only such case at that time.
- **Status:** Good law. Presumption-of-nexus rules were tightened later (Fox Factory, 2019, below). As of 2026-11-18.
- **Skill rule:** Prosecution and portfolio: when the client's product sells, collect nexus evidence tied to claim language (price premium for the claimed feature, customer requests naming it, competitor documents naming it); in any Rule 132 declaration, link each fact to a specific claim limitation, not to the product as a whole.

### Note cases (objective indicia), CB pp. 377–382
- Stratoflex, Inc. v. Aeroquip Corp., 713 F.2d 1530 (Fed. Cir. 1983): objective evidence is considered with all the evidence, not only when the decision-maker is in doubt.
- Iron Grip Barbell Co. v. USA Sports, 392 F.3d 1317 (Fed. Cir. 2004): commercial success needs nexus to the merits of the claimed invention. Mintz v. Dietz & Watson, 679 F.3d 1372 (Fed. Cir. 2012): objective evidence can rebut a prima facie case; beware hindsight.
- Tec Air, Inc. v. Denso Mfg., 192 F.3d 1353 (Fed. Cir. 1999): objective evidence alternatively rebutted any prima facie case.
- Copying: Specialty Composites v. Cabot Corp., 845 F.2d 981 (Fed. Cir. 1988) (copying can be strong evidence); Pentec, Inc. v. Graphic Controls Corp., 776 F.2d 309 (Fed. Cir. 1985) (weak when the accused product differs and infringement is denied). **Skill rule:** treat copying as strong only if the copier took the claimed feature specifically.
- Failure of others: Panduit Corp. v. Dennison Mfg., 774 F.2d 1082 (Fed. Cir. 1985), vacated on other grounds, 475 U.S. 809 (1986) (strong evidence); In re Sneed, 710 F.2d 1544 (Fed. Cir. 1983) (weak if those who "failed" lacked motivation or knowledge). The failures must target the same problem.
- Licensing: Pentec; EWP Corp. v. Reliance Universal, 755 F.2d 898 (Fed. Cir. 1985): licenses taken to avoid litigation, or bundled in cross-licenses, carry little weight.
- Long-felt need: Northern Telecom v. Datapoint, 908 F.2d 931 (Fed. Cir. 1990); Leinoff v. Louis Milona & Sons, 726 F.2d 734 (Fed. Cir. 1984) (an invention can create a new need and still be nonobvious). The need must match the problem the claims solve.
- Unexpected results: Burlington Indus. v. Quigg, 822 F.2d 1581 (Fed. Cir. 1987); Specialty Composites. Compare to the closest prior art and keep the showing commensurate with claim scope (MPEP 716.02).
- Skepticism: In re O'Farrell, 853 F.2d 894 (Fed. Cir. 1988): expert doubt expressed before the invention is especially persuasive and rare.
- Whose sales: Truswal Sys. v. Hydro-Air Eng'g, 813 F.2d 1207 (Fed. Cir. 1987) (Rich, J., dissenting); Syntex v. Paragon Optical, 7 U.S.P.Q.2d 1001 (D. Ariz. 1987): infringers' sales may count once infringement is proved.
- Simultaneous invention: Monarch Knitting Mach. v. Sulzer Morat, 139 F.3d 877 (Fed. Cir. 1998): near-simultaneous independent development is evidence of obviousness. **Skill rule:** invalidity: search for independent same-time solutions (papers, competitor filings within months) and present them as objective evidence for the challenger.
- Prima facie case procedure: In re Oetiker, 977 F.2d 1443 (Fed. Cir. 1992); In re Piasecki, 745 F.2d 1468 (Fed. Cir. 1984): in examination the examiner must first make a prima facie case; the burden of production then shifts; patentability is decided on the whole record by a preponderance. **Skill rule:** Office actions: first test whether the examiner made a prima facie case (all limitations, articulated reason); only then decide whether evidence is needed.

---

## 4. Chemical compounds: structural obviousness

### In re Papesch, 315 F.2d 381 (C.C.P.A. 1963) · CB p. 384
- **Facts:** Claimed triethyl compound was a homolog of a prior-art trimethyl compound (difference of three CH2 groups), so "structurally obvious." Affidavit data showed the triethyl compound had potent anti-inflammatory activity while the prior-art compound had none.
- **Holding / rule:** Reversed the rejection. "A compound and all of its properties are inseparable." A presumption of similarity drawn from formulas must yield to evidence of actual differences in properties. The applicant could have product claims, not only method-of-use claims.
- **Nuance:** Papesch is about whether property evidence must be considered, not about what makes a prima facie case (Dillon). The comparison was against the closest prior-art compound and showed a difference in kind (active vs. inactive).
- **Status:** Good law; cited in MPEP 2144.08 (R-01.2024) and reaffirmed by Dillon. As of 2026-11-18.
- **Skill rule:** Drafting chem/pharma: run and report side-by-side data against the closest prior-art compound in the spec (or plan a Rule 132 declaration), because properties, not formulas, decide structural obviousness.

### In re Dillon, 919 F.2d 688 (Fed. Cir. 1990) (en banc) · CB p. 387
- **Facts:** Claims to fuel compositions containing tetra-orthoesters to reduce soot. The art used closely related tri-orthoesters in fuel for dewatering; other references treated tri- and tetra-orthoesters as equivalent in related uses. Dillon showed no data that her compositions differed in properties from the art's.
- **Holding / rule:** Structural similarity plus a reason in the art to make the claimed composition establishes a prima facie case. The art need not suggest the applicant's newly discovered property or use. The applicant may rebut with unexpected properties, a showing that the art was so deficient there was no motivation, or other evidence. Overruled In re Wright, 848 F.2d 1216 (Fed. Cir. 1988), to the extent it required the art to suggest the new property. The court said it would not "retreat from Papesch one inch."
- **Nuance:** (1) A composition claim reciting an amount "sufficient to reduce particulate emissions" did not distinguish the art: the amount overlapped and was not shown critical (In re Reni). (2) The en banc dissent (Newman, J.) would have required the art to suggest the property. (3) Dillon's new use could support method-of-use claims, which the court did not foreclose. (4) Stemniski qualifies the rule: if the prior-art compound had no known utility, there may be no reason to make close relatives.
- **Status:** Good law; MPEP 2144 and 2144.08–.09 (R-01.2024) still rely on it. Takeda (2007) confirmed the structural-obviousness framework is consistent with KSR, but now requires a reason to select and modify a lead compound. As of 2026-11-18.
- **Skill rule:** Drafting claims: when the inventive insight is a new use of a structurally close compound, lead with method-of-use claims and keep composition claims only if you have comparative data; never rely on a functional amount ("effective to X") to distinguish a composition the art already contains in overlapping amounts.

### Note cases (chemical), CB pp. 386–395
- In re Lalu, 747 F.2d 703 (Fed. Cir. 1984): no prima facie case where the reference gave no reason to stop at an intermediate and expect useful properties. **Skill rule:** intermediates in a known synthesis are not automatically obvious targets.
- Stemniski, 444 F.2d 581 (C.C.P.A. 1971), overruling Henze and Riden in part: no motivation to make analogs of a compound with no known utility. In re Hass, 141 F.2d 122 (C.C.P.A. 1944); In re Henze, 181 F.2d 196 (C.C.P.A. 1950): old homolog/analog presumption. In re Gyurik, 596 F.2d 1012 (C.C.P.A. 1979): no common-properties presumption from a compound's appearance as an intermediate. In re Albrecht, 514 F.2d 1389 (C.C.P.A. 1975): rebuttal by unexpected properties or deficient art.
- Takeda Chem. Indus. v. Alphapharm, 492 F.3d 1350 (Fed. Cir. 2007): post-KSR, a chemist must have had a reason to select the prior-art compound as a lead and to modify it in the claimed way; no reason to pick the asserted lead (it had side effects) meant no prima facie case. MPEP 2143 still uses it as an example where obvious-to-try fails.
- Eisai Co. v. Dr. Reddy's Labs., 533 F.3d 1353 (Fed. Cir. 2008): KSR's "finite number of identified, predictable solutions" presumes a starting point, reasons to modify, and reasons to narrow the options; unpredictable chemistry makes that hard to show. Ortho-McNeil Pharm. v. Mylan Labs., 520 F.3d 1358 (Fed. Cir. 2008): a "finite, and in the context of the art, small or easily traversed" set of options can make an invention obvious to try; a large unpredictable set does not.
- Methods of making: In re Hoeksema, 399 F.2d 269 (C.C.P.A. 1968); In re Grose, 592 F.2d 1161 (C.C.P.A. 1979): if no known or obvious process existed to make the structurally obvious compound, the compound may be nonobvious. **Skill rule:** Drafting: if the compound was hard to make, describe the synthetic obstacle and the new route in the spec; it supports both the compound and process claims.
- In re Johnson, 747 F.2d 1456 (Fed. Cir. 1984): the 103 standard is the same for chemical inventions; only the facts differ.
- Discussed in Dillon (CB pp. 388–392): In re May, 574 F.2d 1082 (C.C.P.A. 1978) (prima facie case conceded, then rebutted by an actual unexpected difference in properties; the showing Dillon never made); In re Shetty, 566 F.2d 81 (C.C.P.A. 1977) (a newly found property alone does not defeat a prima facie case); In re Reni, 419 F.2d 922 (C.C.P.A. 1970) (an amount limitation distinguishes only if different and critical); In re Mod, 408 F.2d 1055 (C.C.P.A. 1969) and In re De Montmollin, 344 F.2d 976 (C.C.P.A. 1965) (whether an added new property beyond a shared one makes compounds nonobvious; left open in Dillon).

---

## 5. Biotechnology and obvious to try

### In re Kubin, 561 F.3d 1351 (Fed. Cir. 2009) · CB p. 396
- **Facts:** Claim 73: isolated DNA encoding a polypeptide at least 80% identical to the CD48-binding region of the NAIL protein, which binds CD48. Valiante disclosed the same protein (as "p38"), a commercially available antibody specific to it, and a cloning protocol citing Sambrook, the standard lab manual. The applicants' own spec said the sequence could be isolated by "standard biochemical methods (such as those outlined in Sambrook)."
- **Holding / rule:** Obvious. Where the art teaches the protein of interest, a reason to isolate its gene, and specific tools to do it, the gene is "the product not of innovation but of ordinary skill and common sense." In re Deuel, 51 F.3d 1552 (Fed. Cir. 1995), is discredited to the extent it barred obvious-to-try reasoning. O'Farrell's two traps define when obvious to try is not obviousness: (1) varying all parameters or trying many choices with no direction, and (2) exploring a promising field with only general guidance. "Obviousness does not require absolute predictability of success," only a reasonable expectation of it (O'Farrell). The court refused to confine KSR to "predictable arts."
- **Nuance:** (1) The applicants' own spec statement that standard methods sufficed was used against them; enablement-friendly language invited the obviousness finding. (2) A different cloning technique was irrelevant because the claim was to the product, not the process. (3) The "binds CD48" limitation was an inherent property of the known protein, so it added nothing. (4) The casebook says Kubin overturned Deuel's key holdings; more precisely, Kubin rejected Deuel's ban on obvious-to-try reasoning and did not formally overrule it. (5) The isolated cDNA remains eligible under Myriad (2013).
- **Status:** Good law; MPEP 2143 (R-01.2024) cites it for the O'Farrell traps. The AIA rewrite of § 103 eliminated former § 103(b) (biotech process claims) for AIA patents; Kubin concerned product claims and is unaffected. As of 2026-11-18.
- **Skill rule:** Drafting spec (bio/chem): do not write that the claimed product is obtainable by "routine" or "standard" methods unless you need it for enablement; instead describe what was hard (unexpected sequence features, failed attempts, unpredictability) and the functional data that the art could not predict.

### Note case
- In re O'Farrell, 853 F.2d 894 (Fed. Cir. 1988) (CB pp. 392, 401): obvious where the art gave detailed enabling methodology, a suggestion to modify, and evidence suggesting success. **Skill rule:** in obvious-to-try analysis, record (a) the number of options, (b) whether the art pointed to the claimed one, and (c) the evidence of expected success; report "obvious-to-try risk high" only when all three favor the challenger.

---

## 6. Analogous art and the level of ordinary skill

### Innovention Toys, LLC v. MGA Entertainment, Inc., 637 F.3d 1314 (Fed. Cir. 2011) · CB p. 405
- **Facts:** Patent on a physical chess-like laser board game with mirrored pieces and movable non-mirrored key pieces. Art: Laser Chess computer games (same rules, virtual) and Swift (a physical laser game with fixed scoring modules). The district court held the computer games non-analogous and judged obviousness from a layperson's view because MGA offered no skill-level evidence.
- **Holding / rule:** Vacated summary judgment of nonobviousness. Analogous art has two tests (In re Bigio): (1) same field of endeavor regardless of problem, or (2) reasonably pertinent to the inventor's problem, meaning it "logically would have commended itself to an inventor's attention" (In re Clay). The computer games were reasonably pertinent as a matter of law because both dealt with game design, which is the same regardless of medium; Swift itself contemplated computer play. Using a layperson's skill level was clear error given the patentee's own admission that a Ph.D. engineer and two students took 18 months.
- **Nuance:** (1) Define the problem from the patent's own spec (here, game design: not too simple, not too complex). (2) A wrong skill finding is harmless only if obviousness was found at the lowest skill level or nonobviousness at the highest (Kloster Speedsteel). (3) Lower skill favors the patentee; higher skill favors the challenger (Union Carbide). (4) Infringement was affirmed; only the validity ruling was sent back.
- **Status:** Good law. Later cases refine "reasonably pertinent": Airbus v. Firepass (2019) and Donner v. Pro Stage Gear (2020), both cited in MPEP 2141.01(a) (R-01.2024). As of 2026-11-18.
- **Skill rule:** Deep search and invalidity: define the inventor's problem in functional terms from the patent's own spec, then search outside the field for art solving that problem (software versions of physical devices and vice versa, generic hinges, latches, containers); prosecution: when arguing non-analogous art, argue both tests and the problem as the spec frames it.

### Note cases (analogous art and skill), CB pp. 408–413
- In re Clay, 966 F.2d 656 (Fed. Cir. 1992): a gel used to boost underground oil recovery was not analogous to a gel filling the dead space of a refinery storage tank (different field, different purpose). In re Bigio, 381 F.3d 1320 (Fed. Cir. 2004): the field of endeavor is read from the spec's description of structure and function; toothbrushes fell within a hairbrush patent's field.
- Wyers v. Master Lock Co., 616 F.3d 1231 (Fed. Cir. 2010): padlock seals analogous to trailer-hitch locks as a matter of law (same contamination problem); KSR calls for a broad view of analogous art; motivation to combine is a fact question.
- In re Paulsen, 30 F.3d 1475 (Fed. Cir. 1994): hinges and latches from cabinets, piano lids, and cassette cases were analogous to a laptop housing. Sage Prods. v. Devon Indus., 880 F. Supp. 718 (C.D. Cal. 1994): an 1891 street letter box was analogous to a medical-waste container (receive deposits, block reaching in).
- In re Mlot-Fijalkowski, 676 F.2d 666 (C.C.P.A. 1982): USPTO classification is weak evidence of analogousness.
- Kloster Speedsteel AB v. Crucible Inc., 793 F.2d 1565 (Fed. Cir. 1986); Custom Accessories v. Jeffrey-Allan Indus., 807 F.2d 955 (Fed. Cir. 1986); Union Carbide v. American Can, 724 F.2d 1567 (Fed. Cir. 1984): harmless-error and direction rules for the skill finding.
- Novelty contrast: 102 art has no analogous-art limit; a reference from any field can anticipate. **Skill rule:** never discard a non-analogous reference that discloses every element; chart it under 102.

---

# Edge-case playbook

1. **Every element exists somewhere.** Trap: "A in ref 1, B in ref 2, so obvious." Correct: need a reason to combine as claimed and a reasonable expectation of success, built from pre-filing evidence, with the claim considered as a whole. Cases: KSR, Orexo, In re Gordon, Interconnect Planning.
2. **"It would have worked."** Trap: expert says a skilled person could have used X and it would work. Correct: that addresses expectation of success, not motivation to choose X; silence in the art is not a suggestion. Cases: Orexo, In re Gordon.
3. **The reference solves a different problem.** Trap (patentee side): "irrelevant." Correct: any known need in the field can motivate, and the reference is still prior art; it only drops out if it fails both analogous-art tests. Cases: KSR, Translogic, Innovention.
4. **Software version of a physical device (or the reverse).** Trap: different field, so non-analogous. Correct: if the reference addresses the same functional problem (game design, sealing, hinging), it is reasonably pertinent. Cases: Innovention, Paulsen, Sage.
5. **No skill-level evidence.** Trap: default to a layperson. Correct: the court must find the level from the record; a too-low level is reversible error when nonobviousness was found. Low skill favors the patentee. Cases: Innovention, Environmental Designs, Kloster.
6. **High skill helps the patentee on 112 but hurts on 103.** Trap: argue "highly skilled art" for enablement and "unpredictable, low expectation" for obviousness in the same case. Correct: the same skilled person governs both; inconsistent positions get used against you. Cases: Kubin (spec's "standard methods" sank the claim); compare Wright and Amgen in `specification-112.md`.
7. **Newly discovered property of a close analog.** Trap: "the art never suggested soot reduction, so no prima facie case." Correct: structural similarity plus a reason to make the compound suffices; rebut with comparative data or claim the new use as a method. Cases: Dillon (overruling In re Wright (1988)), Papesch.
8. **Prior-art compound had no use.** Trap: any close homolog is prima facie obvious. Correct: without a known utility there may be no reason to make relatives; also need a reason to pick that compound as a lead. Cases: Stemniski, Takeda, Eisai.
9. **No known way to make the compound.** Trap: structural similarity ends the inquiry. Correct: absence of a known or obvious synthesis can defeat the presumption. Cases: Hoeksema, Grose.
10. **New cloning or synthesis technique, product claimed.** Trap: novelty of the method shows the product is nonobvious. Correct: for a product claim, ask whether the product was obvious; a different route to the same product is irrelevant. Case: Kubin.
11. **"Obvious to try is not the test."** Trap: a pre-2007 maxim. Correct: obvious to try can be obvious when options are finite, identified, and predictable with a reasonable expectation of success; it is not obvious when one must vary all parameters or only general guidance exists. Unpredictable arts are not exempt. Cases: KSR, Kubin, O'Farrell, Ortho-McNeil, Eisai.
12. **Big improvement called "degree, not kind."** Trap: discount a quantitative gain as merely better. Correct: a large unexpected gain (66% bioavailability) is probative; compare to the closest prior art and match the claim scope. Cases: Orexo, Papesch.
13. **Strong commercial success, but the product has unclaimed features or heavy marketing.** Trap: success proves nonobviousness. Correct: nexus to the claimed features is required; a presumption of nexus applies only when the product is coextensive with the claim; a blocking patent can discount success. Cases: Transocean, Fox Factory, Acorda, Iron Grip.
14. **Licenses as proof.** Trap: many licenses show respect. Correct: licenses taken to end litigation or bundled in portfolios carry little weight unless royalties exceed litigation cost or licensees were under no threat. Cases: Transocean, EWP, Pentec.
15. **Copying by someone who thought the patent invalid.** Trap: not "real" copying. Correct: still copying if they took the claimed feature; but copying is weak where the accused product differs and infringement is denied. Cases: Transocean, Pentec, Specialty Composites.
16. **Simultaneous independent invention.** Trap: shows the problem was hard (many tried). Correct: near-simultaneous independent success points toward obviousness. Case: Monarch Knitting.
17. **Foreign office found no inventive step.** Trap: persuasive on 103. Correct: irrelevant to commercial success and not binding; different law. Case: Transocean.
18. **Advantage first argued in litigation.** Trap: argue any benefit the product shows. Correct: an unmentioned advantage, never argued to the PTO, invites the "afterthought" label. Case: Graham. Drafting fix: state functional advantages in the spec.
19. **Examiner calls the gap "common sense."** Trap: accept it. Correct: common sense needs reasoned explanation and cannot supply an important missing limitation; demand an articulated reason (USPTO Feb. 2024 guidance). Cases: KSR, In re Lee; Arendi.
20. **Reference that does not enable its own disclosure.** Trap: non-enabled art is useless for 103. Correct: a 103 reference need not be self-enabling, but the art as a whole must enable the claimed invention; prior art is presumed enabling and need enable only one embodiment for 102. Cases: Raytheon v. GE, Agilent v. Synthego.
21. **Prima facie case in examination vs. litigation.** Trap: treat the examiner's burden-shifting as the litigation rule. Correct: in examination, the examiner makes a prima facie case and the burden of production shifts (Oetiker); in litigation the challenger bears clear-and-convincing proof throughout and objective indicia are weighed with everything (Transocean).
22. **Applicant-admitted prior art in the background.** Trap: harmless context. Correct: statements in the spec that something is prior art can be used against the applicant in examination; in IPR such admissions cannot be "the basis" of a ground but can show general knowledge. Case: Qualcomm v. Apple (2022, 2025). Drafting fix: describe problems neutrally and never label your own or unpublished work "prior art."
23. **Claimed dose or range inside a broad prior-art range.** Trap: always obvious under the overlap presumption. Correct: the presumption applies only where the art's general conditions encompass the claim; the expectation of success must be for the specific claimed value. Case: Teva v. Corcept (2021); overlap presumption: In re Peterson, 315 F.3d 1325 (Fed. Cir. 2003).
24. **Design patent obviousness.** Trap: apply Rosen-Durling ("basically the same" primary reference). Correct: LKQ (2024, en banc) replaced it with Graham/KSR; analogous art for designs includes the same field of the article. Route design questions per SKILL.md US-utility scope (US utility only).
25. **The process was routine or accidental.** Trap: "anyone could have found it by testing." Correct: how the invention was made does not negate patentability (§ 103, last sentence); the question is whether the result would have been obvious. Cases: Graham (abolishing Cuno's "flash of genius").

---

# Post-casebook developments (after 2018, through Nov. 2026)

Already covered in `../novelty-and-obviousness.md` §6 (not repeated): Honeywell v. 3G Licensing (2025), Lynk Labs v. Samsung (2025), In re Riggs (2025), LKQ v. GM (2024), USPTO Feb. 2024 obviousness guidance.

- **Acorda Therapeutics, Inc. v. Roxane Labs., Inc., 903 F.3d 1310 (Fed. Cir. 2018).** A blocking patent (Elan's, licensed to Acorda) deterred others and justified discounting commercial success, long-felt need, and failure of others; no categorical rule; Newman, J., dissented. Status: good law. **Skill rule:** analysis: before weighing objective indicia, check whether an earlier patent (often the client's own) blocked competitors; if so, flag the indicia as discounted.
- **Airbus S.A.S. v. Firepass Corp., 941 F.3d 1374 (Fed. Cir. 2019); Donner Tech., LLC v. Pro Stage Gear, LLC, 979 F.3d 1353 (Fed. Cir. 2020)** (both cited in MPEP 2141.01(a), R-01.2024). Reasonable pertinence asks what a skilled person would consider, in light of the reality of the circumstances; the reference's and the patent's problems must be identified and compared. **Skill rule:** analogous-art arguments must name both problems and compare them explicitly.
- **Fox Factory, Inc. v. SRAM, LLC, 944 F.3d 1366 (Fed. Cir. 2019).** A presumption of nexus applies only when the product embodying the claims is "coextensive" with them; a product with significant unclaimed features gets no presumption, and the patentee must prove nexus. Status: good law. **Skill rule:** when citing product success, show the product is the claimed invention and nothing materially more, or prove nexus feature by feature.
- **Raytheon Techs. Corp. v. General Electric Co., 993 F.3d 1374 (Fed. Cir. 2021).** Reversed a PTAB obviousness finding: the prior art, taken as a whole, must enable a skilled person to make and use the claimed invention; a lone reference relied on for a limitation (Knip's power density) must enable it unless other evidence does. **Skill rule:** invalidity: for each limitation drawn from a speculative or forward-looking reference, cite evidence that it could actually be achieved.
- **Teva Pharms. USA, Inc. v. Corcept Therapeutics, Inc., 18 F.4th 1377 (Fed. Cir. 2021)** (No. 21-1360, decided Dec. 7, 2021). Reasonable expectation of success must be shown for the specific claimed dose (600 mg), and the overlapping-range presumption did not apply where the art capped co-administration at 300 mg. **Skill rule:** chart expectation of success at the claimed value, not for the general concept.
- **In re Entresto, 125 F.4th 1090 (Fed. Cir. 2025).** Affirmed nonobviousness of the valsartan–sacubitril combination claims (its written-description holding is in `specification-112.md`). Status: precedential; still cited by the Federal Circuit in Oct. 2026; rehearing history not verified.
- **Qualcomm Inc. v. Apple Inc., Nos. 23-1208, -1209 (Fed. Cir. Apr. 23, 2025)** (following Qualcomm I, 24 F.4th 1367 (Fed. Cir. 2022)). Applicant-admitted prior art cannot be "the basis," or part of the basis, of an IPR ground; combining it with patents does not automatically take it out of the basis, and a petition that expressly lists it in a ground's "Basis" violates § 311(b). It remains usable as evidence of general knowledge. **Skill rule:** drafting: keep background admissions minimal and neutral.
- **Agilent Techs., Inc. v. Synthego Corp., No. 23-2186 (Fed. Cir. June 11, 2025).** Prior art is presumed enabled; an anticipatory reference need enable only a single embodiment; Amgen governs claim enablement, not prior-art enablement; contemporaneous literature supplied a reasonable expectation that chemical modifications would keep guide RNA functional. **Skill rule:** do not argue a reference is non-enabling unless you have evidence it could not be practiced; presume it works.

---

# Checklist for the skill (103)

- Set the timing date per claim (AIA effective filing date; pre-AIA invention date) before choosing art.
- Write down the level of ordinary skill with Environmental Designs factors; use the same skilled person for 103 and 112.
- Confirm each reference is prior art (dates, exceptions) and analogous (field of endeavor or reasonably pertinent, with both problems named).
- Pick the closest reference as primary; for compounds, state why a chemist would choose it as the lead.
- For every gap, name the KSR rationale and write the reason to combine with a pinpoint; reject "could," "would work," and bare "common sense."
- Record the reasonable expectation of success for the specific claimed feature or value.
- Check counter-evidence: teaching away (quotes), change of principle, loss of intended purpose, unpredictability, non-enabled art.
- Inventory objective indicia; for each, test nexus (coextensive product, price premium, documents naming the feature) and discounts (blocking patent, litigation licenses, unclaimed features, marketing).
- Look for simultaneous independent invention (challenger side) and pre-invention skepticism (patentee side).
- Drafting: state each functional advantage and any unexpected data in the spec; compare to the closest art; avoid "routine/standard methods" language for the claimed product; avoid labeling anything prior art.
- Office actions: first test the prima facie case (all limitations, articulated reason), then decide on arguments vs. a Rule 132 declaration with data commensurate in scope with the claims.
- Give a scoped, evidence-backed assessment with the strongest objection, response and resolution; do not promise a tribunal outcome.
