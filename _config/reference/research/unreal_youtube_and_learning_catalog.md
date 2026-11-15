# Unreal Engine YouTube and Epic Learning Catalog for the 2026 Epic AI MegaJam (solo dev, agent-heavy, regular UE)

Research date: 2026-10-27. Jam: Nov 12–15, 2026 (theme reveal Nov 11).

**How to read the entries.** Each entry gives: Title | channel | date | length (if known) | URL | 2–4 line actionable summary | engine version | verification tag. The tags are:
- **[V]**: I opened the YouTube watch page (or the Epic page that hosts it), and the title, channel and date are confirmed from that page.
- **[E]**: The URL and title come from an official Epic page (unrealengine.com learning roundup, blog or forum), but I did not open the video page.
- **[S]**: I saw only the title and URL in a search result. The content is **inferred from the title alone**, and the video page was not opened.

YouTube pages returned bot-protection stubs, so video **lengths were usually not recoverable**. Lengths appear only where the page or a secondary source exposed them. Summaries describe what the video description or Epic's write-up says. I did not watch the videos.

---

## Q1. Sampling method, what could not be opened, and current engine version

### Takeaway
The current engine is **UE 5.8**, released June 17, 2026 at State of Unreal / Unreal Fest Chicago 2026. Epic calls it the last planned major UE5 release (a 5.9 is "possible"), and UE6 Early Access is targeted for end of 2027. The catalog below was built from Epic's monthly learning roundups, Epic news and forum posts, the Unreal Fest Chicago 2026 playlist (via search), and direct YouTube watch-page fetches. YouTube channel, playlist and RSS listings could not be enumerated.

