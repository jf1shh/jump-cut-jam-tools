# Jump Cut: pre-jam design prep pack

2026-11-11, written before the contest window opens (Wed Nov 11 21:00 PT). **Planning text and reference pictures only
(Rule 7(h)).** Nothing here is a game asset: no file in this folder is imported into the UE project or shipped. The
pictures are labelled "pre-jam reference, not a game asset" and listed with their tool and prompt in
[`PREJAM-DECLARATION.md`](PREJAM-DECLARATION.md).

**[`../gdd.md`](../gdd.md) is the build target and wins over everything here.** This pack only turns it into shot lists,
screens, words and pictures the team can build from on jam night. Where the GDD leaves a number or a rule open, this
pack writes a *proposal* (marked **Proposal**) and lists it under "Open decisions" below for the owner or the hub.

## What is in the pack

| File | What it is for |
|---|---|
| [`storyboards.md`](storyboards.md) | Proposed stunt roster for Scenes 1-3 (25 stunts) and a shot list per stunt: camera, beat, drive-or-cut moment, near-miss moments, crash-to-control; the Director's Cut wrap clip and the final 30 s reel |
| [`style-guide.md`](style-guide.md) | Palette, film look, lighting, car and set look, camera grammar, audio mood, typography direction |
| [`hud-ui-spec.md`](hud-ui-spec.md) | Every HUD element and its purpose, wireframes, menus (boot, title, pause, scene card, wrap clip, Special Features), controller and keyboard map, readability rules |
| [`onboarding.md`](onboarding.md) | The first 60 seconds (teach drive vs cut with no text walls), feedback rules (hit-stop, sound, colour), failure states, accessibility basics |
| [`fun-plan.md`](fun-plan.md) | "One more take": loop timing, reward cadence, near-miss juice, retry speed, scene card and grade |
| [`concepts.md`](concepts.md) | The owner's add-ons: three hero-car directions, three stunt-driver directions, car mods, crash look and real-physics options, music source options, a run-long colour script, the VFX list and mood notes |
| [`reference-images/`](reference-images/) | 17 reference pictures: 12 key frames (hero car, three sets, the mid-air money shot, HUD over a frame, hold, crash, results, Special Features, title, a storyboard sheet) and 5 concept sheets (car directions, driver directions, liveries and rig parts, a crash storyboard, a colour script) |
| [`greybox-layouts.md`](greybox-layouts.md) | A metric sheet per scene: shared metrics, every stunt's position, lanes and boxes in metres, ASCII top-down sketches, the checks run, and how to block it out after 21:00 |
| [`data-schema.md`](data-schema.md) | GDD §8 "Content is data": the five data-asset types (car, scene, stunt preset, modifier, tuning), the stunt-row columns, curves and the lane rule, all 33 stunt rows for Scenes 1-3, how a modifier overrides tuning, and the naming glossary. Planning text; the classes land on jam night |
| [`jam-night-runbook.md`](jam-night-runbook.md) | Jam night Wed 21:00 to Thu 01:00 minute by minute: who does what, the C++ classes that land tonight, slice briefs, what goes in C++ vs config vs scripts vs MCP vs by hand, bail rules |
| [`stranger-test.md`](stranger-test.md) | The Thursday 20:00 stranger test (the real gate): the four GDD §9 criteria and how each is measured, who counts as a tester, setup checklist, word-for-word facilitator script and consent line, score sheet, decision rule |
| [`risk-and-audio.md`](risk-and-audio.md) | Risk register with early and hard triggers and the fallback for each, a trigger clock in time order, and the audio cue table (every `S_` sound and music cue) |
| [`PREJAM-DECLARATION.md`](PREJAM-DECLARATION.md) | Every file in this pack with the tool and prompt that made it, for the submission |

## Shared anchors (every doc in the pack uses these names and values)

**Scenes** (working names from the one-pager; the GDD is silent on names):

