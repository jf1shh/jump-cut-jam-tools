---
tier: community
source: ~/.cache/superagent/research/ai-3d-asset-research.md
updated: 2026-11-06
---

# Acceptance checklist for an AI GLB or Blender MCP asset

The checks come from the research (a Claude plus Blender course video and articles); the idea is ours to apply.

## Tip: check the numbers, not the picture
- **Why:** a mesh can look right and still be 100x too large, rotated, or floating.
- **How to check:** all of these, ideally in a headless script
  (`blender -b --factory-startup --python check.py --python-exit-code 1`, which fails the run on error):
  - bounding box in metres sensible for the prop (1 Blender unit = 1 m; UE is 1 unit = 1 cm)
  - scale is (1,1,1) after applying transforms
  - origin at the base centre, so a prop at z=0 sits on the floor
  - triangle count within the budget
  - no non-manifold edges or flipped normals
  - simple collision planned (box or convex)

## Tip: thin, flag-like and spoked shapes: go straight to a coded mesh
- **Why:** in mock jam 11 the AI chain's cleanup step failed on a pinwheel, and the generated balloon and flag came
  out shredded. Flags, ribbons, pinwheels and fans are paper-thin or spoked, and the image-to-3D step turns them into
  broken shells. The session lost time before it replaced them with Blender-coded meshes by hand.
- **How to check:** do not send flag, ribbon, pinwheel or fan to the AI chain. Build them with
  `scripts/procedural_props.py` or by hand in Blender. `scripts/asset_chain.py` does this for you: it builds the coded
  prop when one exists, and otherwise stops with one line (`--force-ai` overrides).
- **If the AI chain was used anyway:** a failed cleanup step or a mesh that `scripts/asset_preview.py` rejects (broken
  shape, thin footprint, non-manifold edges, flat mesh) is retried at most `--max-tries` times (default 2). Then it stops and says what failed.
  `--fallback procedural` builds the coded prop of that name or kind instead and records in `provenance.json` and
  `stages/02_build/output/asset-pipeline-log.csv` that the shipped mesh is the coded fallback, not the AI one. The coded prop must be
  the asset's own head noun (`red_crate` gets the crate; `crate_lid` and `fence_flag` do not get a crate or fence).
- **Mixed queues:** `--expect-aspect` is one value for the whole run. A queue entry can carry `aspect: "1:4"` to
  override it for that asset only.

## Tip: do not trust a check that can pass by accident
- **Why:** one agent floor check hit the object's own collider and passed vacuously.
- **How to check:** break the asset on purpose once and confirm the check fails.

## Tip: know Blender 5.1 default primitive costs
- **Why:** cube 12 triangles, cylinder 124, UV sphere 960; a 12-segment 6-ring sphere is 120.
- **How to check:** use low-segment primitives when a budget is tight.

## Tip: Blender MCP is unauthenticated
- **Why:** the socket has no auth or encryption.
- **How to check:** keep it on localhost, save first, disable the add-on when idle, never open untrusted `.blend` files while it runs.
