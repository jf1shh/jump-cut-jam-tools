"""agent_playtest_cli tests: a fake Legion backend and fake OBS/record module stand in for ssh, the game and
the screen. No network, no Legion. NOT run against the real Legion (see stages/03_playtest/references/agent-playtest.md)."""
import importlib.util
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("agent_playtest_cli", ROOT / "scripts" / "agent_playtest_cli.py")
ap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ap)


class FakeBackend:
    # One fake Legion shared by every backend the CLI builds (it makes a new backend per command).
    instances = []
    plays, ssh_calls, front, launched = [], [], True, False

    @classmethod
    def reset(cls):
        cls.instances, cls.plays, cls.ssh_calls, cls.front, cls.launched = [], [], [], True, False

    def __init__(self, host, zip_, game, task="T"):
        self.game, self.warmup = game, 0
        self.log_text = "LogWorld: ok\nSIGNAL DELIVERED\n"
        FakeBackend.instances.append(self)

    def launch(self):
        FakeBackend.launched = True

    def alive(self):
        return True

    def play(self, steps, out_dir):
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        FakeBackend.plays.append(steps)
        shot = [s for s in steps if s["op"] == "shot"][-1]["label"]
        (out_dir / f"01_{shot}.png").write_bytes(b"\x89PNG fake")
        (out_dir / "manifest.json").write_text(json.dumps(
            [{"label": shot, "file": f"01_{shot}.png", "t": 1, "after_input": True, "foreground": FakeBackend.front}]))

    def ssh(self, cmd, timeout=120):
        FakeBackend.ssh_calls.append(cmd)
        if "Get-ChildItem" in cmd:
            return 0, "C:\\Dev\\G\\Saved\\Logs\\G.log\n", ""
        return 0, self.log_text, ""

    def close(self):
        return True


class FakeRecord:
    def __init__(self, ok=True):
        self.ok, self.started, self.calls = ok, 0, []

    def obs_up(self, host):
        return False

    def start_obs(self, host, on_launch=None, **_):
        self.started += 1
        on_launch and on_launch()

    def record(self, host, seconds, replay):
        self.calls.append(seconds)
        return "C:\\vid\\clip.mp4"

    def fetch(self, host, remote, out_dir):
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / "clip.mp4"
        p.write_bytes(b"mp4")
        return p

    def check_video(self, path, min_seconds=0):
        return self.ok, ([] if self.ok else ["frame at 1.0s is black"])

    def close_process(self, host, name, **_):
        self.calls.append(("close", name))


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.dir = self.td.name + "/s"
        self.tick = 0.0
        FakeBackend.reset()
        self.rec = FakeRecord()

    def tearDown(self):
        self.td.cleanup()

    def now(self):
        self.tick += 1
        return self.tick

    def cli(self, *argv, rec=None):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = ap.main(["--session", self.dir, *argv], make=FakeBackend, record_mod=rec or self.rec, now=self.now)
        return rc, out.getvalue(), err.getvalue()

    def start(self):
        rc, out, _ = self.cli("start", "--remote-zip", "C:/z.zip", "--game-name", "G")
        self.assertEqual(rc, 0, out)

    def shot(self, *argv):
        rc, out, err = self.cli(*argv)
        self.assertEqual(rc, 0, err)
        return out.strip().splitlines()[-1]

    def rel(self, path):
        return str(Path(path).relative_to(self.dir))


