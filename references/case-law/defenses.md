---
title: Infringement defenses (experimental use, safe harbor, misuse, estoppel, laches, shop rights, exhaustion, repair, prior use, assignor estoppel, licenses) — case law and edge cases
last_verified: 2026-11-18
sources:
  - Adelman et al., Patent Law — Cases and Materials (5th ed.), ch. 13 (used for case selection only; digests are original)
  - https://www.law.cornell.edu/supct/html/03-1237.ZO.html (Merck v. Integra, 2005)
  - https://www.supremecourt.gov/opinions/16pdf/15-927_6j37.pdf (SCA Hygiene, 2017)
  - https://www.supremecourt.gov/opinions/16pdf/15-1189_ebfj.pdf (Impression Products, 2017)
  - https://www.supremecourt.gov/opinions/20pdf/594us2r64_anbf.pdf (Minerva v. Hologic, 2021)
  - https://www.cafc.uscourts.gov/opinions-orders/24-2274.OPINION.5-6-2025_2509887.pdf (Jazz v. Avadel, 2025)
  - https://www.supremecourt.gov/orders/journal/jnl02.pdf (Madey cert. denied, No. 02-1007)
  - https://www.sec.gov/Archives/edgar/data/1447028/000144702826000064/abus-20260930.htm (Arbutus Form 10-Q, Nov. 10, 2026: Moderna settlement and § 1498 appeal)
  - https://www.law.cornell.edu/uscode/text/35/273 ; https://www.law.cornell.edu/uscode/text/35/271
  - https://www.supremecourt.gov/docket/docketfiles/html/public/24-428.html (Edwards v. Meril cert. denied)
  - full list in "Verification sources" at the end of this file
---

# How to use this file

Load it for FTO screens (Phase 2, FTO mode), for any "can we keep doing X?" question, for license and supply-chain questions, and when a user who sold, assigned, or licensed a patent asks what they can still do. Defenses here are not validity attacks (those live in the novelty, obviousness, and disclosure files). Most are fact-heavy and equitable; the skill never concludes that a defense "applies." It lists which defenses the facts make available, what evidence each needs, and who bears the burden.

Burden reminder: the accused infringer bears the burden on every defense in this file (Madey; Aukerman; § 273 requires clear and convincing evidence).

---

## 1. Common-law experimental use

### Roche Products, Inc. v. Bolar Pharmaceutical Co., 733 F.2d 858 (Fed. Cir. 1984) · CB p. 861
- **Facts:** Before Roche's flurazepam patent expired, generic maker Bolar imported 5 kg of the compound to run stability, dissolution, and bioequivalence tests for FDA approval so it could launch on expiry.
- **Holding / rule:** Using a patented compound to generate FDA test data is infringing use. The experimental-use exception is "truly narrow": it covers use for amusement, idle curiosity, or strictly philosophical inquiry, not tests with "definite, cognizable, and not insubstantial commercial purposes." Small quantity did not make it de minimis. The court refused to create a policy exception for generics; that was for Congress.
- **Nuance:** Bolar conceded its use fell outside traditional limits, which was fatal. The court relied on Pitcairn v. United States, 547 F.2d 1106 (Ct. Cl. 1976): tests in keeping with the user's legitimate business are not exempt.
- **Status:** Common-law holding on experimental use remains good law (applied in Embrex and Madey). The result for FDA testing was superseded by statute: 35 U.S.C. § 271(e)(1) (Drug Price Competition and Patent Term Restoration Act of 1984, "Hatch-Waxman"), which also added 271(e)(2) and patent-term extension (§ 156).
- **Skill rule:** FTO: never tell a commercial user that internal testing, benchmarking, or "R&D only" use is exempt; the only broad exemption is the statutory FDA safe harbor (§ 2 below), which has its own limits.

### Madey v. Duke University, 307 F.3d 1351 (Fed. Cir. 2002) · CB p. 868
- **Facts:** Madey, a laser researcher, moved his free-electron-laser lab (with equipment practicing his two patents) from Stanford to Duke. After Duke removed him as director and he left, Duke kept operating the equipment for research. The district court applied experimental use because Duke's use was non-profit and academic.
- **Holding / rule:** Experimental use is a very narrow defense limited to use "solely for amusement, to satisfy idle curiosity, or for strictly philosophical inquiry." Use in furtherance of the user's legitimate business does not qualify, and a research university's business includes research, education, prestige, and grant-getting. Non-profit status is not determinative. The defense is the accused infringer's to prove; the district court wrongly made the patentee disprove it.
- **Nuance:** The court declined to hold that Warner-Jenkinson's rejection of intent abolished the defense. Experimental use need not be pleaded as an affirmative defense; it can be raised later at the court's discretion. The Ruth v. Stearns-Roger (D. Colo. 1935) approach (school use exempt) was rejected.
- **Status:** Good law as of 2026-11-18. Cert denied, 539 U.S. 958 (2003) (No. 02-1007, June 27, 2003), after the Court invited the Solicitor General's views (Supreme Court Journal, OT 2002). No later case limits it.
- **Skill rule:** FTO for universities, hospitals, labs, and nonprofits: treat their research use as ordinary infringing use; flag that the defense almost never succeeds and that the realistic options are licensing, design-around, the 271(e)(1) safe harbor if FDA-related, or § 1498 if the work is for the US government.

### Note cases (compact)
- **Embrex, Inc. v. Service Engineering Corp., 216 F.3d 1343 (Fed. Cir. 2000) · CB p. 869, 872.** Restated the amusement/idle-curiosity/philosophical-inquiry limit; Rader's concurrence would deny the defense for use with the "slightest commercial implication." **Skill rule:** Same as Madey.
- **Whittemore v. Cutter, 29 F. Cas. 1120 (C.C.D. Mass. 1813) (Story, J.) · CB p. 862.** Origin of the exception (philosophical experiments, testing whether the machine works). **Skill rule:** Analysis: cite only for history, never as a modern standard.
- **Exhaustion substitute · CB p. 851.** Buying a patented product on the market and testing it raises no experimental-use issue because the sale exhausted the patent for that unit; synthesizing your own copy does. **Skill rule:** FTO: when a user wants to test a competitor's patented product, recommend buying authorized units rather than making copies.
- **Foreign research and regulatory exemptions · CB p. 859–60.** Japan (Ono v. Kyoto, 1999) exempts generic approval testing as "experiment"; Germany (Klinische Versuche I and II) exempts research on the patented subject matter but not use of a patented research tool for its purpose; EU Directive 2004/27/EC art. 10(6) harmonized a Bolar exemption. **Skill rule:** All phases: never apply these to US activity or US law to them; route foreign questions to local counsel (SKILL.md US-utility scope).

---

## 2. Statutory safe harbor, 35 U.S.C. § 271(e)(1)

Enacted in 1984 (Hatch-Waxman) to reverse Roche v. Bolar's result. It is not infringement to make, use, offer, sell, or import a patented invention "solely for uses reasonably related to the development and submission of information" under a federal law regulating the manufacture, use, or sale of drugs or veterinary biological products. The casebook defers the cases to ch. 16. They are digested here because the safe harbor is the main FTO defense for regulated products.

### Merck KGaA v. Integra Lifesciences I, Ltd., 545 U.S. 193 (2005) · not excerpted (CB p. 843 intro points to ch. 16)
- **Facts:** Merck funded university experiments using Integra's patented RGD peptides to identify drug candidates and test their efficacy, mechanism, and toxicity in the lab and in animals before any clinical filing.
- **Holding / rule:** The safe harbor "extends to all uses of patented inventions that are reasonably related to the development and submission of *any* information under the FDCA." That includes preclinical studies of candidates that are never submitted, and experiments on drugs that never reach the FDA. Coverage holds as long as there is a reasonable basis to believe the experiments will produce information relevant to an IND or NDA.
- **Nuance:** Footnote 7 expressly declined to decide whether the safe harbor covers patented "research tools" used in the development process. Basic research not aimed at any regulatory submission is outside it. The test is objective (a reasonable basis), not the experimenter's subjective motive.
- **Status:** Good law as of 2026-11-18; applied in Edwards v. Meril (2024) and Jazz v. Avadel (2025).
- **Skill rule:** FTO for drug, biologic, and device development: map each planned activity to the regulatory submission it feeds; mark activities with a plausible link to an IND/NDA/ANDA/BLA/510(k)/PMA as "safe-harbor candidate," and mark research-tool use, platform screening unrelated to a specific product, and commercial-scale production as outside it or unresolved.

