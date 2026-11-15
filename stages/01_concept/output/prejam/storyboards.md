# Jump Cut: stunt roster, shot lists and beat boards

2026-11-11, pre-jam planning text only (Rule 7(h)): no level, stunt, camera or replay exists before 21:00 PT. The build
target is [`../gdd.md`](../gdd.md); where this file disagrees with it, the GDD wins. Shared names and colours:
[`README.md`](README.md). Every stunt below is a **proposal** for the jam-night author: the counts, tiers and MustCut
placement come from the GDD, the stunt ideas, lanes and times are starting values to tune on the DataAsset.

## How to read the shot lists

- **Lanes:** L, C, R. The car starts every scene in C.
- **T** is scene time in seconds at the stunt's collision-on line. **Mark k** sits 2-3 s past stunt k in a clear zone
  (GDD §3; the DataAsset default is 2 s, so every cut lands before the next stunt's telegraph starts); mark 0 is the start line. The mark after stunt k is the landing for cutting k and the restart point for k+1.
- **Spacing (Proposal):** about 5 s from one mark to the next, so the next mark is never more than ~5 s ahead (GDD §3).
  After a stunt with a long collision span (the two MustCuts) the next stunt sits 5 s past the span's end, so no landing
  puts a hazard inside 2 s (GDD §3). Each stunt's key light snaps on and its telegraph starts about 2.5 s before
  collision-on; that is the read and when the cut window opens.
- **Tier** (GDD §4): *easy* = one lane change with 1.5 s or more of slack; *two-hop* = two lane changes inside ~0.6 s;
  *timed gap* = one lane change inside a ~0.6 s window (too early is hit by the hazard's first part, too late by its
  second). The car speed is fixed (f(T)), so every skill test is lane plus moment.
- **Near-miss** comes from closest approach (GDD §4). In three discrete lanes, closeness comes from **committing late**:
  the later you change into the safe lane, or the tighter you sit on the gap's edge, the closer the pass. That is the
  skill ceiling, and it is why every row names its "Perfect moment".
- **Cut** = release before the collision-on line; lands on mark k with the GDD §3 juice. **Crash** = back to mark k-1 with
  that mark's film (GDD §4). **Replay angle** is the CineCamera used when the replay passes this stunt (A low
  side-tracking, B high crane wide, C locked-off at the mark looking back; one change per cut, GDD §6).

## Scene 1 "Rehearsal": teach (6 stunts, 1 MustCut, 2 execution-tier)

Main Street backlot, amber tungsten, the water tower on the skyline. Base speed 18 m/s (starting value), surge +6 m/s for
3 s before S1-6. Driving time about 37 s; with the clapperboard, the first prompt and one crash, the wrap lands near
minute 1.5 from boot, as the GDD wants.

| # | Stunt | T | Tier | The read (telegraph, 2.5 s) | Drive line | Perfect moment | Replay angle |
|---|---|---|---|---|---|---|---|
| S1-1 | Leaning False Front | 7 | easy | ropes snap with a twang, the right-hand false front tilts 8°, dust at its base | C to L (the front falls across C and R) | change to L in the last 0.5 s before it lands | A |
| S1-2 | Prop Truck | 12 | easy | horn, headlights, a prop truck noses out of a left alley and stops across L and C | to R | slip into R late; the truck nose passes inside 0.6 m | B |
| S1-3 | Light Rig Swing | 17 | timed gap | a lamp truss on a crane arm starts a low sweep from R to L | into R inside the 0.6 s after the truss leaves it | enter R as the truss's tail clears | C |
| S1-4 | **The Water Tower** (MustCut) | 22-24 | MustCut | DIRECTOR'S NOTE: cut card; the tower's legs buckle, it falls across all three lanes (2 s fall) | none: cut is free (costs 0 film) | n/a | B (cut lands with the tower crashing behind) |
| S1-5 | Barrel Roll | 30 | easy | a flatbed tips; oil barrels roll across C and R | to L | stay in C until 0.5 s before, then L | A |
| S1-6 | The Big Facade | 35 | two-hop | music swell; the two-storey facade leans out from the left while a scaffold tower falls from the right | L to C to R inside 0.6 s as the gap travels | the second hop in the last 0.2 s | B then C |

