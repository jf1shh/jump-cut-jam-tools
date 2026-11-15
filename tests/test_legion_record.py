import importlib.util
import json
import math
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location("legion_record", os.path.join(ROOT, "scripts", "legion_record.py"))
rec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rec)

HAVE_FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


def make_mp4(path, source):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", source, "-t", "4",
                    "-pix_fmt", "yuv420p", str(path)], check=True)


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class FrameCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.black = d / "black.mp4"
        cls.normal = d / "normal.mp4"
        cls.solid = d / "solid.mp4"
        make_mp4(cls.black, "color=c=black:s=320x180:r=10")
        make_mp4(cls.normal, "testsrc2=s=320x180:r=10")
        make_mp4(cls.solid, "color=c=0x1030c0:s=320x180:r=10")  # blue-screen style
        cls.junk = d / "junk.mp4"
        cls.junk.write_bytes(b"not a video")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_normal_passes(self):
        ok, problems = rec.check_video(self.normal)
        self.assertTrue(ok, problems)
        self.assertEqual(problems, [])

    def test_black_fails(self):
        ok, problems = rec.check_video(self.black)
        self.assertFalse(ok)
        self.assertTrue(all("black" in p for p in problems))
        self.assertEqual(len(problems), 5)

    def test_solid_colour_fails_as_flat(self):
        ok, problems = rec.check_video(self.solid)
        self.assertFalse(ok)
        self.assertIn("flat", problems[0])

    def test_corrupt_fails(self):
        ok, problems = rec.check_video(self.junk)
        self.assertFalse(ok)
        self.assertIn("duration", problems[0])

    def test_too_short_fails(self):
        ok, problems = rec.check_video(self.normal, min_seconds=60)
        self.assertFalse(ok)
        self.assertIn("expected at least", problems[0])


class ParseRecordJson(unittest.TestCase):
    def test_fail_lines_before_json(self):
        text = "FAIL GetFoo : 600 nope\n" + json.dumps({"recordFile": "C:\\v\\a.mp4"}, indent=2)
        data, fails = rec.parse_record_json(text)
        self.assertEqual(data["recordFile"], "C:\\v\\a.mp4")
        self.assertEqual(len(fails), 1)

    def test_no_json(self):
        self.assertEqual(rec.parse_record_json("FAIL x\nboom"), (None, ["FAIL x"]))


