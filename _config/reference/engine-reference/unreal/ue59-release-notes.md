# Unreal Engine 5.9 "MegaJam Preview" (5.9.0-preview-1) vs 5.8.4: release notes digest

**Last verified:** 2026-11-11 (links pass: see `ue59-linked-pages.md`). Build read: tag `5.9.0-preview-1`, commit `acf0265`, built from source. `Build.version` says 5.9.0 with Changelist 0, so this is not a promoted build.

Epic says the preview had about a week of development and a short QA pass. Epic advises copying projects, not converting them in place.

## How to read the tags

| Tag | Meaning |
|---|---|
| `[notes-full]` | Epic's 5.9 Preview release notes page, read in full (raw page text) |
| `[docs]` | An Epic documentation page (MCP, Python with agents, Assistant, PCG, Canvas), read in full unless noted |
| `[page]` | A page linked from the release notes, read 2026-11-11 (see `ue59-linked-pages.md`) |
| `[forum]` | Epic forum thread 2852840 (announcement, known issues, replies), all 19 posts read |
| `[source]` | Only a `git diff` of 5.8.4 (`f45729c0b6`) to `acf0265`; no Epic text confirms it |
| `[both]` | Epic text and the source diff agree |
| `[observed]` | Measured on this machine on 2026-11-10 with the 5.9 editor on a copy of a mock project |
| UNCONFIRMED | Claimed somewhere but not verified, or sources disagree. Do not rely on it |

The diff covers 26,024 files (+3.30M / -0.61M lines).

## Sources

