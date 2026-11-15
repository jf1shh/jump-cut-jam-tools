---
tier: tested
source: stages/02_build/references/look-kit/part-b-run-2026-11-10.md
updated: 2026-11-10
---

# Look kit, measured: seam test, master material, Legion fps (n=1)

Tested on 5.8.4; re-test on 5.9 before relying on it.

What we ran on 2026-11-10 (T-20261109-10 Part B). Practice content only, in the throwaway `megajam-mock12-kept` project
(Rule 7(h)); nothing here is reusable in the entry. Recipes: `stages/02_build/references/look-kit/`. Full log with wall times:
`stages/02_build/references/look-kit/part-b-run-2026-11-10.md`. One run each, so treat the numbers as n=1.

## Tip: the stylised master material costs almost nothing on the Legion
- **Why:** 400 primitives plus a floor, sky, fog, one directional light. Plain engine material: 79.8 fps median, 1 % low 69.5.
  `M_LookKitMaster` through three instances: 78.7 fps median, 1 % low 71.7 (frame time 12.53 ms vs 12.70 ms, +0.17 ms).
  Both stay above the 60 fps target. Render thread bound (about 12.5 ms), game thread about 2.4 ms.
- **How to check:** Development build, 1920x1080 fullscreen output, but the engine drew at 72.9 % (1400x788, the project's
  default screen percentage), VSync off, `t.MaxFPS 0`, CSV profiler `-csvCaptureFrames=3000`, first 300 frames dropped.
  Native 1080p (100 %) was **not** measured.

## Tip: a seam ratio above 1.5 was a real seam on the one tile we made
- **Why:** krea-2-turbo "seamless tileable wood planks" (1024 px, seed 104): `seam_ratio` 1.76, `seam_step` 118.8,
  `ref_step` 67.7, `blotch` 0.34, FAIL. A 50 % offset view showed the wood grain breaking along the horizontal wrap edge,
  so "seamless" in the prompt did not make it seamless and the test caught it. One tile only: the 1.5 limit is still not
  calibrated (no passing generated tile to compare against).
- **How to check:** `python3 scripts/seam_test.py tile.png --json`, then look at the 50 % offset by eye.

## Tip: krea-2-turbo needs more than 14 GB of RAM; do not run it beside a busy desktop
- **Why:** the first tile took about 2 min with no cap. The second run (uncapped, with many Claude sessions open) got the
  whole Claude app killed by systemd-oomd. Capped scopes at 10 GB and 14 GB both sat at the cap swapping and never made an image.
- **How to check:** `grep MemAvailable /proc/meminfo` well above 16 GB before a run; watch
  `systemctl --user show <scope> -p MemoryCurrent`.

## Tip: a map you open by URL must be in the cook list
- **Why:** with no `MapsToCook`, the package cooked only the default map and what it references. Launching
  `MockSlime.exe /Game/LookKitPractice/L_...` loaded nothing ("package to load does not exist") and fell back to the main level.
- **How to check:** add `+MapsToCook=(FilePath="/Game/...")` under `[/Script/UnrealEd.ProjectPackagingSettings]` in
  `DefaultGame.ini`; the cook count went from 565 to 572 packages.

## Tip: a content-only package writes its logs and CSVs under `Engine\Saved`, and the game runs as `UnrealGame.exe`
- **Why:** the `MockSlime.exe` stub starts `Engine\Binaries\Win64\UnrealGame.exe`; stopping `MockSlime*` leaves the game
  running, and `MockSlime\Saved` stays empty.
- **How to check:** look in `Packaged\Windows\Engine\Saved\Logs` and `...\Profiling\CSV`; stop `UnrealGame` too.

## Tip: the editor MCP has no arbitrary-Python tool; build material graphs headless
- **Why:** UE 5.8 AllToolsets has no console or Python exec. `UnrealEditor-Cmd <uproject> -unattended -nullrhi -nosound
  -ExecCmds="py /abs/script.py"` built the material, three instances and two 400-actor levels in about 20 s wall
  (script 1.3 s). Desaturation and Saturate inputs take the empty pin name `""`, not `"Input"`.
- **How to check:** print a marker at the top and the result at the end of the script; grep the log for both.
