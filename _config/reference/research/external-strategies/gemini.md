# MegaJam strategy — Gemini 2.5 Pro, October 27, 2026

## 1. Verdict on my plan: what to keep, change and cut, and the single biggest mistake in it

### Can this actually be built in 93 hours?
**Hard Reality Check:** **No**, not with your current architecture and hardware setup. While your production principles (feature slices, daily gates, sleep schedule, avoiding humanoid rigs) are top-tier, your **technical stack and execution pipeline will collapse under its own weight within 24 hours.** 

### What to Keep
*   **Non-humanoid / stylized hero:** Mandatory when relying on automated mesh generation.
*   **Daily milestones and 2-hour feature slices:** Standard agile jam practice that prevents feature creep.
*   **Aiming for 4s across the board before pushing 5s:** High baseline consistency wins jams over uneven games with one brilliant mechanic and broken UI.
*   **6 hours of sleep a night:** Exhaustion breeds critical technical mistakes on Linux/CachyOS setup scripts.

### What to Change
*   **The Concept Selection Window:** The theme drops at 11 AM PT Nov 11, but the jam clock starts at 9 PM PT Nov 11. You currently plan to pick your concept by 3 PM PT on paper. **Change this:** Do all paper design between 11 AM and 3 PM PT *before* the jam clock even starts! Use those 10 hours before 9 PM to write agent prompts, build paper maps, and refine specs. When 9 PM hits, you should be typing code, not brainstorming.
*   **Asset Generation Strategy:** Do not use local batch generation on your single GPU for primary assets during active editor work. Shutting down UE5, clearing VRAM, generating, retopologizing, and re-opening UE5 takes 45–60 minutes per batch. You will lose 15+ production hours just context-switching.

### What to Cut
*   **The Automated "Remesh-and-Bake" Step:** Automated remeshing/baking tools fail on 30%–40% of generated raw meshes (non-manifold edges, inverted face normals, overlapping UVs). Debugging asset import failures in UE5 will consume 12+ hours. **Cut retopology entirely.** Use generated 3D meshes as high-poly models with Auto-Generate LODs in UE5, or rely on World-Aligned / Triplanar Master Materials that ignore UV topology completely.
*   **Linux Editor to Windows Packaging Hand-off:** Unreal Engine cannot cross-compile Windows builds natively from Linux without a custom cross-toolchain build of the engine. Moving a `.uproject` directory across network/USB to a Legion Go S (powered by a handheld APU) to run `RunUAT.sh BuildCookRun` will result in 2–4 hour compile/cook times and endless shader cache mismatches. **Cut Linux from the production pipeline.** Run Windows 11 natively on your main desktop rig for the duration of the jam, or use the Legion Go S purely as a build client receiving pre-cooked assets.

### The Single Biggest Mistake
**Relying on Claude Code via Unreal MCP as your primary driver while having "little hands-on UE5 editor time."**
Epic's Unreal MCP (Model Context Protocol) plugin is experimental, sequential, and prone to silent failures when Python/C++ API endpoints mismatch across engine sub-versions (especially unreleased/bleeding-edge UE 5.8). When the MCP agent generates corrupt Blueprint node connections, breaks material instance bindings, or fails to serialize a level asset, your lack of hands-on UE5 editor experience means you will spend 3 hours manually un-breaking the project for every 1 hour of automated progress. **The MCP agent must be demoted from "Driver" to "Background Assistant."**

---

## 2. Your winning strategy in one paragraph
Your path to a top-3 spot and the Glass Box modifier relies on **Systemic Arcade Simplicity powered by Custom Materials rather than Heavy Assets.** Instead of burning GPU hours generating custom 3D props and fighting mesh topology, build a polished top-down or 2.5D physical interaction game (e.g., marble/fluid dynamics, modular tile building, or destruction-sweeper mechanics) using UE5 primitive geometry enhanced with a single, highly reactive Master Toon Shader. Write all core game logic in native C++ using Claude Code file agents, compile directly in a native Windows environment, and run automated packaging builds every 12 hours. By offloading 80% of visual flair to Niagara particle systems and dynamic MetaSound audio, you deliver a buttery-smooth 60 FPS build under 500 MB on handheld devices like the Legion Go S, letting your Glass Box dev log shine as a masterclass in AI-human hybrid software engineering.

