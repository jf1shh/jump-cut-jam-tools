import contextlib
import io
import json
import os
import re
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import ue_import_asset as uia  # noqa: E402
from mcp_call import McpError  # noqa: E402


def text_result(text):
    return {"content": [{"type": "text", "text": text}]}


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = uia.main(argv)
        except SystemExit as e:  # argparse usage error
            rc = e.code
    return rc, out.getvalue(), err.getvalue()


class ArgHandling(unittest.TestCase):
    def test_wav_needs_no_type(self):
        a = uia._parse_cli_args(["--wav", "a.wav", "--dest", "/Game/Audio/", "--name", "Jump"])
        self.assertEqual((a.wav, a.glb, a.live, a.type), ("a.wav", None, False, None))

    def test_glb_still_needs_type(self):
        rc, _, err = run_main(["--glb", "a.glb", "--dest", "/Game/Props/", "--name", "Crate"])
        self.assertEqual(rc, 2)
        self.assertIn("--type is required", err)

    def test_glb_args_unchanged(self):
        a = uia._parse_cli_args(["--glb", "a.glb", "--dest", "/Game/Props/", "--name", "Crate", "--type", "prop"])
        self.assertEqual((a.glb, a.type, a.require_pbr), ("a.glb", "prop", True))

    def test_live_rejects_glb(self):
        rc, _, err = run_main(["--live", "--glb", "a.glb", "--dest", "/Game/P/", "--name", "C", "--type", "prop"])
        self.assertEqual(rc, 2)
        self.assertIn("audio only", err)

    def test_glb_and_wav_together_rejected(self):
        rc, _, _ = run_main(["--glb", "a.glb", "--wav", "a.wav", "--dest", "/Game/", "--name", "X"])
        self.assertEqual(rc, 2)

    def test_one_source_required(self):
        rc, _, _ = run_main(["--dest", "/Game/", "--name", "X"])
        self.assertEqual(rc, 2)

    def test_wav_must_be_wav(self):
        rc, _, err = run_main(["--wav", "a.mp3", "--dest", "/Game/", "--name", "X"])
        self.assertEqual(rc, 2)
        self.assertIn(".wav", err)

    def test_wav_with_type_rejected(self):
        rc, _, _ = run_main(["--wav", "a.wav", "--dest", "/Game/", "--name", "X", "--type", "prop"])
        self.assertEqual(rc, 2)


class EditorOpenRefusal(unittest.TestCase):
    def test_headless_refuses_when_editor_open(self):
        with mock.patch.object(uia, "editor_open_reason", return_value="an Unreal editor is already running (pid 42)"):
            rc, out, err = run_main(["--wav", "a.wav", "--dest", "/Game/Audio/", "--name", "Jump"])
        self.assertEqual(rc, uia.EXIT_REFUSED)
        self.assertIn("refusing to run headless", err)
        self.assertIn("pid 42", err)
        self.assertIn("--live", err)  # tells the user the way out

    def test_headless_glb_refuses_too(self):
        with mock.patch.object(uia, "editor_open_reason", return_value="editor open"):
            with mock.patch.object(uia, "import_asset") as imp:
                rc, _, _ = run_main(["--glb", "a.glb", "--dest", "/Game/P/", "--name", "C", "--type", "prop"])
        self.assertEqual(rc, uia.EXIT_REFUSED)
        imp.assert_not_called()

    def test_headless_runs_when_no_editor(self):
        with mock.patch.object(uia, "editor_open_reason", return_value=None):
            with mock.patch.object(uia, "import_sound") as imp:
                rc, _, _ = run_main(["--wav", "a.wav", "--dest", "/Game/Audio/", "--name", "Jump"])
        self.assertEqual(rc, 0)
        imp.assert_called_once_with("a.wav", "/Game/Audio/", "Jump")

    def test_live_does_not_consult_the_probe(self):
        with mock.patch.object(uia, "editor_open_reason", side_effect=AssertionError("probed")):
            with mock.patch.object(uia, "live_import_sound", return_value="/Game/Audio/S_Jump"):
                rc, out, _ = run_main(["--live", "--project", "/p", "--wav", "a.wav", "--dest", "/Game/Audio/",
                                       "--name", "Jump"])
        self.assertEqual(rc, 0)
        self.assertIn("Created /Game/Audio/S_Jump", out)

    def test_probe_finds_a_fake_editor_process(self):
        procs = {"4242": ["/opt/UE/Engine/Binaries/Linux/UnrealEditor", "/p/Mock.uproject", "-nosplash"],
                 "4243": ["/usr/bin/vim", "notes.txt"],
                 "4244": ["/opt/UE/UnrealEditor", "/p/Other.uproject"]}
        with mock.patch.object(uia.os, "listdir", return_value=list(procs)), \
                mock.patch.object(uia, "_read_cmdline", side_effect=lambda pid: procs.get(str(pid), [])), \
                mock.patch.object(uia, "_ancestor_pids", return_value={1}):
            self.assertEqual([p for p, _ in uia.editor_processes()], [4242, 4244])
            self.assertEqual([p for p, _ in uia.editor_processes("/p/Mock.uproject")], [4242])
            self.assertEqual(uia.editor_processes("/p/None.uproject"), [])
            self.assertIn("pid 4242", uia.editor_open_reason("/p/Mock.uproject"))
        with mock.patch.object(uia.os, "listdir", return_value=["4243"]), \
                mock.patch.object(uia, "_read_cmdline", return_value=["/usr/bin/vim"]), \
                mock.patch.object(uia, "_ancestor_pids", return_value={1}):
            self.assertIsNone(uia.editor_open_reason())


