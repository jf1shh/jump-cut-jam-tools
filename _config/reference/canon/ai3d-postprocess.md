---
tier: community
source: ~/.cache/superagent/research/ai-3d-asset-research.md
updated: 2026-11-06
---

# Making AI meshes game-ready: the post-process steps

Distilled from the owner's research (articles and captions of 13 videos). Numbers are speaker claims. None is tested on our setup.

## Tip: plan a decimate or retopo step, always
- **Why:** hosted TRELLIS.2 and Hunyuan 3.1 Pro gave about 500K triangles, Meshy "low poly" still 322K. A
  comfortable prop size was about 6-12K triangles; one cloud model gave about 5K.
- **How to check:** Blender statistics overlay shows the triangle count. Set a budget before you generate.

## Tip: bake high-poly detail onto the low-poly mesh
- **Why:** decimation loses the AI colour. Blender Cycles "Selected to Active" bakes colour, normal or AO from the
  high mesh to the low one, free and without an add-on. A rushed unwrap causes bleeding.
- **How to check:** look for seams and bleed on a closeup render; fix seams and re-bake.

## Tip: texture-free look, AO into vertex colour
- **Why:** bake ambient occlusion into a vertex colour attribute, then tint with a Lerp in one UE master material.
  No AI texture seams. Export FBX with a saved preset (default settings gave upside-down meshes in one video).
- **How to check:** the mesh looks right in UE with only a colour parameter and the vertex colour node.

## Tip: order matters for texturing
- **Why:** generate untextured, retopo, then texture; baking onto a bad mesh wastes the texture.
- **How to check:** the face count is final before the texture step.

## Tip: write the concept image for 3D
- **Why:** clean results need a plain white background, centred, front view (and an exact back view for two-image
  input), neutral pose, no held items, open palms for characters, upscaled first. Sketches must be redrawn as full renders.
- **How to check:** the background removal step works with no halo.

## Tip: low resolution for drafts, high only for keepers
- **Why:** 512 took about 30-56 s and 1024 about 90 s in TRELLIS.2 reports; batches of cheap drafts let you pick.
- **How to check:** log time per asset in `stages/02_build/output/asset-pipeline-log.csv`.

## Tip: build roughness and metal maps yourself
- **Why:** AI roughness and metal maps were rarely usable, and baked lighting in an albedo breaks engine lighting.
- **How to check:** albedo has no baked shadows.
