---
tier: community
source: stages/00_prep/output/mock-jam-findings-11.md
updated: 2026-11-10
---

# Mock jam 11 traps seen once, not re-tested

Each item below was seen once in mock jam 11 and not re-tested, so treat it as a lead, not a fact. Confirm it before relying on it.

## Tip: `merge_actors` prefixes the new mesh name with `SM_`
- **Why:** merging Flag and Pinwheel gave `SM_SM_Flag` (tool gap 4). Seen on that one merge only.
- **How to check:** read the new asset name with `list_assets` right after the merge; rename it if it is doubled.

## Tip: a component edit on a Blueprint CDO does not reach an already placed instance
- **Why:** the placed actor kept its old value (tool gap 10). Seen once; other component properties not tried.
- **How to check:** set the value on the level actor too, then read the placed actor's component, not only the Blueprint's.

## Tip: `save_assets` can write nothing after `set_pin_value` + `compile_blueprint`
- **Why:** it returned true and logged "All files are already saved", yet the `.uasset` md5 was unchanged (tool gap 23). The blueprint was not marked dirty. `AssetTools.update_metadata_tags` on the asset marked it dirty and then `save_assets` wrote it. Seen on BP_Kid and BP_HUD edits in that run only.
- **How to check:** `AssetTools.is_dirty` before saving, and md5 the file after.
- *Update (2026-11-10):* mock 10 saw the same thing (`mock-jam-findings-10.md:92`), so it is confirmed twice and now lives in `jam-mcp-tool-traps` (tested).

## Tip: `montage` of more than 12 frames splits into `-0` and `-1` files
- **Why:** a single expected output file was not there (tool gap 17). The "keep it to 12 frames or fewer" advice is untested.
- **How to check:** list the output folder after the run and read both numbered files. The playtest gate doc points here.

## Tip: a scaled mesh can read wrong while `asset_preview` says ok
- **Why:** the balloon mesh was 1.5x wider than tall; a non-uniform scale (2.2, 2.2, 4.6) fixed it, and the level instance kept the old scale until it was set on the actor (`mock-jam-findings-11.md:34`). Seen once.
- **How to check:** read the bounds numbers, not only the preview picture, and set the scale on the level actor.
