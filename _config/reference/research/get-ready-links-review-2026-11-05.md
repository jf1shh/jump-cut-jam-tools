# Get ready links review (itch.io jam page, Tools + Tips), 2026-11-05

Ticket T-20261105-22. Source: the "Get ready" section of <https://itch.io/jam/2026-epic-ai-megajam>, hub extract `~/.cache/hub-review-megajam/get-ready-section-2026-11-05.txt`. Compared against `AGENTS.md`, `PLAN.md`, `RULES.md`, `stages/00_prep/references/win-plan.md`, `_config/reference/knowledge-base.md`, `stages/00_prep/references/jam-day-runbook.md`, `_config/reference/research/ai_agents_mcp_and_asset_pipelines.md`. We use UE 5.8 on Linux (editor) plus the Legion Go S (Windows build). No other doc was edited; proposed edits are listed at the end.

Update T-20261105-24 (2026-11-05): links 1, 2, 8 and 11 were read in Chrome by the hub (read only, no sign-in, no posting). Source: `~/.cache/hub-review-megajam/chrome-notes-2026-11-05.md`. Link 13 (Discord) stays unopened.

How the reading was done: WebFetch for pages; YouTube by subtitles only (`yt-dlp --skip-download --dump-single-json`, then the auto-caption JSON fetched to stdout; no video or audio, and no files written because the ticket guard allows only the claimed file). No sign-in anywhere. Four Epic web pages (links 1, 2, 8, 11) answered bots with HTTP 403. The hub then read all four in Chrome on 2026-11-05 (read only); see the table.

## Coverage table (13 links)

| # | Link | Status | Why / what was read |
|---|---|---|---|
| 1 | Unreal Engine download (unrealengine.com/download) | **Read in Chrome** (hub, 2026-11-05) | Was 403 on WebFetch. Full page read by the hub. |
| 2 | UEFN download (Epic Store page) | **Read in Chrome** (hub, 2026-11-05) | Was 403 on WebFetch. Store page read by the hub. Not relevant. |
| 3 | MCP in UE: setup video (YouTube `FON_noub0C0`) | **Read fully** | Title, description, full transcript (4:13). No chapters. |
| 4 | MCP in UE: documentation | **Read fully** | The page has no sub-pages; it links only to the MCP spec and Inspector. |
| 5 | MCP in UE: livestream (`k0tgmrBuIJc`) | **Read fully** | Title, description, full transcript (60:52). No chapters. |
| 6 | MCP in UEFN: documentation | **Read fully** | Main page plus the two sub-pages it links (Python scripting, profiling); the third related page is the UE MCP doc (link 4). UEFN only. |
| 7 | MCP in UEFN: livestream (`OU5OT06YxtQ`) | **Read fully** (update) | Full 2:08:40 subtitle transcript, 0 to 128 min, read by a helper agent and digested (second pass 2026-11-05). Minute marks are estimates. |
| 8 | AI-powered NPC conversations (fortnite.com news) | **Read fully in Chrome** (hub, 2026-11-05) | Was 403 and second-hand only. Full article read by the hub (Epic post dated Apr 16, 2026). UEFN only. |
| 9 | Fab (fab.com) | **Read** (front page) | Front page only. No licence terms or AI policy on the page. |
| 10 | Packaging Unreal Engine projects | **Read fully; sub-pages partly** | Main page plus Build Configurations, Project Launcher, and the Sharing and Releasing index. The Content Cooking, Cooking and Chunking and Releasing Your Project pages returned only a table-of-contents heading to WebFetch (dynamic content), so they are **not read**. |
| 11 | Epic Developer Community (dev.epicgames.com/community) | **Read in Chrome** (hub, 2026-11-05) | Was 403. Portal read by the hub (layout via the accessibility tree; no sign-in). The doc pages we need (links 4, 6, 10) were read directly. |
| 12 | Unreal Engine Forums (`epic.gm/2026-ue-megajam`) | **Read** (pages 1 and 2) | Redirects to the "Looking for teammates? Start here" thread. Page 1: 19 replies, Oct 22 to Nov 3. Page 2: Nov 5 posts. The fetch tool did not show whether a page 3 exists. |
| 13 | UEFN Discord channel | **Not opened** (login wall) | Discord invite-style channel link. Not opened by me or by the hub: login wall, and the owner was not asked to use an account. Nothing public recorded. |

