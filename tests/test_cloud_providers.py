"""fal, Hyper3D Rodin and Tripo adapters: mocked HTTP only. No live calls, no real keys."""
import csv
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import providers as P  # noqa: E402
from providers import cloud as C  # noqa: E402
from providers import fal as F  # noqa: E402
from providers import hyper3d as H  # noqa: E402
from providers import tripo as T  # noqa: E402

SPEC = importlib.util.spec_from_file_location("gen_asset_cloud", os.path.join(ROOT, "scripts", "gen_asset.py"))
gen_asset = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_asset)

GLB = b"glTF" + b"\x02\x00\x00\x00" + b"x" * 20
PNG = P.PNG_MAGIC + b"pixels"
KEYS = {"FAL_KEY": "fal_SECRET_1", "RODIN_API_KEY": "rdn_SECRET_2", "TRIPO_API_KEY": "tsk_SECRET_3"}
ENV = {**KEYS, "FAL_TERMS_REVIEWED": "2026-11-10", "HYPER3D_TERMS_REVIEWED": "2026-11-10",
       "TRIPO_TERMS_REVIEWED": "2026-11-07"}


class Resp:
    def __init__(self, data):
        self.data = data if isinstance(data, bytes) else json.dumps(data).encode()

    def read(self, n=-1):
        n = len(self.data) if n is None or n < 0 else n
        chunk, self.data = self.data[:n], self.data[n:]
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Router:
    """Stands in for urlopen. routes: list of (url prefix, method or None, reply or callable(req)->reply)."""
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, req, timeout=None):
        url = req if isinstance(req, str) else req.full_url
        method = "GET" if isinstance(req, str) else req.get_method()
        headers = {} if isinstance(req, str) else {k.lower(): v for k, v in req.header_items()}
        self.calls.append((method, url, headers, getattr(req, "data", None)))
        for prefix, want, reply in self.routes:
            if url.startswith(prefix) and want in (None, method):
                value = reply(req) if callable(reply) else reply
                if isinstance(value, list):  # scripted sequence: pop until one left
                    value = value.pop(0) if len(value) > 1 else value[0]
                return Resp(value)
        raise AssertionError(f"unexpected request {method} {url}")


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s or 1


def make(cls, router, env=ENV, root=None, clock=None):
    clock = clock or Clock()
    return cls(environ=env, opener=router, connect=lambda *a, **k: mock.Mock(), clock=clock, sleep=clock.sleep,
               poll_seconds=5, allowed_roots=[root or tempfile.gettempdir()])


def tripo_routes(status=("running", "success"), glb=GLB, code=0):
    return [
        ("https://openapi.tripo3d.ai/v3/files", "POST", {"code": code, "data": {"file_token": "file_abc"}}),
        ("https://openapi.tripo3d.ai/v3/generation/", "POST", {"code": 0, "data": {"task_id": "t-1"}}),
        ("https://openapi.tripo3d.ai/v3/tasks/t-1", "GET",
         [{"code": 0, "data": {"status": s, "output": {"model_url": "https://tripo-data.example/m.glb?sig=1"}}}
          for s in status]),
        ("https://tripo-data.example/", "GET", glb),
    ]


def rodin_routes(status=("Generating", "Done"), files=None):
    files = files if files is not None else [{"name": "preview.webp", "url": "https://file.hyper3d.example/p.webp"},
                                             {"name": "base_basic_pbr.glb", "url": "https://file.hyper3d.example/m.glb"}]
    return [
        ("https://api.hyper3d.com/api/v2/rodin", "POST",
         {"uuid": "r-1", "jobs": {"uuids": ["j1"], "subscription_key": "sub-1"}, "consumed": 0.5}),
        ("https://api.hyper3d.com/api/v2/status", "POST", [{"jobs": [{"uuid": "j1", "status": s}]} for s in status]),
        ("https://api.hyper3d.com/api/v2/download", "POST", {"list": files}),
        ("https://file.hyper3d.example/", "GET", GLB),
    ]


def fal_routes(model, result, status=("IN_QUEUE", "IN_PROGRESS", "COMPLETED"), status_host="https://queue.fal.run"):
    app = "/".join(model.split("/")[:2])
    return [
        (f"https://queue.fal.run/{model}", "POST",
         {"request_id": "q-1", "status_url": f"{status_host}/{app}/requests/q-1/status",
          "response_url": f"https://queue.fal.run/{app}/requests/q-1"}),
        (f"https://queue.fal.run/{app}/requests/q-1/status", "GET", [{"status": s} for s in status]),
        (f"https://queue.fal.run/{app}/requests/q-1", "GET", result),
        ("https://v3.fal.media/", "GET", lambda req: GLB if str(req).endswith(".glb") else PNG),
    ]


