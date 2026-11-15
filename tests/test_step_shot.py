import ast
import base64
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
import step_shot  # noqa: E402

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
PY_TOOL = {"name": "execute_python", "inputSchema": {"type": "object", "properties": {"code": {"type": "string"}}}}
SHOT_TOOL = {"name": "take_screenshot", "inputSchema": {"type": "object", "properties": {
    "filename": {"type": "string"}, "width": {"type": "integer"}, "height": {"type": "integer"}}}}
IMG_TOOL = {"name": "viewport_screenshot", "inputSchema": {"type": "object", "properties": {}}}


def script_params(code):
    line = next(l for l in code.splitlines() if l.startswith("PARAMS = "))
    return json.loads(ast.literal_eval(line[len("PARAMS = "):]))


class FakeEditor:
    """Fake MCP server. The python tool 'runs' the generated script by reading its PARAMS."""

    def __init__(self, tools, python_reply=None, write_png=True, image_reply=False, pie_running=True,
                 echo_source=False, bad_image=False, wrap=None, mime=False):
        self.tools, self.calls = tools, []
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
                m = msg["method"]
                if m == "initialize":
                    res = {"protocolVersion": "2025-03-26", "capabilities": {}}
                elif m == "tools/list":
                    res = {"tools": outer.tools}
                else:
                    name, args = msg["params"]["name"], msg["params"]["arguments"]
                    outer.calls.append((name, args))
                    text, content = "ok", None
                    if name == "execute_python":
                        code = args["code"]
                        p = script_params(code)
                        if "take_high_res_screenshot" in code:
                            if write_png:
                                with open(p["path"], "wb") as f:
                                    f.write(PNG)
                            text = "STEP_SHOT_OK queued"
                        else:
                            text = python_reply or "STEP_SHOT_OK framed Crate (1 match(es))"
                            if p.get("pie") and not pie_running:
                                text = "STEP_SHOT_ERROR PIE is not running (no game world)"
                    elif name == "take_screenshot":
                        with open(args["filename"], "wb") as f:
                            f.write(PNG)
                    elif name == "viewport_screenshot":
                        data = "abc" if bad_image else (base64.encodebytes(PNG * 20) if mime else base64.b64encode(PNG)).decode()
                        content = [{"type": "image", "data": data, "mimeType": "image/png"}]
                    if echo_source and name == "execute_python":
                        text = ">>> " + args["code"].replace("\n", "\n>>> ") + "\n" + text
                    if wrap == "json" and name == "execute_python":
                        text = json.dumps({"success": True, "output": text + "\n"})
                    elif wrap == "log" and name == "execute_python":
                        text = "\n".join("LogPython: " + l for l in text.splitlines())
                    res = {"content": content or [{"type": "text", "text": text}], "isError": False}
                body = json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": res}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.httpd = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/mcp"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = step_shot.main(list(argv))
        except SystemExit as e:  # argparse / usage helpers
            code = e.code if isinstance(e.code, int) else 2
            err.write(str(e.code))
    return code, out.getvalue().strip(), err.getvalue()


class CodeArgsTests(unittest.TestCase):
    """code_args: string on 5.8.4, CodeBlock on 5.9, and a flavor-following fallback when the schema is missing.
    NOTE: the 5.9 CodeBlock shape is INFERRED from engine source, not captured live; confirm in the 5.9 smoke."""

    class Cli:
        def __init__(self, flavor):
            self._f = flavor

        def flavor(self):
            return self._f

    BLOCK = {"type": "object", "properties": {"Content": {"type": "string"}, "Language": {"type": "string"}}}
    EXPECT59 = {"script": {"Content": "x=1", "Language": "Python"}}

    def test_schema_present_both_flavors(self):
        t58 = {"name": "execute_python", "inputSchema": {"properties": {"code": {"type": "string"}}}}
        t59 = {"name": "execute_python", "inputSchema": {"properties": {"script": self.BLOCK}}}
        self.assertEqual(step_shot.code_args(t58, "x=1", self.Cli("old")), {"code": "x=1"})
        self.assertEqual(step_shot.code_args(t59, "x=1", self.Cli("new")), self.EXPECT59)

    def test_missing_schema_follows_probed_flavor(self):
        for schema in (None, {}, {"properties": {}}):
            tool = {"name": "execute_python", **({"inputSchema": schema} if schema is not None else {})}
            self.assertEqual(step_shot.code_args(tool, "x=1", self.Cli("new")), self.EXPECT59)
            self.assertEqual(step_shot.code_args(tool, "x=1", self.Cli("old")), {"code": "x=1"})
            self.assertEqual(step_shot.code_args(tool, "x=1"), {"code": "x=1"})  # plain client: old behaviour

    def test_codeblock_needs_content_and_language_not_any_object(self):
        self.assertTrue(step_shot._is_codeblock(self.BLOCK))
        self.assertTrue(step_shot._is_codeblock({"$ref": "#/$defs/CodeBlock"}))
        self.assertFalse(step_shot._is_codeblock({"type": "object"}))
        self.assertFalse(step_shot._is_codeblock({"type": "object", "properties": {"x": {"type": "number"}}}))
        self.assertFalse(step_shot._is_codeblock({"$ref": "#/$defs/Vector"}))

    def test_unrelated_struct_param_is_not_a_python_tool(self):
        tool = {"name": "python_docs", "inputSchema": {"properties": {"source": {"type": "object"}}}}
        self.assertIsNone(step_shot.pick_python_tool([tool]))


class StepShotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "shots")
        self.servers = []

    def tearDown(self):
        for s in self.servers:
            s.close()
        self.tmp.cleanup()

    def editor(self, *a, **k):
        s = FakeEditor(*a, **k)
        self.servers.append(s)
        return s

    def shot(self, srv, *argv):
        return run("--url", srv.url, "--outdir", self.out, "--settle", "0", "--wait", "3", *argv)

    def steps(self):
        return open(os.path.join(self.out, "steps.md"), encoding="utf-8").read()

    def test_actor_shot_numbers_and_logs(self):
        srv = self.editor([PY_TOOL])
        code, out, err = self.shot(srv, "--label", "crate placed!", "--actor", "SM_Crate")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, os.path.abspath(os.path.join(self.out, "01-crate-placed.png")))
        self.assertTrue(os.path.isfile(out))
        code, out2, _ = self.shot(srv, "--label", "two", "--actor", "SM_Crate")
        self.assertTrue(out2.endswith("02-two.png"))
        rows = [l for l in self.steps().splitlines() if l.startswith("| 0")]
        self.assertEqual(len(rows), 2)
        self.assertIn("| 01 | crate-placed |", rows[0])
        self.assertTrue(rows[0].endswith("| (pending) |"))
        frame = json.loads(json.dumps(script_params(srv.calls[0][1]["code"])))
        self.assertEqual((frame["mode"], frame["actor"]), ("actor", "SM_Crate"))
        # two python calls per shot: frame, then shoot
        self.assertEqual([c[0] for c in srv.calls[:2]], ["execute_python"] * 2)

    def test_location_and_rotation_passed(self):
        srv = self.editor([PY_TOOL])
        code, _, err = self.shot(srv, "--label", "spawn", "--location", "0,0,300", "--rotation", "-20,90,0")
        self.assertEqual(code, 0, err)
        p = script_params(srv.calls[0][1]["code"])
        self.assertEqual((p["mode"], p["location"], p["rotation"]), ("location", [0, 0, 300], [-20, 90, 0]))

    def test_pie_does_not_move_camera(self):
        srv = self.editor([PY_TOOL])
        self.assertEqual(self.shot(srv, "--label", "play", "--pie")[0], 0)
        self.assertEqual(script_params(srv.calls[0][1]["code"])["mode"], "none")

    def test_verdict_with_shot_and_alone(self):
        srv = self.editor([PY_TOOL])
        self.shot(srv, "--label", "a", "--viewport", "--verdict", "good | clean")
        self.shot(srv, "--label", "b", "--viewport")
        code, out, _ = run("--outdir", self.out, "--verdict", "floor is\nmissing")  # no editor needed
        self.assertEqual(code, 0)
        rows = [l for l in self.steps().splitlines() if l.startswith("| 0")]
        self.assertTrue(rows[0].endswith("| good \\| clean |"))
        self.assertTrue(rows[1].endswith("| floor is missing |"))
        self.assertIn("02-b", out)

    def test_verdict_without_steps_fails(self):
        code, _, err = run("--outdir", self.out, "--verdict", "x")
        self.assertEqual(code, 2)
        self.assertIn("take a shot first", err)

    def test_numbering_continues_after_existing_files(self):
        os.makedirs(self.out)
        open(os.path.join(self.out, "07-old.png"), "wb").close()
        srv = self.editor([PY_TOOL])
        _, out, _ = self.shot(srv, "--label", "n", "--viewport")
        self.assertTrue(out.endswith("08-n.png"))

    def test_dedicated_tool_with_path_arg(self):
        srv = self.editor([SHOT_TOOL])
        code, out, err = self.shot(srv, "--label", "v", "--viewport")
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.basename(srv.calls[0][1]["filename"]).startswith(".pending-01-v-"))
        self.assertTrue(out.endswith("01-v.png") and os.path.isfile(out))
        self.assertEqual(srv.calls[0][1]["width"], 1920)

    def test_dedicated_tool_returning_image(self):
        srv = self.editor([IMG_TOOL])
        code, out, err = self.shot(srv, "--label", "v", "--viewport")
        self.assertEqual(code, 0, err)
        self.assertEqual(open(out, "rb").read(), PNG)

    def test_framing_without_python_tool_is_clear_error(self):
        srv = self.editor([SHOT_TOOL])
        code, _, err = self.shot(srv, "--label", "v", "--actor", "X")
        self.assertEqual(code, 2)
        self.assertIn("needs a Python tool", err)
        self.assertFalse(os.path.exists(os.path.join(self.out, "steps.md")))

    def test_no_usable_tool(self):
        srv = self.editor([{"name": "save_all"}])
        code, _, err = self.shot(srv, "--label", "v", "--viewport")
        self.assertEqual(code, 2)
        self.assertIn("--list-tools", err)

    def test_editor_reports_error(self):
        srv = self.editor([PY_TOOL], python_reply="STEP_SHOT_ERROR no actor named 'Nope'")
        code, _, err = self.shot(srv, "--label", "v", "--actor", "Nope")
        self.assertEqual(code, 1)
        self.assertIn("no actor named", err)
        self.assertIn("| FAILED: ", self.steps())  # logged, so numbering and the log stay in step

    def test_python_tool_ran_nothing(self):
        srv = self.editor([PY_TOOL], python_reply="some other output")
        code, _, err = self.shot(srv, "--label", "v", "--actor", "X")
        self.assertEqual(code, 1)
        self.assertIn("did not report STEP_SHOT_OK", err)

    def test_png_never_appears(self):
        srv = self.editor([PY_TOOL], write_png=False)
        code, _, err = run("--url", srv.url, "--outdir", self.out, "--settle", "0", "--wait", "0.5",
                           "--label", "v", "--viewport")
        self.assertEqual(code, 1)
        self.assertIn("no PNG appeared", err)
        self.assertIn("| (no file) | FAILED: ", self.steps())

    def test_late_png_from_failed_attempt_is_not_accepted_by_retry(self):
        srv = self.editor([PY_TOOL], write_png=False)
        run("--url", srv.url, "--outdir", self.out, "--settle", "0", "--wait", "0.3", "--label", "crate", "--viewport")
        # attempt 1's editor finally writes its PNG, to the name it was given
        late = next(c for c in srv.calls if "take_high_res_screenshot" in c[1]["code"])
        with open(script_params(late[1]["code"])["path"], "wb") as f:
            f.write(b"STALE")
        code, out, err = run("--url", srv.url, "--outdir", self.out, "--settle", "0", "--wait", "0.3",
                             "--label", "crate", "--viewport")
        self.assertEqual(code, 1, err)  # retry's own editor call produced nothing
        self.assertFalse(any(f.startswith("02-") for f in os.listdir(self.out)))

    def test_failed_shot_gets_row_and_verdict_targets_it(self):
        srv = self.editor([PY_TOOL])
        self.shot(srv, "--label", "a", "--viewport", "--verdict", "good")
        srv.tools = [{"name": "save_all"}]
        failing = self.editor([PY_TOOL], python_reply="STEP_SHOT_ERROR boom")
        self.shot(failing, "--label", "b", "--viewport")
        self.assertEqual(run("--outdir", self.out, "--verdict", "level missing")[0], 0)
        rows = [l for l in self.steps().splitlines() if l.startswith("| 0")]
        self.assertTrue(rows[0].endswith("| good |"))
        self.assertTrue(rows[1].endswith("| level missing |"))

    def test_verdict_does_not_overwrite_judged_row(self):
        srv = self.editor([PY_TOOL])
        self.shot(srv, "--label", "a", "--viewport", "--verdict", "crate sits on floor")
        code, _, err = run("--outdir", self.out, "--verdict", "other")
        self.assertEqual(code, 2)
        self.assertIn("--replace", err)
        self.assertIn("crate sits on floor", self.steps())
        self.assertEqual(run("--outdir", self.out, "--verdict", "changed my mind", "--replace")[0], 0)
        self.assertIn("changed my mind", self.steps())

    def test_pie_not_running_is_an_error(self):
        srv = self.editor([PY_TOOL], pie_running=False)
        code, _, err = self.shot(srv, "--label", "p", "--pie")
        self.assertEqual(code, 1)
        self.assertIn("PIE is not running", err)

    def test_pie_without_python_tool_shoots_and_says_unchecked(self):
        # Real editor has no Python tool: the shot is taken, and the output admits PIE was not verified.
        srv = self.editor([SHOT_TOOL])
        code, out, err = self.shot(srv, "--label", "p", "--pie")
        self.assertEqual(code, 0, err)
        self.assertIn("PIE state UNCHECKED", err)

    def test_bad_arguments_exit_2_without_editor(self):
        for argv in (["--label", "x", "--location", "1,2"], ["--label", "!!!", "--viewport"],
                     ["--label", "x", "--location", "1,2,3", "--rotation", "a"]):
            code, _, err = run("--url", "http://127.0.0.1:9/mcp", "--outdir", self.out, *argv)
            self.assertEqual(code, 2, argv)
            self.assertNotIn("cannot reach", err)

    def test_echoed_source_is_not_mistaken_for_a_marker(self):
        srv = self.editor([PY_TOOL], echo_source=True)
        code, _, err = self.shot(srv, "--label", "e", "--viewport")
        self.assertEqual(code, 0, err)
        srv = self.editor([PY_TOOL], python_reply="nothing here", echo_source=True)  # echo only, never ran
        self.assertEqual(self.shot(srv, "--label", "e2", "--viewport")[0], 1)

    def test_docs_tool_named_python_is_not_the_python_tool(self):
        docs = {"name": "search_python_api_docs", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}}
        self.assertIsNone(step_shot.pick_python_tool([docs]))
        srv = self.editor([docs, SHOT_TOOL])
        code, out, err = self.shot(srv, "--label", "v", "--viewport")
        self.assertEqual(code, 0, err)
        self.assertEqual(srv.calls[0][0], "take_screenshot")

    def test_refused_screenshot_falls_back_to_console_command(self):
        self.assertIn("is False", step_shot.SHOOT_SCRIPT)
        self.assertIn("HighResShot", step_shot.SHOOT_SCRIPT)

    def test_empty_verdict_is_a_usage_error(self):
        srv = self.editor([PY_TOOL])
        self.shot(srv, "--label", "a", "--viewport")
        for v in ("", "   "):
            self.assertEqual(run("--outdir", self.out, "--verdict", v)[0], 2)
        self.assertIn("(pending)", self.steps())

    def test_bad_base64_image_is_a_failed_row_not_a_traceback(self):
        srv = self.editor([IMG_TOOL], bad_image=True)
        code, _, err = self.shot(srv, "--label", "b", "--viewport")
        self.assertEqual(code, 1)
        self.assertIn("base64", err)
        self.assertIn("| FAILED: ", self.steps())
        self.assertEqual([f for f in os.listdir(self.out) if f.startswith(".pending")], [])

    def test_numbering_past_999_via_steps_md(self):
        os.makedirs(self.out)
        step_shot.append_row(self.out, 1000, "x", "(no file)", "FAILED: x")
        srv = self.editor([PY_TOOL])
        _, out, _ = self.shot(srv, "--label", "n", "--viewport")
        self.assertTrue(out.endswith("1001-n.png"))

    def test_date_and_epoch_named_files_are_not_shots(self):
        os.makedirs(self.out)
        for n in ("20261108-devlog.png", "1731100000-cap.png", "1080-reference.png"):
            open(os.path.join(self.out, n), "wb").close()
        srv = self.editor([PY_TOOL])
        _, out, _ = self.shot(srv, "--label", "n", "--viewport")
        self.assertTrue(out.endswith("01-n.png"))

    def test_markers_inside_json_or_log_wrappers(self):
        for wrap in ("json", "log"):
            out = os.path.join(self.out, wrap)
            srv = self.editor([PY_TOOL], wrap=wrap, echo_source=(wrap == "log"))
            code, _, err = run("--url", srv.url, "--outdir", out, "--settle", "0", "--wait", "3",
                               "--label", "w", "--actor", "SM_Crate")
            self.assertEqual(code, 0, f"{wrap}: {err}")
        err_srv = self.editor([PY_TOOL], python_reply="STEP_SHOT_ERROR no actor named 'Nope'", wrap="json")
        code, _, err = run("--url", err_srv.url, "--outdir", self.out, "--label", "w", "--actor", "Nope")
        self.assertEqual(code, 1)
        self.assertIn("no actor named 'Nope'", err)

    def test_mime_wrapped_base64_image(self):
        srv = self.editor([IMG_TOOL], mime=True)
        code, out, err = self.shot(srv, "--label", "m", "--viewport")
        self.assertEqual(code, 0, err)
        self.assertEqual(open(out, "rb").read(), PNG * 20)

    def test_name_fallback_python_tool_with_other_code_arg_names(self):
        for props in ({"py_script": {"type": "string"}}, {"code": {"type": ["string", "null"]}}):
            t = {"name": "unreal_python", "inputSchema": {"type": "object", "properties": props}}
            self.assertIs(step_shot.pick_python_tool([t]), t)
            self.assertEqual(step_shot.code_key(t), next(iter(props)))

    def test_dated_files_do_not_hijack_numbering(self):
        os.makedirs(self.out)
        for n in ("2026-11-08-notes.md", "2026-11-08-devlog.png"):
            open(os.path.join(self.out, n), "wb").close()
        srv = self.editor([PY_TOOL])
        _, out, _ = self.shot(srv, "--label", "n", "--viewport")
        self.assertTrue(out.endswith("01-n.png"))

    def test_editor_down(self):
        code, _, err = run("--url", "http://127.0.0.1:9/mcp", "--outdir", self.out, "--timeout", "2",
                           "--label", "v", "--viewport")
        self.assertEqual(code, 2)
        self.assertIn("cannot reach", err)

    def test_usage_errors(self):
        self.assertEqual(run("--outdir", self.out)[0], 2)
        # a label alone now means "shoot the viewport" (not a usage error), so it reaches for the editor:
        # point it at a dead port, or it talks to whatever listens on the real :8010
        dead = "http://127.0.0.1:9/mcp"
        self.assertEqual(run("--outdir", self.out, "--label", "x", "--url", dead)[0], 2)
        self.assertEqual(run("--outdir", self.out, "--verdict", "v", "--pie")[0], 2)

    def test_list_tools(self):
        srv = self.editor([PY_TOOL, SHOT_TOOL, {"name": "other"}])
        code, out, _ = run("--url", srv.url, "--list-tools")
        self.assertEqual(code, 0)
        self.assertIn("execute_python (code arg: code)", out)
        self.assertIn("take_screenshot", out)

    def test_generated_scripts_are_valid_python(self):
        p = {"mode": "actor", "actor": "a'b\"c", "path": "/x", "width": 1, "height": 1, "game_view": True,
             "distance": None, "azimuth": 1, "elevation": 1, "location": None, "rotation": [0, 0, 0]}
        for t in (step_shot.FRAME_SCRIPT, step_shot.SHOOT_SCRIPT):
            code = step_shot.render(t, p)
            ast.parse(code)
            self.assertEqual(script_params(code)["actor"], "a'b\"c")

    def test_script_returns_marker_as_last_expression_for_59(self):
        """5.9 execute_python returns only returnValue (no stdout): the script must end with the markers as a value."""
        import ast
        import types
        for t, marker in ((step_shot.FRAME_SCRIPT, "STEP_SHOT_OK"), (step_shot.SHOOT_SCRIPT, "STEP_SHOT_OK")):
            code = step_shot.render(t, {"actor": None, "pie": False, "location": None, "look_at": None,
                                        "width": 8, "height": 8, "path": "/x.png", "game_view": False})
            tree = ast.parse(code)
            self.assertIsInstance(tree.body[-1], ast.Expr)  # the value 5.9 hands back
            fake = types.ModuleType("unreal")
            sys.modules["unreal"] = fake
            try:
                scope = {}
                exec(compile(ast.Module(tree.body[:-1], []), "s", "exec"), scope)  # noqa: S102
                scope["_ok"]("done")
                value = eval(compile(ast.Expression(tree.body[-1].value), "s", "eval"), scope)  # noqa: S307
            finally:
                del sys.modules["unreal"]
            self.assertIn(marker + " done", value)

    def test_59_returnvalue_error_reply_is_reported(self):
        srv = self.editor([PY_TOOL], python_reply=json.dumps({"returnValue": "STEP_SHOT_ERROR no actor named 'Nope'"}))
        code, _, err = run("--url", srv.url, "--outdir", self.out, "--settle", "0", "--wait", "3",
                           "--label", "r", "--actor", "Nope")
        self.assertEqual(code, 1, err)
        self.assertIn("no actor named", err)
        self.assertIn("| FAILED: ", self.steps())

    def test_59_returnvalue_reply_is_read(self):
        srv = self.editor([PY_TOOL], python_reply='{"returnValue":"STEP_SHOT_OK framed Crate (1 match(es))"}')
        code, _, err = run("--url", srv.url, "--outdir", self.out, "--settle", "0", "--wait", "3",
                           "--label", "r", "--actor", "SM_Crate")
        self.assertEqual(code, 0, err)
        self.assertNotIn("falling back", err)


if __name__ == "__main__":
    unittest.main()
