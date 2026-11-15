# Jump Cut pre-jam prep pack: declaration

2026-11-11, written before the contest window opens (Wed Nov 11 21:00 PT). For the submission and for any version-control
review Epic asks for (Official Rules 7(h)): what is in [`stages/01_concept/output/prejam/`](.), who or what made each file,
and the exact prompt for every picture.

## What this pack is, and is not

- **Planning text and labelled reference pictures only.** No gameplay, level, Blueprint, C++, widget, material, mesh,
  texture, sound or music exists in it. Rule 7(h) allows AI tools, agent configs, prompts and scripts before the
  window; this pack is the planning those tools work from.
- **No file here is imported into the Unreal project or shipped.** Every picture has a burned-in strip reading
  "PRE-JAM REFERENCE, NOT A GAME ASSET". Any in-game art is made inside the window and logged in
  `stages/02_build/output/asset-pipeline-log.csv` (AI-made) or `stages/02_build/output/sourced-assets.csv` (sourced).
- **The build target is [`../gdd.md`](../gdd.md)** (locked 2026-11-11 13:31 PT). This pack never edits it.
- Requested by the hub session (hub 98) for the owner, Jared Fisher. The owner wrote none of the text below; the GDD
  decisions it builds on are the owner's (see the GDD header).

## Text files

| File | Made by | How |
|---|---|---|
| [`README.md`](README.md) | Claude Opus 5.5 (Claude Code, lead session) | written from `gdd.md` and `jump-cut-concept.md` |
| [`storyboards.md`](storyboards.md) | Claude Opus 5.5 | written by the lead; consistency edits in a second lead session the same day |
| [`style-guide.md`](style-guide.md) | Claude Sonnet (Claude Code subagent), edited by Claude Opus 5.5 | subagent draft from the GDD and README anchors; the lead aligned hazard names, Niagara names and picture notes |
| [`hud-ui-spec.md`](hud-ui-spec.md) | Claude Sonnet (Claude Code subagent), edited by Claude Opus 5.5 | subagent draft; the lead fixed wireframe numbers, sound names, a flicker rate and the open questions |
| [`onboarding.md`](onboarding.md) | Claude Opus 5.5 | written by the lead |
| [`fun-plan.md`](fun-plan.md) | Claude Opus 5.5 | written by the lead |
| [`concepts.md`](concepts.md) | Claude Opus 5.5 (Claude Code, add-ons session) | written from `gdd.md`, the pack and the owner's add-on list relayed by the hub (hub 99) |
| `PREJAM-DECLARATION.md` (this file) | Claude Opus 5.5 | written by the lead; prompts copied by script from the saved `prompt.txt` files |

**Second pass, 2026-11-11 afternoon (Claude Opus 5.5, add-ons session):** `concepts.md` and pictures 13-17 added; README
"Open decisions" updated with the hub 99 decisions, the owner add-on calls (17-21) and the title check (22). The Fable
review fixes and hub 99 decisions in `storyboards.md`, `onboarding.md`, `hud-ui-spec.md`, `fun-plan.md` and
`style-guide.md` were made by a Claude Opus 5.5 subagent (a fork of that session) and checked by the session.

Reviews: a Claude Sonnet subagent opened and checked pictures 01-12 against their prompts and the game rules (results
in the table below); the add-ons session opened and checked 13-17 itself (one roll rejected, see below). A Claude Fable agent reviewed the whole pack for fun, clarity, ease of use and contradictions with
the GDD; see "Review" at the end.

## Pictures

**Tool:** Cursor CLI (`agent -p --trust --sandbox enabled --workspace <empty scratch folder per picture>`), using
Cursor's built-in image generation tool. **The tool reported no model name** for any picture. Run 2026-11-11 between
13:52 and 14:02 PT, four at a time, each in its own empty sandboxed folder.

