# UE 5.9 release notes: linked pages digest

**Last verified:** 2026-11-11 (all pages fetched that day; sections 11-14 re-fetched live 2026-11-11 for a page-by-page diff against the repo). Companion to `ue59-release-notes.md`. Tag `[page]` means the linked page text itself; anything marked UNCONFIRMED is not on the page. The pages describe 5.9 docs, and our build is the 5.9.0-preview-1 source build (commit `acf0265`), so cvars and defaults were unchecked against that build when written; the Fable gate of PR #186 then checked every cvar, default and RHI requirement in sections 4-8 against `acf0265` source on 2026-11-11 and found them correct (page-only facts stay tagged). Own-words summaries only.

The release notes page was still "last updated 2026-11-09" on 2026-11-11, so nothing new on it.

## 1. Unreal Canvas Overview
https://dev.epicgames.com/documentation/unreal-engine/unreal-canvas-overview-in-unreal-engine

- Experimental; the page tells you to be careful shipping with it. A separate "Native" variant exists with different controls than the web tab. Unrelated to the Canvas asset and the UMG Canvas Panel.
- Canvas Bridge pulls in Spatial Annotations, Canvas Graph, Unreal MCP, rendering, media and Python. Dependencies vary by platform.
- Local models total about 1.8 GB (SAM 2.1 segmentation, Depth Anything 3, SkinTokens auto-rig). Depth Anything 3 is Windows x64 only, so it cannot run on our Linux editor. UNCONFIRMED whether SkinTokens runs on AMD.
- Cloud providers are unnamed here (see section 2). Costs follow the provider; batch and Re-run make extra paid calls.
- Quick Render uses PIE by default, so gameplay logic runs during capture; Editor World mode avoids PIE where supported.
- Generated assets import under `/Game/Merlin` (kept for compatibility); renders go to `Saved/UnrealCanvasSequenceRender`, scene state to `Saved/UnrealCanvasSceneState`.
- Cutout actors are editor-only but saved in the level: review or remove them before cooking a package. Actor annotations switch on custom depth and a stencil value; removing one resets stencil to 0 without restoring prior values (watch post-process stencil use).
- Generated meshes need manual checks (topology, scale, materials, perf). Reject on an agent review does not undo changes.
- Page asks teams to review content rights, provenance labels and provider terms.

## 2. Getting Started with Unreal Canvas
https://dev.epicgames.com/documentation/unreal-engine/getting-started-with-unreal-canvas-in-unreal-engine

- Targets 5.9 Preview; work on a copy of the project.
- Requires an NVIDIA GPU with at least 8 GB VRAM for the local steps (our Linux box is AMD, the Legion is unknown: UNCONFIRMED), plus your own account and API key for at least one provider. Pre-release providers: fal.ai, Scenario, Luma (incl. Luma Agents), World Labs, plus local models. Optional agents: Claude Code, Codex CLI.
- Setup: Edit > Plugins > Unreal Canvas Bridge (restart) then Tools > Unreal Canvas > Install; models download only after consent; declining disables segmentation, depth and edge steps.
- Server version must match the plugin exactly or the tab is blank; fix by reinstalling or updating to the latest 5.9 Preview.
- Keys in environment variables or key files override Settings. Models carry Approved / Limited Use / Unreviewed badges; project restrictions can block listed models. For the jam, cloud use is terms-gated (see repo rules), so check the contest rules first.
- User data (canvases, uploads) lives under the user profile (`%APPDATA%` on Windows) by default; Storage > Scan / Quarantine repairs damaged canvases.

## 3. AI Features, Tools, and Plugins (index)
https://dev.epicgames.com/documentation/unreal-engine/ai-features-tools-and-plugins-in-unreal-engine

- Pure index: five topics (Unreal MCP, PCG with LLMs, External Agents in the Assistant panel, Python with AI Agents, Unreal Canvas). No defaults, limits or settings on the page itself. Page slugs: `unreal-mcp-in-unreal-editor`, `working-with-pcg-and-llms-using-unreal-mcp-in-unreal-engine`, `run-external-ai-agents-in-the-unreal-assistant-panel-in-unreal-engine`, `using-python-with-ai-agents-in-unreal-engine`, `unreal-canvas-in-unreal-engine` (the Canvas landing page was read 2026-11-11: section 14).
- The four non-Canvas pages were already read in full for the digest (items 14-27, 55, 85-91).

## 4. Lumen World Cache
https://dev.epicgames.com/documentation/unreal-engine/lumen-world-cache-in-unreal-engine

