# AI-generated assets into a finished UE 5.8 game: models, import, rigging, look, audio

Research date: 2026-10-29. Source: a `/deep-research` run (5 search angles, 22 sources fetched, 108 claims
extracted, 25 put through 3-vote adversarial verification: 20 confirmed, 5 refuted; 9 findings survived
synthesis, 8 further claims dropped for budget). Confidence levels and votes below are the run's own.
Sections 4 and 5, and the parent-material correction in section 2, come from a second `/deep-research`
pass the same day (4 researcher notes plus a synthesis report, no 3-vote stage). Its rows carry a
**Basis** column instead of a vote: Epic doc, Epic staff post, user report, third-party, or inference.

**Status: research notes only.** No gameplay, levels or art are built or implied by this note; nothing here
may be built before the contest window opens (Rule 7(h)).

**Takeaway.** The verified route for a solo UE 5.8 entry is: generate props with an image-to-3D model, import
them through Interchange (Nanite or LOD group and collision set at import, scriptable from Python), route
every GLB's materials into one opaque master through the **Predefined glTF Material Library** (the Parent
Material box does nothing for GLB; see section 2), and rig humanoids and retarget them from the UE Mannequin
with the IK Retargeter (also scriptable). The main gap is hardware: none of the checked models (TRELLIS.2-4B,
SF3D, UniRig) documents AMD/ROCm support, and TRELLIS.2 and UniRig are built on CUDA-only dependencies, so
running them on the RX 9070 XT would be an unverified port. This is a documentation gap, not a tested
incompatibility. It does not touch the pipeline we already have: the Modly/Hunyuan3D-2 3D stage behind
`scripts/gen_asset.py` already runs on this machine (`stages/02_build/output/asset-pipeline-log.csv`, four `3d` rows with exit
code 0, about 82–92 s each, 2026-10-28/29). SF3D fits low-poly props best if it can be added. Hunyuan3D 2.1 is licensed for commercial and competition use
for a US entrant, with an AI-content labelling duty. For the look (section 4), cohesion is a material-pipeline
job (glTF library override, a gradient-map master, Custom Primitive Data tint); toon lighting is a layer on
top (5.8's Experimental Substrate Toon BSDF, or a post-process cel pass). The biggest look risk is Linux:
Vulkan device-lost crashes in Lumen/Nanite on this exact GPU in 5.8.0. For audio (section 5), ACE-Step 1.5 is
MIT with commercial use of outputs explicitly allowed and has an official ROCm path; MusicGen/AudioGen
(CC BY-NC weights) are excluded; FLAC imports into 5.8 natively.

## 1. Image/text-to-3D models on AMD

### Verified findings

| Finding | Confidence | Vote | Source |
|---|---|---|---|
| **TRELLIS.2-4B**: one image to a mesh with PBR materials, GLB export (example uses 4096 px textures, not a documented maximum). No stated text input. Requires an NVIDIA GPU with at least 24 GB, CUDA Toolkit (12.4 recommended), verified only on A100/H100. AMD/ROCm never mentioned; flex_gemm, flash_attn, nvdiffrast, cumesh and o_voxel are CUDA-only dependencies. The only non-NVIDIA port found (trellis-mac) targets Apple MPS. | high | 3-0, 3-0 | [model card](https://huggingface.co/microsoft/TRELLIS.2-4B/blob/main/README.md) |
| **SF3D** (Stability AI): textured, UV-unwrapped mesh in about 0.5 s on an H100, export about 150 ms. UVs come from a cube/box projection, not a seam-optimised unwrap, so re-unwrap or rebake before putting assets in a shared atlas. One metallic and one roughness value per object, tangent-space normal map baked into the GLB: suits a flat or stylized master material, poor for multi-material objects. README: about 6 GB VRAM at default settings; lists CUDA, experimental MPS and CPU fallback, no ROCm. Timings are inference only, on an H100. | high | 3-0 x3 | [paper](https://arxiv.org/html/2408.00653v1), [repo](https://github.com/Stability-AI/stable-fast-3d) |
| **Hunyuan3D 2.1 Community License**: commercial and competition use allowed inside its Territory; non-exclusive, royalty-free; a separate Tencent licence only above 1M monthly active users; Tencent claims no rights in outputs, user is solely responsible; **Territory excludes the EU, UK and South Korea**; outputs may not be used to improve other AI models; the Acceptable Use Policy requires AI-generated content to be labelled; outputs provided AS IS. A US-based solo entrant is inside the Territory. | high | 3-0 x3 | [LICENSE (third-party mirror, matched to Tencent's official file)](https://gitserver.onethingai.com/ai-models/Hunyuan3D-2.1/raw/branch/main/LICENSE), [HF card](https://huggingface.co/tencent/Hunyuan3D-2.1) |

### What this means for our pipeline

- `scripts/gen_asset.py` shells out to `nexus-image` then `nexus-3d`; per `stages/00_prep/references/license-check-modly-foundrylab.md`
  the 3D generator behind it (Modly) is Hunyuan3D-2/2mv. The verified licence here is for **2.1**; the repo's
  check covers the **2.0** Community Licence. Same family and similar terms, but the labelling rule and the
  EU/UK/KR territory exclusion above should be confirmed against whichever version Modly actually loads.
- **Update 2026-11-01:** Modly loads Hunyuan3D **2.0** (2mini DiT, Paint v2-0 turbo, Delight v2-0), and the §5(c)
  territory clause covers *outputs*, not just the user's location (the "US-based solo entrant is inside the Territory"
  reading above is wrong for distribution to the EU, UK and South Korea). The owner decided to replace the 3D
  generator with **TripoSplat (MIT)**, pending live ROCm smoke test; not yet wired because `nexus-3d` hardcodes the
  Hunyuan model ids. See `stages/00_prep/references/license-check-modly-foundrylab.md`.
- `_config/reference/NOTICE.txt` already carries Hunyuan3D-2 notice text. The AUP labelling duty is consistent with the
  jam's AI-disclosure requirements (inference; confirm against the Rules).
- `_config/reference/knowledge-base.md` lists TRELLIS.2 as a "strong local, no-cost option". That does not hold on this
  machine as documented: it needs NVIDIA 24 GB CUDA. Treat it as not available locally unless ported.
- SF3D is the lowest-effort fit for low-poly props if it can be made to run here (see next checks).

### Gaps

- No published ROCm/gfx1201 evidence for TRELLIS.2, SF3D or UniRig; all speed and VRAM numbers are
  vendor-reported on NVIDIA H100/A100. Our own local evidence covers only the Modly/Hunyuan3D-2 stage (see
  Takeaway), and it comes from this repo's log, not from this research run.
- Hunyuan3D 2.x and TripoSR: no capability or hardware claims verified (only the 2.1 licence).
- Effective TRELLIS.2 output licence once dependency licences (e.g. nvdiffrast) are counted is unresolved
  (see Refuted).

## 2. Mesh cleanup and Interchange import

### Verified findings

| Finding | Confidence | Vote | Source |
|---|---|---|---|
| UE 5.8 Interchange is format-agnostic, asynchronous, customizable (C++, Blueprint, Python) and usable at runtime. Epic's Python example picks a pipeline per extension (.glb, .gltf, .fbx, .usd): the basis for scripted bulk import (batch use is the run's inference). Runtime import is Blueprint/C++, not editor Python. | high | 3-0 | [Epic: Importing assets using Interchange](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-assets-using-interchange-in-unreal-engine) |
| Static-mesh import options cover most prop clean-up: Build Nanite; LOD Group presets (Small Prop, Large Prop, Foliage, Level Architecture); Import Collision (custom collision, or created if absent); name-prefix collision `UBX_` box, `UCP_` capsule, `USP_` sphere, `UCX_` convex (One Convex Hull Per UCX option); Material Import can create Material Instances of a chosen parent, with no parent set Interchange picks one from `/Interchange/Materials` (Lambert/Phong, Unlit, Metallic/Roughness PBR, Specular/Glossiness PBR). **Corrected below: the chosen parent applies to the generic pipeline only, not glTF/GLB.** | high | 3-0 x3 | [Interchange import reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/interchange-import-reference-in-unreal-engine) |
| **Correction (second pass): for glTF/GLB the Parent Material field is greyed out by design.** Interchange only creates instances of its predefined glTF parents, each input named after the glTF parameter. To use our own master, override **Project Settings > Engine > glTF Settings > Predefined glTF Material Library** (`UGLTFPipelineSettings.MaterialParents`, keys such as `MI_Default_Opaque`, `MI_Default_Opaque_DS`) with instances of the master, or add a custom pipeline after the glTF pipeline that reparents (Epic's suggested route). Epic called the dialog "confusing" and promised a clearer one; not confirmed in 5.8. | high | Epic staff posts (5.6, early 2026), Epic API | [forum 2707236](https://forums.unrealengine.com/t/cannot-select-parent-material-when-importing-glb-files/2707236), [forum 2597367](https://forums.unrealengine.com/t/ue5-6-interchange-gltf-how-interchangegltfpipeline-is-supposed-to-replace-customize-imported-materials/2597367), [UGLTFPipelineSettings](https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/InterchangePipelines/UGLTFPipelineSettings) |
| The master must expose Epic's glTF parameter names: `BaseColorTexture`, `BaseColorFactor`, `NormalTexture`, `MetallicRoughnessTexture`, `MetallicFactor`, `RoughnessFactor`, `EmissiveTexture`, `EmissiveFactor`, `OcclusionTexture`, `AlphaCutoff`, plus `bHas…Texture` flags that look like static switches. Epic publishes the constant names, not their string values, so read the real names off a generated `MI_Default_Opaque` instance before building the master. | medium | Epic API (names); string values unverified | [InterchangeImport API](https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/InterchangeImport?lang=en-US) |
| FBX is no workaround: in 5.7 the FBX Parent Material was skipped in favour of `FBXLegacyPhongSurfaceMaterial` (UE-355242); Epic said the fix needed a full release. Fix in 5.8 not confirmed. | medium | Epic staff post | [forum 2687353](https://forums.unrealengine.com/t/ue5-7-interchangegenericassetpipeline-materialpipeline-are-not-using-parent-material-for-material-creation-on-import-was-working-in-ue5-6/2687353) |
| `unreal.InterchangeGenericMeshPipeline` has read-write settings a script can set (`combine_static_meshes`, `generate_lightmap_u_vs`, `lod_group`, `build_scale3d`, `create_physics_asset`); `fallback_collision_type` NONE turns off generated fallback collision. In 5.8 `import_collision` is deprecated for `collision`, so 5.8 scripts should set `collision`. | medium | 2-1, 2-1 | [5.3 API](https://docs.unrealengine.com/5.3/en-US/PythonAPI/class/InterchangeGenericMeshPipeline.html) (403 on fetch; checked via snippets and the 5.6 copy), [5.8 API (Experimental)](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InterchangeGenericMeshPipeline) |

### What this means for our pipeline

- `gen_asset.py` output is a GLB. Interchange handles GLB with a per-extension pipeline, so a small Python
  import script (driven through the Unreal MCP setup in `ai_agents_mcp_and_asset_pipelines.md`) is a
  plausible final step. Not yet built or tested.
- One shared master is still the cheapest route to a cohesive look (it pairs with SF3D's single
  roughness/metallic per object), but for our GLBs it is wired through the glTF Material Library override,
  not the import dialog. Zero-dependency fallback: import with default materials, then bulk-assign master
  instances with a short Python pass over `StaticMesh.set_material`. The script may be written before the
  window; the master material is art and must be made inside it (Rule 7(h)).
- Property names are Experimental and changed between versions: test in the 5.8 editor before relying on them.

### Gaps

- Whether glTF/GLB or FBX is the safer Interchange route in 5.8 is **unresolved** (the "FBX is Experimental" claim was refuted).
- The exact string values of the glTF parameter names are not published; read them off a generated
  instance on jam day 1.
- Nanite blend-mode support is now covered in section 4 (opaque and masked yes, translucent no).

## 3. Rigging and retargeting

### Verified findings

| Finding | Confidence | Vote | Source |
|---|---|---|---|
| **UniRig** (MIT) predicts skeleton and per-vertex skin weights locally for humans, animals and objects. README requires a CUDA GPU with at least 8 GB VRAM and builds spconv, torch_scatter/torch_cluster and flash_attn against CUDA. ROCm is undocumented; spconv has no official ROCm build, so it needs porting (flash-attn and PyG can be built for ROCm, per the verifier). Skinning quality drops sharply on a wrong skeleton; released checkpoint is Articulation-XL2.0; README points to a successor, SkinTokens. | high | 3-0, 3-0 | [README](https://raw.githubusercontent.com/VAST-AI-Research/UniRig/main/README.md) |
| UE 5.8 **Auto Retarget Chains** matches a skeleton to templates from hierarchy and bone names; exact names not required; spine/neck chains may have more or fewer bones. Only documented template is "Common Biped Skeletons" (UE4/UE5 Mannequin, MetaHumans, Stack O Bot). No match gives an error, inexact match a warning with suggestions. Quadrupeds and unusual creatures need manual chains. | high | 3-0, 3-0 | [Epic: Auto retargeting](https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-retargeting-in-unreal-engine) |
| Retargeting is scriptable in 5.8 Python: create an IK Retargeter via `AssetTools.create_asset(... IKRetargetFactory())`, edit only through `unreal.IKRetargeterController`; batch Mannequin animations onto a generated character with `unreal.IKRetargetBatchOperation.duplicate_and_retarget` (supports search/replace/prefix/suffix renaming and reference remapping). The target still needs its own IK Rig (`unreal.IKRigController`). | high | 3-0, 2-1 | [Epic: Python IK Retargeter](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-python-to-create-and-edit-ik-retargeter-assets-in-unreal-engine) |

### What this means for our pipeline

- `stages/00_prep/references/license-check-modly-foundrylab.md` lists UniRig (via foundry-lab) as the rigging glue and the
  knowledge base calls it the "rigging fallback". Its licence is fine (MIT); its hardware requirement is the
  problem: CUDA-only as documented. Whether foundry-lab already runs it on this box is not established by
  this research.
- Humanoid characters rigged roughly to biped naming can take Mannequin animation via Auto Retarget Chains
  plus the scripted batch retarget. Non-humanoids are out of reach of the verified route.

### Gaps

- Whether UniRig output imports cleanly into UE (file-format claim refuted 1-2).
- AccuRig and the Game Animation Sample / motion matching were searched but no claims survived.
- Skinning quality on stylized low-poly meshes is untested.

## 4. Cohesive stylized look

From the second pass. Cohesion for AI props is mostly a **material-pipeline** problem (section 2's glTF
library override plus one master); toon lighting is a layer on top that can be swapped late.

### Findings

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| UE 5.8 ships **Substrate Toon Shading (Experimental)**: a Substrate Toon BSDF node plus a per-material Toon Profile (ramp diffuse/specular with dithering, hatched self-shadowing, anisotropic specular, GI scale), all light types and Lumen GI. Runs only in Substrate's **Blendable GBuffer (legacy)** mode, a project-wide setting with a full shader recompile. | high | Epic release notes | [UE 5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes) |
| Two open 5.8 Toon bugs, no fix recorded: a Toon Profile set as a Material Instance override stops applying after an editor restart; the "standard" profile shows black stripes at large shadow edges, only partly hidden by lowering Shadow Extinction. Workaround for the first: set the Toon Profile in the parent master, never per instance (ToonProfile properties are per material by API design). | medium | user reports; Epic API | [forum: MI override](https://forums.unrealengine.com/t/ue-5-8-substrate-toon-profile-override-in-material-instance-fails-to-apply-after-restarting-the-editor/2738757), [forum: stripes](https://forums.unrealengine.com/t/ue5-8-substrate-toon-bsdf-black-stripes-bug/2736175), [ToonProfile API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ToonProfile) |
| Post-process cel fallback still works in 5.8: Post Process material reads `PostProcessInput0` and `DiffuseColor`, divides to isolate lighting, quantizes into bands, multiplies back (clamp the divisor). Place it **Before Tonemapping**; read PostProcessInput0, not SceneColor; don't replace the tonemapper (WIP). Translucent surfaces never reach DiffuseColor, so water/VFX need their own stylizing. Whether DiffuseColor is populated under Substrate's default Adaptive GBuffer is undocumented. | high (Epic parts), unknown (Substrate) | Epic doc; third-party tutorial | [Post Process Materials (5.8)](https://dev.epicgames.com/documentation/en-us/unreal-engine/post-process-materials-in-unreal-engine), [Habr tutorial](https://habr.com/post/350172) |
| Lock exposure with **Min EV100 = Max EV100** (or Metering Mode Manual); Exposure Compensation is only an offset. Turning off bloom, motion blur, grain, vignette, CA, flares, DoF and lowering AO is practitioner convention, not Epic guidance. | high | Epic doc | [Auto Exposure (5.8)](https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-exposure-in-unreal-engine) |
| **Lumen Lite (Beta)** in 5.8 uses Irradiance Fields with Probe Occlusion, about twice as fast as Lumen High; enabled by GI and reflection scalability at Medium (`sg.GlobalIlluminationQuality 1`, `sg.ReflectionQuality 1`), reflections fall back to SSR. Keep **Diffuse Color Boost at 1** to limit colour bleed. With Lumen on, lightmaps are hidden and Static lights unsupported. | high | Epic release notes / doc; Tom Looman for the cvars | [release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes), [Tom Looman](https://tomlooman.com/unreal-engine-5-8-performance-highlights/), [Lumen GI](https://dev.epicgames.com/documentation/es-es/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine) |
| **Linux risk on this GPU:** 5.8.0 on the RX 9070 XT with RADV reports `VK_ERROR_DEVICE_LOST` / GPUVM read faults in Lumen screen-probe gather, radiance caches, VSM/Nanite and distance fields. Async compute off stabilised the editor; one user says 5.8.1 fixes it; Epic closed it as a duplicate, so the fix is user-reported only. 5.8.2 RDNA2 reports add a PSO precaching crash (`r.PSOPrecaching=0`). Software ray tracing is the safer Lumen default (inference). Packaged Windows build (Rule 1(b)) is unaffected. | medium | user reports | [forum: RX 9070 XT](https://forums.unrealengine.com/t/ue-5-8-vulkan-on-linux-triggers-vk-error-device-lost-gpuvm-read-fault-on-amd-rx-9070-xt-with-radv/2730749), [forum: PSO](https://forums.unrealengine.com/t/ue-5-8-2-steam-deck-linux-vulkan-compute-pso-precaching-crashes-radv-aco-store-deref/2771073) |
| Nanite in 5.8 supports **Opaque and Masked**, not Translucent; WPO supported but limited. Masked moves meshes to the programmable rasterizer; Epic's Fortnite work found it usually faster to avoid masked and add triangles (5.1-era finding, no newer figures). | high | Epic doc; Epic tech blog | [Nanite (5.8)](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine), [Fortnite Nanite blog](https://www.unrealengine.com/tech-blog/bringing-nanite-to-fortnite-battle-royale-in-chapter-4) |
| **Custom Primitive Data** stores per-object values on the primitive (up to 32 floats) and keeps dynamic instancing: Epic's example drops 25 spheres from 94 draw calls to 46. Works on Nanite meshes in 5.8: not confirmed. | high | Epic doc | [Custom Primitive Data (5.8)](https://dev.epicgames.com/documentation/en-us/unreal-engine/storing-custom-data-in-unreal-engine-materials-per-primitive) |
| **PCG** has been Production-Ready since 5.7. Minimal scatter: PCG Volume → Surface Sampler → transform jitter → Static Mesh Spawner (weighted props) → Bounds Modifier → Self-Pruning → Output. Spawner's `instance_data_packer_type` packs per-instance custom data for tinting (read with PerInstanceCustomData). Generate in editor, not at runtime. Mesh Terrain is Experimental; skip. | high (Production-Ready, API); medium (graph) | Epic news / API; community tutorial | [UE 5.7 news](https://www.unrealengine.com/news/unreal-engine-5-7-is-now-available), [PCGStaticMeshSpawnerSettings](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/PCGStaticMeshSpawnerSettings), [PCG Generation Modes](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-pcg-generation-modes-in-unreal-engine) |

### What this means for our pipeline

- One **opaque** master, reached through the glTF library override, carries the look: sample
  `BaseColorTexture`, posterize luminance, remap through a 1D gradient-map texture so every AI prop shares one
  ramp; global ramp in a Material Parameter Collection; per-object tint from Custom Primitive Data (or PCG
  per-instance data). This gradient-map design is our synthesis, not an Epic recipe. Masked and WPO go behind
  static switches; glass/water get a separate non-Nanite material.
- The swatch-atlas trick from hand-made low-poly packs doesn't fit AI meshes (box-projected / auto UVs); the
  gradient map replaces it, which also answers the old SF3D re-bake question: don't re-bake.
- If the Toon BSDF route is chosen, the same master carries the Toon Profile (sidesteps the MI-override bug).
  Because Blendable GBuffer is project-wide, decide it in a throwaway level in the first in-window hour.
- Lighting tiers, safest first: movable sun + sky light with GI off; Lumen Lite; full Lumen High with
  software RT. Keep these ready for `DefaultEngine.ini` `[SystemSettings]` on the Linux editor:
  `r.Vulkan.AllowAsyncCompute=0`, `r.RDG.AsyncCompute=0`, and `r.PSOPrecaching=0` only if PSO compiles crash.
  Run the latest 5.8.x hotfix.
- **Fallback for bad UVs/topology on AI meshes**: project the base color through a world-aligned
  (triplanar) sample in the master material instead of relying on the mesh's own UVs. Cheaper than
  re-baking or manual UV fixes and hides seams on auto-UV'd AI output; add as a switch in the same
  master material, not a separate pass. Source: external strategy review,
  `_config/reference/research/external-strategies-synthesis.md` item 4.

### Gaps

- Whether post-process `DiffuseColor` is filled under Substrate Adaptive GBuffer (hypothesis: Blendable GBuffer
  keeps it).
- Custom Primitive Data on Nanite meshes in 5.8; how a colour attribute packs into PCG instance floats.
- No UE5-era cost figure for a cel/Sobel pass (UE4 blur outline ≈ 0.8 ms at 1080p on a GTX 980 Ti; expect
  well under 1 ms here, confirm with `ProfileGPU`). Frame cost of async compute off is unmeasured.
- 5.8.1 Vulkan fix is user-reported only.

## 5. AI audio

### Findings

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| **ACE-Step 1.5**: model card lists **MIT** and says the generated music may be used commercially; 10–600 s output. The README's originality check and "clearly disclose AI involvement" sit in a disclaimer, not the licence. | high | model card | [HF ACE-Step 1.5](https://huggingface.co/ACE-Step/Ace-Step1.5), [GitHub](https://github.com/ace-step/ACE-Step-1.5) |
| ACE-Step ROCm: official ROCm launch scripts and `requirements-rocm-linux.txt`; `uv run acestep` silently installs CUDA wheels over ROCm. A repo manual tested on RDNA4 under CachyOS uses Python 3.11, ROCm 6.4 PyTorch wheels, `pt` LM backend, int8 off, no GFX override. INSTALL.md's `HSA_OVERRIDE_GFX_VERSION=11.0.0` hint for the 9070 XT looks wrong (11.0.0 = gfx1100; the card is gfx1201) (inference). No measured gfx1201 run published. | high (docs); inference (override) | repo docs | [INSTALL.md](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md), [ROCm Linux manual](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/ACE-Step1.5-Rocm-Manual-Linux.md) |
| **Stable Audio Open**: Stability AI Community License, commercial use while annual revenue is under US$1M, outputs owned by the user, commercial use requires registering with Stability, "Powered by Stability AI" display on distribution, outputs may not train other foundation models. Best at SFX/field recordings; 1.0 caps at 47 s, Small at 11 s. ROCm undocumented. | high | licence, model card | [LICENSE.md](https://huggingface.co/stabilityai/stable-audio-open-1.0/blob/main/LICENSE.md), [HF 1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0), [HF Small](https://huggingface.co/stabilityai/stable-audio-open-small) |
| **AudioCraft (MusicGen/AudioGen)**: code MIT, **weights CC BY-NC 4.0**; NC covers anything "directed towards commercial advantage or monetary compensation". Exclude from a prize entry. | high | repo, licence text | [GitHub audiocraft](https://github.com/facebookresearch/audiocraft), [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/legalcode.en) |
| Other permissive options: **YuE v1** Apache 2.0, card encourages commercial use with credit; **DiffRhythm 1.2** "code and DiT weights" Apache 2.0, up to 285 s, ≥ 8 GB VRAM, VAE terms unverified. ROCm undocumented for both. | medium | model card / repo | [HF YuE](https://huggingface.co/m-a-p/YuE-s1-7B-anneal-en-cot), [GitHub DiffRhythm](https://github.com/ASLP-lab/DiffRhythm) |
| UE 5.8 imports **`.wav`, `.ogg`, `.flac`, `.aif`, `.opus`, `.mp3`**, any sample rate, mono to 7.1; stored as 16-bit, 24-bit is **not dithered** (Epic recommends 16-bit input). ACE-Step 1.5 output is 48 kHz per third-party docs only. | high (Epic); low (48 kHz) | Epic doc; third-party | [Importing Audio Files](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-audio-files), [ComfyUI audio docs](https://www.mintlify.com/Comfy-Org/ComfyUI/models/audio-models) |
| Batch import: `unreal.AssetImportTask` (`automated`, `save`, `replace_existing`) via `import_asset_tasks()`; when Interchange handles the file, **`destination_name` is ignored**. 5.8 has Interchange WAV/OPUS translators and a Generic Audio Pipeline; whether FLAC goes through Interchange or the legacy factory is unconfirmed. SoundWave settings (`sound_asset_compression_type`, `compression_quality`, `loading_behavior`, `looping`, `sound_class_object`, `attenuation_settings`) are scriptable. | high (API); unconfirmed (FLAC route) | Epic API | [AssetImportTask](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetImportTask), [SoundWave](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SoundWave) |
| Epic's 5.8 audio overview calls **Sound Cues "legacy"**; MetaSounds replace them (no removal announced). MetaSound Presets inherit base-graph edits. Volume sliders: **Audio Modulation** plugin (off by default) Control Buses and Bus Mixes. MetaSound node names are from 5.1–5.5 knowledge. | high | Epic doc | [Audio in UE5](https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-in-unreal-engine-5), [MetaSounds](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-the-next-generation-sound-sources-in-unreal-engine), [Audio Modulation](https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-modulation-overview-in-unreal-engine) |
| Epic's **SFX Generator** is a procedural "SoundGenerator" MetaSound in the free Fab plugin **TechAudioTools Content** (released 2026-01-27 for 5.7; Epic said updates start with 5.8, a 5.8 build not confirmed). Needs the **TechAudioTools** (Experimental) and **UMG Viewmodel** plugins; aimed at sci-fi and abstract sounds; parameters randomized then recorded to a SoundWave; Fab Standard License. | medium | Epic forum post, Fab listing | [Epic announcement](https://forums.unrealengine.com/t/power-up-your-metasound-workflows-with-techaudiotools-content/2695319), [Fab](https://www.fab.com/listings/d44cbd49-7691-4f82-abdb-6428c78508f6) |

### What this means for our pipeline

- The existing choice holds: **ACE-Step 1.5 for music** (`scripts/gen_music.py`), Stable Audio Open only as an
  optional SFX supplement, SFX Generator for UI blips/zaps/abstract ambience. MusicGen/AudioGen stay out.
- Treat the entry as commercial (cash prizes, Epic's publicity licence under Rules 2/15(b)). Costs nothing for
  MIT/Apache models; for Stable Audio Open it means registering and crediting "Powered by Stability AI".
- One **credits block** (each model, its licence, what it made) in the game credits and the dev log covers
  ACE-Step's disclosure request, Hunyuan3D's AI-labelling duty and the Glass Box log (Rule 10). AI output is
  not a "sourced asset" (Rule 15(c)), so it does not go in the sourced-asset list; Fab/library sounds do.
  Disclosed AI use is context only for scoring (Rule 9). All in-game audio must be English (Rule 7(i)).
- `gen_music.py`'s FLAC imports as-is. Convert to 16-bit with ffmpeg before import (avoids undithered 24-bit
  truncation and covers 32-bit float), keep source audio outside `Content/`, and rename files on disk (since
  `destination_name` may be ignored). Use MetaSound Sources, not Sound Cues, for new content; bake SFX
  Generator output to plain SoundWaves so the Windows build doesn't depend on an Experimental plugin.

### Gaps

- FLAC route (Interchange vs legacy factory) and 5.8 MetaSound node names.
- Whether a 5.8 build of TechAudioTools Content exists on Fab.
- ACE-Step output sample rate (48 kHz) is third-party only; no measured gfx1201 ACE-Step run published.
- The Rules PDF's IP warranty/indemnity wording was summarised from the project digest, not quoted.

## Refuted or dropped claims

| Claim | Vote | Note |
|---|---|---|
| TRELLIS.2-4B is MIT, so permissive enough for commercial/competition use | 0-3 | Model card states MIT, but the "permissive enough" conclusion was refuted, most likely over dependency licences (e.g. nvdiffrast under NVIDIA's own licence). Check before shipping any TRELLIS output. |
| Interchange FBX is Experimental behind a flag, so glTF is safer in 5.8 | 0-3 | Depends on the page's scope (may only cover runtime/Import Into Level). Not established. |
| Interchange mesh pipeline `build_nanite` only works with simple opaque materials | 0-3 | Refuted; leave Nanite-with-stylized-materials as untested. |
| UniRig accepts .obj/.fbx/.glb/.vrm and writes .fbx and rigged .glb, both importable into Unreal | 1-2 | Not established. |
| In 5.8 Auto Retarget Chains removes manual chain setup | 1-2 | Matching is best effort. |

8 further claims were dropped for budget, not refuted. The existing knowledge-base entry that TRELLIS.2 is
MIT and a "strong local, no-cost option" sits uneasily with the first row.

## Next checks before Nov 11

1. Run `gpu-preflight`, then test whether SF3D runs under ROCm on the RX 9070 XT (gfx1201): install, one
   image, time, VRAM, output GLB. Record in `stages/02_build/output/asset-pipeline-log.csv`.
2. (Answered 2026-11-01: Modly loads 2.0; Hunyuan is being replaced.) Confirm which Hunyuan3D version Modly loads, and re-read that version's licence (2.0 vs 2.1) for the
   labelling duty and territory clause; update `stages/00_prep/references/license-check-modly-foundrylab.md` if they differ.
3. Check whether foundry-lab's UniRig actually runs on this box (ROCm build of spconv) or only on CPU/other.
4. Import one existing generated GLB through Interchange in the 5.8 editor via Python: set `collision`
   (not `import_collision`), `lod_group` and Build Nanite; note the property names that work. Read the
   parameter names off the generated `MI_Default_Opaque` instance (show engine and plugin content).
5. Point the Predefined glTF Material Library's opaque keys at instances of a throwaway (not shipped) master
   that exposes those names, re-import, and confirm textures connect. Also check Custom Primitive Data on a
   Nanite mesh and whether post-process `DiffuseColor` is filled under the project's Substrate GBuffer mode.
6. Retarget one Mannequin animation onto a test humanoid using Auto Retarget Chains and
   `duplicate_and_retarget`; log failures.
7. Import a `gen_music.py` FLAC into 5.8 (converted to 16-bit), note whether Interchange or the legacy
   factory takes it and its sample rate. Check Fab for a 5.8 build of TechAudioTools Content.
8. Re-read the Rules PDF's IP warranty and indemnity wording (the digest paraphrases it), and draft the
   credits block (model, licence, what it made) for game credits and the dev log.
9. On the Linux 5.8.x editor, open a Lumen + Nanite test level on the RX 9070 XT; if it device-losts, apply
   the async-compute cvars from section 4 and record which hotfix was installed.
10. Re-check model repos and licences on 2026-11-11; they may change before the window.

## Caveats from the run

Sections 4 and 5 rest on a second pass without the 3-vote stage; several of their rows are user reports or
Epic staff forum posts, labelled in the Basis column. Several Epic pages (parts of the 5.8 release notes, PCG
overview, Sound Waves) did not render, so some details come from search snippets or third-party copies. All
verification was documentation-level; no one tested hardware. One Hunyuan source was a third-party mirror (matched to the official file). Epic labels the
Python API docs Experimental. Everything was checked on 2026-10-29.
