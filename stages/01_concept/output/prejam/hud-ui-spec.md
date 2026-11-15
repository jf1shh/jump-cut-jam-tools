# Jump Cut: HUD and UI spec

2026-11-11. Pre-jam planning only (Rule 7(h)): words and ASCII only. **No HUD shell exists before 21:00 PT** (gdd
section 8 and the intro say so). [`../gdd.md`](../gdd.md) wins over this file. Anchors (layout, palette, grade, scene
names) come from [`README.md`](README.md). Every number the GDD does not give is marked "starting value" and lives on
the DataAsset. Items marked **Proposal** fill a GDD gap and are listed under "Open questions".

Reference pictures (mood only; **this spec wins where the text differs**): driving
[`reference-images/prejam-ref-06-hud-drive.jpg`](reference-images/prejam-ref-06-hud-drive.jpg), hold
[`prejam-ref-07-hud-hold.jpg`](reference-images/prejam-ref-07-hud-hold.jpg) (its grey inset is a mood plate: the inset is in colour), crash
[`prejam-ref-08-crash-take2.jpg`](reference-images/prejam-ref-08-crash-take2.jpg), scene card
[`prejam-ref-09-results-screen.jpg`](reference-images/prejam-ref-09-results-screen.jpg), Special Features
[`prejam-ref-10-special-features.jpg`](reference-images/prejam-ref-10-special-features.jpg), title
[`prejam-ref-11-title-screen.jpg`](reference-images/prejam-ref-11-title-screen.jpg). All the pack's pictures were made on 2026-11-11; what
each really shows, and where it differs from this text, is in [`PREJAM-DECLARATION.md`](PREJAM-DECLARATION.md).

## 1. Screen flow

```
 BOOT
  |
  v
 PHOTOSENSITIVITY CARD (any confirm, or 4 s starting value)
  |
  v
 LOADING REEL CARD (PSO prewarm: spawns every Niagara + material once) --- done --+
  |                                                                              |
  v                                                                              |
 TITLE  <------------------------------------------------------------------+    |
  | Play                                          Quit (pause, to title)   |    |
  v                                                                        |    |
 SCENE n CLAPPERBOARD (goal line on Scene 1) --> PLAY <--- Resume ---- PAUSE (Start/Esc)
  ^                                              |   |                    |
  | RETRY SCENE                                  |   +--- Restart Scene --+--> clapperboard
  |                                   crash: "CUT! TAKE n" -> back to prev mark (stays in PLAY)
  |                                              | last stunt done
  |                                              v
  |                            WRAP CLIP "Director's Cut of Scene n" (10-15 s, skippable):
  |                              replay 7-10 s, then its DELETED SCENE clip (3 s), inside the 10-15 s
  |                                              |
  |                                              v
  +--------------------------------------- SCENE CARD (stars, counts, formula)
  |  DIRECTOR'S CUT TAKE (once per scene, only if a non-MustCut stunt was cut) --> clapperboard, same scene,
  |                                                  cut stunts restored (MustCuts stay cut), their marks off
  |  NEXT SCENE --> SCENE n+1 CLAPPERBOARD (n = 1, 2)
  |  NEXT SCENE on Scene 3 --> FINAL REEL (30 s cap) --> SPECIAL FEATURES
  v
 SPECIAL FEATURES: Play the Director's Cut (30 s reel) | Deleted Scenes (3 clips)
                   | Critic's Review (stars) | Credits | Play Again | Quit
   Play Again -> Scene 1 clapperboard     Quit -> close game
```

Flow rules from the GDD: the wrap clip plays at every scene's end, with its 3 s deleted-scene clip inside the 10-15 s
(GDD §6); the final reel is capped at 30 s; the Deleted Scenes reel has 3 clips. Pause is reachable from play only (Proposal: also from a hold, see section 5).

## 2. HUD elements

All widgets are plain UMG (`WBP_` prefix), explicit focus, not Common UI. `WBP_HUD` is the one root widget that owns the
others. Tier colours are never alone: the word is always on screen. Sound hooks are `S_` names for the audio list (style guide §8), not files.