class Commands(Base):
    def test_start_launches_and_writes_session(self):
        self.start()
        self.assertTrue(FakeBackend.launched)
        self.assertEqual(json.loads((Path(self.dir) / "session.json").read_text())["game_name"], "G")

    def test_look_returns_png_path_that_exists(self):
        self.start()
        p = self.shot("look", "--label", "menu")
        self.assertTrue(p.endswith(".png") and Path(p).is_file())
        self.assertIn("menu", p)

    def test_press_sends_keys_in_order_then_one_shot(self):
        self.start()
        self.shot("press", "w,a space", "--hold", "1.5", "--gap", "0.3")
        steps = FakeBackend.plays[-1]
        self.assertEqual([s["key"] for s in steps if s["op"] == "key"], ["w", "a", "space"])
        self.assertEqual([s.get("hold") for s in steps if s["op"] == "key"], [1.5] * 3)
        self.assertEqual(steps[-1]["op"], "shot")
        self.assertEqual(sum(1 for s in steps if s["op"] == "shot"), 1)

    def test_press_rejects_unknown_key_and_bad_hold(self):
        self.start()
        self.assertEqual(self.cli("press", "f13")[0], 2)
        self.assertEqual(self.cli("press", "w", "--hold", "0")[0], 2)
        self.assertEqual(self.cli("press", "w", "--hold", "99")[0], 2)
        self.assertEqual(FakeBackend.plays, [])

    def test_mouse_click_and_move(self):
        self.start()
        self.shot("mouse", "--click", "left", "--x", "100", "--y", "50")
        self.shot("mouse", "--move", "300", "0")
        plays = FakeBackend.plays
        self.assertEqual(plays[0][0], {"op": "click", "button": "left", "x": 100, "y": 50})
        self.assertEqual(plays[1][0], {"op": "move", "dx": 300, "dy": 0})
        self.assertEqual(self.cli("mouse", "--click", "left", "--x", "5")[0], 2)
        self.assertEqual(self.cli("mouse")[0], 2)

    def test_state_reports_alive_and_log_tail(self):
        self.start()
        rc, out, _ = self.cli("state", "--lines", "5")
        self.assertEqual(rc, 0)
        self.assertIn("game_running: True", out)
        self.assertIn("SIGNAL DELIVERED", out)
        self.assertTrue(any("-Tail 5" in c for c in FakeBackend.ssh_calls))

    def test_clip_records_fetches_and_journals(self):
        self.start()
        rc, out, _ = self.cli("clip", "10")
        self.assertEqual(rc, 0)
        self.assertTrue(Path(out.strip()).is_file())
        self.assertEqual(self.rec.started, 1)
        self.cli("clip", "10")
        self.assertEqual(self.rec.started, 1, "OBS we started is reused, not started twice")
        self.assertEqual(self.cli("clip", "1")[0], 2)

    def test_bad_clip_exits_nonzero(self):
        self.start()
        rc, _, err = self.cli("clip", "10", rec=FakeRecord(ok=False))
        self.assertEqual(rc, 1)
        self.assertIn("black", err)

    def test_stop_closes_obs_only_if_ours(self):
        self.start()
        self.cli("clip", "5")
        self.cli("stop")
        self.assertIn(("close", "obs64"), self.rec.calls)

    def test_no_session_is_a_clean_error(self):
        rc, _, err = self.cli("look")
        self.assertEqual(rc, 2)
        self.assertIn("start", err)

    def test_front_window_warning(self):
        self.start()
        FakeBackend.front = False
        rc, _, err = self.cli("look")
        self.assertEqual(rc, 0)
        self.assertIn("not the front window", err)


