import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import mx  # noqa: E402

TS = "editor_toolset.toolsets.actor.ActorTools"
PY = "editor_toolset.toolsets.python.PythonTools"
DESCRIBE = {"tools": [
    {"name": "find_actors", "description": "Find actors", "inputSchema": {
        "type": "object", "required": ["tag"], "properties": {"tag": {}, "limit": {}}}},
    {"name": "big", "description": "returns a lot", "inputSchema": {"type": "object", "properties": {}}},
]}


class FakeEditor:
    """Fake MCP endpoint with the 3 top-level tools. Records every call_tool."""

    def __init__(self):
        self.calls = []
        self.meta = []  # names the top-level tools/list reports ([] = a 5.8.4-style server)
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if "id" not in msg:
                    self.send_response(202)
                    self.end_headers()
                    return
                if msg["method"] == "initialize":
                    res = {"protocolVersion": "2025-03-26", "capabilities": {}}
                elif msg["method"] == "tools/call":
                    name, args = msg["params"]["name"], msg["params"]["arguments"]
                    outer.calls.append((name, args))
                    text, err = outer.top(name, args)
                    res = {"content": [{"type": "text", "text": text}], "isError": err}
                elif msg["method"] == "tools/list":
                    res = {"tools": [{"name": n} for n in outer.meta]}
                else:
                    res = {}
                data = json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": res}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.httpd = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/mcp"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def top(self, name, args):
        if name == "list_toolsets":
            return json.dumps({"toolsets": [TS, "editor_toolset.toolsets.asset.AssetTools", PY]}), False
        if name == "describe_toolset":
            if "toolset_name" not in args:
                return "x" * 5000 + " missing toolset_name", True
            if args["toolset_name"] == PY:
                return json.dumps({"tools": [{"name": "execute_python", "inputSchema": {
                    "type": "object", "required": ["code"], "properties": {"code": {"type": "string"}}}}]}), False
            return json.dumps(DESCRIBE), False
        if name == "call_tool":
            if args["tool_name"] == "big":
                return "B" * 5000, False
            if args["tool_name"] == "find_actors" and "tag" not in args["arguments"]:
                return "schema error " + "E" * 11000, True
            return json.dumps({"returnValue": True}), False
        return "unknown", True

    def close(self):
        self.httpd.shutdown()


def run(url, sd, *argv):
    out, err = io.StringIO(), io.StringIO()
    os.environ["MX_DIR"] = sd
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = mx.main(["--url", url, *argv])
    return rc, out.getvalue(), err.getvalue()


