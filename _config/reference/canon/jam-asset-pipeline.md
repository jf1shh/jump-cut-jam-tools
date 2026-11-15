---
tier: tested
source: stages/00_prep/output/mock-jam-findings.md
updated: 2026-11-06
---

# Our local asset pipeline: timing and licence guardrails

## Tip: budget 2-3 tries for the first image-to-3D call
- **Why:** after Modly sat idle, the first calls failed fast (12 s and 58 s, exit 1) and the third worked
  (95 s). A cold-start problem, not a real error. An image took about 151 s.
- **How to check:** `stages/02_build/output/asset-pipeline-log.csv` records every attempt; read the exit codes.

## Tip: free the GPU first, one workload at a time
- **Why:** Lemonade keeps a model in VRAM while idle and blocks the editor and generators.
- **How to check:** `lemonade unload`, then `gpu-preflight` must print CLEAR.

## Tip: only licensed models
- **Why:** Rule 15(b). Use `nexus-image --model krea-2-turbo`, upscale with the default `realesrgan-x4plus`,
  3D with `nexus-3d ... --model triposplat`. Never `ultrasharp` (non-commercial) or Hunyuan3D (territory clause).
- **How to check:** `scripts/gen_asset.py` enforces these and writes a provenance sidecar with model names and hashes.

## Tip: TripoSplat output is albedo only
- **Why:** no PBR maps, and splats come out puffy on hard-surface shapes (`stages/00_prep/output/triposplat-findings-2026-11-01.md`).
- **How to check:** look at the render; for crates and fences use the procedural props instead.

## Tip: launch GPU jobs in their own scope
- **Why:** a job inherits the desktop app's 20 GB cap and stalls loading Krea.
- **How to check:** start it with `systemd-run --user --scope ... -p MemoryMax=28G` as in `AGENTS.md`.