---

## 3. Concept strategy: how to pick, plus 5 game archetypes

### How to Pick
1. **11:00 AM PT (Theme Drop) – 1:00 PM PT:** Generate 10 literal and metaphorical readings.
2. **1:00 PM PT – 2:00 PM PT:** Eliminate any idea requiring:
   * Complex character animations or facial expressions.
   * Fine-tuned melee hitboxes or ladder/climbing physics.
   * Narrative dialogue UI or branching quest systems.
   * Highly specific environmental art assets that can't be made with procedural shaders or primitive shapes.
3. **2:00 PM PT – 3:00 PM PT:** Score the remaining candidates on a matrix:
   $$\text{Score} = (\text{Fun} \times 2) + \text{Visual Cohesion} + \text{Low-Spec Feasibility} + \text{Theme Fit}$$

### 5 High-Scoring, Adaptable Game Archetypes

```
+-------------------------------------------------------------------------------+
|                        5 HIGH-SCORING JAM ARCHETYPES                          |
+-------------------------------------------------------------------------------+
|  1. KINETIC PHYSICS PUZZLER / MARBLE SURVIVAL                                 |
|     - Zero rigged meshes; pure physics, Niagara particles, and MetaSounds.    |
+-------------------------------------------------------------------------------+
|  2. TOP-DOWN TWIN-STICK TACTICAL DEFENSE                                      |
|     - Top-down camera hides mesh flaws; grid snapping simplifies level design.|
+-------------------------------------------------------------------------------+
|  3. ISOMETRIC FACTORY / CONVEYOR SYSTEMIC GAME                                |
|     - High "Ambition" score through emergent gameplay logic; static props.    |
+-------------------------------------------------------------------------------+
|  4. VEHICULAR CLEANUP / CHAOS DESTRUCTION SWEEPER                             |
|     - Uses built-in UE5 Chaos Physics; high visual satisfaction & feedback.   |
+-------------------------------------------------------------------------------+
|  5. 2.5D CONTROL ROOM / TACTICAL ARENA COMMANDER                              |
|     - Fixed camera, heavy UI/Juice, minimal spatial asset requirements.       |
+-------------------------------------------------------------------------------+
```

1. **Kinetic Physics Puzzler / Marble Survival:**
   * *Why it works:* Zero character animation required. Sphere/cylinder collisions are mathematically perfect. High score potential in *Fun Factor* and *Audio* using dynamic pitch shifting on roll speed and impact force.
2. **Top-Down Twin-Stick Tactical Defense:**
   * *Why it works:* Top-down orthogonal cameras mask missing surface detail and lighting imperfections. Enemies can be abstract robotic/crystalline constructs created easily with low-poly shapes.
3. **Isometric Factory / Modular Conveyor Logic:**
   * *Why it works:* Highly systemic. Judges award massive points in *Ambition & Innovation* when systems interact dynamically. Uses simple static props aligned to an array grid.
4. **Vehicular Destruction Sweeper (Chaos Physics):**
   * *Why it works:* Utilizing UE5 Chaos Destruction on pre-fractured static primitives yields immediate visual fidelity and high *Gameplay* satisfaction without complex animation pipelines.
5. **2.5D Control Room / Tactical Arena Commander:**
   * *Why it works:* Confining the player to a static room or interface with a 3D tactical viewport eliminates open-world performance bottlenecks while allowing heavy emphasis on UI polish, sound effects, and clear win/loss conditions.

---

## 4. Criterion by criterion scoring guide

