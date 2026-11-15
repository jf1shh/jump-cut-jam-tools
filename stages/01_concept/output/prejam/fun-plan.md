# Jump Cut: fun plan ("one more take")

2026-11-11, pre-jam planning text only (Rule 7(h)). [`../gdd.md`](../gdd.md) wins. Numbers the GDD does not fix are
starting values on the DataAsset and are marked **Proposal**. Stunts and times: [`storyboards.md`](storyboards.md).

**The GDD's own test for "addictive"** (§1): a judge restarts Scene 1 or takes the Director's Cut take once. Nothing is
built for a second session. Every item below serves that one moment on the scene card, or the minute before it.

## 1. The loop at three sizes

| Size | Length | Shape | What pulls the player into the next one |
|---|---|---|---|
| Stunt | ~5 s mark to mark | read (2.5 s telegraph) > choose (drive, or hold and cut) > answer (stamp, or splice) | the next key light is already snapping on |
| Scene | Scene 1 ~37 s of scene time, Scene 2 ~48 s, Scene 3 ~62 s (the storyboards' driving times); plus holds and crashes | clapperboard > 6 / 9 / 10 stunts > wrap > Director's Cut clip > scene card | the clip shows your run as a film, the DELETED SCENE shows what you skipped, the card shows the next star |
| Run | about 5 minutes from boot to Special Features | Scene 1 teach > Scene 2 test > Scene 3 twist > 30 s reel > Special Features | each scene is faster, darker and has more tier stunts |

Run budget (wall clock, starting values): boot, card, loading reel and title ~20 s; Scene 1 ~65 s including its wrap
clip and card; Scene 2 ~75 s; Scene 3 ~90 s; final reel 30 s. Total about 4.5-5 minutes, so a judge sees the whole
game and still has time to press Retry.

## 2. Reward cadence (something lands every ~2.5 s)

Scene 1, from the storyboards' times. Each stunt gives a **read** beat and an **answer** beat about 2.5 s apart.

| `T` | Beat | Kind |
|---|---|---|
| 0 | clap, "ACTION!", engine | start |
| 4.5 | S1-1 key light, rope twang | read |
| 7 | the cut (splice, timecode jump) or the first stamp | answer |
| 9.5-12 | prop truck horn; CLOSE! for a late swerve | read, answer |
| 14.5-17 | light rig sweep; first timed gap | read, answer |
| 19.5 | DIRECTOR'S NOTE slides in (the theme in one card) | read |
| 22-24 | the water tower falls behind your cut | answer, spectacle |
| 27.5-30 | barrels roll; easy refill after a cutter's zero point | read, answer |
| 32 | music swell, speed surge +6 m/s for 3 s | build |
| 35 | The Big Facade, two-hop: the set piece | answer, spectacle |
| 37.5 | THAT'S A WRAP, stinger, then your Director's Cut clip | payoff |

**Visible progress inside a scene:** colour. Every scene starts at ~50% saturation and every kept shot steps it up
(Proposal: +0.1 a shot, cap 1.0; GDD §7). A good run ends in full colour; a run of cuts stays faded. The player sees
the film "come to life" without reading a number. (Last on the cut list; the static floor is the fallback.)

## 3. Near-miss juice (the skill ceiling)

In three lanes, closeness comes from **committing late** (storyboards: "Perfect moment" per stunt). The later you
change into the safe lane, the closer the pass and the bigger the reward:

| Tier | Closest approach (Proposal) | Film | Stamp | Sound | Grade points (decided, hub 99) |
|---|---|---|---|---|---|
| WIDE | beyond 1.5 m | +1 | "WIDE", white, 96 px | short whoosh | 1 |
| CLOSE! | 1.5 m or less | +1 and a bonus star point (GDD §4) | "CLOSE!", yellow, 120 px | longer whoosh | 2 |
| PERFECT! | 0.6 m or less | +2 | "PERFECT!", red-orange, 150 px, 2-frame shake | whoosh, bright tick, stamp thump | 3 |

- **Risk and reward are the same choice.** Waiting longer to change lanes is both the near-miss and the crash risk. A
  crash costs a take (stars), never film, so greed is punished gently.
- **Film is the currency that links the two verbs.** Driving well earns the film that lets you cut the stunt you
  cannot do. A driver who keeps PERFECTing reaches the 6-film cap; the stamp then shows the real gain (Proposal:
  "+1 FILM", or "FILM FULL" when nothing fits) so the number never lies.
- **The film cap is a nudge, not a wall.** At 6 film the player is told, kindly, that a cut is affordable now. The
  hard stunts (timed gap, two-hop) are where spending makes sense.

## 4. Retry speed (never wait to try again)

| Retry | Target | How |
|---|---|---|
| Crash to control | under 1 s (GDD §4, never cut) | 120 ms hit-stop, canned flip, clapper, hard cut, previous mark; no menu, no fade |
| Retry Scene from the scene card | under 2 s to the clapperboard (Proposal) | same level stays loaded; reset the scene clock, stunts and film; the clapperboard rolls after 2 s without a press on a retry |
| Restart Scene from pause | same as above | pause menu (GDD §5 keeps restart and Quit) |
| Skip the wrap clip | 0.5 s hold of B or Esc, after the first 1.5 s | HUD spec proposal (c) |

Nothing reloads a map between a crash and control, or between Retry and the clapperboard. The deterministic scene clock
(GDD §3, §8) makes a reset a clock reset, not a level reload.

## 5. The scene card (where "one more take" is decided)

Layout and widgets: HUD spec §3.8. What it must do for fun:

1. **Show the run as a film result**, not a score screen: "SCENE 1  REHEARSAL  -  WRAP", stars as icons and "4 / 5".
2. **Show the formula in one line of numbers** (GDD §4: "formula on the scene card"), with the next star:
   "Points 10 of 16 = 62% -> 4 stars; retakes 2 -> cap 4; next star at 13". The "next star" part is the hook
   (decided with the grade; one more number, no critic text).
3. **Offer the two "one more" buttons** next to NEXT SCENE (default focus): **RETRY SCENE** and **DIRECTOR'S CUT TAKE:
   Restore n deleted scenes** (only when a non-MustCut stunt was cut, and once per scene). Both are the GDD's addictive
   test.

### Grade (decided by hub 99, 2026-11-11; the GDD gives no formula)

- Points per stunt: PERFECT 3, CLOSE 2, WIDE 1, cut 0; a MustCut stunt that is cut scores 1 (it is what the director
  asked for). A MustCut cannot be driven, so a scene's maximum is 3 per non-MustCut stunt plus 1 per MustCut.
- Stars from the share of the maximum: 1 for wrapping, 2 at 25%, 3 at 40%, 4 at 60%, 5 at 80%.
- Take cap (GDD: "5 stars needs 0-1 takes"): 0-1 retakes keep the cap at 5; 2-3 retakes cap at 4; 4 or more cap at 3.
  The free first crash on S1-1 is not a retake.

**Worked examples, Scene 1** (6 stunts, 1 MustCut, maximum 5 x 3 + 1 = 16):

| Player | Shots | Points | Share | Stars before cap | Retakes | Stars |
|---|---|---|---|---|---|---|
| Cuts everything allowed | S1-1, 2, 3 cut; MustCut cut; S1-5 WIDE; S1-6 cut | 0+0+0+1+1+0 = 2 | 12% | 1 | 0 | 1 |
| Mixed (the target) | cut; CLOSE; cut; MustCut; WIDE; PERFECT | 0+2+0+1+1+3 = 7 | 44% | 3 | 1 | 3 |
| Drives everything | WIDE; CLOSE; PERFECT; MustCut; WIDE; CLOSE | 1+2+3+1+1+2 = 10 | 62% | 4 | 2 | 4 |
| Expert | PERFECT x4, CLOSE x1; MustCut | 12+2+1 = 15 | 94% | 5 | 0 | 5 |

The spread (1 to 5) is wide enough that a judge's first run lands at 2-4 stars and the card shows a reachable next star.

## 6. The Director's Cut take (D3: the reward)

GDD §6: replay the scene with your cut stunts restored and their marks off, for extra stars; optional; one flag per
stunt. How many extra stars: **option A, decided by hub 99 (2026-11-11).**

**Rules:**

- Only the stunts you cut are restored. Their marks are off: they cannot be cut, only driven. Every other stunt plays
  as normal. **MustCut stunts stay cut** (the director asked for that cut; a MustCut cannot be driven).
- The take is scored with the same formula. The scene keeps the **better** of the two star results.
- **Offered once per scene.** After the take the button is gone from that scene's card, so it cannot loop.
- **Reward (D3, option A, decided):** +1 star (cap 5) if every restored stunt is kept (any tier) in the take. The card
  then reads "DIRECTOR'S CUT" under the stars.
- Option B (not chosen): no bonus; best-of-two only. Simpler, but "for extra stars" then depends on the player doing
  better.

Why A: it rewards exactly the theme (restore what you cut) and needs one boolean per restored stunt, which the "one flag
per stunt" already gives.

## 7. What is deliberately not here (GDD §4)

No streak multiplier, no personal-best save, no beat splice, no critic style line. When a scene has no cut at all, its
wrap clip shows "NO DELETED SCENES" (a fact about the edit, not a streak; earlier drafts said "ONE TAKE", dropped
because it reads like a crash count or a streak). The hub's background note mentioned a "one-take streak"; the GDD bans
streaks, so this pack follows the GDD.

## 8. Fun risks and the knob for each

| Risk | Sign at the Thu 20:00 test or Fri build | Knob (DataAsset unless noted) |
|---|---|---|
| Cutting feels better than driving | testers cut everything allowed, ignore stamps | raise Perfect band to 0.8 m; louder PERFECT; more slack on easy stunts |
| Driving feels unfair | 3+ crashes on S1-3 or S1-6 (gate item d) | widen the 0.6 s timed-gap and two-hop windows to 0.8 s; slower Scene 1 base speed |
| The cut reads as lag | testers say "lag" or "teleport" (gate item c) | shorter hit-stop (60 ms), louder splice click, bigger timecode jump; check the inset matches the landing |
| Hold-cancel chaining | a tester holds, cancels, holds again to play in slow motion | watch only: a hold moves only the landing lane, so the live car cannot be steered in slow motion, and the GDD says no cooldown. If it breaks the game, the owner decides |
| Film never runs out | drivers sit at 6 film all scene | start film 2 instead of 3; Perfect +1 instead of +2 (GDD table values: owner call) |
| Film runs out too often | NO FILM stamps before S1-4 | start film 3 (GDD) is the floor; check stunt tiers after a zero point |
| Wrap clip gets skipped every time | skip pressed within 2 s | shorten to 10 s; make sure a cut shows as a hard cut with the timecode jump burned in |
| Nobody presses Retry or the DC take | Fri build #2 card watch | make "next star at n" larger; default focus stays NEXT SCENE so judges still see Scene 2 |

## 9. Open decisions from this file

- **F1** Decided by hub 99: grade formula and take cap (above); "next star at n" on the card.
- **F2** (= D3) Decided by hub 99: option A (+1 star, cap 5, if every restored stunt is kept), offered once per scene.
- **F3** Film cap display: "+1 FILM" / "FILM FULL" (shared with HUD spec open question 2).
- **F4** Retry Scene on the card and Restart Scene in pause (HUD spec open question 6), recommended yes: the GDD's
  addictive test is a restart.
