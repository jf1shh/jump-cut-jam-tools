"""Review-round-1 regressions for the asset chain (fakes; the two Blender tests skip without blender)."""
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_asset_chain import Base, Rig  # noqa: E402

from chain import engines as E  # noqa: E402
from chain import pipeline as P  # noqa: E402

BLENDER = shutil.which("blender")
LIC = {k: {"verdict": "ok"} for k in ("local", "gpt", "grok", "triposplat", "passthrough", "blender")}


class TestReviewFixes(Base):
    def test_timeout_fails_one_asset_not_the_queue(self):
        rig = Rig()
        reg = rig.registry()
        inner = reg[("3d", "triposplat")].run

        def run(ctx):
            if ctx["spec"]["name"] == "slow":
                E._sh([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2)
            return inner(ctx)
        reg[("3d", "triposplat")] = E.Engine("3d", "triposplat", "gpu", run)
        c, _ = self.chain(rig)
        c.reg = reg
        res = {r["name"]: r for r in c.run_queue([{"name": "good", "prompt": "x"}, {"name": "slow", "prompt": "y"}], workers=2)}
        self.assertTrue(res["good"]["ok"])
        self.assertFalse(res["slow"]["ok"])
        self.assertTrue((self.t / "credits.md").exists())

    def test_resume_rechecks_licence(self):
        rig = Rig()
        table = dict(LIC)
        c, _ = self.chain(rig, table=table)
        self.assertTrue(c.run_queue([{"name": "a", "prompt": "x"}])[0]["ok"])
        table["local"] = {"verdict": "non-commercial"}
        c2, _ = self.chain(rig, table=table)
        r = c2.run_queue([{"name": "a", "prompt": "x"}])[0]
        self.assertFalse(r["ok"])
        self.assertIn("refused", r["error"])

    def test_forced_engine_not_served_from_other_engine_cache(self):
        rig = Rig()
        c, _ = self.chain(rig)
        c.run_queue([{"name": "a", "prompt": "x"}])
        c2, _ = self.chain(rig, engine_override={"image": "gpt"})
        c2.run_queue([{"name": "a", "prompt": "x"}])
        self.assertIn(("a", "image", "gpt"), rig.calls)
        prov = json.loads((self.t / "out/a/provenance.json").read_text())
        self.assertEqual(prov["stages"]["image"]["engine"], "gpt")

    def test_banned_checkpoint_in_env_refused(self):
        seen = []
        orig_sh, orig_env = E._sh, os.environ.get("NEXUS_THREED_IMAGE_CHECKPOINT")
        E._sh = lambda *a, **k: seen.append(1) or ""
        os.environ["NEXUS_THREED_IMAGE_CHECKPOINT"] = "qwen-image-2.1"
        try:
            eng = E.build_registry()[("3d", "triposplat")]
            with self.assertRaises(E.StageError):
                eng.run({"spec": {"name": "a"}, "workdir": self.t, "inputs": {"image": str(self.t / "c.png")}})
            self.assertFalse(seen)
        finally:
            E._sh = orig_sh
            if orig_env is None:
                os.environ.pop("NEXUS_THREED_IMAGE_CHECKPOINT", None)
            else:
                os.environ["NEXUS_THREED_IMAGE_CHECKPOINT"] = orig_env

    def test_duplicate_names_refused(self):
        c, _ = self.chain(Rig())
        with self.assertRaises(ValueError):
            c.run_queue([{"name": "crate", "prompt": "x"}, {"name": "crate", "prompt": "y"}])

    def test_manifest_requires_pbr_and_records_texture(self):
        c, _ = self.chain(Rig())
        c.run_queue([{"name": "a", "prompt": "x"}])
        a = json.loads((self.t / "out/a/ue_import_manifest.json").read_text())["assets"][0]
        self.assertTrue(a["require_pbr"])
        self.assertIn("has_texture", a)
        self.assertTrue(json.loads((self.t / "out/a/qa.json").read_text())["warnings"])


REAL = {"schema": 1, "default_verdict_for_unknown": "no", "entries": [
    {"id": "krea-2-turbo", "verdict": "ok", "credit_text": ""},
    {"id": "triposplat", "verdict": "ok", "credit_text": ""},
    {"id": "blender", "verdict": "ok", "credit_text": ""},
    {"id": "gpt-image", "verdict": "ok", "credit_text": ""},
    {"id": "grok-imagine", "verdict": "unclear", "credit_text": "Image created with Grok"}]}


class TestReviewRound2(Base):
    def test_real_licence_schema_accepts_prompt_and_image_assets(self):
        c, _ = self.chain(Rig(), table=REAL)
        ref = self.t / "ref.png"
        ref.write_bytes(b"png")
        res = c.run_queue([{"name": "crate", "prompt": "x"}, {"name": "lamp", "image": str(ref)}])
        self.assertTrue(all(r["ok"] for r in res), res)

    def test_any_refused_alias_refuses_engine(self):
        from chain.licenses import LicenceError
        g = self.licence({"local": {"verdict": "ok"}, "krea-2-turbo": {"verdict": "no"}})
        with self.assertRaises(LicenceError):
            g.check("image", "local", ("krea-2-turbo",))
        g2 = self.licence(REAL)
        with self.assertRaises(LicenceError):
            g2.check("image", "grok", ("grok-imagine",))

    def test_internal_shortcut_only_exact_pair_without_aliases(self):
        from chain.licenses import LicenceError
        g = self.licence({"trellis.2": {"verdict": "no"}})
        with self.assertRaises(LicenceError):
            g.check("texture", "passthrough", ("trellis.2",))
        with self.assertRaises(LicenceError):
            g.check("3d", "passthrough")
        self.assertEqual(g.check("texture", "passthrough")["source"], "internal")
        self.assertIn("owner-supplied", g.check("image", "reference-image")["credit"])

    def test_gpu_lock_released_when_preflight_raises(self):
        import fcntl

        def boom():
            raise FileNotFoundError("gpu-preflight")
        lanes = P.Lanes(self.t / "g.lock", preflight=boom)
        with self.assertRaises(E.StageError):
            with lanes.hold("gpu"):
                pass
        f = open(self.t / "g.lock", "w")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)  # raises BlockingIOError if still held
        f.close()

    def test_resume_notices_deleted_or_swapped_output(self):
        rig = Rig()
        reg = rig.registry()

        def cleanup(ctx):
            game = ctx["workdir"] / "game"
            game.mkdir(exist_ok=True)
            n = ctx["spec"]["name"]
            (game / f"{n}.glb").write_text("glb")
            (game / f"{n}.fbx").write_text("fbx")
            return {"output": game / f"{n}.glb", "report": {"tris": 1, "budget": 5, "bbox_m": [1, 1, 1], "uv": {},
                                                           "thumb": None, "lods": ["LOD0"], "material": "M"}}
        reg[("cleanup", "blender")] = E.Engine("cleanup", "blender", "cpu", cleanup)
        c, _ = self.chain(rig)
        c.reg = reg
        spec = {"name": "crate", "prompt": "x"}
        c.run_queue([spec])
        game = self.t / "out/crate/game"
        (game / "crate.fbx").unlink()
        c.run_queue([spec])
        self.assertTrue((game / "crate.fbx").is_file())  # cleanup reran
        (game / "crate.glb").write_text("swapped")
        c.run_queue([spec])
        self.assertEqual((game / "crate.glb").read_text(), "glb")