class Gate(Base):
    def play_all(self, win=True, lose=True, restart=True, inputs=6):
        self.start()
        for _ in range(inputs):
            f = self.shot("press", "w")
        w = self.shot("look", "--label", "win")
        if win:
            self.cli("mark", "win", "--evidence", w)
        l = self.shot("look", "--label", "lose")
        if lose:
            self.cli("mark", "lose", "--evidence", l)
        r = self.shot("look", "--label", "restart")
        if restart:
            self.cli("mark", "restart", "--evidence", r)

    def test_full_trail_passes(self):
        self.play_all()
        rc, out, _ = self.cli("gate")
        self.assertEqual(rc, 0, out)
        self.assertIn("GATE PASS", out)

    def test_missing_milestones_fail_by_name(self):
        for kw, word in (({"win": False}, "mark win"), ({"lose": False}, "mark lose"), ({"restart": False}, "mark restart")):
            with self.subTest(kw=kw):
                self.td.cleanup()
                self.setUp()
                self.play_all(**kw)
                rc, out, _ = self.cli("gate")
                self.assertEqual(rc, 1)
                self.assertIn(word, out)

    def test_too_few_inputs_fails(self):
        self.play_all(inputs=2)
        rc, out, _ = self.cli("gate")
        self.assertEqual(rc, 1)
        self.assertIn("input commands", out)

    def test_evidence_must_exist_and_be_captured_in_session(self):
        self.play_all(win=False)
        fake = Path(self.dir) / "invented.png"
        fake.write_bytes(b"x")
        rc, _, err = self.cli("mark", "win", "--evidence", str(fake))
        self.assertEqual(rc, 0, err)
        rc, out, _ = self.cli("gate")
        self.assertEqual(rc, 1)
        self.assertIn("not captured", out)
        self.assertEqual(self.cli("mark", "win", "--evidence", self.td.name + "/outside.png")[0], 2)
        self.assertEqual(self.cli("mark", "win", "--evidence", str(Path(self.dir) / "nope.png"))[0], 2)

    def test_restart_before_lose_fails(self):
        self.start()
        for _ in range(6):
            self.shot("press", "w")
        r = self.shot("look", "--label", "r")
        w = self.shot("look", "--label", "w")
        self.cli("mark", "restart", "--evidence", r)
        self.cli("mark", "win", "--evidence", w)
        self.cli("mark", "lose", "--evidence", w)
        rc, out, _ = self.cli("gate")
        self.assertEqual(rc, 1)
        self.assertIn("restart evidence was not captured after the lose", out)

    def test_win_marked_before_any_input_fails(self):
        self.start()
        w = self.shot("look", "--label", "w")
        self.cli("mark", "win", "--evidence", w)
        for _ in range(6):
            self.shot("press", "w")
        l = self.shot("look", "--label", "l")
        self.cli("mark", "lose", "--evidence", l)
        self.cli("mark", "restart", "--evidence", l)
        rc, out, _ = self.cli("gate")
        self.assertIn("before any real input", out)

    def test_input_with_game_not_in_front_fails(self):
        self.start()
        FakeBackend.front = False
        for _ in range(6):
            self.shot("press", "w")
        FakeBackend.front = True
        w = self.shot("look", "--label", "w")
        self.cli("mark", "win", "--evidence", w)
        self.cli("mark", "lose", "--evidence", w)
        self.cli("mark", "restart", "--evidence", w)
        rc, out, _ = self.cli("gate")
        self.assertEqual(rc, 1)
        self.assertIn("front window", out)

    def test_clip_counts_as_evidence(self):
        self.play_all(win=False)
        rc, out, _ = self.cli("clip", "10")
        clip = out.strip()
        self.cli("mark", "win", "--evidence", clip)
        # win now marked after lose/restart but evidence is captured before the mark: still valid
        self.assertEqual(self.cli("gate")[0], 0)