- Release notes: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-9-release-notes (last updated 2026-11-09). It has no Linux, Niagara, Audio, Deprecations or Upgrade-notes sections.
- Forum thread (announcement and known issues, 2026-11-09): https://forums.unrealengine.com/t/2852840
- Epic docs read earlier: Unreal MCP in Unreal Editor; Using Python with AI Agents; Run External AI Agents in the Unreal Assistant Panel; AI Features, Tools, and Plugins (index); Working with PCG and LLMs Using Unreal MCP; Unreal Canvas Overview.
- Links pass 2026-11-11: the release notes page was re-fetched and still says "last updated 2026-11-09" (nothing new). Every body link was read in full on 2026-11-11; per-page detail is in `ue59-linked-pages.md`. Read (10 pages; the Canvas landing page `unreal-canvas-in-unreal-engine` and a second full pass of the PCG, External Agents and Python pages were added 2026-11-11, sections 11-14 of the linked-pages file): Unreal Canvas Overview; Getting Started with Unreal Canvas (found via the Overview); AI Features, Tools, and Plugins index; Lumen World Cache; Adaptive Voxel-Based OIT; Nanite Technical Details (5.7 variant as linked, plus the 5.9 variant); Debugging Shadows; Dynamic Wind for Nanite Foliage; Lighting the Environment (index); NVIDIA Kimodo (https://research.nvidia.com/labs/sil/projects/kimodo/).
- Skipped: site chrome only (nav, footer, language picker, login). Failed: none.
- Not read: public roadmap and press articles (the page links none), the sub-pages the Lighting index links to, and the Level Editor toolbar page.
- Links pass corrections: the notes' Nanite link points at the 5.7 page, which has no culling section (the 5.9 page does); item 46's "LOD levels per step" is really hierarchy fanout; Lumen World Cache has no project setting (config only, Inline RT mode unsupported); AVBOIT is also config only.

## 1. Editor and Linux

1. The Linux editor failed at start on Wayland ("InitSDL() failed ... did not add any displays"). Fix: `SDL_VIDEODRIVER=x11`. `[observed]`
2. CORRECTION: the `-sdlvideodriver=` flag and the `[Linux.SDL] VideoDriver=` ini key are not new in 5.9; identical code already ships in 5.8.4. Priority: `-RenderOffScreen`, then `-sdlvideodriver=`, then the `SDL_VIDEO_DRIVER` / `SDL_VIDEODRIVER` environment variable, then the ini, then auto. Source: `LinuxPlatformApplicationMisc.cpp`. `[source]`
3. In the same file the "IsUsingWayland before SDL init" warning now fires only when the app can render, and a window-destroy helper was renamed (`DeferDestroyWindow` to `RequestDestroyWindow`). `[source]`
4. `LinuxApplication` input-device code was refactored into shared helpers; there is no user setting. `[source]`
5. Linux now defaults `[Audio] AudioCaptureModuleName=AudioCaptureSDL` (microphone through SDL); the AudioCapture plugin gained an AudioCaptureSDL dependency. Source: `BaseLinuxEngine.ini`, `AudioCapture.Build.cs`. `[source]`
6. ICU data moved from `icudt64l` to `icudt78l` (Linux and Windows configs). `[source]`
7. Bundled SDL is 3.4.4. `[observed]` The source tree does not show the version (`SDL3.Build.cs` is unchanged), so it is UNCONFIRMED in source.
8. Linux build (source builds only): the UBT linker now uses import-library stub `.so` files in an "ImportLib" folder (was "Prelink") for single-pass linking with UBA; a new Linux ray-tracing mode "SimplifiedMaterial" (inline RT plus a simplified material closest-hit shader). `[source]`
9. `RunUAT.sh` looks for `AutomationTool.csproj` one folder deeper (`Source/Programs/AutomationTool/AutomationTool/`). `[source]`
10. Editor additions: a Map Check subsystem, functions to replace actors with an asset or class, preview-platform options in Editor Preferences, updates to Data Validation, the Curve Editor and user asset tags, Common UI editor passthrough commands, and "Forge" web-based designer tools. `[notes-full]`
11. Sequencer: "marks and mark ranges" replace marked frames (existing marked-frame data and usage changes); new Blueprint nodes and preferences for duration, snapping and playback. `[notes-full]`
12. UI / UMG: widget components output depth and velocity; editable text gets selection events and colours; list and tile views get orientation and selection options. `[notes-full]`
13. Core engine: a source-control option to validate soft dependencies; updated bandwidth-manager settings (item 66). `[notes-full]`

## 2. AI, MCP and toolsets

14. Unreal MCP (Experimental) starts with the editor by default: `bAutoStartServer=True` under `[/Script/ModelContextProtocol.ModelContextProtocolSettings]` now ships in `BaseEditorPerProjectUserSettings.ini`; 5.8.4 had no such line. `[both]`
15. Default port is 8000, URL path `/mcp`, bound to 127.0.0.1. A different port is a project or user override. `[docs]` `[source]`
16. The settings class moved from module `ModelContextProtocolEngine` to `ModelContextProtocol`. The old ini section `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]` still loads through a redirect (`ConfigRedirects.ini`, the plugin's `DefaultModelContextProtocol.ini`) but logs a deprecation warning; write the new section name. CAVEAT: the docs still list both modules as runtime modules, so which one owns the class in the final release is not settled. The docs place the settings in Editor Preferences > Agentic Workflows > Model Context Protocol. `[source]` `[observed]` (warning logged)
17. New settings (category "Model Context Protocol"): `ServerUrlPath`, `ServerPortNumber`, `bAutoStartServer`, `AdditionalAllowedOrigins`, `MaximumProtocolVersion` (default 2026-07-28; not in the docs table), `bEnableToolSearch` (default true), `bDumpMediaToDisk` (false; writes tool-result images and audio under `Saved/ModelContextProtocol/`), user `Instructions`, plus a project-level settings class in `DefaultGame.ini` whose Instructions go to clients (clients must reconnect to pick them up). `[both]` `[docs]`
18. Tool-search mode (`bEnableToolSearch=true`, the default) exposes four meta-tools: `list_toolsets`, `describe_toolsets` (plural), `describe_tools`, `call_tool`. 5.8.4 had `list_toolsets`, `describe_toolset` (singular) and `call_tool`, so `describe_toolset` is gone. `describe_toolsets` takes toolset names (with `include_schemas:true` it returns schemas); `describe_tools` takes `Toolset.Tool` names (a bare name for a top-level tool) and errors per unknown name; `call_tool` without a toolset name calls a top-level tool. With `bEnableToolSearch=false` every tool is listed up front (a large first response; the docs say not to rely on it). `[observed]` `[source]` `[docs]`
19. `call_tool` arguments: required string `tool_name`; optional string `toolset_name`; optional `arguments`, which must be a JSON object (anything else is rejected with "Expected object parameter: arguments"). It cannot call itself. `[source]`
20. A `CodeBlock` is a struct with two properties: `Content` (the code) and `Language` (enum: Unspecified, Cpp, Verse, Python, Markdown, HTML, CSS, JavaScript, TypeScript). A plain string cannot import into it. Send `{"toolset_name":"PythonScriptingTools","tool_name":"execute_python","arguments":{"script":{"Content":"print(1)","Language":"Python"}}}`. Key case is not significant on import; confirm names with `describe_tools`. `[source]` `[observed]`
21. `PythonScriptingTools` (listed in the docs as part of EditorToolset) has `execute_python` (access mode Execute), `read_me` (call once per conversation), `get_symbol`, `search_symbols`, `grep_stubs`. `[observed]` `execute_python` takes `{"script":{"Content":"...","Language":"Python"}}` and returns the value of the last expression (it returned `"5.9.0-0+UE5"`); `print()` goes to `LogPython`, not the result. `[docs]` adds: all imports must be top-level and `from x import *` is rejected before running; a final `await` returns the awaited value; a script can call other tools with `await call_tool(full_tool_name, **arguments)` and results are checked against the output schema (a missing field raises KeyError listing the fields); for many edits use one script. The tool's Python source is not in the checkout: UNCONFIRMED in source.
22. Toolsets are off by default in new projects although the server is on: `AllToolsets.uplugin` is `EnabledByDefault=false` (known issue UE-412135; the forum lists AllToolsets, EditorToolset, BlueprintToolsets, ConsoleToolset and LiveCodingToolset as off; the docs setup steps also say to enable All Toolsets). Workaround: Edit > Plugins > "All Toolsets", or add an `AllToolsets` entry to the `.uproject` with `TargetAllowList: ["Editor"]`; restart the editor and reconnect the agent, once per project. `[both]` `[forum]`
23. AllToolsets references 43 plugins; 502 files were added under `Plugins/Experimental/Toolsets` (new: Blueprint, Console, FileSystem, Geometry, Input, KnowledgeBase, MediaToolset, MetaSound, MovieRenderPipeline, NavMesh, Perf, RewindDebugger, SceneCapture, WidgetAnimation, WidgetStaticAnalysis, AgentPlugin; existing: EditorToolset, StateTree, PCG, Niagara, Physics, MVVM, TextureGraph). Docs add example toolsets with runtime-callable tools: NavMesh, Scene Capture, Console, Widget Finder, Perf (CSV, GPU profiler, Stats), Input; GASToolsets (AttributeSetToolset) is experimental and off by default; PCGToolset is enabled through Edit > Plugins or by the agent. `[both]` `[docs]`
24. CONTRADICTION, open: the forum announcement says a new Fab toolset lets agents search the catalog, browse your library and install free or purchased assets. The release notes only mention "Fab image and mesh generation" (a different thing). `Plugins/Experimental/Toolsets/UE59-DISABLED.md` lists FabToolset (and CommonUI, CaptureManager, all MetaHuman toolsets, MassGameplay, CrashDiagnostics, MutableAgentSkills) as NOT part of 5.9. SemanticSearchToolset and UMGToolSet were deleted (UMG tools now register from UMGEditor). The notes also say "Unreal MCP and Semantic Search add server and provider settings"; the PCG docs say semantic asset search shipped in 5.8 or later. Treat the Fab toolset as UNCONFIRMED / absent. `[source]` vs `[forum]` vs `[notes-full]`
25. New plugins (from added `.uplugin` files): AgentCapability, AgentLook, KnowledgeBase (+KnowledgeBaseToolset), LoreCore, LoreSourceControl, MCPClientToolset (manages external MCP servers), ToolsetRegistry updates (controls which toolsets agents may use), WidgetFinder, WidgetHelper, SlateDebugger, DebugDraw, Doodle, GaussianSplat, Provenance (AssetProvenance, C2PA), UnrealCanvas (Bridge, Graph, Annotations), ModularTestFramework / Resolver / RunnerEditor, GraphDsl, UAF (AnimGen, ACL, DefaultNotifies), Kimodo, AnimGenOffline, NNERuntimeLiteRT, PolarisSurveys, IoStorePrioritization, OpenXR RenderModel / SpatialEntities, SharedMemoryMedia, MassCharacters, UnrealConsoleRuntime. `[source]` (many also in the notes)
26. Unreal Assistant: "AI Assistant" was renamed "Unreal Assistant"; it is now `EnabledByDefault=true` and no longer editor-only (new AIAssistantEditor and FileSandbox modules). It works with external agents (Claude Code, Codex, Cursor, OpenCode), with notification preferences, hand-off to an external agent through a custom command, a tool-access level (Ask / Read / Edit / Auto / Full), a live AI-processed viewport preview and custom ACP agents (item 85). `[both]`
27. The MCP client-config helper offers a client choice (All / Claude Code / Codex / Cursor / Gemini / VS Code; default Claude Code); `ModelContextProtocolClientConfig.cpp` was rewritten. `[source]`
28. The MCP server took about 195 s to come up on the jam test project. `[observed]` No source reason found (UNCONFIRMED); plausible causes are registering many toolset plugins and importing the Python toolset on first start.
29. Knowledge Base: query knowledge from live engine state or markdown files. `[notes-full]`
30. Unreal Canvas (Experimental): a shared workspace for people and agents, with text / image / video / mesh generators driven by a prompt and a chosen service (bring your own API keys); web app plus in-editor tab (Tools > Unreal Canvas); Canvas Bridge exposes Movie Render Graph as MCP tools; Spatial Annotations. Details in item 91. `[both]`
31. Generative integrations named in the notes: Fab image and mesh generation, chat completion, ElevenLabs voice, Google Gemini, Claude Code; Learning Agents observation functions; NNE LiteRT runtime. `[both]`

## 3. Python

32. Python can manage extra search paths (`IPythonAdditionalPaths`). `[both]`
33. New Python wrappers: InstancedStruct, PropertyBag, Variant, element editor, write scope; a `PythonScriptPluginTests` module. `[source]`
34. Slate Qt Bridge embeds PySide6 widgets in editor windows. `[notes-full]` Not found in the diff: UNCONFIRMED in source.
35. The notes say the old Python Foundation Packages plugin was removed. At `acf0265` its `.uplugin` still exists and is identical to 5.8.4. Removal is UNCONFIRMED (maybe later, or only in the Launcher build). `[notes-full]` vs `[source]`
36. New Blueprint and Python libraries edit Blueprints, chooser tables, StateTrees and Dataflow graphs. The wider list of Python APIs (audio, MetaSounds, modeling, physics, Niagara, materials, PCG, networking, UI) comes from the forum announcement only. `[notes-full]` `[forum]`
37. Bundled Python is unchanged (3.11 under `Engine/Binaries/ThirdParty/Python3`). `[source]`
38. Known: UE-411502 Python Blueprint root swaps can crash the editor (use a C++ base class that owns the root); UE-410941 undo after scripted Deformer Graph additions can crash. `[forum]`

## 4. Blueprint, gameplay and world building

39. Editor Utility Blueprint and Python functions to create and edit Blueprints, graphs, nodes and variables (BlueprintToolsets). `[both]`
40. Control Rig can be referenced as an asset, not only a class (hierarchy-key helpers, mirroring edit-mode options, new Dynamics / Physics options); Blueprint nodes to check, convert and spawn rigs; the older Control Rig nodes are deprecated in favour of asset-reference versions. `[notes-full]`
41. StateTree tasks, considerations, evaluators and global tasks are editable from Blueprint / Python; World Partition gets many Blueprint functions; Data Layer nodes get child layers and a can-add-actor check; navmesh can build progressively (tiles per tick) and keep tiles outside the invoker radius. `[notes-full]`
42. GraphDsl: a text-based language for authoring graph assets (99 new files). `[both]`
43. Mesh Partition: simplification settings, a ray-tracing proxy option, better PCG interop. Shallow-water rivers: exclude actors from capture, collision resolution, a water-input paint tool. Mass Characters: traits for interpolation and visualization, selective pawn replication, a game-feature action. `[notes-full]`

## 5. Rendering and Vulkan

44. Lumen World Cache: caches lighting from ray hits by path tracing at runtime instead of mesh cards, so tiny, large, spline, skeletal and WPO meshes work without card cooking. Needs hardware ray tracing; enabled per project. A forum reply says its docs page has typos. `[notes-full]` `[forum]`
45. Adaptive Voxel-Based OIT (AVBOIT; the notes heading mistypes it ABVOIT): correct blending of overlapping glass, smoke and particles, Nanite and non-Nanite, coloured glass. Translucent materials must output only their own colour. `[notes-full]`
46. Nanite culling: simple and complex (skinned, spline, WPO) instances are handled separately and several LOD levels are tested per step. Automatic; gains grow with scene size. `[notes-full]`
47. Shadow debugging: VSM Overview mode, cascaded-shadow-map views (cascade colouring, depth tiles), a Far Shadow view; far shadows can update at their own rate and be toggled per component. `[notes-full]`
48. Dynamic Wind for Nanite foliage (Experimental plugin): GPU per-bone sway and flutter, shared simulations that switch to their own sim under local forces (radial, swirl, cone, directional, character brush), a cheaper stylized mode. `[notes-full]`
49. Vulkan RHI (40 files changed): new `VulkanDeviceAnalytics`; the deferred-delete queue is processed once per frame when `GVulkanNumFramesToWaitForResourceDelete > 0`; the async ray-trace dispatch flag is computed after vendor compatibility checks; AMD compatibility-mode flag refactor; an Android hardware-buffer texture helper. No Linux-only Vulkan change found. `[source]`
50. The GPUReshape ThirdParty plugin was removed while 2,113 GPUReshape ThirdParty files changed. `[source]`
51. The Web target renders through WebGPU using the mobile renderer (Dawn build script under `Engine/Platforms/Wasm`). `[both]` `[forum]`
52. Known: UE-411439 Mobile Forward metallic surfaces turn black near reflection captures (web). Workaround in item 93. `[forum]`

## 6. PCG

53. New PCG nodes: Concave Hull, Trapezoidal Decomposition, Find Closest Point On Spline, Editor Switch, Get Landscape Grass Types, Navigation Mesh Sampler, Editor Blueprint Element. The notes list only Concave Hull. `[source]` `[both]`
54. Blueprints can read and write custom HLSL node source; script functions add and validate graph edges; PCGToolset moved to the new registry. `[both]`
55. PCG with LLMs (docs): load the PCG toolset, then the PCG graph generation skill (called mandatory); extra skills `Skill_PCGShapeGrammarDefinition`, `Skill_PCGMeshPartition`, `Skill_PCGInstancingOnMeshActor`, `Skill_PCGBiomeCore`; reuse example graphs from the PCG plugin's SampleContent; plan first, execute step by step; use the Dataview workflow for point attributes (keeps data out of context). `[docs]`

## 7. Niagara

56. The notes have no Niagara section. The source adds: a Ribbon data interface, asset-operation APIs for systems, renderers and simulation stages (with tests), an edit API for simulation stages, a Niagara Blueprint preview tab / viewport / controller, data channel editor utilities, a shader file hash; the Cascade plugin also changed (275 files). `[source]`
57. The UAF notify handler "Play Niagara Effect" and Python Niagara APIs. `[notes-full]`
58. Removed ini keys `bCustomCameraAlignEmitter` and `CustomCameraAlignEmitterDistance` (`BaseEngine.ini`). `[source]`

## 8. Animation

59. IK Retargeter: Proximity IK (limbs and contacts relative to the body), Pelvis Volume (pelvis across proportions), Limb Twist (spreads twist). `[notes-full]`
60. Unreal Animation Framework (UAF, 1,540 changed files): node and layering settings, a notify system with Play Sound and Play Niagara Effect handlers, StateTree conditions (Animation Is Looping / Time Remaining), Chooser, Pose Search, Warping, Mirroring; UAFAnimGen (AI animation generation), Kimodo, AnimGenOffline plugins; chooser tables buildable from Blueprint / Python. `[both]`
61. Smaller: morph target tools, Sequencer animation tools, IK Rig, Motion Warping, Rig Mapper, Ease Curve, Animation Insights. `[notes-full]`
62. Known: UE-411097 Dataflow Add / Remove Option Pin crashes with a comment box selected. `[forum]`

## 9. Audio

63. The notes have no audio section. Source: AudioMixer changed in 115 files together with MetaSound, Synesthesia and AudioCapture; Linux audio capture through SDL (item 5); Python audio / MetaSound APIs (item 36); a MetaSoundToolset. `[source]`
64. Web: an audio-thread single-thread setting; iOS 26 memory issue UE-412148 (item 93). `[forum]`

## 10. Packaging, Windows and platforms

65. Windows SDK: main 10.0.26100.0 (was 10.0.22621.0), minimum 10.0.22621.0 (was 10.0.19041.0). `Windows_SDK.json`. `[source]`
66. MSVC: the VS2026 toolchain 14.51 (18.10.x) is flagged as an optimizer miscompile with memory corruption with no fixed version yet, and `Windows_SDK.json` now lists `14.51.0-14.51.99999` under `BannedVisualCppVersions`, so UBT refuses a 14.51 toolchain. The Visual Studio 2022 minimum rose from 17.8 to 17.14, the required components now name the Windows 11 SDK 26100 and `Microsoft.Component.CodeAnalysis.SDK`, and the .NET 4.8 targeting pack replaces 4.6.2. `[source]` Bandwidth manager (`BaseEngine.ini`): `net.DLBW.RolloutChance=100` and `net.DLBW.Enforcement=False` added, `RolloutPercentage` / `EnforceDistributionAllocation` removed, `MinimumGameplayReservedBandwidthInKbps=1000`; `UseSeperateBulkDataFiles` and `IgnoreInlineBulkDataReloadEnsures` removed. `[both]`
67. DDC: default graphs drop the "Local" and "Shared" file stores, leaving ProjectPak, EnginePak, ZenLocal, ZenShared and Cloud; the first open of a project may rebuild the DDC through Zen. `BaseEngine.ini`. `[source]`
68. iOS 15 and 16 are no longer supported (enum redirect to `IOS_Minimum`); an iOS home-indicator option. `[both]`
69. Experimental Web (WebAssembly / WebGPU) target: needs a source build and a C++ project; Chrome works best; cooks are long; 160 source files under `Engine/Platforms/Wasm`. `[both]` `[forum]`
70. Turnkey: `ExecuteBuild.cs` and `Turnkey.Automation.csproj` changed; AutomationTool changed in 96 files (9 added, 10 deleted, project moved one level); no Windows packaging flag change found. `[source]`
71. A bundled Modular Test Framework for scoped plugin tests; UnrealToolbox, Horde and UBA changes (source-only tooling). `[both]`

## 11. Deprecations and breaking changes (summary)

72. MCP ini section renamed (item 16). `[source]`
73. Old Control Rig nodes deprecated (item 40). `[notes-full]`
74. Python Foundation Packages removal: UNCONFIRMED (item 35).
75. Sequencer marked frames replaced by marks and mark ranges (item 11). `[notes-full]`
76. iOS 15/16 dropped, Windows SDK minimum raised, DDC Local/Shared stores gone (items 65, 67, 68). `[source]`
77. SemanticSearchToolset and UMGToolSet plugins deleted (item 24). `[source]`
78. Epic's advice: copy projects, do not convert in place. `[forum]`

## 12. Known issues from Epic and forum replies

79. Mac and Linux premade and Launcher builds miss part of the Wasm support files; use a source build; a QFE was planned for the week of 11-09. `[forum]`
80. UE-412135: toolsets off in new projects (item 22). `[forum]`
81. Web: UE-412003 lost saves; UE-411671 crash over 2 GB Wasm memory; UE-411514 / 412029 mobile startup crashes; UE-412148 iOS 26 memory; UE-411884 rotate during load; UE-411441 AMD browser GPU crash; UE-411710 second Lyra match crash; UE-411672 Bink unsupported on web. `[forum]`
82. Web build and hosting: itch.io limits (500 MB / 200 MB); UE-412027 no IpNetDriver for `--web-ready` projects; UE-411774 trim profile failures; UE-411525 stale content with `-NoCleanStage`; UE-411308 / 411939 `file://` isolation (use `Play_.bat` or `serve.py`); UE-411973, UE-411974, UE-412037. `[forum]`
83. Editor: UE-411502, UE-410941, UE-411097 (items 38, 62). `[forum]`
84. Forum replies are mostly negative about the AI direction and doc quality; one is supportive; Epic did not reply. A user asked whether jam participants should use 5.9 or 5.8 and got no answer (2026-11-10). The build is in the Launcher under "Other builds". The notes' Lighting Documentation Audit (72 pages, AI-assisted: 671 fixes, 162 additions, 76 removals) still awaits expert sign-off, so lighting docs may be wrong. `[forum]` `[notes-full]`

## 13. Detail from the full documentation read

85. External agents in the Assistant panel (Window > Unreal Assistant): Claude Code (adapter `claude-agent-acp`, installed with npm from `@agentclientprotocol/claude-agent-acp`), Codex (`codex-acp`), Cursor (`agent acp`), OpenCode (`opencode acp`), and a custom command (never put secrets in it; it is logged). The editor starts the agent locally over the Agent Client Protocol and wires it to its own MCP server. Enable under Editor Preferences > General > Unreal Assistant > External Agent. Per user and per project, with an approval prompt per command; each agent keeps its own chat history; needs Node.js and the agent's own login; restart the editor after installing an adapter (PATH is read at startup). Troubleshooting: Claude Code Manual mode can hang on "waiting for approval" (use Auto or Accept edits, start a new chat); Enter inserts a newline (click the send arrow); an `AIAssistant.json` with empty `mcp_servers` hides the editor; the panel connects to one editor only. `[docs]`
86. MCP security: no authentication; loopback only by default; the Origin allow-list is localhost, 127.0.0.1 and [::1] plus Additional Allowed Origins (each widens DNS-rebinding exposure); setting `[HTTPServer.Listeners] DefaultBindAddress` to any exposes it to the network. Transports: Streamable HTTP and SSE only (no stdio, no WebSocket). Tool calls run one at a time on the game thread. `[docs]`
87. Server control: console commands `ModelContextProtocol.StartServer [port]`, `StopServer`, `RefreshTools`, `GenerateClientConfig <ClaudeCode|Cursor|VSCode|Gemini|Codex|All>`; flags `-ModelContextProtocolStartServer` (also required in commandlets, which never auto-start) and `-ModelContextProtocolPort=N` (1-65535; use for agent-launched second editors). CVars: `WrapPODToolResultsInObject` (true), `AudioResultOggFormat` (false), `ProgressIntervalSeconds` (1.0), `PaginationPageSize` (0 = off), `EnableAnalytics` (true). `[docs]`
88. Client config: `.mcp.json` goes in the project root for installed builds, or the ENGINE root for source builds (copy the entry into the project if you launch there). The entry name is always `unreal-mcp`; JSON configs merge and update the URL, the Codex TOML is write-once. Several editors need one port and one entry name each. Every `initialize` result carries instance info (id, PID, engine version, branch, changelist, project, folders) in `_meta["com.epicgames.unrealengine/instance"]`; `serverInfo.name` is `unreal-mcp`. `[docs]`
89. Long calls: Claude Code gives up near 120 s; send a `progressToken` in `_meta` for heartbeats; `notifications/cancelled` cancels; split Live Coding builds, big scripts, asset scans and automation runs. Agents can restart the editor with `EditorToolset.EditorAppToolset` `ExitEditor` (`bDiscardUnsavedChanges`) and reconnect. ImportFile tools (Sound Wave, Texture, Static / Skeletal Mesh, Data / Curve / String Table) take `bReplaceExisting` and `bSave`, both false by default, and only replace assets of the same class. `[docs]`
90. Extending: toolsets derive from `UToolsetDefinition` / `unreal.ToolsetDefinition` and register with the Toolset Registry (Python: a module under a plugin's `Content/Python`, `Registration([...]).register()` from `init_unreal.py`, tools decorated `@toolset_registry.tool_call(mode=unreal.ToolAccessMode.READ/WRITE/EXECUTE)` plus `@staticmethod`; async allowed; raise on errors; tests via `register_test_runner`). C++ metadata: `AICallable`, `AIRuntimeCallable` (only these ship in cooked builds), `AIAccessMode` Read / Write / Execute (default Execute, maps to `readOnlyHint`), `AIIgnore`, `UsesInstanceDispatch` / `UsesInstanceArgument`. Direct `IModelContextProtocolTool` registration exists; Resources are supported but the engine ships none; Prompts are unsupported. A new C++ UFUNCTION needs an editor restart (Live Coding handles edited bodies); Python needs a module reload plus RefreshTools. Agent skills: Python `@agent_skill` classes, C++ `UAgentSkill`, or `SKILL.md` folders in `<Plugin>/Skills`, `<Project>/Skills`, `Engine/Extras/AgentTools/Skills`; CreateSkill / UpdateSkill tools exist. Cooked and Shipping builds can host an MCP server (`-ModelContextProtocolStartServer`) exposing only `AIRuntimeCallable` tools (cooked games are not read-only). Debug with `LogModelContextProtocol` (Verbose), `LogToolsetRegistry` and the MCP Inspector (`npx @modelcontextprotocol/inspector` against `http://127.0.0.1:8000/mcp`). A Claude Code plugin "unreal-mcp" with a create-toolset skill is mentioned. The Terminal plugin can host the agent CLI inside the editor (set `TERM=xterm-256color`; start in the folder holding `.mcp.json`). `[docs]`
91. Unreal Canvas (Experimental; unrelated to the Canvas asset or UMG Canvas Panel): the Canvas Bridge plugin installs and launches a local server and the editor tab (Tools > Unreal Canvas); enabling it also enables Spatial Annotations, Canvas Graph, Unreal MCP, rendering, media and Python. The editor sends viewport renders and passes (Beauty / Depth / Normal), sequence renders, a live viewport stream, selected assets and annotations; Canvas can create viewport-facing cutout actors (editor-only, remove before cooking), import mesh / image / Gaussian-splat / rigged files and place assets. Side effects: default import root `/Game/Merlin`; files under `Saved/UnrealCanvasSequenceRender` and `Saved/UnrealCanvasSceneState`; annotating an actor enables custom depth and a stencil (removal resets it to 0); optional component downloads and network use; cloud providers bill per call; the local auto-rig route (SkinTokens) needs model files and a supported GPU. `[docs]` (second half of the page grepped, not read in full)
92. Announcement (2026-11-09): the first UE release built mostly with agentic workflows (a few people directing agent fleets; AI tooling ported from the UE6 branch; the Web platform written by agents from the retired UE4 HTML5 platform); about a week of development and short QA; parts of the web renderer are prototypes; the jam runs Nov 12-15; download from the Launcher ("Other builds"), GitHub, or a Linux link in the post. It says MCP "delivers more reliable connections" and covers rendering, source control, profiling, debugging, gameplay testing, geometry, audio, UI and level creation, plus Lore integration for agents managing changes. `[forum]`

## 14. Known-issue workarounds from the forum

93. QFE for the missing Mac / Linux Wasm files planned for the week of 11-09. UE-412148 (iOS 26): disable Project Settings > Platforms > Wasm > Threading and sound > iOS > Audio Thread, or open with `?audiothread=0` (iOS 27 is fine). UE-411439: enable Project Settings > Rendering > Mobile > Clustered reflections (Forward), restart, recook (Mobile Deferred is unaffected). BC / DXT textures are unsupported on Android and iPhones older than 15 Pro: cook ASTC (`-cookflavor=ASTC` plus `-WasmAddTextureSet`). UE-412027: remove "Wasm" from the PlatformDenyList of OnlineSubsystemUtils and OnlineSubsystemNull (`--web-ready` projects only). UE-412003: append `-project=../../..//<name>.uproject` to Page Args. UE-411514 / 412029: keep single-threaded mode and use Shipping on Launcher builds. UE-412037: leave `bSimd128` / `bSseEmulation` / Malloc at defaults on the Launcher engine. `[forum]`

## 15. Additions from the links pass (2026-11-11; details in `ue59-linked-pages.md`)

94. Lumen World Cache is config only: `r.Lumen.WorldCache.Supported=1` under `[SystemSettings]` plus editor restart; `r.Lumen.WorldCache.Allowed` toggles at runtime. Needs hardware RT in Full or Simplified Material mode (not Inline), SM6, wave ops, and on D3D12 SM 6.6 / Binding Tier 3. Opaque only; no Water, RT translucency or foliage transmission. `[page]`
95. AVBOIT: `r.OIT.Method=1` plus `r.AVBOIT.NonNanite=1`; SM6 desktop, no MSAA; materials must not sample SceneColor; refraction wrong. `r.AVBOIT.Support` defaults to 1 and builds an extra shader variant per translucent material, so set it 0 if unused. Experimental. `[page]`
96. Nanite culling cvars (5.9 page): `r.Nanite.Culling.Classification`=1, `r.Nanite.Culling.AdaptiveFanoutThreadBudget`=6144. The notes' link goes to the 5.7 page, which lacks this. `[page]`
97. Shadows: past the dynamic shadow distance, only objects with Far Shadow enabled cast; with VSM, non-Nanite objects there are culled otherwise. Debug tools are absent in Shipping. `[page]`
98. Dynamic Wind needs SM6, Nanite Foliage (Experimental) and PVE or USD wind data; default per-mesh budget 256 simulated instances. Probably out of scope. `[page]`
99. Unreal Canvas: local models need an NVIDIA GPU with 8 GB or more (Depth Anything is Windows x64 only), cloud providers need your own keys and bill per call; cutout actors are editor-only and must be reviewed before cooking. Not suited to this jam on an AMD Linux editor. `[page]`
100. Kimodo is a research model; the page does not mention Unreal. `[page]`

## Open questions

- Whether the 5.9 Preview is required for or recommended by the MegaJam: Epic gave no statement. UNCONFIRMED; check the jam rules page.
- The final owner of the MCP settings class (item 16), the Fab toolset (item 24) and Python Foundation Packages removal (item 35).
