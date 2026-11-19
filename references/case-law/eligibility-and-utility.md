---
title: Patent eligibility (§101), utility, and patent vs. trade secret — case law and edge cases
last_verified: 2026-11-18
sources:
  - Adelman et al., Patent Law — Cases and Materials (5th ed.), ch. 1–3 (used for case selection only; digests are original)
  - https://www.law.cornell.edu/uscode/text/18/1839 (DTSA "improper means" definition, read 2026-11-18)
  - https://www.uspto.gov/web/offices/pac/mpep/s2107.html (MPEP 2107 utility; cites Fisher, Brenner, Brana, Brooktree, Newman v. Quigg)
  - https://www.uspto.gov/patents/ptab/trials/transitional-program-covered-business-method (CBM sunset Sept. 16, 2020)
  - https://law.justia.com/cases/federal/appellate-courts/cafc/17-2508/17-2508-2019-07-03.html (Athena v. Mayo en banc denial)
  - https://law.justia.com/cases/federal/appellate-courts/cafc/22-1027/22-1027-2022-07-18.html (CareDx v. Natera)
  - https://www.cafc.uscourts.gov/opinions-orders/21-2167.OPINION.9-28-2022_2010108.pdf (Cooperative Entertainment v. Kollective)
  - https://www.scotusblog.com/case-files/cases/american-axle-manufacturing-inc-v-neapco-holdings-llc (cert. denied June 30, 2022)
  - https://uspto.gov/sites/default/files/documents/memo-vanda-20180607.PDF (Vanda memo; Vanda v. West-Ward holding)
  - https://www.law.cornell.edu/wex/vessel_hull_design_protection_act and https://www.govinfo.gov/content/pkg/CRPT-105hrpt436/html/CRPT-105hrpt436.htm (VHDPA as response to Bonito Boats)
  - https://www.supremecourt.gov/DocketPDF/24/24-635/334626/20241209131054138_Celanese%20Petition%20for%20Certiorari.pdf (Celanese v. ITC; petition gives 111 F.4th 1338; cert. denied Apr. 28, 2025 per docket https://www.supremecourt.gov/docket/docketfiles/html/public/24-635.html)
  - Supreme Court dockets read 2026-11-18 for dispositions: 20-891 (American Axle; CVSG brief May 24, 2022; denied June 30, 2022), 20-892 (Ariosa v. Illumina; dismissed under Rule 46 May 21, 2021), 23-245 (ChromaDex; denied Oct. 16, 2023), 25-505 (Recentive; denied Dec. 8, 2025)
  - Secondary summaries used only to confirm cites and dispositions (each named in the entry): Knobbe, Finnegan, Winston, Foley, Fish, JD Supra, Patently-O, Wiley
---

# How to use this file

Load it at Phase 1 Check B (eligibility red flag), Phase 3 claim and spec drafting for software, AI, diagnostics, natural products, and business methods, office-action responses with 101 or utility rejections, and invalidity or FTO screens where 101 is a likely defense.

**Division of labor.** Current USPTO examination guidance (MPEP 2106 steps, the 2024 AI update, the Aug. 2025 memo, Desjardins, SMEDs, 2025–2026 Federal Circuit decisions, PERA) lives in [`../eligibility-101.md`](../eligibility-101.md). This file covers the cases behind that guidance, where each rule stops, and the fact patterns a naive analysis gets wrong. Novelty bars (Metallizing, secret sales, Celanese) are in `novelty-and-bars.md`; the §273 prior-user defense is in `defenses.md`; design patents are in `design-patents.md`.

**Three framing points the cases force.**
1. Courts and the USPTO apply the same Supreme Court test differently. An allowance is weak evidence of eligibility in court. Never tell a user that allowance "settled" 101.
2. Eligibility is decided claim by claim, on the claim as drafted, not on the invention as the inventor describes it.
3. Utility (§101 "useful") and eligibility (§101 categories plus judicial exceptions) are different doctrines with different tests. Keep them in separate sections of any output.

---

## 1. Foundations: the patent bargain, trade secrets, and preemption (ch. 1)

### Bonito Boats, Inc. v. Thunder Craft Boats, Inc., 489 U.S. 141 (1989) · CB p. 7
- **Facts:** A Florida statute barred copying unpatented boat hulls by the direct-molding process. Bonito had never patented its hull, which had been on the market for years.
- **Holding / rule:** Federal patent law preempts state laws that give patent-like protection to unpatented, publicly marketed designs and utilitarian ideas. Free copying of what the patent system leaves unprotected is part of the federal scheme: "free exploitation of ideas will be the rule, to which the protection of a federal patent is the exception."
- **Nuance:** The Court left room for state laws aimed at different harms: trade secret law (Kewanee), passing off and consumer confusion (unfair competition), and contract. What fails is a state right against copying itself, once the article is in public commerce. The excerpt's references to 17-year terms and pre-AIA §102(a)/(b) are dated.
- **Status:** Good law as of 2026-11-18. Congress answered the specific gap with the Vessel Hull Design Protection Act, 17 U.S.C. ch. 13 (1998; sui generis, 10-year hull protection, unavailable once a design patent issues). That statute leaves Bonito's preemption rule intact for every other article. Term is now 20 years from filing (35 U.S.C. §154(a)(2)); novelty is AIA §102.
- **Skill rule:** Inventor intake and `modules/mine.md`: when a product will be sold or shown publicly and cannot be kept secret, tell the user that after public release the only exclusivity for its function is a patent (or a design patent for appearance), so the filing decision must come before launch. Never suggest a state-law "anti-copying" right as a substitute.

### Kewanee Oil Co. v. Bicron Corp., 416 U.S. 470 (1974) · CB p. 63 (note)
- Trade secret law is not preempted by the patent laws, even for patentable subject matter; the two regimes coexist because trade secrecy protects only against improper acquisition and leaves independent invention and reverse engineering free. Status: good law. **Skill rule:** `modules/mine.md` and Phase 1 intake: when the novel feature is invisible in the sold product (a process, a server-side algorithm, a formulation), present trade secret as a real alternative and state its weak point (no protection against independent development or reverse engineering).

