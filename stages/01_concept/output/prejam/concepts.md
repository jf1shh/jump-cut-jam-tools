# Jump Cut: concepts (hero car, driver, car mods, crash feel, music source, colour script and VFX)

2026-11-11. **Pre-jam planning text only (Rule 7(h)). Nothing here is built, downloaded or recorded before Wed Nov 11
21:00 PT**: no mesh, material, Niagara system, sound, music or widget. [`../gdd.md`](../gdd.md) is the build target and
wins over this file. Shared names, colours and sets come from [`README.md`](README.md); the look rules are in
[`style-guide.md`](style-guide.md). This file adds the owner's add-ons (relayed by the hub) that the pack did not cover.

Where an add-on goes past the GDD, it is written as options with a recommendation and listed in README "Open decisions"
(items 17-21). **The owner took every pick on 2026-11-11 15:25 PT ("Yes, use the picks"); each section below ends with its
DECIDED line.**

Pictures 13-17 in [`reference-images/`](reference-images/) go with this file. They are mood only; where a picture
differs from this text, the text wins (captions and differences: [`PREJAM-DECLARATION.md`](PREJAM-DECLARATION.md)).

## 1. Hero car: three directions

All three fit the film-set look: toy-scale, built in the jam from boxes and cylinders (GDD §7), four separate wheels
that spin, front wheels that steer, the README car palette (cream `#F1E5C8`, signal red `#C8312F`, black trim
`#1A1A1A`), driven on the spline plus lane offset (style-guide §5). Picture:
[`prejam-ref-13-car-directions.jpg`](reference-images/prejam-ref-13-car-directions.jpg) (A, B, C left to right).

| | A "Number 7" coupe | B "Camera Wagon" | C "Cage Buggy" |
|---|---|---|---|
| Silhouette | chunky two-door 1970s coupe, twin red stripes bonnet to tail, "7" on doors and roof, roll cage behind the glass | long boxy estate, one wide red band down the side, roof rack with a small film camera on an arm | open-top buggy, exposed red tube cage, stubby nose, big tyres |
| Story | the stunt car of the film | the crew's camera car doing its own stunts ("the car films the shot") | a stunt rig, half built |
| Read from the chase cam | strong: wide cream box, stripes show the heading | strong: the roof camera is a clear marker from behind | weak: thin tubes shimmer at Medium scalability and in the low-res landing inset |
| Read in black and white | best: cream is the lightest big shape (style-guide §5) | good | poor: mostly cage and tyre, little light surface |
| Build cost in the jam | baseline (style-guide §5 table) | +~45 min (longer body, rack, camera) | +~1.5 h (cage tubes), and an open cockpit shows the driver (see §2) |
| Fit with the pack | the car in pictures 01-11 | new; 4.8 m long, still fits a 4 m lane | conflicts with GDD §5 if the driver must show |

**Recommended: A, the "Number 7" coupe**, exactly as style-guide §5 (no change). It is the anchor in pictures 01-12,
the cheapest, and the best black-and-white read. **DECIDED by owner 2026-11-11** (README item 21). B's roof camera is kept as a mood
idea only; it is not a mod (see §3).

## 2. The stunt driver: three directions

**GDD §5 puts "humanoid actors" out of scope** and style-guide §11 repeats it. So any driver needed an owner call
(README item 20, **DECIDED** 2026-11-11: D1). All three directions are original: faceless, full-face helmet, visor always down, no real person, no
existing character. Picture: [`prejam-ref-14-driver-directions.jpg`](reference-images/prejam-ref-14-driver-directions.jpg).

| | A "Number 7" | B "The Double" | C "The Stand-in" |
|---|---|---|---|
| Look | cream race suit with two red stripes, cream helmet with a red stripe, black visor, black gloves (matches car A) | padded tan work jumpsuit, knee and elbow pads, scuffed red helmet, clapperboard under the arm | pale jointed wooden mannequin, cream helmet, black gloves |
| Idea | the stunt driver the film is about | the double who does the take the star will not | the dummy the crew drives into hazards; it fits the DELETED SCENE ghost car |
| Silhouette in a car | cream helmet with a red stripe through the rear glass | red helmet (warm accent; reads as a red dot in black and white) | cream helmet, same as A |

**What a car game shows** (the camera is behind the car, GDD §8; the replays add a low side camera, style-guide §7):

