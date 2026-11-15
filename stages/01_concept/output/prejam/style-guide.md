# Jump Cut: style guide (palette, film look, lighting, car, sets, camera, audio, type)

2026-11-11. **Pre-jam planning text only (Rule 7(h)). Nothing here is built before Wed Nov 11 21:00 PT.** This file is
words, not assets. [`../gdd.md`](../gdd.md) is the build target and wins over this guide; where this guide gives a
number the GDD does not, it is marked **starting value** and is tuned on the DataAsset or the post volume during the
jam. Shared names, colours and sets come from [`README.md`](README.md).

## 1. Look pillars

1. **Toy-scale 1970s backlot.** Plywood, scaffold, gaffer tape, studio lamps. A stunt set built to be driven past,
   not a real city.
2. **The edit is visible.** Timecode, sprocket holes, splice frame, clapper, letterbox in replays. The film-making
   is the look.
3. **Readable first, pretty second.** A hazard, a lane and the landing must read at 0.3x and in black and white.
4. **Colour is rationed.** Each scene starts at about half colour. Full colour is earned by kept shots; full
   black and white belongs to the hold.

## 2. Palette and grading

Hex values are the README anchors; they are starting points for `MI_` children and the post volume.

| Use | Colour |
|---|---|
| Backstage void | `#0E0D0C` |
| Set neutrals | warm grey `#8C8478`, plywood tan `#B9A98C` |
| Scene 1 key | amber tungsten `#FFB04A` |
| Scene 2 key | steel-blue gel `#5B86C9`, sodium pools `#FF9A3C` |
| Scene 3 key | fire red-orange `#FF5A1F` |
| Hero car | cream `#F1E5C8`, signal red `#C8312F`, black trim `#1A1A1A` |
| Mark, UI focus | gaffer-tape yellow `#FFC93C` |
| HUD text | warm white `#F5F2EA` on black box, ~65% opacity |
| Tiers | WIDE white, CLOSE `#FFC93C`, PERFECT `#FF5A36` (always with the word) |
| Director's note | blue pencil `#3A6FD8` on a cream card |

**Per-scene grading target (starting values; tune in the jam):**

| Scene | Overall cast | Shadows | Highlights | Floor saturation at scene start |
|---|---|---|---|---|
| 1 Rehearsal | warm, sun-faded | brown-black | amber | ~50% (gdd §7) |
| 2 The Chase | cold blue with orange pools | deep blue-black | sodium orange | ~50% |
| 3 The Finale | hot, smoky | red-black | fire orange | ~50% |

**Saturation rules (gdd §3, §7):**
- Scene start: the saturation parameter sits at the floor, about 0.5.
- Hold: the parameter goes to 0 (full black and white) and returns to its previous value on release or cancel.
- Kept shots step the floor up from where it is. Step size: starting value 0.1 per kept shot, capped at 1.0. This is
  a cheap post blend and is last on the cut list (gdd §10); the fallback is the static 50% floor.
- **Only the landing is in colour** (decided by hub 99, 2026-11-11). During the hold the whole world goes full black
  and white, the gaffer-yellow mark included (GDD §3). The landing inset (the SceneCapture) renders in colour, so the
  mark and the landing lane show yellow there, and the UMG HUD stays in colour on its backdrop boxes.
- Letterbox (2.39:1 bars) appears in replays and wrap clips only, never in play or in the hold.
- Black and white is judged on value, not hue: every hazard and the car must still separate from the road in a
  greyscale screenshot (see section 6).

## 3. Film look (post stack)

One post-process material (`M_PostFilm`) driven by one post volume. Parameters live on the DataAsset or as material
parameters so tuning needs no recompile.

| Layer | What it does | Starting value (tune on the DataAsset/post) |
|---|---|---|
| Saturation | the one parameter from section 2 | floor 0.5; hold 0 |
| Film grain | fine, always on; a short burst on the cut (gdd §3) | 0.10 idle, 0.35 burst for ~0.2 s |
| Vignette | soft, slightly stronger during the hold | 0.25 idle, 0.40 hold |
| Workprint overlay (hold only) | sprocket holes down both edges, burned-in timecode, dust and scratches | scratches ~15% opacity |
| Punch-in | 5% scale-up on the cut (gdd §3) | 5% |
| Letterbox | replays and wrap clips only | 2.39:1 |