### Note cases on the safe harbor (compact, verified)
- **Proveris Scientific v. Innovasystems, 536 F.3d 1256 (Fed. Cir. 2008).** A measuring device that itself needs no FDA premarket approval cannot claim the safe harbor, even though customers use it to make FDA submissions. **Skill rule:** FTO: the safe harbor protects makers of products subject to FDA approval, not suppliers of unregulated tools.
- **Classen Immunotherapies v. Biogen IDEC, 659 F.3d 1057 (Fed. Cir. 2011); Momenta Pharms. v. Amphastar, 686 F.3d 1348 (Fed. Cir. 2012).** Classen: information routinely reported to the FDA long after approval is outside the harbor. Momenta: post-approval batch testing required to keep an approval is protected, which limits Classen. **Skill rule:** FTO: post-approval activity is protected only when required to maintain approval, not when it is ordinary commercial reporting.
- **Amgen Inc. v. Hospira, Inc., 944 F.3d 1327 (Fed. Cir. 2019).** The test applies to each act of manufacture, asking "whether each act of manufacture was for uses reasonably related" to FDA submission; other purposes do not matter once that link is proved. The jury's finding that 14 of 21 batches were unprotected was affirmed, although Hospira argued all 21 fed its FDA filings. A "commercial inventory" label was probative but not dispositive (the jury found some such batches protected). Submitting a lot's data to the FDA does not by itself protect its manufacture (n.3, citing Momenta v. Teva (Fed. Cir. 2015) on routine record-retention requirements of commercial production). **Skill rule:** FTO / biosimilars: track each batch's purpose at the time it was made; inventory or launch builds are strong evidence against the safe harbor even if some batches later go to the FDA.
- **Edwards Lifesciences v. Meril Life Sciences, 96 F.4th 1347 (Fed. Cir. 2024) (2–1; Lourie, J., dissenting), cert. denied, No. 24-428 (Jan. 13, 2025).** Importing two transcatheter-valve samples to a medical conference to recruit clinical investigators was protected. Intent and alternative uses are irrelevant if the act is reasonably related to FDA submission. **Skill rule:** FTO: treat imports and demonstrations tied to recruiting trial sites as safe-harbor candidates; flag sales-oriented marketing at the same event as unprotected.
- **Jazz Pharms. v. Avadel CNS Pharms., No. 2024-2274 (Fed. Cir. May 6, 2025) (precedential; reporter cite 136 F.4th 1075 not verified).** After an infringement verdict, the injunction's bar on new clinical trials and open-label extensions was reversed as unlawfully overbroad under § 271(e)(1) and (e)(3). Its bar on seeking FDA approval for new indications was vacated and remanded: if that submission would infringe under § 271(e)(2), it cannot be enjoined; if not, the court must redo the eBay analysis. **Skill rule:** Litigation-risk notes: courts cannot enjoin safe-harbored clinical development even after an infringement finding on commercial activity.

---

## 3. Patent misuse

### USM Corp. v. SPS Technologies, Inc., 694 F.2d 505 (7th Cir. 1982) (Posner, J.) · CB p. 877
- **Facts:** In settling an infringement suit, SPS licensed USM and let it sublicense. USM kept 75% of sublicense royalties, but only 25% for four companies SPS had already licensed directly. USM later sued, calling the differential royalty patent misuse.
- **Holding / rule:** Outside a handful of conventional per se categories (tying, resale price maintenance, post-expiration royalties, royalties on unpatented products), misuse claims are tested by antitrust principles and require proof of actual or probable anticompetitive effect in a relevant market. Differential royalties (price discrimination) are not misuse by themselves; the differential here plausibly addressed a free-rider problem. Summary judgment for SPS on misuse affirmed.
- **Nuance:** Regional-circuit case, but its antitrust-anchored view is the one the Federal Circuit later adopted. Misuse is a defense, not a tort (Transitron, cited in USM). Misuse bars enforcement until "purged," and under Morton Salt the infringer need not have been harmed by the misuse. The court also noted the irony that the patent may have been invalid, but res judicata from the consent judgment barred USM from showing it.
- **Status:** The approach matches current Federal Circuit law (Princo, en banc 2010) and 35 U.S.C. § 271(d)(4)–(5); see Post-casebook.
- **Skill rule:** FTO / licensing review: raise misuse only for the recognized categories (tying a staple without market power does not count after § 271(d)(5); post-expiration royalties under Brulotte/Kimble; royalties on unpatented goods coerced by the patentee); otherwise treat aggressive licensing terms as an antitrust question for counsel, not a defense.

### Note cases on misuse (compact)
- **Morton Salt Co. v. G.S. Suppiger Co., 314 U.S. 488 (1942) · CB p. 860.** Patentee that tied unpatented salt tablets to its patented machine could not enforce the patent even against a direct infringer it had not harmed. **Skill rule:** FTO: if the patentee ties unpatented supplies to its patented product, flag misuse as a possible unenforceability defense until purged.
- **Motion Picture Patents Co. v. Universal Film Mfg., 243 U.S. 502 (1917); Heaton-Peninsular Button-Fastener v. Eureka Specialty, 77 F. 288 (6th Cir. 1896) · CB p. 860.** Motion Picture Patents refused enforcement of a tie of unpatented films to patented projectors, displacing Heaton-Peninsular's tolerance of supply ties. **Skill rule:** Analysis: cite for history; modern ties also need market power (§ 271(d)(5)).
- **Brulotte v. Thys Co., 379 U.S. 29 (1964); Zenith Radio v. Hazeltine Research, 395 U.S. 100 (1969); Bauer & Cie v. O'Donnell, 229 U.S. 1 (1913) · CB p. 878.** Post-expiration royalties, coerced royalties on unpatented end products, and resale price control are misuse categories. **Skill rule:** Portfolio / licensing: flag any license that collects royalties past the last-to-expire patent without a step-down; Kimble (2015) kept Brulotte (see Post-casebook).
- **Dawson Chemical v. Rohm & Haas, 448 U.S. 176 (1980) · CB p. 878.** A patentee may refuse to license and may control nonstaple goods used only in its patented process without misuse, consistent with § 271(d). **Skill rule:** FTO: selling a nonstaple component for a patented method and suing contributory infringers is protected conduct, not misuse.
- **Windsurfing Int'l v. AMF, 782 F.2d 995 (Fed. Cir. 1986); Senza-Gel v. Seiffhart, 803 F.2d 661 (Fed. Cir. 1986); Mallinckrodt v. Medipart, 976 F.2d 700 (Fed. Cir. 1992) · CB p. 867.** Federal Circuit misuse requires impermissibly broadening the patent's scope with anticompetitive effect (Windsurfing); Senza-Gel applied the traditional tying per se rule; Mallinckrodt's post-sale restriction holding was later abrogated by Impression Products (2017). **Skill rule:** Analysis: never cite Mallinckrodt for enforcing post-sale restrictions through patent law.
- **Shrimp-peeler cases (La Peyre v. FTC, 366 F.2d 117 (5th Cir. 1966); Laitram v. King Crab, 244 F. Supp. 9 (D. Alaska 1965)) · CB p. 880.** Discriminatory royalty rates were condemned where they distorted competition among the patentee's customers and the patentee had an interest in one group. **Skill rule:** Licensing review: differential royalties are suspect only with proof of competitive harm in a market.

---

## 4. Equitable estoppel

