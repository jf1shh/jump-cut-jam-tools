"""Asset chain tests: fakes only, no GPU, no network, no Blender."""
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from chain import engines as E  # noqa: E402
from chain import pipeline as P  # noqa: E402
import asset_chain as A  # noqa: E402
from chain.licenses import LicenceError, LicenceGate  # noqa: E402

REPORT = {"tris": 400, "budget": 500, "bbox_m": [1, 1, 1], "uv": {"status": "present"}, "thumb": None,
          "lods": ["LOD0"], "material": "M_x"}


class Rig:
    """Fake registry that records calls and concurrency."""

    def __init__(self, delay=0.0):
        self.calls = []
        self.delay = delay
        self.gpu_now = 0
        self.gpu_peak = 0
        self._m = threading.Lock()

    def _eng(self, stage, name, lane, ext, aliases=()):
        def run(ctx):
            with self._m:
                self.calls.append((ctx["spec"]["name"], stage, name))
                if lane == "gpu":
                    self.gpu_now += 1
                    self.gpu_peak = max(self.gpu_peak, self.gpu_now)
            time.sleep(self.delay)
            out = ctx["workdir"] / f"{stage}_{name}.{ext}"
            out.write_text(f"{stage}:{name}:{ctx['spec'].get('prompt')}:{ctx['inputs']}")
            res = {"output": out}
            if stage == "cleanup":
                game = ctx["workdir"] / "game"
                game.mkdir(exist_ok=True)
                out = game / f"{ctx['spec']['name']}.glb"
                out.write_text("glb")
                res = {"output": out, "report": dict(REPORT)}
            with self._m:
                if lane == "gpu":
                    self.gpu_now -= 1
            return res
        return E.Engine(stage, name, lane, run, aliases)

    def registry(self):
        r = self._eng
        return {
            ("image", "local"): r("image", "local", "gpu", "png", ("krea-2-turbo",)),
            ("image", "gpt"): r("image", "gpt", "cloud", "png"),
            ("image", "grok"): r("image", "grok", "cloud", "png"),
            ("image", "reference-image"): E.Engine("image", "reference-image", "cpu",
                                                   lambda c: {"output": Path(c["spec"]["image"])}),
            ("3d", "triposplat"): r("3d", "triposplat", "gpu", "glb"),
            ("texture", "passthrough"): r("texture", "passthrough", "cpu", "glb"),
            ("cleanup", "blender"): r("cleanup", "blender", "cpu", "glb"),
        }


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        self.warnings = []

    def tearDown(self):
        self.tmp.cleanup()

    def licence(self, table=None):
        p = self.t / "lic.json"
        if table is not None:
            p.write_text(json.dumps(table))
        return LicenceGate(p, warn=self.warnings.append)

    def chain(self, rig, table="all", **kw):
        if table == "all":
            table = {k: {"verdict": "ok"} for k in ("local", "gpt", "grok", "triposplat", "passthrough", "blender", "reference-image")}
            table["grok"] = {"verdict": "ok-with-credit", "credit": "Images by xAI Grok"}
        gate = self.licence(table)
        lanes = P.Lanes(self.t / "gpu.lock", cloud=3, cpu=3, preflight=kw.pop("preflight", None))
        c = P.Chain(rig.registry(), gate, self.t / "out", self.t / "log.csv", self.t / "credits.md", lanes, **kw)
        return c, lanes


