"""epic_ask tests: temp queue file via MEGAJAM_EPIC_ASK_FILE, no network, no real Obsidian note."""
import importlib.util
import io
import json
import multiprocessing
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "epic_ask.py"
SPEC = importlib.util.spec_from_file_location("epic_ask", SCRIPT)
ea = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ea)


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = ea.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


def _worker(path, n):
    os.environ["MEGAJAM_EPIC_ASK_FILE"] = path
    with mock.patch.object(ea.shutil, "which", return_value=None):
        with redirect_stdout(io.StringIO()):
            ea.main(["add", "question %d" % n, "--from", "w%d" % n])


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sub" / "q.md"
        p = mock.patch.dict(os.environ, {"MEGAJAM_EPIC_ASK_FILE": str(self.path)})
        p.start()
        self.addCleanup(p.stop)
        w = mock.patch.object(ea.shutil, "which", return_value=None)
        w.start()
        self.addCleanup(w.stop)
        self.addCleanup(self.tmp.cleanup)

    def answer(self, qid, text):
        t = self.path.read_text()
        head = "## %s\n" % qid
        i = t.index(head)
        j = t.index("### Answer", i)
        k = t.index("-->", j) + 3
        self.path.write_text(t[:k] + "\n" + text + "\n" + t[k:])


