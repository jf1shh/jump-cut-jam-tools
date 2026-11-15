# The first two minutes: level design and onboarding for jam judges

Research date: 2026-10-29. Method: about 14 web searches and fetches (WebSearch/WebFetch), plus a read of the existing megajam notes. No GDC Vault video was watched; GDC material below is second-hand via write-ups. Pages that did not load are listed under Gaps.

**Status: research notes only.** No gameplay, levels or art are built or implied by this note; nothing here may be built before the contest window opens (Rule 7(h)).

**Takeaway.** Everything found points the same way: a judge gives a game a few minutes, so the first 120 seconds are most of the Level Design, Gameplay and Fun Factor scores. The Nintendo method (teach one verb in a safe space, test it, twist it, then stop) is the one well-documented recipe for wordless onboarding, and World 1-1 is the model: the first mistake costs almost nothing, the first reward arrives in seconds, and one verb is taught at a time. Jam evidence agrees: judges say "make it very easy to get to the game", flag onboarding overload first, and complain about missing checkpoints. So for day 3: one verb in the first 30 seconds, a first success inside 20 to 30 seconds (inference), no way to be stuck or to fail permanently in the first minute, a respawn at the start of the current room, light and colour that point at the goal, and a finish at about 5 to 8 minutes. There are few hard numbers; most of the "how fast" figures below are inference. Test on someone who has never seen the game.

This note builds on, and does not repeat, `jam_winning_strategy_and_presentation.md` section 3 (Rob Miles, Kenney, "state the goal on screen", "theme-twist mechanic within about 30 s"), `scope_discipline_and_iterative_design.md` (30-second fun test, feature/content/polish ratios), `mechanics_and_genre_ideas.md` section 1 (gradual per-level rules beat front-loaded complexity, GMTK 2023/2024), and `jam_rules_judging_past_winners.md` Q2 (the criteria list includes "Level design and game progression", read as a reason for a clear start, escalation and end). `RULES.md` supplies the seven criteria and the double-weight Fun Factor tiebreak.