### E.I. duPont deNemours & Co. v. Christopher, 431 F.2d 1012 (5th Cir. 1970) · CB p. 55
- **Facts:** Photographers hired by an unknown competitor flew over DuPont's methanol plant while it was under construction and photographed the exposed process layout from the air. There was no trespass or contract, and the court found it unnecessary to decide whether the flight broke aviation rules.
- **Holding / rule:** Acquiring a trade secret by means that defeat reasonable secrecy precautions is "improper means" even if the conduct is otherwise lawful. The owner need not take unreasonable precautions: "an impenetrable fortress is an unreasonable requirement."
- **Nuance:** The rule protects only against espionage that could not reasonably have been anticipated or prevented. Inspecting a product bought on the open market, reading public documents, and reverse engineering remain proper. If DuPont had left a finished plant open to view from a public road, the result would likely flip.
- **Status:** Good law as persuasive authority as of 2026-11-18. The UTSA official comment cites this fact pattern as improper means, and the federal Defend Trade Secrets Act defines improper means to exclude "reverse engineering, independent derivation, or any other lawful means of acquisition" (18 U.S.C. §1839(6)(B)).
- **Skill rule:** Confidentiality step (SKILL.md rule 4) and `modules/mine.md`: when a user chooses trade secret over patent, list concrete secrecy measures (NDAs, access limits, marking) because protection depends on reasonable efforts; when a user chooses patent, warn that publication at 18 months ends secrecy for everything the application discloses, even if no patent issues.

**Compact note cases (ch. 1)**
- *Smith v. Dravo Corp.*, 203 F.2d 369 (7th Cir. 1953) · CB p. 54: a duty of confidence can be implied from acquisition negotiations even without an express promise. **Skill rule:** intake question 3 (disclosures): ask whether investor or acquirer pitches happened under an NDA; an implied duty may protect a trade secret but does not stop a patent bar clock if the disclosure was public.
- *Rockwell Graphic Sys. v. DEV Indus.*, 925 F.2d 174 (7th Cir. 1991) · CB p. 50: reasonable-precaution analysis balances cost against benefit; perfect secrecy is not required.
- *Religious Tech. Ctr. v. Wollersheim*, 796 F.2d 1076 (9th Cir. 1986) · CB p. 54: value must be commercial, not spiritual.
- *Shellmar* (7th Cir. 1937) vs. *Conmar* (2d Cir. 1949); UTSA §2(a) · CB p. 60: modern trade secret injunctions last only for the head-start period a lawful competitor would have needed.
- *W.L. Gore & Assocs. v. Garlock*, 721 F.2d 1540 (Fed. Cir. 1983) · CB p. 62: a third party's secret commercial use does not bar a later independent inventor's patent; the secret user can then be liable for infringement. The AIA's prior-commercial-use defense (35 U.S.C. §273) softens this (see `defenses.md`). **Skill rule:** FTO: if the client has secretly used the accused process commercially in the US more than one year before the patent's effective filing date, flag §273 as a possible defense `[review]`; never treat secret prior use as invalidating prior art without checking whether the use was public.
- *Metallizing Eng'g v. Kenyon Bearing*, 153 F.2d 516 (2d Cir. 1946) · CB p. 62: an inventor who commercially exploits a secret invention for more than the grace period forfeits the patent. *Celanese Int'l Corp. v. ITC*, 111 F.4th 1338 (Fed. Cir. 2024), held the AIA did not change this for sales of products made by a secret process (cert. denied 2025). Details in `novelty-and-bars.md`. **Skill rule:** Phase 1 Check A: ask whether products made by the process were sold; selling the output starts the clock on the process.
- *Pennock v. Dialogue*, 27 U.S. (2 Pet.) 1 (1829) · CB p. 8 (quoted in Bonito): the inventor's own public sales before applying forfeit the right.
- *South Corp. v. United States*, 690 F.2d 1368 (Fed. Cir. 1982) (en banc) · CB p. 19: CCPA and Court of Claims decisions bind the Federal Circuit; *Newell Cos. v. Kenney Mfg.*, 864 F.2d 757 (Fed. Cir. 1988): an earlier panel decision controls a later panel unless overruled en banc. **Skill rule:** when two Federal Circuit panel opinions conflict, treat the earlier precedential one as controlling and flag the conflict `[review]`; CCPA cases (e.g., In re Kalm, In re Seaborg, Nelson v. Bowler) are binding, not "old."

---

## 2. Products of nature and living things

### Diamond v. Chakrabarty, 447 U.S. 303 (1980) · CB p. 73
- **Facts:** Claim to a genetically engineered *Pseudomonas* bacterium carrying two or more plasmids, each providing a separate hydrocarbon-degrading pathway. The PTO rejected it as a product of nature and as a living thing.
- **Holding / rule:** A live, human-made microorganism is a "manufacture" or "composition of matter." The line is between products of nature, living or not, and human-made inventions. The organism qualified because it had "markedly different characteristics from any found in nature" and potential for significant utility. 5–4.
- **Nuance:** The "anything under the sun that is made by man" phrase comes from legislative history whose full sentence adds that the thing must still satisfy the other conditions; it is not a holding that everything made by humans is eligible. *Funk Bros. Seed Co. v. Kalo Inoculant Co.*, 333 U.S. 127 (1948) (discussed at CB p. 75, 106), is the contrast: a mixture of natural bacterial strains, each unchanged and working as it does in nature, was ineligible. The difference that flips the result is human change that gives the product new properties.
- **Status:** Good law as of 2026-11-18. Applied in Myriad. Congress barred claims "directed to or encompassing a human organism" (AIA §33(a), Pub. L. 112-29).
- **Skill rule:** Drafting claims (biologics, engineered organisms, materials): claim the engineered feature that does not occur in nature and describe in the spec the new property it produces (structure, function, stability); for any claim to an organism, add a limitation that excludes humans, and Check B flags any claim that could read on a human.

