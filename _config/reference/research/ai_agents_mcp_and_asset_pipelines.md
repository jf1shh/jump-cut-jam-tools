# AI-Agent-Driven Unreal Development, MCP Servers, Asset Pipelines, and Linux Constraints (as of 2026-10-27)

Research scope: practical, verified reference for a solo dev (Claude Code + local models, CachyOS Linux, AMD RX 9070 XT) entering the 2026 Epic AI MegaJam (Nov 12-15, 2026) with regular Unreal Engine (not UEFN).

Method note: GitHub API access was blocked in this session, so star counts come from fetched GitHub pages (WebFetch) and "last commit" dates come from shallow `git clone` of each public repo performed on 2026-10-27. Several pages could not be read (listed under Gaps in each section and summarized in the final section).

---

## Q1. Official Epic AI features: in-editor AI, Unreal MCP (UE 5.7 / 5.8), MegaJam-recommended setup, UEFN AI

### Takeaway
UE 5.8 (released ~June 2026, patch 5.8.1 by late July 2026) ships Epic's own **Experimental "Unreal MCP" plugin** (`ModelContextProtocol`) that serves a local HTTP MCP endpoint at `http://127.0.0.1:8000/mcp` and can auto-generate a Claude Code `.mcp.json`; this is the setup Epic's MegaJam page explicitly points entrants to ("connect your agents to the editor with Unreal MCP"). UE 5.7 (Nov 2025) only added an in-editor Q&A-style AI Assistant, not an agent bridge.

### Cited Findings

