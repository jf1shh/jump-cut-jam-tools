import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
import contextlib
import io
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import editor_watchdog  # noqa: E402
from test_mcp_call import GIT_ENV, FakeMcp  # noqa: E402

LAUNCHER = os.path.join(ROOT, "scripts", "launch-editor.sh")


def write_exec(path, text):
    with open(path, "w") as f:
        f.write(text)
    os.chmod(path, 0o755)


class Watchdog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        os.environ.update(GIT_ENV)
        self.proj = os.path.join(self.tmp, "Proj")
        os.makedirs(os.path.join(self.proj, "Saved", "Logs"))
        os.makedirs(os.path.join(self.proj, "Saved", "Autosaves"))
        subprocess.run(["git", "init", "-q", self.proj], check=True)
        with open(os.path.join(self.proj, "Saved", "Logs", "Proj.log"), "w") as f:
            f.write("crash context")
        with open(os.path.join(self.proj, "Saved", "Autosaves", "x_Auto1.umap"), "w") as f:
            f.write("a")
        with open(os.path.join(self.proj, "work.txt"), "w") as f:
            f.write("v1")
        self.repo_root = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo_root)
        self.mcp = FakeMcp()
        self.addCleanup(self.mcp.stop)
        self.spawned = []
        self.addCleanup(self.reap)
        # fake launcher: starts a "new editor" (sleep), records the pid, prints it like launch-editor.sh
        self.marker = os.path.join(self.tmp, "launched")
        self.launcher = os.path.join(self.tmp, "fake-launch.sh")
        write_exec(self.launcher,
                   f"#!/bin/sh\nsleep 300 >/dev/null 2>&1 &\necho $! > {self.marker}\necho $!\n")

    def reap(self):
        for p in self.spawned:
            try:
                os.kill(p, signal.SIGKILL)
            except OSError:
                pass
        if os.path.exists(self.marker):
            try:
                os.kill(int(open(self.marker).read()), signal.SIGKILL)
            except OSError:
                pass

    def args(self, pid, *extra):
        return ["--project", self.proj, "--uproject", "/x/P.uproject", "--editor", "/x/UnrealEditor",
                "--pid", str(pid), "--max-ticks", "1", "--mcp-url", self.mcp.url, "--launcher", self.launcher,
                "--repo-root", self.repo_root, "--journal-cmd",
                "echo 'systemd-oomd: Killed megajam-job-1 due to memory pressure'", *extra]

    def commits(self):
        r = subprocess.run(["git", "-C", self.proj, "log", "--format=%s"], capture_output=True, text=True)
        return r.stdout.split("\n")[:-1] if r.returncode == 0 else []

    def test_alive_saves_and_commits_dead_relaunches(self):
        editor = subprocess.Popen(["sleep", "300"])
        self.spawned.append(editor.pid)
        # tick 1: alive -> save-all + snapshot, no relaunch
        self.assertEqual(editor_watchdog.main(self.args(editor.pid)), 0)
        self.assertEqual(self.mcp.calls[-1][1]["name"], "save_all")
        self.assertEqual(len(self.commits()), 1)
        self.assertFalse(os.path.exists(self.marker))
        # the editor gets a SIGTERM (as in mock jam 10), with new unsaved-on-disk work
        with open(os.path.join(self.proj, "work.txt"), "w") as f:
            f.write("v2")
        editor.terminate()
        editor.wait()
        before = len(self.mcp.calls)
        import io
        import contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            editor_watchdog.main(self.args(editor.pid))
        text = out.getvalue()
        # dead: no save-all over MCP, but a commit, crash logs copied, why logged, relaunched
        self.assertEqual(len(self.mcp.calls), before)
        self.assertEqual(len(self.commits()), 2)
        self.assertIn("before relaunch", self.commits()[0])
        self.assertTrue(os.path.exists(self.marker))
        new_pid = int(open(self.marker).read())
        self.assertIn(f"new pid {new_pid}", text)
        self.assertIn("is GONE", text)
        self.assertIn("systemd-oomd: Killed megajam-job-1", text)
        self.assertIn("last snapshot:", text)
        self.assertIn("autosave files on disk: 1", text)
        crash_dirs = os.listdir(os.path.join(self.repo_root, "stages", "04_ship", "output", "crash-logs"))
        self.assertEqual(len(crash_dirs), 1)
        copied = os.path.join(self.repo_root, "stages", "04_ship", "output", "crash-logs", crash_dirs[0], "Logs", "Proj.log")
        self.assertEqual(open(copied).read(), "crash context")

    def test_restart_budget(self):
        dead = subprocess.Popen(["true"])
        dead.wait()
        out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "editor_watchdog.py"),
                              *self.args(dead.pid, "--max-restarts", "0")], capture_output=True, text=True)
        self.assertIn("restart budget 0 used up", out.stdout)
        self.assertFalse(os.path.exists(self.marker))

    def test_broken_mcp_reply_still_commits(self):  # truncated reply: watchdog must not crash
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(5)
        self.addCleanup(srv.close)

        def loop():
            while True:
                try:
                    c, _ = srv.accept()
                except OSError:
                    return
                c.recv(65536)
                c.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 500\r\nConnection: close\r\n\r\n{\"jsonrpc\"")
                c.close()

        threading.Thread(target=loop, daemon=True).start()
        editor = subprocess.Popen(["sleep", "300"])
        self.spawned.append(editor.pid)
        a = self.args(editor.pid)
        a[a.index("--mcp-url") + 1] = f"http://127.0.0.1:{srv.getsockname()[1]}/mcp"
        a += ["--mcp-timeout", "5"]
        editor_watchdog.main(a)
        self.assertEqual(len(self.commits()), 1)

    @unittest.skipUnless(shutil.which("waitfor"), "waitfor not installed")
    def test_slow_relaunch_is_adopted_not_doubled(self):
        """Launcher times out (exit 5, editor alive): watchdog tracks the new pid, next tick saves to it."""
        port_sock = socket.socket()
        port_sock.bind(("127.0.0.1", 0))
        port = port_sock.getsockname()[1]
        port_sock.close()
        pidfile = os.path.join(self.tmp, "editor.pid")
        calls = os.path.join(self.tmp, "calls")
        editor = os.path.join(self.tmp, "UnrealEditor")
        write_exec(editor, f"""#!/usr/bin/env python3
import json, os, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
port = [int(a.split("=")[1]) for a in sys.argv if a.startswith("-ModelContextProtocolPort=")][0]
open({pidfile!r}, "w").write(str(os.getpid()))
time.sleep(3)
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(405); self.end_headers()
    def do_POST(self):
        msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        open({calls!r}, "a").write(msg.get("method", "") + "\\n")
        if "id" not in msg:
            self.send_response(202); self.end_headers(); return
        body = json.dumps({{"jsonrpc": "2.0", "id": msg["id"], "result": {{"content": [], "isError": False}}}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
HTTPServer(("127.0.0.1", port), H).serve_forever()
""")
        open(os.path.join(self.proj, "P.uproject"), "w").close()
        dead = subprocess.Popen(["true"])
        dead.wait()
        env = dict(os.environ, MCP_PORT=str(port), LAUNCH_SCOPE_CMD="none", WAIT_TIMEOUT="1", LAUNCH_PREFLIGHT="0")
        self.addCleanup(lambda: os.path.exists(pidfile) and os.kill(int(open(pidfile).read()), signal.SIGKILL))
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "editor_watchdog.py"),
                            "--project", self.proj, "--uproject", os.path.join(self.proj, "P.uproject"),
                            "--editor", editor, "--pid", str(dead.pid), "--max-ticks", "3", "--interval-sec", "5",
                            "--mcp-url", f"http://127.0.0.1:{port}/mcp", "--mcp-timeout", "5",
                            "--repo-root", self.repo_root, "--journal-cmd", "true",
                            "--launcher", LAUNCHER], capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(r.stdout.count("is GONE"), 1, r.stdout)
        self.assertIn("tools/call", open(calls).read())

    def test_save_failure_still_commits(self):
        s = FakeMcp(fail_tool="save_all")
        self.addCleanup(s.stop)
        editor = subprocess.Popen(["sleep", "300"])
        self.spawned.append(editor.pid)
        a = self.args(editor.pid)
        a[a.index("--mcp-url") + 1] = s.url
        editor_watchdog.main(a)
        self.assertEqual(len(self.commits()), 1)


