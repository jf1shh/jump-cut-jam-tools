import csv
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import providers as P  # noqa: E402
from providers import meshy as M  # noqa: E402

SPEC = importlib.util.spec_from_file_location("gen_asset", os.path.join(ROOT, "scripts", "gen_asset.py"))
gen_asset = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_asset)

M.DEFAULT_ROOTS = (Path(tempfile.gettempdir()),)  # tests write images under the system temp dir
KEY = "msy_SECRET_KEY_123"
ENV = {"MESHY_API_KEY": KEY, "MESHY_TERMS_REVIEWED": "2026-11-07"}
GLB = b"glTF" + b"\x02\x00\x00\x00" + b"x" * 20


class Resp:
    def __init__(self, data):
        self.data = data if isinstance(data, bytes) else json.dumps(data).encode()

    def read(self, n=-1):
        if n is None or n < 0:
            n = len(self.data)
        chunk, self.data = self.data[:n], self.data[n:]
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeMeshy:
    """Stands in for urlopen: records requests, plays back a script of task statuses."""
    def __init__(self, statuses=("PENDING", "SUCCEEDED"), glb=GLB, error=None):
        self.statuses = list(statuses)
        self.glb = glb
        self.error = error
        self.calls = []

    def __call__(self, req, timeout=None):
        url = req if isinstance(req, str) else req.full_url
        headers = {} if isinstance(req, str) else dict(req.header_items())
        self.calls.append((url, headers, getattr(req, "data", None)))
        if url.startswith("https://assets.meshy.ai/"):
            return Resp(self.glb)
        if req.get_method() == "POST":
            return Resp({"result": "task-1"})
        status = self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
        task = {"status": status, "task_error": {"message": self.error} if self.error else None}
        if status == "SUCCEEDED":
            task["model_urls"] = {"glb": "https://assets.meshy.ai/x/model.glb?sig=1"}
        return Resp(task)


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def provider(fake, env=ENV, clock=None):
    clock = clock or Clock()
    return M.MeshyProvider(environ=env, opener=fake, clock=clock, sleep=clock.sleep, poll_seconds=5)


