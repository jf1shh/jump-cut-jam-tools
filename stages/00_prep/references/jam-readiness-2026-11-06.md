# Jam readiness check, 2026-11-06 (T-20261106-10)

Five days before the window opens (Wed 2026-11-11 21:00 PT). Tooling check only: no gameplay, levels,
art, config change, install or itch upload (Rule 7(h)). Run on the CachyOS desktop around 13:30 PT,
plus read-only `ssh <device-host>`. Fixes below are proposals for the owner.

Sources: `AGENTS.md`, `PLAN.md`, `stages/00_prep/output/dress-rehearsal-2026-11-04.md`, `stages/00_prep/references/mock-jam-5-checklist-dryrun.md`,
`stages/00_prep/references/jam-day-runbook.md` (PRs #80-#84).

## Results

Status: PASS, FAIL, NOT RUN (could not be run by this ticket; reason given), UNTESTED (never tested by anyone).

| # | Check | Status | Evidence | Fix |
|---|---|---|---|---|
| 1a | `gpu-preflight` gate | PASS after unload | First run: `BLOCKED` (VRAM 15.79 GB, GTT 5.84 GB; Lemonade model resident). `lemonade unload` then `gpu-preflight` printed `CLEAR — safe to start a large job.` | None. The runbook step 1 is right. |
| 1b | UE 5.8.4 binary on desktop | PASS | `~/Projects/UnrealEngine-5.8/Engine/Binaries/Linux/UnrealEditor` exists; `Build.version` MinorVersion 8, PatchVersion 4 = PLAN.md's 5.8.4. | None. |
| 1c | Editor / headless start works | NOT RUN | The ticket guard denied every launch shape I tried: `systemd-run ... -- UnrealEditor` ("command name is built by the shell"), and a direct `UnrealEditor ... -nullrhi` ("script outside checkout"). Last proven start: dress rehearsal 2026-11-04 (2b). | Owner or the hub session (no ticket guard) runs the launch line from `stages/00_prep/references/jam-day-runbook.md` section 2 once before Nov 11 and checks `ss -ltnp \| grep :8010`. Or allow-list the engine path for the launch in the ticket guard. |
| 1d | Lemonade restored | PASS | `lemonade load Qwen3-Coder-30B-A3B-Instruct-GGUF --ctx-size 32768` printed "Model loaded successfully!", server on port 13305. `gpu-preflight` now prints 32768 too, so the 32768 vs 65536 mismatch (rehearsal 2g) is gone. | None. Note: the box was at 65536 on 11-04 and is now 32768 as `CLAUDE.md` says. |
| 2a | Unreal MCP config | PASS (static) | `~/Projects/ue-mcp-verify/.mcp.json` points at `http://127.0.0.1:8010/mcp`, matching the runbook. | The jam project does not exist yet; its `.mcp.json` and `ServerPortNumber=8010` are created inside the window (runbook section 2). |
| 2b | MCP server starts, one read-only call answers | NOT RUN | Needs the editor (1c). Last proof: 2026-11-04, `list_toolsets` returned 67 toolsets; spawn and delete of one actor passed. | Same as 1c; then run `list_toolsets` over `127.0.0.1:8010/mcp`. |
| 2c | Editor-restart recovery, and cook with MCP plugin on | UNTESTED | `stages/00_prep/references/jam-day-runbook.md` marks both "UNTESTED"; no one has run them. | Run before Nov 11, not in the window. Steps are in the runbook ("Editor-restart recovery check" and the three cook checkboxes). |
| 3a | Legion reachable | PASS | `ssh <device-host>` answered; clock 2026-11-06 13:35 local. | None. |
| 3b | Same UE version on Legion | PASS | `C:\Dev\UE_5.8\Engine\Build\Build.version` = 5.8.4; `RunUAT.bat` and `UnrealEditor.exe` present. | None. |
| 3c | Disk on Legion | PASS | 801.8 GB free on C:. | None. |
| 3d | butler found and logged in | PASS | `C:\Users\shino\butler\butler.exe -V` = v15.32.0. `butler status jf1shh/megajam-pretest:win64` returned a table: build #2280252, `gate-test-1`, processed (so login is still valid today). User PATH contains `C:\Users\shino\butler`. | None. Re-check on Nov 11 morning. |
| 3e | `package-and-push.ps1` finds butler | PASS (read) | Script has `Resolve-Butler` (BUTLER_PATH, PATH, `%USERPROFILE%\butler`, `C:\Users\shino\butler`) and a `-CheckButler` switch. Rehearsal fix 7 is done. I did not run the script. | None. The real push target for the jam page does not exist yet (see 5a). |
| 4a | `claude-loop` installed | PASS | `~/.local/bin/claude-loop` links to `workflow-tools-live/scripts/claude_loop.sh`. | None. |
| 4b | `claude-loop-revive.service` installed | PASS | `~/.config/systemd/user/claude-loop-revive.service` (oneshot, `ExecStart=%h/.local/bin/claude-loop-revive`) and the `default.target.wants` link exist, so it is enabled. I did not start or change it. | None. |
| 4c | Restart cap survives a reboot (rehearsal 3d) | PASS (code read) | `claude_loop.sh` lines 304-308 now write every `HANDOFF_*` variable to `<state>/ENV`, and `claude_loop_revive.sh` line 120 replays it. So `HANDOFF_MAX_RESTARTS=300 proj start megajam` survives a revive. Not run end to end. | `stages/00_prep/references/jam-day-runbook.md` section 3 still says the cap is lost on revive. Update that note (owner/hub; not my claimed file). Keep "restart by hand after a reboot" as a safe habit anyway. |
| 4d | Megajam on the auto-start list | EXPECTED FAIL | `~/.local/state/proj/wanted` = `workflow`, `uc2-char-mod`, `myjobsearch`. `proj path megajam` resolves to `~/Projects/megajam`. `proj start megajam` marks it. | Nothing now. `HANDOFF_MAX_RESTARTS=300 proj start megajam` at window open, then `proj list` shows `megajam` busy. Not started here, per the ticket. |
| 4e | Revive dry run | PASS | `claude-loop-revive --dry-run` printed decisions only. The script code confirms `dry` skips every `rm` and start. It lists a `workflow` resume at the top; the second pass skips names already started, so the double-start worry (rehearsal 3c b) is handled in code (line 198). | None. |
| 5a | itch.io page and butler channel named | PARTIAL | Docs name only the private test page `jf1shh/megajam-pretest` channel `win64`. The real entry page and its butler target (`user/game:win64`) are not named anywhere. `win-plan.md` risk table wants a day-1 test upload so page and channel exist. | **Must fix:** owner creates the real itch.io project (draft) before Nov 11 and writes its `user/slug:channel` into `stages/00_prep/references/jam-day-runbook.md` section 3. Then the day-1 test upload is a plain `butler push`. |
| 5b | Under-1 GB zip plan | PASS | `package-and-push.ps1` has `-MaxBytes = 1GB`, names `TeamName_GameName.zip`, checks size before push. Past zips: 447 MiB (gate), 431.6 MB (mock 5). `win-plan.md` notes butler is the escape hatch above 1 GB. | **Open question:** the real `TeamName` and `GameName` are not written down. Pick the team name before Nov 15. |
| 5c | 30-60 s video capture tool | PARTIAL | Plan is OBS on the Legion; verified 2026-11-01 (1080p60, replay buffer 60 s, F9, 0 dropped frames). Desktop: `ffmpeg` has `x11grab`/`kmsgrab`, `spectacle` is installed, but the session is Wayland and there is no `wf-recorder`. My test capture was denied by the guard (an `rm` outside the work root in the same command), so it did not run. | If you want a desktop fallback: `sudo pacman -S wf-recorder` (owner; I install nothing). Otherwise rely on Legion OBS and add the Game Capture source once a build exists (`stages/04_ship/references/capture-setup.md`). |
| 6a | `pre-jam-tooling` tag | FAIL | `git tag -l` is empty. PLAN.md line "Tag `pre-jam-tooling`" is unchecked. | Last step before Nov 11 after final doc merges: `git tag pre-jam-tooling origin/master` then `git push origin pre-jam-tooling` (owner). |
| 6b | UE EULA update 22 accepted | UNKNOWN | Owner-only, needs the Epic account in a browser. Not checkable by an agent. | Owner accepts before Nov 11 (`stages/00_prep/references/jam-day-runbook.md` section 3). |
| 6c | MCP plugin list (Editor Toolsets) | UNTESTED | Runbook: `ue-mcp-verify` enables only `ModelingToolsEditorMode`, `ModelContextProtocol`, `AllToolsets`. Whether `AllToolsets` pulls in Editor Toolsets is unverified. | In the jam project, open Edit > Plugins and enable Editor Toolsets explicitly. |
| 6d | Ticket guard blocks a worker's own tooling | FAIL (this ticket) | It denied editor launch, `systemctl`, `rm` of a temp file, a redirect into the job temp dir, and reads of `workflow-tools-live`. The unattended lead agent will meet the same guard if it runs under it. | Owner: confirm the guard does **not** apply to the `proj start megajam` loop (it did not appear to apply to the 11-04 rehearsal's editor launches). Test with one launch from that loop before Nov 11. |
| 6e | Dress rehearsal blockers 1-7 | MOSTLY FIXED | 1 (claim guard): works for this ticket's file. 2 (cap): fixed, 4c. 3 (MCP port): flag in runbook. 4 (GPU first step): in runbook. 5 (ctx): fixed, 1d. 6 (double start): handled, 4e. 7 (butler path): fixed, 3e. | None. |

