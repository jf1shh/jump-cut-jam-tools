# License check: Modly / foundry-lab asset pipeline

**Verdict:** NEEDS ATTRIBUTION for Hunyuan3D-2 output (Notice file required if any 3D asset is
distributed outside a hosted service; "Powered by Tencent Hunyuan" marking is encouraged, not
mandatory) + **ACTION NEEDED** on the image-gen default: Nexus's default image model, Qwen-Image 2.1,
is licensed non-commercial-only and cannot legally back a prize-money jam entry (Rule 15(b),
publicity/commercial use). Switch the default to Krea 2 Turbo (commercial OK under $1M revenue) or
SDXL (RAIL++-M, commercial OK with use-based restrictions) before any art ships in the real entry.

Scope: every generative model and pipeline tool behind Nexus's local asset pipeline (Modly for 3D,
foundry-lab's rigging/remeshing glue, and the image-gen models Nexus can select), checked for
compatibility with a solo US entrant submitting a cash-prize UE 5.8 entry under the MegaJam official
rules (Rule 15(b): entry must not infringe any third party's IP or publicity rights).

| Tool / model | License | Commercial OK? | Restrictions | Compatible with 15(b)? | Source |
|---|---|---|---|---|---|
| Modly (nexus mesh server) | N/A — delegates to Hunyuan3D-2/2mv, vendors no model of its own | — | — | — | `~/Projects/nexus/CONTEXT.md` |
| UniRig (foundry-lab rigging glue) | MIT (VAST-AI-Research, 2025) | Yes | None | Yes | `~/Projects/foundry-lab/UniRig/LICENSE` |
| autoremesher (foundry-lab remeshing glue) | MIT (Dust3D Project, 2026) | Yes | None | Yes | `~/Projects/foundry-lab/autoremesher/LICENSE` |
| Hunyuan3D-2 / 2mv (Tencent, the real 3D generator behind Modly) | Tencent Hunyuan 3D 2.0 Community License | Yes, free under 1M MAU | Mandatory Notice text file on any distribution to third parties outside a hosted service: *"Tencent Hunyuan 3D 2.0 is licensed under the Tencent Hunyuan 3D 2.0 Community License Agreement, Copyright © 2025 Tencent. All Rights Reserved."* "Powered by Tencent Hunyuan" product marking is **encouraged**, not mandatory. Must disclose actual provider identity and that Tencent isn't affiliated/endorsing. | Yes, once the Notice file ships with the build | https://huggingface.co/tencent/Hunyuan3D-2/blob/main/LICENSE |
| **Qwen-Image 2.1 (Nexus's current default image model)** | **Qwen Research License ("qwen-research")** | **No — non-commercial only** | *"You shall not use the Materials for any commercial purpose without obtaining a separate commercial license from us"* — request via model-business@notice.qwencloud.com | **No, as currently defaulted** | https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE |
| Krea 2 Turbo (optional Nexus image model, `Comfy-Org/Krea-2`) | Krea 2 Community License | Yes, under $1M annual company revenue | Notice file + "Krea" name prefix on any distributed derivative model; content-filter + Acceptable Use Policy compliance | Yes | https://www.krea.ai/krea-2-licensing |
| SDXL / SD 1.5 (optional Nexus image model) | CreativeML Open RAIL++-M | Yes | Use-based restrictions only (no unlawful/harmful-use categories in Attachment A); no revenue cap, no Notice-file requirement | Yes | https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 |
| Wan 2.2 (optional Nexus video model) | Apache 2.0 | Yes | None beyond standard Apache 2.0 notice/modification terms | Yes | https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_repackaged |

## What has to happen before jam assets ship

1. **Switch the asset pipeline's default image model off Qwen-Image 2.1** before generating any art
   intended for the real entry (`~/Projects/nexus/README.md` line ~306/506 and whatever
   `NEXUS_*` env var selects the default — not yet located exactly; grep for `qwen` in
   `~/Projects/nexus/` config/env files). Krea 2 Turbo is the cleanest swap (already wired as
   `krea-2-turbo`, see `docs/sdd/krea-2-turbo.md`); a solo jam entrant is nowhere near the $1M
   revenue cap. SDXL is the fallback if Krea's VRAM cost (14.2 GiB peak) is a problem during jam week.
   Qwen-Image 2.1 can stay available for throwaway exploration/concept art that never ships in the
   zipped build, since that's not "commercial use" of the output — but nothing Qwen-rendered should
   end up in the submitted game.
2. **Ship the Notice text file** (`_config/reference/NOTICE.txt`, now TripoSplat/BiRefNet/DINOv3/FLUX.2-VAE; the Hunyuan notice is dropped because no Hunyuan3D-2-derived
   mesh is in the submitted entry, since the zip is a distribution to a third party (Epic/the judges)
   outside a hosted service. One `NOTICE.txt` or `THIRD_PARTY_LICENSES.txt` in the packaged build
   covers it.
3. UniRig, autoremesher, Wan 2.2, SDXL, and Krea 2 Turbo (under the revenue cap) need no further
   action — all read against license files and found commercial-clean. The Hunyuan row above is superseded by the section on the territory clause below.

## Notes

- Krea 2 Turbo in this pipeline is `Comfy-Org/Krea-2` (Krea's own license,
  krea.ai/krea-2-licensing) — not to be confused with `black-forest-labs/FLUX.1-krea-dev`, a
  different, non-commercial-only Krea collaboration model that Nexus does not use.
- The rows above were read against each project's license file or page (HuggingFace LICENSE blob,
  krea.ai licensing page, or local `LICENSE` file in the repo). This check was incomplete: it missed
  the Hunyuan §5(c) territory clause below and the AUP labelling duty, so do not read it as a full
  primary-source verification. The 2026-11-01 audit found the gaps.
- 2026-11-01: the Hunyuan version Modly loads is 2.0 (2mini DiT, Paint v2-0 turbo, Delight v2-0).

## Hunyuan territory clause (§5(c)): replaced by TripoSplat

Tencent Hunyuan 3D 2.0 Community License §5(c) says you must not use, reproduce, modify, distribute or
display the model's Output outside the Territory (worldwide excluding the European Union, United
Kingdom and South Korea); the AUP also bars use outside it. A public itch.io download and Epic's
worldwide publicity license under Rule 15(b) both distribute and display Hunyuan-made meshes and
textures there. The table above read the Territory as the user's location; the clause covers outputs.
AUP item 12 also requires conspicuous "machine generated" labelling of public content.

**Owner decision 2026-11-01:** replace Hunyuan3D 2.0 with TripoSplat (`VAST-AI/TripoSplat`, MIT, Modly extension `triposplat`). Why: Tencent license §5(c) restricts use and display of Outputs outside its Territory (EU, UK and South Korea excluded), and a public itch.io download plus Epic's worldwide publicity license (Rule 15(b)) reach those regions. TripoSplat outputs a watertight mesh GLB, UV-baked albedo with `--model triposplat` (texture "Baked 2K"); no PBR maps. **Status: wired 2026-11-01 as `nexus-3d --model triposplat` (jf1shh/nexus PR 273; megajam contest guard allows only that form). Live ROCm smoke test result is in the PR description / hub notes.** Dependency licenses are checked below: BiRefNet MIT, FLUX.2 VAE Apache-2.0, DINOv3 License (no territory, revenue or output restriction; VAST's HF repo ships the DINOv3 weights without the DINOv3 Agreement text, so `_config/reference/NOTICE.txt` carries "Built with DINOv3").

| Tool / model | License | Commercial OK? | Notes |
|---|---|---|---|
| TripoSplat (`VAST-AI/TripoSplat`, Modly extension) | MIT | Yes | UV-baked albedo GLB (code MIT, (c) 2026 VAST); deps: BiRefNet MIT (Copyright (c) 2024 ZhengPeng), DINOv3 License (Meta), FLUX.2 VAE Apache-2.0; Modly extension MIT |
