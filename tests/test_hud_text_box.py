import contextlib
import io
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import hud_text_box as h  # noqa: E402


def covers(r, pad_min=0.0):
    """Box rect contains the text rect (estimated size) with at least pad_min on every side."""
    b, t = r["box"], r["text"]
    tw, th = h.measure(t["text"], t["scale"])
    return (t["x"] - b["x"] >= pad_min and t["y"] - b["y"] >= pad_min
            and b["x"] + b["w"] - (t["x"] + tw) >= pad_min - 1e-6
            and b["y"] + b["h"] - (t["y"] + th) >= pad_min - 1e-6)


class Order(unittest.TestCase):
    def test_box_drawn_before_text(self):
        r = h.build("YOU LOSE")
        self.assertEqual(r["draw_order"], ["HUD|DrawRect", "HUD|DrawText"])
        self.assertLess(r["dsl"].index("HUD|DrawRect"), r["dsl"].index("HUD|DrawText"))

    def test_named_args_only(self):
        d = h.build("hi")["dsl"]
        for pin in (":RectColor", ":ScreenW", ":ScreenH", ":Text ", ":TextColor", ":Scale"):
            self.assertIn(pin, d)

    def test_dsl_shape_and_call(self):
        r = h.build("hi", fn="EndLine")
        self.assertTrue(r["dsl"].startswith("(fn EndLine ()"))
        self.assertEqual(r["call"], "(CallFunction|EndLine)")
        d = r["dsl"].replace('"(R=', '"').replace(')"', '"')  # colour strings carry their own parens
        self.assertEqual(d.count("("), d.count(")"))


class Rect(unittest.TestCase):
    def test_short_and_long_lines_covered_with_padding(self):
        for text in ("OK", "YOU LOSE", "All 5 ribbons in 20.5 seconds - restart with R", "x" * 60):
            for anchor in h.ANCHORS:
                for scale in (1.0, 2.0):
                    r = h.build(text, anchor=anchor, padding=20, scale=scale, screen_w=3840, screen_h=2160)
                    self.assertTrue(covers(r, 20), (text[:10], anchor, scale))

    def test_long_line_gives_wider_box(self):
        self.assertGreater(h.build("x" * 60)["box"]["w"], h.build("x")["box"]["w"])

    def test_multiline_uses_longest_line_and_line_count(self):
        r = h.build("ab\nabcdef\nabc", padding=0)
        self.assertEqual(r["box"]["w"], 6 * h.CHAR_W)
        self.assertEqual(r["box"]["h"], 3 * h.LINE_H)

    def test_center_anchor_is_centred(self):
        r = h.build("YOU LOSE", anchor="center", screen_w=1000, screen_h=600)
        b = r["box"]
        self.assertAlmostEqual(b["x"] + b["w"] / 2, 500)
        self.assertAlmostEqual(b["y"] + b["h"] / 2, 300)

    def test_edges_stay_on_screen(self):
        for anchor in h.ANCHORS:
            b = h.build("hello world", anchor=anchor, screen_w=800, screen_h=450)["box"]
            self.assertGreaterEqual(b["x"], 0)
            self.assertGreaterEqual(b["y"], 0)
            self.assertLessEqual(b["x"] + b["w"], 800)
            self.assertLessEqual(b["y"] + b["h"], 450)

    def test_corner_anchor_respects_margin(self):
        b = h.build("hi", anchor="top-left", margin=40)["box"]
        self.assertEqual((b["x"], b["y"]), (40, 40))
        b = h.build("hi", anchor="bottom-right", margin=40, screen_w=1000, screen_h=500)["box"]
        self.assertEqual((b["x"] + b["w"], b["y"] + b["h"]), (960, 460))

    def test_box_alpha_is_opacity_text_is_opaque(self):
        r = h.build("hi", opacity=0.4)
        self.assertEqual(r["box"]["color"][3], 0.4)
        self.assertEqual(r["text"]["color"][3], 1.0)


