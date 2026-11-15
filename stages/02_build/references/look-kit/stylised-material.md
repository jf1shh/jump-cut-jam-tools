# Look kit: one stylised material (recipe)

Status: **recipe, UNTESTED.** From lessons 1.15 and 2.12 (superagent report). Frame rate on the Legion is **not measured yet**; do not quote any
number until Part B writes one into `_config/reference/canon/jam-look-kit.md`. Throwaway practice content only (Rule 7(h)).

Pick **one** of the two. Default: A (one master material with parameters), because it also colour-matches AI props (lesson 2.12, UNTESTED).
Naming follows CLAUDE.md: `M_LookKitMaster`, instances `MI_LookKit_*`.

## A. Master material with a shared look (default)
Parameters (all scalar or vector, exposed so instances only change values):
- `BaseColorMap` (tileable albedo), `Tint`, `Desaturation`, `Brightness`, `Contrast`.
- `Roughness` and `Metallic` as flat scalars (lesson 1.14, UNTESTED), optional `EmissionMask` x `EmissionColor`.
- `NormalIntensity` (0 flattens the normal map).
- `SharedDetail` texture plus `DetailBlend` (one common detail texture blended over every prop).
- `UVScale` so the doubled-UV check is one value.

## B. Toon bands plus outline (alternative)
- Bands: quantise the lighting term into 3 steps (`floor(NdotL * 3) / 3`) multiplied into the base colour; add a rim term from the view angle.
- Outline: inverted hull. Duplicate the mesh, scale it up a little, flip normals, give it an unlit dark material. This doubles the draw calls
  for those meshes, so measure it.
- Pickup highlight: same hull trick with an emissive material.

## How to build it once (Part B, needs the editor slot)
Build with Python editor scripting or the editor MCP (one MCP caller at a time; see `_config/reference/canon/jam-blueprint-python-vs-mcp.md`). Apply to
primitives only (cube, plane, sphere): no jam props.

## Frame-rate measurement on the Legion (Part B)
Package the practice scene, copy to the Legion, run the existing capture helpers (`scripts/legion_record.py`, `scripts/legion_preflight.py`) and
read the fps from the recording or the engine `stat fps`. Record: Legion model, resolution (target 1080p), fps with the plain default material,
fps with the stylised material, scene counts. The target is 60 fps at 1080p (`stages/04_ship/references/capture-setup.md`). If the stylised material drops below it, the
recipe is out for the jam.
