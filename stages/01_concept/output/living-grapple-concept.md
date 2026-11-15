# Living Grapple — candidate game concept

Date: 2026-11-07. Status: pre-jam planning proposal requested by Jared. Working title, not the selected entry or confirmed theme. No gameplay, level data or art is created here. Declare this planning document as applicable. AGENTS.md, RULES.md and PLAN.md remain authoritative.

## Pitch and player promise

A tiny seed courier must carry the last rainseed across a shattered sky garden. Fire a living tether at seed anchors, swing over empty space, and plant permanent vine routes behind you. Every successful crossing makes the next journey easier.

**Hook:** Your best jumps become a garden you can travel through.

Single-player third-person traversal game for UE 5.8 with a Windows package. Target an 8–12 minute first run through three short terraces and one return journey in a single map. This is a movement concept: satisfying attachment, release and landing must work before story or scenery earns time.

## Theme and pillars

Connection is both the tether connecting player to anchor and the permanent route joining isolated islands. Growth is the persistent expansion of that route network. Show a seed becoming a traversable vine within the opening minute. At reveal, keep the concept only if the real theme fits the actual actions.

- A visible anchor promises a reachable landing, never an invisible trick.
- Momentum feels expressive, but recovery makes experimentation cheap.
- A planted route remains useful; the return trip demonstrates what the player changed.
- One polished traversal verb supports the whole game.

The fun bet: attaching, swinging and releasing across a modest gap is enjoyable in greybox without collectibles or spectacle. Ask a fresh player to repeat the first swing voluntarily. If nobody wants another attempt, polish the motion or take the safer traversal fallback.

## Story and structure

The sky garden once exchanged water through flowering vines. A drought broke those connections. The courier carries a rainseed from a nursery to the empty Crown Basin. Three terraces hold pollinator bells; ringing each unlocks the next terrace and provides a safe reset point. Reaching the basin plants the rainseed and sends water through the routes you grew.

The ending is playable: return along the permanent routes to the opening nursery, now blooming. Keep that trip under one minute, with shortcuts. End with a clear completion screen, replay and quit. No dialogue tree, combat, inventory or survival meter.

## Controls and camera

Use a Character-based third-person pawn. WASD / left stick move; mouse / right stick orbit; Space / A jumps. Hold left mouse / right trigger to attach to the highlighted anchor; release to detach. E / X plants at a landing socket or rings a bell. R / Y returns to the latest terrace checkpoint. Escape / Menu pauses and exposes controls, camera sensitivity, music/SFX volume, restart and quit.

The gamepad reticle selects the nearest valid anchor inside a generous cone. The camera keeps the landing island in view, with no mandatory rapid pan. Camera shake is subtle and optional. Provide a reduced-motion setting that removes FOV pulses and landing shake. Anchor highlight uses both a ring and a distinct petal silhouette; availability does not depend on color alone.

## Exact traversal rules

### Attachment and swing

Only authored seed anchors accept the tether. A candidate must be visible, within the proposed 18-meter range, and inside the targeting cone. Display an attach ring before input. One active tether at a time; no second rope, wrapping or surface grappling.

On attachment, record the player-to-anchor distance as tether length. Player input adds bounded sideways/tangential acceleration; gravity supplies the arc. The tether limits outward distance while preserving tangential motion. No rope shortening or manual reel-in in the core scope. Release preserves current velocity up to a safe speed cap. Anchor placement, ground height and movement values are tuning proposals until tested.

Use a movement constraint and a decorative spline, rather than simulated rope links. No rope collision. A short attach grace period and modest coyote time make a near miss forgiving. Reset cancels the tether and clears velocity. Never quietly change the tether target while attached.

### Growing permanent routes

Each traversal segment has a departure socket, one associated swing anchor and a destination landing socket. Activating departure marks it as the current segment. Reach its destination after attaching to the associated anchor to earn the planting prompt. This check prevents planting a route from the wrong terrace or from a mere distant interaction.

Planting grows a predefined vine walkway along an authored path between the two static sockets. It takes about one second and then enables collision. That route remains for the run; it costs no currency and is never deleted. It is a shortcut and a visible record of progress, not a new aiming mechanic. The walkway may curve independently of the tether used to cross, avoiding an implausibly steep path.

Each terrace has two required segments. Completing both allows its bell to ring. Planting a route also updates the safe checkpoint to the landing island. Falling before planting returns to the previous checkpoint; already planted routes stay intact.

### Failure and assistance

Falling into the cloud layer fades and respawns within about two seconds. There are no lives, health or lost plants. Checkpoints are static ground markers with capsule clearance. Restarting the whole game clears progress only after a hold confirmation.

After three falls on the same segment, offer an explicit assist: wider anchor acquisition and stronger landing guidance. If the player still struggles, an optional “Grow a practice crossing” bypass marks the segment complete and grows its route. Show that assistance was used only in the optional end summary; never block the ending. No competitive leaderboard.

## Complete run: three terraces

### 1. Nursery Reach — teach attachment and planting, 2–3 minutes

Start on a broad island with a bell visible across a shallow gap. A practice anchor hangs above a safe lower floor, so the first attach cannot kill progress. Teach hold, swing, release, then land on a broad shelf and plant the first route. The second segment crosses a true cloud gap but uses the same timing and generous landing.

Intended first connection within 20 seconds, first planted route within 60 seconds. Walk a few steps back across the new vine to make permanence obvious. Ring bell one and open the next terrace gate. No lore panel before movement.

### 2. Turning Leaves — steering, 3–4 minutes

