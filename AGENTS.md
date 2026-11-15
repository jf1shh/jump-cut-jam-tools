# 2026 Epic AI MegaJam — entry project

Goal: win (or place in) the 2026 Epic AI MegaJam. Track: **Unreal Engine** (not UEFN), engine **UE 5.9 MegaJam Preview** (5.9.0-preview-1), with **5.8.4 as the working fallback**.
Team: **solo** (+ AI agents). Target: top 3 in Best Overall, Unreal Engine, plus the **Glass Box**
modifier (best dev log).

- `_config/CANON.md`: searchable index of every doc and data file in this project, by topic — check
  here first when looking for something instead of guessing a path
- `scripts/ask_canon.sh "question"`: ask the curated jam canon (`_config/reference/canon/`, Nexus collection
  `megajam_canon`) for tips and UE 5.8 know-how; check each hit's `tier` and source before acting
- `stages/00_prep/references/win-plan.md`: the full plan (rules analysis, decisions, prep, agent setup, runbook, risks, sources)
- `PLAN.md`: the short schedule and gates
- `RULES.md`: rules digest with rule numbers from the Official Rules (current revision v3, created 2026-10-26; the v2 original of 2026-10-22 is superseded, see RULES.md)
- `_config/reference/knowledge-base.md`: sourced reference knowledge base (rules lookup, disqualification risks,
  Linux/packaging, Unreal MCP and agent setup, AI asset tools and licenses, past winners, dev log,
  must-watch videos, open questions). `_config/reference/research/` holds the underlying research notes.
- `_config/reference/research/external-strategies/`: outside strategy answers from ChatGPT, Grok, Gemini and a
  fresh Claude agent (2026-10-27), plus the prompts that produced them. Reviewed against the plan 2026-10-29; see
  `_config/reference/research/external-strategies-synthesis.md`.

## Fixed facts (from the Official Rules; re-check the Box PDF on Nov 10 and Nov 15 morning)

- Contest period: 2026-11-12 00:00 ET (Nov 11, 9:00 PM PT) to 2026-11-15 8:59 PM ET (5:59 PM PT). Rule 4.
- Theme reveal: kickoff livestream, 2026-11-11, 11 AM PT.
- Before the contest period, only AI tools, agent configs, MCP settings, prompt libraries and scripts
  may exist. No gameplay, levels or art. Epic may ask for this repo's version-control history. Rule 7(h).
- UE submission: a packaged build for Windows (playable on Win 10/11), macOS, Android or iOS; runs
  with no extra software; zip `TeamName_GameName.zip` under 1 GB (or butler); 30–60 s gameplay video at
  1920×1080 or higher; dev log link for Glass Box. Rules 1, 7, 10.
- A human submits the entry, never an agent. Rule 17.
- Winners notified on or about 2027-01-29; 72 hours to respond. Rule 14.

## Decisions already made

- **Unreal Engine over UEFN** (2026-10-27): develop on the CachyOS desktop (RX 9070 XT) with the UE 5.8
  Linux editor and Epic's Unreal MCP plugin, so the local Nexus asset tools stay on the same box.
  UEFN is Windows-only for the whole build.
- **Windows build box: Legion Go S** with Windows 11 installed. Unreal cannot package a Windows build
  from Linux. Same exact UE version on both machines. **Updated 2026-11-10 21:05 PT (read-only check):** the
  Legion has a 5.9 **source build** at `C:\Dev\UE_5.9` (scheduled task `UE59Build`; editor built, `END editor
  exit=0` at 21:00) beside 5.8.4 at `C:\Dev\UE_5.8`. The scripted helper-tools stage failed on a cmd quoting bug in
  `_build-logs\ue59_build.ps1` (line 25, fixed there), and the helper tools were rebuilt by hand. **Checked 2026-11-11
  16:55 PT:** `ShaderCompileWorker.exe`, `UnrealPak.exe` and `UnrealEditor.exe` are in `Engine\Binaries\Win64` (hub
  ssh), and the Legion Claude reports UBT and AutomationTool built too, so no tools rebuild is needed. Both machines
  report 5.9.0 (`Build.version`, branch UE5). *Superseded:*
  "no UE 5.9 install yet; the owner installs it via the Epic Launcher". `legion_ship.py` still probes only
  `C:\Dev\UE_5.8` / `C:\UE_5.8`, so always pass `--engine C:\Dev\UE_5.9`.