class MxTests(unittest.TestCase):
    def setUp(self):
        self.ed = FakeEditor()
        self.tmp = tempfile.TemporaryDirectory()
        self.sd = os.path.join(self.tmp.name, "mx")

    def tearDown(self):
        self.ed.close()
        self.tmp.cleanup()

    def test_call_caps_output_and_saves_full(self):
        save = os.path.join(self.tmp.name, "full.txt")
        rc, out, _ = run(self.ed.url, self.sd, "call", TS, "big", "--save", save)
        self.assertEqual(rc, 0)
        self.assertLess(len(out), 1000)
        self.assertIn("chars cut", out)
        self.assertEqual(open(save).read(), "B" * 5000)

    def test_call_sends_toolset_name_tool_name_arguments(self):
        run(self.ed.url, self.sd, "call", TS, "set_label", '{"a": 1}')
        self.assertEqual(self.ed.calls[-1], ("call_tool", {"toolset_name": TS, "tool_name": "set_label", "arguments": {"a": 1}}))

    def test_error_capped_with_required_params_from_describe(self):
        rc, out, err = run(self.ed.url, self.sd, "call", TS, "find_actors", "{}")
        self.assertEqual(rc, 1)
        # 300-char body + cut note + the params line; count only mx's own lines (stray
        # ResourceWarnings from other tests' sockets can be garbage-collected into stderr)
        mx_err = "\n".join(l for l in err.splitlines() if l.startswith("mx:") or l.startswith("required:"))
        self.assertLess(len(mx_err), 800)
        self.assertIn("required: tag", err)
        # the cache lives in a per-editor-URL folder under MX_DIR
        self.assertTrue(os.path.exists(os.path.join(mx.url_state_dir(self.ed.url), "describe", TS + ".json")))

    def test_describe_cached_and_only_excerpts_printed(self):
        rc, out, _ = run(self.ed.url, self.sd, "describe", TS)
        self.assertEqual(rc, 0)
        self.assertIn("find_actors", out)
        n = len(self.ed.calls)
        rc, out, _ = run(self.ed.url, self.sd, "describe", TS, "--grep", "limit")
        self.assertEqual(len(self.ed.calls), n, "second describe must come from the cache")
        self.assertIn("limit", out)
        run(self.ed.url, self.sd, "describe", TS, "--refresh")
        self.assertEqual(len(self.ed.calls), n + 1)

    def test_describe_uses_toolset_name_param(self):
        run(self.ed.url, self.sd, "describe", TS)
        self.assertEqual(self.ed.calls[0], ("describe_toolset", {"toolset_name": TS}))

    def test_short_toolset_name_resolves_after_toolsets(self):
        run(self.ed.url, self.sd, "toolsets")
        run(self.ed.url, self.sd, "call", "ActorTools", "set_label", "{}")
        self.assertEqual(self.ed.calls[-1][1]["toolset_name"], TS)

    def test_session_budget_describe_plus_10_calls_under_10k(self):
        total = 0
        rc, out, err = run(self.ed.url, self.sd, "describe", TS)
        total += len(out) + len(err)
        for i in range(10):
            rc, out, err = run(self.ed.url, self.sd, "call", TS, "big" if i % 2 else "find_actors", "{}")
            total += len(out) + len(err)
        self.assertLess(total, 10000)

    def test_save_calls_save_assets_with_empty_args(self):
        rc, out, _ = run(self.ed.url, self.sd, "save")
        self.assertEqual(rc, 0)
        self.assertEqual(self.ed.calls[-1][1]["tool_name"], "save_assets")
        self.assertEqual(self.ed.calls[-1][1]["arguments"], {"asset_paths": []})

    def test_failed_describes_are_cached_not_repeated(self):
        class Prose(FakeEditor):
            def top(self, name, args):
                if name == "list_toolsets":
                    return json.dumps({"toolsets": [TS], "note": "e.g. Engine.Actor, unreal.EditorLevelLibrary"}), False
                if name == "describe_toolset" and args["toolset_name"] != TS:
                    return "unknown toolset", True
                return super().top(name, args)
        ed = Prose()
        try:
            cli = mx.ProxyClient(ed.url, 30, self.sd)
            for _ in range(3):
                cli.list_tools()
            bogus = [c for c in ed.calls if c[0] == "call_tool" or c[0] == "describe_toolset"]
            failed = [c for c in bogus if c[1].get("toolset_name") not in (TS,)]
            self.assertEqual(len(failed), 3)  # e.g, Engine.Actor, unreal.EditorLevelLibrary: once each
        finally:
            ed.close()

    def test_proxy_lists_tools_from_every_toolset(self):
        cli = mx.ProxyClient(self.ed.url, 30, self.sd)
        names = [t["name"] for t in cli.list_tools()]
        self.assertIn("execute_python", names)  # python toolset sorts after ActorTools
        self.assertIn("find_actors", names)     # and an earlier toolset's tools are still there

    def test_bad_json_is_usage_error(self):
        rc, _, err = run(self.ed.url, self.sd, "call", TS, "x", "{nope")
        self.assertEqual(rc, 2)
        self.assertIn("bad JSON", err)

    def test_unreachable_editor_exits_2(self):
        rc, _, err = run("http://127.0.0.1:1/mcp", self.sd, "call", TS, "x", "{}")
        self.assertEqual(rc, 2)
        self.assertLess(len(err), 500)

    def test_shot_rejects_unknown_option(self):
        rc, _, err = run(self.ed.url, self.sd, "shot", "lbl", '{"bogus": 1}')
        self.assertEqual(rc, 2)
        self.assertIn("unknown shot option", err)

    def test_shot_finds_python_tool_inside_toolsets_and_routes_via_call_tool(self):
        cli = mx.ProxyClient(self.ed.url, 30, self.sd)
        names = [t["name"] for t in cli.list_tools()]
        self.assertIn("execute_python", names)
        cli.call("execute_python", {"code": "print(1)"})
        self.assertEqual(self.ed.calls[-1], ("call_tool", {"toolset_name": PY, "tool_name": "execute_python",
                                                           "arguments": {"code": "print(1)"}}))

    def test_shot_with_no_tool_reports_in_toolset_terms(self):
        class Empty(FakeEditor):
            def top(self, name, args):
                return "{}", False  # no toolsets at all, like the reviewer's fake server
        ed = Empty()
        try:
            rc, _, err = run(ed.url, self.sd, "shot", "crate", '{"viewport": true}')
        finally:
            ed.close()
        self.assertEqual(rc, 2)
        self.assertIn("inside the editor's toolsets", err)
        self.assertNotIn("tools/list", err)

    def test_max_chars_zero_means_no_cap_for_grep(self):
        run(self.ed.url, self.sd, "describe", TS)
        rc, out, _ = run(self.ed.url, self.sd, "--max-chars", "0", "describe", TS, "--grep", "find_actors")
        self.assertIn("find_actors", out)

    def test_options_accepted_after_subcommand(self):
        rc, out, _ = run(self.ed.url, self.sd, "call", TS, "big", "{}", "--max-chars", "50")
        self.assertEqual(rc, 0)
        self.assertLess(len(out), 120)
        rc, out, _ = run("http://127.0.0.1:1/mcp", self.sd, "call", TS, "big", "{}", "--url", self.ed.url)
        self.assertEqual(rc, 0)  # the later --url wins over the unreachable one

    def test_help_carries_gotchas(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit):
            mx.main(["--help"])
        h = buf.getvalue()
        for needle in ("toolset_name", "bool, int, float, Vector", "8010", "exec_tool_script only calls toolset tools"):
            self.assertIn(needle, h)


