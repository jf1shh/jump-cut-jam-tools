---
tier: epic
source: https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine
updated: 2026-11-06
---

# Lumen and Nanite settings for judges with weak hardware

Judges may use machines below the Lumen/Nanite baseline (Epic Linux requirements page: SM6, RX 6000 / RTX 2000 class and up). Notes are ours; the 5.8 specifics come from `_config/reference/knowledge-base.md`.

## Tip: offer a "Lumen Medium" path for low-end PCs and handhelds
- **Why:** UE 5.8 Lumen Medium is aimed at low-end PCs and handhelds. The knowledge base lists the
  scalability settings `sg.GlobalIlluminationQuality 1` and `sg.ReflectionQuality 1`.
- **How to check:** run the build on the Legion Go S and watch `stat unit`; the Legion doubles as our low-end test device.

## Tip: scalability groups are the quick dial
- **Why:** `sg.*` groups and the Engine Scalability Settings menu lower shadows, effects and post processing together.
- **How to check:** type `Scalability` in the console to see levels; set the default in `DefaultScalability.ini`.

## Tip: Nanite is for static meshes with compatible materials
- **Why:** Nanite saves triangle-count worry on static meshes. Materials need the Nanite usage flag (see
  `jam-import-and-materials`). Translucent and some other material types are limited; check the page.
- **How to check:** Static Mesh Editor > Nanite Support; the viewport's Nanite visualization view modes; no Nanite warnings in the log.

## Tip: upscale instead of rendering native
- **Why:** lowering `r.ScreenPercentage` with TSR gives a large GPU saving for a modest blur.
- **How to check:** change `r.ScreenPercentage` in the console while watching `stat gpu`.

## Tip: cheap shadows
- **Why:** Virtual Shadow Maps are costly; few dynamic lights and smaller light ranges help.
- **How to check:** `stat gpu` and `ProfileGPU` before and after.
