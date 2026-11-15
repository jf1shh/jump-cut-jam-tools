---
tier: tested
source: hub 50 real UE 5.8 run 2026-11-09 on MockSlime (superagent-sandbox/.handoff/hub50/t08-partb/REPORT.md)
updated: 2026-11-10
---

# Cheat sheet: materials through MCP (MaterialTools)

Tested on 5.8.4; re-test on 5.9 before relying on it.

Toolset `editor_toolset.toolsets.material.MaterialTools` (short `MaterialTools`). Its full describe is 26,445 chars.
Everything below was run once except where marked "listed only". `*` = required argument.

## Tip: the call chain for a flat-colour material (run, worked)
- **Why:** with only tool names, a guessing agent made 17 failed calls in 28 s and did not finish. With the
  describe output it took 6 s and 2 failed calls (n=1 each, wall clock of MCP calls only, model thinking not counted).
- **Chain:** `create_material(folder_path*, asset_name*)` -> `add_expression(material_or_function*, expression_class*, x, y)`
  -> `ObjectTools.set_properties(instance*, values)` -> `connect_to_output(expression*, output_name*, material_property*)`
  -> `recompile(material_or_function*)` -> `get_expressions(material_or_function*)` to confirm.
- **How to check:** the last call lists the expression and `get_property_input` on `MP_BaseColor` shows it connected.

## Tip: argument shapes that failed first
- References are objects: `{"refPath": "/Game/..."}`, not bare strings.
- `expression_class` is a full class path, e.g. `/Script/Engine.MaterialExpressionConstant3Vector`.
- `set_properties` takes `instance`, and `values` is a JSON STRING, not an object.
- `recompile` takes `material_or_function`. `connect_to_output` uses `material_property` such as `MP_BaseColor`.
- These do not exist (tried, failed): `new_material`, `add_node`, `add_material_expression`, `create_expression`, `connect_*` guesses.
- **How to check:** an error that lists required arguments means the shape is wrong; read it before retrying.

## Tip: the rest of the toolset (listed only, not called)
`list_expression_classes(material_or_function*, search*)`, `connect_expressions(from_expression*, from_output_name*,
to_expression*, to_input_name*)`, `disconnect_expressions`, `disconnect_from_output`, `get_expression_input_names`,
`get_expression_output_names`, `get_expression_inputs`, `get_property_input`, `delete_expression`,
`delete_unused_expressions(material*)`, `layout_expressions`, `create_function`, `create_parameter_collection`,
parameter-group tools. Also `material_instance.MaterialInstanceTools` exists (names only).
- **Why:** use nodes, not raw HLSL, unless asked (see `jam-agent-lint-rules`).
- **How to check:** `mx.py describe MaterialTools --grep NAME` prints excerpts; the cache holds the full JSON.