| Widget | Purpose (question it answers) | Position | Visible | States | Text / number | Animation and timing | Sound hook |
|---|---|---|---|---|---|---|---|
| `WBP_FilmCounter` | "How many cuts do I have left?" | bottom-left | all play; hidden on wrap/menus | Normal; Preview (hold); NO FILM; MustCut preview; Gain pop | 6-cell film strip + big number and "FILM" ("4 FILM"). Hold preview "3 > 2". MustCut preview "3 > 3 (-0)". At 0: number "0", strip all empty, red-orange outline; a MustCut at 0 film still previews "0 > 0 (-0)". Gain stops at the 6-cell cap | Gain: new cells fill left to right, 80 ms per cell (starting value), number pops 120% for 150 ms. Spend: last cell flashes then empties 120 ms | `S_UI_FilmGain`, `S_UI_FilmSpend`, `S_UI_FilmEmpty` |
| `WBP_Slate` | "Which scene and take am I on?" | top-left | all play | Normal; take bump on crash | "SCENE 1  TAKE 2" (TAKE = 1 + retakes; the free first crash on S1-1 does not bump it, Open question 3) | Take number flips like a clapper stick, 200 ms (starting value) | `S_UI_SlateTick` |
| `WBP_Timecode` | "Where am I in the scene; did the cut skip me ahead?" | top-right | all play; large version inside the workprint overlay | Running; Jump (on cut) | `HH:MM:SS:FF` at 24 fps, e.g. `00:00:21:12`. Scene time `T`, not wall time | Runs every frame at 0.3x during hold (digits slow down). On cut the number jumps to the landing time with a 100 ms yellow flash (starting value) | `S_UI_TimecodeJump` (shares the splice click) |
| `WBP_Stamp` | "How close was that, and what did I get?" | upper middle (the one thing allowed in the centre third) | after a kept shot, 0.9 s (starting value) | WIDE / CLOSE! / PERFECT! / NO FILM | "WIDE", "CLOSE!", "PERFECT!" plus "+1 FILM" / "+1 FILM" / "+2 FILM" below. NO FILM: "NO FILM". At the 6-film cap the line shows the real gain ("+1 FILM" or "FILM FULL"). Size grows by tier: WIDE 96 px, CLOSE 120 px, PERFECT 150 px (starting values). Colours: white / `#FFC93C` / `#FF5A36`, always on a box | Slams in from 130% to 100% in 90 ms, holds, fades 200 ms. PERFECT adds a 2-frame shake (never when shake is off) | WIDE `S_Whoosh_Wide`, CLOSE `S_Whoosh_Close`, PERFECT `S_Whoosh_Perfect` + `S_Stamp`; NO FILM `S_DryClick` |
| `WBP_LandingInset` | "Where does my cut put me, and is it safe?" | top centre, ~32% screen width, 16:9 frame | hold only | Live; DRIVE IT (cut window closed during the hold; there is no cut counter); Safe-lane highlight; WRAP (last stunt: its mark is the wrap line, Proposal) | Label "NEXT MARK". Ghost car in the chosen landing lane, three lane ticks with the chosen one lit `#FFC93C`. Hazards near the landing drawn at arrival time. After 3 crashes on this stunt the safe lane tick pulses and gets a small outline (no name, no badge) | Opens with a 100 ms scale-up from 90%; closes 60 ms. Image comes from one low-res SceneCapture that runs only while held, rendered **in colour** while the world is black and white (decided, hub 99: only the landing is in colour) | `S_InsetOpen` (part of the whir) |
| `WBP_HoldRing` | "How long can I look?" | around the button hint, bottom-right; also a thin bar under the inset | hold only | Draining; Last 0.3 s (pulse); Auto-cancel | Ring plus seconds as text "1.1" (one decimal) beside it. At 0 the ring flashes and the text reads "CANCELLED" for 0.6 s (starting value) | Drains from full to empty over 1.5 s real time (not slowed by 0.3x). Last 0.3 s: ring turns red-orange and the seconds text grows; no blinking (photosensitivity: nothing flashes more than 3 times a second) | `S_RingTick` in the last 0.3 s, `S_Cancel` on auto-cancel |
| `WBP_Prompt` | "What do I press?" | bottom centre | From the moment S1-1's cut window opens (its telegraph, about 2.5 s before collision-on), and on every cuttable stunt after it, until one hold-and-cut is done; then never again in the run, including after Retry (Proposal). Returns on a MustCut after a crash there (D4) | Waiting; Holding ("Let go to cut"); Done (fades) | Gamepad: "Hold A to look. Let go to cut. B to keep driving." KB/M: "Hold SPACE to look. Let go to cut. SHIFT to keep driving." (gdd wording; glyph swap by last input device) | Fades in 300 ms when S1-1's cut window opens; fades out 200 ms after the first cut | none |
| `WBP_ButtonHint` | "What does the main button do right now?" | bottom-right, small | all play | LOOK; CUT (during hold: "RELEASE: CUT  B: BACK"); dead (0 film); dim (no cut window open, Proposal) | "(A) LOOK" / "[SPACE] LOOK"; at 0 film "(A) LOOK  NO FILM" greyed with a strike line; during hold "(A) RELEASE = CUT" | Swaps text in 80 ms | none |
| `WBP_DirectorsNote` | "Why is this one free to cut, and why should I?" | right middle, in the README layout spot | MustCut stunt, from the previous mark (about 3 s ahead, starting value) until the stunt passes | Approaching; Cut (shows "-0"); Driven | Cream card, blue pencil `#3A6FD8`: "DIRECTOR'S NOTE: cut" and below "costs 0 film". Text only, no sound-only cue | Slides in from the right 200 ms; blue pencil underline draws over 300 ms | `S_PencilScratch` |
| `WBP_ClapperSlam` | "What just happened; where am I going back to?" | full width band, centre (a crash interrupts play, so this overrides the centre-third rule for 0.8 s) | crash only | Slam; Hold; Hard cut to black | "CUT! TAKE 3" on a clapper graphic with the take number, then "BACK TO MARK 2" small underneath (Proposal) | 120 ms hit-stop, slam in 80 ms, hold 500 ms (starting value), cut to black, mark reached. Impact to control under 1 s (gdd) | `S_Clapper` |
| `WBP_Clapperboard` | "What is this scene and what is the goal?" | centre card | scene start. Scene 1: waits for a press ("(A) ACTION!" after 1 s), rolls on its own after 6 s. Scenes 2-3 and every retry: rolls after 2 s; a press after 0.4 s rolls at once (Proposal, onboarding O1) | Scene 1 (with goal line); Scene 2/3 (no goal line); Director's Cut take (Proposal: label "DIRECTOR'S CUT TAKE") | "SCENE 1  Rehearsal", "TAKE 1", date line. Scene 1 goal line: "Drive the stunts. Cut the ones you can't. Film runs out." | Clapper stick closes at the end, 150 ms | `S_Clapper_Soft` |
| `WBP_Workprint` | "Am I in look mode?" | full screen overlay, behind the inset, ring and film counter | hold only | On | Black-and-white look over the whole world, the mark included (GDD §3; the inset and the UMG HUD stay in colour), big timecode, "WORKPRINT" tag top-centre under the inset (starting value), grain. Must not cover the inset or the film counter (it is a full-screen post pass; the UI widgets draw above it) | Eases in 150 ms with the time scale; off in 60 ms | `S_ProjectorWhir` loop |
| In-world mark (world element, not UMG) | "Where do I land?" | on the road | from 5 s ahead of the stunt, until passed. In the hold it goes grey with the rest of the world; the landing inset shows it in colour (**Decided, hub 99, 2026-11-11**: only the landing is in colour) | Normal | Gaffer-yellow tape strip across all three lanes (`#FFC93C`) and a roadside clapper sign showing the mark number "MARK 3" | none (static) | none |