class TestQueue(Base):
    def test_queue_json_and_yaml(self):
        specs = [{"name": "a", "prompt": "x"}, {"name": "b", "image": "/tmp/i.png", "class": "prop_small"}]
        j = self.t / "q.json"
        j.write_text(json.dumps(specs))
        y = self.t / "q.yaml"
        y.write_text("assets:\n  - {name: a, prompt: x}\n  - {name: b, image: /tmp/i.png}\n")
        self.assertEqual(len(P.load_queue(j)), 2)
        self.assertEqual(P.load_queue(y)[1]["name"], "b")

    def test_bad_specs_rejected(self):
        for bad in ({"name": "a b", "prompt": "x"}, {"name": "a"}, {"name": "a", "prompt": "x", "image": "y"},
                    {"name": "a", "prompt": "x", "kind": "character"}, {"name": "a", "prompt": "x", "class": "huge"}):
            with self.assertRaises(ValueError, msg=bad):
                P.validate_spec(bad)

    def test_runs_all_assets_and_logs_rows(self):
        rig = Rig()
        c, _ = self.chain(rig)
        res = c.run_queue([{"name": "a", "prompt": "x"}, {"name": "b", "prompt": "y"}])
        self.assertTrue(all(r["ok"] for r in res))
        rows = (self.t / "log.csv").read_text().splitlines()
        self.assertEqual(rows[0].split(",")[0], "timestamp_iso")
        stages = [r.split(",")[2] for r in rows[1:]]
        for s in ("chain:image:local", "chain:3d:triposplat", "chain:texture:passthrough", "chain:cleanup:blender", "chain:total"):
            self.assertEqual(stages.count(s), 2, s)
        man = json.loads((self.t / "out/a/ue_import_manifest.json").read_text())
        self.assertEqual(man["assets"][0]["dest"], "/Game/Props/a")
        self.assertTrue((self.t / "out/a/ue_import_manifest.py").is_file())
        self.assertTrue(json.loads((self.t / "out/a/qa.json").read_text())["within_budget"])


class TestResume(Base):
    def test_second_run_skips_everything(self):
        rig = Rig()
        c, _ = self.chain(rig)
        spec = {"name": "a", "prompt": "x"}
        c.run_queue([spec])
        n = len(rig.calls)
        c.run_queue([spec])
        self.assertEqual(len(rig.calls), n)
        self.assertIn("skipped", (self.t / "log.csv").read_text())

    def test_changed_prompt_reruns_from_image(self):
        rig = Rig()
        c, _ = self.chain(rig)
        c.run_queue([{"name": "a", "prompt": "x"}])
        n = len(rig.calls)
        c.run_queue([{"name": "a", "prompt": "y"}])
        self.assertEqual(len(rig.calls) - n, 4)

    def test_changed_budget_reruns_only_cleanup(self):
        rig = Rig()
        c, _ = self.chain(rig)
        c.run_queue([{"name": "a", "prompt": "x"}])
        n = len(rig.calls)
        c.run_queue([{"name": "a", "prompt": "x", "tri_budget": 900}])
        self.assertEqual(rig.calls[n:], [("a", "cleanup", "blender")])


class TestLanes(Base):
    def test_never_two_gpu_jobs(self):
        rig = Rig(delay=0.03)
        c, lanes = self.chain(rig)
        res = c.run_queue([{"name": f"a{i}", "prompt": "x"} for i in range(5)], workers=5)
        self.assertTrue(all(r["ok"] for r in res), res)
        self.assertEqual(rig.gpu_peak, 1)
        self.assertEqual(lanes.peak["gpu"], 1)

    def test_cloud_runs_in_parallel(self):
        rig = Rig(delay=0.05)
        c, lanes = self.chain(rig, engine_override={"image": "gpt"})
        c.run_queue([{"name": f"a{i}", "prompt": "x"} for i in range(3)], workers=3)
        self.assertGreater(lanes.peak["cloud"], 1)

    def test_preflight_failure_blocks_gpu_stage(self):
        rig = Rig()
        c, _ = self.chain(rig, preflight=lambda: (False, "busy"))
        res = c.run_queue([{"name": "a", "prompt": "x"}])
        self.assertFalse(res[0]["ok"])
        self.assertIn("gpu-preflight", res[0]["error"])


