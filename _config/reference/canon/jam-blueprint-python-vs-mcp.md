---
tier: tested
source: stages/00_prep/output/mock-jam-findings-2.md
updated: 2026-11-06
---

# Building Blueprints: Python versus Unreal MCP

## Tip: do not build Blueprint event graphs from headless Python
- **Why:** on UE 5.8.4, three probes showed `get_editor_property("UbergraphPages")` is protected and
  `BlueprintEditorLibrary` has no way to add or find event nodes. A Python-registered `UClass` (via
  `@unreal.uclass()`) also does not survive packaging, so it worked only for an in-editor scripted run.
- **How to check:** try the call once on a scratch Blueprint before planning around it.

## Tip: live Unreal MCP can wire a Blueprint end to end
- **Why:** the follow-up smoke test built `BP_TestActor` with `BlueprintTools.create`, `add_event` (BeginPlay),
  `create_node` (PrintString), `connect_pins`, `set_pin_value`, `compile_blueprint`, and every step was
  re-read with `get_node_infos`.
- **How to check:** re-read the compiled graph. Hand-building a few core Blueprints in the GUI is still
  the safer default (MCP calls are serial and can be slow).

## Tip: use Python for data, MCP or the GUI for graphs
- **Why:** Python is good at variable defaults, asset wiring and level dressing.
- **How to check:** if a Python step needs a graph node, move it to MCP.