Notes:
- **Max 3 HUD changes at once.** Stamp + film gain + timecode jump is the busiest moment; the Director's Note slide-in
  waits until the stamp has faded.
- The cut juice (hit-stop 60-80 ms, one black splice frame, 5% punch-in, grain burst, tape-stop stinger) is camera and
  post work, not a widget, apart from the timecode jump and film change above.
- No streak counter, no personal best, no critic line on any screen (gdd section 4).
- `DisableAllScreenMessages` at startup; no print-to-screen (gdd section 8).

## 3. Wireframes (80 columns)

### 3.1 Driving

```
+------------------------------------------------------------------------------+
| [SCENE 1  TAKE 2]                                          [00:00:21:12]     |
|                                                                              |
|                                                                              |
|                        (stamp slot, empty)                                   |
|                                                                              |
|                  | lane 1 | lane 2 | lane 3 |                                 |
|                  |        |  (car) |        |                                 |
|                  |        |        |        |                                 |
|                  =========== MARK 3 (yellow tape) ===========                |
|                                                                              |
| [|#|#|#|#| | | 4 FILM]                                         [(A) LOOK]    |
+------------------------------------------------------------------------------+
```

### 3.2 Holding (inset, ring, prompt, workprint)

```
+------------------------------------------------------------------------------+
| [SCENE 1  TAKE 2]   +--------[ NEXT MARK ]---------+          [00:00:21:12]  |
|  B&W workprint      |  :  :  :   <- lane ticks      |          big timecode   |
|  grain, scratches   |  .  [*] .  ghost car, lane 2  |                         |
|                     |  hazard (truck) at arrival    |                         |
|                     +-------------------------------+                         |
|                           WORKPRINT                                           |
|                                                                              |
|                              (car, live lane)                                 |
|                                                                              |
|          Hold A to look. Let go to cut. B to keep driving.                    |
| [|#|#|#|#| | | 4 > 3 FILM]                              (ring 1.1) [(A) CUT]  |
+------------------------------------------------------------------------------+
```

