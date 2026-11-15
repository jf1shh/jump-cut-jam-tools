import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import presubmit_gate as g  # noqa: E402


def line(label, mats, visible=True):
    return "VERIFY_ACTOR_JSON=" + json.dumps({"label": label, "materials": mats, "visible": visible})


GRID = "/Engine/EngineMaterials/WorldGridMaterial"


def complete(text, count=None):
    """Wrap record lines the way a finished verify run prints them."""
    n = text.count("VERIFY_ACTOR_JSON=") if count is None else count
    return f"VERIFY_ACTOR_COUNT={n}\n{text}\nVERIFY_DONE\n"


class Gate(unittest.TestCase):
    def go(self, text, raw=False, **kw):
        buf = io.StringIO()
        return g.run(text if raw else complete(text), out=buf, **kw), buf.getvalue()

    def test_unreal_log_prefix(self):
        pre = "[2026.11.09-19.13.42:749][  0]LogPython: "
        text = (pre + "VERIFY_ACTOR_COUNT=2\n" + pre + line("Floor", [GRID]) + "\n" + pre + line("W", []) + "\n"
                + pre + "VERIFY_DONE\n")
        code, out = self.go(text, raw=True)
        self.assertEqual(code, 1)
        self.assertIn("GATE_FAIL Floor", out)

    def test_truncated_log_is_error(self):
        text = "VERIFY_ACTOR_COUNT=3\n" + line("Wall", ["/Game/M_Wall"]) + "\n"  # no DONE, 1 of 3
        code, out = self.go(text, raw=True)
        self.assertEqual(code, 2)
        self.assertIn("incomplete", out)

    def test_count_mismatch_even_with_done(self):
        self.assertEqual(g.run(complete(line("A", []), count=2), out=io.StringIO()), 2)

    def test_done_without_count_is_error(self):
        self.assertEqual(self.go(line("A", []) + "\nVERIFY_DONE\n", raw=True)[0], 2)

    def test_pass(self):
        code, out = self.go("VERIFY_WORLD=x\n" + line("Floor", ["/Game/M_Floor"]))
        self.assertEqual(code, 0)
        self.assertIn("GATE_PASS actors=1", out)

    def test_visible_grid_fails(self):
        code, out = self.go(line("Floor", [GRID]) + "\n" + line("Wall", ["/Game/M_Wall"]))
        self.assertEqual(code, 1)
        self.assertIn("GATE_FAIL Floor shows default material", out)
        self.assertIn("violations=1", out)

    def test_hidden_grid_ignored(self):
        self.assertEqual(self.go(line("Proxy", [GRID], visible=False))[0], 0)

    def test_checker_one_of_many_slots(self):
        self.assertEqual(self.go(line("Statue", ["/Game/M_A", "/Game/T/M_Checker"]))[0], 1)

    def test_empty_log_is_not_a_pass(self):
        code, out = self.go("VERIFY_DONE\n")
        self.assertEqual(code, 2)
        self.assertIn("GATE_ERROR", out)

    def test_garbage_lines_skipped(self):
        text = complete("VERIFY_ACTOR_JSON={bad json\n" + line("A", []), count=1)
        self.assertEqual(g.run(text, out=io.StringIO()), 0)

    def test_json_output(self):
        code, out = self.go(line("Floor", [GRID]), as_json=True)
        data = json.loads(out)
        self.assertEqual((code, data["pass"], data["violations"][0]["label"]), (1, False, "Floor"))

    def test_main_file_and_missing(self):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
            f.write(complete(line("Floor", [GRID])))
        self.addCleanup(os.unlink, f.name)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(g.main([f.name]), 1)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(g.main(["/nonexistent/x.log"]), 2)
            self.assertEqual(g.main([]), 2)


if __name__ == "__main__":
    unittest.main()