**Post-processing (Python Pillow):** each 1280x720 PNG got a 34 px black strip added below it with the text
"PRE-JAM REFERENCE, NOT A GAME ASSET | Jump Cut prep pack 2026-11-11 | <file name>", and was saved as a 1280x754 JPG.
Picture 12's strip text ran off both edges, so the strip was redrawn the same day at a smaller size (DejaVu Sans Bold);
the picture itself was not changed.

**Status:** these are not entries in `asset-pipeline-log.csv` (that log is for game content made in the window), and
Cursor is not one of the repo's image adapters in `_config/reference/ai-providers.md`. The hub chose Cursor for these
reference pictures; if the owner wants the declaration in the dev log, quote this section.

**Wrapper.** Each prompt below was sent inside this instruction (`{name}` = the job name, `{prompt}` = the prompt):

```text
Generate exactly one image with your image generation tool and save it in this workspace as {name}.png. Do not write any other files. After saving, reply with the file path and the name of the image model if the tool reports one. Image brief: {prompt}
```

**Pictures win nothing over text:** where a picture differs from the docs, the docs and the GDD win.

| # | File | What it really shows (visual check) | Differences from the docs |
|---|---|---|---|
| 01 | [`prejam-ref-01-hero-car.jpg`](reference-images/prejam-ref-01-hero-car.jpg) | Hero stunt coupe turnaround (three-quarter front, side with the red 7, rear) on a warm-grey backdrop. | none |
| 02 | [`prejam-ref-02-scene1-set.jpg`](reference-images/prejam-ref-02-scene1-set.jpg) | Scene 1 backlot street: a tipping facade on the right, one yellow tape mark across all lanes with a clapper sign, the water tower. | the tape sits slightly right of centre |
| 03 | [`prejam-ref-03-scene2-set.jpg`](reference-images/prejam-ref-03-scene2-set.jpg) | Scene 2 day-for-night street: crane with wrecking ball, rail trestle, prop truck, crates, a thin yellow tape mark. | no clapper sign at the mark (the prompt did not ask for one) |
| 04 | [`prejam-ref-04-scene3-set.jpg`](reference-images/prejam-ref-04-scene3-set.jpg) | Scene 3 fuel depot: burning wrecks, drums, a sagging timber trestle, a ramp and the gas-holder tank. | **no landing mark shown**; an odd dark tail-light shape on the car |
| 05 | [`prejam-ref-05-stunt-midair.jpg`](reference-images/prejam-ref-05-stunt-midair.jpg) | Letterboxed replay frame: the car airborne off a ramp past an exploding drum, a camera crane behind. | the 'gas tank' reads as a small barrel, not the big gas-holder |
| 06 | [`prejam-ref-06-hud-drive.jpg`](reference-images/prejam-ref-06-hud-drive.jpg) | Driving HUD: SCENE 1 TAKE 1, timecode 00:00:21:12, CLOSE! stamp with +1 FILM, 6-cell strip with 4 filled, (A) LOOK. | the stamp has no backing box; generic 'STAGE 7' and 'SALOON' signs |
| 07 | [`prejam-ref-07-hud-hold.jpg`](reference-images/prejam-ref-07-hud-hold.jpg) | Black-and-white hold: one NEXT MARK inset with one ghost car at the yellow tape, lane ticks, ring, 3 > 2 film, the prompt. | **the car is drawn as a hatchback, not the coupe**; the tape is faint; the facade is not clearly across the lanes; the inset is grey with only the tape in colour (the decided rule: the whole inset in colour) |
| 08 | [`prejam-ref-08-crash-take2.jpg`](reference-images/prejam-ref-08-crash-take2.jpg) | Crash: the car mid-flip over a fallen facade under a CUT! TAKE 2 clapper. | generic 'STAGE 7' / 'BACKLOT SET 3' signs; a palm tree |
| 09 | [`prejam-ref-09-results-screen.jpg`](reference-images/prejam-ref-09-results-screen.jpg) | Scene card: clapperboard 'SCENE 1 - THAT'S A WRAP.', 4 of 5 stars, stats, three buttons with NEXT SCENE focused. | pad glyphs in the hint bar instead of text; numbers are mood, not the HUD spec's example |
| 10 | [`prejam-ref-10-special-features.jpg`](reference-images/prejam-ref-10-special-features.jpg) | Special Features menu with all six items and the car jumping a fireball. | not letterboxed; a 'STAGE 7' sign |
| 11 | [`prejam-ref-11-title-screen.jpg`](reference-images/prejam-ref-11-title-screen.jpg) | Title: the spliced JUMP CUT logo, the tagline, 'Press (A) or SPACE', the car under a spotlight, a camera crane and the water tower. | a 'STAGE 7' sign |
| 12 | [`prejam-ref-12-storyboard-cut-moment.jpg`](reference-images/prejam-ref-12-storyboard-cut-moment.jpg) | Six-panel pencil storyboard of the cut: facade tips, black-and-white inset, release, black frame, landed past the collapse, stamp. | the tape runs along the road in places, not clearly across it; label strip redrawn (see below) |