- **Splice frame = one black frame.** The cut shows exactly one black frame, never a white flash (gdd §3). Nothing in
  the stack may flash white: no bloom spike, no additive overlay. A photosensitivity card exists anyway (gdd §3).
- The workprint overlay fades in with the 150 ms ease to 0.3x. It is a screen-space layer, so it costs nothing in
  the world.
- Timecode format is `HH:MM:SS:FF` (the README HUD uses `00:00:21:12`). It runs in scene time and jumps on the cut.
- Keep grain and scratches subtle behind HUD text; the backdrop boxes carry readability, not the post.

## 4. Lighting

- **Each hazard has its own key light** (gdd §7), in the scene's key colour. The light is part of the telegraph: it
  comes on, swings or brightens as the hazard becomes active.
- **Backstage void:** the world beyond the set is near-black `#0E0D0C` with a light fog (starting value: low density,
  fog colour tinted to the scene key). It hides nothing that matters, only the edges of the set.
- **Practical lamps:** studio lamps on stands, hanging fixtures and a few visible spotlights as set dressing. They
  are bright shapes, not extra shadow-casting lights. Budget: few dynamic lights; prefer baked or emissive
  materials (Medium default scalability, gdd §8).
- **One silhouette piece per scene** (water tower, rail trestle, gas-holder) is rim-lit so its shape reads against
  the void even in black and white.
- **Readability rules:**
  1. A hazard's telegraph (facade tipping, truck nosing in, ball starting to swing) must read at 0.3x, because the
     hold shows it there (gdd §3).
  2. The landing zone and the mark are always lit; the gaffer-yellow strip is the brightest flat thing in the frame.
  3. Never hide a hazard in darkness. If a hazard is dark in a greyscale screenshot, add a key light, not a glow.
  4. The three lanes keep a stable value gap from the sidewalk and the void.
  5. No colour-only cue: every state also has a shape, word or number (gdd §4).

## 5. Hero car

Built in the jam from primitives or a modelling-tool box model. Not a licensed kit, not Chaos vehicle physics (the
car follows a spline and a lane offset, gdd §7 and §8). Four wheels are separate meshes that spin, and the two front
wheels also steer (gdd §7).

| Part | Primitive build | Size (starting value) |
|---|---|---|
| Body | one box, bevelled if the tool allows | ~4.2 m long x 1.9 m wide x 0.7 m |
| Cabin | smaller box on top, rear-set | ~2.0 m long x 1.6 m wide x 0.6 m |
| Wheels | four cylinders, separate meshes | ~0.7 m diameter x 0.25 m wide |
| Bumpers | two flat black boxes, front and rear | full width x 0.25 m |
| Roll cage | thin cylinders or boxes over the cabin | tube ~0.05 m |
| Stripes | two signal-red stripes, bonnet to tail | ~0.2 m wide each |
| Number | "7" on both doors and the roof | ~0.5 m tall |

- Colours: cream body `#F1E5C8`, signal red `#C8312F` stripes, black trim and bumpers `#1A1A1A`. One master material,
  `M_Car`, with parameters for body, stripe and trim.
- **Why it reads in black and white:** cream is the lightest big shape on screen; tyres, bumpers and road are dark.
  The red stripes turn mid-grey, so the number and stripes still show. Check this in a greyscale screenshot.
- Motion feel (all starting values): body lean into lane changes (~4 degrees), a small speed-linked bob (~2 cm),
  tyre smoke on lane changes and the crash flip, lane change eased over ~0.15 s (from planning notes, not the GDD).
  The car in a hold keeps its lane; only the landing lane marker moves (gdd §2).
- Crash: canned flip animation (gdd §4), no physics simulation.

