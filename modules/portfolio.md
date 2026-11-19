# Tool: deadlines, docket, portfolio

A working copy of the user's patent deadlines. The office record is always the truth. A deadline docketed wrong is worse than none, so every date is computed from events by `scripts/deadlines.py` and never typed in by hand.

Rules: `references/deadlines.md`. Fees: `references/fees.md`.

## Commands

- **One deadline:** `python3 scripts/deadlines.py <kind> --date YYYY-MM-DD [--options]`. Kinds include the bar clock, a provisional going to a nonprovisional or PCT, an office action response, final, restriction, issue fee, maintenance fee, PCT national phase, and appeal. It prints the date, the rule it comes from, extension or grace windows with fees, and the weekend or holiday roll that was applied.
- **Docket:** `python3 scripts/deadlines.py portfolio --dir patent` reads `portfolio.json` and recomputes every next deadline from the recorded events. It groups them: overdue but in grace, due within 30 days, due within 90 days, later, and missing data. Initialize from `state.json` after filing, from a spreadsheet the user gives (map the columns, show the mapping, confirm), or by hand.
- **Add an event:** office action mailed, reply filed, notice of allowance, issue, maintenance fee paid. Before recording any filing or payment as done, ask the user to confirm it with the filing receipt or Patent Center. Never mark something done on assumption.

## Audit (on request or when initializing)

Flag:
- Lapsed assets not marked abandoned or expired.
- Applications pending more than 4 years (check prosecution status).
- Patents expiring in the next 24 months (continuation, licensing, and product planning).
- Owner names that differ across assets, and assignments that may not be recorded.
- Entity status that may have changed: a license or assignment to a large entity ends small or micro status going forward. Tell the user to notify the USPTO before the next fee.
- Assets with missing data needed to compute deadlines.
- Provisionals within 3 months of their 12-month date with no nonprovisional or PCT on the docket.

## Weekly watcher (optional)

If the host supports scheduled tasks, offer a weekly run of the docket report. It posts items in grace or lapsed state immediately, sends a short all-clear when nothing is due (so silence never means a broken job), and repeats "verify against Patent Center before acting." It never files, pays, or edits the register.