class LaunchPreflightWait(unittest.TestCase):
    def _wait_seen(self, relaunch):
        seen = {}

        def fake_run(cmd, **kw):
            seen["wait"] = kw["env"].get("PREFLIGHT_WAIT")
            return subprocess.CompletedProcess(cmd, 0, "4242\n", "")
        orig = editor_watchdog.subprocess.run
        saved = os.environ.pop("PREFLIGHT_WAIT", None)
        editor_watchdog.subprocess.run = fake_run
        try:
            editor_watchdog.launch("/bin/true", "ed", "p", relaunch=relaunch)
        finally:
            editor_watchdog.subprocess.run = orig
            if saved is not None:
                os.environ["PREFLIGHT_WAIT"] = saved
        return seen["wait"]

    def test_first_launch_keeps_launcher_default_wait(self):
        self.assertIsNone(self._wait_seen(False))

    def test_relaunch_gets_short_wait(self):
        self.assertEqual(self._wait_seen(True), "30")


class LaunchBindRetry(unittest.TestCase):
    """launch-editor.sh exit 9 (port 8010 bind race) is retried once in the same cycle."""

    def _launch(self, codes, relaunch=True):
        calls, slept = [], []

        def fake_run(cmd, **kw):
            rc = codes[len(calls)]
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, rc, "4242\n" if rc in (0, 3, 5) else "", f"exit {rc}")
        orig = editor_watchdog.subprocess.run
        editor_watchdog.subprocess.run = fake_run
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                pid = editor_watchdog.launch("/bin/true", "ed", "p", relaunch=relaunch, sleep=slept.append)
        finally:
            editor_watchdog.subprocess.run = orig
        return pid, calls, slept

    def test_bind_error_then_up_returns_pid(self):
        pid, calls, slept = self._launch([9, 0])
        self.assertEqual((pid, len(calls), slept), (4242, 2, [editor_watchdog.BIND_RETRY_WAIT]))
        self.assertEqual(editor_watchdog.BIND_RETRY_WAIT, 5)

    def test_bind_error_twice_raises_after_one_retry(self):
        with self.assertRaisesRegex(RuntimeError, "launcher exit 9"):
            self._launch([9, 9, 0])

    def test_other_failures_are_not_retried(self):
        for rc in (4, 7, 8):
            with self.subTest(rc=rc), self.assertRaisesRegex(RuntimeError, f"launcher exit {rc}"):
                self._launch([rc, 0])

    def test_first_launch_also_retries(self):
        self.assertEqual(self._launch([9, 5], relaunch=False)[0], 4242)


