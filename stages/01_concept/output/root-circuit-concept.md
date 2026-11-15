# Root Circuit — candidate game concept

Date: 2026-11-07. Status: pre-jam design proposal requested by Jared; not the selected entry or confirmed contest theme. Working title only. No gameplay, levels, art or audio are created by this document. Review against the actual theme at reveal; include this planning document in the pre-jam declaration as applicable. AGENTS.md, RULES.md and PLAN.md remain authoritative.

## The pitch

You are the last caretaker of a suspended botanical power station. Its water still flows, but its living circuits have fallen apart. Connect roots between sockets to awaken bridges, spring flowers and ancient doors. Every connection consumes part of a limited root network, so reaching a new place means deciding what you can safely let go.

**One-sentence hook:** Build your own path through a dead garden, then pull that path apart to bring the garden back to life.

Single-player, third-person exploration puzzle game for Unreal Engine 5.8, developed on Linux and packaged for Windows. Target a complete first playthrough of 10–15 minutes, with three compact chambers and a short finale in one persistent map. No combat, resource grinding or precision platforming. The challenge is reading and rearranging a network.

## Why it could fit the theme

For **connection**, the player creates a literal network and learns that a useful connection depends on the larger system. For **growth**, the player chooses where life can grow under a shared constraint. Both appear in the first interaction and the final payoff, rather than existing only in story text.

The banner's glossy flower forms are visual inspiration only; there is no evidence here that they reveal Epic's theme. At reveal, write a fresh one-sentence theme statement. Keep this candidate only if the actual theme changes the player's decisions in a convincing way. Do not force an unrelated theme into a subtitle.

## Design pillars and fun bet

1. **A connection visibly changes the world.** A root draws itself across stone; a bridge unfurls; a dark flower opens with a musical note.
2. **Rewiring is the puzzle.** The interesting choice is which useful structure to turn off so another can turn on.
3. **Experimentation is safe.** Failed attempts cost seconds. Reset and undo never require replaying solved chambers.
4. **The whole garden is readable.** Sockets, routes and structures share symbols. The player can inspect the network without memorizing hidden rules.

The fun bet is that growing a route, walking across it and reclaiming it from the far side feels like clever use of space. Test that in greybox on day 1. If that sequence is confusing or tedious, more art will not fix it.

## Player fantasy, story and ending

A palm-sized caretaker with a seed-shaped backpack wakes beneath an empty irrigation reservoir. The central Heartseed is dormant. Three maintenance seals prevent its final water supply from opening. Each chamber houses one seal, reached by repairing its local network.

Tell the story through dry waterways, closed petals and the contrast between machinery and returning vegetation. Use three short environmental messages at most: “Water remains.” “Find another way to reach.” “Let the garden carry it.” No voiced dialogue, branching story or NPC simulation.

At each chamber exit, manually turn its maintenance seal. This permanently opens the next route and replenishes the garden's central reservoir; local puzzle connections remain reversible. In the finale, connect one last root to the Heartseed. Previously restored sections bloom in a coordinated wave. The camera rises briefly to show the garden the player rebuilt, then returns control before an explicit completion screen. Credits, replay and quit are available.

## Camera, movement and controls

Use a proven Character-based third-person pawn with walk, camera orbit and a forgiving jump. Compact paths have guardrails where falling would be tedious. No sprint requirement, stamina, climbing or grappling.

| Action | Keyboard / mouse | Gamepad proposal |
|---|---|---|
| Move / camera | WASD / mouse | Left / right stick |
| Jump | Space | A |
| Select socket / confirm route / use seal | Left click or E | Right trigger |
| Cancel pending selection | Right click | B |
| Remove highlighted root | Hold R | Hold X |
| Undo last network edit | Z | D-pad left |
| Network overview | Tab | Y |
| Reset chamber | Hold T | Hold D-pad down |
| Pause, controls, volume, restart, quit | Escape | Menu |

Final prompts reflect the active input device. Overview uses a fixed elevated camera with a visible player marker; movement pauses while inspecting. Connection mode shows only legal destinations. No tiny aiming targets: generous socket targeting, clear focus outline and nearest-target assistance.

## The living circuit: exact rules

### Nodes and links

Each chamber is its own independent rooted graph. It has one blue droplet-marked water source, branch sockets and plant sockets. Authored candidate routes connect particular pairs of sockets. The player chooses among those routes; there is no freehand drawing, arbitrary surface attachment or simulated fluid.

A live link costs **one root segment**, regardless of its visual length. The chamber's budget is displayed as filled root icons plus a number. Water is binary: a node is supplied if reachable from the source through active links. There is no flow rate, distance loss, colored resource mixing or timed drainage.

