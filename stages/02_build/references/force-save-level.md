# Force-save the level before every package step

**Rule: no package step (gate build, nightly build, final build) without a `VERIFIED` line from
`scripts/force_save_level.py` in the same session.**

## Why

Mock jam 10 (2026-11-08, PR #97, "Playable gate failure"): level edits made through the Unreal MCP were
never written to the `.umap`. `save_assets` answered "already saved" because it skips packages it believes
are clean. The packaged build shipped the old junk level. The workaround that worked was duplicating the map
with `AssetTools.duplicate_asset`, which forces a write.

The editor's answer is not proof. The file on disk is.

## Run it (lead agent, live editor, MCP on port 8010)

```bash
cd ~/Projects/megajam
python3 scripts/force_save_level.py --expect-actor <a label you just placed> --expect-actor <another>
```

Optional: `--level /Game/Maps/L_Main` (default: the open level), `--umap PATH` (default: the editor reports
it), `--asset /Game/UI/WBP_HUD` (force-save extra assets), `--python-tool NAME`, `--list-tools`.

`--level` must be the level that is already open; any other value is refused (the save and reload act on the
open level only). Open the level you want first.

What it does:

1. Reads the open level (path, actor count, file) and hashes the `.umap` on disk, each `--asset` file, and the
   level's `__ExternalActors__` folder (One File Per Actor: placed actors live there, not in the `.umap`).
2. Marks the level and every external actor package dirty and force-saves them (`only_if_is_dirty=False`),
   saves the level, saves all dirty packages, force-saves each `--asset`.
3. Checks the disk: the `.umap` exists, starts with the Unreal package header, mtime is newer, hash is
   different; the same for every `--asset` file and for the `__ExternalActors__` folder (which must hold at
   least one file per external actor). The editor's "saved" answer is never trusted. If any check fails the
   script stops here and does NOT reload, because a reload would throw away the unsaved edits.
4. Reloads the level fresh (empty map, then the level) and requires the same actor count as before the save
   plus every `--expect-actor` label.

Exit 0 and a `VERIFIED ...` line means it is safe to package. Exit 1 (`NOT VERIFIED`) means do not package.
Exit 2 means a usage error or the editor is unreachable.
`--allow-unchanged` only relaxes the "contents are different" check, for when you made no edits on purpose
(for example a re-package of the same level). The file's mtime must still move, so a save that wrote nothing
still fails. Any editor note such as "returned False" also fails the run. The reload never runs unless every
disk check passed, and it checks that `new_level` / `load_level` worked and the same level came back.

If the editor lacks `Actor.is_package_external`, the script prints a `warning from editor` line, treats every
actor as possibly external and hashes `__ExternalActors__` anyway. Tell the hub; step 6 below is how to fix it.

## If it says NOT VERIFIED

1. "mtime did not move" or "identical": run it once more. If you also see a "warning from editor" line, read it.
2. Still failing: escalate by hand, in the editor Python tool:
   ```python
   import unreal
   unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset("L_Main_tmp", "/Game/Maps", unreal.load_asset("/Game/Maps/L_Main"))
   ```
   The duplicate is a forced write of the current in-memory level. Then rename or move it over the original
   in the Content Browser (or copy the new `.umap` file onto the old one with the editor closed), delete the
   `_tmp` leftovers, and run `python3 scripts/force_save_level.py --verify-only --expect-actor <a label you placed>`.
   It does not save (the copy happened before the run, so no mtime can move during it). It checks the `.umap`
   header and reloads the level to prove the edits are in the file.
3. Never package until you have a `VERIFIED` line.

## Real-editor check (hub, once, before relying on it)

No UnrealEditor ran for the ticket that wrote this (guard), so the in-editor Python is untested against a
real 5.8 editor; only the fake-editor tests in `tests/test_force_save_level.py` ran. Check it once:

1. Launch the editor with MCP (runbook step 2). Open a scratch level.
2. `python3 scripts/force_save_level.py --list-tools` shows a python tool (not NONE).
3. Place one actor through MCP, label it `ForceSaveProbe`. Do NOT save.
4. `python3 scripts/force_save_level.py --expect-actor ForceSaveProbe` prints `VERIFIED`.
5. `ls -l` and `sha256sum` the `.umap` before and after; both must change.
6. Confirm the unverified API names in `PROBE_SCRIPT` / `SAVE_SCRIPT` / `RELOAD_SCRIPT` exist in 5.8:
   `EditorAssetLibrary.save_loaded_asset`, `LevelEditorSubsystem.save_current_level` / `new_level` /
   `load_level`, `EditorLoadingAndSavingUtils.save_dirty_packages` / `save_packages`, `Actor.is_package_external`,
   `Object.get_package`, `Paths.project_content_dir` / `file_exists` / `combine`, `PackageName.long_package_name_to_filename`.
   A missing name shows up as a `FORCE_SAVE_ERROR AttributeError` line; fix the script, then update this page.
7. Reload caveat: `new_level("/Temp/ForceSaveScratch")` may prompt about unsaved changes in some builds. If
   the editor blocks, that is itself a sign the level was still dirty after the save.

Record the result in `stages/05_devlog/output` and delete this checklist's "untested" wording once it passes.

Tests: `python3 -m unittest tests.test_force_save_level`.
