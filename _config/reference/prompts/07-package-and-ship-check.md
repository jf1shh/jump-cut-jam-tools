# 07 Package and Legion ship check

**Purpose:** package the game on the Legion Go S, check the staged exe, push to the private test page, and prove the
result with the agent playtest. Windows packages only come from the Legion; Unreal cannot package Windows from Linux.
**When:** at each scheduled package (jam-night runbook: Package A and B; the daily gate builds and the 07:30 night
package in `jam-execution-plan.md`).
**Hub sends to:** the lead. VERIFIED needs the editor, so this job stays with the lead; helpers do not run it. The owner does the Windows Firewall prompt and any push to the real itch page.
**Model:** Opus for the lead; Haiku to digest the long package log.

**Inputs**

| Placeholder | Fill with |
|---|---|
| `{HOUSE_RULES}` | the block from `00-house-rules.md` |
| `{uproject}` | absolute path to the `.uproject` in `{game_dir}` |
| `{package_label}` | e.g. `Package B` or `gate1-thu` |
| `{target_note}` | "default pretest page" (every night) or the owner's named target at a flagged gate |

## Prompt

```text
{HOUSE_RULES}

Package {package_label} for {uproject}. Target: {target_note}.

Preconditions (all must hold; if one fails, stop and report, do not package):
1. python3 ~/Projects/megajam/scripts/jam_clock.py check prints exit 0 or 10 (not 11 or 12 unless the owner said so).
2. The determinism test is green and the tree is committed.
3. python3 ~/Projects/megajam/scripts/force_save_level.py prints VERIFIED for the shipped level.
4. python3 ~/Projects/megajam/scripts/ue_verify_level.py output goes through scripts/presubmit_gate.py: exit 0.
5. grep Source/ for on-screen debug calls (PrintString, AddOnScreenDebugMessage, GEngine->AddOnScreenDebugMessage): none.
6. python3 ~/Projects/megajam/scripts/legion_preflight.py: exit 0 (ssh, OBS and its websocket, firewall rule for
   the exe, stale tasks, console session); engine path and butler are checked by legion_ship.py itself. It reads only; the firewall prompt is the owner's.
7. No generation job is running (the sync reads the project). One package per night.

Run: python3 ~/Projects/megajam/scripts/legion_ship.py {uproject} --engine C:\Dev\UE_5.9
(the script only probes 5.8 paths on its own, so always pass --engine). No --target means the private pretest page. Never
pass another --target unless the owner named it in this prompt. Add --dry-run first if anything looks off. Watch it with
waitfor or Monitor, with a timeout; read the tee'd log only through a digest.
Steps: 1 sync, 2 package, 3 exe check (root <Game>.exe launcher; a C++ project has its own game exe), 4 push, 5 butler
status until itch has processed it. On failure, resume with --from-step N; do not start over unless step 1 failed.

After it passes: run 05-agent-playtest-visual-check.md on the staged build (the root launcher, never the decoy exe),
then jam_backup.sh gate {package_label}. Report the summary line with minutes per step and the itch build id.
You never submit the entry and never push to the real page unless the owner told you to in this prompt.
```

## Done when

`legion_ship.py` exits 0 with step 5 processed, the agent playtest gate passed or its failures are listed with frames,
and the backup ran.

## Reply format

House format, plus `Package:` (label, commit sha, itch target and build id), `Minutes:` (per step), `Playtest:`
(PASS or FAIL with the report path), `Owner needs to:` (firewall prompt, pad test, anything by hand).