PS59 = "PythonScriptingTools"
CODEBLOCK = {"type": "object", "properties": {"Content": {"type": "string"}, "Language": {"type": "string"}}}


# NOTE: every UE 5.9 fixture below (describe_toolsets/list_toolsets payloads, the CodeBlock schema) is INFERRED
# from the engine source, not captured from a live 5.9 editor. Replace with recorded payloads once the live
# smoke of this branch confirms the shapes.
class Ue59Editor(FakeEditor):
    """UE 5.9 shape: tools/list shows describe_toolsets / describe_tools (no describe_toolset), undotted toolset
    names, and execute_python takes a CodeBlock. Unknown top-level tools (describe_toolset) are errors."""

    def __init__(self):
        super().__init__()
        self.meta = ["list_toolsets", "describe_toolsets", "describe_tools", "call_tool"]

    def top(self, name, args):
        if name == "list_toolsets":
            return json.dumps({"toolsets": [{"name": PS59, "description": "py"}]}), False
        if name == "describe_toolsets":
            if args.get("toolset_names") != [PS59] or args.get("include_schemas") is not True:
                return json.dumps({"toolsets": {}, "errors": {str(args.get("toolset_names")): "unknown"}}), False
            return json.dumps({"toolsets": {PS59: {"tools": [{"name": "execute_python", "description": "run", "inputSchema": {
                "type": "object", "required": ["script"], "properties": {"script": CODEBLOCK}}}]}}, "errors": {}}), False
        if name == "call_tool":
            return json.dumps({"returnValue": 42}), False
        return "Unknown tool " + name, True