**Compact note cases**
- *J.E.M. Ag Supply, Inc. v. Pioneer Hi-Bred Int'l, Inc.*, 534 U.S. 124 (2001) · CB p. 81: sexually reproduced plants may get utility patents despite the Plant Patent Act and PVPA; overlapping regimes coexist. Status: good law. **Skill rule:** routing (SKILL.md US-utility scope): a plant invention may qualify for a US utility patent; mention plant patents and PVP certificates as other US options without advising on them.
- *In re Roslin Inst. (Edinburgh)*, 750 F.3d 1333 (Fed. Cir. 2014) · CB p. 81: clones of donor mammals (Dolly) are ineligible because they are genetically identical to the donor; unclaimed phenotypic or mitochondrial differences did not help. Status: good law. **Skill rule:** Drafting: a difference from nature saves eligibility only if the claim recites it and the spec explains its effect.
- *AIA §33(a)* · CB p. 145: no patent may issue on a claim directed to or encompassing a human organism.

### Association for Molecular Pathology v. Myriad Genetics, Inc., 569 U.S. 576 (2013) · CB p. 99
- **Facts:** Myriad located and sequenced the BRCA1 and BRCA2 genes and claimed isolated DNA molecules with those sequences, plus cDNA (exons only, made in the lab from mRNA).
- **Holding / rule:** A naturally occurring DNA segment is a product of nature and is not eligible merely because it has been isolated. cDNA is eligible because it is not naturally occurring, except for short sequences with no introns, which may be indistinguishable from natural DNA.
- **Nuance:** The argument that isolation breaks covalent bonds and creates a new molecule lost because the claims were written in terms of genetic information, not chemical structure. The Court expressly left open method claims, new applications of the gene knowledge, and DNA whose nucleotide order has been altered. Hard work and brilliant discovery do not count: separating the gene "is not an act of invention." Prior USPTO practice of granting gene patents got no deference.
- **Status:** Good law as of 2026-11-18. Applied to isolated natural compounds in *ChromaDex, Inc. v. Elysium Health, Inc.*, 59 F.4th 1280 (Fed. Cir. 2023) (isolated nicotinamide riboside composition not markedly different from milk; ineligible). *In re BRCA1- & BRCA2-Based Hereditary Cancer Test Patent Litig.*, 774 F.3d 755 (Fed. Cir. 2014), held short primers and sequence-comparison methods ineligible (preliminary-injunction posture). Engineered compositions survive: see `../eligibility-101.md` (REGENXBIO, 2026).
- **Skill rule:** Drafting claims (life sciences): never rely on "isolated" or "purified" alone; claim a composition defined by a structural or functional property the natural product lacks (altered sequence, formulation, non-natural combination, stabilized form) and put data on that property in the spec. Lite search Check B: flag high risk for any claim whose only departure from nature is isolation.

---

## 3. Laws of nature and diagnostics

### Mayo Collaborative Servs. v. Prometheus Labs., Inc., 566 U.S. 66 (2012) · CB p. 83
- **Facts:** Claims to optimizing thiopurine dosing: administer the drug, determine the metabolite level in the patient's blood, and be informed that levels above or below set thresholds indicate a need to lower or raise the dose.
- **Holding / rule:** A process that recites a law of nature is eligible only if it adds enough to ensure the claim is more than a drafting effort to monopolize the law itself. Steps that tell doctors to do "well-understood, routine, conventional activity previously engaged in by researchers in the field," plus a "wherein" clause stating the correlation, add nothing. Unanimous.
- **Nuance:** The Court refused the government's suggestion to let §§102, 103, and 112 do the work, making 101 a threshold question. Conventionality in step two overlaps with novelty, despite *Diamond v. Diehr*'s warning not to dissect claims into old and new parts. The "administering" step only identified the audience (doctors treating patients); it did not require a changed treatment. A claim that required actually adjusting the dose in a specific way would likely have come out differently (see Vanda, below).
- **Status:** Good law as of 2026-11-18. The Federal Circuit applies it strictly to detection claims: *Athena Diagnostics, Inc. v. Mayo Collaborative Servs.*, 915 F.3d 743 (Fed. Cir. 2019), reh'g en banc denied, 927 F.3d 1333 (2019) (7–5; eight separate opinions: four concurrences, several asking the Supreme Court or Congress to clarify the law, and four dissents urging the court itself to rehear); *CareDx, Inc. v. Natera, Inc.*, 40 F.4th 1371 (Fed. Cir. 2022) (conventional techniques used to detect a natural phenomenon; the patent's own statement that techniques were conventional hurt it). Treatment and preparation claims survive (Vanda 2018; Natural Alternatives 2019; Illumina v. Ariosa 2020; see Post-casebook).
- **Skill rule:** Drafting claims (diagnostics, personalized medicine): write the independent claim as a method of treatment (administering a named therapy at a dose to a patient selected by the test) or a specific method of preparing or measuring a sample, never "detect X and conclude Y"; spec drafting: never call the assay steps "conventional," "standard," or "well known" (CareDx).

**Compact note cases**
- *35 U.S.C. §287(c)* · CB p. 94: no remedies against a medical practitioner (or related health-care entity) for performing a patented medical or surgical procedure on a body; the exemption does not cover patented machines, compositions, uses of compositions, or biotechnology processes. **Skill rule:** FTO and portfolio: a pure surgical-technique claim may be valid but unenforceable against doctors; tell the user that claims reciting a device or composition keep enforcement value.
- *EPC Art. 53(c); G 1/04* · CB p. 96: Europe bars diagnostic methods practiced on the body, but reads the bar narrowly. **Skill rule:** SKILL.md US-utility scope: never apply US Mayo analysis to EP or other offices; say foreign counsel must assess.

---

## 4. Abstract ideas: algorithms, software, business methods

### Gottschalk v. Benson, 409 U.S. 63 (1972) · CB p. 113
- **Facts:** Claims to converting binary-coded decimal numerals to pure binary in a general-purpose digital computer, not limited to any end use or apparatus (one claim recited a shift register).
- **Holding / rule:** A claim that would in practical effect preempt a mathematical algorithm is not an eligible process. Because the formula had no substantial practical use except in a digital computer, the patent would "wholly pre-empt the mathematical formula."
- **Nuance:** The Court disclaimed holding that software is never eligible and said machine-or-transformation was a clue, not a requirement. Its prediction that the algorithm had little use outside computers drove the preemption finding. A claim tied to a specific technical application (as in Diehr) is the contrast.
- **Status:** Good law as of 2026-11-18 as a building block of Alice step one. Its machine-or-transformation "clue" was confirmed as non-exclusive in *Bilski v. Kappos*, 561 U.S. 593 (2010).
- **Skill rule:** Drafting claims (software): never claim an algorithm at a level of generality that covers every use of it; tie the independent claim to the technical problem and the concrete system behavior it changes, and keep the bare math in dependent claims or the spec.