class LiveCli(unittest.TestCase):
    def test_live_needs_project(self):
        rc, _, err = run_main(["--live", "--wav", "a.wav", "--dest", "/Game/A/", "--name", "X"])
        self.assertEqual(rc, 2)
        self.assertIn("--project", err)

    def test_main_live_prints_asset_and_maps_errors(self):
        args = ["--live", "--project", "/p", "--wav", "a.wav", "--dest", "/Game/A/", "--name", "X"]
        with mock.patch.object(uia, "live_import_sound", side_effect=uia.LiveError("boom", 2)):
            rc, _, err = run_main(args)
        self.assertEqual(rc, 2)
        self.assertIn("boom", err)
        with mock.patch.object(uia, "live_import_sound", return_value="/Game/A/S_X") as m:
            rc, out, _ = run_main(args)
        self.assertEqual((rc, out.strip()), (0, "Created /Game/A/S_X"))
        self.assertEqual(m.call_args.args[3], "/p")


class InEditorImport(unittest.TestCase):
    """import_sound against a fake `unreal` module (the same code the live editor runs)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.wav = os.path.join(self.tmp.name, "jump.wav")
        open(self.wav, "wb").close()
        self.saved, self.task = [], None

        class SoundWave:
            pass

        class Task:
            def __init__(s):
                s.props = {}
                s.props["imported_object_paths"] = ["/Game/Audio/S_Jump.S_Jump"]

            def set_editor_property(s, k, v):
                s.props[k] = v

            def get_editor_property(s, k):
                return s.props.get(k)

        outer = self
        tools = types.SimpleNamespace(import_asset_tasks=lambda tasks: setattr(outer, "task", tasks[0]))
        lib = types.SimpleNamespace(load_asset=lambda p: SoundWave(), save_asset=lambda p: outer.saved.append(p))
        self.fake = types.SimpleNamespace(
            AssetImportTask=Task, SoundWave=SoundWave, EditorAssetLibrary=lib,
            AssetToolsHelpers=types.SimpleNamespace(get_asset_tools=lambda: tools))

    def test_imports_and_saves_prefixed_soundwave(self):
        with mock.patch.object(uia, "unreal", self.fake), contextlib.redirect_stdout(io.StringIO()):
            got = uia.import_sound(self.wav, "/Game/Audio", "Jump")
        self.assertEqual(got, "/Game/Audio/S_Jump")
        self.assertEqual(self.saved, ["/Game/Audio/S_Jump"])
        self.assertEqual(self.task.props["destination_name"], "S_Jump")
        self.assertTrue(self.task.props["automated"])  # no dialog in a live editor

    def test_no_soundwave_raises(self):
        self.fake.EditorAssetLibrary.load_asset = lambda p: object()
        with mock.patch.object(uia, "unreal", self.fake):
            with self.assertRaises(RuntimeError):
                uia.import_sound(self.wav, "/Game/Audio/", "Jump")

    def test_ogg_imports_headless(self):
        # UE 5.9 smoke test: a plain AssetImportTask on an .ogg yields a SoundWave (all Kenney audio is .ogg).
        ogg = os.path.join(self.tmp.name, "impact.OGG")
        open(ogg, "wb").close()
        with mock.patch.object(uia, "unreal", self.fake), contextlib.redirect_stdout(io.StringIO()):
            got = uia.import_sound(ogg, "/Game/Audio/", "Jump")
        self.assertEqual(got, "/Game/Audio/S_Jump")
        self.assertEqual(self.task.props["filename"], ogg)

    def test_other_sound_formats_still_refused(self):
        mp3 = os.path.join(self.tmp.name, "a.mp3")
        open(mp3, "wb").close()
        with mock.patch.object(uia, "unreal", self.fake):
            with self.assertRaises(ValueError):
                uia.import_sound(mp3, "/Game/Audio/", "Jump")


class OggCli(unittest.TestCase):
    def test_headless_accepts_ogg(self):
        a = uia._parse_cli_args(["--wav", "a.ogg", "--dest", "/Game/Audio/", "--name", "Hit"])
        self.assertEqual(a.wav, "a.ogg")

    def test_live_refuses_ogg_with_a_way_out(self):
        rc, _, err = run_main(["--live", "--project", "/p", "--wav", "a.ogg", "--dest", "/Game/A/", "--name", "X"])
        self.assertEqual(rc, 2)
        self.assertIn("headless", err)
        self.assertIn("ffmpeg", err)


class MeshImport(unittest.TestCase):
    """import_asset against a fake `unreal`: rigged GLBs (SkeletalMesh) and multi-part/LOD FBX
    (several StaticMeshes), the two shapes the UE 5.9 asset smoke test hit (2026-11-10)."""

    class _Mesh:
        slots_prop = None

        def __init__(self, textured=True):
            self.textured = textured

        def get_editor_property(self, k):
            if k != self.slots_prop:
                raise AttributeError(k)  # the real engine refuses the other class's slot property
            mat = types.SimpleNamespace(textured=self.textured)
            return [types.SimpleNamespace(get_editor_property=lambda _k: mat)]

    class StaticMesh(_Mesh):
        slots_prop = "static_materials"

    class SkeletalMesh(_Mesh):  # not a StaticMesh subclass, like the engine's classes
        slots_prop = "materials"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.src = os.path.join(self.tmp.name, "src.glb")
        open(self.src, "wb").close()
        self.assets, self.saved, self.imported = {}, [], []
        outer = self

        class Task:
            def __init__(s):
                s.props = {}

            def set_editor_property(s, k, v):
                s.props[k] = v

            def get_editor_property(s, k):
                return outer.imported if k == "imported_object_paths" else s.props.get(k)

        tools = types.SimpleNamespace(import_asset_tasks=lambda tasks: None)
        lib = types.SimpleNamespace(load_asset=lambda p: outer.assets.get(p, object()),
                                    save_asset=lambda p: outer.saved.append(p),
                                    does_asset_exist=lambda p: False)
        mel = types.SimpleNamespace(
            get_texture_parameter_names=lambda m: ["BaseColorTexture"] if m.textured else [])
        self.fake = types.SimpleNamespace(
            AssetImportTask=Task, StaticMesh=self.StaticMesh, SkeletalMesh=self.SkeletalMesh,
            EditorAssetLibrary=lib, MaterialEditingLibrary=mel,
            AssetToolsHelpers=types.SimpleNamespace(get_asset_tools=lambda: tools))

    def add(self, path, asset):
        self.assets[path] = asset
        self.imported.append(f"{path}.{path.rsplit('/', 1)[-1]}")

    def run_import(self, asset_type="prop", **kw):
        setup = mock.Mock(return_value="collision=ok, lod=ok")
        with mock.patch.object(uia, "unreal", self.fake), mock.patch.object(uia, "_apply_static_mesh_setup", setup), \
                contextlib.redirect_stdout(io.StringIO()):
            summary = uia.import_asset(self.src, "/Game/Props/", "Crate", asset_type, **kw)
        return summary, setup

    def test_rigged_glb_prop_skips_static_setup(self):
        door = "/Game/Props/src/SkeletalMeshes/SM_Crate"
        self.add(door, self.SkeletalMesh())
        summary, setup = self.run_import()
        setup.assert_not_called()  # used to raise TypeError and abort the batch
        self.assertTrue(summary.startswith(f"Created {door} | skipped(SkeletalMesh"), summary)
        self.assertIn("material_check=pass", summary)  # PBR check reads the skeletal `materials` slots
        self.assertEqual(self.saved, [door])

    def test_rigged_glb_prop_still_fails_loud_without_pbr(self):
        self.add("/Game/Props/src/SkeletalMeshes/SM_Crate", self.SkeletalMesh(textured=False))
        with self.assertRaises(RuntimeError):
            self.run_import()

    def test_multi_part_fbx_sets_up_every_part(self):
        parts = ["/Game/Props/lid", "/Game/Props/SM_Crate", "/Game/Props/latch"]
        for p in parts:
            self.add(p, self.StaticMesh())
        self.imported.append("/Game/Props/M_Wood.M_Wood")  # a material in the same task is ignored
        summary, setup = self.run_import()
        self.assertEqual(setup.call_count, 3)
        self.assertEqual(self.saved, parts)
        # The asset named after --name leads the summary even when it was not imported first.
        self.assertTrue(summary.startswith("Created /Game/Props/SM_Crate (+2 more mesh(es): "), summary)
        for leaf in ("lid", "latch", "SM_Crate"):
            self.assertIn(f"{leaf}: collision=ok", summary)
        self.assertEqual(summary.count("material_check=pass"), 3)

    def test_one_untextured_part_fails_loud(self):
        self.add("/Game/Props/SM_Crate", self.StaticMesh())
        self.add("/Game/Props/latch", self.StaticMesh(textured=False))
        with self.assertRaises(RuntimeError):
            self.run_import()

    def test_single_mesh_summary_unchanged(self):
        self.add("/Game/Props/src/StaticMeshes/SM_Crate", self.StaticMesh())
        summary, setup = self.run_import()
        setup.assert_called_once()
        self.assertEqual(summary, "Created /Game/Props/src/StaticMeshes/SM_Crate | collision=ok, lod=ok | "
                                  "material_instance=skipped(no-master-material) | "
                                  "material_check=pass(texture-bound material found)")

    def test_mixed_static_and_skeletal_parts(self):
        self.add("/Game/Props/SM_Crate", self.StaticMesh())
        self.add("/Game/Props/hinge", self.SkeletalMesh())
        summary, setup = self.run_import()
        setup.assert_called_once()
        self.assertIn("hinge: skipped(SkeletalMesh", summary)

    def test_no_mesh_reports_failure(self):
        self.imported.append("/Game/Props/M_Wood.M_Wood")
        summary, _ = self.run_import()
        self.assertTrue(summary.startswith("FAILED: import produced no mesh"), summary)
        self.assertEqual(self.saved, [])

    def test_character_skips_setup(self):
        self.add("/Game/Chars/SK_Crate", self.SkeletalMesh())
        summary, setup = self.run_import(asset_type="character")
        setup.assert_not_called()
        self.assertIn("skipped(character mesh", summary)

class EditorProbeProjectNames(unittest.TestCase):
    """Review r1: the open editor's project may be named relatively, via -project=, or not at all."""

    def refuse(self, own, other):
        cm = {"self": own, "4242": other}
        with mock.patch.object(uia.os, "listdir", return_value=["4242"]), \
                mock.patch.object(uia, "_read_cmdline", side_effect=lambda p: cm.get(str(p), [])), \
                mock.patch.object(uia, "_ancestor_pids", return_value={1}), \
                contextlib.redirect_stderr(io.StringIO()):
            return uia.refuse_if_editor_open()

    ED = "/opt/UE/Engine/Binaries/Linux/UnrealEditor"
    CMD = "/opt/UE/Engine/Binaries/Linux/UnrealEditor-Cmd"

    def test_relative_headless_vs_absolute_editor(self):
        self.assertTrue(self.refuse([self.CMD, "Mock.uproject"], [self.ED, "/p/Mock/Mock.uproject"]))

    def test_absolute_headless_vs_relative_editor(self):
        self.assertTrue(self.refuse([self.CMD, "/p/Mock/Mock.uproject"], [self.ED, "Mock.uproject"]))

    def test_project_flag_form(self):
        self.assertTrue(self.refuse([self.CMD, "/p/Mock/Mock.uproject"], [self.ED, "-project=/p/Mock/Mock.uproject"]))

    def test_editor_without_project_is_a_possible_clash(self):
        self.assertTrue(self.refuse([self.CMD, "/p/Mock/Mock.uproject"], [self.ED, "-nosplash"]))

    def test_other_project_is_not_a_clash(self):
        self.assertFalse(self.refuse([self.CMD, "/p/Mock/Mock.uproject"], [self.ED, "/q/Other/Other.uproject"]))