### 3.3 NO FILM moment (0 film, button pressed)

```
+------------------------------------------------------------------------------+
| [SCENE 2  TAKE 1]                                          [00:00:27:02]     |
|                                                                              |
|                       +-------------------+                                  |
|                       |     NO FILM       |  (stamp, red-orange outline)     |
|                       +-------------------+                                  |
|                              (car)                                           |
|                                                                              |
| [| | | | | | | 0 FILM]                              [(A) LOOK  NO FILM]        |
+------------------------------------------------------------------------------+
```

### 3.4 MustCut approach

```
+------------------------------------------------------------------------------+
| [SCENE 1  TAKE 1]                                          [00:00:20:08]     |
|                                          +---------------------------+       |
|                                          | DIRECTOR'S NOTE: cut      |       |
|                              (car)       | costs 0 film              |       |
|                                          +---------------------------+       |
|                  === MARK 4 (yellow tape) ===                                |
| [|#|#|#| | | | 3 FILM]                                         [(A) LOOK]   |
+------------------------------------------------------------------------------+
```

### 3.5 Crash slam

```
+------------------------------------------------------------------------------+
| [SCENE 1  TAKE 3]                                          [00:00:30:01]     |
|                                                                              |
|              +-------------------------------------+                         |
|              |  ==clapper==                        |                         |
|              |  CUT!  TAKE 3                       |                         |
|              +-------------------------------------+                         |
|                      BACK TO MARK 4                                          |
|                                                                              |
| [|#|#|#| | | | 3 FILM]  (film unchanged: a crash costs a take)               |
+------------------------------------------------------------------------------+
```

### 3.6 Scene-start clapperboard (Scene 1)

```
+------------------------------------------------------------------------------+
|                                                                              |
|          +----------------------------------------------------+              |
|          | ##//##//##//##//##//##//##//##  (clapper stick)    |              |
|          | SCENE 1   REHEARSAL          TAKE 1                |              |
|          | Drive the stunts. Cut the ones you can't.          |              |
|          | Film runs out.                                     |              |
|          +----------------------------------------------------+              |
|                                          [(A) ACTION!]                       |
+------------------------------------------------------------------------------+
```

### 3.7 Wrap clip with skip hint

```
+------------------------------------------------------------------------------+
|==============================  (letterbox bar)  ============================|
|                                                                              |
|          "Director's Cut of Scene 1"  (replay, one camera change per cut)    |
|                                                                              |
|==============================================================================|
|                              (hold B to skip)   [|||    ]  <- 0.5 s fill      |
+------------------------------------------------------------------------------+
  First 1.5 s: hint hidden, input ignored (Proposal c). KB/M text: "hold ESC to skip".
```

