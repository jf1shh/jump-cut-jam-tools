# Jam-day dress rehearsal, 2026-11-04 (tools only)

Ticket T-20261104-23. Rule 7(h): no gameplay, levels or art before 2026-11-11 21:00 PT, so this
rehearsal touched tooling only. No game content was made, nothing was saved into a level, nothing
was packaged, nothing was pushed to itch, no license was accepted and no sign-in was done.
Broken tooling was not fixed here; each needed fix is listed in the last column and in "Fixes needed".

Run on the CachyOS desktop, 2026-11-04 ~11:30 PT (19:30 UTC), plus read-only `ssh <device-host>`.

## Results

| # | Check | Command | Result | Fix needed |
|---|---|---|---|---|
| 1 | Super agent loop: branch from `master`, commit this doc, push own branch only, PR to `master` | `git worktree add -b claude/dress-rehearsal-2026-11-04 ../megajam-wt-dress-rehearsal origin/master`; Write of the claimed doc | FAIL (blocked). Branch made from `origin/master` b42eba0 in a separate worktree, so the owner's checkout (used by the IDE) stayed on `master`. The ticket guard then refused to write the claimed doc, both in that worktree and at the exact claimed path `~/Projects/megajam/stages/00_prep/output/dress-rehearsal-2026-11-04.md`, and refused `git worktree remove`. Refusals quoted below. No commit, push or PR happened. | Ticket guard: it does not see this ticket's claim (`stages/00_prep/output/dress-rehearsal-2026-11-04.md`), most likely because the session runs from `~/Projects/superagent-sandbox` and the guard reads another ticket's claims. Also accept the claimed path in a worker's own worktree of the same repo. Owner: remove leftover empty worktree `~/Projects/megajam-wt-dress-rehearsal` and local branch `claude/dress-rehearsal-2026-11-04` (still at b42eba0, never pushed), or reuse them. |
| 2a | GPU gate | `gpu-preflight` | FAIL first, then PASS. First run: `BLOCKED — something else owns this host.` (VRAM 15.86 GB used, GTT 9.09 GB, RAM avail 10.12 GB): Lemonade had Qwen3-Coder-30B loaded at ctx 65536, idle. After `lemonade unload`: `CLEAR — safe to start a large job.` | Jam-day runbook needs "`lemonade unload`, then `gpu-preflight`" as the first step before opening the editor. |
| 2b | UE 5.8.4 on scratch project | `systemd-run --user --scope ... -- Engine/Binaries/Linux/UnrealEditor ~/Projects/ue-mcp-verify/ue-mcp-verify.uproject -ModelContextProtocolPort=8010 -nosplash` | PASS. Engine `Build.version` = 5.8.4. Editor opened `~/Projects/ue-mcp-verify` only (current level `/Game/LastLight/L_LastLight`); no megajam game project was opened. | Port: see 2c. |
| 2c | Unreal MCP port | `ss -ltnp \| grep :8000`; `.mcp.json` in ue-mcp-verify | PASS with a catch. The plugin default is 8000, but port 8000 is held by the Nexus backend (uvicorn). `ue-mcp-verify/.mcp.json` expects 8010, yet nothing in the project config sets 8010, so the editor only serves 8010 when launched with `-ModelContextProtocolPort=8010`. | Pin the port in config (`ServerPortNumber=8010` under `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]`) for ue-mcp-verify and the jam project, or put the flag in every launch command. |
| 2d | MCP lists toolsets | `initialize` → `tools/list` → `list_toolsets` over HTTP at `127.0.0.1:8010/mcp` | PASS. Top-level tools: `list_toolsets`, `describe_toolset`, `call_tool`. `list_toolsets` returned 67 toolsets, including `editor_toolset.toolsets.actor.ActorTools` and `editor_toolset.toolsets.scene.SceneTools`. | None. |
| 2e | MCP spawn and delete one actor | `call_tool` SceneTools `add_to_scene_from_class` (`/Script/Engine.TargetPoint`, name `RehearsalProbe_20261104`) → ActorTools `get_label` → SceneTools `remove_from_scene` → `get_label` again | PASS. Spawned `PersistentLevel.TargetPoint_0` labelled `RehearsalProbe_20261104`; `remove_from_scene` returned `true`; the follow-up call said the actor "has been destroyed". | None. |
| 2f | Close editor, level not saved | `kill -TERM <editor pid>`; `find Content -newer <start marker> -name '*.umap'` | PASS. Editor exited within 60 s (wrapper exit code 144 after SIGTERM). No `.umap` changed after the run started. | None. |
| 2g | Restore Lemonade | `lemonade load Qwen3-Coder-30B-A3B-Instruct-GGUF --ctx-size 65536` | PASS. Restored to the exact state found (ctx 65536, `ready`). Note: the ticket and `~/.claude/CLAUDE.md` say "restore with --ctx-size 32768", but the box was running 65536 and `gpu-preflight`'s own restore hint also prints 65536. | Owner: pick one value and make `CLAUDE.md` and `gpu-preflight` agree. |
| 3a | `claude-loop` installed | `command -v claude-loop`; `ls -l` | PASS. `~/.local/bin/claude-loop` → `~/Projects/worktrees/workflow-tools-live/scripts/claude_loop.sh` (live worktree at 54d8ac2, workflow-tools PR 115). | None. |
| 3b | `claude-loop-revive.service` installed | `systemctl --user cat/status claude-loop-revive.service` | PASS (installed), with a note. Unit runs `%h/.local/bin/claude-loop-revive` as a oneshot at login. It was **already enabled** before this rehearsal (last ran 2026-11-03 14:12 PST, exit 0). This rehearsal did not enable, start or change it. | Owner: confirm "already enabled at boot" is what you want before the window. |
| 3c | What revive would run | `claude-loop-revive --dry-run` (changes nothing) | FAIL for the jam. Auto-start list (`~/.local/state/proj/wanted`) is `workflow`, `uc2-char-mod`, `myjobsearch`; **megajam is not on it**, so a reboot today revives nothing for megajam. Expected until `proj start megajam` runs in the window. The dry run also prints both a `--resume` of registry entry 00b5bfae for `workflow` and a fresh start for `workflow`, which may start two loops for one name (not verified; dry run only). | (a) Expected: `HANDOFF_MAX_RESTARTS=300 proj start megajam` at window open. (b) Check the double-start for `workflow` in `claude_loop_revive.sh`. |
| 3d | Restart cap survives a reboot | `grep HANDOFF_MAX_RESTARTS/FORWARD` in `claude_loop.sh`, `claude_loop_revive.sh`, `proj.sh` | FAIL. `claude_loop.sh` records only its arguments in `<state>/FORWARD`; `HANDOFF_MAX_RESTARTS` is an env var and is not recorded, and the revive unit does not set it. A loop revived after a reboot during the window would fall back to the default cap of 20, which the 2026-10-28 measurement says runs out in under a day. | workflow-tools: persist `HANDOFF_MAX_RESTARTS` in the loop state (or a flag that lands in FORWARD) and replay it on revive. |
| 4a | Legion: UE 5.8.4 at `C:\Dev\UE_5.8` | `ssh <device-host>` PowerShell: read `Engine\Build\Build.version`; `Test-Path` `UnrealEditor.exe`, `RunUAT.bat` | PASS. 5.8.4, same as the desktop. Editor exe and `RunUAT.bat` present. | None. |
| 4b | Legion: free disk | `Get-PSDrive C` | PASS. 804.5 GB free of 952.8 GB. | None. |
| 4c | Legion: butler present | `Get-Command butler`; `butler.exe -V` | PASS with a note. Not on `PATH` over ssh; found at `C:\Users\shino\butler\butler.exe`, v15.32.0 (2026-10-05). Login state not checked (no sign-in by rule). | Confirm `package-and-push.ps1` calls butler by full path or adds it to `PATH`. Owner-only: butler login + itch test push. |
| 5 | CyberNinja IDE answers, points at megajam | `pgrep -af cyberninja`; `curl http://127.0.0.1:47820/` | PASS. Server runs as `node ~/Projects/cyberninja-ide/server.js --workspace ~/Projects/megajam --port 47820`. `GET /` answers 401 with its "open the URL printed by the server" text, the expected reply without the token. `/api/status` not called (needs the IDE token). Not restarted. | None. |

