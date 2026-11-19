# Tool: office-action response

This tool covers nonfinal and final rejections, restriction and election requirements, and notices of non-compliant amendment. It delivers a complete inventory, a strategy the user approves, then a reply in 37 CFR 1.111 / 1.121 form. Nothing is filed by you.

Law and format rules: `references/prosecution.md`. Deadlines: `references/deadlines.md`.

## Step 0: get the documents (no silent supplement)

You need the office action itself (PDF or text), the claims as currently pending, the specification as filed, and every reference the examiner cites.
- **Office action:** ask for it. Use `pdftotext -layout oa.pdf patent/prosecution/oa-YYYY-MM-DD/oa.txt`. With `USPTO_ODP_API_KEY`, the file wrapper documents can be listed and downloaded (`references/sources-and-apis.md`).
- **Pending claims and spec:** from `patent/draft/`, the user, or the published application (`patent_fetch.py`). Confirm the claims are the latest version, since amendments since publication change everything.
- **Cited references:** fetch each by number with `patent_fetch.py`. For NPL the examiner cites, ask the user for the copy if it can't be fetched.

## Step 1: deadline first

`python3 scripts/deadlines.py oa --mailed YYYY-MM-DD --type nonfinal|final|restriction`. It prints the shortened statutory period, the last day without fees, each extension month with its fee (from `references/fees.md`), and the absolute 6-month limit, all rolled for weekends and federal holidays. Final rejections also show the 2-month date that matters for an advisory action. Put the dates in a banner.

## Step 2: inventory (deterministic + read)

`python3 scripts/oa_parse.py patent/prosecution/oa-…/oa.txt --out patent/prosecution/oa-…/inventory.json`. It finds every rejection (statute, claims, references), objection, restriction group, and the examiner's stated claim interpretation. Read the action yourself and correct the inventory: the parser is a first pass.

For each rejection, chart the examiner's mapping. Do this per claim element: the reference passage the examiner cites, whether the quoted text is actually in that reference (check with `quote_check.py` against the cached reference), and your read of the gap.

Treat an element as properly rejected only if the examiner's cited passage, as fetched, actually shows it. Each element falls into one of these:
- **Uncharted:** the examiner names no passage.
- **Mischaracterized:** the passage doesn't say it.
- **Assumed:** the element rests on official notice or inherency without evidence.

Each of these is an argument target.

For 103, also record the stated reason to combine and test it: does the combination change the primary reference's principle of operation or make it unfit for its purpose, is there teaching away, is the rationale conclusory? 101: map the examiner's step analysis against the current guidance in `references/eligibility-101.md`. 112: identify the exact term or gap.

## Step 3: strategy (gate)

Load the case files for each statute rejected (`references/case-law/README.md`) plus `case-law/prosecution.md` (new matter, double patenting, candor) and run their edge-case playbooks before proposing a strategy.

For each rejection, propose one or more of: **argue** (traverse), **amend** (narrow with a fallback from the dependents or the spec), **cancel**, or **interview first**. Give the trade-offs in a table:
- **Estoppel cost.** Narrowing amendments and argued distinctions limit later equivalents and claim scope (Festo, prosecution disclaimer). Prefer the narrowest amendment that wins, and arguments tied to specific claim words over broad statements about "the invention."
- **Amendment support.** Each proposed claim feature needs a spec cite. `python3 scripts/oa_check.py newmatter --claims amended.md --spec spec.md` lists every added word not found in the as-filed spec. New matter is barred (35 USC 132).
- **Interview.** Recommend one when the action shows a misunderstanding or a claim-interpretation disagreement. Give the Automated Interview Request steps and draft a short agenda.
- **After final.** Options: amend under 37 CFR 1.116 (limited), RCE (1.114), appeal (notice + pre-appeal brief request), or a continuation. Check the reference for which programs are still running.
- **Restriction.** Elect the group that best covers the product. Traverse only with a real argument, and note that you can file a divisional later. The election goes with the reply.

Also flag:
- Double patenting: a terminal disclaimer has consequences for enforceability and term.
- An IDS for newly found art, with its timing.
- Claim fee changes caused by adding claims (`fees.py`).

**🔒 Gate:** the user picks a strategy per rejection. Record it with `state.py decide --gate oa-strategy`.

## Step 4: draft the reply

Write `response.md` following `templates/oa-response.md`:
1. Introductory comments, with the identification of the application and the date of the action.
2. **Amendments to the claims:** a complete listing of every claim, each with its status identifier: (Original), (Currently Amended), (Canceled), (Withdrawn), (Previously Presented), (New), or (Not Entered). Currently amended claims show added text underlined (`<u>added</u>`) and deleted text struck through (`~~deleted~~`). Use double brackets (`[[abc]]`) for deletions of five or fewer characters, or where strikethrough is hard to see (37 CFR 1.121(c)).
3. Amendments to the specification, if any: replacement paragraphs with markup.
4. **Remarks:** status of the claims; then each rejection in the action's order. Each one gets the examiner's position in one sentence, the response (amendment basis with spec pinpoints, the element-by-element distinction quoting the reference), and the legal standard with a cite. No broad characterizations of the invention; argue the claim words. Close with a request for allowance or an interview.
5. **Checks:** `python3 scripts/oa_check.py all --inventory inventory.json --response response.md --spec spec.md`. It fails if any rejection, objection, or claim in the inventory has no response. It also checks claim status identifiers and markup format against 1.121, flags new matter, and confirms the claim listing is complete and consecutive. Then run `check_claims.py` on the clean version of the amended claims.

**🔒 Gate** (`decide --gate oa-final`): the final review. List the open items: signatures, fees, extension petition, IDS, and an RCE transmittal if needed. Export with `build_docx.py`/`md_to_docx.py`. The registered practitioner (or pro se applicant) signs and files.

## Output summary in chat

The deadline banner, then one line per rejection with the recommended strategy, then the gate question.
