---
tier: tested
source: stages/02_build/references/procedural-props.md
updated: 2026-11-10
---

# Procedural props from Blender code (crate, barrel, fence)

## Tip: hard-surface props come from `scripts/procedural_props.py`, not an AI model
- **Why:** clean UVs, tiny triangle counts (crate 1532, barrel 1784, fence 1144), origin at the bottom centre,
  1 unit = 1 m, one material. No GPU needed.
- **How to check:** `blender -b -P scripts/procedural_props.py -- OUT_DIR --only crate`, then open the GLB.

## Tip: no hero mesh yet? Use the coded fallback character, never a single-colour primitive
- **Why:** mock jam 11 shipped the player as a grey pillar with a stick: no better mesh was ready and the AI 3D
  chain had made shredded props that day. A single-colour primitive (capsule, cube, pillar) as the player is a
  **playtest FAIL**. `character` is a coded person (head, torso, arms, legs, nose and toes facing +X), about
  570 tris, three flat colours, origin at the feet, no AI model and no GPU.
- **How to use:** `blender -b -P scripts/procedural_props.py -- OUT_DIR --only character --height 1.7 --skin '#E0AC85' --shirt '#D9382B' --trousers '#2B4A8C'`
  (all options optional; colours are `#RRGGBB`). Pick a shirt colour that contrasts with the level floor.
  Then `python3 scripts/asset_preview.py OUT_DIR/character.glb --ref human`. The `no_textures` warning is expected.
- **How to check:** shrink the preview to about 64 px tall; you should still see a head, shoulders, two arms and two
  legs. Swap in the hero mesh as soon as one passes `asset_preview`; keep the fallback until then.

## Tip: know the limits
- **Why:** base colour only (no normal, roughness, metal); wood is not tileable and looks soft up close; barrel
  hoops are 20-sided. Only checked in Blender renders, not yet in Unreal.
- **How to check:** import into the level once and look at it at play distance.

## Tip: preview renders use the CPU
- **Why:** `scripts/render_glb.py` runs Cycles on the CPU so it never fights Lemonade for the GPU.
- **How to check:** `blender -b -P scripts/render_glb.py -- in.glb out_prefix` writes three PNG views.

## Tip: do not commit generated GLB or PNG before the window opens
- **Why:** Rule 7(h), no art before 2026-11-12 00:00 ET. The script and docs are fine.
- **How to check:** `git status` before every commit; regenerate inside the window.

## Tip: keep a code-built fallback for every hero prop
- **Why:** in mock 11 the generated balloon and flag came out shredded and the pinwheel cleanup step failed; Blender-coded meshes replaced them. Smoke-test GLBs were not usable (`mock-jam-findings-11.md:20,100`; `mock-jam-findings-10.md:102`). Six of 17 props were still primitives at the end, and mock 12 ended with spheres and cones (`mock-jam-findings-12.md:80`).
- **How to check:** each hero prop has a primitive or script-built version in the level before you ask a generator for a better one. One world-space master material over the grey-box pieces comes first (see `jam-agent-playtest-gate`, judge tip).