| Scene | Set | Key light colour | Unique silhouette | Stunts | MustCut |
|---|---|---|---|---|---|
| 1 "Rehearsal" | Main Street backlot: plywood false fronts on scaffold braces | amber tungsten | wooden water tower | 6 | 1 (the water tower) |
| 2 "The Chase" | day-for-night city street on a soundstage | steel-blue moonlight gel, sodium-orange pools | elevated steel rail trestle | 9 | none |
| 3 "The Finale" | studio fuel depot and timber bridge | fire red-orange | giant gas-holder tank | 10 | 1 long one (the bridge) |

**The mark** is a strip of gaffer-tape yellow across all three lanes with a small clapperboard sign at the roadside
showing the mark number. In the hold it goes black and white with the rest of the world; it shows yellow only inside
the landing inset (**decided**, open decision 4: "only the landing is in colour").

**HUD layout** (16:9 judges' screens and the Legion's 16:10 1920x1200; every element anchored to a corner or the top
centre, inside a 5% safe margin):

```
+--------------------------------------------------------------------------+
| [SCENE 1  TAKE 2]          [  landing inset (hold only)  ]   00:00:21:12 |
|                            [      NEXT MARK  o o *        ]               |
|                                                                          |
|                          CLOSE!  (stamp, upper middle)    [DIRECTOR'S   |
|                          +1 FILM                           NOTE: cut]    |
|                                                                          |
|                               (car)                                      |
|                                                                          |
| [|#|#|#|#| | |  4 FILM]     [ prompt / NO FILM stamp ]        [(A) LOOK]  |
+--------------------------------------------------------------------------+
```

**Palette** (hex values are starting points for the post and the `MI_` children, not final):

| Use | Colour |
|---|---|
| Backstage void | near-black `#0E0D0C` |
| Set neutrals | warm grey `#8C8478`, plywood tan `#B9A98C` |
| Scene 1 key | amber tungsten `#FFB04A` |
| Scene 2 key | steel-blue gel `#5B86C9`, sodium pools `#FF9A3C` |
| Scene 3 key | fire red-orange `#FF5A1F` |
| Hero car | cream `#F1E5C8`, signal red stripes `#C8312F`, black trim `#1A1A1A` |
| Mark and UI focus | gaffer-tape yellow `#FFC93C` |
| HUD text | warm white `#F5F2EA` on black boxes at ~65% opacity |
| Near-miss tiers | WIDE white, CLOSE yellow `#FFC93C`, PERFECT red-orange `#FF5A36` (always with the word) |
| Director's note | blue pencil `#3A6FD8` on a cream card |