**Pictures 13-17 (second batch).** Same tool, wrapper, style and post-processing. Run 2026-11-11 between 14:20 and
14:30 PT, five at a time, each in its own empty sandboxed folder; the tool again reported no model name. Strip text in
DejaVu Sans Bold 20 px (19 px for 14 so the file name fits), gaffer yellow on near-black, JPG quality matched to 01-11.

| # | File | What it really shows (visual check) | Differences from the docs |
|---|---|---|---|
| 13 | [`prejam-ref-13-car-directions.jpg`](reference-images/prejam-ref-13-car-directions.jpg) | Three cars on a warm-grey backdrop, lettered A, B, C: the striped coupe with a boxed 7 and a roll cage, a long wagon with a roof rack and a film camera, an open buggy with a red tube cage and empty seats. | all three sit high like lifted off-roaders; A reads closer to a two-door sedan than picture 01 |
| 14 | [`prejam-ref-14-driver-directions.jpg`](reference-images/prejam-ref-14-driver-directions.jpg) | Three helmeted figures, visors down, lettered A, B, C: cream suit with red stripes (thumbs-up), padded tan jumpsuit with a clapperboard, a jointed pale-wood mannequin in helmet and gloves; under each, the same driver at a steering wheel. | none (second roll; the first was rejected, below) |
| 15 | [`prejam-ref-15-liveries-mods.jpg`](reference-images/prejam-ref-15-liveries-mods.jpg) | The coupe in side view in four paint schemes (cream with red stripes and 7, primer grey with yellow tape and chalk marks, steel blue with orange stripes, scorched black and red) above four parts: tube cage, push-bar, camera mount, off-road tyres. | the blue and scorched liveries are darker than cream, which `concepts.md` §3 rules out for black-and-white reads |
| 16 | [`prejam-ref-16-crash-beat.jpg`](reference-images/prejam-ref-16-crash-beat.jpg) | Six-panel pencil storyboard: impact on a fallen facade, mid-air flip with debris, a clapperboard reading CUT!, a black frame, the car back on a tape strip with the facade standing ahead, pulling away. | the car is drawn as a modern four-door sedan, not the coupe; the tape is yellow-and-black striped and runs at an angle |
| 17 | [`prejam-ref-17-colour-script.jpg`](reference-images/prejam-ref-17-colour-script.jpg) | Eight tall thumbnails with a colour bar under them: amber street, black-and-white street with a colour inset, warmer street, blue night street under a rail bridge, clapper over a wreck, burning fuel depot with a gas holder, letterboxed fireball jump, dark menu with a yellow highlight. | thumbnails are portrait, not 16:9; generic sedans; frame 5 shows a wrecked car (the crash keeps no damage) |

