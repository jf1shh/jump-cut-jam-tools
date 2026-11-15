# Licence audit: the whole MegaJam asset chain — 2026-11-07

Ticket T-20261107-08. Owner ask: make sure everything installed (ComfyUI and the rest) is licensed
properly, now that the jam is not local-only. Docs and config only; nothing was downloaded,
installed or run. Not legal advice. Machine-readable twin: `config/asset-licenses.json`.

Builds on `stages/00_prep/references/legal-audit-2026-11-02.md` and `stages/00_prep/references/license-check-modly-foundrylab.md` (not redone).
Those rows are carried over as "2026-11-02". New reads are dated 2026-11-07.

**Setting:** solo US entrant, cash-prize contest, free worldwide itch.io download, Epic gets a
worldwide publicity licence (Rule 15(b)). So "worldwide" and "outputs shown anywhere" matter.

## Headline

1. **Installed and "no":** Qwen-Image 2.1 (GGUF + its VAE), both Hunyuan3D checkpoints in ComfyUI
   (`hunyuan3d-dit-v2_fp16`, `hunyuan3d-dit-v2-mv-turbo_fp16`), the Modly extensions
   `hunyuan3d-mini` and `hunyuan3d-paint`, and the Qwen prompt-enhancer node. They are in
   `config/asset-licenses.json` as `no` with `match` patterns, so the guard can block them.
2. **New finding:** Hunyuan3D **2mini** and **2.1** carry the same EU/UK/South Korea exclusion as 2.0.
   Switching Hunyuan version does not fix it.
3. **New finding:** `nexus-upscale` defaults to a chain called `feral` (BCGone + UniversalUpscaler).
   Neither has a clearly confirmed commercial licence, and Real-ESRGAN (the one the rules name) is
   now installed (the hub checked the sha256). Never run `nexus-upscale` without `--chain realesrgan`.
