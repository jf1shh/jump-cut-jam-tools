"""Tests for scripts/mock_scorecard.py, using small fixture evidence built in tmp dirs."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import mock_scorecard as ms  # noqa: E402

FINDINGS = "# Mock 99\n\nStart: Sat 2026-11-07 21:02 PT. Hard stop: Sun 2026-11-08 07:00 PT.\n"
STEPS = ("# Step shots\n\n| NN | label | path | verdict |\n|---|---|---|---|\n"
         "| 01 | a | /x/01-a.png | OK looks fine |\n| 02 | b | /x/02-b.png | ok: looks fine |\n")
TEMPLATE = "intro\n\n" + ms.START_MARK + "\n" + ms.END_MARK + "\n\nfooter\n"


def run_cli(*args):
    return subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "mock_scorecard.py"), *args],
                          capture_output=True, text=True)


class Fixture(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.d = Path(self._td.name)
        self.addCleanup(self._td.cleanup)

    def write(self, name, text):
        p = self.d / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def args(self, **kw):
        ns = dict(repo=None, findings=None, step_shots=None, assets=None, playtest=None, butler_log=None,
                  agent_gate=None, data=None)
        ns.update(kw)
        return type("A", (), ns)


class TestParsing(Fixture):
    def test_findings_times_are_pacific(self):
        kick, stop = ms.read_findings_times(self.write("f.md", FINDINGS))
        self.assertEqual(ms.local(kick), "2026-11-07T21:02:00-08:00")
        self.assertEqual(ms.local(stop), "2026-11-08T07:00:00-08:00")

    def test_delta_is_real_elapsed_time_across_dst(self):
        # DST ended 2026-11-01 02:00 PDT -> 01:00 PST: 23:00 PDT to 03:00 PST is 5 real hours
        self.assertEqual(ms.fmt_delta(ms.parse_when("2026-10-31T23:00"), ms.parse_when("2026-11-01T03:00")), "5 h 00 min")

    def test_bad_hand_entered_time_is_an_error(self):
        data = self.write("d.json", json.dumps({"first_packaged_at": "2026-11-07 22:55 PT"}))
        with self.assertRaises(ValueError):
            ms.build_row(1, self.args(data=data))
        self.assertIsNone(ms.parse_strict("", "x"))

    def test_bugs_missed_must_be_a_list_of_strings(self):
        for bad in ("floor too big", [1, 2], {"a": 1}):
            data = self.write("d.json", json.dumps({"bugs_missed": bad}))
            with self.assertRaises(ValueError):
                ms.build_row(1, self.args(data=data))

    def test_non_build_commit_subjects_do_not_match(self):
        for s in ("notes: nothing shipped yet", "fix packaging script path", "docs: packaging checklist",
                  "add package.json", "do not ship yet"):
            self.assertFalse(ms.PACKAGE_RE.search(s), s)
        for s in ("mock 10: package build", "package-and-push ok", "butler push win64"):
            self.assertTrue(ms.PACKAGE_RE.search(s), s)

    def test_failed_butler_push_is_skipped_and_stop_bounds_it(self):
        b = self.write("b.log", "2026-11-07T21:30:00-08:00 butler push failed: invalid API key (401)\n"
                       "2026-11-07T21:40:00-08:00 butler push error\n"
                       "2026-11-07T23:30:00-08:00 butler push ok, build 1234 live\n")
        kick, stop = ms.read_findings_times(self.write("f.md", FINDINGS))
        self.assertEqual(ms.local(ms.butler_first_push(b, kick, stop))[11:16], "23:30")
        self.assertEqual(ms.butler_first_push(b, kick, stop).strftime("%H:%M"), "23:30")  # log's own offset kept
        late = self.write("late.log", "2026-11-09T10:00:00-08:00 butler push ok\n")  # next mock
        self.assertIsNone(ms.butler_first_push(late, kick, stop))

    def test_delta(self):
        a, b = ms.parse_when("2026-11-07T21:02"), ms.parse_when("2026-11-07T22:55")
        self.assertEqual(ms.fmt_delta(a, b), "1 h 53 min")
        self.assertEqual(ms.fmt_delta(a, None), "n/a")
        self.assertIn("before kickoff", ms.fmt_delta(b, a))

    def test_butler_first_push(self):
        p = self.write("b.log", "2026-11-07 23:10:00 Pushing build ok\n2026-11-07 22:50:00 butler push ok\nnoise\n")
        self.assertEqual(ms.local(ms.butler_first_push(p))[11:16], "22:50")
        self.assertIsNone(ms.butler_first_push(self.d / "none.log"))


class TestGates(Fixture):
    def test_step_shots(self):
        self.write("s/steps.md", STEPS)
        self.assertEqual(ms.gate_step_shots(self.d / "s")[0], "pass")
        self.write("s2/steps.md", STEPS + "| 03 | c | /x/03-c.png | FAIL: floats |\n")
        self.assertEqual(ms.gate_step_shots(self.d / "s2")[0], "fail")
        self.write("s3/steps.md", STEPS + "| 03 | c | /x/03-c.png | (pending) |\n")
        self.assertEqual(ms.gate_step_shots(self.d / "s3")[0], "n/a")  # not judged yet
        self.write("s4/steps.md", STEPS + "| 03 | c | /x/03-c.png | crate floats 20cm above floor; fix Z |\n")
        self.assertEqual(ms.gate_step_shots(self.d / "s4")[0], "n/a")  # free text is not a pass
        self.write("s5/steps.md", STEPS + "| 03 | c | /x/03-c.png | Badge readable, fine |\n")
        self.assertEqual(ms.gate_step_shots(self.d / "s5")[0], "n/a")  # BAD must be a whole word
        self.assertEqual(ms.gate_step_shots(self.d / "nope")[0], "n/a")

    def test_assets(self):
        self.write("a/x/preview.json", json.dumps({"ok": True}))
        self.write("a/y/preview.json", json.dumps({"ok": True}))
        self.assertEqual(ms.gate_assets(self.d / "a")[0], "pass")
        self.write("a/z/preview.json", json.dumps({"ok": False}))
        self.assertEqual(ms.gate_assets(self.d / "a"), ("fail", "2/3 previews ok"))
        self.assertEqual(ms.gate_assets(self.d / "empty")[0], "n/a")

    def test_playtest_and_motion(self):
        items = [{"id": "level", "auto": "PASS"}, {"id": "input", "auto": "PASS"}, {"id": "motion", "auto": "FAIL"}]
        self.write("p/results.json", json.dumps({"items": items}))
        pt, mo = ms.gate_playtest(self.d / "p")
        self.assertEqual((pt[0], mo[0]), ("pass", "fail"))
        items[0]["auto"] = "FAIL"
        self.write("p/results.json", json.dumps({"items": items}))
        self.assertEqual(ms.gate_playtest(self.d / "p")[0][0], "fail")

    def test_agent_left_to_human_is_not_a_pass(self):
        self.write("p/results.json", json.dumps({"items": [{"id": "hud", "auto": "AGENT"}, {"id": "motion", "auto": "PASS"}]}))
        pt, mo = ms.gate_playtest(self.d / "p")
        self.assertEqual((pt[0], mo[0]), ("n/a", "pass"))  # an item left AGENT on an auto-judged check is not a pass

    def test_failed_capture_is_a_fail(self):
        self.write("s/steps.md", "# Step shots\n\n| NN | label | path | verdict |\n|---|---|---|---|\n"
                   "| 01 | crate | (no file) | FAILED: editor timed out |\n")
        self.assertEqual(ms.gate_step_shots(self.d / "s")[0], "fail")

    def test_auto_only_pass_is_labelled(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import visual_playtest as vp
        items = [{"id": k, "title": t, "auto": "AGENT" if k in ("objects", "endscreen") else "PASS"} for k, t in vp.ITEMS]
        self.write("p/results.json", json.dumps({"items": items}))
        (pt, _), (mo, _) = ms.gate_playtest(self.d / "p")
        self.assertEqual((pt, mo), ("pass", "pass"))
        row = ms.build_row(1, self.args(playtest=self.d / "p"))
        self.assertIn("pass (auto only)", ms.render_row(row))  # never read as a human pass

    def test_motion_found_by_id_not_current_title(self):
        import visual_playtest as vp
        out = self.d / "old"
        out.mkdir()
        (out / "manifest.json").write_text("[]")
        (out / "a.png").write_bytes(b"x")
        items = [{"id": k, "title": ("Old motion wording" if k == "motion" else t), "auto": "PASS", "detail": "",
                  "frames": []} for k, t in vp.ITEMS]
        vp.write_checklist(out, {"items": items, "shots": [{"file": "a.png"}]})
        lines = (out / "checklist.md").read_text().splitlines()
        v = [i for i, l in enumerate(lines) if l == "Verdict: PENDING"]
        for i in v:
            lines[i] = "Verdict: PASS"
        lines[v[-1]] = "Verdict: FAIL - camera keeps drifting"  # motion is last
        (out / "checklist.md").write_text("\n".join(lines))
        (pt, _), (mo, _) = ms.gate_playtest(out)
        self.assertEqual((pt, mo), ("pass", "fail"))

    def test_hand_entered_gate_clears_auto_only_label(self):
        self.write("p/results.json", json.dumps({"items": [{"id": "level", "auto": "PASS"}, {"id": "motion", "auto": "PASS"}]}))
        data = self.write("d.json", json.dumps({"gates": {"playtest": "pass", "clip_motion": "pass"}}))
        text = ms.render_row(ms.build_row(1, self.args(playtest=self.d / "p", data=data)))
        self.assertNotIn("auto only", text)

    def test_ok_word_must_stand_alone(self):
        for verdict in ("Pass-through bug: player falls through the floor", "OK-ish but floor too big",
                        "Good grief, broken"):
            self.write("v/steps.md", STEPS + f"| 03 | c | /x/03-c.png | {verdict} |\n")
            self.assertNotEqual(ms.gate_step_shots(self.d / "v")[0], "pass", verdict)

    def test_run_wide_verify_failure_is_not_a_motion_pass(self):
        import visual_playtest as vp
        out = self.d / "rw"
        out.mkdir()
        (out / "manifest.json").write_text("[]")
        (out / "a.png").write_bytes(b"x")
        items = [{"id": k, "title": t, "auto": "PASS", "detail": "", "frames": []} for k, t in vp.ITEMS]
        vp.write_checklist(out, {"items": items, "shots": [{"file": "a.png"}]})
        (out / "a.png").write_bytes(b"changed after the run")  # run-wide: frames changed
        self.assertFalse(vp.verify(out)[0])
        (pt, _), (mo, _) = ms.gate_playtest(out)
        self.assertEqual((pt, mo), ("fail", "n/a"))

    def test_checklist_verify_decides(self):
        import visual_playtest as vp
        out = self.d / "pt"
        out.mkdir()
        (out / "manifest.json").write_text("[]")
        f = out / "a.png"
        f.write_bytes(b"x")
        items = [{"id": k, "title": t, "auto": "PASS", "detail": "", "frames": []} for k, t in vp.ITEMS]
        items[0]["auto"] = "FAIL"  # an auto FAIL a human overrode below
        results = {"items": items, "shots": [{"file": "a.png"}]}
        vp.write_checklist(out, results)
        lines = (out / "checklist.md").read_text().splitlines()
        v = [i for i, l in enumerate(lines) if l == "Verdict: PENDING"]  # one per item (not the header text)
        for i in v:
            lines[i] = "Verdict: PASS"
        lines[v[0]] = "Verdict: PASS (override: seen by eye)"
        (out / "checklist.md").write_text("\n".join(lines))
        self.assertTrue(vp.verify(out)[0])
        (pt, _), (mo, _) = ms.gate_playtest(out)
        self.assertEqual((pt, mo), ("pass", "pass"))
        # a human FAIL on the motion item (last): playtest and motion columns follow the real gate
        lines[v[-1]] = "Verdict: FAIL - drifts"
        (out / "checklist.md").write_text("\n".join(lines))
        (pt, _), (mo, _) = ms.gate_playtest(out)
        self.assertEqual((pt, mo), ("pass", "fail"))

    def test_missing_results(self):
        pt, mo = ms.gate_playtest(self.d / "nope")
        self.assertEqual((pt[0], mo[0]), ("n/a", "n/a"))

    def test_agent_gate(self):
        self.assertEqual(ms.gate_agent(self.write("g1.txt", "GATE PASS: win, lose and restart"))[0], "pass")
        self.assertEqual(ms.gate_agent(self.write("g2.txt", "GATE FAIL\n- no win"))[0], "fail")
        self.assertEqual(ms.gate_agent(self.write("g3.txt", "hello"))[0], "n/a")
        self.assertEqual(ms.gate_agent(self.d / "none")[0], "n/a")


class TestRow(Fixture):
    def test_full_row(self):
        self.write("s/steps.md", STEPS)
        data = self.write("d.json", json.dumps({
            "first_packaged_at": "2026-11-07T22:55:00-08:00", "first_playable_packaged_at": "2026-11-08T08:40:00-08:00",
            "props_real": 3, "props_primitive": 5, "agent_won_by_real_play": True,
            "bugs_missed": ["a|b", "c"], "gates": {"clip_motion": "pass"}}))
        row = ms.build_row(99, self.args(findings=self.write("f.md", FINDINGS), step_shots=self.d / "s", data=data))
        self.assertEqual(row["to_first_packaged"], "1 h 53 min")
        self.assertEqual(row["to_first_playable_packaged"], "11 h 38 min")
        self.assertEqual(row["gates"]["step_shots"], "pass")
        self.assertEqual(row["gates"]["clip_motion"], "pass")
        self.assertEqual(row["gates"]["asset_previews"], "n/a")
        out = ms.render_row(row)
        self.assertIn("| Mock 99 |", out)
        self.assertIn("3 / 5", out)
        self.assertIn("1. a/b; 2. c", out)  # pipes in free text cannot break the table
        self.assertEqual(out.count("|"), len(ms.ROW_COLS) + 1)

    def test_bad_gate_in_data(self):
        data = self.write("d.json", json.dumps({"gates": {"playtest": "maybe"}}))
        with self.assertRaises(ValueError):
            ms.build_row(1, self.args(data=data))

    def commit(self, repo, msg, when):
        env = {"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when, "PATH": "/usr/bin:/bin", "HOME": str(repo)}
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                        "--allow-empty", "-m", msg], check=True, env=env)

    def repo(self):
        repo = self.d / "repo"
        repo.mkdir()
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        return repo

    def test_git_window_ignores_other_mocks(self):
        repo = self.repo()
        self.commit(repo, "mock 9: package build", "2026-11-06T23:00:00-08:00")      # earlier mock
        self.commit(repo, "add package.json", "2026-11-07T21:30:00-08:00")           # not a packaged build
        self.commit(repo, "mock 10: package build", "2026-11-07T23:00:00-08:00")     # this mock
        self.commit(repo, "mock 11: package build", "2026-11-09T09:00:00-08:00")     # next mock
        f = self.write("f.md", FINDINGS)
        row = ms.build_row(10, self.args(repo=repo, findings=f))
        self.assertEqual(row["to_first_packaged"], "1 h 58 min")
        self.assertIsNone(row["overran"])  # never guessed from a shared repo's log
        data = self.write("d.json", json.dumps({"overran": "no"}))
        self.assertFalse(ms.build_row(10, self.args(repo=repo, findings=f, data=data))["overran"])

    def test_butler_log_before_kickoff_ignored(self):
        b = self.write("b.log", "2026-11-01T10:00:00-08:00 butler push old\n2026-11-07T23:30:00-08:00 butler push ok\n")
        row = ms.build_row(1, self.args(findings=self.write("f.md", FINDINGS), butler_log=b))
        self.assertEqual(row["to_first_packaged"], "2 h 28 min")

    def test_yes_no_words_and_null(self):
        d = lambda **k: self.write("d.json", json.dumps(k))
        self.assertFalse(ms.build_row(1, self.args(data=d(overran="false")))["overran"])
        self.assertTrue(ms.build_row(1, self.args(data=d(overran="yes")))["overran"])
        row = ms.build_row(1, self.args(data=d(overran=None, agent_won_by_real_play=None)))
        self.assertIsNone(row["overran"])
        self.assertIsNone(row["agent_won_by_real_play"])
        with self.assertRaises(ValueError):
            ms.build_row(1, self.args(data=d(overran="maybe")))

    def test_nothing_known_is_na_not_pass(self):
        row = ms.build_row(3, self.args())
        self.assertEqual(set(row["gates"].values()), {"n/a"})
        self.assertIsNone(row["overran"])
        self.assertIn("n/a", ms.render_row(row))


class TestUpdate(Fixture):
    def row(self, n, note=""):
        r = ms.build_row(n, self.args())
        r["notes"] = note
        return r

    def test_append_replace_sort(self):
        p = self.write("sc.md", TEMPLATE)
        ms.update_file(p, self.row(11, "eleven"))
        ms.update_file(p, self.row(10, "ten"))
        ms.update_file(p, self.row(11, "eleven v2"))
        text = p.read_text()
        self.assertEqual(text.count("| Mock 11 |"), 1)
        self.assertLess(text.index("| Mock 10 |"), text.index("| Mock 11 |"))
        self.assertIn("eleven v2", text)
        self.assertNotIn("| eleven |", text)
        self.assertTrue(text.startswith("intro") and text.rstrip().endswith("footer"))
        self.assertEqual(text.count("| Mock |"), 1)  # one header

    def test_missing_markers(self):
        with self.assertRaises(ValueError):
            ms.update_file(self.write("bad.md", "no markers"), self.row(1))


class TestCli(Fixture):
    def test_cli_row_and_update(self):
        f = self.write("f.md", FINDINGS)
        r = run_cli("--mock", "5", "--findings", str(f))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("| Mock 5 |"))
        p = self.write("sc.md", TEMPLATE)
        r = run_cli("--mock", "5", "--update", str(p))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("| Mock 5 |", p.read_text())

    def test_cli_json_and_error(self):
        r = run_cli("--mock", "5", "--json")
        self.assertEqual(json.loads(r.stdout)["mock"], 5)
        r = run_cli("--mock", "5", "--data", str(self.d / "missing.json"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("mock_scorecard:", r.stderr)


class TestMock10Row(unittest.TestCase):
    def test_committed_data_scores_mock_10(self):
        a = type("A", (), dict(repo=None, findings=str(ROOT / "stages/00_prep/output/mock-jam-findings-10.md"), step_shots=None,
                               assets=None, playtest=None, butler_log=None, agent_gate=None,
                               data=str(ROOT / "stages/00_prep/output/mock-scorecard-10.json")))
        row = ms.build_row(10, a)
        self.assertEqual(row["to_first_packaged"], "1 h 53 min")
        self.assertEqual(row["to_first_playable_packaged"], "11 h 38 min")
        self.assertTrue(row["overran"])
        self.assertFalse(row["agent_won_by_real_play"])
        self.assertEqual(len(row["bugs_missed"]), 3)


if __name__ == "__main__":
    unittest.main()