**Grade (decided by hub 99, 2026-11-11; the GDD says "formula on the scene card" and gives no formula):** shot points per stunt: Perfect 3,
Close 2, Wide 1, cut 0, a MustCut stunt cut 1. Stars from the share of the scene's maximum points: 1 star for wrapping,
2 at 25%, 3 at 40%, 4 at 60%, 5 at 80%. Then the take cap: 0-1 retakes keep the cap at 5 (the GDD's "5 stars needs 0-1
takes"), 2-3 retakes cap at 4, 4 or more cap at 3. The free first crash in Scene 1 is not a retake.

**Starting numbers (Proposal, all on the DataAsset):** lane width 4 m; scene speed bases 18 / 22 / 26 m/s with a surge
of +6 m/s for 3 s before each scene's set piece; about 5 s of scene time from one mark to the next (storyboards); near-miss bands from closest
approach: PERFECT 0.6 m or less, CLOSE 1.5 m or less, WIDE beyond that (still kept).

**Three "Director's Cut" things** (all GDD §6 names; keep them apart in every screen and doc):

| Name | What it is | Where |
|---|---|---|
| "Director's Cut of Scene N" | the 10-15 s wrap clip that auto-plays after each scene, then one DELETED SCENE clip | every wrap |
| "Director's Cut take" | playable: the same scene again with your cut stunts restored (MustCuts stay cut) | scene card button |
| "Play the Director's Cut" | the 30 s highlights reel of the whole run | Special Features |

The **Studio Cut** is the player's first run of a scene: what they cut is what the studio would have cut.

## Open decisions (owner or hub)

Each doc ends with its own list; this is the one summary, with the recommended answer first. Nothing here changes
[`../gdd.md`](../gdd.md): each item fills a gap the GDD leaves or, for 17-21, sets out an owner add-on the GDD does
not have.

**Decided by hub 99, 2026-11-11** (were owner calls; Fable had the final say, review of commit `cb0ca47`):

1. **D1 Scene 3 "easy after zero": DECIDED, make S3-5 easy** (8 of the 9 non-MustCut stunts are execution tier); "easy
   after zero" is kept, which sets aside GDD §4 "all of Scene 3's non-MustCut stunts" are execution tier. Why: the three-crash help shows a lane, not a moment, so it does not carry a cutter through a
   timed gap. [`storyboards.md`](storyboards.md)
2. **Grade formula: DECIDED as proposed.** Points PERFECT 3 / CLOSE 2 / WIDE 1 / cut 0 / MustCut cut 1; stars at 25 /
   40 / 60 / 80% of the maximum; take cap 5 / 4 / 3; "next star at n" on the card. Why: it matches the GDD's "5 stars
   needs 0-1 takes" and needs no new rule. [`fun-plan.md`](fun-plan.md) §5
3. **D3 Director's Cut take reward: DECIDED, option A**, offered once per scene: best of the two runs, +1 star (cap 5)
   if every restored stunt is kept. Why: the extra star is the reason to take the restore run, and once per scene
   stops it looping. [`fun-plan.md`](fun-plan.md) §6
4. **Hold colour: DECIDED, the world goes full black and white** (the GDD's rule), the mark included; only the
   landing inset (the SceneCapture) renders in colour, and the UMG HUD stays in colour on its boxes. "Only the landing
   is in colour." Why: it keeps the GDD as written and still makes the landing the one thing that pops.
   [`style-guide.md`](style-guide.md) §2

**Hub can confirm** (fill a gap the GDD clearly implies; all on the DataAsset or one widget):

5. **D2** wrap clip = the last 7-10 s of the scene, one camera change per cut, with the 3 s deleted scene inside the
   10-15 s; deleted scene = a cut MustCut first, else the highest-tier cut stunt, latest wins.
   [`storyboards.md`](storyboards.md)
6. **D4** a crash on a MustCut brings the stunt-1 prompt back at once. [`onboarding.md`](onboarding.md)
7. **Cut window** opens with the telegraph (landing mark at most ~5 s ahead), closes at collision-on; "DRIVE IT" in the
   inset only when the window closes during a hold; the button hint dims outside a window. There is no cut counter:
   GDD §4's "3 cuts in a row from a fresh scene" follows from starting with 3 film (Fable review item 3).
   [`onboarding.md`](onboarding.md)
8. **0 film:** a press shows NO FILM and does not open the hold; a MustCut can still be cut at 0 film (the GDD's
   no-soft-lock claim needs it). [`hud-ui-spec.md`](hud-ui-spec.md) §5, §9
9. **Film cap:** clamp at 6; the stamp shows the real gain ("+1 FILM" or "FILM FULL"). [`fun-plan.md`](fun-plan.md) §3
10. **Take numbers:** TAKE = 1 + retakes; the free S1-1 crash reads "CUT! FREE TAKE" and keeps TAKE 1.
11. **Last stunt:** its mark is the wrap line; the inset reads "WRAP".
12. **Clapperboard:** Scene 1 waits for "(A) ACTION!" (rolls after 6 s); Scenes 2-3 and retries roll after 2 s.
13. **Retry Scene** on the scene card and **Restart Scene** in pause: recommended yes (the GDD's "addictive" test is a
    restart). Pause during a hold cancels the hold; auto-pause on pad loss or focus loss.
14. **No streaks.** The hub's brief mentioned a "one-take streak"; GDD §4 bans streaks, so the pack has none (a scene
    with no cuts shows a "NO DELETED SCENES" card only).
15. **`NS_CutFlash` renamed `NS_SpliceGrain`** so the name never invites a white flash.
16. **Pictures that differ from the text:** 04 (Scene 3) shows no landing mark; 07 (hold) draws a hatchback, not the
    coupe, and, against decision 4, its inset is grey with only the yellow tape in colour while the car keeps its red
    stripes. 13-17 differences are listed in [`PREJAM-DECLARATION.md`](PREJAM-DECLARATION.md) (for example the
    sedan-like cars in 16 and 17). Recommended: keep all as mood plates (the text wins) rather than spend time
    re-rolling.

**The owner's add-ons: all DECIDED by the owner, 2026-11-11 15:25 PT** ("Yes, use the picks"; not in the GDD;
[`concepts.md`](concepts.md)):

