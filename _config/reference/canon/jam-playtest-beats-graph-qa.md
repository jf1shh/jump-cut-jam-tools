---
tier: tested
source: stages/00_prep/output/mock-jam-findings-5.md
updated: 2026-11-06
---

# What graph checks miss: lessons from the owner's playtests

## Tip: a clean graph read does not mean the game works
- **Why:** in mock jam 5, `read_graph_dsl` matched the spec exactly, yet the owner reported "controls dont work".
  Cause: the pawn's parent was a bare `Pawn`, which has no movement component, so `AddMovementInput` did
  nothing. Check possession too (does `DefaultPawnClass` point at it?).
- **How to check:** use a `Character` or `DefaultPawn`, or add a `FloatingPawnMovement`. Then play a build.

## Tip: playtest every packaged build, not only the last
- **Why:** the same owner playtest caught flat grey meshes that the log checks (`errorLines: 0`) did not.
- **How to check:** run the staged build on the Legion and play for two minutes.

## Tip: on-screen warnings may not be in the log
- **Why:** the SkyLight real-time-capture warning never reached the log file. A log grep passes while red text shows on screen.
- **How to check:** fix the condition behind the warning (add a `SkyAtmosphere`) and eyeball the next build.

## Tip: prefer Enhanced Input over polling keys
- **Why:** the broken pawn polled `IsInputKeyDown` each tick, which is a code smell and awkward for gamepads.
- **How to check:** `showdebug enhancedinput` at runtime.
