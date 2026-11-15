---
tier: community
source: ~/Projects/superagent-sandbox/reports/stefan_3d_ai-megajam-lessons.md (lessons 1.4, 1.7, 1.14, 1.15, 2.12, 2.15, 2.23) and stages/02_build/references/look-kit/
updated: 2026-11-10
---

# Look kit: tileable surfaces, lighting presets, one stylised material

Status: **Part B ran 2026-11-10 (n=1).** Measured results live in the `tested` note `jam-look-kit-measured.md` (one tier per
file); the table below repeats the numbers. Everything else here is still a YouTube claim and **UNTESTED**.
Recipes: `stages/02_build/references/look-kit/tileable-textures.md`, `lighting-presets.md`, `stylised-material.md`. Seam tool: `scripts/seam_test.py`.

## Tip: check a tileable texture with a number, not a look
- **Why:** a seam shows only when the tile repeats. The wrap edge is what a 50 % offset puts in the middle and what UV x2 repeats, and a blotchy tile shows its repeat as spots.
- **How to check:** `python3 scripts/seam_test.py tile.png --json`. The tool itself is unit-tested on synthetic images only; the pass limits
  (seam ratio 1.5, blotch 30 levels on 0-255) are a guess until real generated tiles are measured.

## Tip: lighting is a named preset with a clipping and a focal-point check
- **Why:** one fixed preset plus one focal point is claimed to beat asking the agent to judge the look (UNTESTED).
- **How to check:** see the two checks in `stages/02_build/references/look-kit/lighting-presets.md`; the human picks from side-by-side frames.

## Tip: one master material, or toon bands plus outline, must hold 60 fps on the Legion
- **Why:** the look is only usable if the Legion keeps the 60 fps at 1080p budget.
- **How to check:** build once on primitives, package, measure on the Legion.

## Part B results (2026-11-10, n=1; detail in `jam-look-kit-measured.md`, log `stages/02_build/references/look-kit/part-b-run-2026-11-10.md`)
| Item | Result |
|---|---|
| Seam test, generated tiles | 1 tile only (wood, krea-2-turbo 1024 px): seam_ratio 1.76, FAIL; real grain seam seen by eye. Stone and ground NOT RUN (krea needs > 14 GB RAM; capped retries made no image) |
| Albedo-only variant | NOT RUN (UNTESTED) |
| Lighting presets: clipping and focal-point numbers | NOT RUN (UNTESTED) |
| Legion fps, default material | 79.8 median, 69.5 at 1 % low (1920x1080 output, 72.9 % screen percentage, VSync off, 400 primitives) |
| Legion fps, stylised material (`M_LookKitMaster`, recipe A) | 78.7 median, 71.7 at 1 % low (same scene); +0.17 ms per frame |
| Toon bands plus outline (recipe B) | NOT RUN (UNTESTED) |
| Native 1080p (100 % screen percentage) | NOT RUN (UNTESTED) |

GO/NO-GO: **GO** for recipe A (one master material plus instances) in the jam: it held 60+ fps on the Legion. Seam limits
stay uncalibrated: always eye-check the 50 % offset.

## Measured: krea-2-turbo needs more than 14 GB of system RAM
Measured fact (2026-11-10, this machine): krea-2-turbo needs **> 14G system RAM**. With `MemoryMax=10G` and `MemoryMax=14G`
caps the job sat at the cap, thrashed swap and made no image. An uncapped run got the scope (and the Claude app) killed by
systemd-oomd. So a tile run needs a solo slot.

## Stone and ground tiles: UNTESTED, run later in a solo slot
Not run in Part B (docs only here). Run them only when **all** hold: nothing else live (editor closed, no other GPU or
RAM-heavy job), `MemAvailable` well above 16G (`grep MemAvailable /proc/meminfo`), Lemonade unloaded (`lemonade unload`),
`gpu-preflight` says CLEAR. Restore Lemonade with `--ctx-size 32768` afterwards.
```
systemd-run --user --scope --unit=megajam-job-tiles -p MemoryMax=18G -p MemorySwapMax=2G -- nexus-image --model krea-2-turbo --width 1024 --height 1024 --seed 101 --json --out work/generated/look-kit-practice/stone_1.png "seamless tileable stone wall texture, flat top-down, even light, no shadow, no perspective, no vignette"
systemd-run --user --scope --unit=megajam-job-tiles -p MemoryMax=18G -p MemorySwapMax=2G -- nexus-image --model krea-2-turbo --width 1024 --height 1024 --seed 102 --json --out work/generated/look-kit-practice/ground_1.png "seamless tileable dirt ground texture, flat top-down, even light, no shadow, no perspective, no vignette"
python3 scripts/seam_test.py work/generated/look-kit-practice/stone_1.png work/generated/look-kit-practice/ground_1.png --json
```
Run the two image jobs one after the other, never together. Record the seam numbers in the table above and in
`jam-look-kit-measured.md`, and eye-check the 50 % offset of each.

## Part B command (the hub runs it; needs the GPU, editor and Legion slots)
1. `gpu-preflight`, then generate 3 tiles per surface with the spike in `tileable-textures.md` (own `systemd-run` scope).
2. `python3 scripts/seam_test.py work/generated/look-kit-practice/*.png --json` and record the numbers above.
3. Editor closed for step 1, then open it, build the material and presets on throwaway primitives, package, copy to the Legion, record fps.
Expected: seam ratios near 1.0 for good tiles, a clear pass/fail split from three tries; fps at or near 60 at 1080p (a guess).
