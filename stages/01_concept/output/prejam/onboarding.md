# Jump Cut: onboarding, feedback rules, failure states, accessibility

2026-11-11, pre-jam planning text only (Rule 7(h)): no prompt widget, hit-stop, camera or level exists before 21:00 PT.
[`../gdd.md`](../gdd.md) wins over this file. Stunt names and times come from [`storyboards.md`](storyboards.md),
widget names from [`hud-ui-spec.md`](hud-ui-spec.md), colours and fonts from [`style-guide.md`](style-guide.md).
Anything the GDD does not fix is marked **Proposal** and listed at the end.

The job of this file: a judge who has never seen the game knows the goal inside 30 s (GDD §2), lands a cut inside
60 s, drives a stunt on purpose, and reads the cut as an edit, not a glitch (the four Thu 20:00 gate items, GDD §9).
No text walls: one goal line, one prompt, and the game itself.

## 1. The rules the first minute must teach (and nothing else)

| # | Rule | Taught by |
|---|---|---|
| 1 | Drive the stunts; cut the ones you can't; film runs out | the goal line on the Scene 1 clapperboard (GDD §2) |
| 2 | Hold A to look at where a cut lands; let go to cut; B keeps driving | the one prompt, on stunt 1 until done once (GDD §2) |
| 3 | A cut costs 1 film; a kept shot earns film | the film strip: a cell punches out on the cut, cells fill on a stamp |
| 4 | Closer is better | the WIDE / CLOSE! / PERFECT! stamps with their film gain |
| 5 | Crashing is cheap | the free crash on stunt 1, then "CUT! TAKE 2" on the next crash, with control back in under 1 s |
| 6 | Some stunts are meant to be cut | the MustCut "DIRECTOR'S NOTE: cut / costs 0 film" card on S1-4 |

Not taught in the first minute (the player finds them later): the landing lane in the hold, that film alone limits
cuts (there is no cut counter), two-hop and timed-gap tiers, the star formula, the Director's Cut take.

## 2. The first 60 seconds (from pressing Play on the title)

Times are wall-clock from Play. Scene time `T` starts when the car rolls. Stunt times are the storyboards' starting
values (S1-1 at T 7, mark spacing about 5 s).

| Wall time | `T` | What the player sees and hears | What they learn | If they do something else |
|---|---|---|---|---|
| 0:00 | - | Scene 1 clapperboard over the start line: "SCENE 1  REHEARSAL  TAKE 1" and the goal line "Drive the stunts. Cut the ones you can't. Film runs out." Car idles, engine ticking | the goal (rule 1) | - |
| 0:01 | - | "(A) ACTION!" appears on the board (**Proposal**: the Scene 1 board waits for a press; it rolls on its own after 6 s) | A is the main button | no press: rolls at 0:06 |
| ~0:03 | 0 | Clapper stick closes with a clap; the board slides down and off; the car rolls in lane C | - | - |
| 0:03-0:07 | 0-4.5 | Free road. Lane changes feel light and quick (body lean, tyre chirp) | lanes | - |
| 0:07 | 4.5 | S1-1 Leaning False Front: rope twang, the right-hand front tilts, its amber key light snaps on; the cut window opens (**Proposal**: with the telegraph), so the button hint lights "(A) LOOK" and the prompt fades in at the bottom centre: "Hold A to look. Let go to cut. B to keep driving." (KB/M: SPACE / SHIFT) | the read; rule 2 | - |
| 0:07-0:09 | 4.5-7 | **Path A, hold:** world drops to black-and-white workprint at 0.3x, projector whir, the "NEXT MARK" inset (the only world picture in colour) shows the yellow tape past the front with a ghost car; prompt now reads "Let go to cut" | the look is free and shows the landing | auto-cancel at 1.5 s: "CANCELLED", back to live, no cost |
| | | **Path A, release:** freeze, one black frame, splice click, timecode jump, film 3 > 2. The car is on the yellow tape it just saw | rules 2-3; the jump matches the inset, so it reads as an edit | - |
| | | **Path B, drive:** steer L; the front lands across C and R behind; "CLOSE!" stamp, "+1 FILM", film 3 > 4, colour steps up | rule 4 | prompt stays on until one cut is done |
| | | **Path C, crash:** clapper "CUT! FREE TAKE" (**Proposal**), black, back at the start line; slate still "TAKE 1" | rule 5 | the retry is a normal stunt; the next crash is "CUT! TAKE 2" |
| 0:12-0:17 | 9.5-14.5 | S1-2 Prop Truck noses out across L and C: easy, 1.5 s or more of slack. Steering R late gives the first CLOSE! or PERFECT! | driving on purpose with film above 0 (gate b) | no cut done yet: the prompt is back on this stunt |
| 0:17-0:22 | 14.5-19.5 | S1-3 Light Rig Swing: the first timed gap; worth the film to cut | cutting has a use | crash: back to mark 2, film unchanged |
| 0:22-0:28 | 19.5-26 | At mark 3 the blue-pencil card slides in: "DIRECTOR'S NOTE: cut / costs 0 film". The water tower buckles and falls across all three lanes | rule 6; a forced cut: the only way past is hold and release (gate a) | crash: the prompt comes back on this stunt (**Proposal D4**) |
| 0:28-0:42 | 26-37.5 | S1-5 Barrel Roll (T 30; easy, after a cutter's zero point), then the surge and S1-6 The Big Facade (T 35; two-hop set piece) | the scene builds | - |
| ~0:42-0:52 | 37.5 | "THAT'S A WRAP", stinger, then the 10-15 s "Director's Cut of Scene 1" wrap clip | the theme payoff (GDD §6) | skip: hold B or Esc 0.5 s, after the first 1.5 s |

With boot, the photosensitivity card, the loading reel and the title, the wrap lands at about minute 1.1-1.5 from boot,
inside the GDD's "about minute 1.5".

### Prompt rules (follow GDD §2; details are Proposals)

- One prompt, bottom centre, on its own black box. Shown when S1-1's cut window opens (with its telegraph, about 2.5 s
  before collision-on; a press before that does nothing, O2) and on every cuttable stunt after that until the player has
  done **one hold-and-cut**. Then it never shows again in that run, including after Retry Scene.