**Film walk (GDD numbers: start 3, reel 6, cut -1, MustCut 0, Wide +1, Close +1, Perfect +2):**

| Player | S1-1 | S1-2 | S1-3 | S1-4 | S1-5 | S1-6 | Wrap film |
|---|---|---|---|---|---|---|---|
| Cuts all it can | cut 2 | cut 1 | cut 0 | MustCut 0 | must drive (easy) 1 | cut 0, or drive | 0-2 |
| Mixed (the target) | cut 2 (the prompt) | drive Close 3 | cut 2 | MustCut 2 | drive Wide 3 | drive Perfect 5 | 5 |
| Drives all it can | drive Wide 4 | Close 5 | Perfect 6 (cap) | MustCut 6 | Wide 6 | Close 6 | 6 |

The GDD's rules hold through film alone, with no cut counter: starting film 3 means at most three cuts in a row from a
fresh scene (GDD §4); the stunt after the cutter's zero point (S1-5) is easy; all-cut is impossible. The **likely zero
point** of a scene is where a player who cuts everything from the start first runs dry (after three cuts); after that a
player only spends film they just earned, which the film strip shows.

**Why this order:** S1-1 teaches the cut (the prompt sits here; the free crash is here). S1-2 teaches driving and the
near-miss stamp. S1-3 is the first execution stunt, so cutting is now worth film. S1-4 forces a cut at about 25 s (the only way
past is hold and release), which protects the Thu 20:00 gate item (a) "lands a cut inside 60 s". S1-6 is the set
piece and the wrap clip's money shot.

### Scene 1 shot list (beat by beat)

| Beat | Camera | What happens | Player input | Timing |
|---|---|---|---|---|
| Open | gameplay chase cam, locked behind the car | clapperboard over the start line: "SCENE 1  REHEARSAL  TAKE 1" plus the goal line "Drive the stunts. Cut the ones you can't. Film runs out." (GDD §2); "(A) ACTION!" after 1 s | press A / Space (Proposal O1 in [`onboarding.md`](onboarding.md); rolls on its own after 6 s) | clap; the board slides off as the car rolls; `T` starts |
| S1-1 arm | chase cam | false front tilts, key light snaps on; the first prompt appears: "Hold A to look. Let go to cut. B to keep driving." | hold A or steer L | prompt stays on until one hold-and-cut is done |
| S1-1 hold | same camera, world goes B&W workprint, time 0.3x over 150 ms | landing inset at top centre: mark 1 past the front, ghost car in the chosen landing lane | release to cut / B to cancel / lanes set the landing lane | cap 1.5 s real time, then auto-cancel |
| S1-1 cut | hard cut to the mark | 60-80 ms hit-stop, one black splice frame, splice click, 5% punch-in, grain burst, timecode jump, tape-stop stinger; one film cell punches out (3 to 2) | control is back at once | under 0.2 s total |
| S1-1 crash (free) | hold, flip, hard cut to black | 120 ms hit-stop, canned flip, clapper slam "CUT! FREE TAKE" (Proposal O3; not counted, GDD §2; the slate stays TAKE 1) | none | impact to control under 1 s, back at mark 0 |
| S1-2 drive | chase cam with lean on the lane change | truck nose passes close; stamp "CLOSE!" with whoosh, "+1 FILM" ticks into the strip, colour steps up | steer R | stamp 0.9 s on screen |
| S1-4 MustCut | chase cam | blue-pencil card "DIRECTOR'S NOTE: cut" slides in at mark 3, about 3 s before; the film counter shows "-0" on the cut | hold A, release | cut lands on mark 4 with the tower crashing behind (replay later shows it) |
| S1-6 set piece | chase cam, slight FOV widen during the surge | facade and scaffold fall from both sides; the gap travels L to R | two hops, or cut | key light on both hazards |
| Wrap | locked wide on mark 6 | "THAT'S A WRAP" slate, wrap stinger; music keeps running | none | 1.5 s, then the wrap clip |