### Cited Findings
- UE 5.8 released June 17, 2026 during State of Unreal. Highlights: experimental Unreal MCP Server plugin; MegaLights production-ready; Lumen "Lite"/lightweight GI; experimental Mesh Terrain; Procedural Vegetation Editor; MetaHuman Crowd plugin; Single-camera / markerless MetaHuman Animator; Substrate NPR shading. — [GameFromScratch](https://gamefromscratch.com/unreal-engine-5-8-released/)
- Epic says 5.8 is "the last planned major UE5 release, though a 5.9 is possible if needed". UE6 is planned around Verse, open standards and "productivity features such as MCP integrations", with Early Access targeted for end of 2027. Production-ready in 5.8: MegaLights, Audio Insights, Dataflow for Chaos Cloth, Live Link Hub, Iris, Movie Render Graph. — [Epic: State of Unreal 2026 top news](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show)
- UE 5.7 (released ~Nov 12, 2025): PCG framework production-ready; Procedural Vegetation Editor and Nanite Foliage experimental; an **in-editor AI Assistant** (ask questions, get C++ snippets and step-by-step instructions inside the editor). — [Digital Production](https://digitalproduction.com/2025/11/12/unreal-engine-5-7-foliage-pcg-and-in-editor-ai/)
- Epic release notes are at `dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes` and the blog at `unrealengine.com/news/unreal-engine-5-8-is-now-available` (links taken from) — [GameFromScratch](https://gamefromscratch.com/unreal-engine-5-8-released/)
- **Sampling methods used:**
  1. Epic monthly "Epic learning content" roundups. April 2026 and August 2026 gave full URLs. March, June and July 2026 and December 2025 gave titles only, because the link URLs did not survive extraction. ([Apr 2026](https://www.unrealengine.com/learning/aprils-epic-learning-content-pcg-metahuman-mobile-development-and-more), [Aug 2026](https://www.unrealengine.com/learning/augusts-epic-learning-content-networked-physics-dynamic-audio-and-more), [Jul 2026](https://www.unrealengine.com/learning/julys-epic-learning-content-animation-mobile-game-development-and-more), [Jun 2026](https://www.unrealengine.com/learning/junes-epic-learning-content-metahumans-mesh-terrain-and-more), [Mar 2026](https://www.unrealengine.com/learning/marchs-epic-learning-content-substrate-metahuman-and-more), [Dec 2025](https://www.unrealengine.com/learning/decembers-epic-learning-content-animation-world-creation-and-more))
  2. Unreal Fest playlists: Chicago 2026 is `PLZlv_N0_O1gbqqvKFsEnkNhjP7iE9PL3N` ([playlist](https://www.youtube.com/playlist?list=PLZlv_N0_O1gbqqvKFsEnkNhjP7iE9PL3N)) and Orlando 2025 is `PLZlv_N0_O1gbSPueZMAf0gacwmuVBU3hO` (121 videos) ([playlist](https://www.youtube.com/playlist?list=PLZlv_N0_O1gbSPueZMAf0gacwmuVBU3hO)). WebFetch returned only the playlist name and count, not the items. Individual sessions were found via "extended" web search and then opened one by one.
  3. Epic news and forum posts for MegaJam, MCP and templates.
  4. Third-party video-note indexes (lilys.ai / readray.ai) to recover YouTube IDs, which were then verified on YouTube where possible.
  5. The developereducators.com "best Unreal videos" list (updated Oct 25, 2026) for non-official channels. — [developereducators](https://developereducators.com/best/unreal-engine/)
- **Could not open:**
  - The YouTube channel /videos page and its RSS feed: the RSS was robots-blocked and the page fetch returned no list.
  - Playlist item lists.
  - The itch.io 2026 and 2025 jam pages (client error).
  - The Unreal Fest Chicago agenda.
  - The toolfarm.com Chicago session archive (client error).
  - The forums' Inside Unreal tag listing (empty or robots-blocked).
  - The September 2026 learning roundup (client error).
  - Several watch pages: XlbWtoIk-Zc, b8DI-Neocz4, FLDXtAV7qsw, wPgd1J1Tf70.

### Inferences
- For the jam, plan on UE 5.8.x. The MCP plugin, the 5.8 GASP update, the MegaLights production status and the Lumen performance work all assume 5.8. Anything titled 5.4–5.7 still applies in principle, but UI and menus may differ.

### Gaps
- I did not verify the latest 5.8 hotfix number, or whether a 5.9 preview exists as of Oct 27, 2026.
- A forum user asked whether the UE6 mainline branch may be used for the jam. No answer was visible ([forum thread](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983)).

---

## Q2. Videos about the 2026 Epic AI MegaJam, its kickoff, and previous MegaJam showcases

### Takeaway
There is **no kickoff VOD yet**. The theme reveal streams **Nov 11, 2026** on Twitch and YouTube (/unrealengine), and Epic plans daily livestreams during the jam. The best prior-art videos are the official MegaJam winners streams. The 2025 winners stream (March 12, 2026) is the most recent. No judges' comments could be extracted from text sources.

### Cited Findings
- 2026 AI MegaJam facts:
  - Jam Nov 12–15, 2026, with kickoff and theme reveal Nov 11 at 7:00 PM (time zone not stated on the forum page).
  - Streams on twitch.tv/unrealengine and youtube.com/unrealengine.
  - In-person event at Digital Jungle, SF, Nov 14–15.
  - Up to 4 other humans plus unlimited AI agents; pick UE **or** UEFN.
  - "Connect agents to the editor with Unreal MCP".
  - Declare pre-made prompts, scripts and assets.
  - Don't start building until Nov 12, but tools, agents and MCP setup may be done earlier.
  - Source: [Epic forum announcement](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983)
- Epic walked back a mandatory-AI requirement ("Our FAQ originally said you had to use AI… That's our mistake"). Three categories pay $7,500 each, plus Development Continuation Grants of up to $50,000 per team. Epic will run **daily livestreams with progress updates** during the jam. — [PC Gamer, Oct 22, 2026](https://www.pcgamer.com/software/ai/epic-announces-game-jam-where-you-have-to-use-ai/)
- **Epic MegaJam 2025 Winners Announcement | Inside Unreal** | Unreal Engine | streamed Mar 12, 2026 | https://www.youtube.com/watch?v=SsR4mzX9-4o | Official reveal of the 2025 winners. Watch it for the scope, polish and presentation level that won the most recent MegaJam. The description lists no winners or criteria. **[V]** — [YouTube](https://www.youtube.com/watch?v=SsR4mzX9-4o)
- **Mega Stack 'O' Jam Winners Announcement** | https://www.youtube.com/watch?v=F-ZD5E_jM_0 | A companion jam announced alongside the 2025 MegaJam update. Content inferred from title only. **[S]** — [search result](https://www.youtube.com/watch?v=F-ZD5E_jM_0)
- Epic delayed 2025 judging because of a "truly remarkable number of creative entries" (forum post, Jan 5, 2026). — [Epic forum](https://forums.unrealengine.com/t/2025-epic-megajam-mega-stack-o-jam-update/2689696)
- The 2025 MegaJam ran 2025-10-16 to 2025-10-25 with 491 entries (itch search-result snippet; page not opened). Its theme was "Here We Go Again", with three classic past themes as alternatives. — [itch.io search snippet](https://itch.io/jam/2025-epic-megajam); [Unreal Source](https://unrealsource.com/d/the-2025-epic-megajam-theme-is-here-we-go-again/)
- The 2025 MegaJam theme was revealed during an Inside Unreal stream on Oct 16, 2025. The jam had 31 prize categories (9 primary). — [Epic news](https://www.unrealengine.com/news/epic-megajam-2025)
- **Epic MegaJam 2023 Winners Announcement | Inside Unreal** | Unreal Engine | streamed Nov 30, 2023 | https://www.youtube.com/watch?v=e8falymc1Nk | Hosts play the winners and discuss their favorite parts. Use it as a model for what Epic staff call out on stream. **[V]** — [YouTube](https://www.youtube.com/watch?v=e8falymc1Nk)
  - 2023 winners: Rolling Back (1st UE), Lamp Lighter (Army of One, the solo category), and others. — [Unreal Source](https://unrealsource.com/d/2023-epic-megajam-winners/)
- 2022 winners list. Modifier categories included "Army of One" (solo), "Make Us Go WOW! Stylized/Photoreal", "Audio Experience", "Procedural Magicians" and "Tiny But Mighty". No judge comments were on the page. — [Epic blog](https://www.unrealengine.com/blog/presenting-the-winners-of-the-2022-epic-megajam)
- "8 tips for surviving the Epic MegaJam" (Unreal Source):
  - Submission needs an itch project, a **30–60 s gameplay video**, and a list of pre-existing assets.
  - Package and test a build on day 1.
  - Use butler for itch uploads.
  - Ruthlessly cut scope and add audio/UI before secondary features.
  - "All art assets… must have a material other than DefaultMaterial".
  - The article links a Gorka Games packaging video guide.
  - Source: [Unreal Source](https://unrealsource.com/n/8-tips-for-surviving-the-epic-megajam/)

### Inferences
- Plan to watch the Nov 11 kickoff live, because the theme and any 2026 modifiers will only be in that stream.
- Past jams rewarded modifiers such as solo ("Army of One"), audio, stylized "WOW" visuals and procedural work. If 2026 has similar modifiers, they fit a solo AI-assisted entry. This is unconfirmed for 2026.
- The 30–60 s gameplay-video requirement (from 2023-era rules) makes Sequencer and Movie Render Graph skills worth having. Confirm against the 2026 rules.

### Gaps
- Official 2026 judging criteria were not found. The itch page and the rules on Box were not readable.
- I found no 2026 pre-jam prep stream VOD before Oct 27.
- I could not extract judge praise for 2024 or 2025 winners from text. That requires watching SsR4mzX9-4o.

---

## Q3. AI in Unreal: Unreal MCP, agentic coding, in-editor AI Assistant, Python, Unreal Fest AI talks

### Takeaway
The highest-value official material:
- the State of Unreal 2026 MCP segment (41:47)
- the Unreal Fest Chicago 2026 talk "From Words to Worlds: Integrating MCP into the Unreal Editor"
- Epic's Unreal MCP documentation page

The best quick setup video is Smart Poly's (non-official) 5.8 MCP + Claude Code quickstart. Epic also publishes an "Unreal Engine skills for Claude Code" plugin listed as made by Epic Games.

### Cited Findings
- **State of Unreal 2026 Official 4K Livestream | Unreal Fest Chicago** | Unreal Engine | Jun 17, 2026 | ≥2:06:36 (≈2:15:42 per a third-party list) | https://www.youtube.com/live/9ikOoOzAhPE | Chapters (jump to the starred ones):
  - 33:28 UE 5.8 (Simon Tourangeau)
  - 41:47 **Model Context Protocol (MCP) Server Support (Michael Lentine)** *
  - 51:10 Image/Video generation (coming soon)
  - 1:46:41 UE6
  - 1:55:48 Verse
  - Engine: 5.8. **[V]** — [YouTube](https://www.youtube.com/live/9ikOoOzAhPE)
  - A separate search result shows "State of Unreal 2026 Official 4K" at https://www.youtube.com/watch?v=xXGSvLH9zAs **[S]**. This may be a re-upload; it was not opened.
  - Edge reported that Epic demoed Claude Cowork running prompts inside an Unreal project during this segment. — [Edge](https://knowledge.edge-online.com/p/ai-goes-native-in-unreal-engine-the-five-main-takeaways-from-state-of-unreal-2026)
- **Unreal Engine 5.8 Is Now Available | State of Unreal | Unreal Fest Chicago 2026** | Unreal Engine | Jun 23, 2026 | 8:30 | https://www.youtube.com/watch?v=Aaf12f_LA_Y | An 8.5-minute keynote clip with the 5.8 feature overview. Use it as a fast catch-up. **[V]** — [YouTube](https://www.youtube.com/watch?v=Aaf12f_LA_Y)
- **From Words to Worlds: Integrating MCP into the Unreal Editor | Unreal Fest Chicago 2026** | Unreal Engine | Aug 3, 2026 | https://www.youtube.com/watch?v=lDf_y-YPELo | Covers which editor systems UE 5.8 MCP supports out of the box, how to connect any agentic LLM, how to extend it, and LLM + **PCG Primitives** experiments that build and iterate environments from natural-language prompts. Engine 5.8. **[V]** — [YouTube](https://www.youtube.com/watch?v=lDf_y-YPELo)
- **Using UE with Image and Video Generation (Coming Soon)** | https://www.youtube.com/watch?v=LGvsShWEH3k | Appears to be the State of Unreal segment clip on diffusion workflows conditioned on depth, normals and camera. Epic says release is planned for early next year, so it is **not usable for the Nov jam**. Content inferred from title and the Epic news post. **[S]** — [search result](https://www.youtube.com/watch?v=LGvsShWEH3k); [Epic news](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show)
- Epic doc, **Unreal MCP in Unreal Editor** (UE 5.8, Experimental):
  - Enable the "Unreal MCP" and "All Toolsets" plugins, then turn on Auto Start Server or run `ModelContextProtocol.StartServer`.
  - Run `ModelContextProtocol.GenerateClientConfig <Client|All>`, which writes `.mcp.json` to the project root.
  - Clients: Claude Code, Cursor, VS Code, Gemini, Codex, MCP Inspector.
  - Transport is HTTP/SSE only at `http://127.0.0.1:8000/mcp`, loopback only, with no auth.
  - Tool calls run **serially on the game thread**, so don't overlap calls.
  - New UFUNCTION tools need an editor restart.
  - Shipped Python toolsets include SceneTools, ActorTools, MaterialInstanceTools and ObjectTools. An experimental GASToolsets plugin also exists.
  - Source: [Epic docs](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor?lang=en-US)
- **Unreal Engine skills for Claude Code** plugin, listed as "Made by Epic Games":
  - "Hundreds of tools across 30+ toolsets" via ToolsetRegistry, including actors, blueprints, materials, UI widgets, Sequencer, Niagara, Control Rig, GAS and automation tests.
  - A SessionStart hook injects UE conventions.
  - Safety rules: save before and after bulk changes, run serially, wait for compilation.
  - Project-specific Agent Skills can override the defaults.
  - Source: [claude.com plugin page](https://claude.com/plugins/unreal-engine-skills-for-claude-code)
- **NEW Unreal Engine 5.8 MCP Tutorial (QuickStart Guide)** | Smart Poly (NON-OFFICIAL) | Jun 19, 2026 | 12:21 | https://www.youtube.com/watch?v=PqrKqhkj3gQ | Enables the plugins, installs Claude Code, and launches with `TERM=xterm-256color` from the project folder. This is the fastest zero-to-working MCP setup. **[V]** — [YouTube](https://www.youtube.com/watch?v=PqrKqhkj3gQ)
- **I Tested Claude Inside Unreal Engine 5.8...** | Smart Poly (NON-OFFICIAL) | Jun 20, 2026 | https://www.youtube.com/watch?v=OiFtnBj1P9o | Claude Code attempts five Blueprint problems via MCP, compared against hand-built versions. Useful for calibrating what to delegate. **[V]** — [YouTube](https://www.youtube.com/watch?v=OiFtnBj1P9o)
- **MCP in UEFN | Creating in Fortnite** | Fortnite Developers | streamed Aug 21, 2026 | https://youtube.com/live/OU5OT06YxtQ | Magnus Enebakk shows agents writing and compiling Verse, placing devices and running play sessions. **UEFN-only**, so it is lower priority for a regular-UE entry, but it shows the agent "build–compile–playtest" loop. **[V]** — [YouTube](https://youtube.com/live/OU5OT06YxtQ); also see the short announcement video https://www.youtube.com/watch?v=hZHjZVVjEsE **[V]** — [YouTube](https://www.youtube.com/watch?v=hZHjZVVjEsE)
- Puget Systems hands-on with UE 5.8 MCP + Claude:
  - **Worked:** a greybox hallway with rooms in about 5 minutes, and a light-trigger Blueprint.
  - **Failed:** switching to ground character controls broke input, and building PCG graphs from scratch failed (the model faked it with placed meshes).
  - **Cost:** responses often took 5–15 minutes, and token usage was heavy.
  - Conclusion: MCP works best for accelerating systems you already understand. It recommends Smart Poly's tutorial over Epic's thin docs.
  - Source: [Puget Systems, Jul 9, 2026](https://www.pugetsystems.com/blog/2026/07/09/unreal-engine-mcp-hands-on-testing-ai-inside-the-editor/)
- Epic EDC community tutorials (text):
  - "Build a Playable Unreal Engine 5 Level with AI (MCP + Claude Code)" (UE 5.8, Aug 30, 2026; Third Person template + Fab pack turned into a playable level). — [EDC](https://dev.epicgames.com/community/learning/tutorials/bnJ0/build-a-playable-unreal-engine-5-level-with-ai-mcp-claude-code)
  - "Using the UE5 MCP Server with Claude Code, Codex CLI, and Cursor". — [EDC](https://dev.epicgames.com/community/learning/tutorials/DEKE/using-the-unreal-engine-5-mcp-server-with-claude-code-codex-cli-and-cursor)
- **City Sample updated for UE 5.8** with two new PCG-built levels made with LLM assistance. It uses PCG graphs as baseline references for Unreal MCP and shows Claude working with PCG. Content: PCG Assembly data assets, shape-grammar buildings and roads, and the CitySamplePCG_demo plugin. — [Epic learning](https://www.unrealengine.com/learning/city-sample-gets-a-major-update-with-pcg-and-unreal-mcp-workflows)
- UE 5.7 in-editor AI Assistant:
  - Docked in-editor Q&A, C++ snippets, step-by-step help; not a replacement for docs. — [Digital Production](https://digitalproduction.com/2025/11/12/unreal-engine-5-7-foliage-pcg-and-in-editor-ai/)
  - A vendor blog (StraySpark sells an MCP product) claims the assistant cannot execute editor actions, supports BYO Claude/GPT keys, and has a paid tier. **These claims are unverified and come from a biased source.** — [StraySpark](https://www.strayspark.studio/blog/ue57-ai-assistant-vs-mcp-comparison)
- Python editor scripting: no 2025–26 official Python video was found. The Inside Unreal "Python in Unreal Engine" forum thread is older (ID 610567, date not opened). — [forum](https://forums.unrealengine.com/t/610567)
- Unreal MCP feedback thread (Aug 20, 2026). Epic says the UEFN version is beta with "rough edges", and the UE 5.8 and UEFN versions share the Toolset Registry. — [Epic forum](https://forums.unrealengine.com/t/unreal-mcp-feedback-thread/2743365)

### Inferences
- Use agents for greyboxing, actor placement, material instances, Blueprint wiring of simple triggers, batch asset operations and automation tests.
- Hand-own core player controls, Enhanced Input and PCG graph authoring, or start from templates and graphs the agent then modifies. Both Puget and the City Sample approach of "PCG graphs as baseline references" point this way.
- The serial game-thread constraint means one agent per editor instance. Parallel agents should work on code and files outside the editor, or on separate editor instances or projects.

### Gaps
- I found no official Epic step-by-step MCP video tutorial on the Unreal Engine channel. The 41:47 keynote segment and the Fest talk are the official video sources.
- I found no official UE 5.7 AI Assistant demo video and no official doc page for it.
- I found no 2025–26 official Python editor scripting video.

---

## Q4. Fast gameplay creation (templates, GASP / Motion Matching, Mover, StateTree, GAS, UI, Chaos, Niagara)

### Takeaway
Starting points:
- Begin from a **UE 5.6+ template variant**, for example Third Person Combat, Platforming or Side Scroller, or Top Down Twin Stick or Strategy. Watch "New Template Sneak Peek".
- For character feel, use the **Game Animation Sample** (updated for 5.7 with a video, and for 5.8 with a blog).
- For AI behaviour, use the official "Your First 60 Minutes" StateTree and GAS tutorials.

### Cited Findings
- **New Template Sneak Peek | Inside Unreal** | Unreal Engine | streamed Apr 3, 2025 | https://www.youtube.com/watch?v=BHI6zx8QMkg (Epic links timestamp t=965s) | The template team previews the 5.6 template variants. **[V]** — [YouTube](https://www.youtube.com/watch?v=BHI6zx8QMkg)
  - Epic's template post lists the variants:
    - First Person: Survival Horror, Arena Shooter
    - Third Person: **Combat** (combos, AI enemies, health bars), **Side Scroller**, **Platform** (dash, wall jump)
    - Top Down: **Strategy**, **Twin Stick** (AI, score/multiplier UI)
    - Vehicle: Offroad, Time Trial
  - Choosing "None" gives a lightweight version.
  - Install walkthrough video: https://www.youtube.com/watch?v=rldy9yY0yDU **[E]**
  - Sources: [Epic news, Jun 11, 2025](https://www.unrealengine.com/news/updated-game-templates-for-unreal-engine-5-6available-now); [Variants doc](https://dev.epicgames.com/documentation/unreal-engine/variants-in-game-templates)
- **Game Animation Sample Project Update | Unreal Engine 5.7** | Unreal Engine | Feb 20, 2026 | https://www.youtube.com/watch?v=kmXaVIANa-c | Over 500 animations; Mover-based character; slide mechanic; Smart Object benches; new walking modes. Install from Fab, open in the matching engine version, and retarget your own or MetaHuman characters. Engine 5.7. **[V]** — [YouTube](https://www.youtube.com/watch?v=kmXaVIANa-c)
- GASP updated for UE 5.8 (blog, Aug 12, 2026, no video):
  - Physics Control; multi-character motion matching and interactions; powered ragdoll pawn (shoves, tackles, getups); additive look-at Control Rig; Mover blend stack via Chooser; Smart Objects via StateTree.
  - Fab listing 880e319a-….
  - Source: [Epic tech blog](https://www.unrealengine.com/tech-blog/download-the-latest-game-animation-sample-project-now-updated-for-ue-5-8)
- **Motion Matching and the Game Animation Sample in UE 5.4 | Unreal Fest 2024** | Unreal Engine | Aug 15, 2024 | 41:28 | https://www.youtube.com/watch?v=tNw9lD2PW3U | The foundational talk on the GASP toolset (motion matching, choosers, pose search) and best practices. Older version, but the concepts carry over. **[V]** — [YouTube](https://www.youtube.com/watch?v=tNw9lD2PW3U)
- **An Introduction to the Mover Plugin | Unreal Fest 2024** | Unreal Engine | Aug 28, 2024 | https://www.youtube.com/watch?v=P4IKS5k47Wg | Mover concepts versus CharacterMovementComponent, and rollback networking. Mover is still Experimental in 5.7/5.8, so for a 4-day solo jam, CMC is the safer default. **[V]** — [YouTube](https://www.youtube.com/watch?v=P4IKS5k47Wg)
- **Embracing Motion Matching: Using a Little to Get a Lot** | https://www.youtube.com/watch?v=FLDXtAV7qsw | Content inferred from title. The page failed to load. **[S]**
- **Your First Hour in Unreal Engine 5.7** | Unreal Engine | Dec 9, 2025 | https://www.youtube.com/watch?v=b37Z9l-_g7c | Luke Anderton (Tinkr Academy) builds a full coin-collect platformer covering Blueprints, UMG and testing. Good for a refresher on minimal game-loop scaffolding. Engine 5.7. **[V]** — [YouTube](https://www.youtube.com/watch?v=b37Z9l-_g7c)
- Epic course "Your First Game in Unreal Engine" (Jun 4, 2026; 2h43m):
  - Covers countdown, timer, game-over and level-complete screens, coin and speed boost, checkpoints and kill volumes, obstacles, and visuals.
  - This is essentially a jam-loop checklist.
  - No URL was extracted.
  - Source: [Epic learning](https://www.unrealengine.com/learning/start-building-games-with-our-new-course-your-first-game-in-unreal-engine)
- StateTree: Epic tutorial **"Your First 60 Minutes with StateTree"**. It builds a wildlife AI with StateTreeAIComponent and was posted around Jun 2024. — [EDC](https://dev.epicgames.com/community/learning/tutorials/lwnR/unreal-engine-your-first-60-minutes-with-statetree); [forum](https://forums.unrealengine.com/t/1901811)
- GAS: Epic for Indies tutorial "Your first 60 minutes with the Gameplay Ability System" (Spanish forum mirror posted Oct 17, 2025). — [EDC](https://dev.epicgames.com/community/learning/tutorials/7KW6/unreal-engine-epic-for-indies-tus-primeros-60-minutos-con-el-gameplay-ability-system-sistema-de-habilidad-de-juego)
- **Best Practices for Networked Movement Abilities | Unreal Fest Bali 2025** | Unreal Engine | Oct 13, 2025 | https://www.youtube.com/watch?v=tSVcRbfK8X8 | GAS + CMC for dash, vault, climb and grapple. Pick the movement verbs, skip the networking. **[V]** — [YouTube](https://www.youtube.com/watch?v=tSVcRbfK8X8)
- **Chaos Destruction for Beginners** (6-part community series in the July 2026 Epic roundup; URL not extracted). — [Epic Jul 2026 roundup](https://www.unrealengine.com/learning/julys-epic-learning-content-animation-mobile-game-development-and-more)
- **Unreal Engine 5.7 - Chaos Destruction for Beginners - Adding Niagara FX** | Crawford Terrace Studios (NON-OFFICIAL) | Jun 15, 2026 | https://www.youtube.com/watch?v=acNTJdvSX08 | Hooks Niagara to Chaos break events. It links a free Niagara Examples Pack on Fab. **[V]** — [YouTube](https://www.youtube.com/watch?v=acNTJdvSX08)
- **Dynamic Destruction in UE5 with the Chaos Destruction System** | https://www.youtube.com/watch?v=wPgd1J1Tf70 | Content inferred from title. The page failed to load. **[S]**
- Niagara: search surfaced "UE5.6 Niagara" https://www.youtube.com/watch?v=dPZXPQoC_AQ **[S]** and "Unreal Engine 5 - Hits and Impacts Effects - Niagara Tutorial" https://www.youtube.com/watch?v=u64lmeu22PM **[S]**. Both are from unknown channels and were not opened.

### Inferences
- The fastest path to a polished-feeling character is GASP (5.8) plus a template variant map, with the agent wiring game rules (score, timers, UI) via MCP Blueprint tools. Avoid experimental Mover and UAF unless the theme demands it.

### Gaps
- I found no 2025–26 official Common UI/UMG, Enhanced Input or Mass videos.
- I found no official Niagara quickstart video URL. Epic docs and the Fab Niagara Examples Pack are the fallback.

---

## Q5. Visuals fast (Lumen, MegaLights, PCG, Mesh Terrain, Fab/Megascans, MetaHuman, stylized looks, Sequencer/MRG)

### Takeaway
For a 4-day visual win, the most relevant official material is:
- MegaLights 5.8 Inside Unreal (Oct 8, 2026)
- "A First Look at PCG in UE 5.7"
- the UE 5.7 Sneak Peek
- Movie Render Graph Intro, for the trailer and gameplay video

Substrate NPR shading (5.8, experimental) is the official route to toon/cel looks.

### Cited Findings
- **Artist's Guide to Using MegaLights in Unreal Engine 5.8 | Inside Unreal** | Unreal Engine | Oct 8, 2026 | 2:46:35 | https://www.youtube.com/watch?v=Nrb17mtBJPM | Dan Hutnik and Daryl Obert cover what MegaLights is, setup, best practices and tips. MegaLights is production-ready in 5.8, which enables many shadowed dynamic lights cheaply. **[V]** — [YouTube](https://www.youtube.com/watch?v=Nrb17mtBJPM); [forum](https://forums.unrealengine.com/t/artists-guide-to-using-mega-lights-in-unreal-engine-5-8-inside-unreal/2838343)
- **Unreal Engine 5.7 Sneak Peek | Unreal Fest Stockholm 2025** | Unreal Engine | Nov 24, 2025 | https://www.youtube.com/watch?v=VgYwMx5xmDk | A fast tour of 5.7: MegaLights to beta, Substrate on by default, Nanite Foliage, PCG production-ready, and retargeting fixes (per notes). **[V]** — [YouTube](https://www.youtube.com/watch?v=VgYwMx5xmDk); notes via [readray](https://readray.ai/ar/notes/unreal-engine-5-20251128/unreal-engine-5-7-preview-stockholm-2025)
- **A First Look at Procedural Content Generation in Unreal Engine 5.7** | Unreal Engine | Feb 5, 2026 | https://www.youtube.com/watch?v=bgxVHKSdL4M | Covers:
  - the PCG Editor Mode (draw splines, paint points, volumes, each tied to a graph)
  - Polygon2D, spline intersect and split operators, custom data types
  - recap of 5.6 PCG templates, the Data Viewport and **Biome Core V2**
  - the experimental Procedural Vegetation Editor
  - Engine 5.6/5.7. **[V]** — [YouTube](https://www.youtube.com/watch?v=bgxVHKSdL4M)
- **Procedural Cities for Tech Artists: Geometry Scripting & PCG | Unreal Fest Chicago 2026** | Unreal Engine | Oct 3, 2026 | https://www.youtube.com/watch?v=7uuFPOKIw8I | Lucid Games' PCG plus Geometry Scripting building and block tools. **[V]** — [YouTube](https://www.youtube.com/watch?v=7uuFPOKIw8I)
- **A Practical Look at Mesh Terrain** (Inside Unreal) | https://www.youtube.com/watch?v=XlbWtoIk-Zc | Experimental 5.8 3D mesh-based terrain. Listed by Epic's Aug 2026 roundup; the page did not open. **[E]** — [Epic Aug 2026 roundup](https://www.unrealengine.com/learning/augusts-epic-learning-content-networked-physics-dynamic-audio-and-more)
- PCG text tutorials from the Epic Apr 2026 roundup:
  - "PCG for Beginners | 01 Level Setup & First PCG Graph" — [EDC](https://dev.epicgames.com/community/learning/tutorials/l5v0/unreal-engine-fab-ue5-series-pcg-for-beginners-01-level-setup-first-pcg-graph)
  - "Avoid Overlapping Assets" — [EDC](https://dev.epicgames.com/community/learning/tutorials/Ev4d/unreal-engine-ue5-series-pcg-for-beginners-avoid-overlapping-assets-easily)
  - "PCG Parameters Explained" — [EDC](https://dev.epicgames.com/community/learning/tutorials/v7YZ/unreal-engine-ue5-series-pcg-for-beginners-pcg-parameters-explained)
  - "PCG Blueprint Elements in UE 5.7" — [EDC KB](https://dev.epicgames.com/community/learning/knowledge-base/l574/unreal-engine-pcg-blueprint-elements-in-5-7)
  - "How to Fix Lumen Light Flickering…" — [EDC](https://dev.epicgames.com/community/learning/tutorials/mmxB/how-to-fix-lumen-light-flickering-in-unreal-engine-without-losing-performance)
- **Ultimate City PCG… UE 5.5 – Step 1** | BrokeAsDev (NON-OFFICIAL) | May 24, 2025 | https://www.youtube.com/watch?v=k9YVBSs6_mQ | Puget recommended it as a faster PCG route than asking an LLM to author graphs. **[V]** — [YouTube](https://www.youtube.com/watch?v=k9YVBSs6_mQ)
- Stylized look: "Create a Material with Substrate NPR Shading in Unreal Engine 5.8" (community tutorial for toon/cel and graphic-novel looks; listed in Epic's June 2026 roundup; URL not extracted). — [Epic Jun 2026 roundup](https://www.unrealengine.com/learning/junes-epic-learning-content-metahumans-mesh-terrain-and-more)
- **Movie Render Graph Intro | Unreal Engine Animation Hub** | Unreal Engine | Dec 5, 2025 | https://www.youtube.com/watch?v=0c8-8NSarDI | Renders shots to layers with Movie Render Graph (production-ready in 5.8). Use it for the trailer and gameplay video. **[V]** — [YouTube](https://www.youtube.com/watch?v=0c8-8NSarDI)
- MetaHuman:
  - In 5.8, MetaHuman moves to an MIT license, gains Collections and Crowds, Mesh-to-MetaHuman for any human mesh, and a free MetaHuman Crowd Sample on Fab. — [Edge](https://knowledge.edge-online.com/p/ai-goes-native-in-unreal-engine-the-five-main-takeaways-from-state-of-unreal-2026)
  - Markerless Motion Capture plugin on Fab. — [Epic news](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show)
  - **State of Rigging and Animation Tools in Unreal Engine 5.8 | Unreal Fest Chicago 2026** | Unreal Engine | Jul 14, 2026 | https://www.youtube.com/watch?v=yi-oDmC1nqU | In-engine rigging and animation updates; free Zebra Character Sample on Fab. **[V]** — [YouTube](https://www.youtube.com/watch?v=yi-oDmC1nqU)
  - MetaHuman Creator search results, not opened: "Creating Bespoke Characters with MetaHuman Creator" https://www.youtube.com/watch?v=b8DI-Neocz4 **[S]** (page failed) and "An In-Depth Tour of Metahuman Creator Motion Capture" https://www.youtube.com/watch?v=vlKbASuh0L4 **[S]**.
- **Animation Techniques in Unreal Engine 5.8 | Unreal Fest 2026 Lab** | Sir Wade Neistadt (NON-OFFICIAL channel, Fest lab) | Jun 23, 2026 | 1:00:25 | https://www.youtube.com/watch?v=Cc1YgOxdNI8 | In-engine keyframing, physics control rigs, ragdoll sequences and "mouse mocap". Useful for quick custom anims and cutscenes. **[V]** — [YouTube](https://www.youtube.com/watch?v=Cc1YgOxdNI8)

### Inferences
- A solo jam look that should read well quickly: a stylized Substrate NPR or post-process look, MegaLights for many dynamic lights, PCG Biome Core and an editor-mode tool for set dressing, plus Fab assets.
- MetaHumans are heavy. The 5.8 Crowd and Collections path, or GASP Manny/Quinn, is cheaper than custom MetaHuman Creator work in 4 days.

### Gaps
- I found no official 2025–26 Lumen-for-games or Nanite quickstart video URL.
- I found no official Fab/Megascans workflow video URL.
- The Substrate NPR tutorial URL was not extracted.

---

## Q6. Audio (MetaSounds)

### Takeaway
Official MetaSounds video material found is old (2021) or text-based. The newest useful items are Epic's SFX Generator MetaSound tutorial and a 2026 community granular-synthesis tutorial.

### Cited Findings
- **MetaSounds in UE5: From Miniguns to Music** | Unreal Engine | Aug 17, 2021 | https://www.youtube.com/watch?v=3230-FwCts0 | A conceptual intro to procedural and varied SFX. Older, but the concepts still apply. **[V]** — [YouTube](https://www.youtube.com/watch?v=3230-FwCts0)
- Epic tutorial "Using the SFX Generator in the Tech Audio Tools Content Plugin": a procedural runtime SFX generator MetaSound in a free plugin, which is great for placeholder or final jam SFX. Listed in Epic's March 2026 roundup; URL not extracted. — [Epic Mar 2026 roundup](https://www.unrealengine.com/learning/marchs-epic-learning-content-substrate-metahuman-and-more)
- "MetaSound Adaptive Granular Synthesis" (community). — [EDC](https://dev.epicgames.com/community/learning/tutorials/jaX5/unreal-engine-metasound-adaptive-granular-synthesis)
- MetaSounds Quick Start doc. — [Epic docs](https://dev.epicgames.com/documentation/unreal-engine/metasounds-quick-start). A forum user asks whether it is outdated. — [forum](https://forums.unrealengine.com/t/is-the-metasounds-quick-start-tutorial-outdated/2732307)
- Audio Insights is production-ready in 5.8. — [Epic news](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show)
- "Unreal Engine 5 Tutorial - Metasounds Part 1: Getting Started" https://www.youtube.com/watch?v=SAED1BDA1Qc **[S]**. Channel unknown; not opened.

### Inferences
- Past MegaJams had an "Audio Experience" modifier (2022, 2023). Ten minutes on a MetaSound SFX Generator setup could pay off if a similar modifier appears.

### Gaps
- I found no 2025–26 official MetaSounds quickstart video on YouTube.

---

## Q7. Optimization, packaging and shipping (Windows/Android, Project Launcher, Zen)

### Takeaway
Must-watch: Matt Oztalay's "How to Start Your Project at 60 FPS and Keep It There" (Chicago 2026, with an EDC resource hub of CVars). Packaging is best covered by short community videos and Epic docs. I found no official 2025–26 video on Zen or Project Launcher.

### Cited Findings
- **How to Start Your Project at 60 FPS and Keep It There | Unreal Fest Chicago 2026** | Unreal Engine | Jul 22, 2026 | https://www.youtube.com/watch?v=DxBKmQ-0kfw | Covers building at your target frame rate from day one, monitoring and diagnostic tools, and recovering frame rate when off track. A companion resource page lists CVars. **[V]** — [YouTube](https://www.youtube.com/watch?v=DxBKmQ-0kfw); [EDC resource hub](https://dev.epicgames.com/community/learning/talks-and-demos/YoB7/unreal-engine-how-to-start-your-project-at-60-fps-and-keep-it-there)
- **101 Unreal Engine Tips & Tricks: The Reckoning | Unreal Fest Stockholm 2025** | Unreal Engine | Nov 29, 2025 | https://www.youtube.com/watch?v=4w0PWcRwyOc | Rapid-fire tips:
  - Property Matrix
  - simple collision by default
  - Chaos Visual Debugger
  - cooker instigator logging
  - Insights task channel
  - global INI overrides
  - Blueprint diff and debug
  - Mesh-to-Collision
  - `dp.override`
  - Notes per a third-party transcript summary. **[V]** — [YouTube](https://www.youtube.com/watch?v=4w0PWcRwyOc); [transcript notes](https://wiki.kwonsh.duckdns.org/101-Unreal-Engine-Tips-&-Tricks--The-Rec/101-Unreal-Engine-Tips-%26-Tricks--The-Rec.html)
- **Systemic Shader Reduction: How We Cut Fortnite's Shaders by 68% | Unreal Fest Chicago 2026** | Unreal Engine | Jul 17, 2026 | https://www.youtube.com/watch?v=wobQ8ZKQpbc | Material permutation reduction and 5.8 shader-footprint optimizations. Fewer shaders mean faster cooks and less first-run hitching. **[V]** — [YouTube](https://www.youtube.com/watch?v=wobQ8ZKQpbc)
- Other Chicago 2026 performance sessions, seen in search only **[S]**:
  - "Profiling with Pirates: Performance Plundered from a Real Game" https://www.youtube.com/watch?v=CYvLn-tYRag
  - "Fighting the Frame Budget: Stage Optimization Lessons from 2XKO" https://www.youtube.com/watch?v=Pkd7-ouyb-M
  - "Optimizing Next-Gen Mobile Features in Unreal Engine" https://www.youtube.com/watch?v=TnRvkxf6tZY
- Epic tutorial "Optimization - Examining Tools and Techniques" (June 2026 roundup; URL not extracted). — [Epic Jun 2026 roundup](https://www.unrealengine.com/learning/junes-epic-learning-content-metahumans-mesh-terrain-and-more)
- Epic "Performance Tuning for Unreal Engine Mobile Development". — [EDC](https://dev.epicgames.com/community/learning/tutorials/X7Me/performance-tuning-for-unreal-engine-mobile-development)
- Packaging videos (all NON-OFFICIAL):
  - **"How to Build Your Game in Unreal Engine 5 - Super Easy"** | Gorka Games | ~Jan 13, 2023 | https://www.youtube.com/watch?v=JOMrVMwGBso | Package Project flow: Shipping vs Development, default map, platforms, icon and splash. Older UE5.x; ID and channel via [readray notes](https://readray.ai/ru/notes/unreal-engine-5-20260202/build-game-ue5-easy), watch page not opened **[S+notes]**.
  - **"How to package your Unreal Engine 5.7 project and share it with everyone!"** | UNF Games | Nov 13, 2025 | https://www.youtube.com/watch?v=AWzhZnSq9u0 | Engine 5.7. **[V]** — [YouTube](https://www.youtube.com/watch?v=AWzhZnSq9u0)
  - **"How to use Project Launcher to package a game in UE5"** | Eidolon | Sep 6, 2023 | https://www.youtube.com/watch?v=XAtOXmyqq18 | Custom launcher profile for a shipping build (UE 5.0-era UI; the Project Launcher was redesigned later, so verify). **[V]** — [YouTube](https://www.youtube.com/watch?v=XAtOXmyqq18)
  - Android: "On-Click Unreal Engine 5.7 Android Packaging & APK Build Tutorial" https://www.youtube.com/watch?v=SCtAfDeWXBM **[S]** with companion blog [babaei.net](https://www.babaei.net/blog/unreal-engine-android-packaging-apk-build-tutorial-meta-quest-htc-vive-standalone/)
  - Epic docs: [Packaging Your Project](https://dev.epicgames.com/documentation/unreal-engine/packaging-your-project) and [Packaging Android Projects](https://dev.epicgames.com/documentation/en-us/unreal-engine/packaging-android-projects-in-unreal-engine)

### Inferences
- Package a Windows Shipping build on Nov 12 (day 1) and upload via butler, as the 8-tips article recommends. Have an agent script the BuildCookRun/RunUAT command so repackaging is one command. This is my inference; it is not covered by a video.

### Gaps
- I found no official 2025–26 video on Zen Server/Zen loader or the redesigned Project Launcher.

---

## Q8. Inside Unreal livestreams and Unreal Fest talk recordings (index)

### Takeaway
Unreal Fest events since 2025:
- Orlando (June 2025; 121-video playlist)
- Stockholm (Sept 22–24, 2025)
- Bali 2025
- Gold Coast 2024
- **Chicago (June 16–18, 2026)**, with sessions uploaded to YouTube from June through at least Oct 3, 2026

There was **no "Unreal Fest Seattle 2025"** in sources found. Relevant Inside Unreal episodes found: Template Sneak Peek (Apr 2025), MegaJam 2025 Winners (Mar 2026), MegaLights 5.8 (Oct 2026), Mesh Terrain (2026).

### Cited Findings
- Chicago 2026: June 16–18, with State of Unreal on June 17 at 7 AM PT. — [Epic event page](https://www.unrealengine.com/events/unreal-fest-chicago-2026)
- Orlando 2025 playlist (121 videos) and Stockholm Sept 22–24, 2025 (80+ sessions). — [80.lv](https://80.lv/articles/watch-unreal-fest-orlando-2025-sessions-online-now)
- Unreal Fest hub page: Orlando 2025 had 190+ sessions; it also mentions Stockholm 2025, Bali 2025 and Chicago 2026. — [Epic Unreal Fest](https://www.unrealengine.com/unreal-fest)
- Additional Chicago 2026 sessions seen in search only (titles only, **[S]**):
  - "Agora Studio's Real-Time Animation Workflow in UE5" https://www.youtube.com/watch?v=hc6xf-3uDX8
  - "All in on UE: What Happens When 100 Animators Stop Round-Tripping" https://www.youtube.com/watch?v=4fcC1GVSRxU
  - "Building Cartoony Facial Rigs with Control Rig in Unreal Engine" https://www.youtube.com/watch?v=NysFumZcmcQ
  - "MetaHumans x Clo: Workflows and Best Practices" https://www.youtube.com/watch?v=A9CtqkjEa94
- "State of Virtual Production" (Chicago 2026) https://www.youtube.com/watch?v=5SJA1FfRPWs **[E]**. Not jam-relevant.
- Unreal Fest Bali 2025 GAS designer-examples tech notes. — [EDC](https://dev.epicgames.com/community/learning/tutorials/Ekmj/unreal-engine-unreal-fest-bali-2025-gameplay-ability-system-game-designer-examples-technical-notes)

### Inferences
- The Chicago 2026 playlist is the richest current source. Run a direct scan of it (at youtube.com, logged in) for "AI", "MCP", "PCG", "Gameplay", "UI" and "Audio" titles before Nov 12. My scan was search-limited.

### Gaps
- I could not enumerate the Orlando 2025 or Chicago 2026 playlists, or the Inside Unreal 2025–26 back catalog.
- I could not confirm whether Epic will hold an AI MegaJam prep Inside Unreal before Nov 11.

---

## Q9. High-value NON-OFFICIAL channels (clearly not Epic)

### Takeaway
Smart Poly has the best AI and MCP-specific 5.8 content. Unreal Sensei has the best version overviews and the Mesh Terrain tutorial. William Faucher is best for lighting. Gorka Games is quick for packaging. I could not verify specific recent videos from Ryan Laley, Matt Aspland, Kekdot or Ali Elzoheiry.

### Cited Findings
Unless marked [V], each item was listed on [developereducators (updated Oct 25, 2026)](https://developereducators.com/best/unreal-engine/) and its watch page was not opened.
- **Smart Poly** (@smartpoly):
  - MCP QuickStart PqrKqhkj3gQ **[V]**
  - "I Tested Claude Inside UE 5.8" OiFtnBj1P9o **[V]**
  - "Unreal Engine 5 Beginner Tutorial | Getting Started (2026)" https://www.youtube.com/watch?v=gBIFMoFkZP4 (~Feb 2026; UE 5.7.1; via [readray](https://readray.ai/en/notes/unreal-engine-5-20260813/unreal-engine-5-beginner-tutorial-getting-started)) **[S+notes]**
  - "Unreal Engine 5.8 New Features Explained!" https://www.youtube.com/watch?v=K0DdXwmGJ9Q **[S]**
- **Unreal Sensei** (@unrealsensei):
  - "Why Unreal Engine 5.8 is a Game Changer" | Jun 17, 2026 | https://www.youtube.com/watch?v=5d6mZNA_5sg | Mesh Terrain, Lumen probe occlusion, MetaHuman Creator, Edit PCG, movement features. **[V]** — [YouTube](https://www.youtube.com/watch?v=5d6mZNA_5sg)
  - "How to Use Unreal Engine's New Landscape System - Mesh Terrain Tutorial" (1:06:18) https://www.youtube.com/watch?v=Lhj2LutYNjA **[S]**
  - "How to Create a Game in Unreal Engine 5 - UE5 Beginner Tutorial" (2:39:04, ~2023) https://www.youtube.com/watch?v=1XjgLKrb4_M **[S]**
- **William Faucher** (@williamfaucher): "Lighting in Unreal Engine 5 for Beginners" (44:44, ~2022) https://www.youtube.com/watch?v=fSbBsXbjxPo **[S]**. Still a widely cited Lumen lighting primer.
- **Gorka Games** (@gorkagames): packaging video JOMrVMwGBso (see Q7). Also "Unreal Engine 6 is Removing Blueprints…" https://www.youtube.com/watch?v=cLQoSpsK5Ek **[S]**, which is context only.
- **GameFromScratch**: "Unreal Engine 5.8 Is HERE ...and So Is AI!" | Jun 17, 2026 | 12:54 | https://www.youtube.com/watch?v=WJLe8WdHv9g | Quick 5.8 overview. **[V]** — [YouTube](https://www.youtube.com/watch?v=WJLe8WdHv9g)
- **Bad Decisions Studio**: "Unreal Engine + AI is a crazy combo" (1:52) https://www.youtube.com/watch?v=5iiWHbpCoHY **[S]**
- **Sir Wade Neistadt**: Fest 2026 animation lab Cc1YgOxdNI8 **[V]** (see Q5).
- **Matt Aspland** (https://youtube.com/@mattaspland) and **Ali Elzoheiry** (https://youtube.com/@alielzoheiry) are listed as recommended channels. No specific standout video was verified. — [developereducators channels](https://developereducators.com/tutorials/unreal-engine/)
- **Ryan Laley**: a recognized tutorial channel (e.g., UE5 Data Layers and Compass UI series per [gamesinprogress](https://www.gamesinprogress.com/indie-game-developers/ryan-laley/unreal-engine-5-tutorial-data-layers)). I saw no YouTube URL. **Kekdot**: no sources found.

### Inferences
- For AI-agent workflows specifically, the Smart Poly pair (setup plus an honest capability test) is the most directly useful non-Epic content.

### Gaps
- I did not find standout video URLs for Ryan Laley, Matt Aspland, Ali Elzoheiry (e.g., his StateTree or GAS series) or Kekdot.

---

## Q10. MUST-WATCH BEFORE NOV 12 (~15, prioritized for a solo, agent-heavy, regular-UE entry)

### Takeaway
About 6–8 hours total if you skim long streams by chapter. Watch the AI and workflow items first, then the gameplay starters, then visuals and shipping.

### Cited Findings
1. **State of Unreal 2026**, the MCP chapter at 41:47 plus the 5.8 chapter at 33:28 — https://www.youtube.com/live/9ikOoOzAhPE [V, official]
2. **From Words to Worlds: Integrating MCP into the Unreal Editor** (Chicago 2026) — https://www.youtube.com/watch?v=lDf_y-YPELo [V, official]
3. **NEW UE 5.8 MCP Tutorial (QuickStart)**, Smart Poly, 12:21 — https://www.youtube.com/watch?v=PqrKqhkj3gQ [V, non-official]
4. **I Tested Claude Inside UE 5.8**, Smart Poly — https://www.youtube.com/watch?v=OiFtnBj1P9o [V, non-official]
5. **Epic MegaJam 2025 Winners Announcement | Inside Unreal** — https://www.youtube.com/watch?v=SsR4mzX9-4o [V, official]
6. **Unreal Engine 5.8 Is Now Available** (8:30) — https://www.youtube.com/watch?v=Aaf12f_LA_Y [V, official]
7. **New Template Sneak Peek | Inside Unreal** (template variants) — https://www.youtube.com/watch?v=BHI6zx8QMkg [V, official]
8. **Game Animation Sample Project Update | UE 5.7** — https://www.youtube.com/watch?v=kmXaVIANa-c [V, official]. Then read the [5.8 GASP blog](https://www.unrealengine.com/tech-blog/download-the-latest-game-animation-sample-project-now-updated-for-ue-5-8).
9. **A First Look at PCG in UE 5.7** — https://www.youtube.com/watch?v=bgxVHKSdL4M [V, official]
10. **Artist's Guide to Using MegaLights in UE 5.8 | Inside Unreal** (2:46; skim) — https://www.youtube.com/watch?v=Nrb17mtBJPM [V, official]
11. **How to Start Your Project at 60 FPS and Keep It There** — https://www.youtube.com/watch?v=DxBKmQ-0kfw [V, official]
12. **101 Unreal Engine Tips & Tricks: The Reckoning** — https://www.youtube.com/watch?v=4w0PWcRwyOc [V, official]
13. **Movie Render Graph Intro** (for the trailer and gameplay video) — https://www.youtube.com/watch?v=0c8-8NSarDI [V, official]
14. **Your First Hour in Unreal Engine 5.7** (skim, as a jam-loop scaffold) — https://www.youtube.com/watch?v=b37Z9l-_g7c [V, official]
15. **How to package your UE 5.7 project…** (UNF Games) — https://www.youtube.com/watch?v=AWzhZnSq9u0 [V, non-official]. Alternatively Gorka Games JOMrVMwGBso.
- Optional:
  - Best Practices for Networked Movement Abilities (movement verbs) — https://www.youtube.com/watch?v=tSVcRbfK8X8 [V]
  - Epic MegaJam 2023 Winners — https://www.youtube.com/watch?v=e8falymc1Nk [V]
  - MCP in UEFN stream — https://youtube.com/live/OU5OT06YxtQ [V] (agent loop demo; UEFN)
- Must-read non-video items:
  - [Unreal MCP in Unreal Editor docs](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor?lang=en-US)
  - [Epic's Unreal Engine skills for Claude Code plugin](https://claude.com/plugins/unreal-engine-skills-for-claude-code)
  - [Puget MCP hands-on](https://www.pugetsystems.com/blog/2026/07/09/unreal-engine-mcp-hands-on-testing-ai-inside-the-editor/)
  - [Your First 60 Minutes with StateTree](https://dev.epicgames.com/community/learning/tutorials/lwnR/unreal-engine-your-first-60-minutes-with-statetree)
  - [8 tips for surviving the Epic MegaJam](https://unrealsource.com/n/8-tips-for-surviving-the-epic-megajam/)
  - [City Sample PCG + MCP update](https://www.unrealengine.com/learning/city-sample-gets-a-major-update-with-pcg-and-unreal-mcp-workflows)
- **Live, not yet recorded:** the Nov 11 kickoff and theme reveal on youtube.com/unrealengine or twitch.tv/unrealengine — [Epic forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843983)

### Inferences
- Rehearse the Smart Poly MCP setup and the Epic Claude Code skills plugin on a throwaway 5.8 project before Nov 12. Setup is explicitly allowed pre-jam. Then the 4 jam days go to building, not tooling.

### Gaps
- Lengths were not recoverable for most videos because of YouTube bot-protection.
- No video was watched end to end. Summaries come from descriptions, Epic write-ups and third-party transcript notes.
