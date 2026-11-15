"""Gate flags on asset_preview, plus --detach/--wait on asset_chain.py and build_world.py (ticket T-20261108-19)."""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import asset_chain as C  # noqa: E402
import asset_preview as A  # noqa: E402
import build_world as W  # noqa: E402


class AspectGate(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(A.parse_aspect("1:1.2"), (1.0, 1.2, 0.25))
        self.assertEqual(A.parse_aspect("2:3:0.1"), (2.0, 3.0, 0.1))
        for bad in ("1", "a:b", "1:0", "1:2:3:4", "1:2:-1"):
            with self.assertRaises(ValueError):
                A.parse_aspect(bad)

    def test_flat_balloon_fails(self):
        flag = A.aspect_flag([1.0, 1.0, 0.05], A.parse_aspect("1:1.2"))
        self.assertEqual(flag["code"], "aspect_mismatch")
        self.assertEqual(flag["level"], "error")

    def test_right_shape_passes_and_tol_widens(self):
        self.assertIsNone(A.aspect_flag([1.0, 0.9, 1.2], A.parse_aspect("1:1.2")))
        self.assertIsNotNone(A.aspect_flag([1.0, 1.0, 0.8], A.parse_aspect("1:1.2")))
        self.assertIsNone(A.aspect_flag([1.0, 1.0, 0.8], A.parse_aspect("1:1.2:0.5")))

    def test_zero_height_fails(self):
        self.assertIsNotNone(A.aspect_flag([1.0, 1.0, 0.0], A.parse_aspect("1:1")))

    def test_flat_relief_fails_thin_footprint_check_by_default(self):
        flag = A.aspect_flag([1.0, 0.05, 1.2], A.parse_aspect("1:1.2"))
        self.assertEqual(flag["code"], "aspect_mismatch")
        self.assertIn("thin", flag["msg"])
        self.assertIn("--allow-thin", flag["msg"])
        self.assertIsNone(A.aspect_flag([1.0, 0.05, 1.2], A.parse_aspect("1:1.2"), min_depth=0))

    def test_thin_door_passes_aspect_with_min_depth_zero(self):
        self.assertIsNone(A.aspect_flag([1.0, 0.05, 2.0], A.parse_aspect("1:2"), min_depth=0))

    def test_allow_thin_flag_is_parsed(self):
        import argparse
        src = (SCRIPTS / "asset_preview.py").read_text()
        self.assertIn('"--allow-thin"', src)
        self.assertIn("0.0 if ns.allow_thin else ns.min_depth", src)

    def test_max_scale_tightens_the_size_limit(self):
        s = {"mesh_objects": 1, "tris": 10, "size_m": [3.0, 1.0, 1.0], "materials": [{"name": "m"}],
             "textures": [{"role": "albedo", "name": "a", "exists": True}]}
        self.assertNotIn("scale_too_big", {f["code"] for f in A.compute_flags(s)})
        self.assertIn("scale_too_big", {f["code"] for f in A.compute_flags(s, max_m=2.0)})

    def test_cli_rejects_bad_flags(self):
        with self.assertRaises(SystemExit):
            A.main(["x", "--expect-aspect", "nope"])
        with self.assertRaises(SystemExit):
            A.main(["x", "--max-scale", "0"])


class ScaleCheck(unittest.TestCase):
    def test_catches_giant_tiny_and_flat(self):
        probs = W.check_scales([
            {"name": "ok", "scale": 1.5},
            {"name": "giant", "scale": 400},
            {"name": "tiny", "scale": [0.01, 0.01, 0.01]},
            {"name": "flat", "scale": [1, 1, 0]},
        ])
        joined = "\n".join(probs)
        for name in ("giant", "tiny", "flat"):
            self.assertIn(name, joined)
        self.assertNotIn("ok:", joined)

    def test_blockout_floor_and_wall_are_fine(self):
        self.assertEqual(W.check_scales([{"name": "Floor", "scale": [20, 20, 1]},
                                         {"name": "Wall", "scale": [8, 1, 3]}]), [])

    def test_stale_scale_on_reshaped_mesh_is_caught_via_bounds(self):
        # balloon should be ~1.2 m; mesh now 0.1 m and the old 3,3,3 scale was left on: 0.3 m
        probs = W.check_scales([{"name": "Balloon", "scale": [3, 3, 3], "bounds_m": [0.1, 0.1, 0.1],
                                 "expect_size_m": 1.2}])
        self.assertTrue(any("Balloon" in p and "expected" in p for p in probs), probs)
        self.assertEqual(W.check_scales([{"name": "Balloon", "scale": 1, "bounds_m": [1, 1, 1.2],
                                          "expect_size_m": 1.2}]), [])
        self.assertTrue(W.check_scales([{"name": "B", "scale": 1, "expect_size_m": 1.2}]))  # needs bounds
        self.assertTrue(W.check_scales([{"name": "B", "scale": 30, "bounds_m": [10, 1, 1]}]))  # 300 m

    def test_main_check_only(self):
        with tempfile.TemporaryDirectory() as td:
            good, bad = Path(td, "good.json"), Path(td, "bad.json")
            good.write_text(json.dumps({"actors": [{"name": "a", "scale": 1}]}))
            bad.write_text(json.dumps([{"name": "a", "scale": [1, 1, 0]}]))
            self.assertEqual(W.main(["--check-only", "--placements", str(good)]), 0)
            self.assertEqual(W.main(["--check-only", "--placements", str(bad)]), 1)
            self.assertEqual(W.main(["--check-only", "--placements", str(Path(td, "missing.json"))]), 2)

    def test_build_failure_skips_check(self):
        self.assertEqual(W.main(["--", sys.executable, "-c", "raise SystemExit(7)"]), 7)


class Detach(unittest.TestCase):
    def run_detached(self, td, code, extra=()):
        log, done = Path(td, "j.log"), Path(td, "j.done")
        rc = W.main(["--detach", "--detach-log", str(log), "--done-file", str(done), *extra,
                     "--", sys.executable, "-c", code])
        self.assertEqual(rc, 0)
        return log, done

    def test_detached_build_writes_log_pid_and_done(self):
        with tempfile.TemporaryDirectory() as td:
            log, done = self.run_detached(td, "print('built')")
            self.assertEqual(C.wait_done(done, timeout=30, interval=0.1, out=lambda m: None), 0)
            self.assertEqual(done.read_text().strip(), "exit=0")
            self.assertIn("built", log.read_text())
            self.assertTrue(Path(str(done) + ".pid").read_text().strip().isdigit())

    def test_failure_exit_code_reaches_the_waiter(self):
        with tempfile.TemporaryDirectory() as td:
            _, done = self.run_detached(td, "raise SystemExit(5)")
            self.assertEqual(W.main(["--wait", str(done), "--wait-timeout", "30"]), 5)

    def test_wait_prints_pid_at_arm_time(self):
        with tempfile.TemporaryDirectory() as td:
            _, done = self.run_detached(td, "pass")
            lines = []
            C.wait_done(done, timeout=30, interval=0.1, out=lines.append)
            pid = Path(str(done) + ".pid").read_text().strip()
            self.assertIn(f"driver pid {pid}", lines[0])

    def test_dead_driver_without_done_file_exits_3(self):
        with tempfile.TemporaryDirectory() as td:
            done = Path(td, "d.done")
            Path(str(done) + ".pid").write_text("999999\n")  # no such process
            lines = []
            self.assertEqual(C.wait_done(done, timeout=5, interval=0.1, out=lines.append), 3)
            self.assertIn("gone", lines[-1])

    def test_wait_times_out_on_live_driver(self):
        with tempfile.TemporaryDirectory() as td:
            done = Path(td, "d.done")
            Path(str(done) + ".pid").write_text(f"{os.getpid()}\n")
            self.assertEqual(C.wait_done(done, timeout=0.3, interval=0.1, out=lambda m: None), 4)

    def test_armed_waiter_keeps_its_own_runs_verdict(self):
        import threading
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            a, b = td / "a.py", td / "b.py"
            a.write_text("import time; time.sleep(3)\n")
            b.write_text("raise SystemExit(7)\n")
            done, log = td / "j.done", td / "j.log"
            pid_a = C.detach(a, [], log, done, python=sys.executable)
            res = {}

            def waiter():
                res["rc"] = C.wait_done(done, timeout=30, interval=0.1, out=lambda m: None)
                res["a_alive"] = C.pid_alive(pid_a)
            t = threading.Thread(target=waiter)
            t.start()
            time.sleep(0.5)
            C.detach(b, [], log, done, python=sys.executable)
            t.join(40)
            self.assertEqual(res.get("rc"), 0, res)
            self.assertFalse(res.get("a_alive"), res)

    def test_wait_rereads_done_file_before_declaring_driver_dead(self):
        with tempfile.TemporaryDirectory() as td:
            done = Path(td, "r.done")
            Path(str(done) + ".pid").write_text("999999\n")  # dead pid
            real = C.pid_alive

            def racing_alive(pid):  # the run writes its verdict just before we look at the pid
                Path(f"{done}.{pid}").write_text("exit=0\n")
                return False
            C.pid_alive = racing_alive
            try:
                self.assertEqual(C.wait_done(done, timeout=5, interval=0.1, out=lambda m: None), 0)
            finally:
                C.pid_alive = real

    def test_leftover_per_run_file_does_not_answer_a_live_run(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            job = td / "job.py"
            job.write_text("import time; time.sleep(2)\n")
            done = td / "l.done"
            pid = C.detach(job, [], td / "l.log", done, python=sys.executable)
            Path(f"{done}.{pid}").write_text("exit=9\n")  # stale verdict placed while the run is live
            t0 = time.monotonic()
            rc = C.wait_done(done, timeout=20, interval=0.1, out=lambda m: None)
            self.assertGreater(time.monotonic() - t0, 1.0)
            self.assertEqual(rc, 0)

    def test_detach_clears_stale_per_pid_done_file(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            job = td / "j.py"
            job.write_text("import time; time.sleep(2)\n")
            done = td / "s.done"
            real = C.subprocess.Popen

            class Fake:
                pid = 424242
            C.subprocess.Popen = lambda *a, **k: Fake()
            Path(f"{done}.424242").write_text("exit=9\n")  # leftover from an older run with this pid
            try:
                C.detach(job, [], td / "s.log", done)
            finally:
                C.subprocess.Popen = real
            self.assertFalse(Path(f"{done}.424242").exists())

    def test_second_detach_on_same_done_file_waits_for_the_second_run(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            a, b = td / "a.py", td / "b.py"
            a.write_text("import time; time.sleep(1)\n")
            b.write_text("import time; time.sleep(3); raise SystemExit(5)\n")
            done, log = td / "j.done", td / "j.log"
            C.detach(a, [], log, done, python=sys.executable)
            pid_b = C.detach(b, [], log, done, python=sys.executable)
            self.assertEqual(C.wait_done(done, timeout=30, interval=0.1, out=lambda m: None), 5)
            self.assertTrue((td / f"j.done.{pid_b}").is_file())  # per-run done-file

    def test_build_command_after_dashdash_is_passed_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            out, prog, done = td / "argv.txt", td / "prog.py", td / "b.done"
            prog.write_text("import sys, pathlib; pathlib.Path(sys.argv[1]).write_text(' '.join(sys.argv[2:]))\n")
            rc = W.main(["--detach", "--detach-log", str(td / "b.log"), "--done-file", str(done),
                         "--", sys.executable, str(prog), str(out), "--wait-timeout", "30", "-x"])
            self.assertEqual(rc, 0)
            self.assertEqual(C.wait_done(done, timeout=30, interval=0.1, out=lambda m: None), 0)
            self.assertEqual(out.read_text(), "--wait-timeout 30 -x")

    def test_stale_done_file_is_cleared_on_detach(self):
        with tempfile.TemporaryDirectory() as td:
            done = Path(td, "j.done")
            done.write_text("exit=9\n")
            C.detach(__file__, [], Path(td, "j.log"), done, python="true")
            # right after launch the old verdict must not be visible as the new result
            deadline = time.time() + 10
            while time.time() < deadline and done.read_text().strip() == "exit=9" if done.exists() else False:
                time.sleep(0.05)
            self.assertNotEqual(done.read_text().strip() if done.exists() else "", "exit=9")

    def test_asset_chain_detach_flags_parse_and_strip(self):
        a = C.parse_args(["--detach", "--name", "x", "--prompt", "p", "--done-file", "/tmp/d"])
        self.assertTrue(a.detach)
        self.assertEqual(a.done_file, "/tmp/d")
        self.assertEqual(C.parse_args(["--wait", "/tmp/d"]).wait, "/tmp/d")
        with tempfile.TemporaryDirectory() as td:
            done = Path(td, "c.done")
            rc = C.main(["--detach", "--list-engines", "--detach-log", str(Path(td, "c.log")), "--done-file", str(done)])
            self.assertEqual(rc, 0)
            self.assertEqual(C.wait_done(done, timeout=60, interval=0.2, out=lambda m: None), 0)
            self.assertIn("licence=", Path(td, "c.log").read_text())


if __name__ == "__main__":
    unittest.main()
