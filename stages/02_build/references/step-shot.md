# step_shot: look at every step

Owner rule (2026-11-08, #1 priority): check each asset and step visually. Mock jam 10 shipped a
non-playable build because nobody looked. `scripts/step_shot.py` makes looking cheap: one command
frames the editor viewport, saves a PNG, and logs it. The lead agent then **Reads the PNG and writes
a verdict**.

## When

After EVERY build step in the editor: an asset imported, a mesh placed, a material applied, a light
changed, a Blueprint wired, a level section finished, PIE started. Not at the end of the day. A step
with no shot and no verdict is not done.

Only the lead agent calls Unreal MCP (AGENTS.md), so only the lead runs this.

## How

```bash
cd ~/Projects/megajam   # or your worktree
# 1. frame a named actor and shoot (label or object name; exact match first, then substring)
python3 scripts/step_shot.py --label crate-placed --actor SM_Crate
# 2. then Read the printed PNG path, and record what you saw
python3 scripts/step_shot.py --verdict "crate sits on floor, texture correct"
```

Targets (pick one with `--label`):

| Flag | What it shoots |
|---|---|
| `--actor NAME` | Moves the editor camera to look at the actor. `--distance`, `--azimuth` (default 200), `--elevation` (default 20) tune the angle. |
| `--location X,Y,Z [--rotation P,Y,R]` | Camera at a spot (Unreal units, degrees). |
| `--pie` | The Play-In-Editor player view. Camera untouched. Fails if PIE is not running (needs the Python tool to check). |
| `--viewport` | The viewport exactly as it is now. |

Other flags: `--verdict TEXT` (with `--label`: stored on the new shot; alone: stored on the last
shot, no editor needed), `--outdir` (default `work/step-shots`, or `MEGAJAM_STEPSHOT_DIR`),
`--width/--height` (1920x1080), `--editor-ui` (keep gizmos; default is a clean game view),
`--settle` (seconds between camera move and shot, default 0.7), `--wait` (seconds for the PNG to
appear, default 30), `--url` (default `http://127.0.0.1:8010/mcp`, or `MEGAJAM_MCP_URL`).

Output: `<outdir>/NN-<label>.png` (NN counts up from the highest existing), its absolute path on
stdout, and a row appended to `<outdir>/steps.md`:

```
| NN | label | path | verdict |
| 03 | crate-placed | /…/work/step-shots/03-crate-placed.png | (pending) |
```

`(pending)` means nobody has judged it yet. Clear every pending row before moving on. Copy the
folder (or the best shots) into the dev log; `steps.md` is raw Glass Box material.

Exit codes: 0 ok, 1 editor reported a failure or no PNG appeared, 2 usage error (bad `--label`,
`--location`, `--rotation`; checked before any editor call), editor unreachable, or no usable editor tool.

A shot that fails after the editor was reached still takes a number and gets a row
(`| (no file) | FAILED: reason |`), so numbering and the log never drift; a bare `--verdict` then lands
on that row. The editor writes to a per-attempt `.pending-…png` name that is renamed to `NN-<label>.png`
only when it arrives, so a late file from an earlier failed try is never taken for a new shot. A bare
`--verdict` refuses to overwrite a row that already has a verdict unless you add `--replace`.

## Which editor tools it uses

`step_shot.py` reads the live `tools/list` and picks by name; nothing is hardcoded to Epic's plugin.

- **Python tool** (preferred): the first tool named `execute_python`, `editor_run_python`,
  `run_python`, `python_exec` or `exec_python`, else a tool whose name contains `python` AND whose schema
  has a string code argument (so a python-docs search tool is skipped). If a name-picked Python tool never
  reports back and a screenshot tool exists, a no-framing shot falls back to the screenshot tool. Markers are
  found inside JSON or `LogPython:` wrappers too; a marker followed by a closing quote is an echo of the
  source and is ignored. The code argument
  is `code`, `script`, `python_code`, `python`, `command` or `source` (first found in its schema).
  Two calls per shot: (1) frame the camera with `UnrealEditorSubsystem.set_level_viewport_camera_info`
  (actor bounds from `EditorActorSubsystem`), (2) after `--settle`, `AutomationLibrary.take_high_res_screenshot`,
  falling back to the `HighResShot` console command. The scripts print `STEP_SHOT_OK` / `STEP_SHOT_ERROR`;
  anything else is reported as a failure.
- **Screenshot tool** (fallback, cannot move the camera): a tool whose name contains `screenshot`.
  A `filename`/`path`/`file_path`/`output_path` argument gets the target path; `width`+`height` are
  passed if the schema has them; a returned image content block is saved as the PNG.

Run `python3 scripts/step_shot.py --list-tools` once in the live editor to see what it picked. If it
picks wrong, override with `--python-tool NAME` / `--screenshot-tool NAME` (or
`MEGAJAM_STEPSHOT_PYTHON_TOOL` / `MEGAJAM_STEPSHOT_SCREENSHOT_TOOL`). If there is no editor, no
matching tool, or `--actor`/`--location` is asked of a screenshot-only server, it stops with a message
saying which. **Unverified until a live run:** the exact tool names, that
`take_high_res_screenshot` works in the editor viewport on this build (`qa_harness.py` uses the same
call), and that 0.7s settle is enough for the viewport to redraw. If the first live shot shows the
old camera, raise `--settle`.

## Tests

`python3 -m unittest tests.test_step_shot`. A fake MCP server stands in for the editor, so CI needs no
Unreal.