META = [{"name": n, "inputSchema": {"type": "object", "properties": {}}}
        for n in ("list_toolsets", "describe_toolset", "call_tool")]


class RealShapedEditor:
    """Looks like the real editor: three meta tools, ConfigSettings among the toolsets, NO python tool."""

    def __init__(self, set_reply="true", toolsets=("ConfigSettingsToolset.ConfigSettingsToolset",
                                                    "ProgrammaticToolset.ProgrammaticToolset")):
        self.calls, self.set_reply, self.toolsets = [], set_reply, toolsets

    def list_tools(self):
        return META

    def call(self, tool, args=None):
        self.calls.append((tool, args))
        if tool == "list_toolsets":
            return text_result("\n".join(self.toolsets))
        if tool == "call_tool" and args.get("tool_name") == "SetSectionProperties":
            if isinstance(self.set_reply, McpError):
                raise self.set_reply
            return text_result(self.set_reply)
        raise AssertionError(f"unexpected call {tool} {args}")


class StaticMeshCollisionSetup(unittest.TestCase):
    """_apply_static_mesh_setup against a fake engine that counts shapes the way UE 5.9 does:
    get_simple_collision_count() sees only boxes/spheres/capsules, never convex hulls (NDOP18 is a hull)."""

    class Mesh:
        def __init__(self, convex=0, box=0):
            self.convex, self.box, self.lod_group = convex, box, None

        def get_name(self):
            return "SM_Crate"

    def make_engine(self, add_returns=0, lod_wipes=False, with_subsystem=True):
        calls = []

        class Counts:
            def get_simple_collision_count(s, m):
                return m.box

            def get_convex_collision_count(s, m):
                return m.convex

        class Subsystem(Counts):
            def add_simple_collisions(s, m, shape):
                calls.append(("add", shape))
                if add_returns < 0:
                    return -1
                m.convex += 1
                return m.convex - 1

            def set_lod_group(s, m, group):
                calls.append(("lod", group))
                m.lod_group = group
                if lod_wipes:
                    m.convex = m.box = 0

        class Library(Subsystem):  # the deprecated EditorStaticMeshLibrary has the same calls
            pass

        def get_editor_subsystem(cls):
            if not with_subsystem:
                raise AttributeError("no subsystem")
            return Subsystem()

        fake = types.SimpleNamespace(
            ScriptingCollisionShapeType=types.SimpleNamespace(NDOP18="NDOP18"),
            StaticMeshEditorSubsystem=object, get_editor_subsystem=get_editor_subsystem,
            EditorStaticMeshLibrary=Library())
        return fake, calls

    def setup(self, mesh, **kw):
        fake, calls = self.make_engine(**kw)
        out = io.StringIO()
        with mock.patch.object(uia, "unreal", fake), contextlib.redirect_stdout(out):
            status = uia._apply_static_mesh_setup(mesh)
        return status, calls, out.getvalue()

    def test_added_hull_is_counted_even_though_simple_count_ignores_convex(self):
        mesh = self.Mesh()
        status, calls, _ = self.setup(mesh)
        self.assertEqual(status, "collision=convex(NDOP18) shapes=1, lod=auto(SmallProp LODGroup)")
        self.assertEqual(calls, [("add", "NDOP18"), ("lod", "SmallProp")])
        self.assertEqual(mesh.convex, 1)

    def test_import_collision_is_kept_not_doubled(self):
        mesh = self.Mesh(convex=1)  # Interchange already built a hull
        status, calls, _ = self.setup(mesh)
        self.assertEqual(status, "collision=kept(import) shapes=1, lod=auto(SmallProp LODGroup)")
        self.assertNotIn(("add", "NDOP18"), calls)
        self.assertEqual(mesh.convex, 1)

    def test_box_from_import_is_kept(self):
        status, calls, _ = self.setup(self.Mesh(box=1))
        self.assertTrue(status.startswith("collision=kept(import) shapes=1"), status)
        self.assertNotIn(("add", "NDOP18"), calls)

    def test_engine_refusing_the_hull_is_reported(self):
        status, _, out = self.setup(self.Mesh(), add_returns=-1)
        self.assertTrue(status.startswith("collision=NONE(failed(NDOP18 returned -1))"), status)
        self.assertIn("NO simple collision", out)

    def test_collision_lost_in_lod_rebuild_is_reported(self):
        status, _, out = self.setup(self.Mesh(), lod_wipes=True)
        self.assertTrue(status.startswith("collision=NONE(convex(NDOP18))"), status)
        self.assertIn("NO simple collision", out)

    def test_falls_back_to_deprecated_library(self):
        mesh = self.Mesh()
        status, _, _ = self.setup(mesh, with_subsystem=False)
        self.assertTrue(status.startswith("collision=convex(NDOP18) shapes=1, lod=skipped"), status)
        self.assertEqual(mesh.convex, 1)

    def test_no_enum_member_skips_without_crash(self):
        fake, _ = self.make_engine()
        fake.ScriptingCollisionShapeType = types.SimpleNamespace()
        with mock.patch.object(uia, "unreal", fake), contextlib.redirect_stdout(io.StringIO()):
            status = uia._apply_static_mesh_setup(self.Mesh())
        self.assertTrue(status.startswith("collision=NONE(skipped(no-enum-member))"), status)


