"""visual_playtest tests: synthetic PNGs and a fake ssh/scp/xdotool stand in for the Legion and the game.
No network, no GPU, no editor, no real game. NOT run against the real Legion (see stages/03_playtest/references/playtest-gate.md)."""
import importlib.util
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("visual_playtest", ROOT / "scripts" / "visual_playtest.py")
vp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vp)

W, H = 160, 90


def frame(kind="scene", shift=0):
    """Synthetic RGB frame. scene = coloured gradient with a block at x=shift; grey = untextured grey
    grid; black; debug = scene plus a red block top-left (stands in for on-screen warning text)."""
    px = bytearray()
    for y in range(H):
        for x in range(W):
            if kind == "black":
                px += b"\x00\x00\x00"
            elif kind == "grey":
                v = 120 + (30 if (x // 10 + y // 10) % 2 else 0)
                px += bytes((v, v, v))
            else:
                r, g, b = (x * 255 // W, y * 255 // H, 90)
                if shift <= x < shift + 30 and 40 <= y < 70:
                    r, g, b = 250, 240, 20
                if kind == "debug" and x < 40 and y < 20:
                    r, g, b = 255, 0, 0
                px += bytes((r, g, b))
    return bytes(px)


def put(d, name, kind="scene", shift=0):
    vp.write_png(Path(d) / name, W, H, frame(kind, shift))


def judge_text(text, line="Verdict: PASS"):
    """What a careful agent does after looking: every item verdict, and every prefilled step stub
    (AGENT / WARN / FAIL), becomes `line`."""
    text = text.replace("Verdict: PENDING", line)
    return re.sub(r"^Verdict: (AGENT|WARN|FAIL)$", line, text, flags=re.M)


def manifest(d, entries):
    Path(d, "manifest.json").write_text(json.dumps(entries))


def entry(n, label, after=False):
    return {"label": label, "file": f"{n:02d}_{label}.png", "t": n, "after_input": after}


def zoom_frame(z):
    """The scene seen through a camera that has zoomed in by factor z around the centre."""
    px = bytearray()
    cx, cy = W / 2, H / 2
    for y in range(H):
        for x in range(W):
            sx, sy = min(W - 1, max(0, int(cx + (x - cx) / z))), min(H - 1, max(0, int(cy + (y - cy) / z)))
            r, g, b = (sx * 255 // W, sy * 255 // H, 90)
            if (sx // 12 + sy // 9) % 3 == 0:  # a busy floor pattern so a zoom really moves pixels
                r, g, b = 250, 120, 100
            px += bytes((r, g, b))
    return bytes(px)


def burst_entries(d, label, frames, start=1, end_state=None, spacing=0.25):
    """Write one idle burst of RGB byte-frames into d and return its manifest entries (captured `spacing`
    seconds apart). frames: list of raw RGB bytes (W x H). end_state: 'lose'/'win' tag, as the backends write."""
    out = []
    for i, px in enumerate(frames, 1):
        name = f"{start + i - 1:02d}_burst_{label}_{i:02d}.png"
        vp.write_png(Path(d) / name, W, H, px)
        out.append({"label": f"burst_{label}_{i:02d}", "file": name, "t": round(start * 10 + i * spacing, 2),
                    "after_input": False, "burst": label, "burst_index": i,
                    **({"end_state": end_state} if end_state else {})})
    return out


def valid_sequence(play_key="w", states=("lose",)):
    """Smallest sequence the validator accepts: declare, play, end-state burst(s), restart, after-restart burst."""
    mid = []
    for st in states[:-1]:  # an earlier end state: burst, then the input that leaves it
        mid += [{"op": "burst", "label": st, "end_state": st, "seconds": 3, "frames": 12}, {"op": "key", "key": "r"}]
    return [{"op": "declare", "end_states": list(states)},
            {"op": "shot", "label": "start"}, {"op": "key", "key": play_key},
            {"op": "shot", "label": "after_play"}] + mid + [
            {"op": "burst", "label": states[-1], "end_state": states[-1], "seconds": 3, "frames": 12},
            {"op": "key", "key": "r"}, {"op": "shot", "label": "restarted"},
            {"op": "burst", "label": "afterrestart", "seconds": 3, "frames": 12}]


def complete_manifest(d, end_frames=None, end_label="lose", after_frames=None):
    """A full run's manifest + frames: start, input, end-state burst, restart, after-restart burst."""
    put(d, "01_start.png")
    put(d, "02_after_w.png", shift=80)
    ents = [entry(1, "start"), entry(2, "after_w", True)]
    ents += burst_entries(d, end_label, end_frames or [frame("scene", 80)] * 12, 3, end_state="lose")
    put(d, "15_restarted.png")
    ents.append(entry(15, "restarted", True))
    ents += burst_entries(d, "afterrestart", after_frames or [frame("scene", 0)] * 12, 16)
    return ents


def still_burst(d, label, start=1, n=12):
    return burst_entries(d, label, [frame("scene", 20)] * n, start)


def looping_zoom_frames(n=12):
    """The 2026-11-08 bug: the camera falls toward the floor (zoom grows) then snaps back wide, repeating."""
    return [zoom_frame(1.0 + 0.45 * (i % 4)) for i in range(n)]


class Sequence(unittest.TestCase):
    def test_default_is_valid(self):
        vp.validate_sequence(vp.DEFAULT_SEQUENCE)

    def test_rejects_bad_sequences(self):
        for bad in ([], [{"op": "dance"}], [{"op": "shot", "label": "a b"}, {"op": "key", "key": "w"}],
                    [{"op": "shot", "label": "a"}],            # no input
                    [{"op": "key", "key": "w"}],               # no shot
                    [{"op": "shot", "label": "a"}, {"op": "key", "key": "W; rm"}]):
            with self.assertRaises(ValueError):
                vp.validate_sequence(bad)

    def test_manifest_normalising(self):
        self.assertEqual(vp.normalize_manifest(""), [])
        self.assertEqual(vp.normalize_manifest({"a": 1}), [{"a": 1}])
        self.assertEqual(vp.normalize_manifest([{"a": 1}]), [{"a": 1}])


class Png(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            put(d, "a.png")
            w, h, rgb = vp.read_png(Path(d) / "a.png")
            self.assertEqual((w, h), (W, H))
            self.assertEqual(rgb, frame())

    def test_rejects_non_png(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "x.png").write_bytes(b"nope")
            with self.assertRaises(ValueError):
                vp.read_png(Path(d) / "x.png")


class Analyze(unittest.TestCase):
    def run_case(self, files, entries, **kw):
        d = tempfile.mkdtemp()
        for name, kind, shift in files:
            put(d, name, kind, shift)
        manifest(d, entries)
        res = vp.analyze(d, use_ocr=False, **kw)
        return {i["id"]: i for i in res["items"]}

    def test_good_run_passes_cheap_checks(self):
        items = self.run_case(
            [("01_start.png", "scene", 10), ("02_idle.png", "scene", 10), ("03_after_w.png", "scene", 70),
             ("04_restarted.png", "scene", 10)],
            [entry(1, "start"), entry(2, "idle"), entry(3, "after_w", True), entry(4, "restarted")])
        self.assertEqual(items["capture"]["auto"], "PASS")
        self.assertEqual(items["input"]["auto"], "PASS")
        self.assertEqual(items["hud"]["auto"], "PASS")
        self.assertEqual(items["restart"]["auto"], "PASS")
        self.assertEqual(items["level"]["auto"], "AGENT")

    def test_input_that_changes_nothing_fails(self):
        items = self.run_case([("01_start.png", "scene", 10), ("02_after_w.png", "scene", 10)],
                              [entry(1, "start"), entry(2, "after_w", True)])
        self.assertEqual(items["input"]["auto"], "FAIL")

    def test_no_input_shot_fails(self):
        items = self.run_case([("01_start.png", "scene", 10), ("02_idle.png", "scene", 10)],
                              [entry(1, "start"), entry(2, "idle")])
        self.assertEqual(items["input"]["auto"], "FAIL")

    def test_black_frame_fails_capture(self):
        items = self.run_case([("01_start.png", "black", 0)], [entry(1, "start")])
        self.assertEqual(items["capture"]["auto"], "FAIL")
        self.assertIn("black", items["capture"]["detail"])

    def test_unreadable_frame_fails_capture(self):
        d = tempfile.mkdtemp()
        Path(d, "01_start.png").write_bytes(b"garbage")
        manifest(d, [entry(1, "start")])
        res = vp.analyze(d, use_ocr=False)
        self.assertEqual(res["items"][0]["auto"], "FAIL")

    def test_no_frames_fails_capture(self):
        d = tempfile.mkdtemp()
        manifest(d, [])
        self.assertEqual(vp.analyze(d, use_ocr=False)["items"][0]["auto"], "FAIL")

    def test_grey_grid_warns(self):
        items = self.run_case([("01_start.png", "grey", 0)], [entry(1, "start")])
        self.assertEqual(items["level"]["auto"], "WARN")

    def test_debug_colour_text_warns(self):
        items = self.run_case([("01_start.png", "debug", 10)], [entry(1, "start")])
        self.assertEqual(items["hud"]["auto"], "WARN")

    def test_ocr_debug_words_warn(self):
        d = tempfile.mkdtemp()
        put(d, "01_start.png")
        manifest(d, [entry(1, "start")])
        res = vp.analyze(d, ocr=lambda p: "Hello World  LogBlueprint")
        hud = next(i for i in res["items"] if i["id"] == "hud")
        self.assertEqual(hud["auto"], "WARN")
        res = vp.analyze(d, ocr=lambda p: "SCORE 10  TIME 0:42")
        self.assertEqual(next(i for i in res["items"] if i["id"] == "hud")["auto"], "PASS")

    def test_restart_that_looks_like_end_screen_warns(self):
        items = self.run_case(
            [("01_start.png", "scene", 10), ("02_restarted.png", "grey", 0)],
            [entry(1, "start"), entry(2, "restarted")])
        self.assertEqual(items["restart"]["auto"], "WARN")


class ChecklistAndVerify(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        manifest(self.d, complete_manifest(self.d))
        self.res = vp.analyze(self.d, use_ocr=False)
        self.path = vp.write_checklist(self.d, self.res, "Game.zip")

    def set_all(self, verdict):
        self.path.write_text(judge_text(self.path.read_text(), verdict))

    def test_pending_checklist_does_not_pass(self):
        ok, problems = vp.verify(self.d)
        self.assertFalse(ok)
        self.assertEqual(len(problems), len(vp.ITEMS) + len(json.loads((Path(self.d) / "results.json").read_text())["steps"]))

    def test_all_pass_passes_unless_auto_fail(self):
        # the single 'restart' item has no restart shot -> AGENT, fine. Force one Auto FAIL below.
        self.set_all("Verdict: PASS")
        self.assertEqual(vp.verify(self.d), (True, []))

    def test_one_fail_blocks(self):
        text = self.path.read_text().replace("Verdict: PENDING", "Verdict: PASS", len(vp.ITEMS) - 1)
        self.path.write_text(judge_text(text.replace("Verdict: PENDING", "Verdict: FAIL - grey grid")))
        ok, problems = vp.verify(self.d)
        self.assertFalse(ok)
        self.assertIn("FAIL", problems[0])

    def test_auto_fail_needs_override(self):
        # Auto is read from results.json, so editing the checklist's Auto line changes nothing...
        self.path.write_text(self.path.read_text().replace("Auto: PASS - 2 frames", "Auto: FAIL - 2 frames", 1))
        self.set_all("Verdict: PASS")
        self.assertTrue(vp.verify(self.d)[0])
        # ...a real Auto FAIL (in results.json) needs an override.
        rp = Path(self.d) / "results.json"
        res = json.loads(rp.read_text())
        res["items"][0]["auto"] = "FAIL"
        rp.write_text(json.dumps(res))
        ok, problems = vp.verify(self.d)
        self.assertFalse(ok)
        self.assertIn("override", problems[0])
        # (the intro text also contains "Verdict: PASS", so aim at item 1's own line)
        text = self.path.read_text().replace("Verdict: PASS\n\n### 2.", "Verdict: PASS (override: frame is dark by design)\n\n### 2.")
        self.path.write_text(text)
        self.assertTrue(vp.verify(self.d)[0])

    def test_missing_checklist_and_edited_headings(self):
        self.assertFalse(vp.verify(tempfile.mkdtemp())[0])
        self.path.write_text("### 1. only one\nVerdict: PASS\n")
        self.assertFalse(vp.verify(self.d)[0])

    def test_cli_verify_exit_codes(self):
        self.assertEqual(vp.main(["verify", self.d]), 1)
        self.set_all("Verdict: PASS")
        self.assertEqual(vp.main(["verify", self.d]), 0)


class FakeLegionRun:
    """Stands in for ssh/scp. Records commands; scp -r fetch materialises frames from a prepared dir."""

    def __init__(self, frames_dir, game_dies_after_close=True, task_run_rc=0, error_text=None):
        self.calls, self.frames_dir, self.error_text = [], frames_dir, error_text
        self.closed, self.task_run_rc = False, task_run_rc

    def __call__(self, cmd, timeout=120):
        self.calls.append(cmd)
        if cmd[0] == "scp":
            if "-r" in cmd:
                dest = Path(cmd[-1])
                (dest / "vp").mkdir(parents=True)
                for f in Path(self.frames_dir).iterdir():
                    (dest / "vp" / f.name).write_bytes(f.read_bytes())
                (dest / "vp" / "DONE").write_text("ok")
                if self.error_text:
                    (dest / "vp" / "ERROR").write_text(self.error_text)
            return 0, "", ""
        remote = cmd[-1]
        if "Get-Process" in remote and "Select-Object" in remote:
            return 0, ("" if self.closed else "4242\n"), ""
        if "CloseMainWindow" in remote and "/Create" in remote:
            self.closed = True
        if "schtasks /Run /TN MegaJamLaunchGame" in remote:
            return self.task_run_rc, "", "denied" if self.task_run_rc else ""
        if remote.startswith("if exist"):
            return 0, "YES\r\n", ""
        return 0, "", ""


class LegionFlow(unittest.TestCase):
    def setUp(self):
        self.src = tempfile.mkdtemp()
        put(self.src, "01_start.png", shift=10)
        put(self.src, "02_idle.png", shift=10)
        put(self.src, "03_after_w.png", shift=80)
        manifest(self.src, [entry(1, "start"), entry(2, "idle"), entry(3, "after_w", True)])
        self.out = tempfile.mkdtemp()
        self.steps = [{"op": "shot", "label": "start"}, {"op": "shot", "label": "idle"},
                      {"op": "key", "key": "w", "hold": 1}, {"op": "shot", "label": "after_w"}]
        self.deployed = []

    def backend(self, run):
        return vp.LegionBackend("device-host", "C:\\Dev\\G\\G.zip", "G", run=run, sleep=lambda s: None,
                                deploy=lambda *a: self.deployed.append(a))

    def test_full_run_uses_console_session_task_and_real_input_script(self):
        run = FakeLegionRun(self.src)
        results, checklist = vp.run_gate(self.backend(run), self.steps, self.out, build="G.zip", use_ocr=False)
        joined = "\n".join(" ".join(c) for c in run.calls)
        self.assertIn("/IT", joined)                       # interactive-logon task = console session
        self.assertIn("visual_playtest_input.ps1", joined)
        self.assertIn("schtasks /Delete /TN MJToolVisualPlaytest", joined)
        self.assertEqual(self.deployed[0][3], "MegaJamLaunchGame")
        self.assertTrue(Path(checklist).exists())
        self.assertTrue((Path(self.out) / "01_start.png").exists())
        self.assertFalse((Path(self.out) / "DONE").exists())
        by = {i["id"]: i for i in results["items"]}
        self.assertEqual(by["input"]["auto"], "PASS")
        self.assertTrue(run.closed)                        # polite close ran

    def test_steps_file_sent_to_remote_is_the_sequence(self):
        sent = {}

        class Spy(FakeLegionRun):
            def __call__(s, cmd, timeout=120):
                if cmd[0] == "scp" and "-r" not in cmd and cmd[-1].endswith("vp_steps.json"):
                    sent["steps"] = json.loads(Path(cmd[-2]).read_text())
                return super().__call__(cmd, timeout)
        vp.run_gate(self.backend(Spy(self.src)), self.steps, self.out, use_ocr=False)
        self.assertEqual(sent["steps"], self.steps)

    def test_game_not_running_after_launch_raises_and_still_closes(self):
        class Dead(FakeLegionRun):
            def __call__(s, cmd, timeout=120):
                if "Get-Process" in cmd[-1] and "Select-Object" in cmd[-1]:
                    s.calls.append(cmd)
                    return 0, "", ""
                return super().__call__(cmd, timeout)
        run = Dead(self.src)
        with self.assertRaises(RuntimeError):
            vp.run_gate(self.backend(run), self.steps, self.out)
        self.assertTrue(any("CloseMainWindow" in " ".join(c) for c in run.calls))

    def test_input_script_error_is_reported(self):
        run = FakeLegionRun(self.src, error_text="unknown key name: zz")
        with self.assertRaises(RuntimeError) as cm:
            vp.run_gate(self.backend(run), self.steps, self.out)
        self.assertIn("unknown key", str(cm.exception))

    def test_cli_capture_failure_exits_2(self):
        # --remote-zip without a reachable host: patch the backend class to fail fast
        orig = vp.LegionBackend.launch
        vp.LegionBackend.launch = lambda self: (_ for _ in ()).throw(RuntimeError("no ssh"))
        try:
            rc = vp.main(["run", "--remote-zip", "C:\\x.zip", "--game-name", "G", "--out", self.out])
        finally:
            vp.LegionBackend.launch = orig
        self.assertEqual(rc, 2)

    def test_legion_needs_zip_and_name(self):
        with self.assertRaises(SystemExit):
            vp.main(["run", "--out", self.out])


class GameProcessOverride(unittest.TestCase):
    """MJ_GAME_PROC: a content-only package runs UnrealGame.exe, not the blocked stub exe."""
    setUp = LegionFlow.setUp
    backend = LegionFlow.backend

    def test_default_watches_game_name_and_leaves_task_alone(self):
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("MJ_GAME_PROC", None)
            run = FakeLegionRun(self.src)
            b = self.backend(run)
            b.launch()
        joined = "\n".join(" ".join(c) for c in run.calls)
        self.assertNotIn("Set-ScheduledTask", joined)
        self.assertIn("Get-Process G ", joined)

    def test_override_repoints_task_before_run_and_watches_engine_exe(self):
        with mock.patch.dict(os.environ, {"MJ_GAME_PROC": "UnrealGame"}):
            run = FakeLegionRun(self.src)
            self.backend(run).launch()
        cmds = [c[-1] for c in run.calls]
        repoint = next(i for i, c in enumerate(cmds) if "Set-ScheduledTask -TaskName MegaJamLaunchGame" in c)
        run_at = next(i for i, c in enumerate(cmds) if "schtasks /Run /TN MegaJamLaunchGame" in c)
        self.assertLess(repoint, run_at)
        self.assertIn("UnrealGame.exe", cmds[repoint])
        self.assertIn("..\\..\\..\\G\\G.uproject", cmds[repoint])
        self.assertTrue(any("Get-Process UnrealGame " in c for c in cmds))
        self.assertFalse(any("Get-Process G " in c for c in cmds))

    def test_override_goes_to_the_input_script(self):
        with mock.patch.dict(os.environ, {"MJ_GAME_PROC": "UnrealGame"}):
            run = FakeLegionRun(self.src)
            self.backend(run).play(self.steps, self.out)
        create = next(" ".join(c) for c in run.calls if "MJToolVisualPlaytest" in " ".join(c) and "/Create" in " ".join(c))
        self.assertIn("-GameProcess UnrealGame", create)

    def test_unsafe_override_is_rejected(self):
        with self.assertRaises(ValueError):
            vp.game_process("G", env={"MJ_GAME_PROC": "a b"})

    def test_repoint_failure_stops_launch_before_running_the_task(self):
        class Denied(FakeLegionRun):
            def __call__(self, cmd, timeout=120):
                self.calls.append(cmd)
                if cmd[0] != "scp" and "Set-ScheduledTask" in cmd[-1]:
                    return 1, "", "access denied"
                return 0, "", ""
        with mock.patch.dict(os.environ, {"MJ_GAME_PROC": "UnrealGame"}):
            run = Denied(self.src)
            with self.assertRaisesRegex(RuntimeError, "UnrealGame.exe.*access denied"):
                self.backend(run).launch()
        self.assertFalse(any("schtasks /Run /TN MegaJamLaunchGame" in c[-1] for c in run.calls))

    def test_override_close_targets_engine_exe_not_game_name(self):
        class Stuck(FakeLegionRun):
            def __call__(self, cmd, timeout=120):
                self.calls.append(cmd)
                if cmd[0] != "scp" and "Get-Process" in cmd[-1] and "Select-Object" in cmd[-1]:
                    return 0, "4242\n", ""  # never dies, so the force path runs
                return 0, "", ""
        with mock.patch.dict(os.environ, {"MJ_GAME_PROC": "UnrealGame"}):
            run = Stuck(self.src)
            closed = self.backend(run).close()
        cmds = [c[-1] for c in run.calls]
        self.assertFalse(closed)
        self.assertTrue(any("(Get-Process UnrealGame " in c and "CloseMainWindow" in c for c in cmds))
        self.assertTrue(any("Stop-Process -Name UnrealGame " in c for c in cmds))
        self.assertFalse(any("Get-Process G " in c or "Stop-Process -Name G " in c for c in cmds))

    def test_watch_only_override_does_not_repoint_the_launch_exe(self):
        # same process in another case, or a C++ game's shipping process: only the watched name changes
        for proc in ("g", "G-Win64-Shipping"):
            with mock.patch.dict(os.environ, {"MJ_GAME_PROC": proc}):
                run = FakeLegionRun(self.src)
                self.backend(run).launch()
            cmds = [c[-1] for c in run.calls]
            self.assertFalse(any("Set-ScheduledTask" in c or "UnrealGame.exe" in c for c in cmds), proc)
            self.assertTrue(any(f"Get-Process {proc} " in c for c in cmds), proc)

    def test_default_close_still_targets_game_name(self):
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("MJ_GAME_PROC", None)
            run = FakeLegionRun(self.src)
            self.backend(run).close()
        self.assertTrue(any("(Get-Process G " in c[-1] and "CloseMainWindow" in c[-1] for c in run.calls))


class LocalFlow(unittest.TestCase):
    def test_local_backend_drives_xdotool_and_ffmpeg(self):
        calls = []

        def run(cmd, timeout=60):
            calls.append(cmd)
            if cmd[0] == "xdotool" and cmd[1] == "getdisplaygeometry":
                return SimpleNamespace(returncode=0, stdout="1920 1080\n", stderr="")
            if cmd[0] == "ffmpeg":
                put(Path(cmd[-1]).parent, Path(cmd[-1]).name, shift=10 + 60 * (len(calls) % 2))
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        proc = SimpleNamespace(poll=lambda: None, terminate=lambda: calls.append(["terminate"]), returncode=None)
        b = vp.LocalBackend(["./Game"], run=run, popen=lambda cmd: proc, sleep=lambda s: None)
        out = tempfile.mkdtemp()
        steps = [{"op": "shot", "label": "start"}, {"op": "key", "key": "w", "hold": 1}, {"op": "click"},
                 {"op": "move", "dx": 5, "dy": 0}, {"op": "shot", "label": "after_input"}]
        results, _ = vp.run_gate(b, steps, out, use_ocr=False)
        flat = [" ".join(c) for c in calls]
        self.assertTrue(any(c.startswith("xdotool keydown w") for c in flat))
        self.assertTrue(any(c.startswith("xdotool keyup w") for c in flat))
        self.assertTrue(any("mousemove_relative" in c for c in flat))
        self.assertTrue(any("x11grab" in c and "1920x1080" in c for c in flat))
        self.assertIn(["terminate"], calls)
        m = json.loads((Path(out) / "manifest.json").read_text())
        self.assertEqual([s["after_input"] for s in m], [False, True])

    def test_local_game_that_exits_is_an_error(self):
        proc = SimpleNamespace(poll=lambda: 1, returncode=1, terminate=lambda: None)
        b = vp.LocalBackend(["./Game"], popen=lambda cmd: proc, sleep=lambda s: None)
        with self.assertRaises(RuntimeError):
            b.launch()


class VideoFrames(unittest.TestCase):
    def test_extract_n_frames(self):
        out = tempfile.mkdtemp()

        def runner(cmd, **kw):
            if cmd[0] == "ffprobe":
                return SimpleNamespace(stdout="40.0\n")
            Path(cmd[-1]).write_bytes(b"png")
            return SimpleNamespace(stdout="")
        files = vp.extract_frames("v.mp4", out, 4, runner=runner)
        self.assertEqual([f.name for f in files], [f"video_0{i}.png" for i in range(1, 5)])

    def test_bad_duration_raises(self):
        with self.assertRaises(RuntimeError):
            vp.extract_frames("v.mp4", tempfile.mkdtemp(), 3, runner=lambda c, **k: SimpleNamespace(stdout="N/A"))


PS1 = (ROOT / "scripts" / "visual_playtest_input.ps1").read_text()


class ReviewR1(unittest.TestCase):
    """Fixes for review round 1 of PR 102."""

    def judged_dir(self, build="old build"):
        d = tempfile.mkdtemp()
        manifest(d, complete_manifest(d))
        res = vp.analyze(d, use_ocr=False)
        p = vp.write_checklist(d, res, build)
        p.write_text(judge_text(p.read_text()))
        return d

    # 2: stale PASS checklist
    def test_failed_rerun_does_not_leave_a_passing_gate(self):
        d = self.judged_dir()
        self.assertEqual(vp.main(["verify", d]), 0)
        # Never start a real LocalBackend here: its xdotool would type into the developer's desktop.
        orig = vp.LocalBackend.launch
        vp.LocalBackend.launch = lambda self: (_ for _ in ()).throw(RuntimeError("crashed on launch"))
        try:
            rc = vp.main(["run", "--target", "local", "--no-ocr", "--out", d, "--local-cmd", "never-started"])
        finally:
            vp.LocalBackend.launch = orig
        self.assertEqual(rc, 2)
        self.assertEqual(vp.main(["verify", d]), 1)

    def test_swapped_or_edited_frames_fail_verify(self):
        d = self.judged_dir()
        put(d, "02_after_w.png", shift=40)  # a different picture under the same name
        ok, problems = vp.verify(d)
        self.assertFalse(ok)
        self.assertIn("02_after_w.png", problems[0])

    def test_checklist_from_another_run_fails_verify(self):
        d = self.judged_dir()
        other = self.judged_dir()
        (Path(d) / "checklist.md").write_text((Path(other) / "checklist.md").read_text())
        self.assertIn("different run", vp.verify(d)[1][0])

    def test_missing_results_json_fails_verify(self):
        d = self.judged_dir()
        (Path(d) / "results.json").unlink()
        self.assertFalse(vp.verify(d)[0])

    # 6: Auto comes from results.json, not the editable checklist
    def test_editing_auto_line_cannot_launder_a_fail(self):
        d = self.judged_dir()
        rp = Path(d) / "results.json"
        res = json.loads(rp.read_text())
        res["items"][3]["auto"] = "FAIL"
        rp.write_text(json.dumps(res))
        ok, problems = vp.verify(d)
        self.assertFalse(ok)
        self.assertIn("override", problems[0])

    # 3: idle baseline
    def test_self_animating_game_that_ignores_input_is_not_a_pass(self):
        d = tempfile.mkdtemp()
        names = [("start", 0, False), ("idle", 30, False), ("after_w", 60, True), ("after_d", 90, True)]
        entries = []
        for n, (label, shift, after) in enumerate(names, 1):
            put(d, f"{n:02d}_{label}.png", shift=shift)  # block drifts by the same amount every shot
            entries.append(entry(n, label, after))
        manifest(d, entries)
        items = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}
        self.assertEqual(items["input"]["auto"], "FAIL", items["input"]["detail"])

    def test_input_without_idle_shot_only_warns(self):
        d = tempfile.mkdtemp()
        put(d, "01_a.png", shift=0)
        put(d, "02_b.png", shift=80)
        manifest(d, [entry(1, "a", True), entry(2, "b", True)])
        items = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}
        self.assertNotEqual(items["input"]["auto"], "PASS")

    # 7: frozen game
    def test_restart_that_changes_nothing_fails(self):
        d = tempfile.mkdtemp()
        for n, label in enumerate(["start", "late", "restarted"], 1):
            put(d, f"{n:02d}_{label}.png", shift=40 if label != "start" else 10)
        manifest(d, [entry(1, "start"), entry(2, "late"), entry(3, "restarted")])
        items = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}
        self.assertEqual(items["restart"]["auto"], "FAIL")

    # r2-1: the restart shot must not count as player-input movement
    def test_play_keys_ignored_but_restart_reloads_level_is_not_a_pass(self):
        d = tempfile.mkdtemp()
        seq = [("start", 10, False), ("idle", 10, False), ("after_w", 10, True), ("after_d", 10, True),
               ("late", 10, False), ("restarted", 90, True)]  # only the R shot changes the picture
        entries = []
        for n, (label, shift, after) in enumerate(seq, 1):
            put(d, f"{n:02d}_{label}.png", shift=shift)
            entries.append(entry(n, label, after))
        manifest(d, entries)
        items = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}
        self.assertEqual(items["input"]["auto"], "FAIL", items["input"]["detail"])

    # r2-2: restart bar uses the idle baseline
    def test_self_animating_game_that_ignores_restart_fails(self):
        d = tempfile.mkdtemp()
        seq = [("start", 0, False), ("idle", 30, False), ("late", 60, False), ("restarted", 90, False)]
        entries = []
        for n, (label, shift, after) in enumerate(seq, 1):
            put(d, f"{n:02d}_{label}.png", shift=shift)  # drifts 30 px per shot no matter what
            entries.append(entry(n, label, after))
        manifest(d, entries)
        items = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}
        self.assertEqual(items["restart"]["auto"], "FAIL", items["restart"]["detail"])

    # DPI: on a scaled display CopyFromScreen crops to a corner unless the process is DPI aware first
    def test_input_script_is_dpi_aware_before_any_screen_capture(self):
        call = PS1.index("[MJInput]::SetProcessDPIAware()")
        self.assertIn("SetProcessDPIAware();", PS1)  # the P/Invoke is declared
        self.assertLess(call, PS1.index("SystemInformation]::VirtualScreen"))
        self.assertLess(call, PS1.index("$g.CopyFromScreen("))
        shot = (ROOT / "scripts" / "legion_screenshot.ps1").read_text()
        self.assertIn("SetProcessDPIAware();", shot)
        scall = shot.index("[MJDpi]::SetProcessDPIAware()")
        self.assertLess(scall, shot.index("SystemInformation]::VirtualScreen"))
        self.assertLess(scall, shot.index("$graphics.CopyFromScreen("))

    # r3: restart label matching is case-insensitive in both checks
    def test_capitalised_restart_label_is_still_checked(self):
        for label in ("Restarted", "RESTART", "restarted"):
            d = tempfile.mkdtemp()
            seq = [("start", 10), ("late", 40), (label, 40)]  # restart frame identical to the one before
            entries = []
            for n, (lb, shift) in enumerate(seq, 1):
                put(d, f"{n:02d}_{lb}.png", shift=shift)
                entries.append(entry(n, lb))
            manifest(d, entries)
            items = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}
            self.assertEqual(items["restart"]["auto"], "FAIL", label)

    # r2-3: analyze cannot mint a verifiable stamp
    def test_analyze_command_writes_nothing_and_cannot_unlock_verify(self):
        d = tempfile.mkdtemp()
        put(d, "01_start.png", shift=0)
        put(d, "02_idle.png", shift=0)
        put(d, "03_after_w.png", shift=80)
        manifest(d, [entry(1, "start"), entry(2, "idle"), entry(3, "after_w", True)])
        before = sorted(os.listdir(d))
        vp.main(["analyze", d, "--no-ocr"])
        self.assertEqual(sorted(os.listdir(d)), before)
        self.assertEqual(vp.main(["verify", d]), 1)

    # 1: focus
    def test_input_task_is_hidden_and_game_is_forced_to_foreground(self):
        run = FakeLegionRun(tempfile.mkdtemp())
        b = vp.LegionBackend("device-host", "C:\\z.zip", "G", run=run, sleep=lambda s: None, deploy=lambda *a: None)
        d = tempfile.mkdtemp()
        put(d, "01_x.png")
        manifest(d, [entry(1, "x")])
        run.frames_dir = d
        b.play([{"op": "shot", "label": "x"}, {"op": "key", "key": "w"}], tempfile.mkdtemp())
        create = next(" ".join(c) for c in run.calls if "MJToolVisualPlaytest" in " ".join(c) and "/Create" in " ".join(c))
        self.assertIn("-WindowStyle Hidden", create)
        self.assertIn("-GameProcess G", create)
        for fn in ("SetForegroundWindow", "Assert-GameForeground", "GetForegroundWindow"):
            self.assertIn(fn, PS1)
        for op in ('"key" {', '"click" {', '"move" {'):
            self.assertIn("Assert-GameForeground", PS1[PS1.index(op):PS1.index(op) + 400], op)

    def test_shot_taken_while_game_not_in_front_fails_capture(self):
        d = tempfile.mkdtemp()
        put(d, "01_x.png")
        manifest(d, [{**entry(1, "x"), "foreground": False}])
        self.assertEqual(vp.analyze(d, use_ocr=False)["items"][0]["auto"], "FAIL")

    def test_bad_game_name_refused(self):
        with self.assertRaises(ValueError):
            vp.LegionBackend("device-host", "z", "G; calc")

    # 4: one key list
    def test_every_key_python_accepts_is_in_the_ps1_table(self):
        table = PS1[PS1.index("$ScanCodes = @{"):PS1.index("\n}\n", PS1.index("$ScanCodes = @{"))]
        ps = {m[0]: (int(m[1], 16), m[2] == "true")
              for m in re.findall(r'"([a-z0-9]+)"\s*=\s*@\(0x([0-9A-Fa-f]+),\s*\$(true|false)\)', table)}
        py = {k: (v[0], v[1]) for k, v in vp.KEYS.items()}
        self.assertEqual(ps, py)

    def test_documented_keys_validate_and_unknown_fail_before_deploy(self):
        for k in list("abcdefghijklmnopqrstuvwxyz0123456789") + ["shift", "ctrl", "esc", "enter", "up"]:
            vp.validate_sequence(valid_sequence(k))
        for k in ("lshift", "f1", "W", "pgup"):
            with self.assertRaises(ValueError):
                vp.validate_sequence(valid_sequence(k))

    def test_keys_list_holds_keys_together(self):
        # mock jam 16: the magnet game needs SPACE held while steering with D
        def seq(step):
            s = valid_sequence()
            s[2] = step
            return s
        vp.validate_sequence(seq({"op": "key", "keys": ["space", "d"], "hold": 4}))
        for bad in ({"op": "key"}, {"op": "key", "key": "d", "keys": ["space"]}, {"op": "key", "keys": []},
                    {"op": "key", "keys": "space"}, {"op": "key", "keys": ["space", "space"]},
                    {"op": "key", "keys": ["space", "f1"]}, {"op": "key", "keys": ["space", "alt"]}):
            with self.assertRaises(ValueError, msg=bad):
                vp.validate_sequence(seq(bad))
        self.assertIn("$s.keys", PS1)  # the Legion input script reads the list too

    def test_local_keys_list_presses_in_order_releases_in_reverse(self):
        seen = []

        def run(cmd, timeout=60):
            seen.append(cmd)
            if cmd[1] == "getdisplaygeometry":
                return SimpleNamespace(returncode=0, stdout="64 36\n", stderr="")
            if cmd[0] == "ffmpeg":
                put(Path(cmd[-1]).parent, Path(cmd[-1]).name)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        vp.LocalBackend(["./G"], run=run, sleep=lambda s: None).play(
            [{"op": "key", "keys": ["space", "d"], "hold": 2}, {"op": "shot", "label": "a"}], tempfile.mkdtemp())
        xdo = [c[1:3] for c in seen if c[0] == "xdotool" and c[1] in ("keydown", "keyup")]
        self.assertEqual(xdo, [["keydown", "space"], ["keydown", "d"], ["keyup", "d"], ["keyup", "space"]])

    # 5: local backend
    def test_local_xdotool_failure_stops_the_run(self):
        def run(cmd, timeout=60):
            if cmd[1] == "getdisplaygeometry":
                return SimpleNamespace(returncode=0, stdout="64 36\n", stderr="")
            if cmd[0] == "xdotool":
                return SimpleNamespace(returncode=1, stdout="", stderr="No such key")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        b = vp.LocalBackend(["./G"], run=run, sleep=lambda s: None)
        with self.assertRaises(RuntimeError):
            b.play([{"op": "shot", "label": "a"}, {"op": "key", "key": "esc"}], tempfile.mkdtemp())

    def test_local_uses_x_keysyms(self):
        seen = []

        def run(cmd, timeout=60):
            seen.append(cmd)
            if cmd[1] == "getdisplaygeometry":
                return SimpleNamespace(returncode=0, stdout="64 36\n", stderr="")
            if cmd[0] == "ffmpeg":
                put(Path(cmd[-1]).parent, Path(cmd[-1]).name)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        out = tempfile.mkdtemp()
        vp.LocalBackend(["./G"], run=run, sleep=lambda s: None).play(
            [{"op": "key", "key": "esc"}, {"op": "key", "key": "enter"}, {"op": "key", "key": "shift"}, {"op": "shot", "label": "a"}], out)
        keys = [c[2] for c in seen if c[0] == "xdotool" and c[1] == "keydown"]
        self.assertEqual(keys, ["Escape", "Return", "Shift_L"])

    def test_local_window_grab_focus_and_uinput(self):
        # mock jam 15: a root grab is black on KDE Wayland; grab the game window, click it once, keys via uinput
        seen, writes = [], []

        def run(cmd, timeout=60):
            seen.append(cmd)
            if cmd[:3] == ["xdotool", "search", "--name"]:
                return SimpleNamespace(returncode=0, stdout="11\n22\n", stderr="")
            if cmd[:2] == ["xdotool", "getwindowgeometry"]:
                w = "1920" if cmd[-1] == "22" else "1"
                return SimpleNamespace(returncode=0, stdout=f"WINDOW={cmd[-1]}\nWIDTH={w}\nHEIGHT=1080\n", stderr="")
            if cmd[0] == "ffmpeg":
                put(Path(cmd[-1]).parent, Path(cmd[-1]).name)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        class UI:
            def write(self, t, c, v): writes.append((t, c, v))
            def syn(self): pass
            def close(self): writes.append("closed")

        proc = SimpleNamespace(poll=lambda: None, terminate=lambda: None, returncode=None)
        b = vp.LocalBackend(["./G"], run=run, popen=lambda c: proc, sleep=lambda s: None, window="SkyLantern",
                            keyinput="uinput", uinput_factory=lambda codes: UI())
        b.launch()
        self.assertEqual(b.win_id, "22")
        out = tempfile.mkdtemp()
        b.play([{"op": "key", "key": "space"}, {"op": "key", "key": "left"}, {"op": "shot", "label": "a"}], out)
        b.close()
        grabs = [c for c in seen if c[0] == "ffmpeg"]
        self.assertIn("-window_id", grabs[0])
        self.assertNotIn("-video_size", grabs[0])
        self.assertIn(["xdotool", "click", "1"], seen)
        self.assertFalse(any(c[:2] == ["xdotool", "keydown"] for c in seen))
        self.assertEqual(writes, [(1, 57, 1), (1, 57, 0), (1, 105, 1), (1, 105, 0), "closed"])

    def test_local_window_never_found_is_an_error(self):
        def run(cmd, timeout=60):
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        proc = SimpleNamespace(poll=lambda: None, terminate=lambda: None, returncode=None)
        b = vp.LocalBackend(["./G"], run=run, popen=lambda c: proc, sleep=lambda s: None, window="Nope", window_tries=2)
        with self.assertRaises(RuntimeError):
            b.launch()

    def test_evdev_codes(self):
        self.assertEqual([vp.evdev_code(k) for k in ("esc", "a", "d", "r", "space", "up", "right")],
                         [1, 30, 32, 19, 57, 103, 106])


EVIDENCE = Path.home() / "Projects/megajam/work/legion-video/contact_sheet.png"


class IdleMotion(unittest.TestCase):
    """T-20261108-10: idle bursts catch what still frames passed (mock 10 OUT OF WATER camera loop)."""

    def motion(self, frames, label="lose"):
        d = tempfile.mkdtemp()
        manifest(d, complete_manifest(d, end_frames=frames, end_label=label))
        res = vp.analyze(d, use_ocr=False)
        return d, {i["id"]: i for i in res["items"]}["motion"]

    def test_still_scene_passes(self):
        _, m = self.motion([frame("scene", 20)] * 12)
        self.assertEqual(m["auto"], "PASS", m["detail"])

    def test_looping_zoom_fixture_fails(self):
        _, m = self.motion(looping_zoom_frames())
        self.assertEqual(m["auto"], "FAIL", m["detail"])
        self.assertIn("lose:", m["detail"])

    def test_falling_camera_without_snap_back_fails(self):
        _, m = self.motion([zoom_frame(1.0 + 0.2 * i) for i in range(12)])
        self.assertEqual(m["auto"], "FAIL", m["detail"])

    def test_flicker_fails(self):
        _, m = self.motion([frame("scene", 10 if i % 2 else 90) for i in range(12)])
        self.assertEqual(m["auto"], "FAIL", m["detail"])

    def test_slight_ambient_animation_is_not_a_fail(self):
        _, m = self.motion([frame("scene", 20 + i // 4) for i in range(12)])
        self.assertIn(m["auto"], ("PASS", "WARN"), m["detail"])

    def test_too_few_frames_fails(self):
        _, m = self.motion([frame("scene", 20)] * 6)
        self.assertEqual(m["auto"], "FAIL")

    def test_no_burst_at_all_fails(self):
        d = tempfile.mkdtemp()
        put(d, "01_start.png")
        manifest(d, [entry(1, "start")])
        by = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}
        self.assertEqual(by["motion"]["auto"], "FAIL")

    def test_one_bad_burst_among_good_ones_fails_and_names_it(self):
        d = tempfile.mkdtemp()
        put(d, "01_start.png")
        ents = [entry(1, "start")] + still_burst(d, "midplay", 2) + burst_entries(d, "lose", looping_zoom_frames(), 20)
        manifest(d, ents)
        m = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}["motion"]
        self.assertEqual(m["auto"], "FAIL")
        self.assertIn("midplay: PASS", m["detail"])
        self.assertIn("lose: FAIL", m["detail"])

    def test_burst_frames_do_not_disturb_input_and_restart_checks(self):
        d = tempfile.mkdtemp()
        put(d, "01_start.png", shift=10)
        put(d, "02_idle.png", shift=10)
        put(d, "03_after_w.png", shift=80)
        put(d, "04_restarted.png", shift=10)
        ents = [entry(1, "start"), entry(2, "idle"), entry(3, "after_w", True)]
        ents += burst_entries(d, "lose", [frame("scene", 80)] * 12, 5, end_state="lose")
        ents += [entry(4, "restarted")]
        ents += burst_entries(d, "afterrestart", [frame("scene", 10)] * 12, 20)
        manifest(d, ents)
        by = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}
        self.assertEqual(by["input"]["auto"], "PASS", by["input"]["detail"])
        self.assertEqual(by["restart"]["auto"], "PASS", by["restart"]["detail"])
        self.assertEqual(by["motion"]["auto"], "PASS", by["motion"]["detail"])

    @unittest.skipUnless(EVIDENCE.exists(), "mock 10 evidence contact sheet not on this machine")
    def test_real_mock10_evidence_frames_fail(self):
        w, h, rgb = vp.read_png(EVIDENCE)
        tw, th = w // 5, h // 2
        tiles = []
        for r in range(2):
            for c in range(5):
                tiles.append(b"".join(rgb[((r * th + y) * w + c * tw) * 3:((r * th + y) * w + (c + 1) * tw) * 3] for y in range(th)))
        d = tempfile.mkdtemp()
        ents = []
        for i, t in enumerate(tiles, 1):
            name = f"{i:02d}_burst_lose_{i:02d}.png"
            vp.write_png(Path(d) / name, tw, th, t)
            ents.append({"label": f"burst_lose_{i:02d}", "file": name, "t": i, "after_input": False, "burst": "lose", "burst_index": i})
        manifest(d, ents)
        m = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}["motion"]
        self.assertEqual(m["auto"], "FAIL", m["detail"])

    def test_run_writes_contact_sheet_and_stamps_it(self):
        out = tempfile.mkdtemp()
        calls = []

        def run(cmd, timeout=60):
            calls.append(cmd)
            if cmd[0] == "xdotool":
                return SimpleNamespace(returncode=0, stdout="1920 1080\n", stderr="")
            if cmd[0] == "ffmpeg":
                grabs = len([c for c in calls if c[0] == "ffmpeg"])
                put(Path(cmd[-1]).parent, Path(cmd[-1]).name, shift=80 if grabs == 2 else 20)  # input moves grab 2
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        proc = SimpleNamespace(poll=lambda: None, terminate=lambda: None, returncode=None)
        b = vp.LocalBackend(["./G"], run=run, popen=lambda c: proc, sleep=lambda s: None)
        steps = vp.validate_sequence([{"op": "declare", "end_states": ["lose"]},
                                      {"op": "shot", "label": "start"}, {"op": "key", "key": "w"},
                                      {"op": "shot", "label": "after_w"},
                                      {"op": "burst", "label": "lose", "end_state": "lose", "seconds": 3, "frames": 12},
                                      {"op": "key", "key": "r"}, {"op": "shot", "label": "restarted"},
                                      {"op": "burst", "label": "afterrestart", "seconds": 3, "frames": 12}])
        results, checklist = vp.run_gate(b, steps, out, use_ocr=False)
        sheet = Path(out) / "contact_lose.png"
        self.assertTrue(sheet.exists())
        sw, sh, _ = vp.read_png(sheet)
        self.assertGreater(sw, vp.SHEET_COLS * vp.SHEET_TILE[0])
        self.assertGreaterEqual(sh, 3 * vp.SHEET_TILE[1])  # 12 frames, 5 columns -> 3 rows
        self.assertEqual(len([c for c in calls if c[0] == "ffmpeg"]), 27)
        m = json.loads((Path(out) / "manifest.json").read_text())
        bursts = [e for e in m if e.get("burst")]
        self.assertEqual(len(bursts), 24)
        self.assertTrue(all(e["after_input"] is False for e in bursts))
        by = {i["id"]: i for i in results["items"]}
        self.assertEqual(by["motion"]["auto"], "PASS", by["motion"]["detail"])
        self.assertEqual(by["motion"]["frames"], ["contact_lose.png", "contact_afterrestart.png"])
        self.assertIn("contact_lose.png", json.loads((Path(out) / "results.json").read_text())["frames_sha256"])
        # the sheet is tied to the run: swapping it breaks verify
        p = Path(checklist)
        p.write_text(judge_text(p.read_text()))
        self.assertEqual(vp.main(["verify", out]), 0)
        vp.write_png(sheet, 8, 8, b"\x10" * 192)
        self.assertEqual(vp.main(["verify", out]), 1)

    def test_looping_run_blocks_the_gate_without_override(self):
        d = tempfile.mkdtemp()
        manifest(d, complete_manifest(d, end_frames=looping_zoom_frames(), end_label="lose"))
        res = vp.analyze(d, use_ocr=False)
        res["sheets"] = vp.write_burst_sheets(d, res)
        p = vp.write_checklist(d, res, "G.zip")
        p.write_text(judge_text(p.read_text()))
        ok, problems = vp.verify(d)
        self.assertFalse(ok)
        self.assertIn("Idle stability", problems[0])

    def test_sequence_validation_and_defaults(self):
        vp.validate_sequence(vp.DEFAULT_SEQUENCE)
        labels = [s["label"] for s in vp.DEFAULT_SEQUENCE if s["op"] == "burst"]
        self.assertEqual(labels, ["midplay", "lose", "afterrestart"])
        self.assertIn("lose", vp.DEFAULT_SEQUENCE[0]["end_states"])  # the default declares at least lose
        base = valid_sequence()
        for bad in ({"op": "burst", "label": "x", "frames": 5}, {"op": "burst", "label": "x", "seconds": 0},
                    {"op": "burst", "label": "bad_label"}, {"op": "burst"}, {"op": "burst", "label": "x", "frames": "many"}):
            with self.assertRaises(ValueError, msg=str(bad)):
                vp.validate_sequence(base + [bad])
        with self.assertRaises(ValueError):
            vp.validate_sequence(base + [{"op": "burst", "label": "lose"}])  # duplicate label
        vp.validate_sequence(base + [{"op": "burst", "label": "win", "frames": 10, "seconds": 2}])

    # review round 1, finding 1: the end states must be sampled
    def test_sequence_with_only_a_midplay_burst_is_rejected(self):
        seq = [{"op": "declare", "end_states": ["lose"]},
               {"op": "shot", "label": "start"}, {"op": "burst", "label": "midplay"},
               {"op": "key", "key": "w", "hold": 1.5}, {"op": "shot", "label": "after_w"},
               {"op": "wait", "seconds": 25}, {"op": "shot", "label": "late"},
               {"op": "key", "key": "r"}, {"op": "shot", "label": "restarted"}]
        with self.assertRaisesRegex(ValueError, "declared end state 'lose' has no burst"):
            vp.validate_sequence(seq)
        with self.assertRaisesRegex(ValueError, "declare its end states"):  # no declaration at all
            vp.validate_sequence(seq[1:])

    def test_sequence_without_after_restart_burst_or_restart_shot_is_rejected(self):
        seq = valid_sequence()
        with self.assertRaisesRegex(ValueError, "after the 'restarted' shot"):
            vp.validate_sequence(seq[:-1])
        with self.assertRaisesRegex(ValueError, "restarted"):
            vp.validate_sequence([s for s in seq if s.get("label") != "restarted"])

    def test_manifest_without_end_state_or_restart_burst_fails_motion(self):
        d = tempfile.mkdtemp()
        put(d, "01_start.png")
        put(d, "02_after_w.png", shift=80)
        put(d, "03_late.png", shift=80)
        put(d, "16_restarted.png")
        base = [entry(1, "start"), entry(2, "after_w", True)]
        mid = burst_entries(d, "midplay", [frame("scene", 20)] * 12, 4)
        # only a burst before any input: still FAIL, even though that burst is perfectly still
        manifest(d, [entry(1, "start")] + mid + [entry(2, "after_w", True), entry(3, "late"), entry(16, "restarted", True)])
        m = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}["motion"]
        self.assertEqual(m["auto"], "FAIL", m["detail"])
        self.assertIn("declared 'lose' end state", m["detail"])
        self.assertIn("after the restart", m["detail"])
        # end-state burst present, after-restart burst missing
        end = burst_entries(d, "lose", [frame("scene", 80)] * 12, 4, end_state="lose")
        manifest(d, base + [entry(3, "late")] + end + [entry(16, "restarted", True)])
        m = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}["motion"]
        self.assertEqual(m["auto"], "FAIL")
        self.assertNotIn("declared 'lose' end state", m["detail"])
        self.assertNotIn("not an end-state burst", m["detail"])
        self.assertIn("after the restart", m["detail"])
        # review r2 #2: the end-state burst sits BEFORE a long wait + a late shot, not right before the restart
        manifest(d, base + end + [entry(3, "late"), entry(16, "restarted", True)])
        m = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}["motion"]
        self.assertEqual(m["auto"], "FAIL")
        self.assertIn("not an end-state burst", m["detail"])

    # review round 1, finding 2: spacing must not alias with a ~1 s loop
    def test_burst_spacing_is_capped(self):
        base = valid_sequence()
        for frames, seconds in ((10, 10), (12, 12), (10, 3.5)):  # 1.0, 1.0, 0.35 s apart
            with self.assertRaisesRegex(ValueError, "apart"):
                vp.validate_sequence(base + [{"op": "burst", "label": "x", "frames": frames, "seconds": seconds}])
        vp.validate_sequence(base + [{"op": "burst", "label": "x", "frames": 10, "seconds": 3}])  # exactly 0.3 s

    def test_one_second_loop_is_hidden_at_one_second_spacing_but_caught_at_point_two(self):
        def zooms(spacing):  # camera loop with a 1.0 s period: zoom depends on the time modulo 1 s
            return [zoom_frame(1.0 + 1.8 * ((i * spacing) % 1.0)) for i in range(12)]
        _, slow = self.motion(zooms(1.0))   # every sample lands on the same phase: looks perfectly still
        self.assertEqual(slow["auto"], "PASS", slow["detail"])
        _, fast = self.motion(zooms(0.2))
        self.assertEqual(fast["auto"], "FAIL", fast["detail"])

    # review round 2, finding 1: judge the CAPTURED spacing, not the requested one
    def test_burst_captured_slowly_is_not_trusted(self):
        d = tempfile.mkdtemp()
        loop = [zoom_frame(1.0 + 1.8 * ((i * 1.0) % 1.0)) for i in range(12)]  # a 1.0 s loop sampled 1.0 s apart
        slow = burst_entries(d, "lose", loop, 3, end_state="lose", spacing=1.0)
        put(d, "01_start.png")
        put(d, "02_after_w.png", shift=80)
        put(d, "15_restarted.png")
        ents = [entry(1, "start"), entry(2, "after_w", True)] + slow + [entry(15, "restarted", True)]
        ents += burst_entries(d, "afterrestart", [frame("scene", 0)] * 12, 16)
        manifest(d, ents)
        m = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}["motion"]
        self.assertEqual(m["auto"], "FAIL", m["detail"])
        self.assertIn("frames too slow to judge motion", m["detail"])
        # the same frames captured fast enough are judged on their pictures instead (and a still scene passes)
        ents[2:14] = burst_entries(d, "lose", [frame("scene", 80)] * 12, 3, end_state="lose", spacing=0.25)
        manifest(d, ents)
        m = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}["motion"]
        self.assertEqual(m["auto"], "PASS", m["detail"])

    def test_burst_without_capture_times_fails(self):
        d = tempfile.mkdtemp()
        ents = complete_manifest(d)
        for e in ents:
            if e.get("burst") == "lose":
                del e["t"]
        manifest(d, ents)
        m = {i["id"]: i for i in vp.analyze(d, use_ocr=False)["items"]}["motion"]
        self.assertEqual(m["auto"], "FAIL")
        self.assertIn("capture times", m["detail"])

    # review round 2, finding 2: the end-state burst is the LAST capture before the restart key
    def test_end_state_burst_before_a_long_wait_is_rejected(self):
        seq = [{"op": "declare", "end_states": ["lose"]}, {"op": "shot", "label": "start"},
               {"op": "key", "key": "w", "hold": 1.5}, {"op": "shot", "label": "after_w"},
               {"op": "burst", "label": "lose", "end_state": "lose", "seconds": 3, "frames": 12},  # still mid-play
               {"op": "wait", "seconds": 25},                                                    # lose state arrives
               {"op": "shot", "label": "late"},
               {"op": "key", "key": "r"}, {"op": "shot", "label": "restarted"},
               {"op": "burst", "label": "afterrestart", "seconds": 3, "frames": 12}]
        with self.assertRaisesRegex(ValueError, "immediately followed by an input"):
            vp.validate_sequence(seq)
        # a wait or shot between the burst and the restart key is refused even without that rule's wording
        seq2 = [dict(s) for s in valid_sequence()]
        i = next(n for n, s in enumerate(seq2) if s["op"] == "key" and s["key"] == "r")
        seq2.insert(i, {"op": "shot", "label": "extra"})
        with self.assertRaises(ValueError):
            vp.validate_sequence(seq2)
        vp.validate_sequence(valid_sequence())

    # review round 2, finding 3: declared end states each need their own burst
    def test_declared_win_and_lose_each_need_a_burst(self):
        vp.validate_sequence(valid_sequence(states=("lose", "win")))
        seq = valid_sequence(states=("lose", "win"))
        only_win = [s for s in seq if not (s["op"] == "burst" and s.get("end_state") == "lose")]
        with self.assertRaisesRegex(ValueError, "declared end state 'lose' has no burst"):
            vp.validate_sequence(only_win)
        undeclared = [dict(s) for s in valid_sequence()]
        undeclared[0] = {"op": "declare", "end_states": ["lose", "win"]}  # declares win, never samples it
        with self.assertRaisesRegex(ValueError, "declared end state 'win' has no burst"):
            vp.validate_sequence(undeclared)
        for bad in ({"op": "declare", "end_states": []}, {"op": "declare", "end_states": ["draw"]},
                    {"op": "declare", "end_states": ["lose", "lose"]}, {"op": "declare"}):
            with self.assertRaises(ValueError, msg=str(bad)):
                vp.validate_sequence([bad] + valid_sequence()[1:])

    def test_analyze_fails_when_a_declared_win_state_was_never_sampled(self):
        d = tempfile.mkdtemp()
        manifest(d, complete_manifest(d))
        ok = {i["id"]: i for i in vp.analyze(d, use_ocr=False, end_states=("lose",))["items"]}["motion"]
        self.assertEqual(ok["auto"], "PASS", ok["detail"])
        bad = {i["id"]: i for i in vp.analyze(d, use_ocr=False, end_states=("lose", "win"))["items"]}["motion"]
        self.assertEqual(bad["auto"], "FAIL")
        self.assertIn("'win' end state", bad["detail"])

    def test_run_gate_uses_the_declared_end_states(self):
        class Fake:
            def launch(self): pass
            def close(self): return True

            def play(self, steps, out_dir):
                m = complete_manifest(out_dir)
                manifest(out_dir, m)
        steps = valid_sequence(states=("lose", "win"))
        results, _ = vp.run_gate(Fake(), steps, tempfile.mkdtemp(), use_ocr=False)
        by = {i["id"]: i for i in results["items"]}
        self.assertEqual(results["end_states"], ["lose", "win"])
        self.assertEqual(by["motion"]["auto"], "FAIL")  # the fake never produced a 'win' burst
        self.assertIn("'win' end state", by["motion"]["detail"])

    def test_burst_time_counts_toward_the_wait_budget(self):
        self.assertGreaterEqual(vp.sequence_seconds([{"op": "burst", "label": "x", "seconds": 3, "frames": 12}]), 9)

    def test_ps1_has_burst_op_with_after_input_false(self):
        ps = (ROOT / "scripts" / "visual_playtest_input.ps1").read_text()
        self.assertIn('"burst"', ps)
        self.assertIn("burst_index", ps)
        self.assertRegex(ps, r'Save-Shot \("burst_\{0\}_\{1:D2\}" -f \$s\.label, \$i\) \$false')