## Scene 2 "The Chase": test (9 stunts, no MustCut, 3 execution-tier)

Day-for-night street, steel-blue moonlight with sodium pools, the rail trestle overhead. Base speed 22 m/s, surge before
S2-9. Driving time about 48 s.

| # | Stunt | T | Tier | The read | Drive line | Perfect moment | Replay angle |
|---|---|---|---|---|---|---|---|
| S2-1 | Alley Truck | 6 | easy | horn and headlights from a right alley; the truck blocks C and R | to L | late change to L | A |
| S2-2 | Wrecking Ball | 11 | timed gap | crane groans; the ball swings R to L on a long pendulum | into R inside 0.6 s after the ball leaves it | enter R as the chain clears | B |
| S2-3 | Crate Drop | 16 | easy | a crate sways on a crane hook; its shadow grows on L | stay out of L | pass the shadow's edge | C |
| S2-4 | Scaffold Topple | 21 | easy | scaffold boards rain, the tower leans over L and C | to R | late change to R | A |
| S2-5 | Pipe Spill | 26 | two-hop | a flatbed's straps snap; concrete pipes roll diagonally | R to C to L inside 0.6 s | second hop in the last 0.2 s | B |
| S2-6 | Camera Car | 31 | easy | the film crew's camera car swerves out from R and runs into C | to L | stay in C until it commits | C |
| S2-7 | Fruit Cart | 36 | easy | a street cart rolls off the kerb into L and C (fruit burst on any hit) | to R | late change to R | A |
| S2-8 | Barricade Line | 41 | easy | studio sawhorse barricades drop into L and R | to C | hold C, pass between them | B |
| S2-9 | Level Crossing | 46 | timed gap | bell rings under the trestle; a slow prop train crosses; the gap between the last two cars sweeps R to L | be in the gap's lane at arrival: change inside the 0.6 s window | ride the gap's edge | C (wrap clip money shot) |

**Film walk:** a cutter goes cut, cut, cut (0) and must drive S2-4, S2-6 and S2-8 (all easy), and can cut S2-5, S2-7 and
S2-9 with the film each drive earns. The three tier stunts (S2-2, S2-5, S2-9) are exactly where cutting is worth it.

**S2-9 at 0 film (traced, accepted):** with WIDE or CLOSE drives only, every stunt moves film by exactly 1, so film at
S2-9 is odd (3 plus eight steps) and never 0. It can be 0 only after a PERFECT (+2) plus two more cuts, for example cut,
cut, cut (0), S2-4 PERFECT (2), cut S2-5 (1), cut S2-6 (0), drive S2-7 (1), cut S2-8 (0). That is a skilled player
spending film they just earned, not the scene's likely zero point (after S2-3, followed by the easy S2-4), and the strip
reads 0 and "NO FILM" before the bell. A film pickup would change the GDD's one economy table, so there is none: S2-9
stays a timed gap, drivable at 0 film like every non-MustCut stunt (GDD §4).

### Scene 2 beats worth boarding

- **Open:** clapperboard "SCENE 2  TAKE 1" (no goal line now, the prompt does not return). The car starts in C.
- **S2-3 shadow read:** the crate's shadow on the road is the telegraph. In the hold it reads clearly at 0.3x; this is
  the scene's "readability" lesson.
- **S2-6 theme wink:** the camera car is the crew; on a near-miss the replay cuts to its own camera (angle C).
- **S2-9 surge:** speed rises for 3 s; the train bell starts 3 s out; a clean pass is the scene's wrap-clip money shot.

## Scene 3 "The Finale": twist (10 stunts, 1 long MustCut, 8 of the 9 others execution-tier)