## 6. Sets (one sheet per scene)

Every scene shares one road read: **three lanes, 4 m each** (README starting value), dashed white lane lines, sidewalks
and a kerb on both sides, the backstage void beyond. Materials: one master `M_Set` with `MI_` children per scene
(`MI_Set_Rehearsal`, `MI_Set_Chase`, `MI_Set_Finale`), plus `M_Car`. Naming follows `CLAUDE.md` (`SM_`, `NS_`, `S_`).

**Shared dressing list (from the one-pager):** studio light, camera crane, wrecking ball, truck, scaffold, barrel,
clapperboard, boom mic, two flat kits. Every piece is a low-poly primitive-built or simple static mesh. Fab may fill
**background only** (gdd §7): distant flats, crowd-free street furniture, signage that carries no third-party mark.

### Scene 1 "Rehearsal" (Main Street backlot)

- **Key:** amber tungsten `#FFB04A`. **Silhouette:** wooden water tower (the MustCut stunt).
- **Layout:** straight Main Street, plywood false fronts on both sides held up by visible scaffold braces; sidewalks
  with painted-on shopfronts. Calm, wide, forgiving.
- **Dressing:** studio lights on stands, clapperboard sign at each mark, barrels, one flat kit of shop fronts.
- **Hazards (cues are starting proposals; stunt list is in `storyboards.md`):**

| Hazard | Telegraph cue | Own key light |
|---|---|---|
| S1-1 Leaning False Front, S1-6 The Big Facade (gdd §3 "facade tipping") | ropes snap, scaffold braces shake, facade leans, dust | amber spot from behind the facade |
| S1-2 Prop Truck (gdd §3 "truck nosing in") | horn, headlights, the truck nose enters first | amber plus a cold white headlight cone |
| S1-3 Light Rig Swing | crane arm creaks, the lamp truss starts its sweep | the truss's own lamps |
| S1-4 The Water Tower (MustCut) | legs buckle, the tower falls across all three lanes; "DIRECTOR'S NOTE: cut" card | brighter amber |
| S1-5 Barrel Roll | flatbed tips, barrels rattle first | amber |

### Scene 2 "The Chase" (day-for-night city street)

- **Key:** steel-blue gel `#5B86C9` with sodium-orange pools `#FF9A3C`. **Silhouette:** elevated steel rail trestle.
- **Layout:** city street built on a soundstage floor; hard-edged flats of tall buildings, wet-looking road (a
  value trick, no real reflections), the trestle crossing over the road ahead.
- **Dressing:** boom mic swinging into frame edge, camera crane on a tracked base, two flat kits (apartment block,
  shopfronts), a few lit windows as emissive squares.
- **Hazards:**

| Hazard | Telegraph cue | Own key light |
|---|---|---|
| S2-1 Alley Truck, S2-6 Camera Car | headlights sweep across the lane, the nose enters first | cold white headlight cone |
| S2-2 Wrecking Ball | crane arm turns, ball swings on a visible cable | orange pool on the swing arc |
| S2-3 Crate Drop | crate sways on its hook; its shadow grows on lane L | a hard top light so the shadow reads |
| S2-4 Scaffold Topple, S2-5 Pipe Spill, S2-7 Fruit Cart, S2-8 Barricade Line | boards rain / straps snap / cart rolls off the kerb / sawhorses drop | a sodium pool on each |
| S2-9 Level Crossing | bell, crossing lamps alternate (2 a second or slower), train under the trestle | sodium plus the train's headlamp |

### Scene 3 "The Finale" (studio fuel depot and timber bridge)

- **Key:** fire red-orange `#FF5A1F`. **Silhouette:** giant gas-holder tank (also the strongest rim light).
- **Layout:** fuel depot with tanks and pipes on one side, the road running onto a long timber bridge (the MustCut
  stunt). Darker and denser than the other scenes, but lanes and lamps stay clear.
- **Dressing:** barrels in stacks, scaffold, floodlight on a stand, a fake burning drum (emissive + `NS_Fireball`).
- **Hazards:**

