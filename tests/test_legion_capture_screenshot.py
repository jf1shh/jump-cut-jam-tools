import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cap = load("legion_capture_screenshot")
pre = load("legion_preflight")
vp = load("visual_playtest")


def png(kind):
    """A small PNG: 'black' is one colour, 'real' has a gradient of many colours."""
    w, h = 64, 36
    px = bytearray()
    for y in range(h):
        for x in range(w):
            px += b"\x00\x00\x00" if kind == "black" else bytes((x * 4 % 256, y * 7 % 256, (x + y) * 3 % 256))
    path = Path(tempfile.mkdtemp()) / f"{kind}.png"
    vp.write_png(path, w, h, bytes(px))
    return str(path)


def fake_fetch(kind):
    def fetch(host, local_out):
        Path(local_out).write_bytes(Path(png(kind)).read_bytes())
    return fetch


class CaptureLockCheck(unittest.TestCase):
    def main(self, kind, locked=False, extra=()):
        out = str(Path(tempfile.mkdtemp()) / "s.png")
        with mock.patch.object(cap, "deploy_and_register"), \
                mock.patch.object(cap, "trigger_and_wait", return_value=True), \
                mock.patch.object(cap, "fetch", fake_fetch(kind)), \
                mock.patch.object(pre, "console_locked", return_value=locked), \
                mock.patch.object(cap, "_load_preflight", return_value=pre), \
                mock.patch("builtins.print") as pr:
            rc = cap.main(["--out", out, *extra])
        return rc, [str(c.args[0]) for c in pr.call_args_list], out

    def test_real_screen_prints_the_path_and_exits_0(self):
        rc, lines, out = self.main("real")
        self.assertEqual(rc, 0)
        self.assertEqual(lines[-1], out)

    def test_locked_legion_stops_before_any_shot(self):
        with mock.patch.object(cap, "deploy_and_register") as dep:
            rc, lines, _ = self.main("real", locked=True)
        self.assertEqual(rc, 1)
        self.assertTrue(any(pre.MSG_LOCKED in ln for ln in lines))
        dep.assert_not_called()

    def test_black_capture_says_rerun_once(self):
        rc, lines, _ = self.main("black")
        self.assertEqual(rc, 1)
        self.assertTrue(any("capture is black: re-run once before suspecting the build" in ln for ln in lines))

    def test_skip_lock_check_keeps_a_black_shot(self):
        rc, lines, out = self.main("black", locked=True, extra=("--skip-lock-check",))
        self.assertEqual(rc, 0)
        self.assertEqual(lines[-1], out)


class ProbeSafety(unittest.TestCase):
    """Review r1: the probe task is hidden and every remote call is capped and non-interactive."""

    def test_screenshot_task_runs_hidden(self):
        cmds = []
        with mock.patch.object(cap, "run", lambda cmd, **kw: cmds.append(cmd) or mock.Mock(stdout="1")):
            cap.deploy_and_register("device-host", "T")
        self.assertIn("-WindowStyle Hidden", " ".join(str(x) for c in cmds for x in c))

    def test_remote_calls_have_timeout_and_batchmode(self):
        seen = []

        def fake(cmd, **kw):
            seen.append((cmd, kw))
            return mock.Mock(stdout="1", returncode=0)
        with mock.patch.object(cap.subprocess, "run", fake):
            cap.run(["ssh", "device-host", "echo ok"])
            cap.run(["scp", "a", "<device-host>:b"])
        for cmd, kw in seen:
            self.assertEqual(kw["timeout"], cap.CALL_TIMEOUT)
            self.assertIn("BatchMode=yes", cmd)
            self.assertIn("ConnectTimeout=10", cmd)

    def test_black_wait_is_bounded_by_wall_clock_estimate(self):
        seq = iter([None] + [pre.MSG_BLACK] * 20)
        n = []
        b = vp.LegionBackend("device-host", "z", "G", run=lambda c, timeout=0: (0, "1\n", ""),
                             deploy=lambda *a: None, sleep=lambda s: None,
                             probe=lambda: (n.append(1), next(seq))[1])
        with self.assertRaises(RuntimeError):
            b.launch()
        self.assertLessEqual(len(n) - 1, 4)  # about (90-30)/(15+10) + 1 probes, not 7

    def test_black_before_launch_does_not_block_a_relaunch(self):
        """Review r3: the black frame may be the old hung game; only a lock blocks before deploy."""
        seq = iter([pre.MSG_BLACK, None])
        deployed = []
        b = vp.LegionBackend("device-host", "z", "G", run=lambda c, timeout=0: (0, "1\n", ""),
                             deploy=lambda *a: deployed.append(a), sleep=lambda s: None, probe=lambda: next(seq))
        b.launch()
        self.assertEqual(len(deployed), 1)


