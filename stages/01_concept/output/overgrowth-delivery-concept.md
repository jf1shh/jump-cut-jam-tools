# Overgrowth Delivery — candidate game concept

Date: 2026-11-07. Status: pre-jam design proposal requested by Jared. Working title only; not the selected game or confirmed theme. Planning creates no gameplay, levels or art. Declare this document as applicable and follow AGENTS.md, RULES.md and PLAN.md.

## Pitch

You are the last seed courier in a little rooftop town. Every delivery makes a neighborhood bloom—and changes the route map. A root bridge may open a shortcut while its canopy blocks a low passage. Plan the order, carry the seed, and find a new way through the town you are growing.

**Hook:** Every successful delivery changes your next route.

Single-player third-person route-planning adventure for UE 5.8 with a Windows package. Target 12–15 minutes, one compact walkable district, three mandatory seed deliveries and a final rooftop celebration. No vehicles, combat, platforming precision or procedural city.

## Theme and design pillars

Growth directly transforms traversal. Connection is the network of homes, bridges and garden routes the courier builds. Completion should visibly reunite the district rather than merely increment three delivery counters. At reveal, evaluate the actual theme against the route-changing mechanic.

- Make a delivery's route consequences visible before commitment.
- Reward remembering the town, not memorizing hidden lock conditions.
- Permit multiple delivery orders without permitting permanent failure.
- Keep walking distances short enough that rerouting feels clever instead of punitive.

The fun bet: taking a seed to a destination, watching a shortcut grow and immediately using it feels satisfying; choosing delivery order makes the second trip meaningfully different. Prove one opening/closing transformation in greybox before adding a town's worth of scenery.

## Story and completion

The neighborhood's last rain collection has arrived. Three residents left seed requests at the depot: a bridge tree for the clinic, a shade vine for the market and a spring garden for the rooftop school. Use short original notes and visible location symbols instead of quest dialogue.

The depot offers three distinct seed parcels, one per destination. After all three deliveries, the grown routes lead toward a rooftop greenhouse where residents' lights and banners form a simple celebration. The courier places the empty seed satchel at a final planter; the district blooms in a synchronized wave. Return control briefly, then show completion/replay/quit.

Residents can remain represented by lit windows, notes and simple silhouettes. Full NPC animation, dynamic schedules and dialogue are unnecessary.

## Controls and camera

Use a Character-based third-person pawn with WASD / left stick movement, mouse / right stick orbit, Space / A jump and E / X interact. Tab / Y opens the district map. At the depot, choose a parcel through a clear three-item panel; B / circle-style cancel returns without taking one. R / left bumper opens a hold-confirmed Return to Depot action. Escape / Menu pauses, shows controls, camera sensitivity, music/SFX volume, restart and quit.

A single seed parcel sits visibly on the satchel. Delivery targets show matching shape icons: clinic cross, market awning and school book. Colors reinforce the symbols. No UI assumes knowledge of real street names. The district map shows current player, destination, open paths and previewed transformation effects, with a legend.

## Exact delivery and transformation rules

### Parcel state

One parcel at a time. Picking a parcel from the depot marks its destination on HUD/map. Each seed has exactly one compatible planter. Interacting with a wrong planter explains the required seed; no consumption occurs. Return to Depot transports the player to its safe marker and returns an undelivered parcel to stock. Completed deliveries remain completed.

At the correct planter, hold Interact for about one second. The seed is consumed once, the delivery flag latches and a fixed growth sequence plays. Before the hold begins, show the affected routes on the map and nearby world markers. No health, lives, currency, fuel or delivery timer. Optional end stats may count distance but cannot block the ending.

### Growth changes

Each delivery replaces an authored route state, not arbitrary vegetation simulation. One route opens, and at most one low passage closes. No growth closes the only path to an undelivered destination or the depot. The player's capsule must be outside each changing collision volume before activation commits; move the interaction point to a safe static apron by design.

If another actor or the player occupies a closure volume, delay closure and mark it “Clearing path,” rather than crush or teleport them. Disable obsolete collision and enable new route collision at deliberate animation stages; cancel/reset cannot leave both states partly enabled. Already completed growth is permanent for the run.

### Map logic and topology

Plan the district as static hubs: Depot D, Plaza P, Clinic C, Market M, School S and Roof Finale F. Proposed base routes, all bidirectional:

