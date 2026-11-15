"""asset_preview tests: flag logic and file discovery are pure Python; the render test needs Blender and PIL."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import asset_preview as A  # noqa: E402


def stats(**kw):
    base = {"mesh_objects": 1, "tris": 100, "size_m": [1.0, 1.0, 1.0], "non_manifold_edges": 0,
            "materials": [{"name": "m", "textures": ["a"]}],
            "textures": [{"role": "albedo", "name": "a", "exists": True}]}
    base.update(kw)
    return base


def codes(s, level=None):
    return {f["code"] for f in A.compute_flags(s) if level in (None, f["level"])}


class FlagLogic(unittest.TestCase):
    def test_clean_asset_has_no_flags(self):
        self.assertEqual(A.compute_flags(stats()), [])

    def test_empty_mesh(self):
        self.assertIn("empty_mesh", codes(stats(mesh_objects=0, tris=0, size_m=[0, 0, 0]), "error"))
        self.assertIn("empty_mesh", codes(stats(tris=0), "error"))

    def test_zero_size_is_not_also_reported_as_scale(self):
        c = codes(stats(size_m=[0, 0, 0]))
        self.assertIn("zero_size", c)
        self.assertNotIn("scale_too_small", c)

    def test_flat_mesh_is_only_a_warning(self):
        self.assertEqual(codes(stats(size_m=[1, 1, 0])), {"flat_mesh"})

    def test_scale_limits(self):
        self.assertIn("scale_too_big", codes(stats(size_m=[20.5, 1, 1]), "error"))
        self.assertIn("scale_too_small", codes(stats(size_m=[0.01, 0.01, 0.01]), "error"))
        self.assertEqual(codes(stats(size_m=[20.0, 1, 1])), set())
        self.assertEqual(codes(stats(size_m=[0.02, 0.01, 0.01])), set())  # judged by the largest side

    def test_missing_texture_is_an_error(self):
        s = stats(textures=[{"role": "albedo", "name": "a.png", "exists": False}])
        self.assertIn("missing_textures", codes(s, "error"))

    def test_no_textures_is_a_warning(self):
        self.assertEqual(codes(stats(textures=[])), {"no_textures"})

    def test_non_manifold_and_no_material_warn(self):
        self.assertEqual(codes(stats(non_manifold_edges=3, materials=[])), {"non_manifold", "no_material"})

    def test_empty_mesh_does_not_pile_on(self):
        self.assertEqual(codes(stats(mesh_objects=0, tris=0, size_m=[0, 0, 0], materials=[], textures=[])), {"empty_mesh"})


class RefChoice(unittest.TestCase):
    def test_auto(self):
        self.assertEqual(A.pick_ref([0.5, 0.5, 1.9]), ("human", 1.8))
        self.assertEqual(A.pick_ref([0.5, 0.4, 0.5]), ("cube", 1.0))
        self.assertEqual(A.pick_ref([0.05, 0.05, 0.05]), ("cube", 0.1))

    def test_forced(self):
        self.assertEqual(A.pick_ref([0.05] * 3, "human"), ("human", 1.8))
        self.assertEqual(A.pick_ref([9] * 3, "cube"), ("cube", 1.0))


class Discovery(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def touch(self, *parts):
        p = self.root.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
        return p

    def test_prefers_game_glb_over_raw_and_high(self):
        game = self.touch("crate", "game", "crate.glb")
        self.touch("crate", "game", "crate.fbx")
        self.touch("crate", "raw.glb")
        self.touch("crate", "raw.high.glb")
        self.assertEqual(A.find_assets(self.root / "crate"), [game])

    def test_falls_back_to_raw_not_high(self):
        raw = self.touch("a", "raw.glb")
        self.touch("a", "raw.high.glb")
        self.assertEqual(A.find_assets(self.root / "a"), [raw])

    def test_folder_of_assets_gives_one_model_each(self):
        a = self.touch("a", "game", "a.glb")
        b = self.touch("b", "raw.glb")
        self.touch("c", "notes.txt")
        self.assertEqual(A.find_assets(self.root), [a, b])

    def test_single_file_and_non_model(self):
        f = self.touch("x", "thing.fbx")
        self.assertEqual(A.find_assets(f), [f])
        self.assertEqual(A.find_assets(self.touch("x", "thing.txt")), [])

    def test_flat_folder_previews_every_model_with_own_names(self):
        for n in ("crate.glb", "barrel.glb", "lamp.fbx"):
            self.touch("props", n)
        plan = A.plan_assets(self.root / "props")
        self.assertEqual({m.name for m, _o, _p in plan}, {"crate.glb", "barrel.glb", "lamp.fbx"})
        self.assertEqual(len({(o, p) for _m, o, p in plan}), 3)
        self.assertEqual({p for _m, _o, p in plan}, {"crate_", "barrel_", "lamp_"})

    def test_shared_game_folder_with_several_models(self):
        self.touch("run", "game", "a.glb")
        self.touch("run", "game", "b.glb")
        self.touch("run", "raw.glb")
        plan = A.plan_assets(self.root / "run")
        self.assertEqual(len(plan), 3)
        self.assertEqual(len({(o, p) for _m, o, p in plan}), 3)

    def test_asset_folder_keeps_plain_names(self):
        self.touch("crate", "game", "crate.glb")
        self.touch("crate", "raw.glb")
        self.assertEqual([(o.name, p) for _m, o, p in A.plan_assets(self.root / "crate")], [("crate", "")])

    def test_explicit_files_in_one_folder_do_not_collide(self):
        a, b = self.touch("props", "crate.glb"), self.touch("props", "barrel.glb")
        plan = A.dedupe_outputs(A.plan_assets(a) + A.plan_assets(b))
        self.assertEqual(len({(o, p) for _m, o, p in plan}), 2)
        raw, high = self.touch("x", "raw.glb"), self.touch("x", "raw.high.glb")
        plan = A.dedupe_outputs(A.plan_assets(raw) + A.plan_assets(high))
        self.assertEqual(len({(o, p) for _m, o, p in plan}), 2)

    def test_same_name_in_root_and_game_do_not_collide(self):
        a, b = self.touch("crate", "crate.glb"), self.touch("crate", "game", "crate.glb")
        plan = A.dedupe_outputs(A.plan_assets(a) + A.plan_assets(b))
        self.assertEqual(len({(o, p) for _m, o, p in plan}), 2)

    def test_relative_and_absolute_paths_of_one_folder_do_not_collide(self):
        import os
        a, b = self.touch("props", "crate.glb"), self.touch("props", "barrel.glb")
        old = os.getcwd()
        os.chdir(self.root)
        try:
            plan = A.dedupe_outputs([(Path("props/crate.glb"), Path("props"), "")] + [(b, self.root / "props", "")])
        finally:
            os.chdir(old)
        self.assertEqual(len({(o, p) for _m, o, p in plan}), 2)

    def test_same_model_twice_is_one_job(self):
        a = self.touch("props", "crate.glb")
        plan = A.dedupe_outputs(A.plan_assets(a) + A.plan_assets(a) + A.plan_assets(a.parent))
        self.assertEqual(len(plan), 1)

    def test_find_blender_validates(self):
        self.assertIsNone(A.find_blender(str(self.root / "no-such-blender")))
        fake = self.touch("bin", "blender")
        self.assertIsNone(A.find_blender(str(fake)))  # exists but not executable
        fake.chmod(0o755)
        self.assertEqual(A.find_blender(str(fake)), str(fake))

    def test_main_fails_early_on_bad_blender(self):
        m = self.touch("crate", "game", "crate.glb")
        self.assertEqual(A.main([str(m), "--blender", str(self.root / "nope")]), 2)

    def test_collision_names(self):
        for n in ("UCX_crate_00", "UBX_a", "usp_b", "UCP_c"):
            self.assertTrue(A.is_collision_name(n), n)
        self.assertFalse(A.is_collision_name("crate"))
        self.assertFalse(A.is_collision_name("SM_UCX"))

    def test_asset_root_strips_game(self):
        self.assertEqual(A.asset_root(Path("/w/crate/game/crate.glb")), Path("/w/crate"))
        self.assertEqual(A.asset_root(Path("/w/crate/raw.glb")), Path("/w/crate"))

    def test_sidecars_fill_only_missing_roles(self):
        self.touch("crate", "raw.albedo.png")
        self.touch("crate", "raw.normal.png")
        model = self.touch("crate", "game", "crate.glb")
        got = {t["role"] for t in A.sidecar_textures(model, {"albedo"})}
        self.assertEqual(got, {"normal"})


BLENDER = shutil.which("blender")
try:
    import PIL  # noqa: F401
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

MAKE_FIXTURE = """
import bpy, sys
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=1.0)  # 1 m cube, 12 tris, closed
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
"""


@unittest.skipUnless(BLENDER and HAVE_PIL, "needs Blender on PATH and Pillow: skipping the render test")
class RenderFixture(unittest.TestCase):
    def test_cube_end_to_end(self):
        with tempfile.TemporaryDirectory() as td:
            asset = Path(td) / "cube"
            (asset / "game").mkdir(parents=True)
            script = Path(td) / "make.py"
            script.write_text(MAKE_FIXTURE)
            model = asset / "game" / "cube.glb"
            subprocess.run([BLENDER, "-b", "--factory-startup", "--python", str(script), "--", str(model)],
                           check=True, capture_output=True, timeout=120)
            rc = A.main([str(asset)])
            self.assertEqual(rc, 0)
            self.assertGreater((asset / "preview.png").stat().st_size, 1000)
            res = json.loads((asset / "preview.json").read_text())
            self.assertEqual(res["tris"], 12)
            for v in res["size_m"]:
                self.assertAlmostEqual(v, 1.0, places=3)
            self.assertEqual(res["non_manifold_edges"], 0)
            self.assertEqual({f["code"] for f in res["flags"]}, {"no_material", "no_textures"})
            self.assertTrue(res["ok"])
            self.assertLess(res["seconds"], 60)


MAKE_COLLISION_FBX = """
import bpy, sys
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=1.0)
bpy.context.active_object.name = 'crate'
bpy.ops.mesh.primitive_cube_add(size=3.0)
bpy.context.active_object.name = 'UCX_crate_00'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=out, object_types={'MESH'})
"""


@unittest.skipUnless(BLENDER and HAVE_PIL, "needs Blender on PATH and Pillow: skipping the collision test")
class CollisionHull(unittest.TestCase):
    def test_ucx_hull_is_not_counted_or_drawn(self):
        with tempfile.TemporaryDirectory() as td:
            asset = Path(td) / "crate"
            (asset / "game").mkdir(parents=True)
            script = Path(td) / "make.py"
            script.write_text(MAKE_COLLISION_FBX)
            subprocess.run([BLENDER, "-b", "--factory-startup", "--python", str(script), "--", str(asset / "game" / "crate.fbx")],
                           check=True, capture_output=True, timeout=120)
            self.assertEqual(A.main([str(asset)]), 0)
            res = json.loads((asset / "preview.json").read_text())
            self.assertEqual(res["tris"], 12)
            for v in res["size_m"]:
                self.assertAlmostEqual(v, 1.0, places=2)
            self.assertEqual(res["collision_meshes"], ["UCX_crate_00"])


if __name__ == "__main__":
    unittest.main()
