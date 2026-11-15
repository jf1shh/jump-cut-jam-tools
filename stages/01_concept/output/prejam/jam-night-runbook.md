# Jump Cut: jam-night runbook (Wed Nov 11 21:00 to Thu Nov 12 01:00 PT)

2026-11-11, written before the contest window opens. **Planning text only (Rule 7(h)):** nothing below exists before Wed
21:00 PT, and no class, script, asset or level is made from this file until then. [`../gdd.md`](../gdd.md) wins over
this file; the pack index is [`README.md`](README.md). Generic rules not repeated here (GPU gate, memory scopes, merge
rule, overnight cards, recovery) are in
[`jam-execution-plan.md`](../../../00_prep/references/jam-execution-plan.md),
[`jam-day-runbook.md`](../../../00_prep/references/jam-day-runbook.md) and
[`jam-recovery.md`](../../../04_ship/references/jam-recovery.md).

**Data names:** data asset fields are named here by their GDD and README terms. The exact class and field names are in
`data-schema.md` (this folder, pending PR); where the two differ, `data-schema.md` wins. The greybox layout
for Scene 1 is the parallel greybox spec in this folder; tonight needs only its first stunt, S1-1.

**The night in one line:** all C++ in one compile (no Live Coding on the Linux editor, GDD §8), then data assets, then
the greybox, then a package on the Legion. The 01:00 gate checks plumbing only and cannot kill the concept (GDD §9).

**Who:** **Owner** (awake to 01:00; plays, tunes by hand, makes the calls). **Lead** (the `proj start megajam` loop
session; the only Unreal MCP caller; writes the contract, integrates, compiles, packages). **Helpers A, B, C** (file-only
C++ writers; lead + 3 is the 4-worker cap). `<Game>` = the `.uproject` name picked at 21:00. Class names with the `JC`
prefix are proposals.

## 1. Timeline