**Rejected roll.** The first roll of 14 drew C (the wooden stand-in) as a figure in a cream jumpsuit with a brown chin
and brown hands under the visor: it read as a person, not a wooden dummy, against "no face is visible". It was not
kept. Its prompt was the one quoted for 14 below except for the C sentence, which read: "Right: a faceless wooden stunt
mannequin like an artist's jointed figure, in a cream jumpsuit and black gloves, a plain cream helmet with a black
visor, standing stiffly."

**Hold colour (hub 99, 2026-11-11):** in the game only the landing inset is in colour during the hold. Picture 07 shows
a grey inset with only the yellow tape in colour and red stripes on the car in the grey world: a mood plate, the text
wins. Picture 17's frame 2 matches the decision.

### Exact prompts

**01 `hero-car`**

```text
Landscape 16:9. Pre-production concept sheet for an original video game, not based on any real car brand. Subject: a chunky, boxy 1970s-style two-door stunt coupe at toy scale, simple low-poly shapes that could be built from boxes and cylinders, cream white body with two bold signal-red racing stripes over the hood and roof, matte black bumpers and window trim, oversized separate black tyres with cream hubcaps, a roll cage visible through the windows, a small number 7 on the door. Show it as a turnaround: three-quarter front view large on the left, side view and rear view smaller on the right, on a neutral warm-grey studio backdrop with soft tungsten key light and a gentle floor shadow. Clean stylized render, no logos, no text other than the number 7.
```

**02 `scene1-set`**

```text
Gameplay frame from a third-person chase camera behind and above a small chunky boxy cream-white two-door stunt coupe with two signal-red racing stripes, black bumpers, oversized black tyres (car small in the lower third, centred), driving down a three-lane studio-backlot Main Street with dashed lane lines. Both sides: false-front 1970s shop facades of painted plywood held up from behind by visible wooden scaffold braces and sandbags; studio lamps on stands; cables on the ground. Ahead, about 40 metres away, one facade on the right is starting to tip toward the road, a rope snapping, a single amber key light on it. Beyond it a wide strip of bright yellow gaffer tape runs across all three lanes with a small yellow clapperboard sign on a stand at the roadside (the landing mark). On the horizon a tall wooden water tower silhouette against the black backstage void. Warm amber tungsten (3200K) key light, deep shadows. No readable text. Style: stylized low-poly toy-scale 3D render of a 1970s Hollywood studio backlot stunt movie, warm tungsten studio lights against a dark backstage void, light haze, colours at about half saturation (muted, filmic) unless stated, fine film grain. Original design: no real brands, no logos, no real people. 16:9 landscape.
```

**03 `scene2-set`**

```text
Gameplay frame from a third-person chase camera behind a small chunky boxy cream-white two-door stunt coupe with two signal-red racing stripes, black bumpers, oversized black tyres, on a three-lane soundstage city street shot day-for-night: cool steel-blue gel moonlight wash with small pools of sodium-orange practical streetlamp light. An elevated steel railway trestle crosses over the road ahead (the scene's landmark silhouette). A tall crane on the left swings a black wrecking ball across the lanes; a boxy prop truck noses out of a side alley on the right; stacks of wooden crates and a scaffold tower. Beyond the hazards a strip of bright yellow gaffer tape across the road marks the landing point. No readable text. Style: stylized low-poly toy-scale 3D render of a 1970s Hollywood studio backlot stunt movie, warm tungsten studio lights against a dark backstage void, light haze, colours at about half saturation (muted, filmic) unless stated, fine film grain. Original design: no real brands, no logos, no real people. 16:9 landscape.
```

**04 `scene3-set`**

