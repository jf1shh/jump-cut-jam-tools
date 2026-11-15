# Stage 05_devlog — contract (Layer 2)

Rules are in `AGENTS.md` and `CLAUDE.md`; this file only routes.

## Purpose

Glass Box dev log: honest dated entries on what was built, by whom (agent or owner) and with what evidence.

## Inputs

- `stages/05_devlog/output/builds.csv`, `evidence.md`, `decisions.md`
- `stages/05_devlog/references/ai-disclosure-draft.md`, `itch-devlog-template.md`
- `_config/reference/templates/dev-log-entry.md`
- `_config/voice.md`

## Process

1. Run `python3 scripts/evidence_index.py` to refresh `output/evidence.md`.
2. Run `scripts/gen_devlog.py` to draft today's entry from builds, evidence and decisions.
3. Edit the draft for voice (`_config/voice.md`); keep AI use stated plainly.
4. Append new decisions to `output/decisions.md`.

## Outputs

`output/YYYY-MM-DD.md` (entry), `output/builds.csv`, `output/evidence.md`, `output/decisions.md`

## Routing

End of pipeline; the owner posts. On failure (missing evidence): list the gap in the entry instead of inventing it.
