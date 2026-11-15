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
sys.path.insert(0, os.path.join(ROOT, "tests"))
import force_save_level  # noqa: E402

PY_TOOL = {"name": "execute_python", "inputSchema": {"type": "object", "properties": {"code": {"type": "string"}}}}
MAGIC = bytes.fromhex("c1832a9e")


class FakeEditor:
    """Fake MCP server holding an in-memory level and a real .umap file on disk.

    mode: "good"      forced save writes the new level to disk (what we want)
          "stale"     forced save reports success but never writes (the mock jam 10 bug)
          "same"      forced save rewrites the old bytes (mtime moves, content does not)
          "badmagic"  forced save writes junk that is not a package
          "lossy"     file is written, but the reload loses an actor
          "error"     the save script prints FORCE_SAVE_ERROR
    """

    def __init__(self, umap, mode="good", actors=("Floor", "Player", "Beacon"), wrap=None, echo=False,
                 asset_mode="good", external=0, ext_mode="good", notes=None, unknown=False, reload_level=None):
        """asset_mode "stale": --asset saves report success but write nothing.
        external=N: N actors live in <umap dir>/__ExternalActors__; ext_mode "stale" never writes them."""
        self.umap, self.mode, self.wrap, self.echo = umap, mode, wrap, echo
        self.asset_mode, self.external, self.ext_mode = asset_mode, external, ext_mode
        self.notes, self.unknown, self.reload_level = notes or [], unknown, reload_level
        self.ext_dir = os.path.join(os.path.dirname(umap), "__ExternalActors__")
        self.version = 0
        for i in range(external):
            os.makedirs(self.ext_dir, exist_ok=True)
            with open(os.path.join(self.ext_dir, f"a{i}.uasset"), "wb") as f:
                f.write(b"old actor")
        self.labels = list(actors)
        self.calls = []
        self.params = []
        outer = self
        with open(umap, "wb") as f:
            f.write(MAGIC + b"old level")

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
                    res = {"tools": [PY_TOOL]}
                else:
                    code = msg["params"]["arguments"]["code"]
                    text = outer.run(code)
                    if outer.echo:
                        text = ">>> " + code.replace("\n", "\n>>> ") + "\n" + text
                    if outer.wrap == "json":
                        text = json.dumps({"success": True, "output": text + "\n"})
                    res = {"content": [{"type": "text", "text": text}], "isError": False}
                body = json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": res}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.httpd = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/mcp"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def run(self, code):
        line = next(l for l in code.splitlines() if l.startswith("PARAMS = "))
        import ast
        self.params.append(json.loads(ast.literal_eval(line[len("PARAMS = "):])))
        if "save_loaded_asset" in code:  # only the save script calls it (_COMMON names mark_package_dirty)
            self.calls.append("save")
            if self.mode == "error":
                return "FORCE_SAVE_ERROR RuntimeError: disk full"
            if self.mode == "good":
                self.write(MAGIC + b"new level " + ",".join(self.labels).encode())
            elif self.mode == "same":
                self.write(MAGIC + b"old level")
            elif self.mode == "badmagic":
                self.write(b"junk-not-a-package")
            elif self.mode == "lossy":
                self.write(MAGIC + b"lossy")
            self.version += 1
            if self.asset_mode == "good":
                for a in self.params[-1]["assets"]:
                    self.write(self.asset_file(a), b"asset v%d" % self.version)
            if self.ext_mode == "good":
                for i in range(self.external):
                    self.write(os.path.join(self.ext_dir, f"a{i}.uasset"), b"actor v%d" % self.version)
            notes = ["asset not saved: " + a for a in self.params[-1]["assets"]] if self.asset_mode == "lying" else []
            notes += self.notes
            return "FORCE_SAVE_OK " + json.dumps({"level": "/Game/Maps/L_Main", "actors": len(self.labels), "notes": notes})
        if "new_level" in code:
            self.calls.append("reload")
            labels = self.labels[:-1] if self.mode == "lossy" else self.labels
            return "FORCE_SAVE_OK " + json.dumps({"level": self.reload_level or "/Game/Maps/L_Main",
                                                  "actors": len(labels), "labels": labels})
        self.calls.append("probe")
        files = {}
        for a in self.params[-1]["assets"]:
            f = self.asset_file(a)
            if not os.path.exists(f):
                with open(f, "wb") as fh:
                    fh.write(b"old asset")
            files[a] = f
        warn = ("FORCE_SAVE_ERROR Actor.is_package_external is missing in this build (AttributeError)\n"
                if self.unknown else "")
        return warn + "FORCE_SAVE_OK " + json.dumps({
            "external_unknown": self.unknown,
            "level": "/Game/Maps/L_Main", "open_level": "/Game/Maps/L_Main", "file": self.umap,
            "actors": len(self.labels), "labels": self.labels, "asset_files": files,
            "external_actors": self.external, "external_dir": self.ext_dir if self.external else None})

    def asset_file(self, name):
        return os.path.join(os.path.dirname(self.umap), os.path.basename(name) + ".uasset")

    def write(self, path, data=None):
        if data is None:  # level file
            path, data = self.umap, path
        # Make sure mtime strictly moves even on coarse filesystems.
        before = os.stat(path).st_mtime_ns
        with open(path, "wb") as f:
            f.write(data)
        if os.stat(path).st_mtime_ns <= before:
            os.utime(path, ns=(before + 10**9, before + 10**9))

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = force_save_level.main(list(argv))
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 2
    return code, out.getvalue().strip(), err.getvalue()


class ForceSaveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.umap = os.path.join(self.tmp.name, "L_Main.umap")
        self.servers = []

    def tearDown(self):
        for s in self.servers:
            s.close()
        self.tmp.cleanup()

    def editor(self, **k):
        s = FakeEditor(self.umap, **k)
        self.servers.append(s)
        return s

    def go(self, srv, *argv):
        return run("--url", srv.url, "--settle", "0.3", *argv)

    def test_good_save_is_verified(self):
        srv = self.editor()
        code, out, err = self.go(srv, "--expect-actor", "Beacon")
        self.assertEqual(code, 0, err)
        self.assertIn("VERIFIED /Game/Maps/L_Main", out)
        self.assertEqual(srv.calls, ["probe", "save", "reload"])
        with open(self.umap, "rb") as f:
            self.assertIn(b"new level", f.read())

    def test_stale_save_is_caught(self):
        """The mock jam 10 bug: editor says saved, file never changes."""
        srv = self.editor(mode="stale")
        code, out, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("NOT VERIFIED", err)
        self.assertIn("mtime did not move", err)
        self.assertNotIn("reload", srv.calls)  # never trusted the editor, never reached the reload

    def test_same_bytes_is_caught(self):
        srv = self.editor(mode="same")
        code, _, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("identical", err)

    def test_same_bytes_allowed_on_request(self):
        srv = self.editor(mode="same")
        code, _, err = self.go(srv, "--allow-unchanged")
        self.assertEqual(code, 0, err)

    def test_bad_header_is_caught(self):
        srv = self.editor(mode="badmagic")
        code, _, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("package header", err)

    def test_reload_missing_actor_is_caught(self):
        srv = self.editor(mode="lossy")
        code, _, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("after reload the level has 2 actors, expected 3", err)

    def test_expected_actor_missing(self):
        srv = self.editor()
        code, _, err = self.go(srv, "--expect-actor", "Crate", "--expect-actor", "Beacon")
        self.assertEqual(code, 1)
        self.assertIn("missing: Crate", err)
        self.assertNotIn("Beacon,", err)

    def test_editor_error_marker(self):
        srv = self.editor(mode="error")
        code, _, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("disk full", err)

    def test_missing_file_after_save(self):
        srv = self.editor(mode="stale")
        os.remove(self.umap)
        code, _, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("no file", err)

    def test_json_wrapped_and_echoed_reply(self):
        srv = self.editor(wrap="json", echo=True)
        code, out, err = self.go(srv)
        self.assertEqual(code, 0, err)

    def test_assets_and_level_passed_to_editor(self):
        srv = self.editor()
        code, _, err = self.go(srv, "--level", "/Game/Maps/L_Main", "--asset", "/Game/UI/WBP_HUD")
        self.assertEqual(code, 0, err)
        self.assertTrue(all("level" not in p for p in srv.params))  # the editor never gets a level to navigate to
        self.assertEqual(srv.params[1]["assets"], ["/Game/UI/WBP_HUD"])

    def test_asset_saved_is_verified_on_disk(self):
        srv = self.editor()
        code, out, err = self.go(srv, "--asset", "/Game/UI/WBP_HUD")
        self.assertEqual(code, 0, err)
        self.assertIn("1 asset(s)", out)

    def test_asset_lying_save_is_not_verified(self):
        srv = self.editor(asset_mode="lying")
        code, out, err = self.go(srv, "--asset", "/Game/UI/WBP_HUD")
        self.assertEqual(code, 1)
        self.assertIn("asset not saved: /Game/UI/WBP_HUD", err)
        self.assertNotIn("VERIFIED", out)
        self.assertNotIn("reload", srv.calls)

    def test_allow_unchanged_still_needs_a_write(self):
        """Mock-10 bug with --allow-unchanged: nothing written. Must fail and must not reload (it would drop edits)."""
        srv = self.editor(mode="stale")
        code, out, err = self.go(srv, "--allow-unchanged")
        self.assertEqual(code, 1)
        self.assertIn("mtime did not move", err)
        self.assertNotIn("reload", srv.calls)

    def test_allow_unchanged_asset_not_written_fails(self):
        srv = self.editor(asset_mode="stale")
        code, _, err = self.go(srv, "--asset", "/Game/UI/WBP_HUD", "--allow-unchanged")
        self.assertEqual(code, 1)
        self.assertIn("WBP_HUD.uasset", err)
        self.assertNotIn("reload", srv.calls)

    def test_editor_note_is_fatal(self):
        """Any 'returned False' note fails the run even if the file looks written."""
        srv = self.editor(notes=["save_current_level returned False"])
        code, out, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("returned False", err)
        self.assertNotIn("reload", srv.calls)

    def test_unknown_external_api_hashes_folder_anyway(self):
        srv = self.editor(external=2, ext_mode="stale", unknown=True)
        code, out, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("__ExternalActors__", err)
        self.assertNotIn("reload", srv.calls)

    def test_unknown_external_api_good_save_warns(self):
        srv = self.editor(external=2, unknown=True)
        code, out, err = self.go(srv)
        self.assertEqual(code, 0, err)
        self.assertIn("warning from editor: Actor.is_package_external is missing", out)

    def test_reload_names_another_level(self):
        srv = self.editor(reload_level="/Game/Maps/L_Other")
        code, _, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("expected /Game/Maps/L_Main", err)

    # Real script text, run against a stub `unreal` module.
    def test_reload_script_fails_when_new_level_fails(self):
        import stub_unreal
        mem = [stub_unreal.Actor(n) for n in ("Floor", "Player", "NewEditNotOnDisk")]
        state = {"world": stub_unreal.World("/Game/Maps/L_Main", mem), "new_level_ok": False,
                 "levels": {"/Game/Maps/L_Main": [stub_unreal.Actor("Floor")]}}
        out = stub_unreal.run(force_save_level.render(force_save_level.RELOAD_SCRIPT, {"assets": []}), state)
        self.assertIn("FORCE_SAVE_ERROR new_level failed", out)
        self.assertNotIn("FORCE_SAVE_OK", out)

    def test_reload_script_ok_rereads_level(self):
        import stub_unreal
        mem = [stub_unreal.Actor(n) for n in ("Floor", "Unsaved")]
        state = {"world": stub_unreal.World("/Game/Maps/L_Main", mem),
                 "levels": {"/Game/Maps/L_Main": [stub_unreal.Actor("Floor")]}}
        out = stub_unreal.run(force_save_level.render(force_save_level.RELOAD_SCRIPT, {"assets": []}), state)
        self.assertIn("FORCE_SAVE_OK", out)
        self.assertNotIn("Unsaved", out)

    def test_probe_script_missing_external_api_is_loud(self):
        import stub_unreal
        acts = [stub_unreal.Actor(n, has_external_api=False, external=True) for n in ("Floor", "Player")]
        state = {"world": stub_unreal.World("/Game/Maps/L_Main", acts), "levels": {}}
        out = stub_unreal.run(force_save_level.render(force_save_level.PROBE_SCRIPT, {"assets": []}), state)
        self.assertIn("FORCE_SAVE_ERROR Actor.is_package_external is missing", out)
        self.assertIn('"external_unknown": true', out)
        self.assertIn('"external_actors": 2', out)
        self.assertIn("FORCE_SAVE_OK", out)  # warning, not fatal: the host keeps going

    def test_probe_script_without_package_name_59(self):
        # mock jam 15: "AttributeError: module 'unreal' has no attribute 'PackageName'" on UE 5.9
        import stub_unreal
        acts = [stub_unreal.Actor(n) for n in ("Floor", "Player")]
        state = {"world": stub_unreal.World("/Game/Maps/L_Main", acts), "levels": {}, "no_package_name": True}
        out = stub_unreal.run(force_save_level.render(force_save_level.PROBE_SCRIPT, {"assets": []}), state)
        self.assertNotIn("PackageName", out)
        self.assertIn("/proj/Content/Maps/L_Main.umap", out)
        self.assertIn("FORCE_SAVE_OK", out)

    def test_level_other_than_open_is_rejected(self):
        srv = self.editor()
        code, out, err = self.go(srv, "--level", "/Game/Maps/L_Other")
        self.assertEqual(code, 1)
        self.assertIn("not the open level", err)
        self.assertEqual(srv.calls, ["probe"])  # nothing saved, nothing reloaded

    def test_level_equal_to_open_is_accepted(self):
        srv = self.editor()
        code, _, err = self.go(srv, "--level", "/Game/Maps/L_Main")
        self.assertEqual(code, 0, err)

    def test_quoted_actor_label_in_wrapped_reply(self):
        srv = self.editor(wrap="json", actors=("Floor", 'Sign "Exit" \\ x', "Beacon"))
        code, _, err = self.go(srv, "--expect-actor", 'Sign "Exit" \\ x')
        self.assertEqual(code, 0, err)

    def test_external_actors_saved_is_verified(self):
        srv = self.editor(external=2)
        code, out, err = self.go(srv)
        self.assertEqual(code, 0, err)
        self.assertIn("2 external actor files", out)

    def test_external_actors_not_on_disk_blocks_and_never_reloads(self):
        """One File Per Actor: the .umap changes, the actor files do not. Must not reload (it would discard edits)."""
        srv = self.editor(external=2, ext_mode="stale")
        code, out, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("__ExternalActors__", err)
        self.assertNotIn("VERIFIED", out)
        self.assertNotIn("reload", srv.calls)

    def test_external_files_missing_for_actor_count(self):
        srv = self.editor(external=2, ext_mode="stale")
        for f in os.listdir(srv.ext_dir)[:1]:
            os.remove(os.path.join(srv.ext_dir, f))
        code, _, err = self.go(srv)
        self.assertEqual(code, 1)
        self.assertIn("holds 1 files", err)
        self.assertNotIn("reload", srv.calls)

    def test_umap_override(self):
        srv = self.editor()
        other = os.path.join(self.tmp.name, "elsewhere.umap")
        code, _, err = self.go(srv, "--umap", other)
        self.assertEqual(code, 1)  # editor wrote self.umap, the override file was never created
        self.assertIn("no file", err)

    def test_unreachable_editor_is_exit_2(self):
        code, _, err = run("--url", "http://127.0.0.1:1/mcp", "--timeout", "1")
        self.assertEqual(code, 2)

    def test_list_tools(self):
        srv = self.editor()
        code, out, _ = run("--url", srv.url, "--list-tools")
        self.assertEqual(code, 0)
        self.assertIn("execute_python", out)

    def test_reload_scratch_name_is_fresh_each_run(self):
        """UE's new_level returns False when a package already exists at the path, so a fixed scratch name
        would make every second run fail with 'new_level failed'."""
        import stub_unreal
        on_disk, orig = set(), stub_unreal.make

        def ue_like_make(state):
            u = orig(state)
            ls = u.get_editor_subsystem(u.LevelEditorSubsystem)

            def new_level(path):
                if path in on_disk:
                    return False
                on_disk.add(path)
                state["world"] = stub_unreal.World(path, [])
                return True
            ls.new_level = new_level
            return u

        script = force_save_level.render(force_save_level.RELOAD_SCRIPT, {"assets": []})
        stub_unreal.make = ue_like_make
        try:
            for _ in range(2):
                state = {"world": stub_unreal.World("/Game/Maps/L_Main", [stub_unreal.Actor("Floor")]),
                         "levels": {"/Game/Maps/L_Main": [stub_unreal.Actor("Floor")]}}
                self.assertIn("FORCE_SAVE_OK", stub_unreal.run(script, state))
        finally:
            stub_unreal.make = orig

    def test_verify_only_after_hand_copy(self):
        """Doc escalation step 2: the .umap was copied by hand before the run, so no mtime can move during it."""
        srv = self.editor(mode="stale")
        with open(self.umap, "wb") as f:
            f.write(MAGIC + b"new level Floor,Player,Beacon")
        code, out, err = self.go(srv, "--verify-only", "--expect-actor", "Beacon")
        self.assertEqual(code, 0, err)
        self.assertIn("VERIFIED", out)
        self.assertEqual(srv.calls, ["probe", "reload"])  # no save was attempted

    def test_verify_only_needs_expect_actor(self):
        srv = self.editor()
        code, _, err = self.go(srv, "--verify-only")
        self.assertEqual(code, 2)
        self.assertIn("--expect-actor", err)

    def test_verify_only_rejects_bad_header_and_missing_actor(self):
        srv = self.editor(mode="stale")
        with open(self.umap, "wb") as f:
            f.write(b"junk-not-a-package")
        code, _, err = self.go(srv, "--verify-only", "--expect-actor", "Beacon")
        self.assertEqual(code, 1)
        self.assertIn("package header", err)
        with open(self.umap, "wb") as f:
            f.write(MAGIC + b"x")
        code, _, err = self.go(srv, "--verify-only", "--expect-actor", "NoSuchActor")
        self.assertEqual(code, 1)
        self.assertIn("NoSuchActor", err)

    def test_unwrap_empty_output_does_not_hide_returnvalue(self):
        self.assertEqual(force_save_level.unwrap('{"output":"","returnValue":"FORCE_SAVE_OK x"}'), "FORCE_SAVE_OK x")
        self.assertEqual(force_save_level.unwrap('{"output":"","result":"","text":"T"}'), "T")
        self.assertEqual(force_save_level.unwrap('{"output":"real","returnValue":"other"}'), "real")

    def test_unwrap_59_returnvalue(self):
        self.assertEqual(force_save_level.unwrap('{"returnValue":"FORCE_SAVE_OK {}\\nx"}'), "FORCE_SAVE_OK {}\nx")
        self.assertIn("_OUT.append", force_save_level._COMMON)


if __name__ == "__main__":
    unittest.main()


class EditorScripts59(unittest.TestCase):
    # mock jam 16, first live run on UE 5.9: Package has no mark_package_dirty, and execute_python
    # rejects "imports must be at the top level of the script"
    SCRIPTS = ("SAVE_SCRIPT", "RELOAD_SCRIPT")

    def test_no_import_inside_a_function(self):
        for name in self.SCRIPTS:
            for line in getattr(force_save_level, name).splitlines():
                if line.lstrip().startswith(("import ", "from ")):
                    self.assertEqual(line, line.lstrip(), f"{name}: nested import {line!r}")

    def test_save_never_calls_mark_package_dirty_directly(self):
        body = force_save_level.SAVE_SCRIPT.split("def run():", 1)[1]
        self.assertNotIn("mark_package_dirty", body)
        self.assertIn("_dirty(", body)
        self.assertIn("obj.modify(True)", force_save_level.SAVE_SCRIPT)