Fuel depot and timber bridge, fire red-orange, the gas-holder tank on the skyline. Base speed 26 m/s, surge before S3-9.
Driving time about 62 s.

| # | Stunt | T | Tier | The read | Drive line | Perfect moment | Replay angle |
|---|---|---|---|---|---|---|---|
| S3-1 | Fuel Drum Spill | 6 | two-hop | a drum stack topples on the right; two waves of drums | C to R to C inside 0.6 s as the waves cross | second hop in the last 0.2 s | A |
| S3-2 | Wreck Slide | 11 | timed gap | a burning wreck slides from R across to L | into R inside 0.6 s after the wreck leaves it | enter R right behind the flames | B |
| S3-3 | Flare Burst | 16 | two-hop | pipes hiss; flame jets fire across L and C, then R | L to C to... (gap travels) inside 0.6 s | late second hop | C |
| S3-4 | **The Bridge Goes** (long MustCut) | 21-30 | MustCut | DIRECTOR'S NOTE: cut; the timber trestle drops span by span ahead of the car | none: cut is free and lands on the far bank | n/a | B (wide crane: the whole collapse) |
| S3-5 | Tanker Jackknife | 35 | easy | air brakes hiss; a tanker trailer swings across C and R | to L (1.5 s of slack) | late change to L as the trailer swings | A |
| S3-6 | Crane Hook | 40 | timed gap | a hook block swings low across lanes | enter the lane it just left inside 0.6 s | pass under the tail chain | C |
| S3-7 | Pipe Rack Fall | 45 | two-hop | a pipe rack collapses from the left in two stages | two hops inside 0.6 s | late second hop | B |
| S3-8 | Fire Wall | 50 | timed gap | gas burners ignite in sequence R to L | enter the lane that just went out, inside 0.6 s | enter as the flame drops | A |
| S3-9 | The Ramp | 55 | timed gap | a wreck burns in C before a plywood ramp; the ramp lip is in C only | from L into C inside the 0.6 s between the wreck and the ramp lip; the car arcs over the fire (the arc is spline height, no physics) | hop at the last moment | C (mid-air side shot) |
| S3-10 | The Gas Holder | 60 | two-hop | the tank's lattice glows; the fireball grows from the right, then debris from the left | R to C to L inside 0.6 s | second hop in the last 0.2 s | B then A (the final shot) |

S3-4 sits where a cutter runs dry: cut, cut, cut (0), then the free MustCut absorbs the zero point and S3-5 is easy
(decision D1 below). The ramp in S3-9 is
optional content: if it costs more than 30 minutes, flatten it and keep the timed gap. S3-10 is the stunt the stretch end
cards read ("Studio Cut" if cut and never restored, "Director's Cut" if driven or restored; GDD §6).

**D1, decided by hub 99 (2026-11-11):** GDD §4 says every Scene 3 stunt except the MustCut is execution-tier, and also
says the stunt after any likely zero point is "easy"; Scene 3 cannot do both, because a cutter at 0 film after S3-4 must
drive S3-5. S3-5 is tier **easy** (8 of the 9 non-MustCut stunts are execution-tier) and "easy after zero" is kept. Why:
the three-crash help shows a lane, not a moment, so it does not help a cutter through a timed gap.

## Beat boards (the five moments that make or break the game)

Each board is a row of panels to build and to judge against. Reference sheet:
[`reference-images/prejam-ref-12-storyboard-cut-moment.jpg`](reference-images/prejam-ref-12-storyboard-cut-moment.jpg).

### Board 1: the cut (the core verb; Day 1 feel budget item 1)