class Ue59Tests(unittest.TestCase):
    def setUp(self):
        self.ed = Ue59Editor()
        self.tmp = tempfile.TemporaryDirectory()
        self.sd = os.path.join(self.tmp.name, "mx")

    def tearDown(self):
        self.ed.close()
        self.tmp.cleanup()

    def test_describe_uses_describe_toolsets_with_schemas(self):
        rc, out, _ = run(self.ed.url, self.sd, "describe", PS59)
        self.assertEqual(rc, 0)
        self.assertEqual(self.ed.calls[0], ("describe_toolsets", {"toolset_names": [PS59], "include_schemas": True}))
        self.assertNotIn("describe_toolset", [c[0] for c in self.ed.calls])
        self.assertIn("execute_python", out)

    def test_unknown_toolset_in_errors_map_is_a_tool_error(self):
        rc, out, err = run(self.ed.url, self.sd, "describe", "NoSuchTools")
        self.assertEqual(rc, 1)
        self.assertIn("unknown", err)

    def test_toolsets_lists_undotted_names(self):
        rc, out, _ = run(self.ed.url, self.sd, "toolsets")
        self.assertEqual(rc, 0)
        self.assertIn(PS59, out)

    def test_py_sends_a_codeblock(self):
        rc, out, _ = run(self.ed.url, self.sd, "py", "1+41")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.ed.calls[-1], ("call_tool", {"toolset_name": PS59, "tool_name": "execute_python", "arguments": {
            "script": {"Content": "1+41", "Language": "Python"}}}))
        self.assertIn("42", out)

    def test_save_on_59_saves_all_dirty_through_editor_python(self):
        # 5.9 renamed AssetTools to AssetToolset and it only has save_asset (one path): save-all goes via editor Python.
        rc, out, _ = run(self.ed.url, self.sd, "save")
        self.assertEqual(rc, 0, out)
        name, args = self.ed.calls[-1]
        self.assertEqual((name, args["toolset_name"], args["tool_name"]), ("call_tool", PS59, "execute_python"))
        self.assertEqual(args["arguments"], {"script": {"Content": mx.SAVE_PY_59, "Language": "Python"}})
        self.assertIn("save_dirty_packages(True, True)", mx.SAVE_PY_59)
        self.assertNotIn("asset.AssetTools", json.dumps(self.ed.calls))

    def test_save_on_59_reports_false_as_failure(self):
        self.ed.top = lambda name, args: (json.dumps({"returnValue": False}), False) if name == "call_tool" else \
            Ue59Editor.top(self.ed, name, args)
        rc, out, _ = run(self.ed.url, self.sd, "save")
        self.assertEqual(rc, 1)
        self.assertIn("mx: ERROR", out)

    def test_old_server_py_still_sends_a_string(self):
        ed = FakeEditor()
        try:
            rc, _, _ = run(ed.url, self.sd + "-old", "py", "print(1)")
        finally:
            ed.close()
        self.assertEqual(rc, 0)
        self.assertEqual(ed.calls[-1][1]["arguments"], {"code": "print(1)"})


