# Build ledger (Jump Cut)

One entry per build. Add the entry when the build is staged, then append test results as they come in. Times are PT, 2026-11-11 night unless noted. Sources: `dv log` for megajam-game, the hub log (`superagent-sandbox/.handoff/hub80/LOG.md`), the Lead night log, `stages/05_devlog/output/2026-11-11.md`.

Ship command (all builds): `python3 scripts/legion_ship.py ~/Projects/megajam-game/JumpCut.uproject --engine 'C:\Dev\UE_5.9' --kill-leftovers [--no-push]`. It syncs the project to the Legion, packages there (UE 5.9 source build), checks the exe, then pushes to itch with butler unless `--no-push`. Staged build path on the Legion: `C:\Dev\megajam-game\Packaged\Windows\JumpCut.exe`. itch channel: `jf1shh/megajam-pretest:win64`. `butler status` at ~00:00 shows upload #20235025, build #2363485 (from #2363343), version 24: that is the latest push (B2); per-build versions for A and B were not recorded.

Rule (owner 23:49): no itch push of any later build until the owner passes it on the Legion; ship stage-only.

---

## A: auto-roll (pushed 22:54)
- First try (unit megajam-shipA) failed at 22:14:30, exit 1, AutomationTool exception (log megajam-game-20261111-221407.log). A = unit megajam-shipA2, log megajam-game-20261111-221503.log.
- dv commit: dv.commit.11 ("cap 60 fps, no Lumen or VSM for greybox", 22:02:29) plus any uncommitted edits at 22:15, because step 1 tars the working folder at sync time (22:15:05 to 22:15:06). The auto-roll flag (`ClapperWaitsForPress=false`) is data in that tree.
- Ship: `legion_ship.py` push step from the PC. BuildCookRun 2206 s (36m50s), BUILD SUCCESSFUL, zip 286.1 MB. The Legion script skipped butler (no -ItchTarget); step 4 pushed: 567.33 MiB (829 files), re-used 41.86% of old, added 329.86 MiB fresh, 133.82 MiB patch (76.41% savings), SHIPPED to jf1shh/megajam-pretest:win64 (processed) at 22:54:09. Timings: sync 0.0 min, package 37.4 min, push 0.7 min.
- Tests: none recorded beyond "shipped".
- Open issues: no start press; no stunts in the scene.

## B: press-to-start, sky, S1 stunt blocks (pushed ~22:57)
- Unit megajam-shipB, log megajam-game-20261111-225500.log. dv commit: the hub log says "dv 15" (dv.commit.15, 22:54:53, S1-2..S1-6 stunt BPs, asset only); the sync tar is of the working folder, so it may also hold uncommitted edits.
- Why: press-to-start handler, ACTION prompt, stunt blocks for the scene.
- Ship: sync 0.1 min, package 1.8 min, push: 567.35 MiB (829 files), re-used 47.15%, added 299.86 MiB fresh, 121.11 MiB patch (78.65% savings), SHIPPED to jf1shh/megajam-pretest:win64 (processed).
- Tests: owner by hand on the Legion at 23:03 to 23:17, gamepad.
- Result: FAIL. Owner: "none of the controls seemed to work on the legion gamepad".
- Key log lines (Legion log, read by the Lead 23:19): no "Clapper: rolling"; pad registers (XInput id 1); CommonInput flips Touch/Gamepad every 1 to 3 s; no errors.
- Open issues: pad input never starts the scene; possible touch ghosting.

## B2: raw-key start fallback (23:24)
- dv commit: dv.commit.18 (compiled 23:21:53). dv.17 added the raw-key start fallback and input bind logs. dv.18 added `-JCAutoStart` (injects pad A, logs the result). dv.16 added the ground plane and M_Ground.
- Why: fix the gamepad not starting. Fallback is PlayerController-based.
- Ship: unit megajam-shipB was reused (log megajam-game-20261111-232132.log): sync 0.1 min, package 2.0 min, push 567.37 MiB (829 files), re-used 42.33%, added 327.19 MiB fresh, 132.10 MiB patch (76.72% savings), SHIPPED to jf1shh/megajam-pretest:win64 (processed). Pushed at 23:24, before the no-push rule. The hub accepted it and did not roll back.
- Tests:
  - Desktop off-screen `-JCAutoStart`: PASS (Clapper: rolling).
  - Yo on the Legion 23:25 and 23:31, `-JCAutoStart`: PASS (24 IMC mappings, `phase=1 STARTED`, no errors, clean exit). On screen: red "LIGHTING NEEDS TO BE REBUILT"; the build line wrongly said base dv.commit.16.
  - Owner by hand, real A press, 23:45: PASS. Lanes left/right work; hold, cut and cancel work on the pad; one CommonInput line, no flipping; the car drives the road to the end.
  - Yo replay of the owner run (23:44): at T7.0 S1-1 is a flat grey slab down and right of the car; at T9.0 points 0 to 1, film 3 to 4 (the pass scored); no Stunt/Crash/Take log lines.
- Open issues: S1-1 hard to read; crash path unproven in this run; red banner.