| Where | What is visible | Cost |
|---|---|---|
| Play (chase cam) | the top of a helmet through the rear window | part of the car mesh |
| Hold, cut, crash | nothing new; in the canned flip the helmet turns with the car | none |
| Replay camera A (low side-tracking) | helmet and two gloved hands on the wheel | part of the car mesh |
| Title, scene card, Special Features | a pose (thumbs-up at "THAT'S A WRAP", arms folded against the car on the title) | only as a 2D title card made in the jam with the cloud image tools (GDD §7 already allows title cards); never a 3D figure |

**Options for the build:**

| Option | What | Cost | GDD fit |
|---|---|---|---|
| D0 | tinted windows, no driver | 0 | as written |
| D1 | a static helmet (sphere plus visor box) and two glove blobs on the wheel, part of the car mesh, no skeleton, no animation | ~30-45 min | a car part, not an actor (needs the owner to read §5 that way) |
| D2 | D1 plus one 2D pose card on the title or scene card | +~30 min (one image prompt, logged in `asset-pipeline-log.csv`) | 2D art, not an actor |
| D3 | a rigged 3D driver for menus and wrap poses | 4-8 h (rig, poses, animation import) | breaks GDD §5 |

**Recommended: direction A, built as D1** (helmet and gloves inside car A), D2 only if the Fri 19:00 AAA gate is met. **DECIDED:** the owner accepted this pick on 2026-11-11. It
reads as "someone is driving" in replays at almost no cost and never needs a rig. D3 is not recommended.

## 3. Car mods

"Mod" is not in the GDD. It could mean three things. Picture:
[`prejam-ref-15-liveries-mods.jpg`](reference-images/prejam-ref-15-liveries-mods.jpg) (four liveries, four rig parts).

| Option | What it is | Effect on play | Jam cost | GDD fit |
|---|---|---|---|---|
| M0 none | the car stays car A | none | 0 | as written |
| M1 liveries | 2-3 extra `MI_Car_*` children of `M_Car` (for example "Rehearsal primer": light grey with yellow tape; "Night Shoot": pale blue with orange stripes). A scene wrapped at 4 stars or more unlocks one, shown on the scene card ("NEW LIVERY"), worn from the next scene. Session only: no SaveGame (GDD §4, §5) | none | ~1-1.5 h: MIs 20 min, unlock rule and scene card line 45 min, both-input check 15 min | not in the GDD and breaks none of its rules; new scope not on the cut list; nothing persists, so it fits "nothing is built for a second session" (GDD §1) |
| M2 stunt-rig parts | a heavier cage, a push-bar, a side camera mount, chunkier tyres as extra meshes on the car | cosmetic only; if a part changed collisions (a push-bar that rams crates) it would break the authored stunts, where hazards are pure functions of `T` (GDD §1, §8) | ~45 min a part, cosmetic | cosmetic: fine; with play effects: breaks GDD §8 |
| M3 handling tweaks | faster lane change, more grip, more top speed | changes the tier timings (two hops in ~0.6 s), the near-miss bands and the per-scene speed curves f(T) that set every mark | 3-6 h plus retuning three scenes | breaks GDD §4 tuning and the Thu 20:00 gate data; speed belongs to the scene clock, not the car |

