---
tier: tested
source: 02_build dry-run-plan.md
updated: 2026-11-10
---

# Rigging a character: timed log of the dry run (both halves run; NO-GO for now)

Practice run on the coded fallback character (`procedural_props.py`), not entry content (Rule 7(h)). Only what we
ran is in this note. Both halves are run. Result: **NO-GO** (see the last section).

## Tip: the Blender half is seconds, not an hour
- **Why:** measured 2026-11-09 on Blender 5.2.3, CPU only: `rig_mannequin.py` (26 bones, mannequin names) took
  0.5 s of script time; `rig_rigify.py` (Rigify rig, 33 deform bones after dropping face/finger bones) took 2.7 s. Both included importing the
  1248-vertex character; neither included Blender's start-up or building the prop.
- **How to check:** `blender -b -P scripts/rig_rigify.py -- OUT_DIR` prints a `RIGIFY ... secs=` line.

## Tip: "unweighted=0" proves nothing: check that every body group got vertices
- **Why:** automatic weights fail on a character made of loose boxes ("Bone Heat Weighting: failed to find
  solution", all 1248 vertices). The first fallback (nearest thin bone segment) printed `unweighted=0` while the
  torso went to clavicles and thighs (spine and pelvis got 0 vertices) and, on Rigify, the arms went to the spine
  (16 arm vertices against 384 on the mannequin rig). Review caught both. Fixed 2026-11-09: radius-based nearest
  bone, Rigify metarig fitted to the layout, only trunk/limb bones deform, and the scripts now print
  `cover_core/arms/legs/head` and exit 3 with `COVERAGE FAIL` when a group holds too little (core 10%, arms 5%,
  legs 10%, head 3%).
- **Measured now (fallback prop, 1248 vertices):** mannequin path core 256, arms 400, legs 368, head 224; Rigify
  path core 224, arms 400, legs 368, head 256; both exit 0. The skin is still rigid (one bone per vertex, no smooth
  armpits or knees): good enough to see the rig move, not a quality result.
- **How to check:** the `cover_*` fields on the RIG / RIGIFY line; `tests/test_rig_scripts.py` asserts the floors.

## Tip: counting vertices per body group still misses a rig turned apart from its mesh
- **Why:** with `--face -Y` the first version turned the mesh and the armature together, but the mesh is a child
  of the armature after binding, so the mesh turned twice (-180) and the bones once (-90): upper-arm bones 0.56 m
  from their vertices while `cover_arms=400` and `unweighted=0` looked fine (review round 3). Now the mesh is
  turned alone before the bones are built and nothing is turned after binding, and each bone's distance to the
  centre of its own vertices is checked (`align_max_m`; limit 0.15 x height; healthy prop 0.24 m mannequin path,
  0.16 m Rigify path; the broken case 0.56 m). Failure exits 4 with `ALIGNMENT FAIL`.
- **How to check:** `tests/test_rig_scripts.py::test_bones_sit_on_their_vertices_for_every_output_facing` runs all
  four `--face` values.

## Tip: inputs must face +X with feet on z=0; Blender exits 0 on failure unless wrapped
- **Why:** the bone layout assumes the prop's pose. Sideways meshes (facing -Y or +Y) are refused from the bounding
  box. Backwards meshes (facing -X) are refused by a floor-level check: toes must reach farther forward of the
  lower-leg line than heels reach back. That check needs feet that differ by at least 1% of the height; on symmetric
  feet the script prints `NOTE front/back assumed +X, not checked` and carries on, so front/back is NOT guaranteed.
  Bones are fitted to the mesh's own height, and `rig_bones.run_main` forces a real exit code because
  `blender -b -P` returns 0 even after an error. Blender's heat weights proved fragile on loose pieces (a copy of
  the prop turned 180 degrees got a partial, wrong heat result), so when the checks fail the scripts redo the skin
  by nearest bone (`weights=` on the RIG line says which was used).
- **How to check:** `tests/test_rig_scripts.py` (`test_wrong_facing_input_is_refused`,
  `test_backwards_input_is_refused_and_accepted_with_input_facing`, `test_generic_names_skip_root_in_skinning`).

