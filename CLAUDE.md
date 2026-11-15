# MegaJam agent rules

@AGENTS.md

AGENTS.md has the project facts, decisions, and the MCP-caller rule. This file adds the two things
jam week needs that aren't there yet: naming and the Blueprint/C++ call.

## Naming

Epic's standard content prefixes, so assets sort and read correctly in both the Content Browser and
source control:

| Type | Prefix | Example |
|---|---|---|
| Blueprint (Actor/Component) | `BP_` | `BP_Door` |
| Widget Blueprint (UMG) | `WBP_` | `WBP_HUD` |
| Material | `M_` | `M_Hero` |
| Material Instance | `MI_` | `MI_Hero_Rust` |
| Static Mesh | `SM_` | `SM_Crate` |
| Skeletal Mesh | `SK_` | `SK_Hero` |
| Texture | `T_` + suffix (`_D` diffuse, `_N` normal, `_ORM` occlusion/roughness/metallic) | `T_Hero_D` |
| Animation | `A_` | `A_Hero_Idle` |
| Sound Cue/Wave | `S_` | `S_Door_Open` |
| Level | `L_` | `L_MainLevel` |
| Niagara System | `NS_` | `NS_Sparks` |

One master material per hero look, driven by Material Instances — the pipeline plan (asset scripts)
already assumes this for retopo/bake consistency.

## Blueprint vs C++

Blueprint stays the default for wiring, UI, level scripting and simple gameplay glue. This is a 4-day
jam: Blueprint iterates fast there, and Unreal MCP drives Blueprint graphs directly. But big Blueprint
graphs are slow for agents to build and edit over MCP, and hard to review. So:
- Logic-heavy work goes in C++: state machines, scoring and rules, procedural generation, data
  processing, anything with many branches or loops. Expose it to Blueprint with thin
  `UFUNCTION`/`UPROPERTY` hooks and wire it there.
- Editor-time tooling goes in Python editor scripts (bulk asset setup, import rules, level population).
- Also C++: a system Blueprint can't express cleanly (custom save/load, a non-trivial algorithm,
  perf-sensitive per-tick logic touching many actors), and anything the asset/QA pipeline scripts need
  as an engine-side Python/C++ hook (import rules, the QA harness's screenshot+fps capture).

Cost: C++ means a compile. Use Live Coding in the editor; the Windows build happens on the Legion.

If you drop to C++, it goes through a normal commit and review like any other code — no exception to
the one-agent-on-MCP-at-a-time rule just because the change started as a C++ edit.

Source: Epic webinar "Getting Started with MCP in Unreal Engine 5.8" (2026-09-07); owner decision
2026-11-05, see `_config/reference/research/get-ready-links-review-2026-11-05.md` (change 4).