**Compact note cases (CB p. 115–119)**
- *In re Bernhart*, 417 F.2d 1395 (CCPA 1969): a computer programmed in a new way is physically a different machine. Status: largely displaced in practice by Alice; claiming software as "a computer configured to" no longer avoids 101 by itself. **Skill rule:** Drafting: system and medium claims rise or fall with the method claim unless they add specific structure (Alice part C).
- *Parker v. Flook*, 437 U.S. 584 (1978): updating an alarm limit with a new formula was ineligible; a field-of-use limit and post-solution activity do not save a formula. Status: good law; Mayo and Alice rely on it.
- *Diamond v. Diehr*, 450 U.S. 175 (1981): a rubber-curing process that used the Arrhenius equation with continuous mold-temperature measurement and automatic press opening was eligible; claims are read as a whole. Status: good law; Mayo recast it as a process whose added steps made the equation an inventive application. **Skill rule:** Drafting: the Diehr model is a claim where the computation controls a physical process step and the claim recites the sensing and the actuation.
- *State Street Bank & Trust v. Signature Fin. Grp.*, 149 F.3d 1368 (Fed. Cir. 1998), and *AT&T Corp. v. Excel Commc'ns*, 172 F.3d 1352 (Fed. Cir. 1999): "useful, concrete and tangible result" test and no business-method exception. Status: abrogated; *Bilski* rejected the State Street test and *Alice* controls. **Skill rule:** Never cite State Street or AT&T as authority for eligibility.
- *Bilski v. Kappos*, 561 U.S. 593 (2010): hedging risk is an abstract idea; machine-or-transformation is a useful clue, not the sole test; business methods are not categorically excluded (5–4; four Justices would have excluded them). Status: good law.
- *AIA §18 (CBM review)* · CB p. 119: post-grant review program for covered business method patents. Status: expired for new petitions on Sept. 16, 2020. **Skill rule:** invalidity mode: do not offer CBM review as an option; use IPR/PGR or district court 101 motions.
- *AIA §14* · CB p. 119: tax strategies are deemed insufficient to distinguish over the prior art for §§102 and 103 (inventions used solely to prepare tax filings or solely for financial management are excepted, to the extent severable from a tax strategy). Status: in force. **Skill rule:** Phase 1: when the novel element is a tax-reduction strategy, report it as giving no novelty or nonobviousness credit, separate from any 101 flag.

