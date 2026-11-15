---
tier: tested
source: stages/00_prep/references/jam-day-runbook.md
updated: 2026-11-10
---

# Start-of-session routine (our own rules)

Forum-sourced habits (cache wipe, prompt habits) are in `jam-linux-editor-rx9070xt` and `jam-mcp-forum-reports`.

## Tip: free the GPU before anything else
- **Why:** `gpu-preflight` reports BLOCKED while Lemonade holds a model (seen with 15.86 GB in VRAM).
- **How to check:** `lemonade unload`, then `gpu-preflight` prints CLEAR. Afterwards restore Lemonade with `--ctx-size 32768`, never 8192 (owner rule; `jam-execution-plan` ruling C3).

## Tip: launch the editor from the shell in its own scope with the MCP flags
- **Why:** memory cap and port rules, see `jam-mcp-port-and-logs`.
- **How to check:** `ss -ltnp | grep :8010` shows it.
- **Memory cap, two numbers on record (not ruled here):** `AGENTS.md` and the `launch-editor.sh` default are 26G/28G with 8G swap. Mock 14 and mock 16 used a 16G crash scope through `LAUNCH_SCOPE_CMD` because RAM is tight (`mock-jam-findings-14.md:22`; `asset-test-ue59-2026-11-10.md:43-44` ran under 28G). The hub should settle one number.

## Tip: only the lead agent calls Unreal MCP
- **Why:** MCP runs tool calls one at a time on the game thread. Others work in files and asset tools.
- **How to check:** `proj list` shows one busy `megajam` session.

## Rule: no asset generation until the grey-box loop is proven (UNTESTED claim, see `jam-grey-box-first`)
- **Why:** videos say the loop is proved in primitives first and one-shot "build the game" prompts fail. We have not measured it here.
- **How to check:** build with primitives only until it can be won, lost and restarted, then run
  `python3 ~/Projects/megajam/scripts/greybox_gate.py record --project "$UPROJECT" --won --lost --restarted`; it prints
  "grey-box loop proven at HH:MM". `$UPROJECT` is the path of the game's `.uproject`.
  The session is rooted in the game project, not in megajam, so always use the absolute path to the script.
  Before any image, 3D or audio generation run `python3 ~/Projects/megajam/scripts/greybox_gate.py check --project "$UPROJECT"`:
  only exit 0 means go; any other code (13, 2 without --project, a python error) means stop.
  The marker is tied to that project path, so a practice project's marker never opens the jam project, and it
  does not expire.
  Prompt library: `_config/reference/prompts/greybox/`.

## Tip: copy crash logs before restarting the editor
- **Why:** the next run overwrites `Saved/Logs` and `Saved/Crashes`.
- **How to check:** a dated folder exists under `stages/04_ship/output/crash-logs/`.

## Tip: `lemonade unload` is not permanent; re-run `gpu-preflight` before every heavy step
- **Why:** an inbox-sorter timer called the Lemonade chat endpoint every minute and reloaded the model (11 GB GTT) beside the 5.9 editor, though `gpu-preflight` had said CLEAR at 12:04. `worker-health` has no GPU-busy check either (`mock-jam-findings-15.md:198-206`).
- **How to check:** pause `obsidian-inbox-sorter.timer` for the window, then `gpu-preflight` before each editor or generation start.

## Tip: start the editor first, then the lead session; if tools are missing use `mx.py`
- **Why:** a session started before the editor never got the `unreal-mcp` tools (ECONNREFUSED, no retry). `mx.py` over plain HTTP still worked (`mock-jam-findings-12.md:51`).
- **How to check:** `.mcp.json` points at `http://127.0.0.1:8010/mcp`; if the tools are missing run `scripts/mx.py toolsets`, then restart the lead session.

## Tip: inside a worktree session use literal absolute paths and one command per call
- **Why:** the harness refused multi-line shell, heredocs, and `$HOME` or `$(date)` inside `systemd-run` as "too complex to verify" (`mock-jam-findings-10.md:12-19`). `pkill -f` matches its own shell (`mock-jam-findings-11.md:101`). Unquoted `$VAR` does not word-split in zsh (`mock-jam-findings-15.md:172`).
- **How to check:** write scripts with the Write tool, use `git -C PATH`, kill by PID, call a wrapper script or an array instead of `$M ...`.

## Tip: never end a turn while a job runs; wait with a timeout
- **Why:** a turn with no tool call ends the loop (`mock-jam-findings-10.md:44`). A turn that ended during an upload slept 19 min (`mock-jam-findings-12.md:38`).
- **How to check:** wait with `waitfor` or Monitor, with a timeout, in the same turn as the job start.

## Rule: the grey-box gate is a bot loop plus one real-key run on the package
- **Why:** bot-driven PIE loops hid a real-key bug in mock 15 (`mock-jam-findings-15.md:181-183`), and mock 12 had no packaged build for hours. Mock 11 had its first playable package after 2 h 57 min, mock 12 after 5 h 16 min, mock 10 after 11 h 38 min (`mock-scorecard.md:39-42`). The plan's night N1 only needs a pretest package that launches.
- **How to check:** package the grey-box the same night (N1) and run one real-key probe on it. Do not wait for build #1.

## Tip: freeze tooling and run the lead from a pinned copy
- **Why:** a hub fast-forward of the shared checkout changed the mock's scripts under it (PR 124 merged 10:45:10Z, a ship started 10:45:46Z; `mock-jam-findings-12.md:43,103`).
- **How to check:** no tooling merges to `master` after Wed 19:00 (`jam-execution-plan`); the lead runs from a pinned copy of `scripts/`.

## Tip: substep any Tick physics in a grey-box
- **Why:** mock 16's PIE ran near 30 fps and the magnet tunnelled through a plate; fixed 1/60 s substeps and a 0.05 s frame cap fixed it. A 60-line Python model of the same equations, run first, matched PIE to 0.1 s and reproduced the bug at dt 0.033. Source: `stages/00_prep/output/mock-jam-16-findings.md` (2026-11-10; branch `mock16-findings` merged to master 2026-11-11).
- **How to check:** run the feel model at dt 0.033 and 0.016; the outcome must not change.