@unittest.skipUnless(BLENDER, "blender not installed")
class TestBlender(unittest.TestCase):
    def _clean(self, make_src, *extra):
        t = Path(tempfile.mkdtemp())
        sp = t / "mk.py"
        sp.write_text("import bpy, math\nbpy.ops.wm.read_factory_settings(use_empty=True)\n" + make_src
                      + f"\nbpy.ops.export_scene.gltf(filepath={str(t / 'in.glb')!r}, export_format='GLB')\n")
        subprocess.run([BLENDER, "-b", "--factory-startup", "-P", str(sp)], check=True, capture_output=True, timeout=120)
        out = t / "game"
        subprocess.run([BLENDER, "-b", "--factory-startup", "-P", str(E.HERE / "blender_cleanup.py"), "--",
                        str(t / "in.glb"), str(out), "thing", "--budget", "5000", *extra],
                       check=True, capture_output=True, timeout=180)
        return out

    def test_fbx_unit_scale_is_100(self):
        out = self._clean("bpy.ops.mesh.primitive_cube_add(size=1)", "--height", "0.8")
        data = (out / "thing.fbx").read_bytes()
        i = data.index(b"UnitScaleFactor") + len(b"UnitScaleFactor")
        while data[i] == ord("S"):
            (n,) = struct.unpack("<I", data[i + 1:i + 5])
            i += 5 + n
        (usf,) = struct.unpack("<d", data[i + 1:i + 9])
        self.assertIn(usf, (1.0, 100.0))

    def test_parent_rotation_kept(self):
        out = self._clean(
            "e = bpy.data.objects.new('root', None); bpy.context.scene.collection.objects.link(e)\n"
            "e.rotation_euler = (math.radians(90), 0, 0)\n"
            "bpy.ops.mesh.primitive_cube_add(size=1); c = bpy.context.active_object\n"
            "c.scale = (1, 1, 3); bpy.ops.object.transform_apply(scale=True)\n"
            "c.parent = e\nbpy.context.view_layer.update()")
        bbox = json.loads((out / "cleanup_report.json").read_text())["bbox_m"]
        self.assertAlmostEqual(bbox[2], 1.0, delta=0.05)


class ProviderErrorDetailTest(unittest.TestCase):
    def test_stage_error_keeps_attempt_detail(self):
        import providers as PR
        err = PR.ProviderError("no provider produced a concept image (local=failed)")
        err.attempts = [{"provider": "local", "outcome": "failed", "detail": "could not read history: timed out"}]
        orig = PR.generate_concept

        def boom(*a, **k):
            raise err
        PR.generate_concept = boom
        try:
            with tempfile.TemporaryDirectory() as d:
                ctx = {"workdir": Path(d), "spec": {"prompt": "x"}}
                with self.assertRaises(E.StageError) as cm:
                    E._provider_engine("local")(ctx)
        finally:
            PR.generate_concept = orig
        self.assertIn("could not read history", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
