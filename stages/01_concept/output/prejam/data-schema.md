# Jump Cut: data-asset schema (GDD §8 "Content is data, so the game is mod-ready")

2026-11-11, pre-jam planning text only (Rule 7(h)): no class, data asset, DataTable or level exists before Wed Nov 11
21:00 PT. [`../gdd.md`](../gdd.md) wins over this file. Shared names and numbers: [`README.md`](README.md); stunt ideas
and times: [`storyboards.md`](storyboards.md). Every value names its source; anything this file adds is marked
**Proposal**.

Why now: all C++ classes land on jam night, because Live Coding does not work on the Linux editor (GDD §8). Every field
they need has to be known before then. After that night, agents and the owner change data, not code, and a post-jam mod
adds a car, a stunt track or a modifier by adding assets of these types.

**Who tunes** (last column of every table): **Owner** = feel and input, by hand on the asset (GDD §8). **Owner (GDD)** =
a GDD number: it is a field so it needs no recompile, but only the owner changes it. **Hub** = decided by hub 99/100
(README "Decided" and "Hub can confirm"); change it through the hub. **Lead** = the lead agent sets it while placing and
wiring art, sound and props.

## 1. Asset types

Rules for all five types (GDD §8; class, type and folder names are **Proposal**):

- Each type is one C++ class derived from `PrimaryDataAsset`; its primary asset id is `<Type>:<asset name>`. Code finds
  assets by type through the Asset Manager and never names one car, scene, stunt preset or modifier.
- Each `UJC*` class overrides `GetPrimaryAssetId()` to return its short type name (`Car`, `Scene`, `StuntPreset`,
  `Modifier`, `Tuning`). Without the override the type would be the class name (`JCCarData`) and the ini entries would
  not match. **Picked: the override**, not class-named ini types.
- One Asset Manager entry per type (`PrimaryAssetTypesToScan` in `Config/DefaultGame.ini`), cook rule Always Cook, so
  assets nothing references still cook. The `GameFeatureData` entry the mocks needed stays
  (`_config/reference/canon/jam-packaging-windows.md`).
- Levels, meshes, sounds and effects are soft references, loaded at scene start.
- Every asset also has `DisplayName` (text) and `SortOrder` (whole number, lowest first). The tables below leave them out.

| Asset Manager type | C++ class | Folder | Assets in the jam build |
|---|---|---|---|
| `Car` | `UJCCarData` | `/Game/Data/Cars` | `DA_Car_Number7` (README item 21) |
| `Scene` | `UJCSceneData` | `/Game/Data/Scenes` | `DA_Scene_01`, `DA_Scene_02`, `DA_Scene_03` (names from the merged jam-night runbook) |
| `StuntPreset` | `UJCStuntPreset` | `/Game/Data/Stunts` | 24 presets, `DA_Stunt_<Preset>` (list in 1.3) |
| `Modifier` | `UJCModifierData` | `/Game/Data/Modifiers` | none: all are parked (README); the type and class exist so adding one needs no code |
| `Tuning` | `UJCTuning` | `/Game/Data/Tuning` | `DA_Tuning_Default`, the only one (GDD §4: "one DataAsset") |

A scene's stunt list is a DataTable (`DT_Stunts_S1` to `DT_Stunts_S3`, row struct `FJCStuntRow`, **Proposal**) that the
scene asset points at. Why a table: the rows in §2 import from CSV in one editor Python call, while filling 33 rows
over MCP would take hours (5-15 min a response, GDD §8). It cooks because its scene asset points at it. If the import
fights back on jam night, the same columns become an array on the scene asset.

### 1.1 Car (`DA_Car_<Name>`)

GDD §8: "a car = mesh, livery and numbers". **The numbers are look and sound only.** The hit box and the lane-change
time sit on Tuning and are the same for every car, so a new car can never move a stunt's window (README item 17:
handling tweaks are rejected).

| Field | Type | Unit | Starting value (source) | Who |
|---|---|---|---|---|
| BodyMesh | static mesh | - | `SM_Car_Number7_Body`, built in the jam from primitives; 4.2 x 1.9 x 0.7 m body plus cabin (GDD §7; style guide §5) | Lead |
| WheelMesh | static mesh | - | `SM_Car_Number7_Wheel`, 0.7 m across (style guide §5) | Lead |
| WheelSockets | 4 socket names on BodyMesh | - | `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR`; the front two steer (GDD §7). **Proposal** | Lead |
| WheelRadius | number | cm | 35, sets the spin rate from speed | Lead |
| SteerAngleMax | number | deg | 20, look only, during a lane change. **Proposal** | Owner |
| DriverMesh | static mesh | - | `SM_Driver_Number7`: helmet and gloves, no rig (README item 20) | Lead |
| Material | material instance | - | `MI_Car_Number7`, child of `M_Car` (GDD §7) | Lead |
| Livery | 3 colours | hex | body `#F1E5C8`, stripes `#C8312F`, trim `#1A1A1A` (README palette) | Lead |
| ExtraLiveries | list of {name, 3 colours, stars to unlock} | - | empty. M1 session-only light liveries, unlocked at a 4-star wrap, parked until after Fri 19:00 (item 17) | Owner |
| BodyLean | number | deg | 4 into a lane change (style guide §5) | Owner |
| BodyBob | number | cm | 2, linked to speed (style guide §5) | Owner |
| EngineLoop | sound | - | `S_Engine_Loop`, pitched from the speed curve (GDD §7). **Proposal** name | Lead |
| EnginePitch | low, high | ratio | 0.8 at 0 m/s, 1.6 at 32 m/s (Scene 3 base plus surge). **Proposal** | Owner |
| RevFOVKick | number | deg | 1.0, RT only, cosmetic (GDD §2). **Proposal** | Owner |
| CrashFlips | 3 float-curve sets | - | three canned flip variants, 0.4 s each (item 18; storyboards board 2: 120-520 ms) | Lead |

