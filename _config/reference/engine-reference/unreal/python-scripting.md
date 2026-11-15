# Unreal Engine 5.8 — Python Scripting & Headless Import

**Last verified:** 2026-11-10 (5.9 section only); 2026-10-28, live-tested against UE 5.8 (Linux editor) via `~/Projects/ue-mcp-verify`,
using `UnrealEditor-Cmd <uproject> -ExecCmds="py <path>" -unattended -nosplash -stdout -FullStdOutLogOutput`.

## UE 5.9 (5.9.0-preview-1)

Live-tested 2026-11-10 with the 5.9 editor on a copy of a mock project (Linux, KDE Wayland). Everything in the 5.8 sections below was written for 5.8 and has not been re-run on 5.9 unless a line here says so. Full tagged list: `ue59-release-notes.md`.

- **Editor start on Linux:** under Wayland the editor only starts with `SDL_VIDEODRIVER=x11` `[observed]`. The `-sdlvideodriver=x11` flag (already in 5.8.4) should work too but was not run `[source]`.
- **MCP `execute_python`** (toolset `PythonScriptingTools`) takes `{"script":{"Content":"<python>","Language":"Python"}}` through `call_tool`'s `arguments`, and returns the value of the last expression. `print()` goes to `LogPython`, not to the tool result. `[observed]`
- **Rules from Epic's docs:** imports must be at the top level and `from x import *` is rejected before the script runs; a final `await` returns the awaited value; inside a script, `await call_tool(full_tool_name, **arguments)` calls other tools and checks the result against its output schema; for many edits send one script, not many calls. `[docs]`
- **Companion tools:** `read_me` (once per conversation), `get_symbol`, `search_symbols`, `grep_stubs`. `[observed]`
- **New in the engine:** `IPythonAdditionalPaths` (extra search paths), wrappers for InstancedStruct, PropertyBag and Variant, a `PythonScriptPluginTests` runner `[source]`; Blueprint / Python libraries to edit Blueprints, chooser tables, StateTrees and Dataflow graphs, and a Slate Qt Bridge for PySide6 (not found in the diff) `[notes-full]`. Bundled Python stays 3.11. `[source]`
- **Known crashes:** Python Blueprint root swaps (UE-411502: use a C++ base class that owns the root) and undo after scripted Deformer Graph additions (UE-410941). `[forum]`
- **Not re-tested on 5.9:** the headless `-ExecCmds="py <path>"` route below.

## Running a Python script headlessly

- `-ExecutePythonScript="<path>"` does **not** work on this build/config: the editor loads and exits
  cleanly but produces zero `LogPython` output, no error either. Root cause not determined (may need
  the Python plugin's "startup scripts" project setting). Don't rely on this flag.
- `-ExecCmds="py <path>"` works: `Cmd: py <path>` and `LogPython: ...` lines appear in the log.
- **Correction, live-tested twice, 2026-10-28:** `-ExecCmds="py <path>; quit"` does **not** work for
  `py` specifically, even though `-ExecCmds` entries are semicolon-separated in general. The `py`
  command consumes the *entire rest of the string*, including `; quit`, as Python source — both
  attempts threw `SyntaxError: invalid decimal literal` trying to eval the literal text
  `/path/to/script.py; quit`. There is no working in-line way to chain a `quit` after `py` in the
  same `-ExecCmds` value. Use `-ExecCmds="py <path>"` alone and rely on `timeout` + `pkill` (next
  bullet) for shutdown — this corrects the previous version of this line, which had never actually
  been tried in-session before 2026-10-28.
- **Working shutdown, live-tested 2026-11-02:** end the script itself with
  `unreal.SystemLibrary.quit_editor()`. `UnrealEditor-Cmd <uproject> -ExecCmds="py <path>"` then exits 0
  by itself in about a minute. (`-ExecCmds="py <path>,quit"` does log `Cmd: quit`, but the editor keeps
  running until `timeout` kills it; `py <path>; quit` passes `; quit` to the script as argv.)
- **Gotcha, live-tested 2026-10-28:** a **comma** inside a `-ExecCmds="..."` value is also unsafe,
  separately from the semicolon point above — UE's own command-line parser splits on comma too, even
  though the shell has the whole `-ExecCmds="..."` value correctly quoted as one argument. Confirmed
  by passing a script a comma-joined list (`--maps /Game/A,/Game/B`): everything after the first
  comma was silently dropped, including unrelated later flags like `--out-dir`, and the script's own
  `argparse` failed with a missing-required-argument error that had nothing to do with the actual
  bug. If a script needs to take a list via `-ExecCmds`, use a repeated flag (`--map A --map B`) or
  another non-comma delimiter, never a bare comma-joined string.
- Reliable pattern used repeatedly: wrap the invocation in `timeout <N> ...` and `pkill -9 -f
  "UnrealEditor-Cmd.*<project>"` right after, rather than depending on an in-script quit. Always
  verify with `ps aux | grep -i UnrealEditor` after any headless run.

## Importing a .glb via AssetImportTask / Interchange

- `unreal.AssetImportTask` + `AssetToolsHelpers.get_asset_tools().import_asset_tasks()` on a `.glb`
  **does** route through Interchange in 5.8 — material, textures and static mesh are all created.
- The Interchange glTF pipeline does **not** honor `destination_path` as the flat final folder. It
  nests output under `<destination_path>/<source_glb_basename>/StaticMeshes/<destination_name>`
  (and `.../Materials/`, `.../Textures/`), e.g. `/Game/Props/pipeline_test_crate2/StaticMeshes/SM_Crate3`,
  not `/Game/Props/SM_Crate3`. `destination_name` (the leaf name) **is** honored.
- Never assume the final asset path from `destination_path` + `destination_name`. Resolve it from the
  task's `imported_object_paths` property and load each entry to find the actual `StaticMesh`/
  `SkeletalMesh`.

### Verifying the import actually got materials

Mock jam 5 shipped a mesh with no real textures because the import step did not go through this
Interchange path at all — it most likely went through a different, MCP-native import tool that only
pulls in geometry (root-caused in `stages/00_prep/references/mock-jam-6-tooling-plan.md` Phase A). This script alone being
correct does not guarantee every future import uses it. Two independent checks now guard against a
repeat:
- `scripts/ue_import_asset.py`'s own `_assert_real_material()` (on by default, `--no-require-pbr` to
  opt out for a deliberate greybox) fails loudly right after import if no material has a bound
  texture parameter.