Segment three adds a modest sideways offset: swing around a hanging planter toward a broad landing, using tangential input. The planter must not occlude the anchor. Segment four puts the landing slightly higher, teaching a later release. Each segment has one intended anchor; the player is learning motion, not guessing target order.

Plant both routes, ring bell two and look back at the newly connected islands. An optional harmless seed chime sits on the outer side of one landing, rewarding steering without gating the bell.

### 3. Crown Crossing — combine, 2–3 minutes

The first segment combines a small lateral offset and higher landing. The second is the longest apparent gap, but uses an intermediate permanent landing: two short swings with a plant/checkpoint between them, not a mandatory midair reattachment. This limits the most technical interaction to what earlier terraces already taught.

Ring the third bell, walk to the Crown Basin and plant the rainseed. A wave travels down the visible vine network. The return route opens immediately, connecting planted walkways through a few static ramps. Reach the nursery for the completion screen.

### Puzzle and route invariants

Every required landing is reachable with the chosen movement tuning before art is placed. Each segment has a safe departure, an unobstructed anchor and a broad destination. Planted routes never cover another anchor or block later jumps. The return path is walkable in both directions. Test every segment with assistance off and then on.

## Art, animation and audio

Look: wind-worn ceramic islands with thick mint vines, dark blue clouds and warm pink seed lanterns. Favor strong anchor silhouettes and clean sky behind them. Avoid transparent foliage clutter around the reticle. Create original assets during the contest window using the repo's licensed pipeline.

Asset cap: one courier shell, one anchor family, departure/landing seed socket, bell, Crown Basin, modular island kit and a few foliage variants. One hero master material per look. A simple courier with limited animation is acceptable; character rigging must not become critical path.

Tether attach has a wet pluck, tension adds a rising tone, release gives a breath of air, and planting resolves it into a chord. Bells add musical layers. Supply clear visual feedback for each cue. Use scale, petal unfolding, a pulse along the spline and small camera response; skip simulated cloth and rope physics.

## Technical responsibilities

Build during the permitted window only. Follow the repo's Blueprint/C++ split and pinned references.

- C++ movement/constraint component owns attachment state, bounded acceleration, velocity projection, detach and reset. Expose tuning and events to Blueprint. Avoid a giant Blueprint per-frame physics graph.
- BP_SeedAnchor supplies target point and eligibility; BP_TraversalSegment tracks its departure, anchor and landing; BP_VineRoute handles authored growth and collision; BP_TerraceBell owns one-shot progression.
- Blueprint handles visual/audio events, camera volumes and map flow. WBP_HUD owns prompts, assist and route progress.
- Checkpoints retain planted route IDs and latest landing for this run. Persistent disk saves are outside scope.

No runtime mesh generation, dynamic rope collision, fluid simulation or procedural islands. Measure 60 fps at 1080p on the Legion Go S per the repo target; reduce sky effects, foliage and shadows first. Attach targeting and tether rendering must remain responsive.

## Four-day plan and cut gates

| Gate | Deliverable | If behind |
|---|---|---|
| Opening session | Attach, swing, release, fall recovery and one plantable route in greybox | Replace dynamic swing with guided arc if unstable |
| Day 1 / Windows build 1 | First terrace and ending stub; movement feels good before art | Lock movement tuning; reduce segment count |
| Day 2 / build 2 | Complete run plus return path, outside playtest and controller pass | Four segments across two terraces, preserve return payoff |
| Day 3 / build 3 | Art/audio/feedback, assist, rough video and insurance upload; PLAN.md freeze | Cut optional chimes, fancy courier animation and extra vista |
| Day 4 | Fixes, final package/video/dev log, human submission at PLAN.md times | No new traversal rules |

**Minimum coherent fallback:** two terraces, four crossings, guided launch arcs toward highlighted anchors, permanent vine shortcuts and a final return. A guided arc must still allow visible steering or release timing; otherwise pitch it honestly as a traversal puzzle rather than a physics grapple game.

**Excluded:** midair multi-anchor combos, wall running, free grappling, rope wrapping, combat, enemies, crafting, time trials and multiplayer. Optional end stats show falls and routes planted, with no grading requirement.

## Acceptance checks and risk decisions

Verify attachment from moving/falling states, release under a ledge, pause mid-swing, reset while attached and fall during route growth. Check that route collision cannot enable inside the capsule. A segment cannot require an anchor hidden by foliage or locked behind its own planted route. Repeated planting and bell activation do nothing after completion.

A new player should understand hold/release without coaching and plant the first route within a minute. Observe ten attempts on the first real gap: if success is rare or landing feels arbitrary, widen the shelf and tune assistance before adding content. If stable movement cannot be achieved on day 1, use guided arcs or reject the concept.

Complete a fresh run, assisted run, reset run and return path in the actual Windows package. Verify controller focus, audio sliders, quit/replay and Legion performance. Editor movement alone is insufficient evidence.

Primary risk is movement engineering. Secondary risks are camera nausea, anchor readability and spending too long generating scenery. The decision to choose this concept should depend on a convincing movement prototype after the window opens, not its screenshot potential.

## Video, dev log and reveal decision

45-second video: attach/swing in first five seconds; land and plant; return across that same route; show a later turning swing; finish on the basin bloom and connected garden. Record only what the shipped build does.

Glass Box story: early swing failure, motion tuning, simplified rope model, landing assistance, then the persistent-route payoff. Preserve generated asset provenance and distinguish plans from tested behavior.

At reveal, score with _config/reference/templates/scoring-rubric.md. Compared with Root Circuit, this candidate has a stronger movement trailer and a higher day-1 technical risk. Select it only if the actual theme and available implementation time justify that bet.