| Time (PT) | Who | What | Done check |
|---|---|---|---|
| 20:45 | Hub | Local models off (owner 2026-11-11: no local AI in the jam), `gpu-preflight` CLEAR, `proj list` shows no other loop | CLEAR, no loop running |
| 21:00-21:15 | Owner | `HANDOFF_MAX_RESTARTS=300 proj start megajam` | `proj list` shows `megajam` busy |
| | Lead | `jam_clock.py start`; `jam_start.py <Game> ~/Projects/megajam-game` (project, config, `IDENTITY.md` and `CONTEXT.md`, jam-path file); remove `TargetAllowList` from the MCP plugin entry (runbook step 2, plan G4); first `dv commit -a` | `jam_start.py` reports every step OK; `dv status` clean |
| 21:15-21:35 | Lead | **The contract** (section 2, last table): add the `Modules` entry to the `.uproject`; module skeleton (`Build.cs` with Enhanced Input and UMG, the game and editor `Target.cs`); the shared types header (lanes, tiers, hold states); the four data asset classes; every public header in section 2 with empty bodies. **Config before launch** (section 4): global default game mode `JCGameMode`, one Asset Manager entry per data asset type, MCP port 8010 pin. **Map lines:** in `Config/DefaultEngine.ini`, section `[/Script/EngineSettings.GameMapsSettings]`, remove the two `L_MainLevel` lines `jam_start.py` wrote (`EditorStartupMap`, `GameDefaultMap`: the `new-mock-project.py` template default, since `jam_start.py` passes no `--level`) and the template's two comment lines above them, and add no `L_Scene01` lines yet: that map does not exist until 23:15 and package A cooks against this ini | All headers and ini edits on disk; the lead ticks each class against section 2 |
| 21:35-21:50 | Lead | Compile the skeleton once: UBT `Build.sh <Game>Editor Linux Development` with `-Project=` the `.uproject`, in its own scope like the editor. The toolchain is proven: mock 17 compiled a C++ editor target on this 5.9 tree today (24 s cold, 4-8 s incremental) | Exit 0. Still red at 22:15: bail rule B1 |
| 21:35-22:20 | Helpers A, B, C | Write class bodies in `~/Projects/megajam-game/work/cpp/<A, B or C>/` (`work/` is ignored by Diversion, so a half-written file never reaches a compile or a commit). A: scene clock and road. B: car pawn and cut component. C: stunt, determinism test, run recorder. Each works from its slice brief (section 3) and the contract headers; a helper that needs a header change asks the lead, never edits it. If the headers run 10 min late, helpers start anyway on the pure maths (box distance, pose curves, lane geometry) from the section 2 prose | Each helper hands over a file list plus every contract call it uses |
| 21:40 | Owner | Legion on, plugged in, idle lock off, built-in pad in its normal mode | Lead's `legion_preflight.py` passes |
| 21:50-22:20 | Lead | File-only: `JCGameMode` and `JCHudWidget` bodies; two editor Python scripts in this repo's `scripts/` (data and input assets; the `L_Scene01` greybox). Each script saves what it makes and is safe to re-run (it replaces by name) | Both scripts pass `py_compile` |
| 22:20-22:40 | Lead | Copy helper files into `Source/<Game>/`; full editor-target compile; fix errors (or hand an error back to its helper) | Exit 0 |
| 22:40-22:50 | Lead | Headless determinism test on the code-only test stunts: `UnrealEditor-Cmd` with `-ExecCmds="Automation RunTests <Game>.Stunt;Quit" -unattended -nullrhi -nosplash`; `dv commit -a` | Every test passes, including the check that catches the deliberately bad stunt. The `-nullrhi` process has exited before the 22:50 editor launch (a second engine process costs memory, not GPU) |
| 22:45 | Lead | **Package A**, in the background: `legion_ship.py <uproject> --engine C:\Dev\UE_5.9` (pretest target, no ask). C++ and config only, no map yet. It proves the MSVC compile, cook, stage and exe check for a code project; the content-only packaging tips no longer apply (canon `jam-packaging-windows`) | Ship log ends OK. Budget about 10-20 min, worst case 69 min (mock 17: a C++ project packaged on the Legion in 69.0 min cold, including the one-time 5.9 game-target engine compile, then 4.8 min incremental; exe check PASS) |
| 22:50-23:00 | Lead | `gpu-preflight`; `scripts/launch-editor.sh <uproject>` (own scope; waits up to 300 s for :8010). With no map lines the editor opens on the engine `OpenWorld` template: never save it; the greybox script makes `/Game/Maps/L_Scene01` with `new_level` | :8010 answers; `mx.py toolsets` lists toolsets |
| 23:00-23:15 | Lead | MCP call: `mx.py py` the data-asset script: `DA_Tuning` (the one tuning asset), `DA_Scene_01` (S1-1 only tonight), `DA_Car_Number7`, the input actions and `IMC_Default` for both devices | The script prints each asset, every key mapping, and the Asset Manager count per type |
| 23:15-23:35 | Lead | MCP call: `mx.py py` the greybox script: `L_Scene01` with the road, a floor strip, one light and sky, a player start. Stunts come from `DA_Scene_01`, not from placement. Then `force_save_level.py --expect-actor JCRoad` and `mx.py shot greybox`. Once the level is saved, write the map entries to the ini: `EditorStartupMap` and `GameDefaultMap` = `/Game/Maps/L_Scene01` in `DefaultEngine.ini` `[/Script/EngineSettings.GameMapsSettings]`, and `+MapsToCook=(FilePath="/Game/Maps/L_Scene01")` under `[/Script/UnrealEd.ProjectPackagingSettings]` in `DefaultGame.ini` (the Legion cooker reads the ini, so no editor restart) | VERIFIED; the shot shows the road, S1-1's cube and marks 0 and 1 (look at it) |
| 23:35-00:00 | Owner (lead reads the log) | Play in editor on keyboard and mouse: drive, change lanes, hold, release, cancel, crash into S1-1, cut over S1-1. Tune `DA_Tuning` by hand where the feel is off | Each verb works once; the lead writes the fix list |
| 00:00-00:15 | Owner | Dev log entry (15 min; `gen_devlog.py --dry-run` draft) | Entry drafted |
| | Lead | Data fixes in place. A C++ bug gets one restart cycle now (save, VERIFIED, close, compile, relaunch: about 10 min, bail rule B10). Then the determinism test on `DA_Scene_01` in the open editor (`mx.py py` runs the automation command) | Test green on real data |
| 00:15-00:20 | Lead | `force_save_level.py` VERIFIED; `dv commit -a`; **Package B** (same command) once A has finished | B started by 00:30; at about 5 min incremental (mock 17: 4.8 min) it is ready to play by 00:40. Not started by 00:35: bail rule B9 |
| 00:20-00:40 | Lead | Grep `Source/` for on-screen debug calls; night log line; N1 inputs (fix list, what slipped, any planned restart) | N1 inputs written |
| 00:40-00:55 | Owner | On the Legion: start build B from the staged folder; answer the Windows Firewall prompt once; play S1-1 with the built-in pad only: lanes, hold, cut, cancel, crash | Each works on the pad |
| 00:55-01:00 | Lead, owner | Gate call (below); the lead flags the result; the owner approves the N1 card and sleeps | Gate line in the night log |