- **Engine switch (owner 2026-11-10): UE 5.9 Preview is the default, 5.8.4 the fallback.** Engine trees:
  `~/Projects/UnrealEngine-5.9` (a git worktree of `~/Projects/UnrealEngine-5.8`; never move, delete or
  modify either tree) and `~/Projects/UnrealEngine-5.8`. `scripts/launch-editor.sh PROJECT.uproject` starts
  5.9; `UE_VERSION=5.8 scripts/launch-editor.sh PROJECT.uproject` (or `--ue58`) starts 5.8.4. The script
  exports `SDL_VIDEODRIVER=x11` (the 5.9 editor fails SDL init on KDE Wayland otherwise). The 5.9 MCP server
  can take about 195 s to listen on :8010, so `launch-editor.sh` waits up to 300 s (`WAIT_TIMEOUT`) and exits 9 at once
  if the editor logs "HttpListener unable to bind" (leave a few seconds between stopping one editor and starting another).
  `scripts/mx.py` detects the server by probing `tools/list`
  (5.9: `describe_toolsets` / `describe_tools` and CodeBlock `execute_python`; 5.8.4: `describe_toolset`
  and a string). Live-smoked on 5.9 on 2026-11-10: toolsets, describe PythonScriptingTools, py, shot and step_shot
  (STEP_SHOT_OK). `force_save_level.py` failed its first live 5.9 run (mock 16: `mark_package_dirty` missing, nested `import`), then PASSED live after fixes (from `mock16-findings`, merged to master 2026-11-11). Mock 16 measured :8010 up in 14.2 s. Details: `_config/reference/canon/jam-ue59-upgrade.md`. A project made in one version is not opened in
  the other: copy it, do not convert it.
- **Both input methods are required (owner 2026-11-11).** Keyboard and mouse, tested on the desktop (editor
  play-in-editor runs), and the Legion Go S built-in gamepad (sticks, d-pad, face and shoulder buttons), tested on
  every Legion build. Each must fully play the game on its own: gameplay, menus, pause, restart and quit. Use Enhanced
  Input with keyboard/mouse and gamepad mappings from the first greybox (never key polling), and UI that works with
  the mouse and with gamepad focus. Gates in `stages/00_prep/references/jam-execution-plan.md` section 4.
- **Solo, aiming for Glass Box.** Each entry wins at most one main prize and one modifier (Rule 13).
- **Online, not in person** at Digital Jungle SF.
- **Not local-only** (owner 2026-11-07): any tool, service or asset the Official Rules allow is fair game.
  Cloud AI is terms-gated: each provider needs its key and `*_TERMS_REVIEWED` date in `~/.config/megajam.env`
  and is called only through its repo adapter. Banned regardless: Hunyuan3D (all versions), Qwen-Image 2.1,
  4x-UltraSharp, and raw curl/wget of store or asset pages. Store assets only if licensed and listed (Rule 15(c)).

## Working rules for agents

- One lead agent is the only Unreal MCP caller. Unreal MCP runs tool calls one at a time on the game
  thread. Other agents work in source files and asset tools.
- **Unreal questions: ladder, then hand-ask.** (1) Repo canon and `_config/reference/engine-reference/unreal/`; (2) grep the engine source at `~/Projects/UnrealEngine-5.9` (acf0265); (3) Epic doc pages; (4) only if still blocked, `python3 scripts/epic_ask.py add "question" --context "what you checked" --from NAME`, then work on something else and check `show Q-NNN` later. The owner asks Epic's Developer Assistant by hand and pastes the reply. **Never drive the Assistant website or the in-editor Unreal Assistant panel** (no browser automation, no Claude in Chrome, no anti-detect browsers, no curl): Epic's Supplemental Terms §2.c.ii-iii ban circumventing access controls and automated extraction. Never put secrets, third-party code or large private code in a question (short snippets of our own only). Every answer is an unverified hint (§2.a): verify against the engine source or in the editor first, and cite the Q-id in the commit or note that uses it. Queue note: Obsidian `Projects/megajam/Epic Assistant questions.md`.
- Generate original art and audio. Sourced assets (Fab etc.) are allowed if licensed and listed, but
  they are not scored. AI-generated content is not a sourced asset. Rule 15(c).