```text
Gameplay frame from a third-person chase camera behind a small chunky boxy cream-white two-door stunt coupe with two signal-red racing stripes, black bumpers, oversized black tyres, on a three-lane road through a studio fuel-depot set for an action-movie finale. Landmark silhouette: an enormous cylindrical gas-holder tank in a steel lattice frame, lit from below by red-orange fire light. Burning wrecked cars, oil drums, a timber trestle bridge ahead whose middle span is starting to sag and drop in sections, sparks and embers in the air, a plywood stunt ramp in the middle lane. Red-orange fire key light, deep black backstage beyond, haze. No readable text. Style: stylized low-poly toy-scale 3D render of a 1970s Hollywood studio backlot stunt movie, warm tungsten studio lights against a dark backstage void, light haze, colours at about half saturation (muted, filmic) unless stated, fine film grain. Original design: no real brands, no logos, no real people. 16:9 landscape.
```

**05 `stunt-midair`**

```text
Cinematic replay frame, letterboxed to 2.39:1 with black bars top and bottom: low side-tracking camera; a small chunky boxy cream-white two-door stunt coupe with two signal-red racing stripes, black bumpers, oversized black tyres flies through the air off a plywood stunt ramp, wheels hanging, nose slightly up, a huge orange fireball blooming behind it from an exploding cylindrical gas tank on a studio fuel-depot set, debris and embers frozen in mid-air, a film camera on a crane in silhouette in the background. Full rich colour for this moment, warm fire light against the dark backstage. The money shot of a 1970s stunt movie. No readable text. Style: stylized low-poly toy-scale 3D render of a 1970s Hollywood studio backlot stunt movie, warm tungsten studio lights against a dark backstage void, light haze, colours at about half saturation (muted, filmic) unless stated, fine film grain. Original design: no real brands, no logos, no real people. 16:9 landscape.
```

**06 `hud-drive`**

```text
Video game screenshot mockup: a clean flat 2D HUD over a 3D gameplay frame. Frame: third-person chase camera behind a small chunky boxy cream-white two-door stunt coupe with two signal-red racing stripes, black bumpers, oversized black tyres on a three-lane studio-backlot street with plywood false-front facades and amber tungsten lamps; a prop truck has just swept past close on the right; colours muted at about half saturation. HUD, every element on a small dark translucent backing box, white text: top-left a small slate tag reading "SCENE 1  TAKE 1"; top-right a monospace timecode reading "00:00:21:12"; bottom-left a horizontal strip of 6 film frames with sprocket holes, 4 frames filled bright and 2 empty, beside a big number "4" and the word "FILM"; upper middle of the screen a tilted red rubber-stamp graphic reading "CLOSE!" with a small "+1 FILM" beneath it; bottom-right a small button hint reading "(A) LOOK". Clear, readable, minimal, cinematic. Style: stylized low-poly toy-scale 3D render of a 1970s Hollywood studio backlot stunt movie, warm tungsten studio lights against a dark backstage void, light haze, colours at about half saturation (muted, filmic) unless stated, fine film grain. Original design: no real brands, no logos, no real people. 16:9 landscape.
```

**07 `hud-hold`**

```text
Video game screenshot mockup of a slow-motion look-ahead moment. The whole 3D frame is black and white like an old film workprint: grain, sprocket holes down both edges, faint scratches. Third-person chase camera behind a small chunky boxy cream-white two-door stunt coupe with two signal-red racing stripes, black bumpers, oversized black tyres on a three-lane studio-backlot street; just ahead a plywood building facade is tipping over across the right two lanes, frozen mid-fall. Top centre of the screen: a picture-in-picture inset framed like a director's video-assist monitor (thin white frame), about a third of the screen wide, labelled "NEXT MARK", showing the road a few seconds ahead past the collapse with a yellow tape line across the road and a white outline ghost car in the left lane; three small lane ticks under the inset with the left one lit; a thin circular countdown ring like a film leader at the inset's corner. Top-right monospace timecode "00:00:07:03". Bottom-left a strip of 6 film frames with 3 filled and the text "3 > 2". Bottom centre a short prompt on a dark box: "Let go to CUT   (B) keep driving". Only the white HUD and the yellow tape line have any colour. Style: stylized low-poly toy-scale 3D render of a 1970s Hollywood studio backlot stunt movie, warm tungsten studio lights against a dark backstage void, light haze, colours at about half saturation (muted, filmic) unless stated, fine film grain. Original design: no real brands, no logos, no real people. 16:9 landscape.
```

