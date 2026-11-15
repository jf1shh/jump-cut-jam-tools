#!/usr/bin/env python3
"""Per-step visual check: frame the editor viewport, screenshot it, log it, so the agent can Read the PNG.

Owner rule 2026-11-08: look at every asset and step. Mock jam 10 shipped a non-playable build because
nobody looked. Run this after EVERY build step in the Unreal editor (stages/02_build/references/step-shot.md).

  step_shot.py --label crate-placed --actor SM_Crate        # frame a named actor, shoot
  step_shot.py --label spawn --location 0,0,300 --rotation -20,90,0
  step_shot.py --label playing --pie                         # PIE player view, camera untouched
  step_shot.py --label hud --viewport                        # shoot whatever the viewport shows now
  step_shot.py --verdict "crate floats 20cm above floor; fix Z"   # judgement for the LAST shot
  step_shot.py --list-tools                                  # show which editor tools it would use

Writes <outdir>/NN-<label>.png (default outdir: work/step-shots), prints its absolute path on stdout,
and appends `| NN | label | path | verdict |` to <outdir>/steps.md. Standard library only; talks to the
editor through scripts/mcp_call.py (default http://127.0.0.1:8010/mcp, or --url / MEGAJAM_MCP_URL).

Exit: 0 ok, 1 tool/screenshot failure, 2 usage error, editor unreachable, or no usable editor tool.
Only the lead agent calls Unreal MCP (AGENTS.md). The tool names below are discovered from tools/list;
which ones Epic's plugin really exposes is UNVERIFIED until a live run (`--list-tools`).
"""
import argparse
import base64
import contextlib
import json
import math
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_call import McpClient, McpError, EXIT_TOOL, EXIT_CONN  # noqa: E402

def make_client(url, timeout):
    """The real editor lists only 3 meta-tools at top level; mx.ProxyClient looks inside the toolsets
    (cached describes) and routes calls through call_tool. Shared with mx.py, not copied. Falls back to a
    plain client if mx.py is not beside this file."""
    try:
        import mx
    except ImportError:
        return McpClient(url, timeout)
    # Cache keyed by editor URL: a toolset cache left by another editor must never be trusted here.
    return mx.ProxyClient(url, timeout, mx.url_state_dir(url))


DEFAULT_OUTDIR = "work/step-shots"
HEADER = "# Step shots\n\n| NN | label | path | verdict |\n|---|---|---|---|\n"
PENDING = "(pending)"
ROW_RE = re.compile(r"^\| (\d{2,}) \| (.*?) \| (.*?) \| (.*) \|$")
# Only NN- / NNN- on disk. Numbers past 999 are still found through the steps.md rows (ROW_RE), which we
# write for every attempt; date or epoch named files (20261108-x.png, 1731100000-x.png) are not shots.
SHOT_RE = re.compile(r"^(\d{2,3})-.*\.png$")  # NN-<label>.png only; dated notes like 2026-11-08-x are not shots
FAILED = "FAILED"

PYTHON_PREFERRED = ("execute_python", "editor_run_python", "run_python", "python_exec", "exec_python")
CODE_KEYS = ("code", "script", "python_code", "python", "command", "source")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PATH_KEYS = ("filename", "file_name", "path", "file_path", "output_path", "save_path")

# In-editor Python. PARAMS is one line holding a Python string literal of JSON, so it is easy to parse.
_COMMON = '''import json
import math
import unreal
PARAMS = @@PARAMS@@
P = json.loads(PARAMS)
_OUT = []  # UE 5.9's execute_python returns only the last expression's value, not stdout: collect the markers too
def _ok(msg):
    _OUT.append("STEP_SHOT_OK " + msg)
    print("STEP_SHOT_OK " + msg)
def _err(msg):
    _OUT.append("STEP_SHOT_ERROR " + msg)
    print("STEP_SHOT_ERROR " + msg)
'''

