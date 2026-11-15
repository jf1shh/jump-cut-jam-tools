# Legal audit + end-to-end pipeline check — 2026-11-02

Owner ask: "full audit for legality and make sure image, video, 3d, audio, music generation are all
working end to end." Branch `claude/legal-audit-e2e-2026-11-02`. Not legal advice.

**Verdict:** no license blocker in the pipeline as wired. The two blocked models (Hunyuan3D 2.0,
4x-UltraSharp) are kept out by `gen_asset.py` and `scripts/hooks/contest_guard.py`.
Pipelines: **all five pass** (image, video, 3D → UE import, SFX via MetaSound, music), once each GPU job runs in its own memory scope (finding 1). SFX passes on the built-in MetaSound path; Epic's SFX Generator is not installed (finding 4).

## 1. Licenses

Method: model cards, LICENSE files and vendor pages read 2026-11-02 (WebFetch, plus a browser
for pages that blocked fetch). Risk: **ok** = fine as used; **check** = fine as far as we can tell,
one primary source still unread; **blocker** = must not be used.

| Item | Used for | License | Outputs / commercial | Duties for us | Risk | Source |
|---|---|---|---|---|---|---|
| Krea 2 Turbo (`krea2_turbo_fp8_scaled`) | Image | Krea 2 Community License | Commercial OK under $1M company revenue (s2.3); entrant owns outputs (s5.3); worldwide; revocable on breach; entrant indemnity (s8–9) | Keep content filters (s4.2); AUP binds outputs (s4.1(a), 4.4; read 2026-11-02, fine for a teen game); disclose AI origin where required (s4.3, dev log covers it); don't ship weights | ok | https://www.krea.ai/krea-2-licensing ; https://www.krea.ai/krea-2-use-policy ; https://huggingface.co/Comfy-Org/Krea-2 |
| Qwen3-VL-4B text encoder | Krea text encoder | Apache-2.0 | Commercial OK | None for outputs | ok | https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct |
| Qwen-Image VAE (`qwen_image_vae`) | Krea VAE | Apache-2.0 (Qwen/Qwen-Image card); **not** the qwen-research 2.1 license | Commercial OK | None for outputs | ok (file came from the Apache repo, not a 2.1 checkpoint: confirm once) | https://huggingface.co/Qwen/Qwen-Image ; https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI |
| TripoSplat (VAST-AI) | Image → 3D | MIT (code and weights) | Commercial OK, no output limits | MIT notice only if code/weights ship | ok | https://huggingface.co/VAST-AI/TripoSplat ; https://github.com/VAST-AI-Research/TripoSplat |
| DINOv3 (TripoSplat feature encoder) | 3D | DINOv3 License (gated) | Worldwide, royalty-free, no output clause; bans military/ITAR use only | Include the agreement only if weights are redistributed (they aren't). No "Built with DINOv3" duty | ok | https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md |
| FLUX.2 VAE (TripoSplat VAE) | 3D | Apache-2.0: BFL ships the same VAE under apache-2.0 in FLUX.2-klein-4B (browser-read 2026-11-02) | Commercial OK | None for outputs | ok | https://huggingface.co/black-forest-labs/FLUX.2-klein-4B |
| BiRefNet | Background removal | MIT | Commercial OK | Notice only if shipped | ok | https://huggingface.co/ZhengPeng7/BiRefNet |
| Wan 2.2 TI2V-5B (+ its VAE) | Video | Apache-2.0 | Commercial OK; licensor claims no output rights | Prohibited-use list applies | ok | https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B |
| umt5-xxl | Wan text encoder | Apache-2.0 | Commercial OK | None | ok | https://huggingface.co/google/umt5-xxl |
| ACE-Step 1.5 (+ Qwen3 LM bases) | Music | MIT; card allows commercial use of generated music | Commercial OK | Disclose AI music (dev log/credits) | ok | https://github.com/ace-step/ACE-Step-1.5 ; https://huggingface.co/ACE-Step/Ace-Step1.5 |
| Real-ESRGAN x4plus | Upscale | BSD-3-Clause (code); weights carry no stated limit | Commercial OK | Notice only if code ships | ok | https://github.com/xinntao/Real-ESRGAN |
| MetaSound (engine) | SFX | Part of UE, under the UE EULA | Ships with games under the EULA | None beyond the EULA | ok | https://www.unrealengine.com/eula |
| SFX Generator (Fab "TechAudioTools Content") | SFX (planned primary) | Free Fab item, Fab EULA | Presumed OK in shipped games | Owner must add it from Fab (sign-in + license click) | check (not installed; see §3) | https://dev.epicgames.com/documentation/en-us/fab/licenses-and-pricing-in-fab |
| Kenney.nl packs | SFX fallback | CC0 | Commercial OK | List as sourced assets (Rule 15(c)); they don't score | ok | https://kenney.nl/support |
| Unreal Engine 5.8 EULA | Engine | UE EULA; update 22 (2026-10-30) removed the §6(e) gen-AI input limit | Standard royalty terms | **Owner: accept the amended EULA** when the Epic Games Launcher prompts (see §4) | check (owner action) | https://www.unrealengine.com/eula-change-log/unreal |
| ComfyUI, Modly, UniRig, AutoRemesher ≥1.0, xatlas, trimesh, open3d, butler, faster-whisper, OBS, ffmpeg | Tools | GPL-3.0 / MIT / GPL / LGPL | Tool licenses don't reach outputs (GPL FAQ); none ship in the game | None | ok | see `stages/00_prep/references/license-check-modly-foundrylab.md` |
| Claude Code | Code | Anthropic Commercial Terms | Customer owns outputs | None | ok | https://www.anthropic.com/legal/commercial-terms |
| Roboto (UE default font) | UI | Apache-2.0 | OK | None | ok | https://github.com/google/roboto |
| **Hunyuan3D 2.0** | Was 3D | Tencent community license: territory excludes EU/UK/KR; output use outside it unlicensed (s5.c) | Can't satisfy a worldwide itch download | n/a | **blocker if used**; denied by `gen_asset.py` + contest guard | https://huggingface.co/tencent/Hunyuan3D-2/blob/main/LICENSE |
| **4x-UltraSharp** | Upscale | CC BY-NC-SA 4.0 | Non-commercial | n/a | **blocker if used**; denied | https://openmodeldb.info/models/4x-UltraSharp |
| **Qwen-Image 2.1** (Nexus default image model) | — | qwen-research (non-commercial) | Non-commercial | n/a | **blocker if used**; `gen_asset.py` always passes `--model krea-2-turbo` | https://huggingface.co/Qwen/Qwen-Image-2.1 |

**Owner decision 2026-11-02:** the owner accepted the DINOv3 License ("Yes, I accept", given to the Master
control hub after it summarized the license). Weights stay local only (bundled with Modly's TripoSplat as
`dino_v3_vit_h.safetensors`, never shipped). Duties: include the agreement only if redistributing (§1b.i); name
DINOv3 in any published pipeline write-up, including the dev log (§1b.ii); no military/ITAR/trade-control use
(§1b.v). Meta may amend the terms and continued use counts as acceptance (§8), so re-check before the jam.

Full research notes (per-clause): the side-session notes file `legal-research-2026-11-02.md`,
summarized above. Doc corrections it found: NOTICE.txt's "Built with DINOv3" is optional, not a duty;
knowledge-base open question 21 (UE EULA AI-input limit) is stale since EULA update 22.

## 2. End-to-end pipeline runs

All runs on the CachyOS box, one GPU job at a time, `gpu-preflight` CLEAR before each. Scratch
outputs were deleted afterwards (receipt in §5).

| Pipeline | Command | Output | Result |
|---|---|---|---|
| Image (Krea 2 Turbo) | `python3 scripts/gen_asset.py --name e2e_20261102_crate --prompt "a weathered sci-fi supply crate with glowing teal trim, game prop, plain grey background, centered, full object visible"` (image stage) | `work/generated/e2e_20261102_crate/concept.png` | **PASS**: 82.6 s, exit 0, teen-safe crate on grey. First attempt (before the scope fix) failed at 608 s, see finding 1 |
| 3D (TripoSplat) | same command (3D stage, `--model triposplat`, `NEXUS_THREED_IMAGE_CHECKPOINT=krea-2-turbo`) | `e2e_20261102_crate.glb` (+ `.high.glb`, albedo/AO/normal PNGs, `.glb.provenance.json`) | **PASS**: 206.7 s, exit 0, total 289.3 s. Sidecar records `image_model=krea-2-turbo`, `threed_model=triposplat` |
| 3D → UE import | `UnrealEditor-Cmd ~/Projects/ue-mcp-verify/ue-mcp-verify.uproject -ExecCmds="py <wrapper>"`; the wrapper calls `scripts/ue_import_asset.py`'s `import_asset(glb, "/Game/E2E_20261102/", "E2ECrate", "prop", require_pbr=True)` (scratch project, not this repo: Rule 7(h)) | `/Game/E2E_20261102/e2e_20261102_crate/StaticMeshes/SM_E2ECrate` | **PASS**: convex NDOP18 collision, SmallProp LOD group, texture-bound material found (`--require-pbr` passes; 3 textures + 1 material imported). MI step skipped: no master material in the scratch project |
| Video (Wan 2.2 TI2V-5B) | `nexus-video "a small hovering sci-fi drone with teal lights drifting slowly over a rusty metal floor, game trailer shot" --out work/generated/e2e_20261102_video/clip.mp4 --frames 49 --json` | `clip.mp4` | **PASS**: 231 s, status ok, 864×480, 49 frames @ 24 fps (2.04 s), h264. Into UE as `FileMediaSource` `/Game/E2E_20261102/Video/MS_E2E_Clip`, `validate()` = True |
| Music (ACE-Step 1.5) | `python3 scripts/gen_music.py "tense synthwave, pulsing bass, teal neon, loopable game music" --out work/audio/e2e_20261102_theme.flac --duration 15 --seed 0` | `work/audio/e2e_20261102_theme.flac` | **PASS**: 96.5 s, exit 0, FLAC 48 kHz stereo, 15.0 s; row in `stages/02_build/output/audio-pipeline-log.csv`. UE imports the FLAC directly as `SoundWave` `/Game/E2E_20261102/Audio/S_E2E_Theme`, duration 15.0 s (no WAV conversion needed) |
| SFX (MetaSound, built-in) | in-editor Python: `MetaSoundBuilderSubsystem.create_source_builder` → `add_node_by_class_name(UE.Sine.Audio)` → `connect_nodes` to the audio out → `MetaSoundEditorSubsystem.build_to_asset` → `EditorAssetLibrary.save_asset` | `/Game/E2E_20261102/SFX/MSS_E2E_Zap` | **PASS**: builder result SUCCEEDED, saved `.uasset` 44.6 KB, reloads as `MetaSoundSource`. Proves agents can author SFX graphs without the Fab plugin |

## 3. Findings

1. **GPU jobs stalled because of the Claude desktop app's memory cap (fixed by launch rule).** A user
   drop-in (`~/.config/systemd/user/app-com.anthropic.Claude-.scope.d/`, added 2026-11-01 after oomd killed
   the app) caps the app at MemoryHigh 18G / MemoryMax 20G. Every job started from Claude's shell inherits
   it. Krea needs ~17.5 GB RAM while loading, so ComfyUI ("RAM limited by cgroup to 20480 MB") thrashed at
   "Requested to load Krea2" and `nexus-image` gave up after 608 s. The last good run (2026-10-30) predates
   the cap; ComfyUI itself is unchanged. Fix without touching the owner's cap: start each GPU job (and the
   editor) in its own transient scope:
   `systemd-run --user --scope --unit=megajam-job-$(date +%H%M%S) -p MemoryHigh=26G -p MemoryMax=28G -p MemorySwapMax=8G -- <cmd>`.
   Now in `AGENTS.md` under the one-GPU-workload rule.