- Off by default; no Project Settings toggle. Set `r.Lumen.WorldCache.Supported=1` under `[SystemSettings]` in `DefaultEngine.ini` and restart (shaders recompile). `r.Lumen.WorldCache.Allowed` (default on) flips it at runtime between World Cache and Surface Cache; switching back to Surface Cache causes a few frames of bad lighting. `Supported=0` removes it and its shaders.
- Requires hardware ray tracing: Lumen GI, "Support Hardware Ray Tracing" and "Use Hardware Ray Tracing when available" on; HW RT mode Full or Simplified Material (Inline NOT supported; the setting also exists for Linux). Needs SM6, inline RT, wave ops; on D3D12 also SM 6.6 and Resource Binding Tier 3. If RT is unavailable, Lumen drops to software RT and the World Cache is off. Our Windows Legion GPU must meet this: UNCONFIRMED.
- Simplified Material mode drops Lumen hit lighting. Editor-only preview cvar `r.RayTracing.SimplifiedMaterialOverride` (0 platform, 1 simplified, 2 full).
- Defaults listed: CellDensity 20 (1-63), MaxEntriesLog2 20, PathDownsampleFactor 8, MaxBounces 3, MaxFramesAccumulated 16, MaxFramesUnused 64, MaxLocalLightCandidateSamples 16, MaxRayIntensity 40, AsyncCompute on. Cost shows as LumenWorldCache in `stat gpu`.
- Limits: opaque surfaces only (no translucent caching); lighting lags changes; unsupported for Water, RT translucency, foliage and subsurface transmission, Far Field; split screen reset only hits the first view. LumenPT has its own separate cache.
- Contradicts nothing in the digest; the forum claim of "typos" was not visible to the page reader (UNCONFIRMED). Digest item 44 gap: it did not say it is config-only and Inline mode is unsupported.

## 5. Adaptive Voxel-Based OIT (AVBOIT)
https://dev.epicgames.com/documentation/unreal-engine/adaptive-voxelbased-order-independent-transparency-in-unreal-engine

- Experimental; desktop SM6 only; off with MSAA; no Project Settings option.
- Enable: `r.OIT.Method=1` (0 none default, 2 sorted pixels) plus `r.AVBOIT.NonNanite=1` for non-Nanite translucency and particles, in `[SystemSettings]`. Nanite translucency needs `r.Nanite.AllowTranslucency`; `r.AVBOIT.Nanite` defaults to 1. Unsupported setups fall back to standard sorting.
- `r.AVBOIT.Support` defaults to 1 (read-only, restart): SM6 projects compile an extra shader variant per translucent material even when unused. Set it to 0 if skipping AVBOIT, to save shader build time and memory.
- Other defaults: RGB 1, PixelSize 8, MaxDistance 20000 cm, EarlyOut 1. Changing `r.OIT.Method` at runtime hitches.
- Materials: Translucent, Additive, Modulate, AlphaComposite; must output only their own colour and must NOT sample SceneColor behind them (looks washed out; check with `r.AVBOIT.DebugWeightOutput 2`). Debug views `r.AVBOIT.Visualize 1-10` need `r.ShaderPrint 1`, not in Test or Shipping.
- Limits: refraction and distortion are wrong; same-slice surfaces average; large enclosing translucent volumes cost depth precision; beyond MaxDistance all lands in the last slice; colour edges step at cell size.

## 6. Nanite Technical Details (culling)
Linked URL (`?application_version=5.7`): https://dev.epicgames.com/documentation/unreal-engine/nanite-technical-details?application_version=5.7
Also read: same page with `?application_version=5.9`.

