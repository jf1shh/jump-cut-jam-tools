---
tier: community
source: https://www.youtube.com/watch?v=n5WQ1kOJ7aY&t=3304s ; https://www.youtube.com/watch?v=1vCPxBibdp4&t=277s ; repo stages/02_build/references/layout-spec/README.md
updated: 2026-11-09
---

# Jam level layout spec (design page to grey-box level)

One practice run (n=1) of the tooling was done on 2026-11-09 (table below); everything else is UNTESTED.
The claims come from videos; the tooling is ours. Rule 7(h): the run used throwaway content, nothing is reused.

## Tip: plan the level as a top-down sketch with numbers before the agent places anything

**Why:** Video claim (lessons 1.2 and 2.13): agents build mechanics well but compose dull or broken spaces. One
presenter got a playable level in about two hours after about ten rounds on a top-down HTML sketch with distances and
walk times, before placing anything in the engine. Another gave a design doc with door and window sizes and the first
layout came out linear. A text description of an optional path failed; a screenshot painted with start, main route and
side route worked. Door smaller than a window was seen once.
**How to check:** Run the rehearsal below. Compare rounds and minutes with the claims, and look at the built level
from the top view next to the sketch.

## Tip: give the sketch a metric sheet it must obey

**Why:** Claim: check each building against a 1.9 m hero marker; a good door is about 2.2 m, a gate about 2.7 m.
Our numbers are in `stages/02_build/references/layout-spec/metrics.json` and every one is a guess or from memory of the UE template.
**How to check:** In the editor read the character's capsule and walk speed, measure the jump apex and run-jump
distance, and walk a 220 cm door. Write the real numbers into `metrics.json` and this note.

## What exists (tested by unit tests only)

- `stages/02_build/references/layout-spec/`: `prompt-template.md`, `metric-sheet.md`, `metrics.json`, `example-layout.json`, `README.md`.
- `scripts/layout_spec.py`: `check` (exit 0 clean, 1 findings, 2 bad input), `render` (SVG with 500 cm scale bar, hero
  marker, path length and walk time labels), `build` (check, then plan JSON).
- `scripts/ue_build_level.py --plan plan.json`: builds the planned rooms, doors (gaps plus lintels), start and
  objective; missing beacon/orb meshes fall back to engine basic shapes. Without `--plan` the old fixed room is
  built as before. Run it headless with the editor closed (the editor MCP has no Python tool); exact command in
  `stages/02_build/references/layout-spec/README.md` step 6.
- Level paths must start with `/Game/Mock` (Rule 7(h): practice only, never reusable in the entry).

## Rehearsal (Part B): one run, 2026-11-09, f3744ea

Mock theme "Three Grey Boxes", made up by the hub, unrelated to any jam idea; 3 rooms (StartRoom, Hall, GoalRoom),
real UE 5.8, MockSlime project. A single practice run, throwaway content. Raw files: hub50 `t07-partb/`
(REPORT.md, layout.json, build.log, editor.png).

| Number | Value |
|---|---|
| Sketch rounds (checker fails sent back + human paint-over edits) | 0 (first layout.json passed `check`; no paint-over) |
| Minutes, design page to a saved grey-box level in the editor | about 2 (21:10:06 to 21:11:52, incl. looking) |
| Minutes of that spent in the editor run itself | headless build about 0.5 (Python about 9 s); editor to MCP-ready 0.3 |
| Did the built level match the sketch from the top view (handedness, door positions)? | Yes, with top camera pitch -90 **yaw -90**: StartRoom top-left, Hall below, GoalRoom lower-right, X right, Y down. At yaw 0 it looks rotated 90 degrees. Doors too small at that zoom to see the gaps |
| Real capsule height/width, walk speed, jump apex, run-jump distance | not measured (UNTESTED) |
| What broke | Nothing in the build: `LEVEL_SAVE_RESULT=True`, `BUILD_LEVEL_OK`, 2 `MESH_FALLBACK` (expected), MapCheck 0 errors, 23 actors. Gotchas: `UnrealEditor-Cmd` never exits; `mx.py toolsets` answers from cache without `--refresh`; `mx.py call` needs the full toolset name; editor window was 900x640, not the saved 2560x1380 rule |

How to read the numbers: top-view picture with `spectacle -b -n -f -o FILE`, then crop (`mx.py shot` is broken on
the real editor). Capsule size, walk speed and jump apex: read the character's properties in the editor (by eye in
the details panel); no Python tool exists, so any value not read that way stays UNTESTED.

Compare with the video claim of about two hours and about ten rounds. Do not write the claim as our result. Our run: 3 rooms, one theme, zero rounds, about 2 minutes. Too small to say anything about a real jam level (n=1).