| Criterion | Score 3 (Average) | Score 4 (Strong Entry) | Score 5 (Winner Tier) | How to Get to a 5 |
| :--- | :--- | :--- | :--- | :--- |
| **Ambition & Innovation** | Generic clone of a tutorial mechanic. | Blends two distinct mechanics smoothly with a clean game loop. | Introduces an unexpected, highly emergent mechanic that changes the game state dynamically. | Implement real-time physical level alteration (e.g., gravity flip, terrain fracture, or dynamic fluid flow). |
| **Use of Theme** | Theme is purely cosmetic or named in the title. | Theme is required to understand the core objective. | Theme dictates every fail-state, UI element, and mechanical loop. | Tie the theme directly to the player's core resource management or victory trigger. |
| **Fun Factor** | Mechanically sound, but feels stiff or slow. | Good controller response, clear feedback, fun for 5 minutes. | Addictive game feel ("juice"), screenshake, hit stop, instant restart loops. | Add frame-freeze on impact ($0.05\text{s}$ time dilation), camera kickback, dynamic pitch variation on sound FX. |
| **Gameplay** | Has controls, a start screen, and a game over state. | Well-balanced difficulty progression across 3 distinct levels. | Intuitive onboarding, zero tutorial text needed, multi-path tactical depth. | Implement seamless UI overlay tutorial cues integrated directly into the 3D environment. |
| **Visuals** | Default materials, unlit assets, inconsistent art style. | Cohesive color palette, stylized toon shading, readable UI. | Striking art direction, custom post-processing, active Niagara FX, crisp resolution. | Use a unified Post-Process Toon/Outline Shader combined with dynamic visual palette shifts per level. |
| **Level Design** | Flat arena or repetitive grid blocks. | 3–5 distinct levels with clear signposting and hazard escalation. | Environmental storytelling, verticality, dynamic level hazards. | Use snap-to-grid modular pieces with variable layout configurations per run. |
| **Audio** | Silent or single royalty-free background track with sudden cuts. | Dynamic background music with distinct audio triggers for key actions. | Generative MetaSound graphs, spatialized 3D audio, dynamic ducking. | Route velocity, speed, and health ratios directly into MetaSound audio parameter controllers. |

---

## 5. Where AI agents help most and where they'll hurt me

```
                   +------------------------------------+
                   |        AI AGENT ASSIGNMENTS        |
                   +------------------------------------+
                                     |
           +-------------------------+-------------------------+
           |                                                   |
           v                                                   v
  [ WHERE AGENTS EXCEL ]                             [ WHERE AGENTS HURT ]
  • C++ Mechanics & State Machines                    • Live Editor Blueprint Editing (MCP)
  • Master Shaders / HLSL Code Snippets               • Complex Mesh Rigging & Weight Painting
  • MetaSound Graph Setup via Python                  • Unsupervised Multithreaded Refactoring
  • Automated Packaging & Build Scripts               • Level Layout Asset Placement
```

### Where AI Agents Excel
* **Boilerplate C++ Development:** Claude Code writing clean, uncompiled C++ classes (`.h` / `.cpp`) on disk for GameModes, Player Pawns, Data Tables, and UI Controllers.
* **HLSL / Material Expression Generation:** Generating custom shader functions (e.g., world-aligned triplanar mapping, distance-field glow, pixelation filters).
* **Python Automation in Editor:** Batch-renaming assets, setting up collision channels, and generating Data Assets from JSON files.
* **MetaSound Logic Generation:** Drafting procedural audio node structures and parameter bindings via Python scripts.

### Where AI Agents Will Hurt You (Technical Traps)
* **Unreal MCP Live Blueprint Manipulation:** The MCP plugin frequently hallucinates API syntax when connecting complex execution pins in Blueprints, leading to silent serialization corruption.
* **Mesh Rigging & Retopology:** Automated AI agents attempting to fix bad geometry or generate character skeletons produce vertex tearing along joints.
* **Unsupervised Deep Code Refactoring:** Letting an agent rewrite core C++ headers mid-jam forces complete engine re-indexing and compile cascades that destroy 30+ minutes of dev time.

---

## 6. Schedule: The 93-Hour Engine-First Timeline