class Obs(unittest.TestCase):
    def test_already_up_no_task_created(self):
        calls = []

        def fake(cmd, timeout=0):
            calls.append(cmd[-1])
            return 0, "True\n", ""
        with mock.patch.object(rec, "run", side_effect=fake):
            self.assertFalse(rec.start_obs("device-host", sleep=lambda s: None))
        self.assertFalse(any("schtasks" in c for c in calls))

    def test_waits_for_websocket_then_starts_without_hang_flags(self):
        state = {"polls": 0}
        calls = []

        def fake(cmd, timeout=0):
            c = cmd[-1]
            calls.append(c)
            if "Test-NetConnection" in c:
                state["polls"] += 1
                return 0, ("True\n" if state["polls"] >= 5 else "False\n"), ""
            return 0, "", ""
        with mock.patch.object(rec, "run", side_effect=fake):
            self.assertTrue(rec.start_obs("device-host", sleep=lambda s: None))
        create = [c for c in calls if "/Create" in c][0]
        self.assertNotIn("--minimize-to-tray", create)
        self.assertNotIn("--disable-updater", create)
        self.assertIn("MJToolObsStart", create)
        self.assertIn("/IT", create)

    def test_never_answers_raises(self):
        def fake(cmd, timeout=0):
            return 0, "False\n", ""
        with mock.patch.object(rec, "run", side_effect=fake):
            with self.assertRaises(RuntimeError):
                rec.start_obs("device-host", wait_s=9, interval=3, sleep=lambda s: None)

    def test_close_is_polite_then_force_only_if_alive(self):
        calls = []

        def fake(cmd, timeout=0):
            c = cmd[-1]
            calls.append(c)
            return 0, ("" if "Select-Object -ExpandProperty Id" in c else ""), ""
        with mock.patch.object(rec, "run", side_effect=fake):
            self.assertTrue(rec.close_process("device-host", "Game", sleep=lambda s: None))
        self.assertTrue(any("CloseMainWindow" in c for c in calls))
        self.assertFalse(any("Stop-Process" in c or "taskkill" in c for c in calls))

    def test_close_runs_in_console_session_task(self):
        """ssh is not the window's session, so CloseMainWindow must run via an /IT task, which is cleaned up."""
        calls = []

        def fake(cmd, timeout=0):
            calls.append(cmd[-1])
            return 0, "", ""
        with mock.patch.object(rec, "run", side_effect=fake):
            rec.close_process("device-host", "Game", sleep=lambda s: None)
        create = [c for c in calls if "/Create /TN MJToolCloseGame" in c][0]
        self.assertIn("/IT", create)
        self.assertIn("CloseMainWindow", create)
        self.assertTrue(any("/Run /TN MJToolCloseGame" in c for c in calls))
        self.assertTrue(any("/Delete /TN MJToolCloseGame" in c for c in calls))

    def test_obs_timeout_closes_our_obs_and_uses_flag(self):
        calls = []

        def fake(cmd, timeout=0):
            calls.append(cmd[-1])
            if "Get-Process obs64" in cmd[-1]:
                return 0, "99\n", ""  # OBS stays alive, so the forced stop must follow
            return 0, ("False\n" if "Test-NetConnection" in cmd[-1] else ""), ""
        with mock.patch.object(rec, "run", side_effect=fake), \
                mock.patch.object(rec.playtest, "deploy_and_register", return_value={}):
            with self.assertRaises(RuntimeError):
                rec.one_take(Orchestration.args(None, "/tmp/x"), sleep=lambda s: None)
        self.assertTrue(any("--disable-shutdown-check" in c for c in calls if "/Create" in c))
        self.assertTrue(any("obs64" in c and "Stop-Process" in c for c in calls))

    def test_trigger_disabled_when_run_fails(self):
        calls = []

        def fake(cmd, timeout=0):
            calls.append(cmd[-1])
            if "/Run /TN T" in cmd[-1]:
                return 1, "", "no"
            return 0, ("True\n" if "Test-NetConnection" in cmd[-1] else ""), ""
        with mock.patch.object(rec, "run", side_effect=fake), \
                mock.patch.object(rec.playtest, "deploy_and_register", return_value={}):
            ok, _, _ = rec.one_take(Orchestration.args(None, "/tmp/x"), sleep=lambda s: None)
        self.assertFalse(ok)
        self.assertTrue(any("Disable-ScheduledTask -TaskName T" in c for c in calls))

    def test_trigger_disabled_when_firewall_fails(self):
        calls = []

        def fake(cmd, timeout=0):
            calls.append(cmd[-1])
            return 0, ("True\n" if "Test-NetConnection" in cmd[-1] else ""), ""
        with mock.patch.object(rec, "run", side_effect=fake), \
                mock.patch.object(rec.playtest, "deploy_and_register", return_value={"exePath": "C:\\g\\Game.exe"}), \
                mock.patch.object(rec.pre, "collect", return_value=({}, None)), \
                mock.patch.object(rec.pre, "evaluate", return_value=["No inbound firewall allow rule"]):
            ok, _, _ = rec.one_take(Orchestration.args(None, "/tmp/x"), sleep=lambda s: None)
        self.assertFalse(ok)
        self.assertTrue(any("Disable-ScheduledTask -TaskName T" in c for c in calls))

    def test_existing_obs_is_never_killed(self):
        calls = []

        def fake(cmd, timeout=0):
            calls.append(cmd[-1])
            if "Get-Process obs64" in cmd[-1]:
                return 0, "99\n", ""
            return 0, ("True\n" if "Test-NetConnection" in cmd[-1] else ""), ""
        with mock.patch.object(rec, "run", side_effect=fake), \
                mock.patch.object(rec.playtest, "deploy_and_register", side_effect=RuntimeError("stop")):
            with self.assertRaises(RuntimeError):
                rec.one_take(Orchestration.args(None, "/tmp/x"), sleep=lambda s: None)
        self.assertFalse(any("obs64" in c and "Stop-Process" in c for c in calls))

    def test_trigger_disabled_after_run(self):
        calls = []

        def fake(cmd, timeout=0):
            calls.append(cmd[-1])
            return 0, ("True\n" if "Test-NetConnection" in cmd[-1] else ""), ""
        with mock.patch.object(rec, "run", side_effect=fake), \
                mock.patch.object(rec.playtest, "deploy_and_register", return_value={}):
            rec.one_take(Orchestration.args(None, "/tmp/x"), sleep=lambda s: None)
        i = next(n for n, c in enumerate(calls) if "/Run /TN T" in c)
        self.assertTrue(any("Disable-ScheduledTask -TaskName T" in c for c in calls[i + 1:]))

    def test_close_forces_when_stuck(self):
        calls = []

        def fake(cmd, timeout=0):
            c = cmd[-1]
            calls.append(c)
            return 0, ("123\n" if "Select-Object -ExpandProperty Id" in c else ""), ""
        with mock.patch.object(rec, "run", side_effect=fake):
            self.assertFalse(rec.close_process("device-host", "Game", sleep=lambda s: None))
        self.assertTrue(any("Stop-Process" in c for c in calls))
        self.assertFalse(any("taskkill" in c for c in calls))


