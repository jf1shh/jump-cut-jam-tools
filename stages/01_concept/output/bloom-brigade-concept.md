# Bloom Brigade — candidate game concept

Date: 2026-11-07. Status: pre-jam design proposal requested by Jared. Working title only; neither selected entry nor confirmed theme. This document creates no gameplay, levels or art. Declare the planning document as applicable; AGENTS.md, RULES.md and PLAN.md govern execution.

## Pitch

You are a little garden keeper leading a handful of round, living petals home. Call them together into a bridge, gather them around you into a bouncing seed ball, then release them to follow you again. Rescue the rest of the colony by changing the shape of the group.

**Hook:** Your companions are your traversal tools—and every rescue makes your next formation bigger.

A single-player third-person formation puzzle adventure in UE 5.8, packaged for Windows. Target 10–15 minutes, three linked garden courtyards and a final communal bloom. The creatures should look alive without requiring individual physics or sophisticated crowd AI.

## Theme, fantasy and fun bet

Connection is the act of assembling individuals into one useful structure. Growth expands the colony and unlocks longer formations. Express both through visible creature counts and physical arrangements, not only dialogue.

- Every companion remains recognizable as part of the formation.
- Switching shape feels immediate, playful and understandable.
- Rescued creatures add capability without becoming a currency you spend or lose.
- One group is easier to manage than eight independent characters.

The fun bet: seeing followers snap into a useful shape, traversing with it, and calling them back feels good in a plain test room. A bridge and ball are enough. Do not add a third formation to compensate for weak switching.

## Story and completion

A sudden dry wind scattered the nursery's eight bloomlings. The keeper begins with two. They must rescue three pairs from progressively deeper courtyards and return the group to the empty motherflower. Use chirps, body movement and a few short signs, not dialogue generation.

Each rescue opens a permanent shortcut. Once all eight reach the final court, the player calls them into a ring around the motherflower. They bloom together; the ending then returns to a clear completion menu. No companion deaths, combat, hunger or morality system.

## Controls and camera

Character-based third-person movement: WASD / left stick, mouse / right stick, Space / A jump in follower mode. E / X rescues or interacts. Q / left bumper recalls to follower mode. Left click / right trigger deploys a highlighted bridge when valid; B / right bumper toggles seed-ball mode from safe ground. R / Y holds to reset the current courtyard. Escape / Menu pauses, shows controls and music/SFX volume, and supports restart/quit.

Bridge previews snap to generous marked pads. Controller targeting chooses a pad in front of the player; no tiny creature selection. Camera follows a single leader, with a slightly pulled-back view in ball mode. Device-specific prompts show the actual action and current group count.

## Exact formation rules

### One authoritative group

The keeper owns the authoritative count and formation state. Two bloomlings begin rescued, then three rescue pairs bring the total to four, six and eight. Creature visuals are reusable actors with stable IDs. No resource is consumed by forming a bridge or ball. The whole group has one active state: Follow, Bridge, Ball or Transition.

In Follow, companions occupy a small set of trailing slots based on the keeper's recent safe path. They use gentle interpolated movement and decorative hop cycles. They do not need navigation decisions, collisions with each other, avoidance or separate rescue AI. If obstructed beyond a short grace period, regroup with a visible seed-pop at a safe slot. The group count never decreases.

### Bridge formation

Bridge pads appear in paired authored endpoints with a visible capacity label. Required counts are 2, 4 or 6. If the colony meets the requirement, preview a fixed bridge shape; confirm and the bloomlings take equally spaced visual positions along it. Extra bloomlings cluster at the supports. All companions are assigned to the formation, with one shared collision surface.

After roughly 0.7 seconds, enable that surface and permit crossing. A bridge stays until recalled or replaced. Recall is permitted only when the keeper is on static ground; show “Reach the bank first” when standing on the formation. From the far bank, recall works across the gap, so the player never has to fetch individual creatures.