class FlavorSwitchTests(unittest.TestCase):
    """Both engines serve the same URL: a cache written by one must not be trusted by the other."""

    def setUp(self):
        self.ed = Ue59Editor()
        self.tmp = tempfile.TemporaryDirectory()
        self.sd = os.path.join(self.tmp.name, "mx")
        mx._FLAVORS.clear()

    def tearDown(self):
        self.ed.close()
        self.tmp.cleanup()
        mx._FLAVORS.clear()

    def test_switch_59_to_58_on_the_same_url_drops_the_cache(self):
        rc, out, _ = run(self.ed.url, self.sd, "toolsets")
        self.assertEqual(rc, 0)
        self.assertIn(PS59, out)
        self.ed.meta = []  # the same port now answers as a 5.8.4 editor
        mx._FLAVORS.clear()  # a new process
        rc, out, _ = run(self.ed.url, self.sd, "toolsets")
        self.assertEqual(rc, 0)
        self.assertEqual(self.ed.calls[-1][0], "list_toolsets")  # re-listed, not served from the 5.9 cache
        self.assertEqual(self.ed.calls.count(("list_toolsets", {})), 2)

    def test_switch_58_to_59_drops_cached_describe(self):
        # A describe cache with no marker, or the wrong one, is wiped on the next probe.
        root = os.path.join(self.tmp.name, "stamped")
        os.environ["MX_DIR"] = root
        sd = mx.url_state_dir(self.ed.url)
        os.makedirs(os.path.join(sd, "describe"))
        open(os.path.join(sd, "describe", PS59 + ".json"), "w").write("OLD 5.8 TEXT")
        open(os.path.join(sd, "flavor"), "w").write("old")
        rc, out, _ = run(self.ed.url, root, "describe", PS59)
        self.assertEqual(rc, 0)
        self.assertNotIn("OLD 5.8 TEXT", out)
        self.assertIn("execute_python", out)
        self.assertEqual(open(os.path.join(sd, "flavor")).read(), "new")

    def test_tools_list_error_is_retried_then_raised_not_guessed_old(self):
        n = {"c": 0}

        class Cli(mx.McpClient):
            def request(c, method, params=None):
                if method == "tools/list":
                    n["c"] += 1
                    raise mx.McpError("tools/list blew up", 1)
                return super().request(method, params)
        cli = Cli(self.ed.url, 5)
        with self.assertRaises(mx.McpError):
            mx.describe_flavor(cli)
        self.assertEqual(n["c"], 2)
        self.assertNotIn("describe_toolset", [c[0] for c in self.ed.calls])

    def test_flavor_probed_once_per_url_across_clients(self):
        n = {"c": 0}

        class Cli(mx.McpClient):
            def request(c, method, params=None):
                n["c"] += method == "tools/list"
                return super().request(method, params)
        for _ in range(3):
            self.assertEqual(mx.describe_flavor(Cli(self.ed.url, 5)), "new")
        self.assertEqual(n["c"], 1)


PNG_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
SLATE = "SlateInspectorToolset.SlateInspectorToolset"
APP = "EditorAppToolset.EditorAppToolset"
SCHEMAS = {
    SLATE: [{"name": SLATE + ".Screenshot", "description": "Screenshot a widget", "inputSchema": {
        "type": "object", "required": ["ref"], "properties": {"ref": {"type": "string"}}}}],
    APP: [{"name": APP + ".CaptureViewport", "description": "Capture the viewport", "inputSchema": {
        "type": "object", "required": ["captureTransform"], "properties": {
            "captureTransform": {"type": "object", "properties": {
                "location": {"type": "object"}, "rotation": {"type": "object"}, "scale": {"type": "object"}}},
            "annotations": {"type": "object"}, "bShowUI": {"type": "boolean"}}}}],
}


class RealShapeEditor(FakeEditor):
    """Only what the real UE 5.8 editor exposes for shots: the 3 meta tools, Slate Screenshot and
    CaptureViewport. NO python tool. Like the real server, call_tool takes the BARE tool name and rejects a
    toolset-prefixed one with 'Unknown tool <toolset>.<name>'."""

    def top(self, name, args):
        if name == "list_toolsets":
            return json.dumps({"toolsets": [SLATE, APP]}), False
        if name == "describe_toolset":
            return json.dumps({"tools": SCHEMAS[args["toolset_name"]]}), False
        if name == "call_tool":
            ts, tool, a = args["toolset_name"], args["tool_name"], args["arguments"]
            if tool == "Screenshot" and ts == SLATE and a == {"ref": ""}:
                return PNG_B64, False
            if tool == "CaptureViewport" and "annotations" not in a:  # exact text the real editor gives
                return 'CaptureViewport input param "annotations" needs a default value', True
            if tool == "CaptureViewport" and ts == APP and "captureTransform" in a:
                return json.dumps({"image": PNG_B64}), False
            return f"Unknown tool {ts}.{tool} or bad arguments {a}", True
        return "unknown", True


