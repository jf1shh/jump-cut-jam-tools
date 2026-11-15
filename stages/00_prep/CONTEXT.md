# Stage 00_prep — contract (Layer 2)

Rules are in `AGENTS.md` and `CLAUDE.md`; this file only routes.

## Purpose

Prep (to Nov 11): tools, plans, rehearsals and audits finished before the window opens (Rule 7(h): no gameplay, levels or art).

## Inputs

- `PLAN.md` Phase 0
- `stages/00_prep/references/win-plan.md` (why), `jam-execution-plan.md` (hour by hour), `jam-day-runbook.md`
- `stages/00_prep/references/mock-jam-NN-brief.md` for the mock being run
- `_config/reference/canon/jam-top-lessons.md`

## Process

1. Read the brief and the runbook for the mock or audit; run it in the separate mock project (`~/Projects/megajam-mock`).
2. Bring back only findings and tooling fixes (no game content); write `output/mock-jam-findings-N.md`.
3. Fill the scorecard row: `python3 scripts/mock_scorecard.py --mock N ...`; update `references/mock-scorecard.md`.
4. Fix tools in `scripts/` with tests; add rows to `_config/CANON.md`.

## Outputs

`output/mock-jam-findings-N.md`, `output/mock-scorecard-N.json`, `output/mock-jam-NN-evidence/`, dated rehearsal and drill notes `output/<topic>-YYYY-MM-DD.md`

## Routing

Next: `stages/01_concept/CONTEXT.md` (at window open). On failure: record the gap in the findings file, fix the tool pre-jam, re-run the gate; never add game content to this repo.