### A.C. Aukerman Co. v. R.L. Chaides Construction Co., 960 F.2d 1020 (Fed. Cir. 1992) (en banc) · CB p. 884
- **Facts:** In 1979 Aukerman's counsel wrote Chaides several times offering a license for its highway-barrier slip-form patents. Chaides replied that any problem was its supplier's and that Aukerman could sue "for $200–$300 a year." Aukerman then said nothing for over eight years while Chaides's business grew, before threatening suit in 1987 and suing in 1988.
- **Holding / rule:** Equitable estoppel can bar the entire suit (past and future). Elements: (1) the patentee, through misleading conduct (statements, action, inaction, or silence where there was a duty to speak), led the accused infringer reasonably to infer that it would not enforce the patent against it; (2) the infringer relied on that conduct; (3) the infringer would be materially prejudiced (economic or evidentiary) if suit proceeds. No presumption applies; delay is evidence but not an element. The trial judge has discretion and weighs other equities. Summary judgment for Chaides reversed: Chaides's "$200–$300 a year" remark allowed an inference that Aukerman was only waiving a trivial claim, not abandoning it for all time.
- **Nuance:** Unlike laches, the infringer must have known of the patentee and patent and must show reliance (a relationship or communication that lulled it), not just harm. Silence alone rarely suffices; threats followed by long silence are the classic pattern. Litigation against others excuses delay only if the infringer was told about it. Jamesbury's mixed laches/estoppel test was overruled. Estoppel attaches to the claims the patentee's conduct concerned. It did not bar claims that were substantively amended or added in a later reexamination, for conduct before the reexamination certificate issued (John Bean Techs. v. Morris & Assocs., 887 F.3d 1322 (Fed. Cir. 2018)). The same en banc opinion created the laches presumption (six-year delay) that SCA Hygiene later displaced for damages.
- **Status:** Equitable-estoppel portion is good law as of 2026-11-18. Fraunhofer-Gesellschaft v. Sirius XM Radio, No. 2023-2267 (Fed. Cir. June 9, 2025) (precedential) applies the three elements, cites Aukerman as abrogated on other grounds, and reversed an estoppel summary judgment for lack of proven reliance. The laches portion was overruled for damages within § 286 by SCA Hygiene (2017).
- **Skill rule:** FTO: ask whether any listed patentee previously contacted the user (letters, license offers, trade-show encounters) and then went silent; record dates, what the user did in reliance (investments, product expansion), and whether the user's reply minimized its use, because a minimizing reply undercuts estoppel if use later grows.

### Note cases (compact)
- **Jamesbury Corp. v. Litton Indus. Prods., 839 F.2d 1544 (Fed. Cir. 1988) · CB p. 888.** Four-factor estoppel test that folded in laches-style delay; expressly overruled by Aukerman on that point. **Skill rule:** Analysis: never cite Jamesbury's test.
- **Letters as triggers · CB p. 891.** A charge letter can also create declaratory-judgment jurisdiction for the recipient and can serve as actual notice under § 287 for damages. **Skill rule:** FTO: when the user received a letter, note the three consequences (estoppel clock, DJ standing, damages notice) and route to counsel.

---

## 5. Laches

### SCA Hygiene Products Aktiebolag v. First Quality Baby Products, LLC, 580 U.S. 328 (2017) · CB p. 891
- **Facts:** SCA wrote First Quality in 2003 asserting an adult-diaper patent, then waited (through a reexamination that confirmed the claims) until 2010 to sue. The Federal Circuit, following Aukerman, held laches barred pre-suit damages.
- **Holding / rule:** Laches cannot bar a claim for damages for infringement occurring within § 286's six-year period. Following Petrella v. MGM (2014) (copyright), Congress's limitations judgment displaces a judge-made timeliness defense for legal relief; § 286 counts as such a judgment even though it runs backward from suit.
- **Nuance:** Breyer dissented: a patentee can wait decades, let an infringer lock in, then sue repeatedly for six-year windows. The Court did not eliminate equitable estoppel, which remains available against misleading conduct. Footnote 2 expressly did "not address" the Federal Circuit's separate holdings on laches as a bar to equitable relief (injunctions, ongoing royalties) or on equitable estoppel. The opinion observed that equitable estoppel answers some of the defendant's concerns. Prosecution laches (unreasonable delay in getting the patent issued) is a different doctrine and survives (see the prosecution-laches note below).
- **Status:** Good law as of 2026-11-18; it overruled Aukerman's laches holding as applied to damages within § 286.
- **Prosecution laches (separate doctrine, verified).** A patent can be unenforceable for unreasonable and unexplained delay in prosecution that prejudices others. Hyatt v. Hirshfeld, 998 F.3d 1347 (Fed. Cir. 2021): the PTO may assert prosecution laches in a § 145 action even without earlier rejections. On remand laches was affirmed (Hyatt v. Stewart, 148 F.4th 1376 (Fed. Cir. Aug. 29, 2025); cert. denied sub nom. Hyatt v. Squires, No. 25-1049 (June 29, 2026)). Personalized Media Commc'ns v. Apple, 57 F.4th 1346 (Fed. Cir. 2023): unenforceability affirmed. Google LLC v. Sonos, Inc., No. 2024-1097 (Fed. Cir. Aug. 28, 2025) (nonprecedential): a laches judgment was reversed because Google showed no prejudice attributable to Sonos's delay. Prejudice, typically intervening rights or investment during the delay, is essential.
- **Skill rule:** FTO / risk ranking: never discount a patent because the owner knew of the product for years and did nothing; delay alone no longer cuts off damages within six years before suit, so investigate estoppel facts (misleading communications plus reliance) instead.

---

## 6. Shop rights (an implied license from employment)

### McElmurry v. Arkansas Power & Light Co., 995 F.2d 1576 (Fed. Cir. 1993) · CB p. 897
- **Facts:** Bowman, a consultant to AP&L, co-designed (with an AP&L employee) a vacuum-based hopper level detector. AP&L paid for testing and installation on hundreds of hoppers, with Bowman's consent and participation, before his patent issued. Bowman believed AP&L would have shop rights. His assignee later sued AP&L for hiring a different contractor to install detectors on more hoppers.
- **Holding / rule:** Whether an employer holds a shop right is decided on the totality of the circumstances under equity and fairness: the circumstances of the invention's development (employer time, materials, money) and the inventor's later conduct (consent, acquiescence, inducement, assistance without demanding pay). AP&L had a shop right, which let it duplicate and keep using the detector in its business and have outside contractors build it.
- **Nuance:** A shop right is non-exclusive, free, and limited to the employer's own business; it does not let the employer license or sell the invention to others. Merely sharing specifications with contractors is not infringement. Applies to consultants, not only W-2 employees, when the equities fit. Classic statement: United States v. Dubilier Condenser Corp., 289 U.S. 178 (1933). Pre-assignment conduct by the inventor binds the later assignee.
- **Status:** Good law as of 2026-11-18. No later limiting decision found; no later citing case was verified this session.
- **Skill rule:** FTO: when the user's own employee or contractor invented and patented something using the user's time, money, or facilities, and the user has been using it with the inventor's knowledge, flag a possible shop right and gather the employment or consulting agreement, funding records, and the inventor's statements.

### Note cases (compact)
- **Employee-inventor law abroad · CB p. 903.** Germany's Employee Inventions Act gives employees mandatory compensation for service inventions. **Skill rule:** Portfolio: flag foreign-inventor compensation duties for non-US inventors; do not apply US shop-right law abroad.

---

## 7. Exhaustion (first sale)

