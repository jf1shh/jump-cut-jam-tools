# Prompt template: one-page design → layout JSON

Fill the `<...>` parts and send it to the lead agent with `stages/02_build/references/layout-spec/metrics.json` and
`stages/02_build/references/layout-spec/example-layout.json` attached. The agent writes the layout only; it never places anything in the engine.
UNTESTED (see README). A human fixes the plan before any build: the videos say agents place objects well but
compose dull or broken spaces.

```text
You are laying out a grey-box level on paper first. Do not use Unreal. Output ONE JSON object and nothing else.

DESIGN PAGE (human wrote this):
<paste one page: player goal, the route in beats (one beat per room), what the player learns where,
 how long the first win should take, any optional side branch>

RULES
- Units are cm. Same numbers as Unreal X/Y: in the top view +x is right and +y is DOWN the page (+y is the walker's
  right when facing +x). Door sides: N = low-y side (top), S = high-y side, W = low-x side, E = high-x side.
  A room is a rectangle: centre x,y and size w (along x), h (along y).
- Keep the start and the objective at least 39 cm from every wall (capsule radius + half wall).
- Obey metrics.json exactly: door width/height, corridor width, room size, wall height, jump gap, ledge height.
  Do not invent a door that violates it; make the room bigger instead.
- Rooms may touch but never overlap. A door sits on a wall the two rooms share, and its gap must stay inside that wall.
- Every beat in the design page is one room or one corridor. Name rooms after the beat.
- Give the main route as a path with id "main": points [[x,y],...] from start to objective, through the doors.
  Put its length_cm and walk_time_s (length / walk_speed_cm_s from metrics.json) in the path.
- Set targets.main_walk_time_s to [min, max] seconds from the design page's first-win time.
- If the design has a side branch, add a second path with its own id and numbers.
- level_path must start with /Game/Mock (practice only).
- Same keys as example-layout.json. No comments, no extra keys.

SELF-CHECK before answering: list each door with its width and height, each path with its length and time,
and say in one line each whether it meets metrics.json. Then output the JSON.
```

## After the answer

1. Save the JSON as `layout.json`. Run `python3 scripts/layout_spec.py check layout.json`.
2. If it fails, paste the FAIL lines back to the agent: "fix only these". One round = one check run that went back.
3. When `check` is clean, run `render`, look at the SVG, and paint over it or edit the JSON where the space is
   dull (linear, no choice, no landmark). Each human edit then `check` again counts as a round too.
4. `build`, then run `ue_build_level.py --plan` (README step 6).