- `scripts/qa_harness.py`'s material/texture validation check (`stages/00_prep/references/mock-jam-6-tooling-plan.md`
  Phase B) catches the same signature independently, regardless of which tool performed the import.

## Collision

- `unreal.ScriptingCollisionShapeType` in 5.8 has **no** `CONVEX` or `CONVEX_DECOMPOSITION` member
  (both resolve to `None` via `getattr`). Only `NDOP18` exists among the options tried.
- `unreal.EditorStaticMeshLibrary.add_simple_collisions()` works given a real, non-null mesh with
  `NDOP18`. It returns the new shape's index, or -1 when the engine built nothing. In 5.9 the same call
  lives on `StaticMeshEditorSubsystem` (the library is deprecated but still answers).
- **`get_simple_collision_count()` never counts convex hulls** (UE 5.9 source:
  `StaticMeshEditorSubsystem.cpp` `GetSimpleCollisionCount` sums only box, sphere and capsule elements).
  NDOP18 and Interchange's import collision are both convex hulls, so it reads 0 on a mesh that has
  collision. Count `get_simple_collision_count() + get_convex_collision_count()`, or read
  `body_setup.agg_geom.convex_elems`. LIVE-VERIFIED 2026-11-11 (UE 5.9, scratch AssetTest59): Poly Haven
  crate parts read simple=0, convex=1 after import, save and a fresh-process reload; Nanite on, 4 LODs.
- Interchange (5.9) already gives each imported static mesh one convex hull. `ue_import_asset.py` keeps
  it (`collision=kept(import) shapes=1`) and adds NDOP18 only when the mesh has none; before 2026-11-11
  it always added one, so older imports carry 2 overlapping hulls (harmless).

## LOD / rebuild after setting LODGroup

- `unreal.StaticMesh` has **no** Python-exposed `post_edit_change()` in 5.8 (raises
  `'StaticMesh' object has no attribute 'post_edit_change'`).

## Frame time / FPS measurement (see scripts/qa_harness.py)

- `unreal.AutomationLibrary.get_stat_inc_average(<name>)` returned `0.0` for every candidate stat
  name tried (`FrameTime`, `Frame`, `Unit`, `GameThreadTime`, `RenderThreadTime`, `GPU`), even after
  real frames had ticked. The exact stat name it expects is still unconfirmed — don't trust this API
  for frame timing without finding the right name first.
- What works instead: `unreal.register_slate_pre_tick_callback(fn)` fires `fn(delta_seconds)` once
  per **real** engine frame (confirmed live: 20 frames measured, ~0.0256s avg on a cold headless
  editor). Averaging `delta_seconds` over N ticks gives frame time directly with no stat-name
  dependency. Unregister with `unreal.unregister_slate_pre_tick_callback(handle)` when done.
- **Critical gotcha:** a one-shot `py <path>` script runs synchronously on the game thread and does
  **not** itself advance frames — real frames only tick once the script returns control to the
  editor's own loop. Blocking inside the script (e.g. a `time.sleep()` polling loop waiting for the
  tick callback to fill a buffer) blocks that same game thread the ticks need, so the callback never
  fires and the wait times out. The script must register the callback and return immediately,
  letting the actual work happen across later real ticks (a small state machine inside the callback,
  as in `scripts/qa_harness.py`) — this applies to any one-shot headless Python script that needs
  more than one frame to elapse, not just frame timing.
- Correct 5.8 API (found by live-probing `dir(unreal.StaticMeshEditorSubsystem)` in the editor):
  `unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).set_lod_group(static_mesh,
  "SmallProp")`. This both sets the LODGroup and triggers the rebuild — use it instead of
  `static_mesh.set_editor_property("lod_group", ...)` + `post_edit_change()`.