- Its text follows the last device used: "Hold A ... B" on a pad (Cross / Circle names on a PlayStation pad),
  "Hold SPACE ... SHIFT" on keyboard and mouse.
- While held it reads "Let go to cut". It never covers the inset, the film counter or the stamp slot.
- The only other words before the wrap: the goal line, the Director's Note, stamps, NO FILM, CANCELLED, DRIVE IT and the
  clapper. No tutorial screen, no how-to page (the title has a one-line controls strip).

## 3. Feedback rules (the juice contract)

Every player action gets an answer in under 100 ms, in picture **and** sound **and** text or number. GDD numbers are
fixed; the rest are starting values on the DataAsset.

| Event | Time | Picture | Sound | Text / number |
|---|---|---|---|---|
| Hold starts | 150 ms ease to 0.3x | full black-and-white workprint, sprocket edges, grain; inset opens in colour (100 ms) | projector whir in; music low-passed, not slowed | "NEXT MARK", ring with seconds "1.5" counting down |
| Landing lane change in the hold | instant | ghost car moves in the inset, lane tick lights yellow | soft tick | - |
| Cut (release) | 60-80 ms hit-stop, then 1 black frame | 5% punch-in relaxing over ~0.3 s, grain burst ~0.2 s | splice click, tape-stop then tape-start | timecode jumps; film cell punches out ("3 > 2") |
| Cancel (B, or auto at 1.5 s) | 60 ms back to 1x | workprint off, inset closes | whir out, cancel tick | "CANCELLED" on the ring (auto-cancel only) |
| Near miss, kept shot | stamp holds 0.9 s | stamp slams in; saturation steps up | whoosh, longer per tier; PERFECT adds a stamp thump | "WIDE" / "CLOSE!" / "PERFECT!" and "+1 FILM" / "+1 FILM" / "+2 FILM" |
| Crash | 120 ms hit-stop, flip, black, control back in under 1 s | canned flip, clapper slam, hard cut to black | crunch, metal tumble, clapper crack | "CUT! TAKE n", then "BACK TO MARK k" |
| Press at 0 film | instant, no hold | NO FILM stamp, film strip outline red-orange | dry click | "NO FILM", "0 FILM" |
| MustCut approaching | slides in at the previous mark | blue-pencil card | pencil scratch | "DIRECTOR'S NOTE: cut / costs 0 film"; hold preview shows "3 > 3 (-0)" |
| Wrap | 1.5 s | locked wide on the last mark, slate | wrap stinger; music keeps running | "THAT'S A WRAP" |

Rules that keep it feeling right:

1. **Input is never eaten.** A lane press during a hit-stop or the splice frame is buffered and applied on the first
   live frame (**Proposal**).
2. **The cut lands where the inset showed.** Same lane, same mark, same hazard state at arrival. If the two ever
   disagree, testers will say "teleport" (gate item c fails). The determinism test (GDD §8) protects this.
3. **Music never stops, never seeks** (GDD §7). Holds low-pass it, cuts stinger over it, crashes clap over it.
4. **At most 3 HUD changes at once** (HUD spec §2). The Director's Note waits for a stamp to fade.
5. Hit-stop and shake scale with weight: cut 60-80 ms, crash 120 ms, PERFECT a 2-frame stamp shake (off with the
   screen-shake switch).
6. Rumble on a pad is optional polish (Day 3 or later). If it goes in, the screen-shake switch turns it off too.

## 4. Failure states (nothing ends the run; there is no game-over screen)