- **Black-and-white check:** a livery must keep the car the lightest big shape (style-guide §5). Dark liveries (the
  picture's steel blue and scorched black) fail it in the hold and in the inset, so they are out.
- **Judge window:** a judge sees Scene 1's wrap at about minute 1.5 (GDD §6), so a Scene 1 unlock is the only one most
  judges see.

**Recommended: M0 for the build; M1 only as a stretch after the Fri 19:00 AAA gate, and first to go** (above item 1 of
the GDD §10 cut order). M2 cosmetic parts are not worth the time; M3 is rejected. **DECIDED by owner 2026-11-11** (README item 17): M0 in the core build; M1 liveries a stretch after Fri 19:00, first to cut; handling tweaks rejected.

## 4. Crash look and feel

The GDD fixes the crash: 120 ms hit-stop, canned flip, clapper slam "CUT! TAKE n", hard cut to black, back at the
previous mark, impact to control in under 1 s (GDD §4). The timeline is
[`storyboards.md`](storyboards.md) Board 2; the slam widget is [`hud-ui-spec.md`](hud-ui-spec.md) §3.5. Picture:
[`prejam-ref-16-crash-beat.jpg`](reference-images/prejam-ref-16-crash-beat.jpg).

### Inside the canned-flip rule (recommended, P0)

| Part | Proposal (starting values) |
|---|---|
| Flip | three canned flips picked by the hit side: hit on the left rolls right, hit on the right rolls left, a head-on hit goes nose-over. Each lasts the 400 ms of Board 2 (120-520 ms). Curves, not physics, so the wrap clip and the DELETED SCENE ghost crash replay them exactly (GDD §6) |
| Camera | the chase cam stops following at impact and holds still (Board 2); one 120 ms shake with the hit-stop (off with the screen-shake switch, onboarding §5); no FOV punch (that belongs to the cut) |
| Hit-stop | 120 ms freeze (GDD §4); everything freezes, debris included |
| Debris | Niagara only, no simulated bodies: `NS_CrashSplinters` (plywood planks and splinters as mesh particles), `NS_CrashDust` (a puff tinted to the scene key), `NS_TyreSmoke` (shared with lane changes), and one hubcap mesh particle rolling away (the gag) |
| The hazard | keeps its authored curve; hazards never react to the car (pure functions of `T`, GDD §1, §8). Debris sells the hit |
| "CUT!" beat | the clapper slams at 520 ms with a crack; "CUT! TAKE n", then "BACK TO MARK k" (onboarding §3). Text only: no voice (GDD §5) |
| After the cut | a clean car at the mark: a new take, so no damage carries over |
| Safety | no white or bright flash from fire or sparks; the black frame is the only hard change (GDD §3, style-guide §3) |

### Real physics (README item 18; rejected)

| Option | What | Cost | Risk |
|---|---|---|---|
| P1 hybrid debris | canned flip; 2-4 loose parts (hubcap, bumper) spawned as simulated bodies at impact, destroyed at the hard cut | ~1-2 h | low to medium: a different spill each replay; extra physics in the packaged build and the PSO prewarm; at 0.5 s on screen it looks almost the same as Niagara debris |
| P2 ragdoll car | at impact the car switches to simulated physics for ~0.5 s, then the hard cut resets it | ~3-5 h | high: the hand-over from spline to physics can pop; replays must record transforms instead of replaying the canned flip; the under-1 s reset must clear physics state; packaged physics can differ from the editor |
| P3 Chaos vehicle | Chaos vehicle movement for driving and crashes | 1-2 days | breaks GDD §7, §8 (spline plus lane offset), the tiers, the landing and the determinism test; the Day 1 feel budget is spent on the car instead of the cut |

**Recommended: P0**, the GDD's canned flip with the three variants and the Niagara debris above. **DECIDED by owner 2026-11-11:** P0; P1-P3
are out.

## 5. Music source

GDD §7: music runs on real time and never seeks; "one CC0 track listed in the sourced-assets ledger, or a MetaSound
loop (no local music generation: local AI is off)". Mood: style-guide §8 (1970s action-library funk, 110-125 BPM, no
vocals). Rules: sourced assets are allowed but **not reviewed or scored** and must be listed (Rule 15(c), Rule 1(d));
AI-made content is **not** a sourced asset (Rule 15(c)). **No audio is made or downloaded before 21:00 PT.**

| Option | What | Licence and logging | Cost | Risk |
|---|---|---|---|---|
| A CC0 track (GDD option 1) | one instrumental track whose page says CC0 1.0 (public domain dedication); loopable or long enough for a run | no credit is required by CC0, but list it anyway: `scripts/sourced_assets.py` into `stages/02_build/output/sourced-assets.csv` (name, source URL, licence, author, files, date) and in the submission. Reject "royalty free" store licences, CC BY-NC and anything with samples of other records. Find it in a browser (no `curl`/`wget` of store pages, AGENTS.md) | 1-2 h to find, check and log | low; not scored for Audio, but the treatment (low-pass, stingers) and every SFX are ours and are scored |
| B MetaSound score (GDD option 2) | an 8-bar funk loop built in the jam from MetaSound oscillators, noise and envelopes (bass, kick, hats, a filtered wah stab) | original; nothing to license; log the build in the dev log | 3-5 h | medium: can sound thin or like chiptune; an agent cannot hear it, so the owner must judge it by ear |
| C cloud AI music after 21:00 (not in the GDD) | one instrumental track from a cloud music service | counts as our content, not sourced (Rule 15(c)); log provider and prompt in `asset-pipeline-log.csv` and the dev log. The provider's terms must grant commercial use of outputs on the plan used (often paid plans only). Repo rule: a key, a `*_TERMS_REVIEWED` date and a repo adapter (`_config/reference/ai-providers.md`); no music adapter exists and `contest_guard.py` blocks raw calls to music hosts, so it is an adapter written in the jam or the owner using the web page by hand | 1-3 h | medium: terms, tracks that sound like a known song, judges' view of AI music; vocals must stay off (English-only and teen rules) |

