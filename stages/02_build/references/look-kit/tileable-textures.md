# Look kit: tileable surfaces (recipe)

Status: **recipe, UNTESTED.** Every claim below comes from YouTube lessons 1.4, 1.14 and 2.23 in the superagent report. Nothing here is
measured until the Part B run is written into `_config/reference/canon/jam-look-kit.md`. Practice tooling only (Rule 7(h)): generated test tiles are
throwaway, live under `work/generated/look-kit-practice/` (git-ignored scratch), and must not be reused in the entry.

## Order of choice
1. Free library first (Poly Haven, AmbientCG). Each download goes in the ledger (`_config/reference/canon/jam-sourced-assets-ledger.md`) with its licence
   line. Nothing is downloaded into the repo before the contest window.
2. Generate only when nothing fits. Local only: `krea-2-turbo` through Nexus (see `local-media-gen`). No cloud texture service
   (Patina, Chord hosted, Nano Banana) without reading its terms first and recording them like `_config/reference/canon/ai3d-options-and-licences.md`.

## Spike A: three tiles with krea-2-turbo
Run `gpu-preflight` first. One GPU job at a time; launch in its own scope (see AGENTS.md). Always pass `--model krea-2-turbo`.

Prompt shape (short beats long; UNTESTED):

```
seamless tileable <wood planks | stone wall | dirt ground> texture, flat top-down, even light, no shadow, no perspective, no vignette
```

Run (confirm the flags with `nexus-image --help` first; this shape is from `scripts/gen_asset.py`, which forwards `--model`):

```bash
mkdir -p work/generated/look-kit-practice
nexus-image --model krea-2-turbo --prompt "<prompt above>" --out work/generated/look-kit-practice/wood.png
```

Make 3 tries per surface. Retry instead of repairing (lesson 1.4, UNTESTED).

## The seam test
```bash
python3 scripts/seam_test.py work/generated/look-kit-practice/*.png --json
```

- **Seam (covers both the 50 % offset and the doubled UV scale):** the wrap edge is what a 50 % offset moves to the middle and what UV x2 puts at
  every join. The tool averages two strips of pixels each side of a boundary, takes the difference, and averages that along the edge in short
  windows, so pixel grain cancels but a step or a cut object stays. `seam_step` is the biggest such step at the wrap (0-255 levels);
  `ref_step` is the 99th percentile of the same step inside the tile; `seam_ratio` = `seam_step / max(ref_step, 4)`. The floor of 4 levels stops
  smooth, evenly lit tiles failing for a step nobody sees. Worst axis and worst colour channel count. Flat tile = 0.0.
- **Repeat blotches:** `blotch` is the spread of 4x4 block averages of luminance in 0-255 levels; a blotchy tile shows its repeat as spots.
- 16-bit and float greyscale maps are scaled to 0-255. One unreadable file is reported in the JSON as `error`; the others are still measured (exit 2).
- Result is a number per file. Exit 0 pass, 1 fail, 2 bad input.
- Defaults `--max-ratio 1.5`, floor 4, `--max-blotch 30` (levels on 0-255, absolute so dark tiles are not punished) are a **guess, UNTESTED**. Part B looks at the real tiles beside their numbers and sets
  the limits from that. A pass is not proof the tile looks good: also look at the doubled tile by eye (rule: visual check every step).

## Spike B: "albedo only, derive the other maps locally" (lesson 2.23, UNTESTED)
1. Prompt for albedo only: flat, no baked shadow, no highlights.
2. Roughness and metal: do not generate them. Use flat scalar values per material (lesson 1.14, UNTESTED), or a mid-grey 1K mask.
3. Normal: derive from the albedo luminance as a height map (Sobel, strength a parameter). Done locally with numpy/Pillow; no service.
   A script for this step is not written yet; if Part B shows the albedo-only look is worth it, add it then (a new script needs tests and a
   CANON row).
4. Check the result in the master material (see `stylised-material.md`) at 1x and 2x UV scale.

Fix for a failing seam (lesson 2.23, UNTESTED): offset 50 %, inpaint a cross-shaped mask. Prefer a retry; only try this if three retries fail.
