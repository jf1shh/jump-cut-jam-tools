---
tier: tested
source: stages/00_prep/output/mock-jam-findings-13.md
updated: 2026-11-10
---

# Wayland: automation cannot press keys in PIE, so a human must test real input

Seen once (mock jam 13, native Wayland editor, n=1).

## Trap: a passing automated loop does not prove WASD or R work
- **Why:** `xdotool` exists but finds no X window for the editor (it is Wayland native), so no key can be injected
  into PIE. Mock 13 drove every proof (win, lose, restart) with an in-game test bot (instance-editable variable
  `Auto`: 1 collects oil, 2 walks into fog). Real WASD and R input stayed UNPROVEN.
- **What to do:** label real key input as unproven in the findings, and have a human press the keys (move, restart)
  before calling the loop done. Packaged-build real-input tests on the Legion are the other route (mock 12).
- **Related:** on-screen PrintString text never showed in `CaptureEditorImage`, so show state by pawn size or
  colour as well, and prove the text from log lines.

## Tip: under the X11 SDL driver `xdotool` does inject keys, but unreliably
- **Why:** the claim above was true for the native Wayland editor. With `SDL_VIDEODRIVER=x11` (needed on 5.9), `xdotool` into the `-game` window sent keys, but SPACE and R arrived late or were lost across six runs, so a FAIL may be the input path and a PASS may not hold on the target (`mock-jam-findings-15.md:45,192-195`). *Superseded (2026-11-10):* "no key can be injected into PIE" for the X11 driver.
- **How to check:** use the `xdotool` probe as a smoke test only. Prove real keys on the packaged Windows build early, right after the grey-box gate.

## Tip: mock 15's SPACE bug was not reproduced on Windows, so most likely the Linux input path
- **Why:** mock 16 (a different game, same key-reading: `IsInputKeyDown` every Tick) did NOT reproduce it with real Windows key input in the packaged build: SPACE lifted the magnet, SPACE+D held together won, R restarted. Source: `stages/00_prep/output/mock-jam-16-findings.md` (2026-11-10; branch `mock16-findings` merged to master 2026-11-11).
- **How to check:** judge keys only on the packaged Windows build with real OS input; treat `xdotool` FAILs on Linux as unproven, not as game bugs.
