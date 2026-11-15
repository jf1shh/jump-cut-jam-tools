# MegaJam strategy — Claude Opus 5.5, 2026-10-27

Role for this answer: **the game designer.** I'm treating Fun Factor as the criterion that matters most, because it's the tiebreaker and because it pulls Gameplay and Level Design up or down with it. Facts about the jam come from the [2026 Epic AI MegaJam itch.io page](https://itch.io/jam/2026-epic-ai-megajam) unless I cite something else. I couldn't fetch Epic's own news post or the Official Rules PDF (unrealengine.com returned 403 to my fetcher), so anything that depends on the Official Rules is marked **verify**.

Facts that shape everything below:

- Judges score 1–5 on seven criteria. Epic's short descriptions of them: Ambition and Innovation ("a new mechanic, bold art style, or bigger scope than a four-day jam usually allows"); Theme ("fresh, clever take"); Fun factor; Gameplay ("solid, original mechanics that feel good"); Visuals ("strong, consistent look"); **Level design *and game progression*** ("spaces that support gameplay and guide the player"); and Audio. ([itch page](https://itch.io/jam/2026-epic-ai-megajam))
- The criteria have changed over the years. In 2023 there were five: theme, fun, visuals, audio, gameplay ([2023 page](https://itch.io/jam/2023-epic-megajam)). 2025 added Level Design ([2025 page](https://itch.io/jam/2025-epic-megajam)), and 2026 adds Ambition & Innovation. Most veterans have practised for the old five, so the two new criteria are where an informed solo dev can gain ground.
- The modifiers are Best Team, Solo Driver, Render Royalty (UE only), Pocket Powerhouse (mobile), Glass Box (best dev log; a dev log is required) and Walkie-Talkie (UEFN only). An entry wins at most one main prize and one modifier. ([itch page](https://itch.io/jam/2026-epic-ai-megajam))
- The page says to package a **development build** for Windows/macOS/Android/iOS, and to **declare any prompts, scripts or assets created before the jam**. ([itch page](https://itch.io/jam/2026-epic-ai-megajam))
- AI use is optional, not required. Epic corrected its early wording ([TweakTown coverage](https://www.tweaktown.com/news/114250/epic-games-2026-ai-megajam-offers-dollars65000-in-prizes-but-the-ai-requirements-are-confusing/index.html)). So you're competing against human-made games as well as AI-made ones.

## 1. Verdict on my plan: what to keep, change and cut, and the single biggest mistake in it

**Keep**

- **The asset constraints:** no multiplayer, open world, dialogue trees or humanoid hero. The 2025 results back this up. 2nd place, *Phantom's Manor*, is a ghost that possesses objects ([entry](https://itch.io/jam/2025-epic-megajam/rate/3985022)). 2022's winner, *Fregward*, is a frog ([page](https://honestdan.itch.io/fregward)). Neither needs a good humanoid rig.
- **Daily gates, a Windows build on day 1, and an outside playtester on day 2.** Unreal Source's survival tips put "package and test early" second only to reading the submission rules ([Unreal Source](https://unrealsource.com/n/8-tips-for-surviving-the-epic-megajam/)).
- **Slices of 2 hours or less with a done-test**, and a written cut list. That's ordinary good engineering and it suits you.
- **Six hours of sleep.** Keep it, and use those hours: they are when the GPU is free (see Change #4).
- **The 24-hour mock jam.** It's the most valuable prep item on your list.

**Change**

1. **Ambition from breadth → ambition from depth.** This is the biggest mistake; see below.
2. **Concept picked on paper by 3 PM → two finalists on paper, then pick by feel in the editor before Thursday 1 AM.** A spreadsheet can't measure fun. Score the paper candidates only to get down to two. Greybox both verbs for about 90 minutes each on night 0, then commit to the one that's fun in an empty room.
3. **"Get every criterion to 4, then push two to 5" → choose the two 5s on Nov 11, before you build anything.** The 5s have to come from the concept, not from polish. Pick Fun Factor (it's the tiebreak) and one of Theme or Ambition (the concept decides those). Audio is your best route to a cheap 4 (see §4).
4. **Generation "in batches while the editor is closed" → generation every night while you sleep.** Queue a Qwen-Image / Modly / ACE-Step batch before bed each night. That's about 24 GPU-hours over the jam that would otherwise go unused, and it keeps generation off your waking hours.
5. **Submit by 4:30 PM Sunday → make an insurance submission Saturday night**, a complete and valid entry with the current build and a placeholder video. Then replace the build on Sunday. Whether itch lets you update an entry after submitting is a **verify** item, but itch jams usually allow edits until the deadline.
6. **Day 3 "art, audio, UI and juice" → juice the core verb on day 1, before any art.** Feel is part of the verb, not a coat of paint. If the verb isn't satisfying in greybox, art won't save it. Day 3 is for level dressing and audio.
7. **Level building through the experimental one-call-at-a-time MCP → a data-driven level builder.** Agents edit a text or JSON room spec, and an editor Python or C++ utility spawns the room. Use the MCP for inspection and small fixes, not for placing 300 actors.

**Cut**

- **"More enemy types."** Every enemy type costs AI rigging, animation, tuning and audio. One enemy (or obstacle) archetype with three behaviours tuned by parameters beats four types that each feel half-made.
- **"A bigger hand-built level."** Replace it with more distinct rooms, each with a new idea. Size isn't progression.
- **Render Royalty as an aspiration.** It's UE-only and it's judged on visuals; you're a solo dev with little UE5 lighting experience and AI meshes. Don't spend effort chasing it (more in §7).

**The single biggest mistake:** *"Ambition comes from breadth (a bigger hand-built level, more enemy types), not a fragile tech gimmick."* You've set this up as breadth versus a gimmick, and that's a false choice. Ambition can also come from a **mechanic with depth**: one verb that keeps producing new situations, which is exactly the "new mechanic" in Epic's own wording. Look at what placed in 2025. *These Four Walls* (1st) was one time-projection verb ("project your future self") across puzzle rooms ([entry](https://itch.io/jam/2025-epic-megajam/rate/3977835)). *Phantom's Manor* (2nd) was one possession-and-haunting verb ([entry](https://itch.io/jam/2025-epic-megajam/rate/3985022)). *Renaissance* (3rd) appears to be by one developer, and commenters praised how it "slowly unlocked new gameplay elements" ([entry](https://itch.io/jam/2025-epic-megajam/rate/3984989)). Mark Brown's GMTK 2024 top-20 write-up makes the same point: the standouts start simple and add rules gradually ([GMTK](https://gmtk.substack.com/p/the-best-games-from-gmtk-game-jam-500)). Breadth is the most expensive kind of ambition for a solo dev and the least likely to raise Fun, Gameplay or Level Design. Depth raises all four, Ambition included.

## 2. Your winning strategy in one paragraph

Build a 10–15 minute game around **one verb that *is* the theme**, so that taking the theme out breaks the mechanic. Teach the verb in the first room with no way to fail. Then run 7–9 short rooms, each pairing the verb with one new element. Put a twist at the midpoint that reveals a second meaning of the theme, and end with a finale that uses everything the player has learned plus a clear end screen. Decide the concept by feel: greybox two verbs on night 0 and keep the one that's fun in an empty room. Juice that verb on day 1, before any art. Use AI where it's strong (code volume, props, textures, music, narration, a stylized look that hides mesh quality) and keep it away from where it's weak (character animation, level layout by hand through MCP). Run your GPU pipeline overnight while you sleep. Make Audio a guaranteed 4 with generated music, layered SFX and a narrator. Make the dev log a cheap automated by-product of the work, which keeps you eligible for Glass Box (Epic's natural showcase in an *AI* jam) while Solo Driver eligibility comes free. Ship an insurance build Saturday night.

## 3. Concept strategy: how to pick, plus 5 game archetypes that adapt to most themes and score well, each with why

### The method: theme → verb in 5 passes (about 4 hours on Nov 11)

**Pass 1: Ten readings (30 min).** Write the theme five ways: as a **noun** (an object), a **verb** (an action), an **adjective** (a property of the world), a **situation** (a story beat) and a **feeling**. For each way, write two readings. In 2021, "Running Out of Space" was read by entrants as both outer space and physical room ([Epic 2021 winners post](https://www.unrealengine.com/blog/presenting-the-winners-of-the-2021-epic-megajam)). GMTK 2024 winners read "Built to Scale" as fish scales, window resizing and tower climbing ([GMTK](https://gmtk.substack.com/p/the-best-games-from-gmtk-game-jam-500)).

**Pass 2: Ban the obvious (15 min).** Write down the three readings you think 50 other entrants will pick. Ban them, or keep one only if you can invert it. The obvious reading caps Use of Theme at 3 and Ambition at 3. Inverting the player's role is a dependable source of 5s: *Phantom's Manor* makes you the haunting rather than the hero.

**Pass 3: Verb test (45 min).** For each surviving reading, finish the sentence: *"The player [VERB]s [OBJECT] to [GOAL], and the theme is the verb."* Then apply the "one sentence without *and*" test ([jam survival guide, opinion](https://bugnet.io/blog/your-first-game-jam-a-survival-guide)). If the theme is only the setting ("it's set in space"), reject it.

**Pass 4: The 8-rooms test (60 min, the real filter).** For each of your top 3, spend 10 minutes listing 8 rooms, each as *verb + one new element*. If you can't reach 8 in 10 minutes, the verb is too shallow for Level Design, Gameplay or Ambition to reach a 4. Also write the **midpoint twist** and the **finale** in one line each. A concept without a finale isn't a concept yet.

**Pass 5: Feasibility gate (30 min).** Check each finalist against these:

- At most 15 unique hero or prop meshes, and no humanoid animation beyond idle, move and one action.
- One camera.
- Fail and restart in under 2 seconds.
- Builds on systems you can have agents write in C++ against UE APIs they know well: Enhanced Input, Chaos physics, Niagara, MetaSounds, UMG.

Score the survivors on the seven criteria plus feasibility, keep **two**, and write a half-page for each. Final selection happens in greybox on night 0 (§6).

### Five archetypes that adapt to most themes

1. **One-verb puzzle-platformer with a rule twist** (*These Four Walls*; most of GMTK 2024's top 20).
   - **Why it scores:** Gameplay and Level Design come almost for free, because every room is a designed idea. Theme lives inside the verb. Third-person camera, stylized look, short rooms.
   - **Risk:** platforming feel in UE needs tuning. Add coyote time and a jump buffer on day 1. TFW's commenters called the controls "heavy at first" ([entry](https://itch.io/jam/2025-epic-megajam/rate/3977835)).
2. **Role inversion: you are the obstacle, the haunt or the trap** (*Phantom's Manor*).
   - **Why it scores:** Theme and Innovation get an instant fresh angle, and Fun comes from comedy and from systems reacting to you. The hero is an abstract presence, so nothing needs rigging.
   - **Risk:** you need NPCs that react legibly. Keep them as simple state machines with big readable "scared / angry / fleeing" telegraphs. A commenter wanted "more variety and randomness," so plan 3–4 reaction types.
3. **Top-down arena survival with a theme-mutating rule** (survivors-like, with the theme changing the rules each wave).
   - **Why it scores:** Fun is the highest floor of the five, and it's the easiest to juice (hits, numbers, pickups). It also scales with AI props and textures.
   - **Risk:** it's the most common jam genre, so Innovation sits at 3 unless the theme rule is truly novel. Level Design is weak unless each wave changes the arena itself.
4. **Two-state world toggle** (*Fregward*: switch between physical and spirit realms that sit on top of each other and mirror each other ([page](https://honestdan.itch.io/fregward))).
   - **Why it scores:** one input doubles your level content and *shows* Ambition. Swapping post-process, lighting and materials between the states is a visual wow that costs little in UE (one Material Parameter Collection plus a post-process volume blend).
   - **Risk:** you have to build two versions of each room. Mitigate with the level builder (spawn both states from one spec).
5. **Physics toy or vehicle across a gauntlet of set pieces** (a creature or vehicle hero; GMTK's *Tinker Co.* and *Pizzascaper* are the small-scale version ([GMTK](https://gmtk.substack.com/p/the-best-games-from-gmtk-game-jam-500))).
   - **Why it scores:** Chaos physics produces emergent comedy, which is great for Fun and the trailer. A vehicle or object hero dodges rigging entirely.
   - **Risk:** physics bugs on a different machine. Test it on the Legion from day 1, and fix the physics tick or substepping early.

My ranking for you specifically: **1, 4, 2, then 5, then 3.** Archetypes 1 and 4 suit a systems-minded engineer working with agents. They depend on room design, which a data-driven level builder makes fast, more than on the content volume where AI assets are weakest.

### Core-loop patterns that fit 93 hours and AI assets

- **Room loop:** enter → read the space → try → fail fast → retry → solve → reward beat (sound and light) → door. This is the best fit.
- **Wave loop:** survive → upgrade choice (pick one of three) → the arena mutates → survive. Good for Fun, weaker for Level Design.
- **Caretaker loop:** several needs decay → you route between them → a crisis event → upgrade. *Fregward* used it. It's systemic and needs little content, but it's harder to teach.

## 4. Criterion by criterion: for each of the 7, what a 3, a 4 and a 5 look like in a 4-day jam, and how I get there

These are my own calibrations, based on the 2025 finalists and jam norms. They aren't Epic's rubric, which isn't public beyond the one-line descriptions.

| Criterion | 3 | 4 | 5 | How you get there |
|---|---|---|---|---|
| **Ambition & Innovation** | Familiar genre, competently made | Familiar genre with a mechanic twist I haven't seen, or clearly beyond normal jam scope | "I haven't played this before" *and* it's finished | Concept Passes 2–4. The twist is the verb. A two-state world or a role inversion *looks* ambitious for the cost. Don't count breadth as ambition. |
| **Use of Theme** | Theme in the setting or story | Theme in the mechanic | Theme is the mechanic *and* gets a second meaning at the midpoint twist | Verb test plus a midpoint twist that re-reads the theme. Say the theme out loud in the first 30 seconds (title card or narrator line). |
| **Fun Factor** | Works; you finish it out of duty | You want to finish it; one or two moments of delight | You laugh or say "oh!" and want to replay | Find the fun in greybox on night 0. Juice the verb on day 1. Blind playtests on days 2 and 3, watching for the first smile and the first frown. Under 2 s to restart. A finale. |
| **Gameplay** | Controls work; some floatiness or jank | Tight controls, clear feedback, no soft-locks | Feel is polished: buffers, coyote time, readable telegraphs, fail states that feel fair, and depth from combining the verb with elements | Day 1 feel tuning (checklist below). An agent-written soft-lock audit per room. A respawn volume under every room (TFW lost players to a missing fall respawn ([entry](https://itch.io/jam/2025-epic-megajam/rate/3977835))). |
| **Visuals** | Coherent but generic; AI-asset seams show | One clear style that hides asset quality; lighting is good | A striking art direction you'd remember from one screenshot | Pick the look first, from one style frame. Use flat or toon materials, strong silhouettes, 3–5 colour palettes and fog. Don't attempt photoreal. Use one master material with instances, and grade colour with a LUT. |
| **Level Design & Progression** | Rooms exist; difficulty is flat or random | Each room teaches or tests one thing; guidance through light and colour | A designed arc (introduce → develop → twist → conclude), landmarks, a finale | Level structure (below). A data-driven builder. Guide the player by lighting the door. |
| **Audio** | Music loop plus a few SFX | Music fits; every action has a sound; mixed; distinct tracks for menu, game and finale | Audio is part of the design: a reactive layer, a narrator, rhythm or diegetic sound | ACE-Step for 3–4 tracks with stems. Layered SFX with pitch variance (MetaSounds). A narrator or announcer voice, from a local TTS if your pipeline has one (**guess**: you'd need to add one). 2025's audio winner was the same game as 1st overall ([2025 page](https://itch.io/jam/2025-epic-megajam)), and TFW's narration and voice were singled out ([entry](https://itch.io/jam/2025-epic-megajam/rate/3977835)). |

**Where I'd aim:** 5s in Fun and Theme; 4s in Gameplay, Level Design, Audio and Ambition; a 4 in Visuals if the style is disciplined. That's 31/35. My guess is that's top-3 territory in a ~500-entry field, where 2025 had 491 entries ([2025 page](https://itch.io/jam/2025-epic-megajam)).

### Level structure (template)

The finished game should run **10–15 minutes** for a first-time player. My guess is that judges with hundreds of entries give each one 5–15 minutes.

| # | Beat | Content | Time |
|---|---|---|---|
| 0 | Title | Theme stated, one-line goal, **chapter select** | — |
| 1 | Teach | Verb in a safe room; you can't fail | 60 s |
| 2–3 | Develop | Verb + element A, then verb + element B | 1–2 min each |
| 4 | Combine | A + B | — |
| 5 | **Midpoint twist** | Theme's second meaning; the verb changes or inverts | — |
| 6–8 | Twist rooms | The new meaning × the old elements | — |
| 9 | Finale set piece | Everything, plus music change, slow-mo, payoff | — |
| End | End screen | Time, deaths and score, one funny or emotional closing line, credits, "play again / chapter select" | — |

Each room should be one screen of intent: the door or goal is visible or lit from the entrance. Each room introduces exactly one new idea. That's the Mario-style four-step (kishōtenketsu) approach to level design that Mark Brown has covered on GMTK; I haven't linked that video here.

### Juice checklist (apply to the core verb on day 1, everything else on day 3)

- **Input:** response under 100 ms; Enhanced Input; jump buffer of about 0.1 s; coyote time of about 0.1 s; controller support (judges may prefer a pad; Renaissance recommended one ([entry](https://itch.io/jam/2025-epic-megajam/rate/3984989))).
- **Hit-stop:** 50–80 ms of global time dilation on impacts.
- **Camera:** shake scaled to impact, a slight FOV kick on dash or speed, camera lag on the spring arm, a look-ahead.
- **Hero:** squash and stretch on jump and land (scale the mesh even when there's no skeleton), dust on landing, a trail on fast moves.
- **Every contact:** a Niagara burst, a sound with ±5–10% pitch randomization, and a light flash.
- **Success beats:** a short music stinger, a door-open flourish, a ~1-frame white flash, a counter tween.
- **Failure:** a death effect under 0.5 s, then instant respawn (under 2 s in total), with no menu.
- **UI:** tween everything in (scale from 0.8 with an overshoot); keep the HUD minimal; show diegetic prompts in the first rooms.
- **Audio mix:** duck the music under SFX, use a reverb send per room, and add one ambient bed per area.
- **Post-process:** colour grade LUT, a light vignette, bloom on interactables only; make interactables rim-lit or a distinct colour.
- **Finale:** slow motion, a music shift, a camera pull-out.
- **End:** a stat screen with a punchline.

## 5. Where AI agents help most and where they'll hurt me

**Help most**

- **C++ and Blueprint volume:** player controller, state machines, save and restart, UI wiring, settings menu (resolution, volume, invert Y), and the end screen. This is boilerplate where agents are reliable and you can test with automation.
- **The level builder and room specs.** Agents are good at editing structured text. "Room 6: verb + moving platform + timer, door lit amber" becomes JSON, and the builder spawns it. This is the single largest use of AI for Level Design.
- **Props, textures, skyboxes and UI art** from Qwen-Image, plus image-to-3D for *static* props. Stylized, low-detail props hide remesh artefacts.
- **Music** (ACE-Step): generate many, keep few, and ask for stems or loopable sections.
- **QA:** scripted screenshot tours of every room, fps capture on the Legion, an automated soft-lock test (can the player reach the exit spline in every room?), and a log scan for warnings.
- **The dev log**, drafted from git log, captured screenshots and your voice notes.

**Hurt most**

- **Character animation and rigging.** Avoid it. You already know this.
- **Hand-placing level geometry through the MCP.** One tool call at a time is slow and error-prone, and it's easy to lose an afternoon here. Use it for inspecting and nudging.
- **Taste.** Agents will happily build a mechanic that isn't fun. Only you, in the editor with a controller, can decide fun. Don't delegate the night-0 pick.
- **Consistency of art style.** Image-to-3D outputs vary in proportion, texel density and palette. Enforce consistency with one master material, a palette-quantize step and re-texturing in-engine (triplanar or flat colour) rather than trusting baked textures.
- **Unreal version drift.** Agents trained mostly on UE4 and UE5.0–5.3 code may produce outdated APIs for 5.8. Have them compile often and keep a "5.8 gotchas" note in the prompt library.
- **Audio balance.** Generated music is often over-mastered and fights with SFX. Normalise loudness in the pipeline (about −16 LUFS for music, mixed lower in-game).
- **IP and rating drift.** Image models can produce near-copies of known characters or logos. Review every hero asset for third-party IP and Teen-appropriateness.
- **Agent parallelism making merge conflicts in `.uasset` files.** Binary assets don't merge. Exactly one writer (the MCP or you) touches any `.umap` or `.uasset` at a time. Other agents write only C++ and text.

## 6. Schedule: your version of the 4 days, with gates

All times are PT. The jam opens Wed Nov 11 at 21:00 and closes Sun Nov 15 at 17:59 ([itch page](https://itch.io/jam/2026-epic-ai-megajam), 05:00 UTC Nov 12 = 21:00 PT Nov 11). Each day gets six hours of sleep with a GPU batch running during it.

**Wed Nov 11, pre-jam (paper only)**
- 11:00 Kickoff and theme.
- 11:30–15:30 Concept Passes 1–5. Two finalists, each with a half-page: verb, 8 rooms, twist, finale, asset list, sound palette.
- 15:30–17:00 For both finalists, write the art-direction prompt sets, music prompts and room-spec drafts *as text*. (Prompts are allowed pre-jam; declare them.)
- 17:00–20:30 Eat, rest, nap. Don't build.

**Night 0, Wed 21:00 → Thu 02:00**
- 21:00 Create the jam repo from your tooling commit and tag `jam-start`.
- 21:15–22:45 Finalist A verb in a greybox room: agents write the C++ while you tune.
- 22:45–00:15 Finalist B, the same.
- 00:15 **Gate 0, "find the fun":** which verb do you keep playing after the test is done? Commit to it. Archive the other in a branch.
- 00:30 Write the cut list and the day-1 slices.
- 01:30 **Queue the overnight batch:** 100+ style frames for the chosen concept (3 directions), 10 music sketches.
- 02:00 Sleep.

**Thu Nov 12, Day 1: feel and skeleton**
- 08:00 Pick one style frame and lock the art bible (palette, shapes, materials) in 30 minutes.
- 08:30–12:30 **Juice the core verb** (checklist §4) plus fail and restart.
- 12:30–17:00 Rooms 1–4 greybox through the level builder.
- 17:00 **Gate 1:** Windows build #1 on the Legion, uploaded to a *hidden* itch page with butler. Checks: runs from a cold start, no on-screen debug text, fps logged.
- 18:00–23:00 Rooms 5–6, midpoint twist stub, finale stub, end screen. Every room should be reachable through the chapter select.
- 23:30 Queue overnight: props and hero 3D batch (Modly + remesh), skybox, UI art.
- 01:00 Sleep.

**Fri Nov 13, Day 2: complete arc**
- 08:00–09:00 Import the overnight assets through the pipeline. Swap in the hero mesh.
- 09:00–17:00 Rooms 7–9 plus the finale playable. Settings menu.
- 17:00 **Gate 2:** full start-to-end run in a Windows build. **Two blind playtests, recorded** (screen plus their voice). Don't help them. Note where they first smile, where they first get stuck, and when they look away.
- 19:00–23:30 Fix the top 5 playtest issues. Re-order rooms by difficulty.
- 23:30 Queue overnight: final music (menu, game, finale, with stems), SFX batch, remaining props.
- 01:00 Sleep.

**Sat Nov 14, Day 3: make it beautiful and loud**
- 08:00–14:00 Art pass and lighting; level dressing driven by the builder.
- 14:00–18:00 Audio pass (music, SFX on every action, narrator lines, mix).
- 18:00 **Content freeze:** no new rooms.
- 18:00–21:00 UI polish and juice on everything else. Title screen.
- 21:00 Blind playtest #3 on the RC build.
- 22:00 **Feature freeze.**
- 22:30 **Gate 3, insurance submission:** a complete entry with the current Windows zip, a rough 45 s video and the itch page drafted.
- 23:30 Queue overnight: re-generate or upscale any weak assets flagged today. Optionally an extra music variant.
- 00:30 Sleep.

**Sun Nov 15, Day 4: ship**
- 07:00–11:00 Bug fixes only, from playtest #3. Perf on the Legion.
- 11:00 **Gate 4:** RC2 build.
- 11:00–12:30 Record the gameplay video (§8) and edit it to 45–55 s.
- 12:30–14:00 Final screenshots, itch page, dev log final post, pre-jam declaration.
- 14:00 Final build; test the zip on the Legion from a clean extract; check it's under 1 GB.
- 15:00 **Submit final.** That leaves 3 hours of buffer, more than your plan's 1.5 hours, because Windows packaging depends on a second machine.
- 15:00–17:59 Hands off. Fix only something that's actually broken.

## 7. Modifier strategy: Glass Box vs. the alternatives, and what a winning dev log looks like

You can be *eligible* for several modifiers and win at most one ([itch page](https://itch.io/jam/2026-epic-ai-megajam)). So the question isn't "which one," it's "how much effort on each." Solo Driver costs nothing (you're solo). Glass Box costs a dev log.

- **Solo Driver:** automatic eligibility. Data point: a solo-appearing entry (*Renaissance*, Ghislain Girardot) placed 3rd overall in 2025, and the solo modifier that year went to a different game, *Memory Gate* ([2025 page](https://itch.io/jam/2025-epic-megajam)). So a solo entry can place in the main ranking and the solo modifier can still go elsewhere. Don't count on it.
- **Glass Box:** in an *AI* MegaJam, the dev log of how an agent fleet built a game is the content Epic most wants to showcase. My reasoning: the jam's marketing leans on AI (Epic's announcement is titled "Vibe your way to $50k" ([forum](https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973))). That's a guess about judges' tastes, not a fact. You also have a rare story: an MCP-driven editor, a local image/3D/music pipeline on one consumer AMD GPU, a Linux editor with Windows packaging on a handheld. **Keep Glass Box as the target**, but cap the effort at about 3 hours of your own time across the jam by automating it.
- **Render Royalty:** skip. Visuals specialists will dominate it.
- **Pocket Powerhouse:** skip. Android packaging, touch controls and mobile perf are a fourth project.

**What a winning dev log looks like** (my design; there's no published Glass Box precedent):

1. **Daily posts on itch** (the game's devlog), 15–20 minutes each, drafted by an agent from git log, captured screenshots, the agent run log and your three voice-note lines. Post them *during* the jam, because it shows the work is live.
2. **A final post** that's a real case study:
   - an architecture diagram (agents → MCP → editor, the generators and their GPU schedule);
   - a **decision log** (the 10 readings, the two finalists, why A beat B on night 0, with the greybox GIFs);
   - before/after pairs (prompt → generated image → 3D → in-engine);
   - a **failure log** of what broke and how you fixed it;
   - **numbers**: hours, agent tasks, assets generated vs. kept (people love a keep rate), build count, playtest findings;
   - a 60-second timelapse of the 93 hours;
   - the pre-jam tool declaration.
3. Be honest about where AI failed. That's what makes it a *glass* box rather than an ad.

## 8. Presentation: video, itch.io page, screenshots, and the first 60 seconds of play

**Video (30–60 s, 1080p or higher, required).** Aim for 45–55 s.

| Time | Content |
|---|---|
| 0–3 s | The best moment of the game, the finale or the funniest emergent beat |
| 3–8 s | Title card with the theme in its wording |
| 8–25 s | The verb taught in three escalating clips |
| 25–40 s | The midpoint twist and the variety montage, cut on music beats |
| 40–50 s | The finale |
| 50–55 s | Title and "Made solo with AI agents in 93 hours" |

- Capture from a packaged build at 1080p60 or 1440p on the desktop. A Linux packaged build of the same content is fine for capture. Use OBS with an unlisted YouTube upload.
- Use in-game audio, not a separate track.
- No debug text, no editor UI.

**itch page**
- A cover image at itch's recommended size with readable text; the hero silhouette plus the title.
- A GIF at the top of the description.
- A 3-line pitch: verb, twist, length.
- Controls in an image, with keyboard and pad.
- "Plays in 10–15 minutes" and the minimum specs (tested on Legion Go S).
- Credits and AI disclosure; the pre-jam declaration; a link to the dev log.
- Studies of itch jams find description quality correlates with ranking ([Univ. of Alberta jam study, via search summary](https://asgaard.ece.ualberta.ca/publications/?tgid=20)).

**Screenshots:** five. One per beat (teach, combine, twist, finale, a moody beauty shot). No UI except where it explains.

**The first 60 seconds of play**
1. The title screen loads in under 5 s and music starts immediately.
2. "Play" puts you in Room 1 *with control within 3 seconds*. No unskippable intro.
3. One diegetic prompt shows the verb ("Hold RMB, project yourself"), and the room can only be solved with the verb.
4. The first use of the verb gets the biggest juice moment of the first minute.
5. The door lights up, you walk through, and a stinger plays.
6. In Room 2, the new element is visible from the door.

The judge should know **what the game is about by second 30** and **have smiled by second 60**.

**Technical first impressions**
- Disable on-screen debug messages in the packaged build. In a Development build, Print String shows on screen; TFW's fatal bug came from a debug macro ([entry](https://itch.io/jam/2025-epic-megajam/rate/3977835)).
- Start in borderless fullscreen at the native resolution, and offer a scalability preset menu.
- No crash on alt-tab.

## 9. Pre-jam prep: what to build in the next 2 weeks, ranked, within the rules

Everything goes in a tools repo that the jam repo imports at `jam-start`, plus a declaration file listing every pre-jam script and prompt ([itch page: declare pre-jam prompts, scripts, assets](https://itch.io/jam/2026-epic-ai-megajam)).

1. **The end-to-end ship pipeline:** Linux editor → git push → Legion pulls over SSH → package Development Win64 → zip as `TeamName_GameName` → size check → butler push to a hidden itch page. Prove it on an empty project, time it, and make it one command.
2. **The asset import pipeline:** Qwen-Image → Modly → remesh, bake, scale-normalise → FBX → UE Python import with naming, collision, LODs or Nanite, and a material instance from a master. Prove it with throwaway test assets and delete them. No art in the jam repo.
3. **An overnight GPU batch runner** that takes a prompt file and runs image → 3D → audio sequentially with a manifest, so you queue at 01:00 and import at 08:00. Include a `gpu-preflight` check and a wake-time summary.
4. **The data-driven level builder**, a theme-agnostic editor utility: JSON room spec → spawns primitives, lights, volumes, spawn and exit points. It's a tool, not a level. **Verify** with the rules that a generic editor utility counts as a "script/tool."
5. **The audio pipeline:** ACE-Step → loudness normalise → loop-point trim → UE import into Sound Classes and a sound mix; a SFX generation path; optionally local TTS for a narrator. Test with throwaway outputs.
6. **The QA harness:** automated room tour screenshots, an fps log on the Legion, a "reach the exit" smoke test, and a scan of the packaged build log for errors and on-screen debug text.
7. **The dev log kit:** a periodic screenshot capture plus the agent run log, both feeding an agent that drafts the daily post. OBS scenes for the video and timelapse.
8. **The prompt library:** concept passes (§3) as a prompt; per-archetype system-design prompts; a UE 5.8 API gotchas file; art-direction prompt templates (toon, low-poly, papercraft, ink); and a juice checklist turned into agent tasks.
9. **The mock jam:** 24 hours this weekend or next on a made-up theme, through upload and video. Then fix the tools. Then a second 6-hour mini-mock that only runs from theme to Gate 1, to rehearse night 0.
10. **Practice:** 10 hours of hands-on UE5 editor time on throwaway projects (lighting, post-process, Niagara, MetaSounds, Enhanced Input). This is your weakest skill, and it caps Visuals and Audio. I'd rank it higher than item 7.

## 10. Top 10 risks with mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | The verb isn't fun and you discover it on day 2 | Night-0 two-verb greybox, then juice the verb on day 1. If Gate 0 fails both, take the more feelable one and simplify. |
| 2 | Windows packaging fails late (Legion, SDK, shader compile time) | Ship pipeline proven before the jam; Gate 1 on day 1; nightly builds; an insurance submission Saturday. |
| 3 | The GPU is contended between the editor and generation, starving assets | Overnight batches; the art bible locked on day 1 so batches don't need re-runs; Fab assets as a last resort (allowed but unscored ([itch page](https://itch.io/jam/2026-epic-ai-megajam))). |
| 4 | AI-asset style is inconsistent and Visuals reads 2–3 | One style frame, one master material, palette quantize, stylized flat shading, fog and a LUT. Fewer, better assets. |
| 5 | Scope creep: the "more rooms" instinct | A room budget of 9; content freeze Saturday 18:00; a cut list with pre-decided cuts (cut rooms 7–8 before cutting the finale). |
| 6 | Soft-locks and fall-throughs ruin a judge's run | A kill-and-respawn volume under every room; checkpoint per room; a chapter select; an automated reachability test. |
| 7 | MCP instability or slowness | The level builder plus C++ in files; MCP only for inspection; keep the editor-manual fallback in mind. |
| 8 | Perf on judges' machines (Lumen/Nanite cost, shader stutter) | Scalability presets with a medium default; test on the Legion; precache PSOs if possible (**verify** on 5.8); no Lumen dependency for readability. |
| 9 | Rules or compliance: IP lookalikes, Teen rating, the pre-jam declaration, a Development-build requirement | Review each generated hero asset; write the declaration file now; read the Official Rules PDF line by line. |
| 10 | Fatigue on days 3–4 drives bad decisions | Six hours of sleep, with the GPU working while you do; no new features after Saturday 22:00; Sunday is fixes only, with a written checklist. |

## 11. One thing you'd do that most entrants won't

**Build for the judge's 10 minutes: the finale and the end screen exist by Thursday night, and the title screen has a chapter select.**

Most jam games are built front to back and run out of time before their best part. Judges with hundreds of entries may never reach a game's second half. Two things follow:

1. **The finale is designed and stubbed on day 1**, so it gets polish time.
2. **A chapter select** (labelled "Rooms" or similar, unlocked from the start) lets a judge who's stuck at room 4 jump to the twist and the finale. That turns a "3, got stuck" into a "4, saw the whole arc."

Pair it with a **recorded blind-playtest protocol**: three strangers, no help, watching for the first smile and the first stuck moment. The playtest is already in your plan; recording it and analysing it against those two moments is what most entrants won't do.

## 12. What you're least sure about, and what I should verify

**What to verify**

1. **Pre-jam code allowance.** You wrote "no gameplay," but in 2025 the 1st-place entry declared pre-jam Blueprints ("Relays," "Energy Bow") and the ALS character movement and still won ([TFW entry](https://itch.io/jam/2025-epic-megajam/rate/3977835)). The 2026 page says only "declare" ([itch page](https://itch.io/jam/2026-epic-ai-megajam)). Check whether the 2026 Official Rules allow declared generic code such as a juice library or a level builder. If they do, you're under-preparing; if they don't, the level builder (§9 #4) needs a sign-off first.
2. **"Development build" wording.** Does Epic require the Development configuration, or is Shipping OK? In Development, on-screen debug text shows, so plan for it either way.
3. **Whether you can update an itch jam submission before the deadline.** My insurance-submission plan depends on it.
4. **Who judges modifiers and how many entries each judge plays.** 2025 judging took until March and involved an industry panel ([Epic forum](https://forums.unrealengine.com/t/2025-epic-megajam-mega-stack-o-jam-update/2689696)). My "10–15 minutes per game" figure is a guess.
5. **Whether Glass Box has format expectations** (length, platform, video vs. text). The itch page says only that it's required for that modifier.
6. **Whether the Legion Go S is a good proxy for judges' hardware.** It's low-end; judges probably play on stronger PCs.
7. **UE 5.8 Linux editor stability with the RX 9070 XT** under a 93-hour load. Do the mock jam on exactly this stack.

**What I'm least sure about**
- That judges reward depth over breadth as strongly as I claim. The 2025 top 3 support it, but three games is a small sample, and I couldn't read Epic's 2021–2023 winner write-ups.
- How much Epic's judges will care about the AI story for Glass Box.

**Sections I couldn't source well**
- **Details of past MegaJam winners from Epic's own blog posts** (2019, 2021, 2022). unrealengine.com blocked fetching, so 2021/2022 rely on search snippets, and I have nothing on the 2019 winners' design.
- **The 2023 winners' design** (*Rolling Back*, *Neo-Siege*, *The Lost Slipper* ([Unreal Source](https://unrealsource.com/d/2023-epic-megajam-winners/))). Only the names, not their mechanics.
- **The full 2026 Official Rules.** I couldn't read them.

## 13. Concept worksheet (fill in Nov 11, 11:00–15:30 PT)

**Theme (exact wording):** ______________________

**Pass 1: Ten readings**

| As | Reading 1 | Reading 2 |
|---|---|---|
| Noun | | |
| Verb | | |
| Adjective | | |
| Situation | | |
| Feeling | | |

**Pass 2: Banned obvious readings (what 50 others will do)**

1. ______________
2. ______________
3. ______________

Inversion kept? ______

**Pass 3: Verb sentences (top 5)**

*"The player ___s ___ to ___."* One clause, no "and." Is the theme the verb (not the setting)? Y/N

1.
2.
3.
4.
5.

**Pass 4: The 8-rooms test (top 3, 10 minutes each)**

| Concept | R1 teach | R2 +A | R3 +B | R4 A+B | R5 twist | R6 | R7 | R8 | Finale (1 line) |
|---|---|---|---|---|---|---|---|---|---|
| A | | | | | | | | | |
| B | | | | | | | | | |
| C | | | | | | | | | |

**Midpoint twist (the theme's second meaning):** A ____________ B ____________ C ____________

**Pass 5: Feasibility gate (a fail on any line disqualifies)**

| Check | A | B | C |
|---|---|---|---|
| 15 or fewer unique meshes | | | |
| No humanoid animation beyond idle, move, one action | | | |
| One camera | | | |
| Restart under 2 s | | | |
| Systems agents know (Input / Chaos / Niagara / MetaSounds / UMG) | | | |
| Runs on the Legion | | | |

**Scoring (1–5; predict honestly; Fun counts double)**

| Concept | Ambition | Theme | Fun ×2 | Gameplay | Visuals | Level | Audio | Feasibility | Total |
|---|---|---|---|---|---|---|---|---|---|
| A | | | | | | | | | |
| B | | | | | | | | | |
| C | | | | | | | | | |

**Two finalists:** ________ and ________

**For each finalist**

- One-line pitch: ________________________________
- Hero (creature / vehicle / object / abstract): ________
- Camera: ________
- The juice moment (the first use of the verb looks and sounds like): ________________
- Art direction in 3 words, plus a palette of 3–5 colours: ________________
- Music mood (menu / game / finale): ________ / ________ / ________
- Narrator or voice? Y/N. Who are they? ________
- The first 60 seconds, beat by beat: ________________
- The end screen's closing line: ________________
- Asset list (≤15): ________________
- Pre-decided cuts, in order: 1. ______ 2. ______ 3. ______
- Biggest technical risk, and how night 0 tests it: ________________

**Night 0 Gate 0 (00:15 Thursday):** Which verb did I keep playing after the test was over? ________ → **COMMIT**