- Teen-rated content, English only, no third-party IP or trademarks except the Unreal Engine logo.
  Rules 7(i), 8, 15(d).
- **Licensed models only.** Never call `nexus-image` without `--model krea-2-turbo` (Nexus's own default,
  Qwen-Image 2.1, is non-commercial). Never use `ultrasharp` (CC BY-NC-SA) or Hunyuan3D (territory clause on outputs; replaced by TripoSplat); upscale with the default
  `realesrgan-x4plus`. Never use any non-commercial model for anything that could ship. `gen_asset.py`
  enforces this and pins `NEXUS_THREED_IMAGE_CHECKPOINT=krea-2-turbo` for the 3D stage; export the same
  variable in any shell where you call `nexus-3d` by hand. Rule 15(b).
- **Concept images may also come from GPT** (owner approved 2026-11-06, via the codex bridge) **and Grok**
  (xAI API, key from `XAI_API_KEY` only; use only after the owner has read xAI's live terms, which could
  not be fetched). They are AI-generated, not sourced, content (Rule 15(c)). Pick with
  `gen_asset.py --provider auto|local|gpt|grok`; `--providers-check` shows what is ready. The provider is
  recorded in the sidecar and `stages/02_build/output/asset-pipeline-log.csv`. Never run `codex login`; never ask for, print,
  store or commit a key. Details and licence evidence: `_config/reference/ai-providers.md`.
- **3D = Meshy (cloud, opt-in, speed-first) or local TripoSplat.** `gen_asset.py --3d-provider auto|local|meshy`: auto uses Meshy when configured, TripoSplat as fallback; a forced choice never falls back. Local form is `nexus-3d ... --model triposplat` (MIT, via Modly); `gen_asset.py` passes it. Plain `nexus-3d` defaults to Hunyuan and is denied, as are direct `modly` and `127.0.0.1:8765` calls. Needs the Nexus build that has `--model` (jf1shh/nexus PR 273). Output is albedo only (no PBR maps); ship no `.ply`/`.splat` side files.
- **ICM layout (owner 2026-11-11, strict).** Every new document goes into its ICM stage folder (`stages/NN_*/references` or `output/`) or `_config/`; add its row to `_config/CANON.md`. No new top-level doc folders. Map: `IDENTITY.md` (Layer 0), `CONTEXT.md` (Layer 1), `_config/` (shared rules and reference), `stages/00_prep` to `05_devlog` (contract in each `CONTEXT.md`).
- GPU freeze guard: if it SIGSTOPs an UnrealEditor it writes `~/.local/state/megajam/guard-STOPPED.txt` (why + what to do). Read it first; never `kill -CONT` the editor, kill it and relaunch headless (`-nullrhi`) or `-game -RenderOffScreen`.
- Contest guard: scripts/hooks/contest_guard.py runs before every Bash command in this repo (wired globally, scoped to this folder).
- **Display tests run off-screen (owner 2026-11-11 23:25, whole jam).** The owner's only monitor (5120x1440@60) is on the
  motherboard iGPU, which sits near 100% busy even at idle; the 9070 XT renders and every presented frame is copied to the
  iGPU. An uncapped visible PIE window tipped it over and froze KWin twice on night 1 (22:00 and 23:05). The cable stays on
  the iGPU so the 9070 XT VRAM stays free. So: never run PIE in a visible editor for stunt/screenshot tests. Use
  `UnrealEditor <uproject> /Game/Maps/L_Scene01 -game -RenderOffScreen -ResX=1280 -ResY=720 -unattended -nosplash -nosound -ExecCmds="t.MaxFPS 30;jc.ShotTour"`
  (`jc.ShotTour` in `Source/JumpCut/JCShotTour.cpp`: rolls, jumps to each stunt TOn+0.3, HighResShot, one log line per stunt).
  Any open editor stays at `t.MaxFPS 30`; re-apply it after every editor restart. Never suggest moving the monitor cable.
