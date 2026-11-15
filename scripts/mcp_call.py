#!/usr/bin/env python3
"""Small CLI for the Unreal MCP server (streamable HTTP, JSON-RPC) at http://127.0.0.1:8010/mcp.

Replaces the improvised x.py from mock jam 10. Standard library only.

  mcp_call.py list-tools
  mcp_call.py call TOOL '{"arg": 1}'        # JSON args optional, '-' reads stdin
  mcp_call.py save-all                      # calls the save tool (see MEGAJAM_MCP_SAVE_TOOL)
  mcp_call.py snapshot-commit [--project DIR] [--message MSG]

Global options: --url URL (or MEGAJAM_MCP_URL), --timeout SECONDS.
Exit code: 0 ok, 1 tool/JSON-RPC/HTTP-status error (message carries the code, e.g. -32602 unknown tool),
2 usage error, editor unreachable, or unreadable reply.

Only the lead agent calls Unreal MCP (AGENTS.md). Run list-tools once in the real editor to confirm the
save tool name; the default is a guess and is unverified until then.
"""
import argparse
import datetime
import http.client
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:8010/mcp"
DEFAULT_SAVE_TOOL = "save_all"  # unverified guess; override with MEGAJAM_MCP_SAVE_TOOL
PROTOCOL = "2025-03-26"


EXIT_TOOL, EXIT_CONN = 1, 2


class McpError(Exception):
    """exit_code: 1 = tool/RPC/HTTP-status error, 2 = unreachable or unreadable reply."""

    def __init__(self, msg, exit_code=EXIT_TOOL):
        super().__init__(msg)
        self.exit_code = exit_code


def _parse_body(raw, content_type, want_id):
    """Body is plain JSON or an SSE stream; return the JSON-RPC message with id want_id."""
    text = raw.decode("utf-8", "replace").strip()
    if not text:
        return None
    if "text/event-stream" in (content_type or "") or text.startswith(("event:", "data:")):
        # Only a message carrying our request id answers it; progress notifications do not.
        for line in text.splitlines():
            if line.startswith("data:"):
                try:
                    msg = json.loads(line[5:].strip())
                except ValueError:
                    continue
                if isinstance(msg, dict) and msg.get("id") == want_id:
                    return msg
        return None
    msg = json.loads(text)
    if isinstance(msg, list):
        for m in msg:
            if isinstance(m, dict) and m.get("id") == want_id:
                return m
        return None
    return msg if isinstance(msg, dict) else None


class McpClient:
    def __init__(self, url=None, timeout=30):
        self.url = url or os.environ.get("MEGAJAM_MCP_URL", DEFAULT_URL)
        self.timeout = timeout
        self.session = None
        self._id = 0
        self._ready = False

    def _post(self, payload):
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(self.url, json.dumps(payload).encode(), headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                sid = r.headers.get("Mcp-Session-Id")
                if sid:
                    self.session = sid
                return _parse_body(r.read(), r.headers.get("Content-Type"), payload.get("id"))
        except urllib.error.HTTPError as e:
            raise McpError(f"HTTP {e.code} from {self.url}: {e.read()[:200].decode('utf-8', 'replace')}", EXIT_TOOL)
        except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
            # includes timeouts and IncompleteRead (editor killed mid-reply)
            raise McpError(f"cannot reach {self.url}: {type(e).__name__}: {e}", EXIT_CONN)
        except ValueError as e:  # non-JSON body
            raise McpError(f"unreadable reply from {self.url}: {e}", EXIT_CONN)

    def request(self, method, params=None):
        self._id += 1
        msg = self._post({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}})
        if msg is None:
            raise McpError(f"no reply carrying our request id for {method}", EXIT_CONN)
        if "error" in msg:
            err = msg["error"]
            detail = f"code {err.get('code')}: {err.get('message')}" if isinstance(err, dict) else str(err)
            raise McpError(f"{method} RPC error ({detail})", EXIT_TOOL)
        result = msg.get("result")
        if not isinstance(result, dict):
            raise McpError(f"{method}: reply has no object result ({result!r})", EXIT_CONN)
        return result

    def connect(self):
        if self._ready:
            return
        self.request("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                    "clientInfo": {"name": "megajam-mcp-call", "version": "1"}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self._ready = True

    def list_tools(self):
        self.connect()
        return self.request("tools/list").get("tools", [])

    def call(self, tool, args=None):
        """Return the tools/call result dict. Raises McpError if the tool reports isError."""
        self.connect()
        res = self.request("tools/call", {"name": tool, "arguments": args or {}})
        if res.get("isError"):
            raise McpError(f"tool {tool} failed: {json.dumps(res.get('content'))[:500]}")
        return res

    def save_all(self):
        return self.call(os.environ.get("MEGAJAM_MCP_SAVE_TOOL", DEFAULT_SAVE_TOOL))


def snapshot_commit(project, message=None):
    """git add -A and commit in the project. Returns the new short hash, or None if nothing changed."""
    def git(*a):
        return subprocess.run(["git", "-C", project, *a], capture_output=True, text=True)
    if git("rev-parse", "--git-dir").returncode != 0:
        raise McpError(f"{project} is not a git repository")
    # Pathspec "." keeps this to the project folder even when it sits inside a bigger repo.
    r = git("add", "-A", "--", ".")
    if r.returncode != 0:
        raise McpError(f"git add failed: {r.stderr.strip()}")
    if git("diff", "--cached", "--quiet", "--", ".").returncode == 0:
        return None
    msg = message or "snapshot: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    r = git("commit", "-q", "-m", msg, "--", ".")  # --only: files staged outside the project stay out
    if r.returncode != 0:
        raise McpError(f"git commit failed: {r.stderr.strip() or r.stdout.strip()}")
    return git("rev-parse", "--short", "HEAD").stdout.strip()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--url", default=None)
    p.add_argument("--timeout", type=float, default=30)
    sub = p.add_subparsers(dest="verb", required=True)
    c = sub.add_parser("call")
    c.add_argument("tool")
    c.add_argument("args", nargs="?", default="{}")
    sub.add_parser("list-tools")
    sub.add_parser("save-all")
    s = sub.add_parser("snapshot-commit")
    s.add_argument("--project", default=os.getcwd())
    s.add_argument("--message", default=None)
    a = p.parse_args(argv)
    cli = McpClient(a.url, a.timeout)
    try:
        if a.verb == "list-tools":
            for t in cli.list_tools():
                print(f"{t.get('name')}\t{(t.get('description') or '').splitlines()[0] if t.get('description') else ''}")
        elif a.verb == "call":
            raw = sys.stdin.read() if a.args == "-" else a.args
            try:
                args = json.loads(raw)
            except ValueError as e:
                print(f"bad JSON args: {e}", file=sys.stderr)
                return 2
            print(json.dumps(cli.call(a.tool, args), indent=2))
        elif a.verb == "save-all":
            cli.save_all()
            print("saved")
        elif a.verb == "snapshot-commit":
            h = snapshot_commit(a.project, a.message)
            print(f"committed {h}" if h else "nothing to commit")
    except McpError as e:
        print(f"mcp_call: {e}", file=sys.stderr)
        return e.exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main())
