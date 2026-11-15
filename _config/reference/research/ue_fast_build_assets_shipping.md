# UE fast-build, free assets, and shipping playbook for the 2026 Epic AI MegaJam (solo, 4 days)

Research date: 2026-10-27. Scope: Unreal Engine features, templates, free assets, packaging/shipping, Linux-host constraints, version control, and jam scheduling for a solo regular-UE (not UEFN) entry. Fetch failures and items I could not verify are flagged. Where I rely on prior (training) knowledge and could not re-verify it this session, it is marked **[unverified]** and kept out of Cited Findings.

---

## 0. Current engine version and jam ground rules (context for every other section)

### Takeaway
UE 5.8 (released June 17, 2026) is current and is likely the last UE5.x release; it is the version to use. The 2026 jam requires a packaged **development build** for Windows/macOS/Android/iOS. The 2026 rules page itself could not be fetched, so the "<1 GB zip" and asset-scoring rules come from the 2023 MegaJam and need re-checking against the 2026 Official Rules.

### Cited Findings
- UE 5.8 was released June 17, 2026 at State of Unreal. Gamefromscratch says 5.8 "will likely be the final UE5.x release," with first UE6 previews "late 2027ish." — [GameFromScratch](https://gamefromscratch.com/unreal-engine-5-8-released/)
- UE 5.7 was released November 12, 2025. In 5.7: PCG became **Production-Ready** (with a PCG Editor Mode, faster GPU compute, and Polygon2D operators); Nanite Foliage was **Experimental**; MegaLights moved from Experimental to **Beta**; Substrate became **Production-Ready**. 5.7 also added an in-editor AI Assistant, MetaHuman Linux/macOS plugin support, a first Experimental Procedural Vegetation Editor, and an interactive Getting Started sample. — [Unreal Engine news: 5.7 is now available](https://www2.unrealengine.com/news/unreal-engine-5-7-is-now-available)
- 5.8 headline features:
  - MegaLights is **Production Ready**.
  - Lumen Lite (Beta) is a medium-quality GI mode using irradiance fields, "twice as fast as Lumen high quality."
  - The Procedural Vegetation Editor (Experimental) authors Nanite-foliage vegetation.
  - PCG gains manual overrides, complex attribute types, embedded subgraphs, and GPU runtime scatter "in the same performance range as the landscape GPU grass system."
  - Mover is still **Experimental**.
  - StateTree gains a starting state and a Compiler Manager.
  - Enhanced Input and Common Input/UI are unified, so duplicate data assets are no longer needed, and there is a new Input Debugger.
  - Substrate NPR (toon) shading is Experimental.
  - MetaSound Templates are Experimental.

  — [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)
- More 5.8 features: an experimental Unreal MCP Server Plugin ("open-standard gateway that connects LLMs to UE projects"), an experimental Mesh Terrain System, and Substrate NPR shading for stylized looks. — [GameFromScratch](https://gamefromscratch.com/unreal-engine-5-8-released/)
- 2026 jam basics:
  - Runs Nov 12–15. Kickoff and theme reveal are Nov 11, 7:00 PM, with no timezone given in the post. One forum poster claims 2 PM ET, which conflicts.
  - Engine is "Unreal Engine or UEFN"; each team picks one.
  - Teams can have "up to four other humans and as many AI agents as you want."
  - Entrants must "Declare any prompts, scripts, or assets you made before the jam."
  - "You can set up your tools, agents, and MCP ahead of time."
  - AI use is optional.
  - Posters quoting the rules say UE submissions "must be packaged for Windows 10 or 11, macOS, Android, or iOS," and that the jam page says "(development build)."
  - The thread does not state a zip size limit.

  — [Epic forum announcement thread](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)
- The official 2026 jam page (unrealengine.com/news/2026-epic-ai-megajam) **could not be fetched** this session (client error). — [unrealengine.com/news/2026-epic-ai-megajam](https://unrealengine.com/news/2026-epic-ai-megajam)
- 2023 Epic MegaJam precedent:
  - "Submissions must be packaged for Windows, MAC OS X, Android, or iOS (development build)"; "no full, unpackaged projects"; "your .zip file must be UNDER 1GB." Larger files could be uploaded via Butler or Blendo Itch Uploader.
  - Judges scored 1–5 on Unique Use of Contest Theme, Fun Factor, Visuals, Audio, and Gameplay.
  - "Sourced (non-original) assets are allowed but will not be reviewed and scored." Marketplace art "could get points for lighting and composition, but the pre-made assets wouldn't."
  - "The game must include custom gameplay that exceeds the gameplay found in Epic Games' starter templates."
  - Entrants had to list pre-jam content.

  — [itch.io 2023 Epic MegaJam](https://itch.io/jam/2023-epic-megajam)

### Inferences
- Build on **UE 5.8**. No 5.9 or UE6 will ship before Nov 12. Pin the exact hotfix (5.8.x) now and do not upgrade during the jam.
- Rules say "development build," so set Build Configuration = Development and do **not** tick "For Distribution," which forces Shipping (see §5). Check that judges' builds don't show dev-only debug text on screen; see §4.
- Assume the 1 GB zip cap and the "sourced assets not scored / must exceed template gameplay" rules carry over until the 2026 Official Rules say otherwise. The scoring lesson: free assets buy presentation, but **original gameplay, theme use, and audio** are where points come from.

### Gaps
- 2026 Official Rules text was not retrievable: §1(b) build rules, §7(h) pre-jam tooling vs content, the zip size limit, judging criteria, whether modifiers exist, and the exact timezone. **Action: read the 2026 itch.io jam page and Official Rules PDF directly before kickoff.**

---

## 1. Starting points: templates, Variant templates, samples — speed by genre and size

### Takeaway
UE 5.6+ Variant templates (Arena Shooter, Survival Horror, Combat, Side Scroller, Platforming, Strategy, Twin Stick, Offroad, Timetrial) are the fastest legal starting points for a solo jam. The Game Animation Sample (GASP, motion matching, 500+ animations) gives AAA-feeling locomotion but is heavy. Pick the variant closest to the genre, then add custom gameplay beyond the template, which 2023 rules required.

### Cited Findings
- Variant templates and what they contain:
  - **First Person, Arena Shooter:** weapon pickups, multiple bullet types, AI opponents, ammo UI, arena map.
  - **First Person, Survival Horror:** low-light/high-contrast lighting, flashlight, sprint with UI, flickering lights, dark map.
  - **Third Person, Combat:** hand combat, combos, AI opponents, health system with in-world health bar UI.
  - **Third Person, Side Scroller:** locked side camera, constrained plane, pickups, single-sided/drop-through collision.
  - **Third Person, Platforming:** dash, wall jump, platforming map.
  - **Top Down, Strategy:** grid movement, drag-select AI, roof transition, orthographic camera.
  - **Top Down, Twin Stick:** dual-axis aim, AI opponents, bomb-and-shoot, score/multiplier UI.
  - **Vehicle, Offroad:** modular vehicle, open-world map, AWD, spline roads, RVT, HLOD.
  - **Vehicle, Timetrial:** lap timing, checkpoint gates, best-time UI, track.
  - Choosing "None" in the Variant dropdown gives the plain template. Vehicle maps have Runtime Virtual Texturing enabled.

  — [Variants in Game Templates (Epic docs)](https://dev.epicgames.com/documentation/unreal-engine/variants-in-game-templates)
- Epic announced the updated 5.6 game templates in a news post. — [Updated game templates for UE 5.6](https://www.unrealengine.com/news/updated-game-templates-for-unreal-engine-5-6available-now)
- GASP for 5.7:
  - 400 new animations and a new locomotion dataset. Fab advertises 500+ game-ready animations.
  - A Mover-based character (Experimental), Simple Spring Walking and Smooth Walking modes, and a slope-aware slide added as a Blueprint Mover mode.
  - A Smart Objects level where NPCs sit on benches from multiple angles.
  - An Experimental Pose Search Column (Choosers + Motion Matching) and a Footplacement Control Rig node.
  - Distributed via Fab. A UAF character is planned for 5.8, with UAF still Experimental.

  — [Epic tech blog: GASP updated for UE 5.7](https://www.unrealengine.com/en-US/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7)
- "In Unreal Engine even a blank project will end up being roughly 300 MB when making a build" (Epic community tutorial). — [Epic forum: How to Reduce Package Size in UE5](https://forums.unrealengine.com/t/1950640)
- A 2021 MegaJam solo C++ entry shipped as a **61 MB zip**, or 101 MB with prerequisites included. — [Bit Barrage postmortem](https://patrickdean.itch.io/bit-barrage/devlog/292175/epic-megajam-2021-postmortem)

### Inferences
- Fastest by genre:
  - **Action brawler / third-person:** TP Combat.
  - **Platformer:** TP Platforming or Side Scroller.
  - **Shooter:** FP Arena Shooter.
  - **Horror / walking-sim:** FP Survival Horror. It is cheap to make atmospheric, which is good for Visuals and Audio scores.
  - **Arcade / score-attack:** Top Down Twin Stick.
  - **Tactics / RTS-lite:** Top Down Strategy.
  - **Racing:** Vehicle Timetrial.
- Use GASP only if character movement feel is the core. Migrating its character into a variant template is a known community pattern **[unverified]**. Its animation and motion-matching database will add hundreds of MB, so budget against the 1 GB cap.
- **Lyra, City Sample, Cropout, Stack-O-Bot, Content Examples:**
  - Lyra (GAS, Common UI, modular gameplay) is a multi-day learning curve and a time sink for a solo 4-day jam.
  - City Sample is far too large: tens of GB of source, and too heavy for judges' PCs.
  - Cropout (top-down casual/mobile-friendly) and Stack-O-Bot (small stylized platformer) are good *reference* projects for juice, UI flow, and mobile-friendly settings.
  - Content Examples is a reference only, not a base.

  These characterizations are **[unverified this session]**: package sizes for these samples were not found.
- Expect a lean template build of roughly 300 MB uncompressed for Win64, assuming compressed pak. A jam game with modest Fab content fits well under a 1 GB zip if Megascans 8K textures and Nanite-heavy kits are avoided.

### Gaps
- No official package/download sizes found for Lyra, Cropout, Stack-O-Bot, City Sample, Content Examples, or GASP.
- Whether 5.8 changed the template set or added variants: the release notes only mention the VR template's `bPackageForOpenXRImmersive`. The relevant release-notes portion was truncated.
- PCG/biome sample templates and 5.8 template changes were not verified.

---

## 2. Free assets and licensing; how jam rules treat pre-made assets

### Takeaway
Pre-made assets have historically been **allowed but not scored** at MegaJam, and must be declared. Fab offers a permanent free tier, including some free Megascans, plus a rotating two-week "Limited-Time Free" drop. Megascans stopped being entirely free after 2024. MetaHumans are free under $1M revenue and can be used in any engine. Claim the Fab freebies *before* the jam and list them in the submission.

### Cited Findings
- Fab "Limited-Time Free" runs on a two-week cycle: "Every two weeks, we partner with some of Fab's top publishers…". These items "won't be free forever." Fab also has "completely free resources, including high-quality Megascans." — [Unreal Engine: Free Content for Creators](https://www.unrealengine.com/fabfreecontent)
- Megascans moved exclusively to Fab in mid-October 2024 and were free under Fab's Standard License through end of 2024. From 2025 the library is "no longer free" as a whole. Assets acquired earlier keep "the license that was in place when it was acquired." — [80.lv: Megascans no longer free after 2024](https://80.lv/articles/megascans-no-longer-free-after-2024/)
- Epic forum thread about accessing legacy Megascans on Bridge/Quixel.com — [Epic forum](https://forums.unrealengine.com/t/access-legacy-megascans-on-bridge-and-quixel-com/2142664)
- Contradiction: the 2023 MegaJam page said "Quixel Megascans are free for all Unreal Engine users!" That was true in 2023 and is superseded by the 2025 change. — [itch.io 2023 Epic MegaJam](https://itch.io/jam/2023-epic-megajam) vs [80.lv](https://80.lv/articles/megascans-no-longer-free-after-2024/)
- MetaHuman license: MetaHumans "can be used with any engine or creative software." MetaHuman is free for anyone under $1M USD revenue; above that, standard UE terms apply. — [metahuman.com/license](https://www.metahuman.com/en-US/license)
- The June 2025 change let MetaHumans be sold and used in Unity and Godot. — [CG Channel, June 4 2025](https://www.cgchannel.com/2025/06/you-can-now-sell-metahumans-or-use-them-in-unity-or-godot/)
- 2023 MegaJam asset rules: "Sourced (non-original) assets are allowed but will not be reviewed and scored." Entrants had to list pre-jam content. Gameplay must exceed starter templates. — [itch.io 2023 Epic MegaJam](https://itch.io/jam/2023-epic-megajam)
- 2026 jam: "Declare any prompts, scripts, or assets you made before the jam." Forum posters asked whether Starter Content, Mixamo, and third-party plugins are allowed, and the thread does not answer. — [Epic forum 2026 thread](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)

### Inferences
- Prep checklist, Oct 27 – Nov 11:
  1. Claim every Fab Limited-Time Free pack in the next ~2 rotations that could plausibly fit (stylized kits, VFX, SFX, UI packs). They stay in the library after claiming, though "keep forever" was **not confirmed** on the page read.
  2. Browse the permanent-free Fab filter, including free Megascans.
  3. Keep a running asset list (name, author, URL, license) to paste into the itch submission's credits/declaration.
- Treat Epic sample content (template meshes, Mannequins, GASP animations) as allowed but unscored. Ask in the jam Discord/forum whether Mixamo is accepted **[unanswered]**. Mixamo's own terms permit royalty-free use in games, but this was **not verified this session**.
- MetaHumans are a trap for a 4-day solo jam. They have heavy grooms and LODs that bloat package size and frame cost. Use them only with LOD-restricted, low-quality export settings, or avoid them.
- For scoring, spend asset time on **custom audio mix, custom VFX tweaks, and lighting/composition**, which judges can credit even with sourced meshes.

### Gaps
- The exact current Fab Standard License text (UE-only vs any engine, redistribution in packaged builds) was not read. fab.com license pages were not fetched.
- Whether claimed Limited-Time Free assets are permanent was not confirmed on the official page.
- The current status of the Paragon/Epic-owned free asset license was not checked.
- 2026 rulings on Mixamo, Starter Content, and plugins are unanswered in the forum thread.

---

## 3. Speed features: worth it vs time sink in a 4-day jam

### Takeaway
Use what is Production Ready and Blueprint-friendly: Enhanced Input, PCG (production-ready since 5.7), Niagara, MetaSounds, StateTree (simple AI), Lumen/Lumen Lite, MegaLights (production-ready in 5.8), and Substrate (production-ready in 5.7). Avoid Experimental systems (Mover, Nanite Foliage/Procedural Vegetation Editor, Mesh Terrain, Substrate NPR/toon, MetaSound Templates) and big frameworks (GAS, Lyra-style Common UI stacks) unless already fluent.

### Cited Findings
- Status matrix:

  | Feature | Status | Version |
  |---|---|---|
  | PCG | Production-Ready | 5.7 |
  | Substrate | Production-Ready | 5.7 |
  | Nanite Foliage | Experimental | 5.7 |
  | MegaLights | Beta | 5.7 |
  | MegaLights | Production Ready | 5.8 |
  | Lumen Lite | Beta | 5.8 |
  | Mover | Experimental | 5.8 |
  | Procedural Vegetation Editor | Experimental | 5.8 |
  | Substrate NPR (toon) | Experimental | 5.8 |
  | MetaSound Templates | Experimental | 5.8 |
  | Incremental Cooking | Beta | 5.8 |

  — [5.7 news](https://www2.unrealengine.com/news/unreal-engine-5-7-is-now-available); [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)
- 5.8 unifies Enhanced Input with Common Input/UI ("no longer need duplicate data assets") and adds an Input Debugger. This lowers the cost of controller-navigable menus. — [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)
- 5.8 PCG adds manual editing with overrides on generated content. — [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes); [GameFromScratch](https://gamefromscratch.com/unreal-engine-5-8-released/)
- `r.MegaLights.Supported` "removes all MegaLights shader compilation overhead if your project doesn't use it." — [Tom Looman: UE 5.8 performance highlights](https://tomlooman.com/unreal-engine-5-8-performance-highlights/)
- Distance-field shader permutations are removed when distance fields are disabled in Project Settings (5.8). — [Tom Looman](https://tomlooman.com/unreal-engine-5-8-performance-highlights/)
- Jammer lesson from a 2021 MegaJam postmortem:
  - A Blueprint boss with hardcoded block counts was rewritten in C++, wasting about 4 hours.
  - Ability logic spread through Tick was "held together by a single delicate thread."
  - He had learned GAS a week earlier but didn't use it.
  - His conclusion: prototype in the approach you'll ship, and use built-in systems when they fit.

  — [Bit Barrage postmortem](https://patrickdean.itch.io/bit-barrage/devlog/292175/epic-megajam-2021-postmortem)

### Inferences
Per-feature verdict for a solo 4-day jam:

| Feature | Verdict | Why |
|---|---|---|
| Enhanced Input | Use | Template default; gamepad mappings are nearly free. |
| StateTree | Use for simple enemy AI | Template AI already uses Blueprint/StateTree patterns **[template internals unverified]**. Faster than Behavior Trees plus blackboard for 2–3 state enemies. |
| Smart Objects | Skip | Unless the core loop is NPC-environment interaction; GASP has an example level. |
| Niagara | Use | Start from built-in emitter templates and Fab freebie VFX. Highest juice per hour. |
| MetaSounds | Use lightly | Pitch/volume randomization on hit/footstep sounds is a cheap polish win. Skip Experimental Templates. |
| PCG | Use only for scatter | Dressing (rocks, grass, props on spline or volume) saves hours. Building a custom biome graph is a time sink. |
| Lumen | Keep on | Default; the RX 9070 XT meets requirements. Expose a scalability toggle; see §4. |
| MegaLights | Only for many dynamic lights | e.g., a neon/horror look. Otherwise set `r.MegaLights.Supported` off to cut shader cost. |
| Nanite | OK for static meshes | Avoid Experimental Nanite Foliage. Nanite on low-end judges' GPUs is a perf risk; see §4. |
| Substrate | Fine | Production-ready, but legacy materials are faster to author for most jammers. Toon/NPR is Experimental, so use a post-process stylization material instead. |
| Chaos | Only as a gimmick | Destruction caching and fracture eat time. Simple physics impulses are fine. |
| GAS | Skip | Unless already fluent. Solo setup overhead exceeds benefit in 4 days. |
| Mover | Skip | Experimental. Use the Character Movement Component. |
| Common UI | Use lightly | Worth it in 5.8 for gamepad-navigable menus. Otherwise UMG plus explicit focus handling. |

### Gaps
- No primary-source jammer data on time cost per feature; the verdicts above are inference.
- Niagara and Gameplay Camera 5.8 changes were in the truncated part of the release notes.

---

## 4. Look/feel polish ("game juice"), menus, and performance on judges' PCs

### Takeaway
2023 judging criteria were Theme, Fun, Visuals, Audio, and Gameplay. Audio is a full fifth of the score and is the cheapest to raise. Juice (camera shake, hit-stop, VFX, SFX variation, UI feedback) plus a complete shell (title, pause, settings with scalability and volume, controller support) is what separates entries. For performance, ship defaulting to a mid scalability preset. 5.8's Lumen Lite / Medium GI is the new low-end-friendly path.

### Cited Findings
- 2023 criteria: Unique Use of Contest Theme, Fun Factor, Visuals, Audio, Gameplay (1–5 each). — [itch.io 2023 Epic MegaJam](https://itch.io/jam/2023-epic-megajam)
- The 2026 thread says "Online and in-person entries are judged the same way." A poster paraphrased judges as valuing quality and originality, which is unofficial. — [Epic forum 2026 thread](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)
- Lumen Lite / Medium in 5.8:
  - Enabled via Medium GI/Reflection quality, `sg.globalilluminationquality 1` and `sg.reflectionquality 1`. Reflections fall back to SSR when Lumen is off.
  - "Lumen Medium Quality is targeted at low end PC and handhelds."
  - Dynamic Resolution is now supported on PC with DX12 and Vulkan.
  - `MallocBinned3` is the default Windows allocator.
  - `r.Material.StripUnusedDefaultTextures` avoids loading unused default textures.

  — [Tom Looman: UE 5.8 performance highlights](https://tomlooman.com/unreal-engine-5-8-performance-highlights/)
- Lumen Lite is "twice as fast as Lumen high quality" and is the default on current-gen handhelds. — [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)
- Hardware requirements per Epic's Linux docs, which state the same GPU classes as general UE requirements:
  - Lumen and MegaLights need SM6 and an NVIDIA RTX 2000+, AMD RX 6000+, or Intel Arc A+.
  - Nanite and Virtual Shadow Maps need VK_KHR_shader_atomic_int64 and SM6.

  — [Linux Development Requirements (Epic, 5.8)](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine)
- PSO precaching:
  - `r.PSOPrecaching` defaults to Enabled when the RHI supports it.
  - Global shaders, Nanite, hair, and ray-tracing geometry are only partly covered.
  - Docs suggest a small bundled PSO cache for global graphics PSOs.
  - The loading screen should wait until `FShaderPipelineCache::NumPrecompilesRemaining()` reaches 0.
  - Use `-clearPSODriverCache` for first-run testing.
  - `stat PSOPrecache` shows stats.

  — [PSO Precaching (Epic docs)](https://dev.epicgames.com/documentation/en-us/unreal-engine/pso-precaching-for-unreal-engine)
- Bundled PSO walkthrough (community, Epic MVP author). — [Tom Looman: PSO Precaching & Bundled PSOs](https://tomlooman.com/psocaching-unreal-engine)

### Inferences
- **Judges' hardware:** assume some judges lack RTX 2000 / RX 6000-class GPUs. Lumen and Nanite VSM would then fail or fall back, so test the fallback path. Steps:
  1. Default to Medium (`sg.*` = 1) or an auto-detect benchmark on first launch. `UGameUserSettings::RunHardwareBenchmark` + `ApplyHardwareBenchmarkResults` is a standard API **[not re-verified this session]**.
  2. Expose Low/Medium/High/Epic, resolution scale, and VSync in a settings menu.
  3. Cap the frame rate.
- **Shader hitch mitigation:** add a short loading/title screen that waits on `NumPrecompilesRemaining()`. This turns first-play hitches into a progress bar, and judges notice stutter.
- Juice checklist, ordered by cost-effectiveness, all built-in. These are standard UE features, but specific class names were **not re-verified this session**.
  - Camera shake assets on hit, land, and explosion (Legacy or Pattern-based camera shake).
  - Hit-stop via brief global time dilation (`Set Global Time Dilation` ~0.05–0.1 for 50–100 ms) or custom time dilation per actor.
  - Niagara burst plus decal on impact.
  - Hit flash material parameter.
  - FOV kick or radial blur on dash.
  - Post-process volume look: color grading LUT, vignette, bloom, film grain, or a stylization material for "stylized" visuals.
  - UI tween or scale-punch on score and damage numbers.
  - MetaSounds or Sound Cue with random pitch ±5–10% and multiple variations.
  - Music with a ducking submix.
  - Controller rumble via Force Feedback.
- **Shell that judges notice** (common jam-review consensus, unsourced here): title screen with game name; how-to-play or control hints that switch for gamepad; pause menu with resume, restart, settings, and quit; volume sliders; scalability presets; working Quit; no debug text on screen. Development builds show on-screen debug messages from `Print String` by default, so remove them or disable them with `DisableAllScreenMessages` **[console command not re-verified]**.

### Gaps
- No primary-source list of what MegaJam judges specifically comment on; past judge feedback was not found.
- The `RunHardwareBenchmark` API, camera-shake class names, and the `DisableAllScreenMessages` command were not re-verified against 5.8 docs.

---

## 5. Performance & build size: getting under 1 GB, Development config, prerequisites

### Takeaway
Use the official Packaging settings:
- Build Configuration = Development.
- Use Pak File / IoStore on.
- Create Compressed Cooked Packages on, with Oodle (Kraken or Leviathan).
- Exclude Editor Content When Cooking on.
- An explicit "List of Maps to Include."
- Directories to Never Cook for unused template/variant folders.
- Include Prerequisites Installer on.

A small jam game lands far under 1 GB. The baseline blank build is about 300 MB.

### Cited Findings
- Packaging settings, quoted from Epic docs:
  - **Build Configuration** offers Debug, DebugGame, Development, Test, and Shipping.
  - **For Distribution:** "If enabled, a distribution build will be created using the shipping configuration."
  - **Use Pak File** defaults to enabled.
  - **Use Io Store:** ".utoc/.ucas container files instead of .pak."
  - **Create Compressed Cooked Packages:** "decreased deployment size."
  - **Package Compression Format** takes a comma-separated list of formats.
  - **Package Compression Method** for Oodle: Kraken, Mermaid, Selkie, or Leviathan.
  - **Encoder Effort Level for Debug & Development:** "makes packages smaller but takes more time to encode."
  - **Exclude Editor Content When Cooking:** skips `Engine/Content/Editor*`.
  - **Cook Only Maps** only affects the Cookall flag.
  - **List of Maps to Include in a Packaged Build**, **Additional Asset Directories to Cook**, and **Directories to Never Cook** ("should never be cooked, even if they are referenced").
  - **Share Material Shader Code** and **Shared Material Native Libraries**.
  - **Include Prerequisites Installer**.
  - **Include Crash Reporter** is on by default for Blueprint projects but can be disabled.
  - **Full Rebuild**.
  - **Staging Directory**.

  — [Project Settings > Packaging (Epic docs)](https://dev.epicgames.com/documentation/en-us/unreal-engine/project-section-of-the-unreal-engine-project-settings)
- 5.8: "Zenserver as Cooked Output Store is now enabled by default." Incremental Cooking is Beta. — [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)
- A blank UE5 project build is ~300 MB. — [Epic community tutorial thread](https://forums.unrealengine.com/t/1950640). The full tutorial is at [dev.epicgames.com/community/learning/tutorials/KpXX](https://dev.epicgames.com/community/learning/tutorials/KpXX/how-to-reduce-package-size-in-unreal-engine-5) and was not read.
- MegaJam size precedent: a 61 MB zip, or 101 MB with prerequisites. — [Bit Barrage postmortem](https://patrickdean.itch.io/bit-barrage/devlog/292175/epic-megajam-2021-postmortem)
- Older official Android APK-size docs (UE 4.26) cover reducing mobile package size. — [Reducing APK Size (UE 4.26)](https://docs.unrealengine.com/4.26/SharingAndReleasing/Mobile/Android/ReducingAPKSize)
- butler rejects builds over 30 GB uncompressed; this is not a concern. — [itch.io butler docs](https://itch.io/docs/butler/pushing.html)

### Inferences
- Sub-1 GB recipe for UE 5.8, Development:
  1. **Development only.** Do not tick For Distribution.
  2. Use Pak/IoStore on, compressed on, Oodle **Kraken** for a balance or **Leviathan** for smallest size at a cost in build time. Raise the encoder effort level for the final build only.
  3. Fill in **List of Maps to Include** (title map + game maps). Do not use Cook Everything.
  4. Add unused variant/template folders, test maps, and big unused Fab packs to **Directories to Never Cook**, or delete them from the project.
  5. Exclude Editor Content on.
  6. Disable unused plugins: e.g., Online subsystems, Bridge/Fab, MetaHuman, Water, Chaos Destruction (if unused), XR, and media plugins. Verify the game still runs, since some defaults are required.
  7. Set texture Max In-Game Size (e.g., 2048) or per-platform LOD bias in Device Profiles for large Fab textures, and avoid 8K Megascans.
  8. Run Size Map / Asset Audit on the cooked content.
  9. Check the zip size. The zip must be the deliverable folder (Windows: `Windows/` with `<Game>.exe`, `<Game>/Content/Paks`, `Engine/`).
- Include Prerequisites Installer adds ~40 MB but prevents "VCRUNTIME missing" crashes on clean judge machines. Worth it. Alternatively, ship `UEPrereqSetup_x64.exe` in the zip **[file name not re-verified]**.
- Clean-machine test: run the zip on a Windows install that has never had UE or Visual Studio, e.g., a fresh Windows VM or a friend's PC. Test with `-clearPSODriverCache` to see first-run hitches.

### Gaps
- No official 5.8 "reduce package size" doc page found; the community video was not read.
- No measured sizes for template-variant builds in 5.8.
- Texture LOD bias / Device Profile exact settings were not quoted from docs.

---

## 6. Packaging pipeline: Platforms menu / Project Launcher, RunUAT, Android, itch.io butler

### Takeaway
Package from the editor's Platforms menu, or a Project Launcher custom profile whose output log shows the exact `RunUAT BuildCookRun` line to reuse in scripts. Upload with butler: `butler push <dir> user/game:windows`, plus `android` and `mac` channels. For Android, UE 5.8 wants NDK r27c, SDK 35 (min 34), build-tools 35.0.1, and OpenJDK 21.0.3.

### Cited Findings
- Official RunUAT example: `[UnrealEngineRoot]/Engine/Build/BatchFiles/RunUAT.bat BuildCookRun -project=MyProject.uproject -clientconfig=Development`. Project Launcher logs show the equivalent full command line ("-ScriptsForProject=MyProject.uproject BuildCookRun -project=… -clientconfig=Development"), so you can copy the exact flags from a Custom Launch Profile's output log. The page does **not** document other BuildCookRun flags. — [Build Operations: Cooking, Packaging, Deploying and Running (Epic docs)](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-operations-cooking-packaging-deploying-and-running-projects-in-unreal-engine)
- UE 5.8 Android toolchain:
  - Android Studio Koala 2024.1.2 Patch 1.
  - NDK r27c.
  - SDK 35 recommended, minimum SDK 34 for compiling UE, default target SDK 34, minimum install SDK 26.
  - Build-tools 35.0.1.
  - OpenJDK 21.0.3.
  - Gradle 8.7 with AGP 8.5.2.

  — [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)
- UE 5.8 iOS/Mac toolchain: Xcode 26.1.1 recommended (minimum 26.0); macOS Sequoia 15 recommended (minimum Sonoma 14.5). — [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)
- UE 5.8 Windows toolchain: Visual Studio 2026 recommended (minimum VS 2022 v17.14); MSVC 14.50 recommended (minimum 14.38); Windows SDK 10.0.26100.0 default (minimum 10.0.22621.0). — [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)
- butler:
  - Syntax: `butler push directory user/game:channel`. Channels are kebab-case.
  - Platform tags come from channel names: `win`/`windows`, `linux`, `mac`/`osx`, `android`.
  - `--userversion 1.1.0` or `--userversion-file` sets the version.
  - A directory holding a single .zip is auto-unzipped; disable with `--no-auto-unzip`.
  - `--ignore '*.pdb'` excludes files, and `--dry-run` previews.
  - The docs recommend pushing an exact release folder.

  — [itch.io butler: Pushing builds](https://itch.io/docs/butler/pushing.html)
- 2023 MegaJam said files over 1 GB could be uploaded via Butler or Blendo Itch Uploader, but the zip itself must be under 1 GB. — [itch.io 2023 Epic MegaJam](https://itch.io/jam/2023-epic-megajam)
- Older UE Android docs used Android (ETC1/ASTC) flavors and an `Install_<Project>_Development-arm64…sh` install script. "Shipping builds strip console commands, statistics, and profiling tools." — [Android on Linux (UE 4.27, outdated)](https://docs.unrealengine.com/4.27/en-US/SharingAndReleasing/Linux/IntermediateLinuxDeveloper/AndroidOnLinux)

### Inferences
- Script to adopt, built from the Project Launcher's logged command, not hand-written flags. Commonly seen BuildCookRun flags (`-platform=Win64 -build -cook -stage -pak -iostore -compressed -prereqs -archive -archivedirectory=<dir> -map=<maps> -unattended -utf8output -nocompileeditor`) are **[community-known, not verified from Epic docs this session]**. Copy them from your own Launcher log.
- itch channel plan:
  - `jf1shh/<game>:windows` (primary, judges mostly on Windows).
  - Optionally `:android` with an arm64 ASTC APK. Ignore Meta Quest; the VR template has `bPackageForOpenXRImmersive`, which is not needed.
  - Optionally `:mac` only if a Mac and Xcode 26 are available.
- Also upload the zip manually, or confirm butler's result is downloadable as a <1 GB zip, since judges download from the itch page.
- Push with `--ignore '*.pdb'` to strip debug symbols. They are big and not needed for a Development build judges run. Keep the .pdb locally for crash diagnosis.

### Gaps
- No official full BuildCookRun flag reference was retrieved (the uetools page didn't have it).
- Blendo Itch Uploader specifics were not fetched.
- Current (5.8) "Setting up Android SDK/NDK" doc steps (SetupAndroid.sh/.bat, Turnkey) were not fetched.
- iOS packaging requirements (Apple developer account, Mac host) were not researched beyond toolchain versions.

---

## 7. Linux host (CachyOS + RX 9070 XT): what works, and how to get a Windows build

### Takeaway
The Linux editor (Vulkan, SM6) runs on AMD RDNA GPUs with RADV ≥ 24.2.8 (25.0+ recommended). The RX 9070 XT exceeds the RX 6000+ requirement for Lumen/MegaLights. Epic documents Linux packaging only for Linux targets; the only cross-compile path is Windows → Linux. Packaging a **Windows** build from Linux is not supported, so plan a Windows machine (dual-boot, GPU-passthrough VM, or a friend's or rented PC) for cooking Win64. Do a full Windows package test **before** the jam.

### Cited Findings
- Epic Linux requirements for 5.8:
  - Develop on Ubuntu 22.04 (recommended) or Rocky Linux 8; run on Rocky/RHEL 8+.
  - Kernel ≥ 4.18 and glibc ≥ 2.28; upgrade to glibc 2.35+ if startup is slow.
  - clang 20.1.8.
  - 32 GB RAM; GPU like a GeForce 2080 with 8 GB+.
  - AMD Vulkan: RADV ≥ 24.2.8, 25.0.0+ recommended. NVIDIA: driver 570+.
  - Lumen and MegaLights need SM6 and RX 6000+. Nanite/VSM need VK_KHR_shader_atomic_int64.
  - The page discusses **only Linux as a target**. Cross-compiling to Linux is supported only from Windows.

  — [Linux Development Requirements (Epic)](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine)
- 5.8 release notes repeat the Linux toolchain (clang 20.1.8, cross-compile toolchain v26). MetaHuman Animator body animation is Windows-only. — [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)
- Forum reply (2016): cross-compiling Linux from Windows is possible, "the reverse is not available." On Linux, the only packaging target is Linux. A 2018 follow-up asking if this changed went unanswered. — [Epic forum: How to build for Windows developing on Linux?](https://forums.unrealengine.com/t/how-to-build-for-windows-developing-on-linux/349719)
- A community article on UE on Linux suggests a VM (VMware/VirtualBox) or dual-boot as options and recommends native installs for daily use. — [Artificial Life substack](https://artificiallife.substack.com/p/unreal-engine-development-and-linux)
- GitHub-hosted standard Windows runners: public repos get 4 CPU, 16 GB RAM, **14 GB SSD**; private repos get 2 CPU, 8 GB RAM, 14 GB SSD. Larger runners need GitHub Team/Enterprise Cloud org plans. — [GitHub docs: GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- Old UE4-era docs supported Android packaging from a Linux editor via CodeWorks and JAVA_HOME, and noted Android Vulkan was unsupported from Linux then. This is **outdated** for 5.8. — [Android on Linux (UE 4.27)](https://docs.unrealengine.com/4.27/en-US/SharingAndReleasing/Linux/IntermediateLinuxDeveloper/AndroidOnLinux)

### Inferences
- Windows build options, ranked for this developer:
  1. **Windows dual-boot on the same desktop.** This is most reliable: full RX 9070 XT, native D3D12 shader compile, and the same project via Git. Install Windows + UE 5.8 + VS 2022 17.14+/VS 2026 + Windows SDK now and run a full package of a template before Nov 12.
  2. **Windows VM with GPU passthrough** (VFIO) on CachyOS. Cooking needs CPU and RAM more than GPU (cook ≠ render), so a VM **without** passthrough may still cook and package. The editor and runtime testing would be poor without a GPU. Inference, **not verified**.
  3. **Friend's PC or rented cloud Windows GPU box** (e.g., Shadow PC or an AWS g-instance). Workable, but upload/download of the project and engine (~50+ GB engine install) is slow.
  4. **GitHub Actions hosted Windows runners are not viable.** 14 GB SSD can't hold a UE install. A self-hosted Windows runner on your own dual-boot or VM is possible but pointless overhead for a jam.
- **Don't pursue Wine/Proton for the editor.** There is no supported path, and debugging it during a 4-day jam is a failure mode.
- CachyOS is not an Epic-listed distro (Ubuntu 22.04 / Rocky 8 are). Its newer Mesa (RADV 25+) and glibc should satisfy the minimums. Expect occasional distro-specific issues, which is why the Windows partition also doubles as a fallback editor.
- **Android from Linux:** plausible in UE5 (Linux is an Android host in modern UE via the SDK setup scripts), but **not verified for 5.8 this session**. Treat it as optional, since Windows is the primary judged platform.
- Decide on a **single source-of-truth project in Git**. Develop on Linux or Windows, but do final cooks on Windows. Shader DDC is per-platform, so expect a long first D3D12 shader compile on Windows. Warm it before the jam by packaging the template once.

### Gaps
- No current (UE5.x) official statement explicitly saying "Windows targets cannot be packaged from a Linux host." The evidence is the 2016 forum reply plus the Linux docs listing only Linux targets.
- Whether an RDNA4 (RX 9070 XT) Linux editor has known issues in 5.8 was not researched.
- 5.8 Android-from-Linux setup was not verified.

---

## 8. Version control for UE in a jam

### Takeaway
For a solo dev, Git + Git LFS (binary `*.uasset`/`*.umap` in LFS) with a standard UE .gitignore and One File Per Actor is sufficient. Avoid UE's built-in Git plugin, which has no LFS or locking. Watch GitHub LFS quota. Perforce or Unreal Revision Control only matter for teams.

### Cited Findings
- Anchorpoint's Unreal Git guidance:
  - Use Git LFS for binaries, and exclude regenerable caches like DerivedDataCache.
  - Don't use Unreal's built-in Git plugin: it "lacks LFS and file locking support and has never left beta."
  - World Partition enables One File Per Actor by default; otherwise enable "Use External Actors" in World Settings so changes go into small actor files instead of the level.
  - Unreal identifies assets by path, so renames require fixing redirectors; plan folder naming early.
  - Use trunk-based development with minimal branches.

  — [Anchorpoint: Git with Unreal Engine](https://docs.anchorpoint.app/docs/version-control/first-steps/unreal)
- Community UE5 .gitignore — [MOZGIII/ue5-gitignore](https://GitHub.com/MOZGIII/ue5-gitignore)
- A community guide covers .gitignore, LFS, and One File Per Actor. — [uhiyama-lab: Managing UE Projects Safely with Git](https://uhiyama-lab.com/en/notes/ue/git-lfs-project-management/)

### Inferences
- Setup for `jf1shh/megajam`:
  1. `.gitignore`: `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`, `.vs/`, `*.sln`, build output (`Packaged/`, `Builds/`). Folder names are standard UE but only DDC was confirmed by the source.
  2. `.gitattributes`: `*.uasset filter=lfs diff=lfs merge=lfs -text` and same for `*.umap`, plus raw source art (`*.fbx`, `*.wav`, `*.png`, `*.psd`) if kept in the repo.
  3. Commit at each milestone (end of each jam block).
  4. **Never commit packaged builds.**
- GitHub LFS free quota is limited (historically 1 GB storage/bandwidth on free accounts) **[not verified this session]**. Fab packs can blow it. Mitigations: don't commit unused Fab packs, or use an Azure DevOps or TrueNAS-hosted Git remote, which Anchorpoint suggests for storage.
- Use Git as the bridge between the Linux dev environment and the Windows packaging partition.

### Gaps
- Current GitHub LFS free-tier quotas were not verified.
- Unreal Revision Control (Epic's hosted offering) status and pricing were not researched.

---

## 9. Scope and timeline: 4-day schedule and common failure modes

### Takeaway
The dominant failure modes are scope creep after the core works and last-hour packaging problems. Schedule a packaged build on Day 1 and every day after. Freeze features at ~T-24h, and reserve the final ~8 hours for polish, packaging, a clean-machine test, and upload.

### Cited Findings
- A 2021 MegaJam postmortem:
  - "The scope grew once the core worked, so the extra days went to new features rather than polish."
  - A late rewrite cost about 4 hours.
  - He kept difficulty easy so players could reach the boss.
  - A simple concept helped him finish.

  — [Bit Barrage postmortem](https://patrickdean.itch.io/bit-barrage/devlog/292175/epic-megajam-2021-postmortem)
- More MegaJam postmortems exist but were **not read** this session:
  - [lopcario: Epic Mega Jam Jumper postmortem](https://lopcario.itch.io/epic-mega-jam-jumper/devlog/424406/postmortem)
  - [jkrafty postmortem](https://jkrafty.itch.io/jkrafty-pixel-hero-in-a-3d-world/devlog/425356/postmortem)
  - [Junglefall: Post MegaJam Thoughts](https://tree-industries.itch.io/junglefall/devlog/203808/post-megajam-thoughts)
- 2023 rules required uploading to your own itch page first, then submitting to the jam page. — [itch.io 2023 Epic MegaJam](https://itch.io/jam/2023-epic-megajam)
- Testing guidance: use `-clearPSODriverCache` to test first-run behavior. — [PSO Precaching docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/pso-precaching-for-unreal-engine)

### Inferences
Suggested solo schedule (inference; adjust to the actual deadline timezone):

- **Pre-jam (Oct 27 – Nov 11):**
  - Install UE 5.8 on Linux and Windows.
  - Package each candidate variant template on Windows once, which warms the DDC and proves the toolchain.
  - Push a test build to a private itch page via butler.
  - Claim Fab freebies.
  - Build a reusable, theme-agnostic "shell" kit: title, pause, settings, and a loading screen that waits on PSO precompile.
  - **Check the rules.** Prior-made assets must be declared. Find out whether a pre-built menu shell is allowed under §7(h)'s tooling-vs-content rule.
  - Set up the Unreal MCP plugin and AI agents, which the rules explicitly allow.
- **Day 1 (Nov 12):**
  - Hours 0–2: theme brainstorm; pick one verb and one twist.
  - Hours 2–10: greybox the core loop in the chosen variant.
  - End of day: first **packaged Windows Development build** plus a butler push to a private channel.
- **Day 2:**
  - Core loop complete and fun-tested.
  - Enemies/AI (StateTree) and win/lose states.
  - Package again.
- **Day 3:**
  - Content: levels via Fab assets and PCG scatter.
  - Juice pass: VFX, SFX, camera shake, hit-stop.
  - Music.
  - UI shell hooked up.
  - Package plus a clean-machine test.
  - **Feature freeze at end of Day 3.**
- **Day 4:**
  - Bugs and balance (make it easy and finishable).
  - Scalability defaults, controller pass, credits/asset declaration, itch page (screenshots, GIF, controls).
  - Final package by **T-6h**, test on a clean Windows box, zip under 1 GB, upload, submit by **T-2h**.
- Failure modes and prevention:

  | Failure mode | Prevention |
  |---|---|
  | Packaging fails at the last hour | Daily builds |
  | Missing maps in the cook | Explicit map list |
  | Crash on launch from a missing prerequisite or plugin | Prereqs installer + clean-machine test |
  | Shader compile stalls on first play | PSO wait screen |
  | Game too hard for judges | Tune easy, add skip/checkpoints |
  | Debug text left on screen | Remove Print Strings |
  | Wrong default map | Set Game Default Map in Maps & Modes |
  | Linux-only toolchain discovered late | Windows partition ready pre-jam |

### Gaps
- No hour-by-hour schedules from experienced UE jammers were retrieved; three postmortems were found but not read.
- No data on MegaJam judges' hardware or how many judges test on Android/Mac.