- **Legion testing goes through "Yo" (owner rule 2026-11-11 ~23:30).** All Legion tests and agent commands (launch a build,
  read logs, screenshots, checks) go through the Legion Claude session "Yo": `SendMessage` to "Yo" and ask it to reply to
  you by name. Security, firewall, driver and system-setting changes stay owner-only. Packaged start test:
  `JumpCut.exe -JCAutoStart -log` presses pad A through the real input path after 6 s and logs `JCAutoStart: result ... STARTED`
  (plus `JC input:` bind lines and the `JumpCut build:` line).
- One GPU workload at a time: batch generation while the editor is closed; run `gpu-preflight` first.
  Launch each GPU job (and the editor) from Claude's shell in its own scope, or it inherits the desktop
  app's 20 GB memory cap and stalls while loading Krea (2026-11-02):
  `systemd-run --user --scope --unit=megajam-job-$(date +%H%M%S) -p MemoryHigh=26G -p MemoryMax=28G -p MemorySwapMax=8G -- <cmd>`

## Jam-week autonomy (owner 2026-10-28, Nov 11–15 00:00 ET through 8:59 PM ET only)

Scoped exception to the global "agent opens PR, owner merges" rule, for the contest window only.
Outside that window the global rule applies as normal.

- **Merge/push:** commit and merge continuously onto an integration branch (`jam-integration`) without
  asking each time. Master/main (the branch Epic packages from) only gets fast-forwarded to it at the
  four scheduled gate builds in `PLAN.md`'s Phase 1 table (day 1–4) — flag it to the owner right before
  each fast-forward, don't ask permission first.
- **Editor recovery:** if the live Unreal Editor / MCP session hangs or crashes, restart it and resume
  without waiting for the owner. Before restarting, copy the project's `Saved/Logs/` and any
  `Saved/Crashes/<timestamp>/` folder out to a dated location (e.g.
  `stages/04_ship/output/crash-logs/<YYYY-MM-DDTHHMM>/`) so the crash can be diagnosed later without it being
  overwritten by the next run — this is a straight copy, not a commit of build output; see the log
  map below for what else to preserve.
- **Run schedule:** the lead agent runs unattended via `claude-loop` for the full window, including
  overnight, with `claude-loop-revive.service` keeping it alive through reboots. Before starting it for
  the window, raise its restart budget for this run only — the default (`HANDOFF_MAX_RESTARTS=20`) was
  measured burning ~1 restart/hour on 2026-10-28, nowhere near enough for 4 unattended days:
  `HANDOFF_MAX_RESTARTS=300 proj start megajam`. If the budget is ever exhausted anyway, an ntfy alert
  fires (workflow-tools PR #66) instead of the loop stopping silently.
- **Jam-start: new UE project.** When `~/Projects/megajam-game` is created (21:00 PT window open, `stages/04_ship/references/diversion.md`), give it its own `IDENTITY.md` + `CONTEXT.md` (Layer 0/1) from `_config/reference/templates/game-project-identity.md` and `game-project-context.md`. Leave Unreal's own folders (`Content/`, `Source/`, `Config/`) where they are.
- Everything else in this file still applies unchanged: one lead agent as the only Unreal MCP caller,
  one GPU workload at a time, Rule 7(h) (no gameplay/levels/art before the window opens), Rules 7(i)/8/15.

### Manual fallback runbook (if the unattended loop stalls during the window)

The loop can get stuck "busy" without making real progress — a session restarts cleanly but spins
without committing anything, which looks the same as healthy work from the outside unless you check.
A watchdog for this is tracked separately (`workflow-tools/integrations/pc-maint/watch/stall-watch`);
until it's installed and enabled, or if it doesn't catch something, use this by hand:

1. **Check status:** `proj list` — look at the `megajam` row. `busy` with a recent handoff timestamp
   is healthy. `idle` while the contest window is still open, or a handoff timestamp that's stopped
   advancing, is the stall signal.
2. **See what it's actually doing:** `claude logs <id> 2>&1 | tail -n 80` (the id from `proj list`).
   Repeated "Deliberating… (running SessionStart hooks…)" cycles with no new tool calls, or
   background-task-didn't-finish warnings on every restart, means it's spinning, not working.
3. **Force a clean restart:** `proj stop megajam --yes` then
   `HANDOFF_MAX_RESTARTS=300 proj start megajam`. This is the same restart-budget value used to
   start the window-long run in the first place — keep it, don't drop back to the default.
4. **If restart is refused because of a dead session's worktree state** (uncommitted or unpushed
   changes blocking `claude rm`): commit what's there first; if `claude rm` then refuses again over
   unpushed commits with no remote to push to, use the exact `--discard-unpushed <sha>@<worktree-id>`
   command it prints — it names precisely what to pass. Only discard when the content has no value
   beyond unblocking the restart (true for jam-integration scratch work that hasn't been merged up
   yet; never discard anything already fast-forwarded into `jam-integration` or master).