FRAME_SCRIPT = _COMMON + '''
def run():
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if P.get("pie") and ues.get_game_world() is None:
        return _err("PIE is not running (no game world); press Play first, then shoot --pie")
    if P["mode"] == "actor":
        acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        want = P["actor"].lower()
        hits = [a for a in acts if want in (a.get_actor_label().lower(), a.get_name().lower())]
        if not hits:
            hits = [a for a in acts if want in a.get_actor_label().lower() or want in a.get_name().lower()]
        if not hits:
            return _err("no actor named %r in the open level (%d actors)" % (P["actor"], len(acts)))
        origin, extent = hits[0].get_actor_bounds(False)
        radius = max(extent.x, extent.y, extent.z, 25.0)
        dist = P.get("distance") or radius * 2.4
        az, el = math.radians(P["azimuth"]), math.radians(P["elevation"])
        loc = unreal.Vector(origin.x + dist * math.cos(el) * math.cos(az),
                            origin.y + dist * math.cos(el) * math.sin(az),
                            origin.z + dist * math.sin(el))
        rot = unreal.MathLibrary.find_look_at_rotation(loc, origin)
        ues.set_level_viewport_camera_info(loc, rot)
        return _ok("framed %s (%d match(es))" % (hits[0].get_actor_label(), len(hits)))
    if P["mode"] == "location":
        x, y, z = P["location"]
        pitch, yaw, roll = P["rotation"]
        ues.set_level_viewport_camera_info(unreal.Vector(x, y, z), unreal.Rotator(roll, pitch, yaw))
        return _ok("camera set")
    return _ok("camera untouched")
try:
    run()
except Exception as e:
    _err("%s: %s" % (type(e).__name__, e))
'''

SHOOT_SCRIPT = _COMMON + '''
def run():
    w, h, path = P["width"], P["height"], P["path"]
    try:
        if unreal.AutomationLibrary.take_high_res_screenshot(w, h, path, force_game_view=P["game_view"]) is False:
            raise RuntimeError("take_high_res_screenshot refused the request (returned False)")
        return _ok("queued via AutomationLibrary")
    except Exception as first:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        unreal.SystemLibrary.execute_console_command(world, 'HighResShot %dx%d filename="%s"' % (w, h, path))
        return _ok("queued via HighResShot console command (AutomationLibrary failed: %s)" % first)
try:
    run()
except Exception as e:
    _err("%s: %s" % (type(e).__name__, e))
'''


class NoMarkerError(McpError):
    """The python tool ran but our script never reported back: it probably does not execute code."""


def render(template, params):
    # repr() of a JSON str is a valid, single-line Python literal. The last line is a bare expression: 5.9's
    # execute_python returns only that value (returnValue), 5.8's CodeBlock path still reads the printed markers.
    return template.replace("@@PARAMS@@", repr(json.dumps(params))) + '\n"\\n".join(_OUT)\n'


def result_text(res):
    return "\n".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict) and c.get("type") == "text")


def pick_python_tool(tools, override=None):
    names = [t.get("name", "") for t in tools]
    if override:
        return next((t for t in tools if t.get("name") == override), None)
    for want in PYTHON_PREFERRED:
        if want in names:
            return tools[names.index(want)]
    # Name fallback: only tools that take a code-like string argument (not e.g. a python-docs search).
    return next((t for t in tools if "python" in t.get("name", "").lower() and code_prop(t)), None)


def pick_shot_tool(tools, override=None):
    if override:
        return next((t for t in tools if t.get("name") == override), None)
    return next((t for t in tools if re.search(r"screen_?shot", t.get("name", ""), re.I)), None)


def bare(name):
    """Tool name without a toolset prefix: the real editor lists 'Toolset.Tool' but call_tool wants 'Tool'."""
    return (name or "").rsplit(".", 1)[-1]


def pick_capture_tool(tools, override=None):
    if override:
        return next((t for t in tools if t.get("name") == override), None)
    return next((t for t in tools if bare(t.get("name", "")).lower() == "captureviewport"), None)


def _png_in(o):
    """Bytes of the first base64 PNG found in o (string, list or dict), else None."""
    if isinstance(o, str):
        t = re.sub(r"\s+", "", o)
        if t.startswith("data:") and "," in t:
            t = t.split(",", 1)[1]
        if t.startswith("iVBOR"):
            try:
                data = base64.b64decode(t, validate=True)
            except ValueError as e:
                raise McpError(f"the editor returned a PNG that is not valid base64: {e}")
            return data if data.startswith(PNG_MAGIC) else None
        if o.lstrip().startswith(("{", "[")):
            try:
                return _png_in(json.loads(o))
            except ValueError:
                return None
    elif isinstance(o, dict):
        for v in o.values():
            r = _png_in(v)
            if r:
                return r
    elif isinstance(o, list):
        for v in o:
            r = _png_in(v)
            if r:
                return r
    return None