class ReviewR1(Base):
    def trail(self):
        self.start()
        for _ in range(5):
            self.shot("press", "w")

    def test_same_pre_input_frame_cannot_be_all_three(self):
        self.start()
        title = self.shot("look", "--label", "title")
        for _ in range(5):
            self.shot("press", "w")
        for m in ("win", "lose", "restart"):
            self.assertEqual(self.cli("mark", m, "--evidence", title)[0], 0)
        rc, out, _ = self.cli("gate")
        self.assertEqual(rc, 1)
        self.assertIn("before any real input", out)

    def test_shared_post_input_frame_and_restart_order(self):
        self.trail()
        a = self.shot("look", "--label", "a")
        for m in ("win", "lose", "restart"):
            self.cli("mark", m, "--evidence", a)
        self.assertIn("share evidence", self.cli("gate")[1])
        # distinct files but restart captured before lose
        self.td.cleanup()
        self.setUp()
        self.trail()
        w, r, l = (self.shot("look", "--label", n) for n in "wrl")
        self.cli("mark", "win", "--evidence", w)
        self.cli("mark", "restart", "--evidence", r)
        self.cli("mark", "lose", "--evidence", l)
        self.assertIn("restart evidence was not captured after the lose", self.cli("gate")[1])

    def test_bad_mark_then_good_mark_passes_with_note(self):
        Gate.play_all(self, win=False)
        wrong = Path(self.dir) / "report.md"
        wrong.write_text("draft")
        self.cli("mark", "win", "--evidence", str(wrong))
        good = self.shot("look", "--label", "win2")
        self.cli("mark", "win", "--evidence", good)
        rc, out, err = self.cli("gate")
        self.assertEqual(rc, 0, out)
        self.assertIn("older bad mark ignored", err)

    def test_good_mark_then_later_bad_mark_still_passes(self):
        Gate.play_all(self)
        wrong = Path(self.dir) / "report.md"
        wrong.write_text("draft")
        self.cli("mark", "win", "--evidence", str(wrong))
        self.assertEqual(self.cli("gate")[0], 0)

    def test_start_again_keeps_history_and_numbering(self):
        self.trail()
        before = len(ap.Session(self.dir).entries())
        self.start()
        entries = ap.Session(self.dir).entries()
        self.assertEqual(len(entries), before + 1)
        self.assertEqual(entries[-1]["kind"], "relaunch")
        names = {self.shot("look", "--label", "t") for _ in range(2)}
        self.assertEqual(len(names), 2)

    def test_start_other_build_refused_and_fresh_archives(self):
        self.trail()
        rc, _, err = self.cli("start", "--remote-zip", "C:/other.zip", "--game-name", "G")
        self.assertEqual(rc, 2)
        self.assertIn("different build", err)
        rc, _, _ = self.cli("start", "--remote-zip", "C:/other.zip", "--game-name", "G", "--fresh")
        self.assertEqual(rc, 0)
        self.assertEqual([e["kind"] for e in ap.Session(self.dir).entries()], ["start"])
        self.assertEqual(len(list(Path(self.dir).glob("archive-*/journal.jsonl"))), 1)

    def test_black_clip_is_not_evidence(self):
        self.trail()
        rc, out, _ = self.cli("clip", "10", rec=FakeRecord(ok=False))
        self.assertEqual(rc, 1)
        clip = out.strip()
        l, r = self.shot("look", "--label", "l"), self.shot("look", "--label", "r")
        self.cli("mark", "win", "--evidence", clip)
        self.cli("mark", "lose", "--evidence", l)
        self.cli("mark", "restart", "--evidence", r)
        rc, out, _ = self.cli("gate")
        self.assertEqual(rc, 1)
        self.assertIn("video check", out)

    def test_frame_with_game_not_in_front_is_not_evidence(self):
        self.trail()
        FakeBackend.front = False
        w = self.shot("look", "--label", "w")
        FakeBackend.front = True
        l, r = self.shot("look", "--label", "l"), self.shot("look", "--label", "r")
        self.cli("mark", "win", "--evidence", w)
        self.cli("mark", "lose", "--evidence", l)
        self.cli("mark", "restart", "--evidence", r)
        rc, out, _ = self.cli("gate")
        self.assertEqual(rc, 1)
        self.assertIn("not known to be in front", out)

    def test_session_relative_evidence_path_from_other_cwd(self):
        import os
        self.start()
        png = self.shot("look", "--label", "win")
        rel = str(Path(png).relative_to(self.dir))
        old = os.getcwd()
        os.chdir(tempfile.mkdtemp())
        try:
            rc, _, err = self.cli("mark", "win", "--evidence", rel)
        finally:
            os.chdir(old)
        self.assertEqual(rc, 0, err)


GOOD_REPORT = """# Verdict
Playable.
## Win
Watered all plants (frame 012).
## Lose
Timer ran out.
## Restart
R worked.
## Edges
Spammed space; nothing broke. Idle 30 s fine.
## Confusing
None.
## Stuck
None.
## Glitches
None.
## Fun score: 4/5
## Clarity score: 3/5
"""


