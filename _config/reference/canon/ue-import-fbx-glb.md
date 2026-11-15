---
tier: epic
source: https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-content-pipeline
updated: 2026-11-06
---

# Importing FBX and GLB: scale, pivot, collision

Our notes from the Epic pipeline docs plus what our imports taught us; confirm option names in the import dialog.

## Tip: mind the units
- **Why:** Unreal uses centimetres; Blender and glTF use metres. A 1 m crate must arrive as 100 units, or you get a
  tiny or giant prop. Procedural props are built at 1 unit = 1 m.
- **How to check:** drop the mesh next to the mannequin (about 180 cm) and compare.

## Tip: apply transforms and put the origin at the base before export
- **Why:** unapplied scale or rotation arrives wrong, and a base-centred pivot makes placement easy.
- **How to check:** the Static Mesh Editor shows the pivot at the feet and Bounds match your sizes.

## Tip: set up collision on purpose
- **Why:** imported meshes may have none. Simple collision (box, sphere, convex) is cheap; complex collision uses
  the render mesh. FBX can carry `UCX_`, `UBX_` and `USP_` shapes named after the mesh.
- **How to check:** Static Mesh Editor > Collision menu; `Show > Collision` in the viewport; walk into it.

## Tip: flat grey after import means no material came in
- **Why:** our MCP-native import did this. Use `scripts/ue_import_asset.py` (Interchange path, PBR check on).
- **How to check:** see `jam-import-and-materials`.

## Tip: FBX export settings matter
- **Why:** default Blender FBX settings gave upside-down meshes in a video. Save a working export preset.
- **How to check:** the imported mesh stands upright at scale 1.

## Tip: keep names to the prefixes
- **Why:** `SM_`, `T_`, `M_` etc. keep the Content Browser and source control readable (`CLAUDE.md`).
- **How to check:** sort the folder by name.
