import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import mcp_call  # noqa: E402

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"}


class FakeMcp:
    """Tiny streamable-HTTP MCP server. sse=True answers tools/call as an event stream."""

    def __init__(self, sse=False, fail_tool=None):
        self.calls = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.calls.append((msg.get("method"), msg.get("params"), self.headers.get("Mcp-Session-Id")))
                if "id" not in msg:
                    self.send_response(202)
                    self.end_headers()
                    return
                m = msg["method"]
                if m == "initialize":
                    res = {"protocolVersion": "2025-03-26", "capabilities": {}, "serverInfo": {"name": "fake"}}
                elif m == "tools/list":
                    res = {"tools": [{"name": "save_all", "description": "Save everything\nmore"}, {"name": "ping"}]}
                else:
                    name = msg["params"]["name"]
                    res = {"content": [{"type": "text", "text": f"ran {name}"}], "isError": name == fail_tool}
                body = json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": res})
                if sse and m == "tools/call":
                    data = f"event: message\ndata: {body}\n\n".encode()
                    ctype = "text/event-stream"
                else:
                    data, ctype = body.encode(), "application/json"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Mcp-Session-Id", "sess-1")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.httpd = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/mcp"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class McpCall(unittest.TestCase):
    def test_list_and_call(self):
        s = FakeMcp()
        self.addCleanup(s.stop)
        c = mcp_call.McpClient(s.url)
        self.assertEqual([t["name"] for t in c.list_tools()], ["save_all", "ping"])
        res = c.call("ping", {"a": 1})
        self.assertEqual(res["content"][0]["text"], "ran ping")
        methods = [m for m, _, _ in s.calls]
        self.assertEqual(methods[:3], ["initialize", "notifications/initialized", "tools/list"])
        self.assertEqual(s.calls[-1][1], {"name": "ping", "arguments": {"a": 1}})
        self.assertEqual(s.calls[-1][2], "sess-1")  # session id echoed back

    def test_sse_reply(self):
        s = FakeMcp(sse=True)
        self.addCleanup(s.stop)
        self.assertEqual(mcp_call.McpClient(s.url).call("ping")["content"][0]["text"], "ran ping")

    def test_tool_error_raises(self):
        s = FakeMcp(fail_tool="boom")
        self.addCleanup(s.stop)
        with self.assertRaises(mcp_call.McpError):
            mcp_call.McpClient(s.url).call("boom")

    def test_unreachable(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        with self.assertRaises(mcp_call.McpError):
            mcp_call.McpClient(f"http://127.0.0.1:{port}/mcp", timeout=2).connect()

    def run_cli(self, *args, env=None):
        e = dict(os.environ, **(env or {}))
        return subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "mcp_call.py"), *args],
                              capture_output=True, text=True, env=e)

    def test_cli_verbs(self):
        s = FakeMcp()
        self.addCleanup(s.stop)
        r = self.run_cli("--url", s.url, "list-tools")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("save_all\tSave everything", r.stdout)
        r = self.run_cli("--url", s.url, "call", "ping", '{"x": 2}')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ran ping", r.stdout)
        r = self.run_cli("--url", s.url, "save-all")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "saved"))
        self.assertEqual(s.calls[-1][1]["name"], "save_all")
        r = self.run_cli("--url", s.url, "save-all", env={"MEGAJAM_MCP_SAVE_TOOL": "ping"})
        self.assertEqual(s.calls[-1][1]["name"], "ping")

    def test_cli_errors(self):
        s = FakeMcp(fail_tool="boom")
        self.addCleanup(s.stop)
        self.assertEqual(self.run_cli("--url", s.url, "call", "boom").returncode, 1)
        self.assertEqual(self.run_cli("--url", s.url, "call", "ping", "{nope").returncode, 2)

    def test_snapshot_commit(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, **GIT_ENV)
            subprocess.run(["git", "init", "-q", d], check=True, env=env)
            os.environ.update(GIT_ENV)
            self.assertIsNone(mcp_call.snapshot_commit(d))  # empty repo, nothing to add
            with open(os.path.join(d, "a.txt"), "w") as f:
                f.write("one")
            h = mcp_call.snapshot_commit(d)
            self.assertTrue(h)
            subject = subprocess.run(["git", "-C", d, "log", "-1", "--format=%s"], capture_output=True, text=True).stdout
            self.assertTrue(subject.startswith("snapshot: 20"), subject)
            self.assertIsNone(mcp_call.snapshot_commit(d))  # unchanged
            with open(os.path.join(d, "a.txt"), "w") as f:
                f.write("two")
            self.assertTrue(mcp_call.snapshot_commit(d, "custom msg"))

    def raw_server(self, response):
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
                c.sendall(response)
                c.close()

        threading.Thread(target=loop, daemon=True).start()
        return f"http://127.0.0.1:{srv.getsockname()[1]}/mcp"

    def test_truncated_reply_is_mcp_error(self):  # editor killed mid-reply -> IncompleteRead
        url = self.raw_server(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 500\r\n"
                              b"Connection: close\r\n\r\n{\"jsonrpc\": \"2.0\"")
        with self.assertRaises(mcp_call.McpError) as cm:
            mcp_call.McpClient(url, timeout=5).connect()
        self.assertEqual(cm.exception.exit_code, 2)

    def test_non_json_reply_is_mcp_error(self):
        body = b"<html>editor busy</html>"
        url = self.raw_server(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: "
                              + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
        with self.assertRaises(mcp_call.McpError):
            mcp_call.McpClient(url, timeout=5).connect()

    def test_rpc_error_exits_1_with_code(self):
        init = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode()
        err = json.dumps({"jsonrpc": "2.0", "id": 2, "error": {"code": -32602, "message": "Unknown tool: nope"}}).encode()

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if "id" not in msg:
                    self.send_response(202)
                    self.end_headers()
                    return
                data = init if msg["method"] == "initialize" else err
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        httpd = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        r = self.run_cli("--url", f"http://127.0.0.1:{httpd.server_port}/mcp", "call", "nope")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("-32602", r.stderr)

    def test_non_object_result_and_progress_only_stream(self):
        for body, ctype in ((b'{"jsonrpc":"2.0","id":2,"result":null}', "application/json"),
                            (b'event: message\ndata: {"jsonrpc":"2.0","method":"notifications/progress"}\n\n',
                             "text/event-stream"),
                            (b'[1, {"jsonrpc":"2.0","method":"notifications/progress"}]', "application/json")):
            head = (b"HTTP/1.1 200 OK\r\nContent-Type: " + ctype.encode() + b"\r\nContent-Length: "
                    + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n")
            url = self.raw_server(head + body)
            c = mcp_call.McpClient(url, timeout=5)
            c._ready = True
            c._id = 1  # next request id is 2
            with self.assertRaises(mcp_call.McpError, msg=body):
                c.call("save_all")

    def test_snapshot_stays_inside_project_folder(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, **GIT_ENV)
            subprocess.run(["git", "init", "-q", d], check=True, env=env)
            os.environ.update(GIT_ENV)
            os.makedirs(os.path.join(d, "Game"))
            with open(os.path.join(d, "Game", "Level.umap"), "w") as f:
                f.write("x")
            with open(os.path.join(d, "other-agent-wip.py"), "w") as f:
                f.write("wip")
            subprocess.run(["git", "-C", d, "add", "other-agent-wip.py"], check=True)  # staged outside
            mcp_call.snapshot_commit(os.path.join(d, "Game"))
            files = subprocess.run(["git", "-C", d, "show", "--name-only", "--format=", "HEAD"],
                                   capture_output=True, text=True).stdout.split()
            self.assertEqual(files, ["Game/Level.umap"])

    def test_snapshot_not_a_repo(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(mcp_call.McpError):
                mcp_call.snapshot_commit(d)


if __name__ == "__main__":
    unittest.main()