class Base(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        self.d = Path(d)
        self.img = self.d / "concept.png"
        self.img.write_bytes(PNG)
        self.out = self.d / "a.glb"

    def assert_key_only_to(self, router, host, key, scheme):
        for method, url, headers, _ in router.calls:
            if url.startswith(f"https://{host}/"):
                self.assertEqual(headers.get("authorization"), f"{scheme} {key}", url)
            else:
                self.assertNotIn("authorization", headers, url)


class Gate(Base):
    CASES = [(T.TripoProvider, "TRIPO_API_KEY", "TRIPO_TERMS_REVIEWED"),
             (H.Hyper3DProvider, "RODIN_API_KEY", "HYPER3D_TERMS_REVIEWED"),
             (F.FalProvider, "FAL_KEY", "FAL_TERMS_REVIEWED"),
             (F.Fal3DProvider, "FAL_KEY", "HYPER3D_TERMS_REVIEWED")]

    def test_not_configured_without_key_or_terms(self):
        for cls, key_env, terms_env in self.CASES:
            router = Router([])
            env = dict(ENV)
            del env[key_env]
            self.assertEqual(make(cls, router, env).check()[0], P.NOT_CONFIGURED, cls)
            env = dict(ENV)
            del env[terms_env]
            status, detail = make(cls, router, env).check()
            self.assertEqual(status, P.NOT_CONFIGURED, cls)
            self.assertIn(terms_env, detail)
            with self.assertRaises(P.ProviderError):
                gen = make(cls, router, env)
                (gen.generate("x", self.out, 10) if cls is F.FalProvider else gen.generate_3d(self.img, self.out, 10))
            self.assertEqual(router.calls, [])

    def test_check_is_tcp_only_and_reports_down(self):
        for cls, *_ in self.CASES:
            hosts = []
            ok = cls(environ=ENV, connect=lambda addr, timeout: hosts.append(addr) or mock.Mock())
            self.assertEqual(ok.check()[0], P.READY)
            self.assertEqual(hosts, [(cls.API_HOST, 443)])

            def boom(*a, **k):
                raise OSError("no route")
            self.assertEqual(cls(environ=ENV, connect=boom).check()[0], P.DOWN)

    def test_empty_env_reports_not_configured(self):
        for cls, *_ in self.CASES:
            self.assertEqual(cls(environ={}).check()[0], P.NOT_CONFIGURED)


class Tripo(Base):
    def test_image_to_model_success(self):
        router = Router(tripo_routes())
        info = make(T.TripoProvider, router).generate_3d(self.img, self.out, 100)
        self.assertEqual(self.out.read_bytes(), GLB)
        self.assertEqual((info["task_id"], info["model"]), ("t-1", T.TRIPO_MODEL))
        self.assertEqual(info["licence_gate"], "TRIPO_TERMS_REVIEWED=2026-11-07")
        upload = router.calls[0]
        self.assertIn(b'name="file"', upload[3])
        self.assertTrue(upload[2]["content-type"].startswith("multipart/form-data; boundary="))
        body = json.loads(router.calls[1][3])
        self.assertEqual(router.calls[1][1], "https://openapi.tripo3d.ai/v3/generation/image-to-model")
        self.assertEqual((body["input"], body["model"], body["pbr"]), ("file_abc", T.TRIPO_MODEL, True))
        self.assert_key_only_to(router, T.API_HOST, KEYS["TRIPO_API_KEY"], "Bearer")

    def test_text_to_model(self):
        router = Router(tripo_routes())
        make(T.TripoProvider, router).generate_3d_from_text("a wooden crate", self.out, 100)
        self.assertEqual(router.calls[0][1], "https://openapi.tripo3d.ai/v3/generation/text-to-model")
        self.assertEqual(json.loads(router.calls[0][3])["prompt"], "a wooden crate")
        self.assertEqual(self.out.read_bytes(), GLB)

    def test_failed_task_hides_key(self):
        router = Router(tripo_routes(status=("banned",)))
        with self.assertRaises(P.ProviderError) as cm:
            make(T.TripoProvider, router).generate_3d(self.img, self.out, 100)
        self.assertIn("banned", str(cm.exception))
        self.assertEqual(cm.exception.task_id, "t-1")
        self.assertNotIn(KEYS["TRIPO_API_KEY"], str(cm.exception))
        self.assertFalse(self.out.exists())

    def test_nonzero_code_is_failure(self):
        with self.assertRaisesRegex(P.ProviderError, "upload refused"):
            make(T.TripoProvider, Router(tripo_routes(code=2010))).generate_3d(self.img, self.out, 100)

    def test_bad_glb_and_timeout(self):
        with self.assertRaisesRegex(P.ProviderError, "not a GLB"):
            make(T.TripoProvider, Router(tripo_routes(glb=b"<html>"))).generate_3d(self.img, self.out, 100)
        with self.assertRaisesRegex(P.ProviderError, "TimeoutError"):
            make(T.TripoProvider, Router(tripo_routes(status=("running",)))).generate_3d(self.img, self.out, 30)


class Hyper3D(Base):
    def test_image_to_3d_success(self):
        router = Router(rodin_routes())
        info = make(H.Hyper3DProvider, router).generate_3d(self.img, self.out, 100)
        self.assertEqual(self.out.read_bytes(), GLB)
        self.assertEqual(info["task_id"], "r-1")
        form = router.calls[0][3]
        for part in (b'name="images"; filename="concept.png"', b"Gen-2.5-Medium", b'name="geometry_file_format"'):
            self.assertIn(part, form)
        self.assertEqual(json.loads(router.calls[1][3]), {"subscription_key": "sub-1"})
        self.assertEqual(json.loads(router.calls[-2][3]), {"task_uuid": "r-1"})
        self.assertEqual(router.calls[-1][1], "https://file.hyper3d.example/m.glb")  # the .glb, not the preview
        self.assert_key_only_to(router, H.API_HOST, KEYS["RODIN_API_KEY"], "Bearer")

    def test_text_to_3d_sends_prompt_and_no_image(self):
        router = Router(rodin_routes())
        make(H.Hyper3DProvider, router).generate_3d_from_text("a stone lantern", self.out, 100)
        self.assertIn(b"a stone lantern", router.calls[0][3])
        self.assertNotIn(b'name="images"', router.calls[0][3])

    def test_failed_and_no_glb(self):
        with self.assertRaisesRegex(P.ProviderError, "Failed"):
            make(H.Hyper3DProvider, Router(rodin_routes(status=("Failed",)))).generate_3d(self.img, self.out, 100)
        with self.assertRaisesRegex(P.ProviderError, "no .glb"):
            make(H.Hyper3DProvider, Router(rodin_routes(files=[]))).generate_3d(self.img, self.out, 100)

    def test_image_checks_before_upload(self):
        router = Router(rodin_routes())
        bad = self.d / "notes.png"
        bad.write_bytes(b"secret text")
        with self.assertRaises(P.ProviderError):
            make(H.Hyper3DProvider, router).generate_3d(bad, self.out, 100)
        uc2 = self.d / "UC2" / "x.png"
        uc2.parent.mkdir()
        uc2.write_bytes(PNG)
        with self.assertRaises(P.ProviderError):
            make(H.Hyper3DProvider, router).generate_3d(uc2, self.out, 100)
        with self.assertRaises(P.ProviderError):
            make(H.Hyper3DProvider, router, root="/nonexistent-root").generate_3d(self.img, self.out, 100)
        self.assertEqual(router.calls, [])


class Fal(Base):
    def test_concept_image(self):
        router = Router(fal_routes(F.IMAGE_MODEL, {"images": [{"url": "https://v3.fal.media/files/x.png"}]}))
        out = self.d / "c.png"
        info = make(F.FalProvider, router).generate("a crate", out, 60)
        self.assertEqual(out.read_bytes(), PNG)
        self.assertEqual(info["model"], "fal-ai/flux/schnell")
        body = json.loads(router.calls[0][3])
        self.assertEqual((body["prompt"], body["output_format"]), ("a crate", "png"))
        self.assertEqual(router.calls[1][1], "https://queue.fal.run/fal-ai/flux/requests/q-1/status")
        self.assert_key_only_to(router, F.API_HOST, KEYS["FAL_KEY"], "Key")

    def test_rodin_on_fal_3d(self):
        router = Router(fal_routes(F.THREED_MODEL, {"model_mesh": {"url": "https://v3.fal.media/files/m.glb"}}))
        info = make(F.Fal3DProvider, router).generate_3d(self.img, self.out, 100)
        self.assertEqual(self.out.read_bytes(), GLB)
        self.assertEqual(info["licence_gate"], "FAL_TERMS_REVIEWED=2026-11-10,HYPER3D_TERMS_REVIEWED=2026-11-10")
        body = json.loads(router.calls[0][3])
        self.assertTrue(body["image_urls"][0].startswith("data:image/png;base64,"))
        self.assertEqual(body["geometry_file_format"], "glb")
        self.assert_key_only_to(router, F.API_HOST, KEYS["FAL_KEY"], "Key")

    def test_status_url_off_host_is_refused(self):
        router = Router(fal_routes(F.IMAGE_MODEL, {}, status_host="https://evil.example"))
        with self.assertRaisesRegex(P.ProviderError, "refusing to send the key"):
            make(F.FalProvider, router).generate("x", self.d / "c.png", 60)
        self.assertEqual([c[1] for c in router.calls], ["https://queue.fal.run/fal-ai/flux/schnell"])

    def test_completed_with_error_fails(self):
        router = Router(fal_routes(F.IMAGE_MODEL, {}))
        router.routes[1] = (router.routes[1][0], "GET", {"status": "COMPLETED", "error": "nsfw", "error_type": "x"})
        with self.assertRaisesRegex(P.ProviderError, "nsfw"):
            make(F.FalProvider, router).generate("x", self.d / "c.png", 60)


class Wiring(Base):
    def setUp(self):
        super().setUp()
        self.log = self.d / "log.csv"
        gen_asset.ensure_csv_header(self.log)
        p = mock.patch.object(gen_asset, "run_stage", lambda *a, **k: (0.1, {}))
        p.start()
        self.addCleanup(p.stop)

    def args(self, choice):
        return SimpleNamespace(name="a", prompt=None, model="krea-2-turbo", profile=None, qa_kind="prop",
                               threed_provider=choice)

    def rows(self):
        return [r[2] for r in csv.reader(io.StringIO(self.log.read_text()))][1:]

    def stage(self, choice, env, router, local_ok=True):
        clock = Clock()

        def factory(cls):
            return lambda **k: cls(environ=k["environ"], opener=router, connect=lambda *a, **kw: mock.Mock(),
                                   clock=clock, sleep=clock.sleep, allowed_roots=[self.d])
        with mock.patch.object(gen_asset, "run_local_3d", lambda *a, **k: (local_ok, 1.0, ["nexus-3d"])), \
                mock.patch.object(gen_asset.tripo_provider, "TripoProvider", factory(T.TripoProvider)), \
                mock.patch.object(gen_asset.hyper3d_provider, "Hyper3DProvider", factory(H.Hyper3DProvider)), \
                mock.patch.object(gen_asset.fal_provider, "Fal3DProvider", factory(F.Fal3DProvider)):
            return gen_asset.three_d_stage(self.args(choice), self.img, self.out, self.log, {}, env, {}, [])

    def test_auto_skips_unconfigured_and_uses_tripo(self):
        env = {"TRIPO_API_KEY": "k", "TRIPO_TERMS_REVIEWED": "2026-11-07"}  # no Meshy, Rodin or fal
        threed = self.stage("auto", env, Router(tripo_routes()))
        self.assertEqual(threed["provider"], "tripo")
        self.assertEqual(self.rows(), ["3d:tripo"])
        self.assertEqual((self.d / "a.tripo_raw.glb").read_bytes(), GLB)

    def test_auto_falls_through_failed_cloud_to_next_then_local(self):
        env = {k: v for k, v in ENV.items() if not k.startswith("FAL")}
        router = Router(tripo_routes(status=("failed",)) + rodin_routes(status=("Failed",)))
        self.assertIsNone(self.stage("auto", env, router))
        self.assertEqual(self.rows(), ["3d:tripo", "3d:hyper3d"])
        self.assertFalse(any(self.d.glob("*_raw.glb")))

    def test_auto_with_nothing_configured_is_local_only(self):
        router = Router([])
        self.assertIsNone(self.stage("auto", {}, router))
        self.assertEqual((router.calls, self.rows()), ([], []))

    def test_forced_cloud_not_configured_exits_and_logs(self):
        for name in ("tripo", "hyper3d", "fal"):
            gen_asset.ensure_csv_header(self.log)
            with self.assertRaises(SystemExit):
                self.stage(name, {}, Router([]))
            self.assertEqual(self.rows()[-1], f"3d:{name}")

    def test_forced_cloud_failure_does_not_fall_back(self):
        with mock.patch.object(gen_asset, "run_local_3d", side_effect=AssertionError("local ran")):
            with self.assertRaises(SystemExit):
                self.stage("hyper3d", ENV, Router(rodin_routes(status=("Failed",))))


class ProvidersCheckCli(unittest.TestCase):
    def test_new_lines_show_not_configured_without_keys(self):
        with tempfile.TemporaryDirectory() as home:
            env = {k: v for k, v in os.environ.items()
                   if not any(k.startswith(p) for p in ("FAL", "RODIN", "HYPER3D", "TRIPO", "MESHY", "XAI"))}
            env["HOME"] = home  # no ~/.config/megajam.env
            out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "gen_asset.py"), "--providers-check"],
                                 capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        lines = out.stdout.splitlines()
        for want in ("fal: not configured - FAL_KEY not set",
                     "tripo (3d): not configured - TRIPO_API_KEY not set",
                     "hyper3d (3d): not configured - RODIN_API_KEY not set",
                     "fal (3d): not configured - FAL_KEY not set"):
            self.assertIn(want, [l.split(" | licence:")[0] for l in lines])


if __name__ == "__main__":
    unittest.main()
