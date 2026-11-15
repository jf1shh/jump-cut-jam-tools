# Mock jam 11 brief: helium balloon

Plan: `stages/00_prep/references/mock-jams-10-14-plan.md`. Slot: Sun Nov 8 21:00 PT to Mon Nov 9 07:00 PT, overnight (8-10 h, hard stop 10 h = 07:00; no sliding into the day).
Overnight: the owner starts the loop before bed; do not block on an owner ask (log it in the findings doc and keep going).
Findings file: `stages/00_prep/output/mock-jam-findings-11.md`.

**Rule 7(h):** run only in the throwaway `~/Projects/megajam-mock`, and delete it after. No gameplay,
level, art, audio or game code from this mock may be reused in the real entry. Only tooling fixes and the
findings doc come back.

## Theme reveal (read at T+0)

> **HELIUM BALLOON.** Make a game about a balloon that wants to float away.

## Game idea seed

A small helium balloon is tied to a kid's wrist by a string. You steer the kid through a windy street fair.
The balloon pulls up, drifts with gusts and snags on signs. Collect ribbons without letting the string
tangle or the balloon pop on a spike.

## Physics and material focus

Buoyancy (constant upward force), drift in a wind field, tether (a distance constraint or cable between
balloon and anchor). Glossy shell with a simple fresnel rim. Keep it cheap: one rigid body plus a cable
component.

## Readiness gap to prove: 2b + 6c (MCP read-only call, Editor Toolsets listed)

Start through the loop as in mock 10 (owner runs `proj start megajam-mock`). Then:

1. After the editor is up, make one **read-only** Unreal MCP call from the lead agent's own session
   (`list_toolsets`). Record the toolset count (dress rehearsal 2026-11-04 saw 67).
2. Open Edit > Plugins in the jam-style project. Record whether **Editor Toolsets** is enabled when only
   `ModelContextProtocol` and `AllToolsets` are on. If it is off, enable it explicitly and record the final
   `Plugins` list from the `.uproject`. Paste that list into the findings so the hub can copy it into
   `stages/00_prep/references/jam-day-runbook.md`.
3. Pin `ServerPortNumber=8010` in `Config/DefaultEngine.ini` and confirm the editor serves 8010 even
   without relying on the flag alone.
4. Check `describe_toolset` on one small toolset only. Do not describe Niagara.

## Pass / fail gates

- [ ] PASS 2b: `list_toolsets` returned, toolset count recorded.
- [ ] PASS 6c: Editor Toolsets status (on by default or enabled by hand) recorded, final `Plugins` list pasted.
- [ ] Greybox plays: float, drift with gusts, tether tug and pop all visible.
- [ ] PASS visual playtest (REQUIRED before "done"): `scripts/visual_playtest.py` ran on the PACKAGED build with
      real OS input (never the game's autopilot), and every item in its `checklist.md` is PASS after you read the
      frames. "Greybox plays" means this, not a PIE log grep. Details: `stages/03_playtest/references/playtest-gate.md`.
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
- [ ] Windows package built on the Legion, pushed to `jf1shh/megajam-pretest:win64`, processed.
- [ ] 30-60 s video recorded.
- [ ] Within 10 h. Lemonade restored at ctx 32768.
- [ ] Findings in `stages/00_prep/output/mock-jam-findings-11.md` (include any mock 10 fix that was needed to get started).
- [ ] `~/Projects/megajam-mock` deleted after the findings merge.