```
  NOV 11 (WED)        NOV 12 (THU)        NOV 13 (FRI)        NOV 14 (SAT)        NOV 15 (SUN)
  9:00 PM PT          9:00 PM PT          9:00 PM PT          9:00 PM PT          5:59 PM PT
  +-------------------+-------------------+-------------------+-------------------+-------------------+
  | GATE 0: GREYBOX   | GATE 1: WIN BUILD | GATE 2: PLAYTEST  | GATE 3: FREEZE    | GATE 4: SUBMIT    |
  | Native Win setup  | First packaged    | 3 levels playable | Post-process &    | Video render,     |
  | C++ core loop     | .zip verified on  | end-to-end by     | MetaSounds locked;| itch.io page live |
  | playable in editor| Legion Go S       | external tester   | zero code changes | buffer remaining  |
  +-------------------+-------------------+-------------------+-------------------+-------------------+
```

### Day 0: Setup & Core Mechanics (Wed Nov 11, 9:00 PM – Thu Nov 12, 3:00 AM)
* **Target:** Core C++ physics/pawn movement playable in editor on greybox geometry.
* **9:00 PM – 11:00 PM:** Initialize pre-built C++ template on native Windows environment. Verify compiler toolchain.
* **11:00 PM – 3:00 AM:** Write core Player Pawn, GameMode state machine, and primary input context.
* **GATE 0 (3:00 AM Nov 12):** Pawn movement, basic win/loss triggers, and camera controls functioning in editor.

### Day 1: Full Loop & Packaging Pipeline (Thu Nov 12, 9:00 AM – Fri Nov 13, 2:00 AM)
* **Target:** First fully packaged Windows ZIP running natively on Legion Go S.
* **9:00 AM – 2:00 PM:** Implement UI overlays (UMG), HUD bindings, game reset triggers, and scoring controllers.
* **2:00 PM – 7:00 PM:** Construct greybox Level 1, Level 2, Level 3 with objective triggers and obstacles.
* **7:00 PM – 10:00 PM:** **First Packaged Build Attempt.** Run `RunUAT.sh` Shipping Cook.
* **10:00 PM – 2:00 AM:** Resolve missing DLLs, shader cook errors, and input mapping issues on Legion Go S.
* **GATE 1 (2:00 AM Nov 13):** Executable ZIP (< 500 MB) extracted and played on Legion Go S at 60 FPS.

### Day 2: Systems, Audio, & External Playtest (Fri Nov 13, 9:00 AM – Sat Nov 14, 2:00 AM)
* **Target:** Complete playable playthrough tested by an independent third party.
* **9:00 AM – 3:00 PM:** Asset population pass using Master Toon Material, Niagara particle impacts, and environmental props.
* **3:00 PM – 8:00 PM:** Integration of MetaSound dynamic audio, pitch-shifting physics sounds, and background loops.
* **8:00 PM – 11:00 PM:** **External Playtest.** Hand handheld device to a third party. Observe without providing instructions.
* **11:00 PM – 2:00 AM:** Fix usability bottlenecks, re-balance physics variables, adjust camera stiffness.
* **GATE 2 (2:00 AM Nov 14):** External user successfully completes all levels without encountering soft-locks or game crashes.

### Day 3: Juice, Visual Polish, & Feature Freeze (Sat Nov 14, 9:00 AM – Sun Nov 15, 2:00 AM)
* **Target:** Final Release Candidate packaged and feature-locked.
* **9:00 AM – 3:00 PM:** Visual juice pass: post-process toon outlines, screen shake, hit-stop effects, and UI animations.
* **3:00 PM – 7:00 PM:** Media capture: record high-bitrate 1080p60 raw footage, assemble itch.io screenshots, draft dev log posts.
* **7:00 PM – 10:00 PM:** Balance tuning pass and high-score saving implementation.
* **10:00 PM (HARD FEATURE FREEZE):** **Zero code, asset, or level modifications permitted beyond this timestamp.**
* **10:00 PM – 2:00 AM:** Package final Shipping Release Candidate build. Verify archive integrity.
* **GATE 3 (2:00 AM Nov 15):** Final Release Candidate `.zip` stored on backup media, tested on clean target hardware.

