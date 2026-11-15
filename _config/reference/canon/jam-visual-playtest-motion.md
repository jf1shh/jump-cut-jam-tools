---
tier: tested
source: stages/03_playtest/references/playtest-gate.md
updated: 2026-11-10
---

# Visual playtest: catching motion that still frames miss

## Tip: judge a burst of frames with no input, not four stills
- **Why:** the mock jam 10 packaged build, left on its OUT OF WATER screen, looped (camera fell toward the floor,
  snapped back wide, repeated). The gate looked at four stills and passed it. A `burst` step takes 10 to 60
  frames with no input and compares each frame with the next.
- **How to check:** `scripts/visual_playtest.py run` writes the motion item (item 8) and a `contact_<label>.png`
  sheet per burst. Read the sheet: the same view should repeat in every tile. The looping build measured 15 to 20
  grey-level change per step; a calm scene is under 1.

## Tip: frames must be at most 0.3 s apart (the old 3 s spacing is obsolete)
- **Why:** frames spaced about as far apart as a camera loop's period land on the same phase of the loop and
  look identical. The first version put no cap on the spacing (10 frames over 30 s is 3 s apart, which can hide a
  ~1 s loop). The limit is now `BURST_MAX_SPACING = 0.3`; the default burst, 12 frames over 3 s, is 0.25 s apart.
- **How to check:** a sequence with `seconds / frames > 0.3` is refused before anything runs. The same limit is
  applied to the real capture times: `analyze` averages the gaps and FAILs the motion item ("frames too slow to
  judge motion") above 0.3 s plus 25%. The Legion's screen grab can be slower than requested. If that happens,
  capture faster; do not override.

## Tip: a flat or black frame is a failed capture, not a quiet scene
- **Why:** a frame whose pixel spread is below 3.0 is black or one colour. Item 1 FAILs it, and a burst with
  fewer than 10 readable frames FAILs. The game being behind another window also FAILs item 1, because the
  screenshot shows the screen, not the game.
- **Re-run hint:** all-black frames can be the capture, not the build (the Legion console locks itself after
  idle time; one run came back black and a straight re-run on the same package was fine). The run now takes a
  probe shot first and stops with `Legion is locked` or `capture is black: re-run once before suspecting the
  build`. Re-run once, after unlocking, before you touch the game.
- **How to check:** `analyze DIR` prints the checks without writing anything. A burst FAILs on a mean step above
  4.0, a single step above 12.0, or a last frame more than 15.0 away from the first. It WARNs above a mean step
  of 1.5 (something animates by itself, such as water): read the sheet.

## Tip: sample the end screens and the restart, not just mid-play
- **Why:** the loop lived on the lose screen. The sequence must declare its end states
  (`{"op":"declare","end_states":["lose"]}`), have a burst tagged for each, make the last capture before the
  restart key an end-state burst, and take a burst after the restart. A missing one FAILs the motion item; it is
  never skipped.
- **How to check:** the default sequence has three bursts: `midplay`, `lose` and `afterrestart`. Tune limits in
  the `IDLE_*` constants at the top of `visual_playtest.py`. An animated game can pass a FAIL only with
  `Verdict: PASS (override: <why>)` after the sheet was read.

## Tip: first launch after a package needs a long warmup
- **Why:** the first start of a packaged game is slow and gives black frames (`mock-jam-findings-11.md:110`; the mock 14 re-run line used `--warmup 60`, `mock-jam-findings-14.md:17`).
- **How to check:** `visual_playtest.py run --warmup 60` on the first run after a package; a re-run after a short warmup may be fast.

## Tip: never paste one reason onto many checklist items
- **Why:** mock 12's second gate settled 14 items with one pasted reason and no result file (`mock-jam-findings-12.md:28-33`). Mock 15 hand-overrode every row (`mock-jam-findings-15.md:173-180`).
- **How to check:** each override carries its own reason after you read the frame. `verify` refuses one reason on many items (a tooling fix listed by mock 12).

## Tip: read the contact sheet; identical tiles mean the step labels lie
- **Why:** in mock 12 tiles 14 to 16 of `contact_steps_2.png` were the same YOU WIN frame under three step names, so no gate pass showed the second squeeze.
- **How to check:** look at the last tiles of every sheet. If two differ only in their label, the gate evidence is not real.

## Tip: whole-frame diffs miss a small player
- **Why:** a 40 px lantern that rose 300 px scored 0.1 against a limit of 12.0, so items 4 and 7 said FAIL though the frames showed the move and the reset (`mock-jam-findings-15.md:173-180`).
- **How to check:** override per item with a reason after reading the frames. A region diff around the player is the planned fix.