### Alice Corp. Pty. Ltd. v. CLS Bank Int'l, 573 U.S. 208 (2014) · CB p. 120
- **Facts:** Method, system, and computer-readable-medium claims for mitigating settlement risk: a computer acting as intermediary keeps shadow credit and debit records, updates them in real time, permits only transactions the shadow balances cover, and instructs banks at day's end.
- **Holding / rule:** The two-step Mayo framework applies to all judicial exceptions: (1) is the claim directed to an exception; (2) if so, do the remaining elements, individually and as an ordered combination, add an inventive concept that transforms it. Intermediated settlement is an abstract idea (a fundamental economic practice), and "merely requiring generic computer implementation" does not transform it. Unanimous.
- **Nuance:** The system claims failed because the recited hardware (data processing system, communications controller, data storage unit) was purely functional and generic; patent eligibility must not depend on "the draftsman's art." The Court noted the claims did not purport to improve the functioning of the computer itself or any other technology; that remark became the main escape route (Enfish, McRO). The Court did not define "abstract idea."
- **Status:** Good law as of 2026-11-18. No later Supreme Court eligibility merits decision was found; review was denied in *American Axle v. Neapco* (June 30, 2022, over the Solicitor General's recommendation to grant) and in Recentive (Dec. 8, 2025, No. 25-505). Current USPTO application and 2025–2026 Federal Circuit cases: [`../eligibility-101.md`](../eligibility-101.md).
- **Skill rule:** Drafting claims (software, fintech, AI): write the independent claim around the technical mechanism that solves a technical problem (data structure, protocol, architecture, sensor or network behavior), and draft system and medium claims with that same mechanism, not just generic components; Check B: a claim whose novelty is a business or economic rule run on a computer is high risk in court even if the USPTO allows it.

**Compact note cases after Alice (CB p. 130–132)**
- *Digitech Image Techs. v. Electronics for Imaging*, 758 F.3d 1344 (Fed. Cir. 2014): a "device profile" made of color and spatial data is intangible information, not a machine or manufacture; generating it by mathematical correlation is abstract. Abstract-idea doctrine is not limited to business concepts. **Skill rule:** Drafting: never claim a data set or data structure in the abstract; claim the system or process that uses it to change device behavior.
- *DDR Holdings v. Hotels.com*, 773 F.3d 1245 (Fed. Cir. 2014): eligible where the claims solve a problem specific to the internet (keeping visitors on a host site via a composite page) in a specific way.
- *Enfish, LLC v. Microsoft Corp.*, 822 F.3d 1327 (Fed. Cir. 2016): a self-referential database table is directed to an improvement in computer functionality itself; step one can end the inquiry.
- *Bascom Global Internet Servs. v. AT&T Mobility*, 827 F.3d 1341 (Fed. Cir. 2016): an unconventional arrangement of known parts (filtering at the ISP server, customized per user) can be an inventive concept at step two.
- *McRO, Inc. v. Bandai Namco Games Am.*, 837 F.3d 1299 (Fed. Cir. 2016): specific rules for automated lip-sync animation, different from what animators did by hand, were not abstract.
- *Amdocs (Israel) Ltd. v. Openet Telecom*, 841 F.3d 1288 (Fed. Cir. 2016); *Thales Visionix v. United States*, 850 F.3d 1343 (Fed. Cir. 2017); *Visual Memory LLC v. NVIDIA*, 867 F.3d 1253 (Fed. Cir. 2017): eligible where generic-looking components operate in an unconventional way that improves the system (distributed network enhancement; inertial sensors on a moving frame; configurable cache). *Trading Techs. v. CQG*, 675 F. App'x 1001 (Fed. Cir. 2017) is nonprecedential.
- **Skill rule (all six):** Spec drafting: for software, describe the prior technical limitation and how the claimed structure overcomes it, with measurable effect (memory, latency, accuracy, error rate); claim drafting: recite the rules or structure that produce the improvement, not the result. Prosecution: cite these cases only for claims that actually recite the improving mechanism.
- *Berkheimer v. HP Inc.*, 881 F.3d 1360 (Fed. Cir. 2018), and *Aatrix Software v. Green Shades Software*, 882 F.3d 1121 (Fed. Cir. 2018) · CB p. 132: whether claim elements were well-understood, routine, and conventional is a question of fact; specification statements and complaint allegations of unconventionality can defeat summary judgment or dismissal. Being in one prior-art reference does not make something conventional. Status: good law; applied in *Cooperative Entm't, Inc. v. Kollective Tech., Inc.*, 50 F.4th 127 (Fed. Cir. 2022). **Skill rule:** Spec drafting: state, in factual terms, what is unconventional about the claimed combination and why; prosecution: demand evidence under the USPTO's Berkheimer requirements when an examiner calls an element conventional without support (MPEP 2106.07(a), subsection III).
- *AIPLA-style legislative proposal* · CB p. 132: would limit exceptions to what exists in nature or is performed solely in the mind. Not law. Current bill status: [`../eligibility-101.md`](../eligibility-101.md) §6.

---

## 5. Utility (§101 "useful")

Utility is a low bar outside chemistry and biotechnology. It fails in three situations: the invention cannot work (inoperability), the asserted use is too vague or too far from a real-world benefit (Brenner, Fisher), or, historically, the invention was "immoral" (now essentially dead after Juicy Whip). A utility rejection usually travels with a §112(a) how-to-use enablement rejection.

### Lowell v. Lewis, 15 F. Cas. 1018 (C.C.D. Mass. 1817) (Story, J.) · CB p. 135
- **Facts:** Infringement suit on a pump patent; the defendant argued the patentee had to prove the pump was better than pumps in common use.
- **Holding / rule:** An invention need not be superior to existing technology to be "useful." It need only not be frivolous or injurious to the well-being, good policy, or morals of society.
- **Nuance:** The "better than the prior art" argument loses even today; the market, not the patent office, judges commercial worth. Story's "mischievous or immoral" limit is the part that has not survived (Juicy Whip). Brenner later rejected reading Story's test as the whole of utility for chemical inventions.
- **Status:** Good law on "no superiority required" (see *Custom Accessories v. Jeffrey-Allan Indus.*, 807 F.2d 955, 960 n.12 (Fed. Cir. 1986)); moral-utility component effectively abandoned (Juicy Whip); the "not frivolous" floor was raised for chemistry and biotech by Brenner and Fisher.
- **Skill rule:** Office-action response and Phase 1: never argue or concede that an invention must outperform the prior art to be useful; if a user worries their device is "worse but different," explain that utility is met and the real questions are novelty and nonobviousness.

**Compact note cases: inoperability (CB p. 137)**
- *Brooktree Corp. v. Advanced Micro Devices*, 977 F.2d 1555, 1571 (Fed. Cir. 1992): to violate 101 the device must be "totally incapable of achieving a useful result"; partial success suffices. **Skill rule:** invalidity mode: do not propose a utility attack because the product works poorly or only sometimes.
- *Newman v. Quigg*, 877 F.2d 1575 (Fed. Cir. 1989) (perpetual motion); *In re Swartz*, 232 F.3d 862 (Fed. Cir. 2000) (cold fusion); *In re Citron*, 325 F.2d 248 (CCPA 1963) (uncharacterized cancer cure); *Fregeau v. Mossinghoff*, 776 F.2d 1034 (Fed. Cir. 1985) (magnetic field asserted to change the taste of food); *In re Houghton*, 433 F.2d 820 (CCPA 1970) (flapping flight); *In re Eltgroth*, 419 F.2d 918 (CCPA 1970) (control of aging); *In re Speas*, 273 F. App'x 945 (Fed. Cir. 2008) (devices violating thermodynamics): utility fails where the asserted result is incredible in light of accepted science; the PTO may then demand proof. **Skill rule:** Phase 1 intake and Phase 3: if the claimed effect contradicts established physics or biology, flag a likely 101/112(a) credibility rejection `[review]` and ask the user for test data before drafting; draft the claims around what the data actually shows.

### Juicy Whip, Inc. v. Orange Bang, Inc., 185 F.3d 1364 (Fed. Cir. 1999) · CB p. 138
- **Facts:** Claims to a post-mix beverage dispenser with a display bowl of colored fluid, not connected to the outlet, that makes customers think the drink comes from the bowl. The district court held the patent invalid for lack of utility because its purpose was to deceive buyers.
- **Holding / rule:** An invention is useful if it is "capable of providing some identifiable benefit." Making one product look like another is itself a specific benefit (cubic zirconia, imitation leather). The utility requirement is "not a directive to the Patent and Trademark Office or the courts to serve as arbiters of deceptive trade practices." Reversed.
- **Nuance:** The court declined to follow two old Second Circuit cases (*Rickard v. Du Bon*, 103 F. 868 (2d Cir. 1900), spotted tobacco; *Scott & Williams v. Aristo Hosiery*, 7 F.2d 1003 (2d Cir. 1925), fake stocking seams). Consumer deception is for the FTC, FDA, and state police powers. Congress may exclude categories by statute (atomic weapons, 42 U.S.C. §2181(a); human organisms, AIA §33). Gambling devices, once held immoral, are no longer excluded (*In re Murphy*, 200 USPQ 801 (PTO Bd. App. 1977)).
- **Status:** Good law as of 2026-11-18. It removed the basis for morality-based utility rejections; statutory exclusions remain.
- **Skill rule:** Phase 1 and office-action response: do not flag a utility problem because an invention is deceptive, addictive, or controversial; flag only the statutory exclusions (human organisms, AIA §33(a); nuclear weapons, 42 U.S.C. §2181(a)) and note that legality of use is a separate question from patentability. Foreign caveat: EPC Art. 53(a) ordre public exclusions exist (SKILL.md US-utility scope).

### Brenner v. Manson, 383 U.S. 519 (1966) · CB p. 146
- **Facts:** Manson sought an interference over a process for making a known steroid. No use was shown for the steroid; he pointed to a published report that an adjacent homologue inhibited tumors in mice.
- **Holding / rule:** A chemical process (or product) whose only use is as an object of further research lacks utility. Utility requires that "specific benefit exists in currently available form." "A patent is not a hunting license. It is not a reward for the search, but compensation for its successful conclusion."
- **Nuance:** The homologue evidence failed because steroids are unpredictable; in a predictable field, close-analog data might have sufficed. Process and product rise or fall together. Harlan dissented: a workable new process is itself a contribution to chemistry. Utility discovered after filing does not cure an application that disclosed none (a §112(a) problem as well).
- **Status:** Good law as of 2026-11-18. Codified in USPTO practice as "specific, substantial, and credible" utility (MPEP 2107).
- **Skill rule:** Drafting spec (chemistry, biotech, materials): state at least one specific, practical, currently available use for every claimed compound, sequence, or intermediate, with whatever data exist (in vitro counts); never rely on "useful for research" or "has biological activity." Phase 1: if the user cannot name a concrete use, flag a utility risk and suggest waiting for data or filing a provisional and adding data within 12 months, warning that the later data date may control.

**Compact note cases (CB p. 147, 153–155)**
- *In re Bremner*, 182 F.2d 216 (CCPA 1950), and *In re Nelson*, 280 F.2d 172 (CCPA 1960): the CCPA's swing from strict to lenient that Brenner reversed.
- *Nelson v. Bowler*, 626 F.2d 853 (CCPA 1980): adequate proof of any pharmacological activity is a practical utility.
- *Cross v. Iizuka*, 753 F.2d 1040 (Fed. Cir. 1985): in vitro data can establish practical utility for a drug candidate.
- *In re Brana*, 51 F.3d 1560 (Fed. Cir. 1995): FDA approval and human testing are not required; activity in a standard animal model supports anticancer utility; the PTO bears the initial burden of doubting an asserted utility. Status: good law (MPEP 2107.03 quotes it).
- *In re Chilowsky*, 229 F.2d 457 (CCPA 1956): therapeutic inventions face the same utility standard as others.
- **Skill rule (these four):** Office-action response: answer a pharmaceutical utility rejection with the art-accepted model data in the spec or a Rule 132 declaration showing a reasonable correlation to the asserted use; do not concede that clinical data are needed.

### In re Fisher, 421 F.3d 1365 (Fed. Cir. 2005) · CB p. 155
- **Facts:** Claims to five expressed sequence tags (ESTs) from maize leaf tissue. The underlying genes and proteins had no known function. The spec listed seven uses (genome mapping markers, PCR primers, polymorphism detection, promoter isolation, expression monitoring, and others), all of which any EST could serve.
- **Holding / rule:** §101 requires a specific and substantial utility. Substantial means a "significant and presently available benefit to the public," not one that needs further research to identify. Specific means particular to the claimed subject matter, not a use shared by the whole class. The ESTs were research intermediates, "objects of use-testing" under Brenner. Utility is a fact question reviewed for substantial evidence.
- **Nuance:** Rader's dissent compared ESTs to microscopes (research tools have utility) and argued the real problem was obviousness, which *In re Deuel*, 51 F.3d 1552 (Fed. Cir. 1995), had weakened for DNA. The majority distinguished the microscope: it gives an immediate benefit on any sample, while an EST only detects its own complementary sequence. Disclosing the function of the underlying gene, or one specific target and real result, would have flipped the outcome. MPEP guidelines are not binding on courts but the court found them consistent with the law.
- **Status:** Good law as of 2026-11-18 (MPEP 2107.01 cites it). EST and natural-sequence claims now also face Myriad.
- **Skill rule:** Drafting spec (genomics, chemistry, AI models and datasets claimed as research tools): for each claimed item, state a use tied to its specific identity and a presently available real-world result; a laundry list of uses that every member of the class shares will fail. Lite search Check B should treat research-tool-only inventions as a utility flag separate from the eligibility flag.

**Compact note cases (CB p. 162, 169–170)**
- *In re Kirk*, 376 F.2d 936 (CCPA 1967), and *In re Diedrich*, 318 F.2d 946 (CCPA 1963): "biological activity" or "useful for technical and pharmaceutical purposes" is too vague to be a utility.
- *Fujikawa v. Wattanasin*, 93 F.3d 1559 (Fed. Cir. 1996): no patent until substantial or practical utility is discovered and disclosed.
- *Enzo Biochem v. Gen-Probe*, 323 F.3d 956 (Fed. Cir. 2002): MPEP and USPTO guidelines are not binding on courts; courts may notice them where consistent with the statute. **Skill rule:** analysis and invalidity: never treat an MPEP example or USPTO memo as binding in litigation; label it "USPTO practice."
- *Human-animal chimera application (Newman/Rifkin, 1997)* · CB p. 170: the PTO's public statement that such claims could fail the morality aspect of utility predates Juicy Whip; the controlling rule now is the AIA §33(a) human-organism bar, not moral utility.

---

## Edge-case playbook

1. **"It's allowed, so it's eligible."** Trap: treating a USPTO allowance (or a favorable Desjardins-style argument) as settling 101. Correct: courts apply Alice/Mayo without deference to USPTO guidance and frequently invalidate issued claims on a Rule 12 motion. Report USPTO outlook and litigation outlook separately. Cases: Alice; Myriad (no deference to past PTO practice); Enzo (guidelines not binding).
2. **"Isolated" or "purified" natural product.** Trap: assuming lab isolation makes a natural compound or DNA eligible. Correct: isolation alone is not a marked difference; claim a new structural or functional property. Cases: Myriad; Funk Bros.; ChromaDex (2023).
3. **cDNA vs. short cDNA.** Trap: assuming every cDNA is eligible. Correct: short sequences with no introns may be identical to natural DNA and ineligible. Case: Myriad.
4. **Clone or copy of a natural organism.** Trap: phenotypic differences in the spec save the claim. Correct: the difference must be claimed and its effect explained. Case: Roslin.
5. **Diagnostic "detect and correlate" claim with an administering step.** Trap: thinking an "administering" step makes it a treatment claim. Correct: in Mayo the administering step only set the context; a treatment claim must require a specific treatment decision acted on (dose, drug, patient group). Cases: Mayo; Vanda (2018); CareDx (2022).
6. **New measurement on a known sample type.** Trap: a "new" assay recited with standard lab techniques. Correct: standard techniques used to observe a natural phenomenon are ineligible; a new technique or a method of preparing the sample may survive. Cases: CareDx; Illumina v. Ariosa (2020); Rapid Litigation Mgmt. v. CellzDirect, 827 F.3d 1042 (Fed. Cir. 2016).
7. **Software claimed as a "system with a processor and memory."** Trap: adding hardware nouns avoids 101. Correct: generic, functionally described hardware adds nothing; system and medium claims rise or fall with the method. Case: Alice (part C); Bernhart is no longer protective.
8. **Physical device claimed broadly.** Trap: "it's a camera, so it can't be abstract." Correct: a device claim at a high level of generality whose only advance is an idea can be abstract (*Yu v. Apple*, 1 F.4th 1040 (Fed. Cir. 2021)); but courts must read the claim as construed, and specific technical means win (*Contour IP v. GoPro*, 113 F.4th 1373 (Fed. Cir. 2024)). Correct action: match claim breadth to the specific hardware improvement the spec describes.
9. **Physical process applying a law of physics.** Trap: a mechanical manufacturing method is always eligible. Correct: a claim that only says "tune X so it attenuates vibration" can be directed to a natural law (Hooke's law). Case: American Axle v. Neapco, 967 F.3d 1285 (Fed. Cir. 2020), cert. denied 2022. Recite the specific structure and steps, not the goal.
10. **Spec calls the core steps "conventional."** Trap: humble background language. Correct: the patentee's own words become clear evidence of conventionality at step two; conversely, specific statements of unconventionality create fact issues that defeat early dismissal. Cases: CareDx; Berkheimer; Aatrix; Cooperative Entertainment.
11. **"It's novel, so it's eligible."** Trap: merging 101 with 102/103. Correct: a new abstract idea is still abstract; novelty of the idea does not supply an inventive concept. Cases: Mayo; Myriad ("groundbreaking" discovery insufficient); Flook.
12. **Field-of-use limit.** Trap: restricting a formula to one industry saves it. Correct: limiting an abstract idea to a technological environment or adding insignificant post-solution activity does not. Cases: Flook; Alice; Bilski.
13. **State Street, AT&T, or "useful, concrete and tangible result."** Trap: citing pre-Bilski Federal Circuit law. Correct: abrogated. Cases: Bilski; Alice.
14. **Tax strategy as the novel feature.** Trap: treating it as a 101 question only. Correct: AIA §14 removes it from the novelty and obviousness comparison regardless of 101.
15. **Surgical technique patent.** Trap: treating it as valuable against hospitals. Correct: §287(c) removes remedies against medical practitioners for pure procedures; claim the device or composition too.
16. **Deceptive, addictive, or controversial invention.** Trap: flagging a utility or morality rejection. Correct: no US moral-utility bar; only statutory exclusions (human organisms, nuclear weapons). Case: Juicy Whip; AIA §33(a). Foreign offices differ (EPC Art. 53(a)).
17. **"Worse than the prior art."** Trap: thinking an inferior device lacks utility. Correct: superiority is not required. Cases: Lowell v. Lewis; Custom Accessories; Brooktree (only total inoperability fails).
18. **Research intermediate or tool with no known end use.** Trap: listing generic uses (probe, marker, screening). Correct: uses shared by the whole class are not specific; uses needing further research are not substantial. Cases: Brenner; Fisher. A microscope-like tool with immediate benefit on any sample is different.
19. **Drug candidate with only cell or animal data.** Trap: assuming human or FDA-level proof is needed for utility. Correct: art-accepted in vitro or animal data can suffice. Cases: Cross v. Iizuka; Brana.
20. **Perpetual motion, cold fusion, "anti-aging device."** Trap: drafting as if any asserted effect is accepted. Correct: incredible utility triggers a demand for proof; claim what the data support. Cases: Newman v. Quigg; Swartz.
21. **Trade secret vs. patent for an invisible process.** Trap: keeping the process secret while selling its output for years, then filing. Correct: commercial exploitation of the secret (including selling products made by it) starts the grace-period clock on the process. Cases: Metallizing; Celanese (2024). Choose early.
22. **Someone else's secret prior use.** Trap: treating a competitor's secret, earlier commercial use as invalidating prior art. Correct: secret third-party use is generally not prior art against a later independent inventor, but the secret user may have a §273 defense. Cases: W.L. Gore v. Garlock; 35 U.S.C. §273.
23. **State-law protection for an unpatented product design.** Trap: suggesting a state anti-copying claim after launch. Correct: preempted unless it targets confusion, breach of confidence, or contract. Cases: Bonito Boats; Kewanee.

---

## Post-casebook developments (through Nov. 2026)

The casebook's notes stop at Berkheimer and Aatrix (Feb. 2018). The 2025–2026 Federal Circuit decisions (Recentive, US Synthetic, PowerBlock, GoTV, Constellation, REGENXBIO, Ollnova, Dental Monitoring) and the Desjardins/USPTO guidance are digested in [`../eligibility-101.md`](../eligibility-101.md) §§4–5; they are not repeated here.

- *Vanda Pharms. Inc. v. West-Ward Pharms. Int'l Ltd.*, 887 F.3d 1117 (Fed. Cir. 2018): a claim to treating schizophrenia by genotyping the patient and administering iloperidone at a dose set by the genotype is not directed to a natural law; it applies the relationship in a specific treatment. Prost dissented. USPTO memo of June 7, 2018 adopted it. **Skill rule:** Drafting: for any biomarker discovery, include an independent method-of-treatment claim with a specific drug and dose tied to the test result.
- *Athena Diagnostics, Inc. v. Mayo Collaborative Servs.*, 915 F.3d 743 (Fed. Cir. 2019), reh'g en banc denied, 927 F.3d 1333 (Fed. Cir. 2019): detecting antibodies to a protein (MuSK) to diagnose a neurological disorder, using standard techniques, is ineligible even though the correlation was new. **Skill rule:** Phase 1 Check B: rate pure diagnostic claims high risk in court.
- *Natural Alternatives Int'l v. Creative Compounds, LLC*, 918 F.3d 1338 (Fed. Cir. 2019): beta-alanine dietary supplement and treatment claims at specific doses not directed to a natural law at the pleading stage. **Skill rule:** Drafting: claim the formulation and the dosing regimen, not the natural compound's effect.
- *Illumina, Inc. v. Ariosa Diagnostics, Inc.*, 952 F.3d 1367, modified, 967 F.3d 1319 (Fed. Cir. 2020) (2–1): a method of preparing a cell-free DNA fraction enriched for fetal DNA by size selection is eligible; it manipulates the sample rather than merely observing a natural phenomenon. Reyna dissented. Cert. petition dismissed by stipulation under Rule 46 (No. 20-892, May 21, 2021). **Skill rule:** Drafting: for discoveries about natural phenomena, include method-of-preparation claims with concrete physical steps.
- *American Axle & Mfg. v. Neapco Holdings LLC*, 967 F.3d 1285 (Fed. Cir. 2020), cert. denied, No. 20-891 (June 30, 2022): claim 22, a method of making a driveshaft by tuning a liner's mass and stiffness to damp vibrations, merely required applying Hooke's law to reach a result (claim 1, which also required positioning the liner, was vacated and remanded; the 2019 original opinion, 939 F.3d 1355, was modified on panel rehearing); the Court denied review despite the SG's recommendation to grant. **Skill rule:** Drafting mechanical claims: recite the specific structural parameters or steps that achieve the effect.
- *Yu v. Apple Inc.*, 1 F.4th 1040 (Fed. Cir. 2021) (Newman, J., dissenting): a two-sensor digital camera claim directed to enhancing one image with another is abstract; conventional hardware gave no inventive concept.
- *CareDx, Inc. v. Natera, Inc.*, 40 F.4th 1371 (Fed. Cir. 2022): detecting donor cell-free DNA with conventional techniques to diagnose transplant rejection is ineligible; the court considered conventionality at step one too and noted the case did not involve a method of preparation or a new measurement technique.
- *Cooperative Entm't, Inc. v. Kollective Tech., Inc.*, 50 F.4th 127 (Fed. Cir. 2022): reversed a Rule 12 dismissal; spec statements about how the claimed network differed from the prior art made an inventive concept plausible. **Skill rule:** Spec drafting: explain the prior-art gap and the claimed fix in concrete terms; these sentences are the patentee's best Rule 12 evidence.
- *ChromaDex, Inc. v. Elysium Health, Inc.*, 59 F.4th 1280 (Fed. Cir. 2023): isolated nicotinamide riboside compositions not markedly different from NR in milk; ineligible (cert. denied Oct. 16, 2023, No. 23-245).
- *Celanese Int'l Corp. v. ITC*, 111 F.4th 1338 (Fed. Cir. 2024), cert. denied (Apr. 28, 2025): the AIA did not change the rule that pre-critical-date sales of products made by a secret process bar a patent on that process. (Full treatment in `novelty-and-bars.md`.)
- *Contour IP Holding LLC v. GoPro, Inc.*, 113 F.4th 1373 (Fed. Cir. 2024) (Nos. 22-1654, -1691, decided Sept. 9, 2024): reversed ineligibility of point-of-view camera claims; the district court described the claims at too high a level of generality, and reciting known components does not make a claim abstract.
- *AIA §18 CBM review* expired for new petitions on Sept. 16, 2020.
- **Utility:** No precedential Federal Circuit decision since Fisher was found that changes the utility standard; MPEP 2107 (2107.01 revised 07.2022) still applies Brenner and Fisher. Status of any newer utility case: not verified.

---

## Checklist for the skill

- Separate the three questions in every 101 output: statutory category, judicial exception (Alice/Mayo), and utility. Never merge them with novelty.
- Read the claim as drafted, not the invention. Eligibility attaches to each claim; flag claims, not inventions.
- Report two outlooks for 101: USPTO (per `../eligibility-101.md`) and court (per this file). Never say allowance settles it.
- For natural products and DNA: ask what structural or functional difference from nature the claim recites. "Isolated" alone gets a high-risk flag.
- For diagnostics: ask whether the claim requires a specific treatment, a new measurement technique, or a specific sample-preparation step. If none, flag high risk and propose those claim types.
- For software and AI: identify the technical problem, the mechanism, and the measurable improvement; confirm the independent claim recites the mechanism, not just the result, and that system and medium claims carry the same mechanism.
- Scan the draft spec for "conventional," "standard," "well known," "routine," and "generic" near the core steps; rewrite or remove (CareDx, Berkheimer).
- Add at least one sentence per core element explaining what is unconventional about it, in factual terms.
- For every claimed compound, sequence, intermediate, or dataset: state one specific, substantial, currently available use with supporting data (Brenner, Fisher, Brana).
- If the asserted effect contradicts accepted science, ask for data before drafting and expect a credibility rejection.
- Do not flag morality or deception; flag only AIA §33(a) (human organisms) and 42 U.S.C. §2181(a) (atomic weapons) as US statutory exclusions.
- Exclude humans from any organism claim.
- Never cite State Street, AT&T, or machine-or-transformation as the test.
- For invisible processes, raise the trade-secret alternative and its limits, and warn that selling products made by a secret process starts the patent clock on that process.
- For FTO: check §287(c) for medical procedures and §273 for the client's own prior secret commercial use.
- Never apply US 101 law to EP, JP, or CN; refer to local counsel.
