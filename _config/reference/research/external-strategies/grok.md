# MegaJam strategy — Grok 4 (xAI), October 27, 2026

**Role note:** This is an independent, deliberately contrarian take. I argue against parts of your plan where the case is real, not for the sake of disagreement. Sources are linked inline. Where I am guessing (especially on 2026 judge psychology and what will feel overdone), I say so.

---

## 1. Verdict on my plan: what to keep, change and cut, and the single biggest mistake in it

**Keep**
- Solo + heavy AI agents setup. Solo Driver is a clean $2,500 modifier and your profile (strong software/AI, weak UE5 editor time) fits it.
- Pre-jam tooling only (packaging scripts, asset pipeline, prompt library, QA harness, OBS, dev-log tooling, mock jam). Rules explicitly allow this; building gameplay early is the disqualifier. See [itch.io jam page](https://itch.io/jam/2026-epic-ai-megajam) and Unreal’s correction post that AI is optional and pre-work is limited to tools/agents/MCP.
- Avoid multiplayer, open worlds, dialogue trees, and complex humanoid animation. Correct. AI rigs remain weak; humanoids eat time and look mid. Creature/vehicle/object/abstract heroes + stylized + top-down/third-person is the right bias for a solo 93-hour run.
- Feature slices ≤2 hours with done-tests and your own playtest. Cut list on day 1. 6 hours sleep. These are survival rules.
- Target Glass Box as primary modifier and Solo Driver as fallback. Glass Box is explicitly “best dev log showing how you built your game.” Your agent-heavy workflow is almost designed for it.

**Change**
- Ambition from “breadth (bigger hand-built level, more enemy types)” is the wrong lever. In a 4-day jam with limited UE5 editor fluency, breadth produces shallow systems and greybox-looking levels. Judges reward *coherent* ambition (one strong new mechanic or one bold constrained art direction) more than checklist breadth. Past winners (2025: These Four Walls, Phantom’s Manor) show polish and identity over sprawl.
- “Get every criterion to a 4, then push two to a 5” is too even. Fun Factor is the tie-breaker (double weight on ties). You should bias harder toward Fun + Gameplay + Theme early and treat Visuals/Audio/Level Design as “good enough + juice” rather than equal.
- Concept selection by 3 PM PT Nov 11 is fine, but the 10-readings → 3-filter → score-on-7-criteria process is over-engineered for a theme you will hear at 11 AM PT. You will lose the afternoon to analysis paralysis. Cut to 45–60 minutes of forced generation + ruthless feasibility filter.
- Daily gates are mostly good but night-0 “playable greybox” is optimistic given your UE5 editor experience and Linux → Windows packaging hop. Move first Windows build earlier and treat greybox as “character moves + one interactable + camera feels good.”

**Cut**
- Explicit goal of “top 3 Best Overall + Glass Box.” Best Overall is a bloodbath of teams who ship more content. Solo Driver + Glass Box is the higher-expected-value path for your skills. Treat Best Overall as upside, not the primary target.
- The idea that AI-generated assets “count as my own original work” and therefore give scoring advantage. Official stance: AI use is context only and does not move scores up or down. [itch.io rules](https://itch.io/jam/2026-epic-ai-megajam). Relying on volume of AI assets is a trap; judges still see generic AI look.

**Single biggest mistake**
Treating the jam as a coverage problem (“hit 4s across the board, then push two 5s”) instead of a *signature* problem. In 2026, with AI flooding the field, the entries that stand out will have one unmistakable creative or mechanical identity that survives the AI sameness. Your plan optimizes for competence, not memorability. That is the classic way competent solo entries finish mid-pack.

---

## 2. Your winning strategy in one paragraph

**Safe strategy:** Ship a tight, 8–12 minute single-player experience with one clear core loop, strong theme integration, polished first 60 seconds, consistent stylized look, and functional audio. Greybox core loop by end of day 1, full vertical slice + first Windows package by end of day 2, art/audio/juice + feature freeze by 10 PM day 3, submit with 90+ minutes buffer. Aim for solid 4s everywhere and a 5 on Fun + Theme. Claim Solo Driver and make Glass Box a high-effort secondary. High chance of a respectable placement and a real shot at Solo Driver / Glass Box.

**High-risk / high-reward strategy:** Bet everything on one novel, theme-tied mechanic that AI cannot easily replicate (procedural rule-breaking, player-authored systems, physics toys that feel hand-tuned, or a camera/control scheme that is immediately legible and delightful). Keep the rest of the game deliberately small and supporting. Accept that Visuals or Level Design may land at 3 if the mechanic and fun are exceptional. Document the design and agent process obsessively for Glass Box. This is how you actually threaten Best Overall as a solo; it is also how you get a 2 on Fun if the mechanic does not click by day 2.

**What I would pick and why:** The high-risk version, but with a hard kill switch at end of day 1. If the core mechanic is not fun in greybox after one focused day, fall back to the safe plan immediately. Your strengths (software + agents + local asset pipeline) give you a real edge on a novel system; your weakness (UE5 editor hours) makes breadth and polish expensive. Most entrants will play it safe with AI-assisted content volume. A sharp, playable idea that feels *designed* rather than *generated* is the differentiator in 2026.

**How an AI-heavy solo entry looks to judges in 2026, and how to stand out when many entries will be AI-made:** AI use is disclosed as context only and does not raise or lower scores. Judges will see a lot of competent, slightly samey stylized 3D with AI meshes, AI music, and agent-written Blueprints. An AI-heavy solo will look impressive on process (especially for Glass Box) but average on product unless you deliberately fight the AI aesthetic. Stand out by: (1) strong, constrained art direction that AI is used *in service of*, not the default look; (2) one mechanic that feels human-tuned; (3) ruthless cutting so the game feels finished rather than “AI-generated volume”; (4) a first 30 seconds that communicates identity immediately; (5) a dev log that shows judgment and taste, not just agent throughput. Guess based on 2025 winners and the explicit “AI is context only” language.

---

## 3. Concept strategy: how to pick, plus 5 game archetypes that adapt to most themes and score well, each with why

**How to pick (force the process)**
Theme drops ~11 AM PT Nov 11. From 11:15–12:00 force 8–10 raw ideas on paper or voice notes (no filtering). 12:00–12:30 kill anything that needs multiplayer, complex animation, open world, or heavy dialogue. 12:30–1:30 take the top 3 and score only on: (1) can I greybox the core loop in <8 hours, (2) does the theme feel essential rather than bolted on, (3) is there one clear “this is the game” moment in the first 60 seconds. Pick one by 2 PM. Write a half-page design doc max: core loop, win/lose, 3–4 moments that must feel good, camera, art constraints. Stop. Start tooling verification and sleep. Over-analysis on day 0 is a silent killer.

**5 adaptable archetypes**
1. **Constrained physics toy / object controller** — Player is a single object or simple creature with unusual movement or interaction rules. Theme becomes the environment’s rules or the object’s purpose. Why it scores: high Fun and Gameplay potential from feel; Level Design can be short and dense; Visuals can be bold and limited; easy to make theme-central. Avoids animation hell.
2. **Single-screen or short linear “room” game with escalating rules** — One or a few spaces that change rules, gravity, time, or player abilities based on theme. Why: Ambition comes from systemic cleverness instead of content volume; easy to polish; strong Theme and Level Design scores possible in small scope.
3. **Top-down or isometric resource / survival micro-loop** — Gather, convert, survive or escape under theme pressure. Why: Clear progression and fun feedback loops; AI assets work well for props and creatures; audio can punch above weight with good SFX; Solo Driver friendly.
4. **Vehicle or “thing you pilot” with a strong fantasy** — Theme supplies the vehicle’s purpose or the world’s hostility. Why: Camera and controls can be the star; avoids humanoid animation; Visuals can lean stylized and readable; good for first-60-seconds impact.
5. **Abstract or non-representational system with a strong metaphor** — Theme is the system itself (e.g., light, memory, growth, decay). Why: Highest Ambition/Innovation ceiling if the system is novel; stands out against literal AI-generated worlds; Level Design and Visuals become expressive rather than representational. Highest risk of “clever but not fun.”

All five can be made with your local image-to-3D + remesh pipeline and agent-written systems. None require complex animation or large levels.

---

## 4. Criterion by criterion: for each of the 7, what a 3, a 4 and a 5 look like in a 4-day jam, and how I get there

**Ambition & Innovation**  
3: Competent execution of a familiar genre with AI help.  
4: One clear new or unusual mechanic or a bold constrained art direction that feels intentional.  
5: A mechanic or presentation that makes judges say “I haven’t seen this in a jam before” and it actually works.  
How: Bet on one novel system early. Kill scope elsewhere. Document the idea clearly in the dev log.

**Use of Theme**  
3: Theme is present in the title and a few assets.  
4: Theme drives the core loop or the player’s goal; removing the theme would break the game.  
5: Theme is reinterpreted in a surprising but coherent way that creates new gameplay or emotional effect.  
How: During concept selection, reject any idea where the theme is decoration. Test by asking “what changes if the theme word is different?”

**Fun Factor**  
3: It works and is not frustrating.  
4: Moments of genuine pleasure; player wants another run or to show a friend.  
5: The core loop is addictive or delightfully surprising in the first few minutes. (This is the tie-breaker.)  
How: Playtest yourself every 2-hour slice. Get one external playtester on day 2. Cut anything that is “interesting” but not fun.

**Gameplay**  
3: Controls work, win/lose is clear, no soft-locks.  
4: Mechanics feel responsive and intentional; systems interact in interesting ways.  
5: The feel of the controls and the interplay of systems are the main reason the game is good.  
How: Prioritize input feel and camera in the first 12 hours. Agent-write systems only after the feel is locked.

**Visuals**  
3: Consistent and readable; no broken materials.  
4: Strong, coherent style (stylized preferred for solo time) that supports the mood.  
5: Memorable look that judges remember after seeing dozens of entries; lighting and composition do real work.  
How: Lock a tight art direction (limited palette, strong shapes, readable silhouettes) on day 1. Use your pipeline for volume but hand-direct every hero asset. Avoid “AI default” look.

**Level Design**  
3: Player can progress without getting lost; basic flow.  
4: Spaces teach the mechanics and create interesting moments; good pacing.  
5: Levels feel authored and purposeful; the space itself is part of the fun.  
How: Design short, dense spaces. One strong vertical slice beats three mediocre areas. Greybox first, art second.

**Audio**  
3: Functional SFX and a looping track that does not annoy.  
4: Audio supports gameplay and mood; key actions have satisfying feedback.  
5: Sound design and music elevate the experience and create identity.  
How: Your ACE-Step pipeline can produce music quickly. Prioritize 8–12 high-quality SFX for core actions over a long soundtrack. Mix for clarity on laptop speakers.

Target: 4+ on Fun, Gameplay, Theme; 4 on the rest if possible; accept a 3 on one secondary if it protects the highs.

---

## 5. Where AI agents help most and where they'll hurt me

**Help most**
- Boilerplate C++ / Blueprint scaffolding and repetitive systems once the design is locked.
- Rapid iteration on parameters and small variants.
- Generating and iterating on art direction prompts, then feeding your local image → 3D pipeline.
- Writing the bulk of the Glass Box dev log from structured logs of agent actions and your decisions.
- QA scripts, packaging automation, screenshot/FPS harnesses.

**Hurt you**
- Early concept and feel. Agents are bad at “does this feel good to control?” You must own the first playable.
- Over-generation of content. Agents will happily produce more enemies, more rooms, more systems that you then have to integrate, debug, and art. This is the classic jam death spiral.
- MCP experimental status. One-tool-at-a-time and potential flakiness will cost hours if you lean on it for every editor action. Use it for high-leverage tasks, not as the primary interface.
- Visual sameness. Unchecked AI assets produce the “2026 AI jam look.” You must curate aggressively.
- False confidence. Agents can make broken systems look complete in the editor until a real playtest.

Rule: You decide the feel and the cuts. Agents implement and document.

---

## 6. Schedule: your version of the 4 days, with gates

Times approximate PT. Theme reveal Nov 11 ~11 AM. Jam proper starts Nov 12 00:00 EST (so late night Nov 11 PT). Submission Nov 15 5:59 PM PT.

**Nov 11 (theme day)**  
11 AM–2 PM: Theme → concept lock (see section 3). Half-page design doc.  
2–6 PM: Verify packaging path, MCP, asset pipeline, OBS, git. One small smoke test.  
Evening: Sleep early. No feature work.

**Day 0 / Night of Nov 11 into Nov 12 (first ~12–16 hours)**  
Gate: Character/object moves, camera feels intentional, one core interaction works in a greybox space.  
Focus exclusively on feel and the core loop. No art, no audio, no secondary systems.

**Day 1 (Nov 12)**  
Gate by end of day: Full core loop playable start-to-something, first Windows package succeeds (even if ugly), cut list written and respected.  
Continue systems. Begin locking art direction. External playtest if possible.

**Day 2 (Nov 13)**  
Gate: Complete start-to-end run possible by a fresh player. Second Windows build. Major systems frozen.  
Vertical slice quality. Begin hero assets and key SFX. Record rough gameplay for video planning.

**Day 3 (Nov 14)**  
Feature freeze 10 PM. Art, audio, UI, juice, lighting, polish.  
Gate: Game feels finished even if not perfect. Final content complete.

**Day 4 (Nov 15)**  
Fixes only, packaging, video capture/edit, itch page, screenshots, dev log polish, submission by 4:30 PM PT.  
90-minute buffer is non-negotiable. Late = disqualified.

Sleep 6 hours minimum every night. If core loop is not fun by end of Day 1, execute the safe fallback.

---

## 7. Modifier strategy: Glass Box vs. the alternatives, and what a winning dev log looks like

Primary: **Glass Box** ($2,500, best dev log). Secondary/fallback: **Solo Driver**. Render Royalty is possible if your stylized look is exceptional but secondary. Pocket Powerhouse requires mobile packaging — skip unless you already have a clean path. Best Team is unavailable to solo.

Glass Box is the highest-leverage modifier for an agent-heavy solo. A winning dev log is not a diary of “I prompted X then Y.” It is a clear story of decisions: what the theme suggested, why you chose the core mechanic, what you cut and why, how agents accelerated specific parts, where you overrode the AI, screenshots of greybox → final, and honest failures. Structure it as a short narrative with timestamps or phases, heavy on visuals and light on filler. Keep notes from hour one (agent logs + your decisions). The log should make a judge understand both the process *and* the taste that shaped the final game. See the official description: “best dev log showing how you built your game.”

Solo Driver is almost automatic if you are truly solo and the game is competitive; treat it as the safety net.

---

## 8. Presentation: video, itch.io page, screenshots, and the first 60 seconds of play

- **Video (30–60 s, 1080p+)**: First 5 seconds must show the core fantasy and the fun. No logos, no slow pans of environments. Gameplay immediately. End on a strong moment or the title. Record on the Legion Go or a clean Windows machine. Multiple takes.
- **First 60 seconds of play**: Player understands the fantasy, the controls, and the theme’s relevance. One “oh, that’s cool” moment. No tutorials that feel like tutorials.
- **Itch.io page**: Clean title, one-sentence hook that includes the theme, 4–6 strong screenshots (not editor views), short description focused on what the player does and feels, clear controls, link to video and dev log. List any Fab/store assets. English only.
- **Screenshots**: Composition and lighting matter more than fidelity. Show the distinctive look and the core activity.

Judges and players form an opinion in under a minute. Optimize for that.

---

## 9. Pre-jam prep: what to build in the next 2 weeks, ranked, within the rules

1. Rock-solid Windows packaging script and test (Linux editor → Legion Go package path). Highest risk item.
2. Unreal MCP reliability and a small set of high-leverage agent tools (not every possible editor action).
3. Local asset pipeline: text-to-image → image-to-3D → remesh/bake, with batch mode while editor is closed. Prompt library for your preferred styles.
4. QA harness: automated screenshots, basic FPS log, simple play-mode checks.
5. OBS + simple video template and naming conventions.
6. Dev-log tooling: structured way to capture agent steps + your decisions + screenshots with timestamps.
7. 24-hour mock jam on a fake theme. Full cycle including package and video. This is the single highest-value prep.
8. Git hygiene and a clean starting project template that declares pre-jam work.
9. Basic music and SFX prompt sets for ACE-Step.
10. Cut-list template and daily gate checklist.

Do not build gameplay, levels, or final art.

---

## 10. Top 10 risks with mitigations

1. Packaging fails late → Test full Windows package on Day 1 and Day 2. Keep a known-good package.
2. Core loop not fun → Hard kill switch end of Day 1; fall back to safe archetype.
3. MCP flakiness → Use for high-leverage tasks only; keep manual editor skills warm.
4. GPU contention (editor vs generators) → Strict batch schedule; generate overnight or while sleeping.
5. Scope creep from agents → Written cut list on Day 1; review every evening.
6. AI visual sameness → Locked art direction with limited palette and strong shapes; heavy curation.
7. Sleep debt → 6-hour minimum; no all-nighters.
8. External playtester unavailable → Self-playtest ruthlessly; record yourself playing and watch it.
9. Theme is awkward for your strengths → Pre-commit to the five archetypes so you can map any theme quickly.
10. Over-investment in Glass Box at expense of the game → Log continuously but write the final log on Day 4 after the game is locked.

---

## 11. One thing you'd do that most entrants won't

Ship a game whose first 20 seconds are *better* than 90% of the field, even if the total content is smaller. Most entrants (especially AI-heavy ones) will front-load world-building, systems, and asset volume. I would treat the opening as a separate product: perfect the camera, the first interaction, the audio sting, and the moment the theme clicks. Judges and players decide in seconds. A short, sharp, memorable opening beats a longer, more ambitious but slower game in this format.

---

## 12. What you're least sure about, and what I should verify

Least sure:
- Exact judge weighting and taste in 2026 now that AI is explicitly optional and common. The “AI is context only” language is clear, but human reaction to AI aesthetics may still create soft penalties or soft preferences. Guess only.
- How reliable Unreal MCP will be under jam pressure in November 2026.
- Whether Solo Driver will be heavily contested or relatively open.

Verify yourself:
- Official rules PDF (linked from the itch page) for any last-minute clarifications on pre-work, packaging, and eligibility.
- Exact packaging requirements and size limits for Windows builds.
- Whether your local asset pipeline produces assets that import cleanly and perform on the Legion Go (low-end test device).
- Current state of MCP documentation and any known issues in UE 5.8.
- Sponsor AI credits if/when announced — claim early if useful, but do not depend on them.

Good luck. Make something that feels designed, not generated. Submit early.  
— Grok