class Orchestration(unittest.TestCase):
    def args(self, out_dir):
        return SimpleNamespace(host="device-host", remote_zip="C:\\z.zip", game_name="Game", task_name="T",
                               seconds=4, replay_seconds=1, warmup=0, out_dir=out_dir, keep_obs=False)

    def test_retry_once_then_success(self):
        takes = [(False, Path("a.mp4"), ["frame at 1.0s is black"]), (True, Path("b.mp4"), [])]
        with mock.patch.object(rec, "one_take", side_effect=takes), \
                mock.patch.object(rec.pre, "main", return_value=0), \
                mock.patch.object(rec.pre, "probe_message", return_value=None):
            rc = rec.main(["--remote-zip", "z", "--game-name", "Game"])
        self.assertEqual(rc, 0)

    def test_exception_then_failure_returns_one(self):
        with mock.patch.object(rec, "one_take", side_effect=RuntimeError("boom")) as m, \
                mock.patch.object(rec.pre, "main", return_value=0), \
                mock.patch.object(rec.pre, "probe_message", return_value=None):
            rc = rec.main(["--remote-zip", "z", "--game-name", "Game"])
        self.assertEqual(rc, 1)
        self.assertEqual(m.call_count, 2)

    def test_preflight_failure_blocks(self):
        with mock.patch.object(rec.pre, "main", return_value=1), \
                mock.patch.object(rec, "one_take") as m:
            self.assertEqual(rec.main(["--remote-zip", "z", "--game-name", "Game"]), 1)
        m.assert_not_called()

    def test_one_take_end_to_end_with_fake_legion(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []

            def fake_run(cmd, timeout=0):
                c = cmd[-1] if cmd[0] == "ssh" else " ".join(cmd)
                calls.append(c)
                if cmd[0] == "ssh" and "Test-NetConnection" in c:
                    return 0, "True\n", ""
                if cmd[0] == "ssh" and "Get-Process Game" in c:
                    return 0, ("" if any("Stop-Process" in x or "/Run /TN MJToolCloseGame" in x for x in calls) else "123\n"), ""
                if cmd[0] == "ssh" and "legion_obs_record_test.ps1" in c and "-File" in c:
                    return 0, json.dumps({"recordFile": "C:\\Videos\\take.mp4"}, indent=2), ""
                if cmd[0] == "scp" and cmd[-2].startswith("<device-host>:"):
                    Path(cmd[-1]).write_bytes(b"x")
                return 0, "", ""
            with mock.patch.object(rec, "run", side_effect=fake_run), \
                    mock.patch.object(rec.playtest, "deploy_and_register", return_value={"logPath": "x"}), \
                    mock.patch.object(rec, "check_video", return_value=(True, [])):
                ok, local, problems = rec.one_take(self.args(tmp), sleep=lambda s: None)
            self.assertTrue(ok)
            self.assertEqual(local.name, "take.mp4")
            self.assertTrue(any("/Run /TN T" in c for c in calls))
            self.assertTrue(any("/Delete /TN MJToolObsStart" in c for c in calls))
            self.assertFalse(any("taskkill" in c for c in calls))

    def test_content_only_package_launches_engine_exe_and_watches_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []

            def fake_run(cmd, timeout=0):
                c = cmd[-1] if cmd[0] == "ssh" else " ".join(cmd)
                calls.append(c)
                if cmd[0] == "ssh" and "Test-NetConnection" in c:
                    return 0, "True\n", ""
                if cmd[0] == "ssh" and "Get-Process UnrealGame" in c:
                    return 0, ("" if any("Stop-Process" in x or "/Run /TN MJToolCloseUnrealGame" in x for x in calls) else "9\n"), ""
                if cmd[0] == "ssh" and "legion_obs_record_test.ps1" in c and "-File" in c:
                    return 0, json.dumps({"recordFile": "C:\\Videos\\take.mp4"}, indent=2), ""
                if cmd[0] == "scp" and cmd[-2].startswith("<device-host>:"):
                    Path(cmd[-1]).write_bytes(b"x")
                return 0, "", ""
            with mock.patch.dict(os.environ, {"MJ_GAME_PROC": "UnrealGame"}), \
                    mock.patch.object(rec, "run", side_effect=fake_run), \
                    mock.patch.object(rec.playtest, "deploy_and_register",
                                      return_value={"exePath": "C:\\Dev\\Game\\Game.exe"}), \
                    mock.patch.object(rec.pre, "collect", return_value=({}, None)) as collect, \
                    mock.patch.object(rec.pre, "evaluate", return_value=[]) as evaluate, \
                    mock.patch.object(rec, "check_video", return_value=(True, [])):
                ok, _, problems = rec.one_take(self.args(tmp), sleep=lambda s: None)
            self.assertTrue(ok, problems)
            # the firewall check covers the engine exe that really runs, not the stub exe
            collect.assert_called_once()
            self.assertEqual(evaluate.call_args.args[1:3],
                             ("UnrealGame.exe", "C:\\Dev\\Game\\Engine\\Binaries\\Win64\\UnrealGame.exe"))
            repoint = [i for i, c in enumerate(calls) if "Set-ScheduledTask -TaskName T " in c]
            run_at = [i for i, c in enumerate(calls) if "schtasks /Run /TN T" in c and "Close" not in c]
            self.assertEqual(len(repoint), 1)
            self.assertIn("UnrealGame.exe", calls[repoint[0]])
            self.assertIn("..\\..\\..\\Game\\Game.uproject", calls[repoint[0]])
            self.assertLess(repoint[0], run_at[0])  # repointed before the task runs
            self.assertFalse(any("Get-Process Game " in c for c in calls))


class GameProcess(unittest.TestCase):
    def test_repoint_failure_returns_a_failed_take_without_running_the_task(self):
        calls = []

        def fake_run(cmd, timeout=0):
            calls.append(cmd[-1])
            return (1, "", "access denied") if "Set-ScheduledTask" in cmd[-1] else (0, "", "")
        args = SimpleNamespace(host="device-host", remote_zip="z", game_name="Game", task_name="T", seconds=4,
                               replay_seconds=1, warmup=0, out_dir="/tmp", keep_obs=False)
        with mock.patch.dict(os.environ, {"MJ_GAME_PROC": "UnrealGame"}), \
                mock.patch.object(rec, "run", side_effect=fake_run), \
                mock.patch.object(rec, "start_obs"), \
                mock.patch.object(rec.playtest, "deploy_and_register", return_value={}):
            ok, local, problems = rec.one_take(args, sleep=lambda s: None)
        self.assertFalse(ok)
        self.assertIn("access denied", problems[0])
        self.assertFalse(any("schtasks /Run /TN T" in c for c in calls))

    def test_default_is_game_name(self):
        self.assertEqual(rec.game_process("Game", env={}), "Game")

    def test_override_from_env(self):
        self.assertEqual(rec.game_process("Game", env={"MJ_GAME_PROC": "UnrealGame"}), "UnrealGame")

    def test_unsafe_override_is_rejected(self):
        with self.assertRaises(ValueError):
            rec.game_process("Game", env={"MJ_GAME_PROC": "x; calc"})

    def test_no_override_leaves_launch_untouched(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MJ_GAME_PROC", None)
            calls = []
            with mock.patch.object(rec, "run", side_effect=lambda cmd, timeout=0: (calls.append(cmd[-1]), (0, "", ""))[1]), \
                    mock.patch.object(rec, "start_obs"), \
                    mock.patch.object(rec.playtest, "deploy_and_register", return_value={}):
                rec.one_take(SimpleNamespace(host="device-host", remote_zip="z", game_name="Game", task_name="T", seconds=4,
                                             replay_seconds=1, warmup=0, out_dir="/tmp", keep_obs=False),
                             sleep=lambda s: None)
        self.assertFalse(any("Set-ScheduledTask" in c for c in calls))


class LockProbe(unittest.TestCase):
    """T-20261108-32: a locked or black Legion stops legion_record in one line, before OBS or the game."""

    def run_main(self, probe_msg, extra=()):
        with mock.patch.object(rec.pre, "main", return_value=0), \
                mock.patch.object(rec.pre, "probe_message", return_value=probe_msg), \
                mock.patch.object(rec, "one_take") as take, \
                mock.patch("builtins.print") as pr:
            rc = rec.main(["--remote-zip", "z", "--game-name", "G", *extra])
        return rc, take, [str(c.args[0]) for c in pr.call_args_list]

    def test_locked_console_says_so_and_names_obs(self):
        rc, take, lines = self.run_main(rec.pre.MSG_LOCKED)
        self.assertEqual(rc, 1)
        take.assert_not_called()
        self.assertEqual(len(lines), 1)
        self.assertIn("Legion is locked", lines[0])
        self.assertIn("OBS cannot start on a locked console", lines[0])

    def test_black_probe_says_rerun_once(self):
        rc, take, lines = self.run_main(rec.pre.MSG_BLACK)
        self.assertEqual(rc, 1)
        take.assert_not_called()
        self.assertIn("re-run once", lines[0])

    def test_real_screen_goes_on_to_the_take(self):
        with mock.patch.object(rec.pre, "main", return_value=0), \
                mock.patch.object(rec.pre, "probe_message", return_value=None), \
                mock.patch.object(rec, "one_take", return_value=(True, "/tmp/v.mp4", [])) as take, \
                mock.patch("builtins.print"):
            self.assertEqual(rec.main(["--remote-zip", "z", "--game-name", "G"]), 0)
        take.assert_called_once()

    def test_skip_probe_never_shoots(self):
        with mock.patch.object(rec.pre, "main", return_value=0), \
                mock.patch.object(rec.pre, "probe_message") as probe, \
                mock.patch.object(rec, "one_take", return_value=(True, "/tmp/v.mp4", [])), \
                mock.patch("builtins.print"):
            rec.main(["--remote-zip", "z", "--game-name", "G", "--skip-probe"])
        probe.assert_not_called()

    def test_default_warmup_is_30(self):
        seen = {}
        with mock.patch.object(rec.pre, "main", return_value=0), \
                mock.patch.object(rec.pre, "probe_message", return_value=None), \
                mock.patch.object(rec, "one_take", side_effect=lambda a: (seen.setdefault("w", a.warmup), (True, "/tmp/v", []))[1]), \
                mock.patch("builtins.print"):
            rec.main(["--remote-zip", "z", "--game-name", "G"])
        self.assertEqual(seen["w"], 30)


class Sequence(unittest.TestCase):
    """--sequence: play keys on the Legion while OBS records, so the jam video is not the idle start screen."""

    SEQ = [{"op": "declare", "end_states": ["lose"]}, {"op": "wait", "seconds": 2},
           {"op": "shot", "label": "start"}, {"op": "key", "keys": ["space", "d"], "hold": 6},
           {"op": "burst", "label": "lose", "end_state": "lose", "seconds": 3, "frames": 12},
           {"op": "key", "key": "r", "hold": 0.2}, {"op": "move", "dx": 100, "dy": 0}]

    def write(self, tmp, steps):
        path = Path(tmp) / "seq.json"
        path.write_text(json.dumps(steps) if not isinstance(steps, str) else steps, encoding="utf-8")
        return str(path)

    def test_input_steps_keep_input_drop_captures_and_lead_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            steps = rec.load_input_steps(self.write(tmp, self.SEQ))
        self.assertEqual(steps[0], {"op": "wait", "seconds": rec.LEAD_IN})
        self.assertEqual([s["op"] for s in steps], ["wait", "wait", "key", "wait", "key", "move"])
        self.assertEqual(steps[3], {"op": "wait", "seconds": 3.0})  # the burst kept its pacing
        self.assertEqual(steps[2]["keys"], ["space", "d"])
        self.assertEqual(rec.seconds_needed(steps), rec.HEAD + math.ceil(rec.LEAD_IN + 2 + 6 + 3 + 0.2 + 0.3) + rec.TAIL)
        self.assertEqual(rec.HEAD, 10)  # the documented head allowance (input task startup + focus + cut margin)

    def test_bad_steps_rejected_by_visual_playtest_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ([{"op": "key", "key": "nosuchkey"}], [{"op": "key", "key": "alt"}], [{"op": "jump"}], [],
                        [{"op": "wait", "seconds": 2}, {"op": "shot", "label": "x"}], "not json"):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    rec.load_input_steps(self.write(tmp, bad))

    def run_main(self, argv):
        with mock.patch.object(rec.pre, "main", return_value=0) as pre_main, \
                mock.patch.object(rec.pre, "probe_message", return_value=None), \
                mock.patch.object(rec, "one_take", return_value=(True, "/tmp/v.mp4", [])) as take, \
                mock.patch("builtins.print") as pr:
            rc = rec.main(["--remote-zip", "z", "--game-name", "G", *argv])
        return rc, take, pre_main, [str(c.args[0]) for c in pr.call_args_list]

    def test_too_short_seconds_stops_before_the_legion(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, self.SEQ)
            need = rec.seconds_needed(rec.load_input_steps(path))
            rc, take, pre_main, lines = self.run_main(["--seconds", str(need - 1), "--sequence", path])
        self.assertEqual(rc, 2)
        take.assert_not_called()
        pre_main.assert_not_called()
        self.assertIn(f"--seconds {need} or more", lines[0])

    def test_unreadable_or_bad_sequence_exits_two(self):
        rc, take, _, lines = self.run_main(["--sequence", "/nonexistent/seq.json"])
        self.assertEqual(rc, 2)
        take.assert_not_called()
        self.assertIn("--sequence", lines[0])

    def test_long_enough_seconds_passes_steps_to_the_take(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, self.SEQ)
            need = rec.seconds_needed(rec.load_input_steps(path))
            rc, take, _, _ = self.run_main(["--seconds", str(need), "--sequence", path])
        self.assertEqual(rc, 0)
        self.assertEqual(take.call_args.args[0].input_steps[0]["op"], "wait")

    def test_no_sequence_means_no_input_steps(self):
        rc, take, _, _ = self.run_main([])
        self.assertEqual(rc, 0)
        self.assertIsNone(take.call_args.args[0].input_steps)

    def fake_take(self, args, input_err=None, focused="FOCUSED 1000", start_ft=0, trim=None):
        """one_take with ssh faked; returns (result, events) where events order launch, input and recording."""
        events = []
        trim = trim or mock.Mock(return_value=["cut note"])
        with tempfile.TemporaryDirectory() as tmp:
            args.out_dir = tmp

            def fake_run(cmd, timeout=0):
                c = cmd[-1] if cmd[0] == "ssh" else " ".join(cmd)
                if cmd[0] == "ssh" and "Test-NetConnection" in c:
                    return 0, "True\n", ""
                if cmd[0] == "ssh" and "Get-Process Game" in c:
                    return 0, ("" if any(e == "close" for e in events) else "123\n"), ""
                if cmd[0] == "ssh" and "schtasks /Run /TN T" in c:
                    events.append("game_task")
                if cmd[0] == "ssh" and "MJToolCloseGame" in c and "/Run" in c:
                    events.append("close")
                if cmd[0] == "scp" and cmd[-2].startswith("<device-host>:"):
                    Path(cmd[-1]).write_bytes(b"x")
                return 0, "", ""

            def fake_start(a, steps, out_dir):
                events.append("input_start")
                if focused is not None:  # what LegionBackend.play copies back from the input script
                    (Path(out_dir) / "FOCUSED").write_text(focused, encoding="ascii")
                return lambda: (events.append("input_join"), input_err)[1]

            def fake_record(host, seconds, replay):
                events.append("record")
                return {"recordFile": "C:\\Videos\\take.mp4", "startRecordFileTimeUtc": start_ft}
            with mock.patch.object(rec, "run", side_effect=fake_run), \
                    mock.patch.object(rec.playtest, "deploy_and_register", return_value={}), \
                    mock.patch.object(rec, "start_input", side_effect=fake_start) as start, \
                    mock.patch.object(rec, "record_run", side_effect=fake_record), \
                    mock.patch.object(rec, "trim_head", trim), \
                    mock.patch.object(rec, "check_video", return_value=(True, [])):
                result = rec.one_take(args, sleep=lambda s: events.append(f"sleep{s}"))
        self.trim = trim
        return result, events, start

    def args(self, steps):
        return SimpleNamespace(host="device-host", remote_zip="C:\\z.zip", game_name="Game", task_name="T", seconds=30,
                               replay_seconds=1, warmup=7, out_dir="", keep_obs=False, input_steps=steps)

    def test_input_runs_after_warmup_inside_the_recording(self):
        steps = [{"op": "wait", "seconds": rec.LEAD_IN}, {"op": "key", "key": "d", "hold": 1}]
        (ok, _, problems), events, start = self.fake_take(self.args(steps))
        self.assertTrue(ok, problems)
        self.assertIs(start.call_args.args[1], steps)
        i = events.index
        # game launched, warmup slept, input started, then the recording, then joined, then the game closed
        self.assertLess(i("game_task"), i("sleep7"))
        self.assertLess(i("sleep7"), i("input_start"))
        self.assertEqual(i("input_start") + 1, i("record"))
        self.assertEqual(i("record") + 1, i("input_join"))
        self.assertLess(i("input_join"), i("close"))

    def test_input_error_fails_the_take(self):
        steps = [{"op": "key", "key": "d", "hold": 1}]
        (ok, local, problems), events, _ = self.fake_take(self.args(steps), input_err="game not in front")
        self.assertFalse(ok)
        self.assertIsNone(local)
        self.assertIn("game not in front", problems[0])

    def test_no_sequence_never_starts_input(self):
        (ok, _, problems), events, start = self.fake_take(self.args(None))
        self.assertTrue(ok)
        start.assert_not_called()
        self.assertIn("record", events)
        self.trim.assert_not_called()  # no --sequence: no trim, nothing new
        self.assertEqual(problems, [])

    def test_sequence_take_trims_with_start_and_focused_times(self):
        steps = [{"op": "wait", "seconds": rec.LEAD_IN}, {"op": "key", "key": "d", "hold": 1}]
        (ok, local, problems), _, _ = self.fake_take(self.args(steps), focused="FOCUSED 134070000123456789\r\n",
                                                     start_ft=134070000000000000)
        self.assertTrue(ok)
        self.trim.assert_called_once_with(local, 134070000000000000, 134070000123456789)
        self.assertIn("cut note", problems)

    def test_missing_focused_still_passes_the_take_to_trim_head_with_none(self):
        steps = [{"op": "key", "key": "d", "hold": 1}]
        (ok, _, _), _, _ = self.fake_take(self.args(steps), focused=None)
        self.assertTrue(ok)
        self.assertIsNone(self.trim.call_args.args[2])

    def test_start_input_runs_backend_play_in_a_thread_and_reports_errors(self):
        class Backend:
            def __init__(self, err=None):
                self.err, self.got = err, None

            def play(self, steps, out_dir):
                self.got = (steps, out_dir)
                if self.err:
                    raise RuntimeError(self.err)
        steps = [{"op": "key", "key": "d", "hold": 0.1}]
        ok = Backend()
        self.assertIsNone(rec.start_input(None, steps, "/tmp/x", backend=ok)())
        self.assertEqual(ok.got, (steps, "/tmp/x"))
        self.assertEqual(rec.start_input(None, steps, "/tmp/x", backend=Backend("ERROR focus"))(), "ERROR focus")


class HeadTrim(unittest.TestCase):
    """--sequence: the video must open on the game, so cut the head up to the input script's FOCUSED time."""
    S = 134070000000000000  # a FILETIME (100 ns ticks)

    def test_offset_is_focus_minus_start_plus_margin(self):
        self.assertAlmostEqual(rec.trim_start(self.S, self.S + 72_500_000), 7.25 + rec.CUT_MARGIN)
        self.assertEqual(rec.CUT_MARGIN, 0.5)
        self.assertIsNone(rec.trim_start(self.S, self.S))           # game in front at StartRecord
        self.assertIsNone(rec.trim_start(self.S, self.S - 30_000_000))  # focused 3 s before StartRecord

    def test_read_focused(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(rec.read_focused(d))
            (Path(d) / "FOCUSED").write_bytes(b"FOCUSED 134070000123456789\r\n")
            self.assertEqual(rec.read_focused(d), 134070000123456789)
            (Path(d) / "FOCUSED").write_text("garbage")
            self.assertIsNone(rec.read_focused(d))

    def trim(self, start_ft, focused_ft, ffmpeg_rc=0, dur=40.0):
        calls = []

        def fake_run(cmd, timeout=0):
            calls.append(cmd)
            if cmd[0] == "ffmpeg":
                if ffmpeg_rc == 0:
                    Path(cmd[-1]).write_bytes(b"x")
                return ffmpeg_rc, "", "boom" if ffmpeg_rc else ""
            return 0, f"{dur}\n", ""  # ffprobe
        d = tempfile.mkdtemp()
        video = Path(d) / "2026-11-11 02-21-31.mp4"
        video.write_bytes(b"orig")
        with mock.patch.object(rec, "run", side_effect=fake_run):
            notes = rec.trim_head(video, start_ft, focused_ft)
        return notes, calls, video

    def test_ffmpeg_argv_cuts_at_the_offset_and_keeps_the_original(self):
        notes, calls, video = self.trim(self.S, self.S + 100_000_000)  # focused 10 s in
        cut = Path(video.parent) / "2026-11-11 02-21-31_trimmed.mp4"
        self.assertEqual(calls[0], ["ffmpeg", "-v", "error", "-y", "-ss", "10.500", "-i", str(video),
                                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(cut)])
        self.assertNotIn("-vf", calls[0])  # no scale or fps filter: 1920x1080 and the frame rate are kept
        self.assertNotIn("-r", calls[0])
        self.assertEqual(calls[1][0], "ffprobe")
        self.assertTrue(cut.exists())
        self.assertEqual(video.read_bytes(), b"orig")
        self.assertFalse(any("WARNING" in n for n in notes), notes)

    def test_missing_times_skip_the_trim_with_a_warning(self):
        for start, focused, word in ((None, self.S, "StartRecord"), (self.S, None, "FOCUSED")):
            with self.subTest(word=word):
                notes, calls, video = self.trim(start, focused)
                self.assertEqual(calls, [])
                self.assertIn("WARNING", notes[0])
                self.assertIn(word, notes[0])
                self.assertFalse(rec.trimmed_path(video).exists())

    def test_no_cut_when_game_was_already_in_front(self):
        notes, calls, video = self.trim(self.S, self.S - 1)
        self.assertEqual(calls, [])
        self.assertIn("no head trim needed", notes[0])

    def test_duration_outside_30_60_warns(self):
        for dur, warn in ((29.0, True), (30.0, False), (60.0, False), (61.5, True)):
            with self.subTest(dur=dur):
                notes, _, _ = self.trim(self.S, self.S + 50_000_000, dur=dur)
                self.assertEqual(any("WARNING" in n and "30-60" in n for n in notes), warn, notes)

    def test_ffmpeg_failure_warns_and_leaves_no_cut(self):
        notes, _, video = self.trim(self.S, self.S + 50_000_000, ffmpeg_rc=1)
        self.assertIn("WARNING", notes[0])
        self.assertIn("boom", notes[0])
        self.assertFalse(rec.trimmed_path(video).exists())

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
    def test_real_cut_is_frame_accurate(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "v.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=30",
                            "-t", "6", "-pix_fmt", "yuv420p", str(src)], check=True)
            self.assertEqual(rec.trim_head(src, self.S, self.S + 15_000_000)[0][:16], "cut 2.00 s of he")
            self.assertAlmostEqual(rec.probe_duration(rec.trimmed_path(src)), 4.0, delta=0.1)

    def test_main_prints_candidate_then_original(self):
        with tempfile.TemporaryDirectory() as d:
            video = Path(d) / "take.mp4"
            video.write_bytes(b"x")
            rec.trimmed_path(video).write_bytes(b"x")
            seq = Path(d) / "seq.json"
            seq.write_text(json.dumps([{"op": "key", "key": "d", "hold": 1}]))
            with mock.patch.object(rec.pre, "main", return_value=0), \
                    mock.patch.object(rec.pre, "probe_message", return_value=None), \
                    mock.patch.object(rec, "one_take", return_value=(True, video, [])), \
                    mock.patch("builtins.print") as pr:
                self.assertEqual(rec.main(["--remote-zip", "z", "--game-name", "G", "--seconds", "60", "--sequence", str(seq)]), 0)
                out = lambda: [str(c.args[0]) for c in pr.call_args_list if "file" not in c.kwargs]  # stdout only
                self.assertEqual(out(), [f"submission candidate (head trimmed, starts on the game): {rec.trimmed_path(video)}",
                                         f"untrimmed original: {video}"])
                pr.reset_mock()
                rec.main(["--remote-zip", "z", "--game-name", "G"])  # no --sequence: the path alone, as before
                self.assertEqual(out(), [str(video)])

    def test_obs_script_reports_start_record_time_right_after_start_record(self):
        ps = (Path(ROOT) / "scripts" / "legion_obs_record_test.ps1").read_text()
        at = ps.index("Req StartRecord")
        self.assertLess(at, ps.index("$out.startRecordFileTimeUtc = (Get-Date).ToFileTimeUtc()"))
        self.assertLess(ps.index("startRecordFileTimeUtc"), ps.index("Start-Sleep -Seconds $RecSeconds"))

    def test_record_run_returns_the_start_time_and_record_keeps_its_contract(self):
        out = json.dumps({"recordFile": "C:\\V\\a.mp4", "startRecordFileTimeUtc": self.S}, indent=2)
        with mock.patch.object(rec, "run", return_value=(0, out, "")):
            self.assertEqual(rec.record_run("device-host", 4, 1)["startRecordFileTimeUtc"], self.S)
            self.assertEqual(rec.record("device-host", 4, 1), "C:\\V\\a.mp4")


if __name__ == "__main__":
    unittest.main()
