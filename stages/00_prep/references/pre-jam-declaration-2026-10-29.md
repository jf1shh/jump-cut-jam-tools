# Pre-jam declaration — 2026-10-29

What exists in this repo and on the dev machines before the 2026-11-12 00:00 ET contest window
opens, for Rule 7(h) ("only AI tools, agent configs, MCP settings, prompt libraries and scripts
may exist; no gameplay, levels or art"). Epic may ask for this repo's version-control history —
this file is the audit trail for that ask.

Repo state at declaration time: `master` at `ef6378e` (after PR #39 and #40 merged, worktrees and
branches cleaned up).

## 1. What's declared to exist (all allowed under Rule 7(h))

**Agent configs / prompt library**
- `AGENTS.md`, `CLAUDE.md` — project facts, decisions, working rules, jam-week autonomy exception
- `_config/reference/templates/*.md` — dev log entry, feature-slice brief, GDD one-pager, playtest checklist,
  scoring rubric (all blank templates, no real content filled in)
- `stages/00_prep/references/pre-jam-mechanic-toolkit.md` — pre-built Blueprint mechanic toolkit notes (prose/plan, not
  a packaged mechanic committed as an asset)

**MCP settings**
- Unreal MCP + All Toolsets plugins enabled on the desktop editor; `ModelContextProtocol.GenerateClientConfig
  ClaudeCode` run (config only, no project content)

**Scripts**
- `scripts/gen_asset.py` — Nexus image/3D asset pipeline CLI
- `scripts/gen_music.py` — Nexus ACE-Step music pipeline CLI
- `scripts/gen_devlog.py` — dev log drafting CLI
- `scripts/qa_harness.py` — map-load/screenshot/frame-time QA CLI
- `scripts/ue_import_asset.py` — headless UE Python asset import
- `scripts/package-and-push.ps1` — RunUAT cook/stage/archive/zip/butler-push CLI
- `scripts/transcribe-videos.py` — research transcript tooling (pre-jam research only)
- Added after the original declaration (refreshed 2026-11-01): `scripts/agent_playtest.py`,
  `scripts/legion_capture_screenshot.py`, `scripts/legion_playtest.py`, `scripts/legion_obs_record_test.ps1`,
  `scripts/legion_remote_launch.ps1`, `scripts/legion_screenshot.ps1`, `scripts/ue_build_level.py`
  (builds a greybox mock level in a scratch project, not entry content), `scripts/ue_verify_level.py`
- `_config/reference/templates/theme-spread-prompt.md` (prompt template) and 8 further research docs under `_config/reference/research/`

**Research and reference docs (no gameplay content)**
- `_config/reference/knowledge-base.md`, `_config/reference/research/**`, `_config/reference/engine-reference/unreal/**`,
  `stages/00_prep/references/win-plan.md`, `PLAN.md`, `RULES.md`, `_config/CANON.md`, `stages/04_ship/references/capture-setup.md`
- `stages/00_prep/references/license-check-modly-foundrylab.md` — license review (prose, not shipped content)

**Pipeline timing logs (not game assets)**
- `stages/02_build/output/asset-pipeline-log.csv`, `stages/02_build/output/audio-pipeline-log.csv` — timing/exit-code rows only (name,
  stage, seconds, exit code, output path). No art, meshes, or audio files are tracked in git; the
  actual generated outputs they reference live under `work/generated/` and `work/audio/`, both
  gitignored, and get deleted/regenerated per mock jam.

**Mock-jam findings (rehearsals, not the real entry)**
- `stages/00_prep/output/mock-jam-findings.md` through `-4.md` — four rehearsals of the full pipeline (generation →
  Blueprint wiring → packaging → playtest), each run in a throwaway scratch project
  (`megajam-mock`, `~/Projects/ue-mcp-verify`) outside this repo, never the real entry project, and
  explicitly deleted/discarded per PLAN.md's "run early then delete" instruction. The *findings
  about* those rehearsals (gotchas, timings, API behavior) are allowed prose; the *content* of
  those rehearsals (Blueprints, meshes, levels) is not in this repo and was not carried forward.

**Refresh note (2026-11-01):** this declaration was cut at `ef6378e`; `master` has moved since. The
lists above and below now include everything the license audit found undeclared.

**Tracked image files (QA captures, not entry art).** `stages/03_playtest/output/qa-screenshots/Game_MockJam6_L_MockJam6.png`
and `stages/03_playtest/output/qa-screenshots/Game_MockJam7_L_MockJam7.png` are two committed screenshots of mock-jam
rehearsal levels (greybox, scratch projects). They are QA evidence, not entry art or content; §2 below
originally said no art is tracked, and these two PNGs are the exception.

**Tools in the pipeline (named in full)**
- Modly (3D server, MIT, loopback only, offline env); ComfyUI (host for image, music, upscale)
- Image: Krea 2 Turbo (`Comfy-Org/Krea-2`) with its Qwen3-VL-4B text encoder and Qwen-Image VAE
- 3D: **TripoSplat** (`VAST-AI/TripoSplat`, Modly extension `triposplat` v1.0.1; weights and code MIT), called as `nexus-3d --model triposplat` (the only 3D form `contest_guard.py` allows). Replaces Hunyuan3D 2.0 (owner decision 2026-11-01; Tencent license §5(c) territory clause on outputs). Output is a UV-baked albedo GLB (no PBR maps). Dependencies: BiRefNet (MIT), DINOv3 (DINOv3 License; "Built with DINOv3" in `_config/reference/NOTICE.txt`), FLUX.2 VAE (Apache-2.0). No new downloads: weights were pre-staged. No Hunyuan output is committed or shipped.
- 3D, opt-in cloud (added 2026-11-07, owner decision "Yes, add Meshy"): **Meshy** (meshy.ai image-to-3D API), called only by the stdlib adapter `scripts/providers/meshy.py` through `scripts/gen_asset.py --3d-provider auto|meshy`. Off unless the owner sets `MESHY_API_KEY` and `MESHY_TERMS_REVIEWED` in `~/.config/megajam.env`. Policy 2026-11-07: not local-only; `--3d-provider auto` is speed-first (Meshy when configured, local TripoSplat as fallback). Image `--provider auto` order is now `grok, local, gpt`. No new dependency, no model download. Licence notes and open questions: `_config/reference/ai-providers.md`.
- Background removal: BiRefNet (MIT) inside TripoSplat
- CPU tail: AutoRemesher, xatlas, trimesh, open3d; UniRig (only with `--unirig`, not passed by default)
- Music: ACE-Step 1.5 turbo with its Qwen text encoders
- Upscale: Real-ESRGAN x4plus (default). 4x-UltraSharp is installed but banned (non-commercial).
- faster-whisper (research transcripts only); Claude Code (code and Blueprint generation)
  (owner confirmed 2026-11-01 that Claude's "help improve Claude" model-training setting is OFF; relevant to the UE EULA generative-AI input clause, whose text is still unverified from a primary source because Epic pages returned 403)

## 2. What is confirmed NOT present (verified this session)

- `find . -iname "*.uasset" -o -iname "*.umap"` in this repo: zero matches.
- `work/generated/` and `work/audio/` (actual generated art/audio) are gitignored and untracked —
  `git ls-files work/` returns nothing.
- No `.uproject` or UE project folder is tracked in this repo.
- Exception noted 2026-11-01: two QA screenshot PNGs are tracked under `stages/03_playtest/output/qa-screenshots/` (see §1).

## 3. Licensing adherence — audit run this session

Full review already existed in `stages/00_prep/references/license-check-modly-foundrylab.md` (2026-10-28 version). This
session re-checked it against the actual pipeline code, not just the doc's claims, and found two of
its three action items were still open in code:

| Finding | Status before this session | Fixed this session |
|---|---|---|
| `scripts/gen_asset.py` never passed `--model`, so it silently used Nexus's default image model, **Qwen-Image 2.1 — non-commercial-only, cannot back a cash-prize entry (Rule 15(b))** | Open — flagged in the doc 2026-10-28, never wired into the script | **Fixed**: `--model` now defaults to `krea-2-turbo` (commercial-OK under $1M revenue), forwarded to `nexus-image`. Hardened 2026-11-01: `gen_asset.py` refuses `qwen-image*`, `ultrasharp` and `hunyuan3d*`, and pins `NEXUS_THREED_IMAGE_CHECKPOINT=krea-2-turbo` for the 3D stage |
| Packaged build had no Hunyuan3D-2 Notice file, required on any build distributed outside a hosted service | Open | **Fixed**: added `_config/reference/NOTICE.txt` with the exact mandated text; `scripts/package-and-push.ps1` now copies it into the staged build by default (`-NoticeFile`, pass `''` to explicitly skip for a non-shipping dry run; script warns loudly if skipped) |
| ACE-Step 1.5 (music) license | MIT, confirmed in `_config/reference/knowledge-base.md` | No action needed |
| UniRig, autoremesher, Wan 2.2, Krea 2 Turbo, SDXL | All already confirmed commercial-clean against primary sources | No action needed |
| Epic MetaSound SFX Generator (primary SFX source) | Generated, not sourced — scores under Rule 15(c), zero external license | No action needed |
| Kenney.nl CC0 packs (SFX fallback) | Confirmed CC0 1.0 on kenney.nl | No action needed; still needs a sourced-asset ledger entry if ever used (Rules 1(d)/15(c)) |
| Unreal MCP + All Toolsets (Epic's own plugin) | Editor-only tooling, never cooked into a packaged build | No action needed |
| VS 2022 Build Tools / Windows SDK (Legion Go S) | Standard Microsoft dev toolchain, not shipped content | No action needed |

**Mock jam 4's generated art** (`mockjam4_throwable`, `mockjam4_target`) was produced before this
fix, so it used the (then-default) Qwen-Image path. That's fine under the license's own terms —
non-commercial exploration/concept art that never ships — but confirms the fix was live, not
theoretical: nothing from mock jam 4 goes into the real entry anyway (§1 above).

## 4. Tooling test run this session

- All six Python scripts compile clean (`python3 -m py_compile`): `gen_asset.py`, `gen_devlog.py`,
  `gen_music.py`, `qa_harness.py`, `transcribe-videos.py`, `ue_import_asset.py`.
- `scripts/package-and-push.ps1` is Windows-only (runs on the Legion Go S); no `pwsh` available on
  the Linux desktop to execute it here. Reviewed by hand for the notice-file change; not re-run
  end-to-end this session (last end-to-end proof: PLAN.md Week 2, Nov 4 gate, 2026-10-28). A fresh
  end-to-end packaging run (now exercising the new `-NoticeFile` copy step) is worth doing once more
  before Nov 11, from the Legion, now that VS Build Tools / full Visual Studio is confirmed
  installed there.
- GPU was busy with another workload when this audit ran (`gpu-preflight` → BLOCKED), so no live
  `nexus-image`/`nexus-3d`/`nexus-music` calls were made this session — the `--model krea-2-turbo`
  fix was verified by reading Nexus's own README (`krea-2-turbo` documented as an explicit CLI
  option) rather than by generating a real asset. **Update 2026-11-01:** `stages/02_build/output/asset-pipeline-log.csv`
  logs a `smoketest-krea` run on 2026-10-29 (image 69.9 s, 3D 96.3 s, exit 0), but its output folder is
  gone and no provenance sidecar was kept, so the log row is the only evidence and it does not prove
  which model rendered it. **A live re-test with a provenance sidecar is still pending**, to confirm the
  flag reaches `nexus-image` and produces a Krea-licensed concept image.

## 5. Open items (carried into PLAN.md's Final days checklist)

1. Re-run the live `gen_asset.py --model krea-2-turbo` smoke test (§4) with a provenance sidecar once the GPU is free (the 2026-10-29 run is logged, exit 0, but kept no provenance).
   1a. Live ROCm smoke test of `nexus-3d --model triposplat` (time, VRAM, offline) is recorded outside the repo by the Nexus-side session; re-check UV albedo surviving the foundry-lab bake and UE Interchange import (owner/hub).
2. Re-run `package-and-push.ps1` once end-to-end on the Legion to confirm the NOTICE.txt step
   works against a real cook.
3. OBS capture profile setup on the Legion still needs an interactive session (not SSH-reachable).
4. Final rules re-read against the Box PDF, tag `pre-jam-tooling`.