| Panel | Frame | Sound | Time |
|---|---|---|---|
| 1 | chase cam; hazard key light snaps on, telegraph starts | hazard cue (rope twang, horn) | T-2.5 s |
| 2 | player holds: world eases to 0.3x and full B&W workprint, sprocket edges, timecode runs; landing inset fades in at top centre with "NEXT MARK", ghost car in the landing lane, the inset in colour (only the landing is in colour); hold ring starts to drain | projector whir in, music low-passed (not slowed) | 150 ms ease |
| 3 | player taps a lane: the ghost car moves in the inset, the lane tick lights; the live car keeps its lane | soft tick | any time in the hold |
| 4 | release: freeze 60-80 ms | silence then splice click | 60-80 ms |
| 5 | one black splice frame | tape-stop stinger starts | 1 frame |
| 6 | landed on the mark, camera locked, 5% punch-in relaxing over ~0.3 s, grain burst, timecode digits jump, one film cell punches out | tape-start, whir out, music back to full | control at once |

If the cut window closes during the hold (the car reaches the collision-on line), the inset label changes to "DRIVE IT"
and release only cancels (Proposal; HUD spec). There is no cut counter: film alone limits cuts (GDD §4). At 0 film the
press does not enter the hold: "NO FILM" stamp and a dry click (Proposal; HUD spec).

### Board 2: the crash and take two (Day 1 item 3)

| Panel | Frame | Sound | Time from impact |
|---|---|---|---|
| 1 | impact freeze | crunch | 0-120 ms hit-stop |
| 2 | canned flip, camera holds still, debris | metal tumble | 120-520 ms |
| 3 | clapper slams in from top-left: "CUT! TAKE 3" | clapper crack | 520 ms |
| 4 | hard cut to black | hush | 1-2 frames |
| 5 | car at the previous mark, rolling, film at the mark's value, take slate fading | engine back in | under 900 ms: control |

No game-over screen, ever. After three crashes on the same stunt, the next hold shows the safe lane lit in the inset,
with no name or badge (GDD §4).

### Board 3: the near-miss (the skill ceiling)

| Panel | Frame | Sound |
|---|---|---|
| 1 | car holds its lane while the hazard closes in | rising hazard sound |
| 2 | late lane change, body roll, tyre smoke | tyre chirp |
| 3 | closest approach: the hazard passes inside the PERFECT band | whoosh (louder per tier) |
| 4 | stamp "PERFECT!" (largest size), "+2 FILM" ticks into the strip, saturation steps up | stamp thump, film tick |

WIDE, CLOSE! and PERFECT! always show as words (GDD §4); size and colour only add to the word.

### Board 4: the MustCut (theme in one beat)

| Panel | Frame |
|---|---|
| 1 | blue-pencil card slides in at the right: "DIRECTOR'S NOTE: cut"; the film counter shows "-0" |
| 2 | the hazard starts (tower buckles, bridge spans drop) |
| 3 | the hold: inset shows the landing past the wreck (far bank for the bridge) |
| 4 | the cut lands; the collapse happens behind the car. In the wrap clip the DELETED SCENE shows what the cut skipped |

If the player does not cut a MustCut, the car crashes and takes a take (GDD §4). There is no safe lane to show, so
**Proposal (D4):** the first prompt comes back on that stunt after the first crash there, not the third.

### Board 5: the wrap and the scene card

| Panel | Frame | Time |
|---|---|---|
| 1 | "THAT'S A WRAP" slate over a locked wide at the last mark; wrap stinger | 1.5 s |
| 2 | letterbox in (2.39:1); title card "THE DIRECTOR'S CUT OF SCENE 1" | 1 s |
| 3 | replay (see below), one camera change per cut | 7-10 s |
| 4 | "DELETED SCENE" slate; ghost car drives the authored danger lane into the cut hazard; canned crash (inside the 10-15 s clip) | 3 s |
| 5 | letterbox out; scene card slides up (stars, numbers, formula; see the HUD spec) | stays |

## The Director's Cut wrap clip (every scene, 10-15 s, skippable; GDD §6)

