# Editor MCP helper: `mx.py`

One script to drive the Unreal editor over MCP without flooding your context. Source: mock 11 observer
(`work/mock11-observer.md` sections 2 and 6): every session rewrote its helper from a lost job tmp dir
(3-4 min each) and one burned 139K context, ~45K chars of it re-sent helper heredocs and ~91K chars of
schema and probe dumps.

## Where it is

`scripts/mx.py` in this repo (it uses `scripts/mcp_call.py`, and `scripts/step_shot.py` for `shot`).
`scripts/launch-editor.sh` copies all three to `~/.local/state/megajam-mx/` on every launch. That folder is
outside the project on purpose: the project is a git repo that the watchdog snapshots with `git add -A`, and
the helper must not land in the entry's history. `MX_DEST=/abs/dir` changes the folder, `MX_DEST=none` skips it. Never copy a helper from a job tmp dir; never rewrite it.

```bash
python3 ~/.local/state/megajam-mx/mx.py --help      # gotchas are in the help text
```

## Commands

| Command | What it does |
|---|---|
| `mx.py toolsets [--grep RE]` | `list_toolsets`, cached. Run once; short names like `BlueprintTools` then work. |
| `mx.py describe TOOLSET [--grep RE] [--refresh]` | `describe_toolset` once, cached at `$STATE/describe/<toolset>.json` (`$STATE` is per editor URL, see below). Prints tool names, or only the lines matching `--grep`. |
| `mx.py call TOOLSET TOOL '{"a":1}' [--save PATH]` | `call_tool`. Prints at most 800 chars (`--max-chars N` to change, 0 = all). `--save` keeps the full result. |
| `mx.py save` | `AssetTools.save_assets` with an empty list (save everything dirty). |
| `mx.py shot LABEL '{"actor":"SM_Crate"}'` | Screenshot through `step_shot.py`; prints the PNG path. Options: actor, location, rotation, distance, azimuth, elevation, pie, viewport, verdict, outdir, width, height. Also `--outdir DIR`. Modes on the real editor (no Python tool): **no target or `{"viewport":true}`** = the whole editor window, about 900x640, with the editor UI in the picture. **`{"location":"X,Y,Z","rotation":"P,Y,R"}`** = a render from that pose, no editor UI (a grid/label overlay may still show); it does not move the viewport camera. **`{"pie":true}`** = the same window shot; it does not start PIE, but is refused when `IsPIERunning` says PIE is off. `width`/`height` are ignored (said in the output). **`{"actor":..}`** is refused (needs Python; use `location`). `--help` lists these. `step_shot.py` alone now takes the same route. See `_config/reference/canon/jam-editor-mcp-helper.md`. |

`$STATE` is `<root>/url-<10 hex>`: `<root>` is `$MX_DIR`, else `$CLAUDE_JOB_DIR/mx`, else `./work/mx` (relative to the
current directory), and `url-<10 hex>` is the first 10 hex digits of the SHA-1 of the editor URL in use (`--url`, else
`MEGAJAM_MCP_URL`, else the default). So each editor gets its own cache and one editor's cache is never reused for
another. `step_shot.py` run alone uses the same folder. Add `--url http://127.0.0.1:PORT/mcp` (or
`MEGAJAM_MCP_URL`) if the editor is not on 8010.

## Context rules

- A bad call prints at most 300 chars of the error, then the tool's required and optional params from the cached
  describe. Fix the call from that line; do not re-describe.
- To read a saved result use `peek --grep RE FILE` or `jq`, never `cat`.
- A describe plus ten calls costs under 10K chars of context (checked by `tests/test_mx.py`).

## Gotchas (also in `--help`)

- The server has three top-level tools: `list_toolsets`, `describe_toolset`, `call_tool`. `describe_toolset`
  takes `toolset_name`, not `toolset`.
- `exec_tool_script` only calls toolset tools. It does not run arbitrary Python.
- `add_variable` types: `bool`, `int`, `float`, `Vector`.
- `set_properties` `values` is a JSON string. `get_properties` on a CDO needs `get_default_object` first.
- DSL events are `EventTick` and `EventReceiveDrawHUD` (`add_event` first). Sin is `Math|Trig|Sin(Degrees)`.
- There is no MCP save-all; `mx.py save` is it. `merge_actors` prefixes names with `SM_`.

Only the lead agent calls Unreal MCP (AGENTS.md); the helper does not change that.