class ReviewR3(unittest.TestCase):
    def test_shot_between_restart_key_and_restarted_shot_is_refused(self):
        seq = valid_sequence()
        i = max(n for n, s in enumerate(seq) if s["op"] == "key")  # the restart key
        seq.insert(i + 1, {"op": "wait", "seconds": 1})
        seq.insert(i + 2, {"op": "shot", "label": "loading"})
        with self.assertRaisesRegex(ValueError, "between the restart key"):
            vp.validate_sequence(seq)

    def test_wait_between_restart_key_and_restarted_shot_is_fine(self):
        seq = valid_sequence()
        i = max(n for n, s in enumerate(seq) if s["op"] == "key")
        seq.insert(i + 1, {"op": "wait", "seconds": 3})
        vp.validate_sequence(seq)

    def test_non_string_end_states_raise_value_error(self):
        for bad in ([["lose"]], [{"a": 1}], [1], [None]):
            seq = valid_sequence()
            seq[0] = {"op": "declare", "end_states": bad}
            with self.assertRaisesRegex(ValueError, "declare.end_states"):
                vp.validate_sequence(seq)


class StepSheetsAndGate(unittest.TestCase):
    """T-20261108-21: 15 frames cost 2 image reads, blank or AGENT verdicts never pass, `gate` blocks shipping."""

    def make(self, n=15):
        d = tempfile.mkdtemp()
        ents = complete_manifest(d)  # a clean run: 3 stills + 2 bursts (bursts get their own sheets, not step sheets)
        for i in range(n - 3):  # pad with extra stills up to n step frames
            e = entry(30 + i, f"look{i}")
            put(d, e["file"], shift=10 + i * 7)
            ents.append(e)
        manifest(d, ents)
        res = vp.analyze(d, use_ocr=False)
        res["sheets"] = vp.write_step_sheets(d, res)
        self.checklist = vp.write_checklist(d, res, "G.zip")
        self.d, self.res = d, res
        return d

    def edit(self, fn):
        self.checklist.write_text(fn(self.checklist.read_text()))

    def set_step(self, n, line):
        """Judge everything, then give step n this exact verdict line."""
        self.edit(judge_text)
        self.edit(lambda t: re.sub(rf"(#### Step {n:02d}.*?\nAuto: \w+\n)Verdict: PASS", lambda m: m.group(1) + line, t,
                                   count=1, flags=re.S))

    def test_fifteen_frames_make_two_sheets(self):
        self.make(15)
        self.assertEqual(self.res["sheets"], ["contact_steps_1.png", "contact_steps_2.png"])
        self.assertEqual(len(self.res["steps"]), 15)
        w, h, _ = vp.read_png(Path(self.d) / "contact_steps_1.png")
        self.assertEqual((w, h), (4 * (320 + 4) + 4, 2 * (180 + vp.LABEL_H + 4) + 4))  # 8 frames: 4 x 2
        self.assertEqual(vp.read_png(Path(self.d) / "contact_steps_2.png")[:2], (w, h))  # 7 frames still fill 2 rows
        self.assertEqual(self.res["steps"][8]["sheet"], "contact_steps_2.png")
        self.assertEqual(self.res["steps"][8]["tile"], 1)
        self.assertIn("contact_steps_1.png, contact_steps_2.png", self.checklist.read_text())
        stamped = json.loads((Path(self.d) / "results.json").read_text())["frames_sha256"]
        self.assertIn("contact_steps_2.png", stamped)  # a swapped sheet breaks verify

    def test_label_strip_is_drawn(self):
        self.make(3)
        w, h, rgb = vp.read_png(Path(self.d) / "contact_steps_1.png")
        y = 4 + 5  # inside the first tile's label strip
        strip = [rgb[(y * w + x) * 3:(y * w + x) * 3 + 3] for x in range(4, 4 + 320)]
        self.assertIn(b"\xff\xff\xff", strip)  # text pixels
        self.assertIn(b"\x10\x10\x10", strip)  # strip background
        canvas = bytearray(60 * 20 * 3)
        vp.draw_text(canvas, 60, 0, 0, "A", 60)
        self.assertEqual(bytes(canvas[4 * 3:5 * 3 + 3]), b"\xff" * 6)  # the A's apex (row 0, columns 1-3 at 2x)

    def test_checklist_prefills_the_harness_verdicts(self):
        self.make(15)
        blocks = self.checklist.read_text().split("\n#### Step ")[1:]
        self.assertEqual(len(blocks), 15)
        for b, st in zip(blocks, self.res["steps"]):
            self.assertIn(f"Auto: {st['auto']}\nVerdict: {st['auto']}", b)
        self.assertIn("AGENT", {st["auto"] for st in self.res["steps"]})

    def test_worst_item_verdict_wins_per_frame(self):
        res = {"items": [{"frames": ["a.png"], "auto": "PASS"}, {"frames": ["a.png", "b.png"], "auto": "FAIL"},
                         {"frames": ["a.png"], "auto": "AGENT"}],
               "shots": [{"file": "a.png", "ok": True}, {"file": "b.png", "ok": True}, {"file": "c.png", "ok": True},
                         {"file": "d.png", "ok": False}, {"file": "e.png", "ok": True, "burst": "x"}]}
        self.assertEqual([s["auto"] for s in vp.build_steps(res)], ["FAIL", "FAIL", "PASS", "FAIL"])  # burst excluded

    def test_blank_agent_warn_pending_and_fail_verdicts_do_not_verify(self):
        for line, expect in (("Verdict:", "blank"), ("Verdict: ", "blank"), ("Verdict: AGENT", "AGENT"),
                             ("Verdict: WARN", "WARN"), ("Verdict: PENDING", "PENDING"), ("Verdict: FAIL - grey", "FAIL")):
            self.make(15)
            self.set_step(7, line)
            ok, problems = vp.verify(self.d)
            self.assertFalse(ok, line)
            self.assertEqual(len(problems), 1, problems)
            self.assertIn("Step 07", problems[0])
            self.assertIn(expect, problems[0])
        self.make(15)
        self.set_step(7, "Verdict: PASS (reviewed: water ripples)")
        self.assertTrue(vp.verify(self.d)[0])

    def test_deleting_a_verdict_line_or_step_block_fails(self):
        self.make(15)
        self.edit(judge_text)
        self.edit(lambda t: re.sub(r"(#### Step 03.*?\n)Auto: \w+\nVerdict: PASS\n", r"\1", t, count=1, flags=re.S))
        self.assertIn("blank", vp.verify(self.d)[1][0])
        self.make(15)
        self.edit(judge_text)
        self.edit(lambda t: t[:t.index("#### Step 15")])
        self.assertIn("step blocks", vp.verify(self.d)[1][0])
        self.make(15)
        self.edit(lambda t: t.split(vp.STEPS_HEADING)[0])
        self.assertIn("no step review", vp.verify(self.d)[1][0])

    def test_step_auto_fail_needs_override(self):
        self.make(15)
        self.edit(judge_text)
        rp = Path(self.d) / "results.json"
        res = json.loads(rp.read_text())
        res["steps"][3]["auto"] = "FAIL"
        rp.write_text(json.dumps(res))
        ok, problems = vp.verify(self.d)
        self.assertFalse(ok)
        self.assertIn("override", problems[0])
        self.edit(lambda t: re.sub(r"(#### Step 04.*?\nAuto: \w+\n)Verdict: PASS", r"\1Verdict: PASS (override: dark by design)",
                                   t, count=1, flags=re.S))
        self.assertTrue(vp.verify(self.d)[0])

    def test_gate_blocks_until_every_verdict_is_real(self):
        d = self.make(15)
        receipt = Path(d) / "gate.ok"
        self.assertEqual(vp.main(["gate", d]), 1)
        self.assertFalse(receipt.exists())
        self.edit(judge_text)
        self.assertEqual(vp.main(["gate", d]), 0)
        self.assertEqual(json.loads(receipt.read_text())["run_id"], self.res["run_id"])
        self.edit(lambda t: re.sub(r"^Verdict: PASS$", "Verdict:", t, count=1, flags=re.M))  # a later edit blanks one
        self.assertEqual(vp.main(["gate", d]), 1)
        self.assertFalse(receipt.exists())

    def test_receipt_check_goes_stale_after_an_edit(self):
        d = self.make(15)
        self.edit(judge_text)
        self.assertEqual(vp.main(["gate", d, "--check"]), 1)  # no receipt yet
        self.assertEqual(vp.main(["gate", d]), 0)
        self.assertEqual(vp.main(["gate", d, "--check"]), 0)
        self.edit(lambda t: re.sub(r"^Verdict: PASS$", "Verdict:", t, count=1, flags=re.M))
        self.assertEqual(vp.main(["gate", d, "--check"]), 1)  # receipt still on disk, but stale

    def test_shot_without_ok_key_is_not_a_fail(self):
        res = {"items": [], "shots": [{"file": "a.png"}]}
        self.assertEqual(vp.build_steps(res)[0]["auto"], "PASS")

    def test_scorecard_reads_step_problems_as_item_problems(self):
        sys_path = str(ROOT / "scripts")
        import sys
        sys.path.insert(0, sys_path)
        import mock_scorecard as ms
        d = self.make(15)
        self.edit(judge_text)
        self.edit(lambda t: re.sub(r"(#### Step 05.*?\nAuto: \w+\n)Verdict: PASS", r"\1Verdict: WARN", t, count=1, flags=re.S))
        playtest, motion = ms.gate_playtest(d)
        self.assertEqual(playtest[0], "fail")
        self.assertEqual(motion[0], "pass")  # the motion item itself was judged PASS

    def test_bad_burst_frame_does_not_fail_every_still(self):
        d = tempfile.mkdtemp()
        manifest(d, complete_manifest(d, end_frames=[frame("scene", 80)] * 11 + [frame("black")]))
        res = vp.analyze(d, use_ocr=False)
        self.assertEqual({i["id"]: i["auto"] for i in res["items"]}["capture"], "FAIL")  # the item still fails
        self.assertNotIn("FAIL", [s["auto"] for s in vp.build_steps(res)])

    def test_bad_still_blames_only_that_still(self):
        d = tempfile.mkdtemp()
        ents = complete_manifest(d)
        put(d, "02_after_w.png", "black")
        manifest(d, ents)
        steps = vp.build_steps(vp.analyze(d, use_ocr=False))
        self.assertEqual([s["auto"] for s in steps if s["file"] == "02_after_w.png"], ["FAIL"])
        self.assertNotEqual(steps[0]["auto"], "FAIL")

    def test_gate_without_a_run_fails(self):
        d = tempfile.mkdtemp()
        self.assertEqual(vp.main(["gate", d]), 1)
        self.assertFalse((Path(d) / "gate.ok").exists())

    def test_rerun_clears_an_old_receipt(self):
        d = self.make(15)
        self.edit(judge_text)
        self.assertEqual(vp.main(["gate", d]), 0)
        vp.clear_previous(d)
        self.assertFalse((Path(d) / "gate.ok").exists())


