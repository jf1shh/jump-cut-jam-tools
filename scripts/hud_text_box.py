#!/usr/bin/env python3
"""hud_text_box.py - recipe for a HUD text line on a dark, semi-transparent backdrop box. Standard library only.

  hud_text_box.py "YOU LOSE" --color "#ffcc00" --anchor center
  hud_text_box.py "All 5 ribbons!" --color 0.1,1,0.2 --anchor top-center --box-color "#000000" --opacity 0.7 --json
  hud_text_box.py "YOU WIN" --apply --blueprint /Game/Slime/BP_HUD.BP_HUD

Why: mock jam 11 drew the end lines as bare HUD text. Dark red hid on the scene, bright colours washed out on the
light ground (_config/reference/canon/jam-hud-readable-text.md). A backdrop box makes any text colour readable.

Path (_config/reference/canon/jam-blueprint-python-vs-mcp.md): graph DSL through the editor MCP. Editor Python cannot add graph
nodes. The recipe is one `(fn NAME () ...)` for BlueprintTools.write_graph_dsl:
    (HUD|DrawRect ...)   the box, FIRST so the text lands on top of it
    (HUD|DrawText ...)   the line, with NAMED args (positional args shift, mock 11 gap 31)
Splice a call `(NAME)` into the EventReceiveDrawHUD chain after the state test (e.g. only when state is win or lose).

Default prints the DSL plus the exact `scripts/mx.py call` command. --json prints the whole recipe. --apply runs
that mx.py call itself (needs the editor up, MCP on 8010; only the lead agent may call MCP, see AGENTS.md).

Box maths (HUD DrawText cannot be measured here, so the size is an estimate that errs on the large side):
    text width  = longest line chars * CHAR_W * scale      (CHAR_W 26 px)
    text height = lines * LINE_H * scale                   (LINE_H 40 px)
    (mock 11 frames at 1920x1200: the default HUD font draws about 18-25 px per char and 30-40 px per line.)
    box = text + 2 * padding on each axis; the anchor places the box, the text sits padding inside it.
Tune with --char-w / --line-h after one look at a frame.

Exit: 0 ok, 2 bad arguments, 1 --apply failed.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

CHAR_W = 26.0  # at or above the widest seen (25 px/char)
LINE_H = 40.0
SCREEN_W = 1920.0
SCREEN_H = 1200.0  # the Legion playtest frames (mock 11 vp_r16) are 1920x1200
ANCHORS = ("top-left", "top-center", "top-right",
           "center-left", "center", "center-right",
           "bottom-left", "bottom-center", "bottom-right")
NAMED = {"white": (1, 1, 1), "black": (0, 0, 0), "red": (1, 0, 0), "green": (0, 1, 0), "blue": (0, 0, 1),
         "yellow": (1, 1, 0), "orange": (1, 0.5, 0), "cyan": (0, 1, 1), "magenta": (1, 0, 1)}
BLUEPRINT_TOOLSET = "editor_toolset.toolsets.blueprint.BlueprintTools"
DEFAULT_FN = "DrawEndLine"
HERE = os.path.dirname(os.path.abspath(__file__))


class ArgError(ValueError):
    pass


def parse_color(value, alpha=1.0):
    """'#rrggbb', '#rrggbbaa', a name, or 'r,g,b[,a]' floats 0..1 -> (r, g, b, a) floats."""
    s = str(value).strip().lower()
    if s in NAMED:
        r, g, b = NAMED[s]
        return (float(r), float(g), float(b), float(alpha))
    m = re.fullmatch(r"#([0-9a-f]{6})([0-9a-f]{2})?", s)
    if m:
        h = m.group(1)
        r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        a = int(m.group(2), 16) / 255.0 if m.group(2) else alpha
        return (r, g, b, a)
    parts = s.split(",")
    if len(parts) in (3, 4):
        try:
            nums = [float(p) for p in parts]
        except ValueError:
            nums = None
        if nums is not None:
            if any(not (0 <= n <= 1) for n in nums):  # also rejects nan
                raise ArgError(f"colour {value!r}: r,g,b[,a] floats must be 0..1")
            if len(nums) == 3:
                nums.append(alpha)
            return tuple(nums)
    raise ArgError(f"colour {value!r}: use #rrggbb, #rrggbbaa, a name ({', '.join(sorted(NAMED))}) or r,g,b[,a] in 0..1")


def color_text(c):
    return "(R=%.4f,G=%.4f,B=%.4f,A=%.4f)" % c


def measure(text, scale, char_w=CHAR_W, line_h=LINE_H):
    lines = text.split("\n")
    return max(len(x) for x in lines) * char_w * scale, len(lines) * line_h * scale


def place(anchor, box_w, box_h, screen_w, screen_h, margin):
    col = anchor.split("-")[-1] if "-" in anchor else "center"
    row = anchor.split("-")[0] if "-" in anchor else "center"
    if anchor == "center":
        col = row = "center"
    x = {"left": margin, "center": (screen_w - box_w) / 2.0, "right": screen_w - margin - box_w}[col]
    y = {"top": margin, "center": (screen_h - box_h) / 2.0, "bottom": screen_h - margin - box_h}[row]
    return x, y


def build(text, color="#ffffff", anchor="center", box_color="#000000", opacity=0.65, padding=16.0, scale=1.0,
          screen_w=SCREEN_W, screen_h=SCREEN_H, margin=24.0, char_w=CHAR_W, line_h=LINE_H, fn=DEFAULT_FN):
    """Validate the arguments and return the recipe dict. Raises ArgError."""
    if not isinstance(text, str) or not text.strip():
        raise ArgError("text must not be empty")
    if "\r" in text or any(ord(ch) < 32 and ch != "\n" for ch in text):
        raise ArgError("text has control characters other than newline")
    if anchor not in ANCHORS:
        raise ArgError(f"anchor {anchor!r}: pick one of {', '.join(ANCHORS)}")
    for name, v in (("padding", padding), ("margin", margin)):
        if not (math.isfinite(v) and v >= 0):
            raise ArgError(f"{name} must be a finite number >= 0")
    for name, v in (("scale", scale), ("screen-w", screen_w), ("screen-h", screen_h),
                    ("char-w", char_w), ("line-h", line_h)):
        if not (math.isfinite(v) and v > 0):
            raise ArgError(f"{name} must be a finite number > 0")
    if not (0.0 <= opacity <= 1.0):  # also rejects nan
        raise ArgError("opacity must be 0..1")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", fn):
        raise ArgError(f"function name {fn!r} is not a valid identifier")
    tc = parse_color(color)
    if tc[3] < 0.5:
        raise ArgError("text colour alpha must be >= 0.5 (a near-invisible end line defeats the box)")
    bc = parse_color(box_color)
    bc = (bc[0], bc[1], bc[2], opacity)  # --opacity always wins; any alpha in --box-color is ignored
    tw, th = measure(text, scale, char_w, line_h)
    bw, bh = tw + 2 * padding, th + 2 * padding
    if bw > screen_w or bh > screen_h:
        raise ArgError(f"box {bw:.0f}x{bh:.0f} does not fit the {screen_w:.0f}x{screen_h:.0f} screen; "
                       "shorten the text, lower --scale or --padding, or add newlines")
    bx, by = place(anchor, bw, bh, screen_w, screen_h, margin)
    if bx < 0 or by < 0 or bx + bw > screen_w or by + bh > screen_h:
        raise ArgError(f"box at {anchor} with margin {margin:.0f} falls off screen; lower --margin")
    tx, ty = bx + padding, by + padding
    box = {"node": "HUD|DrawRect", "color": bc, "x": bx, "y": by, "w": bw, "h": bh}
    label = {"node": "HUD|DrawText", "text": text, "color": tc, "x": tx, "y": ty, "scale": scale}
    dsl = to_dsl(fn, box, label)
    return {"fn": fn, "draw_order": ["HUD|DrawRect", "HUD|DrawText"], "box": box, "text": label,
            "dsl": dsl, "call": f"(CallFunction|{fn})"}


def dsl_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def to_dsl(fn, box, label):
    return (
        f"(fn {fn} ()\n"
        f"  (HUD|DrawRect :RectColor {dsl_string(color_text(box['color']))} :ScreenX {box['x']:.1f} "
        f":ScreenY {box['y']:.1f} :ScreenW {box['w']:.1f} :ScreenH {box['h']:.1f})\n"
        f"  (HUD|DrawText :Text {dsl_string(label['text'])} :TextColor {dsl_string(color_text(label['color']))} "
        f":ScreenX {label['x']:.1f} :ScreenY {label['y']:.1f} :Scale {label['scale']:.2f}))"
    )


def add_args(recipe, blueprint):
    """Step 1: the function graph must exist before write_graph_dsl (mock 11: 'AddEvent|<fn> does not exist').
    Arg names confirmed on the real editor 2026-11-09 (the hub's run)."""
    return {"blueprint": {"refPath": blueprint}, "graph_name": recipe["fn"]}  # real editor: `graph_name`


def mx_args(recipe, blueprint):
    return {"graph": {"refPath": f"{blueprint}:{recipe['fn']}"}, "code": recipe["dsl"]}


def steps(recipe, blueprint):
    """The ordered (tool, args) MCP calls. Splicing the (fn) call into EventReceiveDrawHUD is a manual step."""
    return [("add_function_graph", add_args(recipe, blueprint)), ("write_graph_dsl", mx_args(recipe, blueprint))]


def mx_command(recipe, blueprint):
    return "\n".join(" ".join(_q(x) for x in ["python3", "scripts/mx.py", "call", BLUEPRINT_TOOLSET, tool, json.dumps(args)])
                     for tool, args in steps(recipe, blueprint))


def _q(a):
    return a if re.fullmatch(r"[A-Za-z0-9_./:=-]+", a) else "'" + a.replace("'", "'\\''") + "'"


def main(argv=None):
    p = argparse.ArgumentParser(description="HUD text on a dark backdrop box: graph DSL recipe for the editor MCP.")
    p.add_argument("text", help='the line; "\\n" in the shell text is a line break only if you pass a real newline')
    p.add_argument("--color", default="#ffffff", help="text colour (#rrggbb, name or r,g,b[,a] 0..1)")
    p.add_argument("--anchor", default="center", choices=ANCHORS)
    p.add_argument("--box-color", default="#000000")
    p.add_argument("--opacity", type=float, default=0.65, help="box alpha 0..1 (default 0.65); overrides any alpha in --box-color")
    p.add_argument("--padding", type=float, default=16.0)
    p.add_argument("--scale", type=float, default=1.0, help="text scale")
    p.add_argument("--screen-w", type=float, default=SCREEN_W)
    p.add_argument("--screen-h", type=float, default=SCREEN_H, help="default 1200: the Legion playtest is 1920x1200")
    p.add_argument("--margin", type=float, default=24.0, help="gap to the screen edge for non-centred anchors")
    p.add_argument("--char-w", type=float, default=CHAR_W)
    p.add_argument("--line-h", type=float, default=LINE_H)
    p.add_argument("--fn", default=DEFAULT_FN, help="name of the HUD function to create")
    p.add_argument("--blueprint", default="/Game/Slime/BP_HUD.BP_HUD",
                   help="refPath of the HUD Blueprint; the function graph is BLUEPRINT:FN")
    p.add_argument("--json", action="store_true", help="print the whole recipe as JSON")
    p.add_argument("--apply", action="store_true", help="run the mx.py call now (editor + MCP must be up)")
    a = p.parse_args(argv)
    try:
        r = build(a.text, a.color, a.anchor, a.box_color, a.opacity, a.padding, a.scale, a.screen_w, a.screen_h,
                  a.margin, a.char_w, a.line_h, a.fn)
    except ArgError as e:
        print(f"hud_text_box: {e}", file=sys.stderr)
        return 2
    cmd = mx_command(r, a.blueprint)
    if a.json:
        print(json.dumps(dict(r, mx_commands=cmd.split("\n"),
                              mx_steps=[{"tool": t, "args": x} for t, x in steps(r, a.blueprint)]), indent=2))
    else:
        print(r["dsl"])
        print("\n# two calls: 1) create the function graph, 2) write the DSL into it. Then add "
              f"{r['call']} to the EventReceiveDrawHUD body (write the whole event again; it replaces the chain) "
              "and compile.")
        print(cmd)
        print("# look at the result: take a desktop screenshot and Read it (mx.py shot may not work on the real editor)")
    if a.apply:
        for tool, args in steps(r, a.blueprint):
            res = subprocess.run([sys.executable, os.path.join(HERE, "mx.py"), "call", BLUEPRINT_TOOLSET,
                                  tool, json.dumps(args)])
            if res.returncode != 0:
                if tool == "add_function_graph":
                    print("hud_text_box: add_function_graph failed (maybe the function already exists); "
                          "trying write_graph_dsl anyway", file=sys.stderr)
                    continue
                return 1
        print(f"hud_text_box: applied. Now add {r['call']} to the EventReceiveDrawHUD body, compile, "
              "then look at a desktop screenshot")
    return 0


if __name__ == "__main__":
    sys.exit(main())