To add a route, select a supplied socket, then an unconnected destination along a highlighted candidate route. It must have a free budget segment. All ordinary sockets may branch along their authored routes. Ordinary loops and multiple parents are disallowed to keep pruning predictable; a loop attempt previews “Already connected.” Invalid attempts spend nothing.

The final Heartseed has its own single input and uses the same ordinary connection rule; there is no special multi-source logic to teach at the end.

### Growth and plant effects

A valid edit updates the graph immediately. Visual growth takes roughly 0.6–1.0 seconds, after which its device becomes usable. Inputs are locked only for that short transition to prevent overlapping edits. A supplied plant maintains its effect until disconnected:

| Plant | Visual identity | Effect | Job in the puzzles |
|---|---|---|---|
| Bridge vine | Long leaf / horizontal bar symbol | Unfurls a fixed walkway across a gap | Create a crossing and reclaim it after crossing |
| Spring bloom | Upward petals / chevron | Launches the player to a fixed landing shelf | Reach a socket from a different side |
| Root lock | Coiled roots / lock symbol | Opens a nearby gate | Spend budget to reach a new route |

Spring launches use an authored destination, generous landing surface and a brief input assist; no ballistic aiming puzzle. Devices display their linked socket's symbol and pulse together when targeted.

### Pruning, undo and reset

Remove a highlighted link from any visible socket in the current chamber, including from across a gap. Removal also removes its downstream subtree and refunds every removed segment. Preview that subtree and show the refund count before confirmation. This avoids stranded disconnected links and hidden budget consumption.

Undo restores the previous complete graph state, including a pruned subtree. Keep a short history of at least 10 edits within the current chamber. Undo never teleports the player; safety checks apply to its structural changes too. Reset clears only the current unsolved chamber, returns the player to its entrance and restores its budget. Explain hold actions with a visible progress ring.

If an edit would retract the bridge currently supporting the player, reject it with “Step onto solid ground first.” If a fall occurs, fade and return the player to the last safe static landing surface, preserving the network. A chamber reset remains available even when no route back exists. Safe respawn markers never sit on dynamic structures. Seals and chamber completion are irreversible, outside the network undo stack.

### Readability

Dry roots are matte and contracted. Wet roots have moving droplets or a traveling pulse; supplied plants open. Candidate routes appear as dotted strands during selection. Use shape, animation, icons and labels alongside blue/green color. HUD: current chamber seal, root budget, focused action and a short contextual explanation. On budget exhaustion, preview the proposed route and highlight reclaimable roots instead of silently ignoring input.

## A complete playthrough

All layouts below are design briefs, not prebuilt maps or level data. Lettered sockets are explanatory names. Physical routing must be authored and verified during the contest window.

### Chamber 1: First Drink — 2–3 minutes

Teach selection, crossing and reclamation. Budget: **1** segment.

Candidate links: source S–bridge B; S–lock D. B creates a crossing from the entrance bank to a permanent middle island. D opens the exit gate on that island. A tutorial baffle makes D targetable only from the island. The seal sits beyond that gate on permanent ground.

Solution: connect S–B; cross onto the island; prune S–B remotely; connect S–D; walk through and turn the seal. The single-segment budget makes reclamation necessary. A contextual prompt appears on the safe island: “The bridge has carried you. Reclaim its root to open the gate.”

Target first valid connection within 30 seconds and first bridge crossing within 60 seconds. One prompt per action; dismiss permanently when performed.

### Chamber 2: Borrowed Reach — 3–4 minutes

Make pruning necessary. Budget: **2** segments.

Links: S–junction J; J–spring F; S–lock D. The player begins on static ground beside S/J/F. F launches to a permanent upper shelf. D is visible and targetable only from that shelf and opens its exit gate. S and the J branch remain visible from the shelf.

Solution: build S–J–F (2/2); ride F to the upper shelf; prune S–J and its child J–F (refund 2); build S–D (1/2); reach the seal. Show the subtree preview clearly. The important realization is that a route can finish its job and be reclaimed, even though it was essential a moment earlier.

Wrong turn: trying D from below gives “Reach the upper shelf,” not a generic invalid message. Missing the spring landing triggers safe recovery on the starting bank.

### Chamber 3: A Different Way Back — 4–5 minutes

Combine bridge and spring, then reclaim a route to open the last gate. Budget: **3** segments.

Links: S–bridge B; S–junction J; J–spring F; J–lock D. B crosses from entrance to a static middle island containing J and F. F launches from there to a permanent overlook. D opens the gate on the overlook. The entrance has no view of J; the middle island has no view of D. From the overlook, B's socket and J/D are targetable.