**08 `crash-take2`**

```text
Video game screenshot mockup of a crash moment: a small chunky boxy cream-white two-door stunt coupe with two signal-red racing stripes, black bumpers, oversized black tyres frozen mid-flip, upside down in the air above a three-lane studio-backlot street, a plywood facade fallen across the lanes, dust and splinters. Over the frame a big black and white movie clapperboard slams in from the top-left, its slate reading "CUT!  TAKE 2" in white chalk letters. Slight motion blur, punchy comic timing, colours muted at half saturation. Style: stylized low-poly toy-scale 3D render of a 1970s Hollywood studio backlot stunt movie, warm tungsten studio lights against a dark backstage void, light haze, colours at about half saturation (muted, filmic) unless stated, fine film grain. Original design: no real brands, no logos, no real people. 16:9 landscape.
```

**09 `results-screen`**

```text
Video game results screen mockup, 16:9. Background: a frozen gameplay frame of a studio-backlot street, blurred and darkened. Centre: a large movie clapperboard-styled card (black slate, white chalk-style typewriter text, diagonal black and white clapper stripes on top) reading "SCENE 1 - THAT'S A WRAP". Under it four filled gold stars and one empty star with "4 / 5" beside them. Then a short tidy list: "Shots kept 4 / 6", "Perfect 1  Close 2  Wide 1", "Deleted scenes 1", "Takes 2", "Film left 3". At the bottom three buttons in a row: "NEXT SCENE" (focused, yellow outline), "DIRECTOR'S CUT TAKE", "RETRY SCENE". A small hint bar at the very bottom: "(A) Select  (B) Back". Clean, readable, 1970s film-title typography. Style: stylized low-poly toy-scale 3D render of a 1970s Hollywood studio backlot stunt movie, warm tungsten studio lights against a dark backstage void, light haze, colours at about half saturation (muted, filmic) unless stated, fine film grain. Original design: no real brands, no logos, no real people. 16:9 landscape.
```

**10 `special-features`**

```text
DVD-menu style end screen mockup for an original game called JUMP CUT, 16:9. Background: a darkened letterboxed still of a small chunky boxy cream-white two-door stunt coupe with two signal-red racing stripes, black bumpers, oversized black tyres jumping through an orange fireball on a studio set. Left side: large title "JUMP CUT" in a bold condensed 1970s film-title font, subtitle "SPECIAL FEATURES". Menu list under it: "Play the Director's Cut", "Deleted Scenes", "Critic's Review", "Credits", "Play Again", "Quit"; the first item highlighted with a yellow film-strip cursor. Early-2000s DVD menu feel mixed with 1970s movie poster typography. Style: stylized low-poly toy-scale 3D render of a 1970s Hollywood studio backlot stunt movie, warm tungsten studio lights against a dark backstage void, light haze, colours at about half saturation (muted, filmic) unless stated, fine film grain. Original design: no real brands, no logos, no real people. 16:9 landscape.
```

**11 `title-screen`**

```text
Title screen mockup for an original video game called JUMP CUT, 16:9: a dark studio backlot at night, a small chunky boxy cream-white two-door stunt coupe with two signal-red racing stripes, black bumpers, oversized black tyres parked under a single tungsten spotlight, a movie camera on a crane behind it, light haze. Big bold condensed 1970s film-title lettering "JUMP CUT" across the upper third with a film-splice break through the middle of the letters; under it the tagline "Your run. Your edit. Your director's cut." Small prompt at the bottom: "Press (A) or SPACE". Style: stylized low-poly toy-scale 3D render of a 1970s Hollywood studio backlot stunt movie, warm tungsten studio lights against a dark backstage void, light haze, colours at about half saturation (muted, filmic) unless stated, fine film grain. Original design: no real brands, no logos, no real people. 16:9 landscape.
```