**Thu 01:00 gate (GDD §9, plumbing only)**

| Item | How it is checked | Who |
|---|---|---|
| Project packages on the Legion | Package A or B: the ship log ends OK and step 3 finds `Binaries\Win64\<Game>.exe`; B launches into `L_Scene01` | Lead |
| Car on the spline | PIE and build B: the car follows `JCRoad` from mark 0 at the Scene 1 base speed | Owner |
| One stunt | S1-1 (Leaning False Front, T 7, easy): the front falls across C and R; driving L passes it; staying in C crashes back to mark 0 | Owner |
| Hold, cut, cancel on both inputs | Keyboard and mouse in PIE on the desktop; the pad on build B; the data script's printout shows every action on both devices | Owner |
| Determinism test green | On the code test stunts (22:40) and on `DA_Scene_01` (00:15) | Lead |

Fail: fix plumbing; N1 stays on plumbing (plan §4); no concept change (GDD §9).

## 2. The C++ classes (all land tonight)

**Rules for every class**

- Every number is a data asset field (a UPROPERTY), never a literal in code (GDD §4, §8).
- Gameplay runs on **scene time T** from the clock. Only the hold cap and hit-stop count real time, since they must not
  slow down with the world. World timers slow with time dilation, so neither uses them (engine behaviour; confirm in
  slice 1).
- No physics simulation, no Chaos vehicle, no random numbers in gameplay, no Timelines, no Tick in Blueprint children.
- No class names a specific car, scene, stunt or modifier (GDD §8 "Content is data"). Data assets are found through the
  Asset Manager by type.
- Every event another system needs is a Blueprint-assignable delegate, so HUD, audio and juice get wired in Blueprint
  on Thursday without touching C++.
- Anything Thursday or Friday will need from C++ goes in tonight's compile, even if nothing uses it yet. Those are the
  "Hooks" lines below.

### Scene clock (`UJCSceneClock`, a ticking world subsystem). Helper A

- **Job:** the one source of scene time T and of the scene's progress. T advances by world delta (so the 0.3x hold
  slows it), stops during hit-stop, jumps forward to the landing mark on a cut and back to the previous mark on a crash.
  Each frame it pushes T to every stunt and asks the active stunt for contact and closest approach.