### 3.8 Scene card

```
+------------------------------------------------------------------------------+
|                        SCENE 1  REHEARSAL  -  WRAP                           |
|                                                                              |
|   STARS   [*][*][*][*][ ]    4 / 5                                           |
|   Shots kept 4 of 5    PERFECT 2   CLOSE 1   WIDE 1                          |
|   Deleted scenes 2 (1 restorable)  Retakes 2   Film left 6                               |
|   Points 10 of 16 = 62% -> 4 stars; retakes 2 -> cap 4; next star at 13      |
|                                                                              |
|       [ NEXT SCENE ]  [ DIRECTOR'S CUT TAKE: Restore 1 deleted scene ]       |
|                            [ RETRY SCENE ]                                   |
+------------------------------------------------------------------------------+
```

### 3.9 Pause

```
+------------------------------------------------------------------------------+
|              (game frozen, dimmed 50%)                                       |
|                       +------------------------+                             |
|                       |        PAUSED          |                             |
|                       |  > Resume              |                             |
|                       |    Restart Scene       |                             |
|                       |    Volume    [====  ]  |                             |
|                       |    Screen shake  On    |                             |
|                       |    Quit                |                             |
|                       +------------------------+                             |
+------------------------------------------------------------------------------+
```

### 3.10 Title

```
+------------------------------------------------------------------------------+
|                                                                              |
|                              J U M P   C U T                                 |
|                          Includes deleted scenes.                            |
|                                                                              |
|                              > Play                                          |
|                                Quit                                          |
|                                                                              |
| PAD: stick lane | A hold to look, release to cut | B cancel | Start pause    |
| KEYS: A/D lane | SPACE or L-mouse hold/cut | SHIFT or R-mouse cancel | ESC  |
+------------------------------------------------------------------------------+
```

### 3.11 Special Features

```
+------------------------------------------------------------------------------+
|                         S P E C I A L   F E A T U R E S                      |
|                                                                              |
|                  > Play the Director's Cut                                   |
|                    Deleted Scenes                                            |
|                    Critic's Review                                           |
|                    Credits                                                  |
|                    Play Again                                                |
|                    Quit                                                     |
+------------------------------------------------------------------------------+
```

### 3.12 Photosensitivity card, then loading reel card

```
+------------------------------------------------------------------------------+
|                                                                              |
|   +----------------------------------------------------------------------+   |
|   | NOTICE: this game has brief flashes, hard cuts, and flicker.         |   |
|   | There is no white flash. If you are sensitive to flicker, play       |   |
|   | with care.                                          [(A) CONTINUE]   |   |
|   +----------------------------------------------------------------------+   |
|                                                                              |
+------------------------------------------------------------------------------+
+------------------------------------------------------------------------------+
|                                                                              |
|                         LOADING REEL                                         |
|                         [ ####----------- ]   (frame-count bar)              |
|                         Warming the projector...                             |
+------------------------------------------------------------------------------+
```

## 4. Menus

| Menu | Items and content |
|---|---|
| Title | Play, Quit. Controls strip for both devices at the bottom of the title; no separate how-to screen. Default focus Play |
| Pause | Resume, Restart Scene, Volume (slider), Screen shake On/Off, Quit. Default focus Resume. Nothing else (gdd section 5 names volume, screen-shake off, restart and Quit). Quit returns to the title, whose own Quit closes the game: one Quit item, as the GDD lists, and a misclick never closes the game |
| Scene card | Stars as icons AND "4 / 5". Shots kept. Perfect / Close / Wide counts. Deleted scenes. Takes. Film left. Formula line (Proposal f). Buttons NEXT SCENE, DIRECTOR'S CUT TAKE, RETRY SCENE |
| Special Features | Play the Director's Cut (30 s reel), Deleted Scenes (3 clips), Critic's Review (stars only), Credits, Play Again, Quit (gdd section 6 plus Play Again and Quit) |
| Critic's Review | Star icons and "n / 5" per scene and a total, stars only (no critic text; gdd section 10 cut order item 4). Back button |
| Credits | Agents listed as crew (roles as film crew titles), then the real jam cut-list card. Back button. Auto-scroll with pause on any input is not needed; plain static pages |