Solution: S–B (1); cross; S–J and J–F (3); launch to overlook; prune S–B (2); add J–D (3); enter the final seal room. J–F can also be pruned instead of B once safely on the overlook: accept both solutions. The puzzle tests resource reasoning, not guessing a single prescribed answer.

Keep required sockets visible from all decision landings. Wrong network choices are reversible; the overview identifies each device and its candidate route. Turning the seal opens a permanent return passage to the Heartseed court.

### Finale: Let It Flow — 1–2 minutes

The three seals have charged the central reservoir through visible channels. Back in the court, the reservoir's single root route becomes available. Connect it to the Heartseed and trigger the bloom wave. This is a low-friction reward, not a fourth rule set or a timed boss.

A small hub can reveal new views after each seal, but a linear corridor between chambers is the fallback. Never require an unexplained backtrack to find the finale.

## Scope and progression

**Must ship:** one map; three reusable device types; source and branch sockets; authored route selection; root budget; subtree pruning; undo; reset and fall recovery; three chambers; seal progression; finale; controls/pause/volume; packaged Windows build; gameplay video and dev log.

**Minimum coherent fallback:** two chambers, bridge plus lock only, then Heartseed finale. Replace the spring shelf with a static ramp. Preserve a mandatory budget-and-reclaim puzzle, clear ending and feedback. If pruning is not fun, reassess the concept rather than adding enemies or crafting.

**Only after a complete packaged run:** optional bloom collectibles on alternate routes, chamber replay selection, richer hub vistas and additional musical layers. None can gate completion.

**Excluded:** multiplayer, procedural levels, freeform vines, realistic fluids, simulated soft bodies, combat, inventory, crafting, day/night cycle, dialogue generation, skill trees, persistent campaign saves and a second biome. One environment, short session, fast restart.

## Art direction and asset plan

Phrase: **a rain-starved ceramic conservatory awakening into a luminous garden**. Warm ivory stone, dark indigo voids and water channels; mint-green supplied roots; magenta spring flowers. Use glossy rounded petals as an original stylistic motif, without copying the contest banner or importing it as game art.

Silhouettes carry meaning: long flat leaves for bridges, upward cupped flowers for springs, tight coils for locks. Keep roots thick enough to read against the floor. The caretaker needs a simple original silhouette and readable locomotion; elaborate skeletal animation is not a dependency. Use the existing proven movement setup, with a simple visual shell if needed.

Asset budget: one caretaker look; one socket family with source/branch/device variants; one bridge, spring and lock; one Heartseed; one modular stone kit; one foliage kit. Reuse material instances, scale and placement. Use one master material per hero look per repo conventions. Fake growth with spline reveal and device scaling, not mesh regeneration. Camera framing and synchronized color change deliver the final vista.

Create all shipping art during the permitted window. Follow AGENTS.md's licensed generation providers and asset ledger; no additional provider or model is assumed approved. Prefabricated geometry is not a prerequisite for a readable greybox.

## Sound and game feel

The inactive garden has wind, sparse drips and distant ceramic creaks. A connection plays a soft pluck and water rush, a bridge unfolds with leafy movement, a spring gives a clear launch cue, and a lock releases with a low wooden click. Invalid actions use a soft dry tap plus explanatory text. Pruning has a distinct reverse ripple so it feels deliberate rather than destructive.

Chamber seals add musical texture; the finale combines it into a short resolution. Sound is reinforcement: no puzzle depends on hearing a cue. Provide independent music and SFX volume. Record connection, pruning, seal and final bloom footage for the Glass Box dev log and video.

## Implementation plan for jam week

This describes intended responsibilities, not code created ahead of the window. Reuse the repo's verified tools; consult its pinned engine references before selecting APIs.

- **C++ graph component:** stable node/route IDs, source reachability, budget validation, subtree removal, undo snapshots and deterministic edit results. Return explicit failure reasons. Recompute on edits; no per-frame graph traversal.
- **Blueprint actors:** BP_RootSocket, BP_RootLink, BP_BridgeVine, BP_SpringBloom, BP_RootLock, BP_MaintenanceSeal and BP_Heartseed. Device state reacts to supplied/not-supplied events. Keep visual completion separate from graph validation.
- **Player interaction:** focus targeting and selection; inspectable preview; controller assistance; holds for destructive actions. Camera overview is authored per chamber.
- **Chamber controller:** entrance reset, static safe markers, root budget, completion flag and progression. Completion resets selection/history and enables the next chamber. No cross-chamber edges.
- **UI:** WBP_HUD, pause/controls/settings, completion screen. Prompts show actual costs and refund totals.
- **Data:** during the window, author socket IDs, legal routes, devices and safety markers per chamber. Do not infer connectivity from spline overlap or physics collision.