### Impression Products, Inc. v. Lexmark International, Inc., 581 U.S. 360 (2017) · CB p. 903
- **Facts:** Lexmark sold toner cartridges in the US under a discounted "Return Program" with single-use, no-resale terms, and also sold cartridges abroad. Remanufacturer Impression bought spent cartridges, defeated the anti-reuse chip, refilled them, and resold them in the US, including imported foreign-sold units.
- **Holding / rule:** (1) A patentee's authorized sale exhausts all patent rights in that item regardless of any post-sale restriction; restrictions may be enforceable in contract but not by an infringement suit. The same applies to sales by a licensee acting within its license. (2) An authorized sale outside the US exhausts US patent rights just as a domestic sale does. Federal Circuit reversed; Mallinckrodt and Jazz Photo's territorial rule abrogated.
- **Nuance:** The key line is sale versus license. A patentee can restrict a licensee (General Talking Pictures, 1938), and a licensee who sells outside its license makes an unauthorized sale that exhausts nothing. Boesch v. Graff (1890) survives: a foreign sale by someone with no authority from the US patentee does not exhaust. Ginsburg dissented on international exhaustion. The Court did not address repair versus reconstruction (Aro), so refurbishment that amounts to making a new article remains infringement.
- **Status:** Good law as of 2026-11-18.
- **Skill rule:** FTO: for resale, refurbishment, gray-market import, or use of purchased parts, first ask who first sold each unit and with what authority; units first sold anywhere in the world by the US patentee or its licensee acting within the license are exhausted (mark `exhausted`, not `absent`), while units from an unlicensed foreign maker or from a licensee selling outside its field are not.

### Note cases on exhaustion (compact)
- **Quanta Computer v. LG Electronics, 553 U.S. 617 (2008); United States v. Univis Lens, 316 U.S. 241 (1942) · CB p. 908.** An authorized sale of an item that substantially embodies a patent (its only reasonable use practices the patent and it contains the inventive features) exhausts method and apparatus claims; Univis: sale of lens blanks exhausted patents on finished lenses. **Skill rule:** FTO: treat buying an authorized component whose only reasonable use is the patented system as likely exhausting the patent for that system; verify the seller's license scope.
- **Bloomer v. McQuewan (1853); Keeler v. Standard Folding Bed (1895) · CB p. 907–08.** Sold article leaves the monopoly; one reward per item. **Skill rule:** Analysis: background only.
- **Boesch v. Graff, 133 U.S. 697 (1890) · CB p. 912.** A German maker lawfully making burners under German law, without authority from the US patentees, could not authorize US sale. **Skill rule:** FTO for imports: exhaustion requires authority traceable to the US patent owner.
- **Kirtsaeng v. John Wiley & Sons, 568 U.S. 519 (2013) · CB p. 910.** Copyright first-sale applies to copies made and sold abroad; Impression extends the same logic to patents. **Skill rule:** None beyond Impression.

---

## 8. Repair versus reconstruction

### Jazz Photo Corp. v. International Trade Comm'n, 264 F.3d 1094 (Fed. Cir. 2001) · CB p. 916
- **Facts:** Fuji's single-use cameras were opened by processors to remove film. Overseas remanufacturers bought the shells, cut them open, inserted new film and container, replaced batteries and sometimes winding wheels, reset the counter, resealed, and recovered; importers brought them into the US. The ITC called this reconstruction.
- **Holding / rule:** For cameras first sold in the US with Fuji's authority and refurbished only by the listed steps, the work is permissible repair. Owners may preserve the useful life of the article; reconstruction requires a second creation of the patented entity after the whole has become spent. Replacing unpatented, shorter-lived parts (film, battery) is repair. Reusing (not replacing) separately patented components is neither repair nor reconstruction. The patentee's unilateral intent that the article be single-use does not convert repair into reconstruction unless embodied in an enforceable contract.
- **Nuance:** The court refused rigid factor tests (Aro I warned against them). Cameras of solely foreign first sale were held not exhausted; Impression Products (2017) abrogated that territorial holding, so authorized foreign first sales now exhaust too. Remanufacturers who refused discovery lost because they could not prove their process stayed within the permitted steps. Follow-on enforcement, Fuji Photo Film v. ITC, 474 F.3d 1281 (Fed. Cir. 2007): the accused importer bore the burden of proving both US first sale and permissible repair, and lost for most cameras (foreign first sale, or no adequate process evidence). The court held that replacing the camera's full back was still repair, reversing the Commission on that point. Fuji's foreign-sale reasoning falls with Jazz Photo's after Impression (an inference; Fuji was not itself reviewed).
- **Status:** Repair/reconstruction holding good law as of 2026-11-18; foreign-sale (territorial exhaustion) holding abrogated by Impression Products, 581 U.S. 360 (2017).
- **Skill rule:** FTO for refurbishers and aftermarket parts: list each step of the process and each replaced part; mark repair-type steps (replacing worn or consumable unpatented parts, cleaning, resetting) as lower risk and steps that rebuild a spent article or replace a separately patented component as reconstruction risk; insist on records proving the process for every unit.

### Note cases on repair and reconstruction (compact)
- **Aro Mfg. Co. v. Convertible Top Replacement Co., 365 U.S. 336 (1961) (Aro I) · CB p. 922, 928.** Replacing the worn fabric of a patented convertible-top combination is repair; mere replacement of individual unpatented parts, one at a time, is repair, and reconstruction requires making a new article after the whole is spent. **Skill rule:** FTO: a replacement-parts supplier is not a contributory infringer when its customers' replacement is repair of authorized products.
- **Wilson v. Simpson, 50 U.S. (9 How.) 109 (1850) · CB p. 922.** Replacing dull planing-machine knives that last 60–90 days is repair. **Skill rule:** Analysis: short-lived consumable parts point to repair.
- **Wilbur-Ellis Co. v. Kuther, 377 U.S. 422 (1964) · CB p. 922.** Resizing six parts of used fish-canning machines to pack a different can size was "kin to repair." **Skill rule:** FTO: adapting a lawfully bought machine to a related use is usually not reconstruction, but creating a new machine is.
- **General Electric v. United States, 572 F.2d 745 (Ct. Cl. 1978); Dana Corp. v. American Precision, 827 F.2d 755 (Fed. Cir. 1987) · CB p. 923.** Large-scale overhaul with parts pooling (gun mounts) and commercial rebuilding of discarded clutches were repair. **Skill rule:** FTO: commercial scale and parts mixing do not by themselves make reconstruction.
- **Sandvik Aktiebolag v. E.J. Co., 121 F.3d 669 (Fed. Cir. 1997) · CB p. 924, 928.** Brazing a new carbide tip on a spent drill was reconstruction: the tip was not designed as replaceable, had no shorter expected life, was not easily detachable, and Sandvik never sold tips. **Skill rule:** FTO: when the patentee never sells the replacement part and the part was not designed to be replaced, rate reconstruction risk high.
- **Hewlett-Packard v. Repeat-O-Type Stencil, 123 F.3d 1445 (Fed. Cir. 1997) · CB p. 926.** A seller's intent, unless embodied in an enforceable contract, does not restrict a buyer's modification short of reconstruction. **Skill rule:** FTO: ask whether the purchase contract (not just packaging) restricts reuse; after Impression even a contract restriction is enforceable only in contract.
- **Other repair holdings · CB p. 923–24.** Bottom Line Mgmt. v. Pan Man, 228 F.3d 1352 (Fed. Cir. 2000) (recoating); Kendall v. Progressive Med. Tech., 85 F.3d 1570 (Fed. Cir. 1996) (pressure sleeve); Sage Prods. v. Devon, 45 F.3d 1575 (Fed. Cir. 1995) (inner container); FMC v. Up-Right, 21 F.3d 1073 (Fed. Cir. 1994) (picking heads); Everpure v. Cuno, 875 F.2d 300 (Fed. Cir. 1989) (filter cartridge); Porter v. Farmers Supply, 790 F.2d 882 (Fed. Cir. 1986) (harvester disks). Contra: Lummus Indus. v. D.M.&E., 862 F.2d 267 (Fed. Cir. 1988) (jury verdict of reconstruction for cutter wheels). **Skill rule:** Analysis: most Federal Circuit cases find repair; a reconstruction finding needs strong facts like Sandvik.
- **Akeva v. Nike (2020) · supplemental.** Despite its replaceable-sole subject matter, Akeva decides specification disclaimer and continuation priority, not repair; it is digested in `infringement.md`. **Skill rule:** Analysis: do not cite Akeva for repair or exhaustion.

---

## 9. Prior commercial user defense, 35 U.S.C. § 273 · CB p. 910

