"""Tests for scripts/gen_devlog.py: resuming from the last entry's Build/version commit (no git needed)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import gen_devlog as gd  # noqa: E402


class ResumeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._old = gd.DEVLOG_DIR
        gd.DEVLOG_DIR = Path(self._tmp.name)
        self.addCleanup(setattr, gd, "DEVLOG_DIR", self._old)

    def write(self, name, text):
        (gd.DEVLOG_DIR / name).write_text(text)

    def test_resumes_from_its_own_generated_entry(self):
        entry = gd.render_entry("2026-11-12", "abc1234", ["- x"], None, None, [])
        self.write("2026-11-12.md", entry)
        self.assertEqual(gd.find_last_build_ref(), "abc1234")

    def test_commit_subject_naming_build_version_is_ignored(self):
        entry = gd.render_entry("2026-11-12", "bbbbbbb", ["- fix gen_devlog Build/version resume regex (`aaaaaaa`)"], None, None, [])
        self.write("2026-11-12.md", entry)
        self.assertEqual(gd.find_last_build_ref(), "bbbbbbb")

    def test_prose_mention_and_later_hex_word_is_ignored(self):
        self.write(
            "2026-11-12.md",
            "# x\n\n- resumes from the Build/version line.\n- see `c0ffee1`\n\n## Build/version\n`ddddddd` (2026-11-12)\n",
        )
        self.assertEqual(gd.find_last_build_ref(), "ddddddd")

    def test_hand_edited_forms_still_resume(self):
        forms = [
            "## Build/version\nMaster `abc1234`, 2026-11-12\n",
            "## Build/version\n\n   \n`abc1234`\n",
            "## Build/version:\n`abc1234`\n",
            "- **Build/version:** `abc1234`\n",
            "## Build/version\n`abc1234`",
        ]
        for form in forms:
            with self.subTest(form=form):
                self.write("2026-11-12.md", "# x\n\n- see `c0ffee1`\n\n" + form)
                self.assertEqual(gd.find_last_build_ref(), "abc1234")

    def test_hash_after_the_next_heading_is_not_used(self):
        self.write("2026-11-12.md", "## Build/version\nzip only\n\n## Notes\n`c0ffee1`\n")
        self.assertIsNone(gd.find_last_build_ref())

    def test_bullet_form_with_zip_only_ignores_later_bullets(self):
        self.write(
            "2026-11-12.md",
            "- **Build/version:** `SilentBlade_LastLight.zip`, packaged 2026-11-12\n- **Screenshots:** see the fix in `c0ffee1`\n",
        )
        self.assertIsNone(gd.find_last_build_ref())

    def test_existing_entry_is_not_overwritten(self):
        self.write("2026-11-10.md", "hand written\n")
        saved = (gd.is_git_ref, gd.fetch_commits, gd.run_git)
        self.addCleanup(lambda: [setattr(gd, n, f) for n, f in zip(("is_git_ref", "fetch_commits", "run_git"), saved)])
        gd.is_git_ref = lambda ref: True
        gd.fetch_commits = lambda range_args: []
        gd.run_git = lambda args: "480d8e3\n"
        old_argv = sys.argv
        self.addCleanup(setattr, sys, "argv", old_argv)
        sys.argv = ["gen_devlog.py", "--since", "480d8e3", "--date", "2026-11-10"]
        with self.assertRaises(SystemExit) as cm:
            gd.main()
        self.assertEqual(cm.exception.code, 2)
        self.assertEqual((gd.DEVLOG_DIR / "2026-11-10.md").read_text(), "hand written\n")
        sys.argv = sys.argv + ["--force"]
        gd.main()
        self.assertNotEqual((gd.DEVLOG_DIR / "2026-11-10.md").read_text(), "hand written\n")

    def test_newest_entry_wins(self):
        self.write("2026-11-12.md", gd.render_entry("2026-11-12", "1111111", [], None, None, []))
        self.write("2026-11-13.md", gd.render_entry("2026-11-13", "2222222", [], None, None, []))
        self.assertEqual(gd.find_last_build_ref(), "2222222")

    def test_non_hash_tag_means_nothing_to_resume(self):
        self.write("2026-10-29.md", "## Build/version\n`SilentBlade_LastLight.zip`, packaged.\n")
        self.assertIsNone(gd.find_last_build_ref())

    def test_no_entries(self):
        self.assertIsNone(gd.find_last_build_ref())

    def test_non_entry_files_in_devlog_dir_do_not_hide_the_last_entry(self):
        self.write("2026-11-12.md", gd.render_entry("2026-11-12", "1111111", [], None, None, []))
        for name in ("decisions.md", "evidence.md", "itch-devlog-template.md", "ai-disclosure-draft.md"):
            self.write(name, "## Build/version\n`deadbee`\n")
        self.assertEqual(gd.find_last_build_ref(), "1111111")


DECISIONS = """# Decision log