| State | What happens | What the player sees | Why it is fair |
|---|---|---|---|
| Crash on any stunt | +1 take; back to the previous mark with that mark's film (GDD §4) | clapper "CUT! TAKE n", "BACK TO MARK k" | film is never lost to a crash |
| First crash on S1-1 | free: no take counted (GDD §2) | "CUT! FREE TAKE" (**Proposal**); slate stays "TAKE 1" | teaches that crashing is cheap |
| Third crash on the same (non-MustCut) stunt | the next hold lights the safe lane in the inset (GDD §4) | lane tick pulses with an outline; no name, no badge | help without shame |
| Crash on a MustCut | the prompt comes back on that stunt (**Proposal D4**; a MustCut has no safe lane) | the stunt-1 prompt | the Director's Note already asked for a cut |
| 0 film | cut button dead; every non-MustCut stunt is drivable; the stunt after a likely zero point is easy (GDD §4; in Scene 3 that is S3-5, D1 decided by hub 99) | "NO FILM" stamp, empty strip, "(A) LOOK  NO FILM" struck through | the next easy stunt refills film |
| 0 film on a MustCut | the hold and cut still work, at 0 cost (follows from GDD §4's no-soft-lock claim) | hold preview "0 > 0 (-0)" | no soft-lock |
| Cut window closes during a hold | release only cancels (**Proposal**) | inset label "DRIVE IT" | the car reached the collision-on line |
| Held too long | auto-cancel at 1.5 s real time, never auto-cut (GDD §3) | "CANCELLED" | looking is free |
| Pause during a hold | the hold cancels, then pause (**Proposal g**, HUD spec) | pause menu | no slow-mo hiding behind pause |
| Pad disconnects or the window loses focus | auto-pause (**Proposal**) | pause menu | nothing happens while the player is away |
| A weak run | the scene still wraps; the worst grade is 1 star for wrapping | the scene card | the game always moves on |

## 5. Accessibility basics (jam scale)

- **Never colour or sound alone** (GDD §4): every tier, the film count, NO FILM, DRIVE IT, the Director's Note, the
  take number and CANCELLED are words or numbers too. Tiers also differ by stamp size.
- **Black and white must read.** The hold is greyscale, so every hazard, the car and the mark separate by value, not
  hue (style guide §2, §4). Check a greyscale screenshot of each stunt.
- **Photosensitivity.** A notice card at boot (HUD spec §3.12). No white flash anywhere; the splice is one black frame
  (GDD §3). Nothing flickers faster than 3 times a second: the hold ring's last 0.3 s is a colour and size change, not
  a blink. Grain bursts never raise brightness.
- **Screen-shake off** switch in pause (GDD §8). It removes camera shake, the PERFECT stamp shake and any rumble. The
  5% punch-in stays (it is a zoom, not a shake).
- **One-button verb.** Hold and release; no mashing, no chords. The hold is capped at 1.5 s and auto-cancels, so a
  player who freezes loses nothing.
- **Either hand setup.** Pad alone, keyboard alone (A/D or arrows, Space, Shift, Esc), or arrows plus mouse (left
  button to hold and cut, right button to cancel). No remapping (GDD §5).
- **Text size and place for the Legion Go S** (8 inch, 16:10, 1920x1200) and 16:9 1920x1080: body 30 px or more,
  numbers 44 px, stamps 96 px, every line on a black box at ~65%, 5% safe margin, corners and top centre only (HUD
  spec §7). Check a packaged 1920x1200 frame on the Legion.
- **No voice, no dialogue** (GDD §5), so there is nothing to subtitle. The UI is English only (contest rule).
- **Pause works everywhere in play**, including during a hold. Every menu works by pad focus and by mouse.

## 6. How this protects the Thu 20:00 gate (GDD §9)

| Gate item | Protected by | Watch for in the recording |
|---|---|---|
| (a) a cut inside 60 s | the prompt on S1-1, the prompt returning on each cuttable stunt, the free MustCut at ~0:25 | a tester who holds but never releases; a tester who never reads the prompt |
| (b) drives a stunt on purpose with film above 0 | S1-2 is easy with 1.5 s slack and a clear horn-and-headlights read | steering only after a crash |
| (c) "what happened when you let go?" is not lag, glitch, bug or teleport | the inset shows the landing first; splice click + black frame + timecode jump say "edit" | testers saying "skip" or "jump" is fine; "lag" or "teleport" fails |
| (d) finishes Scene 1 with 3 crashes or fewer | the free crash, easy tiers, the safe-lane help, crash costs no film | repeated crashes on S1-3 or S1-6 (tune their windows on the DataAsset) |

## 7. Open decisions from this file

- **O1** Scene 1 clapperboard waits for a press ("(A) ACTION!", auto-roll after 6 s); Scenes 2-3 roll after 2 s; a press after 0.4 s rolls at once.
- **O2** The cut window opens with the telegraph (landing mark at most ~5 s ahead) and closes at collision-on; outside
  a window the button hint dims and a press does nothing.
- **O3** The free S1-1 crash shows "CUT! FREE TAKE" and keeps "TAKE 1".
- **O4** (= D4) A crash on a MustCut brings the prompt back at once, not after three crashes.
- **O5** Buffered lane input through hit-stop; auto-pause on pad loss or focus loss; "DRIVE IT" only when the cut
  window closes during a hold. No cut counter: start film 3 already caps a fresh scene at three cuts in a row (GDD §4).