class BindRetryInTick(unittest.TestCase):
    """End to end through tick(): a fake launcher that loses the bind race once costs one restart, not two."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.count = os.path.join(self.tmp, "count")
        self.launcher = os.path.join(self.tmp, "fake-launch.sh")
        write_exec(self.launcher, f"""#!/bin/bash
n=$(cat {self.count} 2>/dev/null || echo 0); n=$((n+1)); echo $n > {self.count}
if [ "$n" = 1 ]; then echo "launch-editor: HttpListener unable to bind" >&2; exit 9; fi
echo 777
""")

    def test_one_bind_race_still_relaunches_this_cycle(self):
        a = editor_watchdog.argparse.Namespace(
            launcher=self.launcher, editor="ed", uproject="p", project=self.tmp, repo_root=self.tmp,
            journal_cmd="true", max_restarts=5, mcp_url=None, mcp_timeout=1)
        dead = subprocess.Popen(["true"])
        dead.wait()
        state = {"pid": dead.pid, "start": None, "restarts": 0, "stop": False}
        with mock.patch.object(editor_watchdog, "snapshot_commit", return_value=None), \
                mock.patch.object(editor_watchdog, "restored_summary", return_value="x"), \
                mock.patch.object(editor_watchdog, "proc_start", return_value=None), \
                mock.patch.object(editor_watchdog.time, "sleep") as slept, \
                contextlib.redirect_stdout(io.StringIO()) as out:
            editor_watchdog.tick(a, state)
        self.assertEqual(state["pid"], 777)
        self.assertEqual(state["restarts"], 1)
        slept.assert_called_once_with(5)
        self.assertIn("retrying once", out.getvalue())
        self.assertNotIn("relaunch FAILED", out.getvalue())


class LaunchEditor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.uproject = os.path.join(self.tmp, "P.uproject")
        open(self.uproject, "w").close()
        self.editor = os.path.join(self.tmp, "UnrealEditor")
        # fake editor: answers 405 on the port given by -ModelContextProtocolPort=N
        write_exec(self.editor, """#!/usr/bin/env python3
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
port = [int(a.split("=")[1]) for a in sys.argv if a.startswith("-ModelContextProtocolPort=")][0]
assert "-ModelContextProtocolStartServer" in sys.argv
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(405); self.end_headers()
    def log_message(self, *a): pass
