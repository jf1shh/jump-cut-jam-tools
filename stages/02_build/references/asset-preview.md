# Asset preview: look at every asset before it goes in the game

Owner rule (2026-11-08): **no asset is imported until an agent has looked at its preview sheet.**
Mock jam 10 placed placeholder shapes and nobody looked. `scripts/asset_preview.py` makes the look cheap.

## Run it

```bash
python3 scripts/asset_preview.py work/generated/<run>/<asset>          # one asset folder
python3 scripts/asset_preview.py work/generated/<run>                  # every asset folder under it
python3 scripts/asset_preview.py path/to/thing.glb --ref human         # one file, force the human reference
```

It prints one line per asset: the `preview.png` path, `ok` / `warn ...` / `ERROR ...`, the size in metres
and the triangle count. **Then Read the PNG** and judge it. The flags only catch the obvious; shape,
proportion and material look are your call.

Needs Blender (`$BLENDER`, `--blender`, or `blender` on PATH) and Pillow. Blender runs in background
mode with Cycles on the **CPU**, 16 samples, so it never touches the GPU and can run beside other
GPU work. About 1-2 s per asset on this box (budget: 60 s; each Blender call times out at 120 s).

## What it writes (beside the asset, or `--out DIR` for a single asset)

- `preview.png`: header (name, status, size, tris, flags), four orthographic views (front, side, back,
  3/4) on a neutral grey background with a scale reference, then the texture maps (albedo / normal / AO)
  as thumbnails. A missing texture shows as a red `MISSING` box.
- `preview.json`: `size_m`, `bounds_min_m`, `bounds_max_m`, `tris`, `verts`, `non_manifold_edges`,
  `materials` (with their texture names), `textures` (role, name, source, size, exists), `ref`, `flags`,
  `ok` (false when any flag is an error), `seconds`.

Which model is previewed for an asset folder: `game/*.glb`, then `game/*.fbx`, then the raw `*.glb`,
and the `.high.` file last. Pass a model file to pick one yourself.

A flat folder of different models (`props/crate.glb`, `props/barrel.glb`) gets one sheet per model,
named `<name>_preview.png` / `<name>_preview.json`, so none is skipped or overwritten. The same goes for
a `game/` folder shared by several assets. If you pass several files that would write the same
`preview.png`, each gets a name from its file name (`raw_glb_preview.png`, `raw_high_glb_preview.png`).
The printed line always shows the real path.

**`--expect-aspect A:B[:tol]`** fails an asset whose footprint width:height is off, and also one whose
footprint is thin (short side under `--min-depth`, default 0.25, of the long side): that catches flat
image-to-3D reliefs. A prop that is meant to be thin (door, sign, fence) passes with `--allow-thin`
(or `--min-depth 0`).

**Collision hulls are ignored.** Meshes named `UCX_`, `UBX_`, `USP_` or `UCP_` (Unreal collision, present
in the game FBX) are removed before measuring and rendering, so size, tris and the picture show only
the visible asset. Their names are listed in `preview.json` under `collision_meshes`. Maps stored beside the model
(`raw.albedo.png`, `raw.normal.png`, `raw.ao.png`, or `<model>.<role>.png`) are shown too when the
model does not embed that role itself.

## Scale reference

- `auto` (default): a 1.8 m human silhouette (orange) when the asset's largest side is 1.2 m or more;
  a 1 m cube (blue) from 0.4 m; a 10 cm cube below that. The header says which one.
- `--ref human` or `--ref cube` forces it (human is always 1.8 m, cube always 1 m).
- The reference stands to the right of the asset in front/back/side, so it never hides it.

## Flags

| Code | Level | Meaning |
| --- | --- | --- |
| `empty_mesh` | error | no mesh objects, or 0 triangles |
| `zero_size` | error | bounding box is a point |
| `scale_too_big` | error | largest side over 20 m (usually a units bug) |
| `scale_too_small` | error | largest side under 2 cm |
| `missing_textures` | error | a texture node points at a file or data that is not there |
| `flat_mesh` | warning | one axis has zero thickness |
| `non_manifold` | warning | open or broken edges, counted after merging seam vertices (1e-5 m) |
| `no_material` | warning | mesh has no material |
| `no_textures` | warning | no maps used by the material and none beside the model |

Non-manifold is only a warning: AI-generated meshes often have a few and still look fine. A large count
(hundreds, as on the smoke barrel) is worth a look at the views.

Exit code: 0 when no asset has an error flag, 1 if one does or a render fails, 2 for bad usage.

## What to look for when you Read the sheet

- Is it the thing the brief asked for, or a blob, a half shape, floating bits? (The smoke-20261107
  balloon is a half bowl with a loose string; the barrel is shreds. Both said only `non_manifold`.)
- Is the size sensible next to the reference?
- Do the textures match the surface, with no black holes, wrong colours or stretched UVs?
- If it fails the look, regenerate or fix it before import. Do not import and hope.

## Tests

`python3 -m unittest tests.test_asset_preview`: flag logic, reference choice and file discovery are pure
Python. The render test builds a 1 m cube GLB with Blender and runs the whole tool on it; without
Blender or Pillow it is skipped with a message.
