# Jump Cut: the Thursday stranger test (the real gate)

2026-11-11, pre-jam planning text only (Rule 7(h)): the test happens in the contest window, Thu Nov 12 20:00 PT. Nothing
here is built or run before 21:00 Wed. [`../gdd.md`](../gdd.md) §9 wins over this file. The first minute it checks is
[`onboarding.md`](onboarding.md) §2 and §6. This file is the runbook the owner follows. It adds no game rules. Anything
the GDD does not fix is marked **Proposal** and listed in section 8.

The gate in one sentence: two people who have never seen the game play the Scene 1 greybox for 3 minutes each on the
Legion Go S gamepad, with only the on-screen prompt, while the screen and their voice are recorded. Pass means all four
criteria hold. The result decides, by Thu 21:00, whether the hold keeps its preview.

## 1. The four criteria, and how each one is measured here

| | GDD §9 criterion | Measured as | Source of truth |
|---|---|---|---|
| (a) | Each tester lands at least one cut inside 60 s | Stopwatch from the tester's first press of Play (or ACTION on the Scene 1 board if the build has no title). A cut counts when a hold ends in a release that lands on the mark (black frame, timecode jump, film cell punches out, or a MustCut at "-0"). A cancel is not a cut | recording |
| (b) | Each drives at least one stunt on purpose with film above 0 | The film count is 1 or more when the stunt's telegraph starts, the car clears the stunt (WIDE, CLOSE! or PERFECT! stamp), and there is a sign of intent: a lane change inside the telegraph window toward the safe lane, or the tester says it aloud ("left", "go right"), or Q4 explains it. A stamp earned by sitting still with no input is not on purpose | recording + Q4 |
| (c) | Asked "what happened when you let go?", neither says lag, glitch, bug or teleport | Q1 below, word for word, plus any unprompted remark about the cut during play. The four words fail it. **Proposal:** close equivalents (froze, stuttered, jumped by itself, broke) are flagged and the Fable review rules on them | verbatim answer on the sheet |
| (d) | Each finishes Scene 1 with 3 crashes or fewer | Finished = the "THAT'S A WRAP" slate appears by 3:30 on the stopwatch (**Proposal**: the 3 minutes plus the 30 s grace in §4 C, so a stunt already on the road at 3:00 may resolve and a wrap slate between 3:00 and 3:30 passes). Crashes = every "CUT!" clapper slam, the free first crash on S1-1 included (**Proposal**: stricter than the take number, which does not count it) | recording |

Fixed by the GDD and repeated here so nobody drifts: at least one stranger if two cannot be found; the owner's own run
never counts; the recording is reviewed with a Fable agent before the call; the fallback is decided Thu 21:00, never
later.

## 2. Who counts as a tester

- Has never seen or heard about the game, its rules or its design. Not part of the project. Not told the title, the
  theme or the genre. Invite line: "a 15 minute test of a short game on a handheld, no preparation."
- An adult (**Proposal**: so the recording consent is theirs).
- Two people if you can find them. Each plays alone. The second waits out of sight and earshot: they must not watch,
  hear or be told anything about the first run.
- Log their game habit on the sheet (never / sometimes / often) but do not filter on it. **Proposal:** if the choice is
  free, take one who plays games and one who rarely does. Judges can be either.
- Ask three people on Wed. Two confirmed by Thu 18:00. One no-show is fine; zero is the case the GDD covers with "at
  least one stranger" (risk R29 in [`risk-and-audio.md`](risk-and-audio.md)).

## 3. Setup checklist (done by Thu 19:45; the owner does it, an agent cannot)

**Build**

- [ ] Build under test frozen at 19:30: the newest packaged Win64 Development build that passed the Thu 17:00 check
  ("launches, and the core loop plays on the built-in pad alone"). Write its commit sha on both sheets. **No patch
  between tester 1 and tester 2**, or the two runs are not comparable.
- [ ] It contains what GDD §9 lists: the Scene 1 greybox (6 stunts, cubes allowed), the cut juice (hit-stop, one black
  frame, splice click, tape stinger, timecode jump) and the film economy. It must also have the **goal line on the
  board and the on-screen prompt**: the gate tests the teaching, so a build without them is not a valid test. The wrap
  clip and Special Features are not needed; the run ends at the wrap slate.
