# legion_ship.py: ship a build from the PC through the Legion

`scripts/legion_ship.py PROJECT` syncs a UE project to the Legion, packages it there, checks the
staged exe, pushes to itch and waits for itch to finish processing. The Legion only packages by
default; the push runs from the PC's `butler`.

```bash
python3 scripts/legion_ship.py ~/Projects/megajam/work/MockHelium            # full run
python3 scripts/legion_ship.py ~/Projects/megajam/work/MockHelium --dry-run  # checks everything, changes nothing
python3 scripts/legion_ship.py ~/Projects/megajam/work/MockHelium --from-step 3   # resume, no repackage
```

## Steps

| # | Name | What it does |
|---|---|---|
| 0 | preflight | Cheap checks (below). Fails in seconds, one line per problem. |
| 1 | sync | tar the project, scp it to the Legion, mirror it onto the previous copy (cook cache kept). |
| 2 | package | `package-and-push.ps1` on the Legion (no itch push). Output streams live and is logged. |
| 3 | check | Staged exe is sane: root `<Game>.exe` launcher exists; content-only keeps `UnrealGame.exe`, C++ has its game exe and a disabled decoy. A failure stops the run. |
| 4 | push | PC (default): tar+scp the staged build to the PC, then `butler push`. Legion (`--push-from legion`): ssh and run butler there. |
| 5 | status | `butler status` (same side as the push) until itch has processed the build. |

The playtest is not a step here. It lives in `visual_playtest.py` / `legion_remote_launch.ps1`.
Playtest must start the **root launcher** `<Package>\<Game>.exe`, never
`Engine\Binaries\Win64\UnrealGame.exe <Game>`: a content-only package reads the bare name as a missing
project path and stops on a "must contain DefaultEngine.ini" dialog (mock 11). Step 3 and preflight
(when resuming) both check that the launcher exists.

## Preflight

Runs before sync. Each failure prints `PREFLIGHT FAIL: <reason>` and the run stops with all reasons
on the `STOPPED:` line. It needs well under 30 seconds: every probe has a 15 s timeout, and if ssh is
down it stops after that one probe.

| Check | Fails when |
|---|---|
| ssh | `ssh <device-host> echo OK` does not answer |
| engine | `RunUAT.bat` is missing under `--engine`, or (no flag) under both `C:\Dev\UE_5.8` and `C:\UE_5.8` on the Legion (steps 1-2). Since 2026-11-10 UE 5.9 is the default engine: always pass `--engine C:\Dev\UE_5.9` (the probe list is unchanged) |
| disk | less than `--min-free-gb` (default 20) free on the Legion's `--remote-root`, and on the PC for the fetch |
| leftovers | `UnrealGame.exe`, `<Game>.exe` or `<Game>-Win64-Shipping.exe` is running on the Legion (steps 1-3). `--kill-leftovers` kills them (taskkill) and re-checks; without it the run fails. |
| butler | PC push: `--pc-butler` not found. Legion push: `--butler` path missing on the Legion. |
| itch DNS | PC push: the PC cannot resolve `api.itch.io`. Legion push: `nslookup api.itch.io` on the Legion fails. |
| stage | `--from-step 3` or later: `<Game>.exe` is not in the Legion's `Packaged\Windows` |

`--no-preflight` skips all of it.

## Resume with `--from-step N`

Earlier steps are skipped; preflight still runs for the steps that remain.

- `--from-step 2` repackage without resyncing
- `--from-step 3` re-check the staged build, then push (a failed push or DNS needs no repackage)
- `--from-step 4` push without re-checking
- `--from-step 5` only wait for itch processing

Steps 3-5 need the packaged build still on the Legion; preflight says so if it is gone. A stage only
counts if a package step finished OK: sync and package delete `_ship\<Project>.packaged-ok` when they
start, and a successful package writes it. A package that failed after staging (zip over the gate,
NOTICE missing) leaves a rejected build with no marker, so `--from-step 3+` refuses it; start at step 2.
The PC keeps a twin record, `<--log-dir>/<Project>.packaged-state`: set to `invalid` before the
Legion marker is touched and to `ok` after a successful package. A resume needs both, so a marker the
Legion failed to delete (ssh drop) is still not trusted. A resume from another PC has no record: start at step 2.
`--from-step 5` with the default PC push only runs butler on the PC and needs neither ssh nor the stage.
A DNS answer of `0.0.0.0`, `::` or `127.x` (a Pi-hole block) counts as a DNS failure.

## Push from the PC

Default `--push-from pc`: after the check, the Legion tars `Packaged\Windows`, the PC copies it to
`<--log-dir>/stage-<Project>/` and runs `butler push` and `butler status` locally.

The fetch is incremental. The Legion hashes the stage (path, size, sha256) and the PC keeps the manifest of
the last good fetch in `<--log-dir>/stage-<Project>.manifest.json`. The next run copies only new or changed
files and deletes files that are gone, so a second ship of an unchanged build copies nothing. `--full`
copies everything. A missing, unreadable or stale manifest, a deleted local copy, or no manifest from the
Legion also means a whole copy (so does any non-ASCII file name in the stage, which ssh can garble).
The manifest must be complete or it is not used: the Legion script stops on any hash error (exit 1) and
ends with a `#END|<count>` line taken from the directory listing; a non-zero exit, a missing marker, a
count that does not match the lines received, or any unreadable line means no manifest and a whole copy.
Ssh warnings on stderr are ignored. **This path (PowerShell hashing, exit codes, the end marker) was
tested with a fake ssh only and has not been run against the real Legion.**
If the preferred engine path does not answer, the run stops rather than falling back to the older path. The manifest is removed when a fetch starts and written only after the
copy checks out. This is because the Legion could not resolve `api.itch.io` in mock 11, after a 12-minute
package. `--push-from legion` is the old path. The target and butler login are the same either way:
`butler login` must have been done on the machine that pushes.

## Dry run

`--dry-run` prints every command and runs the read-only preflight probes for real (so a wrong engine
path on the Legion is found). It never syncs, packages, kills, fetches or pushes. With
`--kill-leftovers` it only says what it would kill. Exit code 1 if preflight fails.

## Options

`--engine` defaults to a probe on the Legion: `C:\Dev\UE_5.8` first, then `C:\UE_5.8`; if neither has
`Engine\Build\BatchFiles\RunUAT.bat` the run stops and names both. An explicit `--engine` is used as given
and never falls back. With `--no-preflight` there is no probe and `C:\Dev\UE_5.8` is used. *Note (2026-11-10):* UE 5.9 is now the default engine, so pass `--engine C:\Dev\UE_5.9` until the candidate list changes; both defaults above are 5.8-era.

`--host`, `--remote-root`, `--engine`, `--full`, `--team`, `--game-name`, `--target`, `--butler`, `--pc-butler`,
`--push-from pc|legion`, `--from-step N`, `--kill-leftovers`, `--no-preflight`, `--min-free-gb`,
`--status-interval`, `--status-timeout`, `--log-dir`. `python3 scripts/legion_ship.py -h` has the rest.

## Code boundaries

Stages are the functions in `legion_ship.py`: `preflight()`, `fetch_stage()`, and the step closures in
`ship()`. T-20261108-19 (detached driver with a done-file) wraps the whole `main()` run; it should call
`main(argv)` or `ship(ctx)` and not edit the stages.

## Tests

`python3 -m unittest tests.test_legion_ship` (a fake ssh, scp and butler; no network).
