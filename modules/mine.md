# Tool: find patentable inventions in code or documents

For teams that don't know what's worth patenting. Input: a repository, design docs, research notes, or a product spec. Output: a ranked list of candidate inventions, each ready for Phase 1.

## Confidentiality
This reads private material. Work locally. Send nothing to search engines during mining. Searching starts only in Phase 1, per candidate, with the user's approval and abstracted queries.

## Steps
1. **Scope.** Ask what to read (folders, docs) and what to skip (vendored code, generated files). Ask about anything already released publicly. Open-source releases, published papers, and public demos are disclosures that start the clock (see `references/bars-and-eligibility.md`).
2. **Scan for technical distinctiveness**, not size. Look for:
   - a non-obvious algorithm or data structure;
   - an unusual combination of known parts that produces a measurable gain (speed, memory, accuracy, power, cost, safety);
   - a workaround for a known hard limit;
   - hardware–software interplay;
   - a new protocol or file format;
   - a training or data pipeline trick with a measurable effect;
   - a user-interaction mechanism with a technical effect.
   Skip routine glue, CRUD, and configuration.
3. **For each candidate** write: a one-line title; the problem; the mechanism (where in the code or doc, with file paths); the measurable effect claimed (and whether there's evidence such as benchmarks or tests); detectability (could a competitor's use be seen from outside?); disclosure status (public repo? released? published?); the 101 risk (`references/eligibility-101.md`); and trade-secret suitability.
4. **Rank** by commercial value × technical distinctiveness × detectability, with bar urgency first: anything already disclosed less than 12 months ago goes to the top, with its last safe filing day.
5. **Report** to `patent/reports/candidates.md`. Bottom line: the top three, and why.

## Gate
"Run the quick knockout check on candidate #1 (or pick another)? Each check creates its own matter folder." Record the pick with `state.py decide --gate mine --choice "…"`. For each pick, run `state.py init --title …` in a subfolder (`patent-<slug>/`) and start Phase 1 with the candidate's notes as the disclosure.