4. **Candidate trap:** TRELLIS.2 is MIT, but its default pipeline loads Bria RMBG-2.0 (CC BY-NC).
5. **Cloud:** free tiers of Meshy, Tripo, ElevenLabs and Suno are credit-only or non-commercial.
   Use a paid plan whose terms allow commercial output, and keep the terms gate. The jam is not
   local-only (owner 2026-11-07): any option the contest rules allow is open. Auto order is speed-first
   (megajam PR #94: Meshy first when configured, TripoSplat fallback).
6. Everything in the current Krea → TripoSplat → Wan → ACE-Step chain stays **ok**.

## 1. Installed on this machine

ComfyUI: `~/.nexus/comfyui` (GPL-3.0). Modly: `~/Documents/Modly`. Blender 5.2.3 with two add-ons.

| Item (file / version) | Code licence | Weights licence | Outputs / commercial | Duty, limits, flags | Verdict | Source (read) |
|---|---|---|---|---|---|---|
| Krea 2 Turbo `krea2_turbo_fp8_scaled` | n/a | Krea 2 Community | Own outputs; commercial < $1M revenue | Filters on; AUP binds outputs | ok | krea.ai/krea-2-licensing (11-02) |
| Qwen3-VL-4B encoder `qwen3vl_4b_fp8_scaled` | n/a | Apache-2.0 | OK | none | ok | HF Qwen/Qwen3-VL-4B-Instruct (11-02) |
| `qwen_image_vae` (243 MB) | n/a | Apache-2.0 | OK | not the 2.1 VAE | ok | HF Qwen/Qwen-Image (11-02) |
| **Qwen-Image 2.1** `qwen-image-2.1-UC-Q4_K_M.gguf`, `qwen_image_2.1_vae_bf16` | n/a | qwen-research | **Non-commercial** | NC flag | **no** | HF Qwen-Image-2.1 LICENSE (11-02) |
| `qwen3vl_8b_int8_convrot` (8.8 GB) | n/a | Qwen3-VL base is Apache-2.0; this repack's source unknown | unknown | looks like the Qwen-Image 2.1 encoder | unclear | not found in repo (11-07) |
| TripoSplat (Modly ext) | MIT | MIT | OK | MIT notice only if shipped | ok | HF VAST-AI/TripoSplat (11-02) |
| DINOv3 `dino_v3_vit_h` | n/a | DINOv3 Licence | No output clause; no military use | Owner accepted 11-02; name it in dev log | ok-with-credit | Meta LICENSE.md (11-02) |
| FLUX.2 VAE | n/a | Apache-2.0 | OK | none | ok | HF FLUX.2-klein-4B (11-02) |
| BiRefNet `birefnet.safetensors` | MIT | MIT | OK | none | ok | HF ZhengPeng7/BiRefNet (11-02) |
| Wan 2.2 TI2V-5B + `wan2.2_vae` | Apache-2.0 | Apache-2.0 | OK | In-game media only (864×480) | ok | HF Wan-AI (11-02) |
| umt5-xxl fp8 | n/a | Apache-2.0 | OK | none | ok | HF google/umt5-xxl (11-02) |
| ACE-Step 1.5 (turbo, `ace_1.5_vae`, Qwen 0.6B/1.7B LM) | MIT | MIT | Commercial OK | Disclose AI music | ok-with-credit | HF ACE-Step (11-02) |
| SDXL base 1.0 `sd_xl_base_1.0` | n/a | CreativeML Open RAIL++-M | Licensor claims no output rights; no cap, no territory | Use bans (Attachment A); flow-down only if redistributing | ok (fallback) | HF LICENSE.md (11-07) |
| SD 1.5 `v1-5-pruned-emaonly` | n/a | CreativeML OpenRAIL-M | Same | Training data has adult material; weak quality | ok (not recommended) | CompVis licence.txt (11-07) |
| **Hunyuan3D 2.0** `hunyuan3d-dit-v2_fp16`, `-v2-mv-turbo_fp16` | Tencent | Tencent 3D 2.0 Community | Tencent claims no output rights, **but Territory excludes EU/UK/KR (s5c)** | itch.io reaches them | **no** | HF tencent/Hunyuan3D-2 LICENSE (11-02) |
| **Hunyuan3D 2mini** (Modly `hunyuan3d-mini`) | Tencent | Same 2.0 licence, dated 21 Jan 2025 | Same territory clause | same | **no** | HF Hunyuan3D-2mini LICENSE (11-07) |
| **Hunyuan3D Paint/Delight** (Modly `hunyuan3d-paint`) | Tencent | Tencent 2.0 | Same | same | **no** | as above (11-07) |
| 1x BCGone-DetailedV2 | n/a | WTFPL listed (author Mutin Choler); commercial tick unreadable | probably OK | In the default `feral` chain | unclear | openmodeldb.info/models/1x-BCGone-DetailedV2-40-60 (11-07) |
| 4x UniversalUpscaler-Detailed | n/a | Not found on OpenModelDB; sibling V2-Sharp is WTFPL | unknown | In the default `feral` chain | unclear | openmodeldb.info (404) (11-07) |
| MoGe-2 vitl-normal | MIT (+ DINOv2 Apache-2.0) | MIT (HF metadata, card empty) | No output clause | none | ok | HF Ruicheng/moge-2-vitl-normal (11-07) |
| ComfyUI | GPL-3.0 | n/a | Tool licence does not reach outputs | do not bundle | ok | local LICENSE (11-07) |
| ComfyUI-GGUF 2.0.0 | Apache-2.0 | n/a | n/a | Weights keep own licence | ok | local LICENSE (11-07) |
| ComfyUI-VideoHelperSuite 1.7.9 | GPL-3.0 | n/a | n/a | do not bundle node code | ok | local LICENSE (11-07) |
| comfyui-obvpm 0.2.9 | GPL-3.0 | n/a | n/a | utility nodes | ok | local LICENSE (11-07) |
| **ComfyUI-Qwen-Image-2.1-PromptEnhancer-MTP 1.2.2** | MIT | drives Qwen 2.1 | n/a | Only useful for the NC model | **no** (don't use) | local LICENSE (11-07) |
| Modly built-ins `mesh-exporter/optimizer/remesher/repair/smoother` | not read | none | geometry only | licence files unread | unclear | `~/.config/Modly/builtin-extensions` (11-07) |
| UniRig (foundry-lab) | MIT | MIT (HF metadata) | No output clause | training data unread | ok | github VAST-AI-Research/UniRig (11-07) |
| autoremesher ≥ 1.0 | MIT | n/a | n/a | not pre-1.0 | ok | 11-02 audit |
| Blender 5.2.3 | GPL | n/a | Output is yours | none | ok | blender.org (11-07) |
| Blender add-on `io_scene_psk_psa` 9.1.2 | GPL-3.0+ | n/a | n/a | UC2 format tool: not for MegaJam (Rule 8) | no (unused) | add-on manifest (11-07) |
| Blender add-on `mcp` 1.0.0 | GPL-3.0+ | n/a | n/a | tool only | ok | add-on manifest (11-07) |
| Real-ESRGAN x4plus | BSD-3 | no stated limit | OK | installed (hub, sha256 matches) | ok | github xinntao (11-02) |
| 4x-UltraSharp | n/a | CC BY-NC-SA 4.0 | Non-commercial | not installed | **no** | OpenModelDB (11-02) |

## 2. Candidates (not installed)

| Candidate | Code / weights | Output, territory | Flags | Verdict |
|---|---|---|---|---|
| TRELLIS.2 (microsoft) | MIT / MIT | No output clause | Default pipeline loads **Bria RMBG-2.0 (CC BY-NC)**; DINOv3 (accepted); nvdiffrast/nvdiffrec licences unread | unclear: ok only with BiRefNet swapped in |
| TripoSG / TripoSF (VAST-AI) | MIT / MIT | No output clause | Dependency licences unread | ok (candidate) |
| Step1X-3D | Apache-2.0 / Apache-2.0 | None | Texture stage SDXL-based; reuses Hunyuan 2.0 rasterizer code | unclear |
| Hunyuan3D 2.1 | Tencent | Tencent claims no output rights; territory EU/UK/KR excluded; cap > 1M MAU | Same trap | no |
| UniRig | MIT / MIT | none | HF card holds the skeleton and skin parts only | ok |

Sources (all read 2026-11-07): raw.githubusercontent.com `microsoft/TRELLIS.2`, `VAST-AI-Research/TripoSG`,
`TripoSF`, `stepfun-ai/Step1X-3D`; HF `microsoft/TRELLIS.2-4B` (+ `pipeline.json`), `briaai/RMBG-2.0`,
`tencent/Hunyuan3D-2.1/raw/main/LICENSE`, `tencent/Hunyuan3D-2mini/raw/main/LICENSE`.
Note: these were summarised by a small fetch model, not verbatim; re-read the two Tencent licences
and RMBG-2.0 by eye before relying on "no".

## 3. Cloud providers

| Provider | Output ownership | Free vs paid | Credit duty | Verdict |
|---|---|---|---|---|
| GPT image (OpenAI) | Assigned to user (Dec 2024 mirror; live page 403) | Plan quota only | none found | ok (concept art; owner approved 11-06) |
| Grok Imagine (xAI) | "You own the Outputs" (secondhand); API terms differ | API billed | Some versions require attributing the service | unclear (gated by `XAI_TERMS_REVIEWED`) |
| Meshy | Owner owns output | Free = CC BY 4.0; paid = private commercial | Free: visible credit | ok-with-credit (paid is cleaner) |
| Tripo | Free-tier outputs retained by Tripo / public CC BY (excerpt) | Commercial needs paid | unread | unclear |
| Stability AI | Owner owns output | Community licence free < $1M, registration | "Powered by Stability AI" if distributing the Materials | ok-with-credit |
| ElevenLabs | User keeps output | **Free = non-commercial only** | none found | no on free; ok on paid |
| Suno | Paid: output assigned; free: personal only | Paid needed; keep receipts; no watermark removal | may be identified as Suno | no on free |
| Udio | Personal non-commercial (excerpt) | no downloads | n/a | no |

Primary pages read: docs.meshy.ai/en/webapp/pricing, stability.ai/license, stability.ai/community-license-agreement,
elevenlabs.io/terms-of-use, suno.com/terms (all 2026-11-07). 403 or 404: openai.com terms, x.ai terms,
tripo3d.ai terms, meshy.ai/terms.

## 4a. Owner answers (2026-11-07, relayed by the hub)

- Upscaler: **Real-ESRGAN x4plus**. The hub installed `RealESRGAN_x4plus.safetensors` (sha256 matches). Always run `nexus-upscale ... --chain realesrgan`; with no chain it runs the unclear `feral` pair, and the allowlist entry `nexus-upscale-default-feral-chain` denies that.
- The owner read the OpenAI, xAI, Tripo and Meshy terms on 2026-11-07. The outcome is not recorded here; the Grok and Tripo entries stay `unclear` until it is written down.
- Hunyuan3D stays banned (all versions).

## 4. Unclear — owner list (items 1–3 answered above)

1. **Upscale default.** Answered: the owner chose Real-ESRGAN x4plus (BSD-3), now installed. Always pass
   `--chain realesrgan` (or `--model realesrgan`). With no chain, `nexus-upscale` runs the unconfirmed
   `feral` pair and the allowlist denies it; `--model` beats `--chain`, so no other model may appear.
2. **Provider terms.** Answered (owner 2026-11-07): OpenAI, xAI, Tripo and Meshy terms read; the
   `*_TERMS_REVIEWED` dates are set in `~/.config/megajam.env`.
3. **Hunyuan territory.** Our reading is that a worldwide itch.io download breaks s5(c). That is a legal
   judgement; a lawyer could say otherwise, but the no-Hunyuan rule is the cheap safe path.
4. **TRELLIS.2.** Worth trying only if the owner wants a stronger 3D model: swap RMBG-2.0 for BiRefNet and
   read the nvdiffrast/nvdiffrec licences first. Not before the jam without a decision.
5. **`qwen3vl_8b_int8_convrot`.** Where did it come from? Delete from the pick list if it was fetched for Qwen-Image 2.1.
6. **Modly built-in mesh extensions.** Licence files unread; low risk (geometry only).
7. **Step1X-3D texture weights** may inherit SDXL RAIL terms. Skip unless needed.
8. **Paid cloud plans.** ElevenLabs and Suno need a paid plan for a prize entry. Say if you want either.
9. **Tencent and Meta may amend terms.** Re-check DINOv3 and Krea pages Nov 10.

## 5. Recommended optimised chain (all `ok`)

- Concept image: Krea 2 Turbo local → fallback GPT image (owner-approved) → SDXL.
- Cut-out: BiRefNet (never RMBG-2.0).
- 3D: TripoSplat (local, albedo only; no PBR) plus terms-gated cloud 3D (Meshy, Tripo) under the owner's 2026-11-07 policy. Hunyuan3D stays banned. TripoSG/TripoSF is the only other MIT 3D candidate.
- Rig/remesh: UniRig, autoremesher ≥ 1.0, Blender.
- Upscale: Real-ESRGAN x4plus (installed; always pass `--chain realesrgan`).
- Video (in-game only): Wan 2.2 TI2V-5B.
- Music: ACE-Step 1.5. SFX: MetaSound + Kenney CC0.
- Depth/normal helper: MoGe-2.

## 6. Using the allowlist

`config/asset-licenses.json` has `default_verdict_for_unknown: "no"`. A guard should run each entry's
`match` regex over the command and the file names it touches, deny `no` and `unclear`, and collect
`credit_text` from `ok-with-credit` entries into the credits file. `scripts/hooks/contest_guard.py` is not
edited by this ticket (not claimed); wiring is a follow-up.