### Day 4: Submission, Media, & Buffer (Sun Nov 15, 9:00 AM – 5:59 PM)
* **Target:** Successful submission on itch.io with 90+ minutes remaining.
* **9:00 AM – 12:00 PM:** Cut and edit 45-second gameplay trailer at 1080p60.
* **12:00 PM – 2:00 PM:** Build itch.io page layout, embed gameplay trailer, insert controls diagram, publish AI disclosure table.
* **2:00 PM – 3:30 PM:** Upload packaged ZIP archive to itch.io. Download back onto secondary machine and verify execution.
* **3:30 PM – 4:30 PM:** Submit entry to 2026 Epic AI MegaJam track on itch.io.
* **GATE 4 (4:30 PM Nov 15):** Submission confirmed live on itch.io (90-minute safety buffer before 5:59 PM deadline).

---

## 7. Modifier strategy: Glass Box vs. alternatives

```
+-------------------------------------------------------------------------------+
|                        MODIFIER PRIORITY MATRIX                               |
+-------------------------------------------------------------------------------+
|  PRIMARY TARGET: GLASS BOX ($2,500)                                           |
|  - High probability when pairing AI agents with structured technical logging. |
|                                                                               |
|  AUTOMATIC SECONDARY: SOLO DRIVER ($2,500)                                    |
|  - Inherited automatically by operating solo without human teammates.         |
|                                                                               |
|  AVOID: POCKET POWERHOUSE / RENDER ROYALTY                                     |
|  - Chasing ultra-high graphics or mobile limits risks core game stability.   |
+-------------------------------------------------------------------------------+
```

### Winning Glass Box Dev Log Architecture
The Glass Box modifier rewards transparency, tool usage clarity, and production insight. Structure your dev log as 3 distinct itch.io posts across the jam:

1. **Log 1: The Prompt-to-Architecture Pipeline (Day 1)**
   * Show exact prompt chains used with Claude Code to generate C++ GameModes.
   * Highlight human intervention points where AI output was rejected or corrected.
2. **Log 2: Resolving Technical Failure States (Day 2)**
   * Detail a real technical failure (e.g., an asset import error or broken physics serialization) and document how AI agents assisted in diagnosing the root cause.
3. **Log 3: The Asset & Audio Pipeline Flowchart (Day 3)**
   * Publish a full visual flowchart demonstrating how local generation tools (Qwen, ACE-Step) interfaced with native UE5 MetaSounds and Master Materials.

---

## 8. Presentation: Video, itch.io page, and first 60 seconds

### The 45-Second Video Structure
```
[0:00 - 0:05] Hook: High-impact gameplay explosion/interaction (No logos).
[0:05 - 0:20] Mechanics: Show core controls and objective in motion.
[0:20 - 0:35] Escalation: Display level hazards, dynamic mechanics, and progression.
[0:35 - 0:45] Outro: Game Title, "Epic AI MegaJam 2026", and Key Controls layout.
```

### The Itch.io Page Layout
* **Header:** Animated GIF showing high-energy gameplay action.
* **Hero Image:** High-contrast 1080p screenshot featuring the Master Toon Shader styling.
* **Controls Chart:** Visual key map supporting both Gamepad (Legion Go S layout) and KBM.
* **AI Tool Disclosure Table:** Fully compliant disclosure listing models, inputs, and usage context.

### The First 60 Seconds of Gameplay (Judge Experience)
* **0:00 – 0:05:** Fast boot directly to Main Menu. High-contrast UI, instant load times.
* **0:05 – 0:15:** Level 1 loads. Controls displayed in world-space floating text.
* **0:15 – 0:45:** Intuitive micro-puzzle or obstacle completed in under 30 seconds.
* **0:45 – 0:60:** Victory particle burst, dynamic sound payoff, and instant progression to Level 2.

---

## 9. Ranked Pre-Jam Prep Plan (Next 2 Weeks)

