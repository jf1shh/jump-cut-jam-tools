"""new-mock-project port pin + --verify-port, and launch-editor.sh's gpu-preflight wait (T-20261108-19)."""
import http.server
import importlib.util
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("nmp2", ROOT / "scripts" / "new-mock-project.py")
nmp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nmp)

SECTION = "[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]"


class PortPin(unittest.TestCase):
    def test_pin_is_in_user_settings_ini_only(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(nmp.main(["MockEleven", td]), 0)
            pin = (Path(td) / "Config" / "DefaultEditorPerProjectUserSettings.ini").read_text()
            self.assertIn(SECTION, pin)
            self.assertIn("ServerPortNumber=8010", pin)
            self.assertIn("[/Script/ModelContextProtocol.ModelContextProtocolSettings]", pin)  # 5.9 name, 5.8.4 name above
            eng = (Path(td) / "Config" / "DefaultEngine.ini").read_text()
            self.assertNotIn("ServerPortNumber", eng)
            self.assertIn("GameDefaultMap=", eng)  # the rest of the engine ini survives

    def test_custom_url_port_goes_to_pin(self):
        with tempfile.TemporaryDirectory() as td:
            nmp.main(["MockEleven", td, "--mcp-url", "http://127.0.0.1:8123/mcp"])
            self.assertIn("ServerPortNumber=8123",
                          (Path(td) / "Config" / "DefaultEditorPerProjectUserSettings.ini").read_text())

    def test_strip_section_keeps_neighbours(self):
        text = "[A]\nx=1\n\n; note\n" + SECTION + "\nServerPortNumber=1\n\n[B]\ny=2\n"
        out = nmp.strip_section(text, SECTION)
        self.assertNotIn("ServerPortNumber", out)
        self.assertNotIn("; note", out)
        self.assertIn("x=1", out)
        self.assertIn("[B]\ny=2", out)


class _H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(405)
        self.end_headers()

    def log_message(self, *a):
        pass


class VerifyPort(unittest.TestCase):
    def test_405_counts_as_up(self):
        srv = http.server.HTTPServer(("127.0.0.1", 0), _H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            msgs = []
            self.assertTrue(nmp.verify_port(srv.server_address[1], timeout=5, interval=0.1, out=msgs.append))
            self.assertIn("405", msgs[0])
        finally:
            srv.shutdown()

    def test_closed_port_fails_after_timeout(self):
        s = http.server.HTTPServer(("127.0.0.1", 0), _H)
        port = s.server_address[1]
        s.server_close()
        self.assertFalse(nmp.verify_port(port, timeout=0.3, interval=0.1, out=lambda m: None))

    def test_scaffold_with_verify_port_does_not_poll(self):
        s = http.server.HTTPServer(("127.0.0.1", 0), _H)
        port = s.server_address[1]
        s.server_close()  # nothing listens, as before any editor launch
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(nmp.main(["MockEleven", td, "--verify-port", str(port), "--verify-timeout", "30"]), 0)

    def test_cli_verify_only(self):
        s = http.server.HTTPServer(("127.0.0.1", 0), _H)
        port = s.server_address[1]
        s.server_close()
        self.assertEqual(nmp.main(["X", "/nonexistent", "--verify-only", "--verify-port", str(port),
                                   "--verify-timeout", "0.2"]), 1)
        with self.assertRaises(SystemExit):
            nmp.main(["X", "/nonexistent", "--verify-only"])


class LaunchPreflight(unittest.TestCase):
    def run_launch(self, td, pf_body, wait="1"):
        td = Path(td)
        ed, proj, pf = td / "UnrealEditor", td / "P.uproject", td / "pf"
        ed.write_text("#!/bin/sh\nexit 0\n")
        pf.write_text(pf_body)
        proj.write_text("{}")
        for f in (ed, pf):
            f.chmod(0o755)
        env = {**os.environ, "PREFLIGHT_BIN": str(pf), "PREFLIGHT_WAIT": wait, "LAUNCH_SCOPE_CMD": "none",
               "WAIT_TIMEOUT": "2", "MCP_PORT": "1", "EDITOR_LOG": str(td / "ed.log")}
        return subprocess.run([str(ROOT / "scripts" / "launch-editor.sh"), str(ed), str(proj)],
                              env=env, capture_output=True, text=True, timeout=60)

    def test_preflight_that_never_clears_blocks_launch(self):
        with tempfile.TemporaryDirectory() as td:
            r = self.run_launch(td, "#!/bin/sh\nexit 1\n")
            self.assertEqual(r.returncode, 7, r.stderr)
            self.assertIn("did not clear", r.stderr)
            self.assertFalse((Path(td) / "ed.log").exists())  # nothing launched

    def test_clear_preflight_lets_launch_proceed(self):
        with tempfile.TemporaryDirectory() as td:
            r = self.run_launch(td, "#!/bin/sh\nexit 0\n")
            self.assertNotEqual(r.returncode, 7, r.stderr)
            self.assertIn("started pid", r.stderr)

    def _default_env_run(self, td, extra):
        td = Path(td)
        bindir = td / "bin"
        bindir.mkdir()
        ed, proj, pf = td / "UnrealEditor", td / "P.uproject", bindir / "gpu-preflight"
        ed.write_text("#!/bin/sh\nexit 0\n")
        pf.write_text("#!/bin/sh\nexit 1\n")  # GPU busy
        proj.write_text("{}")
        for f in (ed, pf):
            f.chmod(0o755)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("PREFLIGHT_", "LAUNCH_PREFLIGHT"))}
        env.update(PATH=f"{bindir}:{env.get('PATH', '/usr/bin:/bin')}", LAUNCH_SCOPE_CMD="none",
                   WAIT_TIMEOUT="2", MCP_PORT="1", PREFLIGHT_WAIT="1", EDITOR_LOG=str(td / "ed.log"), **extra)
        return subprocess.run([str(ROOT / "scripts" / "launch-editor.sh"), str(ed), str(proj)],
                              env=env, capture_output=True, text=True, timeout=60)

    def test_gate_is_on_by_default_when_gpu_preflight_on_path(self):
        with tempfile.TemporaryDirectory() as td:
            r = self._default_env_run(td, {})
            self.assertEqual(r.returncode, 7, r.stderr)
            self.assertNotIn("started pid", r.stderr)

    def test_launch_preflight_zero_opts_out(self):
        with tempfile.TemporaryDirectory() as td:
            r = self._default_env_run(td, {"LAUNCH_PREFLIGHT": "0"})
            self.assertNotEqual(r.returncode, 7, r.stderr)
            self.assertIn("started pid", r.stderr)

    def test_preflight_bin_none_skips_the_gate(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            ed, proj = td / "UnrealEditor", td / "P.uproject"
            ed.write_text("#!/bin/sh\nexit 0\n")
            ed.chmod(0o755)
            proj.write_text("{}")
            env = {**os.environ, "PREFLIGHT_BIN": "none", "LAUNCH_SCOPE_CMD": "none", "WAIT_TIMEOUT": "2",
                   "MCP_PORT": "1", "EDITOR_LOG": str(td / "ed.log")}
            r = subprocess.run([str(ROOT / "scripts" / "launch-editor.sh"), str(ed), str(proj)],
                               env=env, capture_output=True, text=True, timeout=60)
            self.assertNotEqual(r.returncode, 7, r.stderr)
            self.assertIn("started pid", r.stderr)

    def test_missing_preflight_is_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            ed, proj = td / "UnrealEditor", td / "P.uproject"
            ed.write_text("#!/bin/sh\nexit 0\n")
            ed.chmod(0o755)
            proj.write_text("{}")
            env = {**os.environ, "PREFLIGHT_BIN": str(td / "nope"), "LAUNCH_SCOPE_CMD": "none", "MCP_PORT": "1"}
            r = subprocess.run([str(ROOT / "scripts" / "launch-editor.sh"), str(ed), str(proj)],
                               env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 7)


if __name__ == "__main__":
    unittest.main()
