# Tooling survey for the MegaJam window (T-20261108-15)

Written Sun 2026-11-08. Window opens Wed 2026-11-11 21:00 PT (Rule 4). Docs only: no installs, no editor
runs, nothing launched. Every "buys" figure is an estimate, marked as such.

**Read first, so nothing here repeats it:** `stages/00_prep/references/jam-day-runbook.md`, `stages/00_prep/references/mock-jams-10-14-plan.md`,
`stages/00_prep/output/mock-jam-findings-10.md`, `stages/03_playtest/references/playtest-gate.md`, `stages/04_ship/references/capture-setup.md`, `_config/reference/ai-providers.md`,
`stages/00_prep/references/jam-readiness-2026-11-06.md`, `_config/reference/knowledge-base.md` (packaging, butler, itch checklist, Fab).
Already built and not re-proposed: step_shot, asset_preview, visual_playtest (bursts, contact sheets),
agent_playtest, force_save_level, legion_ship / package-and-push, legion_record, OBS 1080p60 profile,
gpu-preflight, editor_watchdog, the Meshy/TripoSplat/GPT/Grok provider chain.

**Line numbers.** Every `file:line` below was re-checked against master d5798a1 on 2026-11-08 (after review); they drift, so search the quoted text if one is off.

**Trust labels.** VERIFIED = I fetched the primary page this session (URL given). UNVERIFIED = a claim I
could not confirm from a primary page; do not rely on it. Epic's doc pages returned only part of their
text to my fetcher, so several details below are marked UNVERIFIED on purpose.

## Top 5 (ranked by failure prevented per hour of effort, before Wed 21:00 PT)

| # | Ticket title | Why it ranks here | Effort |
|---|---|---|---|
| 1 | `T: video_gate.py - ffprobe size/fps/length + blackdetect/freezedetect on the final mp4` | The video is a hard rule (30-60 s, 1920x1080 or higher). Today only duration is checked (`legion_record.py:193`, `visual_playtest.py:762`). A 1200p/short/black-tail clip is a disqualification-class miss and the check takes seconds. | S |
| 2 | `T: obs_ctl.py - persistent OBS, SaveReplayBuffer + ReplayBufferSaved path + GetStats, 60 s ready poll` | Mock 10 lost hours to OBS websocket start races, stray dialogs and a clip full of popups. A wrapper that waits for the socket and reads the saved path from the event removes the guessing. | M |
| 3 | `T: submission_sheet.md - paste-ready form answers, URLs, AI declaration, TeamName_GameName decided` | The form fields are unpublished, so the only prep is a sheet with every likely answer. Jam-readiness 5a/5b are still open (real itch page, team name). Saves a panicked last hour and prevents a wrong-name zip. | S |
| 4 | `T: legion_link_budget - time ssh+scp+butler for a 450 MB zip over Wi-Fi, sleep-off + keepalive in legion_preflight` | The Legion is the only packaging box and mock 10 saw `ssh <device-host>` time out for minutes. Know the real minutes now, and stop the box sleeping. | S-M |
| 5 | `T: gauntlet_boot_smoke - RunUAT RunUnreal UE.BootTest against a staged mock build on the Legion` | A hands-free "does the packaged build boot clean" check in front of butler. Epic documents the command; whether it works on a content-only Development build is untested. | M |