class LegionCapturePath(unittest.TestCase):
    """T-20261108-32: lock preflight, cold start, bare Alt, focus (mock jam 11 gaps 14-16, 19, 21, 34)."""

    def backend(self, probe, warmup=30, warmup_max=60, sleeps=None):
        run = FakeLegionRun(tempfile.mkdtemp())
        self.run = run
        self.deployed = []
        return vp.LegionBackend("device-host", "C:\\z.zip", "G", run=run, deploy=lambda *a: self.deployed.append(a),
                                sleep=(sleeps.append if sleeps is not None else lambda s: None),
                                warmup=warmup, warmup_max=warmup_max, probe=probe)

    def test_locked_legion_stops_before_deploy_with_one_line(self):
        b = self.backend(lambda: vp.MSG_LOCKED)
        with self.assertRaises(RuntimeError) as cm:
            b.launch()
        self.assertEqual(str(cm.exception), vp.MSG_LOCKED)
        self.assertIn("Legion is locked", str(cm.exception))
        self.assertEqual(self.deployed, [])  # not one launch command ran
        self.assertEqual(self.run.calls, [])

    def test_locked_legion_is_reported_by_main_as_capture_failed(self):
        with mock.patch.object(vp, "legion_probe", return_value=vp.MSG_LOCKED), \
                mock.patch.object(vp.LegionBackend, "close", lambda self: True):
            out = tempfile.mkdtemp()
            with mock.patch("builtins.print") as pr:
                rc = vp.main(["run", "--out", out, "--remote-zip", "z", "--game-name", "G"])
        self.assertEqual(rc, 2)
        self.assertTrue(any("CAPTURE FAILED: Legion is locked" in str(c.args[0]) for c in pr.call_args_list))

    def test_cold_start_extends_warmup_while_black_then_plays(self):
        shots, sleeps = iter([None, "black", "black", None]), []  # pre-launch ok, 2 black, then real
        b = self.backend(lambda: next(shots), sleeps=sleeps, warmup_max=120)
        b.launch()
        self.assertEqual(sleeps.count(vp.PROBE_INTERVAL), 2)
        self.assertEqual(sleeps[0], 30)  # the warmup itself

    def test_still_black_at_the_limit_reports_re_run_hint(self):
        msg = "capture is black: re-run once before suspecting the build."
        calls = iter([None] + [msg] * 20)
        b = self.backend(lambda: next(calls), warmup=30, warmup_max=50)
        with self.assertRaises(RuntimeError) as cm:
            b.launch()
        self.assertEqual(str(cm.exception), msg)
        self.assertIn("re-run once", str(cm.exception))

    def test_default_warmup_is_30_and_capped(self):
        self.assertEqual(vp.WARMUP_DEFAULT, 30)
        self.assertGreater(vp.WARMUP_MAX, vp.WARMUP_DEFAULT)
        self.assertEqual(vp.LegionBackend("device-host", "z", "G").warmup, 30)

    def test_no_probe_means_old_behaviour(self):
        b = self.backend(None)
        b.launch()
        self.assertEqual(len(self.deployed), 1)

    def test_bare_alt_is_refused_in_the_step_parser(self):
        for name in ("alt", "Alt", "lalt", "menu"):
            with self.assertRaises(ValueError) as cm:
                vp.validate_sequence(valid_sequence(name))
            self.assertIn("bare Alt", str(cm.exception))
            self.assertIn("AMD overlay", str(cm.exception))

    def test_input_script_never_sends_alt(self):
        self.assertNotIn("AltTap", PS1)
        self.assertNotIn("keybd_event", PS1)
        self.assertNotIn('"alt"', PS1)
        self.assertNotIn("0x12, 0", PS1)

    def test_focus_step_retries_minimises_others_and_names_the_holder(self):
        body = PS1[PS1.index("function Assert-GameForeground"):PS1.index("function Save-Shot")]
        self.assertIn("for ($i = 0; $i -lt 6", body)
        self.assertIn("Hide-OtherWindows", body)
        self.assertIn("ForegroundTitle", body)
        self.assertIn("focus is held by", body)
        self.assertIn("ShowWindow($_.MainWindowHandle, 6)", PS1)  # SW_MINIMIZE

    def test_focuses_the_game_before_the_first_step_and_writes_focused(self):
        # mock 16: the video's first ~22 s showed OBS because focus came only at the first key step
        body = PS1[PS1.index("\ntry {"):PS1.index("foreach ($s in $steps)")]
        self.assertIn("Assert-GameForeground", body)  # the strict helper: throws -> ERROR, never films the desktop
        focus, stamp = body.index("Assert-GameForeground"), body.index('"FOCUSED {0}" -f (Get-Date).ToFileTimeUtc()')
        self.assertLess(focus, stamp)
        self.assertIn('Join-Path $OutDir "FOCUSED"', body)
        self.assertLess(PS1.index('Join-Path $OutDir "FOCUSED"'), PS1.index('Join-Path $OutDir "DONE"'))
        d = tempfile.mkdtemp()
        (Path(d) / "FOCUSED").write_text("FOCUSED 1")
        vp.clear_previous(d)  # a rerun never keeps a stale one
        self.assertFalse((Path(d) / "FOCUSED").exists())