class PieEditor(RealShapeEditor):
    """Real shape plus EditorAppToolset.IsPIERunning (no args), as the real editor has it."""
    running = False

    def top(self, name, args):
        if name == "describe_toolset" and args["toolset_name"] == APP:
            tools = SCHEMAS[APP] + [{"name": APP + ".IsPIERunning", "description": "Is PIE running",
                                     "inputSchema": {"type": "object"}}]
            return json.dumps({"tools": tools}), False
        if name == "call_tool" and args["tool_name"] == "IsPIERunning":
            return json.dumps({"returnValue": self.running}), False
        return super().top(name, args)


class PieReplyShapeTests(unittest.TestCase):
    def test_reply_shapes_the_real_editor_may_send(self):
        import step_shot
        def res(*texts):
            return {"content": [{"type": "text", "text": t} for t in texts]}
        yes = [res('{"returnValue":true}'), res('Result: {"returnValue":true}'),
               res("Calling IsPIERunning", '{"returnValue":true}'), res('{"returnValue": true}'), res("true")]
        no = [res('{"returnValue":false}'), res('Result: {"returnValue":false}'), res("false")]
        for r in yes:
            self.assertTrue(step_shot.pie_running(r), r)
        for r in no:
            self.assertFalse(step_shot.pie_running(r), r)


