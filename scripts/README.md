# Scripts catalog (tooling only, Rule 7(h))

Every tracked file in `scripts/` (`git ls-files scripts`: 71 scripts plus this README). These are tools, not game content. Declared in
`stages/01_concept/output/prejam/PREJAM-DECLARATION.md`. Prompts that call them: `_config/reference/prompts/README.md`.
Use `python3 scripts/NAME.py --help` for options; descriptions below come from each file's header.

**Who may run it**

- **Lead**: calls Unreal MCP (port 8010) or drives the open editor. Only the one lead agent runs these (AGENTS.md).
- **Any**: no MCP, no editor, no local model. A helper, a docs agent or the lead may run it.
- **Legion**: runs on the Windows box (`.ps1`) or from the PC over ssh to it. One Legion job at a time; the lead or the
  playtest agent starts them, never two at once.
- **Owner**: needs the owner's hands, keys, or a decision.
- **OFF**: needs a local AI model or the local model host; local AI is off for the whole jam. Do not run during the window.

Marks: **mock-only** = built for a mock jam rehearsal, not the real game; **stale** = likely out of date, check before use.

## Editor and MCP

| Script | What it does | When in the jam | Who |
|---|---|---|---|
| `launch-editor.sh` | Starts the UE editor (5.9 default, `UE_VERSION=5.8` fallback) with the MCP port, in its own memory scope; waits up to 300 s for :8010 (exit 8/9 on failure). | Every editor start; after a crash | Lead |
| `mx.py` | Context-cheap helper for the MCP server: `shot`, `call`, `describe`, `toolsets`, `py`; caches describes, caps output. | Default way to talk to the editor | Lead |
| `mcp_call.py` | Small CLI for the MCP server: `list-tools`, `call`, `save-all`, `snapshot-commit`. | When `mx.py` is not enough; scripted saves | Lead |
| `force_save_level.py` | Force-saves the dirty level through MCP and verifies the `.umap` on disk (prints VERIFIED). | Before every package, gate and night end | Lead |
| `step_shot.py` | Frames the editor viewport, screenshots it, logs it, so the agent can Read the PNG. | After every build step | Lead |
| `editor_watchdog.py` | On a timer: MCP save-all and snapshot commit; if the editor died, copies the logs to `stages/04_ship/output/crash-logs/`, relaunches. | Start once the editor is up for unattended hours | Lead |
| `ue_import_asset.py` | Imports a GLB into the project with `SM_`/`SK_`/`MI_` names; runs inside the editor's Python (via `mx.py py` or headless). Header names UE 5.8; check on 5.9. | When an asset is ready to land | Lead |
| `ue_verify_level.py` | Loads the saved level fresh, lists actors, flags agent traps (grid material, etc.); its output feeds `presubmit_gate.py`. | Before every package | Lead |
| `presubmit_gate.py` | Fails if any visible actor still shows a default grid or checker material; reads the verify log only, no editor. | Before every package and gate | Any |
| `ue_build_level.py` | Builds the mock-jam-7 grey-box room with `SM_Beacon`/`SM_Orb`; headless editor script. **mock-only**, useful as a pattern for a level script. | Not as is | Lead |
| `build_world.py` | Runs a level build command (can detach), then checks the scale of what it placed from a placements list. **Mock-era**; the pattern (detach, scale check) still works. | Optional, big level builds | Lead |
| `layout_spec.py` | Checks a top-down layout against the metric sheet, renders an SVG, writes a build plan (JSON) for `ue_build_level.py --plan`. File-only. | When laying out a scene from the greybox sheets | Any |
| `hud_text_box.py` | Recipe for a HUD text line on a dark backdrop box (readable text); `--apply` writes into a Blueprint through the editor. | HUD work; without `--apply` it only prints | Any (Lead for `--apply`) |
| `new-mock-project.py` | Writes a content-only UE project: `.uproject`, `.mcp.json`, config with the MCP port pin. Called by `jam_start.py`. | Only through `jam_start.py` | Lead |

## Assets (generation, preview, ledgers)