One bridge may exist at a time. Deploying a different bridge first recalls the old one, provided occupancy is safe. No free placement, stacking, branching bridges or bridge rotation.

### Seed-ball formation

Unlock at four rescued bloomlings. From static ground in a valid ball area, companions cluster around the keeper into a single animated shell. The controllable body remains a single movement actor with ball tuning, not a physics pile.

Ball mode has faster acceleration and a capped speed. Crossing an authored spring ramp with sufficient speed launches the group along a forgiving arc to a broad landing. The player steers on the ground; during launch, use limited air steering and an authored landing assist. No manual jump in ball mode, avoiding an extra launch interaction. Ramp markings and a speed ring explain when a launch is ready.

Exit ball mode only at a stable landing or pad with capsule clearance. If clearance is blocked, keep the shell and explain why. The group cannot enter ball while a bridge still supports the player.

### Rescue, reset and falls

A rescue pair sits on permanent ground behind a traversal challenge. Interact to join them instantly, update the count and open the local shortcut. They never need escort pathfinding. Court completion checkpoints preserve the cumulative rescued count.

Falls return keeper and group to the last static safe marker with the last confirmed rescue count. No damage or lost companions. Reset recalls formations and returns to the current court entrance while preserving rescued pairs; completed rescue sites remain empty. Full restart clears the run after confirmation. Pause and reset cannot strand the game in Transition.

## Complete playthrough

### Court 1: Two Make a Way — 2–3 minutes

Start with two followers beside a short gap marked “2.” Deploy a bridge, cross, then recall on the opposite bank. The first rescue pair is a few steps away, increasing the visible group to four. The rescue opens a static side gate back toward the main path.

The player sees four creatures circle into the newly unlocked seed ball. A short safe practice lane has a low spring ramp and a broad grassy landing on the same platform. Teach speed, launch and exit without a deadly gap. Target first formation within 30 seconds and first rescue within 90 seconds.

### Court 2: Carry the Momentum — 3–4 minutes

A four-creature bridge reaches a static launch garden. Recall it from the far bank, enter ball, accelerate along a curved but wide lane, then take the ramp to an upper shelf. Exit on the marked landing pad and rescue the next pair, bringing the count to six.

A failed launch returns to the launch garden, not the start of court 1. The six-creature group can now span the next courtyard's longer gap. A permanent elevator or ramp opens after rescue so the return does not require a reverse launch.

### Court 3: Everyone Has a Place — 4–5 minutes

Begin with a six-creature bridge across a wider ravine. At the far static bank, recall and form ball to reach a raised garden. Exit onto the landing pad; a second six-capacity bridge reaches the final rescue pair. Recall from their island and reunite all eight.

The rescue opens a permanent return gate into the motherflower court. No newly unlocked third formation and no surprise precision section. The final ring asks the player to apply the familiar “gather together” action in a celebratory context. All eight remain visible in the ending.

### Layout and count invariants

No required bridge demands creatures located beyond itself. Every bridge has static recall banks. Every ramp has a clear run-up, safe launch and forgiving landing. Every rescue has a permanent route forward or back. Required counts progress 2 → 4 → 6; the final eight are a story payoff, avoiding a final mechanic introduced seconds before credits.

## Look, assets and audio

Look: glossy petal creatures against rough, warm garden masonry, with mint, pink and deep blue accents. This is original art inspired by the broad idea of rounded organic forms, not a copy of Epic's banner. Put eyes or a simple face on one side so companions remain recognizable when arranged.

Asset cap: one keeper shell, one bloomling mesh/material family with a few color instances, bridge pad, spring ramp, rescue nest, motherflower, modular courtyard kit and limited foliage. Reuse the same creatures across all states. Scale/squash and idle hopping give personality without skeletal animation or a nine-state creature animation project.

Each bloomling contributes a small chirp to formation assembly. Increasing group size enriches the chord. Bridge deployment has a soft sequence of landing taps; ball acceleration adds a rising flutter; rescue resolves into a clear cadence. All key state changes also have visual cues. Keep music and effects sliders and avoid constant follower chatter.

