# Jump Cut: one-page plan (recommended #1 for "Director's Cut")

2026-11-11, pre-jam planning text only (Rule 7(h)); nothing is built before 21:00 PT. Working title (alternative:
"Cut to the Chase"); check itch.io for a clash before the page is named. Filled from
`_config/reference/templates/gdd-one-pager.md`. Ideas and scores: [`directors-cut-ideas.md`](directors-cut-ideas.md).
**Superseded where they differ by [`gdd.md`](gdd.md)** (locked 2026-11-11 13:31 PT with Fable's final change list). Lines that the lock changed are fixed below and marked *(locked)*; anything else that disagrees with `gdd.md` is wrong here.

## One-pager

- **Pick:** Jump Cut 29/35 (leader), Rolling! 27/35 (runner-up), Cheat the Angle 26/35 (third). All three have Fun
  Factor and Gameplay at 3+.
- **Risk fork** *(locked)*: replaced by `gdd.md` section 9: Thu 01:00 is a plumbing gate only; the real gate is Thu 20:00 (two strangers play the Scene 1 greybox on the Legion gamepad); fallbacks (Jump Cut without preview, or Rolling!) are decided by Thu 21:00 and never later.
- **Theme tie-in:** *(superseded: see gdd.md §2, §6)* title "JUMP CUT", line "Your run. Your edit. Your director's cut." Play starts on a clapperboard
  ("Scene 1, Take 1") inside 5 s; the first prompt is "Hold to look ahead. Let go to cut." Every run ends with your
  director's cut: the run replayed as an edited film, one camera change per cut you made.
- **Core verb:** *(superseded: see gdd.md §3)* cut time. Hold to preview the scene a moment ahead (longer hold, further ahead, 0.5-3 s), release to
  jump there. The car is not in the skipped frames, so it passes through anything in them.
- **Loop:** *(superseded: see gdd.md §6)* title, three scenes on a studio backlot (Rehearsal, The Chase, The Finale), each ending on "That's a
  wrap", then the director's-cut replay and a grade screen with Restart and Quit.
- **Win/lose states:** *(superseded: see gdd.md §4)* reach the wrap of scene 3 to win and see the replay and grade (money shots kept, takes used,
  film left). A crash is "Cut, take two": an instant restart from the last slate marker, never a game-over screen; the
  take count lowers the grade. Out of film means you cannot cut until you drive through a money shot.
- **Fun Factor bet:** *(superseded: see gdd.md §4)* it already works with grey cubes. Every few seconds the player chooses: cut now (safe, costs
  film, may skip a money shot) or drive it (risky, earns film). The preview turns reflexes into a quick read of the
  future, and the payoff (flash, angle change, the music jumping with you) lands on every press.
- **Visual direction:** *(superseded: see gdd.md §7)* a 1970s backlot stunt movie at toy scale. Stylized low-poly, warm tungsten studio lights
  against a dark backstage. The film starts black and white with grain and gains colour with each money shot kept.
  One master material per look: `M_Set` (props and flats via `MI_`) and `M_Car`.
- **Scope cut list (if Day 3 runs long, in this order):** *(superseded: see gdd.md §10; lanes are never-cut)* 1. Scene 3 (ship two scenes plus the replay). 2. Lanes
  (single lane, cut only). 3. Colour-return effect and extra replay angles (keep one angle change per cut).
- **Out of scope:** *(superseded: see gdd.md §5)* multiplayer, saves, online leaderboard, humanoid actors or dialogue, a level editor, settings
  beyond pause, restart, volume and Quit, a web build, Android (dropped, D-008).

## How it works *(superseded: build from gdd.md §3, §4, §7 and §8, not from here)*

- **Scene clock.** *(superseded: see gdd.md §3, §8)* One scene time `T`. The car's track position and every hazard's pose and "collision on" state are
  pure functions of `T`. A cut is `T += Δ` with no collision test in between; after landing, an overlap with a live
  hazard is a crash. This makes the preview exact (ghosts drawn at `T + Δ`) and the replay deterministic (record the
  list of cuts and lane changes, replay from `T = 0`). Logic-heavy, so C++ per `CLAUDE.md`: a scene-clock subsystem,
  a timed-hazard base class, the car pawn on a spline, a cut component (preview, film stock, money shots), a run
  recorder. Blueprint children for each hazard and all wiring; `WBP_` widgets for title, HUD, pause, end, replay.
- **Controls** *(locked, `gdd.md` section 2)*: gamepad A/Cross = hold to look, release to cut; B/Circle = cancel; stick or d-pad = lane; RT = cosmetic rev; Start = pause. KB/M: Space or left mouse = hold/cut; Shift or right mouse = cancel; A/D or arrows = lane; Esc = pause. Looking is free and auto-cancels at 1.5 s; a cut goes to the next mark only. Enhanced Input from the first greybox; plain UMG with explicit focus, not Common UI.
- **Audio** *(locked)*: music runs on real time and never seeks (hold = low-pass, cut = tape-stop stinger, crash = clapper). One CC0 track in the ledger or a MetaSound loop; local music generation is off. SFX on every action.
- **Assets (cloud only, through the repo adapters, once keys and terms dates exist).** *(superseded: see gdd.md §7)* Hero car *(locked)*: built in the jam from primitives or a box model with spinning, steering wheels, not AI 3D or a kit. About
  10 set props (studio light, camera crane, wrecking ball, truck, scaffold, barrel, clapperboard, boom mic, two flat
  kits), Niagara `NS_CutFlash`, `NS_Sparks`, `NS_Fireball`. 3D from Meshy or Hyper3D Rodin (direct or via fal) *(static props and posters only, never the car; gdd.md §7)*; concept
  sheets, posters and title cards from GPT, Grok or fal FLUX; set materials from PBRGen. Primitives fill the rest.
- **Levels.** *(superseded: see gdd.md §4)* `L_Title`, `L_Scene01` (teach: one hazard, the prompt, a free first crash), `L_Scene02` (test: hazards
  with different rhythms, money shots that compete with cuts), `L_Scene03` (twist: a collapse you can only cut past,
  chains you must read in the preview). Every win object tagged `QAObjective`, a reachable `PlayerStart` in each.
- **Stretch only after the Sat 10:00 risk fork passes:** *(superseded: see gdd.md §6, §9)* a "Director's Cut" mode (each scene's extended cut with extra
  "deleted scenes" segments), and an end-credits "Deleted scenes" card listing our real jam cut list (text only, ties
  the game to the Glass Box dev log).

## Day plan *(superseded: see gdd.md §9)* (PT; the gates in `PLAN.md` and `stages/00_prep/references/jam-execution-plan.md` win where they differ)

| When | Target | Gate |
|---|---|---|
| Wed 21:00-01:00 (jam night) | New 5.9 project; greybox spline course, car moves, one timed hazard, hold-preview-release cut; KB/M and gamepad bound | Thu 01:00: move + cut work in greybox on both input methods |
| Thu Nov 12 (Day 1) | Cut juice (flash, slow-mo hold, angle change, splice SFX, hit-stop on crash), take-two restart, film stock, money shots, end screen stub; art direction from 3 cloud hero assets | **Build #1** launches on the Legion and the loop plays on the gamepad alone (17:00) *(superseded: the real gate is Thu 20:00, gdd.md §9)* |
| Fri Nov 13 (Day 2) | **Vertical slice:** Scene 1 at final quality (set dressing, light, post look, music that jumps, HUD) from title through replay to end screen; Scenes 2-3 greyboxed so a full run exists | **Build #2**; the owner plays a full run on the Legion gamepad (19:00) |
| Sat Nov 14 (Day 3) | **Playable build:** Scenes 2-3 dressed, replay polished, pause and Quit, every action has a sound, theme on the title and in minute 1 | Risk fork 10:00; *(superseded: scope check only, gdd.md §9)* feature freeze 22:00; **build #3**; insurance upload 23:30 |
| Sun Nov 15 (Day 4) | Fixes only to 12:00; final build 13:00; video 14:00; dev log and tools list 15:00; uploaded 16:00 | **Owner submits by 16:30** (hard deadline 17:59, 5:59 PM PT) |

Agents (at most 4 live): the lead is the only Unreal MCP caller and builds in the editor; one worker writes the C++
in source files *(locked: Live Coding is not available on the Linux editor, so every C++ class lands on jam night with its tunables as UPROPERTYs or on the DataAsset; after that agents change data and Blueprints, and the Windows build happens on the Legion)*; one runs cloud asset jobs; one runs QA (agent
playtest, judge pass) and drafts the nightly dev log.

## Ship and submission notes (carry into `stages/04_ship`)

- **Build config:** the Windows zip keeps its current setup, the Development config (D-009). **Any web build must
  be a Shipping build, not Development** (kickoff stream, 2026-11-11). No web build is planned.
- Zip `TeamName_GameName.zip` under 1 GB, Windows 10/11, runs with no extra software (Rules 1, 7, 10).
- Video 30-60 s at 1080p, gameplay in the first 5 s, end on the title card. The director's-cut replay is built to
  double as trailer footage.
- Dev log link for Glass Box; nightly entries via `scripts/gen_devlog.py`. Possible frame: a "director's
  commentary" track on how the owner directed the agents (the hosts' own point).
- **Tools-used list** (needed for partner prizes such as the Hyper3D cash pool and the NVIDIA RTX award; the award
  criteria are not in this repo, read the prize page): list only what was really used (for example Meshy, Hyper3D
  Rodin, fal, GPT image, Grok, PBRGen, Claude, Cursor, Diversion). iClone Personal is skipped (no commercial use).
  Rokoko is possible but its terms are unchecked; do not use it until they are.