class MeshyAdapter(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        self.img = Path(d) / "concept.png"
        self.img.write_bytes(P.PNG_MAGIC + b"data")
        self.out = Path(d) / "a.glb"

    def test_success(self):
        fake = FakeMeshy()
        info = provider(fake).generate_3d(self.img, self.out, 100)
        self.assertEqual(self.out.read_bytes(), GLB)
        self.assertEqual(info["task_id"], "task-1")
        self.assertEqual(info["licence_gate"], "MESHY_TERMS_REVIEWED=2026-11-07")
        body = json.loads(fake.calls[0][2])
        self.assertTrue(body["image_url"].startswith("data:image/png;base64,"))
        self.assertEqual(body["target_formats"], ["glb"])
        # the key goes to api.meshy.ai only, never to the asset host
        for url, headers, _ in fake.calls:
            if url.startswith("https://api.meshy.ai/openapi/v1/image-to-3d"):
                self.assertEqual(headers["Authorization"], f"Bearer {KEY}")
            else:
                self.assertNotIn("Authorization", headers)

    def test_image_checks_before_upload(self):
        fake = FakeMeshy()
        bad = self.out.parent / "notes.png"
        bad.write_bytes(b"secret text, not an image")
        with self.assertRaises(P.ProviderError):
            provider(fake).generate_3d(bad, self.out, 100)
        uc2 = self.out.parent / "UC2" / "x.png"
        uc2.parent.mkdir()
        uc2.write_bytes(P.PNG_MAGIC)
        with self.assertRaises(P.ProviderError):
            provider(fake).generate_3d(uc2, self.out, 100)
        outside = M.MeshyProvider(environ=ENV, opener=fake, allowed_roots=["/nonexistent-root"])
        with self.assertRaises(P.ProviderError):
            outside.generate_3d(self.img, self.out, 100)
        self.assertEqual(fake.calls, [])

    def test_redirect_refused_so_key_cannot_leak(self):
        import urllib.error
        req = urllib.request.Request("https://api.meshy.ai/x", headers={"Authorization": f"Bearer {KEY}"})
        with self.assertRaises(urllib.error.HTTPError):
            M._NoRedirect().redirect_request(req, None, 302, "Found", {}, "https://evil.example/x")

    def test_slow_trickle_download_hits_deadline(self):
        clock = Clock()

        class Slow(Resp):
            def read(self, n=-1):
                clock.t += 400  # each chunk "takes" 400 s
                return b"glTF" + b"x" * 10

        class SlowMeshy(FakeMeshy):
            def __call__(self, req, timeout=None):
                if (req if isinstance(req, str) else req.full_url).startswith("https://assets.meshy.ai/"):
                    return Slow(b"")
                return super().__call__(req, timeout)
        with self.assertRaises(P.ProviderError) as cm:
            provider(SlowMeshy(), clock=clock).generate_3d(self.img, self.out, 900)
        self.assertIn("budget", str(cm.exception))
        self.assertFalse(self.out.exists())

    def test_task_failed_hides_key(self):
        fake = FakeMeshy(statuses=("FAILED",), error=f"bad image {KEY}")
        with self.assertRaises(P.ProviderError) as cm:
            provider(fake).generate_3d(self.img, self.out, 100)
        self.assertIn("FAILED", str(cm.exception))
        self.assertNotIn(KEY, str(cm.exception))
        self.assertEqual(cm.exception.task_id, "task-1")
        self.assertFalse(self.out.exists())

    def test_timeout(self):
        fake = FakeMeshy(statuses=("IN_PROGRESS",))
        with self.assertRaises(P.ProviderError) as cm:
            provider(fake).generate_3d(self.img, self.out, 20)
        self.assertIn("budget", str(cm.exception))

    def test_bad_glb(self):
        fake = FakeMeshy(glb=b"<html>error</html>")
        with self.assertRaises(P.ProviderError) as cm:
            provider(fake).generate_3d(self.img, self.out, 100)
        self.assertIn("not a GLB", str(cm.exception))
        self.assertFalse(self.out.exists())

    def test_missing_key_and_terms(self):
        fake = FakeMeshy()
        no_key = provider(fake, {"MESHY_TERMS_REVIEWED": "2026-11-07"})
        self.assertEqual(no_key.check()[0], M.NOT_CONFIGURED)
        with self.assertRaises(P.ProviderError):
            no_key.generate_3d(self.img, self.out, 10)
        no_terms = provider(fake, {"MESHY_API_KEY": KEY})
        status, detail = no_terms.check()
        self.assertEqual(status, M.NOT_CONFIGURED)
        self.assertIn("MESHY_TERMS_REVIEWED", detail)
        self.assertNotIn(KEY, detail)
        with self.assertRaises(P.ProviderError):
            no_terms.generate_3d(self.img, self.out, 10)
        self.assertEqual(fake.calls, [])  # no network when not configured

    def test_ready_and_down(self):
        ok = M.MeshyProvider(environ=ENV, connect=lambda *a, **k: mock.Mock())
        self.assertEqual(ok.check()[0], M.READY)

        def boom(*a, **k):
            raise OSError("no route")
        self.assertEqual(M.MeshyProvider(environ=ENV, connect=boom).check()[0], M.DOWN)


class ThreeDStage(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        self.d = Path(d)
        self.img = self.d / "c.png"
        self.img.write_bytes(P.PNG_MAGIC)
        self.glb = self.d / "a.glb"
        self.log = self.d / "log.csv"
        gen_asset.ensure_csv_header(self.log)
        self.handoffs = []

        def fake_stage(cmd, stage, *a, **k):
            self.handoffs.append(cmd)
            return 0.1, {}
        p = mock.patch.object(gen_asset, "run_stage", fake_stage)
        p.start()
        self.addCleanup(p.stop)

    def args(self, choice):
        return SimpleNamespace(name="a", prompt=None, model="krea-2-turbo", profile="ue2_prop", qa_kind="prop",
                               threed_provider=choice)

    def test_meshy_output_goes_through_handoff(self):
        self.stage("meshy", True)
        cmd = self.handoffs[0]
        self.assertEqual(cmd[:2], ["nexus-3d", "handoff"])
        self.assertEqual(cmd[cmd.index("--profile") + 1], "ue2_prop")
        self.assertIn(str(self.d / "a.meshy_raw.glb"), cmd)
        self.assertEqual(cmd[cmd.index("--out") + 1], str(self.glb))

    def test_local_choice_never_contacts_meshy(self):
        fake = FakeMeshy()
        meshy = mock.Mock(wraps=M.MeshyProvider(environ=ENV, opener=fake))
        meshy.check.side_effect = AssertionError("meshy contacted")
        with mock.patch.object(gen_asset, "run_local_3d", lambda *a, **k: (True, 1.0, [])), \
                mock.patch.object(gen_asset.meshy_provider, "MeshyProvider", lambda **k: meshy):
            gen_asset.three_d_stage(self.args("local"), self.img, self.glb, self.log, {}, ENV, {}, [])

    def stage(self, choice, local_ok, fake=None, env=ENV):
        def fake_local(*a, **k):
            return local_ok, 1.0, ["nexus-3d"]
        meshy = M.MeshyProvider(environ=env, opener=fake or FakeMeshy(), connect=lambda *a, **k: mock.Mock(),
                                clock=Clock(), sleep=lambda s: None)
        with mock.patch.object(gen_asset, "run_local_3d", fake_local), \
                mock.patch.object(gen_asset.meshy_provider, "MeshyProvider", lambda **k: meshy):
            return gen_asset.three_d_stage(self.args(choice), self.img, self.glb, self.log, {}, env, {}, [])

    def rows(self):
        return [r[2] for r in csv.reader(io.StringIO(self.log.read_text()))][1:]

    def test_auto_prefers_meshy_when_configured(self):
        with mock.patch.object(gen_asset, "run_local_3d", side_effect=AssertionError("local ran")):
            meshy = M.MeshyProvider(environ=ENV, opener=FakeMeshy(), connect=lambda *a, **k: mock.Mock(),
                                    clock=Clock(), sleep=lambda s: None)
            with mock.patch.object(gen_asset.meshy_provider, "MeshyProvider", lambda **k: meshy):
                threed = gen_asset.three_d_stage(self.args("auto"), self.img, self.glb, self.log, {}, ENV, {}, [])
        self.assertEqual(threed["provider"], "meshy")
        self.assertEqual(threed["task_id"], "task-1")
        self.assertEqual(self.rows(), ["3d:meshy"])
        self.assertEqual((self.d / "a.meshy_raw.glb").read_bytes(), GLB)

    def test_auto_falls_back_to_local_when_meshy_fails(self):
        self.assertIsNone(self.stage("auto", True, FakeMeshy(statuses=("FAILED",), error="x")))
        self.assertEqual(self.rows(), ["3d:meshy"])

    def test_auto_without_meshy_config_uses_local_only(self):
        fake = FakeMeshy()
        self.assertIsNone(self.stage("auto", True, fake, env={}))
        self.assertEqual(fake.calls, [])

    def test_auto_both_fail_exits(self):
        with mock.patch.object(gen_asset, "run_local_3d", side_effect=SystemExit(1)):
            meshy = M.MeshyProvider(environ=ENV, opener=FakeMeshy(statuses=("FAILED",), error="x"),
                                    connect=lambda *a, **k: mock.Mock(), clock=Clock(), sleep=lambda s: None)
            with mock.patch.object(gen_asset.meshy_provider, "MeshyProvider", lambda **k: meshy):
                with self.assertRaises(SystemExit):
                    gen_asset.three_d_stage(self.args("auto"), self.img, self.glb, self.log, {}, ENV, {}, [])

    def test_forced_meshy_skips_local(self):
        with mock.patch.object(gen_asset, "run_local_3d", side_effect=AssertionError("local ran")):
            meshy = M.MeshyProvider(environ=ENV, opener=FakeMeshy(), connect=lambda *a, **k: mock.Mock(),
                                    clock=Clock(), sleep=lambda s: None)
            with mock.patch.object(gen_asset.meshy_provider, "MeshyProvider", lambda **k: meshy):
                t = gen_asset.three_d_stage(self.args("meshy"), self.img, self.glb, self.log, {}, ENV, {}, [])
        self.assertEqual(t["provider"], "meshy")

    def test_forced_meshy_not_configured_exits_and_logs(self):
        with self.assertRaises(SystemExit):
            self.stage("meshy", True, env={})
        self.assertEqual(self.rows(), ["3d:meshy"])

    def test_forced_meshy_failure_does_not_fall_back(self):
        with self.assertRaises(SystemExit):
            self.stage("meshy", True, FakeMeshy(statuses=("FAILED",), error="x"))

    def test_sidecar_records_meshy(self):
        threed = {"provider": "meshy", "model": "latest", "task_id": "task-1", "licence_gate": "MESHY_TERMS_REVIEWED=2026-11-07"}
        self.glb.write_bytes(GLB)
        sidecar = gen_asset.write_provenance(self.glb, SimpleNamespace(name="a", prompt=None, model="krea-2-turbo"),
                                             self.img, [], gen_asset.threed_env({}), None, threed)
        rec = json.loads(sidecar.read_text())
        self.assertEqual((rec["threed_provider"], rec["threed_provider_model"], rec["threed_provider_task_id"]),
                         ("meshy", "latest", "task-1"))
        self.assertFalse(rec["local_only"])
        self.assertNotIn(KEY, sidecar.read_text())

    def test_upload_roots_do_not_follow_out_dir(self):
        seen = {}

        class Rec(M.MeshyProvider):
            def __init__(self, **k):
                super().__init__(**k)
                seen["roots"] = self.allowed_roots

            def check(self):
                return M.NOT_CONFIGURED, "x"
        root_glb = Path("/") / "a" / "a.glb"  # --out-dir /
        args = SimpleNamespace(name="a", prompt=None, model="krea-2-turbo", profile=None, qa_kind="prop",
                               threed_provider="auto")
        with mock.patch.object(gen_asset.meshy_provider, "MeshyProvider", Rec), \
                mock.patch.object(gen_asset, "run_local_3d", lambda *a, **k: (True, 0.0, [])):
            gen_asset.three_d_stage(args, Path("/x.png"), root_glb, Path("/dev/null"), {}, {}, {}, [])
        self.assertEqual(seen["roots"], [gen_asset.REPO_ROOT.resolve()])

    def test_failed_handoff_removes_raw_meshy_glb(self):
        def fake_stage(cmd, stage, *a, **k):
            return 0.1, None  # handoff fails

        def fake_local(*a, **k):
            self.glb.write_bytes(GLB)
            return True, 1.0, ["nexus-3d"]
        meshy = M.MeshyProvider(environ=ENV, opener=FakeMeshy(), connect=lambda *a, **k: mock.Mock(),
                                clock=Clock(), sleep=lambda s: None, allowed_roots=[self.d])
        with mock.patch.object(gen_asset, "run_stage", fake_stage), mock.patch.object(gen_asset, "run_local_3d", fake_local), \
                mock.patch.object(gen_asset.meshy_provider, "MeshyProvider", lambda **k: meshy):
            threed = gen_asset.three_d_stage(self.args("auto"), self.img, self.glb, self.log, {}, ENV, {}, [])
        self.assertIsNone(threed)
        self.assertFalse((self.d / "a.meshy_raw.glb").exists())


class RealSocketDeadline(unittest.TestCase):
    def test_slow_trickle_cannot_outrun_budget(self):
        import threading
        import time
        import http.server
        import socketserver

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", "100000")
                self.end_headers()
                try:
                    for _ in range(100):
                        self.wfile.write(b"x")
                        self.wfile.flush()
                        time.sleep(0.2)
                except OSError:
                    pass

        class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
            daemon_threads = True
        srv = S(("127.0.0.1", 0), H)
        self.addCleanup(srv.server_close)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.shutdown)
        resp = urllib.request.urlopen(f"http://127.0.0.1:{srv.server_address[1]}/m", timeout=5)
        prov = M.MeshyProvider(environ=ENV)
        t0 = time.monotonic()
        with self.assertRaises(TimeoutError):
            prov._read(resp, time.monotonic() + 1.0, 1 << 20)
        self.assertLess(time.monotonic() - t0, 3)


class BalanceAndPolycount(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        self.img = Path(d) / "concept.png"
        self.img.write_bytes(P.PNG_MAGIC + b"data")
        self.out = Path(d) / "a.glb"

    def test_balance_get_only(self):
        calls = []

        def fake(req, timeout=None):
            calls.append((req.full_url, req.get_method(), dict(req.header_items())))
            return Resp({"balance": 950, "monthly_credits": 950, "permanent_credits": 0, "monthly_resets_at": None, "x": 1})

        got = M.MeshyProvider(environ=ENV, opener=fake).balance()
        self.assertEqual(got, {"balance": 950, "monthly_credits": 950, "permanent_credits": 0, "monthly_resets_at": None})
        self.assertEqual(calls, [("https://api.meshy.ai/openapi/v1/balance", "GET", {"Authorization": f"Bearer {KEY}"})])

    def test_balance_needs_key_and_terms_and_hides_key(self):
        with self.assertRaises(P.ProviderError):
            M.MeshyProvider(environ={"MESHY_API_KEY": KEY}, opener=lambda *a, **k: None).balance()

        def boom(req, timeout=None):
            raise OSError(f"bad {KEY}")

        with self.assertRaises(P.ProviderError) as cm:
            M.MeshyProvider(environ=ENV, opener=boom).balance()
        self.assertNotIn(KEY, str(cm.exception))

    def test_polycount_in_body_and_info(self):
        fake = FakeMeshy()
        info = provider(fake).generate_3d(self.img, self.out, 100, target_polycount=3000)
        body = json.loads(fake.calls[0][2])
        self.assertEqual((body["should_remesh"], body["topology"], body["target_polycount"]), (True, "triangle", 3000))
        self.assertEqual(info["target_polycount"], 3000)

    def test_no_polycount_keeps_default_body(self):
        fake = FakeMeshy()
        info = provider(fake).generate_3d(self.img, self.out, 100)
        body = json.loads(fake.calls[0][2])
        self.assertNotIn("target_polycount", body)
        self.assertNotIn("should_remesh", body)
        self.assertNotIn("target_polycount", info)

    def test_polycount_out_of_range_spends_nothing(self):
        fake = FakeMeshy()
        for bad in (50, 400_000):
            with self.assertRaises(P.ProviderError):
                provider(fake).generate_3d(self.img, self.out, 100, target_polycount=bad)
        self.assertEqual(fake.calls, [])


if __name__ == "__main__":
    unittest.main()
