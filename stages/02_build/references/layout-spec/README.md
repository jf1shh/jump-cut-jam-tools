# Layout spec: design page → top-down sketch → grey-box level

Status: tooling built and unit-tested. Run once in real UE 5.8 on 2026-11-09 (one practice theme, 3 rooms, n=1;
numbers in the canon note); the metric sheet numbers stay **UNTESTED** until measured in the editor. The idea comes from video claims (lessons 1.2, 1.3, 2.13, 2.14 in the
YouTube report); see `_config/reference/canon/jam-level-layout-spec.md`.

Rule 7(h): before 2026-11-12 00:00 ET this is practice only. The example layout is three abstract boxes.
Practice levels must live under `/Game/Mock*`; the checker refuses any other `level_path`.

## The steps

1. Write the one-page design (goal, route, one beat per room). Human.
2. Give an agent `prompt-template.md` plus `metrics.json`. It answers with ONE layout JSON (see `example-layout.json`).
3. `python3 scripts/layout_spec.py check LAYOUT.json` — fails on any breach of the metric sheet (exit 1) and
   says which. Fix and repeat. This is one "sketch round".
4. `python3 scripts/layout_spec.py render LAYOUT.json -o sketch.svg` — top-down SVG with a 500 cm scale bar,
   a hero marker, door marks, and every path's length and walk time. The human looks at it and paints over it
   (start, main route, side route) or edits the JSON. The SVG embeds the JSON, so `check` and `build` also accept the SVG.
5. `python3 scripts/layout_spec.py build LAYOUT.json -o plan.json` — runs `check` first, then writes the plan
   (floors, walls with door gaps, lintels, start, objective).
6. Headless, with the editor CLOSED (the editor's MCP has no arbitrary-Python tool, so an open editor cannot run this;
   invocation from the hub's real UE 5.8 runs, all paths absolute, no `; quit`):
   `timeout 300 ~/Projects/UnrealEngine-5.8/Engine/Binaries/Linux/UnrealEditor-Cmd ~/Projects/megajam-mock/MockSlime.uproject -ExecCmds="py /abs/scripts/ue_build_level.py --plan /abs/plan.json" -unattended -nosplash -stdout -FullStdOutLogOutput`
   then grep the log for `BUILD_LEVEL_OK` and `LEVEL_SAVE_RESULT=True`. `UnrealEditor-Cmd` does NOT exit after the
   script (seen in the rehearsal): the run is done when `BUILD_LEVEL_OK` appears. Then stop it by PID (`kill PID`;
   never `pkill -f`, it matched and killed the calling shell), or let `timeout` end it. Open the editor only afterwards, to look.
   In plan mode a beacon or orb mesh that is not in the project falls back to `/Engine/BasicShapes/Cube` / `Sphere`
   (log line `MESH_FALLBACK`), so `--beacon-mesh` / `--orb-mesh` are not needed. Without `--plan` the script still
   builds the old fixed room and needs its mock-jam meshes.

## What the layout file holds (all cm; same numbers as UE X/Y; the SVG is drawn like UE's top view: +x right, +y DOWN)

`level_path`, `rooms` (id, centre x/y, size w/h, optional `kind: corridor`, optional `height`), `doors` (room, side
N/E/S/W, `to`, offset from the side centre, width, height), `start`, `objective`, `paths` (id, `points`, optional
declared `length_cm` / `walk_time_s` that must match the computed ones), `targets.main_walk_time_s [min,max]`,
`gaps` (width), `ledges` (height).

## What is checked

Room, corridor and door sizes; wall height; rooms overlap; touching rooms must have the same `height`; every door
needs a `to` room, sits on a wall shared with it, stays clear of the wall ends and is not taller than either room;
start and objective are inside rooms and linked through doors; every path stays inside the rooms and crosses a wall
only inside a door gap; the `main` path starts at `start` and ends at `objective` (25 cm); declared lengths and
times match; main-path time inside the target; gap and ledge sizes.

## Not covered (so far)

- Gaps and ledges are checked but not built (listed under `not_built` in the plan).
- Props, kit pieces, decals, lights beyond the default lighting: none. Grey box only.
- The sketch is a rectangle floor plan. No slopes, no upper floors, no curved rooms.
- Compare step: the built level matches the sketch (X right, Y down) only with the editor top camera at pitch -90,
  **yaw -90** (`EditorToolset.EditorAppToolset.SetCameraTransform`, full toolset name). At yaw 0 +X points up the screen
  and the sketch looks rotated 90 degrees. "Editor is up" check: `mx.py toolsets --refresh` (without it the answer
  comes from the cache even with the editor closed); `mx.py call` needs the full toolset name.
- Handedness: UE is left-handed (+Y is the walker's right facing +X), so the SVG draws +y downward and side N means
  the low-y side. This follows the engine convention; the rehearsal still compares the built level's top view to the sketch.
- The checker also requires start and objective 39 cm (capsule radius + half wall) from every wall, and a door gap
  50 cm clear of the wall ends on both rooms it joins. The plan's `orb` (decorative PlayerOrb) is put in the start room.
- Re-running the build on an existing level adds the actors again (old `ue_build_level.py` behaviour).
