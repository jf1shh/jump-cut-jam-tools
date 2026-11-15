# The Last Signal — candidate game concept

Date: 2026-11-07. Status: pre-jam planning proposal requested by Jared. Working title only, not an approved entry or confirmed theme. No gameplay, levels or art created. Declare this planning document as applicable. AGENTS.md, RULES.md and PLAN.md remain authoritative.

## Pitch

The island's last radio operator has one portable relay and a message nobody has heard. Carry the relay through a silent coastal station, place it where signals can reach, and reconnect abandoned greenhouses to the central broadcast tower. Each restored station adds a voice, a light and a patch of returning life.

**Hook:** You can extend the signal or carry it with you—but doing one may silence the path you just opened.

Single-player first-person spatial puzzle exploration for UE 5.8, packaged for Windows. Target 10–15 minutes through three station yards and a broadcast finale in one map. No shooter systems, enemies, generated conversations or realistic radio propagation.

## Theme and design pillars

Connection is an explicit line-of-sight relay chain with a human purpose: reconnecting isolated places. Growth is the expanding coverage network and environmental recovery that follows restored irrigation. Unlike Root Circuit, the central decision is where to physically stand the portable relay, not which authored root to prune.

- Network state is visible in the environment at a glance.
- One movable tool creates several spatial decisions.
- Permanent restorations reward progress, while temporary links remain reversible.
- Voices add emotional texture without withholding required puzzle information.

The fun bet: picking up a relay, moving it a few meters and seeing an entire route light up feels like a discovery. Prove an occluded corner puzzle in greybox on day 1. If players only wander until the light turns green, improve previews and placement choices before adding story.

## Story and ending

A storm severed the station network. The player has a pre-recorded message from the nursery: its seeds survived. Three station caretakers left short recordings that return when their equipment is restored. Use original English text and optional generated or recorded voices only if license and production time permit. Text captions are the core content; voice is optional polish.

Each yard's restored receiver becomes a permanent transmitter and opens the next yard. In the finale the player uses the now-connected network to reach the broadcast tower, then explicitly presses Transmit. Lights answer across the bay and irrigation wakes in the courtyard. A short captioned response confirms the message arrived. End with completion, replay and quit.

No twist that invalidates the player's restoration, no dialogue choices and no moral score. Emotional payoff comes from hearing a quiet place become inhabited again.

## Controls and presentation

WASD / left stick move; mouse / right stick look. E / X picks up, places or operates a focused object. Left mouse / right trigger confirms relay placement while carrying. Right mouse / B cancels a placement preview; the relay stays carried. Q / left bumper toggles network view. Hold R / Y resets the current yard. Escape / Menu pauses and exposes controls, look sensitivity, captions, music/SFX volume, restart and quit.

Use a Character-based pawn. Jump is unnecessary; low curbs and ramps define accessible ground. Camera bob is off or optional. Carrying shows the relay at the lower screen edge without blocking the reticle. Network view reveals legal link paths and coverage rings, with a restrained overlay rather than a mandatory separate map.

## Exact signal rules

### Node types and reachability

Each yard starts with one powered entrance transmitter, several marked relay pads, one or two fixed passive repeaters and one inactive terminal receiver. The player owns exactly one portable relay. A powered node sends to eligible nodes within a proposed 12-meter range and unobstructed line of sight. Links use one signal type; there is no frequency matching or bandwidth simulation.

Passive repeaters only retransmit while reachable from the entrance transmitter. The portable relay does the same while standing on a valid pad; carrying it disables its transmission. The terminal does not retransmit until the player reaches and restores its console. Reachability is recomputed after placement, pickup or gate state changes, not by arbitrary frame timing.

Directional antenna art can indicate link intent, but core links are omnidirectional. Do not introduce aiming/rotation unless all core puzzles are already finished. Distances, collision channel and mount heights are tuning proposals to verify during the window.

### Placement and previews

The relay may be placed only on broad authored pads. Pads show silhouettes and their useful potential links in network view. While carrying near a pad, display a ghost relay and preview which nodes would become supplied; red/gray dashed lines explain blocked or out-of-range links. Confirm snaps it to the pad. Invalid placement leaves it in hand and explains the reason.