- D–P main street, always open.
- P–C clinic alley, always open.
- P–M market stair, always open.
- M–S school ramp, always open.
- C–M low service tunnel, open initially.
- P–S covered arcade, open initially.

Delivery effects:

| Delivery | Opens | Closes | Why the closure is safe |
|---|---|---|---|
| Clinic bridge tree | D–C direct vine bridge | C–M service tunnel | C–P–M always remains |
| Market shade vine | C–S roof walk | P–S covered arcade | P–M–S always remains |
| School spring garden | D–S broad garden stair | Nothing | Adds a shortcut without removing access |

When all three flags are set, S–F opens as a permanent final stair. Growth animation may look like a spring garden, but no launch mechanic is required. The graph is a design specification to author and test during the contest window, not a prebuilt map.

All mandatory destinations remain reachable in every one of the eight completed-delivery subsets because D–P–C and P–M–S never close. That invariant is more important than making every delivery order equally short. Optional shortcuts change route length, not solvability.

### Recovery and persistence

Falling returns to the latest static district marker with the current parcel and growth flags preserved. Return to Depot remains available except during the brief commit/growth transition; after that it must always work. Full Restart clears parcel, flags, map and growth atomically after confirmation. No undo of delivered growth and no save file needed for the short run.

## Complete run and example orders

### Opening: One Small Package — 1–2 minutes

Start beside the depot map with all three destination silhouettes visible in the skyline. The first parcel recommendation is clinic, but the menu permits any order. Before pickup, use one short line: “Each seed changes the streets.” Walk to the plaza, see a marked shortcut tunnel and locate the clinic with its cross-shaped planter sign.

Aim for first pickup within 30 seconds and first delivery within two minutes. Keep the initial clinic route under about 45 seconds of travel. No unrelated fetch step or quest acceptance ceremony.

### Clinic: A Bridge Home — 2–3 minutes

Deliver at a static apron outside the tunnel closure volume. A tree arcs across the canal, opening D–C, while thick roots close C–M's service tunnel. The view frames both changes. The player can use the new bridge to return to the depot; the map marks the service tunnel closed. The clinic window lights and an original short thank-you note appears without stopping movement.

### Market: A Higher Street — 3–4 minutes

Carry its parcel from D via P–M. Delivery opens the clinic-to-school rooftop walk C–S and fills the plaza-to-school arcade P–S with hanging vines. The market destination remains connected to both P and S. Point the camera briefly toward the new roof walk, then restore control.

If clinic was delivered first, the new roof route creates D–C–S for later travel. If market was first, the school is still reachable by P–M–S or P–C–S. The closed arcade's signs clearly redirect rather than leave an invisible wall.

### School: A Stair for Everyone — 2–3 minutes

The school is initially accessible through the market ramp. If market is complete, C–S offers an alternative; if the school is chosen first, P–S remains open. Deliver to grow the broad garden stair D–S. It offers a fast return for remaining parcels and a clear final approach.

After all deliveries, the map reveals S–F and the depot changes its prompt to “All seeds delivered — join the rooftop bloom.” No need to talk to an NPC to unlock the ending.

### Finale: Connected District — 1 minute

Follow any current route to S, climb the permanent final stair and plant the empty satchel. Bloom across the three visible destinations. The camera frames the actual grown shortcuts before the completion screen.

Two example valid orders: C → M → S emphasizes the network expanding across town; S → M → C gives an early depot/school shortcut and closes routes in a different sequence. All six delivery permutations are supported. No “best order” score is promised unless travel distances are later measured and balanced.

## Art, assets and sound

Look: a miniature sunlit rooftop town with chunky pastel masonry, dark purple shadows, glossy mint roots and magenta blooms. Grow large readable silhouettes rather than dense foliage. Canal, elevation and destination signs orient the player; keep the depot visible from several streets.

Asset cap: one courier shell/satchel, three parcel/planter variants, one modular town kit, bridge tree, market canopy, garden stair, finale planter and a few prop/foliage variants. Doors/windows can imply people without NPC systems. Reuse materials and hero growth meshes; avoid bespoke buildings for every corner.

