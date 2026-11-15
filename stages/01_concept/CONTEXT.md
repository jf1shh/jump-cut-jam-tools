# Stage 01_concept — contract (Layer 2)

Rules are in `AGENTS.md` and `CLAUDE.md`; this file only routes.

## Purpose

Theme reveal to a picked concept and one-page GDD, within the first hours of the window.

## Inputs

- theme text (owner relay)
- `stages/01_concept/references/game-concept-shortlist.md`
- `_config/reference/templates/theme-spread-prompt.md`, `gdd-one-pager.md`, `scoring-rubric.md`
- `_config/reference/canon/jam-design-cheatsheet.md`, `jam-judging-criteria.md`

## Process

1. Read the theme and the cheat sheet; list 5 takes with `theme-spread-prompt.md`, drop the 2 obvious.
2. Score the rest with `scoring-rubric.md` (estimates only, no invented proof of fun).
3. Pick one whose core verb drives the loop; write `output/<name>-concept.md` from `gdd-one-pager.md`.
4. Write the cut list in the same file.

## Outputs

`output/<name>-concept.md` (one per candidate), `output/gdd.md` (picked concept), `output/prejam/` (pre-jam design prep pack for the picked concept: storyboards, style guide, HUD/UI spec, onboarding, fun plan, labelled reference pictures, `PREJAM-DECLARATION.md`; planning only, never imported)

## Routing

Next: `stages/02_build/CONTEXT.md`. On failure (no take scores, theme unclear): pick the cheapest loop from the shortlist and flag it to the owner; do not stall past hour 2.