**Proposal (simplest build that keeps the GDD rule):** the clip replays the **last 7-10 s of the scene** at real speed,
from the mark before the set piece to the wrap, with the deterministic replay (the GDD's run recorder). The camera
changes **once per cut** the player made in that window; with no cut in the window it changes once per stunt, so a
clean run still gets coverage. Angles rotate A, B, C. Then one 3 s DELETED SCENE clip. Total 10-14 s.

- **Which deleted scene (Proposal):** a cut MustCut always ranks first, so Scene 1's is always the water tower and
  Scene 3's always the bridge (a MustCut is always cut, or the run cannot pass it). Otherwise the cut stunt with the
  highest tier (set piece first, then two-hop, timed gap, easy), the latest one if tied. If a scene has no cut at all
  (possible only in Scene 2), show a 3 s "NO DELETED SCENES" card instead (a fact about the edit, not a streak; GDD §4
  bans streaks).
- **Skip:** hold B or Esc for 0.5 s, ignored in the first 1.5 s (Proposal; HUD spec), because the player may still be
  pressing A when the scene ends.
- **Ghost car:** the hero car in a translucent workprint grey, driving the authored danger lane into the hazard at the
  hazard's real timing; canned crash, no physics.

| Scene | Likely clip content | DELETED SCENE |
|---|---|---|
| 1 | S1-5 and the Big Facade (S1-6); a cut there shows as a hard cut with the timecode jump burned in | the water tower falls on the ghost car |
| 2 | S2-8 and the Level Crossing | the highest-tier stunt the player cut (often the Wrecking Ball or Pipe Spill) |
| 3 | S3-9 ramp arc (angle C mid-air) and the Gas Holder | the bridge collapse onto the ghost car (the MustCut ranks first) |

## The final reel after Scene 3 (30 s cap; GDD §6) and Special Features

"Play the Director's Cut" on the Special Features menu plays the same reel. **Proposal shot list:**

| Time | Shot | Source |
|---|---|---|
| 0:00-0:02 | black slate "THE DIRECTOR'S CUT" in the title font; projector whir | card |
| 0:02-0:11 | three Scene 1 shots, about 3 s each | the player's best kept stunts in Scene 1, ranked PERFECT, CLOSE, WIDE (later stunt wins a tie), each centred on closest approach, angles A, B, C |
| 0:11-0:20 | three Scene 2 shots | same rule |
| 0:20-0:28 | three Scene 3 shots, always ending on S3-10 if it was driven or restored | same rule; the final shot is angle A, slowed only in the replay, not in play |
| 0:28-0:30 | "JUMP CUT" title card with the total stars | card |

Between shots, the player's own cuts appear as the same splice frame and timecode jump. The reel is letterboxed. The
Deleted Scenes item plays up to 3 clips (GDD §6): the three wrap-clip deleted scenes, one per scene, each under its
"DELETED SCENE" slate.

The reel doubles as video footage (GDD §8: continuous takes, the hold visible before each cut, gameplay in the first 5 s,
end on the title card). The submission video still needs real play with a visible hold; the reel alone does not show it.

## Director's Cut take (scene card option; GDD §6)

Replays the scene with the player's cut stunts restored and their marks switched off, for extra stars. MustCut stunts
stay cut: the director asked for that cut, and a MustCut cannot be driven. Board: the
clapperboard reads "SCENE 1  DIRECTOR'S CUT TAKE"; restored stunts carry a small "RESTORED" tag on their key light
card; the HUD's hold still works for stunts that were driven the first time. Offered **once per scene**: after the take
the button is gone from that scene's card, so it cannot loop. **D3, decided by hub 99 (option A):** the scene keeps the
better of the two runs, plus 1 star (cap 5) if every restored stunt is kept ([`fun-plan.md`](fun-plan.md) §6).

## Open decisions from this file

- **D1** decided by hub 99: S3-5 is easy; "easy after zero" is kept (above).
- **D2** The wrap-clip window and deleted-scene pick (a cut MustCut ranks first) are proposals; confirm or replace when
  the run recorder lands.
- **D3** decided by hub 99: option A, offered once per scene (above and fun plan).
- **D4** MustCut help: bring back the first prompt after the first crash there (Proposal), since a MustCut has no safe
  lane.