## Tip: the exported FBX keeps the mannequin bone names
- **Why:** re-importing `character_mannequin.fbx` into Blender gave 26 bones named `root`, `pelvis`, `spine_01`...
  and a mesh 1.8 m high. Which way it faces in the FBX file, and what Unreal does with it, is not run yet
  (Blender's default FBX import axes differ from our export axes, so a Blender re-import does not show it).
- **How to check:** `tests/test_rig_scripts.py` greps the FBX for the bone names.

## Part B: the Unreal half, timed (2026-11-10, UE 5.8 Linux editor, scratch project, n=1)

`GO/NO-GO: NO-GO` for a rigged character in the jam: in 43 min neither path played a stock animation correctly, and the fix is unknown, so use the no-rig fallback (separate parts on timelines) unless a re-run with the fix below passes under 60 min.

Scratch Third Person template copy outside the repo, never committed (Rule 7(h)). Rig steps ran headless
(`-run=pythonscript`, 4-7 s each): MCP has no IK tool, but `IKRigController`, `IKRetargeterController` and
`IKRetargetBatchOperation.run_batch_retarget` exist in 5.8 Python. Play tests: ONE open editor, mesh swapped live with
MCP `ObjectTools.set_properties` on `...BP_ThirdPersonCharacter_C:CharacterMesh0` (no recompile).
Path A = Rigify mesh + IK Retargeter. Path B = mannequin-named mesh on `SK_Mannequin`, no retarget.

| Step | Minutes | Cumulative | What happened |
|---|---|---|---|
| S0 | 0.8 | 0.8 | Scratch project copied from the template. The template ships no `IK_Mannequin`. |
| A2 | 3.3 | 4.1 | Import (legacy FBX). Broke: 1.8 cm tall, see below. |
| B2 | 0.0 | 4.1 | Path B import onto `SK_Mannequin`: accepted, no hierarchy error, 180 cm. Arms along Y (90 deg off Manny). |
| A4 | 1.1 | 5.1 | `IK_Mannequin` made headless: auto retarget definition works on Manny (29 chains, root pelvis). |
| A3 | 1.1 | 6.3 | `IK_Rigify`: auto definition fails on Rigify; 11 chains set by hand, named like Manny's. |
| A5 | 0.2 | 6.5 | Retargeter: default ops, FUZZY auto-map 11/11 first try. |
| A6 | 2.4 | 8.9 | Batch retarget of `ABP_Unarmed` + 21 anims in 0.7 s, after three fixes (below). |
| STALL | 30.7 | 39.6 | Editor hang: port 8010 still held by the last editor; then the GPU gate waited on RAM. Not rig work. |
| CTRL | 1.1 | 40.8 | Control: Quinn + `ABP_Unarmed` renders and stands. The test setup is fine. |
| B3 | 1.4 | 42.1 | Path B with `ABP_Unarmed`: character invisible. Rest pose (no anim): renders, 180 cm, turned 90 deg sideways. |
| A7 | 0.8 | 42.9 | Path A rest pose: correct. With its ABP: a thin line. One retargeted walk clip, no ABP: mesh gone, shadow far off. |

Rig work was ~12 min of tool time; the rest was the stall. Time is not the problem; the output is.

### What broke (full list: stage 02 `part-b-run-2026-11-10.md`)

- Blender FBX metres read as cm (1.8 cm import): `import_uniform_scale=100`, and re-import into a fresh folder.
- Auto retarget definition fails on Rigify (0 chains); FBX import renames bones `.` to `_`. Set chains by hand.
- Import saves the mesh but not its new Skeleton; batch retarget does not save the ABP. Save both by path.
- Port 8010 still held after closing an editor: next MCP never answers (~31 min lost). Check the port; keep ONE editor.
- **Not fixed:** retargeted clips send the path A mesh out of view (suspect root/pelvis scale vs the x100 import,
  UNTESTED; Rigify has no `root` bone); path B is accepted by `SK_Mannequin` but faces 90 deg off and goes invisible
  under `ABP_Unarmed`. The claim "mannequin skeleton accepted without retarget": accepted, yes; plays, no.

### Still UNTESTED

The fix for either path; the claimed "about an hour"; armpit weight fixes; a repeat run with the lessons applied (the
GO rule needs one). The next try: export the Blender FBX with unit scale applied (so no x100), add a `root` bone to
the Rigify export, re-run A2-A7 headless, play in one open editor. Under 60 min with a walking character = GO.