Collision rules: bridge collision enables only after growth completes; retraction checks occupancy before graph commitment. Spring triggers ignore repeated overlap during launch and cooldown. A seal can activate once. Changing or resetting chambers cancels pending selection and restores input/camera control.

Graph budget target: fewer than 30 nodes and 40 candidate routes across the entire game; chambers remain isolated. Visual roots update only while animating. Pool or reuse components if needed; avoid Niagara fluids, runtime generation and expensive foliage density. Target the repo's 60 fps at 1080p on the Legion Go S; measure there and reduce shadows, effects and vista detail before compromising interaction readability.

## Four-day delivery plan

Follow PLAN.md's exact build and submission times; this concept does not replace those gates.

| Gate | Root Circuit deliverable | Cut trigger |
|---|---|---|
| Opening session | Movement, socket selection, one growing bridge, budget and pruning in greybox | If the core crossing/reclaim sequence cannot work, stop dressing the level and fix it |
| Day 1 / Windows build 1 | Chamber 1 playable; core water/root feedback; tiny finale stub reachable; budget and reset verified | If spring launch is unreliable, use ramp fallback immediately |
| Day 2 / build 2 | Full start-to-ending run; three chambers or two-chamber fallback; outside playtest | If a new player cannot explain pruning after chamber 2, simplify graph and prompts before adding content |
| Day 3 / build 3 | Art/audio/UI pass, gamepad pass, safe recovery checks, rough video, insurance upload | Cut collectibles and hub complexity first; feature freeze at PLAN.md's 10 PM |
| Day 4 | Fixes only, final Windows verification, final package/video/dev log and human submission | No new mechanics or puzzle variants; follow the early submission buffer |

## Acceptance and playtest checklist

During implementation, test the graph rules in isolation where useful; do not spend the jam testing decorative wrappers. At every gate run the actual packaged game, not just graph inspection or an editor launch.

- Valid add spends exactly one; invalid add changes nothing. Pruning a branch refunds its whole subtree. Undo restores it atomically without exceeding the budget.
- No loop, disconnected paid edge, stale selection or repeated seal activation can corrupt the network.
- Complete every chamber using the stated solution; verify both accepted chamber-3 reclamation choices.
- Attempt removing the bridge under the player, miss a spring landing, undo near a moving device and reset from an isolated shelf. Recover without restarting the application.
- Verify bridge collision, spring destination and safe spawn using the actual player capsule. All required sockets remain targetable on keyboard/mouse and gamepad.
- A new player makes a first connection without spoken coaching, understands budget and reclamation by chamber 2, and finishes within roughly 15 minutes. Log observed times and confusion; targets are hypotheses until tested.
- Pause, overview, controls, volume, restart, completion, replay and quit all return usable focus/control. No audio-only or color-only information.
- Windows package launches from its extracted folder without the editor; performance, resolution, controls and audio are checked on the Legion. Packaging success alone is not playability evidence.

## Risks, cuts and concept decision

| Risk | Early evidence to seek | Response |
|---|---|---|
| Rewiring feels like busywork | Player crosses/prunes without making a choice | Keep early teaching brief; make later budget choice change what is reachable |
| Routes are visually confusing | Player cannot match socket to structure | Reduce links, improve framing, use symbols and synchronized highlighting |
| Player gets stranded | Recovery needs replaying a whole chamber | Remote pruning, undo, static safety markers and reset are core scope |
| Spring is unreliable | Landing failures despite correct interaction | Fixed destination assist, then cut spring for ramp |
| Generated art consumes build time | Greybox fun remains unproven | Ship stylized simple forms; reserve generation for a few hero objects |
| Reveal theme does not fit | Theme statement relies on lore alone | Keep this as a candidate and choose a better concept |

Cut in order: optional objectives, extra hub vistas, bespoke caretaker animation, chamber 3, spring device. Keep the core connection/budget/reclaim loop, two readable puzzles, working recovery, satisfying ending and complete submission.

## Presentation and next decision

Suggested 45-second video: 0–5s bridge grows and player crosses; 5–15s root budget fills; 15–25s reclaim a branch and power a new route; 25–35s spring and final lock; 35–45s Heartseed bloom and title. Capture real gameplay and avoid a logo-only opening. Adapt to the two-chamber cut if that is what ships.

Dev log story: initial hypothesis, first greybox crossing, what a new player misunderstood, how pruning previews/recovery changed the design, and the finished before/after garden. Credit AI tools and original human design decisions accurately; preserve prompts, iterations and asset provenance through the repo's existing process.

**Next action:** after the theme reveal, score this candidate with _config/reference/templates/scoring-rubric.md alongside the other candidates. If selected, condense its final decisions into the jam's GDD one-pager and prove the crossing/reclaim loop in greybox once the contest window opens.