- [ ] Launched from the packaged exe on the Legion, not the editor.
- [ ] **Warm-up run** by the owner first (the owner's Thu 19:00 hand playtest in `jam-execution-plan.md` is this run). A
  cold shader hitch would be read as "lag" in (c) and muddy the result. The cold-start check belongs to build #2
  (GDD §8, `-clearPSODriverCache`), not here. Leave the game at the title (or the Scene 1 board).
- [ ] Legion on mains power, idle lock off (planned for Wed 10:00; confirm), notifications and pop-ups off, Windows volume at a
  level you write down (start at 60%). Same level for both testers.

**Input**

- [ ] The built-in pad is the scored device. Check sticks, d-pad, A, B and Start in the packaged build. The prompt shows
  the pad glyphs ("Hold A ... B"), not SPACE and SHIFT.
- [ ] Keyboard and mouse unplugged or out of reach during scored runs. The prompt follows the last device used
  (onboarding §2), so one stray key press changes what the tester reads.
- [ ] **KB/M check, owner alone, 19:15-19:30:** a 2 minute Scene 1 run on keyboard and mouse in the desktop editor (PIE)
  or on the Legion with a USB keyboard. A/D or arrows, Space, Shift, Esc, left and right mouse. Not scored. Both input
  methods must play the whole game (AGENTS.md); log pass or fail in the decision note.

**Recording** (OBS on the Legion, profile in `stages/04_ship/references/capture-setup.md`)

- [ ] 1080p, 60 fps, Game Capture on the game window. **Unmute Mic/Aux in the OBS mixer:** the profile ships it muted,
  and this test needs both the game sound and the voices.
- [ ] 20 second test take, played back: you hear the game and a person speaking at normal distance, and you see the whole
  screen including the film counter.
- [ ] One file per tester, named T1 and T2 with the date. Screen and voice only: **no webcam, no face video.** At least
  5 GB free.
- [ ] Backup: a phone voice memo (audio only, no camera) started at the consent line.
- [ ] A stopwatch (phone) for the 60 s and 3 min marks.
- [ ] Recordings stay on disk and **out of git** (size, privacy). Only the sheets and the decision note are committed.

**Room and paper**

- [ ] Tester seated, Legion in both hands. Facilitator beside and slightly behind, able to see the screen, not looking at
  the tester's face. Phone silent. Nobody else in the room.
- [ ] Two copies of the score sheet (section 6), build sha and date filled in, a pen.
- [ ] Facilitator rules (section 4) read once, aloud, to yourself.

## 4. Facilitator script (neutral; read it as written, same words for both testers)

**Rules**

1. Say only what is in a box below. Do not explain, rescue, praise or sigh.
2. Never name a control or a rule: not "cut", "film", "hold", "look", "mark", "stunt", "scene", "preview", "A" or "B".
   If you repeat something, use the tester's own word.
3. Never answer "am I doing it right?" or "what do I do?" with game information.
4. A **technical fault** (game crash, pad drops out, pop-up) is yours to fix. Say "That was a fault on our side, we'll
   start again", restart the build, restart the clock. Two faults in one run: stop, use another tester.
5. Do not look at the tester's face while they play. Watch the screen and tally.

**A. Welcome and consent** (recording on; the "yes" must be on the recording). **Proposal** wording; keep the five
parts: what is recorded, who sees it, how long, they can stop, a yes on tape.

> "Thanks for helping. I'm testing the game, not you, so nothing you do can be wrong. I'll record the screen and your
> voice, no camera, for about ten minutes, so I can review it with my team, including an AI assistant that sees my
> notes and still pictures, not the audio. The recording and my phone's backup voice memo stay private, aren't
> posted, and I'll delete both by Sunday November 22. You can stop at any moment or skip any question. Is it OK to
> record?"

**B. Brief** (then hand over the Legion at the title or the Scene 1 board)

> "Here's a short game. I won't explain it. Play it the way you would if you'd found it on your own. Please say what
> you're thinking out loud, even small things like 'I don't know what that is.' I can't help with how it works, so if
> you get stuck, say so and keep trying things. You have about three minutes. Start whenever you're ready."

Start the stopwatch at the tester's first press of Play (or ACTION).

**C. During play** (say nothing else)

| The tester | You say |
|---|---|
| Asks how to play, what a thing is, or what to do | "What would you try?" |
| Asks "am I doing it right?" | "There are no right answers. Keep going." |
| Goes quiet for 15 s | "What are you thinking?" (once per silence) |
| Says "it's broken", "is that a bug?", "what was that?" | "Say more." Write the exact words and the time |
| Wants to stop | "Of course." Note the time. Offer the questions anyway |
| No input and no progress for 60 s | Say nothing new. Write STUCK and the time. This is a result, not a problem to fix |
| Reaches the wrap slate | "Thank you. Please put it down for a moment." |
| Stopwatch reads 3:00 | "That's about time. Finish what you're on." If a stunt is on the road let it resolve (30 s at most), then "Please put it down for a moment." Not finished by then: (d) fails, note why |

**D. Questions** (pad down; read exactly, in this order, one at a time; write Q1 and Q4 word for word; the only
follow-ups allowed are "Say more." and "Anything else?")

| # | Say | Feeds |
|---|---|---|
| Q1 | "What happened when you let go?" If they never held and released: "What did the A button do?" | (c) |
| Q2 | "What is this game about? What were you trying to do?" | goal inside 30 s (GDD §2), a signal |
| Q3 | "What was the bar at the bottom left for?" | film economy read, a signal |
| Q4 | "Was there a moment you drove past something on your own? How did you know where to go?" | (b) |
| Q5 | "What happened when the car crashed? What did you do next?" (skip if no crash) | take two read, (d) |
| Q6 | "How did the car feel to steer? A few words." | car feel |
| Q7 | "If you could keep playing right now, would you? Why or why not?" | car feel vote |
| Q8 | "Was anything confusing?" | tune list |
| Q9 | "Is there one thing you would change first?" | tune list |

Then: "Is it still fine for me to show a short clip of the screen, without your voice or name, in the game's dev log?
Yes or no, either is fine." Write Y or N. Then thank them: "Please don't tell the next person anything about the game."
Stop the recording. Rename the file. Relaunch the game to the title for the next tester.

**Reading the Q1 answer.** Words that fail (c): lag, glitch, bug, teleport. Words that pass and are good: skip, jump,
cut, edit, "it went to the next bit", "like a movie". A neutral answer ("I don't know", "it just moved me"): say "Say
more." once. If it stays neutral it passes (c) but mark it **weak**: it is a tune signal even when it is not a fail.

## 5. What to watch, second by second

Clock = stopwatch from Play. Times follow [`onboarding.md`](onboarding.md) §2 for a run with no crash; each crash adds
roughly 10 s. Tick the sheet with the stopwatch time. Do not comment.

| Clock | The game shows | Watch for | Tick |
|---|---|---|---|
| 0:00-0:06 | Scene 1 board: "SCENE 1  REHEARSAL  TAKE 1", goal line "Drive the stunts. Cut the ones you can't. Film runs out.", "(A) ACTION!"; rolls by itself at 6 s | eyes on the goal line; says the goal aloud; presses A or waits | G (goal said by 0:30), board time |
| 0:03-0:07 | clap, board slides off, car rolls, free road | tries the stick; lane changes feel right | steer |
| ~0:07 | S1-1 Leaning False Front: twang, the front tilts, amber key light, prompt fades in | reads the prompt (lips, eyes); presses A at once, steers instead, or ignores it | P (prompt read), first A press |
| 0:07-0:09 | **the hold:** world goes black and white, whir, "NEXT MARK" inset in colour | holds without releasing; taps the stick (landing lane); presses B; lets the ring auto-cancel ("CANCELLED") | H (first hold), C (cancel) |
| the release | freeze, one black frame, splice click, timecode jumps, film 3 to 2 | **the face and the first 3 s of words.** "Whoa" or a laugh is good. "Huh?", "what was that?" is a flag. Any of the four words is a (c) risk | **K (cut landed, time), first words verbatim** |
| 0:07-0:12 alt | **drive:** steers L, front lands behind; **crash:** free "CUT! FREE TAKE", black, back at the line | reaction to the crash: shrug and retry is good, quits or says "unfair" is a flag | X (crash tally) |
| 0:12-0:17 | S1-2 Prop Truck, easy, 1.5 s slack, horn and headlights | lane change inside the telegraph toward the open side; CLOSE! or PERFECT! stamp; "+1 FILM" | D (drive on purpose, time, film) |
| 0:17-0:22 | S1-3 Light Rig Swing, the first timed gap | cuts it, drives it, or crashes. Repeated crashes here are a (d) risk | X |
| ~0:22-0:28 | blue-pencil card "DIRECTOR'S NOTE: cut / costs 0 film", the water tower buckles | reads the card; holds and releases. This is the last easy route to (a) on a clean run | K |
| 0:28-0:42 | S1-5 Barrel Roll (easy), the surge, S1-6 The Big Facade (two hops) | looks at the film bar; two-hop attempts; frustration after 3 crashes | X, film glance |
| ~0:42 | "THAT'S A WRAP" | reaches it inside 3:00 with 3 crashes or fewer | W (wrap, time) |

Trouble signs to timestamp (no comment): holds near the 1.5 s limit again and again; mashing A; a lane press that did
nothing during the freeze; looking at you for help; "teleport", "lag", "bug", "broke"; a pad dropout; a long silence
with no input. The build buffers a lane press through hit-stop (onboarding §3 rule 1, **Proposal** there), so a lost
press is a defect to note.

## 6. Score sheet (one page per tester; copy this block for T1 and T2)

```
JUMP CUT STRANGER GATE   Tester: T1 / T2   Date: Thu 2026-11-12   Build sha: ________
Plays games: never / sometimes / often   Recording file: ________   Recording OK: Y / N   Clip OK: Y / N
Technical faults (time, what): ____________________________________________________
```

**Stamps** (stopwatch from Play; ruling targets in brackets)

| Stamp | Time | Note |
|---|---|---|
| Play pressed (0:00); board rolled by press / by itself | | |
| G: goal said aloud or shown understood [by 0:30] | | |
| P: prompt read; first A press | | |
| H: first hold; C: first cancel (B / auto) | | |
| K: first cut landed [(a) by 1:00] | | |
| D: first stunt driven on purpose, film shown [(b)] | | stunt: film: |
| X: crashes (tally every CUT! slam, free one included) [(d) 3 or fewer] | | |
| W: wrap slate [(d) by 3:00] | | |
| STUCK (longest time with no progress) | | |

**Criteria** (score from the recording; write evidence as a time)

| | Result | Evidence |
|---|---|---|
| (a) cut inside 60 s | PASS / FAIL | cut landed at ____ |
| (b) drove one on purpose, film above 0 | PASS / FAIL | stunt ____ film ____ ; intent: lane change in the telegraph / said aloud / Q4 |
| (c) "what happened when you let go?" | PASS / FAIL / FLAG | Q1 word for word: ______________________ ; fail words said: lag / glitch / bug / teleport / close equivalent (FLAG) ; edit words said: skip / jump / cut / edit ; weak (neutral): Y / N ; unprompted remarks in play: ________ |
| (d) wrap with 3 crashes or fewer, inside 3:00 | PASS / FAIL | crashes ____ ; wrap at ____ |

**Signals** (not scored; they say what to tune)

| Signal | Y / N or words |
|---|---|
| Knew the goal by 0:30 (Q2 and G) | |
| Read the prompt before the first hold | |
| Understood the film bar (Q3) | |
| Understood the crash as "take two" (Q5) | |
| Car feel, their words (Q6) | |
| Would keep playing now (Q7) | Y / N |
| Q4 answer, word for word | |
| Confusion (Q8) and first change (Q9) | |

**Tester result:** ALL FOUR PASS  /  FAILED: a  b  c  d  (circle)   Valid run: Y / N (N if a fault, a build without the
prompt or goal line, or a facilitator slip invalidates it; say which)

## 7. Decision rule (GDD §9 row for Thu 21:00; the owner decides, a Fable agent reviews first)

**Evening timeline** (all PT; GDD §9 wins over the older 20:00 "fixes" row in `jam-execution-plan.md`)

| Time | Step |
|---|---|
| 19:15-19:30 | KB/M check (owner alone) |
| 19:30 | Build frozen; Legion checks: pad, OBS test take, warm-up run |
| 19:45 | Ready; sheets printed; T1 and T2 confirmed |
| 20:00 | T1: consent and brief 3 min, play 3 min (30 s grace), questions up to 8 min. About 15 min in all |
| 20:15 | T2: same. Between them: stop and rename the file, relaunch to the title, new sheet |
| 20:30-20:50 | Finish both sheets from the recordings. Copy the files off the Legion over `ssh <device-host>` while you do. Give the Fable agent the evidence pack (below) |
| 20:50 | The call: read the Fable review, decide |
| 21:00 | Decision written, never later. Fri work starts on the chosen path |

**Fable evidence pack** (an agent cannot hear): both sheets with Q1 and Q4 verbatim; still frames cut from each
recording with `ffmpeg` at every stamp (first hold, first cut, first drive, each crash, the wrap); this file's section 1.
No local model is needed. Ask it to score (a)-(d) independently, list every fail word, flag any sheet line a frame
contradicts, and recommend one row of the table below. The owner listens to the recordings for anything the sheet
missed (tone, hesitation) because only the owner can hear. If the owner and the Fable agent disagree on a criterion,
the stricter reading stands unless the owner writes why.

**The rule** (a criterion fails if it fails for either tester)

| Result | Decision | What Friday starts from |
|---|---|---|
| All four pass for both testers, and the car feels fine | Keep Jump Cut with the preview | Build on it. Fix the signals list from the sheets on the DataAsset |
| Fail (a) or (c), either tester | **Jump Cut without preview:** a press is an instant cut to the next mark, same juice, marks, economy and replay | The no-preview verb. The hold and its inset are dropped; do not retune and retest the preview |
| "The car does not feel good": the owner and both testers would not keep driving (Q7 no, twice, and the owner's own no) | **Rolling!** on the same scene clock, set pieces and replay | The runner-up concept on what exists |
| Fail only (b) or (d) | Tune the DataAsset: tier windows, slack, safe-lane help, prompt timing, crash cost | **Retest Fri 10:00** with a new stranger if one can be found (**Proposal**: the earlier testers are no longer naive), else retest the failed item only and mark it not naive |
| More than one row applies | **Proposal:** car feel first, then (a) or (c), then (b) or (d). The GDD lists each row alone | Fable and the owner confirm in the review |

An invalid run (technical fault, prompt or goal line missing, facilitator slip) is not scored. Replace it with another
tester if one can be found by 20:45. If there is only one valid run, it counts. **Proposal:** if there is no valid run at
all, or no launching build by 19:30, the 21:00 default is Jump Cut without preview, because the preview is the
unproven part, and the owner and Fable confirm it. No concept switch after Thu 21:00 (GDD §9).

**Write it down.** Commit to `jam-integration`: `stages/03_playtest/output/stranger-gate-2026-11-12/` with `T1.md`,
`T2.md` (the filled sheets) and `decision.md`. One line in `decision.md`:
`Stranger gate Thu 20:00. T1 a/b/c/d = _/_/_/_, T2 = _/_/_/_. Car feel: _. Fable: agree / differs on _. Decision: _. Decided HH:MM.`
With the testers' OK, a clip and the numbers are good dev log material for Glass Box.

## 8. Open decisions from this file (all Proposals; none changes the GDD)

- **P1** Count every clapper slam in (d), the free first crash included.
- **P2** Treat close equivalents of the four fail words as a FLAG that the Fable review rules on.
- **P3** Consent wording and the "delete by Sunday Nov 22" retention; clip permission asked separately at the end.
- **P4** Adult testers only; ask three people on Wed; one gamer and one non-gamer if the choice is free.
- **P5** Tie-break order when several rows apply: car feel, then (a) or (c), then (b) or (d). Stricter reading stands on a
  disagreement.
- **P6** Retest Fri 10:00 with a new stranger if possible; invalid runs replaced by 20:45; no valid run or no build means
  Jump Cut without preview.
- **P7** The KB/M run is an owner check, not part of the scored test; the strangers are scored on the pad only.
