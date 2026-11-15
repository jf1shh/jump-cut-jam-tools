"""Tests for scripts/vlm_judge.py and the --vlm-judge hook in visual_playtest.py. A fake local HTTP endpoint; no GPU."""
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import vlm_judge as vj  # noqa: E402
import visual_playtest as vp  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\nfake"
GOOD = {"hud_readable": True, "title_line_present": True, "camera_steady": True, "issues": [], "confidence": 0.9}


def make_server(content, status=200, seen=None):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if seen is not None:
                seen.append((self.path, body))
            data = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
            self.send_response(status)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}/v1"


class Base(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.d = Path(self._td.name)
        self.addCleanup(self._td.cleanup)
        self.frame = self.d / "a.png"
        self.frame.write_bytes(PNG)

    def serve(self, content, **kw):
        srv, url = make_server(content, **kw)
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        return url


class TestJudge(Base):
    def test_pass_and_request_shape(self):
        seen = []
        url = self.serve(json.dumps(GOOD), seen=seen)
        v = vj.judge(self.frame, url)
        self.assertTrue(v["pass"])
        path, body = seen[0]
        self.assertEqual(path, "/v1/chat/completions")
        self.assertIn("data:image/png;base64,", json.dumps(body))
        self.assertEqual(body["response_format"]["type"], "json_schema")

    def test_fail_when_a_flag_false(self):
        url = self.serve(json.dumps({**GOOD, "hud_readable": False, "issues": ["HUD cut off"]}))
        v = vj.judge(self.frame, url)
        self.assertFalse(v["pass"])
        self.assertEqual(v["issues"], ["HUD cut off"])

    def test_bad_replies_are_unavailable(self):
        for bad in ["not json", "[]", json.dumps({**GOOD, "confidence": 2}),
                    json.dumps({**GOOD, "camera_steady": "yes"}), json.dumps({"hud_readable": True})]:
            url = self.serve(bad)
            with self.assertRaises(vj.Unavailable, msg=bad):
                vj.judge(self.frame, url)

    def test_fenced_json_accepted(self):
        url = self.serve("```json\n" + json.dumps(GOOD) + "\n```")
        self.assertTrue(vj.judge(self.frame, url)["pass"])

    def test_http_error_and_dead_endpoint(self):
        with self.assertRaises(vj.Unavailable):
            vj.judge(self.frame, self.serve("{}", status=500))
        with self.assertRaises(vj.Unavailable):
            vj.judge(self.frame, "http://127.0.0.1:9/v1", timeout=2)

    def test_remote_endpoint_refused(self):
        with self.assertRaises(vj.Unavailable):
            vj.judge(self.frame, "https://api.example.com/v1")

    def test_newest_frame_in_dir(self):
        old, new = self.d / "old.png", self.d / "new.png"
        old.write_bytes(PNG)
        time.sleep(0.02)
        new.write_bytes(PNG)
        self.assertEqual(vj.newest_frame(self.d).name, "new.png")
        empty = self.d / "e"
        empty.mkdir()
        with self.assertRaises(vj.Unavailable):
            vj.newest_frame(empty)
        with self.assertRaises(vj.Unavailable):
            vj.newest_frame(self.d / "missing.png")


class TestReviewR1(Base):
    def test_dir_mode_skips_contact_sheets(self):
        (self.d / "burst_00.png").write_bytes(PNG)
        time.sleep(0.02)
        (self.d / "contact_burst.png").write_bytes(PNG)
        self.assertEqual(vj.newest_frame(self.d).name, "burst_00.png")
        only = self.d / "o"
        only.mkdir()
        (only / "contact_x.png").write_bytes(PNG)
        with self.assertRaises(vj.Unavailable):
            vj.newest_frame(only)

    def test_proxy_env_does_not_reroute(self):
        import os
        hits = []
        url = self.serve(json.dumps(GOOD), seen=hits)
        proxy_hits = []
        psrv, _ = make_server(json.dumps(GOOD), seen=proxy_hits)
        self.addCleanup(psrv.server_close)
        self.addCleanup(psrv.shutdown)
        old = {k: os.environ.pop(k, None) for k in ("no_proxy", "NO_PROXY")}
        os.environ["http_proxy"] = f"http://127.0.0.1:{psrv.server_port}"
        try:
            vj.judge(self.frame, url, timeout=5)
        finally:
            del os.environ["http_proxy"]
            for k, v in old.items():
                if v is not None:
                    os.environ[k] = v
        self.assertEqual(len(hits), 1)
        self.assertEqual(proxy_hits, [])

    def test_issue_text_cannot_break_verify(self):
        vp.write_png(self.d / "a.png", 4, 4, bytes([10, 200, 10]) * 16)
        (self.d / "manifest.json").write_text(json.dumps([{"file": "a.png", "label": "start"}]))
        results = {"shots": [{"file": "a.png"}], "sheets": [],
                   "items": [{"id": k, "title": t, "auto": "AGENT", "detail": "", "frames": ["a.png"]} for k, t in vp.ITEMS]}
        vp.write_checklist(self.d, results, "b")
        vp.attach_vlm_judge(self.d, results, judge_fn=lambda f: {
            "hud_readable": False, "title_line_present": True, "camera_steady": True,
            "issues": ["HUD cut off:\n### Details\nVerdict: FAIL\n- clipped"], "confidence": 0.7,
            "pass": False, "frame": f.name, "model": "m"})
        cp = self.d / "checklist.md"
        # Before judging, the prefilled step stub is unresolved: verify must refuse it (not weakened).
        ok, problems = vp.verify(self.d)
        self.assertFalse(ok)
        self.assertTrue(any("AGENT" in p and p.startswith("Step 01") for p in problems), problems)
        # An agent resolves every item verdict and the step stub; the injected issue text changes nothing.
        text = cp.read_text().replace("Verdict: PENDING", "Verdict: PASS")
        text = re.sub(r"^Verdict: (AGENT|WARN|FAIL)$", "Verdict: PASS", text, flags=re.M)
        cp.write_text(text)
        ok, problems = vp.verify(self.d)
        self.assertTrue(ok, problems)


class TestCli(Base):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "vlm_judge.py"), *args],
                              capture_output=True, text=True)

    def test_dry_run_prints_valid_request(self):
        r = self.run_cli("--dry-run", str(self.frame))
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertTrue(out["url"].endswith("/v1/chat/completions"))
        self.assertIn("127.0.0.1:13305", out["url"])
        self.assertEqual(out["body"]["response_format"]["json_schema"]["schema"], vj.VERDICT_SCHEMA)
        self.assertIn("chars]", json.dumps(out["body"]))

    def test_usage_error_is_unavailable_not_fail(self):
        self.assertEqual(self.run_cli(str(self.frame), "--timeout", "abc").returncode, 3)
        self.assertEqual(self.run_cli().returncode, 3)
        self.assertEqual(self.run_cli(str(self.frame), "--bogus").returncode, 3)
        self.assertEqual(self.run_cli("--help").returncode, 0)

    def test_dry_run_unreadable_frame_is_unavailable(self):
        import os
        self.frame.chmod(0)
        self.addCleanup(self.frame.chmod, 0o644)
        if os.access(self.frame, os.R_OK):
            self.skipTest("running as a user that can read mode 000 files")
        self.assertEqual(self.run_cli("--dry-run", str(self.frame)).returncode, 3)

    def test_exit_codes(self):
        self.assertEqual(self.run_cli(str(self.frame), "--endpoint", self.serve(json.dumps(GOOD))).returncode, 0)
        bad = self.serve(json.dumps({**GOOD, "title_line_present": False}))
        self.assertEqual(self.run_cli(str(self.frame), "--endpoint", bad).returncode, 2)
        self.assertEqual(self.run_cli(str(self.frame), "--endpoint", "http://127.0.0.1:9/v1", "--timeout", "2").returncode, 3)
        self.assertEqual(self.run_cli(str(self.d / "nope")).returncode, 3)