- The linked 5.7 variant has NO culling section; the release notes link points at the wrong version. The 5.9 page has "Nanite Culling".
- 5.9 page: culling runs as two GPU dispatches. Instances go to the "complex" class when skeletal, spline, Nanite Assembly parts, first-person, using active WPO or displacement, or moving (the "moving" case is page-only, UNCONFIRMED in source). Near the top of the hierarchy each node gets more threads so one dispatch descends several levels (adaptive fanout). Cvars: `r.Nanite.Culling.Classification` default 1 (0 puts everything on the complex path), `r.Nanite.Culling.AdaptiveFanoutThreadBudget` default 6144 (0 = use the hierarchy's native fanout; `NaniteShared.cpp`).
- CONTRADICTION (small): digest item 46 says "several LOD levels are tested per step"; the page speaks of hierarchy levels (fanout), not LODs. Treat item 46 as loosely worded.
- Ray tracing CLAS scaling cvars, real prefix `r.RayTracing.Nanite.CLAS*` (e.g. `r.RayTracing.Nanite.CLASBufferSize`; defaults on the 5.9 page, match source): CLASBufferSize 512 MB (max 2048), QualityScaling 1, thresholds 85/70, MinScale 0.3, DemandDriven 1, Reclaim 1. Relevant only with Nanite RT.
- Older general facts (not new): `r.Nanite.ProxyRenderMode`, streaming pool size, `r.Nanite.MaxCandidateClusters` / `MaxVisibleClusters` (ini only; overflow shows as blinking or missing geometry, check `NaniteStats`). Meshes average about 14.4 bytes per input triangle on disk.

## 7. Debugging Shadows
https://dev.epicgames.com/documentation/unreal-engine/debugging-shadows-in-unreal-engine

- Tools are not available in Shipping. VSM is the default shadow method for new projects.
- VSM overview shows six views (Shadow Mask, Clipmap/Mip Level, Virtual Page, Cached Page, Nanite Overdraw, SMRT Ray Count). `r.Shadow.Virtual.Visualize Overview` works only inside a VSM view mode; SMRT Ray Count needs `r.Shadow.Virtual.Visualize.Advanced 1`. `r.Shadow.Virtual.Cache 0` disables caching for A/B. If `r.Shadow.Virtual.Visualize` is set it overrides the menu; set it to `none`.
- CSM-only (not VSM) debugging: `r.Shadow.VisualizeCSMOverlay 1`, `r.Shadow.VisualizeCSMDepthBuffers 1`, `r.Shadow.CSMShadowDepthReuse.FarInterval`. Not compiled for Android/iOS.
- Missing-shadow checklist: Cast Shadows on light and component; past the dynamic shadow distance only objects with Far Shadow render (with VSM, non-Nanite objects past it are culled otherwise); tiny non-Nanite objects are culled; max four overlapping Stationary lights; contact shadows vanish when the occluder is off screen.
- Far shadows: `ShowFlag.VisualizeFarShadowCasters 1`; runtime Blueprint "Set Cast Far Shadow"; cost levers are fewer far cascades, smaller far set, longer reuse interval. Measure with `stat GPU`, `stat ShadowRendering`.
- For Jump Cut (long roads, fast camera): far-distance shadow casters need Far Shadow on, or they vanish at range. Directly useful.

## 8. Dynamic Wind for Nanite Foliage
https://dev.epicgames.com/documentation/unreal-engine/dynamic-wind-for-nanite-foliage-in-unreal-engine

- Experimental plugin (Edit > Plugins > Rendering, restart); SM6 only (below SM6 plants do not move); needs Nanite Foliage (Experimental, `r.Nanite.Foliage`) for PVE meshes; works with Instanced Skinned Mesh components whose Transform Provider is a Dynamic Wind Data asset. Plugin pulls in Interchange and USD plugins.
- Wind data comes from Procedural Vegetation Editor export, USD, or JSON; bone groups cannot be hand-built in the editor. Mode `DynamicWind.Mode` 1 force-based (default), 0 parametric (cheap, no forces).
- Call "Update Wind Parameters" from the Dynamic Wind subsystem when weather changes. Defaults: wind speed 5 m/s (force scales with speed squared), amplitude 1, per-mesh budget of 256 individually simulated instances (promoted plants return to shared motion after 3 s; page-only, UNCONFIRMED in source).
- Force components (Radial, Directional, Swirl, Cone) and Push Capsules (default strength 1000) can react to vehicles; up to four external velocity volumes. Possible Jump Cut use: car-wake blast through roadside grass. Needs PVE-authored skeletal foliage, so probably out of scope for 4 days.
- Debug cvars `DynamicWind.Debug.*`, `DynamicWind.Flutter.DebugIsolate`.

## 9. Lighting the Environment (audit index)
https://dev.epicgames.com/documentation/unreal-engine/lighting-the-environment-in-unreal-engine

- The page fetched as a plain index of lighting topics (Lumen, MegaLights, VSM, ray tracing, fog, post process, and so on) with links; the "audit" disclaimer from the notes was not visible in the fetched text (UNCONFIRMED). No settings or defaults. Linked sub-pages (Lumen GI, Lumen technical details, MegaLights, Virtual Shadow Maps, Volumetric Fog) were NOT read; they are not release-notes links.

## 10. NVIDIA Kimodo (external)
https://research.nvidia.com/labs/sil/projects/kimodo/

- A research motion-diffusion model (trained on about 700 hours of mocap) that generates humanoid (SOMA skeleton) and robot (G1) motion from text plus kinematic constraints; Python API. The page does not mention Unreal and states no licence or hardware needs (UNCONFIRMED). The tie to the UAF Kimodo plugin (digest item 60) comes from the release notes, not this page. Not usable for a 4-day driving game.

## 11. Working with PCG and LLMs Using Unreal MCP
https://dev.epicgames.com/documentation/unreal-engine/working-with-pcg-and-llms-using-unreal-mcp-in-unreal-engine

Fetched live 2026-11-11, title "Working with PCG and LLMs Using Unreal MCP in Unreal Engine | Unreal Engine 5.9 Documentation". Banner: Experimental ("use caution when shipping"). No date on the page. Tags: ai, pcg, mcp. Digest item 55 holds the short form; this adds the rest. `[page]`

- Prerequisite: Unreal MCP running, then load the PCG Toolset (in the agent, or enable the `PCGToolset` plugin in Edit > Plugins), then the PCG graph generation skill. Epic calls loading that skill a mandatory part of session setup. Without it the model tends to misread PCG concepts, overbuild, misuse nodes or parameters, and produce unreliable graph logic. How to load a skill is left to the agent's own docs.
- `Skill_PCGGraphGeneration` is the main skill, for anything expressible as a repeatable rule or spatial computation (vegetation scatter, city blocks, road networks); it knows the full primitive-node library. Use it for a system or pattern, not a one-off placement.
- Extra skills (the agent can scan for them; ask for one by name when it fits): `Skill_PCGShapeGrammarDefinition` (rule-driven module sequences along a path: facades, corridors, street furniture), `Skill_PCGMeshPartition` (only for projects whose landscape is Mesh Terrain: layer order, material weight channels, writing to terrain without breaking priority), `Skill_PCGInstancingOnMeshActor` (detail scattered over a mesh surface by Poisson sampling, avoiding millions of points on large or scaled meshes), `Skill_PCGBiomeCore` (building a biome from scratch: definition, assets, generator, filter, placement; guardrails for the usual "nothing spawns" silent failures).
- Recommended order: load MCP, load the toolset, load the skill, find example graphs, select assets or actors yourself in the Content Browser or Level Editor, ask the model to review references before planning, ask for a plan or graph review before it acts, execute in small steps, and supervise.
- References: the page treats existing example graphs as ground truth (plugin samples, project graphs, production graphs). Plugin samples are under Engine > Plugins > Procedural Content Framework (PCG) > SampleContent. Order of preference: reuse a graph that already solves it, else duplicate and edit a close one, else build new. This also cuts context use. Even though the skill already says this, models still build from first principles, so restate it in the prompt. Example prompts on the page: "Look for an example graph that performs a similar operation", "Match the conventions used in the existing project graphs".
- Explicit context beats discovery: select the assets or actors first, then ask. Without a selection the model may write throwaway Python to inspect content, which costs time and tokens.
- Semantic asset search is part of the MCP workflow (shipped with 5.8 or later); the model can use it alone, but searching in the Content Browser yourself is faster. (Item 24: the SemanticSearchToolset plugin itself was deleted in 5.9 source; reconcile before relying on it. UNCONFIRMED how 5.9 exposes it.)
- Plan first for big graph edits, multi-step flows, attribute work and experiments: ask what references it will use and which nodes it will change. Treat it as supervised: interrupt early, give concrete corrections, and discuss errors with the model before more automated edits.
- Expensive operations (time and context): large or multiple graph analysis, big dataset inspection, broad asset analysis.
- Dataview: the model cannot read PCG point attributes directly. The Dataview workflow (part of the PCG toolset) does the heavy processing outside the context window. The model may not pick it on its own, so name it in the prompt ("Use Data View for the attribute inspection").
- Our own jam rules still win: pre-jam this is reading only, and `jam-cheatsheet-pcg.md` holds the tested call shapes (`GetGraphStructure`, `GetNodeDataView`).

## 12. Run External AI Agents in the Unreal Assistant Panel
https://dev.epicgames.com/documentation/unreal-engine/run-external-ai-agents-in-the-unreal-assistant-panel-in-unreal-engine

Fetched live 2026-11-11, title "Run External AI Agents in the Unreal Assistant Panel in Unreal Engine | Unreal Engine 5.9 Documentation". No Experimental banner and no date on the page. Related links: Unreal MCP, AI Features index. Digest item 85 holds the short form; this adds the rest. `[page]`

- How it works: the editor starts your agent as a local program and talks to it over the Agent Client Protocol (ACP), and also connects the agent to the editor's own Unreal MCP server. While an external agent is selected, chat goes to that agent and not to the Unreal Assistant service; replies, model and tool calls are the agent's, on your own account.
- Install table: Claude Code uses the `claude-agent-acp` adapter (`npm install -g @agentclientprotocol/claude-agent-acp`); Codex uses `codex-acp` (`npm install -g @agentclientprotocol/codex-acp`); Cursor runs `agent acp` (install the Cursor CLI); OpenCode runs `opencode acp` (install the OpenCode CLI); Custom is your own ACP command. The npm adapters come from the ACP project, not Epic.
- Prerequisites beyond item 85: Unreal Assistant and Unreal MCP plugins on (both default on); the All Toolsets plugin, or just the toolset plugins the agent needs (without toolsets it has no editor tools); MCP server running (auto-starts by default, check Model Context Protocol in Editor Preferences); Node.js for the npm adapters; the agent's CLI signed in (`claude login`, `codex login`); restart the editor after installing an adapter.
- Security warning repeated: no authentication, so any local process and any browser page served from localhost, 127.0.0.1 or [::1] can call the editor's tools (see the MCP page's Limitations).
- Open the panel: Window > Unreal Assistant, or Assistant on the right of the status bar.
- Turn on: Edit > Editor Preferences > General > Unreal Assistant > External Agent. Pick the agent in the External Agent dropdown, then enable Use External Agent. Custom adds Custom Agent Command and Custom Agent Arguments; no credentials in either (shown in the panel and written to the editor log), use the agent's environment variables or config file. External Agent Status shows the full path it will run. If it shows an error with an install command: restart first, and only then run the command and restart again.
- Approval: the first time a command runs in a project (enabling or changing the agent) a prompt appears. Allow saves it and starts the agent; Don't Allow turns Use External Agent off and falls back to the Assistant service. Approvals are stored per user, per project and per command line; on Windows in the registry under `HKCU\Software\Epic Games\Unreal Engine\AIAssistant\ApprovedAgentCommands`. The External Agent settings go to `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini` (per user).
- Switching: the Agent selector at the panel's top left lists Unreal Assistant and each external agent; agents with no adapter installed are grayed out; choosing an external agent asks you to confirm (and approve if new); choosing Unreal Assistant switches back with no prompt; each agent keeps its own chat history.
- Prompt bar shows the selected agent's own settings (permission mode, model, reasoning effort) and changes with the agent. Claude Code's permission modes: Manual, Accept edits, Plan, Auto, Bypass permissions. Expand Required Actions to see each MCP call.
- Troubleshooting table: `Could not find <command>` means install the adapter and restart; if it persists, fully quit the Epic Games Launcher (also from the system tray) and start the editor from it again, or use Custom with a full path. `<command> is a relative path`: give a full path or a PATH name. "The Unreal Assistant is unavailable": click Reconnect, else restart (the conversation is kept). Prompt bar shows the previous agent's model: the agent starts on your first message, so send one. Enter adds a newline: click the send arrow. Claude Code in Manual mode stuck on "Waiting for your approval": switch to Auto or Accept edits, start a New Chat, resend. Agent replies but cannot see the editor: check the MCP server is running and that `mcp_servers` in `AIAssistant.json` is not `[]`.
- Not on this page: item 85's "the panel connects to one editor only" is not stated here; UNCONFIRMED (the claim may come from the MCP page). Linux is not mentioned: the registry and `WindowsEditor` paths are Windows-only and the Linux equivalents are UNCONFIRMED.
- Jam use: the Terminal plugin route in the MCP page is the proven path for our Claude Code session; this panel route is optional and pre-jam only a note.

