import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import providers as P  # noqa: E402

SPEC = importlib.util.spec_from_file_location("gen_asset", os.path.join(ROOT, "scripts", "gen_asset.py"))
gen_asset = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_asset)


class Fake:
    def __init__(self, name, status=P.READY, error=None, delay=0):
        self.name, self.status, self.error = name, status, error
        self.calls = 0

    def check(self):
        return self.status, f"{self.name} {self.status}"

    def generate(self, prompt, out_path, timeout):
        self.calls += 1
        if self.error:
            raise P.ProviderError(self.error)
        Path(out_path).write_bytes(b"png")
        return {"model": f"{self.name}-model", "command": [self.name]}


def fakes(**kw):
    return {n: kw.get(n, Fake(n)) for n in P.AUTO_ORDER}


class Fallback(unittest.TestCase):
    def run_auto(self, providers, choice="auto"):
        with tempfile.TemporaryDirectory() as tmp:
            return P.generate_concept(choice, "a cube", Path(tmp) / "c.png", providers, log=lambda m: None)

    def test_first_ready_provider_wins(self):
        p = fakes()
        r = self.run_auto(p)
        self.assertEqual(r["provider"], "grok")  # speed-first order
        self.assertEqual(p["gpt"].calls, 0)

    def test_falls_through_failure_then_not_configured(self):
        self.assertEqual(P.AUTO_ORDER, ("grok", "fal", "local", "gpt"))
        r = self.run_auto(fakes(grok=Fake("grok", error="429"), fal=Fake("fal", status=P.NOT_CONFIGURED),
                                local=Fake("local", status=P.DOWN)))
        self.assertEqual(r["provider"], "gpt")
        self.assertEqual([(a["provider"], a["outcome"]) for a in r["attempts"]],
                         [("grok", "failed"), ("fal", "not configured"), ("local", "down"), ("gpt", "ok")])

    def test_down_provider_is_skipped(self):
        r = self.run_auto(fakes(grok=Fake("grok", status=P.DOWN), fal=Fake("fal", status=P.DOWN),
                                local=Fake("local", status=P.DOWN)))
        self.assertEqual(r["provider"], "gpt")

    def test_all_fail_raises_with_attempts(self):
        p = {n: Fake(n, error="boom") for n in P.AUTO_ORDER}
        with self.assertRaises(P.ProviderError) as cm:
            self.run_auto(p)
        self.assertEqual(len(cm.exception.attempts), 4)

    def test_explicit_provider_does_not_fall_back(self):
        p = fakes(gpt=Fake("gpt", error="quota"))
        with self.assertRaises(P.ProviderError):
            self.run_auto(p, choice="gpt")
        self.assertEqual(p["local"].calls, 0)

    def test_explicit_not_configured_provider_fails(self):
        with self.assertRaises(P.ProviderError):
            self.run_auto(fakes(grok=Fake("grok", status=P.NOT_CONFIGURED)), choice="grok")

    def test_order_is_configurable(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = P.generate_concept("auto", "x", Path(tmp) / "c.png", fakes(), order=("grok", "local"), log=lambda m: None)
        self.assertEqual(r["provider"], "grok")


class Timeouts(unittest.TestCase):
    def test_subprocess_timeout_becomes_provider_error(self):
        def runner(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, kw["timeout"])
        local = P.LocalProvider(runner=runner)
        with self.assertRaisesRegex(P.ProviderError, "timed out after 7s"):
            local.generate("x", "/tmp/never.png", 7)

    def test_timeout_is_passed_per_provider(self):
        seen = {}

        class Spy(Fake):
            def generate(self, prompt, out_path, timeout):
                seen[self.name] = timeout
                return super().generate(prompt, out_path, timeout)
        p = {"local": Spy("local", error="x"), "gpt": Spy("gpt"), "grok": Spy("grok")}
        with tempfile.TemporaryDirectory() as tmp:
            P.generate_concept("auto", "x", Path(tmp) / "c.png", p, order=("local", "gpt", "grok"),
                               timeouts={"local": 1, "gpt": 2, "grok": 3}, log=lambda m: None)
        self.assertEqual(seen, {"local": 1, "gpt": 2})


class Review1(unittest.TestCase):
    def test_local_retries_once_on_busy_exit(self):
        calls, slept = [], []

        def runner(cmd, **kw):
            calls.append(cmd)
            if len(calls) == 1:
                return SimpleNamespace(returncode=2, stdout="busy", stderr="")
            Path(cmd[cmd.index("--out") + 1]).write_bytes(b"png")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as tmp:
            P.LocalProvider(runner=runner, sleep=slept.append).generate("x", Path(tmp) / "c.png", 5)
        self.assertEqual((len(calls), slept), (2, [20]))

    def test_local_busy_twice_fails(self):
        runner = lambda cmd, **kw: SimpleNamespace(returncode=2, stdout="busy", stderr="")
        with self.assertRaises(P.ProviderError):
            P.LocalProvider(runner=runner, sleep=lambda s: None).generate("x", "/tmp/never.png", 5)

    def test_timeout_kills_grandchildren(self):
        import time
        with tempfile.TemporaryDirectory() as tmp:
            pidfile, bridge = Path(tmp) / "pid", Path(tmp) / "b.sh"
            bridge.write_text(f"#!/bin/bash\nsleep 30 &\necho $! > {pidfile}\nwait\n")
            bridge.chmod(0o755)
            with self.assertRaises(P.ProviderError):
                P.GptProvider(bridge).generate("x", Path(tmp) / "c.png", 1)
            time.sleep(0.3)
            try:
                os.kill(int(pidfile.read_text()), 0)
                alive = True
            except OSError:
                alive = False
            self.assertFalse(alive)

    def test_stale_output_is_not_credited(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "c.png"
            out.write_bytes(b"OLD")
            ran = lambda cmd, **kw: SimpleNamespace(returncode=0, stdout="", stderr="")
            bridge = Path(tmp) / "bridge"
            bridge.write_text("")
            with self.assertRaises(P.ProviderError):
                P.GptProvider(bridge, ran).generate("x", out, 5)
            out.write_bytes(b"OLD")
            with self.assertRaises(P.ProviderError):
                P.LocalProvider(runner=ran).generate("x", out, 5)


class Review2(unittest.TestCase):
    PNG = b"\x89PNG\r\n\x1a\nxx"

    class Resp:
        def __init__(self, body):
            self.body = body
        def read(self):
            return self.body
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    def grok(self, opener, env=None):
        env = {"XAI_API_KEY": "k", "XAI_TERMS_REVIEWED": "2026-11-07"} if env is None else env
        return P.GrokProvider(environ=env, opener=opener)

    def test_grok_gated_without_terms_signoff(self):
        class Sock:
            def close(self): pass
        g = P.GrokProvider(environ={"XAI_API_KEY": "k"}, connect=lambda *a, **k: Sock())
        self.assertEqual(g.check()[0], P.NOT_CONFIGURED)
        self.assertIn("XAI_TERMS_REVIEWED", g.check()[1])

    def test_grok_signoff_recorded_in_result(self):
        import base64
        body = json.dumps({"data": [{"b64_json": base64.b64encode(self.PNG).decode()}]}).encode()
        with tempfile.TemporaryDirectory() as tmp:
            info = self.grok(lambda *a, **k: self.Resp(body)).generate("x", Path(tmp) / "c.png", 5)
        self.assertEqual(info["licence_gate"], "XAI_TERMS_REVIEWED=2026-11-07")

    def test_grok_rejects_html(self):
        api = json.dumps({"data": [{"url": "https://imgen.x.ai/a.jpg"}]}).encode()
        opener = lambda req, timeout=None: self.Resp(b"<html>denied</html>" if isinstance(req, str) else api)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(P.ProviderError):
            self.grok(opener).generate("x", Path(tmp) / "c.png", 5)

    def test_grok_download_uses_remaining_budget(self):
        api = json.dumps({"data": [{"url": "https://imgen.x.ai/a.png"}]}).encode()
        clock, seen = [0.0], []

        def opener(req, timeout=None):
            seen.append(timeout)
            if isinstance(req, str):
                return self.Resp(self.PNG)
            clock[0] += 100
            return self.Resp(api)
        g = P.GrokProvider(environ={"XAI_API_KEY": "k"}, opener=opener, clock=lambda: clock[0])
        with tempfile.TemporaryDirectory() as tmp:
            g.generate("x", Path(tmp) / "c.png", 120)
        self.assertEqual(seen, [120, 20])

    def test_local_retry_gets_remaining_budget(self):
        clock, seen = [0.0], []

        def runner(cmd, timeout=None, **kw):
            seen.append(timeout)
            clock[0] += 300
            if len(seen) == 1:
                return SimpleNamespace(returncode=2, stdout="busy", stderr="")
            Path(cmd[cmd.index("--out") + 1]).write_bytes(b"png")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        loc = P.LocalProvider(runner=runner, sleep=lambda s: clock.__setitem__(0, clock[0] + s), clock=lambda: clock[0])
        with tempfile.TemporaryDirectory() as tmp:
            loc.generate("x", Path(tmp) / "c.png", 900)
        self.assertEqual(seen, [900, 580])

    def test_ctrl_c_kills_child(self):
        import signal
        import time
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / "pid"
            code = (f"import sys; sys.path.insert(0, {os.path.join(ROOT, 'scripts')!r}); import providers\n"
                    f"providers.run_group(['bash', '-c', 'echo $$ > {pidfile}; exec sleep 30'], timeout=600)\n")
            parent = subprocess.Popen([sys.executable, "-c", code], stderr=subprocess.DEVNULL)
            for _ in range(100):
                if pidfile.exists() and pidfile.read_text().strip():
                    break
                time.sleep(0.05)
            child = int(pidfile.read_text().strip())
            time.sleep(0.2)
            os.kill(parent.pid, signal.SIGINT)
            parent.wait(timeout=10)
            time.sleep(0.3)
            try:
                os.kill(child, 0)
                alive = open(f"/proc/{child}/stat").read().split()[2] != "Z"
            except OSError:
                alive = False
            if alive:
                os.kill(child, signal.SIGKILL)
            self.assertFalse(alive)


class Checks(unittest.TestCase):
    def test_grok_not_configured_without_key(self):
        status, detail = P.GrokProvider(environ={}).check()
        self.assertEqual(status, P.NOT_CONFIGURED)

    def test_grok_down_when_unreachable(self):
        def connect(*a, **k):
            raise OSError("no route")
        status, _ = P.GrokProvider(environ={"XAI_API_KEY": "k", "XAI_TERMS_REVIEWED": "d"}, connect=connect).check()
        self.assertEqual(status, P.DOWN)

    def test_grok_ready_and_key_never_in_detail(self):
        class Sock:
            def close(self): pass
        status, detail = P.GrokProvider(environ={"XAI_API_KEY": "sekret", "XAI_TERMS_REVIEWED": "d"}, connect=lambda *a, **k: Sock()).check()
        self.assertEqual(status, P.READY)
        self.assertNotIn("sekret", detail)

    def test_grok_error_text_redacts_key(self):
        def opener(*a, **k):
            raise RuntimeError("401 for key sekret")
        with self.assertRaises(P.ProviderError) as cm:
            P.GrokProvider(environ={"XAI_API_KEY": "sekret"}, opener=opener).generate("x", "/tmp/n.png", 1)
        self.assertNotIn("sekret", str(cm.exception))

    def test_gpt_login_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge = Path(tmp) / "bridge"
            bridge.write_text("")
            ok = lambda cmd, **kw: SimpleNamespace(stdout="Logged in using ChatGPT", stderr="", returncode=0)
            no = lambda cmd, **kw: SimpleNamespace(stdout="Not logged in", stderr="", returncode=1)
            real_which = P.shutil.which
            P.shutil.which = lambda n: "/bin/codex"
            try:
                self.assertEqual(P.GptProvider(bridge, ok).check()[0], P.READY)
                self.assertEqual(P.GptProvider(bridge, no).check()[0], P.NOT_CONFIGURED)
            finally:
                P.shutil.which = real_which
            self.assertEqual(P.GptProvider(Path(tmp) / "missing", ok).check()[0], P.NOT_CONFIGURED)

    def test_providers_check_one_line_each(self):
        lines = P.providers_check(fakes())
        self.assertEqual(len(lines), 4)
        self.assertTrue(lines[0].startswith("grok: ready"))  # AUTO_ORDER is speed-first


class ProvenanceFields(unittest.TestCase):
    def test_sidecar_records_provider_and_attempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            image, glb = Path(tmp) / "c.png", Path(tmp) / "a.glb"
            image.write_bytes(b"png")
            glb.write_bytes(b"glb")
            concept = {"provider": "gpt", "model": "chatgpt-image (via codex)", "command": ["x"], "seconds": 1,
                       "attempts": [{"provider": "local", "outcome": "failed", "detail": "busy", "seconds": 1.0},
                                    {"provider": "gpt", "outcome": "ok", "detail": "", "seconds": 5.0}]}
            args = SimpleNamespace(name="a", prompt="p", model="krea-2-turbo")
            record = json.loads(gen_asset.write_provenance(glb, args, image, [], gen_asset.threed_env({}), concept).read_text())
        self.assertEqual(record["image_provider"], "gpt")
        self.assertFalse(record["local_only"])
        self.assertIsNone(record["image_model"])
        self.assertEqual([a["provider"] for a in record["image_provider_attempts"]], ["local", "gpt"])
        self.assertNotIn("XAI_API_KEY", json.dumps(record))


if __name__ == "__main__":
    unittest.main()