## 1. Teach without text: Nintendo's method

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| Hayashida (3D Land / 3D World) describes four steps: **introduction** (one core mechanic, learned by using it), **development** (a slightly harder use of the same mechanic), **twist** (something unexpected that makes you rethink it), **conclusion** (a chance to show mastery). He took it from kishōtenketsu; Miyamoto brought the idea in. | high | designer talk (via interview write-up) | [Game Developer, "The secret to Mario level design"](https://www.gamedeveloper.com/design/the-secret-to-i-mario-i-level-design) |
| Mark Brown (GMTK) summarises 3D World stages as a mechanic "taught, developed, twisted and then thrown away", each in roughly five minutes. | high | designer talk (commentator) | [MCV, 18 Mar 2015](https://www.mcvuk.com/development/video-nintendos-level-design-secrets-in-four-steps) |
| Hayashida says picking one core concept per level is "really important". The same article does not say how text is avoided; it only implies learning by doing. | medium | designer talk | [Game Developer](https://www.gamedeveloper.com/design/the-secret-to-i-mario-i-level-design) |
| World 1-1 sequence: a slow Goomba on the first screen, then a row of blocks (the first gives a coin, the second a Mushroom), then pipes of different heights, then pits of different widths. Each element teaches one thing (jump on or over enemies; bump blocks; hold jump longer; run for distance). | medium | third-party (encyclopedia, cites interviews) | [Wikipedia, World 1-1](https://en.wikipedia.org/wiki/World_1-1) |
| The first mistake is cheap: a novice may die to the first Goomba but loses almost no progress; some pits have floors, so you can climb out instead of restarting. | medium | third-party | [Wikipedia, World 1-1](https://en.wikipedia.org/wiki/World_1-1) |
| Miyamoto: Goombas are harmless "as long as you stamp on them", and a player who skips the first one is "shocked" by the Mushroom. Reporting says the first enemy was changed from a turtle to a Goomba because a turtle cannot be beaten by a simple jump. This is a source for: pick the first enemy so the obvious input beats it. | medium | designer talk (Iwata Asks, Eurogamer via secondary) | [Iwata Asks NSMB](https://iwataasks.nintendo.com/interviews/wii/nsmb/0/3) (not opened directly); [GameRevolution](https://www.gamerevolution.com/features/362525-perfect-level-super-mario-bros-world-1-1-changed-everything) (not opened directly) |
| Miyamoto's stated aim for 1-1: players "gradually and naturally understand what they're doing". New elements arrive only when the player is ready, each followed by a slightly harder use. | medium | designer talk (secondary quote) | [Wikipedia](https://en.wikipedia.org/wiki/World_1-1); [search summary of Medium, Pinnguaq, NTU pages](https://medium.com/@daverage/learning-from-games-onboarding-and-mario-53334c7576f1) (Medium page returned 403; claims come from search snippets only) |
| The "mushroom corridor" idea (a block layout that forces you to touch the power-up) is a way to make sure a key discovery happens. | low | third-party | [Wikipedia](https://en.wikipedia.org/wiki/World_1-1) |
| Portal is widely described as having no real tutorial: it teaches through chamber layout. This is commentary, not a Valve source. | low | third-party | [itch.io post](https://itch.io/post/10651558) (snippet only) |
| Portal chamber process: whiteboard sketch, vetted by the design team, built in Hammer, then playtested; GLaDOS speaks at the start and end of a puzzle. | medium | third-party (press feature) | [Game Informer, 2010](https://gameinformer.com/b/features/archive/2010/03/17/thinking-with-portals-making-a-test-chamber) |

What it means (inference): for a 4-day game, plan the level as one kishōtenketsu arc per mechanic, not a tutorial plus a game. Beat 1: the verb in a safe room with an obvious target. Beat 2: the same verb with a small complication. Beat 3: the twist, where the jam theme should show up. Beat 4: a short finale that uses everything.

## 2. How fast must the first win come

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| An itch.io judge limits play to "five to ten minutes" per entry to cover more games, and says that first window decides hook, onboarding, presentation, controls and "whether they want to continue". | medium | judge feedback | [itch.io post 17295975](https://itch.io/post/17295975) |
| The same judge praised the concept but said the mechanics needed more guided onboarding: moving, entering heads and using skills was "a lot to understand quickly". Art cohesion and level design were also flagged. | medium | judge feedback | [itch.io post 17295975](https://itch.io/post/17295975) |
| Another judge wrote that the player needs onboarding because the developer will not be standing beside them. A school-jam judge noted a player spent too long working out how to shoot on the first screen. | low | judge feedback (snippets only) | [itch.io CMGT jam entry](https://itch.io/jam/cmgt-jam-3/rate/2369315) (snippet only) |
| Postmortems describe drop-off when three core mechanics arrive in the first five minutes, or when players get resource, building and lore text before moving a unit. These come from a tools-company blog; the numbers are not verified. | low | postmortem (unverified blog) | [Wayline tutorial postmortem](https://www.wayline.io/blog/tutorial-ux-postmortem) (snippet only) |
| Informal community advice for rating: about 5 to 10 minutes of total play, including restarts. Ludum Dare's own rules call the ideal game one you can play "in the browser, in a few minutes, alone". Ludum Dare has no official rater time. | low | third-party (forum) / organiser rule | [GameSalad forum](https://community.gamesalad.com/discussion/comment/532525/); [LD 2017 rules](https://ludumdare.com/resources/archive/rules-2017/) |
| A jam rater says the instructions/tutorial are among a game's most important features and that a simpler, polished game with clear instructions beats an ambitious one that cannot be understood in a few minutes. | low | judge feedback (one rater, small sample) | [Super Jump Magazine](https://www.superjumpmagazine.com/playing-and-rating-game-jam-games/) |

No source gives a measured "first win by N seconds". Treat these as design targets, not facts (inference):
- First input within 5 seconds of control; no unskippable intro (matches `jam_winning_strategy_and_presentation.md`).
- First visible success (an enemy dies, a door opens, a coin or score ticks) within 20 to 30 seconds.
- Theme twist visible by about 60 seconds; first "that was clever" moment by 90 to 120 seconds.
- First checkpoint-sized goal complete by about 2 minutes, so a judge who stops there has seen a full arc.

## 3. Difficulty for someone who plays once

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| In jam comment threads, missing checkpoints is a recurring complaint; developers admit they ran out of time or the system broke in the last hour. One commenter wanted respawn at the start of the room where you died. | medium | postmortem / judge feedback (anecdotal itch threads) | [itch.io threads, via search](https://itch.io/post/9128356) (snippets only; several posts) |
| Developers who tested only themselves missed how hard their jumps were; some said the first levels were probably too hard, and difficulty spikes upset players. | medium | postmortem (anecdotal) | [itch.io threads, via search](https://itch.io/post/1697472) (snippet only) |
| Perceived difficulty varies a lot with the player's genre experience; the same game was called too easy, too hard and just right. | low | postmortem (anecdotal) | same threads |
| Celeste: checkpoints at the start of each room, near-instant respawn, new hazards introduced one at a time, Assist Mode optional and not the default. Critics argue deaths still feel harsh with assists on. | medium | third-party (reviews and analysis) | [Game Wisdom on Celeste](https://game-wisdom.com/analysis/celeste); [Vice](https://www.vice.com/en/article/celeste-difficulty-assist-mode) (snippet only) |
| In 1-1 the cost of the first error is almost nothing (see section 1). | medium | third-party | [Wikipedia](https://en.wikipedia.org/wiki/World_1-1) |

What it means (inference):
- **No permanent failure in the first minute.** The first hazard can hurt (so the player learns) but should not end the run or lose more than a few seconds.
- **Checkpoint per room or beat**, respawn in under 2 seconds. This is cheap in Blueprint: one `PlayerStart` or checkpoint actor per beat plus a restart-at-last-checkpoint path.
- **Assist options are a bonus, not a need.** One toggle (more health, slower enemies, or "no fail") is enough if time allows. Do not build a menu for it.
- **Front-load forgiveness, back-load challenge.** The judge who plays once should see the hard part last, if at all.
- Recommended playtest order: the designer's own run is not data. Use a first-time player on day 3 (see checklist).

## 4. Guiding the eye: light, colour, landmarks

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| Light the intended route and leave neighbouring areas darker; people are drawn to the brightest point on the screen. Over-intense light feels heavy-handed. Tinted light can reinforce colour coding. | medium | third-party (trade article) | [Game Developer, J. Wilson, 20 Jul 2018](https://www.gamedeveloper.com/design/level-design-tricks-of-the-trade) |
| Give each colour one consistent meaning (e.g. climbable, dangerous) and plan it early into the art. Examples cited: Mirror's Edge orange for the route, highlighted climbables in Uncharted and Tomb Raider. | medium | third-party | [Game Developer, 2018](https://www.gamedeveloper.com/design/level-design-tricks-of-the-trade) |
| Place landmarks that mark objectives and show progress; they also break line of sight. "Show, don't tell": the player should know the destination, discover the route. Foreshadow the goal (e.g. something moves toward it). | medium | third-party | [Game Developer, 2018](https://www.gamedeveloper.com/design/level-design-tricks-of-the-trade) |
| Readability rules from a game developer: large simple shapes, a clear complexity gap between characters and environment, fewer exits per space, standard sizes, avoid ambiguous geometry (e.g. sloped walls), and reduce art density where you need to guide. Test with the squint test. | medium | third-party (developer blog, 2026) | [Blendo Games, "Level Design: Readability", 23 Jun 2026](https://blendogames.com/news/post/2026-06-xx-leveldesign_readability/) |
| The Level Design Book ranks contrasting landmarks and focal points at the top of composition and is sceptical of "leading lines" as a tool. Read through a proxy mirror; check the canonical site before citing. | low | third-party | [Level Design Book (proxy copy)](https://https-book_leveldesignbook_com.proxy.bugsmash.io/process/blockout/massing/composition) |
| Playtesting with others is "the only surefire way" to know a level reads. | medium | third-party | [Blendo Games](https://blendogames.com/news/post/2026-06-xx-leveldesign_readability/) |

## 5. Top-down vs third-person readability

Little solid evidence was found; both rows below are thin and mostly practitioner opinion.

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| Top-down shows everything in view at once (unless fog of war), so layout is easier to understand but has less room for surprise or multi-floor spaces; one team dropped top-down because of ceilings and floors. | low | third-party | [Game Design Skills, top-down level design](https://gamedesignskills.com/game-design/top-down-level-design/) (snippet only); [moddb post](https://www.moddb.com/news/armored-squad-fresh-look-on-level-design) (snippet only) |
| A third-person camera shows avatar and surroundings, but a poorly set camera clips walls or hides key information. | low | third-party | same search results |
| No source on silhouette contrast under overhead vs follow cameras was found. | n/a | none | gap |

Inference, from the readability rules above plus UE practice: in **top-down** the player reads floor-plan shapes, so use floor colour and light pools for the route, keep walls low or cut away so nothing hides the goal, and give the player and key objects a bright saturated rim against a dark muted floor. In **third-person** the player reads depth and sightlines, so put a tall landmark or bright light at the end of the first straight, keep the camera arm short in small rooms, and avoid ceilings or props between camera and character in the first room.

## 6. What makes judges and players quit or mark down

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| Not knowing the goal after minutes of play ("spent 5 minutes without knowing the goal"); instruction screens are the first thing to add; games that "plain didn't work". Already recorded in `jam_winning_strategy_and_presentation.md`. | medium | judge feedback | [Rob Miles, 2015](https://www.robmiles.com/journal/2015/31/3/meatlyjudged) |
| Too many mechanics at once, unclear first action, no checkpoints, unplaytested difficulty, and art that is not cohesive were the repeated complaints in the itch comment threads and judge notes above. | medium | judge feedback / postmortem (anecdotal) | sections 2 and 3 |
| Epic MegaJam winners: no new onboarding-specific judge quotes were found beyond what `jam_winning_strategy_and_presentation.md` section 2 and `jam_rules_judging_past_winners.md` Q9 already record. | n/a | none | gap |

## Day-3 checklist (apply once the core loop works)

Run it in order with a stopwatch and one first-time player (a family member or a friend; do not explain anything). Fix top items first. Items marked (I) are inference from the evidence above.

1. **Cold start.** Packaged build launches to playable control with no unskippable splash, logo or cutscene; first input possible within 5 seconds (I). Controls shown on screen as icons at the moment they are needed, not in a wall of text.
2. **One verb first.** Only one new mechanic in the first 30 seconds; the second arrives only after the first has been used successfully (Hayashida's introduction step).
3. **First win in 20 to 30 seconds** (I): something visibly succeeds (enemy dies, door opens, pickup, score). Reward is audible and visible (sound plus particle).
4. **Safe first mistake.** In the first minute, failure costs under 5 seconds and no progress; no permanent fail, no soft-lock, no way to leave the playable area unnoticed.
5. **Goal on screen.** One short line or icon says what to do, visible for the first minute and re-findable later (e.g. a pause or hint key). Judges who cannot tell the goal after a few minutes leave.
6. **Eye guide.** Squint test: blur or squint the first screen and the path or goal must still be the brightest or most contrasting thing. One colour means one thing, everywhere.
7. **Landmark at each beat.** A bright, tall or moving thing marks the next objective from where the player stands.
8. **Teach, test, twist.** Mark the level in three chunks on paper: verb safe, verb pressured, verb twisted (theme shows up here). Cut anything outside these.
9. **Checkpoints.** Respawn at the start of the current beat in under 2 seconds; test by dying on purpose at every beat.
10. **Difficulty ramp.** First 2 minutes: the first-time player should not die more than once. If they do, soften before adding anything. Hard content only after minute 3 and optional if possible.
11. **Optional assist.** If time allows, one toggle (health, speed or no-fail). Not worth a menu.
12. **Session length.** Full run is about 5 to 8 minutes for a first-time player (I; from the 5 to 10 minute judge norm), with a clear end state and "thanks" screen that says what the player did. Do not pad.
13. **Fresh-player test.** Watch silently; note every pause over 5 seconds, every wrong guess, and every moment they look away from the action. Each is a design bug. Do this at least twice on day 3 and once after fixes.
14. **Video match.** The first 30 seconds of the submission video should be the same arc a player sees (see `jam_winning_strategy_and_presentation.md`).
15. **Cut rule.** If the checklist fails and time is short, cut content and keep the first two minutes. A short, readable game beats a long, confusing one (scope notes).

## Small-level layout templates (words only)

All are single-map, 5 to 8 minute designs for one builder in about a day of layout. Build blockout first with grey boxes and the final light colours; art later.

**A. Linear gauntlet (3 to 4 rooms in a line).** Room 1: empty safe space, one prop that teaches the verb, goal visible at the far end under a bright light. Room 2: same verb with one obstacle or enemy (the test). Room 3: the twist, where the theme changes the rule (e.g. a reversed verb, a new hazard, a changed goal). Room 4: finale mixing both, ending on a clear exit or boss-like target. Checkpoint at each door. Best for: platforming, action, and anything where the camera follows a path. Lowest risk.

**B. Hub and three spokes.** A small central hub with the goal board or exit locked behind three marks. Spoke 1 teaches the verb, spoke 2 tests it, spoke 3 is the twist; each returns to the hub and lights a marker. The hub lights progress (three bulbs, three coloured pillars). Players may take spokes in any order but spoke 1 should be the brightest and nearest. Best for: puzzle, exploration and "choose your path" games; read-order risk is higher, so test that first-time players pick spoke 1.

**C. Single arena with waves.** One readable room (big shapes, one landmark in the centre). Wave 1: one easy enemy while a prompt appears (teach). Wave 2: a few enemies (test). Wave 3: the twist (new enemy type, theme rule, or hazard). Final wave: all of it, then a victory beat. Players cannot get lost, so effort goes to feel and feedback. Best for: top-down shooters or brawlers, survival and defence. Risk: Level Design score can look thin; add a few heights, cover and a clear safe corner, and change the room between waves (doors open, floor changes).

**D. Loop with a shortcut (optional extra).** A circular route that returns to its start so the player sees the goal early, with one shortcut gated by the verb or the twist. It gives a "I get it now" moment (like the 1-1 pipe shortcut) at low cost. Add only after A, B or C works.

Rule for any template (inference): the first screen shows the start, the goal marker or landmark, and the first obstacle together.

## Gaps

- No measured data on jam ratings vs session length or first-win time; the "20 to 30 second" and "5 to 8 minute" targets are inference.
- GDC Vault talks (Portal, Valve level design, Nintendo) were not opened; Portal and Valve claims are second-hand or snippet only.
- The Medium Mario onboarding article returned HTTP 403. The Jesper Juul page held only a video embed, with no transcript. Iwata Asks and GameRevolution were seen only through search snippets. Wayline blog and itch.io comment threads were seen through search summaries; individual posts were not all opened.
- No Epic MegaJam judge quotes about onboarding or level design were found beyond those in the two prior notes.
- Top-down vs third-person readability evidence is thin and anecdotal.
- No source on the Level Design criterion's exact rubric for 2026 (see `jam_rules_judging_past_winners.md` Q2).

## Next checks before Nov 11

1. Open the canonical Level Design Book pages on composition and flow (not the proxy) and the Game Maker's Toolkit episodes on Mario 1-1 and 3D World; add direct quotes.
2. Watch or read the GDC Vault Valve and Nintendo level design talks if free; check transcripts for the safe-failure and checkpoint points.
3. Read two or three Epic MegaJam 2024/2025 winner pages and comment threads for level-design remarks.
4. Choose one template (A, B or C) after the theme drops; do not decide earlier.
5. Prepare, within Rule 7(h), only non-game material: a blank playtest sheet (stopwatch, pauses, deaths, quits) and the checklist above. No levels, art or gameplay before the window opens.

## Caveats

- Nintendo material comes mostly through interviews and write-ups, not the original Japanese sources; quotes may have been translated and shortened.
- Hayashida's four-step pattern is about 3D Mario stages; it is a useful template, not proof that it raises jam scores.
- Jam judging is varied: the judge quoted plays 5 to 10 minutes; others may play less or more. Epic's judges' own habits are unknown.
- itch.io comments are anecdotal and survivorship-biased; no judge score data was found.
- Items marked (I) or "inference" are the author's judgments. Confidence labels are this note's own, not a vote.
- Colours, camera and checkpoint advice must be re-tested in UE 5.8 on the actual build; none of it has been tried here.
