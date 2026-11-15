# Stage 03_playtest — contract (Layer 2)

Rules are in `AGENTS.md` and `CLAUDE.md`; this file only routes.

## Purpose

Check each build with agent playtest, judge pass and QA logs before it is packaged or fast-forwarded.

## Inputs

- the packaged or PIE build from `stages/02_build`
- `stages/03_playtest/references/` (agent-playtest, playtest-gate, judge-pass, vlm-judge-spike)
- `_config/reference/templates/playtest-checklist.md`
- `_config/reference/canon/jam-agent-playtest-gate.md`, `jam-playtest-beats-graph-qa.md`

## Process

1. Read `playtest-gate.md`; run `scripts/qa_harness.py` and `scripts/agent_playtest.py` on the build.
2. Capture screenshots to `output/qa-screenshots/`; append `output/qa-*-log.csv`.
3. Run `scripts/judge_pass.py` (and `vlm_judge.py` if enabled) against the Official Rules criteria.
4. Write the verdict and five playtest questions into `output/playtest-<N>.md`.

## Outputs

`output/qa-checks-log.csv`, `qa-pipeline-log.csv`, `qa-playtest-log.csv`, `output/qa-screenshots/`, `output/playtest-<N>/`

## Routing

Next: `stages/04_ship/CONTEXT.md` on PASS. On FAIL: back to `stages/02_build/CONTEXT.md` with the failing check and screenshot named; a gate build never ships on FAIL.
