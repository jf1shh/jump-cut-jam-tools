import contextlib
import io
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import greybox_gate as g  # noqa: E402

JAM = "/proj/Jam/Jam.uproject"
MOCK = "/proj/Mock/Mock.uproject"
FLAGS = ["--won", "--lost", "--restarted"]


def run_main(argv):
    """Run main(); argparse exits via SystemExit, report its code like a process would."""
    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
        try:
            return g.main(argv)
        except SystemExit as e:
            return e.code


class GreyboxGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name) / "gb"
        self.sd = ["--state-dir", str(self.d)]
        self.addCleanup(self.tmp.cleanup)

    def test_check_blocks_when_nothing_recorded(self):
        self.assertEqual(run_main(self.sd + ["check", "--project", JAM]), g.EXIT_BLOCKED)

    def test_check_without_project_exits_2(self):
        run_main(self.sd + ["record", "--project", JAM] + FLAGS)
        self.assertEqual(run_main(self.sd + ["check"]), 2)

    def test_record_needs_all_three(self):
        self.assertEqual(run_main(self.sd + ["record", "--project", JAM, "--won", "--lost"]), g.EXIT_USAGE)
        self.assertEqual(run_main(self.sd + ["check", "--project", JAM]), g.EXIT_BLOCKED)

    def test_record_then_check_passes(self):
        self.assertEqual(run_main(self.sd + ["record", "--project", JAM] + FLAGS), g.EXIT_OK)
        self.assertEqual(run_main(self.sd + ["check", "--project", JAM]), g.EXIT_OK)

    def test_mock_marker_never_opens_jam(self):
        run_main(self.sd + ["record", "--project", MOCK] + FLAGS)
        self.assertEqual(run_main(self.sd + ["check", "--project", MOCK]), g.EXIT_OK)
        self.assertEqual(run_main(self.sd + ["check", "--project", JAM]), g.EXIT_BLOCKED)

    def test_marker_does_not_expire(self):
        old = datetime.now().astimezone() - timedelta(hours=40)
        g.record(self.d, True, True, True, JAM, now=old)
        self.assertIsNotNone(g.load(self.d, JAM))

    def test_future_marker_is_blocked(self):
        g.record(self.d, True, True, True, JAM, now=datetime.now().astimezone() + timedelta(hours=2))
        self.assertIsNone(g.load(self.d, JAM))

    def test_line_uses_hhmm(self):
        now = datetime(2026, 11, 9, 14, 5, tzinfo=timezone.utc)
        self.assertEqual(g.line(g.record(self.d, True, True, True, JAM, now=now)), "grey-box loop proven at 14:05")

    def test_run_label_must_match_when_given(self):
        g.record(self.d, True, True, True, JAM, run="a")
        self.assertIsNone(g.load(self.d, JAM, run="b"))
        self.assertIsNotNone(g.load(self.d, JAM, run="a"))
        self.assertIsNotNone(g.load(self.d, JAM))

    def test_clear_removes_marker(self):
        g.record(self.d, True, True, True, JAM)
        self.assertTrue(g.clear(self.d))
        self.assertEqual(run_main(self.sd + ["check", "--project", JAM]), g.EXIT_BLOCKED)
        self.assertFalse(g.clear(self.d))

    def test_bad_content_is_blocked(self):
        self.d.mkdir(parents=True)
        for bad in ('{"hhmm": null}', '{"hhmm": "14:05"}', '[1]', '{"hhmm": "x", "proven_at": "y"}', "{not json"):
            (self.d / g.MARKER).write_text(bad, encoding="utf-8")
            self.assertIsNone(g.load(self.d, JAM), bad)

    def test_state_dir_option_after_subcommand(self):
        self.assertEqual(run_main(["check", "--project", JAM, "--state-dir", str(self.d)]), g.EXIT_BLOCKED)

    def test_status_without_project_shows_stored_marker(self):
        g.record(self.d, True, True, True, JAM, run="r1")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(g.main(self.sd + ["status"]), g.EXIT_OK)
        out = buf.getvalue()
        self.assertIn("project not checked", out)
        self.assertIn(JAM, out)
        self.assertNotIn("not proven", out)

    def test_status_without_project_and_no_marker(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            g.main(self.sd + ["status"])
        self.assertIn("not proven", buf.getvalue())

    def test_record_and_check_from_other_cwds_share_marker(self):
        import os
        import subprocess
        script = str(Path(g.__file__).resolve())
        env = {k: v for k, v in os.environ.items() if k != "GREYBOX_GATE_DIR"}
        proj = str(Path(self.tmp.name) / "game" / "G.uproject")
        a, b = Path(self.tmp.name) / "a", Path(self.tmp.name) / "b"
        a.mkdir()
        b.mkdir()
        try:
            r = subprocess.run([sys.executable, script, "record", "--project", proj] + FLAGS,
                               cwd=a, env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            c = subprocess.run([sys.executable, script, "check", "--project", proj],
                               cwd=b, env=env, capture_output=True, text=True)
            self.assertEqual(c.returncode, 0, c.stderr)
        finally:
            subprocess.run([sys.executable, script, "clear"], cwd=b, env=env, capture_output=True, text=True)

    def test_default_dir_is_repo_anchored_not_cwd(self):
        self.assertTrue(g.state_dir().is_absolute())


if __name__ == "__main__":
    unittest.main()
