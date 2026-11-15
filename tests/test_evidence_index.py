"""Tests for scripts/evidence_index.py: classification, builds, ordering, determinism (no git, no network)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_index as ei  # noqa: E402

T1 = 1762920000  # 2025-11-12T04:00:00Z
T2 = T1 + 3600
T3 = T1 + 7200


class TreeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def put(self, rel, text="x", mtime=T1):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        os.utime(path, (mtime, mtime))
        return path

    def collect(self, **kw):
        return ei.collect(str(self.root), use_git=False, **kw)


class ClassifyTest(unittest.TestCase):
    def test_categories(self):
        cases = {
            "stages/00_prep/output/mock-scorecard-12.json": "scorecard",
            "stages/00_prep/references/mock-scorecard.md": "scorecard",
            "work/capture/final_cut.mp4": "video",
            "work/obs/run.MKV": "video",
            "stages/03_playtest/output/playtest-10/step_03.png": "playtest-frame",
            "work/visual_playtest/frames/0001.jpg": "playtest-frame",
            "stages/03_playtest/output/qa-screenshots/menu.png": "screenshot",
            "stages/00_prep/output/mock12/hud.JPG": "screenshot",
            "stages/00_prep/references/win-plan.md": None,
            "stages/00_prep/output/scorecard-notes.txt": None,
            "_config/reference/engine-reference/unreal/shot.png": None,
            "scripts/__pycache__/x.png": None,
        }
        for path, want in cases.items():
            with self.subTest(path=path):
                self.assertEqual(ei.classify(path), want)

    def test_parse_time_forms(self):
        self.assertEqual(ei.iso_utc(ei.parse_time("2026-11-12")), "2026-11-12T00:00:00Z")
        self.assertEqual(ei.iso_utc(ei.parse_time("2026-11-11T21:00:00-08:00")), "2026-11-12T05:00:00Z")
        self.assertEqual(ei.iso_utc(ei.parse_time("2026-11-12T05:00:00Z")), "2026-11-12T05:00:00Z")


class CollectTest(TreeTest):
    def test_lists_each_kind_with_time_and_path(self):
        self.put("stages/03_playtest/output/qa-screenshots/menu.png", mtime=T2)
        self.put("work/capture/cut.mp4", mtime=T3)
        self.put("stages/03_playtest/output/playtest-10/f1.png", mtime=T1)
        self.put("stages/00_prep/output/mock-scorecard-10.json", "{}", mtime=T1)
        self.put("stages/00_prep/output/notes.md", "nothing here", mtime=T1)
        items = self.collect()
        got = [(i.category, i.timestamp, i.path) for i in items]
        self.assertEqual(got, [
            ("scorecard", "2025-11-12T04:00:00Z", "stages/00_prep/output/mock-scorecard-10.json"),
            ("playtest-frame", "2025-11-12T04:00:00Z", "stages/03_playtest/output/playtest-10/f1.png"),
            ("screenshot", "2025-11-12T05:00:00Z", "stages/03_playtest/output/qa-screenshots/menu.png"),
            ("video", "2025-11-12T06:00:00Z", "work/capture/cut.mp4"),
        ])

    def test_builds_csv_and_doc_mentions(self):
        self.put(
            "stages/05_devlog/output/builds.csv",
            "timestamp_iso,tag,commit,itch_target,itch_build,note\n"
            "2026-11-12T22:10:00-08:00,gate1-thu,abc1234,jf1shh/megajam:win64,2360001,build #1\n"
            ",,,,,blank time row is skipped\n",
        )
        self.put("stages/00_prep/output/mock-findings.md", "pushed to `jf1shh/megajam-pretest:win64` (build #2334237, processed)\n", mtime=T1)
        self.put("stages/00_prep/output/later.md", "same build #2334237 again\nand build **#2335223**\n", mtime=T2)
        self.put("stages/05_devlog/output/2026-11-12.md", "quotes build #2999999\n", mtime=T2)
        builds = [i for i in self.collect() if i.category == "build"]
        self.assertEqual([(b.timestamp, b.path) for b in builds], [
            ("2025-11-12T04:00:00Z", "stages/00_prep/output/mock-findings.md:1"),
            ("2025-11-12T05:00:00Z", "stages/00_prep/output/later.md:2"),
            ("2026-11-13T06:10:00Z", "stages/05_devlog/output/builds.csv"),
        ])
        self.assertIn("itch build #2334237; itch_target: jf1shh/megajam-pretest:win64", builds[0].detail)
        self.assertIn("itch build #2360001", builds[2].detail)
        self.assertIn("tag: gate1-thu", builds[2].detail)
        self.assertIn("commit: abc1234", builds[2].detail)

    def test_missing_dirs_and_csv_are_fine(self):
        self.assertEqual(self.collect(dirs=["nope"], builds_csv="missing.csv"), [])

    def test_output_file_is_not_indexed(self):
        self.put("stages/05_devlog/output/evidence.md", "build #1234567\n")
        self.assertEqual(self.collect(), [])

    def test_filter_since(self):
        self.put("stages/03_playtest/output/qa-screenshots/a.png", mtime=T1)
        self.put("stages/03_playtest/output/qa-screenshots/b.png", mtime=T3)
        kept = ei.filter_since(self.collect(), "2025-11-12T05:00:00Z")
        self.assertEqual([i.path for i in kept], ["stages/03_playtest/output/qa-screenshots/b.png"])
        self.assertEqual(len(ei.filter_since(self.collect(), None)), 2)

    def test_git_timestamps_win_over_mtime(self):
        self.put("stages/03_playtest/output/qa-screenshots/a.png", mtime=T3)
        env = {**os.environ, "GIT_AUTHOR_DATE": "2026-11-12T01:02:03Z", "GIT_COMMITTER_DATE": "2026-11-12T01:02:03Z"}
        git = ["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
        subprocess.run([*git, "init", "-q"], check=True)
        subprocess.run([*git, "add", "."], check=True)
        subprocess.run([*git, "commit", "-q", "-m", "x"], check=True, env=env)
        self.put("work/untracked.png", mtime=T1)
        items = ei.collect(str(self.root), use_git=True)
        self.assertEqual({i.path: i.timestamp for i in items}, {
            "stages/03_playtest/output/qa-screenshots/a.png": "2026-11-12T01:02:03Z",
            "work/untracked.png": "2025-11-12T04:00:00Z",
        })


class RenderTest(TreeTest):
    def test_markdown_is_deterministic_and_lists_empty_sections(self):
        self.put("stages/03_playtest/output/qa-screenshots/a|b.png", mtime=T1)
        self.put("stages/00_prep/output/mock-scorecard-10.json", "{}", mtime=T2)
        first = ei.render_markdown(self.collect())
        second = ei.render_markdown(self.collect())
        self.assertEqual(first, second)
        self.assertIn("Totals: builds (itch) 0, scorecards 1, videos 0, playtest frames 0, screenshots 1.", first)
        self.assertIn("## Videos\n\nNone yet.", first)
        self.assertIn("| 2025-11-12T05:00:00Z | `stages/00_prep/output/mock-scorecard-10.json` |  |", first)
        self.assertLess(first.index("## Builds"), first.index("## Scorecards"))

    def test_bullets_are_capped(self):
        items = [ei.Item("screenshot", f"2026-11-12T00:00:{n:02d}Z", f"p{n}.png") for n in range(5)]
        out = ei.render_bullets(items, limit=3)
        self.assertEqual(len(out), 4)
        self.assertEqual(out[0], "- screenshot · 2026-11-12T00:00:00Z · `p0.png`")
        self.assertIn("2 more", out[-1])

    def test_main_json_and_out(self):
        self.put("work/capture/cut.webm", mtime=T1)
        buf = StringIO()
        with redirect_stdout(buf):
            ei.main(["--root", str(self.root), "--no-git", "--format", "json"])
        self.assertEqual(json.loads(buf.getvalue()), [
            {"category": "video", "timestamp": "2025-11-12T04:00:00Z", "path": "work/capture/cut.webm", "detail": ""},
        ])
        out = self.root / "evidence.md"
        with redirect_stdout(StringIO()):
            ei.main(["--root", str(self.root), "--no-git", "--out", str(out)])
        self.assertIn("`work/capture/cut.webm`", out.read_text())


if __name__ == "__main__":
    unittest.main()
