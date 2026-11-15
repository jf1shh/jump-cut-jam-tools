---
tier: epic
source: https://dev.epicgames.com/documentation/en-us/unreal-engine/packaging-unreal-engine-projects
updated: 2026-11-06
---

# Packaging and cooking (UE 5.8)

Our own short notes. The setting names are in Project Settings > Packaging; confirm on the page before relying on a detail.

## Tip: set the default map and list your maps
- **Why:** a missing Game Default Map gives a black screen in the packaged game.
- **How to check:** Project Settings > Maps & Modes > Game Default Map; Packaging > List of Maps to Include.

## Tip: Development for jam builds, know the trade-off
- **Why:** the jam asks for a Development build per the itch page; Shipping has no console. Epic calls Shipping the release config.
- **How to check:** Platforms > Windows > Package Project, then pick the configuration. Write down which you chose.

## Tip: shrink the build early
- **Why:** a blank project is roughly 300 MB; the limit is 1 GB. Use pak files with compression, exclude editor
  content, disable unused plugins, cap texture size.
- **How to check:** Size Map in the Content Browser; look at the final zip size every gate build.

## Tip: cook from the command line for a repeatable script
- **Why:** the Project Launcher log prints the exact `RunUAT BuildCookRun` command (cook, build, stage, pak, archive).
  Copy it into a script.
- **How to check:** the script exits 0 and the staged folder runs by itself on a clean machine.

## Tip: Epic's page has no Linux-to-Windows route and no zip step
- **Why:** Windows builds need a Windows host; we build on the Legion and zip ourselves.
- **How to check:** see `jam-packaging-windows`.