def save_returned_png(res, path):
    """Save the image a tool returned (an image content item, or base64 PNG text). True if one was found."""
    for c in res.get("content", []):
        if isinstance(c, dict) and c.get("type") == "image" and c.get("data"):
            try:
                data = base64.b64decode(re.sub(r"\s+", "", c["data"]), validate=True)  # MIME wraps lines
            except ValueError as e:  # binascii.Error is a ValueError
                raise McpError(f"the editor returned an image that is not valid base64: {e}")
            break
        if isinstance(c, dict) and c.get("type") == "text":
            data = _png_in(c.get("text", ""))
            if data:
                break
    else:
        return False
    with open(path, "wb") as f:
        f.write(data)
    return True


def size_note(a, tool):
    """Warning text when --width/--height were given but the tool takes no size (real editor: neither does)."""
    props, _ = _props(tool)
    if (a.width, a.height) != (1920, 1080) and not ("width" in props and "height" in props):
        return f"; width/height not supported by {tool['name']}: the image is the editor's native size"
    return ""


def pie_running(res):
    """True/False from an IsPIERunning reply ({"returnValue": true}, bare true, or text containing it)."""
    # Real replies can be compact JSON, several text items, or a prefixed line ('Result: {"returnValue":true}').
    # Decode each text item on its own, then fall back to a whitespace-tolerant search of the whole text.
    items = [c.get("text", "") for c in res.get("content", []) if isinstance(c, dict)]
    for t in items:
        try:
            v = json.loads(t.strip())
        except ValueError:
            continue
        if isinstance(v, dict):
            v = v.get("returnValue", next(iter(v.values()), None))
        if v is True or str(v).lower() == "true":
            return True
    text = "\n".join(items).strip().lower()
    return text.startswith("true") or bool(re.search(r'"returnvalue"\s*:\s*true\b', text))


def rotator_quat(pitch, yaw, roll):
    """Unreal FRotator -> quaternion (x, y, z, w)."""
    sp, cp = math.sin(math.radians(pitch) / 2), math.cos(math.radians(pitch) / 2)
    sy, cy = math.sin(math.radians(yaw) / 2), math.cos(math.radians(yaw) / 2)
    sr, cr = math.sin(math.radians(roll) / 2), math.cos(math.radians(roll) / 2)
    return (cr * sp * sy - sr * cp * cy, -cr * sp * cy - sr * cp * sy,
            cr * cp * sy - sr * sp * cy, cr * cp * cy + sr * sp * sy)


def capture_transform(tool, loc, rot):
    """captureTransform for CaptureViewport. VERIFIED on the real UE 5.8 editor (hub 50, 2026-11-09): the shape
    is {location:{x,y,z}, rotation:{pitch,yaw,roll}, scale:{x,y,z}}. The FTransform fallback below (translation /
    quaternion / scale3D) is only for a schema that names no `location` field; the real editor never uses it."""
    sub = (_props(tool)[0].get("captureTransform") or {}).get("properties") or {}
    xyz = dict(zip("xyz", loc))
    if "location" in {k.lower() for k in sub}:
        out = {"location": xyz, "rotation": {"pitch": rot[0], "yaw": rot[1], "roll": rot[2]}}
        if "scale" in {k.lower() for k in sub}:
            out["scale"] = {"x": 1, "y": 1, "z": 1}
        return out
    x, y, z, w = rotator_quat(*rot)
    return {"translation": xyz, "rotation": {"x": x, "y": y, "z": z, "w": w}, "scale3D": {"x": 1, "y": 1, "z": 1}}


def capture_viewport(cli, tool, path, loc, rot, show_ui):
    """EditorAppToolset.CaptureViewport with the camera at (loc, rot); no Python needed. Saves the PNG."""
    props, _ = _props(tool)
    args = {"captureTransform": capture_transform(tool, loc, rot)}
    # The real editor REQUIRES annotations ("needs a default value" without it); {} is accepted (verified hub 50).
    # Always sent, even if a cached schema does not list it. Whether {} gives an overlay-free render is unproven:
    # the live {} render showed a grid and label overlay.
    args["annotations"] = {}
    if "bShowUI" in props:
        args["bShowUI"] = bool(show_ui)
    res = cli.call(tool["name"], args)
    if not save_returned_png(res, path):
        raise McpError(f"tool {tool['name']} returned no PNG; reply: {result_text(res)[:300] or res}")


