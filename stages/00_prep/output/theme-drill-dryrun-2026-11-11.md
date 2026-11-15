# Theme drill dry run (2026-11-11, made-up theme)

One end-to-end run of the reveal-day theme drill (`stages/00_prep/references/jam-execution-plan.md` section 5, Wed 11:45-13:45)
on a made-up theme, **"Hold Your Breath"** (not one of the candidates in `_config/reference/research/theme-speculation.md`
section 3, and not the real theme, which was unrevealed at the time: 01:55 PT). Planning practice only
(Rule 7(h)): nothing here is built, and the drill's picks are not candidates for the entry.

Run by agents only (Sonnet subagents, read-only), 01:55-02:05 PT. Owner reading and thinking time is not
included; on the day it dominates.

## Run 1: the old template, one agent per plan step

| Plan slot | Step | Agent time | What slowed it or was vague |
|---|---|---|---|
| 11:45 | `theme-spread-prompt.md` (10 readings, 4 mechanics, pick) | 31 s | Ignored the 5 shortlist concepts entirely; forced Throw; said UE 5.8. Its pick was a fresh idea the next step could not compare with the shortlist |
| 12:15 | Shortlist theme fit ("how the theme changes decisions; drop cosmetic fits") | 16 s | No prompt existed; written by hand. Concept docs are framed on "connection/growth" and say nothing about timers or resources, so the agent guessed |
| 12:45 | Filter to 3 + score on the rubric + "playable in 12 h" | 25 s | Hand-merging both answers into one list took longer than the agent. Rubric: no feasibility row; 2 and 4 undefined; unclear whether the Fun doubling changes the total |
| 13:45 | One-pager (`gdd-one-pager.md`) | 15 s | No slot for the pick, runner-up, risk fork or fallback |
| | **Total** | **87 s** agent time; ~3 min wall with the hand-offs | |

Note: an agent's own guess of its time was wrong by 15x (it said 4-5 min; the harness measured 16 s). Use
measured times only.

## Fixes made

- `_config/reference/templates/theme-spread-prompt.md`: rewritten as **two prompts for one session**. Prompt 1 = readings +
  fresh mechanics (best verb, not forced Throw) + shortlist fit table + a candidate list in a fixed format.
  Prompt 2 = filter, score, decide, risk fork, one-pager. UE 5.9 (5.8.4 fallback), handheld/gamepad added.
  A step tells the owner to merge their own readings and to check the shortlist-fit table.
- `_config/reference/templates/scoring-rubric.md`: tie rule clarified (doubling only breaks the tie), 2 and 4 defined,
  feasibility sent to the risk fork.
- `_config/reference/templates/gdd-one-pager.md`: "Pick" and "Risk fork" lines added.
- `stages/00_prep/references/jam-execution-plan.md` section 5: the 11:45-13:15 rows now name Prompt 1 and Prompt 2.

## Run 2: the fixed template, one session

| Step | Agent time | Result |
|---|---|---|
| Prompt 1 (readings + mechanics + shortlist fit + candidates) | 23 s | 10 readings, 4 mechanics on 4 different verbs, 5-row fit table, 6 candidates ready to score |
| Owner merge (simulated: one added reading) | - | Added in the Prompt 2 message; picked up as a seventh candidate |
| Prompt 2 (filter, score, decide, risk fork, one-pager) | ~40 s | 3 scored, leader + runner-up, risk fork with mitigation and fallback, one-pager with Pick and Risk fork |
| **Total** | **~63 s** agent time, no hand-copying | |

Left open after run 2 (not fixed, judgment calls):

- Run-to-run variance: run 1 kept Root Circuit as a real fit, run 2 called it cosmetic. The owner checks
  section C; the template now says so.
- Run 2 kept two candidates on the same verb; Prompt 2 now asks for 3 different verbs if it can.
- Concept docs have no "core resource / timer / fail state" line, which is what a non-growth theme needs.
  Adding one line to each concept doc would make the fit step more reliable (follow-up, not done here).
- Goal in `theme-speculation.md` section 6 was under 45 min theme-to-one-pager; agent time is now about
  1 minute, so the budget is the owner's reading and the merge.
