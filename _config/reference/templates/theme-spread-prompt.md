# Theme spread prompt (prompt library)

Use on reveal day (Wed 11:45, `stages/00_prep/references/jam-execution-plan.md` section 5; step 3 of
`_config/reference/research/theme-speculation.md` section 5). Pre-jam prompt artifact only (Rule 7(h)); contains no game
content. Dry-run 2026-11-11 on a made-up theme, with timings: `stages/00_prep/output/theme-drill-dryrun-2026-11-11.md`.

**How to run it (about 1-2 minutes of agent time, measured):**

1. Paste **Prompt 1** into a fresh agent session (Sonnet is enough) with the theme filled in verbatim. It
   reads the shortlist itself, so the 11:45 spread and the 12:15 shortlist fit come back in one answer.
2. While it runs, write your own 10 readings on paper (the owner's 11:45 slot). Then merge: tell the
   session which of yours it missed, before Prompt 2.
3. Check section C yourself: in the dry run, two runs on the same theme disagreed on whether one concept
   was a real or cosmetic fit. Then paste **Prompt 2** into the same session. It filters, scores and
   fills the one-pager. Read it, change what you disagree with, then commit the one-pager at 21:00 (not before: Rule 7(h)).

In the dry run the agents took 15-31 s per step. The slow part was copying one step's answer into the
next prompt by hand. Two prompts in one session remove that.

---

## Prompt 1: spread + shortlist fit

The 2026 Epic AI MegaJam theme is: **"<THEME, verbatim>"**

Read these files in `~/Projects/megajam` first (skim; the "repeated player decision" column is the key):
`stages/01_concept/references/game-concept-shortlist.md` and the five concept docs it links. Write no files.

Constraints: solo developer plus AI agents, four days, Unreal Engine 5.9 (5.8.4 fallback), stylized
low-poly art, Teen rating, no third-party IP, Windows build played on a handheld (Legion Go S, gamepad).
The game should be quick, replayable and skill-based, built around one core verb. Verbs we have prepared:
Throw (lead, `stages/00_prep/references/pre-jam-mechanic-toolkit.md`), Dash, Pull, Stack, Push, plus each shortlist concept's own
verb. Judges score 1-5 on: ambition and innovation, theme ("a fresh, clever take"), fun, gameplay, visuals,
level design and progression, audio. Fun breaks ties. Hundreds of entries will take the literal reading.

Answer in exactly these sections, short lines, no preamble:

**A. Readings.** 10 readings of the theme, most literal to most sideways, one line each. Mark the 2-3 you
expect most other entries to use with `(crowd)`.

**B. Fresh mechanics.** For the 4 freshest readings: the core verb (pick the verb that fits best; do not
force Throw), the one twist that *is* the theme as a rule (a resource, a timer, a state, a fail condition;
not story or title), what a judge sees in the first 60 seconds, and the riskiest part to build in four days.

**C. Shortlist fit.** A table, one row per shortlist concept: how the theme changes its repeated player
decision as a concrete rule | real or cosmetic (cosmetic = a relabel with no new rule) | keep or drop.

**D. Candidates.** Every kept item from B and C, one line each: `ID | name | verb | theme rule | biggest
risk`, ready for scoring.

---

## Prompt 2: filter, score, one-pager (same session)

Now pick. Read `_config/reference/templates/scoring-rubric.md` and `_config/reference/templates/gdd-one-pager.md`. Write no files.
Include any readings I added after Prompt 1.

1. **Filter to 3** from section D. Drop anything that needs multiplayer, an open world, dialogue trees or a
   humanoid hero; then drop the riskiest builds. Prefer 3 different verbs, so the runner-up is a real
   alternative. One line each on why the others went.
2. **Score** each of the 3 on the 7 rubric rows (1-5, one short reason each; 2 and 4 sit between the
   anchors), total /35, plus yes/no: "core verb playable in greybox within 12 h". Fun Factor is a paper
   guess at this point; say so.
3. **Decide** with the rubric rule (highest total among those with 3+ on Fun Factor and Gameplay). Name
   leader and runner-up.
4. **Risk fork:** the one thing that, if it fails at the Thu 01:00 day-1 gate (move + core verb in
   greybox), makes us switch; the cheap mitigation to try first; and the safe fallback (normally the
   runner-up).
5. **One-pager:** fill `gdd-one-pager.md` for the leader, one screen, including its "Pick" and "Risk
   fork" lines.