Background (CB p. 910–12): before 1999, a secret prior commercial user had no defense against a later inventor's patent. W.L. Gore & Assocs. v. Garlock, 721 F.2d 1540 (Fed. Cir. 1983), held that another's secret use is not prior art. Meanwhile the user's own secret commercial use more than a year before filing forfeited its own patent rights (Metallizing Eng'g v. Kenyon Bearing, 153 F.2d 516 (2d Cir. 1946)). The 1999 AIPA gave a defense limited to business methods, responding to State Street Bank (1998). The AIA (2011) extended the defense to all subject matter, let affiliates assert it, and excluded university-owned patents. Whether the AIA changed the treatment of secret sales as prior art is a separate question, answered in Helsinn (2019) and digested in the novelty file.

### Elements and limits, verified against the current text of § 273 (Cornell LII)
- **Who and what.** A person acting in good faith commercially used the subject matter in the US, in an internal commercial use, an arm's-length sale, or an arm's-length transfer of a useful end result. The use must have come at least 1 year before the earlier of (a) the claimed invention's effective filing date or (b) the date the claimed invention was disclosed to the public in a way that qualified for a "section 102(b)" exception. The defense covers a process, or a machine, manufacture, or composition used in a manufacturing or other commercial process (§ 273(a)).
- **Burden.** The defendant must prove it "by clear and convincing evidence" (§ 273(b)).
- **Special cases.** Premarketing regulatory review periods (for example, FDA safety and efficacy review) count as commercial use. Use by a nonprofit research lab or similar entity counts, but only for continued noncommercial use by and in that lab (§ 273(c)).
- **Exhaustion-like effect.** A sale or other disposition of a useful end result by a person entitled to the defense exhausts the patent owner's rights as if the patent owner had made the sale (§ 273(d)).
- **Personal and site-limited.** Only the person who performed or directed the use, or an entity that controls, is controlled by, or is under common control with that person, may assert the defense. It cannot be licensed or assigned except with a good-faith transfer of "the entire enterprise or line of business" to which it relates, and after such a transfer it is limited to sites where the use occurred before the later of the effective filing date or the transfer date (§ 273(e)(1)).
- **Other bars.** No defense if the use was derived from the patentee (§ 273(e)(2)). It is "not a general license under all claims" of the patent; it covers the specific commercially used subject matter, plus variations in quantity or volume and improvements that don't infringe additional claims (§ 273(e)(3)). Abandoned use cannot be revived for later acts (§ 273(e)(4)).
- **University exception.** Unavailable if the claimed invention was, when made, owned by or subject to an obligation of assignment to an institution of higher education or its technology-transfer organization. That exception itself does not apply if the activities needed to reduce the invention to practice could not have been undertaken with federal funds (§ 273(e)(5)).
- **Penalty for overreach and no invalidity inference.** If a defendant pleads the defense and loses without a reasonable basis, the court "shall find the case exceptional" for § 285 fees (§ 273(f)). Asserting the defense creates no inference of invalidity under §§ 102 or 103 (§ 273(g)).
- **Effective date.** The AIA version applies to patents issued on or after Sept. 16, 2011 (AIA § 5(c)).
- **Case law.** No precedential Federal Circuit decision construing the AIA version was found through November 2026.
- **Skill rule:** FTO: when the user has secretly and commercially used the accused process or internal product in the US, collect dated, corroborated evidence (batch records, invoices, SOPs) of use at least one year before the patent's effective filing date and before the patentee's earliest grace-period disclosure. Note the site and business unit, and check university ownership. Present the defense as a possible personal, site-bound shield needing clear and convincing proof, never as clearance. Warn that asserting it without a reasonable basis risks fees.

---

## 10. Assignor estoppel (not in the casebook chapter; assignment topic)

### Minerva Surgical, Inc. v. Hologic, Inc., 594 U.S. 559 (2021)
- **Facts:** Csaba Truckai invented an endometrial-ablation device, assigned the application and patent rights to his company (later acquired by Hologic), then founded Minerva and made a competing device. Hologic later obtained, in a continuation, a claim covering applicator heads generally (not only moisture-permeable ones) and sued Minerva. Minerva challenged validity, and the Federal Circuit applied assignor estoppel to bar the challenge.
- **Holding / rule:** Assignor estoppel survives but is limited. It "applies only when the assignor's claim of invalidity contradicts explicit or implicit representations he made in assigning the patent." The Court gave three examples where the assignor may challenge validity: (1) the assignment came before the inventor could warrant specific claims, such as an employee's assignment of future inventions; (2) a later legal development made the original warranty irrelevant; (3) the assignee obtained materially broader claims after the assignment. Vacated and remanded.
- **Nuance:** The doctrine reaches parties in privity with the assignor, such as a company the inventor founds (Federal Circuit law; the Supreme Court did not address privity). On remand the Federal Circuit found the asserted claim "not materially broader" than what Truckai had assigned, so Minerva remained estopped (Hologic, Inc. v. Minerva Surgical, Inc., No. 2019-2054 (Fed. Cir. Aug. 11, 2022); reporter cite not verified). Assignor estoppel does not apply in inter partes review, because § 311(a) lets any person who is not the owner petition (Arista Networks v. Cisco Sys., 908 F.3d 792 (Fed. Cir. 2018)).
- **Status:** Good law as of 2026-11-18.
- **Skill rule:** FTO and invalidity mode: when the user or its founder or key engineer previously assigned the patent family, flag assignor estoppel for district-court invalidity defenses. Compare the asserted claims with what existed at assignment, since materially broader later claims open the door, and note that an IPR petition is not estopped. Inventor mode: tell inventors who assign that they may later be barred from attacking those claims in court.

---

## 11. Express and implied licenses (assignment topic; shop rights are in § 6, exhaustion in § 7)

### Wang Laboratories, Inc. v. Mitsubishi Electronics America, Inc., 103 F.3d 1571 (Fed. Cir. 1997)
- **Rule:** A license can be implied from conduct: "any conduct on his part exhibited to another from which that other may properly infer that the owner consents" (quoting De Forest Radio, 1927). Wang promoted its memory-module standard, sought Mitsubishi's production, and accepted its parts over six years, so an implied royalty-free license arose (equitable estoppel and legal estoppel are related routes).
- **Skill rule:** FTO: ask whether the patentee solicited the user's adoption of a standard or design (standards work, supply requests, joint development); such conduct can imply a license and needs documents gathered.

### Met-Coil Systems Corp. v. Korners Unlimited, Inc., 803 F.2d 684 (Fed. Cir. 1986)
- **Rule:** When a patentee sells a device whose only use is to practice a patented method, its buyers get an implied license to practice the method, provided two conditions are met. First, "the equipment involved must have no noninfringing uses." Second, the circumstances of the sale must plainly indicate that a license should be inferred. A supplier of parts for that use is then not a contributory infringer.
- **Skill rule:** FTO: when the user bought equipment from the patentee (or its licensee) that has no noninfringing use, record a possible implied license to the method; check for any express restriction at the time of sale.

### General Protecht Group v. Leviton Manufacturing Co., 651 F.3d 1355 (Fed. Cir. 2011)
- **Rule:** Products licensed under a parent patent (here under a settlement) are presumed licensed under continuations sharing the same disclosure, "absent a clear indication of mutual intent to the contrary."
- **Skill rule:** FTO: when the user holds a license or settlement covering a parent patent, list the family's continuations and treat them as presumptively covered unless the agreement clearly excludes them; flag CIPs with new matter separately.

### TransCore, LP v. Electronic Transaction Consultants Corp., 563 F.3d 1271 (Fed. Cir. 2009)
- **Rule:** An unconditional covenant not to sue authorizes sales, so it triggers exhaustion for downstream buyers just as a license does. Legal estoppel extended the authorization to a later-issued related patent needed to practice what was licensed.
- **Skill rule:** FTO for buyers: if the user's supplier has a covenant not to sue or settlement with the patentee, request it; an unconditional covenant can exhaust the patent for the products bought.

