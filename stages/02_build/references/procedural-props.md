# Procedural props (Blender, no AI model)

`scripts/procedural_props.py` builds hard-surface props in code and exports GLB files. Written
2026-11-01 because TripoSplat splats come out puffy on hard-surface shapes
(see `stages/00_prep/output/triposplat-findings-2026-11-01.md`).

## Use

```bash
blender -b -P scripts/procedural_props.py -- OUT_DIR [--only crate|barrel|fence]
```

Tested on Blender 5.2.3. Writes `<prop>.glb` and a `<prop>_atlas.png` per prop into OUT_DIR.

## Props

| Prop | Tris | Size (m) | Parts |
|---|---|---|---|
| crate | 1532 | 0.81 x 0.81 x 0.83 | corner posts, planks with gaps, diagonal braces, nails, 4-plank lid, base |
| barrel | 1784 | 0.74 x 0.74 x 0.90 | 12 tapered staves, 4 metal hoops, recessed lids |
| fence | 1144 | 2.13 x 0.13 x 1.28 | 2 posts with caps, 2 rails, 10 pointed pickets, nails |

All: origin at bottom center, 1 unit = 1 m, one material, one UV map, embedded 1024 px base-color atlas.

## Limits

- Base color only. No normal, roughness or metal maps.
- Wood is not tileable (per-part random patches, about 427 px/m), soft up close.
- Barrel hoops are 20-sided and slightly faceted. Fence nails are on the front face only.
- Checked only in Blender renders, not in Unreal yet.

## Rule 7(h)

Do not commit generated GLB or PNG output before 2026-11-12 00:00 ET. The script and this doc are fine.
Regenerate inside the window.

## How the preview pictures are made

`scripts/render_glb.py` renders a GLB to three PNG views with Blender Cycles on the **CPU**
(24 samples), so it never touches the GPU and can run while Lemonade or other GPU work is up.

```bash
blender -b -P scripts/render_glb.py -- in.glb out_prefix   # writes out_prefix_a/_b/_c.png
```

The geometry and the wood texture are both built by code (`procedural_props.py`); no AI model and no GPU.
