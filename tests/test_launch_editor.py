import os
import socket
import subprocess
import tempfile
import threading
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(ROOT, "scripts", "launch-editor.sh")


def run_launch(d, port, waitfor=None, **extra):
    editor = os.path.join(d, "FakeEditor")
    with open(editor, "w") as f:
        f.write("#!/bin/sh\nexit 0\n")
    os.chmod(editor, 0o755)
    proj = os.path.join(d, "Mock.uproject")
    with open(proj, "w") as f:
        f.write("{}")
    env = {**os.environ, "MCP_PORT": str(port), "XDG_STATE_HOME": os.path.join(d, "state"),
           "WAITFOR_BIN": waitfor or "/nonexistent/waitfor", "LAUNCH_SCOPE_CMD": "none",
           "LAUNCH_PREFLIGHT": "0", **extra}
    env.pop("WAIT_TIMEOUT", None) if "WAIT_TIMEOUT" not in extra else None
    return subprocess.run([LAUNCH, editor, proj], capture_output=True, text=True, env=env, timeout=60)


class LaunchEditorEngine(unittest.TestCase):
    def dry(self, d, *args, **extra):
        proj = os.path.join(d, "Mock.uproject")
        open(proj, "w").write("{}")
        roots = {}
        for v in ("59", "58"):  # fake engine trees with an executable editor, so the -x check passes
            exe = os.path.join(d, "ue" + v, "Engine", "Binaries", "Linux", "UnrealEditor")
            os.makedirs(os.path.dirname(exe), exist_ok=True)
            open(exe, "w").write("#!/bin/sh\n")
            os.chmod(exe, 0o755)
            roots["UE%s_ROOT" % v] = os.path.join(d, "ue" + v)
        self.roots = roots
        env = {**os.environ, "DRYRUN": "1", "LAUNCH_SCOPE_CMD": "none", **roots, **extra}
        env.pop("UE_VERSION", None) if "UE_VERSION" not in extra else None
        env.pop("SDL_VIDEODRIVER", None) if "SDL_VIDEODRIVER" not in extra else None
        r = subprocess.run([LAUNCH, *args, proj], capture_output=True, text=True, env=env, timeout=30)
        return r.returncode, r.stdout, r.stderr

    def test_default_engine_is_59_with_x11(self):
        with tempfile.TemporaryDirectory() as d:
            rc, out, err = self.dry(d)
        self.assertEqual(rc, 0, err)
        self.assertTrue(out.startswith(self.roots["UE59_ROOT"] + "/Engine/Binaries/Linux/UnrealEditor "), out)
        self.assertIn("SDL_VIDEODRIVER=x11", err)

    def test_env_and_flag_select_58(self):
        with tempfile.TemporaryDirectory() as d:
            _, out, _ = self.dry(d, UE_VERSION="5.8")
            self.assertTrue(out.startswith(self.roots["UE58_ROOT"] + "/"), out)
            _, out, _ = self.dry(d, "--ue58")
            self.assertTrue(out.startswith(self.roots["UE58_ROOT"] + "/"), out)

    def test_58_fallback_sets_no_sdl_default(self):
        with tempfile.TemporaryDirectory() as d:
            rc, _, err = self.dry(d, "--ue58")
        self.assertEqual(rc, 0, err)
        self.assertNotIn("SDL_VIDEODRIVER=x11", err)

    def test_user_sdl_driver_is_preserved_on_both_engines(self):
        for flag in ("--ue59", "--ue58"):
            with tempfile.TemporaryDirectory() as d:
                rc, _, err = self.dry(d, flag, SDL_VIDEODRIVER="wayland")
            self.assertEqual(rc, 0, err)
            self.assertIn("SDL_VIDEODRIVER=wayland", err)

    def test_explicit_58_binary_without_version_gets_no_sdl_default(self):
        # editor_watchdog calls: launch-editor.sh /abs/UnrealEditor proj.uproject, with no UE_VERSION.
        with tempfile.TemporaryDirectory() as d:
            proj = os.path.join(d, "Mock.uproject")
            open(proj, "w").write("{}")
            env = {**os.environ, "DRYRUN": "1", "LAUNCH_SCOPE_CMD": "none"}
            for k in ("UE_VERSION", "SDL_VIDEODRIVER", "UE_EDITOR"):
                env.pop(k, None)
            res = {}
            for name in ("UnrealEngine-5.8", "UnrealEngine-5.9"):
                exe = os.path.join(d, name, "Engine", "Binaries", "Linux", "UnrealEditor")
                os.makedirs(os.path.dirname(exe))
                open(exe, "w").write("#!/bin/sh\n")
                os.chmod(exe, 0o755)
                res[name] = subprocess.run([LAUNCH, exe, proj], capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(res["UnrealEngine-5.8"].returncode, 0, res["UnrealEngine-5.8"].stderr)
        self.assertNotIn("SDL_VIDEODRIVER=x11", res["UnrealEngine-5.8"].stderr)
        self.assertIn("SDL_VIDEODRIVER=x11", res["UnrealEngine-5.9"].stderr)  # other explicit binaries keep the 5.9 default

    def test_explicit_binary_with_explicit_version_keeps_the_version(self):
        with tempfile.TemporaryDirectory() as d:
            proj = os.path.join(d, "Mock.uproject")
            open(proj, "w").write("{}")
            exe = os.path.join(d, "UnrealEngine-5.8", "Engine", "Binaries", "Linux", "UnrealEditor")
            os.makedirs(os.path.dirname(exe))
            open(exe, "w").write("#!/bin/sh\n")
            os.chmod(exe, 0o755)
            env = {**os.environ, "DRYRUN": "1", "LAUNCH_SCOPE_CMD": "none", "UE_VERSION": "5.9"}
            env.pop("SDL_VIDEODRIVER", None)
            r = subprocess.run([LAUNCH, exe, proj], capture_output=True, text=True, env=env, timeout=30)
        self.assertIn("SDL_VIDEODRIVER=x11", r.stderr)

    def test_bad_version_is_usage_error(self):
        with tempfile.TemporaryDirectory() as d:
            rc, _, err = self.dry(d, UE_VERSION="5.7")
        self.assertEqual(rc, 2)
        self.assertIn("UE_VERSION", err)


class LaunchEditorPort(unittest.TestCase):
    def test_held_port_fails_fast_with_exit_8(self):
        # A listener that accepts connections (kernel backlog) but never speaks HTTP = a hung editor.
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        try:
            with tempfile.TemporaryDirectory() as d:
                r = run_launch(d, srv.getsockname()[1], HELD_PROBE_TIMEOUT="2")
        finally:
            srv.close()
        self.assertEqual(r.returncode, 8, r.stderr)
        self.assertIn("did not answer MCP within 2s", r.stderr)
        self.assertNotIn("kill it", r.stderr)

    def test_full_accept_queue_still_exits_8_quickly(self):
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(0)
        port = srv.getsockname()[1]
        clients = []
        try:
            for _ in range(4):  # fill the accept queue so new SYNs are dropped
                c = socket.socket()
                c.setblocking(False)
                try:
                    c.connect(("127.0.0.1", port))
                except BlockingIOError:
                    pass
                clients.append(c)
            with tempfile.TemporaryDirectory() as d:
                r = run_launch(d, port, HELD_PROBE_TIMEOUT="2")
        finally:
            for c in clients:
                c.close()
            srv.close()
        self.assertEqual(r.returncode, 8, r.stderr)

    def test_slow_but_healthy_server_is_not_called_hung(self):
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(5)
        port = srv.getsockname()[1]

        def serve():
            while True:
                try:
                    conn, _ = srv.accept()
                except OSError:
                    return
                time.sleep(3)  # busy game thread: answers after more than the 2 s first probe
                try:
                    conn.recv(4096)
                    conn.sendall(b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
                except OSError:
                    pass
                conn.close()

        threading.Thread(target=serve, daemon=True).start()
        try:
            with tempfile.TemporaryDirectory() as d:
                r = run_launch(d, port, HELD_PROBE_TIMEOUT="10")
        finally:
            srv.close()
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("busy", r.stderr)
        self.assertEqual(r.stdout.strip(), str(os.getpid()))  # the socket owner's pid, so callers can adopt it

    def test_free_port_gets_past_the_port_check(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()  # free now
        with tempfile.TemporaryDirectory() as d:
            r = run_launch(d, port)
        self.assertEqual(r.returncode, 6, r.stderr)  # reached the missing-waitfor check

    def test_wait_has_default_timeout_and_names_what_it_waits_for(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "waitfor")
            with open(fake, "w") as f:
                f.write("#!/bin/sh\necho \"waitfor args: $*\" >&2\nexit 1\n")
            os.chmod(fake, 0o755)
            r = run_launch(d, port, waitfor=fake)
            self.assertIn("waiting for MCP on :%d (up to 300s" % port, r.stderr)
            self.assertIn("--timeout 300", r.stderr)
            r = run_launch(d, port, waitfor=fake, WAIT_TIMEOUT="7")
            self.assertIn("up to 7s", r.stderr)
            self.assertIn("--timeout 7", r.stderr)

    def test_bind_error_in_editor_log_exits_9_fast_and_stops_the_editor(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        with tempfile.TemporaryDirectory() as d:
            marker = os.path.join(d, "editor.pid")
            editor = os.path.join(d, "FakeEditor")
            with open(editor, "w") as f:  # logs the bind failure, then idles like a MCP-less editor
                f.write("#!/bin/bash\necho $$ > '%s'\necho 'LogHttpListener: Error: HttpListener unable to bind to 127.0.0.1:%d'\nexec sleep 60\n" % (marker, port))
            os.chmod(editor, 0o755)
            proj = os.path.join(d, "Mock.uproject")
            open(proj, "w").write("{}")
            waitfor = os.path.join(d, "waitfor")  # minimal real waitfor: run the command until it succeeds or times out
            with open(waitfor, "w") as f:
                f.write("#!/bin/bash\nt=0; shift; shift; shift; shift; shift\nfor i in $(seq 1 30); do \"$@\" && exit 0; sleep 0.2; done\nexit 1\n")
            os.chmod(waitfor, 0o755)
            env = {**os.environ, "MCP_PORT": str(port), "XDG_STATE_HOME": os.path.join(d, "state"), "WAITFOR_BIN": waitfor,
                   "LAUNCH_SCOPE_CMD": "none", "LAUNCH_PREFLIGHT": "0", "WAIT_TIMEOUT": "120"}
            t0 = time.time()
            r = subprocess.run([LAUNCH, editor, proj], capture_output=True, text=True, env=env, timeout=60)
            took = time.time() - t0
            pid = int(open(marker).read().strip())
            time.sleep(0.5)
            alive = True
            try:
                os.kill(pid, 0)
            except OSError:
                alive = False
        self.assertEqual(r.returncode, 9, r.stderr)
        self.assertIn("unable to bind", r.stderr)
        self.assertEqual(r.stdout.strip(), "")
        self.assertLess(took, 20)
        self.assertFalse(alive, "the editor that lost the bind race should be stopped")


if __name__ == "__main__":
    unittest.main()