2. **`gen_asset.py` hid stage errors (fixed).** `nexus-* --json` prints errors on stdout, but `run_stage`
   printed only stderr, so the 608 s failure showed no reason. It now prints both. Unit tests: 16 OK.
3. **No provenance sidecar for video.** Nexus writes `.provenance.json` for video only on UC2 paths.
   `gen_asset.py` covers image/3D. Until Nexus does it, note video prompts/model in the asset ledger by hand
   (Nexus follow-up).
4. **Epic's SFX Generator is not installed, and the knowledge base said it was.** It lives in the free Fab
   plugin "TechAudioTools Content"; the engine's `Experimental/TechAudioTools` plugin has no Content
   folder (0 `.uasset`). Adding it needs the owner's Fab sign-in. `_config/reference/knowledge-base.md` corrected. The
   built-in MetaSound path works (row above), with Kenney CC0 as the sourced fallback.
5. **Wan clips are in-game media only.** 864×480 is below the 1920×1080 minimum for the Rule 10
   submission video; that video must be a real gameplay capture.
6. **Editor shutdown from scripts.** `-ExecCmds="py <path>,quit"` logs `Cmd: quit` but the editor stays up
   until `timeout` kills it (two 15-minute timeouts here). Ending the script with
   `unreal.SystemLibrary.quit_editor()` exits 0 in about a minute. Added to
   `_config/reference/engine-reference/unreal/python-scripting.md`.