5. **Re-check after restarting:** `proj list` again — confirm `busy` and a moving handoff timestamp
   before walking away again.
6. If none of this gets it unstuck, this is a session for the owner to drive directly rather than
   something to keep retrying automatically.

### Where every recovery-relevant log lives

One map, so a crash at 3 AM doesn't turn into a search:

| Crash shape | Look here |
| --- | --- |
| Loop won't start / spins on restart | `claude logs <id>`; `~/Projects/megajam/.handoff/loop-*/loop.log` |
| Loop exhausted its restart budget | ntfy alert (workflow-tools PR #66); same `loop.log` |
| Loop started fine but stopped progressing | `stall-watch`'s page (if enabled) includes session/cwd/staleness; `~/.local/state/stall-watch/runs.log` has every stall it's ever seen, deduped by stall, not by tick |
| Unreal Editor / MCP crashed | the dated copy made under `stages/04_ship/output/crash-logs/<timestamp>/` per the Editor recovery step above — don't rely on the project's own `Saved/Logs`/`Saved/Crashes`, those get overwritten by the next run |
| Need the last known-good state before any of the above | the most recent `.handoff/*/HANDOFF.md` (what `proj handoff megajam` prints) — written on every context-limit handoff, so it's always close to current even mid-crash |

## Standing instruction context

This repo is an explicit, dated exception to the owner's "all Unreal Engine work tabled" rule
(table set 2026-10-14; this exception 2026-10-27, jam duration only). That table rule still applies to
every other Unreal-adjacent project on this machine. Nothing from UC2, UT2004, uc2-pc or UTLegacy
goes into this repo. That would be both third-party IP (Rule 8) and pre-jam content (Rule 7(h)).

## Build ledger and nightly devlog (owner 2026-11-11 23:49)

- **Every build gets an entry in `stages/04_ship/output/build-ledger.md` when it is staged.** Fields: id (A, B, B2, B3, B4...), dv commit, time, what changed and why, ship command and flags (push or `--no-push`), where it went (desktop, Legion staged path, itch channel and butler version), every test with who ran it (desktop off-screen, Yo on the Legion, owner by hand), the result and key log lines, open issues.
- Append test results to the entry as they come in. Do not wait for the build to be "done".
- **The devlog draft is saved in the repo every night** under `stages/05_devlog/output/`, not only in `~/.local/state`. Commit it with the night log.
- **Devlogs need no owner approval (owner 2026-11-12 00:00, to the hub: "i dont need to approve the devlogs just proceed with them you have my permission").** Write, commit and post them as part of the normal flow. Jam progress only: no secrets, keys, tokens, private paths or personal data. Log each post (time, where, link) in the ledger or the devlog index.
- **Itch pushes overnight (owner 2026-11-11 23:58, to the hub; confirmed 00:0x "keep them").** Stage every build with `--no-push`. A build goes to the private test page `jf1shh/megajam-pretest:win64` only after a CLEAN pass by the Legion test session (auto-start, keyboard/mouse drive, S1-1 pass and crash both register, no crash or black screen before the results screen, no new errors in the game log) AND a `GO push <build>` line from the master control hub. Record each push (channel, butler version, patch size, time) in the ledger. The real entry page is a separate, owner-only step.

## The editor never appears on the owner's screen (owner 2026-11-12)

Launch it with `scripts/launch-editor.sh`, which now adds `-RenderOffScreen -unattended` (no window at all; MCP :8010 answers as normal, checked 2026-11-12). `EDITOR_WINDOW=1` opts out, and then the window must stay minimized and never be focused. Close any popup windows. If a relaunch says "HttpListener unable to bind", the old editor's sockets are still in TIME_WAIT: wait until `ss -tan | grep :8010` is empty, then relaunch.
