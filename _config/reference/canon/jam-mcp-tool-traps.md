---
tier: tested
source: stages/00_prep/output/mock-jam-findings-5.md, stages/00_prep/output/mock-jam-findings-10.md, stages/00_prep/output/mock-jam-findings-11.md, stages/00_prep/output/mock-jam-findings-12.md, stages/00_prep/output/mock-jam-findings-14.md
updated: 2026-11-10
---

# Unreal MCP tool traps we hit ourselves

Tested on 5.8.4 except where a Tip says 5.9; re-test on 5.9 before relying on it.

Only items found in our own mock jams (5, 7, 9, 11) and the MCP smoke test. Mock 11 items we saw only once and did not re-test are in `jam-mcp-mock11-unconfirmed-traps`. Forum-only traps are in `jam-mcp-forum-traps`.

## Tip: UE 5.9 (2026-11-10)
- **Why:** on 5.9, `execute_python` wants `{"script":{"Content":...,"Language":"Python"}}`; a plain string fails to import. The last expression is returned and `print` goes to `LogPython`. Observed 2026-11-10.
- **How to check:** see `jam-ue59-upgrade` for the other 5.9 changes (toolsets off by default, `call_tool` argument shape; Epic and source, not run here). The traps below were found on 5.8.4.

## Tip: verify graphs with a second read
- **Why:** MCP can report success on a step that did not land; the smoke test re-read every step with `get_node_infos`.
- **How to check:** after wiring a Blueprint, read it back (`get_node_infos` or `read_graph_dsl`) and confirm pins and values.

## Tip: `read_graph_dsl` wants a direct graph path
- **Why:** the `graph` param is an EdGraph path, e.g. `/Game/X/BP_GameMode.BP_GameMode:EventGraph`. The
  `{blueprint, graph}` form errors. Widget Blueprints use no `_C` suffix in that path.
- **How to check:** the error text names the bad path. Copy the form above.

## Tip: DSL node ids drop the `b` prefix on bool variables
- **Why:** a variable `bTriggered` gives nodes `Variables|Default|GetTriggered` and `SetTriggered`.
- **How to check:** `find_node_types` with a filter like `Triggered`.

## Tip: param names are inconsistent between tools
- **Why:** e.g. `StaticMeshTools.get_material_slots` takes `mesh`, not `staticMesh`.
- **How to check:** read the parameter error, it names the right key.

## Tip: use the sanctioned import path, not an MCP-native import
- **Why:** see `jam-import-and-materials`. A geometry-only MCP import produced flat grey meshes.
- **How to check:** run `scripts/ue_import_asset.py` with its PBR assertion on.

## Tip: there is no MCP "save all"; a `HUDClass` edit needs both blueprints recompiled
- **Why:** mock 11 saved with `AssetTools.save_assets` per asset, then confirmed with `stat` on the file (the level's mtime moved). After `HUDClass` was set on the game mode, the HUD text stayed missing in PIE until both `BP_HUD` and `BP_Game` were recompiled; it showed after that.
- **How to check:** `stat` or md5 the `.uasset`/`.umap` before and after the save. For the level, `scripts/force_save_level.py` exists (see `jam-force-save-level`). For a `HUDClass` edit, `compile_blueprint` both blueprints, then run PIE.

## Tip: `write_graph_dsl` rejects `read_graph_dsl` output when the graph has a cast pin
- **Why:** re-applying a read graph failed with "Could not connect pin AsBP Kid to UpdateContext", so there is no round trip for such graphs. The argument is `code`, not `dsl`. Mock 11 edited the literals with `find_nodes` + `get_node_infos` + `set_pin_value` instead, and that worked.
- **How to check:** edit the node by MCP calls, not by DSL round trip, then read the graph back.

## Tip: after `set_pin_value` the Blueprint is not dirty (confirmed in mocks 10 and 11)
- **Why:** `save_assets` says "All files are already saved" and the file md5 stays the same (`mock-jam-findings-10.md:92`, `mock-jam-findings-11.md:121`). Two mocks saw it, so it is no longer a single-run lead. The older note is `jam-mcp-mock11-unconfirmed-traps`.
- **How to check:** `AssetTools.is_dirty` before saving; nudge with `update_metadata_tags`, save, then md5 the file.

## Tip: never create a Blueprint with parent class `Blueprint`
- **Why:** `BlueprintTools.create` with `asset_type=/Script/Engine.Blueprint` opens a modal that freezes the game thread and MCP (`mock-jam-findings-12.md:54`). It cost mock 12 about 3 h with the 8010 hang.
- **How to check:** always pass the real parent (Actor, Pawn, ...). If MCP hangs, look for a modal on the editor window.

## Tip: save after every Blueprint or asset step, then commit
- **Why:** unsaved Blueprint work dies with a killed editor: mock 10 lost a whole rebuild (`mock-jam-findings-10.md:42`), mock 12 about 20 min of `BP_Slime` (`mock-jam-findings-12.md:54`).
- **How to check:** after each step run `AssetTools.save_assets` for what you touched, md5 the file, commit.

## Tip: placing actors: set transform, Mobility and collision yourself
- **Why:** `add_to_scene_from_asset` silently ignores `translation` and `scale3D` (all actors at the origin). Use `ActorTools.set_actor_transform`. StaticMeshActors from `add_to_scene_from_class` are Static: physics and scale do nothing until `Mobility` is Movable. A physics Body's skin child needs `collisionEnabled=NoCollision` (`mock-jam-findings-10.md:48-49`; `mock-jam-findings-14.md:24`).
- **How to check:** read one placed actor's location and mobility back after the call.

## Tip: design for the Blueprint DSL's weak spots
- **Why:** statements after a bare `(if ..)` wire only to the true branch, so use one function per mechanic and call them flat from Tick (`mock-jam-findings-13.md:47`, `mock-jam-findings-14.md:10`). `write_graph_dsl` only adds nodes, so rebuild a Blueprint to change code (`mock-jam-findings-14.md:23`). A variable must be instance-editable before you set it on an instance. `(* a b c)` takes two args (`mock-jam-findings-10.md:51`). `BP_GameMode` CDO properties revert unless compiled after `set_properties` (`mock-jam-findings-12.md:55`).
- **How to check:** keep state in level-placed actors found by tag; read each graph back after every write. On 5.9: else nests inside elif, a positional arg may not follow a keyword arg, and a member call needs `:self` (`mock-jam-findings-15.md:161-163`).