class StaleCacheTests(unittest.TestCase):
    def test_standalone_cache_is_keyed_by_editor_url(self):
        import step_shot
        with tempfile.TemporaryDirectory() as d:
            os.environ["MX_DIR"] = d
            a = step_shot.make_client("http://127.0.0.1:8010/mcp", 5).sd
            b = step_shot.make_client("http://127.0.0.1:8011/mcp", 5).sd
            self.assertNotEqual(a, b)
            self.assertTrue(a.startswith(d) and b.startswith(d))

    def test_env_selected_editor_gets_its_own_cache(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ["MX_DIR"] = d
            try:
                os.environ["MEGAJAM_MCP_URL"] = "http://127.0.0.1:7001/mcp"
                a = mx.url_state_dir(None)
                os.environ["MEGAJAM_MCP_URL"] = "http://127.0.0.1:7002/mcp"
                b = mx.url_state_dir(None)
            finally:
                os.environ.pop("MEGAJAM_MCP_URL", None)
            self.assertNotEqual(a, b)
            self.assertEqual(mx.url_state_dir("http://127.0.0.1:7002/mcp"), b)

    def test_mx_shot_does_not_trust_another_editors_cache(self):
        a, b = RealShapeEditor(), FakeEditor()  # b lists nothing and has no toolsets
        try:
            with tempfile.TemporaryDirectory() as d:
                out = os.path.join(d, "o")
                rc, _, err = run(a.url, d, "shot", "x", json.dumps({"outdir": out}))
                self.assertEqual(rc, 0, err)  # cache now exists for editor A
                rc, _, err = run(b.url, d, "shot", "x", json.dumps({"outdir": out}))
                self.assertNotEqual(rc, 0)
                self.assertIn(("list_toolsets",), [(c[0],) for c in b.calls])  # B was asked, A's cache not used
                self.assertFalse([c for c in b.calls if c[0] == "call_tool" and c[1].get("tool_name") == "Screenshot"])
        finally:
            a.close()
            b.close()

    def test_old_negative_cache_is_retried(self):
        with tempfile.TemporaryDirectory() as d:
            ed = RealShapeEditor()
            try:
                sd = os.path.join(d, "mx")
                os.makedirs(os.path.join(sd, "describe"))
                bad = os.path.join(sd, "describe", mx.safe_name(SLATE) + ".fail")
                open(bad, "w").close()
                old = os.path.getmtime(bad) - 3600
                os.utime(bad, (old, old))  # written an hour ago, e.g. while the editor was loading
                names = [t["name"] for t in mx.ProxyClient(ed.url, 30, sd).list_tools()]
            finally:
                ed.close()
            self.assertIn(SLATE + ".Screenshot", names)


class PieCheckTests(unittest.TestCase):
    def shot_pie(self, running):
        ed = PieEditor()
        ed.running = running
        with tempfile.TemporaryDirectory() as d:
            try:
                rc, out, err = run(ed.url, os.path.join(d, "mx"), "shot", "p",
                                   json.dumps({"pie": True, "outdir": os.path.join(d, "o")}))
            finally:
                ed.close()
        return rc, err, [c[1]["tool_name"] for c in ed.calls if c[0] == "call_tool"]

    def test_pie_not_running_is_refused_without_a_shot(self):
        rc, err, tools = self.shot_pie(False)
        self.assertEqual(rc, 1)
        self.assertIn("PIE is not running", err)
        self.assertNotIn("Screenshot", tools)

    def test_pie_running_is_checked_and_shot(self):
        rc, err, tools = self.shot_pie(True)
        self.assertEqual(rc, 0, err)
        self.assertIn("checked with IsPIERunning", err)
        self.assertNotIn("UNCHECKED", err)


class RealEditorShotTests(unittest.TestCase):
    def setUp(self):
        self.ed = RealShapeEditor()
        self.tmp = tempfile.TemporaryDirectory()
        self.sd = os.path.join(self.tmp.name, "mx")
        self.out = os.path.join(self.tmp.name, "shots")

    def tearDown(self):
        self.ed.close()
        self.tmp.cleanup()

    def shot(self, opts):
        opts = dict(opts, outdir=self.out)
        return run(self.ed.url, self.sd, "shot", "lbl", json.dumps(opts))

    def png_path(self, out):
        path = out.strip().splitlines()[-1]
        with open(path, "rb") as f:
            self.assertTrue(f.read().startswith(b"\x89PNG\r\n\x1a\n"))
        return path

    def test_qualified_name_is_sent_bare_with_ref(self):
        cli = mx.ProxyClient(self.ed.url, 30, self.sd)
        tools = cli.list_tools()
        self.assertIn(SLATE + ".Screenshot", [t["name"] for t in tools])
        cli.call(SLATE + ".Screenshot", {"ref": ""})  # the exact doubled-name case that failed live
        self.assertEqual(self.ed.calls[-1], ("call_tool", {"toolset_name": SLATE, "tool_name": "Screenshot",
                                                           "arguments": {"ref": ""}}))

    def test_viewport_shot_saves_decoded_png(self):
        rc, out, err = self.shot({"viewport": True})
        self.assertEqual(rc, 0, err)
        self.png_path(out)
        self.assertEqual(self.ed.calls[-1][1]["tool_name"], "Screenshot")
        self.assertIn("window shot", err)

    def test_location_shot_uses_capture_viewport_with_transform(self):
        rc, out, err = self.shot({"location": "10,20,300", "rotation": "-20,90,0"})
        self.assertEqual(rc, 0, err)
        self.png_path(out)
        name, args = self.ed.calls[-1]
        self.assertEqual(args["tool_name"], "CaptureViewport")
        a = args["arguments"]
        # the verified real shape: location / rotation{pitch,yaw,roll} / scale; no annotations (it is an object)
        self.assertEqual(a["captureTransform"], {"location": {"x": 10.0, "y": 20.0, "z": 300.0},
                                                 "rotation": {"pitch": -20.0, "yaw": 90.0, "roll": 0.0},
                                                 "scale": {"x": 1, "y": 1, "z": 1}})
        self.assertEqual(a["annotations"], {})  # required by the real editor; the fake rejects a call without it
        self.assertFalse(a["bShowUI"])
        self.assertIn("NOT moved", err)

    def test_pie_shot_is_taken_and_says_pie_unchecked(self):
        rc, out, err = self.shot({"pie": True})
        self.assertEqual(rc, 0, err)
        self.png_path(out)
        self.assertIn("PIE state UNCHECKED", err)

    def test_no_target_means_viewport_shot(self):
        rc, out, err = run(self.ed.url, self.sd, "shot", "lbl", "--outdir", self.out)
        self.assertEqual(rc, 0, err)
        self.assertTrue(self.png_path(out).startswith(self.out))  # --outdir flag works
        self.assertEqual(self.ed.calls[-1][1]["tool_name"], "Screenshot")

    def test_width_height_ignored_is_said_out_loud(self):
        for opts in ({"viewport": True}, {"location": "0,0,500", "rotation": "-90,-90,0"}):
            rc, out, err = self.shot(dict(opts, width=1280, height=720))
            self.assertEqual(rc, 0, err)
            self.assertIn("width/height not supported by", err)
        rc, out, err = self.shot({"viewport": True})  # defaults: no noise
        self.assertNotIn("width/height", err)

    def test_help_lists_the_modes(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit):
            mx.main(["shot", "--help"])
        for needle in ("viewport", "location", "pie", "does NOT start PIE", "--outdir", "900x640"):
            self.assertIn(needle, buf.getvalue())

    def test_standalone_step_shot_uses_the_toolset_route(self):
        # top-level tools/list holds only the 3 meta-tools, like the real editor
        import step_shot
        os.environ["MX_DIR"] = self.sd
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(err):
            rc = step_shot.main(["--url", self.ed.url, "--outdir", self.out, "--label", "s",
                                 "--location", "0,0,500", "--rotation", "-90,-90,0"])
        self.assertEqual(rc, 0, err.getvalue())
        self.png_path(out.getvalue())
        self.assertEqual(self.ed.calls[-1][1]["tool_name"], "CaptureViewport")
        self.assertEqual(self.ed.calls[-1][1]["arguments"]["annotations"], {})

    def test_actor_mode_explains_it_needs_a_location(self):
        rc, _, err = self.shot({"actor": "SM_Crate"})
        self.assertEqual(rc, 2)
        self.assertIn("--location", err)
        self.assertFalse([c for c in self.ed.calls if c[0] == "call_tool" and c[1]["tool_name"] != "x"
                          and c[1]["tool_name"] in ("Screenshot", "CaptureViewport")])



class UnwrapReturn(unittest.TestCase):
    # mock jam 15: `mx.py py` printed {"returnValue":"5.9.0-0+UE5"}; print the value itself
    def test_unwraps_only_a_bare_return_value(self):
        self.assertEqual(mx.unwrap_return('{"returnValue":"5.9.0-0+UE5"}'), "5.9.0-0+UE5")
        self.assertEqual(mx.unwrap_return('{"returnValue":[1,2]}'), "[1, 2]")
        self.assertEqual(mx.unwrap_return('{"returnValue":true}'), "true")
        self.assertEqual(mx.unwrap_return('{"returnValue":1,"output":"x"}'), '{"returnValue":1,"output":"x"}')
        self.assertEqual(mx.unwrap_return("STEP_SHOT_OK plain text"), "STEP_SHOT_OK plain text")


class BulletToolsetNames(unittest.TestCase):
    # mock jam 15: 5.9 list_toolsets is a bullet list; dotted words in the prose (AGENTS.md, e.g.)
    # were described as toolsets and fail-cached. Only the bullet names count.
    TEXT = ("- EditorToolset.ActorToolset: Spawn actors. See AGENTS.md and CLAUDE.md, e.g. csv.bin.\n"
            "  Pins are NodeName.PinName.\n"
            "- editor_toolset.toolsets.python_scripting.PythonScriptingTools: Run Python.\n"
            "* BlueprintToolsets.BlueprintDslToolset : DSL, e.g. BlueprintDslToolset.Write\n")

    def test_bullet_names_only(self):
        self.assertEqual(mx.names_in(self.TEXT), [
            "BlueprintToolsets.BlueprintDslToolset", "EditorToolset.ActorToolset",
            "editor_toolset.toolsets.python_scripting.PythonScriptingTools"])

    def test_no_bullets_keeps_old_scan(self):
        self.assertEqual(mx.names_in("toolsets: EditorToolset.ActorToolset, UMG.UMGToolSet"),
                         ["EditorToolset.ActorToolset", "UMG.UMGToolSet"])

    def test_listed_toolsets_new_flavor_non_json(self):
        self.assertNotIn("AGENTS.md", mx.listed_toolsets(self.TEXT, "new"))


if __name__ == "__main__":
    unittest.main()