7. **Out of scope, reported:** user unit `lemonade-gate.service` is crash-looping (1,046 restarts on
   2026-11-02) because its script path is a removed Nexus Bot worktree
   (`~/.local/share/workflow-worktrees/nexus-bot-m0/...`). Nexus Bot was retired; the unit should be
   disabled or repointed. Not touched here.
8. Benign warnings seen: "Modly GET /health failed: [Errno 111]" during video (Modly isn't needed for
   video), "VRAM did not return within 15s after unloading", and the editor's HTTP listener failing to bind
   :8000 (port in use) plus failed telemetry posts; none affected results.

## 4. Owner-only actions

- Accept the amended UE EULA (update 22). There is no accept page on the Epic account site (checked
  in a browser 2026-11-02). The accept prompt appears in the Epic Games Launcher (on the Legion Go S),
  or on the next engine or Fab download. The EULA says you aren't required to accept the amended
  agreement, but until you do you can't download the Licensed Technology or use certain Epic services.
- Add the free "TechAudioTools Content" plugin from Fab to the 5.8 engine (needs sign-in), or decide
  to use built-in MetaSound graphs + Kenney CC0 as the SFX path.
- Re-read the Official Rules PDF in a browser on Nov 10 and Nov 15 (Box blocks fetching).
- Claim AI tool credits when Epic publishes the terms.
- butler login + a test push to itch stay with the owner (agents never push to itch).