def _props(tool):
    schema = tool.get("inputSchema") or {}
    return schema.get("properties") or {}, schema.get("required") or []


def _is_string(prop):
    t = (prop or {}).get("type")
    return t == "string" or (isinstance(t, list) and "string" in t)


def _is_codeblock(prop):
    """UE 5.9 CodeBlock parameter: an object with Content + Language (a plain string cannot import into it)."""
    if not isinstance(prop, dict) or _is_string(prop):
        return False
    props = prop.get("properties")
    if isinstance(props, dict):
        low = {str(k).lower() for k in props}
        return "content" in low and "language" in low
    return "codeblock" in str(prop.get("$ref", "")).lower()


def _is_code_arg(prop):
    return _is_string(prop) or _is_codeblock(prop)


def code_prop(tool, loose=False):
    """Name of the argument that takes Python source, or None. loose=True also accepts any required string.
    On UE 5.9 the argument is a CodeBlock object ({"Content": src, "Language": "Python"}), on 5.8.4 a string."""
    props, required = _props(tool)
    for k in CODE_KEYS:
        if k in props and _is_code_arg(props[k]):
            return k
    for k, v in props.items():
        if re.search(r"code|script|python|source|command", k, re.I) and _is_code_arg(v):
            return k
    if loose:
        return next((k for k in required if _is_string(props.get(k))), None)
    return None


def code_key(tool):
    return code_prop(tool, loose=True) or "code"


def _flavor_of(cli):
    """'new' (5.9) / 'old' (5.8.4) for a ProxyClient, else None (plain clients have no toolset flavor)."""
    fn = getattr(cli, "flavor", None)
    return fn() if callable(fn) else None


def code_args(tool, script, cli=None):
    """Arguments dict that run `script` through TOOL: a string for 5.8.4, a CodeBlock for 5.9."""
    props = _props(tool)[0]
    if not props:  # schema lookup failed or empty: follow the probed flavor, not a guess
        if cli is not None and _flavor_of(cli) == "new":
            return {"script": {"Content": script, "Language": "Python"}}
        return {"code": script}
    key = code_key(tool)
    prop = props.get(key)
    return {key: {"Content": script, "Language": "Python"} if _is_codeblock(prop) else script}


def run_python(cli, tool, script, what):
    """Run script in the editor; the script prints STEP_SHOT_OK/ERROR. Returns the OK text."""
    res = cli.call(tool["name"], code_args(tool, script, cli))
    text = result_text(res)
    # Markers may sit inside wrappers (JSON output, "LogPython: " prefixes). A marker that an echoed copy of
    # our source would produce is skipped: there the literal is followed by a closing quote (print("STEP_SHOT_OK " + msg)).
    found = {}
    for m in re.finditer(r'STEP_SHOT_(OK|ERROR)\b ?(\\*")?([^\n]*)', text):
        if m.group(2) is None:
            found.setdefault(m.group(1), re.split(r'\\n|"\s*[,}\]]', m.group(3))[0].strip())
    if "ERROR" in found:
        raise McpError(f"{what} failed in the editor: {found['ERROR']}")
    if "OK" not in found:
        raise NoMarkerError(f"{what}: python tool {tool['name']} did not report STEP_SHOT_OK "
                            f"(it may have returned an error or run nothing). Reply: {text[:300] or res}")
    return found["OK"]


def shoot_with_tool(cli, tool, path, width, height):
    """Dedicated screenshot tool: pass a path (and size) if its schema takes them; save returned images."""
    props, _ = _props(tool)
    args = {}
    pk = next((k for k in PATH_KEYS if k in props), None)
    if pk:
        args[pk] = path
    if "ref" in props:  # the real SlateInspectorToolset.Screenshot: "" = the active editor window
        args["ref"] = ""
    if "width" in props and "height" in props:
        args["width"], args["height"] = width, height
    res = cli.call(tool["name"], args)
    if save_returned_png(res, path):
        return
    if not pk:
        raise McpError(f"tool {tool['name']} takes no path argument and returned no image; "
                       f"schema properties: {sorted(props)}. Use a python tool or pass --screenshot-tool.")


def wait_for_file(path, timeout):
    """The editor writes the PNG a frame or more later. Wait until it exists and stops growing."""
    end = time.time() + timeout
    last = -1
    while time.time() < end:
        if os.path.isfile(path):
            size = os.path.getsize(path)
            if size > 0 and size == last:
                return True
            last = size
        time.sleep(0.3)
    return False