class Report(Base):
    def test_good_report_passes_and_bad_ones_name_the_gap(self):
        p = Path(self.td.name) / "r.md"
        p.write_text(GOOD_REPORT)
        self.assertEqual(ap.check_report(p), [])
        p.write_text(GOOD_REPORT.replace("## Stuck\nNone.\n", ""))
        self.assertTrue(any("Stuck" in x for x in ap.check_report(p)))
        p.write_text(GOOD_REPORT.replace("4/5", "9/5"))
        self.assertTrue(any("Fun score" in x for x in ap.check_report(p)))
        p.write_text(GOOD_REPORT + "\nTODO\n")
        self.assertTrue(any("placeholder" in x for x in ap.check_report(p)))
        self.assertTrue(ap.check_report(Path(self.td.name) / "none.md"))

    def test_gate_with_report_fails_on_missing_report(self):
        Gate.play_all(self)
        rc, out, _ = self.cli("gate", "--report", self.td.name + "/none.md")
        self.assertEqual(rc, 1)

    def test_template_in_doc_is_the_one_the_gate_accepts_once_filled(self):
        doc = (ROOT / "stages" / "03_playtest" / "references" / "agent-playtest.md").read_text(encoding="utf-8")
        block = doc.split("<!-- report-template -->")[1].split("<!-- /report-template -->")[0]
        for s in ap.REPORT_SECTIONS:
            self.assertRegex(block, rf"(?im)^#+\s*{s}")
        filled = re.sub(r"<fill[^>]*>", "ok", block).replace("N/5", "3/5")
        p = Path(self.td.name) / "t.md"
        p.write_text(filled)
        self.assertEqual(ap.check_report(p), [])
        p.write_text(block)
        self.assertTrue(ap.check_report(p), "an unfilled template must not pass")


class StartProbeLock(unittest.TestCase):
    def test_locked_start_journals_nothing_and_black_relaunch_is_allowed(self):
        calls = []

        class B:
            warmup = 0
            probe = None
            check_lock = lambda s: (_ for _ in ()).throw(RuntimeError(ap.vp.MSG_LOCKED))
            launch = lambda s: calls.append("launch")
        sess = mock.Mock()
        sess.entries.return_value = []
        a = SimpleNamespace(host="device-host", remote_zip="z", game_name="G", task_name="T", fresh=False,
                            warmup=0, skip_probe=False)
        with mock.patch.object(ap, "backend_for", return_value=B()):
            with self.assertRaises(RuntimeError):
                ap.cmd_start(a, sess)
        sess.append.assert_not_called()  # no phantom journal entry for a launch that never ran
        self.assertEqual(calls, [])


class StartProbe(unittest.TestCase):
    """T-20261108-32 review r2: `start` gets the 30 s warmup and the lock / black probe."""

    def test_start_defaults_match_visual_playtest(self):
        a = ap.build_parser().parse_args(["start", "--remote-zip", "z", "--game-name", "G"])
        self.assertEqual(a.warmup, ap.vp.WARMUP_DEFAULT)
        self.assertFalse(a.skip_probe)
        self.assertTrue(ap.build_parser().parse_args(
            ["start", "--remote-zip", "z", "--game-name", "G", "--skip-probe"]).skip_probe)

    def test_backend_for_sets_the_probe_and_a_locked_legion_stops_launch(self):
        sess = SimpleNamespace(cfg={"host": "device-host", "remote_zip": "z", "game_name": "G"})
        b = ap.backend_for(sess)
        self.assertIsNotNone(b.probe)
        with mock.patch.object(ap.vp, "legion_probe", return_value=ap.vp.MSG_LOCKED):
            deployed = []
            b.deploy = lambda *x: deployed.append(x)
            with self.assertRaises(RuntimeError) as cm:
                b.launch()
        self.assertIn("Legion is locked", str(cm.exception))
        self.assertEqual(deployed, [])


if __name__ == "__main__":
    unittest.main()


class PressTogether(unittest.TestCase):
    # mock jam 16: the magnet game needs SPACE held while steering with D
    def test_together_is_one_key_step_with_all_keys(self):
        self.assertEqual(ap.key_steps(["space", "d"], 3.0, 0.2, together=True),
                         [{"op": "key", "keys": ["space", "d"], "hold": 3.0}])
        self.assertEqual(len(ap.key_steps(["space", "d"], 3.0, 0.2)), 3)  # default: one after another
        for bad in (["space"], ["d", "d"]):
            with self.assertRaises(ValueError):
                ap.key_steps(bad, 1.0, 0.2, together=True)