1. **Unified Windows Engine Environment Setup:** Install UE 5.8 on native Windows 11 desktop with MSVC C++ toolchains configured. Verify executable packaging times under 10 minutes.
2. **Pre-Built C++ Template Repository:** Construct a barebones C++ repository containing base classes for `GameMode`, `PlayerPawn`, `SaveGameSubsystem`, and `UIHUD`.
3. **Master Toon / World-Aligned Shader Library:** Author a reusable HLSL/Material Function library featuring triplanar UV mapping and custom post-process depth outlines.
4. **Claude Code C++ Integration Test:** Test Claude Code generating clean C++ source files directly into a target project directory and compiling via UnrealBuildTool.
5. **MetaSound Parameter Template:** Create a pre-configured MetaSound graph accepting external floats for pitch modulation, velocity impact, and state shifts.
6. **24-Hour Dry Run (Mock Jam):** Execute a continuous 24-hour mock jam on a random past theme to identify pipeline friction before Nov 11.

---

## 10. Top 10 risks with mitigations

1. **Linux-to-Windows Packaging Failures:**
   * *Mitigation:* Develop exclusively on a native Windows 11 host during the jam.
2. **Shader Compilation Stalls on Handheld Target:**
   * *Mitigation:* Disable dynamic Lumen and Virtual Shadow Maps; use stationery lighting and Forward Shading presets.
3. **Unreal MCP Plugin Desynchronization / Crashes:**
   * *Mitigation:* Restrict AI agents to writing raw C++ source files on disk rather than driving live editor operations.
4. **Build Package Exceeds 1 GB Limit:**
   * *Mitigation:* Enable `bCompressPakFiles=True`, strip unused editor content, and compress audio files to OGG Vorbis formats.
5. **AI 3D Asset Topology / Normal Vector Failures:**
   * *Mitigation:* Use World-Aligned Master Materials that render surface textures independent of mesh UV topology.
6. **GPU VRAM Allocation Exhaustion:**
   * *Mitigation:* Never execute local AI generation scripts while the UE5 Editor is active in memory.
7. **Scope Creep Stalling Full Playable Loop:**
   * *Mitigation:* Enforce a strict **Hard Feature Freeze at 10:00 PM PT on Saturday, Nov 14.**
8. **Handheld Performance Drops Below 60 FPS:**
   * *Mitigation:* Cap maximum texture resolution overrides to 2048x2048 in `DefaultEngine.ini`.
9. **Audio Clipping and Concurrency Crashes:**
   * *Mitigation:* Enforce a hard voice limit of 16 concurrent channels inside the UE5 Audio Engine settings.
10. **Git Repository LFS Corruption:**
    * *Mitigation:* Generate local `.zip` compressed source backups at every major gate milestone alongside regular Git commits.

---

## 11. One thing you'd do that most entrants won't
**Build a Low-Spec First Performance Profile directly inside `DefaultEngine.ini` before typing a single line of code.**

Most jam participants build on high-end desktop hardware with default engine settings, resulting in unoptimized builds that suffer from heavy shader compile hitches, dynamic Lumen overhead, and frame drops on judge hardware. By configuring low-overhead defaults (Forward Shading, pre-compiled PSO caches, dynamic resolution scaling, and disabled motion blur) on Day 0, your game will run at a rock-solid 60 FPS on handheld devices like the Legion Go S, delivering an instantly superior player experience.

---

## 12. What I'm least sure about, and what I should verify

1. **UE 5.8 Engine API Stability:**
   * *Uncertainty:* UE 5.8 is bleeding-edge software. Internal Python/C++ API endpoints may differ from UE 5.4/5.5 documentation, potentially breaking automated MCP tool calls.
   * *Verification:* Run script tests in a UE 5.8 scratch project prior to Nov 11 to confirm API stability.
2. **Unreal MCP Plugin Multi-Agent Concurrency:**
   * *Uncertainty:* The experimental MCP plugin may lock local socket communication when handling rapid tool calls from background agents.
   * *Verification:* Test sending continuous sequential requests via Claude Code to verify socket stability.