| Hazard | Telegraph cue | Own key light |
|---|---|---|
| S3-1 Fuel Drum Spill, S3-7 Pipe Rack Fall | the stack or rack shudders, the first wave falls | orange |
| S3-2 Wreck Slide, S3-9 The Ramp | a burning wreck (emissive + `NS_Fireball`) | its own fire light |
| S3-3 Flare Burst, S3-8 Fire Wall | pipes hiss, burners light in sequence | fire red-orange per jet |
| S3-4 The Bridge Goes (long MustCut) | planks creak, dust drops, spans fall one by one; "DIRECTOR'S NOTE: cut" card | hot orange from below |
| S3-5 Tanker Jackknife, S3-6 Crane Hook | air brakes hiss / the hook block starts its swing | orange |
| S3-10 The Gas Holder | the lattice glows, the fireball grows from the right | the scene's strongest rim light |

- Fires and sparks are Niagara (`NS_Fireball`, `NS_Sparks`). The one-pager's `NS_CutFlash` is renamed **`NS_SpliceGrain`**
  (Proposal): the cut is one black frame plus a grain burst, never a flash, and the name should not invite a white one.

## 7. Camera grammar

| Moment | Camera | Starting values and notes |
|---|---|---|
| Gameplay | chase cam behind and above the car, spring-arm lag | FOV ~80 degrees; lean with the car; tiny FOV kick on RT rev (~3 degrees, cosmetic, gdd §2) |
| Hold | the same camera; world goes black and white with the workprint overlay | time eases to 0.3x over 150 ms; one **landing inset** from one low-res SceneCapture that runs **only while held** (gdd §3), in colour |
| Cut | locked camera, hard cut | 60-80 ms hit-stop, one black splice frame, 5% punch-in, timecode jump (gdd §3) |
| Crash | impact view | 120 ms hit-stop, canned flip, hard cut to black, clapper "CUT! TAKE n" (gdd §4) |
| Replay | three CineCamera setups | see below |

**Replay setups (three CineCameras, gdd §6):**
- **A: low side-tracking.** Wheel-height, keeps pace beside the car. Best for speed.
- **B: high crane wide.** Looks down from above and behind the hazard. Best for the whole stunt.
- **C: locked-off at the mark looking back.** Static, the car arrives into frame. Best for the landing and the near-miss.

Rules: **one camera change per cut** (gdd §6); letterbox 2.39:1 in replays only; the replay is deterministic from the
recorded run (gdd §6). The Director's Cut wrap clip is 10-15 s and skippable; it ends on a short title card.
The DELETED SCENE clip is 3 s: a ghost car (semi-transparent, drawn flat grey-white) drives into the hazard on its
authored danger lane and takes a canned crash, with a "DELETED SCENE" stamp and the same workprint overlay as the
hold. The wrap clips and clip stamps always carry text, not only colour.

## 8. Audio mood

Gdd §7 is the rule. This section is direction, not a script.

- **Music runs on real time and never seeks.** One CC0 track listed in `sourced-assets.csv`, or a MetaSound loop.
  **No local music generation** (local AI is off).
- Mood: 1970s action-library funk, about 110-125 BPM (direction only, starting value), bass-forward, dry drums,
  a little wah guitar. No vocals.
- Hold: low-pass on the music (not slowed) plus a projector whir.
- Cut: splice click, then a tape-stop/start stinger.
- Crash: clapper slam.
- Near-miss: whoosh scaled by tier (Wide short, Close longer, Perfect with a bright tick).
- Wrap: short orchestral-brass-style stinger (instrument direction only).
- UI: typewriter key ticks for slate and menu moves.
- Engine loop pitched from the speed curve (gdd §7); RT rev is cosmetic.
- **No voice and no dialogue** (gdd §5). "CUT!" is text plus the clapper sound.
- **Every essential cue also shows as text or a number** (gdd §4): near-miss word, film count, NO FILM stamp,
  DIRECTOR'S NOTE slate, take number. Sound never carries a rule alone.