### 1.2 Scene (`DA_Scene_<nn>`)

GDD §8: "a scene = its level plus its ordered stunt list and values". Play order comes from SortOrder (1, 2, 3); the game
never names a scene. Two things are read from the table rather than stored: the wrap line is the last row's `TMark`
(item 11), and the scene card's maximum points are the sum of `Shot` (S1 16, S2 27, S3 28; fun plan §5 checks S1).

| Field | Type | Unit | Starting value (source) | Who |
|---|---|---|---|---|
| Number, Title | whole number, text | - | 1 "REHEARSAL", 2 "THE CHASE", 3 "THE FINALE" (README) | Hub |
| Level | level | - | `L_Scene01`, `L_Scene02`, `L_Scene03` (jam-night runbook; the hub renames the greybox's `L_Rehearsal` to match) | Lead |
| DriveSplineTag | name | - | `DriveSpline`: the one spline in the level the car follows; lanes are offsets of -4, 0, +4 m. **Proposal** | Lead |
| Stunts | DataTable | - | `DT_Stunts_S1` / `S2` / `S3` (§2) | Owner, Lead |
| BaseSpeed | number | m/s | 18 / 22 / 26 (README starting numbers) | Owner |
| SpeedCurve | float curve over T, optional | m/s added | none (flat); row surges add on top (§2) | Owner |
| KeyLightColour | 1 or 2 colours | hex | S1 `#FFB04A`; S2 `#5B86C9` with sodium pools `#FF9A3C`; S3 `#FF5A1F` (README palette) | Lead |
| SetMaterial | material instance | - | `MI_Set_Rehearsal` / `MI_Set_Chase` / `MI_Set_Finale`, children of `M_Set` (GDD §7) | Lead |
| GoalLine | text | - | S1 "Drive the stunts. Cut the ones you can't. Film runs out." (GDD §2); S2, S3 empty | Hub |
| FirstPromptStunt | row id | - | S1 `S1-1`: "Hold A to look. Let go to cut. B to keep driving." stays until one hold-and-cut (GDD §2); S2, S3 none | Hub |
| FreeTakeStunt | row id | - | S1 `S1-1`: its first crash reads "CUT! FREE TAKE" and keeps TAKE 1 (item 10); S2, S3 none | Hub |
| ClapperWaitsForPress | yes / no | - | S1 yes, "(A) ACTION!"; S2, S3 no (item 12) | Hub |
| ClapperAutoRoll | number | s | S1 6, S2 and S3 2; any retry 2 (item 12) | Owner |

### 1.3 Stunt preset (`DA_Stunt_<Preset>`)

The look and sound of one kind of hazard. A row in §2 picks a preset and times it; rows may share a preset (the prop
truck in S1-2 and S2-1). Each preset spawns a Blueprint child of the one C++ `Stunt` actor. **That child holds meshes,
collision boxes, a key light and effect slots only: no Tick, no Timeline, no physics** (GDD §8). The base class poses it
from scene time.

| Field | Type | Unit | Starting value (source) | Who |
|---|---|---|---|---|
| StuntClass | Blueprint class | - | `BP_Stunt_<Preset>`, child of `Stunt` | Lead |
| Side | L or R | - | the roadside the prop starts on (Fall, Slide, Swing) | Lead |
| Ease | float curve, 0-1 in, 0-1 out | - | linear; shapes the motion between the moments §2.2 schedules (the "curve data" of GDD §8) | Owner |
| TelegraphPose | number | deg or m | the pose at the telegraph, e.g. FalseFront tilts 8° (storyboards S1-1); 0 = none | Owner |
| KeyLightIntensity | number | cd | 5000; snaps on at the telegraph, colour from the scene (GDD §7). **Proposal** | Lead |
| TelegraphSound, ActionSound | sound | - | the cue in the storyboards' "read" column: rope twang, horn, crane groan, bell | Lead |
| TelegraphFX, ActionFX | Niagara system | - | `NS_FacadeDust`, `NS_WaterSplash`, `NS_Sparks`, `NS_Fireball`, `NS_Embers` (concepts §6) | Lead |
| BlockMesh | static mesh, optional | - | the fixed prop shown in the row's Block lanes (§2.1), e.g. the light rig's base truck | Lead |
| CarArc | float curve, optional | m over s | Ramp only: car height after the lip when the car is in the lip lane; flatten it if it costs over 30 min (storyboards S3-9) | Owner |

The 24 presets the rows use: FalseFront, PropTruck, LightRig, WaterTower, Drums, Facade, Scaffold, WreckingBall, Crate,
Pipes, CameraCar, FruitCart, Barricades, Train, BurningWreck, FireJets, Bridge, Tanker, CraneHook, PipeRack, Ramp,
GasHolder, Debris, FireTrench.

### 1.4 Modifier (`DA_Mod_<Name>`)

All modifiers are parked (README, owner ideas 2026-11-11). The class lands on jam night anyway, so one can be added
later with no code. How overrides work: §3.

| Field | Type | Unit | Starting value (source) | Who |
|---|---|---|---|---|
| Kind | Movie or Stunt | - | Movie = look and sound only; Stunt = rule changes (README parked list) | Hub |
| CardTag | text | - | shown on the clapperboard and the scene card, e.g. "NOIR" | Lead |
| PickScreen | Title or SpecialFeatures | - | where the player picks it (README parked list) | Hub |
| Overrides | list of {Tuning field, value} | - | only fields §3 allows; empty by default | Owner |
| PostMaterial | material instance, optional | - | a child of `M_PostFilm` for a look the Tuning numbers cannot make (sepia, a tint) | Lead |
| Sounds | list of {Tuning sound slot, sound} | - | e.g. Silent Film swaps the cut stinger for a piano sting (README parked list) | Lead |

### 1.5 Tuning (`DA_Tuning_Default`)

The one DataAsset of GDD §4: the film economy, look and cut, crash, near-miss, grade, film look, replay and audio. The
game loads the one `Tuning` asset at boot; a second one is a load error. A mod changes play with a Modifier, never with a
second Tuning asset.

| Group | Field | Unit | Starting value (source) | Who |
|---|---|---|---|---|
| Film | ReelSize | film | 6 (GDD §4) | Owner (GDD) |
| Film | StartFilm | film | 3 (GDD §4); this alone limits cuts in a row to 3, there is no cut counter (item 7) | Owner (GDD) |
| Film | CutCost | film | 1 (GDD §4) | Owner (GDD) |
| Film | MustCutCost | film | 0 (GDD §4). Locked (§3) | Owner (GDD) |
| Film | GainWide, GainClose, GainPerfect | film | 1, 1, 2 (GDD §4); Close's "bonus star point" is its extra grade point below | Owner (GDD) |
| Film | FilmOverCap | rule | clamp at ReelSize; the stamp shows the real gain, "+1 FILM" or "FILM FULL" (item 9) | Hub |
| Film | MustCutAtZeroFilm | yes / no | yes (item 8). Locked (§3) | Hub |
| Look and cut | HoldTimeScale | ratio | 0.3 (GDD §3) | Owner (GDD) |
| Look and cut | HoldEaseIn | s | 0.15 (GDD §3) | Owner (GDD) |
| Look and cut | HoldCap | s, real time | 1.5, then auto-cancel; it never auto-cuts (GDD §3) | Owner (GDD) |
| Look and cut | CancelEaseOut | s | 0.06 back to 1x (onboarding §3) | Owner |
| Look and cut | CutHitStop | s | 0.07 (GDD §3: 60-80 ms) | Owner |
| Look and cut | PunchIn, PunchInRelax | %, s | 5, 0.3 (GDD §3; onboarding §3) | Owner |
| Look and cut | LandingMaxAhead | s, scene time | 5.0 (GDD §3 "at most ~5 s ahead"); used by the mark check (§2.3) | Hub |
| Look and cut | MarkGap | s | 2.0: default `TMark` = `TOn` + MarkGap on a point stunt, `TOff` + MarkGap on a MustCut (storyboards "DataAsset default 2 s"; greybox 1.3) | Owner |
| Look and cut | LandingClearance | s | 2.0: no hazard inside 2 s of a landing (GDD §3) | Owner (GDD) |
| Look and cut | InsetSize | px | 480 x 270 SceneCapture, runs only while held (GDD §3 "low-res"). **Proposal** | Lead |
| Look and cut | BufferLaneInput | yes / no | yes: a lane press during a hit-stop or the splice frame applies on the first live frame (onboarding §3 rule 1) | Owner |
| Lanes and speed | LaneWidth | m | 4.0 (README) | Owner |
| Lanes and speed | LaneChangeTime | s | 0.15, eased (style guide §5) | Owner |
| Lanes and speed | CarHitBox | m | 4.2 x 1.9 x 1.3, body plus cabin (style guide §5). **Proposal** | Owner |
| Lanes and speed | BlockBoxWidth | m | 4.0, a full lane: every hazard box ends on a lane line, and hazards are not shrunk (greybox F3) | Owner |
| Lanes and speed | SurgeTime, SurgeEase | s | 3.0: a step from `TOn` - 3 to `TOn` (README; greybox 1.3); ease 0. **Proposal:** a 0.5 s ease, but turning it on means re-running the greybox distance script, never hand-editing distances | Owner |
| Lanes and speed | SceneClockRate | ratio | 1.0 scene seconds per real second; exists for a Stunt modifier only (§3). **Proposal** | Hub |
| Tiers | EasySlackMin | s | 1.5 (storyboards "How to read") | Owner |
| Tiers | ExecWindow | s | 0.6 (GDD §4 "~0.6 s"); the window check allows ±0.1 | Owner |
| Tiers | SpanEasy, SpanExec | s | 0.5, 0.8: default `TOff` - `TOn`. **Proposal** | Owner |
| Tiers | WindowScale | ratio | 1.0. The fun plan §8 knob "widen to 0.8 s" is 1.33: it stretches C0-C2 and the span of TimedGap and TwoHop rows about `TOn`; the checks then re-run and may ask for a mark to move. **Proposal** | Owner |
| Crash | CrashHitStop | s | 0.12 (GDD §4) | Owner (GDD) |
| Crash | CrashToControl | s | 0.9 (GDD §4: under 1 s; storyboards board 2) | Owner |
| Crash | SafeLaneHelpAfter | crashes | 3 on the same stunt (GDD §4) | Owner (GDD) |
| Crash | MustCutPromptAfter | crashes | 1 (D4, item 6) | Hub |
| Near-miss | PerfectBand, CloseBand | m, closest approach | 0.6, 1.0; beyond is WIDE, still kept. CLOSE 1.0 is the greybox F3 ruling (hub 101) and replaces the README's 1.5, so a centred car beside a lane-line edge (1.05 m) scores WIDE | Owner |
| Near-miss | StampTime | s | 0.9 (onboarding §3) | Owner |
| Near-miss | PerfectShake | frames | 2, off with the screen-shake switch (fun plan §3) | Owner |
| Grade | Points | points | PERFECT 3, CLOSE 2, WIDE 1, cut 0, MustCut cut 1 (README grade) | Hub |
| Grade | StarAt | % of max | 25, 40, 60, 80 for stars 2-5; 1 star for wrapping (README grade) | Hub |
| Grade | TakeCap | retakes to cap | 0-1: 5, 2-3: 4, 4 or more: 3 (README grade) | Hub |
| Grade | DirectorsCutBonus | stars | +1, cap 5, if every restored stunt is kept; offered once per scene (D3) | Hub |
| Film look | SaturationFloor, Hold, Step, Max | 0-1 | 0.5, 0, +0.1 per kept shot, 1.0 (GDD §7; fun plan §2) | Owner |
| Film look | GrainIdle, GrainBurst, GrainBurstTime | 0-1, 0-1, s | 0.10, 0.35, 0.2 (style guide §3) | Owner |
| Film look | VignetteIdle, VignetteHold | 0-1 | 0.25, 0.40 (style guide §3) | Owner |
| Film look | ScratchOpacity | 0-1 | 0.15, hold only (style guide §3) | Owner |
| Film look | Letterbox | aspect | 2.39:1, replays and wrap clips only (GDD §7) | Owner |
| Film look | PostMaterial | material | `M_PostFilm` (style guide §3) | Lead |
| Film look | StepFrameRate, CameraWobble | fps, deg | 0 and 0 (off): screen-only effects for Silent Film and Low Budget. **Proposal** | Owner |
| Replay | WrapSlate | s | 1.5, "THAT'S A WRAP" (storyboards board 5) | Owner |
| Replay | WrapClip | s | 8 from the scene's last 7-10 s, one camera change per cut (D2, item 5) | Hub |
| Replay | DeletedScene | s | 3 (GDD §6) | Owner (GDD) |
| Replay | WrapSkipGuard, WrapSkipHold | s | 1.5, 0.5: hold B or Esc (HUD spec §5 c) | Owner |
| Replay | FinalReelCap, DeletedReelMax | s, clips | 30, 3 (GDD §6) | Owner (GDD) |
| Replay | ReplayCamA, B, C | offset m, FOV deg | A low side-tracking: side 6, up 0.8, 50; B high crane wide: back 20, up 12, 70; C locked at the mark looking back: up 1.5, 60. Angles from the storyboards, numbers **Proposal** | Lead |
| Menus | MenuConfirmGuard | s | 0.4 (HUD spec §5 d) | Owner |
| Audio | Music | sound | one CC0 track from the sourced-assets ledger, real time, never seeks (GDD §7; item 19) | Lead |
| Audio | HoldLowPass | Hz | 800. **Proposal** | Owner |
| Audio | Sound slots | sound | `S_Splice_Click`, `S_Clapper`, `S_ProjectorWhir`, `S_Whoosh_Wide` / `_Close` / `_Perfect`, `S_Stamp`, `S_DryClick`, `S_Cancel`, `S_RingTick`, `S_PencilScratch`, `S_InsetOpen`, `S_UI_*` (HUD spec, style guide §8); new: `S_TapeStop`, `S_TapeStart`, `S_Wrap_Stinger` (**Proposal**) | Lead |
| Audio | Volume, ScreenShake | 0-1, on / off | 0.8, on; both in the pause menu; ScreenShake off also stops the stamp shake and rumble (GDD §8; onboarding §3) | Owner |

Not fields, because the GDD fixes them: a crash never costs film; the cut shows exactly one black splice frame, never a
white flash; there is no hold cooldown.

## 2. Stunt rows

### 2.1 Columns (`FJCStuntRow`, **Proposal**)

| Column | Type | Unit | Meaning | Who |
|---|---|---|---|---|
| Id | row name | - | `S<scene>-<n>` (storyboards); an extra part adds a letter (`S1-6b`) | Hub |
| Of | row id | - | blank on a stunt. On an extra part, the stunt it belongs to: a part uses only Preset, Lanes, Block, Curve and C0-C2, and times itself from that stunt's `TOn` | Lead |
| Preset | name | - | the `DA_Stunt_<Preset>` it spawns | Lead |
| TOn | number | s, scene time | collision-on, which is the storyboards' T. The cut window closes here | Owner |
| TOff | number | s | collision-off: `TOn` + 0.5 on Easy, + 0.8 on TimedGap and TwoHop; MustCut spans from the storyboards; S3-9 from its greybox box (X 1448-1490) | Owner |
| Tier | Easy, TwoHop, TimedGap, None | - | GDD §4; None on a MustCut | Hub |
| Tel | number | s | telegraph lead: key light, cue and the cut window all open at `TOn` - `Tel` (item 7) | Owner |
| Lanes | letters from L C R | - | the lanes the prop reaches, in the order it reaches them | Owner |
| Block | letters from L C R | - | lanes a fixed prop closes for the whole zone; LCR on a MustCut | Owner |
| Line | letters joined by > | - | the authored drive line. One letter means "end in this lane, from any lane". Its last letter is the lane the three-crash help lights (GDD §4) | Hub |
| Curve | Fall, Drop, Slide, Swing, Roll, Sweep | - | how the base class moves the prop (§2.2) | Owner |
| C0, C1, C2 | numbers | s, s, per curve | the curve's three numbers (§2.2) | Owner |
| Shot | whole number | points | the stunt's top grade points: 3, or 1 on a MustCut (README grade; scene maximum = sum) | Hub |
| Band | number | ratio | scales PerfectBand and CloseBand for this stunt; 1 = Tuning, 0 = no near-miss (a MustCut) | Owner |
| MustCut | True / False | - | the GDD §1 flag: "DIRECTOR'S NOTE: cut" card at the previous mark; the cut costs 0 film | Hub |
| TMark | number | s | the mark after this stunt: the landing for cutting it and the restart for the next. Default `TOn` + MarkGap on a point stunt and `TOff` + MarkGap on a MustCut (MarkGap 2.0): the greybox's one formula, so every greybox X holds. The last row's `TMark` is the wrap line (item 11) | Owner |
| Surge | number | m/s | speed added as a step from `TOn` - SurgeTime to `TOn`; only the set piece has one (README: +6) | Owner |
| Cam | letters from A B C | - | replay angle (storyboards); two letters = one change during the stunt | Lead |

Worked out from the row, not stored:

- **Ghost lane** (the DELETED SCENE ghost drives into it, GDD §6): C if C is in Lanes or Block, else the first letter of
  Lanes.
- **Set piece:** the row with a Surge. In the deleted-scene pick it ranks after a MustCut, then TwoHop, TimedGap, Easy;
  the latest wins a tie (D2).
- **Place on the road:** the spline distance the car reaches at `TOn`; each mark likewise at its `TMark`.
  **Proposal:** the scene spawns stunts and marks there at scene start, so a new `TOn` or speed moves the stunt, and the
  level holds only the spline and set dressing.
- **Restored** (Director's Cut take) is a flag on the run, not a column (GDD §6: "one flag per stunt").

To make the CSV, copy a scene table below and drop the `---` line. The header row is the field names; Id is the row
name. Enums go in by name, booleans as `True` / `False`. Blank cells import as 0 or empty; extra parts leave the
stunt-only columns blank.

### 2.2 Curves and the lane rule (**Proposal**)

Every curve is a pure function of scene time (GDD §1, §8). Its three numbers schedule when the prop reaches each listed
lane; the preset's Ease curve shapes the motion in between. Because every pose is f(T), the hold inset can draw the
landing at `TMark` and the cut lands on exactly that state (onboarding §3 rule 2).

| Curve | Motion | C0 | C1 | C2 |
|---|---|---|---|---|
| Fall | tips over from Side onto every listed lane | start, s from `TOn` | fall time, s | end angle, deg |
| Drop | drops straight down onto every listed lane (the Bridge drops its spans in order over C1) | start, s from `TOn` | fall time, s | height, m |
| Slide | drives or slides sideways across the listed lanes | reaches the first lane, s from `TOn` | lane to lane, s | time in each lane, s; 0 = stops in the last lane and stays |
| Swing | pendulum across the listed lanes | as Slide | as Slide | as Slide |
| Roll | a wave of round props across the listed lanes | as Slide | as Slide | as Slide |
| Sweep | the listed lanes switch on in turn (jets, burners, train cars, falling boards) | as Slide | as Slide | as Slide |

**The lane rule** (what the checks read): Fall and Drop close every listed lane from `TOn` + C0 + C1 on. Slide, Swing,
Roll and Sweep close the i-th listed lane (the first is i = 0) from `TOn` + C0 + i x C1, for C2 seconds (C2 = 0: it stays
closed). Block lanes are closed from `TOn` to `TOff`. A closed lane can only hit the car between `TOn` and `TOff` (the
zone, where the car is level with the prop). The prop's collision boxes follow this schedule and end on lane lines
(greybox F3), so crash and closest approach (GDD §4) come from the boxes and agree with the rule. One exception, the
Ramp (S3-9): from its row's C0 (the ramp foot) its lane is closed to a car that changes into it, and a car already in
that lane at the foot follows CarArc over every closure until it lands.

### 2.3 Checks (one automated test, before every package)

1. **Determinism (GDD §8):** evaluate every stunt at T and T + Δ twice and compare poses. **Proposal:** Δ = 1/60 s,
   every 0.1 s from `TOn` - `Tel` to `TOff`.
2. **Windows:** sample the lane rule every 0.01 s over the zone; a lane change counts at its midpoint. Easy: the danger
   lanes stay closed and a safe lane stays open for the whole zone, with `Tel` of at least EasySlackMin. TimedGap: every
   line through needs exactly one change, and the window for it is ExecWindow ± 0.1 s. TwoHop: every line needs two
   changes, both inside ExecWindow. MustCut: no line through at all.
3. **Marks:** `TMark` is after `TOff`; the next `TOn` is at least LandingClearance (2 s) after `TMark` (GDD §3); `TMark` is
   no later than the next row's `TOn` - `Tel`, so a cut lands before the next telegraph (storyboards); and on a
   non-MustCut row `TMark` is at most LandingMaxAhead (5 s) after the window opens (GDD §3). MustCuts are exempt from the
   last rule: they land past the whole collapse (storyboards: the bridge lands on the far bank).
4. **Economy:** play each scene as the cutter (cut whenever film allows; MustCut is free). The first stunt it must drive
   at 0 film is Easy (GDD §4: "the stunt after any likely zero point is tier easy"). With the rows below that is S1-5,
   S2-4 and S3-5.
5. **Data:** every Preset exists; every Of names a stunt row; rows are in `TOn` order; Lanes, Block and Line use only L,
   C and R.

The test runs with no modifier, then once per Modifier asset the Asset Manager finds (§3). Any failure names the row and
fails the package gate, like the determinism test. The tables below pass rules 2-5 on paper.

### 2.4 Scene 1 "Rehearsal" (6 stunts, 1 MustCut, 2 execution; base 18 m/s)

| Id | Of | Preset | TOn | TOff | Tier | Tel | Lanes | Block | Line | Curve | C0 | C1 | C2 | Shot | Band | MustCut | TMark | Surge | Cam |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1-1 | | FalseFront | 7.0 | 7.5 | Easy | 2.5 | CR | | C>L | Fall | -1.0 | 1.0 | 90 | 3 | 1.0 | False | 9.0 | 0 | A |
| S1-2 | | PropTruck | 12.0 | 12.5 | Easy | 2.5 | LC | | R | Slide | -2.5 | 0.75 | 0 | 3 | 1.0 | False | 14.0 | 0 | B |
| S1-3 | | LightRig | 17.0 | 17.8 | TimedGap | 2.5 | RC | L | C>R | Swing | -0.5 | 1.2 | 0.6 | 3 | 1.0 | False | 19.0 | 0 | C |
| S1-4 | | WaterTower | 22.0 | 24.0 | None | 2.5 | LCR | LCR | | Fall | 0.0 | 2.0 | 90 | 1 | 0 | True | 26.0 | 0 | B |
| S1-5 | | Drums | 30.0 | 30.5 | Easy | 2.5 | RC | | C>L | Roll | -1.5 | 0.5 | 0 | 3 | 1.0 | False | 32.0 | 0 | A |
| S1-6 | | Facade | 35.0 | 35.8 | TwoHop | 2.5 | LC | | L>C>R | Sweep | 0.3 | 0.3 | 0 | 3 | 1.0 | False | 37.0 | 6 | BC |
| S1-6b | S1-6 | Scaffold | | | | | CR | | | Sweep | -1.4 | 0.3 | 1.5 | | | | | | |

Windows the check must find (seconds from `TOn`): **S1-3** start in C; C to R from +0.1 to +0.7 (the truss leaves R at
+0.1 and reaches C at +0.7). **S1-6** start in L; L to C from +0.1 to +0.3, C to R from +0.4 to +0.6 (the storyboards'
"second hop in the last 0.2 s"). Wrap at 37 s (X 684, greybox).

### 2.5 Scene 2 "The Chase" (9 stunts, no MustCut, 3 execution; base 22 m/s)

| Id | Of | Preset | TOn | TOff | Tier | Tel | Lanes | Block | Line | Curve | C0 | C1 | C2 | Shot | Band | MustCut | TMark | Surge | Cam |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S2-1 | | PropTruck | 6.0 | 6.5 | Easy | 2.5 | RC | | L | Slide | -2.5 | 0.75 | 0 | 3 | 1.0 | False | 8.0 | 0 | A |
| S2-2 | | WreckingBall | 11.0 | 11.8 | TimedGap | 2.5 | RC | L | C>R | Swing | -0.5 | 1.2 | 0.6 | 3 | 1.0 | False | 13.0 | 0 | B |
| S2-3 | | Crate | 16.0 | 16.5 | Easy | 2.5 | L | | C | Drop | -1.0 | 1.0 | 8 | 3 | 1.0 | False | 18.0 | 0 | C |
| S2-4 | | Scaffold | 21.0 | 21.5 | Easy | 2.5 | LC | | R | Fall | -1.0 | 1.0 | 80 | 3 | 1.0 | False | 23.0 | 0 | A |
| S2-5 | | Pipes | 26.0 | 26.8 | TwoHop | 2.5 | RCL | | R>C>L | Roll | -1.7 | 0.3 | 1.5 | 3 | 1.0 | False | 28.0 | 0 | B |
| S2-5b | S2-5 | Pipes | | | | | RC | | | Roll | 0.3 | 0.3 | 0 | | | | | | |
| S2-6 | | CameraCar | 31.0 | 31.5 | Easy | 2.5 | RC | | C>L | Slide | -2.0 | 1.0 | 0 | 3 | 1.0 | False | 33.0 | 0 | C |
| S2-7 | | FruitCart | 36.0 | 36.5 | Easy | 2.5 | LC | | R | Slide | -2.0 | 0.75 | 0 | 3 | 1.0 | False | 38.0 | 0 | A |
| S2-8 | | Barricades | 41.0 | 41.5 | Easy | 2.5 | LR | | C | Drop | -1.5 | 0.5 | 6 | 3 | 1.0 | False | 43.0 | 0 | B |
| S2-9 | | Train | 46.0 | 46.8 | TimedGap | 2.5 | CR | L | R>C | Sweep | -0.5 | 1.2 | 0.6 | 3 | 1.0 | False | 48.0 | 6 | C |

Windows: **S2-2** start in C; C to R from +0.1 to +0.7. **S2-5** start in R; R to C from +0.1 to +0.3, C to L from +0.4
to +0.6 (the first wave of pipes clears C at +0.1 and L at +0.4; the second wave closes R at +0.3 and C at +0.6).
**S2-9** start in R; R to C from +0.1 to +0.7, through the gap between the last two train cars. S2-9 keeps `Tel` 2.5 like every
row (the greybox puts each telegraph at s(T - 2.5)); the storyboards' 3 s bell may start early as sound only. Wrap at
48 s (X 1074).

### 2.6 Scene 3 "The Finale" (10 stunts, 1 long MustCut, 8 of the other 9 execution; base 26 m/s)

| Id | Of | Preset | TOn | TOff | Tier | Tel | Lanes | Block | Line | Curve | C0 | C1 | C2 | Shot | Band | MustCut | TMark | Surge | Cam |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S3-1 | | Drums | 6.0 | 6.8 | TwoHop | 2.5 | RC | L | C>R>C | Roll | 0.0 | 0.3 | 0.1 | 3 | 1.0 | False | 8.0 | 0 | A |
| S3-1b | S3-1 | Drums | | | | | RC | | | Roll | 0.6 | 0.3 | 0.1 | | | | | | |
| S3-2 | | BurningWreck | 11.0 | 11.8 | TimedGap | 2.5 | RCL | L | C>R | Slide | -0.5 | 1.2 | 0.6 | 3 | 1.0 | False | 13.0 | 0 | B |
| S3-3 | | FireJets | 16.0 | 16.8 | TwoHop | 2.5 | CL | | R>C>L | Sweep | -1.4 | 0.3 | 1.5 | 3 | 1.0 | False | 18.0 | 0 | C |
| S3-3b | S3-3 | FireJets | | | | | RC | | | Sweep | 0.3 | 0.3 | 0 | | | | | | |
| S3-4 | | Bridge | 21.0 | 30.0 | None | 2.5 | LCR | LCR | | Drop | 0.0 | 9.0 | 22 | 1 | 0 | True | 32.0 | 0 | B |
| S3-5 | | Tanker | 35.0 | 35.5 | Easy | 2.5 | RC | | L | Swing | -2.0 | 0.5 | 0 | 3 | 1.0 | False | 37.0 | 0 | A |
| S3-6 | | CraneHook | 40.0 | 40.8 | TimedGap | 2.5 | LC | R | C>L | Swing | -0.5 | 1.2 | 0.6 | 3 | 1.0 | False | 42.0 | 0 | C |
| S3-7 | | PipeRack | 45.0 | 45.8 | TwoHop | 2.5 | LC | | L>C>R | Sweep | 0.3 | 0.3 | 0 | 3 | 1.0 | False | 47.0 | 0 | B |
| S3-7b | S3-7 | Pipes | | | | | LCR | | | Roll | -1.7 | 0.3 | 1.5 | | | | | | |
| S3-8 | | FireJets | 50.0 | 50.8 | TimedGap | 2.5 | CL | R | L>C | Sweep | -0.5 | 1.2 | 0.6 | 3 | 1.0 | False | 52.0 | 0 | A |
| S3-9 | | Ramp | 55.0 | 56.6 | TimedGap | 2.5 | C | | L>C | Sweep | 0.8 | 0 | 0 | 3 | 1.0 | False | 57.0 | 6 | C |
| S3-9b | S3-9 | BurningWreck | | | | | C | | | Sweep | -2.5 | 0 | 2.7 | | | | | | |
| S3-9c | S3-9 | FireTrench | | | | | LCR | | | Sweep | 1.15 | 0 | 0.47 | | | | | | |
| S3-10 | | GasHolder | 60.0 | 60.8 | TwoHop | 2.5 | RC | | R>C>L | Sweep | 0.3 | 0.3 | 0 | 3 | 1.0 | False | 62.0 | 0 | BA |
| S3-10b | S3-10 | Debris | | | | | CL | | | Sweep | -1.4 | 0.3 | 1.5 | | | | | | |

Windows: **S3-1** start in C; C to R from +0.1 to +0.3, R to C from +0.4 to +0.6 (two waves of drums; the stack lies in
L). **S3-2** start in C; C to R from +0.1 to +0.7. **S3-3** start in R; R to C from +0.1 to +0.3, C to L from +0.4 to
+0.6 (jets in C and L first, then R). **S3-6** start in C; C to L from +0.1 to +0.7. **S3-7** start in L; L to C from
+0.1 to +0.3, C to R from +0.4 to +0.6. S3-7b keeps pipes rolling across L, C and R before `TOn`, so R is not safe for
the whole zone (hub ruling); the greybox S3-7 row becomes L C R with pipes over X 1170-1182, and the hub updates
`greybox-layouts.md` in its final index PR. **S3-8** start in L; L to C from +0.1 to +0.7 (R burns throughout, C goes out at
+0.1, L lights at +0.7). **S3-9** start in L or R; into C from +0.2 to +0.8, between the wreck (C, X 1448-1453) and the ramp
foot (X 1469). The ramp lifts the car over the fire trench (all lanes, X 1478-1490) and it lands at X 1493, 7 m before
M3-9 (greybox). **S3-10** start in R; R to C from +0.1 to +0.3, C to L from +0.4 to +0.6.
S3-5 is Easy (D1). Wrap at 62 s (X 1630).

## 3. How a modifier overrides tuning

- **When:** at run start the game copies `DA_Tuning_Default`, applies the picked modifier's Overrides in list order, and
  freezes the copy for the run. The asset on disk never changes. One modifier at a time; stacking is post-jam. The run
  recorder stores the modifier id, so the wrap clip, the reel and the Director's Cut take replay with the same values.
- **What:** each override names one Tuning field and one value. A field off the list below, or a value out of range,
  makes the modifier invalid: logged at boot, greyed out on its pick screen, and the package gate fails. It never
  crashes the game.
- **Never:** a modifier does not touch Car, Scene or StuntPreset assets or any stunt row. Different stunts are a new
  scene (a stunt track), not a modifier.

| Class | Tuning fields | Rule |
|---|---|---|
| Free (Movie or Stunt) | the Film look group, PostMaterial, StepFrameRate, CameraWobble, sound slots, HoldLowPass | Screen and sound only. They never feed the scene clock, a pose or a score, so determinism cannot break. Anything random on screen (wobble, grain) is seeded from scene time |
| Gated (Stunt only) | StartFilm, ReelSize, CutCost, GainWide, GainClose, GainPerfect, the Grade group, PerfectBand, CloseBand, HoldTimeScale, HoldCap (1.5 at most), SceneClockRate | Allowed only if the §2.3 test passes for all three scenes with the override applied. Windows and slack are measured in real seconds, so SceneClockRate divides them |
| Locked | MustCutCost, MustCutAtZeroFilm, LaneWidth, LaneChangeTime, CarHitBox, BlockBoxWidth, MarkGap, LandingClearance, LandingMaxAhead, EasySlackMin, ExecWindow, WindowScale | These hold the GDD §4 no-soft-lock claim (a MustCut is always free and always cuttable) and every stunt's windows |

The parked modifiers against this rule (README parked list):

- **Noir, Silent Film, Low Budget** (Movie): Free fields only, so always valid.
- **Fragile Film:** passes as ReelSize 3 with StartFilm 3 (the zero point does not move). StartFilm 2 fails (the cutter
  hits 0 before S1-3, a TimedGap); StartFilm 1 fails on S2-2.
- **One Take** (StartFilm 0, gains 0; MustCuts stay free): fails the economy check on S3-1, a TwoHop at 0 film. It needs
  an owner call before it is built.
- **Double Speed** (SceneClockRate 2.0): fails. Real-time windows halve to 0.3 s and Easy slack drops to 1.25 s. Owner
  call before it is built.

## 4. Naming glossary

| Prefix | What | Examples in the pack |
|---|---|---|
| `DA_` | data asset (§1) | `DA_Tuning_Default`, `DA_Scene_01`, `DA_Stunt_FalseFront`, `DA_Car_Number7`, `DA_Mod_Noir` |
| `DT_` | DataTable. **Proposal:** Epic's standard prefix, not yet in `CLAUDE.md` | `DT_Stunts_S1` |
| `BP_` | Blueprint actor | `BP_Stunt_WaterTower`, a child of the C++ `Stunt` |
| `WBP_` | UMG widget | `WBP_HUD`, `WBP_FilmCounter`, `WBP_LandingInset`, `WBP_Stamp` (HUD spec §8) |
| `NS_` | Niagara system | `NS_SpliceGrain`, `NS_TyreSmoke`, `NS_CrashDust` (concepts §6) |
| `S_` | sound | `S_Splice_Click`, `S_Clapper`, `S_Whoosh_Close` (style guide §8) |
| `M_`, `MI_` | master material, its instances | `M_Set` with `MI_Set_Rehearsal`; `M_Car` with `MI_Car_Number7`; `M_PostFilm` |
| `SM_` | static mesh | `SM_Car_Number7_Body` |
| `L_` | level | `L_Scene01` |

Inside the stunt tables, presets are bare CamelCase names (`FalseFront` means `DA_Stunt_FalseFront` and
`BP_Stunt_FalseFront`). Asset Manager types have no prefix (`Car`, `Scene`, `StuntPreset`, `Modifier`, `Tuning`). C++
data classes start `UJC` and the row struct `FJC` ("Jump Cut"). Row ids are `S<scene>-<n>`, extra parts add a letter.

## 5. Open points for the hub

None of these changes the GDD. Recommended answer first.

1. **Lane rule as the schedule** (§2.2): the boxes follow the rule, so the checks can run on paper and in the test.
   Confirm.
2. **Marks match the greybox:** `TOn` + 2 s on a point stunt, `TOff` + 2 s on a MustCut, so every greybox X holds
   (wrap lines X 684 / 1074 / 1630). A new MarkGap or speed means re-running the greybox distance script.
3. **MustCut landings are more than 5 s ahead** (S1-4 6.5 s, S3-4 13.5 s, the same numbers as greybox F1), so
   the 5 s rule exempts them.
4. **Block lanes are new:** S1-3, S2-2, S2-9, S3-1, S3-2, S3-6 and S3-8 each need a visible fixed prop (BlockMesh); S2-9's is
   the parked train cars. Without one, a timed gap leaves a lane that is safe the whole time and the tier stops testing anything.
5. **S3-3's line is R>C>L.** The storyboards' line breaks off ("L to C to..."); this order follows "flame jets across L
   and C, then R".
6. **Near-miss risk:** boxes end on lane lines (F3), so a centred car is 1.05 m away and scores WIDE; CLOSE (1.0 m) and
   PERFECT (0.6 m) come only from crossing late, perhaps still mid lane change. Watch for it at the Thu 20:00 gate; the knobs are PerfectBand, CloseBand, LaneChangeTime and each row's Band.
7. **The execution rows reuse two timing patterns** (one per tier) as starting values. Vary them in the editor after the
   Thu 20:00 gate, with the window check as the judge.
8. **One Take and Double Speed fail §3 as named;** Fragile Film passes only as a smaller reel. Owner call before either
   failing one is built (both are parked).