### Other license rules (compact)
- **Co-owner licenses (35 U.S.C. § 262; Ethicon v. U.S. Surgical, 135 F.3d 1456 (Fed. Cir. 1998)).** Any co-owner may license without the others' consent, absent an agreement; see playbook item 16.
- **Exhaustion through licensees (Impression Products; Quanta).** A licensee's authorized sale exhausts; a sale outside the license's scope does not.

---

## 12. Government use (28 U.S.C. § 1498) and unclean hands (assignment-adjacent)

- **28 U.S.C. § 1498(a).** When a patented invention is used or manufactured "by or for the United States" without license, the owner's remedy is an action against the United States in the Court of Federal Claims for reasonable and entire compensation. Use or manufacture by a contractor counts as "for the Government" only when it is "for the Government and with the authorization or consent of the Government." This is a statutory channeling of liability, not a license.
  - Sevenson Envtl. Servs. v. Shaw Envtl., 477 F.3d 1361 (Fed. Cir. 2007): work required by a government contract with an express authorization-and-consent clause was covered.
  - IRIS Corp. v. Japan Airlines, 769 F.3d 1359 (Fed. Cir. 2014): an airline's inspection of electronic passports, which federal law mandated, was use "for the Government." The court said "incidental benefit to the government is insufficient," and found consent implied by the legal mandate.
  - Note: McElmurry (§ 6) is a shop-right case, not a § 1498 case.
  - **Skill rule:** FTO for government contractors: separate activity performed under a government contract with an authorization-and-consent clause, or required by federal law, from commercial sales; only the former is likely channeled to the Court of Federal Claims.
- **Unclean hands: Gilead Sciences, Inc. v. Merck & Co., 888 F.3d 1231 (Fed. Cir. 2018).** Merck's patents were held unenforceable against Gilead. A Merck in-house attorney joined a due-diligence call with Pharmasset (later acquired by Gilead), learned its confidential compound structure in breach of a firewall, and then helped prosecute claims aimed at it. He later testified falsely about it. The misconduct "had an immediate and necessary relation to the equity of the patent-enforcement relief Merck seeks." **Skill rule:** FTO: when the patentee obtained the user's confidential information (diligence, licensing talks, joint development) and then filed or amended claims, flag possible unclean hands and preserve the communications.
- **Inequitable conduct** (unenforceability for deceptive withholding of material information from the USPTO) is digested in the prosecution file (ch. 9), not here.

### Also cited in ch. 13 (string cites; no separate digest)
Duplan Corp. v. Deering Milliken, 444 F. Supp. 648 (D.S.C. 1977) (tie-in misuse without market-power proof, criticized in USM); SCM Corp. v. Xerox, 645 F.2d 1195 (2d Cir. 1981) (not every patent confers market power); Transitron Elec. v. Hughes Aircraft, 487 F. Supp. 885 (D. Mass. 1980) (misuse is not a tort); Mitchell v. Hawley, 83 U.S. 544 (1872) and American Cotton-Tie Co. v. Simmons, 106 U.S. 89 (1882) (sold articles leave the monopoly; reconstruction as second creation); Straus v. Victor Talking Machine, 243 U.S. 490 (1917) (restraints on alienation); Dickerson v. Matheson, 57 F. 524 (2d Cir. 1893) (express reservation on foreign sale, rejected as a basis in Impression); Intel Corp. v. ULSI Sys., 995 F.2d 1566 (Fed. Cir. 1993) and United States v. Masonite, 316 U.S. 265 (1942) (authorized sale exhausts); General Talking Pictures v. Western Elec., 304 U.S. 175 (1938) (licensee field limits).

---

# Edge-case playbook (FTO-focused)

Each pattern: the trap, the correct analysis, the controlling case(s).

1. **"We're a university (or hospital, or nonprofit lab), so research use is exempt."** Trap: there is a general research exemption. Analysis: the common-law defense covers only amusement, idle curiosity, or strictly philosophical inquiry. Research that serves an institution's mission, including grants, teaching, and prestige, is its legitimate business, and non-profit status does not matter. Controlling: Madey v. Duke; Embrex; Roche v. Bolar.

2. **"It's only internal testing and benchmarking; we're not selling it."** Trap: no sale means no infringement. Analysis: making or using a patented invention is itself infringement. Testing with a commercial purpose is not exempt. The exits are a license, buying authorized units (exhaustion covers the units bought), the FDA safe harbor if it truly applies, or a design-around. Controlling: Roche v. Bolar; Madey; Impression Products (exhaustion covers purchased units).

3. **"The patentee has known about our product for eight years and never sued."** Trap: laches or the passage of time protects the user. Analysis: laches cannot bar damages for infringement within six years before suit. Delay alone also does not create estoppel. Equitable estoppel needs (a) misleading communication or conduct (typically a threat followed by long silence), (b) the user's reliance, and (c) material prejudice. A reply that minimized the user's use weakens estoppel if use later grew. Estoppel attaches to the claims at issue. Claims materially changed in a later reexamination reset the analysis (John Bean v. Morris, 2018). Reliance must be proven, not assumed (Fraunhofer v. Sirius XM, 2025). Controlling: SCA Hygiene; Aukerman.

4. **The user bought patented goods abroad from the patentee's own distributor and imports them.** Trap: foreign sales do not exhaust US rights. Analysis: an authorized sale anywhere exhausts US patent rights in those units. The rule differs if the foreign maker had no authority from the US patentee, or if a licensee sold outside its license. Controlling: Impression Products; Boesch v. Graff; Jazz Photo (territorial holding abrogated).

5. **The product says "single use only" or carries a no-resale contract.** Trap: reuse or resale infringes. Analysis: after an authorized sale, post-sale restrictions are enforceable only as contracts between the parties to them, never through a patent suit. Refurbishment still has to stay on the repair side of the line. Controlling: Impression Products (abrogating Mallinckrodt); Jazz Photo; Hewlett-Packard v. Repeat-O-Type.

6. **A licensee sold to the user outside its licensed field.** Trap: any sale by a licensee exhausts. Analysis: a sale outside the license's scope is unauthorized and exhausts nothing. The patentee can enforce against downstream users, especially those who know of the limit. Ask for the license scope. Controlling: Impression Products (license versus sale; discussing General Talking Pictures).

7. **The refurbisher replaces the worn part that embodies the "novel feature."** Trap: replacing the inventive part is always reconstruction. Analysis: the test is whether a new article is made after the whole is spent, not whether the replaced part is the novel one. Replaceable, shorter-lived, unpatented parts point to repair. A part never designed or sold as a replacement, with no shorter expected life (the Sandvik drill tip), points to reconstruction. Replacing a component that is separately patented needs its own authority. Controlling: Aro I; Jazz Photo; Sandvik.

8. **Self-replicating products (seeds, cell lines, software copies).** Trap: buying one exhausts rights in the copies it produces. Analysis: exhaustion covers the item sold, not new copies made from it. Controlling: Bowman v. Monsanto, 569 U.S. 278 (2013); Impression Products (exhaustion attaches to "that item").

9. **The user buys an authorized component (chip, module) and builds it into its system.** Trap: the system patent is untouched by the component sale. Analysis: an authorized sale of a component that substantially embodies the patented system or method exhausts those claims for that unit. Confirm the seller's license actually authorized the sale. Controlling: Quanta v. LG; Univis.

10. **The user ran the process secretly for years before the patentee filed.** Trap: the user's earlier invention invalidates the patent, or gives a free license everywhere. Analysis: secret use by another is generally not prior art against the patentee. The § 273 prior-commercial-use defense may apply instead. It is personal, site-limited, needs clear and convincing evidence, and is unavailable against university-owned patents. A defendant who pleads it without a reasonable basis faces a mandatory exceptional-case finding. Controlling: W.L. Gore v. Garlock; 35 U.S.C. § 273 (§ 9).

11. **An employee or consultant invented on company time, patented it, and now demands royalties from the company.** Trap: the patent owner can exclude the company. Analysis: a shop right may give the company a free, non-exclusive right to keep using the invention in its own business, including having outside contractors build it. The right is not transferable to a buyer of the company's other lines and cannot be licensed out. Controlling: McElmurry; Dubilier.

