---
tier: community
source: ~/.cache/superagent/research/ai-3d-asset-research.md
updated: 2026-11-06
---

# AI 3D generators: what exists and the licence catches

Our summary of the owner's 2026-11-06 research. Vendor and blog claims, not tested by us. Check licence pages the day you use one.

## Tip: TRELLIS.2 is the best open candidate, but it is a post-jam test
- **Why:** MIT code and weights. A community repo (`toastmanAu/trellis-2-rocm-comfyui`) reports it working on
  RDNA3 and one RDNA4 report, but needs patches, a manual rasterizer build and a pinned wrapper commit. Native ComfyUI
  nodes (v0.34+) add PBR, UV unwrap and remesh nodes, with no AMD statement. Output is dense and triangulated.
- **How to check:** only if 1-2 spare hours exist; compare one crate against the current pipeline.

## Tip: Hunyuan3D 2.1 has a territory clause
- **Why:** royalty-free, but the territory excludes the EU, UK and South Korea, outputs cannot train other AI
  models, and weights must not be distributed. Our own rule bans it in this repo anyway (`AGENTS.md`).
- **How to check:** read its LICENSE file, and use only `--model triposplat` for 3D here.

## Tip: cloud tools (Meshy, Tripo, Rodin) trade money for tidy meshes
- **Why:** about 1-3 minutes per asset with remesh and PBR. Free tiers are CC BY 4.0, so you must credit the vendor;
  paid tiers (about $20 a month) remove that. Rodin's terms conflict between sources.
- **How to check:** record the plan's licence text the day you buy, and add the credit line if on a free tier.

## Tip: kitbash and procedural beat AI for structure
- **Why:** walls, floors, pillars and crates from a licensed modular pack or our Blender scripts have clean UVs and
  collision. Use AI for tileable textures or trim sheets on top.
- **How to check:** Poly Haven is CC0; Fab packs tagged CreatedWithAI need the jam's rules read first.

## Tip: skip image-to-3D for characters in a 4-day jam
- **Why:** rigging and topology cost more time than they save.
- **How to check:** use sourced characters or keep characters simple.

## Tip: treat video rankings as marketing-adjacent
- **Why:** several videos use an affiliate-style aggregator or promote paid courses, and free-quota claims conflict.
  No video tested AMD or local TRELLIS.2.
- **How to check:** treat numbers as "video claim, unverified" until a vendor page confirms them.

## Also not allowed in this repo
- CUDA-only builds, `nvdiffrast` and `nvdiffrec` (non-commercial), Hunyuan weights, and multi-account tricks.
