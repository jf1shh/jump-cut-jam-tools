---
tier: epic
source: https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-exposure-in-unreal-engine
updated: 2026-11-06
---

# Lighting and exposure basics (UE 5.8)

Our short notes; verify option names in the editor.

## Tip: a small outdoor scene needs four lights/actors
- **Why:** Directional Light (sun), Sky Light, Sky Atmosphere, and Exponential Height Fog give a believable base
  with little work. A Sky Light with real-time capture also needs a Sky Atmosphere (see `jam-playtest-beats-graph-qa`).
- **How to check:** the level looks lit with no red warnings in the viewport.

## Tip: stop the brightness pumping with fixed exposure
- **Why:** auto exposure adapts over time, which makes previews and screenshots flicker. A video also advises
  turning it off in Project Settings (Rendering > Default Settings > Auto Exposure) with min and max brightness both set to 1.
- **How to check:** a Post Process Volume with Infinite Extent, Exposure Min and Max EV100 equal; the view stays steady
  when you look from dark to bright.

## Tip: tune the look with a Post Process Volume
- **Why:** one volume sets exposure, bloom, colour grade and Lumen options in one place.
- **How to check:** toggle the volume's Enabled flag and compare.

## Tip: Lumen needs light to bounce
- **Why:** indoor scenes with no sun or skylight leak go dark.
- **How to check:** add an emissive material or a rect light; use the viewport's Lumen visualization view modes to see what the lighting sees.

## Tip: bake nothing unless you must
- **Why:** with Lumen dynamic GI, lightmap UVs and baking are not needed for most jam scenes.
- **How to check:** Project Settings > Rendering > Global Illumination = Lumen.