12. **The user (or its founder) assigned the patent and now wants to challenge validity.** Trap: assignors can never challenge validity, or can always do so. Analysis: assignor estoppel survives in court but applies only when the invalidity claim contradicts a representation made in the assignment. Exceptions include an assignment of future inventions made before specific claims existed, and materially broader claims obtained later. Assignor estoppel does not apply at the PTAB in IPR. Controlling: Minerva Surgical v. Hologic; Hologic v. Minerva (2022 remand); Arista v. Cisco (§ 10).

13. **The patentee forces customers to buy unpatented supplies.** Trap: misuse automatically voids the patent or gives a damages claim. Analysis: misuse is an unenforceability defense that lasts until the misuse is purged, not a tort. Under § 271(d)(5), tying is misuse only if the patentee has market power in the patented product's market. Other aggressive licensing needs antitrust-style proof of anticompetitive effect. The § 271(d) safe harbors do not protect tying a product that has substantial noninfringing uses, and that conduct can also support antitrust liability (Ingevity v. BASF, 2026). Controlling: Morton Salt; USM v. SPS; Princo; 35 U.S.C. § 271(d) (see Post-casebook).

14. **The license keeps charging royalties after the last patent expires.** Trap: the contract term controls. Analysis: royalties for using the invention after the last-to-expire patent are unenforceable per se. Hybrid licenses can allocate value to non-patent rights. Controlling: Brulotte; Kimble v. Marvel, 576 U.S. 446 (2015).

15. **The user holds a license or covenant under the parent patent; the patentee sues on a continuation.** Trap: the continuation is a new patent outside the license. Analysis: absent clear contrary intent, a license to a parent can extend to continuations with the same disclosure. A covenant not to sue can authorize sales and so exhaust. Read the license's definitions and patent schedule. Controlling: General Protecht; TransCore (§ 11).

16. **A co-owner of the patent licensed the user, and the other co-owner sues.** Trap: the suing co-owner's rights are intact. Analysis: absent a contrary agreement, each co-owner may make, use, sell, and license without the others' consent. All co-owners generally must join an infringement suit as plaintiffs, and a co-owner cannot be joined involuntarily. A license from one co-owner bars future claims, but a retroactive license does not release damages that already accrued to the other co-owner. A co-inventor of even one claim is presumptively a co-owner of the whole patent. Controlling: 35 U.S.C. § 262; Ethicon, Inc. v. United States Surgical Corp., 135 F.3d 1456 (Fed. Cir. 1998); STC.UNM v. Intel Corp., 754 F.3d 940 (Fed. Cir. 2014).

17. **The user makes the accused product for a US government contract.** Trap: no defense, or the contractor is immune for everything it makes. Analysis: under 28 U.S.C. § 1498 the patentee's remedy for use or manufacture "by or for the United States" with the government's authorization or consent is against the US in the Court of Federal Claims. Commercial sales outside the contract are not covered. Controlling: 28 U.S.C. § 1498; Sevenson; IRIS v. JAL (§ 12).

18. **Generic or biosimilar development: validation batches, clinical supply, and commercial stockpiling.** Trap: everything before approval is safe-harbored. Analysis: § 271(e)(1) protects uses reasonably related to generating information for FDA submission, including preclinical work that may never be submitted. It does not protect building launch inventory or other commercial uses. Analysis runs activity by activity. Acts aimed at recruiting clinical investigators can qualify even when other motives exist (Edwards v. Meril). Courts may not enjoin safe-harbored trials (Jazz v. Avadel). Controlling: Merck v. Integra; Amgen v. Hospira; Edwards v. Meril (§ 2).

19. **The patent issued decades after its priority date through serial continuations.** Trap: nothing to do but license. Analysis: prosecution laches can make a patent unenforceable after unreasonable, unexplained delay in prosecution that prejudices others. The defense is narrow and fact-heavy. The defense needs proof of prejudice caused by the delay; it failed for lack of prejudice in Google v. Sonos (2025, nonprecedential). Controlling: Hyatt v. Hirshfeld; Personalized Media v. Apple (§ 5).

20. **The patentee's own misconduct in the dispute (e.g., misusing a competitor's confidential information to draft claims).** Trap: the misconduct is irrelevant to enforcement. Analysis: unclean hands can bar enforcement against the party harmed by the misconduct. Controlling: Gilead v. Merck (§ 12).

---

# Post-casebook developments (verified 2026-11-18)

Main digests for the safe harbor, prosecution laches, assignor estoppel, licenses, § 1498, and unclean hands appear in §§ 2, 5, 10, 11, and 12 above. This section lists post-edition decisions and statute points not already digested, in compact form.

### Princo Corp. v. ITC, 616 F.3d 1318 (Fed. Cir. 2010) (en banc) (pre-edition; not excerpted)
- **Rule:** Misuse is narrow. The patentee must have "impermissibly broadened the physical or temporal scope of the patent grant" with anticompetitive effect. An agreement between patent holders not to license a competing technology was not misuse of the asserted patents.
- **Skill rule:** FTO: raise misuse only when the patentee leverages the asserted patent itself beyond its scope (ties, post-expiration royalties, coerced package terms); route other anticompetitive conduct to antitrust counsel.

### Kimble v. Marvel Entertainment, LLC, 576 U.S. 446 (2015)
- **Rule:** Brulotte retained on stare decisis grounds: "a patent holder cannot charge royalties for the use of his invention after its patent term has expired." Parties can defer payments for pre-expiration use, tie royalties to non-patent rights, or use non-royalty business arrangements.
- **Skill rule:** Portfolio / licensing: check every running-royalty license for a step-down at expiry of the last listed patent.

### 35 U.S.C. § 271(d)(4)–(5) (Patent Misuse Reform Act of 1988; text verified)
- **Rule:** It is not misuse to have "refused to license or use any rights to the patent." Conditioning a license or sale on acquiring another patent right or a separate product is not misuse "unless, in view of the circumstances, the patent owner has market power in the relevant market for the patent or patented product."
- **Skill rule:** FTO: a refusal to license is never a defense; a tie is a misuse candidate only with evidence of market power.

### Ingevity Corp. v. BASF Corp., No. 2024-1577 (Fed. Cir. Feb. 11, 2026)
- **Rule:** A patentee could not invoke § 271(d) to escape an antitrust tying verdict when the tied product was a staple with substantial noninfringing uses. § 271(d) shields only conduct aimed at contributory infringement as defined in § 271(c). The jury's unlawful-tying finding was affirmed.
- **Skill rule:** Licensing review: when a patentee conditions access to a patented product on buying an unpatented staple, flag both misuse and antitrust exposure; § 271(d) does not protect it.

### Bowman v. Monsanto Co., 569 U.S. 278 (2013) (pre-edition; not excerpted)
- **Rule:** "The exhaustion doctrine does not enable Bowman to make additional patented soybeans without Monsanto's permission." Planting purchased patented seed to grow new seed is making new copies.
- **Skill rule:** FTO for biological materials, cell lines, and replicable technologies: exhaustion covers the units bought, never their progeny or copies.

### Quanta Computer, Inc. v. LG Electronics, Inc., 553 U.S. 617 (2008) (pre-edition; quoted in Impression)
- **Rule:** "The exhaustion doctrine applies to method patents," and an authorized sale of components that substantially embody the patents (their only reasonable use practices the patent and they contain its essential inventive features) exhausts them.
- **Skill rule:** See § 7 note.

### Fraunhofer-Gesellschaft v. Sirius XM Radio Inc., No. 2023-2267 (Fed. Cir. June 9, 2025) (precedential)
- **Rule:** Applies Aukerman's three equitable-estoppel elements after SCA Hygiene. It reversed a summary judgment of estoppel because the accused infringer had not shown reliance on the patentee's conduct. (Reporter cite 138 F.4th 1373 reported by secondary sources; not verified.)
- **Skill rule:** FTO: record evidence that the user's decisions were made because of the patentee's conduct (board minutes, emails), not merely after it.