The Special Features "Play the Director's Cut" is the 30 s highlights reel (Proposal: separate from the Director's Cut
take on the scene card, which is a playable replay of one scene).

## 5. Behaviour proposals

**Proposal** (each fills a GDD gap):

- **(a) 0 film.** Pressing A / Space at 0 film shows the NO FILM stamp and plays a dry click. It does not enter the
  hold, because there is no landing to show. (MustCut stunts still allow the hold at 0 film, see Open questions.)
- **(b) Window closes while holding.** If the cut window closes during a hold (the car reaches the collision-on line),
  the inset label flips to "DRIVE IT" and release just cancels.
- **(c) Skip guard.** The wrap clip ignores input for its first 1.5 s (the player may still be pressing A / Space when
  the scene ends). Skip is "hold B / Esc for 0.5 s".
- **(d) Menu guard.** Every menu ignores confirm for 0.4 s after it appears.
- **(e) Scene card focus.** Default focus is NEXT SCENE. DIRECTOR'S CUT TAKE shows only if at least one non-MustCut
  stunt was cut, labelled with the number restored ("Restore 2 deleted scenes"), and only **once per scene**: after
  the take, that scene's card shows NEXT SCENE and RETRY SCENE only, so it cannot loop (D3, decided by hub 99).
- **(f) Formula line.** The scene card shows the star formula as one line of numbers, using the README grade formula
  (decided by hub 99)
  (for example "Points 10 of 16 = 62% -> 4 stars; retakes 2 -> cap 4; next star at 13"; fun plan §5).
- **(g) Pause during a hold.** Start / Esc pauses and cancels the hold; on Resume the hold has ended and the live game
  continues. Esc is not "back" in play (it is pause).

## 6. Input map

### 6.1 Gameplay (gdd section 2, unchanged)

| Action | Gamepad | Keyboard / mouse |
|---|---|---|
| Lane (during a hold: sets the **landing** lane; the live car keeps its lane) | Left stick or d-pad | A/D or arrows |
| Hold to look, release to cut | **A / Cross** | **Space** or left mouse |
| Cancel the look | **B / Circle** | **Shift** or right mouse |
| Engine rev (cosmetic only: sound + tiny FOV kick) | RT | none |
| Pause | Start | Esc |

LT is unused.

### 6.2 Menus (Proposal)

| Action | Gamepad | Keyboard / mouse |
|---|---|---|
| Navigate | Stick or d-pad | Arrows or W/A/S/D; mouse hover moves focus |
| Confirm | A | Enter, Space, or left click |
| Back | B | Esc, or right click |
| Toggle pause (in play) | Start | Esc |
| Slider change (Volume, Screen shake) | d-pad left/right | Arrows left/right |

- **Device-aware glyphs** switch on the last input used (any pad button vs any key or mouse move). Prompts, button hint
  and menus use the same switch. Show the Cross / Circle names when a PlayStation pad is detected.
- **Enhanced Input from the first greybox.** Input mapping contexts: Gameplay, Menu. Never key polling. Menu context is
  pushed when a menu opens and popped when it closes.
- **Explicit focus in plain UMG:** set focus on open, restore the previous focus on close, mouse hover moves focus, all
  buttons have a visible focus state (gaffer-yellow `#FFC93C` outline plus a ">" marker).

## 7. Readability rules

