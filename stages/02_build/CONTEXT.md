# Stage 02_build — contract (Layer 2)

Rules are in `AGENTS.md` and `CLAUDE.md`; this file only routes.

## Purpose

Grey box to the gate builds: levels, assets and the core loop, one lead agent calling Unreal MCP.

## Inputs

- `output/gdd.md` from `stages/01_concept/output/`
- `stages/02_build/references/` (asset-chain, layout-spec/, look-kit/, procedural-props, character-rig/, editor-mcp-helper, force-save-level, step-shot)
- `_config/reference/canon/jam-grey-box-first.md`, `jam-asset-pipeline.md`, `jam-mcp-tool-traps.md`
- `PLAN.md` Phase 1 gate table

## Process

1. Read the GDD and the layout-spec README; write a layout JSON and check it (`scripts/layout_spec.py check`).
2. Build grey box with `scripts/ue_build_level.py`; verify with `ue_verify_level.py`.
3. Generate and import assets through `scripts/gen_asset.py` and `ue_import_asset.py` (licensed models only); logs append to `output/*-log.csv`.
4. Run `scripts/force_save_level.py` before every package step; credits gather into `output/credits.md`.

## Outputs

`output/asset-pipeline-log.csv`, `output/audio-pipeline-log.csv`, `output/sourced-assets*.csv`, `output/credits.md`, `output/asset-test-<engine>-YYYY-MM-DD.md`

## Routing

Next: `stages/03_playtest/CONTEXT.md` after each build. On failure (editor hang or crash): copy logs to `stages/04_ship/output/crash-logs/<stamp>/`, restart, resume (`AGENTS.md` Editor recovery).