| Script | What it does | When in the jam | Who |
|---|---|---|---|
| `gen_asset.py` | Concept image to 3D: providers `grok`, `fal`, `gpt` (image) and `meshy`, `tripo`, `hyper3d`, `fal` (3D); `--providers-check` spends nothing; writes a provenance sidecar and a CSV row. Name the cloud provider; `local` is OFF. | Every generated asset | Any (needs the grey-box gate) |
| `providers/` (folder) | Adapter modules for `gen_asset.py`: `cloud.py` (shared cloud safety and key handling), `fal.py`, `hyper3d.py`, `meshy.py`, `tripo.py`, `__init__.py` (image providers, `AUTO_ORDER`, timeouts). Imported, not run. | Never directly | n/a |
| `asset_chain.py` | One command, prompt to game-ready prop, with queue, lanes and licence gate. Its 3D engine is local TripoSplat and `grok` is refused as "unclear" licence, so only the `gpt` image path is usable in the jam. **Mostly OFF.** | Avoid; use `gen_asset.py` | Any |
| `chain/` (folder) | Library for `asset_chain.py`: `pipeline.py` (queue, resume, provenance), `engines.py`, `licenses.py`, `blender_cleanup.py`. Imported, not run. | Never directly | n/a |
| `asset_preview.py` | Renders a contact sheet (4 views, scale reference, textures) and `preview.json` for a GLB so the agent can Read it before import. Needs Blender (CPU). | After every generated asset | Any |
| `render_glb.py` | Blender script that renders one GLB to a PNG. Small helper for previews. | Optional | Any |
| `triposplat_cleanup_glb.py` | Blender cleanup of a GLB (weld, drop islands, remesh, decimate, bake). Written for TripoSplat output; also fits cloud GLBs. | If a GLB is too heavy or dirty | Any |
| `procedural_props.py` | Blender script: low-poly wooden props (crate, barrel, fence, placeholder person) to GLB. CPU only. A no-AI fallback for placeholders. | When a prop is needed fast and cheap | Any |
| `sourced_assets.py` | Sourced-asset ledger (Rules 1(d), 15(c)): `add`, `list`, `credits` block for the dev log and itch page. | Whenever a non-original asset is used | Any |
| `seam_test.py` | Gives a number for a tileable texture's seams (practice tool for the look kit). | Optional, texture work | Any |
| `gen_music.py` | Wraps Nexus's local ACE-Step music generator and logs timing. **OFF** (local model). | Not in the jam | OFF |

## Build, package and ship

| Script | What it does | When in the jam | Who |
|---|---|---|---|
| `legion_ship.py` | One command from the PC: sync project to the Legion, package, check the exe, push to itch (default: private pretest page), wait for processing. Pass `--engine C:\Dev\UE_5.9`. | Each package | Lead (Legion) |
| `package-and-push.ps1` | Runs on the Legion: RunUAT cook, stage, archive, zip under 1 GB, optional butler push. Called by `legion_ship.py`; the real itch push needs the owner's go. | Via `legion_ship.py` | Legion |
| `legion_preflight.py` | Read-only check of the Legion before a run: ssh, OBS, websocket, firewall, stale tasks, console session. `--remove-stale` deletes only `MJTool*` tasks. | Before every package and recording | Any (Legion) |
| `legion_preflight.ps1` | The part of the preflight that runs on the Legion; prints one JSON object. | Via `legion_preflight.py` | Legion |
| `jam_backup.sh` | Backups to the NAS: `nightly`, `gate <label>`, `check` (writes nothing). Never deletes. | Each gate and night end; `nightly` runs from a timer | Lead (owner approved NAS writes) |
| `android_toolchain_check.sh` | Compares the installed Android SDK pieces with what UE wants. **Not on the plan** (Windows is the target); optional side target. | Only if the owner adds Android | Owner |
| `android_package.sh` | UAT BuildCookRun for Android (ASTC), logged. Refuses while the editor runs. **Not on the plan.** | Only if the owner adds Android | Owner |
| `android_install.sh` | Installs an APK on the owner's phone over adb, launches, screenshots. **Not on the plan.** | Only if the owner adds Android | Owner |

## Playtest and QA

| Script | What it does | When in the jam | Who |
|---|---|---|---|
| `agent_playtest_cli.py` | Closed-loop playtester on the packaged build: `start`, `look`, `press`, `mouse`, `clip`, `state`, `mark`, `gate`, `stop`; real input, real screen. | Every package | Any (Legion) |
| `visual_playtest.py` | Plays the packaged build with scripted real input, captures frames, writes a checklist; `verify` and `gate` need a PASS verdict per item. | Every package | Any (Legion) |
| `visual_playtest_input.ps1` | Runs on the Legion in the console session; sends real OS input (SendInput) from a step list. Called by `visual_playtest.py`. | Via `visual_playtest.py` | Legion |
| `legion_playtest.py` | Package to deploy to launch to verify loop on the Legion in one command (deploy, register task, launch, check). Used by the playtest scripts. | Via the playtest scripts | Any (Legion) |
| `legion_remote_launch.ps1` | Runs on the Legion: deploys a zip to a clean folder and points a scheduled task at the exe so launch lands in the real session. | Via `legion_playtest.py` | Legion |
| `legion_screenshot.ps1` | Runs on the Legion in the interactive session; captures the full virtual screen to a PNG. | Via `legion_capture_screenshot.py` | Legion |
| `legion_capture_screenshot.py` | PC side: takes a screenshot of the Legion's real display over ssh with a scheduled task. | When a look at the Legion screen is needed | Any (Legion) |
| `legion_record.py` | Records the packaged game on the Legion with OBS and checks the video (retries once). | Trailer and gameplay clip, 30 to 60 s at 1080p or higher | Lead (Legion) |
| `legion_obs_record_test.ps1` | OBS end-to-end recording test over the websocket (12 s record, replay clip). Run on the Legion over ssh. | Once, to prove OBS before the clip | Owner or lead (Legion) |
| `judge_pass.py` | Builds a packet from a playtest session and a rubric prompt for a second agent that rates the build like a judge; `parse` reads its report. | After the playtest gate passes | Any |
| `agent_playtest.py` | Headless PIE steering test: moves the pawn toward a `QAObjective` actor and reports whether distance closed. Runs in the editor's Python. | Smoke test of the plumbing, not a playtest | Lead |
| `qa_harness.py` | Headless pass over a list of levels: load, fixed-camera screenshot, real frame time against an FPS budget. | Frame-time check before a gate | Lead |
| `vlm_judge.py` | Judges one frame with a local vision model on the local model host. **OFF** (local model). Use a cloud agent reading the frame instead. | Not in the jam | OFF |
| `mock_scorecard.py` | Fills a mock-jam scorecard row from a mock's evidence. **mock-only.** | Not in the jam | Owner |