Local generation (`scripts/gen_music.py`, ACE-Step) stays off: GDD §7 and local AI is off for the jam.

**Recommended: A**, one CC0 track, with the hold low-pass, the tape-stop and wrap stingers built as MetaSounds. B is the
fallback if no CC0 track fits by Fri 12:00 (style-guide §12 Q4). C only if the owner picks it and reads the
provider's terms first. **DECIDED by owner 2026-11-11** (README item 19): A, with B as the fallback and C only after the owner reads that
provider's terms; the track itself is picked after 21:00 PT.

## 6. Colour script, VFX list, mood notes

Style-guide §2 already has the palette, the per-scene grading and the saturation rules; §4 the lighting; §6 the
per-hazard key lights. This section adds only the run-long colour arc, one VFX list and a mood line per screen.
Picture: [`prejam-ref-17-colour-script.jpg`](reference-images/prejam-ref-17-colour-script.jpg).

### Colour script (how colour moves through one run)

| Beat | Saturation | Dominant / accent | Note |
|---|---|---|---|
| Title | full | void black / one tungsten spot on the cream car | the only fully lit moment before play |
| Scene 1 start | 0.5 floor | amber `#FFB04A` / gaffer yellow at each mark | calm, sun-faded |
| Any hold | 0 (full black and white) | grey world / the landing inset in full colour | "only the landing is in colour" (README item 4) |
| Kept shots | +0.1 each (style-guide §2) | the scene key warms up | the player earns colour |
| Crash | holds the current value | dust in the scene key | the black frame resets nothing but the car |
| Scene 1 wrap clip | the run's value, letterboxed | amber | the DELETED SCENE clip uses the workprint look of the hold |
| Scene 2 | back to 0.5 | steel blue `#5B86C9` / sodium pools `#FF9A3C` | cold; the warm pools are where the hazards are lit |
| Scene 3 | back to 0.5 | fire red-orange `#FF5A1F` / emissive fire | darkest scene; fire is the brightest thing, lanes stay clear |
| Final reel and Special Features | the run's value | void black / yellow focus `#FFC93C` | the menu is dark so the yellow cursor leads |

Every scene starts back at ~50% (GDD §7).

### VFX list (all Niagara, `NS_` prefix per `CLAUDE.md`)

None of these is needed for the Thu 20:00 gate. Four are Fri 19:00 scope: `NS_SpliceGrain`, `NS_TyreSmoke`, `NS_CrashDust`, `NS_CrashSplinters`; the other five come after.

| System | Where | Notes |
|---|---|---|
| `NS_SpliceGrain` | the cut | grain burst only, never a flash (style-guide §6) |
| `NS_TyreSmoke` | lane changes, crash | short puffs, scene-key tinted |
| `NS_CrashSplinters`, `NS_CrashDust` | crash (§4) | mesh particles, no physics |
| `NS_FacadeDust` | facade, scaffold and water-tower falls | one burst as it lands |
| `NS_WaterSplash` | S1-4 the water tower | the MustCut's payoff in the wrap clip and the DELETED SCENE |
| `NS_Sparks` | Scene 3 burners, pipe rack, crane hook | already named in style-guide §6 |
| `NS_Fireball` | Scene 3 wrecks, fire wall, the gas holder | one light at most per system; capped emissive (no white flash) |
| `NS_Embers` | Scene 3 ambient | low count, drifts through the light |

Budget (starting values): Medium scalability default (GDD §8); each system under ~200 particles; every system spawned
once on the title prewarm (GDD §8). `NS_FacadeDust`, `NS_WaterSplash`, `NS_Embers`, `NS_CrashSplinters` and
`NS_CrashDust` are new names in this file (**Proposal**).

### Mood notes (one line per screen)

- **Title:** the backlot at night before the shoot; hushed, one lamp on, the car waiting.
- **Scene 1 "Rehearsal":** warm, forgiving, a little comic; the crew is still setting up.
- **Scene 2 "The Chase":** tense and cool; the car dives between pools of light under the trestle.
- **Scene 3 "The Finale":** hot, loud, the studio burning its whole budget at once.
- **Wrap clips and the final reel:** proud; the player's run cut like a trailer.
- **Special Features:** DVD-menu nostalgia; warm, quiet, a little cheeky (the Critic's Review).

## 7. Open decisions from this file

All are in README "Open decisions": **17** car mods, **18** real-physics crashes, **19** music source, **20** the driver
(GDD §5), **21** hero car direction A. All five are DECIDED (owner, 2026-11-11).