**Version numbers and dates**
- UE 5.7 was released on/around 12 November 2025 (article dated 12 Nov 2025 says Epic "has officially released" 5.7). — [Digital Production](https://digitalproduction.com/2025/11/12/unreal-engine-5-7-foliage-pcg-and-in-editor-ai/); also [CG Channel, Nov 12 2025](https://www.cgchannel.com/2025/11/unreal-engine-5-7-five-key-features-for-cg-artists/) (search result, not opened)
- UE 5.8 "is now available" per Epic's State of Unreal 2026 recap dated June 17, 2026; it is "the last planned major UE5 release" (Epic reserves the option of a 5.9). Production-ready in 5.8: MegaLights, Audio Insights, Dataflow for Chaos Cloth, Live Link Hub, Iris, Movie Render Graph; Experimental: Mesh Terrain. — [Epic: State of Unreal 2026 top news](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show)
- UE 5.8.1 hotfix existed by July 30-31, 2026 (forum users report updating 5.8 -> 5.8.1). — [Epic forums RX 9070 XT thread](https://forums.unrealengine.com/t/ue-5-8-vulkan-on-linux-triggers-vk-error-device-lost-gpuvm-read-fault-on-amd-rx-9070-xt-with-radv/2730749); [Convai forum](https://forum.convai.com/t/convai-fails-to-load-when-updating-from-ue-5-8-to-5-8-1/6436)
- Unreal Engine 6: Epic is "targeting an Early Access release at the end of 2027"; focus on moving gameplay programming to Verse. — [Epic: State of Unreal 2026](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show)

**UE 5.7 in-editor AI Assistant**
- "A new AI Assistant now lives directly within the Unreal Editor" — answers technical questions, gives C++ snippets and step-by-step instructions; described as not intended to replace documentation; article does not describe it editing/acting on the project, does not name the model; "Epic has not disclosed details about data handling or privacy." — [Digital Production](https://digitalproduction.com/2025/11/12/unreal-engine-5-7-foliage-pcg-and-in-editor-ai/)

**UE 5.8 Unreal MCP plugin (official, Experimental)**
- Epic: new Experimental Model Context Protocol plugin lets developers connect models "such as Claude" directly to UE projects; interface is open (Claude, Gemini named). — [Epic: State of Unreal 2026](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show)
- Epic demoed "Claude CoWork" working in an Unreal project at State of Unreal 2026 (~42 min into presentation); article claims built-in access to Blueprints, assets, levels, materials, meshes. — [Edge Online recap](https://knowledge.edge-online.com/p/ai-goes-native-in-unreal-engine-the-five-main-takeaways-from-state-of-unreal-2026)
- **5.9 update (2026-11-11):** the bullets below are 5.8-era. Where they differ, the UE 5.9 table in `knowledge-base.md` ("Official Unreal MCP setup reference") wins: four discovery meta-tools, auto start on by default, Blueprint and Widget Blueprint tools, source builds write `.mcp.json` to the engine root.
- Official doc "Unreal MCP in Unreal Editor": status Experimental ("use caution when shipping with it"; APIs/data formats may change). Plugins: **Unreal MCP** (`ModelContextProtocol`), **All Toolsets**, **Toolset Registry** (auto-enabled dependency), optional **Terminal** (runs an AI agent inside the editor). — [Epic docs: Unreal MCP in Unreal Editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- Setup steps (verbatim from doc): Edit > Plugins > enable "Unreal MCP" and "All Toolsets" > restart. Start server: console `ModelContextProtocol.StartServer` (or `... 8000`), or command-line `-ModelContextProtocolStartServer`; port override `-ModelContextProtocolPort=N`; stop with `ModelContextProtocol.StopServer`; Auto Start Server pref is off by default (Edit > Editor Preferences > General > Model Context Protocol). — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- Claude Code config: console `ModelContextProtocol.GenerateClientConfig ClaudeCode` writes `.mcp.json` to project root: `{"mcpServers":{"unreal-mcp":{"type":"http","url":"http://127.0.0.1:8000/mcp"}}}`. Supported generator targets: `ClaudeCode`, `Cursor`, `VSCode`, `Gemini`, `Codex`, `All`. Launch the agent from the project root. — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- Transport: "HTTP and Server-Sent Events only"; "The `stdio` and WebSocket transports are not supported." Tool Search mode (default on) exposes only three meta-tools: `list_toolsets`, `describe_toolset`, `call_tool`. — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- Documented capabilities: spawning actors, lighting, material instances, inspecting Slate widgets, running automation tests; named toolsets SceneTools, ActorTools, MaterialInstanceTools, ObjectTools, GASToolsets (UAttributeSetToolset, experimental/disabled by default). The doc does not mention Blueprint-specific tools. — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- Custom tools: Python (`unreal.ToolsetDefinition` subclass with `@unreal.uclass()`, `@toolset_registry.tool_call` + `@staticmethod`, Google-style docstrings, under a plugin's `Content/Python/`) or C++ (`UToolsetDefinition`, `UFUNCTION(meta=(AICallable))`). After authoring run `ModelContextProtocol.RefreshTools`; "Live Coding does not propagate new UFUNCTION declarations, so adding a tool requires an editor restart." — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- Limits/security: loopback only, "No authentication layer", "not safe to expose beyond the local machine"; tool calls run serially on the game thread (no overlapping calls); MCP Resources/Prompts not advertised; telemetry on by default (`ModelContextProtocol.EnableAnalytics`); debug with `Log LogModelContextProtocol Verbose` and `npx @modelcontextprotocol/inspector` (Streamable HTTP). Doc does not explicitly list supported platforms; terminal setup shows both `cmd.exe` and bash/zsh variants. — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- Epic-published Claude Code plugin "Unreal Engine skills for Claude Code" ("Made by Epic Games", 871 installs at fetch time, no date shown): connects to the Unreal MCP ToolsetRegistry ("hundreds of tools across 30+ toolsets"), SessionStart hook that detects Unreal projects and injects UE conventions (UObject, Slate, UHT), safety rules (save before/after bulk changes, run serially to avoid game-thread deadlocks, wait for compilation). Listed capabilities include spawning actors, editing Blueprints, authoring materials, UMG widgets, Sequencer, Niagara, Control Rig, GAS, automation tests. Setup: enable ModelContextProtocol + AllToolsets, run `ModelContextProtocol.StartServer`. — [claude.com plugin page](https://claude.com/plugins/unreal-engine-skills-for-claude-code)
- Third-party walkthrough confirms default endpoint/port and that Codex approval mode "does not reliably classify inner operations behind `call_tool`"; Codex default tool timeout 60 s (article sets 120). — [DEV Community: Using Unreal MCP in UE 5.8 from Codex](https://dev.to/gamedevtoollab/using-unreal-mcp-in-ue-58-from-codex-setup-toolsets-and-safe-editor-automation-4pon)

**MegaJam's official stance on tooling**
- Jam page: AI is not mandatory ("Do I have to use AI?" — "No."); "Use any AI tools you like, and connect your agents to the editor with Unreal MCP"; teams of up to 5 humans "and as many AI agents as you want"; pre-jam setup allowed but pre-made prompts/scripts/assets must be declared; building starts Nov 12. — [Epic forum announcement](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)
- Epic's prep resources: "Unreal Engine MCP setup video, documentation, and livestream" and "UEFN MCP documentation and livestream"; kickoff livestream Nov 11 (20:00 CET per Spanish page; forum page says 7:00 PM, timezone context unclear); daily livestreams; in-person at Digital Jungle, San Francisco Nov 14-15 (registration opens Nov 1). — [Epic MegaJam news page (es-ES)](https://www.unrealengine.com/news/2026-epic-ai-megajam?lang=es-ES); [Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)
- Partners: Anthropic, Google, Meshy, OpenAI, SpaceXSI "and many more"; "some AI partners will offer credits so participants can use their tools during the jam" (which partners/how much not yet stated). — [Epic MegaJam page (es-ES)](https://www.unrealengine.com/news/2026-epic-ai-megajam?lang=es-ES)
- Prizes relevant to this entrant: Best Overall UE $7,500/$5,000/$2,500; modifier prizes Solo Development $2,500, Rendering Mastery $2,500, Pocket Power (mobile, UE) $2,500, Creative Transparency (documenting process) $2,500; Walkitalki ($2,500) is UEFN-only (LLM NPC narrative); one main + one modifier per project; up to $50k continuation grants. — [Epic MegaJam page (es-ES)](https://www.unrealengine.com/news/2026-epic-ai-megajam?lang=es-ES)
- Submission platforms: jam page says "Package your game for Windows, macOS, Android, or iOS" and mentions "(development build)"; a forum user quotes Official Rules §1(b): "must be packaged for Windows and playable on Windows 10 or 11, macOS, Android, or iOS" (unclarified by staff). — [Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)
- Jam page does not specify an engine version. — [Epic MegaJam page (es-ES)](https://www.unrealengine.com/news/2026-epic-ai-megajam?lang=es-ES)

**UEFN AI (context only — entrant chose regular UE)**
- Unreal MCP came to UEFN Aug 20, 2026 ("connect agentic coding tools like Claude Code, Codex, or Cursor directly to UEFN" — writing Verse, configuring devices, Scene Graph); "Not every toolset from UE 5.8 is compatible with UEFN just yet." — [Epic forum: Unreal MCP is now available in UEFN](https://forums.unrealengine.com/t/unreal-mcp-is-now-available-in-uefn/2745278)
- UEFN "Conversations" (formerly Persona device), Experimental as of Apr 16, 2026: Gemini 3.1 Flash-Lite (audio in, text out) + ElevenLabs voice; prompt-defined NPCs; Verse can adjust prompts at runtime and consume structured outputs; publishing not available until Beta; Fortnite rule 1.22 restrictions (no medical/mental-health personas, no romantic-partner personas). — [Fortnite news, Apr 16 2026](https://www.fortnite.com/news/bring-npcs-to-life-with-ai-powered-conversations)
- A Spanish news headline says Conversations leaves experimental on July 30 (not verified; Epic page gives no GA date). — [wwwhatsnew, Jul 17 2026](https://wwwhatsnew.com/2026/07/17/fortnite-conversations-npcs-ia-voz-tiempo-real-30-julio-2026/) (search result only, not opened)

### Inferences
- For regular UE, the lowest-risk "official" path is UE 5.8.1 + Unreal MCP plugin + `GenerateClientConfig ClaudeCode` + Epic's Claude Code plugin. It is Experimental, single-threaded on the game thread, and its Blueprint graph coverage is documented inconsistently (Epic doc lists no Blueprint toolset; Epic's Claude plugin page and Edge recap claim Blueprint editing) — verify by calling `list_toolsets` before the jam.
- Because Unreal MCP is HTTP-only, Claude Code connects with `"type":"http"`; no stdio bridge needed.
- Pre-jam: build and test the toolchain, CLAUDE.md, custom Python toolsets, and packaging pipeline now, and declare them in the submission (rules require declaring pre-made prompts/scripts).
- Walkitalki prize is UEFN-only, so in-game LLM NPCs in regular UE do not target a dedicated prize.

### Gaps
- Exact UE 5.8 GA date (State of Unreal recap dated June 17, 2026 says "now available"; no exact day verified). Latest 5.8.x hotfix as of Oct 27, 2026 not verified.
- No Epic statement verified on whether Unreal MCP is supported on Linux editor builds.
- "Epic Developer Assistant" as a named product: no source found/verified in this session.
- itch.io jam page and full Official Rules could not be fetched (client error); English unrealengine.com MegaJam page and TweakTown article also failed to load.
- Which partners give credits (Meshy/Anthropic/OpenAI/Google) and amounts: announced as "more info later."

---

## Q2. Community Unreal MCP servers: capabilities, maturity, stars, last update, UE support

### Takeaway
The early-2025 "famous" repos (chongdashu, kvick-games, runreal) are effectively stale (last commits Apr-Jun 2025, UE 5.4/5.5 era). The actively maintained community options as of Oct 27, 2026 are **ChiR24/Unreal_mcp ("EngineWire", UE 5.0-5.8, committed today)**, **IvanMurzak/Unreal-MCP (UE 5.5+, CI on 5.7/5.8, committed today, explicit Linux notes)**, and **GenOrca/unreal-mcp (UE 5.6+, last commit Jul 2026)**; flopperam's local server is "basic" with its advanced server now a hosted paid-style service owned by Aura.

### Cited Findings

| Repo | Stars (page) | Last commit (git, verified 2026-10-27) | UE support | Key capabilities | Transport | License |
|---|---|---|---|---|---|---|
| chongdashu/unreal-mcp | 2.1k, 345 forks | 2025-04-22 | UE 5.5+ | Actors, Blueprint classes/components, BP graph nodes (events, function calls, connect, variables), input mappings; no materials | Python FastMCP server <-> TCP port 55557 C++ plugin | MIT |
| flopperam/unreal-engine-mcp | 1.1k, 200 forks | 2026-06-26 (README banner merge) | Local: 5.5+; hosted: 5.5-5.7 | Local: actors, 23+ BP node types, BP analysis, materials/colors, procedural world building; Hosted "Flop MCP": 50+ tools, ~40 BP node types, `python_execution`, PIE testing | Local: stdio -> TCP plugin; Hosted: Streamable HTTP `agent.flopperam.com/mcp` + API key | MIT |
| runreal/unreal-mcp | 115, 28 forks | 2025-06-06 | UE 5.4+ "verified" | 20 tools incl. `editor_run_python` (full UE Python API), assets, console, outliner, screenshots; no plugin install (uses built-in Python remote execution) | `npx -y @runreal/unreal-mcp` (Node) | MIT |
| kvick-games/UnrealMCP | 609, 82 forks | 2025-06-21 | Tested UE 5.5 only | Object create/transform, scene info, Python exec; BP/Niagara/PCG etc. still on roadmap | TCP JSON, port 13377 | MIT |
| ChiR24/Unreal_mcp ("EngineWire") | not captured | 2026-10-27 | UE 5.0-5.8 | "over 400 capabilities" behind one `unreal` tool (0.6 beta line; 0.5.30 stable exposes 23 tools): levels/actors, Blueprints + whole event graphs in one batch, UMG, material graphs, landscapes, Niagara, PCG, GAS, BT/StateTree, Sequencer, MetaSounds, PIE with synthetic input, screenshots, logs, Python, packaging | HTTP or stdio; local + token-protected by default; native C++ plugin | MIT |
| IvanMurzak/Unreal-MCP ("AI Game Developer") | not captured | 2026-10-27 | UE 5.5+, CI-tested 5.7, verified 5.8 | 26 core tools: RQL query/mutate, 11 Blueprint tools (create/edit/compile with structured errors), C++ edit + compile (Live Coding or UBT), Python, screenshots; status "beta" | C++ plugin + .NET sidecar + GameDev-MCP-Server (cloud ai-game.dev or self-hosted) | (badge; not captured) |
| GenOrca/unreal-mcp | not captured | 2026-07-07 | UE 5.6+ | "253 actions across 21 domains" + `execute_python`; BP graph build/connect/compile/auto-layout (19), UMG (15), GAS (11), AnimBP (4), LiveCoding compile | Python plugin (UnrealMCPython) | Apache-2.0 |

Sources for table: [chongdashu GitHub](https://github.com/chongdashu/unreal-mcp); [flopperam GitHub](https://github.com/flopperam/unreal-engine-mcp); [runreal GitHub](https://github.com/runreal/unreal-mcp); [kvick-games GitHub](https://github.com/kvick-games/UnrealMCP); ChiR24/IvanMurzak/GenOrca READMEs read from shallow clones of [ChiR24/Unreal_mcp](https://github.com/ChiR24/Unreal_mcp), [IvanMurzak/Unreal-MCP](https://github.com/IvanMurzak/Unreal-MCP), [GenOrca/unreal-mcp](https://github.com/GenOrca/unreal-mcp); last-commit dates from `git log -1` on those clones.

Additional details:
- chongdashu: "This project is currently in an EXPERIMENTAL state... Production use is not recommended"; README references Windows/Visual Studio `.sln` only. — [GitHub](https://github.com/chongdashu/unreal-mcp)
- flopperam: repo says it "is now owned by Aura"; hosted server "shares no code with the local Python/ server" and needs one URL + API key. — [GitHub](https://github.com/flopperam/unreal-engine-mcp)
- runreal: requires enabling Python Editor Script Plugin + "Enable Remote Execution"; "Your AI agents or tools will have full access to your Editor." — [GitHub](https://github.com/runreal/unreal-mcp)
- kvick: "I only use windows, so I don't know how this would be setup for mac/unix"; server "accepts connections from any client by default." — [GitHub](https://github.com/kvick-games/UnrealMCP)
- ChiR24: needs a C++ project (or prebuilt binaries for BP-only projects); "Binaries only work with the engine minor and platform they were built for." README screenshot shows a platformer level built in UE 5.8 on port 3000. — [ChiR24/Unreal_mcp README](https://github.com/ChiR24/Unreal_mcp)
- IvanMurzak: CLI `unreal-mcp-cli` on npm installs plugin; on desktop platforms (`Win64` / `Mac` / `Linux`) runs a pre-launch build; "Linux dialog automation is X11-only; Wayland is detected and warned as unsupported"; screenshot tools need a GPU-backed editor, "everything else runs headless." — [IvanMurzak/Unreal-MCP README](https://github.com/IvanMurzak/Unreal-MCP)
- Other paid/commercial servers named in a May 2026 article: StraySpark (207+ tools, JSON-RPC over HTTP, tool presets) and UnrealCodex (20+ tools, HTTP port 3000, UE 5.7 API context). — [Daniel Vaughan: Codex CLI for UE 5.7](https://codex.danielvaughan.com/2026/05/28/codex-cli-unreal-engine-5-7-game-development-mcp-servers-blueprint-agent-workflows/)

### Inferences
- For a UE 5.8 jam, primary = Epic Unreal MCP (official, but Blueprint graph coverage unclear); fallback/complement for Blueprint graph authoring = ChiR24 EngineWire or GenOrca (both state BP graph build + compile). Running two MCP servers concurrently against one editor risks game-thread contention; test before the jam.
- Only IvanMurzak's README explicitly mentions Linux; none of the others document Linux. Native C++ plugins should compile on Linux if built from source with Epic's clang toolchain, but this is unverified per repo.
- Avoid chongdashu/kvick/runreal as primary tools for UE 5.8 (stale since mid-2025), though runreal's "no plugin, Python remote execution" approach is a useful minimal fallback.

### Gaps
- Star counts for ChiR24, IvanMurzak, GenOrca not captured (GitHub API blocked; pages not fetched).
- No repo explicitly tested on Linux + RDNA4 was found.
- ziggymar/unreal-mcp (listed on mcpservers.org) could not be cloned (auth prompt) — may be private/renamed; not verified. "ue5-mcp" variants and BestDev/unreal_bp_mcp seen only in search listings, not opened.

---

## Q3. Agent workflows that work: C++-first vs Blueprint-first, text interfaces, compile loops, Angelscript

### Takeaway
Agents are reliable writing C++ text and driving the editor through Python/MCP; Blueprints are binary `.uasset` and must be edited via MCP tools (Epic Unreal MCP, EngineWire, GenOrca, IvanMurzak) or Python editor scripting. Recommended pattern: core logic in C++ (`UFUNCTION(BlueprintCallable)`), thin Blueprints/data assets authored via MCP, headless automation tests from the CLI for verification.

### Cited Findings
- "Never modify .uasset files directly — they are binary"; put core logic in C++ exposed via `UFUNCTION(BlueprintCallable)`; wire graphs through MCP tools or editor UI. — [Daniel Vaughan, May 2026](https://codex.danielvaughan.com/2026/05/28/codex-cli-unreal-engine-5-7-game-development-mcp-servers-blueprint-agent-workflows/)
- AGENTS.md pattern: state engine version + target platforms; conventions (`#pragma once`, F/U/A/E prefixes); "Test with Unreal Automation Framework, not GoogleTest"; build with UnrealBuildTool not raw CMake; list MCP tools available. — [Daniel Vaughan](https://codex.danielvaughan.com/2026/05/28/codex-cli-unreal-engine-5-7-game-development-mcp-servers-blueprint-agent-workflows/)
- Headless test command: `UnrealEditor-Cmd MyProject.uproject -ExecCmds='Automation RunTests Projectile' -NullRHI -NoSound -Unattended`; tests via `IMPLEMENT_SIMPLE_AUTOMATION_TEST` with `TestEqual`/`TestTrue`. — [Daniel Vaughan](https://codex.danielvaughan.com/2026/05/28/codex-cli-unreal-engine-5-7-game-development-mcp-servers-blueprint-agent-workflows/)
- Live Coding (Ctrl+Alt+F11) for C++ hot reload during PIE. — [Daniel Vaughan](https://codex.danielvaughan.com/2026/05/28/codex-cli-unreal-engine-5-7-game-development-mcp-servers-blueprint-agent-workflows/)
- Epic doc: Live Coding updates existing function bodies but "new UFUNCTION declarations require a full editor restart" (stated for MCP tools; same reflection limitation applies). — [Epic docs: Unreal MCP](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- Hallucination/version-drift mitigation: tools that inject current class references/signatures instead of "relying on stale training data" (UnrealCodex); Epic's Claude Code plugin injects UE conventions via a SessionStart hook; Flop hosted MCP offers "15,000+ API lookups". — [Daniel Vaughan](https://codex.danielvaughan.com/2026/05/28/codex-cli-unreal-engine-5-7-game-development-mcp-servers-blueprint-agent-workflows/); [claude.com Epic plugin](https://claude.com/plugins/unreal-engine-skills-for-claude-code); [flopperam GitHub](https://github.com/flopperam/unreal-engine-mcp)
- Safety: gate destructive ops (e.g. `delete_all_actors|execute_console_command|save_all`) with approval hooks; restrict toolsets. — [Daniel Vaughan](https://codex.danielvaughan.com/2026/05/28/codex-cli-unreal-engine-5-7-game-development-mcp-servers-blueprint-agent-workflows/)
- Epic's Claude plugin safety rules: save before/after bulk changes; serial commands to avoid game-thread deadlocks; wait for compilation. — [claude.com](https://claude.com/plugins/unreal-engine-skills-for-claude-code)
- Python as the universal escape hatch: runreal's `editor_run_python` "can support the full Unreal Engine Python API" via built-in Python remote execution (enable Python Editor Script Plugin + Enable Remote Execution); GenOrca `execute_python` runs "any BlueprintCallable function or editor subsystem the engine exposes to Python"; new GenOrca actions are Python functions with no C++ rebuild. — [runreal](https://github.com/runreal/unreal-mcp); [GenOrca README](https://github.com/GenOrca/unreal-mcp)
- Structured compile feedback: IvanMurzak exposes Blueprint compile with "structured error/warning feedback loop" and C++ compile via Live Coding or UBT with structured error report. — [IvanMurzak README](https://github.com/IvanMurzak/Unreal-MCP)
- Angelscript (Hazelight): "a set of engine modifications and a plugin for UE5"; script edits hot-reload on save, non-structural changes reload even during PIE; VS Code LSP extension (autocomplete, diagnostics); can subclass/override BlueprintImplementableEvents and serve as base for child Blueprints; transpiled to near-native in shipping. — [angelscript.hazelight.se](https://angelscript.hazelight.se/)
- The Hazelight UnrealEngine-Angelscript GitHub repo could not be cloned anonymously (auth prompt), consistent with it being an Epic-licensee-gated engine fork (requires linked Epic GitHub org access). — observed via `git clone` on 2026-10-27 (no URL content retrievable)

### Inferences
- C++-first is the most agent-friendly for logic (text, diffable, compiler gives ground truth). But each C++ header/reflection change needs a UBT build + editor restart, which costs minutes; on Linux the editor build of a C++ project uses Epic's clang v26 toolchain (see Q5).
- A practical loop for Claude Code: (1) edit C++ -> (2) build with `Engine/Build/BatchFiles/Linux/Build.sh <Project>Editor Linux Development <path>.uproject` (standard UBT entry point; exact command not verified in a fetched source this session) -> (3) restart editor with `-ModelContextProtocolStartServer` -> (4) MCP tools for level/BP/material wiring -> (5) headless `UnrealEditor-Cmd ... -ExecCmds="Automation RunTests ..." -NullRHI -Unattended` and grep `Saved/Logs/*.log` for `Error:` lines.
- Angelscript requires switching to a source-built engine fork — high risk for a 4-day jam and unclear UE 5.8 parity; not recommended.
- Verse in regular UE is not available for gameplay until UE6 (Epic says UE6 moves gameplay programming to Verse), so Verse is UEFN-only for this jam.

### Gaps
- No primary Epic doc fetched for: UBT Linux command-line syntax, `-run=pythonscript` / `-ExecutePythonScript` commandlet usage, Remote Control API, BlueprintAssist, Blueprint-to-text export. These are long-standing UE features but were not verified this session.
- Angelscript's currently supported UE version (5.6/5.7/5.8?) not verified.
- No Reddit r/unrealengine or r/ClaudeAI threads opened; community pitfall anecdotes not collected.
- No CLAUDE.md example specific to Unreal from Anthropic/Epic found (Epic's Claude plugin uses a SessionStart hook instead).

---

## Q4. AI content-generation pipelines into Unreal (3D, rigging, textures, audio, animation, LLM NPCs) and sponsors/licensing

### Takeaway
Meshy is the only asset-gen vendor confirmed as a MegaJam partner (alongside Anthropic, Google, OpenAI, SpaceXSI); it has an official Unreal plugin with a "Bridge" (Pro plan+). Open/local alternatives that fit an RX 9070 XT box exist (TRELLIS.2 MIT, Hunyuan3D 2.1 open but region-restricted license, ACE-Step 1.5 MIT music, Stable Audio 3.0 SFX), but licensing must be checked; in-game LLM NPCs in standalone UE are possible via Convai (plugin tracks UE 5.8.x with lag) or direct API calls, with latency as the main risk.

### Cited Findings

**Sponsors**
- Partners at the in-person jam: Anthropic, Google, Meshy, OpenAI, SpaceXSI "and many more"; some partners will provide credits (details TBA). — [Epic MegaJam page (es-ES)](https://www.unrealengine.com/news/2026-epic-ai-megajam?lang=es-ES)

**3D generation**
- Meshy: text/image -> textured, rig-ready PBR mesh (Meshy 6/7 generations); Free plan 100 credits/month with outputs under CC BY 4.0 (attribution required); Pro ($20/mo)+ grants full ownership (per guide citing Meshy pricing). — [Cinevva guide, updated Sep 6 2026](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games) (vendor guide; verify on [Meshy pricing](https://docs.meshy.ai/pricing), not opened)
- Meshy Bridge to Unreal: sends model from Meshy web app straight into open level as FBX into `Content/MeshyImports`; requires Pro plan or higher; open via Window > Meshy Bridge each session; uses port 5327; rigged/animated models covered on a separate page. Doc does not state UE versions or OS support. — [Meshy docs: Bridge to Unreal](https://docs.meshy.ai/en/webapp/plugins/unreal/bridge-to-unreal)
- Tripo: text/image -> 3D with 4K PBR + auto-rigging; since Feb 2026 rigs non-humanoids; free plan non-commercial, paid includes commercial rights. — [Cinevva](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games)
- Rodin/Hyper3D: clean quad topology; generation free, downloads paid. — [Cinevva](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games)
- Hunyuan3D 2.1: open weights + PBR texturing; license reportedly excludes EU, UK, South Korea. Hunyuan 3D 3.0: hosted only (released globally Nov 2025), 20 free generations/day, not open weights. — [Cinevva](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games)
- TRELLIS.2 (Microsoft): 4B image-to-3D, MIT license, Dec 2025, native PBR (base color, roughness, metallic, opacity). — [Cinevva](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games)
- State of Unreal 2026: Epic showed diffusion tools (depth/normal/camera conditioning; styled frames, object extraction to 3D, video) planned for release "early next year" (i.e., 2027 — not available for the jam). — [Epic State of Unreal 2026](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show)

**Rigging / animation**
- UniRig (open, MIT; SIGGRAPH 2025) predicts skeletons + skin weights for bipeds/quadrupeds/birds/insects; NVIDIA SOMA-X (Apache 2.0) for retargeting; the guide calls Mixamo "become unreliable" (no details); Tripo and Meshy auto-rig in hosted workflow. — [Cinevva](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games)

**2D / textures**
- FLUX.2 klein 4B: Apache 2.0, ~13 GB VRAM (9B variant non-commercial); Qwen-Image Apache 2.0 (good text rendering); SD 3.5 Community License free under $1M revenue; Scenario commercial from $15/mo; Layer commercial on all plans. — [Cinevva](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games)

**Audio**
- Stable Audio 3.0 (May 20, 2026): Small-SFX, Small-Music, Medium open weights under Stability Community License; Large API-only; "trained on licensed data." ACE-Step 1.5 (Feb 2026, MIT) music, <4 GB VRAM. ElevenLabs SFX/music: commercial rights on paid plans. — [Cinevva](https://app.cinevva.com/pt-BR/guides/ai-asset-generators-games)

**In-game LLM NPCs in standalone UE**
- Convai UE plugin: did not initially support 5.8.1 (staff Jul 30, 2026: "Support for this version will be added in a future update"); update released Aug 3, 2026; staff recommend GitHub Releases over Fab because Fab review delays updates. — [Convai forum](https://forum.convai.com/t/convai-fails-to-load-when-updating-from-ue-5-8-to-5-8-1/6436)
- Convai pricing (as cited by guide): free dev tier with daily quota; Indie $29/mo ($19 annual) for 3,000 interactions. Inworld has largely moved away from out-of-the-box NPC studio toward B2B AI infrastructure; SDKs still exist but B2B-oriented. NVIDIA ACE = microservices (Audio2Face, Riva). Latency: ~800 ms feels natural; typical cloud API call adds 1-2 s. — [Cinevva AI NPC guide, Jul 2026](https://app.cinevva.com/de/guides/ai-npcs-dialogue)
- Epic's Unreal MCP can run in cooked/shipping builds via `IModelContextProtocolModule::StartServer()` with tools registered via `AddTool()` (i.e., a game can host an MCP server at runtime). — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)

### Inferences
- Fastest jam pipeline on this hardware: Meshy (sponsor, likely credits; Bridge needs Pro) or Tripo for hero props/characters with auto-rig -> FBX import (or MCP-driven Python import) ; TRELLIS.2 locally as a no-cost MIT fallback; ACE-Step 1.5 locally for music; Stable Audio Small-SFX or ElevenLabs for SFX/voice. Check Hunyuan3D license region (US-based user is outside the excluded territories, but confirm terms).
- Free-tier Meshy CC BY 4.0 requires attribution in credits; record all generated asset sources for the "Creative Transparency" modifier prize and the jam's pre-made asset declaration.
- Live LLM NPC dialogue in a packaged UE build adds API-key handling, latency, and third-party plugin version risk (Convai lagged 5.8.1 by ~4 days); a pre-generated dialogue approach is lower-risk for a 4-day jam.

### Gaps
- Not opened/verified: Meshy pricing & commercial-use page (intercom page failed), Meshy animated-model import page, Tripo/Rodin/ElevenLabs official terms, Suno/Udio status, AccuRIG, Move.ai, Rokoko Vision, Cascadeur, Mixamo current status (only a vendor guide's one-line claim), Inworld official Unreal SDK status, local llama.cpp UE plugins, Anthropic/OpenAI API call patterns from UE (HTTP module).
- Cinevva guides are vendor-authored; pricing/licensing claims should be confirmed on each vendor's site.

---

## Q5. Linux specifics: UE editor on CachyOS + RX 9070 XT, Windows packaging from Linux, Android from Linux, MCP on Linux

### Takeaway
Packaging a Windows build from a Linux host is not supported by Epic (Epic's own Linux requirements page says cross-compiling is "only supported for Windows" hosts targeting Linux); since the jam requires Windows (or macOS/Android/iOS), the entrant needs a Windows machine/VM/cloud box or an Android build. UE 5.8.0 had reproducible Vulkan `VK_ERROR_DEVICE_LOST` freezes on RDNA2/RDNA4 with RADV; reports say 5.8.1 seems to fix it, with async-compute cvars as a workaround.

### Cited Findings

**Editor on Linux + AMD RDNA4**
- Epic Linux requirements (UE 5.8): recommended Ubuntu 22.04 (Rocky 8 also); Vulkan RHI needs AMD RADV >= 24.2.8, 25.0.0+ recommended; Lumen/MegaLights need SM6 + AMD RX 6000+; Nanite/VSM need `VK_KHR_shader_atomic_int64`; compiler clang 20.1.8, toolchain v26 for 5.7-5.8; recommended IDEs VS Code or Rider. — [Epic: Linux development requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine)
- Bug thread (Jun 23, 2026): UE 5.8 source build on Fedora 44, RX 9070 XT (GFX1201), Mesa 26.0.8 RADV -> `VK_ERROR_DEVICE_LOST` from `vkQueueSubmit`, GPUVM read faults, ring resets; breadcrumbs in Lumen/Nanite/VSM/GDF paths; disabling individual systems only "moved the crash"; RADV issue gitlab.freedesktop.org work item 15708. — [Epic forum thread](https://forums.unrealengine.com/t/ue-5-8-vulkan-on-linux-triggers-vk-error-device-lost-gpuvm-read-fault-on-amd-rx-9070-xt-with-radv/2730749)
- Replies: same on RX 6800 XT (last flawless version 5.5.4; disabling SM6 helped partially); Linux Mint user says 5.7.4 works while 5.8.0 freezes; RX 9060 XT (RDNA4) user stabilized with `r.Vulkan.AllowAsyncCompute=0` and `r.RDG.AsyncCompute=0`; `-NoRaytracing` suggested (no result); Jul 31, 2026: "Seems to be fixed with the new 5.8.1 patch" (needs more testing); Epic issue UE-386320 closed as duplicate of a known issue (linkage to this thread inferred). — [Epic forum thread](https://forums.unrealengine.com/t/ue-5-8-vulkan-on-linux-triggers-vk-error-device-lost-gpuvm-read-fault-on-amd-rx-9070-xt-with-radv/2730749)
- A separate thread reports UE 5.8 instant Vulkan crash on Linux with RTX 3090 Ti (not opened), and a "Crash when opening or packaging a project on 5.8.1 Linux (RHEL8)" thread exists (not opened). — [Epic forum (3090 Ti)](https://forums.unrealengine.com/t/ue-5-8-release-instant-vulkan-crash-vk-error-device-lost-on-linux-with-rtx-3090-ti-nvidia-driver/2729632/9); [Epic forum (5.8.1 RHEL8)](https://forums.unrealengine.com/t/crash-when-opening-or-packaging-a-project-on-5-8-1-linux-rhel8/2746210)

**Windows packaging from Linux**
- Epic Linux requirements page: "cross-compiling is only supported for Windows" (i.e., Windows host -> Linux target); no Linux -> Windows path described. — [Epic: Linux development requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine)
- Forum thread (2016-2025): "it is possible to only build for Linux when working on Linux"; advice to copy project to a Windows machine; user workarounds: running the Windows engine under Bottles/Proton and building from Jenkins on Linux (Sep 2024, one user's report), Windows containers (no GPU toolkit), GPU passthrough VM (asked, unanswered). — [Epic forum: Building for Windows on Linux](https://forums.unrealengine.com/t/building-for-windows-on-linux/358294)
- Jam accepts Windows, macOS, Android, iOS (development build mentioned); not Linux. — [Epic forum announcement](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973)

**Android from Linux**
- Epic's Android SDK setup doc includes Linux steps: reset env vars in `~/.bashrc`, run `Engine/Extras/Android/SetupAndroid.sh` ("SetupAndroid.sh – Linux"); doc does not explicitly state which hosts can package Android. — [Epic: Manual Android SDK setup](https://dev.epicgames.com/documentation/unreal-engine/manual-android-sdk-setup-with-android-studio-for-unreal-engine)
- UE 5.8 Android requirements: Android Studio Koala 2024.1.2 Patch 1, target SDK 35 (min compile 34, min install 26), NDK r27c, build-tools 35.0.1, OpenJDK 21.0.3. — [Epic: Android development requirements](https://dev.epicgames.com/documentation/en-us/unreal-engine/android-development-requirements-for-unreal-engine)
- "Pocket Power" (mobile) modifier prize: $2,500 for a UE winner. — [Epic MegaJam page (es-ES)](https://www.unrealengine.com/news/2026-epic-ai-megajam?lang=es-ES)

**MCP plugins on Linux**
- Epic Unreal MCP doc does not list platforms; shows Unix shell terminal setup. — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)
- IvanMurzak/Unreal-MCP explicitly supports Linux desktop builds; dialog automation X11-only (Wayland warned). — [IvanMurzak README](https://github.com/IvanMurzak/Unreal-MCP)
- kvick-games: Windows-only author; chongdashu: Windows/VS-oriented docs. — [kvick](https://github.com/kvick-games/UnrealMCP); [chongdashu](https://github.com/chongdashu/unreal-mcp)
- Meshy Bridge doc does not state OS support. — [Meshy docs](https://docs.meshy.ai/en/webapp/plugins/unreal/bridge-to-unreal)

### Inferences
- Use UE 5.8.1 (or the latest 5.8.x), not 5.8.0, on CachyOS/RDNA4; keep `r.Vulkan.AllowAsyncCompute=0` / `r.RDG.AsyncCompute=0` in `DefaultEngine.ini` or ConsoleVariables as a ready fallback; keep UE 5.7.4 as a known-working fallback (note: Epic Unreal MCP is 5.8-only; community MCPs like EngineWire/GenOrca support 5.6/5.7).
- CachyOS is not an Epic-listed distro (Ubuntu 22.04/Rocky 8 are); Arch-family rolling Mesa should satisfy the RADV >= 25.0 recommendation.
- Windows packaging options, in rough order of reliability: (a) a separate Windows PC or dual-boot running UE 5.8 + VS toolchain, packaging from the same git repo; (b) a cloud Windows VM with GPU (not researched here); (c) Windows engine under Wine/Proton (single anecdotal report; high risk); (d) Android APK packaged directly on Linux (supported setup scripts exist; also targets the Pocket Power prize). GitHub-hosted Windows runners were not verified as feasible (UE install size and cooking time are concerns; no source found).
- Do a full end-to-end "package + run on Windows" dry run before Nov 12.

### Gaps
- No Epic primary statement found explicitly saying "Windows targets cannot be built from Linux" in current 5.8 docs beyond the cross-compile wording; Epic staff never clarified in the forum thread.
- Not verified: whether Epic's Unreal MCP plugin binary ships in the Linux editor build; whether the Epic Games Launcher-equivalent binary UE 5.8 for Linux (download from unrealengine.com/linux) is current at 5.8.1+.
- GitHub Actions / cloud Windows runner feasibility for UE packaging: no relevant source found (searches returned unrelated results).
- iOS/macOS packaging requires a Mac (not researched).

---

## Sources added 2026-11-05 (itch "Get ready" links review)
Detail and verdicts: `_config/reference/research/get-ready-links-review-2026-11-05.md`.
- "A First Look at Unreal MCP in Unreal Engine 5.8", Unreal Engine channel, uploaded 2026-10-08 (setup video, Windows, Claude Code).
- "Getting Started with MCP in Unreal Engine 5.8 | Epic Games Education Webinar", uploaded 2026-09-07 (Editor Toolsets plugin, `describe_toolset` token sizes, prompt habits, `LogModelContextProtocol`).
- "MCP in UEFN | Creating in Fortnite", Fortnite Developers, uploaded 2026-08-22 (save-dialog stall, `print` feedback, plan-file pattern; UEFN only).
- UEFN MCP docs and its sub-pages on Python scripting and profiling (undated; UEFN only).

## Sources that could not be opened (for the report writer)
- https://itch.io/jam/2026-epic-ai-megajam (client error) — official rules/platform details unverified there.
- https://unrealengine.com/news/2026-epic-ai-megajam (English; client error) — used es-ES localized page instead.
- TweakTown MegaJam article (client error).
- Meshy commercial-use help article (intercom; client error).
- Hazelight/UnrealEngine-Angelscript GitHub (requires Epic-linked GitHub access).
- GitHub REST API (blocked in session) — star counts for ChiR24/IvanMurzak/GenOrca not captured.
- Not attempted due to budget: Reddit threads, ElevenLabs/Tripo/Rodin/Convai/Inworld official docs, Remote Control API docs, UBT/commandlet docs, Move.ai/Rokoko/Cascadeur, Suno/Udio.
