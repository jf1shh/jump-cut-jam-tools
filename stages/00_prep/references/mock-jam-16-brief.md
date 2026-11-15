# Mock jam 16 brief: polarity flip (5.9, Windows path on the Legion)

Slot: Tue 2026-11-10 night, started about 21:10 PT by a side session of the master control hub (hub 81),
unattended (the owner is asleep). Hard stop **6 h after the jam clock starts** (about 03:15 PT
2026-11-11), and never later than 2026-11-11 10:00 PT (the owner's checklist stops megajam-mock then; the
real window opens 2026-11-11 21:00 PT). Clock: `python3 scripts/jam_clock.py start --deadline <ISO>`.
Findings file: `stages/00_prep/output/mock-jam-16-findings.md`. Shape copied from `stages/00_prep/references/mock-jam-15-brief.md`.
Context: mock 15 proved the 5.9 editor grey-box loop in about 15 min but left the packaged build, the itch
pretest push, the Windows playtest and the video OPEN, mostly because the Legion had no UE 5.9. The Legion
finished building the 5.9 editor at 21:00 PT tonight (`C:\Dev\UE_5.9`); its helper tools
(ShaderCompileWorker, UnrealPak, CrashReportClient) were restarted by hand at 21:03 PT.

**Rule 7(h):** run only in the throwaway `~/Projects/megajam-mock/mock16`. No gameplay, level, art, audio
or game code from this mock may be reused in the real entry. Only tooling fixes and the findings doc come
back. Nothing in the mock area is deleted.

## Theme reveal (read at T+0)

> **POLARITY FLIP.** You are a fridge magnet. Flip your pole to pull toward or push off metal.

Not used in mocks 10-15 (water, helium, slime, liquid metal, twisted balloon, sleepy lighthouse, sky
lantern).

## Game idea seed

You are a fridge magnet. Hold SPACE to attract: you are pulled toward the nearest steel plate. Release to
repel: you are pushed off it. A/D steer. Reach the goal plate to win. Touch spikes or fall off the screen
to lose. R restarts.

## Physics and material focus

An attract/repel force toward the nearest steel plate that falls off with distance (strong up close,
weak far away), plus gravity and A/D steering. Material: brushed steel plus one red/blue pole colour (red
= attract, blue = repel); one master material with Material Instances.

## Readiness gap to prove: the Windows path on the Legion with UE 5.9

1. Wait until `C:\Dev\UE_5.9\_build-logs\status.txt` shows the tools ended `exit=0` and
   `ShaderCompileWorker.exe` exists (checked over `ssh <device-host>`). Never change a Windows or Legion setting.
2. Package on the Legion: `legion_ship.py --engine C:\Dev\UE_5.9`.
3. Push to `jf1shh/megajam-pretest:win64` and check `butler status` (the only upload allowed).
4. Packaged visual playtest with real input on Windows (`scripts/visual_playtest.py`, gate exit 0; read
   every contact sheet).
5. Retry mock 15's SPACE-key bug in the packaged Windows build (keys read with `IsInputKeyDown`, as in
   mocks 14-15): is it a Linux/XWayland-only problem?
6. If the Legion is locked or its console is black, log it OPEN and use the Linux stand-in
   (`--target local`); do not work around it.

## Pass / fail gates

- [ ] 5.9 launch: `launch-editor.sh` brings the 5.9 editor up on :8010 under the 16G crash scope
      (`LAUNCH_SCOPE_CMD`), after `gpu-preflight` (record the seconds to listen).
- [ ] MCP toolsets answer on 5.9 (`toolsets`, `describe`, `py`).
- [ ] `step_shot` works on 5.9 (every build step has an `NN-step.png` that was Read, with a one-line
      verdict in the findings).
- [ ] `force_save_level` works on 5.9 (first live run of the mock 15 fixes: saved, on-disk check passes,
      reload finds the expected actor).
- [ ] Greybox plays: attract, repel, steer, win (goal plate) and lose (spikes, off screen), and restart,
      proven in PIE on 5.9.
- [ ] Windows package built on the Legion with UE 5.9.
- [ ] Windows package pushed to `jf1shh/megajam-pretest:win64` and processed (`butler status`).
- [ ] PASS visual playtest (REQUIRED before "done"): `scripts/visual_playtest.py` on the PACKAGED Windows
      build with real OS input. Read every `contact_steps_N.png`, resolve every `Verdict:` in
      `checklist.md`, then `visual_playtest.py gate <out>` exits 0. Details: `stages/03_playtest/references/playtest-gate.md`.
- [ ] PASS idle-stability (part of that gate): a ~3 s no-input burst mid-play, in each end state and after
      restart.
- [ ] SPACE key works in the packaged Windows build (mock 15 bug retried).
- [ ] Agent playtester plays like a human (`stages/03_playtest/references/agent-playtest.md`): win by real play, lose on purpose,
      restart, with frames and clips.
- [ ] Zip `TeamName_GameName.zip` named and under 1 GB (record name and size).
- [ ] 30-60 s video recorded.
- [ ] Within 6 h. Editor closed, :8010 free, Lemonade restored with `--ctx-size 32768`.
- [ ] Findings in `stages/00_prep/output/mock-jam-16-findings.md` with a readiness table, a scorecard row in
      `stages/00_prep/references/mock-scorecard.md`. Small tooling fixes on branch `mock16-findings`;
      `python3 -m unittest discover -s tests -p 'test_*.py'` passes. **No push, no PR, no merge** (the hub
      decides in the morning).

## Machine rules for this mock

- One GPU workload at a time: `lemonade unload`, then `gpu-preflight` must print CLEAR before the editor.
  Re-check before each heavy step (mock 15: Lemonade reloaded itself on demand). After the editor closes:
  `lemonade load Qwen3-Coder-30B-A3B-Instruct-GGUF --ctx-size 32768` (never 8192).
- RAM is tight (~9 GB free, swap 12 GB used): editor under the 16G scope, at most 2 helper agents live, no
  other heavy job at the same time.
- One Unreal editor at a time; wait about 5 s between stopping one and starting another (port 8010 bind race).
- No generated art (primitives only); no cloud media gen, no sign-ins, no keys.
- Never work around a permission denial or guard: log it and move on.
- Never delete or move `~/Projects/UnrealEngine-5.8` or `~/Projects/UnrealEngine-5.9`.