## Implementation responsibilities

During the window, build a small formation state machine in C++ with safe transitions, count thresholds and stable companion identities. Expose transition requests and success/failure reasons. Blueprint handles mesh placement, interpolation, sound, camera and UI. Do not issue eight independent pathfinding orders per frame.

Proposed actors: BP_BloomKeeper, BP_BloomlingVisual, BP_BridgePad, BP_SpringRamp, BP_RescueNest and BP_Motherflower. One formation controller owns the bridge collision surface and ball movement mode. Count changes and rescues are one-shot events. Use a fixed set of visual slots for each formation.

The ball should reuse the character's controllable movement foundation with tuned acceleration and an authored launch rather than Chaos rolling-body locomotion. Verify spring behavior in the Windows package early. Controller input and prompts must match the active state.

Maintain the repo's 60 fps at 1080p Legion target. Eight visual creatures are cheap if interpolation and effects stay modest; cap particles, avoid individual ragdolls and do not generate bridge geometry at runtime. Use existing licensed asset tooling and record provenance; no shipping art before the window.

## Scope, milestones and cuts

**Required:** follow/bridge/ball states; two-to-eight rescue progression; three courts; recall and reset; safe launch/recovery; finale; pause/controls/audio; Windows build, video and Glass Box notes.

**Fallback:** two courts, six total bloomlings, bridge only. Replace ball ramps with static ramps and make the second court about deploying a bridge, crossing, recalling and redeploying it. Lower the motherflower requirement to six. Still deliver a complete colony and ending.

**Excluded:** companion combat, individual commands, separate inventories, combat enemies, creature breeding, pathfinding squads, procedural formations, multiplayer and a third transformation. Optional decorative rescue reactions come after the full run.

| Gate | Evidence required | Scope response |
|---|---|---|
| Opening session | Two creatures follow, form a bridge and recall safely | Simplify visual movement if followers snag |
| Day 1 / build 1 | First rescue, ball practice and ending stub | Cut ball if launch/controller is unreliable |
| Day 2 / build 2 | Full run and outside playtest; all rescue counts valid | Remove court 3 and use six-creature finale if behind |
| Day 3 / build 3 | Art/audio, feedback, recovery, rough video and insurance upload | Cut unique animations and optional decoration before PLAN.md freeze |
| Day 4 | Packaged fixes and final submission materials | No new forms or count thresholds |

## Acceptance checks and risks

Attempt recall while standing on the bridge, deploy from both banks, replace a bridge, pause/reset during assembly, enter ball while a bridge exists, hit a ramp too slowly, fall while transforming, and rescue the same pair repeatedly. No case may duplicate companions, reduce the count, leave hidden collision or freeze control.

Play from a fresh run through every count threshold. Check that rescue count, visible count and formation count always agree. Verify gamepad targeting, static spawn clearance and the permanent post-rescue shortcuts. A new player should distinguish forms by purpose without reading a paragraph.

The main risk is mistaking visual followers for eight complex agents. Keep one authoritative group. The second risk is ball handling; cut it if it remains erratic after the first-day build. If switching shapes looks cute but lacks decisions, shorten travel and emphasize the cross/recall/redeploy sequence.

Measure performance and complete the entire game in the actual Windows build on Legion. Packaging alone does not verify bridge occupancy or formation input.

## Presentation and selection

Video opening: two followers become a bridge, then return to follow. Cut to rescue, four-creature ball, spring launch, longer bridge and eight-creature final bloom. Show transformations in context rather than a menu of abilities.

Dev log: why the group uses one state machine, first broken recall case, the safety fix, controller testing and the final creature-count payoff. Preserve asset generation and iteration records accurately.

At reveal, use the repo scoring rubric. This is the strongest character/silhouette candidate but has two traversal states to polish. Compare it with Root Circuit's simpler world-rewiring system before selecting; all scores remain estimates until greybox playtesting.