class TestLicence(Base):
    def test_unlisted_or_bad_verdict_refused(self):
        g = self.licence({"foo": {"verdict": "non-commercial"}, "bar": {"verdict": "ok"}})
        with self.assertRaises(LicenceError):
            g.check("image", "foo")
        with self.assertRaises(LicenceError):
            g.check("image", "missing")
        self.assertEqual(g.check("image", "bar")["verdict"], "ok")

    def test_hunyuan_always_banned_even_if_listed_ok(self):
        g = self.licence({"hunyuan3d": {"verdict": "ok"}})
        with self.assertRaises(LicenceError):
            g.check("3d", "hunyuan3d")

    def test_fallback_without_file_warns_and_allows_only_three(self):
        g = self.licence(None)
        self.assertTrue(self.warnings)
        for ok in ("triposplat", "gpt", "blender"):
            g.check("x", ok)
        with self.assertRaises(LicenceError):
            g.check("image", "grok")

    def test_auto_skips_refused_engine_but_explicit_fails(self):
        rig = Rig()
        table = {k: {"verdict": "ok"} for k in ("gpt", "triposplat", "passthrough", "blender")}
        table["local"] = {"verdict": "non-commercial"}
        c, _ = self.chain(rig, table=table)
        res = c.run_queue([{"name": "a", "prompt": "x"}])
        self.assertTrue(res[0]["ok"], res)
        self.assertEqual(json.loads((self.t / "out/a/provenance.json").read_text())["stages"]["image"]["engine"], "gpt")
        c2, _ = self.chain(Rig(), table=table, engine_override={"image": "local"})
        res = c2.run_queue([{"name": "b", "prompt": "x"}])
        self.assertFalse(res[0]["ok"])
        self.assertIn("refused", res[0]["error"])

    def test_falls_through_when_engine_fails(self):
        rig = Rig()
        reg = rig.registry()

        def boom(ctx):
            raise E.StageError("down")
        reg[("image", "local")] = E.Engine("image", "local", "gpu", boom)
        gate = self.licence({k: {"verdict": "ok"} for k in ("local", "gpt", "grok", "triposplat", "passthrough", "blender")})
        c = P.Chain(reg, gate, self.t / "out", self.t / "log.csv", self.t / "credits.md", P.Lanes(self.t / "l"))
        res = c.run_queue([{"name": "a", "prompt": "x"}])
        self.assertTrue(res[0]["ok"], res)
        self.assertIn(",1,", [ln for ln in (self.t / "log.csv").read_text().splitlines() if "image:local" in ln][0])


class TestSidecarAndCredits(Base):
    def test_provenance_and_credits(self):
        rig = Rig()
        c, _ = self.chain(rig, engine_override={"image": "grok"})
        c.run_queue([{"name": "a", "prompt": "x"}])
        prov = json.loads((self.t / "out/a/provenance.json").read_text())
        self.assertEqual(set(prov["stages"]), {"image", "3d", "texture", "cleanup"})
        img = prov["stages"]["image"]
        self.assertEqual((img["engine"], img["licence_verdict"], img["credit"]), ("grok", "ok-with-credit", "Images by xAI Grok"))
        self.assertEqual(len(img["output_sha256"]), 64)
        self.assertIn("Images by xAI Grok", (self.t / "credits.md").read_text())
        self.assertIn("Images by xAI Grok", json.loads((self.t / "out/a/qa.json").read_text())["licence_line"])
        c.write_credits()  # idempotent: markers are replaced, not duplicated
        self.assertEqual((self.t / "credits.md").read_text().count(P.CREDITS_BEGIN), 1)

    def test_uc2_path_refused(self):
        c, _ = self.chain(Rig())
        res = c.run_queue([{"name": "ok", "prompt": "x"}])
        self.assertTrue(res[0]["ok"])
        c.out_root = self.t / "uc2"
        self.assertFalse(c.run_queue([{"name": "b", "prompt": "x"}])[0]["ok"])