Delivery audio begins with a seed click, builds through leafy unfolding and resolves with the neighborhood's short melodic signature. The ambient mix gains birds/water as flags accumulate. Map changes have a readable visual pulse and captions; no audio-only route instructions. Independent music/SFX sliders. Generate original shipping content during the window through approved tooling and log provenance.

## Implementation responsibilities

C++ owns parcel state, delivery flags, route-state resolution and atomic restart. Expose read-only state and explicit delivery success/failure reasons. A small authored adjacency list supports map previews and reachability checks; runtime navigation generation is unnecessary for a human-controlled courier.

Blueprint actors: BP_SeedDepot, BP_DeliveryPlanter, BP_GrowthRoute, BP_DistrictMarker and BP_RooftopFinale. Route actors have explicit initial/completed collision and visibility states. WBP_DistrictMap reflects the same source-of-truth flags as world actors; do not duplicate progression logic inside widgets.

Growth sequences should interpolate known geometry/material parameters, then finalize collision; avoid procedural vegetation and actual tree physics. UI previews compute “if delivered” states without mutating the world. Idempotent initialization lets a reset restore every route reliably. Follow CLAUDE.md naming and Blueprint/C++ conventions.

Measure the repo's 60 fps at 1080p on Legion. Keep the town small with occlusion between streets, modest shadows and limited animated foliage. A city-sized skyline and crowds add risk without improving route decisions.

## Scope and four-day gates

**Required:** single district, three parcels/planters, three transformations, current/preview map, safe return/reset, support for all delivery orders, rooftop ending, menus, Windows package/video/dev log.

**Fallback:** two destinations and four hubs, one route opening and one safe closure, simple map and same finale. Keep the idea that a delivery changes the next route. If closures consistently confuse players, make all growth additive and retain delivery-order choices through shortcut distances; acknowledge the reduced puzzle depth.

**Excluded:** vehicle physics, timed delivery scoring, procedural city, NPC schedules, combat, crafting, seed inventory sorting, physics trees, persistent campaign and multiplayer. Optional neighborhood notes and decorative plants follow a complete run.

| Gate | Deliverable | Cut decision |
|---|---|---|
| Opening session | One parcel, one delivery, route opens and another safely closes | If route states drift, solve the state model before art |
| Day 1 / build 1 | Readable district blockout, first full delivery, ending stub | Reduce town footprint if travel drags |
| Day 2 / build 2 | Three deliveries, map previews, all order permutations validated, outside playtest | Use two-destination fallback if navigation remains confusing |
| Day 3 / build 3 | Art/audio/growth feedback, recovery, video draft and insurance upload | Cut NPC detail and skyline before PLAN.md freeze |
| Day 4 | Fixes, final package and submission materials at PLAN.md times | No new routes or destinations |

## Acceptance checks and risks

Verify all eight growth-flag subsets, all six delivery permutations, wrong-seed interactions, repeated delivery input, reset during growth, return while carrying, falling after a delivery and restart after all flags are set. Check map and actual collision agree. Closure volumes must never trap or crush a player.

Walk each permanent base route after every transformation; test newly grown routes in both directions. Required street signs must remain visible after foliage changes. A fresh player should predict one opening/closure from the preview and deliberately use a new shortcut after delivery. If they ignore the map, improve world markers rather than force longer text.

Complete a full run on Legion in the Windows package and verify gamepad map focus, controls/audio, replay/quit and performance. Test actual route collision; a state flag alone is not evidence a bridge is walkable.

Main risk is repetitive walking. Keep the district compact, make shortcuts dramatically visible and shorten the run instead of adding parcels. Secondary risk is navigation confusion after growth; previews, permanent base routes and dependable Return to Depot make experimentation safe. No real delivery economy is needed.

## Presentation and reveal decision

Video: seed delivery makes a bridge grow in the first five seconds; show the same street before/after, map preview, a shortcut used on the next delivery and the final district bloom. Show gameplay choices, not a long establishing flythrough.

Glass Box story: original route graph, a confusing closure discovered in playtest, how invariant base routes prevented softlocks and the final compact layout. Keep claims about shortest routes hypothetical until measured.

At reveal, score with _config/reference/templates/scoring-rubric.md. This candidate trades Root Circuit's compact puzzles for a more cohesive place and replayable delivery order. Choose it only if route changes produce decisions within short travel distances.