## Must fix before 11-11

1. **Create the real itch.io project and write its butler target into the runbook** (5a). Without it the day-1 test
   upload cannot happen. Owner step, in a browser; then add the line `user/game:win64` to the runbook.
2. **Run the editor once on the desktop and confirm MCP answers on 8010** (1c, 2b). I could not. Use the launch line in
   `stages/00_prep/references/jam-day-runbook.md` section 2, then `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8010/mcp`
   should print `405`. Then close the editor and run `lemonade load Qwen3-Coder-30B-A3B-Instruct-GGUF --ctx-size 32768`.
3. **Run the two untested checks** (2c): the editor-restart recovery test and one cook with the MCP plugin on. These decide
   whether the unattended loop recovers from a hung editor on its own.
4. **Accept UE EULA update 22** (6b).
5. **Tag `pre-jam-tooling`** as the last pre-jam edit (6a).
6. **Confirm the ticket guard does not block the jam loop's own editor launch** (6d). If it does, the loop cannot restart a
   crashed editor, which `AGENTS.md` promises it will do.
7. Decide the `TeamName_GameName` (5b). Needed by Sunday; cheap to settle now.

## Nice to have

- Update the runbook note that says the restart cap is lost on revive (4c); the code now saves it.
- Add `wf-recorder` or confirm a desktop capture path for quick checks (5c). OBS on the Legion already works.
- Run `package-and-push.ps1 -CheckButler` on the Legion once from a fresh ssh session to record the output (3e).
- Pin `ServerPortNumber=8010` in the jam project config on day 1 (runbook section 2).
- Re-check the Official Rules Box PDF on Nov 10 and Nov 15 morning (`AGENTS.md`).
- After the Lemonade restore, check `gpu-preflight` shows `BLOCKED` again so no one thinks the GPU is free by mistake.

## What this ticket did not do

Did not launch the editor (guard), did not run a desktop capture (guard), did not run `package-and-push.ps1`, did not push
to itch, did not start the unattended loop, changed no config, installed nothing. Lemonade was unloaded for the GPU check and
restored at ctx 32768 before the end of the run.
