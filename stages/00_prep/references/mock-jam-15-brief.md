# Mock jam 15 brief: sky lantern (first full mock on UE 5.9)

Slot: Tue 2026-11-10, daytime, started about 12:05 PT by a hub 71 side session. Hard stop **6 h after
start** (18:05 PT), and in any case before 2026-11-11 15:00 PT (the real window opens 2026-11-11 21:00 PT).
Clock: `python3 scripts/jam_clock.py start --deadline <ISO>`. Findings file: `stages/00_prep/output/mock-jam-findings-15.md`.
Shape copied from `stages/00_prep/references/mock-jam-14-brief.md`. Context: PR 148 made UE 5.9 MegaJam Preview the default
editor (5.8.4 fallback); PR 149 added the follow-ups. This mock is the first end-to-end run on 5.9.

**Rule 7(h):** run only in the throwaway `~/Projects/megajam-mock`. No gameplay, level, art, audio or
game code from this mock may be reused in the real entry. Only tooling fixes and the findings doc come
back. Nothing in the mock area is deleted without the owner's word.

## Theme reveal (read at T+0)

> **SKY LANTERN.** Make a game about a paper lantern carried up by its own flame.

Not used in mocks 10-14 (water, helium, slime, liquid metal, twisted balloon) or the mock 13 mini
(sleepy lighthouse).

## Game idea seed

You are the flame inside a paper sky lantern. Hold to burn hotter and rise; let go to cool and sink.
Fuel runs down while you burn. Wind gusts push you sideways into branches. Reach the stars line before
the fuel runs out. Touch a branch and the paper catches fire (lose).

## Physics and material focus

Buoyancy by heat (a vertical force that follows a heat value that rises and falls with lag), sideways
wind gusts, a fuel meter. Material: warm glowing paper (emissive orange) and a dark blue night sky; one
master material with Material Instances for each colour.

## Readiness gap to prove: the 5.9 path end to end

1. Editor launch on 5.9 through `scripts/launch-editor.sh PROJECT.uproject` (no `UE_VERSION`), under the
   16G crash scope (`LAUNCH_SCOPE_CMD`), after `gpu-preflight` (Lemonade unloaded first).
2. MCP answers: `scripts/mx.py toolsets` lists many toolsets, `mx.py describe PythonScriptingTools`
   answers, `mx.py py` returns a value.
3. `scripts/step_shot.py` writes its marker (`STEP_SHOT_OK`) and a PNG after each build step.
4. `scripts/force_save_level.py` saves the level and verifies it on disk (never run live on 5.9 before
   this mock).
5. Note every time the 5.8.4 fallback is needed, and why. "Never needed" is the hoped-for result.

## Pass / fail gates

- [ ] 5.9 launch: `launch-editor.sh` brings the 5.9 editor up on :8010 (record the seconds to listen).
- [ ] MCP toolsets answer on 5.9 (`toolsets`, `describe`, `py`).
- [ ] `step_shot` marker works on 5.9 (every build step has an `NN-step.png` that was Read, with a one-line
      verdict in the findings). `scripts/asset_preview.py` before any import (primitives only is fine).
- [ ] `force_save_level` works on 5.9 (saved, on-disk check passes, reload finds the expected actor).
- [ ] Greybox plays: rise, sink, wind push, fuel drain, win (stars line) and lose (branch or no fuel), and
      restart, proven in PIE on 5.9.
- [ ] PASS visual playtest (REQUIRED before "done"): `scripts/visual_playtest.py` ran on the PACKAGED build
      with real OS input (never the game's autopilot). Read the two or three `contact_steps_N.png` sheets,
      resolve every item and step `Verdict:` in its `checklist.md`, then `scripts/visual_playtest.py gate
      <out>`: "done" needs exit 0. Blank or AGENT verdicts never pass. Details: `stages/03_playtest/references/playtest-gate.md`.
      Windows/Legion is the real target. If the Legion cannot package 5.9 (no 5.9 install) or is locked,
      log it OPEN and run the stand-in: a 5.9 **Linux** package played with `--target local` (xdotool +
      x11grab under XWayland). The stand-in does not close the Windows row.
- [ ] PASS idle-stability (part of that gate): a ~3 s no-input burst mid-play, in each end state (lose,
      win) and after restart; read each `contact_*.png`; `Idle stability` FAILs on a looping or falling
      camera, flicker or respawn spam.
- [ ] Agent playtester plays like a human (`stages/03_playtest/references/agent-playtest.md`): win by real play, lose on purpose,
      restart, with frames and clips.
- [ ] Zip `TeamName_GameName.zip` named and under 1 GB (record name and size).
- [ ] Windows package pushed to `jf1shh/megajam-pretest:win64` and processed (`butler status`). Needs a
      5.9 engine on the Legion (`legion_ship.py --engine C:\Dev\UE_5.9`); OPEN if it is not installed.
- [ ] 30-60 s video recorded.
- [ ] Within 6 h. Editor closed, :8010 free, Lemonade restored with `--ctx-size 32768`.
- [ ] Findings in `stages/00_prep/output/mock-jam-findings-15.md` with a readiness table and every 5.9 bug or gap.
      Small tooling fixes on the same branch; `python3 -m unittest discover -s tests -p 'test_*.py'` passes.
- [ ] One draft PR on `jf1shh/megajam` (base `master`): brief, findings, tooling fixes. Not merged, not
      tagged, not marked ready (the hub does the Fable check and merges).

## Machine rules for this mock

- One GPU workload at a time: `lemonade unload`, then `gpu-preflight` must print CLEAR before the editor.
  After the editor closes: `lemonade load Qwen3-Coder-30B-A3B-Instruct-GGUF --ctx-size 32768` (never 8192).
- One Unreal editor at a time; wait about 5 s between stopping one and starting another (port 8010 bind race).
- Heavy jobs (editor, cook, package) inside `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=2G`.
- No generated art (primitives only); krea-2-turbo is off limits on this box during mocks (crash rule).
- Never delete or move `~/Projects/UnrealEngine-5.8` or `~/Projects/UnrealEngine-5.9`.