class TestGuarded(Base):
    """Bounded retries, coded fallback, thin kinds. Fake generator and cleanup: no Blender, no GPU, no model."""
    KNOWN = ["crate", "barrel", "fence"]

    def rig_cleanup_fails(self, rig, counter):
        reg = rig.registry()

        def bad(ctx):
            counter.append(1)
            raise E.StageError("blender exit 1: pinwheel hub not manifold")
        reg[("cleanup", "blender")] = E.Engine("cleanup", "blender", "cpu", bad)
        rig.registry = lambda: reg
        return rig

    def builder(self, built):
        def build(prop, out_dir):
            built.append(prop)
            out_dir = Path(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            glb = out_dir / f"{prop}.glb"
            glb.write_text(f"coded {prop}")
            return glb
        return build

    def test_cleanup_failure_stops_after_n_tries_with_one_line(self):
        calls = []
        rig = self.rig_cleanup_fails(Rig(), calls)
        c, _ = self.chain(rig)
        for tries in (2, 3):
            calls.clear()
            r = A.run_guarded(c, {"name": "stake", "prompt": "anchor stake"}, tries=tries, known=self.KNOWN)
            self.assertFalse(r["ok"])
            self.assertEqual(len(calls), tries)
            self.assertNotIn("\n", r["error"])
            self.assertIn("pinwheel hub", r["error"])
            self.assertIn("hand-code it in Blender", r["error"])

    def test_error_names_the_fallback_to_use(self):
        c, _ = self.chain(self.rig_cleanup_fails(Rig(), []))
        r = A.run_guarded(c, {"name": "crate", "prompt": "wooden crate"}, known=self.KNOWN)
        self.assertFalse(r["ok"])
        self.assertIn("--fallback procedural", r["error"])
        self.assertIn("coded crate", r["error"])

    def test_fallback_builds_coded_prop_and_records_it(self):
        built = []
        c, _ = self.chain(self.rig_cleanup_fails(Rig(), []))
        r = A.run_guarded(c, {"name": "wooden_crate", "prompt": "weathered box"}, fallback="procedural",
                          known=self.KNOWN, build=self.builder(built))
        self.assertTrue(r["ok"], r)
        self.assertEqual((built, r["fallback"]), (["crate"], "crate"))
        self.assertEqual(Path(r["glb"]).read_text(), "coded crate")
        prov = json.loads((self.t / "out/wooden_crate/provenance.json").read_text())
        self.assertEqual(prov["shipped_mesh"], "procedural-fallback")
        self.assertIn("pinwheel hub", prov["ai_failure"])
        self.assertIn("fallback:procedural:crate", (self.t / "log.csv").read_text())
        self.assertFalse((self.t / "out/wooden_crate/ue_import_manifest.json").exists())
        self.assertTrue((self.t / "out/wooden_crate/game/wooden_crate.glb").is_file())

    def test_fallback_without_a_matching_prop_is_one_clear_line(self):
        built = []
        c, _ = self.chain(self.rig_cleanup_fails(Rig(), []))
        r = A.run_guarded(c, {"name": "lantern", "prompt": "iron lantern"}, fallback="procedural",
                          known=self.KNOWN, build=self.builder(built))
        self.assertFalse(r["ok"])
        self.assertEqual(built, [])
        self.assertIn("no coded prop", r["error"])

    def test_failed_coded_build_is_reported_not_raised(self):
        def boom(prop, out_dir):
            raise RuntimeError("blender gone")
        c, _ = self.chain(self.rig_cleanup_fails(Rig(), []))
        r = A.run_guarded(c, {"name": "crate", "prompt": "x"}, fallback="procedural", known=self.KNOWN, build=boom)
        self.assertFalse(r["ok"])
        self.assertIn("blender gone", r["error"])

    def test_preview_reject_retries_with_fresh_mesh_then_gives_up(self):
        rig = Rig()
        c, _ = self.chain(rig)
        seen = []

        def check(res):
            seen.append(res["name"])
            return False, "aspect_mismatch: thin footprint"
        r = A.run_guarded(c, {"name": "balloon", "prompt": "red balloon"}, tries=2, check=check, known=self.KNOWN)
        self.assertFalse(r["ok"])
        self.assertEqual(len(seen), 2)
        # the 3D stage really ran again (the cache was dropped), and the bad mesh is never reported as OK
        self.assertEqual([x for x in rig.calls if x[1] == "3d"].__len__(), 2)
        self.assertIn("preview rejected", r["error"])

    def test_preview_reject_then_fallback_ships_coded_not_ai(self):
        built = []
        c, _ = self.chain(Rig())
        r = A.run_guarded(c, {"name": "barrel", "prompt": "barrel"}, check=lambda res: (False, "broken shape"),
                          fallback="procedural", known=self.KNOWN, build=self.builder(built))
        self.assertTrue(r["ok"])
        self.assertEqual(built, ["barrel"])
        self.assertFalse((self.t / "out/barrel/ue_import_manifest.json").exists())  # stale AI manifest removed
        self.assertEqual(json.loads((self.t / "out/barrel/provenance.json").read_text())["shipped_mesh"], "procedural-fallback")

    def test_good_result_passes_through_untouched(self):
        c, _ = self.chain(Rig())
        r = A.run_guarded(c, {"name": "crate", "prompt": "x"}, check=lambda res: (True, ""), known=self.KNOWN)
        self.assertTrue(r["ok"])
        self.assertNotIn("fallback", r)

    def test_thin_kinds_skip_the_ai_chain(self):
        for nm in ("flag", "party_flags", "pinwheel", "ribbon", "desk_fan"):
            self.assertIsNotNone(A.thin_kind({"name": nm, "prompt": "x"}), nm)
        self.assertIsNone(A.thin_kind({"name": "flagstone", "prompt": "stone"}))
        self.assertIsNone(A.thin_kind({"name": "crate", "prompt": "wooden crate"}))
        rig = Rig()
        built = []
        c, _ = self.chain(rig)
        known = self.KNOWN + ["flag"]
        r = A.run_guarded(c, {"name": "flag", "prompt": "pennant"}, known=known, build=self.builder(built))
        self.assertTrue(r["ok"])
        self.assertEqual((rig.calls, built), ([], ["flag"]))  # no image/3D/cleanup call at all

    def test_thin_kind_without_coded_prop_says_so_and_spends_nothing(self):
        rig = Rig()
        c, _ = self.chain(rig)
        r = A.run_guarded(c, {"name": "pinwheel", "prompt": "toy pinwheel"}, known=self.KNOWN)
        self.assertFalse(r["ok"])
        self.assertEqual(rig.calls, [])
        self.assertIn("no coded pinwheel", r["error"])
        self.assertNotIn("\n", r["error"])

    def test_force_ai_overrides_thin_rule(self):
        rig = Rig()
        c, _ = self.chain(rig)
        r = A.run_guarded(c, {"name": "flag", "prompt": "pennant"}, known=self.KNOWN, force_ai=True)
        self.assertTrue(r["ok"])
        self.assertTrue(rig.calls)

    def test_queue_one_bad_asset_does_not_stop_the_rest(self):
        c, _ = self.chain(Rig())
        res = A.run_queue_guarded(c, [{"name": "crate", "prompt": "x"}, {"name": "pinwheel", "prompt": "y"}],
                                  workers=2, known=self.KNOWN)
        self.assertEqual([r["ok"] for r in res], [True, False])

    def test_bad_name_is_refused_before_any_disk_write(self):
        victim = self.t / "escape_flag" / "game"
        victim.mkdir(parents=True)
        (victim / "keep.txt").write_text("not ours")
        c, _ = self.chain(Rig())
        r = A.run_guarded(c, {"name": "../escape_flag", "prompt": "pennant"}, known=["flag"], build=self.builder([]))
        self.assertFalse(r["ok"])
        self.assertTrue((victim / "keep.txt").exists())

    def test_uc2_path_refused_on_the_fallback_path(self):
        c, _ = self.chain(Rig())
        c.out_root = self.t / "UC2004_out"
        r = A.run_guarded(c, {"name": "flag", "prompt": "pennant"}, known=["flag"], build=self.builder([]))
        self.assertFalse(r["ok"])
        self.assertFalse((self.t / "UC2004_out").exists())

    def test_only_the_name_picks_a_coded_prop_or_a_thin_kind(self):
        built = []
        c, _ = self.chain(Rig())
        r = A.run_guarded(c, {"name": "pinwheel", "prompt": "toy pinwheel stuck in a crate"}, known=self.KNOWN,
                          build=self.builder(built))
        self.assertEqual((r["ok"], built), (False, []))
        self.assertIsNone(A.thin_kind({"name": "lantern", "prompt": "iron lantern, no flags or ribbons"}))
        self.assertIsNone(A.match_procedural({"name": "lantern", "prompt": "hangs on a fence"}, self.KNOWN))

    def test_giving_up_removes_the_rejected_mesh_records(self):
        c, _ = self.chain(Rig())
        r = A.run_guarded(c, {"name": "balloon", "prompt": "red balloon"}, tries=2,
                          check=lambda res: (False, "thin"), known=[])
        self.assertFalse(r["ok"])
        w = self.t / "out/balloon"
        for gone in ("ue_import_manifest.json", "qa.json", "provenance.json", "game"):
            self.assertFalse((w / gone).exists(), gone)

    def test_only_the_head_noun_picks_a_coded_prop(self):
        known = self.KNOWN + ["flag"]
        self.assertEqual(A.match_procedural({"name": "fence_flag"}, known), "flag")  # a coded flag, not a fence
        known = self.KNOWN
        self.assertEqual(A.match_procedural({"name": "red_crate"}, known), "crate")
        self.assertEqual(A.match_procedural({"name": "party_flags"}, known + ["flag"]), "flag")
        for nm in ("crate_lid", "barrel_hoop", "fence_post", "fence_flag"):
            self.assertIsNone(A.match_procedural({"name": nm}, known), nm)
        built = []
        c, _ = self.chain(Rig())
        r = A.run_guarded(c, {"name": "fence_flag", "prompt": "cloth flag hung on a fence"}, known=known,
                          build=self.builder(built))
        self.assertEqual(built, [])  # no whole coded fence shipped as the flag
        self.assertFalse(r["ok"])
        r = A.run_guarded(c, {"name": "crate_lid", "prompt": "lid"}, tries=1, fallback="procedural", known=known,
                          build=self.builder(built), check=lambda res: (False, "thin"))
        self.assertEqual((r["ok"], built), (False, []))

    def test_cleanup_failure_regenerates_the_mesh_each_try(self):
        calls, rig = [], Rig()
        rig = self.rig_cleanup_fails(rig, calls)
        c, _ = self.chain(rig)
        r = A.run_guarded(c, {"name": "stake", "prompt": "anchor stake"}, tries=2, known=[])
        self.assertFalse(r["ok"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(sum(1 for x in rig.calls if x[1] == "3d"), 2)  # one real AI try per try, no replay

    def test_preview_check_rejects_shredded_mesh_without_expect_aspect(self):
        import asset_preview as AP
        w = self.t / "out/balloon"
        (w / "game").mkdir(parents=True)
        (w / "game/balloon.glb").write_text("glb")
        stats = {"size_m": [0.4, 0.4, 0.6], "tris": 9000, "mesh_objects": 140, "non_manifold_edges": 4200,
                 "materials": ["M"], "textures": [{"role": "albedo", "exists": True}]}
        old = (AP.find_blender, AP.preview_one)
        AP.find_blender = lambda explicit=None: "/usr/bin/blender"
        AP.preview_one = lambda *a, **k: {"flags": AP.compute_flags(stats), "ok": True}
        try:
            ok, why = A.preview_check()({"name": "balloon", "manifest": str(w / "ue_import_manifest.json")})
        finally:
            AP.find_blender, AP.preview_one = old
        self.assertFalse(ok)
        self.assertIn("non_manifold", why)

    def test_failed_thin_build_leaves_the_earlier_shipped_mesh(self):
        c, _ = self.chain(Rig())
        r = A.run_guarded(c, {"name": "flag", "prompt": "pennant"}, force_ai=True, known=[])
        self.assertTrue(r["ok"])
        w = self.t / "out/flag"
        before = {p.name for p in w.iterdir()}

        def boom(prop, out_dir):
            raise RuntimeError("blender missing")
        r = A.run_guarded(c, {"name": "flag", "prompt": "pennant"}, known=["flag"], build=boom)
        self.assertFalse(r["ok"])
        self.assertIn("blender missing", r["error"])
        self.assertTrue((w / "game").is_dir())
        self.assertTrue((w / "ue_import_manifest.json").exists())
        self.assertEqual({p.name for p in w.iterdir()}, before)  # nothing purged, no temp folder left behind

    def test_per_spec_aspect_overrides_the_queue_flag(self):
        import asset_preview as AP
        seen = {}
        old = (AP.find_blender, AP.preview_one)
        AP.find_blender = lambda explicit=None: "/usr/bin/blender"

        def fake(glb, exe, out_dir=None, expect_aspect=None, **kw):
            seen[Path(glb).stem] = expect_aspect
            return {"flags": []}
        AP.preview_one = fake
        try:
            for nm in ("crate", "lamp_post"):
                w = self.t / "out" / nm
                (w / "game").mkdir(parents=True)
                (w / "game" / f"{nm}.glb").write_text("glb")
            chk = A.preview_check((1, 1, 0.1), aspects={"lamp_post": "1:4:0.1"})
            for nm in ("crate", "lamp_post"):
                chk({"name": nm, "manifest": str(self.t / "out" / nm / "ue_import_manifest.json")})
        finally:
            AP.find_blender, AP.preview_one = old
        self.assertEqual(seen, {"crate": (1, 1, 0.1), "lamp_post": (1, 4, 0.1)})

    def test_bad_aspect_fails_that_asset_only_and_names_it(self):
        c, _ = self.chain(Rig())
        specs = [{"name": "lamp_post", "prompt": "lamp post", "aspect": 64},  # YAML 1.1 read of unquoted 1:4
                 {"name": "sign", "prompt": "sign", "aspect": "wide"},
                 "not a mapping",
                 {"name": "crate", "prompt": "wooden crate"}]
        res = A.run_queue_guarded(c, specs, 1, known=[])
        self.assertEqual([r["ok"] for r in res], [False, False, False, True])
        self.assertIn("lamp_post", res[0]["error"])
        self.assertIn("quote it", res[0]["error"])
        self.assertIn("sign", res[1]["error"])
        self.assertNotIn("--expect-aspect", res[0]["error"] + res[1]["error"])

    def test_thin_kind_is_the_head_noun_like_the_coded_match(self):
        self.assertIsNone(A.thin_kind({"name": "flag_pole"}))
        self.assertEqual(A.thin_kind({"name": "pirate_flag"}), "flag")
        self.assertEqual(A.thin_kind({"name": "party_flags"}), "flag")
        c, _ = self.chain(Rig())
        built = []
        r = A.run_guarded(c, {"name": "flag_pole", "prompt": "steel pole"}, known=self.KNOWN + ["flag"],
                          build=self.builder(built))
        self.assertEqual((r["ok"], built), (True, []))  # went through the AI chain, no coded flag

    def test_procedural_props_read_from_the_real_script(self):
        self.assertEqual(A.procedural_props(), ["crate", "barrel", "fence"])
        self.assertEqual(A.procedural_props(self.t / "missing.py"), [])


if __name__ == "__main__":
    unittest.main()
