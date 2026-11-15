# Mock jam 12 brief: slime balloon

Plan: `stages/00_prep/references/mock-jams-10-14-plan.md`. Slot: Mon Nov 9 21:00 PT to Tue Nov 10 07:00 PT, overnight (8-10 h, hard stop 10 h = 07:00; no sliding into the day).
Overnight: the owner starts the loop before bed; do not block on an owner ask (log it in the findings doc and keep going).
This mock also carries gap 5c (desktop video capture), folded in from mock 13 (see the 5c section below).
Findings file: `stages/00_prep/output/mock-jam-findings-12.md`.

**Rule 7(h):** run only in the throwaway `~/Projects/megajam-mock`, and delete it after. No gameplay,
level, art, audio or game code from this mock may be reused in the real entry. Only tooling fixes and the
findings doc come back.

## Theme reveal (read at T+0)

> **SLIME BALLOON.** Make a game about a balloon made of slime.

## Game idea seed

You are a green slime balloon in a candy-factory vent maze. You stick to walls, stretch through narrow
gaps and wobble back into shape. Sticky pads hold you in place; stretch too thin and you split. Reach the
exit pipe with enough slime left.

## Physics and material focus

Soft body feel, stick (surface contact that holds), stretch (scale along velocity, squash on impact),
split on over-stretch. Material: thick, wet, subsurface-like glow, cheap. Fake the soft body with a
spring-damped mesh deform or a squash-and-stretch shader, not a heavy sim.

## Readiness gap to prove: 2c (editor-restart recovery, and cook with the MCP plugin on)

Both are UNTESTED in `stages/00_prep/references/jam-day-runbook.md` section 2. Run them in the loop, with the real launch line:

1. **Editor-restart recovery.** With the lead agent connected over MCP, kill the editor and relaunch it with
   the launch line. Wait for `curl ... :8010/mcp` to print `405` (can take minutes). Make one MCP call from the
   **same session**. Record: did it work without `/mcp`? If not, write the wait-for-405 helper and reconnect
   step the hub should add to `AGENTS.md` ("Editor recovery").
2. **Windows cook, plugin on.** On the Legion, one `RunUAT BuildCookRun` of this mock's project with the MCP
   plugin enabled and Auto Start off. Record `echo $?`-equivalent exit code (0 = pass).
3. **Linux cook while the editor holds 8010.** Exit code and log: no `unable to bind`. Check the exit code
   right after the cook, not just the log text.
4. If a cook exits 1 with `unable to bind`, try disabling the plugin for the cook
   (`-DisablePlugins=ModelContextProtocol` or a cook-only `.uproject` copy) and record which form works.

## Also prove: 5c (desktop video capture), folded in from mock 13

**Do a short probe EARLY in the night (first hour, before the long work).** Record 10 s of the desktop
with each tool, open the file and check it is not black. Log the result in the findings doc and move on;
a failed or black probe must not eat the night. Owner 2026-11-07: the screen stays unlocked at night.
The probe is still what proves the capture really works. Do the full capture later in the night with the
tool that passed.

The mock's 30-60 s video must be made with the desktop capture path, not only Legion OBS. Try in order:
`wf-recorder` (if the owner installed it), `spectacle` screen recording, `ffmpeg` with `kmsgrab`. Record
which worked, the exact command, resolution (target 1920x1080 or higher) and frame rate. Also record the
same play on the Legion with OBS and compare in one line. Run the ffmpeg two-pass `loudnorm` (-23 LUFS)
once before muxing. Check the clip is 30-60 s and plays. Full text of the old plan: `mock-jam-13-brief.md`.

## Android spike (optional, 4 h box)

Owner 2026-11-08: decide Pocket Powerhouse with a timed Android packaging spike. Follow
`stages/00_prep/references/android-spike.md` (stamp every step; hard stop 4 h after its step 0). Run it only when the editor is
closed and `gpu-preflight` is clear (`scripts/android_package.sh` refuses otherwise). Because the mock
loop itself blocks the script by default, the mock session runs the package step as
`ANDROID_ALLOW_MOCK_LOOP=1 scripts/android_package.sh ...` (only after closing the editor; only this
session sets it). It needs a JDK 21 with javac, which the owner installs. Slot the spike after the
Windows package is pushed or in a gap, never in place of the 2c / 5c gates. Needs the owner for the JDK 21
install and for the phone's Wireless debugging port; if they are not available, log it and skip. Verdict
PASS or FAIL goes in the findings; FAIL means the hours go back to Fun Factor.

## Pass / fail gates

- [ ] Android spike (optional): PASS or FAIL recorded with stamps per `stages/00_prep/references/android-spike.md`, or "skipped, reason".

- [ ] PASS 5c: a desktop capture command that produced a playable 30-60 s clip at 1080p or higher is named
      in the findings. FAIL (with the reason) if none worked; then the fallback is Legion OBS only.

- [ ] PASS 2c-a: session recovered after an editor restart (with or without `/mcp`; record which).
- [ ] PASS 2c-b: Legion cook exit code 0 with the MCP plugin on.
- [ ] PASS 2c-c: Linux cook exit code 0 while the editor holds 8010, no `unable to bind`.
- [ ] Greybox plays: stick, stretch, squash, split visible.
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
- [ ] Windows package pushed to `jf1shh/megajam-pretest:win64`, processed.
- [ ] 30-60 s video recorded.
- [ ] Within 10 h. Lemonade restored at ctx 32768.
- [ ] Findings in `stages/00_prep/output/mock-jam-findings-12.md`, with the exact commands for any new recovery rule.
- [ ] `~/Projects/megajam-mock` deleted after the findings merge.