| Rule | Value |
|---|---|
| Safe margin | 5% on all sides |
| Anchoring | Corners and top centre only; test on 16:9 1920x1080 and the Legion's 16:10 1920x1200 (8 inch) |
| Body text | at least 30 px at 1200p (starting value) |
| Numbers (film, timecode, take) | at least 44 px (starting value) |
| Stamps | at least 96 px (starting value) |
| Backdrop | every text line sits on a warm-white-on-black box at ~65% opacity; never fix contrast by changing the text colour alone (`jam-hud-readable-text.md`) |
| Text size scaling | scale to the 1200p height; check the right edge for clipping at 1920x1200 |
| HUD changes at once | at most 3 |
| Centre third | nothing essential except the stamp (the car and the road live there); the clapper slam and the clapperboard are the two short exceptions, no play happens then |
| Workprint overlay | must not cover the inset or the film counter |
| Colour | never alone: every tier, the film count and NO FILM carry text or a number as well as colour and sound |
| Test frames | read a packaged 1920x1200 frame at the lightest and the darkest spot of each scene (Scene 1 amber backlot daylight vs Scene 2 night street) |

## 8. Build notes for jam night

Widgets by gate (gdd section 9), in the GDD's feel-budget order (cut moment, car feel, crash and take two, audio pass):

| Gate | Needs from this spec |
|---|---|
| Thu 01:00 plumbing | Nothing from this spec beyond a debug hold/cut (a text line "HOLD / CUT / CANCEL" is enough). No HUD shell |
| Thu 20:00 stranger gate | **Minimum (built as specified):** `WBP_FilmCounter`, `WBP_Prompt`, `WBP_Stamp` (WIDE / CLOSE / PERFECT plus NO FILM), `WBP_ClapperSlam`, `WBP_LandingInset`, `WBP_ButtonHint`, in-world mark. **Plain text is enough:** `WBP_Slate`, `WBP_Timecode`, `WBP_HoldRing` (seconds as text), `WBP_Workprint` (the black-and-white post plus a "WORKPRINT" text tag), `WBP_Clapperboard` (the Scene 1 goal line as text) |
| Fri 19:00 AAA | Polish of all of the above for Scene 1; `WBP_DirectorsNote`; photosensitivity card and loading reel card; pause menu; scene card |
| Later | Wrap clip skip UI, Special Features, Critic's Review, Credits, title controls strip |

Order for the HUD shell when the window opens: `WBP_HUD` root with film counter, then stamp, then prompt, then inset.
All widget text, sizes and timings above are starting values on the DataAsset or a widget style asset. Package-test the
loading reel card with `-clearPSODriverCache` (gdd section 8).

## 9. Open questions

Status after the pack review (2026-11-11): 1-4, 6 and 7 have a recommended answer in the README's "Open decisions";
5 is answered in [`fun-plan.md`](fun-plan.md) §6; 8 waits for the dev log.

1. **MustCut at 0 film.** gdd says "at 0 film the cut button is dead" and "MustCut costs 0". It does not say whether a
   MustCut stunt can be cut at 0 film. The soft-lock note ("0-film + MustCut soft-lock cannot happen") implies it must
   be allowed. This spec allows the hold at 0 film on a MustCut stunt. Needs a one-line decision.
2. **Film at the cap.** Reel size is 6. gdd does not say what happens to +1 / +2 film that would go past 6 (wasted?). The
   stamp text "+2 FILM" would be wrong. Proposal: clamp at 6 and show the real gain ("+1 FILM" or "FILM FULL").
3. **Take count and the free first crash.** gdd calls the first stunt "a free crash" and says takes cost stars. The
   README grade says it is not a retake. The slate "TAKE n" and the clapper "CUT! TAKE n" must say which number to show.
4. **Last stunt's mark.** gdd: one mark per stunt, "the mark after stunt N". The final stunt of a scene has no next
   mark (wrap?). The inset needs a state ("WRAP") or the cut is not offered. Proposal: the last stunt's mark is the
   wrap line.
5. **Director's Cut take HUD.** gdd says "marks off" and "cut stunts restored". It does not say whether the hold still
   works on the other stunts, or whether film still counts. This spec shows the same HUD and hides marks.
6. **"Retry scene" and "Restart Scene".** gdd lists "restart" in scope and the scene card offers the Director's Cut take
   only. RETRY SCENE and Restart Scene are Proposals here and need a yes.
7. **Pause during hold and Esc as back.** Not in gdd; section 5 (g) is a Proposal.
8. **Credits content.** gdd says agents as crew plus the real cut-list card; the card's text is not fixed, so
   the Credits layout is a placeholder until the dev log is written.
