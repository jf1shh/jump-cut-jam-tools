# MegaJam — Layer 1 (where do I go?)

Rules are in `AGENTS.md` and `CLAUDE.md`. This file only routes; it does not restate or change them.

## Routing table

| Task | Go to | Load first |
|---|---|---|
| Find any doc or data file | `_config/CANON.md` | `grep -i "<topic>" _config/CANON.md` |
| Find code (symbols, call graph) | `graft` | `graft ask "<task>" --source` |
| Know today's step and gates | `PLAN.md` | `PLAN.md`, then `stages/00_prep/references/win-plan.md` for the why |
| Look up an Official Rule | `RULES.md` | rule number, then `_config/reference/knowledge-base.md` |
| Check jam readiness | `stages/00_prep/references/jam-readiness-2026-11-06.md` | `stages/00_prep/references/jam-day-runbook.md` |
| Run the jam day by day | `stages/00_prep/references/jam-day-runbook.md` | `PLAN.md` Phase 1 table, `AGENTS.md` autonomy section |
| Pick a concept | `stages/01_concept/CONTEXT.md` | `stages/01_concept/references/game-concept-shortlist.md` |
| Generate an asset or music | `scripts/gen_asset.py`, `scripts/gen_music.py` | `AGENTS.md` licensed-models rule, `gpu-preflight` |
| Import or build in Unreal | `scripts/ue_import_asset.py`, `ue_build_level.py`, `ue_verify_level.py` | `stages/02_build/CONTEXT.md`, `AGENTS.md` MCP-caller rule, `CLAUDE.md` naming |
| QA and playtest | `scripts/qa_harness.py`, `agent_playtest.py` | `stages/03_playtest/CONTEXT.md`, `_config/reference/templates/playtest-checklist.md` |
| Package for Windows / Legion | `scripts/package-and-push.ps1`, `scripts/legion_*` | `stages/04_ship/CONTEXT.md` |
| Write a dev log entry | `scripts/gen_devlog.py` | `stages/05_devlog/CONTEXT.md`, `_config/reference/templates/dev-log-entry.md` |
| Submission page, video | `PLAN.md` Phase 2 | `_config/reference/research/submission_page_and_video.md` |
| Past rehearsals and findings | `stages/00_prep/output/_index.md` | `_config/CANON.md` section on mock jams |
| UE 5.9 / 5.8.4 API questions | `_config/reference/engine-reference/unreal/` | `VERSION.md` first; engine switch in `AGENTS.md`, 5.9 how-to in `_config/reference/canon/jam-ue59-upgrade.md` |
| Change the contest guard | `scripts/hooks/contest_guard.py` | `tests/test_contest_guard.py` |
| Add or rename a doc | its stage `references/` or `output/`, or `_config/`; then `_config/CANON.md` | keep CANON in step |

## Session start

1. Read `AGENTS.md` and `CLAUDE.md`.
2. Read `~/Documents/Obsidian/Work Hub Clean/Workflows/Session sync.md` (global rule).
3. Check the date against `PLAN.md`: before 2026-11-12 00:00 ET, no gameplay, levels or art.
4. Read the newest `.handoff/*/HANDOFF.md` if one exists, and `stages/00_prep/references/jam-readiness-2026-11-06.md`.
5. Route the task with the table above. Search `_config/CANON.md` before guessing a path.

## Stages (physical; each folder has its own contract)

| Stage | Purpose | Contract | Outputs land in |
|---|---|---|---|
| 00 Prep (to Nov 11) | Tools, plans, rehearsals only | `stages/00_prep/CONTEXT.md` | `stages/00_prep/output/` |
| 01 Concept (Nov 12) | Theme to concept and GDD | `stages/01_concept/CONTEXT.md` | `stages/01_concept/output/` |
| 02 Build (Nov 12–15) | Grey box to gate builds | `stages/02_build/CONTEXT.md` | `stages/02_build/output/` |
| 03 Playtest | QA each build before it moves on | `stages/03_playtest/CONTEXT.md` | `stages/03_playtest/output/` |
| 04 Ship (by Nov 15 8:59 PM ET) | Package, video, backup; a human submits | `stages/04_ship/CONTEXT.md` | `stages/04_ship/output/` |
| 05 Devlog | Glass Box entries, nightly and at the end | `stages/05_devlog/CONTEXT.md` | `stages/05_devlog/output/` |

New documents go in the stage they serve or in `_config/`, never in a new top-level folder.

## Config

`_config/` (Layer 3): `conventions.md` re-exports `CLAUDE.md`, `glossary.md`, `voice.md`, `article-template.md`; shared reference is in `_config/reference/`. `RULES.md` stays canonical at the root.
