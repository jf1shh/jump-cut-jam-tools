# Stage 04_ship — contract (Layer 2)

Rules are in `AGENTS.md` and `CLAUDE.md`; this file only routes.

## Purpose

Package, capture, back up and submit-ready: Windows build, Legion ship, video, jam clock and recovery; a human submits.

## Inputs

- a PASS verdict from `stages/03_playtest/output/`
- `stages/04_ship/references/` (jam-clock, jam-recovery, legion-ship, capture-setup, diversion)
- `PLAN.md` Phase 2
- `_config/reference/canon/jam-packaging-windows.md`, `jam-legion-ship-preflight.md`, `jam-legion-capture-and-video-traps.md`

## Process

1. Check the clock: `python3 scripts/jam_clock.py status`; obey FORCE_PACKAGE (T-60) and FINAL (T-15).
2. Force-save, package Win64, ship to the Legion with `scripts/legion_ship.py` and `package-and-push.ps1`. Build config: the Windows zip keeps Development (D-009); any web build must be Shipping, not Development (kickoff stream, 2026-11-11).
3. Record and cut the video per `capture-setup.md`; write the itch page under `output/<name>-itch/`.
4. Back up with `scripts/jam_backup.sh nightly|gate <label>`; the owner submits.

## Outputs

`output/<name>-itch/description.md` and shots, `output/crash-logs/<stamp>/`, `output/<topic>-verification-YYYY-MM-DD.md`

## Routing

Next: `stages/05_devlog/CONTEXT.md` (nightly and at the end). On failure: `references/jam-recovery.md` triage ladder; if the package fails twice, ship the last PASS build.
