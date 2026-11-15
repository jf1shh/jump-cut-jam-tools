---
tier: community
source: our own summary of _config/reference/canon/jam-judging-criteria.md (Section 9), _config/reference/research/first_two_minutes_level_design.md, _config/reference/research/game_feel_recipes_ue58.md, _config/reference/research/scope_discipline_and_iterative_design.md and _config/reference/research/jam_winning_strategy_and_presentation.md; talks and books in section 6 named only, not quoted
updated: 2026-11-11
---

# Jam design cheat sheet: one screen, aimed at the seven scores

Judges score seven things, up to 5 points each (`jam-judging-criteria`): Ambition and Innovation, Use of
Contest Theme, Fun Factor, Gameplay, Visuals, Level Design, Audio. A tie is re-scored with Fun Factor
counted twice. Each section below says which scores it moves. Plan only before 21:00 Wed (Rule 7(h)).
Scope rules live in `_config/reference/research/scope_discipline_and_iterative_design.md`, mechanic picks in
`stages/00_prep/references/pre-jam-mechanic-toolkit.md`; this page does not repeat them.

## 1. Theme reading (Theme, Ambition)

Write 5 readings of the theme. Drop the 2 that every other entry will make (the literal noun, the
first pun). Of the 3 left, pick the one that **changes what the player does**, not only how it looks: the
theme should be the rule of the core verb, not a skin on it. Test: can you say "you <verb> because
<theme>" in one line? If the theme only shows in the title and art, pick again. Run it with
`_config/reference/templates/theme-spread-prompt.md` (Prompt 1 + 2, about 1-2 min) and score with
`_config/reference/templates/scoring-rubric.md`.

## 2. The first 60 seconds (Level Design, Gameplay, Fun)

- Core verb usable in the first 10 s. No intro cutscene, no text wall; one key prompt at most.
- Teach by layout: a safe first room where the verb is the only thing to do, then the same verb with a
  small risk, then a twist on it. The first mistake costs almost nothing.
- Lead the eye with light, colour and a clear goal object; the goal is visible from the start.
- Theme visible in the first minute (`_config/reference/templates/playtest-checklist.md`).
- Background and examples: `_config/reference/research/first_two_minutes_level_design.md`; layout sketch first
  (`jam-level-layout-spec`, `jam-grey-box-first`).

## 3. Game feel and juice (Fun, Visuals, Audio)

Every player action gets a response you see **and** hear: hit-stop on impact, camera shake sized to the
event, a particle burst, a sound (placeholder is fine), a camera that leads the motion. One
`Juice_Hit(strength)` call fires them all. Order and hours: `jam-polish-pass` (12 steps, cheapest
first). UE tools: Set Global Time Dilation (hit-stop), Camera Shake assets (shake), Niagara
(`jam-cheatsheet-niagara`), MetaSound random/layered SFX, force feedback on the gamepad. Node names are
from 5.8 notes (`_config/reference/research/game_feel_recipes_ue58.md`); check them in 5.9 before use.

## 4. One loop, done well (Gameplay, Fun)

Thu: one core loop (verb, goal, fail, restart) that is fun with grey boxes and juice. No second feature
until a playtester smiles at the first one without help. Then beats, win/lose, art. **Cut list**, in
this order when time runs short: extra levels or beats, a second mechanic, story text, menus beyond
title/pause/end, fancy VFX. Never cut: restart, the end screen, sound on the core verb, the theme read.
Feature freeze Sat 22:00 (`stages/00_prep/references/jam-execution-plan.md`).

## 5. Five questions after every build (Fun, Gameplay, Level Design)

Ask a fresh player right after they put the pad down; write the answers in the fix list. Do not explain
the game first; watch where they get stuck.

1. What were you trying to do? (goal readable?)
2. What did you press first, and did it do what you expected? (core verb in 10 s?)
3. Where did you get stuck or confused? (layout teaches, or text needed?)
4. What was the best moment? (the thing to make bigger)
5. Would you play again right now? Why or why not? (Fun Factor, the tie-breaker)

This rides on the existing routine, it does not replace it: `_config/reference/templates/playtest-checklist.md`
(every packaged build), the agent gate (`jam-agent-playtest-gate`, `stages/03_playtest/references/playtest-gate.md`) and the hand
playtests in `stages/00_prep/references/jam-execution-plan.md`. The agent gate checks that the build works; these questions
check that it is fun.

## 6. Sources (names and links only)

- Jan Willem Nijman (Vlambeer), "The Art of Screenshake", INDIGO 2013:
  https://www.youtube.com/watch?v=AJdEqssNZ-U
- Martin Jonasson and Petri Purho, "Juice it or lose it", 2012:
  https://www.youtube.com/watch?v=Fy0aCDmgnxg
- Game Maker's Toolkit (Mark Brown): https://www.youtube.com/@GMTK
- Ludum Dare: https://ldjam.com
- Past Epic MegaJam results: https://itch.io/jam/2025-epic-megajam and
  https://forums.unrealengine.com/t/inside-unreal-2021-epic-megajam-results-october-14-2021/255359;
  our notes on winners: `_config/reference/research/jam_winning_strategy_and_presentation.md`
- Books: Steve Swink, *Game Feel*; Jesse Schell, *The Art of Game Design: A Book of Lenses*; Raph Koster,
  *A Theory of Fun for Game Design*; Scott Rogers, *Level Up!*