class LocalCmdArgv(unittest.TestCase):
    # mock jam 15: `--local-cmd systemd-run --user ...` died with "unrecognized arguments: --user ..."
    def test_one_string_is_split_like_a_shell(self):
        self.assertEqual(vp.local_argv(["systemd-run --user --scope env A='b c' Ed x.uproject -game"]),
                         ["systemd-run", "--user", "--scope", "env", "A=b c", "Ed", "x.uproject", "-game"])

    def test_word_list_and_single_word_unchanged(self):
        self.assertEqual(vp.local_argv(["./Game.sh", "arg"]), ["./Game.sh", "arg"])
        self.assertEqual(vp.local_argv(["./Game.sh"]), ["./Game.sh"])
        self.assertEqual(vp.local_argv(None), [])

    def test_existing_file_path_with_a_space_stays_one_item(self):
        with tempfile.TemporaryDirectory() as d:
            exe = os.path.join(d, "My Game", "Game.sh")
            os.makedirs(os.path.dirname(exe))
            open(exe, "w").close()
            self.assertEqual(vp.local_argv([exe]), [exe])

    def test_cli_accepts_quoted_dash_command(self):
        import argparse  # parse only: one quoted string must not be read as options
        ap = argparse.ArgumentParser()
        ap.add_argument("--local-cmd", nargs="+")
        ns = ap.parse_args(["--local-cmd", "systemd-run --user -game"])
        self.assertEqual(vp.local_argv(ns.local_cmd), ["systemd-run", "--user", "-game"])


if __name__ == "__main__":
    unittest.main()
