# Mock jam 14 brief: twisted balloon art

Plan: `stages/00_prep/references/mock-jams-10-14-plan.md`. Slot: Tue Nov 10 21:00 PT to Wed Nov 11 07:00 PT, overnight (8-10 h, hard stop 10 h = 07:00; no sliding into the day).
Overnight: the owner starts the loop before bed; do not block on an owner ask (log it in the findings doc and keep going).
Findings file: `stages/00_prep/output/mock-jam-findings-14.md`. Owner ask 1 (real itch.io page) must be done first.

**Rule 7(h):** run only in the throwaway `~/Projects/megajam-mock`, and delete it after. No gameplay,
level, art, audio or game code from this mock may be reused in the real entry. Only tooling fixes and the
findings doc come back.

## Theme reveal (read at T+0)

> **TWISTED BALLOON.** Make a game about balloon-animal art: long balloons twisted into shapes.

(Hub 25 pick for "some other material or different physics"; it matches the four-lobed balloon logo.)

## Game idea seed

You are a street balloon artist. A customer asks for a shape (dog, flower, sword). You twist a long balloon
into lobes by pinching and turning it at marked points. Wrong twist spacing makes it bulge or pop. Finish
the shape before the customer leaves; the happier the customer, the more you earn.

## Physics and material focus

Constraint chains (a row of linked segments that bend and hold twist points), shape building by player
input, pop when a segment is over-inflated. Material: translucent latex in magenta and blue with a
rim-light. Use one master material with Material Instances for each colour.

## Readiness gap to prove: 5a (real entry page and butler target), then 6a (tag)

1. **Owner ask 1:** before the mock starts, the owner creates the real itch.io entry draft and tells the hub
   its `user/slug:channel`, plus the team name and game name. The hub writes both into
   `stages/00_prep/references/jam-day-runbook.md` section 3. The mock's agent reads the target from there.
2. From the Legion, run `package-and-push.ps1 -CheckButler`, record the output, then push a **tiny
   one-file test folder** (not the mock build) to the real target, as the planned day-1 test upload.
   `butler status <target>` must show it processed. Then the owner deletes the test build or leaves the page
   as a draft. The mock build itself still goes to `jf1shh/megajam-pretest:win64`.
3. Confirm the zip name `TeamName_GameName.zip` is produced with the real names, under 1 GB.
4. After this mock's findings merge: owner tags `pre-jam-tooling` (readiness 6a), the **last step** before
   the window. Run it only after all other doc merges.

```bash
git tag pre-jam-tooling origin/master
git push origin pre-jam-tooling
```

## Pass / fail gates

- [ ] PASS 5a: real butler target is written in the runbook, the test push succeeded and is processed. FAIL if
      the owner did not create the page: then 5a stays open, list it as the one open item.
- [ ] Zip name uses the real team and game names and is under 1 GB.
- [ ] Greybox plays: twist, bulge and pop visible.
- [ ] PASS visual playtest (REQUIRED before "done"): `scripts/visual_playtest.py` ran on the PACKAGED build with
      real OS input (never the game's autopilot). Read the two or three `contact_steps_N.png` sheets (one Read
      each, not every PNG), resolve every item and step `Verdict:` in its `checklist.md`, then run
      `scripts/visual_playtest.py gate <out>`: "done" needs its exit 0. Blank or AGENT verdicts never pass.
      "Greybox plays" means this, not a PIE log grep. Details: `stages/03_playtest/references/playtest-gate.md`.
- [ ] PASS short-clip motion check (REQUIRED, part of that gate): the run includes a ~3 s no-input burst
      mid-play, in each end state (lose, win) and after restart. Read each `contact_*.png` and keep the
      `Idle stability` item PASS: FAIL on a looping or falling camera, flicker or respawn spam. Mock 10's lose
      state looped its camera; 4 still frames passed it, the video
      (`~/Projects/megajam/work/legion-video/legion_screen.mp4`) showed it.
- [ ] Before the owner sees a build, the agent playtester plays it like a human (`stages/03_playtest/references/agent-playtest.md`,
      T-20261108-11): it must reach the WIN state by real play, lose on purpose, and restart, with frames +
      clips as evidence.
- [ ] Screenshot and look after every asset and every build step: each has an `NN-step.png` you Read and a
      one-line verdict in the findings: `scripts/asset_preview.py` before each import, `scripts/step_shot.py`
      after each step (plan's rules; by hand through Unreal MCP if not merged yet). A "wrong" was fixed first.
- [ ] Windows package of the mock pushed to `jf1shh/megajam-pretest:win64`, processed.
- [ ] 30-60 s video recorded.
- [ ] Within 10 h. Lemonade restored at ctx 32768.
- [ ] Findings in `stages/00_prep/output/mock-jam-findings-14.md`, ending with a table of readiness rows 1c to 6e and their final status.
- [ ] `~/Projects/megajam-mock` deleted after the findings merge.
- [ ] Final step, by the owner: `pre-jam-tooling` tag pushed (6a).