class LiveWatchFolder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = os.path.join(self.tmp.name, "Proj")
        os.makedirs(self.project)
        open(os.path.join(self.project, "Proj.uproject"), "w").close()
        self.wav = os.path.join(self.tmp.name, "jump.wav")
        with open(self.wav, "wb") as f:
            f.write(b"RIFF\0\0\0\0WAVE")
        self.target = os.path.join(self.project, "Content", "Audio", "S_Jump.wav")
        self.uasset = self.target[:-4] + ".uasset"
        self.now, self.sleeps = 0.0, 0

    def run_live(self, cli=None, wait=120, on_sleep=None, project=None, dest="/Game/Audio/", name="Jump"):
        def sleep(s):  # a fake clock: the test never really waits
            self.now += s
            self.sleeps += 1
            if on_sleep:
                on_sleep(self.sleeps)
        return uia.live_import_sound(self.wav, dest, name, project or self.project, client=cli or RealShapedEditor(),
                                     wait=wait, poll=2.0, sleep=sleep, clock=lambda: self.now)

    def editor_imports_after(self, n):
        def on_sleep(i):
            if i == n:
                self.assertTrue(os.path.isfile(self.target), "the wav must be in Content/ before the editor can see it")
                with open(self.uasset, "wb") as f:
                    f.write(b"uasset")
        return on_sleep

    def test_success_turns_prompt_off_copies_wav_and_waits_for_uasset(self):
        cli = RealShapedEditor()
        got = self.run_live(cli, on_sleep=self.editor_imports_after(3))
        self.assertEqual(got, "/Game/Audio/S_Jump")
        tool, args = cli.calls[-1]
        self.assertEqual((tool, args["toolset_name"], args["tool_name"]),
                         ("call_tool", "ConfigSettingsToolset.ConfigSettingsToolset", "SetSectionProperties"))
        a = args["arguments"]
        self.assertEqual((a["containerName"], a["categoryName"], a["sectionName"]), ("Editor", "General", "LoadingSaving"))
        self.assertEqual(json.loads(a["propertiesJson"]), {"bPromptBeforeAutoImporting": False})
        with open(self.target, "rb") as f:
            self.assertEqual(f.read(), b"RIFF\0\0\0\0WAVE")
        self.assertFalse(os.path.exists(self.target + ".part"))
        self.assertEqual(self.sleeps, 3)

    def test_timeout_names_the_popup_and_exits_1(self):
        with self.assertRaises(uia.LiveError) as cm:
            self.run_live(wait=10)
        self.assertEqual(cm.exception.exit_code, 1)
        self.assertIn("popup", str(cm.exception))
        self.assertIn("S_Jump", str(cm.exception))

    def test_prompt_not_switched_off_stops_before_copying(self):
        with self.assertRaises(uia.LiveError) as cm:
            self.run_live(RealShapedEditor(set_reply="false"))
        self.assertEqual(cm.exception.exit_code, 1)
        self.assertFalse(os.path.exists(self.target))

    def test_no_config_toolset_exit_2(self):
        with self.assertRaises(uia.LiveError) as cm:
            self.run_live(RealShapedEditor(toolsets=("ProgrammaticToolset.ProgrammaticToolset",)))
        self.assertEqual(cm.exception.exit_code, 2)
        self.assertFalse(os.path.exists(self.target))

    def test_editor_unreachable_exit_2(self):
        with self.assertRaises(uia.LiveError) as cm:
            self.run_live(RealShapedEditor(set_reply=McpError("cannot reach http://127.0.0.1:8010/mcp", 2)))
        self.assertEqual(cm.exception.exit_code, 2)
        self.assertIn("launch-editor.sh", str(cm.exception))

    def test_existing_asset_is_refused(self):
        os.makedirs(os.path.dirname(self.uasset))
        with open(self.uasset, "wb") as f:
            f.write(b"x")
        with self.assertRaises(uia.LiveError) as cm:
            self.run_live()
        self.assertEqual(cm.exception.exit_code, 2)

    def test_project_may_be_the_uproject_file(self):
        got = self.run_live(on_sleep=self.editor_imports_after(1), project=os.path.join(self.project, "Proj.uproject"))
        self.assertEqual(got, "/Game/Audio/S_Jump")

    def test_bad_inputs_exit_2(self):
        for kw in ({"project": self.tmp.name}, {"dest": "Content/A"}):
            with self.assertRaises(uia.LiveError) as cm:
                self.run_live(**kw)
            self.assertEqual(cm.exception.exit_code, 2)
        with self.assertRaises(uia.LiveError) as cm:
            uia.live_import_sound(os.path.join(self.tmp.name, "nope.wav"), "/Game/A/", "X", self.project,
                                  client=RealShapedEditor())
        self.assertEqual(cm.exception.exit_code, 2)

    def test_dest_may_not_escape_content(self):
        outside = os.path.join(self.tmp.name, "outside")
        for dest in ("/Game/../../outside/", "/Game/./A/", "/Game/A/../B/", "/Game//A/"):
            with self.assertRaises(uia.LiveError, msg=dest) as cm:
                self.run_live(dest=dest)
            self.assertEqual(cm.exception.exit_code, 2)
        self.assertFalse(os.path.exists(outside))
        self.assertFalse(os.path.exists(os.path.join(self.project, "Content")))

    def test_name_must_be_plain(self):
        for name in ("a/b", "../../../outside/evil", "../x", "Jump.v2", "", "Jump Big"):
            cli = RealShapedEditor()
            with self.assertRaises(uia.LiveError, msg=repr(name)) as cm:
                self.run_live(cli, name=name)
            self.assertEqual(cm.exception.exit_code, 2)
            self.assertEqual(cli.calls, [])  # refused before any editor call
        self.assertFalse(os.path.exists(os.path.join(self.project, "Content")))

    def test_failed_copy_removes_part_file(self):
        def boom(src, dst):
            with open(dst, "wb") as f:
                f.write(b"half")
            raise OSError("disk full")
        with mock.patch("shutil.copyfile", side_effect=boom):
            with self.assertRaises(OSError):
                self.run_live()
        self.assertFalse(os.path.exists(self.target + ".part"))
        self.assertFalse(os.path.exists(self.target))


if __name__ == "__main__":
    unittest.main()
