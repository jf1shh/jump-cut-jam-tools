---
tier: tested
source: stages/00_prep/output/mock-jam-findings.md
updated: 2026-11-10
---

# Packaging a Windows build on the Legion Go S

Proven for a content-only (Blueprint) project: a 28 second cook, a 374.6 MB zip in the first mock jam.

## Tip: UE 5.9 (2026-11-10)
- **Why:** everything in this note was run on 5.8.x; no 5.9 package has been built here yet.
- **How to check:** before a 5.9 ship run, read the SDK, toolchain and Legion items in `jam-ue59-upgrade` (engine diff, not run).

## Tip: blank `EngineAssociation` in the `.uproject`
- **Why:** it held this desktop's Linux engine path, which broke `RunUAT` on Windows.
- **How to check:** `"EngineAssociation": ""` and pass the engine with `-EnginePath`.

## Tip: omit the `Modules` key entirely for a Blueprint-only project
- **Why:** an empty `"Modules": []` makes `BuildCookRun` treat the project as code-based, find no targets, and
  fail with "does not look like uproject file but no targets have been found".
- **How to check:** if the project ever gains a C++ module this fix no longer applies; re-test then.

## Tip: run the script directly over ssh, with ExecutionPolicy Bypass
- **Why:** nested `Start-Process` quoting is fragile and hides errors. The box blocks `.ps1` files by default.
- **How to check:** `powershell -NoProfile -ExecutionPolicy Bypass -File ...` (plain `powershell`, not `pwsh`).
  Errors then show up at once.

## Tip: use forward slashes for `scp` to the Legion
- **Why:** `<device-host>:C:/Dev/...` works; backslashes fail with "No such file".
- **How to check:** the copy succeeds and the file timestamp matches.

## Tip: butler needs a one-time owner login
- **Why:** it is an interactive OAuth step an agent must not do. Done 2026-11-02 for the pretest page.
- **How to check:** `ssh <device-host>`, then `butler status`.

## Tip: pre-flight checklist for build #1
- **Why:** a missing Game Default Map gives a black screen. Shipping builds have no console, so you need a quit path.
- **How to check:** set Game Default Map, list all cooked maps, run from the staging folder (not the editor),
  and confirm the prerequisites installer is staged. Record Development versus Shipping and why.

## Tip: never rename `UnrealGame.exe` for a Blueprint-only project
- **Why:** in a content-only package `Engine\Binaries\Win64\UnrealGame.exe` IS the game. The root `<Game>.exe` is a stub. Mock 10's first build renamed it as a decoy and failed with "CreateProcess returned 2" (`mock-jam-findings-10.md:71`). The packaging script now renames only when the project has a `Source` folder.
- **How to check:** launch the staged folder once on the Legion before any push.

## Tip: a cook that dies on `GameFeatureData` needs a `PrimaryAssetTypesToScan` entry
- **Why:** the AllToolsets plugin list gave an asset-manager error and the cook exited 25 (`mock-jam-findings-10.md:72`, 5.8). `templates/mock-project/DefaultGame.ini.tmpl` carries the entry. Not re-tested on 5.9.
- **How to check:** `Config/DefaultGame.ini` holds `+PrimaryAssetTypesToScan=(PrimaryAssetType="GameFeatureData",...)`; re-check the cook on 5.9.

## Tip: budget about 10 to 12 minutes per full ship
- **Why:** measured in mocks 11 and 12: sync 0.5 to 4.7 min, package 1.4 to 2.0, butler push 6.6 to 7.8 (full) or 0.6 (patch). A patch re-ship was about 2 min; the delta copy moved 140 MB, not 1 GB (`mock-jam-findings-11.md:80-81,88`; `mock-jam-findings-12.md:25-26`).
- **How to check:** read the summary line of `legion_ship.py`. Start the final package no later than T-60 min on Sunday.

## Tip: set `Force No Precomputed Lighting` on the grey-box level on day 1
- **Why:** the red "LIGHTING NEEDS TO BE REBUILT (15 unbuilt objects)" text was on every frame of mock 15's uncooked `-game` stand-in. World Settings `Force No Precomputed Lighting`, saved with no lighting build, removed it in runs 5 and 6 (`mock-jam-findings-15.md:54-62,184-188`). Mock 15 expects a Development package to show it too; that part was not tested here.
- **How to check:** a frame of the running game has no red engine text; do the same on the first packaged frame.

## Tip: the first 5.9 Win64 package works; it takes 1 h 25 min on a fresh source engine
- **Why:** mock 16 packaged on the Legion with `legion_ship.py PROJECT --engine 'C:\Dev\UE_5.9'`: BUILD SUCCESSFUL, BuildCookRun 5076 s, because a content-only project on a source engine compiles the Development game target with `-build` the first time. Kickoff to first zip was 2 h 13 min; build #2354706 reached `jf1shh/megajam-pretest:win64`. Source: `stages/00_prep/output/mock-jam-16-findings.md` (2026-11-10; branch `mock16-findings` merged to master 2026-11-11).
- **How to check:** package once early on day 1 so later packages are incremental; `legion_ship.py` reports each step's time.

## Tip: keep debug symbols out of the zip; the cap is 1,000,000,000 bytes
- **Why:** the Development `-build` stage held a 2,542 MB `.pdb`; the first zip was 1023.8 MiB, under the old 1 GiB gate but over a strict 1 GB. Without `*.pdb/*.debug/*.sym` it was 370.2 MiB. `package-and-push.ps1` now moves symbols to `Packaged\Symbols` and `MaxBytes` is 1,000,000,000 (fixes from `mock16-findings`, merged to master 2026-11-11). Source: `stages/00_prep/output/mock-jam-16-findings.md` (2026-11-10; branch `mock16-findings` merged to master 2026-11-11).
- **How to check:** list the zip for `.pdb` (none) and read its byte size before every push.

## Tip: a content-only 5.9 package stages `<Game>.exe`, not `UnrealGame.exe`
- **Why:** on the 5.9 source engine the stage had `<Game>\Binaries\Win64\<Game>.exe` and no `Engine\Binaries\Win64\UnrealGame.exe`; the old exe check refused the good build. `legion_ship.py` now accepts either (merged to master 2026-11-11). Source: `stages/00_prep/output/mock-jam-16-findings.md` (2026-11-10; branch `mock16-findings` merged to master 2026-11-11).
- **How to check:** `legion_ship.py` exe check PASS on the first 5.9 package.