**12 `storyboard-cut-moment`**

```text
A hand-drawn pencil storyboard sheet: 6 numbered panels in two rows, rough marker sketch with grey tones and a few yellow highlights, for a car-stunt video game moment. 1: a small stunt car drives down a studio-backlot street toward a plywood building facade that starts to tip. 2: the frame turns black and white, a small picture-in-picture inset at the top shows the landing point past the facade with a yellow tape line. 3: the facade falls toward the road in slow motion. 4: a single solid black frame. 5: the car is now past the collapse at the yellow tape line, camera pushed in slightly. 6: a rubber-stamp shape pops above the car and it drives on. Arrows show camera moves. No words, only panel numbers. Light paper texture, landscape 16:9.
```

**13 `car-directions`**

```text
Landscape 16:9. Pre-production concept sheet for an original video game, not based on any real car brand: three different original stunt-car designs side by side on a neutral warm-grey studio backdrop, each in three-quarter front view at the same scale, toy-scale, simple low-poly shapes that could be built from boxes and cylinders, all in the same palette: cream white body, signal-red stripes or panels, matte black trim, oversized separate black tyres. Left: a chunky boxy 1970s two-door stunt coupe with two red racing stripes over the hood and roof, black bumpers, a roll cage visible through the windows, a small number 7 on the door. Centre: a long boxy 1970s station wagon used as a film camera car, one wide red band along the side, a flat roof rack carrying a small boxy film camera on a short arm. Right: an open-top stunt buggy with an exposed red tube roll cage, cream body panels, a short stubby nose, big tyres and an empty seat. A large letter A, B and C on the floor under each car. Soft tungsten key light, gentle floor shadows. Clean stylized render, no logos, no text other than the number 7 and the letters A, B and C.
```

**14 `driver-directions`**

```text
Landscape 16:9. Pre-production character concept sheet for an original video game: three different original stunt-driver designs standing side by side, full body, front view, same scale, on a neutral warm-grey studio backdrop, stylized low-poly toy-like proportions (slightly large head and hands), simple shapes. Every driver wears a full-face helmet with the visor down, so no face is visible. Left: a classic 1970s stunt driver in a cream racing suit with two signal-red stripes down the front, a cream helmet with a red stripe and a black visor, black gloves, giving a thumbs-up. Centre: a stunt double in a padded tan work jumpsuit with knee and elbow pads, a scuffed plain red helmet with a black visor, a small clapperboard tucked under one arm. Right: a pale birch-wood jointed stunt mannequin like an artist's posing figure, wood grain clearly visible, round ball joints at the shoulders, elbows, hips and knees, no clothes except a plain cream helmet with a black visor and black gloves, standing stiffly. Under each figure a small inset of the same character seen only as a helmet and gloved hands on a steering wheel through a car window. A large letter A, B and C on the floor under each. Soft tungsten key light. Clean stylized render. Original designs: no real people, no real brands, no logos, no text other than the letters A, B and C.
```

**15 `liveries-mods`**

```text
Landscape 16:9. Pre-production concept sheet for an original video game: the same small chunky boxy 1970s two-door stunt coupe (simple low-poly shapes built from boxes and cylinders, oversized black tyres, black bumpers, roll cage visible through the windows) shown four times in a 2 by 2 grid in side view, each with a different paint scheme: top-left cream white with two signal-red racing stripes and a number 7 on the door; top-right flat primer grey with strips of yellow gaffer tape and chalk marks on the panels like an unfinished rehearsal car; bottom-left steel blue with sodium-orange stripes for a night shoot; bottom-right scorched black and dark red with soot streaks for a fiery finale. Along the bottom edge a row of four small separate add-on parts drawn as simple shapes: a heavier tube roll cage, a flat steel push-bar for the front bumper, a small boxy film camera on a side mount, and a set of chunkier off-road tyres. Neutral warm-grey studio backdrop, soft tungsten light. Clean stylized render, no logos, no text other than the number 7.
```