- **Owns:** T; the active scene data; the runtime stunt list in scene order; mark times; the film ledger (film now, the
  film and lane snapshot at each mark, take count, crashes per stunt, the shot result per stunt); the stars sum at
  wrap. Film lives here because a crash restores T and film together (GDD §4: back at the previous mark "with film at
  that mark's value").
- **Reads:** scene data: level, ordered stunt list, speed curve f(T) (base speed, surge). Tuning: reel size, film at
  scene start, cut cost, MustCut cost, kept-shot gains (Wide, Close plus bonus star point, Perfect), near-miss bands,
  mark offset, grade points, star thresholds, take caps, safe-lane help after n crashes. The active modifier's
  overrides, if one is set.
- **Sends:** time jumped (from, to, reason); film changed (old, new, reason); mark passed (k); shot kept (stunt, tier,
  real gain); crash (stunt, take, free or not); wrap (points, stars); phase changed (slate, rolling, wrapped).
- **Never:** reads input; moves the car itself; poses hazards except by calling the stunt's evaluate; seeks or slows the
  music; uses wall-clock time for T; writes to disk.
- **Hooks:** set T for a replay start; a "restored" flag per stunt that turns its mark off (Director's Cut take); the
  free first crash keeps TAKE 1 (README 10); the film cap clamp reports the real gain, "FILM FULL" (README 9); at 0
  film a non-MustCut press is NO FILM and a MustCut can still be cut (README 8); wrap at the last stunt's mark (README
  11); D(T), the road distance at any T (replay, ghost car, mark placement).

### Road (`AJCRoad`). Helper A

An actor whose spline is the drive line, with lane count and lane width from tuning. Each scene level has exactly one;
the clock and the car find it by class. It turns (D(T), lane) into a world position. It never moves at runtime and holds
no game state.

### Stunt (`AJCStunt`, the one authored stunt type, GDD §1). Helper C

- **Job:** a hazard whose pose is a pure function of T. Evaluate at T sets its hazard parts; the same T gives the same
  pose every time, in any call order.
- **Owns:** its hazard parts (components built from its data); its mark (the gaffer-tape strip and clapper sign,
  placed at the mark's road distance); its key light and telegraph state.
- **Reads** (its entry in the scene's ordered stunt list): collision-on T and collision span; telegraph lead (2.5 s);
  the drivable line (which lanes are blocked when); execution tier; shot value; near-miss band (or the tuning default);
  MustCut flag; danger lane (for the deleted-scene ghost car); replay angle; hazard parts with their pose curves. Its
  road position comes from T through D(T), never from hand placement.
- **Answers:** blocked lanes at T; the closest distance from a car box at (lane offset, T) to its hazard boxes, by box
  maths, not physics queries; cut window open at T (from telegraph start to collision-on); safe lane at T.
- **Never:** Tick (the base turns it off; children add no Tick, Timelines, physics or randomness); reads the car, input
  or film; changes its own data at runtime.

### Car pawn (`AJCCarPawn`). Helper B

- **Job:** the player's car. Its forward position is D(T) on the road (speed is fixed per scene as f(T)); the player only
  picks lanes. Binds Enhanced Input for both devices from the first greybox.
- **Owns:** the live lane and lane-change progress (a function of scene time since the input, so replays match); the
  chase camera; the engine-rev FOV kick (cosmetic); canned crash flip playback (three variants, README 18); the cut
  component.
- **Reads:** car data: mesh, livery, numbers (lane-change time, camera offsets, FOV kick, wheel spin). Tuning: lane
  width. Input actions and mapping context from a data asset field (see `data-schema.md`), never a hard-coded path.
- **Sends:** lane changed (T, lane); rev pressed; pause pressed.
- **Never:** physics movement; T from anywhere but the clock; a live lane change during a hold (lanes set the landing
  lane then, GDD §2); its own crash detection (the clock asks the stunt); film.
- **Hooks:** lane source = player, playback (from the recorder) or scripted (one fixed danger lane: the deleted-scene
  ghost car); place at (T, lane) for a cut, a crash restart or a replay start; auto-pause on pad loss or focus loss
  (README 13; tonight, check whether Blueprint has a node for it, else bind it here).

### Cut component (`UJCCutComponent`, on the car). Helper B

- **Job:** the core verb. Hold to look, release to cut, cancel to keep driving (GDD §3).
- **Owns:** the hold state (idle, holding, cut, cancelled, auto-cancelled); the real-time hold timer; the ease to 0.3x
  over 150 ms and back; the landing lane picked during the hold; the one SceneCapture for the landing inset (runs only
  while held); the cut sequence (hit-stop, ask the clock to jump, one black splice frame, punch-in). It is **the only
  class that sets global time dilation**: the clock asks it for the crash hit-stop too.
- **Reads:** tuning: hold time scale (0.3), ease time (150 ms), hold cap (1.5 s), cut hit-stop (60-80 ms), crash
  hit-stop (120 ms), splice frames (1), punch-in (5%). From the clock: T, whether a cut window is open, the next mark
  and its T, film, MustCut.
- **Sends:** hold started; hold ended (cut, cancel, auto-cancel, window closed, paused); cut (from T, to T, mark,
  landing lane); NO FILM pressed.
- **Never:** auto-cuts (the cap only cancels, GDD §3); spends film itself (it asks the clock); steers the live car; runs
  the SceneCapture outside a hold; touches the music; uses time dilation for anything but the hold and hit-stop.
- **Hooks:** pause cancels the hold (README 13); a safe-lane highlight flag for the inset after three crashes on one
  stunt (GDD §4); the DRIVE IT state when the window closes during a hold (README 7); hazards near the landing drawn at
  the arrival time (GDD §3). If that last one needs posing stunts twice in one frame and it does not work tonight, see
  bail rule B4.

### Run recorder (`UJCRunRecorder`, a game-instance subsystem, so it lives across the scene levels). Helper C

- **Job:** a log of what the player did, in scene time, so the wrap clip, the deleted scenes and the Director's Cut take
  can re-run a scene (GDD §6).
- **Owns:** per scene: lane inputs (T, lane); holds (start T, end T, how they ended); cuts (from T, to T, stunt);
  crashes (stunt, T); the shot result per stunt; the cut-stunt list. Playback of the scene's final take (what the
  player kept, not the crashed attempts) into a car whose lane source is playback.
- **Reads:** only the events of the clock, the car and the cut component.
- **Answers:** cut stunts in order; the deleted-scene pick (a cut MustCut first, else the highest-tier cut stunt, latest
  wins; README 5); the stunts to restore for the Director's Cut take.
- **Never:** records transforms per frame (poses come back from T); records wall-clock time; writes to disk (saves are
  out of scope, GDD §4); drives the live game outside playback.

### Small classes in the same compile. Lead

| Class | Job |
|---|---|
| Data assets: `UJCTuningData` (one asset), `UJCSceneData`, `UJCCarData`, `UJCModifierData` | Primary data assets, one Asset Manager type each, fields per `data-schema.md`. No modifier asset exists tonight; the class and the override path do |
| `AJCGameMode` | Default pawn = the car; spawns the HUD widget; runs `DisableAllScreenMessages` at start (GDD §8); finds the scene data whose level is open. Set as the global default game mode in config, so it needs no MCP wiring |
| `UJCHudWidget` | The C++ base for `WBP_HUD` (slice 4). Listens to the events above and re-sends each as a Blueprint event; owns no layout. With no designer tree it draws one fallback text line |
| Test `<Game>.Stunt.Determinism` | Slice 2 |

### The contract (lead, 21:15-21:35; helpers write against it)

| Caller | Calls | When |
|---|---|---|
| Car pawn (input) | Cut component: begin hold, release, cancel, landing lane left or right | Hold, Cancel, Lane input |
| Cut component | Clock: cut window open?, next mark and its T, try to spend a cut (false at 0 film unless MustCut), jump to a mark | Press and release |
| Clock | Stunt: evaluate at T, distance to a car box, blocked lanes, cut window. Car: place at (T, lane), play crash. Cut component: hit-stop for n ms | Every frame; on a crash |
| Run recorder | Listens only. In playback: sets the car's lane source and asks the clock to jump at the recorded cut times | Always |
| HUD base | Listens only | Always |

**On a cut:** release, the cut component asks the clock to spend a cut; if yes: hit-stop 60-80 ms real time, the clock
jumps T to the mark (time jumped, film changed), the car is placed on the mark in the landing lane, one black splice
frame and the punch-in, and the recorder logs the cut. A press at 0 film on a non-MustCut stunt sends NO FILM and opens
no hold.

**On a crash:** the stunt reports contact; T stops; 120 ms hit-stop; the car plays its flip; the clock jumps back to the
previous mark and restores that mark's film and lane; take +1 (not for the free first crash on S1-1). Control is back in
under 1 s (GDD §4).

## 3. Slice briefs

From [`feature-slice-brief.md`](../../../../_config/reference/templates/feature-slice-brief.md). Tonight each slice
means "the C++ is in the one compile and the done-test passes on greybox"; juice, art and audio are Thursday.

### Slice 1: cut component and hold

- **One-paragraph brief:** Helper B writes the cut component (section 2) 21:35-22:20; the owner tests it 23:35. It adds
  the hold (time eases to 0.3x, a black-and-white look, the landing inset from one SceneCapture), release-to-cut (hit-stop,
  one black frame, punch-in, the car lands on the next mark in the chosen landing lane, film -1) and cancel. Tonight's
  look can be a plain desaturate post; the workprint overlay, sound and grain come Thursday.
- **Done-test:** in PIE, drive at S1-1; once its telegraph starts (T 4.5) hold Space: the world slows to 0.3x and the
  inset shows mark 1. Press D: the inset's landing moves to R and the live car stays in C. Release: a short freeze, one
  black frame, the car sits on mark 1 in R and film reads 2. Restart, hold, wait: it cancels itself after 1.5 s of real
  time with film unchanged. Hold and press Shift: full speed again, film unchanged. Same on the pad (A, stick, B) on
  build B.
- **Touches:** `Source/<Game>/JCCutComponent.*`; the input binding in the car pawn (same helper); hold fields on
  `DA_Tuning` (the owner tunes).
- **Playtest note:** (fill in after the done-test)
- **Commit:** (Diversion commit id)

### Slice 2: Stunt and the determinism test

- **One-paragraph brief:** Helper C writes `AJCStunt` and the test. Pose is a pure function of T; contact and closest
  approach use box maths; the stunt places its own mark. S1-1 is data in `DA_Scene_01`: one cube that tips across C
  and R between T 4.5 and 7. The test, for every stunt in every scene data asset plus two code-only test stunts:
  evaluate at T, at T + Δ, at T again and at T + Δ again, and the same in a fresh second instance; all poses must
  match. A last check feeds the comparator a deliberately bad test stunt (its pose depends on call count) and passes
  only if the comparator catches it. It runs headless before the editor opens and in the editor before every package
  (GDD §8).
- **Done-test:** run `Automation RunTests <Game>.Stunt`: everything passes, including the bad-stunt catch and S1-1. In
  PIE stay in C: the front lands across C at T 7 and the car crashes back to mark 0 and TAKE stays 1 (the free take, README 10).
- **Touches:** `Source/<Game>/JCStunt.*`, `Source/<Game>/Tests/JCStuntDeterminismTest.cpp`. Helper C supplies the S1-1
  values; the lead's 23:00 script creates and owns `DA_Scene_01`.
- **Playtest note:** (fill in after the done-test)
- **Commit:** (Diversion commit id)

### Slice 3: car pawn and lanes

- **One-paragraph brief:** Helper B writes `AJCCarPawn`. The car rides the road at D(T) in three lanes 4 m apart
  (starting value). Lane input comes from A/D, the arrows, the d-pad or the left stick. The stick is mapped as its
  digital left and right keys, so the mapping context needs no axis modifiers and the script can write it. The car also
  has a chase camera, the RT rev FOV kick and a placeholder crash roll. The greybox car is a box; the hero car is
  Thursday art.
- **Done-test:** press Play: the car rolls from mark 0 at the Scene 1 base speed (18 m/s starting value). Press A: one
  lane left within the lane-change time. Press A again in L: nothing. The d-pad and left stick do the same on build B.
- **Touches:** `Source/<Game>/JCCarPawn.*`; reads `JCRoad` (Helper A owns it); the lead's script makes `IA_LaneLeft`,
  `IA_LaneRight`, `IA_Hold`, `IA_Cancel`, `IA_Rev`, `IA_Pause`, `IMC_Default` and `DA_Car_Number7`.
- **Playtest note:** (fill in after the done-test)
- **Commit:** (Diversion commit id)

### Slice 4: HUD shell

- **One-paragraph brief:** the lead writes `UJCHudWidget` 21:50-22:20. The 01:00 gate needs no HUD shell, only a text
  line showing HOLD, CUT or CANCEL ([`hud-ui-spec.md`](hud-ui-spec.md) §8). So tonight is the C++ base and its
  fallback line. The base re-sends every gameplay event as a Blueprint event (film changed, hold started and ended,
  cut, shot kept, crash, NO FILM, time, take), so `WBP_HUD` stays layout and animation only. Thursday from 09:00: the
  `WBP_HUD` child in the spec's order (film counter, stamp, prompt, inset), plain UMG with explicit focus (GDD §8).
- **Done-test:** in PIE and on build B: hold Space and the line reads HOLD; release and it reads CUT and FILM 2; hold
  and press Shift and it reads CANCEL; crash and it reads CRASH. A grep of `Source/` finds no print-to-screen call.
- **Touches:** `Source/<Game>/JCHudWidget.*`, `Source/<Game>/JCGameMode.*`.
- **Playtest note:** (fill in after the done-test)
- **Commit:** (Diversion commit id)

### Slice 5: run recorder and replay

- **One-paragraph brief:** Helper C writes `UJCRunRecorder`: the event log and the playback calls. Replay cameras (one
  change per cut), the wrap clip, the deleted-scene ghost and the Director's Cut take are Blueprint work on Thursday and
  Friday, on top of the hooks compiled tonight. Two debug console commands (Development build): `jc.DumpRun` writes the
  log to the output log; `jc.ReplayScene` re-runs the final take from mark 0.
- **Done-test:** in PIE change lanes twice, crash once, then cut S1-1. `jc.DumpRun` shows the lane events, one crash,
  one hold and one cut, all in scene time. `jc.ReplayScene` puts the car on playback: it changes lanes at the same T
  values and lands on mark 1 in the same lane, and the log prints "replay mismatches: 0".
- **Touches:** `Source/<Game>/JCRunRecorder.*`.
- **Playtest note:** (fill in after the done-test)
- **Commit:** (Diversion commit id)

### Slice 6: packaging on the Legion

- **One-paragraph brief:** the lead runs the first Windows packages of the code project. Package A (22:45) proves the
  MSVC compile, cook, stage and step-3 exe check for a project with `Source/` (`Binaries\Win64\<Game>.exe`, no
  UnrealGame decoy). Package B (00:15) adds `L_Scene01` and S1-1 and is the gate build. Config: Development with "For
  Distribution" off (D-009); game default map, editor startup map and cooked maps = `L_Scene01`, written only after the greybox script saves (never
  before package A); `DisableAllScreenMessages` at start.
  Before each package: determinism test green, `force_save_level.py` VERIFIED, `Source/` grepped for print-to-screen.
  Thursday, not tonight: PSO cache, the title-screen prewarm, the `-clearPSODriverCache` first-run test, default
  scalability Medium (GDD §8). No edits to `legion_ship.py` or `package-and-push.ps1` (tooling is frozen).
- **Done-test:** on the Legion, start build B from the staged folder: `L_Scene01` loads (not black), the car drives
  from mark 0, and the built-in pad's A holds and cuts over S1-1.
- **Touches:** `<Game>.uproject` (`Modules`, MCP entry); `Config/DefaultEngine.ini` (maps, game mode);
  `Config/DefaultGame.ini` (packaging, Asset Manager); the ship logs.
- **Playtest note:** (fill in after the done-test)
- **Commit:** (Diversion commit id)

## 4. What goes where: C++, config, scripts, MCP, hands

MCP calls are serial and slow (5-15 min a response, GDD §8), so MCP does placement and wiring only. Tonight's budget is
about **seven calls**: the data-asset script, the greybox script, `force_save_level.py` twice, one shot, the in-editor
determinism test, and one spare.

| Work | Goes in | Why |
|---|---|---|
| Rules, timing, state, maths: clock, film, tiers, near-miss, hold, cut, crash, the run log, stars | C++, tonight only | No Live Coding on Linux; many branches; reviewable in a diff (CLAUDE.md) |
| Every number anyone may tune | Data asset fields; the owner tunes by hand in the editor | No recompile, no MCP call |
| Project settings: maps, game mode, Asset Manager types, MCP port, cooked maps, packaging | Ini files, written **before** the editor opens; the map entries right after the greybox saves | Zero MCP calls; most ini changes after launch need a restart (the map entries do not: the Legion cooker reads them) |
| Making many assets or actors: data and input assets, the greybox level, later the rest of the stunt roster | One editor Python script per batch, run with one `mx.py py` call | One call instead of dozens; re-runnable |
| Small wiring and checks: one property, one class default, `mx.py shot`, `force_save_level.py` | Single MCP calls | Each is one round trip |
| Feel and input tuning; "does it feel good" | The owner, by hand | Faster and better than any agent loop |
| Blueprint graphs | Thin glue only: a widget's layout and animation, a Blueprint child picking a class | Big graphs are slow to build over MCP and hard to review (CLAUDE.md) |
| Never over MCP | Per-actor placement loops; Blueprint logic over a handful of nodes; anything one script could do in one go | |

## 5. Bail rules for jam night

The 01:00 gate time never moves; a block that overruns by 15 minutes takes its bail rule.

| # | Block | Signal | Do this instead |
|---|---|---|---|
| B1 | Skeleton compile (21:35) | Still red at 22:15 | The toolchain is proven (mock 17 built a C++ editor target on this tree today), so look at our module first: `Build.cs` dependencies, the `Modules` entry, the `Target.cs` names. Same bail otherwise: the lead shows the owner the error; the owner calls it by 22:30: keep fixing on 5.9, or recreate the project on 5.8.4 (`UE_VERSION=5.8`, copy, never convert; package with `--engine C:\Dev\UE_5.8`). No content exists yet, so a switch costs about 20 min |
| B2 | Merge compile (22:20) | Errors after 20 min | Stub the failing bodies (every header and contract call stays), compile, go on. The real bodies land in **one** planned restart at the start of N1 (01:00-01:30), never dribbled through Thursday |
| B3 | Helpers (22:20) | A helper is not done | The lead stubs that part (B2); the helper keeps writing in `work/` for the N1 restart |
| B4 | Inset (slice 1) | Inset not right by 23:50 | The gate needs only the slow-down, the black-and-white look and the cut; the inset moves to Thu 09:00. If drawing hazards at the arrival time fails, draw them at their live pose: with the storyboard spacing the next stunt is still at rest when you land, so only the two long MustCuts look different |
| B5 | Editor launch (22:50) | Exit 8 or 9, or no :8010 in 300 s | Wait until `ss -ltn` shows no 8010, retry once. Second failure: copy `Saved/Logs` and `Saved/Crashes` to `stages/04_ship/output/crash-logs/<stamp>/`; the owner opens the editor by hand; the lead does file-only work |
| B6 | Any MCP call | Over 15 min | The owner runs the same script from the editor's Python menu (File, Execute Python Script); the lead only checks with `force_save_level.py` and a shot |
| B7 | Data or greybox script | Fails partway | Fix the script and re-run it; never patch with single MCP calls. If curve keys cannot be set from Python, the owner keys S1-1's one curve by hand (about 2 min) |
| B8 | Package A | Fails on MSVC | Fix the source for Windows; check it on Linux with a **game**-target build (`<Game> Linux Development`, which leaves the open editor's modules alone); re-run `legion_ship.py`. No editor restart for a Windows-only fix. A second failure leads the N1 report and the N1 07:30 package tries again |
| B9 | Package A or B | A not done, or B not started, by 00:35 | Skip B tonight. The "packages" item is A's log; the pad test moves to N1's 07:30 package, played at 08:30 Thursday; the keyboard items stand from PIE |
| B10 | PIE play (23:35) | A C++ bug | One restart cycle at 00:00 (about 10 min). A second C++ bug waits for the N1 restart; work around it in data where you can |
| B11 | Determinism test | Red | Never package with it red. Fix the stunt's data first (it is data); a wrong test gets fixed in the N1 restart and N1 packages |
| B12 | Recorder (slice 5) | Late | Keep the log; the playback body can be a stub (the header stays). Replay is Thursday-Friday work anyway |
| B13 | HUD fallback line | Late | No line tonight; the owner reads the states from what happens on screen. Never PrintString |
| B14 | Gate, 00:55 | Not all green | Write what failed; N1 stays on plumbing (plan §4); no concept change (GDD §9). The owner sleeps at 01:00 regardless |

**Drop order tonight, first to go:** the HUD fallback line; the recorder playback body; drawing inset hazards at the
arrival time; the inset; package B (A still counts).

**Never drop tonight:** the full header contract in the one compile; Enhanced Input on both devices; the determinism
test before any package; VERIFIED before any package; the owner's sleep from 01:00.

**Not tonight, by design:** S1-2 to S1-6 (data, in N1); juice beyond hit-stop, the splice frame and punch-in; audio;
replay cameras and the wrap clip; `WBP_` widgets; art; PSO cache and prewarm; scalability defaults.