Honorable mention, owner-only and cheapest of all: create the real itch.io draft page and write its
`user/game:win64` into the runbook (jam-readiness "Must fix" #1). It is not an agent ticket, so it is not ranked.

---

## 1. Unreal 5.8 automation we are not using yet

| Item | What it is (source) | Buys | Effort | Verdict / ticket |
|---|---|---|---|---|
| 1.1 `-run=pythonscript` commandlet | `UnrealEditor-Cmd.exe <uproject> -run=pythonscript -script="x.py"` runs a script headless, "very fast"; does not load a level on its own, so load one first with `LevelEditorSubsystem.load_level` ([Epic: scripting the editor with Python](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python), VERIFIED) | Verification and bulk edits that skip the single MCP caller (one call at a time on the game thread). Could run `ue_verify_level.py`-style checks while the lead keeps MCP busy, est. minutes per gate. | S-M | **Maybe.** UNVERIFIED: whether a second editor process can open the same project while the first holds it. Test on the mock project before relying on it. Ticket: `T: pythonscript_verify - run ue_verify_level.py via -run=pythonscript, note concurrent-editor result`. |
| 1.2 `-ExecutePythonScript` | Same page: full editor launches, loads default level, runs the script, then shuts down. Needs the Editor Scripting Utilities and Python plugins ([same page](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python), VERIFIED) | A scripted "open level, force save, quit" step that fixes the mock 10 failure (MCP edits never reached the `.umap`). | S | **Strong idea inside the force-save tool's fallback.** `force_save_level.py` already exists, so only add this as its documented plan B. No new ticket. |
| 1.3 Python remote execution | Project Settings has a "Python Remote Execution" section with an enable toggle, a multicast endpoint (IP:port), a bind address and a TTL ([Epic: Python settings](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-settings-in-the-unreal-engine-project-settings), VERIFIED via search snippet). Default port not confirmed. A related setting is flagged as a vulnerability if an outsider can reach the server (UNVERIFIED which setting applies). | Nothing MCP does not already do (`execute_python` is in the toolset notes, KB "agent build-and-verify loop"). | M | **Skip.** Adds a network listener on the dev box for no new capability. |
| 1.4 Movie Render Queue, command line | `UnrealEditor-Cmd.exe <uproject> <map> -game -LevelSequence="/Game/..." -MoviePipelineConfig="/Game/...Preset" -windowed -resx=1920 -resy=1080 -log -notexturestreaming`. One job, one map; Python executor needed for more control ([Epic: command line rendering with MRQ](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-command-line-rendering-with-move-render-queue-in-unreal-engine), VERIFIED). The page says nothing about Render Graph. | Clean 4-6 store screenshots and an end-card shot without hand-driving the editor. | M | **Low priority.** The video rule says recorded gameplay (KB: keep cinematics to a closing shot at most), and OBS is verified. Only worth it if there is spare time on day 4. No ticket. |
| 1.5 Take Recorder | Not researched from a primary page. | n/a | n/a | **UNVERIFIED, skipped.** It records sequences, not the 30-60 s gameplay clip the rule asks for. |
| 1.6 Automation tests | `-ExecCmds="Automation RunTest Test1+Test2;Quit"`, `Group:<name>`, `-ReportExportPath=<dir>` for JSON results ([Epic: run automation tests](https://dev.epicgames.com/documentation/en-us/unreal-engine/run-automation-tests-in-unreal-engine), VERIFIED). The page does not cover `-unattended`, `-nullrhi` or exit codes. (A search summary of Epic's docs says an exit code of 0 means no failures: UNVERIFIED.) The console has both `RunTest` (exact test names, the form this page shows) and `RunTests` (a filter prefix); the KB and `mock-jam-6-tooling-plan.md` use `RunTests <Project>.` as a filter on purpose, so that spelling is not wrong. This page was only partly fetched, so I did not verify `RunTests` myself. | Only useful if we write C++ or functional tests. A Blueprint-first 4-day jam will not. | M | **Skip for the jam.**  |
| 1.7 Gauntlet boot test | `RunUAT RunUnreal -test=UE.BootTest ...`; `UE.TargetAutomation` takes `-build=<path to packaged game>`; add `-platform=<platform> -device=<ip>:<platform>` for a remote device ([Epic: running Gauntlet tests](https://dev.epicgames.com/documentation/en-us/unreal-engine/running-gauntlet-tests-in-unreal-engine), VERIFIED). Gauntlet itself: sessions of processes that run tests and validate results ([Epic: Gauntlet](https://dev.epicgames.com/documentation/en-us/unreal-engine/gauntlet-automation-framework-in-unreal-engine), VERIFIED). | A scripted boot-and-no-crash check on the Legion before butler. Est. saves one "it crashes on a clean box" surprise. | M | **Top 5, #5.** Run it on the Legion (UE 5.8.4 is installed there), not from Linux. UNVERIFIED: that `UE.BootTest` accepts our content-only staged output (the Lyra example uses `-build=local`). It complements, never replaces, `visual_playtest.py`. |
| 1.8 BuildCookRun flags | The only official example is `-project=... -clientconfig=Development`; "any text after BuildCookRun is passed through" ([Epic: build operations](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-operations-cooking-packaging-deploying-and-running-projects-in-unreal-engine), VERIFIED). Our script uses `-cook -build -stage -pak -archive` (`scripts/package-and-push.ps1:100`). It passes no `-prereqs` (already in runbook section 5) and no iterative-cook flag. | Iterative cook could cut repeat packaging time. UNVERIFIED: the flag name and whether it is safe with the 5.8 incremental cook (KB says Beta). | S | **Do not change the script in the window.** If wanted, measure `-iterate` on a mock project first and copy flags from a Project Launcher log, as the KB already says. |
| 1.9 MCP toolsets we never call | `list_toolsets` returned 67 toolsets on 2026-11-04 (readiness 2b). I did not audit which are unused: the Unreal MCP was not available to me (no editor runs) and my grep of `scripts/` found no toolset-name literals. | Unknown. | S | **Not done.** A 30 minute task for the lead once the editor is open: dump `list_toolsets`, mark each with "used / not needed", and keep the list in the runbook. The runbook already warns that `describe_toolset` on Niagara is about 250,000 tokens. |

## 2. Asset speed

The provider order and licence gates are in `_config/reference/ai-providers.md`; nothing is changed here.

| Item | Finding | Buys | Effort | Verdict |
|---|---|---|---|---|
| 2.1 Fab free content | Fab's "Limited-Time Free" page lists three items ending Nov 17, 9:59 AM ET (Underground Tunnel, SciFi Beast06 Bull, 3D Platformer Game Bundle) ([Fab](https://www.fab.com/limited-time-free), VERIFIED). Rotation cadence not stated on the page; the KB says two-week cycle. | Nothing score-wise: sourced assets are not scored (Rule 15(c), KB) and must be listed. | n/a | **Skip.** Also an open question (#8, #21) whether Starter Content / Fab / plugins are allowed or fed to AI. Do not claim anything before Epic answers. |
| 2.2 Megascans | Per the KB, no longer free after 2024 ([80.lv](https://80.lv/articles/megascans-no-longer-free-after-2024/); not re-fetched). | n/a | n/a | **Skip.** Same 15(c) logic. |
| 2.3 Blender add-ons for quick props | Not researched from a primary source. The repo already has `procedural_props.py` and `scripts/chain/blender_cleanup.py`. | n/a | n/a | **UNVERIFIED, not recommended.** A new add-on adds a licence to audit (Rule 15) on top of the ones already in `license-audit-asset-chain-2026-11-07.md`. |
| 2.4 Cloud generators | Nothing new: Meshy (3D, opt-in), GPT and Grok (concept images) are already wired and terms-gated. | n/a | n/a | **Nothing to add.** One check, not a ticket: `gen_asset.py --providers-check` is in the start-of-session checklist. |

## 3. Capture and QA

| Item | Finding | Buys | Effort | Verdict / ticket |
|---|---|---|---|---|
| 3.1 OBS websocket | Auth is SHA256 challenge/response on the `Hello` handshake. Requests: `StartRecord`, `StopRecord`, `GetRecordStatus`, `StartReplayBuffer`, `SaveReplayBuffer`, `GetStats`, `SetInputSettings`. Events: `RecordStateChanged` carries `outputPath` on stop; `ReplayBufferSaved` carries `savedReplayPath` ([obs-websocket protocol](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md), VERIFIED; default port not shown on what I read, our scripts use 4455). | Replaces file-name guessing with the event path; `GetStats` gives skipped frames to fail a bad take. Mock 10's recording cost several attempts (15-35 s start-up race, a stuck dialog after `taskkill /F`, a firewall prompt). | M | **Top 5, #2.** Ticket above. Also fold in: pre-start OBS before the game, poll the socket up to 60 s (as `rec5.ps1` did), and never `taskkill /F` OBS. |
| 3.2 Firewall prompt | Mock 10 found one click per exe path stops it; the agent cannot dismiss it over ssh (secure desktop). | Prevents a popup in the final clip. | S | Owner-only, already in the findings. Add to the day-1 test: run the staged exe once by hand on the Legion, so the exact path is allowed before the real clip. |
| 3.3 Windows SendInput | Subject to UIPI: input goes only to apps of equal or lower integrity; if blocked, "neither GetLastError nor the return value will indicate the failure was caused by UIPI". It does not reset held keys; check `GetAsyncKeyState` ([Microsoft: SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput), VERIFIED). | `visual_playtest_input.ps1:59,65` discards the return count. A zero return means the key never reached the game and the run would still "pass" its blind frames. | S | **Small fix, include in ticket 5 or the playtest owner's next PR:** compare the return count to the number sent and throw; also run the game and the input task at the same (non-elevated) level. No separate ticket. |
| 3.4 Frame-diff / video checks | ffmpeg ships `blackdetect`, `freezedetect`, `psnr`, `ssim` ([ffmpeg filters](https://ffmpeg.org/ffmpeg-filters.html), existence VERIFIED from its table of contents; parameters and log format NOT verified, read them before scripting). | `freezedetect` catches a frozen final clip; `blackdetect` catches a black start/end. These are the checks that stills miss (see the mock 10 loop). | S | **Top 5, #1.** Ticket above: one script on the Linux desktop (ffmpeg already there per readiness 5c). Gate: width >= 1920 and height >= 1080 via ffprobe, 30 <= seconds <= 60, no long black or frozen span. |

## 4. Contest readiness

| Item | Finding | Buys | Effort | Verdict / ticket |
|---|---|---|---|---|
| 4.1 butler flags | Channel names carry platform tags (`win`, `windows`, `linux`, `mac`, `osx`, `android`), lowercase with dashes. `--userversion 1.0.3` labels a build. `--if-changed` skips a push when files match the latest build. `--dry-run` lists files to push. The page does not document `butler status` (the repo uses it, readiness 3d) ([itch: pushing](https://itch.io/docs/butler/pushing.html), VERIFIED). Our pushes (`package-and-push.ps1:168`, `legion_ship.py:335`) use none of these flags. KB already recommends `--ignore '*.pdb'`. | `--userversion` labels each of the 4 gate builds so a judge-visible version matches the dev log; `--dry-run` shows a stray `.pdb`; `--ignore` keeps the upload small. | S | **Fold into ticket 3** (submission sheet): write the exact final push line. Do not edit the script inside the window. |
| 4.2 itch page checklist | Already in KB ("itch page checklist"). Screenshots/cover/GIF not required by anything found (`submission_page_and_video.md` line 29). | n/a | n/a | Nothing new. |
| 4.3 Submission form fields | The real form is not public. The Rules digest lists the required parts (zip, video, dev log link for Glass Box); open questions #3 and #18 stay open until the form is seen. | A pre-written sheet avoids typing under pressure. | S | **Top 5, #3.** The sheet should hold: game title, `TeamName_GameName` (decide now, readiness 5b), itch URL, butler target, video URL (note: YouTube "unlisted" may fail an embed, `submission_page_and_video.md` line 66; pick public or test), dev log URL, modifier notes (Glass Box), and the pre-jam declaration path. |
| 4.4 AI declaration text | Rule 9: the extent of AI use is context only. Rule 7(h): pre-jam tooling must be declared and is already in `stages/00_prep/references/pre-jam-declaration-2026-10-29.md` (tag `pre-jam-tooling` still not created, readiness 6a). | A 6-line paste text in the sheet: tools used per task (names from `ai-providers.md`), human decisions, and any CC BY attributions. | S | Part of ticket 3. Keep claims to what the logs (`asset-pipeline-log.csv`) show. |

## 5. Risks

| Risk | Evidence | Mitigation | Effort | Ticket |
|---|---|---|---|---|
| Legion Wi-Fi / link | `ssh <device-host>` timed out on 2026-11-07 21:22 although Tailscale said active/direct (findings 10). Past zips 431-447 MiB. I have no measured Wi-Fi transfer time. | Measure one full ssh + scp + butler cycle with a dummy 450 MB zip (not a game; no Rule 7(h) issue). Set the Legion to never sleep while plugged in (`powercfg`, owner) and keep `ServerAliveInterval` (already in `legion_preflight.py:28`). | S-M | **Top 5, #4.** |
| GPU contention | Runbook section 1 and `gpu-preflight` cover it; `launch-editor.sh:8` says it does not replace the gate. | One cheap addition: `launch-editor.sh` refuses to start when `gpu-preflight` is BLOCKED. Not verified whether this is wanted (the header says otherwise on purpose). | S | Owner call; not ticketed. |
| Context handoffs | Auto handoff at 140K (memory: Stop hook), `describe_toolset` can use up to about 250K tokens (runbook section 4), mock 10 stall from ending a turn with no tool call. | Keep a one-page `JAM-STATE.md` the lead rewrites at every gate (current gate, last good build, open bugs, next 3 actions) so a cold restart does not depend on the handoff alone. | S | `T: jam_state_template` if the owner agrees. Not top 5. |
| Silent wrong build | Mock 10: the shipped level was stale (force-save). | Already handled by `force_save_level.py`; keep it as step 0 of every package. | n/a | Done. |

## Next step for the owner

Pick any of the five tickets above; each is independent. The two owner-only items that no agent can do
remain: create the real itch.io draft page and settle `TeamName_GameName`.
