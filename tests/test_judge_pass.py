"""Tests for scripts/judge_pass.py with fake sessions, fake pages and a fake video probe (no ffprobe, no GPU)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import judge_pass as jp  # noqa: E402

GOOD_PAGE = """# Game
![a](s1.png) ![b](s2.png) ![c](s3.png)
Video: https://youtu.be/abc
## Controls
WASD to move, mouse to look, space to jump.
## Credits
Made solo.
## AI declaration
Art was generated with AI models; code assisted by an AI agent.
"""


def PASSED(_session):
    """Stand-in for the gate receipt check (visual_playtest.receipt_valid) on a hand-made gate folder."""
    return True


def probe_ok(_p):
    return 45.0, 1920, 1080


class Base(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.d = Path(self._td.name)
        self.addCleanup(self._td.cleanup)

    def session(self, marks=("win", "lose", "restart"), extra_marks=()):
        """20 captured frames (all real input, game in front), then marks on frames 5, 6, 7.
        extra_marks: more journal lines appended after the marks."""
        s = self.d / "sess"
        (s / "frames").mkdir(parents=True)
        lines = []
        for i in range(20):
            (s / "frames" / f"{i:03d}_x.png").write_bytes(b"png")
            lines.append({"kind": "press", "file": f"frames/{i:03d}_x.png", "game_in_front": True})
        order = ["win", "lose", "restart"]
        lines += [{"kind": "mark", "event": m, "evidence": [f"frames/{5 + order.index(m):03d}_x.png"], "note": f"{m} seen"}
                  for m in marks]
        lines += list(extra_marks)
        (s / "journal.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
        return s

    def page(self, text=GOOD_PAGE):
        p = self.d / "page"
        p.mkdir(exist_ok=True)
        (p / "index.md").write_text(text)
        for n in ("s1.png", "s2.png", "s3.png"):
            (p / n).write_bytes(b"x")
        return p


class PageCheck(Base):
    def test_good_page(self):
        r = jp.check_page(self.page(), probe=probe_ok)
        self.assertTrue(r["ok"], r)

    def test_missing_everything(self):
        p = self.page("# Game\nhello")
        for n in ("s1.png", "s2.png", "s3.png"):
            (p / n).unlink()
        r = jp.check_page(p, probe=probe_ok)
        failed = {c["name"] for c in r["checks"] if not c["ok"]}
        self.assertEqual(failed, {"video", "screenshots", "controls_text", "credits", "ai_declaration"})

    def test_local_video_length_and_size(self):
        p = self.page(GOOD_PAGE.replace("https://youtu.be/abc", ""))
        (p / "clip.mp4").write_bytes(b"x")
        self.assertTrue(jp.check_page(p, probe=probe_ok)["ok"])
        short = jp.check_page(p, probe=lambda _p: (12.0, 1920, 1080))
        self.assertFalse(next(c for c in short["checks"] if c["name"] == "video")["ok"])
        small = jp.check_page(p, probe=lambda _p: (45.0, 1280, 720))
        self.assertFalse(next(c for c in small["checks"] if c["name"] == "video")["ok"])

    def test_unprobeable_video_fails_loudly(self):
        p = self.page(GOOD_PAGE.replace("https://youtu.be/abc", ""))
        (p / "clip.mp4").write_bytes(b"x")
        r = jp.check_page(p, probe=lambda _p: None)
        self.assertIn("by hand", next(c for c in r["checks"] if c["name"] == "video")["detail"])
        self.assertFalse(r["ok"])

    def checks(self, text, **kw):
        r = jp.check_page(self.page(text), probe=probe_ok, **kw)
        return {c["name"]: c["ok"] for c in r["checks"]}

    def test_channel_link_is_not_a_video(self):
        t = GOOD_PAGE.replace("https://youtu.be/abc", "Music by Foo, https://www.youtube.com/@foomusic")
        self.assertFalse(self.checks(t)["video"])
        self.assertTrue(self.checks(GOOD_PAGE.replace("https://youtu.be/abc", "https://www.youtube.com/watch?v=abc"))["video"])

    def test_prose_is_not_controls_or_ai_declaration(self):
        r = self.checks("# Game\nYou control a lone ship in deep space. Outsmart cunning AI enemies "
                        "and collect upgrade models.\n")
        self.assertFalse(r["controls_text"])
        self.assertFalse(r["ai_declaration"])

    def test_ai_word_alone_is_not_a_declaration(self):
        for t in ("# Game\n## Smart AI enemies\nThey hunt you.\n", "# Game\nWe built a clever enemy AI that hunts you.\n"):
            self.assertFalse(self.checks(t)["ai_declaration"], t)
        for t in ("## AI use\nArt by a model.", "Art was made with AI tools.", "Music is AI-generated."):
            self.assertTrue(self.checks("# Game\n" + t)["ai_declaration"], t)

    def test_game_ai_prose_is_not_a_declaration(self):
        for t in ("A game made by Jo where you outwit an AI.", "**Smart AI** enemies use cover and flank you.",
                  "## Outsmart the AI: use stealth"):
            self.assertFalse(self.checks("# Game\n" + t + "\n")["ai_declaration"], t)

    def test_controls_keeps_sub_headings_and_bold_labels(self):
        for t in ("## Controls\n**Keyboard & Mouse**\n- WASD: move\n## Credits\nJo\n",
                  "## Controls\n### Keyboard\nWASD to move\n### Gamepad\nStick\n## Credits\nJo\n"):
            self.assertTrue(self.checks(t)["controls_text"], t)

    def test_plain_text_labels(self):
        r = self.checks("Game\nControls: WASD to move, mouse to look.\nCredits: Jo\n")
        self.assertTrue(r["controls_text"] and r["credits"])
        r = self.checks("Control your ship with the keyboard and mouse. Credit goes to Jo.\n")
        self.assertFalse(r["controls_text"] or r["credits"])

    def test_html_page_headings(self):
        html = ("<h1>Game</h1><h2>Controls</h2><p>WASD to move.</p><h2>Credits</h2><p>Me</p>"
                "<h2>AI declaration</h2><p>Art generated with AI.</p>"
                "<img src=\"s1.png\"><img src=\"s2.png\"><img src=\"s3.png\">"
                "<iframe src=\"https://www.youtube.com/embed/abc\"></iframe>")
        p = self.d / "html"
        p.mkdir()
        for n in ("s1.png", "s2.png", "s3.png"):
            (p / n).write_bytes(b"x")
        (p / "page.html").write_text(html)
        r = jp.check_page(p / "page.html", probe=probe_ok)
        self.assertTrue(r["ok"], r)

    def test_controls_section_is_bounded_by_next_heading(self):
        t = "## Controls\nTBD\n## Credits\nKeyboard click sounds by Foo. Music by Mouse Trap Band.\n"
        self.assertFalse(self.checks(t)["controls_text"])

    def test_non_latin_scripts_fail_english(self):
        for t in ("مرحبا بكم", "Καλώς ήρθατε", "こんにちは"):
            self.assertFalse(self.checks(GOOD_PAGE + t)["english_only"], t)
        self.assertTrue(self.checks(GOOD_PAGE + "Café naïve")["english_only"])

    def test_page_file_does_not_scan_neighbours(self):
        # the page is one file; images and videos in the folder around it are not its screenshots or video
        base = self.d / "docs"
        (base / "deep").mkdir(parents=True)
        for i in range(5):
            (base / "deep" / f"{i}.png").write_bytes(b"x")
        (base / "deep" / "playtest.mp4").write_bytes(b"x")
        page = base / "itch.md"
        page.write_text(GOOD_PAGE.replace("https://youtu.be/abc", "").replace("![a](s1.png) ![b](s2.png) ![c](s3.png)", ""))
        r = {c["name"]: c["ok"] for c in jp.check_page(page, probe=probe_ok)["checks"]}
        self.assertFalse(r["screenshots"])
        self.assertFalse(r["video"])

    def test_page_file_counts_its_own_image_refs_and_video(self):
        base = self.d / "docs2"
        base.mkdir()
        for n in ("s1.png", "s2.png", "s3.png", "trailer.mp4"):
            (base / n).write_bytes(b"x")
        page = base / "itch.md"
        page.write_text(GOOD_PAGE.replace("https://youtu.be/abc", "trailer.mp4"))
        r = {c["name"]: c["ok"] for c in jp.check_page(page, probe=probe_ok)["checks"]}
        self.assertTrue(r["screenshots"])
        self.assertTrue(r["video"])

    def test_nonexistent_page(self):
        with self.assertRaises(jp.UsageError):
            jp.check_page(self.d / "nope")


class Packet(Base):
    def test_packet_has_marked_evidence_first(self):
        out = self.d / "out"
        pk = jp.build_packet(self.session(), self.page(), out, max_frames=6, probe=probe_ok)
        names = [f["name"] for f in pk["files"]]
        self.assertEqual(len(names), 6)
        self.assertEqual({f["milestone"] for f in pk["files"][:3]}, {"win", "lose", "restart"})
        for n in names:
            self.assertTrue((out / "frames" / n).is_file())
        prompt = (out / "prompt.md").read_text()
        for c in jp.CRITERIA:
            self.assertIn(c, prompt)
        self.assertIn("Do not open the", prompt)
        self.assertTrue((out / "report-template.json").is_file())

    def test_later_bad_mark_does_not_replace_the_gate_choice(self):
        # a later `mark win` on a file the journal never captured is not usable; the gate keeps the earlier one
        bad = {"kind": "mark", "event": "win", "evidence": ["frames/999_gone.png"], "note": "bad"}
        pk = jp.build_packet(self.session(extra_marks=[bad]), self.page(), self.d / "o", probe=probe_ok)
        win = next(f for f in pk["files"] if f["milestone"] == "win")
        self.assertEqual(win["source"], "frames/005_x.png")

    def test_rerun_drops_old_frames(self):
        out = self.d / "out"
        sess = self.session()
        jp.build_packet(sess, self.page(), out, probe=probe_ok)
        (out / "frames" / "frames__000_oldbuild.png").write_bytes(b"old")
        jp.build_packet(sess, self.page(), out, probe=probe_ok)
        self.assertFalse((out / "frames" / "frames__000_oldbuild.png").exists())

    def test_out_cannot_be_the_session_folder(self):
        sess = self.session()
        with self.assertRaises(jp.UsageError):
            jp.build_packet(sess, self.page(), sess, probe=probe_ok)
        self.assertTrue((sess / "frames" / "005_x.png").is_file())

    def test_foreign_frames_folder_is_not_deleted(self):
        out = self.d / "out"
        (out / "frames").mkdir(parents=True)
        (out / "frames" / "mine.png").write_bytes(b"keep")
        jp.build_packet(self.session(), self.page(), out, probe=probe_ok)
        self.assertTrue((out / "frames" / "mine.png").exists())

    def test_missing_milestone_refused(self):
        with self.assertRaises(jp.UsageError):
            jp.build_packet(self.session(marks=("win", "lose")), self.page(), self.d / "o", probe=probe_ok)

    def test_spread(self):
        self.assertEqual(jp.spread(list(range(10)), 3), [0, 4, 9])
        self.assertEqual(jp.spread([1, 2], 5), [1, 2])
        self.assertEqual(jp.spread([1, 2, 3], 0), [])


class GateFolder(Base):
    """A visual_playtest folder: results.json, frames and contact sheets in the folder, no journal.jsonl."""

    def gate(self):
        g = self.d / "gate"
        g.mkdir()
        for i in range(10):
            (g / f"{i + 1:02d}_step.png").write_bytes(b"png")
        (g / "contact_steps_1.png").write_bytes(b"sheet")
        (g / "results.json").write_text('{"run_id": "r1", "items": []}')
        return g

    def test_packet_builds_without_journal(self):
        g, out = self.gate(), self.d / "out"
        pk = jp.build_packet(g, self.page(), out, max_frames=4, probe=probe_ok, gate_check=PASSED)
        self.assertEqual(pk["source_kind"], "visual_playtest")
        self.assertEqual(pk["marks"], {})
        self.assertEqual(len(pk["files"]), 4)
        self.assertTrue(all(f["milestone"] is None and "contact" not in f["name"] for f in pk["files"]))
        self.assertTrue((out / "prompt.md").is_file())
        self.assertIn("UNTESTED", (out / "prompt.md").read_text())

    def test_out_inside_gate_folder_is_fine_but_not_the_folder_itself(self):
        g = self.gate()
        jp.build_packet(g, self.page(), g / "judge", probe=probe_ok, gate_check=PASSED)
        self.assertTrue((g / "01_step.png").is_file())
        with self.assertRaises(jp.UsageError):
            jp.build_packet(g, self.page(), g, probe=probe_ok, gate_check=PASSED)

    def test_unpassed_gate_is_refused(self):
        g = self.gate()  # results.json but no gate.ok: the real receipt check says no
        with self.assertRaises(jp.UsageError) as cm:
            jp.build_packet(g, self.page(), self.d / "o", probe=probe_ok)
        self.assertIn("gate has not passed", str(cm.exception))
        with self.assertRaises(jp.UsageError):
            jp.build_packet(g, self.page(), self.d / "o", probe=probe_ok, gate_check=lambda _s: False)

    def test_default_sequence_keeps_stills_over_idle_bursts(self):
        g = self.d / "gate2"
        g.mkdir()
        seq = [("shot", "start"), ("shot", "idle"), ("burst", "midplay"), ("shot", "after_w"), ("shot", "after_d"),
               ("shot", "after_space"), ("shot", "after_click"), ("shot", "after_look"), ("shot", "late"),
               ("burst", "lose"), ("shot", "restarted"), ("burst", "afterrestart")]
        n = 0
        for op, label in seq:
            if op == "shot":
                n += 1
                (g / f"{n:02d}_{label}.png").write_bytes(b"png")
            else:
                for i in range(1, 13):
                    n += 1
                    (g / f"{n:02d}_burst_{label}_{i:02d}.png").write_bytes(b"png")
        (g / "results.json").write_text('{"run_id": "r1", "items": []}')
        pk = jp.build_packet(g, self.page(), g / "judge", probe=probe_ok, gate_check=PASSED)
        names = [f["source"] for f in pk["files"]]
        self.assertEqual(len(names), 12)
        self.assertEqual(len([x for x in names if "_burst_" in x]), 3)  # one per burst, stills all kept
        for must in ("15_after_w.png", "20_late.png", "16_after_d.png"):
            self.assertIn(must, names)

    def test_prompt_does_not_claim_a_win_for_a_gate_folder(self):
        g, out = self.gate(), self.d / "o"
        jp.build_packet(g, self.page(), out, probe=probe_ok, gate_check=PASSED)
        prompt = " ".join((out / "prompt.md").read_text().split())
        self.assertNotIn("can be won", prompt.replace("do not assume the build can be won", ""))
        self.assertIn("no win, lose or restart evidence", prompt)

    def test_frames_past_99_keep_capture_order(self):
        g = self.d / "big"
        g.mkdir()
        for i in range(1, 106):
            (g / f"{i:02d}_x.png").write_bytes(b"png")
        (g / "results.json").write_text('{"run_id": "r1", "items": []}')
        pk = jp.build_packet(g, self.page(), g / "judge", probe=probe_ok, gate_check=PASSED)
        nums = [int(f["source"].split("_")[0]) for f in pk["files"]]
        self.assertEqual(nums, sorted(nums))
        self.assertEqual(nums[0], 1)
        self.assertEqual(nums[-1], 105)

    def test_manifest_burst_flag_marks_idle_frames(self):
        g = self.gate()
        (g / "manifest.json").write_text(json.dumps(
            [{"file": f"{i + 1:02d}_step.png", "burst": "idle", "burst_index": i} for i in range(5, 10)]))
        pk = jp.build_packet(g, self.page(), self.d / "o", max_frames=6, probe=probe_ok, gate_check=PASSED)
        names = [f["source"] for f in pk["files"]]
        self.assertEqual(len([x for x in names if x in {f"{i:02d}_step.png" for i in range(6, 11)}]), 1)

    def test_folder_with_neither_file_is_refused(self):
        with self.assertRaises(jp.UsageError):
            jp.build_packet(self.d, self.page(), self.d / "o", probe=probe_ok)


class OfficialCriteria(unittest.TestCase):
    def test_doc_lists_the_labels_in_order(self):
        text = (Path(__file__).resolve().parent.parent / "_config" / "reference" / "canon" / "jam-judging-criteria.md").read_text()
        text = text[text.index("## Judge pass lined up"):]  # the mapping table, not the stream-comparison one
        rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in text.splitlines()
                if ln.startswith("| ") and "`" in ln]
        self.assertEqual([(r[0], r[1].strip("`")) for r in rows],
                         [(jp.LABELS[c], c) for c in jp.CRITERIA])


def good_report(file="a.png"):
    return {"scores": {c: {"score": 3, "evidence": "The frame shows a lit room.", "file": file} for c in jp.CRITERIA},
            "page_notes": "ok", "top_fixes": ["Fix the HUD."]}


class Parse(Base):
    def packet(self):
        return {"files": [{"name": "a.png"}], "page": {"ok": True, "checks": []}}

    def test_fenced_json(self):
        d = jp.extract_json("Here:\n```json\n" + json.dumps(good_report()) + "\n```\nthanks")
        r, probs = jp.validate_report(d, self.packet())
        self.assertEqual(probs, [])
        self.assertEqual(r["total"], 21)

    def test_raw_json(self):
        self.assertIn("scores", jp.extract_json(json.dumps(good_report())))

    def test_no_json(self):
        with self.assertRaises(ValueError):
            jp.extract_json("no braces here")

    def test_bad_scores_and_evidence(self):
        d = good_report()
        d["scores"]["audio"]["score"] = 6
        d["scores"]["visuals"]["score"] = 4.5
        d["scores"]["fun_factor"]["evidence"] = "Fun. Very fun."
        d["scores"]["gameplay"]["file"] = "zzz.png"
        del d["scores"]["level_design"]
        d["scores"]["bonus"] = {}
        _, probs = jp.validate_report(d, self.packet())
        text = "\n".join(probs)
        for needle in ("audio: score", "visuals: score", "fun_factor: evidence must be one", "gameplay: file",
                       "level_design: missing", "unknown criteria"):
            self.assertIn(needle, text)

    def test_file_must_be_one_name(self):
        for bad in (["a.png", "b.png"], {"x": 1}, None):
            d = good_report()
            d["scores"]["audio"]["file"] = bad
            for pk in (self.packet(), None):
                _, probs = jp.validate_report(d, pk)
                self.assertTrue(any("audio: file" in p for p in probs), (bad, pk))

    def test_out_of_range_scores_give_no_total(self):
        d = good_report()
        for c in d["scores"]:
            d["scores"][c]["score"] = 9
        r, probs = jp.validate_report(d, self.packet())
        self.assertTrue(probs)
        self.assertIsNone(r["total"])
        self.assertNotIn("Total", jp.render_md(r))

    def test_bool_score_rejected(self):
        d = good_report()
        d["scores"]["audio"]["score"] = True
        self.assertTrue(jp.validate_report(d, self.packet())[1])

    def test_too_many_fixes_and_long_evidence(self):
        d = good_report()
        d["top_fixes"] = ["a", "b", "c", "d"]
        d["scores"]["audio"]["evidence"] = " ".join(["word"] * 41) + "."
        text = "\n".join(jp.validate_report(d, self.packet())[1])
        self.assertIn("more than 3", text)
        self.assertIn("longer than 40", text)

    def test_md_block_flags_problems_and_failed_page(self):
        d = good_report()
        d["scores"]["audio"]["score"] = 0
        pk = {"files": [{"name": "a.png"}],
              "page": {"ok": False, "checks": [{"name": "video", "ok": False, "detail": "none"}]}}
        md = jp.render_md(jp.validate_report(d, pk)[0])
        self.assertIn("REPORT PROBLEMS", md)
        self.assertIn("video FAIL", md)


class Cli(Base):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "judge_pass.py"), *args],
                              capture_output=True, text=True)

    def test_parse_exit_codes_and_md(self):
        rep = self.d / "r.md"
        rep.write_text("```json\n" + json.dumps(good_report()) + "\n```")
        r = self.run_cli("parse", str(rep), "--md")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Total 21/35", r.stdout)
        bad = good_report()
        bad["scores"]["audio"]["score"] = 9
        rep.write_text(json.dumps(bad))
        self.assertEqual(self.run_cli("parse", str(rep)).returncode, 2)
        rep.write_text("nothing")
        self.assertEqual(self.run_cli("parse", str(rep)).returncode, 3)
        self.assertEqual(self.run_cli("parse", str(self.d / "none")).returncode, 3)
        self.assertEqual(self.run_cli().returncode, 3)

    def test_packet_cli_then_parse_with_packet(self):
        out = self.d / "o"
        r = self.run_cli("packet", "--session", str(self.session()), "--page", str(self.page()), "--out", str(out))
        self.assertIn(r.returncode, (0, 2), r.stderr)  # 2 when the page's video link cannot be length-checked
        pk = json.loads((out / "packet.json").read_text())
        rep = self.d / "r.json"
        rep.write_text(json.dumps(good_report(pk["files"][0]["name"])))
        self.assertEqual(self.run_cli("parse", str(rep), "--packet", str(out)).returncode, 0)
        rep.write_text(json.dumps(good_report("other.png")))
        self.assertEqual(self.run_cli("parse", str(rep), "--packet", str(out)).returncode, 2)


if __name__ == "__main__":
    unittest.main()