17. **Car mods: DECIDED by owner 2026-11-11.** None in the core build (M0); session-only cosmetic liveries (M1, light liveries only,
    unlocked at a 4-star wrap) as a stretch after the Fri 19:00 AAA gate, first to cut. Why: handling tweaks are rejected (they break the authored stunts and tiers); rig parts with play effects likewise. [`concepts.md`](concepts.md) §3
18. **Real-physics crashes: DECIDED by owner 2026-11-11.** Keep the GDD's canned flip (P0) with three flip variants, a
    120 ms shake and Niagara debris; no hybrid debris (P1), ragdoll car (P2) or Chaos vehicle (P3). Why: it is jam-sized
    and keeps the authored stunts deterministic. [`concepts.md`](concepts.md) §4
19. **Music source: DECIDED by owner 2026-11-11.** A, one CC0 track listed in the sourced-assets ledger, with MetaSound stingers and
    low-pass; B (MetaSound loop) as the fallback if nothing fits by Fri 12:00; C (cloud AI music) only after the owner
    reads that provider's terms. The track is picked after 21:00 PT; nothing is downloaded before. [`concepts.md`](concepts.md) §5
20. **Stunt driver (GDD §5 "no humanoid actors"): DECIDED, owner accepted the pick 2026-11-11.** Direction A "Number 7", built only as a static
    helmet and gloves inside the car mesh (no rig), plus at most one 2D pose card on the title after the AAA gate; no
    rigged figure. [`concepts.md`](concepts.md) §2
21. **Hero car direction: DECIDED, owner accepted the pick 2026-11-11.** A, the "Number 7" coupe of [`style-guide.md`](style-guide.md) §5, stays;
    B "Camera Wagon" and C "Cage Buggy" are on file. [`concepts.md`](concepts.md) §1

**Parked: re-add if ahead of schedule.** Owner, 2026-11-11 15:27 PT: "we can always add back some features if we have
made good time". Re-adding anything here needs the core gates green first (Thu 20:00 stranger gate, then the Fri 19:00
AAA gate unless a line says otherwise) and must not change the GDD core loop (look, hold, cut, land, film economy,
tiers). Cheapest first:

