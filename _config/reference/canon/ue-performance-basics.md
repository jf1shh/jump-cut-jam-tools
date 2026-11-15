---
tier: epic
source: https://dev.epicgames.com/documentation/en-us/unreal-engine/performance-and-profiling-in-unreal-engine
updated: 2026-11-06
---

# Performance basics for a small jam game

## Tip: find the bottleneck before tuning
- **Why:** `stat unit` shows Game (CPU logic), Draw (render thread) and GPU times. Fix the biggest one only.
- **How to check:** open the console (` key) and type `stat unit`, then `stat fps`.

## Tip: drill into the GPU
- **Why:** `stat gpu` or `ProfileGPU` lists passes by cost (shadows, Lumen, post).
- **How to check:** compare before and after each change.

## Tip: avoid Tick where an event or timer works
- **Why:** a Tick on many actors adds up. Use timers, timelines, event dispatchers, or turn Tick off in class defaults.
- **How to check:** `stat game` and the actor's Tick settings.

## Tip: pool spawned objects
- **Why:** spawning and destroying many actors (projectiles, balloons) causes hitches.
- **How to check:** spawn 200 in a test level and watch frame time.

## Tip: first-run stutter is shader compile
- **Why:** PSO precaching covers most materials, but not everything. Epic suggests a loading screen that waits
  until `FShaderPipelineCache::NumPrecompilesRemaining()` reaches 0 and testing with `-clearPSODriverCache`.
- **How to check:** `stat PSOPrecache`; launch the packaged game cold on the Legion.

## Tip: texture memory
- **Why:** 4K textures everywhere blow the 1 GB zip and memory. Cap Max In-Game Size and use texture groups.
- **How to check:** Size Map and Statistics > Texture Stats.

## Tip: test on the weak device, not only the desktop
- **Why:** the RX 9070 XT hides problems.
- **How to check:** run the staged build on the Legion Go S every gate.