## Guard refusals seen (quoted word for word)

1. Write in the separate worktree:

   > PreToolUse:Write hook error: ticket guard: ~/Projects/megajam-wt-dress-rehearsal/stages/00_prep/output/dress-rehearsal-2026-11-04.md is not in this ticket's claims; end your turn with outcome "blocked" and list it in need_files

2. Removing that worktree:

   > PreToolUse:Bash hook error: ticket guard: git worktree remove needs the owner. End your turn with outcome "question" and a question starting "ship: git worktree remove".

3. Write at the exact claimed path:

   > PreToolUse:Write hook error: ticket guard: ~/Projects/megajam/stages/00_prep/output/dress-rehearsal-2026-11-04.md is not in this ticket's claims; end your turn with outcome "blocked" and list it in need_files

4. A `cd <dir> && git status` while checking the scratch project (working as designed):

   > PreToolUse:Bash hook error: [command hook 3]: Blocked by guardrails.toml [no-cd-then-git]: `cd X && git ...` defeats permission matching; use `git -C /abs/path ...` instead.

## Fixes needed (not done here)

1. **Ticket guard misses this ticket's claim (1).** Highest blocker for the super agent loop: a
   worker can't write its own claimed file.
2. **Restart cap lost on revive (3d).** Highest risk for an unattended 4-day run.
3. **Unreal MCP port (2c).** Pin `ServerPortNumber=8010`, or add `-ModelContextProtocolPort=8010` to
   every editor launch, since Nexus holds 8000.
4. **GPU first step (2a).** Add `lemonade unload` → `gpu-preflight` to the jam-day start runbook.
5. **Lemonade ctx value (2g).** Make `~/.claude/CLAUDE.md` (32768) and `gpu-preflight` (65536) agree.
6. **Revive double-start for `workflow` (3c).** Check in `claude_loop_revive.sh` (dry run only).
7. **butler path on Legion (4c).** Confirm `package-and-push.ps1` finds butler outside `PATH`.

## Owner-only items

`HANDOFF_MAX_RESTARTS=300 proj start megajam` at window open; butler login and itch test push;
accept the UE EULA update if not done yet; remove or reuse the leftover worktree and local branch in row 1.
