# Pre-jam mechanic toolkit

Prep document only — not game content. The real theme isn't revealed until the Nov 11 kickoff
livestream, and Rule 7(h) bans gameplay/levels/art before the contest window opens
(2026-11-12 00:00 ET). Nothing here is implemented in the editor; this is a planning/prompt
artifact to shorten day-one decision-making once the theme lands.

## Constraints this toolkit was built against

- Genre/perspective: wide open, no existing pull.
- Core feel: quick, replayable fun — arcadey, skill-based, "one more try," not atmosphere/mood
  or a clever-aha puzzle.
- Visual direction: stylized low-poly — flat-shaded/simple-textured, bold silhouettes, fast to
  generate through the local Nexus pipeline, friendly to weaker judge GPUs (Lumen Lite default).
- Mechanic scope ceiling: one verb, deep — a single core action with escalating challenge, not
  one verb plus an interacting twist. Prioritizes finishing and polishing over ambition ceiling.

## Lead pick: Throw

Picked over the rest of the shortlist below because it maps onto almost any theme Epic could
reveal (dodge/defense, delivery, sport, ritual/offering, escape) just by reskinning the
throwable/target fiction — the safest default to lock prep effort into without committing early.

**Core loop:** aim (trajectory preview) → release → object flies and hits or misses a target or
the environment.

**Escalation axes** (pick 2-3 to actually tune in the 4 days, not all of them):
- Target behavior: static → moving linearly → moving unpredictably → multiple simultaneous targets.
- Throw constraints: free aim → fixed power via timing-based release → limited ammo →
  trajectory-bending modifiers (wind zones, bounce surfaces).
- Scoring pressure: untimed → timer → combo multiplier for consecutive hits → risk/reward
  targets (small = high value, far = high value).

**Strongest shape for the brief:** a timed/scored arcade loop (carnival dunk-tank / disc-golf-at-
speed energy) rather than a narrative level. Easiest to make feel good through tight juice
(hit-stop, particle burst, score pop) rather than content volume — matches "quick, replayable
fun" directly.

**Asset footprint:** one throwable mesh (retexture for variety), 3-5 target archetypes, one small
arena. All stylized low-poly primitives, cheap to batch-generate locally.

**Theme-bending risk:** low, for the reason above.

## Fallback shortlist

Kept as a safety net in case the real theme fights "Throw" harder than expected. Not deep-dived;
revisit only if Throw doesn't bend onto the theme on day one.

- **Dash** — short burst-move with a cooldown, used to dodge hazards or cross gaps. Escalation:
  hazard density/speed, tighter timing windows, dash-through-only gates. Cheapest to animate
  (can fake with a blend or root-motion lerp); no rig complexity beyond the base character.
- **Pull** (grapple/magnet) — pull yourself toward an anchor, or pull objects toward you.
  Escalation: sparser/farther anchors, moving anchors, pulling hazards to redirect them. Needs a
  cheap rope/line effect (Niagara beam) on top of the base character mesh.
- **Stack** — pick up and stack objects to build height or bridge gaps. Escalation: less stable
  objects, time pressure, external forces (wind, shockwaves) toppling stacks. Cheapest asset
  footprint of the whole list — a small set of low-poly primitives (crates, blocks, barrels).
- **Push** — push objects or enemies, using momentum to knock things off ledges or into each
  other. Escalation: variable push-back resistance, chain reactions, pushing used defensively
  against incoming threats. No character rig required if framed as a top-down physics toy.

## How to use this on day one

1. Read the revealed theme.
2. Check it against Throw first. If it bends naturally (objects, aiming, targets, offense/
   defense, delivery, ritual), start building immediately — skip the fallback list.
3. Only if Throw genuinely doesn't fit, walk the fallback shortlist in the order above (Dash,
   Pull, Stack, Push) and pick whichever bends onto the theme with the least reskinning.
4. Whichever verb is picked, hold to the escalation-axis discipline above: tune 2-3 axes, not
   all of them, to leave tuning time for feel/juice instead of breadth.

## QA tagging conventions (for `scripts/qa_harness.py`, Phase B)

`scripts/qa_harness.py`'s soft-lock/reachability check (`_check_reachability`,
stages/00_prep/references/mock-jam-6-tooling-plan.md Task B1) needs two things placed in a level during the jam, or
it just reports `skipped`:

- A `PlayerStart` actor placed somewhere reachable.
- Every win-condition actor tagged `QAObjective` (Actor > Tags in the Details panel, not a
  Blueprint variable).

Without both, the check silently skips rather than failing — tag your objectives as you place
them, don't rely on remembering to do it at the end.

## Provenance

This document is a pre-jam planning/prompt artifact, produced in dialogue before the contest
window opens. No gameplay, levels, Blueprints, or art assets were built as part of it — see
Rule 7(h).
