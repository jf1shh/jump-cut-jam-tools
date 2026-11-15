---
tier: tested
source: stages/03_playtest/references/agent-playtest.md
updated: 2026-11-10
---

# Agent playtest of the packaged build on the Legion

## Tip: an agent plays it like a human before the owner sees it
- **Why:** the blind key script in `visual_playtest.py` never watered a plant in mock jam 10, so the win was
  never seen. `scripts/agent_playtest_cli.py` closes the loop: look at a real frame, decide, act, look again,
  with real OS input and real screen capture on the Legion.
- **How to check:** `start`, then `look` / `press` / `mouse` / `clip`. Each `press` and `mouse` ends with a
  screenshot path; Read it before the next command. The tester plays blind to the source: only what the game
  shows on screen. If the screen does not say how to win, that is a Clarity finding.

## Tip: the gate needs win, lose and restart, each with its own evidence
- **Why:** `gate --report FILE` prints `GATE PASS` only if the journal shows at least 5 input commands, and a
  `mark` for each of win, lose and restart. Each mark needs evidence files captured in this session after the
  first real input (a title frame is not play), captured before the mark, with its own file for each milestone,
  and the restart evidence captured after the lose evidence. The report needs every section, `Fun score: N/5`,
  `Clarity score: N/5`, and no `TODO` or `<fill` left.
- **How to check:** the latest usable mark per milestone counts, so a wrong mark is fixed by marking again. The
  gate cannot prove a frame really shows a win; the hub opens the evidence frames and reads the report.

## Tip: a clip counts only if the game is alive and in front at both ends
- **Why:** OBS records the whole display. If OBS or a dialog is in front, the clip shows that, not the game.
  `clip` checks that the game is running and the front window both before and after the take, and the video must
  pass its black/flat check. A frame counts only if the game was in front when it was taken.
- **How to check:** a clip problem is printed and `clip` exits 1. Send a harmless key with `press` to bring the
  game forward, then clip again. A `press` or `mouse` that leaves the game out of front blocks the gate for the
  rest of that run.

## Tip: relaunches are journaled before the launch, and cannot stand in for a restart
- **Why:** a slow launch can raise "not running" and still come up seconds later. `start` writes the
  `relaunch` (or `start`) line to the journal first, then launches, so a game that comes up late is still on
  record. A relaunch keeps the history and numbering, and clears old out-of-front inputs from blocking the gate.
- **How to check:** a `relaunch` between the lose evidence and the restart evidence fails the gate: restart has
  to happen inside the game. `start --fresh` archives the old history; a different build needs a new session
  folder. Tests are fake-backed (`tests/test_agent_playtest_cli.py` and the `r2`/`r3` files); the real Legion
  run is still the hub's first check (`stages/03_playtest/references/agent-playtest.md`).

## Tip: a PIE or bot win proves nothing about the package
- **Why:** mock 10's PIE log showed a win in 8 s while the packaged autopilot ran out of water (`mock-jam-findings-10.md:64,83`). Mocks 13 and 15 proved their loops by bot only; the real-key SPACE bug in mock 15 stayed hidden until late (`mock-jam-findings-15.md:181-183,192-195`; `mock-jam-findings-13.md:22-26`).
- **How to check:** after the grey-box gate, make one real-key run on the packaged Legion build. Label bot proof UNPROVEN until then.

## Tip: play every win and lose rule once
- **Why:** mock 12 never played lose-by-low-mass, so a win check that may never fire stayed a suspicion (`mock-jam-findings-12.md:33`).
- **How to check:** the playtest checklist lists each lose path; each one is played, not only one lose.

## Tip: do not tune phase-dependent difficulty with a blind key script
- **Why:** mock 11's offline plan won in simulation, but the packaged wind phase differed and every run ended at 4 of 5 ribbons (`mock-jam-findings-11.md:129-133`).
- **How to check:** use the look-decide-act `agent_playtest_cli`, or ship the proven values.

## Tip: what a mock judge rewarded (n=1)
- **Why:** mock 12's frames-only judge gave 19/35, then 20/35 after 40 minutes of work. Only Visuals moved (2 to 3), from a world-space candy-stripe material that took about 3 minutes. Fun and Level Design did not move; the judge wanted structure and mechanics, not polish (`mock-jam-findings-12.md:66,74,78-80`). Mock 11's tester found a corridor of primitives, no sound, and a mechanic nobody could see (`mock-jam-findings-11.md:58-67`).
- **How to check:** put one world-space material on all grey-box pieces early; decide at the Sat 10:00 fork whether Fun and Level Design need a new mechanic or layout.
