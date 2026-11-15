# TripoSplat end-to-end test findings (2026-11-01)

First real image-to-3D run through the MegaJam pipeline since `--model triposplat` landed
(megajam #70, nexus #273/#274). Nexus's tests mock Modly, so this was the first time the path ran
for real. Test asset: one wooden crate. All outputs were throwaway scratch (Rule 7(h)); nothing
generated is in this repo.

**Verdict:** TripoSplat works, but it is a poor fit for hard-surface props (crates, fences, frames,
planks). Use it for organic, volumetric set dressing; build hard-surface props in code (see
`stages/02_build/references/procedural-props.md`, and "Recommendation" below).

## What was run

```
export NEXUS_THREED_IMAGE_CHECKPOINT=krea-2-turbo
python3 -I scripts/gen_asset.py --name NAME --image PNG --out-dir DIR --log LOG.csv
```

The picture stage (krea-2-turbo) was fine. The 3D stage is where everything below happened.

## Findings

1. **Port clash.** Modly wants `127.0.0.1:8765`. On 2026-11-01 another session's web server
   (`python3 -m http.server 8765`) held it, so Modly never started and gen_asset got an HTTP 501.
   Workaround that does not touch the other process: `NEXUS_MODLY_PORT=8766` and
   `NEXUS_MODLY_URL=http://127.0.0.1:8766` (Nexus reads both: `scripts/services/modly.sh` and
   `modly_client.py`). Check `ss -ltn | grep 8765` before a run.
2. **Flaky mesh extraction (~50-60% of runs failed).** Error: `SplatToMesh produced no surface (empty
   splat / level off-histogram)` (`generator.py` `_reconstruct`). The splats are healthy (262144
   gaussians, no NaN, opacity mean ~0.83). Inside the live Modly process the density grid
   intermittently goes non-finite on ROCm (`vol max inf, occ 0`), so extraction returns None.
   Replaying the same gaussians outside Modly works on GPU and CPU, so it is nondeterministic ROCm
   numerics in `_splat_density`, not memory pressure and not the input picture. Root cause not
   isolated.
   - **Workaround (outside git, in the Modly extension):** if GPU extraction returns None, free the
     accelerator cache and retry on CPU. Saved as `_config/reference/patches/modly-triposplat-cpu-retry.diff`
     (apply to `~/Documents/Modly/extensions/triposplat/generator.py`). A failing run then costs ~200 s
     instead of 80-90 s. A reinstall or update of the extension drops the patch.
   - The "repair extraction" step also OOMs on the 16 GB card (12.4 GB peak). It is caught and harmless.
3. **Quality of the crate.** Raw output: thin torn shards and ribbons floating around the base and lid,
   a peeled-up lid, black patches, ragged crumpled planks. The `.high.glb` files are byte-identical
   to the raw Modly output, so the junk is in the extension, not Nexus's remesh/bake (which makes it
   a little worse by decimating thin sheets). Cause: the splat is thin shells with no volume, so
   planks, lids and rings come out as open sheets. Black patches are texels the baker never filled.

## Parameter results (same picture, random seed each, so rough)

| Change | Result |
|---|---|
| default (mesh_detail 9, smoothing Medium, steps default) | shards, torn lid, black patches |
| mesh_smoothing Strong | no structural change, more black holes |
| mesh_detail 8 | much worse, shredded |
| mesh_detail 10 | worst |
| steps 40 | best raw: fewer shards, sturdier lid (one seed) |

Keep mesh_detail 9 and smoothing Medium; steps 40 is a mild gain. Not tested in a controlled way:
num_gaussians, vivid_color Refined, other seeds, other input views. Seed variance is large.

## Cleanup script

`scripts/triposplat_cleanup_glb.py` (Blender headless, a few seconds):

```
blender -b -P scripts/triposplat_cleanup_glb.py -- in.glb out.glb \
  --open 16 --solid --thicken 0.03 --voxel 0.01 --clip 0.03 --bottom-pct 4 --target 12000
```

Stages: weld, drop small islands, face-graph opening (deletes ribbons), thicken shells, voxel remesh
into a solid closed mesh, clip ragged base, fill near-black texels from neighbours, decimate, smart-UV,
bake a 1024 albedo, export. `--spike` did not work (leave off); `--fill` makes stray flaps (off by
default). The clip is tuned for boxy props; use `--clip 0` for others.

Result on the crate: solid watertight ~12k verts / 22k faces, no floating ribbons, black patches
gone. Still: puffy lumpy planks (not crisp flat ones), a dark fringe along the bottom, a small dark
flap under one front edge in one view, baked-in dark shading, no PBR maps. Rated usable only as
background/secondary set dressing, not a hero asset. Owner's review of the first, uncleaned version
was "really bad".

## Recommendation for jam week

- **Hard-surface props (crates, fences, shelves, frames, doors):** build in code (Blender headless
  scripts, or Unreal procedural), with a generated texture. Do not use TripoSplat.
- **Organic props (rocks, sacks, barrels?, plants, statues, creatures):** TripoSplat is plausible;
  barrels and creatures are untested. Run `triposplat_cleanup_glb.py` on every output and look at 3-angle renders
  before importing.
- Budget about 4 minutes per asset (plus ~2 minutes when the CPU retry fires), and re-roll seeds:
  the result varies a lot.
- Everything stays original and licensed (MIT TripoSplat weights/code; see
  `stages/00_prep/references/pre-jam-declaration-2026-10-29.md`).

## Open items

- Isolate the ROCm non-finite density cause (or upstream the CPU-retry into Modly / a Nexus PR).
- Test one organic prop (barrel or rock) to confirm the fit claim.
- No real-run (non-mocked) check exists for the triposplat path in Nexus CI.
- The patch above is outside git; re-apply after any Modly reinstall.

## Barrel test (organic prop check), 2026-11-01

One run, prompt "old wooden barrel with iron hoops", krea-2-turbo picture then TripoSplat: 132 s total
(picture 56 s, 3D 76 s), first try, no failure. Judged by Blender renders.

- Good: the overall barrel shape, hoops and wood color read correctly from the picture.
- Bad: several holes in the side, torn dark patches, a ragged blocky top rim. The splat is still a thin
  shell, so round props are not clean either.
- Verdict: better than the crate but not shippable as a hero prop; usable only as distant background
  after the cleanup script, with holes filled. The scripted barrel in `stages/02_build/references/procedural-props.md` is cleaner.
- Not tested: other seeds, `num_gaussians`, `vivid_color`, rocks or other truly irregular shapes.