## B3: Slate raw input, no banner (staged 23:46 to 23:49)
- dv commit: dv.commit.19 (23:38) plus dv.commit.20 (23:46, diagnostics: `jc.Trace`, `-JCTrace`, `-JCKmTest`, "JC action:" logs). The upload ran at 23:46:33, after dv.20, so the staged build includes both.
- Why: Slate IInputProcessor (`FJCRawInput` in JCGameMode.cpp) starts the scene from pad A, Space, Enter, LMB or touch on any device; logs "JC input: SLATE key=.. device=.. user=.." for the first 30 s. `GEngine->bSuppressMapWarnings=true` removes the unbuilt-lighting banner. The build line reads "JumpCut build: B3".
- Ship: `legion_ship.py ... --kill-leftovers --no-push`, unit `megajam-shipB3`. Sync 0.0 min, package 2.2 min, total 2.3 min. NOT on itch. Exe checks: all three paths present.
- Tests:
  - Desktop off-screen autostart: PASS (STARTED).
  - JumpCut.Stunt.Determinism (editor, nullrhi): Success, run twice (23:39, ~00:48 by the box clock). It covers the code test stunts and the DA_Scene_01 rows, pose model only; the runtime event timeline is not covered.
  - K&M synthetic run (`-JCKmTest`, off-screen): every mapped key fires its action. Map: LaneLeft = A, Left, DPad_Left, LeftStick_Left, LeftShoulder; LaneRight = D, Right, DPad_Right, LeftStick_Right, RightShoulder; Hold/start/cut = Space, LMB, Pad A, RightTrigger; Cancel = X, RMB, Pad B, LeftTrigger; Rev = W, Up, Pad X; Pause = Esc, P, Pad Start.
  - Road trace (`-JCTrace`, no input): the car moves 18 m/s along +X; S1-1 (BP_Stunt_FalseFront_C, x=12600) telegraphs from T=4.5, on at 7.0, off at 7.5, mark at 9.0; with no input the car crashes at T=7.0 and the take restarts (intended).
  - S1-1 fall: it fires; part 0 rolls 0 to 90 degrees between T=6.0 and about 7.0, so it is flat on the road side when the car arrives.
  - Source grep: no `AddOnScreenDebugMessage` or `DrawDebug` calls.
  - Yo on the Legion (auto-start, K&M drive, S1-1 pass and crash shots T5 to T10, T58 check, 3 devlog screenshots): started ~23:55; output in `C:\Dev\legion-b3\` (REPORT.md, shots). RESULT (Yo, 6 launches, relayed by hub 113 ~00:30): NOT CLEAN, no itch push.
    - PASS: autostart (T=1.01); K&M Space, A/D lanes, hold+release cut, X cancel; S1-1 front tips T6.5 and lands T7.0; dodge-left PTS 0 to 1 at T7.5; stay-centre crash at T7.0 (mark 0; TAKE stays 1 on the first crash via FreeTakeStunt, +1 on the 2nd and 3rd); 0 Error/Fatal in 6 logs; lighting banner gone; no game crash.
    - FAIL 1: Esc/P pause does nothing (keys logged, HUD clock keeps running, no overlay; nothing binds OnPausePressed).
    - FAIL 2: no results screen. Road ends ~T39, grey ground to ~T50, then black void; HUD still counting at T74.7 (OnWrapped is a BlueprintImplementableEvent on bare C++ UJCHudWidget, so nothing draws).
    - Notes: build label says "B3 (dv.commit.18 + Slate raw input)", should be dv.20; -ResX/-ResY ignored (window 1600x1000).
    - Devlog shots pulled to `stages/05_devlog/output/media/` (devlog-1/2/3, 3b).
- Open issues: black screen at T58.5 (Yo shot, "black except lit car box") is unconfirmed; probably end-of-film Wrapped state, and the C++ fade is only the 1-frame cut splice. Check whether a results screen follows.

## B4: results screen, pause, free-take stamp (staged 00:12:57 to 00:15:20)
- dv commit: dv.commit.23 (includes dv.21 event logs and dv.22 S1-1 readability: lean T5-T7, tall orange false-front). Label in log: "JumpCut build: B4 (results screen, pause, free-take stamp)".
- Why (B3 fails): UJCHudWidget now binds OnWrap and draws "THAT'S A WRAP / POINTS / STARS / play again"; the scene also wraps when the car reaches the road end (log "JC event: end of road"); Esc, P or pad Start toggles pause through the Slate processor (game paused, "PAUSED" overlay); Space/Enter/click/pad A restarts after the wrap (OpenLevel); first crash shows "CUT!  free retake", later ones "CUT!  retake N".
- Ship: `legion_ship.py ... --kill-leftovers --no-push`, unit `megajam-shipB4`, package 2.3 min, total 2.4 min, exe checks EXISTS x3. NOT on itch.
- Tests: compiled; desktop off-screen -JCTrace smoke OK (label, crashes). Wrap, pause and restart NOT yet verified. Yo on the Legion: pending (pad Start cannot be faked: not tested). Expected results at about T39 of a crash-free run.
- Open issues: no off-screen wrap/pause hook yet; road/ground vs scene length handled only by wrap at road end; -ResX/-ResY ignored.

## B4 verdict (Yo, relayed by hub 114, 2026-11-12 ~01:30)
- NOT CLEAN, one fail: the scene clock kept running behind the results screen (T past 60, black void behind the lit car). Everything else passed: autostart, K&M lanes/hold/cut/cancel, S1-1 dodge, centre crash (T->0), pause on Esc/P with T frozen, restart from results (Space/Enter/LMB), "CUT! free retake" then "retake 2", 0 Error/Fatal. Pad Start and pad A not tested. NOT pushed to itch.

## B5: wrap fix + splice grain (staging started 00:37)
- dv commit: dv.commit.27 = B4 (dv.23) + dv.25 film-grain burst on every splice + dv.26 wrap fix (JCSceneClock::Tick returns before advancing T once Phase is Wrapped, so T stays frozen at the wrap and the HUD T line stops) + dv.27 label "JumpCut build: B5 (wrap fix: T frozen on results, splice grain)".
- Proof (desktop, off-screen, -JCWrapTest extended to hold ~33 s on the results screen): T stayed 39.70 over 69 hold lines, no void, restart after wrap OK, 0 Fatal.
- Ship: `legion_ship.py ... --kill-leftovers --no-push`, unit `megajam-shipB5b` (first unit failed at once: wrong working directory, nothing ran). NOT on itch.
- Not covered: pad Start / pad A on the Legion; music low-pass (no music yet).

## B5 verdict and push (2026-11-12)
- Verdict: CLEAN (Yo; `C:\Dev\legion-b5\REPORT.md`, verdict.json checked by hub 115). Label compiled 00:38:13 matches BUILD.txt "dv.commit.27 staged 2026-11-12 00:40:06". Gate lines: won `JC HUD: results screen shown points=4 stars=2`; lost `JC event: CRASH stunt=0 take=1 free=1 T=7.00`; restart `JC: restart after wrap`.
- Hub order: `GO push B5` (hub 115, 2026-11-12 ~01:05).
- PUSHED 2026-11-12 01:10 PT: the exact staged dv.27 build, unit `megajam-shipB5d` (`legion_ship.py --from-step 4`: no re-sync, no re-package; the PC-side packaged-state twin was restored after verifying the Legion marker and BUILD.txt, because the earlier log dir was gone). Channel `jf1shh/megajam-pretest:win64` (private pretest page), butler build #2364016 (from #2363485), version 25, upload #20235025, 568.22 MiB, patch 132.49 MiB (76.68% savings), status processed, total 1.2 min.
- B6 list (cosmetic, nothing blocking): HUD T still visible on results (frozen); overlays centred on the car; low contrast of orange CUT! over the orange S1-1 front and yellow POINTS/STARS on the white road; -ResX/-ResY ignored (1600x1000). Not tested: pad Start/A on the real pad, end-of-road wrap path (needs an off-screen hook). Already committed for B6: dv.28 music hook, dv.29 -JCPadTest flag.
- Devlog note B5 saved in repo: stages/05_devlog/output/2026-11-12-B5.md (not posted to a site; no post path given).

## B6 staged (2026-11-12, stage only, NOT on itch)
- dv.commit.30, label "JumpCut build: B6 (HUD panel, overlays up, -ResX/-ResY, road-end test)" compiled 01:33:00; BUILD.txt "dv.commit.30 staged 2026-11-12 01:42:21". Unit `megajam-shipB6` (`--no-push`; sync 0.0m, package 2.4m).
- Changes: dark 60% backing panel behind PAUSED / CUT! / results; overlays moved to the upper third; "T ..." line hidden on results; -ResX/-ResY honoured via UGameUserSettings (off-screen log "resolution set to 1280x720"; non-shipping block).
- Off-screen proof (-JCRoadEndTest, SetT near end): `JC event: end of road T=39.70` -> `WRAP points=5 stars=2` -> `JC HUD: results screen shown`. Car is placed from T each frame, so moving the car does not work as a test; the clock jump does.
- Not visually checked off-screen (no screenshot hook); Yo to eyeball panel contrast. Pad Start/A on the real pad still untested.

## B6 verdict and push (2026-11-12 02:21 PT)
- Yo's Legion verdict CLEAN (hub 115 read `C:\Dev\legion-b6\verdict.json`: B6, dv.commit.30). Gate lines: won 09.55.36:586 "JC HUD: results screen shown points=4 stars=2"; lost 10.00.51:084 "JC event: CRASH stunt=0 take=1 free=1 T=7.02"; restarted by Space 09.56.07:977, Enter 10.03.38:494, LMB 10.05.43:899. Shots: `C:\Dev\legion-b6\job3a\job3a_S+40.00.png` (results), `job3b\job3b_S+08.00.png` (CUT!).
- PUSHED on hub line "GO push B6": BUILD.txt checked first (dv.commit.30 staged 01:42:21), unit `megajam-pushB6` (`legion_ship.py --from-step 4`). Channel `jf1shh/megajam-pretest:win64` (private pretest page), butler build #2364382 (from #2364016), version 26, upload #20235025, 568.52 MiB, patch 127.95 MiB (77.49% savings), processed, push 1.3 min.
- Fix list for next build: CUT! orange is 4.0:1 on the white road (needs 4.5:1); results panel 8 px past the upper third; -JCRoadEndTest leaves the car 13 m past the road end; verify the -ResX DPI fix (in B7/B8) on the Legion.

## B8 and B9 (not pushed)
- B8 = dv.commit.33 (title screen, Quit via Q / pad Back; includes all of B7). Staging to `C:\Dev\megajam-game-b8` (unit `megajam-shipB8`, no push). Legion testing paused until the owner starts a fresh Legion session.
- B9 = dv.commit.34-35 (action sounds S_Pause, S_Resume, S_Wrap, S_NoFilm, S_ShotKept; `-JCNoFilmTest`): off-screen log lines show all five play. Not in the B8 package.

## B7 music (2026-11-12, not yet staged)
- dv.commit.31: `/Game/Audio/Music/SW_Jam_Loop` (looping SoundWave, 17.14 s, 112 BPM, 8 bars) set as `DA_Tuning_Default.Music`. Made by code (`scripts/synth_music.py`, stdlib, deterministic, no samples, no AI, no download), imported headless by `scripts/ue_import_music.py`. Licence: original, nothing sourced. CC0 route skipped (raw fetch of asset pages is banned; MetaSound graph by script too slow).
- Off-screen proof (`-JCMusicTest`): `JC music: started SW_Jam_Loop`; hold at T=5.00 gave low-pass lines stepping 20000 -> ~11000 Hz and back to ~19555 Hz after release; no Error/Fatal from the game (only the editor's MCP port-8010 bind notice).
- Not heard: nobody has listened yet; Yo/owner to judge on the Legion. No cut stinger yet.

### Provenance: own-work audio (B7, 2026-11-12)
| Asset | Source | Licence | Generator and seed | Game commit |
|---|---|---|---|---|
| `/Game/Audio/Music/SW_Jam_Loop` (17.14 s loop) | own work, synthesized by code | original, nothing sourced, no AI, no samples, no download | `scripts/synth_music.py OUT.wav`, `random.Random(1)`, 112 BPM; wav sha256 `e994a207a7ccc26f...` | dv.commit.31 (+ re-import in dv.32) |
| `/Game/Audio/Music/SW_Jam_Cut_Stinger` (1.10 s) | own work, synthesized by code | same | `scripts/synth_music.py --stinger OUT.wav`, `random.Random(1)`; wav sha256 `c8be0679494e8627...` | dv.commit.32 |
Imported headless by `scripts/ue_import_music.py` (MUSIC_WAV, STINGER_WAV). Stinger sits in `Tuning.SoundSlots["S_Cut_Stinger"]`, played by the HUD crash handler.

### B7 additions so far (not staged; waiting on Yo's B6 verdict)
- Window: `JCGameMode::BeginPlay` honours -ResX/-ResY then clamps to the monitor work area (height minus 40 px). Config `bAllowHighDpiWhenUnattended=True`: the engine only goes per-monitor DPI aware when not `-unattended`, which is likely why the Legion test saw 960x600. Off-screen proof: log `JC window: asked=1 want=1280x720 work area=1280x720 -> 1280x680`. Real DPI behaviour is provable only on the Legion.
- Stinger proof: every `JC event: CRASH` is followed by `JC audio: cut stinger SW_Jam_Cut_Stinger`; no game Error/Fatal.
- Gap 19 (`legion_ship --state-dir`) was already done and merged on PR #191 (89 tests pass).

## B10, B11, B12 (not pushed; not in the B8 package)
- B10 = dv.commit.36: CUT! contrast (panel alpha 0.82, orange 1,0.55,0.18), results panel inside the upper third, shorter hints. Screenshot `JC_results.png` checked by eye; contrast estimated 5.8:1, not measured on the Legion.
- dv.commit.37: end-of-road wrap uses `DistanceAt(T)` instead of straight-line distance (`JCSceneClock.cpp`); `-JCRoadEndTest` logs D(T).
- B11 = dv.commit.38: restart from pause (R / pad Y). `-JCRestartTest` proved it with keyboard and with `-JCPadTest`.
- B12 = dv.commit.39: `-JCFullRunTest` plays the whole scene start to wrap off-screen. Log: 6 stunts, 5 cuts, wrapped at T=37, points 2, stars 1, no Error/Fatal, no timeout.

## B8 failure, dv.40-dv.43 (2026-11-12)
- B8 package (dv.33, unit megajam-shipB8) FAILED after 78 min: MSVC C4458 in `JCHudWidget.cpp`, a local `Slot` hid `UWidget::Slot` (stinger code from dv.31; Linux clang accepts it). Fixed in dv.41 (renamed `StingerSlot`).
- dv.40 = `-JCNoCuts` clean driver (cuts only MustCut). dv.43 ticks it at 0.02 s: S1-1,2,5 kept, S1-3 and S1-6 Perfect, S1-4 MustCut cut, 0 crashes, points 10, stars 4. The earlier S1-6 crash was 0.25 s test-tick jitter, not the game.
- dv.42 = `ShadowVariableWarningLevel = Error` in `JumpCut.Build.cs`: Linux builds, but it does NOT catch the Slot class of bug (local vs inherited member). Kept, harmless.
- Staged Legion build = dv.42 (unit megajam-shipB9w, warm `C:\Dev\megajam-game-b8`, 2.9 min), BUILD.txt "dv.commit.42 staged 2026-11-12 03:33:20", not pushed.
- New guards (PR #191 branch): `scripts/shadow_lint.py` (textual, 0 hits on dv.42) and `scripts/legion_compile_check.py` (Win64 JumpCutEditor compile on the Legion; live run PASSED in about 23 s UBT). `legion_ship.py` now runs the compile check before sync/package (`--skip-compile-check` to bypass).

## GEN 1 art pack (2026-11-12)
- Concepts: **fal-only (gpt bridge broken)**. fal schnell 12/12 ok; gpt 0/12. Cause: `codex exec` reports "image_generation tool unavailable" for the bridge's prompt. Codex's default model gpt-6-luna has no image tool; pinning `gpt-5.6-terra` (bridge now does) did not fix the bridge, though two hand smokes with a short prompt did make a PNG. Root cause not found.
- 3D (Meshy): first 4 jobs failed after generation because `nexus-3d handoff` needed the foundry CPU tail venv (`~/Projects/foundry-lab/tail-venv`, missing). Rebuilt it with uv (python 3.12: numpy, open3d, trimesh, fast-simplification, xatlas, pillow, scipy); relaunch then passed. Rodin asset stays in Hold until the owner OKs it.
- `gen1_launch.py` now stops a lane early and writes `work/gen1-ALERT.txt` when more than half of its finished jobs failed (min 2).
- Sheets: `work/generated/sheets/{s1_mainstreet,s2_chase,s3_depot,hero_car,props}.png`.
- **Hub picks (2026-11-12): direction A for every scene** (only one that keeps the black void + amber tungsten key). Never use: S1-C ("MAIN" text, teal sky), hero B (plate "1974", real-looking grille), S2 B/C (people), S3 C (pumpjack).
- Redos (fal, A only, `scripts/gen1_redo_a.py`): hero car mid-jump and S3 depot with gas holder + timber bridge. v2 rejected (car read as a real Challenger with a badge; depot had a red star and no black void). v3 kept: `concept_A_hero_car_fal_v3` (mid-jump, black void; tiny grille mark and blank plate remain, no readable text) and `concept_A_s3_depot_fal_v3` (tank + plank bridge, black void, no emblem). Sheet: `work/generated/sheets/picks_A.png`.

## Legion test builds for the human runner (2026-11-12)
Numbering here is the runner ladder the hub uses (not the older B10-B12 gate labels above).

| Build | Game commit | BUILD.txt stamp | Published to (Legion) | Zip | Package time | legion_test |
|---|---|---|---|---|---|---|
| B9 | dv.commit.63 | (see hub log) | | | | runner 1 |
| B10 | dv.commit.65 | (see hub log) | | 303 MB | | runner 1 |
| B11 | dv.commit.72 (DPI fix + SM6/iGPU perf preset) | "dv.commit.72 synced 2026-11-12 09:26:10 staged 2026-11-12 09:41:35" | `C:\Dev\megajam-game-b11\megajam-game\Packaged\Windows` | `SecondUnit_JumpCut.zip` 430 MB | 16.0 min (09:25:35 -> zip 09:41:32; sync 0.8 + package 14.6; first SM6 shader compile, full cook 610 pkgs) | runner 2 (pending) |
| B12 | dv.commit.92 (CLOSE-B time-margin tiers + AUD-2 stunt sounds + AUD-3 loudness/limiter + S1 look steps 1/3/4/5) | "dv.commit.92 (+21 uncommitted paths in the tar) synced 2026-11-12 12:57:31 staged 2026-11-12 13:00:34" (the +21 are graft/.cache and .handoff notes, not game files) | `C:\Dev\megajam-game-b12\megajam-game\Packaged\Windows` | `SecondUnit_JumpCut.zip` 436.6 MB | 3.1 min (sync 0.7 + package 2.4; DDC reused). Try 1 stopped at the Win64 shadow_lint (`Slot` C4458), fixed in dv.92 | runner 4 (done; hub 133 PASS as fallback, perf FAIL; see B12 results below) |

- Ship root `C:\Dev\megajam-game-ship` and its DerivedDataCache stay fixed for B12; only `--publish-root` changes, so the SM6 shader DDC is reused.
- After B11: dv.commit.73 = item 18 crash beat + G2 safe lane (hit-stop, black at 0.27 s, CUT!/FREE RETAKE slate, ACTION! stamp, 2-frame crash + PERFECT shake, crash rumble) and `-JCCrashTest` bot. Off-screen proof passed: 3 crashes, safe lane lit on the 3rd-crash hold. Watch: the first crash of a run went black at 0.44 s (later crashes 0.30 s), likely a first-use load; runner 2 times crash 1 vs 2-3 on B11.

- B12 contents (lead e57625c4): dv.83/84 stunt telegraph + action SFX, WRAP slate cover sound, DA_Stunt sound fields, S_Slate_Cover slot; dv.85/86/88/90 Scene 1 look: grade, real props on all 6 stunt BPs (crane removed: its mesh had a car baked in), M_Road with dashed lanes, cyc skyline; dv.87 loudness pass (12 re-imports, 44 volumes, VO +6 LU over the music bed, SMX_Master master submix with a -1 dB / 5 ms limiter); dv.89 CLOSE-B near-miss tiers by time margin (PERFECT 0.10 s / CLOSE 0.20 s / WIDE), stunt name + EARLY/LATE on the stamp, stamp at the pass, one-time CLOSER = MORE POINTS; dv.91 stunt sound code; dv.92 Win64 rename.
- B12 desktop proof (off-screen, sound on): full run wrapped at T=37 with 9 stunt-sound lines and no sync loads; crash test replays telegraph/action sounds on each retake; CLOSE-B tier windows match the model within one 33 ms frame (S1-1, S1-3). Not proven: S1-6 stamp timing, gamepad (runner 4 drives keyboard only; pad = owner check), loudness by ear.
- Tag rule (hub, 2026-11-12): each build that passes the hub look gets a Diversion tag `good-bNN-dv.MM`; `good-b11-dv.72` is set.

## B12 results (2026-11-12)
- Verdict: PASS as the fallback build (hub 133). Diversion tag `good-b12-dv.92`. Owner pad hand-check moved to the Fun-test build (controls change).
- a) Perf (Legion Go S, iGPU preset, 3 clean runs, 10/10 kept, 0 crashes): FAIL on both budgets.
  - fps median 56.6 / 55.0 / 55.9. GPU 15.07-15.32 ms (budget 14.5; B11 14.90). 1% low 28-31 fps without reload, 22-24 with reload (budget > 55). DynRes 51-54 % (floor 50).
  - The frame is paced by GPU and present (render thread waits on GPU). Legion GPU passes: TAA 2.2 ms, MotionBlur 2.0, PostProcess 1.7, ShadowDepths 1.7.
  - Probe 1, `r.AllowOcclusionQueries=0` (-dpcvars, same build): DROP. RT 18.2 -> 11.3 ms, but EventWait 0 -> 6.8 ms; fps, GPU and 1% low unchanged; bigger hitches (S1-4 jump 66.8 vs 48.4 ms).
- b) Cut spikes: first-time cut hitches gone (41 sounds primed). Left: S1-1 start 33-35 ms at every gameplay start; S1-4 hold 24-37 ms, GPU-bound; S1-4 jump 46 ms once (unexplained); new S1-6 resolve ~50 ms in 3 of 4 runs.
- c) Keyboard play-test (4 runs). Fixed: lane lines, "CLOSER = MORE POINTS", stamp box, RETAKE wording, wrap breakdown, R/Q.
  - Open: A/D steering never taught; cold title shows pad prompts on keyboard; hold ring unlabeled; pause does not dim; Director's Note small; "N: NEXT SCENE" unexplained; S1-6 PERFECT stamp ~1.3 s late; HOLD NOW prompt at every approach; DELETED SCENE black frame; N -> scene 2 HUD says SCENE 1; camera inside S1-6 facade at T~35.3; VO_Wrap and VO_Beautiful dropped at wrap.
  - Down time: no-decision gaps 4.5 / 2.3 / 2.3 / 1.7 / 1.5 / 2.3 / 0.35 s; 42 % of the run with no decision; longest no-key stretch 7.2 s. Lane change settles in 0.25 s. Audio meter peak 0.54, no clipping.
- Follow-ups: PERF-1 = GPU-pass cvar groups for B13. Owner-approved pacing plan (`lead-reports/fable-pacing-plan.md` on the lead's machine): throttle -> scene clock rate, S1 re-time to ~24-27 s, TOO SAFE tier, curved S1 road.
- Sources: Legion `C:\Dev\legion-b10\b12-perf.md` and `b12-probe1.md`.

## B13 (2026-11-12, not pushed)
- Contents: dv.commit.101 + working tree (DRIVE-3 pacing: S1 re-timed to 28.5 scene-s, scene clock, ramp jump + jump cam + B-cam, TOO SAFE tier; HUD-3 call sheet, frame corners, stamps; 2-press quit), BUILD.txt stamp dv.commit.102 +14 (take-number fix). Label `B13 (pacing + ramp jump + HUD-3)` from `DefaultGame.ini [JumpCut.Build]`.
- Snapshot 17:28 PT, shipped 17:31 (3.4 min) to `C:\Dev\megajam-game-b13\megajam-game\Packaged\Windows`; zip 465.2 MB; vc_redist present.
- Map: Scene 1 shipped as the old STRAIGHT road. The curved-road rebuild overlapped the snapshot, so the snapshot took the restored straight level (clean, no repackage). Lesson: holding the UE lock is not enough; workers check the journal for a snapshot/freeze line before any save.
- Tests (Legion runners 10 and 11):
  - Label and GameOverride preset (FTB14 / MinSP 67 / AA 2) confirmed.
  - Native-res perf (runner 11): 1% low 20.4 / 21.0 fps (B12 26.5 / 27.4); medians better (frame 16.3 vs 18.0 ms, GPU 12.9 vs 14.9 ms). All 12 frames over 50 ms were the Slate font-atlas flush (`Large atlases out of space 2/1`, x14 per run); without them 1% low 34.2 / 37.9. Fixed for B13b in dv.103 (`Slate.MaxFontNonAtlasTexturesBeforeFlush=8`, `MaxFontAtlasPagesBeforeFlush=4`; desktop run shows no flush).
  - Crash on window close 1 of 6 (`IsInGameThread` in the FSceneViewport destructor from DrawWindow_RenderThread). Fix for B13b: forced exit on Q-quit and window close (`JCExitNow`); Development config kept.
  - Break-it (runner 11, 10 bugs). BLOCKER: pause then R leaves the retake cover stuck until its 12 s failsafe (6 of 11 tries). Root cause: the cover compared raw `UWorld*` addresses and a same-level reload can reuse the address. Fix in progress (weak pointer + reload loop test). Others split B13b / B13c / B14 (held-Space at window open, R-restart take number, S=W speed, CUT HERE shown ~1 s before its window (VO at T ~11.0, window opens 12.0), ramp approached from the closed L/C lanes reads badly (crash walls planned)).
- Verdict: NOT PASSED (soft-lock blocker). B12 stays the safe build.

## Safe build (from 2026-11-12 19:21 PT)
Rule (hub 140 message 2026-11-12 ~19:15 PT, from Fable's plan-B verdict `gdd-backup-fable.md` section 3): after every snapshot, the newest package that PASSED the Legion runner is the named safe build: Legion folder kept, zip + sha256 copied to the NAS jam backup (`megajam-jam/safe-builds/<id>/` with `SAFE.md` = 4-line trim recipe; `safe-builds/CURRENT.txt` names the current one). Go/no-go is the Fri 11:45 Legion check of B14: if red, ship the safe build with its trims.

| Named | Build | Package | sha256 | Trim recipe |
|---|---|---|---|---|
| 2026-11-12 19:21 | B12 (dv.commit.92, tag `good-b12-dv.92`) | Legion `C:\Dev\megajam-game-b12\megajam-game\Packaged\Windows`; NAS `safe-builds/B12/SecondUnit_JumpCut_B12_safe.zip` (501.6 MB: re-zipped on the desktop with Info-ZIP from the Legion folder, so it is bigger than the 436.6 MB package zip of 13:00, which was not kept; the folder holds 946 files) | `436f158921cccae2e3a41cf8a615ce1f52dcfcba2da85966f067e1da58e24c16` | Ship as is (no menu, crane or Director's Cut in B12); rename to `SecondUnit_JumpCut.zip`; known: close crash and pause-R cover stall may exist, Legion 1% low 28-31 fps without reload, 22-24 with reload (B12 results; runner 11's native-res run measured 26.5 / 27.4) |
| 2026-11-12 21:28 | B13b (dv.commit.105, label `B13b (S2 + opener + rumble + curved road + text diet + fixes)`) | Legion `C:\Dev\megajam-game-b13b\megajam-game\Packaged\Windows`; NAS `safe-builds/B13b/SecondUnit_JumpCut_B13b_safe.zip` (493,795,852 bytes) + BUILD.txt + SAFE.md; `CURRENT.txt` points here | `97dc17beda9228cd246886dd9ec37805e1f3ca680ac5b8bb82cb66d0e3de902c` | None: B13b has no unproven features, so the B12 trim recipe does not apply |

## B13b (2026-11-12, not pushed, safe build)
- Contents: dv.commit.104 (all B13b paths) + dv.commit.105 (label `B13b (S2 + opener + rumble + curved road + text diet + fixes)`). DRIVE-4: Scene 2 re-timed (A5 table, S2-R ramp mirrored to lane L), opener ramp S1-0/S2-0 across all lanes (Shot 0: no film, points or cut window), pad rumble on landing and CLOSE, kicker on MI_Set_Plywood and the mark strip on a flat grey (the dark seam), S/Down/LT braking fixed (IMC Negate modifiers had been saved as null). Close crash fix: forced exit on Q-quit and window close (`JCExitNow`). HUD-4 text diet (24 items: fewer words on every screen, SAFE LANE on the retake slate). FIX-1 pause-R soft-lock fix (cover keeps the old world as a weak pointer; `-JCRestartLoopTest=N`; pause restart cover reads TAKE n). ROAD-1 curved Scene 1 road + canal. Font-atlas flush ini from dv.103. Kenney CC0 glyphs, stars and UI sounds imported under `Content/UI/Sourced/` and `Content/Audio/Sourced/` (rows in `sourced-assets.csv`, PR #198; not wired in B13b).
- Desktop proof before the snapshot (DRIVE-4 report `drive1.md` 17:55 and 19:30): S1 and S2 `-JCFullRunTest` wrap (S2 18.0 s, ramp lip 353.7, landed); 10x pause-R in one launch, cover off in 506-588 ms, 0 failsafe (FIX-1 READY, lead journal 19:28) (the lock never reproduced on Linux, even with the old code, so the Legion run decides); `-JCQuitTest` exit 0; S throttle 0.8x, W 1.41x.
- Not in B13b: held-Space bugs 2/3 (parked for B13c), ramp crash walls (B13c).
- Snapshot synced 19:35 PT (journal SNAPSHOT TAKEN 19:38), shipped 19:42 (7.1 min: BUILD.txt sync 19:35:00 to staged 19:42:06) to `C:\Dev\megajam-game-b13b\megajam-game\Packaged\Windows`; BUILD.txt `dv.commit.105 synced 2026-11-12 19:35:00 staged 2026-11-12 19:42:06`; zip 465.2 MB; vc_redist present. `--no-push`.
- Tests (runner 12, queued by the hub): acceptance (close 10x + 5x Esc,Q,Q; no font-atlas flush; canal/ramp stills; text diet), soft-lock hammer (Space, Esc, R 10x), FXAA motion check, A3 sweep. Results (runner 12 `legion-20261112-190234`, Legion, Windows):
  - Close crash PASS 15/15 (10x CloseMainWindow + 5x Esc,Q,Q: 0 dialogs, exit 0 via `JCExitNow`); label OK; 0 asserts in 15 logs; crash slate take matches the event (the B13 stuck take=2 is gone).
  - Part 2: font atlas FAIL on the strict check (flushes 14 -> 1; the '5/4' in the log is the atlas-page limit, so B13c raises `Slate.MaxFontAtlasPagesBeforeFlush` 4 -> 8); text diet title and in-play PASS, airborne and wrap FAIL (HUD-5 fix accepted for B13c at 20:56, not yet built or run); road bends PASS.
  - Break-it re-check CLEAN (16 launches, 0 crash/assert/soft-lock): fixed S-brake, wrap guard, rolling tap, slate count, R cover take; crest PASS. New for B14: safe-lane highlight after 3 crashes never shows (0 in 41 crashes); mid-air lane presses dropped; next-scene cover has no take number; 3 low/log-only items.
  - Soft-lock hammer PASS (10 Space/Esc/R tries, covers max 0.734 s, 0 'still loading').
  - FXAA motion check FAIL (narrow) -> TAA stays; the hub closed the AA question.
  - A3 sweep DONE (runner 12 report `C:\Dev\legion-b10\a3-sweep.md`, lead journal 21:56): 60/60 S1+S2 runs wrapped, exit 0, 0 stuck or timeout, P1 0 crashes. One bug, bot only (hub 142, 22:00): in `-JCFullRunTest -JCJitter=<s>` runs the bot never takes the free must-cut at 0 film on S1-4 and S2-4 (`CRASH stunt=4 take=2 free=0 T=14.50`, then take=3 and a `CUT time jump`); a human gets the CUT: FREE prompt. FIX-4 fixes the bot after JUMPCAM, only if time is left. (An earlier version of this line said "no result by 21:52"; the real clock then was about 21:37.)
  - Perf baseline (runner 12 `b13b-perf-baseline.md`, relayed by hub 142 at 22:3x; native 1920x1200, TAA, 3 runs x 2 takes per scene): S1 frame 16.57 ms (16.40-16.88), GPU 12.91 ms, 1% low 29.1 fps (27.7-30.5), 3.3 hitches over 50 ms per run (opener landing, canal-lip render-target stalls, 1 font flush; the B14 pre-warm targets these); S2 frame 17.06 ms (16.77-17.23), GPU 13.48 ms, 1% low 37.1 fps (35.4-39.0), 0 hitches. Friday kill lines are relative to the B14 baseline on the same runner setup: drop the last-landed item if S1 or S2 average frame rises more than 1.0 ms, 1% low falls more than 3 fps, or hitches over 50 ms rise by 2 or more per run.
- **Safe build = B13b** (21:28 PT, replaces B12): `safe-builds/B13b/SecondUnit_JumpCut_B13b_safe.zip`, 493,795,852 bytes, sha256 `97dc17beda9228cd246886dd9ec37805e1f3ca680ac5b8bb82cb66d0e3de902c`, with BUILD.txt and SAFE.md; `CURRENT.txt` points at it. Legion copy `C:\Dev\megajam-game-b13b` kept. Needs no trims.

## B13c (2026-11-12/13, not pushed)
- Contents: dv.commit.106, label in the commit message `B13c (no-boxes UI + Director's Cut + mercy reel + safe lane + air-press buffer + plywood ramps + fixes)` (40 files). FIX-4/FIX-5: SAFE LANE highlight after crashes, MERCY reel after 2 crashes in a shot + FRESH REEL stamp, Director's Cut slate (cover + clapper sound), air-press buffer (a lane press in the air applies at touchdown), MARK signs hidden on restored stunts and on the wrap card, test-only `-JCShotAtT`. UI-4: no-boxes UI (`jc.UIStyle 0` = old boxed look), CUT HERE alone on the crash-rewind frame, HOLD SPACE TO LOOK hidden at 0 film and while a stamp is up, title and retake slates, keyboard/mouse and pad both reach play, pause and quit. HUD-5 text-diet fix for the airborne and wrap screens. ROAD-3 water plane at -350 + plywood ramps (`T_Plywood_BC`, `M_/MI_Ramp_Plywood`, Poly Haven row in `sourced-assets.csv`). Rodin water tower moved from `Staging/Hold` to `Meshes/Props` (AI-generated, `asset-pipeline-log.csv` rows from PR #191). `Slate.MaxFontAtlasPagesBeforeFlush` 4 -> 8 (runner 12 font-atlas fail).
- Desktop proof before the freeze (lead journal 22:39 to 23:37, each frame viewed by the lead): mercy fires once per shot and not with `-JCMercyCrashes=0`; Director's Cut take WRAPPED 23.5 s cuts=1 film=6 stars=3; air-press buffered 3 of 3 takes, applied on the landing frame; restored-stunt and wrap-card MARK frames clean; UI-4 720p + 1080p proofs; in-game shot flags all fire (FIX-5 `flags.log`). Gate run: WRAPPED T=28.50 cuts=6 (FIX-5 `clean_gate.log`).
- Not in B13c (parked for B14): PREWARM, JUMPCAM, the A3 bot fix. So B13c still has the old bot: 2 crashes + 1 mercy reel per `-JCFullRunTest` gate run are expected, not bugs.
- Freeze 23:38 PT (early, hub 142: all items proven), snapshot synced 23:40:21, staged 23:45:01 (sync 1.8 + package 2.9 = 4.7 min) to `C:\Dev\megajam-game-b13c\megajam-game\Packaged\Windows`; BUILD.txt `dv.commit.106 synced 2026-11-12 23:40:21 staged 2026-11-12 23:45:01`; vc_redist x64 present.
- Tests (runner 13 `legion-20261112-223240`, GO sent 00:04 with the checklist: label gate + exe-strings scan, then H1 economy/DCut/mercy, H2 perf/font/720p/UI, H3 break-it + soft-lock, incl. mashing Start/A during the boot ident for the Slate `RenderBatch.NumIndices > 0` assert seen on the desktop with a test-only flag combo):
  - Gate PASS 00:07: BUILD.txt matches the GO line, 832 files / 796,647,970 bytes on 2 reads, no `Saved` dir, vc_redist x64; exe strings confirm `-JCGainWide=`, `-JCMercyCrashes=`, `-JCNoFilmTest` and the Director's Cut restore/clap lines (`b13c-accept.md` on the Legion).
  - H1a PASS (00:25): bot timeline same as B13b (WRAP T 28.51, with the expected old-bot 2 crashes + mercy reel); scripted plan wraps 2/2 with no re-time; wide = +0 film, S1-4 must-cut FREE, film at mark 4 = 3-5; Director's Cut PASS (C starts it, slate + clapper `SW_Jam_Crash_Clapper`, restore=[1], wraps, N -> Scene 2, 0 asserts). Low bugs for B14: 17 HUD glyph warnings per launch (`JC hud: glyph InputPrompts/keyboard_space missing, text fallback`; the HUD loads the Kenney glyphs by path string, so they were never cooked; 0 in B13b); the build banner still says B13b (the `[JumpCut.Build]` label was not bumped; the B13c label is only in the dv commit message); next-scene cover still has no take number (open since B13b). Judge call to hub 142: the DCut slate box is bigger (888x240 vs 826x192 px) but its headline caps are smaller (48 vs 55 px). FYI: the DCut take scored 4 stars at 9 points vs take 1 3 stars at 10 points (FIX-8 checking).
  - H1b (~00:5x): MERCY PASS (+1 once per shot, a later shot gets its own); mid-air lane press PASS 6/6 (applied at touchdown); SAFE LANE PASS on the static stunts S1-1/S1-2 (incl. strict 0 film) but FAIL on the timed-dodge stunts S1-3/S1-6 (the cued lane is the one that gets hit: `safe lane highlight lane=2` -> `CRASH stunt=3 T=11.00`); CUT: FREE FAIL (the 0-film `[SPACE] CUT: FREE` prompt is gone on the box-free HUD, a regression vs B13b; the free cut itself works and wraps; also no cut prompt at film 2 on S1-4); low: `A/D: CHANGE LANE` hint shows during the S1-4 must-cut window. 8 launches, 0 asserts or crashes. Hub 142: both MEDs are B14 MUSTs (FIX-9 safe lane at arrival time, or no SAFE LANE on timed stunts; UI-5 CUT: FREE). Test note: `-JCNoFilmTest` cannot hold 0 film (a crash rewind restores the mark's film); `-JCStartFilm=0` works.
  - H2a perf (native 1920x1200, TAA): S1 FLAG, frame 16.84 ms (16.78-16.91) vs B13b 16.57, 1% low 26.7 (25.8-27.3) vs 29.1, hitches over 50 ms 4.3 vs 3.3 per run; cause: the Slate font cache still flushes (`Large atlases out of space; 9/8 Textures`, 51-63 ms each, S1 1-2 per launch); 1% low 28.3 without it. S2 PASS: 16.40 vs 17.06 ms, 1% low 35.8 vs 37.1, 0 hitches. Opener-landing stall unchanged (59.6 vs 59.3 ms). One new 63.3 ms render-thread stall at S1 T 17.49. B14 fix (hub 142): `MaxFontAtlasPagesBeforeFlush` 8 -> 16 plus a font pre-warm under the cover.
  - H2b look/UI: 720p colour PASS on Windows (B/R within 1.3% of native; the blue tint was the Linux off-screen path only), no panel boxes PASS, menu/pause/call sheet/wrap card fit PASS at 1080 + 720, plywood walls and canal PASS, jump cam partial. Bugs: MARK world sign slides under PTS and exits cut to "MAR"; PERFECT stamp overlaps HOLD NOW; RELEASE hint off-screen at 720p; pause leaves `[SPACE] LOOK`; canal corkscrew jump cam cuts the car (B13c has no JUMPCAM fit).
  - H3 break-it (21 launches, 0 crashes): soft-lock PASS (10 tries, max cover 0.81 s), Slate boot-mash assert PASS 3/3, ramp crash walls and opener lane hint fixed, keys PASS (play, pause, restart, quit). FAIL: Space held into the S1-4 must-cut window never cuts (crash loop; the fix line never logs; SendInput holds have no key-repeat, so a real-keyboard check is due); Space held from the title is eaten by the menu; CUT HERE VO dropped on the first pass of S1-4 (regression: the S1-3 result VO wins by 0.19 s); mouse clicks on title/pause buttons do nothing (SendInput; real-mouse check due). Low: a key during boot skips the title; still open from B13b: S2 as first map has no title, keyboard Perfect has no rumble, S2 tier labels. Pad: SKIP (needs a human on the built-in pad).
  - Summary (runner 13, 48 launches, 0 app crashes, 0 asserts; Legion `C:\Dev\legion-b10\b13c-accept.md`): PASS economy, scripted plan, Director's Cut chain, mercy, mid-air lane, S2 perf, 720p colour, no boxes, ramp walls, soft-lock, Slate assert, keyboard controls. FAIL held Space x2, CUT HERE VO, CUT: FREE, timed safe lane, S1 1% low, MARK/PERFECT/RELEASE layout, mouse on menus.
- Verdict (hub 142, 2026-11-13 02:27 PT): NOT the safe build. **B13b stays the safe build**; B13c is the base for B14. The human keyboard, mouse and pad checks move into the Fri 14:00 fun test and the owner's 07:52 pack (not a separate owner card).
- B14 fixes from these results: CUT: FREE at 0 film (UI-5; root cause: the look/cut hint row collapsed while the unseen first-hold teach line was pending, not the glyphs) and timed safe lane (FIX-9 `SafeLaneAt` + UI-5 HUD cue), both accepted by the lead 02:28 (desktop stills + gate S1+S2 exact + follow-the-cue bot passes S1-3/S1-6/S2-5/S2-6); font flush 8 -> 16 + font pre-warm, RELEASE at 720p, PERFECT/HOLD NOW overlap, pause hint (UI-5); MARK sign distance fade (FIX-10); held Space at the must-cut window and from the title, menu mouse clicks, CUT HERE VO priority (FIX-11). Proof for all of them is the Legion B14 run.