class ProbeFiles(unittest.TestCase):
    """Review r2: a cut-short PNG is one plain line, and probe folders do not pile up."""
    NONE = staticmethod(lambda h, c: (0, "", ""))

    def probe_dir(self, data):
        d = Path(tempfile.mkdtemp(prefix="legion_probe_"))
        (d / "probe.png").write_bytes(data)
        return str(d / "probe.png")

    def test_truncated_png_is_one_plain_line(self):
        good = Path(png("real")).read_bytes()
        for cut in (len(good) // 2, 40, 12):
            msg = pre.probe_message("device-host", lambda c=cut: self.probe_dir(good[:c]), ssh_fn=self.NONE)
            self.assertIn("not a readable image", msg)
            self.assertNotIn("\n", msg)

    def test_probe_folder_removed_after_reading(self):
        paths = []
        for data in (Path(png("real")).read_bytes(), Path(png("black")).read_bytes(), b"junk"):
            p = self.probe_dir(data)
            paths.append(p)
            pre.probe_message("device-host", lambda p=p: p, ssh_fn=self.NONE)
            self.assertFalse(Path(p).parent.exists())

    def test_cleanup_never_touches_other_folders(self):
        d = Path(tempfile.mkdtemp())
        (d / "x.png").write_bytes(b"x")
        pre.cleanup_probe(str(d / "x.png"))
        self.assertTrue(d.exists())

    def test_take_probe_cleans_up_when_fetch_fails(self):
        made = []
        real = tempfile.mkdtemp
        with mock.patch.object(cap, "deploy_and_register"), \
                mock.patch.object(cap, "trigger_and_wait", return_value=True), \
                mock.patch.object(cap, "fetch", side_effect=RuntimeError("scp failed")), \
                mock.patch("tempfile.mkdtemp", lambda **kw: (made.append(real(**kw)), made[-1])[1]):
            with self.assertRaises(RuntimeError):
                cap.take_probe("device-host")
        self.assertTrue(made)
        self.assertFalse(Path(made[0]).exists())


class ProbeMessage(unittest.TestCase):
    def test_colour_counts(self):
        self.assertLess(pre.count_colours(png("black")), pre.PROBE_MIN_COLOURS)
        self.assertGreaterEqual(pre.count_colours(png("real")), pre.PROBE_MIN_COLOURS)

    def test_logonui_means_locked_without_a_shot(self):
        shot = mock.Mock()
        msg = pre.probe_message("device-host", shot, ssh_fn=lambda h, c: (0, "LogonUI.exe   812 Console", ""))
        self.assertEqual(msg, pre.MSG_LOCKED)
        shot.assert_not_called()

    def test_black_probe_and_real_probe(self):
        none = lambda h, c: (0, "INFO: No tasks are running which match the specified criteria.", "")
        self.assertEqual(pre.probe_message("device-host", lambda: png("black"), ssh_fn=none), pre.MSG_BLACK)
        self.assertIsNone(pre.probe_message("device-host", lambda: png("real"), ssh_fn=none))

    def test_failed_probe_shot_is_one_clear_line(self):
        none = lambda h, c: (0, "", "")

        def boom():
            raise RuntimeError("no fresh screenshot appeared within 20s")
        msg = pre.probe_message("device-host", boom, ssh_fn=none)
        self.assertIn("probe shot failed", msg)
        self.assertNotIn("\n", msg)

    def test_preflight_lock_line_names_the_lock(self):
        facts = {"obsInstalled": True, "obsWebsocket": True, "consoleActive": True, "locked": True}
        self.assertTrue(any("Legion is locked" in f for f in pre.evaluate(facts, "G.exe", check_firewall=False)))


if __name__ == "__main__":
    unittest.main()