## 13. Using Python with AI Agents
https://dev.epicgames.com/documentation/unreal-engine/using-python-with-ai-agents-in-unreal-engine

Fetched live 2026-11-11, title "Using Python with AI Agents in Unreal Engine | Unreal Engine 5.9 Documentation". No Experimental banner and no date. Related: Scripting the Unreal Editor Using Python, Unreal MCP. Audience: technical artists and tools programmers who already script the editor. Digest items 21, 90 and `python-scripting.md` hold the short form; this adds the rest. `[page]`

- Prerequisites: Unreal MCP connected to an agent, and the Python Editor Script Plugin enabled in the project.
- `PythonScriptingTools` (in EditorToolset): `execute_python` runs in Execute access mode; `search_symbols`, `get_symbol` and `grep_stubs` look up the Python API; `read_me` is meant to be called once per conversation. Script rules: top-level imports only and no star imports (rejected before running, error names the line); the final expression's value is returned (an `await` returns the awaited value); `print` goes to the Output Log under `LogPython`; `await call_tool(name, **arguments)` calls other tools by full name, with results checked against the output schema (a missing field raises a `KeyError` listing the fields). For many edits (a widget tree, dozens of Material Instances) have the agent write one script; keep single tool calls for inspection, screenshots and compile errors. All of this was already in items 21 and 90.
- Writing a toolset: put a module in any plugin's `Content/Python` folder, define the class, register it from the plugin's `init_unreal.py`. Registration pattern from the GeometryToolset plugin (`Engine/Plugins/Experimental/Toolsets/GeometryToolset/Content/Python/geometry_toolset/`): `geometry_toolset/__init__.py` builds `Registration([geometry_ops.GeometryTools])` (from `toolset_registry.registration`), then `init_unreal.py` calls `_registration.register()`. A toolset written once works with every AI feature that reads the Toolset Registry, not just MCP. After a change, reload the module and run `ModelContextProtocol.RefreshTools`; clients may need to reconnect.
- Conventions: decorate the class with `@unreal.uclass()` and derive from `unreal.ToolsetDefinition` (CONFIRMED on this page; the MCP page's omission is not a contradiction). The class docstring is the toolset description, so write it as "when should an agent use this". Tools need `@toolset_registry.tool_call(mode=...)` plus `@staticmethod`; undecorated methods are not advertised. Mode is `unreal.ToolAccessMode.READ`, `WRITE` or `EXECUTE`. Type hints define the JSON schema: `list[T]` maps to `unreal.Array(T)`, `dict[str, V]` to `unreal.Map(str, V)`, `set[T]` to `unreal.Set(T)`, `T | None` makes a parameter optional. Google-style docstrings (`Args:`, `Returns:`) become the schema descriptions. Raise exceptions for errors (returned as tool errors) rather than returning error strings. Tools may be `async def` (`execute_python` is). Tests: a `tests` package inside the toolset's Python package, registered in `init_unreal.py` with `register_test_runner('<package>.tests', '<Automation.Path>')` from `_unittest_runner.unittest_runner_bridge`; they then show in Session Frontend automation under that path (EditorToolset uses `AIAssistant.Toolsets.EditorToolset`).
- Agent skills in Python: derive from `unreal.AgentSkill`, decorate with `@agent_skill` (from `toolset_registry.agent_skill`), class docstring says when to apply it, the `instructions` attribute holds the text. Skill classes are found automatically, with no registration. Example: `PlacingActorsSkill` in `EditorToolset/Content/Python/editor_toolset/skills/placing_actors.py` (snap physical objects to the ground when spawning). Epic's advice: put workflow knowledge in skills, not tool descriptions. C++ and Markdown skills are on the MCP page.
- Pre-jam rule reminder: this is know-how for tool-building. Any toolset or skill we write is a script or agent config (allowed), and not a game asset.

## 14. Unreal Canvas (landing page)
https://dev.epicgames.com/documentation/unreal-engine/unreal-canvas-in-unreal-engine

Fetched live 2026-11-11, title "Unreal Canvas in Unreal Engine. | Unreal Engine 5.9 Documentation". Banner: Experimental ("use caution when shipping"). No date. A short landing page; its own facts were all in sections 1-2 and items 30, 91, 99, with these small extras. `[page]`

- Pitch: a shared workspace where people and agents create and refine content with Unreal Engine and other connected tools; it brings references, generated results, notes and reusable processes together on a canvas, for images, video and 3D. Start from a prompt, reference media or an Unreal scene; the chosen model decides which inputs it needs. It refines your existing project assets with generative content, runs in an editor tab, works from renders and annotations of your scene, and can bring results back as cutouts, meshes, splats and imported assets.
- Requirements as listed: UE 5.9 Preview; NVIDIA GPU with at least 8 GB VRAM; plugins Unreal Canvas Bridge, Unreal Canvas Spatial Annotations and Model Context Protocol; bring your own provider keys and restart the editor after changing them; model approval shown by badges and project policy colors (matches section 2).
- Sub-pages: Overview (section 1) and Getting Started (section 2); no other links.
- Nothing here changes the verdict in item 99: not suited to this jam on an AMD Linux editor.
