---
tier: tested
source: stages/04_ship/references/legion-ship.md
updated: 2026-11-10
---

# Shipping through the Legion: preflight and safe resume

Lessons from T-20261108-20 (`scripts/legion_ship.py`), found by mock jam 11 and by the adversarial reviews.
Tested with a fake ssh, scp and butler only; not yet run on the real Legion.

## Tip: check the cheap things before the 12-minute package step
- **Why:** mock 11 lost 3 minutes to a wrong engine path and found a DNS failure only after packaging. Every one of these is a seconds-long probe: ssh answers, `<engine>\Engine\Build\BatchFiles\RunUAT.bat` exists on the Legion (without `--engine` it probes `C:\Dev\UE_5.8`, then `C:\UE_5.8`, and names both if neither exists; *Superseded (2026-11-10):* UE 5.9 is now the default engine and the Legion has a 5.9 source build, so always pass `--engine C:\Dev\UE_5.9`, because the probe list still has only the 5.8 paths), free disk, butler present, `api.itch.io` resolves where the push runs.
- **How to check:** `python3 scripts/legion_ship.py PROJECT --dry-run` runs the read-only probes for real and prints one `PREFLIGHT FAIL` line per problem.

## Tip: a Pi-hole block is a DNS failure, even though the lookup "works"
- **Why:** this network's Pi-hole answers a blocked name with `0.0.0.0` or `::`, or with its own LAN address when `BLOCKINGMODE=IP`. The name resolves, so a naive check passes and the push fails after packaging. Any private, loopback, link-local or unspecified answer counts as a sinkhole. Windows `nslookup` also prints a harmless "DNS request timed out" when its own server has no PTR record, so judge the answer after `Name:`, not that header.
- **How to check:** `nslookup api.itch.io` on the machine that pushes; the address must be public.

## Tip: leftover game processes on the Legion break the run
- **Why:** a running `UnrealGame.exe`, `<Game>.exe` or `<Game>-Win64-Shipping.exe` locks files in `Packaged\Windows` and fails the next package or playtest. Preflight fails on them; `--kill-leftovers` kills them, and only after every other check has passed, so a run that preflight refuses never closes someone's game.
- **How to check:** `tasklist /FO CSV /NH` over ssh.

## Tip: a rejected build is never resumable
- **Why:** package-and-push.ps1 can fail after RunUAT staged the build (zip over the 1 GB gate, NOTICE missing). That leaves a complete but rejected `Packaged\Windows`, and `--from-step 3` would push it. So a successful package writes `C:\Dev\_ship\<Project>.packaged-ok`, and sync and package delete it when they start. Resume at step 3+ refuses a stage without the marker.
- **How to check:** run a ship whose package fails, then `--from-step 3`: it must stop with "not marked as finished".

## Tip: a failed marker delete is a hard stop; keep a second record on the PC
- **Why:** if the remote `del` fails (ssh drop), the old marker survives and would vouch for a build the new run never finished. The run stops before packaging. Because the Legion's state is then unknown, the PC also keeps `<log-dir>/<Project>.packaged-state`, set to `invalid` before the remote marker is touched and `ok` after a good package; resume needs both.
- **How to check:** make the delete fail (fake ssh exit 255), then try `--from-step 3`: it must stop with "did not finish packaging cleanly".

## Tip: push from the PC, and a status-only resume needs nothing from the Legion
- **Why:** the Legion could not resolve `api.itch.io` in mock 11. The Legion now only packages; the PC fetches the stage and runs butler. `--from-step 5` then needs neither ssh nor the stage.
- **How to check:** `--from-step 5` with the Legion off should still print butler's status.

## Tip: the second ship copies only what changed
- **Why:** mock 11 copied the whole 1 GB stage to the PC every time. The fetch now keeps a manifest (path, size, sha256) of the last good copy in `<log-dir>/stage-<Project>.manifest.json`, copies only changed files, and deletes vanished ones. `--full` forces a whole copy; a missing or unreadable manifest also means a whole copy.
- **How to check:** ship twice with the same build (`--from-step 4` the second time): the second run prints "copied 0" and makes no scp fetch. Delete the manifest and it copies everything.

## Tip: no symlinks inside the jam project folder
- **Why:** mock 12 reported symlinks in the project tree breaking the staged copy: 37 failed files and a 17 minute hang (`mock-jam-findings-12.md:117`). A fix was listed as done in that mock's own plan; `scripts/legion_ship.py` shows no symlink handling here, so treat it as not fixed.
- **How to check:** `find PROJECT -type l` is empty before a ship run.

## Tip: a new exe path or engine shows the firewall prompt again
- **Why:** each new `UnrealGame.exe` path (new game name, the 5.9 tree) prompts once and spoils video frames. Only a human click clears it. See `jam-legion-capture-and-video-traps`.
- **How to check:** the owner clicks at the first Legion run with the new path; `legion_preflight.py` prints the command.

## Tip: butler cannot set the itch page text
- **Why:** `butler` pushes builds only; the page description is pasted by the owner (`mock-jam-findings-11.md:152`). The kit lives in `stages/04_ship/output/mock11-itch/`.
- **How to check:** a paste-ready `description.md` sits beside the build; no agent edits the page.

## Tip: a Legion engine installed with GitDependencies platform excludes cannot run UAT
- **Why:** mock 16's first package failed in 1.4 min: `error MSB3554 ... Could not find a part of the path '...\AutomationTool\IOS\Resources\GreenCheck.png'`. `_build-logs\ue59_build.ps1` line 20 ran GitDependencies with `--exclude=Mac --exclude=IOS --exclude=TVOS --exclude=Android ...`, which drops files UAT needs to build its script modules. With the hub's OK, 9 missing files under `Engine\Source\Programs\AutomationTool\IOS\` were copied from the desktop 5.9 tree (sha256 matched; revert list in the findings). The same excludes may break Android packaging. Source: `stages/00_prep/output/mock-jam-16-findings.md` (2026-11-10; branch `mock16-findings` merged to master 2026-11-11).
- **How to check:** after any fresh engine install, run one BuildCookRun before the jam; never install the jam engine with those excludes.

## Tip: a side session waiting on a long Legion job may not wake by itself
- **Why:** hub 81 saw the mock 16 side session sit idle about 1.5 h while a long Legion package ran (hub observation, 2026-11-10).
- **How to check:** wait on the job with `waitfor` or Monitor (it re-invokes the session), and have the hub check the session's state at each 15-minute check-in.