- Sound names: `S_` prefix per `CLAUDE.md` (`S_Splice_Click`, `S_Clapper`, `S_Whoosh_Close`).

## 9. Typography direction

Three roles, three faces. Candidates are open licence (SIL OFL), named only; nothing is downloaded before the window.

| Role | Face candidates | Use |
|---|---|---|
| Condensed bold display | Bebas Neue | title, tier stamps, NO FILM, CUT! |
| Typewriter | Courier Prime | slates, scene cards, DIRECTOR'S NOTE, credits |
| Monospace | IBM Plex Mono or JetBrains Mono | timecode, film count, take number |

- Fallback: the UE default font, so a missing font never blocks the build.
- **Any font used must be logged in the sourced-assets ledger at import** (`stages/02_build/output/sourced-assets.csv`,
  via `scripts/sourced_assets.py`) during the jam, with its licence.
- **Minimum sizes** for the Legion Go S 8-inch 1920x1200 screen (starting values; check on the Legion): body text
  30 px, numbers 44 px, stamps 96 px, smallest allowed text 26 px.
- **Backdrop-box rule:** every line of HUD text sits on a black box at ~65% opacity (`jam-hud-readable-text.md`).
  Check readability on the lightest and darkest part of each scene in a packaged-build screenshot.
- Keep everything inside the 5% safe margin and anchored to a corner or the top centre (README HUD layout).

## 10. Reference images

All 17 pictures are in [`reference-images/`](reference-images/) (made 2026-11-11). The car and set plates:

- [`prejam-ref-01-hero-car.jpg`](reference-images/prejam-ref-01-hero-car.jpg)
- [`prejam-ref-02-scene1-set.jpg`](reference-images/prejam-ref-02-scene1-set.jpg)
- [`prejam-ref-03-scene2-set.jpg`](reference-images/prejam-ref-03-scene2-set.jpg)
- [`prejam-ref-04-scene3-set.jpg`](reference-images/prejam-ref-04-scene3-set.jpg)
- [`prejam-ref-05-stunt-midair.jpg`](reference-images/prejam-ref-05-stunt-midair.jpg)

HUD and menu mock-ups 06-11 are listed in [`hud-ui-spec.md`](hud-ui-spec.md); the storyboard sheet 12 in
[`storyboards.md`](storyboards.md); the concept sheets 13-17 (car and driver directions, liveries, crash beat, colour
script) in [`concepts.md`](concepts.md). What each picture really shows, and where it differs from the text (for example 04
has no landing mark, 07 draws a hatchback, not the coupe, and its hold inset is grey), is in [`PREJAM-DECLARATION.md`](PREJAM-DECLARATION.md).
**Pictures are mood only.** Where a picture disagrees with this text or with `gdd.md`, the text wins. None is a game
asset (README, Rule 7(h)).

## 11. Do not

- No Chaos physics car (spline plus lane offset, canned flip).
- No humanoid actors (gdd §5).
- No white flash, anywhere; the splice is one black frame.
- No colour-only cue; every cue has a word, shape or number too.
- No music seeking; music runs on real time.
- No Common UI; plain UMG with explicit focus (gdd §8).
- No licensed car kit; the hero car is built in the jam (gdd §7).
- No local music generation, no banned models (see `AGENTS.md`).
- No third-party logos, brands or real film titles in set dressing or signage.

## 12. Open questions

1. Decided by hub 99 (2026-11-11): the hold is full black and white per the GDD, the mark included; only the landing
   inset is in colour, and the UMG HUD stays in colour (section 2).
2. Resolved 2026-11-11: the hazard tables above use the [`storyboards.md`](storyboards.md) roster names; that file is
   the single stunt list.
3. Saturation step per kept shot (0.1) is a starting value; the GDD gives none.
4. Font and music choices are not made. A track must be picked and logged by Fri at the latest.
5. Lane change ease (0.15 s) and FOV 80 come from planning notes, not the GDD; the owner tunes them by hand.