- **Session-only cosmetic liveries (M1, item 17):** about 1 h; already a stretch, back after Fri 19:00, first to cut.
- **2D pose card of the driver on the title or scene card (D2, item 20):** about 30 min, one logged image prompt; after Fri 19:00.
- **Hybrid debris (P1, item 18):** 2-4 loose simulated parts at impact, about 1-2 h; after Fri 19:00, only if replays stay deterministic.
- **Cosmetic car parts (M2, item 17):** low value for the time; after Fri 19:00, no play effect.
- **Camera Wagon or Cage Buggy as an extra car (item 21):** about 45 min to 1.5 h, mood plates 13 and 16 on file; after Fri 19:00, no new stunt rules.
- **MetaSound score instead of the CC0 loop (B, item 19):** 3-5 h; only as the Fri 12:00 fallback or a later swap, judged by ear.
- **Cloud AI music (C, item 19):** 1-3 h; only after the owner reads that provider's terms, and with logged provider and prompt.
- **Ragdoll car (P2, item 18):** about 3-5 h and a spline-to-physics pop risk; not before the AAA gate, and a replay test first.
- **Rigged 3D driver (D3, item 20):** 4-8 h; breaks GDD §5 "no humanoid actors" and needs a new owner OK.
- **Handling tweaks and Chaos vehicle (P3, item 17/18):** 1-2 days, break the authored stunts, tiers and determinism; rejected, not planned to come back.

Owner ideas, 2026-11-11 ~15:40 PT ("coop with split screen mode ... built with modding in mind ... custom cars, stunt
tracks ... movie and stunt modifiers, photo mode"). Hub 100 triage; the mod-ready part is now a core rule (GDD §8
"Content is data"). Same gates as above:

- **Photo mode:** pause, free camera in a small radius around the car, HUD off, the film-look presets, a screenshot
  key; about 2-3 h; after Fri 19:00. Also makes the itch page shots.
- **Movie modifiers:** genre filters picked on the title or Special Features screen, e.g. Noir (B&W, grain), Silent
  Film (sepia, stepped frame rate, piano sting), Low Budget (wobbly camera, cardboard tint). Each is one data asset over
  the film-look post and audio, no rule changes; about 3 h for the first, about 1 h each after; after Fri 19:00.
- **Stunt modifiers:** rule changes as data, e.g. One Take (no cuts), Fragile Film (half film), Double Speed. Each must
  pass the stunt determinism test and the tier rules; about 2-4 h for the first; after the movie modifiers.
- **Director co-op (one screen):** the cheap co-op. Two pads, one car, one screen: player 1 drives (lanes), player 2
  is the director (hold to look, release to cut). No split screen; about 3-4 h; breaks GDD §5 "Multiplayer", so it
  needs the owner's OK; after the AAA gate.
- **Split-screen co-op:** post-jam. Two cars and two cameras clash with the one global slow-motion hold (one scene
  clock), double the GPU cost on judges' machines and need a second HUD; 1-2 days.
- **Mod kit (custom cars, stunt tracks):** post-jam. Loading player-made content in a packaged build needs a mod
  pipeline (content packs, a sample mod, docs); 2+ days. The jam build is mod-ready instead (GDD §8).
- **Famous movie cars** (owner, same evening: "james bond cars, KITT, other famous cars (with licensing rights in
  mind)"): not possible in the jam. Rules 8 and 15(d) disqualify any third-party IP or trademark except the Unreal
  Engine logo, licence or not, and a look-alike counts as parody (knowledge base row 14). To lean into car stunts and
  car movies with original work instead: (1) name and dress the storyboard stunts after real stunt-craft moves where
  they fit (ramp jump, two-wheel ski, corkscrew jump, cannon roll, reverse 180, under-truck slide, billboard smash),
  no new stunt rules, hub can confirm; (2) movie modifiers named by genre, never by film (70s Street Chase, Spy
  Thriller, Heist, Desert Pursuit); (3) extra cars stay original archetypes with our own shapes and names (Camera
  Wagon, Cage Buggy above; a spy-style coupe only with cosmetic, original gadgets).

**Checked:**

22. **Title clash (GDD §1, "check itch.io for a clash").** Hub 99 checked on 2026-11-11 at about 15:00 PT: no game
    titled "Jump Cut" on itch.io (relevance search for "jump cut", "jumpcut" and the quoted phrase). The nearest names
    are tools, not games: "Jumpcutter Android Free" (itch.io) and "jumpcutGG" (Steam, a transcript video editor).
    Verdict: no clash; keep the title.
