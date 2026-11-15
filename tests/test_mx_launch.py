import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(ROOT, "scripts", "launch-editor.sh")


def run_launch(proj_dir, **extra):
    editor = os.path.join(proj_dir, "FakeEditor")
    open(editor, "w").write("#!/bin/sh\nexit 0\n")
    os.chmod(editor, 0o755)
    proj = os.path.join(proj_dir, "Mock.uproject")
    open(proj, "w").write("{}")
    state = os.path.join(proj_dir, "state")  # default helper folder lives under XDG_STATE_HOME
    env = {**os.environ, "MCP_PORT": "1", "WAITFOR_BIN": "/nonexistent/waitfor", "XDG_STATE_HOME": state, **extra}
    return subprocess.run([LAUNCH, editor, proj], capture_output=True, text=True, env=env, timeout=60)


class LaunchCopiesHelper(unittest.TestCase):
    def test_copies_helper_from_repo_outside_the_project(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_launch(d)
            self.assertEqual(r.returncode, 6, r.stderr)  # stopped at the missing waitfor, after the copy
            dest = os.path.join(d, "state", "megajam-mx")
            for f in ("mx.py", "mcp_call.py", "step_shot.py"):
                with open(os.path.join(ROOT, "scripts", f), "rb") as src, open(os.path.join(dest, f), "rb") as dst:
                    self.assertEqual(src.read(), dst.read())
            self.assertIn("helper copied", r.stderr)
            self.assertFalse(os.path.exists(os.path.join(d, "tools")))  # nothing inside the project dir

    def test_mx_dest_override_and_none(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as dest:
            run_launch(d, MX_DEST=dest)
            self.assertTrue(os.path.exists(os.path.join(dest, "mx.py")))
        with tempfile.TemporaryDirectory() as d:
            run_launch(d, MX_DEST="none")
            self.assertFalse(os.path.exists(os.path.join(d, "state")))

    def test_dryrun_copies_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_launch(d, DRYRUN="1", LAUNCH_SCOPE_CMD="none")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(os.path.exists(os.path.join(d, "tools")))


if __name__ == "__main__":
    unittest.main()