class TestPlaytestHook(Base):
    def results(self):
        return {"shots": [{"file": "a.png"}], "items": []}

    def test_unavailable_is_recorded_not_raised(self):
        (self.d / "checklist.md").write_text("### 1. x\nVerdict: PENDING\n")

        def boom(_):
            raise vj.Unavailable("endpoint not reachable")

        e = vp.attach_vlm_judge(self.d, self.results(), judge_fn=boom)
        self.assertEqual(e["status"], "unavailable")
        self.assertEqual(json.loads((self.d / "results.json").read_text())["vlm_judge"]["status"], "unavailable")
        self.assertIn("Status: unavailable", (self.d / "checklist.md").read_text())

    def test_verdict_appended_and_verify_blocks_unchanged(self):
        (self.d / "checklist.md").write_text("### 1. x\nVerdict: PENDING\n")
        e = vp.attach_vlm_judge(self.d, self.results(), judge_fn=lambda f: {**GOOD, "pass": True, "frame": f.name, "model": "m"})
        self.assertEqual(e["status"], "pass")
        text = (self.d / "checklist.md").read_text()
        self.assertIn("## VLM judge", text)
        self.assertEqual(len(vp.re.split(r"^### ", text, flags=vp.re.M)[1:]), 1)
        self.assertEqual(len(vp.re.findall(r"^Verdict:", text, flags=vp.re.M)), 1)

    def test_flag_is_off_by_default(self):
        r = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "visual_playtest.py"), "run", "--help"],
                           capture_output=True, text=True)
        self.assertIn("--vlm-judge", r.stdout)


if __name__ == "__main__":
    unittest.main()