### John Bean Technologies Corp. v. Morris & Associates, Inc., 887 F.3d 1322 (Fed. Cir. 2018)
- **Rule:** Equitable estoppel based on the patentee's conduct before an ex parte reexamination could not bar claims that were substantively amended or added in the reexamination. The patentee sought damages only after the certificate issued.
- **Skill rule:** Portfolio / FTO: when a patent emerged from reexamination or reissue with new or amended claims, re-run estoppel and intervening-rights analysis for those claims separately.

### Hyatt v. Stewart, 148 F.4th 1376 (Fed. Cir. Aug. 29, 2025), cert. denied sub nom. Hyatt v. Squires, No. 25-1049 (June 29, 2026); Google LLC v. Sonos, Inc., No. 2024-1097 (Fed. Cir. Aug. 28, 2025) (nonprecedential)
- **Rule:** Prosecution laches was affirmed against Hyatt's decades-long applications; arguments based on Petrella and SCA Hygiene were barred as law of the case. In Sonos, a prosecution-laches judgment was reversed for lack of prejudice attributable to the delay.
- **Skill rule:** FTO: for very late-issuing continuations, document what the user built or invested during the prosecution delay; without prejudice, prosecution laches fails.

### Edwards v. Meril cert denial and Jazz v. Avadel (2025)
- Digested in § 2. No Supreme Court merits decision on the safe harbor since Merck (2005).

### Search result for January 2023 to November 2026
No Supreme Court merits decision was found on exhaustion, the safe harbor, misuse, laches, equitable estoppel, § 273, assignor estoppel, implied license, or § 1498. Precedential Federal Circuit decisions found in the window: Personalized Media v. Apple (2023), Edwards v. Meril (2024), Jazz v. Avadel (2025), Fraunhofer v. Sirius XM (2025), Hyatt v. Stewart (2025), and Ingevity v. BASF (2026). None was found construing the AIA version of § 273. Arbutus v. Moderna (D. Del.) settled in March 2026 except for one § 1498 question: whether § 1498 bars claims for doses sold to the government under a particular contract that did not go directly to government employees. Moderna's appeal on that question was argued at the Federal Circuit on Nov. 5, 2026 and was undecided as of 2026-11-18 (Arbutus Form 10-Q, Nov. 10, 2026, a party filing; no decision posted on the court's site). Arlton v. AeroVironment (Feb. 4, 2026), a § 1498 decision, is nonprecedential.

---

# Checklist for the skill (defenses)

- Ask about history with each listed patentee before ranking risk: prior letters, license offers, silence periods, the user's replies, and what the user invested afterward (equitable estoppel).
- Never discount a patent because of the patentee's delay alone (SCA Hygiene). Never cite Aukerman's laches presumption.
- For research, testing, or nonprofit use, say plainly that the common-law experimental-use defense is almost never available (Madey).
- For FDA-regulated products, split activities into (a) development and submission data and (b) commercial manufacture, inventory, marketing, and launch. Only (a) can be safe-harbored, and the analysis runs activity by activity.
- Trace provenance for every purchased, resold, imported, or refurbished unit: who first sold it, where, and under what authority (patentee, licensee within scope, licensee outside scope, unlicensed maker).
- Treat post-sale restrictions (single use, no resale, no export) as contract issues only after an authorized sale (Impression Products).
- For refurbishment, list each step and each replaced part. Classify repair versus reconstruction risk. Require per-unit process records (Jazz Photo).
- For secret prior commercial use, collect dated evidence of the earliest US commercial use, its site, and the business unit. Compare against the patent's effective filing date and the patentee's earliest public disclosure. Check whether the patent is university-owned (§ 273).
- For employee- or contractor-made inventions used by the company, collect agreements, funding records, and the inventor's consent statements (shop right).
- For assignors, ask what was represented in the assignment, whether claims were broadened after assignment, and whether the forum is court or PTAB (Minerva; Arista).
- For licenses and covenants, read field-of-use limits, patent schedules, continuation language, term, and post-expiration royalty terms (Brulotte/Kimble; General Protecht; TransCore).
- For government work, check whether the use is "by or for the United States" with authorization or consent (§ 1498).
- Present every defense as "available on these facts, needs this evidence, burden on the user." Never write "the defense applies" or "clear to proceed."

---

## Verification sources (defenses)
- Merck v. Integra: https://www.law.cornell.edu/supct/html/03-1237.ZO.html
- SCA Hygiene: https://www.supremecourt.gov/opinions/16pdf/15-927_6j37.pdf
- Impression Products: https://www.supremecourt.gov/opinions/16pdf/15-1189_ebfj.pdf
- Quanta: https://www.law.cornell.edu/supct/html/06-937.ZO.html ; Bowman: https://www.law.cornell.edu/supremecourt/text/11-796 ; Kimble: https://www.law.cornell.edu/supremecourt/text/13-720
- Minerva v. Hologic: https://www.supremecourt.gov/opinions/20pdf/594us2r64_anbf.pdf ; Hologic v. Minerva (2022): https://www.cafc.uscourts.gov/opinions-orders/19-2054.OPINION.8-11-2022_1990706.pdf
- 35 U.S.C. § 271: https://www.law.cornell.edu/uscode/text/35/271 ; § 273: https://www.law.cornell.edu/uscode/text/35/273
- Federal Circuit opinions (prefix https://www.cafc.uscourts.gov/opinions-orders/): Classen 06-1634-1649.pdf; Momenta 12-1062.pdf; Proveris 07-1428.pdf; Amgen v. Hospira 19-1067.opinion.12-16-2019.pdf; Edwards v. Meril 22-1877.OPINION.3-25-2024_2290338.pdf; Fuji v. ITC 04-1618.pdf; General Protecht 11-1115.pdf; TransCore 08-1430.pdf; Sevenson 06-1391.pdf; IRIS v. JAL 10-1051.opinion.10-17-2014.1.pdf; Gilead v. Merck 16-2302.opinion.4-24-2018.1.pdf; Hyatt v. Hirshfeld 18-2390.opinion.6-1-2021_1784662.pdf; PMC v. Apple 21-2275.OPINION.1-20-2023_2066571.pdf; Google v. Sonos 24-1097.OPINION.8-28-2025_2565220.pdf; Fraunhofer v. Sirius XM 23-2267.OPINION.6-9-2025_2527152.pdf; Jazz v. Avadel 24-2274.OPINION.5-6-2025_2509887.pdf; Hyatt v. Stewart 18-2390.OPINION.8-29-2025_2565719.pdf; Ingevity v. BASF 24-1577.OPINION.2-11-2026_2646300.pdf; Arlton v. AeroVironment 21-2049.OPINION.2-4-2026_2642932.pdf
- Harvard Caselaw Access Project (https://static.case.law/): Embrex f3d/216/cases/1343-01.json; Madey f3d/307/cases/1351-01.json; Princo f3d/616/cases/1318-01.json; Aukerman f2d/960/cases/1020-01.json; Wang f3d/103/cases/1571-01.json; Met-Coil f2d/803/cases/0684-01.json; McElmurry f2d/995/cases/1576-01.json
- Dockets: Edwards v. Meril cert. denied https://www.supremecourt.gov/docket/docketfiles/html/public/24-428.html ; Hyatt v. Squires https://www.supremecourt.gov/docket/docketfiles/html/public/25-1049.html (brief in opposition gives 148 F.4th 1376); Madey cert. denied https://www.supremecourt.gov/orders/journal/jnl02.pdf
- Arbutus v. Moderna status: https://www.sec.gov/Archives/edgar/data/1447028/000144702826000064/abus-20260930.htm
- Ethicon v. U.S. Surgical: https://law.justia.com/cases/federal/appellate-courts/F3/135/1456/507580/
- Madey cert denial, 539 U.S. 958: https://static.case.law/us/539/CasesMetadata.json (Duke University v. Madey, 2003-06-27)
- Not verified this session: reporter cites for Fraunhofer (138 F.4th 1373), Jazz v. Avadel (136 F.4th 1075), and Hologic v. Minerva (2022); later citing history of McElmurry.