class Tests(Base):
    def test_env_override_and_header_created(self):
        rc, out, _ = run("add", "How do I X?", "--from", "lead")
        self.assertEqual((rc, out.strip()), (0, "Q-001"))
        text = self.path.read_text()
        self.assertTrue(text.startswith("# Epic Assistant questions"))
        self.assertIn("never drive the site", text)

    def test_default_file_untouched_by_tests(self):
        self.assertNotEqual(ea.ask_file(), ea.DEFAULT_FILE)

    def test_add_list_count_show(self):
        run("add", "first?", "--context", "grepped Engine/Source", "--from", "a")
        run("add", "second?", "--from", "b")
        self.assertEqual(run("count", "--open")[1].strip(), "2")
        rc, out, _ = run("list", "--json")
        data = json.loads(out)
        self.assertEqual([d["id"] for d in data], ["Q-001", "Q-002"])
        self.assertEqual(data[0]["who"], "a")
        self.assertEqual(data[0]["context"], "grepped Engine/Source")
        self.assertRegex(data[0]["time"], r"^\d{4}-\d\d-\d\d \d\d:\d\d$")
        rc, out, _ = run("show", "Q-001")
        self.assertIn("first?", out)
        self.assertIn("No answer yet", out)
        self.assertEqual(run("show", "q-1")[0], 0)
        self.assertEqual(run("show", "Q-099")[0], 2)

    def test_answered_after_hand_edit(self):
        run("add", "first?", "--from", "a")
        run("add", "second?", "--from", "b")
        before = self.path.read_text()
        self.answer("Q-001", "Use UE::Foo::Bar.")
        self.assertEqual(run("count", "--open")[1].strip(), "1")
        self.assertEqual(json.loads(run("list", "--answered", "--json")[1])[0]["id"], "Q-001")
        self.assertEqual(json.loads(run("list", "--open", "--json")[1])[0]["id"], "Q-002")
        out = run("show", "Q-001")[1]
        self.assertIn("Use UE::Foo::Bar.", out)
        self.assertIn("UNVERIFIED", out)
        self.assertNotEqual(before, self.path.read_text())

    def test_comment_only_answer_is_open(self):
        run("add", "first?")
        self.answer("Q-001", "<!-- still thinking -->\n   \n")
        self.assertEqual(run("count", "--open")[1].strip(), "1")

    def test_tolerates_hand_edited_note(self):
        run("add", "first?", "--from", "a")
        t = self.path.read_text().replace("**Context:**", "**context:**").replace("- **Asked by:**", "garbage line\n- **Asked by:**")
        self.path.write_text("Owner scribble\n\n" + t + "\n")
        rc, out, _ = run("add", "second?")
        self.assertEqual(out.strip(), "Q-002")
        self.assertEqual(run("count", "--open")[1].strip(), "2")
        self.assertTrue(self.path.read_text().startswith("Owner scribble"))

    def test_append_only(self):
        run("add", "first?")
        before = self.path.read_text()
        run("add", "second?")
        self.assertTrue(self.path.read_text().startswith(before))

    def test_missing_trailing_newline(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("# my note")
        self.assertEqual(run("add", "q?")[1].strip(), "Q-001")
        self.assertIn("# my note\n", self.path.read_text())

    def test_secret_refusal(self):
        for bad in ["use sk-abcdefghijklmnopqrstuvwx", "ghp_" + "a" * 30, "AKIA" + "A" * 16,
                    "OPENAI_API_KEY=abc123def456", "Authorization: Bearer abcdefghijklmnop1234",
                    "api_key = 'Zm9vYmFyYmF6cXV4'", "-----BEGIN RSA PRIVATE KEY-----"]:
            rc, _, err = run("add", "why? " + bad)
            self.assertEqual(rc, 2, bad)
            self.assertIn("secret", err)
        self.assertEqual(run("add", "q", "--context", "XAI_API_KEY=abcdefgh")[0], 2)
        self.assertFalse(self.path.exists())

    def test_url_credentials_refused(self):
        self.assertEqual(run("add", "why? https://user:p4ssw0rd1234@host/x")[0], 2)
        self.assertEqual(run("add", "see https://example.com:8080/path and a@b.c")[0], 0)

    def test_id_not_reused_after_manual_delete(self):
        run("add", "one?")
        run("add", "two?")
        t = self.path.read_text()
        self.path.write_text(t[:t.index("\n## Q-002")] + "\n")
        self.assertEqual(run("add", "three?")[1].strip(), "Q-003")

    def test_fence_blind_answer_and_context(self):
        run("add", "t\n### Answer\n**Context:** x\nmore", "--context", "real")
        e = ea.read_entries(self.path)[0]
        self.assertEqual(e["answer"], "")
        self.assertEqual(e["question"], "t\n### Answer\n**Context:** x\nmore")
        self.assertEqual(e["context"], "real")
        self.assertEqual(run("count", "--open")[1].strip(), "1")

    def test_outside_fences_closer_length(self):
        blk = ["````", "```", "### Answer", "````", "### Answer"]
        self.assertEqual([i for i, _ in ea.outside_fences(blk)], [4])

    def test_normal_text_not_flagged(self):
        self.assertEqual(run("add", "Does UWorld::SpawnActor tick the token bucket? See Engine/Source/Runtime/Engine.")[0], 0)

    def test_length_cap_and_empty(self):
        self.assertEqual(run("add", "   ")[0], 2)
        self.assertEqual(run("add", "x" * (ea.MAX_QUESTION + 1))[0], 2)
        self.assertEqual(run("add", "x" * ea.MAX_QUESTION)[0], 0)
        self.assertEqual(run("add", "q", "--context", "c" * (ea.MAX_CONTEXT + 1))[0], 2)

    def test_question_with_fences_and_fake_heading_roundtrips(self):
        q = "What does this do?\n```cpp\nint x;\n```\n## Q-009\nmore"
        run("add", q)
        self.assertEqual(run("add", "next")[1].strip(), "Q-002")
        e = ea.read_entries(self.path)[0]
        self.assertIn("int x;", e["question"])
        self.assertEqual(len(ea.read_entries(self.path)), 2)

    def test_lock_concurrent_adds(self):
        procs = [multiprocessing.Process(target=_worker, args=(str(self.path), n)) for n in range(12)]
        for p in procs:
            p.start()
        for p in procs:
            p.join(30)
        ids = [e["id"] for e in ea.read_entries(self.path)]
        self.assertEqual(sorted(ids), ["Q-%03d" % n for n in range(1, 13)])

    def test_notify_optional_and_next(self):
        run("add", "first?", "--from", "a")
        with mock.patch.object(ea.shutil, "which", return_value="/bin/true"), \
                mock.patch.object(ea.subprocess, "run") as r, mock.patch.object(ea.subprocess, "Popen") as po:
            run("add", "second?")
            self.assertEqual(r.call_args[0][0][0], "/bin/true")
            rc, out, _ = run("next")
            self.assertIn("first?", out)
            self.assertEqual(po.call_args[0][0], ["/bin/true", ea.ASSISTANT_URL])
        self.answer("Q-001", "done")
        self.assertIn("second?", run("next", "--no-open")[1])
        self.answer("Q-002", "done")
        self.assertIn("No open questions", run("next")[1])

    def test_empty_queue(self):
        self.assertEqual(run("count", "--open")[1].strip(), "0")
        self.assertEqual(run("list")[1], "")


if __name__ == "__main__":
    unittest.main()
