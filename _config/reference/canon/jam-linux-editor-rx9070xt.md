---
tier: epic
source: https://forums.unrealengine.com/t/ue-5-8-vulkan-on-linux-triggers-vk-error-device-lost-gpuvm-read-fault-on-amd-rx-9070-xt-with-radv/27307
updated: 2026-11-10
---

# UE 5.8 on Linux with an RX 9070 XT: forum-reported issues

From Epic forum threads summarised in `_config/reference/knowledge-base.md`. These are user reports, not Epic fixes. We ran 5.8.4; the project moved to 5.9 Preview on 2026-11-10 with 5.8.4 as fallback.

## Tip: UE 5.9 (2026-11-10)
- **Why:** the 5.9 Preview editor starts on KDE Wayland only with `SDL_VIDEODRIVER=x11` (observed on our machine); `-sdlvideodriver=x11` should also work (source, not run).
- **How to check:** see `jam-ue59-upgrade`.

## Tip: never use 5.8.0; keep the async-compute settings ready
- **Why:** 5.8.0 on RADV with this GPU gave `VK_ERROR_DEVICE_LOST` crashes in Lumen/Nanite/VSM paths. A reply
  says 5.8.1 seems fixed. A fallback people used: `r.Vulkan.AllowAsyncCompute=0` and `r.RDG.AsyncCompute=0`.
- **How to check:** Help > About in the editor shows the version; keep both CVars in a note to try on a crash.

## Tip: Wayland crash fallback
- **Why:** CachyOS KDE defaults to Wayland; SDL3 explicit-sync errors were reported.
- **How to check:** relaunch with `SDL_VIDEO_DRIVER=x11` in the environment.

## Tip: avoid risky 5.8.4 features (5.8-era; re-check on 5.9)
- **Why:** reports of an `InstancedStruct` assert in StateTree-heavy projects, Mutable failing to load, and Mesh
  Terrain not working in packaged builds.
- **How to check:** skip these, or test one in a scratch project first.

## Tip: after an engine update, wipe caches if the project will not open
- **Why:** deleting `Saved`, `Intermediate` and `DerivedDataCache` fixed an "updated to 5.8.4 and won't open" forum report (topic 2849229).
- **How to check:** reopen the project; the editor rebuilds those folders.

## Tip: Linux builds Linux; Windows builds for Windows
- **Why:** Epic's Linux page only covers Linux as a target; Windows packaging is done on the Legion with the same exact engine version (5.9 Preview is the default now, 5.8.x the fallback). *Superseded (2026-11-10):* "the same exact 5.8.x".
- **How to check:** engine versions match on both machines.