| ID | Date (PT) | Who | Decision | Why | Link |
|---|---|---|---|---|---|
| D-001 | 2026-10-27 | owner | Unreal Engine, not UEFN | full control | `stages/00_prep/references/win-plan.md` |
| D-002 | 2026-11-12 09:30 | hub | Cut the grapple | not fun yet | PR #170 |
| D-003 | 2026-11-13 | owner | Tomorrow's call |  |  |
not a row | D-009 | x |
"""


class DecisionsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._old = gd.DEVLOG_DIR
        gd.DEVLOG_DIR = Path(self._tmp.name)
        self.addCleanup(setattr, gd, "DEVLOG_DIR", self._old)
        (gd.DEVLOG_DIR / "decisions.md").write_text(DECISIONS)

    def test_parses_rows_only(self):
        rows = gd.load_decisions()
        self.assertEqual([r["id"] for r in rows], ["D-001", "D-002", "D-003"])
        self.assertEqual(rows[1], {"id": "D-002", "date": "2026-11-12 09:30", "who": "hub", "what": "Cut the grapple",
                                   "why": "not fun yet", "link": "PR #170"})

    def test_skips_ids_already_in_an_entry_and_future_rows(self):
        (gd.DEVLOG_DIR / "2026-11-11.md").write_text("## Decisions since the last entry\n- **D-001** ...\n")
        got = gd.decisions_not_yet_logged(gd.load_decisions(), "2026-11-12")
        self.assertEqual([d["id"] for d in got], ["D-002"])

    def test_rewriting_todays_entry_keeps_its_decisions(self):
        (gd.DEVLOG_DIR / "2026-11-12.md").write_text("- **D-002**\n")
        got = gd.decisions_not_yet_logged(gd.load_decisions(), "2026-11-12")
        self.assertEqual([d["id"] for d in got], ["D-001", "D-002"])

    def test_rendered_draft_has_decisions_evidence_and_marked_placeholders(self):
        import evidence_index as ei
        decisions = gd.decisions_not_yet_logged(gd.load_decisions(), "2026-11-12")
        evidence = [ei.Item("video", "2026-11-12T06:00:00Z", "work/capture/cut.mp4")]
        draft = gd.render_entry("2026-11-12", "abc1234", ["- x"], None, None, [],
                                decisions=decisions, evidence=evidence, ai_hints=["image:gpt", "3d:meshy"])
        self.assertIn("## Decisions since the last entry\n- **D-001** (2026-10-27, owner): Unreal Engine, not UEFN. "
                      "Why: full control. (`stages/00_prep/references/win-plan.md`)", draft)
        self.assertIn("- video · 2026-11-12T06:00:00Z · `work/capture/cut.mp4`", draft)
        self.assertIn("Asset-log providers in this window: `image:gpt`, `3d:meshy`.", draft)
        self.assertEqual(draft.count(gd.OWNER_FILL), 3)
        draft = gd.render_entry("2026-11-12", "abc1234", ["- x"], "next", "huh", [], decisions=[], evidence=[])
        self.assertIn("- None logged in `stages/05_devlog/output/decisions.md` since the last entry.", draft)
        self.assertIn("- none found", draft)
        self.assertEqual(draft.count(gd.OWNER_FILL), 1)  # the AI disclosure always needs the owner's check

    def test_asset_log_providers_in_window(self):
        from datetime import datetime, timezone
        log = gd.DEVLOG_DIR / "log.csv"
        log.write_text(
            "timestamp_iso,name,stage,seconds,exit_code,output_path,human_review\n"
            "2026-11-11T01:00:00Z,a,image:gpt,1,0,x,\n"
            "2026-11-12T06:00:00Z,b,image:gpt,1,0,x,\n"
            "2026-11-12T06:00:00Z,b,3d:meshy,1,0,x,\n"
            "2026-11-12T06:00:00Z,c,image:grok,1,1,x,\n"
            "2026-11-12T06:00:00Z,c,total,1,0,x,\n"
            "garbage,c,image:fal,1,0,x,\n"
        )
        start = datetime(2026, 11, 12, tzinfo=timezone.utc)
        self.assertEqual(gd.asset_log_providers(start, log), ["3d:meshy", "image:gpt"])
        self.assertEqual(gd.asset_log_providers(None, log), [])


if __name__ == "__main__":
    unittest.main()