class Colours(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(h.parse_color("#ff0000"), (1.0, 0.0, 0.0, 1.0))
        self.assertEqual(h.parse_color("yellow"), (1.0, 1.0, 0.0, 1.0))
        self.assertEqual(h.parse_color("0.5,0.5,0.5", alpha=0.3), (0.5, 0.5, 0.5, 0.3))
        self.assertAlmostEqual(h.parse_color("#00000080")[3], 128 / 255)

    def test_bad(self):
        for bad in ("", "#ff", "#gggggg", "1,2,3", "0.1,0.2", "blurple", "-0.1,0,0"):
            with self.assertRaises(h.ArgError, msg=bad):
                h.parse_color(bad)


class Validation(unittest.TestCase):
    def bad(self, *a, **k):
        with self.assertRaises(h.ArgError):
            h.build(*a, **k)

    def test_text(self):
        self.bad("")
        self.bad("   ")
        self.bad("a\x07b")

    def test_numbers(self):
        self.bad("hi", opacity=1.5)
        self.bad("hi", opacity=-0.1)
        self.bad("hi", padding=-1)
        self.bad("hi", scale=0)
        self.bad("hi", screen_w=0)

    def test_anchor_colour_fn(self):
        self.bad("hi", anchor="middle")
        self.bad("hi", color="nope")
        self.bad("hi", box_color="#12")
        self.bad("hi", fn="bad name")
        self.bad("hi", fn="a)(b")

    def test_too_big_for_screen(self):
        self.bad("x" * 400)

    def test_quotes_are_escaped(self):
        d = h.build('say "hi"')["dsl"]
        self.assertIn('\\"hi\\"', d)


class Cli(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = h.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_default_prints_dsl_and_mx_command(self):
        code, out, _ = self.run_cli("YOU WIN", "--color", "#00aa00")
        self.assertEqual(code, 0)
        self.assertIn("(fn DrawEndLine", out)
        self.assertIn("python3 scripts/mx.py call editor_toolset.toolsets.blueprint.BlueprintTools write_graph_dsl", out)
        self.assertLess(out.index("add_function_graph"), out.index("write_graph_dsl"))
        self.assertIn("CallFunction|DrawEndLine", out)
        self.assertNotIn("mx.py shot hud", out)  # no bare promise of mx.py shot
        self.assertIn("desktop screenshot", out)
        for line in out.splitlines():
            if "mx.py call" in line:
                self.assertTrue(line.startswith("python3 scripts/mx.py"), line)

    def test_add_function_graph_uses_graph_name(self):
        r = h.build("hi", fn="Fn")
        args = h.add_args(r, "/Game/X/BP_HUD.BP_HUD")
        self.assertEqual(args, {"blueprint": {"refPath": "/Game/X/BP_HUD.BP_HUD"}, "graph_name": "Fn"})

    def test_json(self):
        code, out, _ = self.run_cli("YOU WIN", "--json", "--blueprint", "/Game/X/BP_HUD.BP_HUD", "--fn", "Fn")
        self.assertEqual(code, 0)
        d = json.loads(out)
        tools = [s["tool"] for s in d["mx_steps"]]
        self.assertEqual(tools, ["add_function_graph", "write_graph_dsl"])
        self.assertEqual(d["mx_steps"][1]["args"]["graph"]["refPath"], "/Game/X/BP_HUD.BP_HUD:Fn")
        self.assertEqual(d["mx_steps"][1]["args"]["code"], d["dsl"])

    def test_apply_creates_function_graph_first(self):
        import subprocess
        calls = []

        class R:
            returncode = 0

        orig = subprocess.run
        subprocess.run = lambda argv, *a, **k: calls.append(argv) or R()
        try:
            self.run_cli("YOU LOSE", "--apply")
        finally:
            subprocess.run = orig
        self.assertEqual([c[4] for c in calls], ["add_function_graph", "write_graph_dsl"])

    def test_apply_continues_if_function_exists_but_stops_on_dsl_failure(self):
        import subprocess
        seen = []

        class R:
            def __init__(self, rc):
                self.returncode = rc

        orig = subprocess.run
        subprocess.run = lambda argv, *a, **k: seen.append(argv[4]) or R(1)
        try:
            code, _, _ = self.run_cli("YOU LOSE", "--apply")
        finally:
            subprocess.run = orig
        self.assertEqual(seen, ["add_function_graph", "write_graph_dsl"])
        self.assertEqual(code, 1)

    def test_box_covers_widest_seen_25px_per_char(self):
        text = "YOU LOSE - PRESS R TO RESTART"
        r = h.build(text)
        self.assertGreaterEqual(r["box"]["x"] + r["box"]["w"], r["text"]["x"] + 25 * len(text))

    def test_opacity_wins_over_box_colour_alpha(self):
        for bc in ("#000000ff", "0,0,0,1"):
            self.assertEqual(h.build("YOU LOSE", box_color=bc, opacity=0.5)["box"]["color"][3], 0.5)

    def test_invisible_text_rejected(self):
        for c in ("#ffcc0000", "1,1,1,0", "1,1,1,0.2"):
            with self.assertRaises(h.ArgError, msg=c):
                h.build("YOU LOSE", color=c)
        h.build("YOU LOSE", color="#ffcc00ff")

    def test_default_screen_is_legion_1920x1200(self):
        b = h.build("YOU LOSE", anchor="center")["box"]
        self.assertAlmostEqual(b["y"] + b["h"] / 2, 600)

    def test_box_covers_mock11_drawn_text(self):
        for text, drawn_w in (("RIBBONS 5 / 5   WASD: walk the kid   R: restart", 880),
                              ("All 5 ribbons in 20 seconds", 545), ("YOU LOSE", 160)):
            r = h.build(text)
            self.assertGreaterEqual(r["box"]["x"] + r["box"]["w"], r["text"]["x"] + drawn_w, text)

    def test_nan_and_inf_rejected(self):
        nan, inf = float("nan"), float("inf")
        for k in ("scale", "padding", "margin", "screen_w", "screen_h", "opacity", "char_w", "line_h"):
            for bad in (nan, inf):
                with self.assertRaises(h.ArgError, msg=f"{k}={bad}"):
                    h.build("hi", **{k: bad})
        with self.assertRaises(h.ArgError):
            h.parse_color("nan,0,0")
        code, out, _ = self.run_cli("hi", "--scale", "nan")
        self.assertEqual((code, out), (2, ""))

    def test_bad_args_exit_2(self):
        code, out, err = self.run_cli("", "--opacity", "2")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("hud_text_box:", err)


if __name__ == "__main__":
    unittest.main()