# ---- steps.md bookkeeping -------------------------------------------------------------------------

def next_number(outdir):
    nums = [0]
    for n in os.listdir(outdir) if os.path.isdir(outdir) else []:
        m = SHOT_RE.match(n)
        if m:
            nums.append(int(m.group(1)))
    md = os.path.join(outdir, "steps.md")
    if os.path.isfile(md):
        with open(md, encoding="utf-8") as f:
            for line in f:
                m = ROW_RE.match(line.rstrip("\n"))
                if m:
                    nums.append(int(m.group(1)))
    return max(nums) + 1


def clean_cell(s):
    return re.sub(r"\s+", " ", str(s)).replace("|", "\\|").strip()


def append_row(outdir, nn, label, path, verdict):
    md = os.path.join(outdir, "steps.md")
    new = not os.path.isfile(md)
    with open(md, "a", encoding="utf-8") as f:
        if new:
            f.write(HEADER)
        f.write(f"| {nn:02d} | {clean_cell(label)} | {clean_cell(path)} | {clean_cell(verdict) or PENDING} |\n")


def set_last_verdict(outdir, verdict, replace=False):
    md = os.path.join(outdir, "steps.md")
    if not os.path.isfile(md):
        raise McpError(f"no {md}; take a shot first", EXIT_CONN)
    with open(md, encoding="utf-8") as f:
        lines = f.read().split("\n")
    for i in range(len(lines) - 1, -1, -1):
        m = ROW_RE.match(lines[i])
        if m:
            old = m.group(4)
            if not replace and old != PENDING and not old.startswith(FAILED):
                raise McpError(f"last row {m.group(1)}-{m.group(2)} already has a verdict ({old!r}); "
                               f"take a new shot first, or pass --replace to overwrite it", EXIT_CONN)
            lines[i] =f"| {m.group(1)} | {m.group(2)} | {m.group(3)} | {clean_cell(verdict)} |"
            with open(md, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return m.group(1), m.group(2)
    raise McpError(f"{md} has no shot rows yet; take a shot first", EXIT_CONN)


# ---- main -----------------------------------------------------------------------------------------

def triple(text, name):
    try:
        v = [float(x) for x in text.split(",")]
        assert len(v) == 3
        return v
    except (ValueError, AssertionError):
        print(f"step_shot: {name} needs three numbers like 0,0,300 (got {text!r})", file=sys.stderr)
        raise SystemExit(2)


def safe_label(s):
    s = re.sub(r"[^A-Za-z0-9_-]+", "-", s).strip("-")
    if not s:
        print("step_shot: --label needs letters or digits", file=sys.stderr)
        raise SystemExit(2)
    return s


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--label", help="short name for this step, becomes NN-<label>.png")
    t = p.add_mutually_exclusive_group()
    t.add_argument("--actor", help="frame the viewport on this actor (label or name; exact match first)")
    t.add_argument("--location", help="camera location X,Y,Z (Unreal units)")
    t.add_argument("--pie", action="store_true", help="shoot the PIE player view, camera untouched")
    t.add_argument("--viewport", action="store_true", help="shoot the viewport as it is, camera untouched")
    p.add_argument("--rotation", default="0,0,0", help="with --location: pitch,yaw,roll degrees (default 0,0,0)")
    p.add_argument("--distance", type=float, help="with --actor: camera distance in units (default auto)")
    p.add_argument("--azimuth", type=float, default=200, help="with --actor: degrees around the actor (default 200)")
    p.add_argument("--elevation", type=float, default=20, help="with --actor: degrees above it (default 20)")
    p.add_argument("--verdict", help="your judgement. With --label: recorded on the new shot. Alone: on the last shot")
    p.add_argument("--replace", action="store_true", help="with --verdict alone: overwrite an existing verdict")
    p.add_argument("--outdir", default=os.environ.get("MEGAJAM_STEPSHOT_DIR", DEFAULT_OUTDIR))
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--editor-ui", action="store_true", help="keep gizmos/overlays (default: game view, clean)")
    p.add_argument("--settle", type=float, default=0.7, help="seconds between moving the camera and shooting")
    p.add_argument("--wait", type=float, default=30, help="seconds to wait for the PNG to appear")
    p.add_argument("--via", choices=("auto", "python", "screenshot", "capture"), default="auto")
    p.add_argument("--python-tool", default=os.environ.get("MEGAJAM_STEPSHOT_PYTHON_TOOL"))
    p.add_argument("--screenshot-tool", default=os.environ.get("MEGAJAM_STEPSHOT_SCREENSHOT_TOOL"))
    p.add_argument("--list-tools", action="store_true", help="show the editor tools this script would use, then exit")
    p.add_argument("--url", default=None)
    p.add_argument("--timeout", type=float, default=30, help="per MCP call, seconds")
    return p


def take_shot(a, cli):
    tools = cli.list_tools()
    py = pick_python_tool(tools, a.python_tool)
    st = pick_shot_tool(tools, a.screenshot_tool)
    if a.python_tool and not py:
        raise McpError(f"--python-tool {a.python_tool!r} is not in the editor's tools/list", EXIT_CONN)
    if a.screenshot_tool and not st:
        raise McpError(f"--screenshot-tool {a.screenshot_tool!r} is not in the editor's tools/list", EXIT_CONN)
    cap = pick_capture_tool(tools)
    framing = bool(a.actor or a.location)
    via = a.via
    if via == "auto":
        # Real editor: no Python tool. A camera position goes through CaptureViewport; the rest through Screenshot.
        via = "python" if py else "capture" if (cap and a.location) else "screenshot"
    if via == "python" and not py:
        raise McpError("no Python-execution tool in the editor's tools/list (looked for a name containing "
                       "'python'). Run --list-tools, then pass --python-tool NAME or --via screenshot.", EXIT_CONN)
    if via == "capture":
        if not cap:
            raise McpError("no CaptureViewport tool in the editor's toolsets. Run --list-tools.", EXIT_CONN)
        if not a.location:
            raise McpError("--via capture needs --location X,Y,Z (CaptureViewport takes a camera transform). "
                           "To shoot the viewport as it is, use --viewport.", EXIT_CONN)
    if via == "screenshot" and not st:
        raise McpError("no screenshot tool in the editor's tools/list (looked for a name containing "
                       "'screenshot') and no Python tool to fall back on. Run --list-tools.", EXIT_CONN)
    if via != "python" and a.actor:
        raise McpError("--actor needs a Python tool to read the actor's bounds, and the real editor has none. "
                       "Find its position (mx.py call ... find_actors) and use --location X,Y,Z --rotation P,Y,R.", EXIT_CONN)
    if via == "screenshot" and framing:
        raise McpError("framing a location needs CaptureViewport (EditorAppToolset) or a Python tool; neither was "
                       "found. Use --viewport/--pie, or point the camera by hand.", EXIT_CONN)

    os.makedirs(a.outdir, exist_ok=True)
    nn = next_number(a.outdir)
    label = safe_label(a.label)
    path = os.path.abspath(os.path.join(a.outdir, f"{nn:02d}-{label}.png"))
    # The editor writes to a name unique to this attempt, so a late PNG from an earlier timed-out
    # attempt can never be mistaken for this one. It is renamed to `path` once it has arrived.
    tmp = os.path.join(os.path.dirname(path), f".pending-{nn:02d}-{label}-{os.getpid()}-{time.time_ns()}.png")
    note = ""
    try:
        if via == "python" and a.via == "auto" and st and not framing and not a.pie:
            # Python tool picked by name only: if it never reports back, it may not run code. Try the screenshot tool.
            try:
                note = _shoot_python(a, cli, py, tmp, framing)
            except NoMarkerError as e:
                print(f"step_shot: {e}\nstep_shot: falling back to screenshot tool {st['name']}", file=sys.stderr)
                shoot_with_tool(cli, st, tmp, a.width, a.height)
        elif via == "python":
            note = _shoot_python(a, cli, py, tmp, framing)
        elif via == "capture":
            capture_viewport(cli, cap, tmp, triple(a.location, "--location"), triple(a.rotation, "--rotation"),
                             a.editor_ui)
            note = f"captured from the given pose through {cap['name']} (no editor UI; the viewport camera is NOT moved; a grid/label overlay may show)" + size_note(a, cap)
        else:
            pie_note = ""
            if a.pie:
                chk = next((t for t in tools if bare(t.get("name", "")) == "IsPIERunning"), None)
                if chk:  # EditorAppToolset.IsPIERunning needs no Python; refuse like the Python path did
                    if not pie_running(cli.call(chk["name"], {})):
                        raise McpError("PIE is not running (IsPIERunning says false); press Play first, then shoot --pie")
                    pie_note = "; PIE is running (checked with IsPIERunning). --pie does NOT start PIE"
                else:
                    pie_note = ("; --pie only takes this window shot: it does NOT start PIE and no IsPIERunning tool "
                                "was found, so PIE state UNCHECKED. Look at the image to see what it shows")
            shoot_with_tool(cli, st, tmp, a.width, a.height)
            note = (f"window shot through {st['name']} (the whole active editor window with its UI, "
                    f"not just the viewport)" + size_note(a, st) + pie_note)
        if not wait_for_file(tmp, a.wait):
            raise McpError(f"the editor reported success but no PNG appeared within {a.wait:g}s "
                           f"(is the editor on this machine, and is the viewport visible and not minimised?)")
        os.replace(tmp, path)
    except (McpError, OSError, ValueError) as e:
        if not isinstance(e, McpError):
            e = McpError(f"{type(e).__name__}: {e}", EXIT_TOOL)
        with contextlib.suppress(OSError):
            os.remove(tmp)
        append_row(a.outdir, nn, label, "(no file)", f"{FAILED}: {e}"[:300])
        print(f"step_shot: shot {nn:02d}-{label} failed; logged as FAILED in steps.md", file=sys.stderr)
        raise e
    append_row(a.outdir, nn, label, path, a.verdict or "")
    return path, note


def _shoot_python(a, cli, py, tmp, framing):
    """Frame the camera, wait for it to settle, queue the screenshot. Returns the framing note."""
    mode = "actor" if a.actor else "location" if a.location else "none"
    params = {"mode": mode, "actor": a.actor or "", "distance": a.distance, "azimuth": a.azimuth,
              "elevation": a.elevation, "location": triple(a.location, "--location") if a.location else None,
              "rotation": triple(a.rotation, "--rotation"), "path": tmp, "width": a.width,
              "height": a.height, "game_view": not a.editor_ui, "pie": bool(a.pie)}
    note = run_python(cli, py, render(FRAME_SCRIPT, params), "framing the camera")
    if framing:
        time.sleep(a.settle)
    run_python(cli, py, render(SHOOT_SCRIPT, params), "taking the screenshot")
    return note


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.list_tools:
        pass
    elif a.verdict is not None and not a.verdict.strip():
        print("step_shot: --verdict is empty; write what you saw (an empty one would hide a pending row)", file=sys.stderr)
        return 2
    elif a.label is None and a.verdict is None:
        print("step_shot: give --label (take a shot), --verdict (judge the last shot) or --list-tools", file=sys.stderr)
        return 2
    elif a.label is None and (a.actor or a.location or a.pie or a.viewport):
        print("step_shot: a target needs --label too", file=sys.stderr)
        return 2
    elif a.label is not None and not (a.actor or a.location or a.pie or a.viewport):
        a.viewport = True  # no target = shoot the viewport window as it is
    if a.label is not None:  # bad arguments are usage errors (exit 2), reported before any editor call
        safe_label(a.label)
        if a.location:
            triple(a.location, "--location")
        triple(a.rotation, "--rotation")
    try:
        if a.label is None and not a.list_tools:  # verdict only: no editor needed
            nn, label = set_last_verdict(a.outdir, a.verdict, a.replace)
            print(f"verdict recorded for {nn}-{label}")
            return 0
        cli = make_client(a.url, a.timeout)
        if a.list_tools:
            tools = cli.list_tools()
            py, st = pick_python_tool(tools, a.python_tool), pick_shot_tool(tools, a.screenshot_tool)
            print(f"python tool:     {py['name'] + ' (code arg: ' + code_key(py) + ')' if py else 'NONE'}")
            print(f"screenshot tool: {st['name'] if st else 'NONE'}")
            cp = pick_capture_tool(tools)
            print(f"capture tool:    {cp['name'] if cp else 'NONE'}")
            print(f"all tools ({len(tools)}): " + ", ".join(sorted(t.get("name", "?") for t in tools)))
            return 0
        path, note = take_shot(a, cli)
    except McpError as e:
        print(f"step_shot: {e}", file=sys.stderr)
        return e.exit_code
    if note:
        print(note, file=sys.stderr)
    print(path)
    print("Read this PNG now and judge it; then: step_shot.py --verdict \"what you saw / what to fix\"", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