Net (updated 2026-11-05 after the hub's Chrome reads): 12 links read (links 1, 2, 8 and 11 now read in Chrome by the hub; link 9 front page only; link 10 with three packaging sub-pages still unread). 1 not opened (link 13, Discord login wall). Three packaging sub-pages stayed unreadable (see link 10).

## Per-link notes

### 1. Unreal Engine download: read in Chrome (hub, 2026-11-05)
Facts from the page:
- Install path: Epic Games launcher, log in, Unreal Engine tab, Install (latest version), or build from source.
- Listed minimum specs: Windows 10 64-bit, quad-core 2.5 GHz, 8 GB RAM, DX11/12 GPU. Linux: Ubuntu 18.04, 32 GB RAM, RTX 2080 or higher. macOS 13.
- Licence: free under $1M gross revenue (royalties after $1M for games); seat licence only for non-game commercial use over $1M.

Verdict: nothing new to act on. Keep "same exact UE 5.8.x on both machines" (AGENTS.md). The Linux line names an NVIDIA RTX 2080 or higher; our desktop is an AMD RX 9070 XT, which we already run on UE 5.8. No conflict.

### 2. UEFN download: read in Chrome (hub, 2026-11-05)
Store page for Unreal Editor for Fortnite. Needs Fortnite installed and an Epic ID. Released 03/22/23. Pitch: build and publish islands inside Fortnite; cross-platform reach; engagement payouts (Epic says over $1B paid to third-party developers) plus in-island item sales. Windows only: minimum Windows 10 1703, Core i3-3225, 8 GB RAM; recommended Windows 10/11, 16 GB RAM, 8 GB VRAM, NVMe SSD.

Verdict: not relevant. AGENTS.md says UE over UEFN; the Forum thread (link 12) quotes the rule "pick one". UEFN ships into Fortnite, not a packaged UE game.

### 3. Setup video, "A First Look at Unreal MCP in Unreal Engine 5.8" (Unreal Engine channel, uploaded 2026-10-08, 4:13)
- Description calls it "an official, Epic-supported way" to connect agent tools; says UE "5.8 and later" in the voiceover.
- Windows walkthrough with Claude Code: enable **Unreal MCP, All Toolsets and Terminal** plugins, restart; Editor Preferences, Model Context Protocol, **Auto Start Server**; Terminal plugin startup commands (`TERM`, `cd` to project, launch `claude`); console command writes `.mcp.json`; open Tools, Terminal; test prompts (make a blue cube and chrome sphere, move up 132 units, space five cubes evenly).
- Verdict: **covered.** KB lines 257 to 272 and the research note already have the same steps. Differences: it is Windows only (we are on Linux; our terminal is the Claude Code CLI, not the in-editor Terminal plugin). Nothing conflicts.

### 4. Documentation, "Unreal MCP in Unreal Editor" (UE 5.8 docs, no date shown)
- Labelled Experimental. Server on `http://127.0.0.1:8000/mcp` (port and path configurable; flags `-ModelContextProtocolStartServer`, `-ModelContextProtocolPort=N`). Client names: ClaudeCode, Cursor, VSCode, Gemini, Codex, All.
- Tool Search on by default (three meta-tools: `list_toolsets`, `describe_toolset`, `call_tool`). Console variables listed (`PaginationPageSize`, `ProgressIntervalSeconds`, `EnableAnalytics` and others).
- Limits: HTTP/SSE only, loopback, no auth, serial tool calls on the game thread, new `UFUNCTION`s need an editor restart, toolset registry adapter is editor-only.
- Verdict: **covered.** Our research note and KB quote the same limits. The doc says nothing about Linux (already flagged in KB line 270; our rehearsal passed). Port: doc default 8000, ours 8010 because Nexus holds 8000 (runbook line 22; dress rehearsal 2c). Consistent.

### 5. Livestream, "Getting Started with MCP in Unreal Engine 5.8 | Epic Games Education Webinar" (uploaded 2026-09-07, 60:52)
Epic instructor, Windows, Claude Code, plus an Epic trainer on other harnesses. Key points that matter to us:
1. **Three plugins, not two.** The speaker says the online docs miss one: Unreal MCP, All Toolsets, and **Editor Toolsets**. Without Editor Toolsets the agent "connects but can't do anything". (The setup video, link 3, names Terminal as the third instead.) **New to us.** Our docs list only Unreal MCP and All Toolsets (plus optional Terminal). Our rehearsal got about 50 toolsets and spawned an actor, so it works on our build, possibly because All Toolsets pulls Editor Toolsets in, but we never wrote it down. Verify.
2. **Restart before the Model Context Protocol preference section appears.** Preference is hidden until the plugin loads. Already implied by our runbook; harmless.
3. **Context blow-out.** The second Epic trainer says `describe_toolset` output is huge: materials about 2,000 to 26,000 tokens, **Niagara almost a quarter of a million**. Small-context models truncate it, then loop by trial and error ("take forever and cost you a fortune"). Healthy check: a simple material should take about one minute. Epic is exploring a search feature; a trainer-made PDF with a trimmed toolset guide exists (the QR link was reported broken). **New to us.** Our KB mentions Tool Search but not these sizes. This is a real day-one budget risk with a 24/7 loop.
4. **Prompt habits:** name things exactly; one task per prompt; ask before you tell ("do you understand my intent?"); read the plan before accepting. Complex or "make a whole game" prompts fail; specific blueprint targets work (a box on `BP_ThirdPersonCharacter`, not "the player's head").
5. Agents do odd things in Blueprint (150 delays instead of a timeline); **C++ or Python gets better results than Blueprint**; animation generation is not supported (Sequencer, control rigs, animation blueprints are). Materials: the agent wrote HLSL; the speaker made it redo with material nodes. One trainer adds a build check that errors on `Event Tick`.
6. Experimental: "stay on 5.8 if you build on it". Output Log category `LogModelContextProtocol`, `Log LogModelContextProtocol Verbose`; MCP Inspector as last resort. Default port 8000; change it if running several things.
7. Runs on any of five clients; Epic's testing is mostly on Claude.
- Verdict: points 1, 3 and 5 are **new**. Point 5 conflicts mildly with CLAUDE.md "Default to Blueprint" (CLAUDE.md says Blueprint iterates faster for a 4-day jam and MCP drives graphs directly; the trainers say C++ is better trained). Our mock-jam finding 2 (Blueprint event-graph Python wall) agrees with the trainers. Not a rule change, but a note for the lead agent. Everything else **covered** (loopback, serial calls, output log).

### 6. Documentation, "UEFN MCP" (no date), with sub-pages
Sub-pages, one line each, for what also applies to UE MCP:
- *Python Scripting with UEFN MCP*: batch many actions into one script instead of one call each; a restricted sandbox is safer, "Execute Python" (full API) is faster but unchecked and freezes the editor, so split long jobs, test small, keep work in source control; `time.sleep` is rejected; vague prompts add unrequested steps. Applies to us (our Python toolsets and `ue_*.py` scripts).
- *Profiling Your Island with the UEFN MCP*: agent runs profilers, proposes a plan, you approve, it re-measures. UEFN tools only (Spatial Profiler, Timing Insights, Memory Snapshot); the loop (baseline, fix, re-measure) is reusable for our QA harness, nothing new for the rulebook.
- *Unreal MCP* (related doc): our link 4.

Main page:
UEFN-only server (Verse, Scene Graph, Creative Devices, Play Session toolsets). Setup path differs: Editor Preferences, Agentic Workflows, Model Context Protocol; `.mcp.json` under `.../FortniteGame`. Default port 8000 also. Known issues: hitches and hangs on tool calls; Python toolsets use XYZ not LUF. Verdict: **not relevant, covered** (AGENTS.md: UE over UEFN). No conflict.

### 7. UEFN livestream, "MCP in UEFN | Creating in Fortnite" (Fortnite Developers, uploaded 2026-08-22, 2:08:40), read fully
Epic developer relations (a Verse specialist) drives Claude Code against UEFN: a gun-game minigame built in about 45 minutes from an empty project, then a crafting system from a long written plan, plus Q&A. No dates or version numbers are said. Tips that also apply to UE MCP:
- **Connect with a project-root `.mcp.json`** (loads on every new session). If Claude cannot see the MCP, give the full URL path; `/mcp` shows status; restarting the editor fixed a dead connection. Pasting the doc snippet with its code-fence or filename line makes the JSON fail to parse. Our `GenerateClientConfig` avoids this.
- Server defaults to port 8000, path `/mcp`; rename the path if another app uses it (we moved the port to 8010 for the same reason). One server per project; several Claude sessions can share one server (but we keep one MCP caller, AGENTS.md).
- **Start at low or medium effort**, raise only if results are weak. Prototype with vague prompts; for real systems write a detailed plan file and tell the agent to implement it.
- The agent compiles, reads errors and fixes them unprompted; it reads the live output log, so add `print` lines for feedback (probably only the recent part of a big log).
- Do not click in the editor while the agent edits (the stream's own mistake). Frequent agent saves pop a "save content" dialog that blocks compiling, so tell it to save after larger batches. This is a hang risk for our unattended loop; worth a line in the runbook.
- The agent ignored parts of a skill file, so review its code. Ask for code-driven test scenarios (it built a runtime demo by itself).
- An editor crash happened live (about minute 65 to 85). No custom MCP tools in UEFN (Python editor scripting instead).

UEFN-only: Verse, devices, scene graph, live push-to-session, gameplay tags, the Beta Access toggle. Named limits (UEFN): no asset migration across projects, no control-rig tools, no mesh generation, unreliable comment boxes in materials.
Verdict: mostly **covered or UEFN-only**. New and small: the save-dialog stall, "print for feedback", the plan-file pattern. No conflicts. The earlier "assets from Fab can be built with, agent does not import them" is from the Q&A.

### 8. Article, "Bring NPCs to Life with AI-Powered Conversations" (fortnite.com, Apr 16, 2026): read in Chrome (hub, 2026-11-05)
Read fully by the hub. Facts from the page:
- UEFN and Creative only. "Conversations" (formerly the Persona device) is labelled Experimental.
- **Publishing islands that use it is not available until a Beta release.** Experimental projects show a watermark in UEFN.
- Runs on Google Gemini 3.1 Flash-Lite (audio in, text out) plus ElevenLabs voices, via Google Cloud. Epic says it does not store player audio. Latency is slower than the final target.
- Driven by Scene Graph and the Verse API: runtime prompt changes, and structured outputs (e.g. mission status) that trigger gameplay.
- **New Fortnite Developer Rule 1.22:** no medical or mental-health personas, no romantic or companion personas, no attempts to bypass safety systems. Bans are possible.

Verdict: **not usable for us.** It is UEFN only and cannot be published yet. A hosted AI service in a UE game would be a third-party service (Rule 8 / local-first). Do not plan on it. No conflict.
The earlier second-hand report that it left Experimental on July 30, 2026 is not confirmed: the page still labels it Experimental. Do not rely on that date.

### 9. Fab (front page)
Free and paid listings. A "Limited-Time Free" section ends **Nov 17, 9:59 AM ET** (after the jam). A filter URL (`is_ai_generated=0`) hints that Fab labels AI-generated listings. No licence or AI policy on the page itself. Verdict: **covered.** Our rule: sourced assets are allowed if licensed and listed, but are not scored (AGENTS.md; Rule 15(c)). Read each listing licence before use; the front page tells us nothing new.

### 10. Packaging Unreal Engine projects (UE 5.8, no date)
Stages: build, cook, stage, package, deploy, run. Cook "by the book" is slower and "recommended for final testing". Development vs Shipping: Shipping drops the console, so the game needs an in-game exit. Without a Game Default Map the packaged game shows a black screen. Output Log and Message Log hold packaging errors. Desktop platforms: Windows, macOS, Linux. The page **does not cover cross-compiling Windows from Linux** and **never mentions zip**; some linked pages are the 5.5 versions.
Verdict: **covered** (we build Windows on the Legion Go S; AGENTS.md and the packaging notes). Sub-pages read (2026-11-05 second pass):
- *Build Configurations Reference* (5.8): Shipping strips console, stats and profiling; Test keeps some. Debug files only if "Include Debug Files" is on.
- *Project Launcher* (5.8): By the Book cook needs the **Cooked Maps** chosen (maps left out may be missing, the page's own wording suggests); Package has "build for distribution to the public", a **prerequisites installer** option, I/O Store containers; "Save Packages Without Versions" is called dangerous; images on the page are from 5.1.
- *Sharing and Releasing Projects*: index only (Releasing, Cooking and Chunking, Project Launcher, Build Operations, Windows ARM64).
- *Content Cooking*, *Cooking and Chunking*, *Releasing Your Project*: **not read** (only a table-of-contents heading came back). Try them in a browser if wanted.

Compared with `scripts/package-and-push.ps1` and the runbook:
- Script runs `BuildCookRun -platform=Win64 -clientconfig=Development -cook -build -stage -pak -archive`, then zips with `tar` and checks 1 GB. Mock jam 7 proved it. It deliberately ships **Development**, not Shipping (win-plan line 158); Epic's pages say Shipping is the release config. Development keeps the console open to players and is larger; acceptable for a jam, but it is a decision to state (change 3).
- The script passes **no `-prereqs` flag and no `-map`**. The KB says the Prerequisites Installer should be on and the Rule 7(f) clean-machine test depends on it (KB lines 113, 206). Whether the project setting alone puts the installer in the staged output is not shown in the script or docs I read; confirm by looking in the staged folder, then add to the clean-machine test.
- The Project Launcher page backs this: maps must be explicit. The jam project is created inside the window, so set Game Default Map and list the maps in Packaging settings on day 1.
- Not in the runbook: Game Default Map, a quit path in the packaged game, the prerequisites check.

Two cheap checks worth adding to the packaging gate: Game Default Map set, and a quit path in Shipping (the black-screen and no-console traps). Neither check is in `stages/00_prep/references/jam-day-runbook.md`, `PLAN.md` or `stages/00_prep/references/win-plan.md` (keyword search for default map, black screen, quit, exit, 2026-11-05).

### 11. Epic Developer Community: read in Chrome (hub, 2026-11-05)
Hub portal (Unreal Engine tab by default) with tabs for Fortnite, Epic for Indies, Epic Online Services, Epic Games Store, RealityScan, MetaHuman, Twinmotion, Fab; a search page; and an Epic assistant at /community/assistant/unreal-engine. Body: latest forum threads by category (Getting Started, Programming & Scripting, Asset Creation, Character & Animation, World Creation); a news carousel that includes the MegaJam announcement thread (forums.unrealengine.com/t/.../2843983) and the UE 5.8 Preview thread (.../2721597); a Learning section (/community/unreal-engine/learning; first card: a UE 5.8 MetaHuman-from-custom-mesh with Motion Matching and Chooser tutorial).
The hub's text read returned only one card, so the layout came from the accessibility tree. No sign-in used. The Epic assistant was not tried (it may need sign-in).
Verdict: a portal with no jam rules, so nothing to change in `RULES.md`. Useful during the jam: forum search for errors, the UE 5.8 Preview thread for known issues, and the learning tab. The docs we need (links 4, 6, 10) were read directly.

### 12. Unreal Engine Forums, "Looking for teammates? Start here" (Oct 22, 2026; pages 1 and 2 read)
Page 2 (Nov 5 posts only): two more people looking for a team, a few "found a team yet?" replies. **No Epic staff reply and no rule clarification** (UE vs UEFN, Fab, AI, MCP) on either page, so the page-1 question about mixing UEFN and Unreal stays unanswered. Total pages not shown by the fetch tool.
Page 1 notes:
Teammate-matching thread with an intro format (handle, role, time zone and so on). One poster asks whether you may build in UEFN and use Unreal to prepare Fab assets; no answer on page 1. Public posts include Discord handles, against the thread's own advice. Mentions Codex, Claude Code and Cursor with Unreal MCP and Blender MCP, with no setup tips. Verdict: **not needed** (we are solo; AGENTS.md). Posting is outward-facing and was not done. The UE/UEFN question is a rules matter; our RULES.md already says pick one.

### 13. UEFN Discord channel: not opened
Discord channel link. Not opened by me or by the hub (login wall; no sign-in, and the owner was not asked to use an account). Nothing public recorded. UEFN-only channel, not our track.

## Tips check against our plan

| Tip (itch page) | Where we stand | Verdict |
|---|---|---|
| Set up agents before Nov 12; MCP on day one costs build time | Dress rehearsal 2026-11-04 passed; runbook has port 8010, startup order, `ss -ltnp` check; agent loop and revive service installed | **Covered.** Add the Editor Toolsets check and the Niagara size warning (changes 1 and 2). |
| Scope small, then polish | `_config/reference/research/scope_discipline_and_iterative_design.md`, PLAN day gates (juice on day 1) | **Covered.** |
| Package early; test build on day two | PLAN.md: Windows build #1 launches on **day 1**, build #2 on day 2 played by someone else | **Covered and ahead of the tip.** Add black-screen and quit-path checks (change 3). |
| Keep notes for the Glass Box dev log | `scripts/gen_devlog.py`, dev log template, devlog post at 3 PM day 4 (PLAN.md) | **Covered.** One gap: the dev log is drafted from commits and screenshots; consider a running notes file the loop appends to on each handoff. Optional. |
| Video: gameplay in the first five seconds | `stages/00_prep/references/win-plan.md` lines 28 and 164 | **Covered.** |
| Give it a shot anyway | Attitude, no action | n/a |
| Find teammates in the Forum/Discord | Solo by decision | **Covered, skip.** |

No conflict with our plan, rules or fixed facts. Itch page nearby facts (all match RULES.md and AGENTS.md): kickoff Nov 11 11 AM PT, contest Nov 12 00:00 ET to Nov 15 8:59 PM ET, winners by Jan 29 2027, AI-tool credit details still "coming soon" (we reconsider credits when published).

## Ranked changes to make before Nov 12

1. **Pin down the plugin list.** Check which plugins the rehearsal project actually enables (Unreal MCP, All Toolsets, Editor Toolsets?). Record the exact list in the runbook and in the project's `.uproject`. A missing Editor Toolsets plugin gives "connected but cannot do anything", the worst day-one failure.
2. **Guard the context budget.** Add to `stages/00_prep/references/jam-day-runbook.md` and the lead agent prompt: do not call `describe_toolset` on large toolsets (Niagara about 250k tokens, materials 2k to 26k) unless needed; describe only the toolset in use; if a simple material takes more than about a minute, suspect truncated tool descriptions. Confirm the lead agent's context window can hold what it asks for.
3. **Packaging gate additions.** In the build #1 checklist: Game Default Map set; quit path works in Shipping; run from the staging folder on the Legion. Note that Epic's packaging page gives no Linux-to-Windows route and no zip step (we zip ourselves, Rule 7).
4. **Prompt habits into the agent prompt library:** exact names, one task per prompt, ask intent first, read the plan, name the target Blueprint class. Also: for logic-heavy work prefer C++ or Python over big Blueprint graphs (the trainers' advice; fits mock-jam finding 2). This softens CLAUDE.md's "default to Blueprint" slightly; owner's call.
4b. **Packaging script and gate (from the sub-page pass):** confirm the prerequisites installer lands in the staged output (script passes no `-prereqs`), record the Development-vs-Shipping decision, set Game Default Map and Cooked Maps on day 1.
4c. **Editor save-dialog stall** (UEFN stream): tell the unattended agent to save after batches; a "save content" dialog blocks compiling and can look like a hang. Also add `print` lines for the agent's output-log feedback.
5. **Add `LogModelContextProtocol` verbose logging** to the crash and recovery map (Output Log category and `Log LogModelContextProtocol Verbose`).
6. **Optional:** a running notes file for Glass Box that the loop appends to at each handoff.
7. **Done (2026-11-05):** links 1, 2, 8 and 11 were read in Chrome by the hub (see above). Nothing to re-read. Link 13 stays unopened.

Link 8 facts (publishing needs a Beta release; Fortnite Developer Rule 1.22) are not top changes. They apply to UEFN personas, which we do not build. No action beyond the note above.

## Proposed edits (not made; this ticket edits only this file)

- `stages/00_prep/references/jam-day-runbook.md`: add the plugin list (change 1), the `describe_toolset` warning (2), the packaging checks (3), the log category (5).
- `_config/reference/knowledge-base.md` near line 257: add the Editor Toolsets note and the Niagara and materials token sizes (attributed to the Epic webinar, link 5), and the packaging-page gaps (no cross-compile, no zip).
- `CLAUDE.md`: optional sentence on the C++/Python preference for logic-heavy work (change 4).
- `_config/reference/research/ai_agents_mcp_and_asset_pipelines.md`: add the webinar and the UEFN docs as sources with dates (video 2026-10-08; webinar upload 2026-09-07; UEFN stream 2026-08-22).