## 5. Cleanup receipt

Deleted 2026-11-02 after the runs above (regenerable scratch, nothing a gate pins). 28 files, 18.3 MB. `<claude-tmp>` = `/tmp/claude-1000/-home-user-Projects-megajam/`.
The rows in `stages/02_build/output/asset-pipeline-log.csv` and `stages/02_build/output/audio-pipeline-log.csv` are kept as evidence.

| Size (KB) | Path |
|---:|---|
| 0.4 | `<claude-tmp>/af34b828-5aa4-45bd-8a5a-6e13920e77a7/scratchpad/crate.log` |
| 0.2 | `<claude-tmp>/af34b828-5aa4-45bd-8a5a-6e13920e77a7/scratchpad/music.log` |
| 3.3 | `<claude-tmp>/af34b828-5aa4-45bd-8a5a-6e13920e77a7/scratchpad/ue_media_check.py` |
| 0.5 | `<claude-tmp>/af34b828-5aa4-45bd-8a5a-6e13920e77a7/scratchpad/video.log` |
| 373.4 | `<claude-tmp>/af34b828-5aa4-45bd-8a5a-6e13920e77a7/scratchpad/video_frame.png` |
| 424.9 | `<claude-tmp>/cd27aa9e-2288-4385-b671-75ec3b36aa5e/scratchpad/ue_all.log` |
| 419.6 | `<claude-tmp>/cd27aa9e-2288-4385-b671-75ec3b36aa5e/scratchpad/ue_import.log` |
| 383.3 | `<claude-tmp>/cd27aa9e-2288-4385-b671-75ec3b36aa5e/scratchpad/ue_sfx.log` |
| 1221.9 | `~/Projects/megajam/work/audio/e2e_20261102_theme.flac` |
| 2.3 | `~/Projects/megajam/work/audio/e2e_20261102_theme.flac.provenance.json` |
| 1072.4 | `~/Projects/megajam/work/generated/e2e_20261102_crate/concept.png` |
| 1173.5 | `~/Projects/megajam/work/generated/e2e_20261102_crate/e2e_20261102_crate.albedo.png` |
| 238.5 | `~/Projects/megajam/work/generated/e2e_20261102_crate/e2e_20261102_crate.ao.png` |
| 2.6 | `~/Projects/megajam/work/generated/e2e_20261102_crate/e2e_20261102_crate.cpu_tail_report.json` |
| 2749.4 | `~/Projects/megajam/work/generated/e2e_20261102_crate/e2e_20261102_crate.glb` |
| 1.4 | `~/Projects/megajam/work/generated/e2e_20261102_crate/e2e_20261102_crate.glb.provenance.json` |
| 3732.6 | `~/Projects/megajam/work/generated/e2e_20261102_crate/e2e_20261102_crate.high.glb` |
| 1046.1 | `~/Projects/megajam/work/generated/e2e_20261102_crate/e2e_20261102_crate.normal.png` |
| 434.2 | `~/Projects/megajam/work/generated/e2e_20261102_video/clip.mp4` |
| 1498.6 | `~/Projects/ue-mcp-verify/Content/E2E_20261102/Audio/S_E2E_Theme.uasset` |
| 44.6 | `~/Projects/ue-mcp-verify/Content/E2E_20261102/SFX/MSS_E2E_Zap.uasset` |
| 1.5 | `~/Projects/ue-mcp-verify/Content/E2E_20261102/Video/MS_E2E_Clip.uasset` |
| 73.5 | `~/Projects/ue-mcp-verify/Content/E2E_20261102/e2e_20261102_crate/Materials/e2e_20261102_crate_material_0.uasset` |
| 377.7 | `~/Projects/ue-mcp-verify/Content/E2E_20261102/e2e_20261102_crate/StaticMeshes/SM_E2ECrate.uasset` |
| 1390.8 | `~/Projects/ue-mcp-verify/Content/E2E_20261102/e2e_20261102_crate/Textures/e2e_20261102_crate_texture_0.uasset` |
| 1247.3 | `~/Projects/ue-mcp-verify/Content/E2E_20261102/e2e_20261102_crate/Textures/e2e_20261102_crate_texture_1.uasset` |
| 323.4 | `~/Projects/ue-mcp-verify/Content/E2E_20261102/e2e_20261102_crate/Textures/e2e_20261102_crate_texture_2.uasset` |
| 44.6 | `~/Projects/ue-mcp-verify/Saved/Autosaves/Game/E2E_20261102/SFX/MSS_E2E_Zap_Auto1.uasset` |