Pickup removes its links immediately. The player may retrieve it even if unpowered. If it becomes inaccessible after a gate closes, a hold Recall action at the entrance service box returns it there and clears the current placement. Recall is always available and costs no progress or resource.

### Gate safety and permanent progress

A signal-operated gate begins opening when its receiver is supplied. If power disappears, it closes only when its doorway safety volume is empty; it must never crush or trap the player in collision. A gated static alcove always has a manual release on the inside leading back to the current yard. That release cannot complete a receiver or bypass a future yard.

To restore a terminal, physically reach its console while supplied and hold Interact for about one second. Completion latches the receiver as a new transmitter, opens a permanent exit and enables irrigation/recording. The portable relay remains the same physical tool; it may be picked up or recalled for the next yard. No timer requires sprinting through a door before the signal disappears.

### Recovery and pause

No damage, lives or forced stealth. Falling below a yard returns to its static service marker; the relay stays placed or carried as before the fall. Reset returns the player to that marker and the relay to the entrance stand, preserves completed terminals and clears only temporary gate/placement state. Never erase earlier yards. Pause suspends interactions and returns focus correctly.

## Complete playthrough

### Yard 1: Around the Corner — 2–3 minutes

The entrance transmitter S cannot see terminal T because a tall wall blocks it. Three pads are visible: P1 within S range but still behind the wall, P2 at the outer corner with clear range/visibility to both S and T, and P3 close to T but out of S range. Only P2 completes S → relay → T.

Use network preview to compare pads. Place at P2, walk to T through the now-open gate, restore it and hear the first captioned message. T becomes transmitter two. Pick up the relay while leaving; the restored gate remains open. Target first successful placement within 60 seconds. The first recording should be under eight seconds and never prevent movement.

### Yard 2: Beyond One Reach — 3–4 minutes

A long service garden requires a fixed passive repeater R. S can see R, but neither sees terminal T. Pad P is visible to R and T while hidden from S by a greenhouse. A tempting pad beside S reaches T geometrically but is blocked by the greenhouse wall. The solution is S → R → portable relay at P → T.

One signal gate near T demonstrates that the relay must remain placed until terminal restoration. If the player retrieves it too early, the gate closes safely and its inside manual release returns them to the garden. Nothing forces a restart. The second restoration opens a permanent ramp and starts water in the greenhouse.

### Yard 3: The Message Path — 4–5 minutes

S reaches fixed repeater R1 across a low courtyard. A tall dividing wall blocks R1's view of R2, and S cannot reach R2. A raised static walkway leads to two relay pads: P1 sees R1 but is occluded from R2, while P2 sees both repeaters. R2 has clear range to the terminal T.

Solution: carry the relay up the ramp, inspect lines, place at P2 to complete S → R1 → relay → R2 → T, then walk down the new open route to T and restore it. The pad walk remains accessible regardless of gate power. The third recording brings the earlier voices together; the terminal enables the final tower's permanent link.

### Finale: Send — 1–2 minutes

A permanent stair leads to the broadcast console. Network view now reveals the three restored terminals as a continuous chain. Press Transmit, watch a visible signal pulse across the yards, hear/see the captioned reply and witness the greenhouse bloom. No new relay rule and no hidden collectible requirement.

### Puzzle invariants

Every legal solution must be verified using real engine line traces after art placement. Each required link has generous range margin; no exact centimeter positioning. No glass pane or decorative foliage may silently block the radio channel. Every gate has a safe inner exit. Recall/reset are usable from every accessible yard location. Completed terminals latch, so retrieving the relay never undoes finished progress.

## Art and audio direction

Look: weathered white radio equipment, indigo coast, warm amber windows and restrained mint signal pulses. Plants respond only to restoration beats, avoiding a generic continuously glowing scene. Use signal arcs and node symbols rather than an overwhelming laser web. Give each terminal a distinct number and shape as well as color.

Asset cap: portable relay, pad, fixed repeater, terminal family, gate, final console and modular coastal station kit. No visible player body or custom locomotion rig is required. Use a small set of foliage and greenhouse props. Generate original assets only during the contest window via the approved pipeline; record provenance.