3. **Official 2026 Epic AI MegaJam Rules & Licensing:**
   * *Uncertainty:* Specific rule additions regarding local vs. cloud AI execution models or mandatory submission forms may update at kickoff.
   * *Verification:* Check the official jam page on itch.io during the Nov 11 kickoff stream.

---

## 13. Technical Go / No-Go Checklist for Nov 10 (24 Hours Pre-Jam)

Execute this technical verification on Nov 10. If any item fails, trigger the specified contingency plan immediately.

```
+---------------------------------------------------------------------------------------------------------+
|                                TECHNICAL GO / NO-GO CHECKLIST (NOV 10)                                  |
+----+----------------------------------------------+--------+--------------------------------------------+
| #  | CHECK ITEM                                   | STATUS | CONTINGENCY PLAN ON FAIL                   |
+----+----------------------------------------------+--------+--------------------------------------------+
| 1  | Packaging Test (Blank C++ -> Windows)        | [ ]    | Switch to native Windows host immediately   |
| 2  | Zip Size Validation (< 300 MB baseline)       | [ ]    | Enable bSkipEditorContent in config settings|
| 3  | Handheld Target Test (Legion Go S 60 FPS)     | [ ]    | Disable Lumen, enable Forward Shading      |
| 4  | Claude Code C++ Compilation Pipeline         | [ ]    | Re-install MSVC v143 build tools           |
| 5  | Local AI VRAM Memory Clearance Test          | [ ]    | Enforce explicit torch.cuda.empty_cache()   |
| 6  | Gamepad Enhanced Input Auto-Mapping          | [ ]    | Load default UE5 Gamepad mapping context   |
| 7  | OBS 1080p60 Video Capture Stability          | [ ]    | Set OBS encoder to AMD VCE / Hardware NVENC |
+----+----------------------------------------------+--------+--------------------------------------------+
```

* **[ ] Check 1: Native Windows Packaging Test**
  * *Pass Condition:* A blank C++ project packages to a Windows ZIP archive in under 10 minutes without errors.
  * *Contingency on Fail:* Reinstall DirectX dependencies and MSVC C++ build tools on host system.

* **[ ] Check 2: ZIP Baseline Archive Size**
  * *Pass Condition:* Uncompressed baseline package output size is under 300 MB.
  * *Contingency on Fail:* Set `bSkipEditorContent=True` and configure asset compression settings in `DefaultEngine.ini`.

* **[ ] Check 3: Handheld Target Performance Baseline**
  * *Pass Condition:* Executable runs at locked 60 FPS on Lenovo Legion Go S at 15W TDP.
  * *Contingency on Fail:* Set `r.DynamicRes.OperationMode=1` and enforce dynamic resolution scaling.

* **[ ] Check 4: Claude Code C++ File Generation & Compilation**
  * *Pass Condition:* Claude Code writes a custom C++ Actor class to disk that compiles cleanly via UnrealBuildTool.
  * *Contingency on Fail:* Fall back to manual C++ class generation using standard Visual Studio templates.

* **[ ] Check 5: GPU VRAM Garbage Collection**
  * *Pass Condition:* Executing local generation scripts and launching UE5 Editor sequentially does not produce Out-Of-Memory (OOM) errors.
  * *Contingency on Fail:* Write a batch shell script that forcibly terminates PyTorch background processes before launching the editor.

* **[ ] Check 6: Gamepad Auto-Detection**
  * *Pass Condition:* Legion Go S built-in controls automatically drive character movement in editor play mode.
  * *Contingency on Fail:* Import UE5 Enhanced Input default mapping context presets for standard gamepads.

* **[ ] Check 7: OBS High-Bitrate Gameplay Recording**
  * *Pass Condition:* 60 seconds of 1080p60 gameplay footage records cleanly without inducing game frame stutter.
  * *Contingency on Fail:* Reduce OBS recording bitrate to 12 Mbps and switch encoding thread priority to low.