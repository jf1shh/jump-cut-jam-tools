---
tier: tested
source: stages/02_build/references/editor-mcp-helper.md
updated: 2026-11-10
---

# Editor MCP helper (`mx.py`): what we verified

`scripts/mx.py` drives the Unreal editor over MCP with small output. Subcommands: `shot`, `call`, `describe`,
`toolsets`, `save`. Full page: `stages/02_build/references/editor-mcp-helper.md`. Checked against a fake MCP endpoint in
`tests/test_mx.py` and `tests/test_mx_launch.py`. *Superseded (2026-11-10):* "not yet run against the real editor"; `toolsets`, `describe`, `py`, `shot` and `step_shot` were live-smoked on the 5.9 editor on 2026-11-10 (`AGENTS.md`). `force_save_level.py` on 5.9 is unit-tested only.

## Tip: UE 5.9 (2026-11-10)
- **Why:** `describe_toolset` was removed in 5.9 (now `describe_toolsets` / `describe_tools`). `mx.py` probes `tools/list` and uses either; `mx.py py` and `mx.py shot` send a CodeBlock when the Python tool asks for one (fake-tested, live 5.9 run pending).
- **How to check:** see `jam-ue59-upgrade`. Everything below was verified on 5.8.4.

## Screenshots on the real editor (fix of 2026-11-09)

The real 5.8 editor (UE 5.8 + AllToolsets) has no arbitrary-Python tool. *Superseded (2026-11-10):* 5.9 has `PythonScriptingTools.execute_python` (see the 5.9 Tip below). The old `shot` assumed one and failed in every
mode. Tested against a fake editor with only the real tool shapes (`RealEditorShotTests` in `tests/test_mx.py`):

- **No target / viewport:** `SlateInspectorToolset.Screenshot` with `{"ref": ""}` (empty ref = the active editor
  window). Returns a base64 PNG; `shot` decodes and saves it. **Verified live (hub 50):** a 900x640 image of the
  whole editor window, with the editor UI (menus, outliner, details) around a lit viewport.
- **`location` + `rotation` (pose mode):** `EditorAppToolset.CaptureViewport` with `captureTransform` and
  `bShowUI` (false) and `"annotations": {}`. **Verified live:** a render with no editor UI (705x464 in the hub's
  run). The shape is `{location:{x,y,z}, rotation:{pitch,yaw,roll}, scale:{x,y,z}}`. **`annotations` is REQUIRED:**
  without it the editor answers `CaptureViewport input param "annotations" needs a default value` (the first
  hub advice to leave it out was wrong). `{}` is accepted, so it is always sent, and the test fake rejects a call
  without it. **Unproven:** that `{}` gives an overlay-free picture; the live `{}` render showed a grid and a label
  overlay. The pose is used for this capture only; the viewport camera does not move (the output line saying so
  was not checked on the real editor). Top-down example: `location 0,0,500`, `rotation -90,-90,0`.
- **`step_shot.py` alone** works on the real editor too: it uses the same toolset route as `mx.py` (shared
  `ProxyClient`), because the real top-level `tools/list` holds only the 3 meta-tools.
- **`actor`:** needs Python for the actor's bounds, so on the real editor it exits with a message: look the
  actor's position up (`find_actors`) and use `location`.
- **`pie`:** the same window shot as the viewport mode. It does not start PIE. If the editor has
  `EditorAppToolset.IsPIERunning` (the real one does; no args), the shot is refused with "PIE is not running" when
  it says false; with no such tool the output says `PIE state UNCHECKED`. Start PIE yourself first.
- **`width` / `height`** are ignored on the real editor (neither tool takes a size); the output line says
  "width/height not supported by <tool>" when you pass them.
- **Doubled tool name bug:** describe lists tools as `Toolset.Tool`; `call_tool` adds the toolset itself, so the
  helper now sends the bare name (`Screenshot`). Before, the editor answered
  `Unknown tool SlateInspectorToolset.SlateInspectorToolset.Screenshot`.
- Never use `spectacle` as a fallback by default: it captures the whole desktop.

## Tips

- **Describe only real toolset names, and remember failures.** The real editor lists only three top-level tools
  (`list_toolsets`, `describe_toolset`, `call_tool`); the real tools sit inside toolsets. To find a screenshot or
  Python tool, `shot` has to describe the toolsets. The `list_toolsets` text also holds prose words that look like
  names (`e.g`, `Engine.Actor`). Each wrong name costs a failed `describe_toolset` on the editor's game thread, and
  without a negative cache it was re-asked on every call (r3 review). `mx.py` writes `$STATE/describe/<name>.fail` for a
  rejected name (`$STATE` = `<root>/url-<10 hex>`: `<root>` is `$MX_DIR`, else `$CLAUDE_JOB_DIR/mx`, else `./work/mx`;
  `url-<10 hex>` is the first 10 hex digits of the SHA-1 of the editor URL, so each editor has its own cache) and skips it from then on. Read all toolsets before choosing a tool: the screenshot tool and the
  Python tool can sit in different ones.
- **The helper lives outside the project checkout.** `launch-editor.sh` copies `mx.py`, `mcp_call.py` and
  `step_shot.py` from the repo to `~/.local/state/megajam-mx/` on every launch. It never uses a job tmp dir (lost on
  each handoff) and never the project folder: the editor watchdog snapshots the project with `git add -A`, which
  would commit the helper and its `__pycache__` into the entry's history.
- **Keep agent output compact.** `call` prints at most 800 chars (`--max-chars`, 0 = no cap; `--save PATH` keeps
  the whole result), errors at most 300 chars plus the tool's required params from the cached describe, and
  `describe` prints tool names or `--grep` hits only. A describe plus ten calls stays under 10K chars of context.
  Read saved results with `peek --grep` or `jq`, never `cat`. `mx.py save` sends `{"asset_paths": []}`: this
  server wants the key even when the list is empty.

## Tip: UE 5.9 helper traps seen in mock 15 (2026-11-10)
- **Why:** mock 15 (`mock-jam-findings-15.md:92-95,149-163`) found five breaks on 5.9. Tooling was fixed after some, and `AGENTS.md` (later that day) says `shot` and `step_shot` (STEP_SHOT_OK) passed a live smoke, so the later evidence wins for those two. Still worth knowing:
  - `mx.py save` calls the old toolset name `AssetTools` (gone on 5.9; not fixed in that PR). Use `unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)`.
  - `step_shot --pie` shot the editor world, not PIE. Use `unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename="..."')`.
  - `CaptureEditorImage` returns a resource URN on 5.9, so the mock 14 capture method is dead.
  - `STEP_SHOT_OK` appeared only in `LogPython` in mock 15, so do not grep stdout for it.
  - `mx.py py SCRIPT` takes code, not a path; use `mx.py py - < file`.
  - `-ExecCmds="py f.py; quit"` passes `; quit` into Python; end the script with `unreal.SystemLibrary.quit_editor()` (`asset-test-ue59-2026-11-10.md:43`).
- **How to check:** run the helper once on the 5.9 editor before the window; if a command fails, switch to the workaround above.

## Tip: a background editor is throttled; a shot that never lands needs realtime on
- **Why:** after StopPIE and `load_level` the viewport shot timed out ("no PNG appeared within 30s"); the editor was throttled to about 3 fps. `editor_set_viewport_realtime(True)` fixed it (`mock-jam-findings-15.md:154`). `step_shot --actor` also needs `--distance` for small actors.
- **How to check:** if a shot times out, turn realtime on, then retry once.
