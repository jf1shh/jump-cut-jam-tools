"""rig_mannequin.py and rig_rigify.py run in Blender background mode (CPU, no GPU); skipped without Blender."""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLENDER = shutil.which("blender")


def run(script, out, *extra):
    return subprocess.run([BLENDER, "-b", "-P", str(ROOT / "scripts" / script), "--", out, *extra],
                          capture_output=True, text=True, timeout=300)


def fields(proc, tag):
    line = next((l for l in proc.stdout.splitlines() if l.startswith(tag + " ")), "")
    return dict(re.findall(r"(\w+)=(\S+)", line))


@unittest.skipUnless(BLENDER, "blender not installed")
class RigScripts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.man = run("rig_mannequin.py", cls.tmp.name, "--names", "mannequin")
        cls.gen = run("rig_mannequin.py", cls.tmp.name, "--names", "generic")
        cls.rfy = run("rig_rigify.py", cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_mannequin_fbx(self):
        f = fields(self.man, "RIG")
        self.assertEqual(f.get("names"), "mannequin", self.man.stderr[-500:])
        self.assertEqual(f["bones"], "26")
        self.assertEqual(f["unweighted"], "0")
        fbx = Path(f["fbx"])
        self.assertTrue(fbx.is_file())
        data = fbx.read_bytes()
        self.assertTrue(data.startswith(b"Kaydara FBX Binary"))
        for name in (b"pelvis", b"spine_05", b"upperarm_l", b"ball_r"):
            self.assertIn(name, data)

    def test_generic_names_differ(self):
        f = fields(self.gen, "RIG")
        self.assertEqual(f.get("names"), "generic", self.gen.stderr[-500:])
        data = Path(f["fbx"]).read_bytes()
        self.assertIn(b"Bone_Pelvis", data)
        self.assertIn(b"Bone_Upperarm_L", data)
        self.assertNotIn(b"upperarm_l", data)

    def test_coverage_is_printed_and_healthy_on_both_paths(self):
        """Review r2: the body groups must hold geometry on the default prop; counts always printed."""
        for proc, tag in ((self.man, "RIG"), (self.rfy, "RIGIFY")):
            f = fields(proc, tag)
            self.assertTrue(f, proc.stdout[-400:] + proc.stderr[-400:])
            total = int(f["verts"])
            for group, floor in (("core", 0.10), ("arms", 0.05), ("legs", 0.10), ("head", 0.03)):
                self.assertGreaterEqual(int(f["cover_" + group]) / total, floor, (tag, group, f))
            self.assertEqual(proc.returncode, 0)
            self.assertLess(float(f["align_max_m"]), 0.27, (tag, f))  # bones sit on the vertices they move

    # Independent geometry check (ported from review r1/r2 test_1): runs after the rig script in the same Blender
    # session and measures, for each bone, the distance from its midpoint to the centre of the vertices it weights.
    CHECK = r'''
import bpy
from mathutils import Vector
bpy.context.view_layer.update()
mesh = bpy.data.objects["Character"]
arm = bpy.data.objects["Armature"]
for name in ("upperarm_l", "upperarm_r", "head", "thigh_l"):
    g = mesh.vertex_groups[name].index
    pts = [mesh.matrix_world @ v.co for v in mesh.data.vertices
           if any(x.group == g and x.weight > 0 for x in v.groups)]
    c = sum(pts, Vector()) / len(pts)
    b = arm.data.bones[name]
    mid = arm.matrix_world @ ((b.head_local + b.tail_local) / 2)
    print("CHECK %s dist=%.3f" % (name, (c - mid).length))
'''

    def test_bones_sit_on_their_vertices_for_every_output_facing(self):
        """Review r1/r2 test_1: with --face -Y the mesh was turned twice and the bones once (0.56 m apart)."""
        check = Path(self.tmp.name) / "check.py"
        check.write_text(self.CHECK, encoding="utf-8")
        for face in ("-Y", "+X", "+Y", "-X"):
            with self.subTest(face=face):
                out = tempfile.mkdtemp(dir=self.tmp.name)
                p = subprocess.run([BLENDER, "-b", "-P", str(ROOT / "scripts" / "rig_mannequin.py"), "-P", str(check),
                                    "--", out, "--face", face], capture_output=True, text=True, timeout=300)
                dists = [float(l.split("dist=")[1]) for l in p.stdout.splitlines() if l.startswith("CHECK ")]
                self.assertEqual(len(dists), 4, p.stdout[-600:] + p.stderr[-600:])
                self.assertLess(max(dists), 0.15, dists)
                self.assertLess(float(fields(p, "RIG")["align_max_m"]), 0.27)

    def test_input_facing_option_accepts_and_turns_the_input(self):
        """A -Y mesh is refused by default and accepted (turned to +X first) with --input-facing -Y."""
        glb = Path(self.tmp.name) / "character.glb"
        turned = Path(self.tmp.name) / "turned2.glb"
        expr = ("import bpy,math;bpy.ops.wm.read_factory_settings(use_empty=True);"
                f"bpy.ops.import_scene.gltf(filepath={str(glb)!r});"
                "o=[x for x in bpy.data.objects if x.type=='MESH'][0];o.rotation_mode='XYZ';"
                "o.rotation_euler=(0,0,math.radians(-90));bpy.context.view_layer.objects.active=o;o.select_set(True);"
                f"bpy.ops.object.transform_apply(rotation=True);bpy.ops.export_scene.gltf(filepath={str(turned)!r})")
        subprocess.run([BLENDER, "-b", "--python-expr", expr], capture_output=True, text=True, timeout=300)
        refused = run("rig_mannequin.py", tempfile.mkdtemp(dir=self.tmp.name), "--input", str(turned))
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--input-facing", refused.stdout + refused.stderr)
        ok = run("rig_mannequin.py", tempfile.mkdtemp(dir=self.tmp.name), "--input", str(turned),
                 "--input-facing", "-Y")
        f = fields(ok, "RIG")
        self.assertEqual(ok.returncode, 0, ok.stdout[-500:] + ok.stderr[-500:])
        self.assertEqual(f["unweighted"], "0")
        self.assertLess(float(f["align_max_m"]), 0.27)

    def test_backwards_input_is_refused_and_accepted_with_input_facing(self):
        """Review r3: a mesh turned 180 degrees (faces -X) passed the sideways check and exported a backwards rig."""
        glb = Path(self.tmp.name) / "character.glb"
        back = Path(self.tmp.name) / "backwards.glb"
        expr = ("import bpy,math;bpy.ops.wm.read_factory_settings(use_empty=True);"
                f"bpy.ops.import_scene.gltf(filepath={str(glb)!r});"
                "o=[x for x in bpy.data.objects if x.type=='MESH'][0];o.rotation_mode='XYZ';"
                "o.rotation_euler=(0,0,math.radians(180));bpy.context.view_layer.objects.active=o;o.select_set(True);"
                f"bpy.ops.object.transform_apply(rotation=True);bpy.ops.export_scene.gltf(filepath={str(back)!r})")
        subprocess.run([BLENDER, "-b", "--python-expr", expr], capture_output=True, text=True, timeout=300)
        for script in ("rig_mannequin.py", "rig_rigify.py"):
            with self.subTest(script=script):
                proc = run(script, tempfile.mkdtemp(dir=self.tmp.name), "--input", str(back))
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn("backwards", proc.stdout + proc.stderr)
        ok = run("rig_mannequin.py", tempfile.mkdtemp(dir=self.tmp.name), "--input", str(back), "--input-facing", "-X")
        self.assertEqual(ok.returncode, 0, ok.stdout[-500:] + ok.stderr[-500:])
        self.assertLess(float(fields(ok, "RIG")["align_max_m"]), 0.27)

    def test_generic_names_skip_root_in_skinning(self):
        out = tempfile.mkdtemp(dir=self.tmp.name)
        check = Path(self.tmp.name) / "check_root.py"
        check.write_text("import bpy\nm=bpy.data.objects['Character']\ng=m.vertex_groups['Bone_Root'].index\n"
                         "print('CHECK root_verts=%d' % sum(1 for v in m.data.vertices for x in v.groups"
                         " if x.group==g and x.weight>0))\n", encoding="utf-8")
        p = subprocess.run([BLENDER, "-b", "-P", str(ROOT / "scripts" / "rig_mannequin.py"), "-P", str(check), "--",
                            out, "--names", "generic"], capture_output=True, text=True, timeout=300)
        self.assertIn("CHECK root_verts=0", p.stdout, p.stdout[-400:] + p.stderr[-400:])

    def test_wrong_facing_input_is_refused(self):
        """Review r2: an input facing -Y (what rig_mannequin.py exports by default) must be refused."""
        glb = Path(self.tmp.name) / "character.glb"
        turned = Path(self.tmp.name) / "turned.glb"
        expr = ("import bpy,math;bpy.ops.wm.read_factory_settings(use_empty=True);"
                f"bpy.ops.import_scene.gltf(filepath={str(glb)!r});"
                "o=[x for x in bpy.data.objects if x.type=='MESH'][0];o.rotation_mode='XYZ';"
                "o.rotation_euler=(0,0,math.radians(-90));bpy.context.view_layer.objects.active=o;o.select_set(True);"
                f"bpy.ops.object.transform_apply(rotation=True);bpy.ops.export_scene.gltf(filepath={str(turned)!r})")
        subprocess.run([BLENDER, "-b", "--python-expr", expr], capture_output=True, text=True, timeout=300)
        self.assertTrue(turned.is_file())
        proc = run("rig_mannequin.py", tempfile.mkdtemp(dir=self.tmp.name), "--input", str(turned))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("input refused", proc.stdout + proc.stderr)
        self.assertIn("faces -Y", proc.stdout + proc.stderr)

    def test_already_rigged_input_is_rebound_cleanly(self):
        """Feeding a rigged FBX (facing +X) back in must drop its old groups and armature (review r1)."""
        first = tempfile.mkdtemp(dir=self.tmp.name)
        src = fields(run("rig_mannequin.py", first, "--names", "mannequin", "--face", "+X"), "RIG")["fbx"]
        out = tempfile.mkdtemp(dir=self.tmp.name)
        proc = run("rig_mannequin.py", out, "--input", src, "--names", "generic")
        f = fields(proc, "RIG")
        self.assertTrue(f, proc.stderr[-500:])
        self.assertEqual(f["auto_missed"], f["verts"])  # old groups no longer hide the failed heat weights
        self.assertEqual(f["unweighted"], "0")
        data = Path(f["fbx"]).read_bytes()
        self.assertIn(b"Bone_Pelvis", data)
        self.assertNotIn(b"upperarm_l", data)  # old mannequin-named bones and groups are gone

    def test_input_without_mesh_exits_cleanly(self):
        empty = Path(self.tmp.name) / "empty.fbx"
        empty.write_bytes(b"")
        proc = run("rig_rigify.py", self.tmp.name, "--input", str(empty))
        self.assertNotIn("IndexError", proc.stderr)
        self.assertNotEqual(proc.returncode, 0)  # failures must reach the caller as a non-zero exit code

    def test_rigify_fbx(self):
        f = fields(self.rfy, "RIGIFY")
        self.assertTrue(f, self.rfy.stderr[-800:])
        self.assertGreater(int(f["deform"]), 20)
        self.assertEqual(f["unweighted"], "0")
        self.assertIn(b"DEF-", Path(f["fbx"]).read_bytes())


if __name__ == "__main__":
    unittest.main()