HTTPServer(("127.0.0.1", port), H).serve_forever()
""")
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        self.port = s.getsockname()[1]
        s.close()
        self.env = dict(os.environ, MCP_PORT=str(self.port), LAUNCH_SCOPE_CMD="none", WAIT_TIMEOUT="30",
                        LAUNCH_PREFLIGHT="0")

    def test_dryrun_shows_scope_profile_and_flags(self):
        env = dict(self.env, DRYRUN="1")
        del env["LAUNCH_SCOPE_CMD"]
        r = subprocess.run([LAUNCHER, self.editor, self.uproject], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        for want in ("systemd-run --user --scope --unit=megajam-job-", "MemoryHigh=26G", "MemoryMax=28G",
                     "MemorySwapMax=8G", "-ModelContextProtocolStartServer",
                     f"-ModelContextProtocolPort={self.port}", "-nosplash"):
            self.assertIn(want, r.stdout)

    @unittest.skipUnless(shutil.which("waitfor"), "waitfor not installed")
    def test_launch_waits_and_prints_pid(self):
        r = subprocess.run([LAUNCHER, self.editor, self.uproject], capture_output=True, text=True, env=self.env)
        pid = int(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else None
        try:
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(pid and editor_watchdog.pid_alive(pid))
            # second launch refuses while the port answers
            r2 = subprocess.run([LAUNCHER, self.editor, self.uproject], capture_output=True, text=True, env=self.env)
            self.assertEqual(r2.returncode, 3)
        finally:
            if pid:
                os.kill(pid, signal.SIGKILL)

    def test_bad_args(self):
        r = subprocess.run([LAUNCHER], capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 2)
        r = subprocess.run([LAUNCHER, "/nope/UnrealEditor", self.uproject], capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 2)


class PidReuseTest(unittest.TestCase):
    def test_reused_pid_counts_as_dead(self):
        me = os.getpid()
        start = editor_watchdog.proc_start(me)
        self.assertTrue(editor_watchdog.pid_alive(me, start))
        self.assertTrue(editor_watchdog.pid_alive(me))
        self.assertFalse(editor_watchdog.pid_alive(me, str(int(start) + 1)))  # same pid, different process


if __name__ == "__main__":
    unittest.main()