Audio identity: relay pickup click, placement thunk, rising connection tone, soft static on a blocked candidate, irrigation release and one short musical layer per yard. Caption all story recordings and provide visible link activation. Duck background music under speech if speech exists. No always-on radio noise that punishes experimentation; independent audio sliders.

## Implementation responsibilities

C++ owns the graph/reachability service, candidate-link validation, terminal latch state and deterministic reset. Use the correct dedicated trace channel, range tests and a visited set so bidirectional links cannot cause traversal loops. Blueprint actors handle placement previews, door motion, irrigation, recordings and progression.

Proposed actors: BP_RadioTransmitter, BP_PassiveRepeater, BP_PortableRelay, BP_RelayPad, BP_SignalGate, BP_RestoreTerminal and BP_BroadcastConsole. WBP_HUD shows focus prompts, network legend, supplied-state explanations and captions. All restoration actions are idempotent.

The portable relay uses attach/snap placement, not physics throwing. Recompute at discrete edits and relevant moving-gate events. Prefer authored immutable blockers; do not make animated foliage affect radio. No actual radio propagation, dynamic audio transport or LLM services. Keep each yard small; measure the repo's 60 fps at 1080p Legion target and reduce distant effects/shadows first.

## Scope and four-day gates

**Required:** one portable relay, snap pads, range/visibility previews, three station puzzles, permanent terminal restoration, safe gates/recall/reset, final broadcast, captioned story text, menus, Windows package, video and dev log.

**Fallback:** two yards, no movable signal gates (terminals open permanent doors only), no voice acting, one passive repeater total, same broadcast payoff. The spatial placement mechanic remains intact.

**Excluded:** antenna rotation, frequency puzzles, battery drain, signal strength gradients, timed doors, enemies, stealth, inventory, multiplayer, open world and generated dialogue. Do not add those to lengthen a short complete game.

| Gate | Deliverable | Cut decision |
|---|---|---|
| Opening session | One relay, three pads, visible preview, corner puzzle | If players guess blindly, simplify and fix preview |
| Day 1 / Windows build 1 | Yard 1, pickup/recall safety and broadcast stub | Remove dynamic gate closure if recovery is unreliable |
| Day 2 / build 2 | Complete playable chain, outside playtest, controls | Use two-yard fallback if layouts remain confusing |
| Day 3 / build 3 | Art, captions/audio, readability, rough video and insurance upload | Cut spoken recordings and distant scenery before PLAN.md freeze |
| Day 4 | Fixes and final package/materials at PLAN.md times | No new signal rules |

## Acceptance checks and risks

Test boundary range, occlusion, duplicate relay placement, pickup while a gate moves, recall from a sealed alcove, reset during restore, repeated restore inputs and pause during captions. No case may duplicate the relay, lose the tool or reverse a completed terminal.

Confirm every listed route in the actual map. Test failed candidate pads too: they must fail for the displayed reason. If every pad works, the puzzle has disappeared; if only a tiny exact placement works, increase tolerance. Watch a fresh player explain why P2 works in yard 1 before proceeding to denser layouts.

Run a full fresh Windows playthrough with keyboard/mouse and gamepad, verify captions/volume/focus, finish after a reset, and check frame time on Legion. Recheck collision/line-of-sight after every major art pass.

Main risk: an invisible line-of-sight rule feels arbitrary. Previews, clear geometry and generous mounts address that. Secondary risk: it becomes a walking story with no decisions. Each yard must ask a visible placement question before a recording rewards it. Caption-first production prevents voice generation from blocking the build.

## Presentation and reveal decision

Video: blocked signal and ghost preview in the first five seconds; place relay and show lines complete; cut to gate/greenhouse response; show a longer repeater chain; finish on broadcast and answering lights. Keep speech out of the critical explanation if the video may be watched muted.

Dev log: first trace/occlusion bug, why snap pads replaced free placement, gate safety and the playtest that clarified preview language. Record actual implementation outcomes, not claims of realistic radio simulation.

At reveal, score with _config/reference/templates/scoring-rubric.md. This is the lower-movement-risk candidate with strong narrative/audio potential. Choose it over Root Circuit only if the theme and spatial placement puzzles justify the quieter pace.