## Jam ops

| Script | What it does | When in the jam | Who |
|---|---|---|---|
| `jam_start.py` | One checked command for the 21:00 setup: project via `new-mock-project.py`, `.dvignore` lines, `IDENTITY.md` and `CONTEXT.md`, jam-path file. `--dry-run`, `--check-stage`. | Once, at 21:00 | Lead |
| `epic_ask.py` | Hand-ask question box for Epic's Developer Assistant: `add "q" --context --from` (queue, refuses secrets, 1500-char cap), `list`, `count --open`, `show Q-NNN` (answers are unverified hints); `next` opens the page for the owner, who types the question by hand. Agents never drive the site or editor panel. | Only after the Unreal question ladder fails | Any (`next`: Owner) |
| `jam_clock.py` | Countdown to the deadline: `start`, `status`, `tick`, `check` (exit 0 go on, 10 package now, 11 final, 12 expired). | Start at 21:00; `check` every loop turn | Lead (`check`: Any) |
| `greybox_gate.py` | Blocks asset generation until a primitives-only build was won, lost and restarted: `record`, `check` (exit 0 or 13), `status`, `clear`. | Before any generation job | Lead records; Any checks |
| `evidence_index.py` | Lists screenshots, videos, playtest frames, scorecards and itch builds with times and paths (no network). | Dev log, evidence file | Any |
| `gen_devlog.py` | Drafts a dated dev log entry from git log, screenshots and notes; `--dry-run`. | Nightly | Any |
| `hooks/` (folder) | `contest_guard.py`: Claude Code PreToolUse hook that denies commands which break the contest rules (banned models, store fetching, unlisted cloud hosts). Wired in the owner's global settings, not in the repo. | Always on, never edit mid-jam | Owner |

## Rigging

The game has no humanoid actors in the core build (the stunt driver is a static prop, owner decision 2026-11-11), so treat
this group as **stale unless a skeletal character is added**. Blender, CPU only.

| Script | What it does | When in the jam | Who |
|---|---|---|---|
| `rig_mannequin.py` | Rigs a throwaway humanoid in Blender with UE mannequin bone names; FBX out. | Only if a rigged character is added | Any |
| `rig_rigify.py` | Rigs a humanoid with Rigify, deform bones only; FBX out. | Same | Any |
| `rig_bones.py` | Pure-Python bone layout for the mannequin dry run (imported by the rig scripts). | Never directly | n/a |
| `rig_timelog.py` | Stopwatch for a timed rig run; markdown table. | Same | Any |

## Canon and docs

| Script | What it does | When in the jam | Who |
|---|---|---|---|
| `ask_canon.sh` | Asks the curated jam canon (Nexus collection `megajam_canon`) a question. Needs the local model host for embeddings. **OFF**; read `_config/CANON.md` and `_config/reference/canon/` directly instead. | Not in the jam | OFF |
| `canon_ingest.sh` | Loads `_config/reference/canon/*.md` into `megajam_canon`; needs the local model host. **OFF.** | Not in the jam | OFF |
| `sync_project_canon.py` | Refreshes engine reference notes in the private Unreal canon. **OFF** (Nexus). | Not in the jam | OFF |
| `transcribe-videos.py` | Transcribes the must-watch videos (captions first, local Whisper fallback) into `_config/reference/research/transcripts/`. Research tool. **OFF** for the Whisper fallback. | Not in the jam | OFF |

## Notes

- CI only compile-checks every `scripts/**/*.py` (`python3.12 -m py_compile`); tests are in `tests/`.
- Secrets: scripts read `~/.config/megajam.env` themselves and never print values. An agent never asks for or prints a key.
- Unverified in this catalog: whether `ue_import_asset.py` and `qa_harness.py` run unchanged on UE 5.9 (headers say 5.8);
  whether the cloud-GLB cleanup step in `gen_asset.py` (its `nexus-3d handoff` call) needs the local model host. Check on first use and tell the hub.