**16 `crash-beat`**

```text
A hand-drawn pencil storyboard sheet: 6 numbered panels in two rows, rough marker sketch with grey tones and a few yellow and red highlights, for a car-crash moment in a stunt-driving video game. 1: a small boxy stunt coupe clips a plywood building facade that has fallen across a studio-backlot street; an impact star, everything frozen for an instant. 2: the car flips onto its roof in mid-air, planks, splinters, dust and one hubcap flying off. 3: a big movie clapperboard slams shut across the frame over the flipping car. 4: a single solid black frame. 5: the car sits upright and undamaged on the road on a strip of yellow tape across the lanes, the facade still standing further ahead. 6: the car pulls away again toward the facade. Arrows show camera moves. No words except the word CUT! chalked on the clapperboard and the panel numbers. Light paper texture, landscape 16:9.
```

**17 `colour-script`**

```text
Landscape 16:9. A colour script for an original stunt-driving video game set on a 1970s Hollywood studio backlot: one long horizontal strip of eight small painted thumbnail frames in a row on a dark grey board, read left to right, loose painterly shapes, little detail, each frame showing a small boxy cream stunt car on a three-lane road. 1: a warm amber tungsten street of plywood facades at half saturation. 2: the same street in full black and white, with a small picture-in-picture inset at the top that is in full colour. 3: the street a little more colourful after a near miss, amber glow. 4: a cold steel-blue night street with small pools of sodium-orange light and an elevated steel rail bridge. 5: a black and white clapperboard over a flipped car, muted colours. 6: a fuel depot burning red-orange with a giant gas-holder tank silhouette. 7: a letterboxed wide frame in full rich colour of the car flying through a fireball. 8: a dark menu screen with one small glowing yellow highlight. Under the strip a thin bar of the matching dominant colours. No readable text, no numbers. Original design: no real brands, no logos, no real people.
```

## Review

A Claude Fable agent reviewed the pack read-only at commit `cb0ca47` (2026-11-11 afternoon): 6 must-fix and 8
should-fix items, plus its view on the four owner calls. All 14 were applied in the next commit; item 14 (can a cutter
meet S2-9 at 0 film?) was traced and accepted in writing in `storyboards.md` rather than changed. Hub 99 then decided
the four calls (README "Open decisions" 1-4). The review file stays in the session handoff folder, outside the repo.

## Tooling made before the jam (Rule 7(h))

Rule 7(h) allows AI tools, agent configs, MCP settings, prompt libraries and scripts before the window. These exist and
are declared here:

- **Prompt library:** [`_config/reference/prompts/`](../../../../_config/reference/prompts/) (index in its `README.md`):
  a house-rules block and one fill-in prompt per recurring job (lead kickoff, helper slice brief, review gate, cloud asset
  job, playtest, triage, package and ship check, dev log, handoff, nightly stop), plus the grey-box prompts in `greybox/`.
  Written by Claude Opus 5.5 (Claude Code) from the repo's own rules and templates.
- **Scripts:** [`scripts/`](../../../../scripts/), catalogued file by file in [`scripts/README.md`](../../../../scripts/README.md)
  (editor and MCP helpers, asset and provider adapters, packaging and Legion ship, playtest, jam clock and backup,
  contest guard hook).

These are tools and prompts, not game content: they contain no gameplay, level, art, audio or game code, and every
prompt has blanks that are filled inside the contest window. The `pre-jam-tooling` tag (first set 2026-11-10 at
`5e0972b`) is moved to the last pre-jam commit on `master` before 21:00 PT on Wed Nov 11 2026 (owner's choice,
2026-11-11), so it marks exactly what existed when the window opened, including this library.
