import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import fake_editor as fe  # noqa: E402


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    os.environ.setdefault("CREW_MODE", "dry")
    spec.loader.exec_module(mod)
    return mod


os.environ["CREW_LOG"] = os.path.join(tempfile.gettempdir(), "crew_test.log")
crew = load("ue_scatter_crew", "scripts/ue_scatter_crew.py")
gen_asset = load("gen_asset_for_crew_test", "scripts/gen_asset.py")


class Layout(unittest.TestCase):
    def plan(self, **kw):
        return crew.plan_layout(crew.S1_STUNTS_M, crew.S1_MARKS_M, **kw)

    def test_surge_distance_matches_the_s1_table(self):
        surges = [(35.0, 6.0)]
        got = [round(crew.dist_at(t, 18.0, surges)) for t in (7, 9, 35, 37)]
        self.assertEqual(got, [126, 162, 648, 684])

    def test_default_side_is_left_and_off_the_road(self):
        plan = self.plan()
        self.assertGreater(len(plan), 60)
        for p in plan:
            self.assertLess(p["lat"], 0)
            self.assertGreaterEqual(abs(p["lat"]), crew.ROAD_HALF_M + 2.5)

    def test_every_mark_cluster_has_camera_and_two_fresnels_aimed_at_the_stunt(self):
        plan = self.plan()
        for i, stunt in enumerate(crew.S1_STUNTS_M):
            mine = [p for p in plan if p["cluster"] == i]
            self.assertEqual(sum(p["kind"] == "camera" for p in mine), 1)
            fres = [p for p in mine if p["kind"] == "fresnel"]
            self.assertEqual(len(fres), 2)
            for f in fres:
                self.assertEqual(f["face"], (stunt, 0.0))

    def test_denser_at_marks_than_between(self):
        plan = self.plan()
        near = sum(1 for p in plan if min(abs(p["dist"] - m) for m in crew.S1_MARKS_M) < 15)
        far = len(plan) - near
        near_len = 30.0 * len(crew.S1_MARKS_M)  # metres of road within 15 m of a mark
        far_len = 720.0 - near_len
        self.assertGreater(near / near_len, 3 * far / far_len)  # items per metre

    def test_right_side_keeps_clear_of_mark_signs(self):
        plan = self.plan(side="right")
        for p in plan:
            if crew.SIGN_LAT_M - 2 < p["lat"] < crew.SIGN_LAT_M + 2:
                self.assertTrue(all(abs(p["dist"] - m) >= 4.4 for m in crew.S1_MARKS_M), p)

    def test_kinds_filter_and_density_and_seed(self):
        only = self.plan(kinds=["camera", "fresnel"])
        self.assertEqual({p["kind"] for p in only}, {"camera", "fresnel"})
        self.assertEqual(self.plan(seed=5), self.plan(seed=5))
        self.assertLess(len(self.plan(density=0.0)), len(self.plan(density=1.0)))

    def test_no_two_props_overlap(self):
        plan = self.plan()
        for i, a in enumerate(plan):
            for b in plan[i + 1:]:
                gap = ((a["dist"] - b["dist"]) ** 2 + (a["lat"] - b["lat"]) ** 2) ** 0.5
                self.assertGreater(gap, (crew.KINDS[a["kind"]]["radius"] + crew.KINDS[b["kind"]]["radius"]) * 0.9)


def load_crew(editor, mode="dry"):
    return fe.load_script("scripts/ue_scatter_crew.py", "ue_scatter_crew_fake", editor, "CREW_MODE", mode)


ARGS = dict(side="left", density=1.0, kinds=None)
OTHER = "/Game/Maps/L_Other"


class Guards(fe.QuietCase):
    """apply / revert against a fake editor: never throw away unsaved edits, stop before changing anything on a bad level."""

    def setUp(self):
        super().setUp()
        self.old_level = os.environ.pop("CREW_LEVEL", None)

    def tearDown(self):
        if self.old_level is not None:
            os.environ["CREW_LEVEL"] = self.old_level

    def test_dry_changes_nothing(self):
        ed = fe.Editor()
        load_crew(ed, "dry")
        self.assertEqual(ed.calls, [])

    def test_same_level_open_is_not_reloaded_and_dirty_edits_survive(self):
        ed = fe.Editor(dirty=[fe.LEVEL])  # unsaved lead edits in the open level
        mod = load_crew(ed)
        mod.apply(ARGS)
        self.assertNotIn("load_map", ed.mutations())
        self.assertEqual(ed.discarded, [])
        self.assertGreater(len(ed.tagged(mod.TAG)), 60)
        self.assertIn("save_current_level", ed.mutations())  # the save writes the lead's edits out with ours

    def test_revert_same_level_no_reload_and_only_tagged_actors_go(self):
        ed = fe.Editor(dirty=[fe.LEVEL])
        mod = load_crew(ed)
        mod.apply(ARGS)
        keep = fe.Actor("StaticMeshActor", "LeadsCube")
        ed.actors.append(keep)
        ed.dirty = [fe.LEVEL]
        mod.revert()
        self.assertEqual(ed.tagged(mod.TAG), [])
        self.assertEqual([a.label for a in ed.actors], ["JCRoad", "LeadsCube"])
        self.assertNotIn("load_map", ed.mutations())
        self.assertEqual(ed.discarded, [])

    def test_apply_twice_leaves_the_same_actors(self):
        ed = fe.Editor()
        mod = load_crew(ed)
        mod.apply(ARGS)
        first = sorted(a.label for a in ed.tagged(mod.TAG))
        mod.apply(ARGS)
        self.assertEqual(sorted(a.label for a in ed.tagged(mod.TAG)), first)
        self.assertEqual(len([a for a in ed.actors if a.label.startswith("Crew_")]), len(first))

    def test_other_level_open_and_dirty_aborts_with_nothing_changed(self):
        ed = fe.Editor(open_level=OTHER, levels={OTHER: [], fe.LEVEL: [fe.make_road()]}, dirty=[OTHER])
        mod = load_crew(ed)
        for fn in (lambda: mod.apply(ARGS), mod.revert):
            with self.assertRaisesRegex(RuntimeError, "unsaved changes"):
                fn()
        self.assertEqual(ed.calls, [])
        self.assertEqual(ed.open, OTHER)
        self.assertEqual(ed.dirty, [OTHER])
        self.assertEqual(ed.discarded, [])

    def test_other_level_open_and_clean_is_loaded(self):
        ed = fe.Editor(open_level=OTHER, levels={OTHER: [], fe.LEVEL: [fe.make_road()]})
        mod = load_crew(ed)
        mod.apply(ARGS)
        self.assertEqual(ed.open, fe.LEVEL)
        self.assertEqual(ed.mutations().count("load_map"), 1)
        self.assertGreater(len(ed.tagged(mod.TAG)), 60)

    def test_load_map_returning_none_aborts(self):
        ed = fe.Editor(open_level=OTHER, levels={OTHER: []}, load_ok=False)
        mod = load_crew(ed)
        for fn in (lambda: mod.apply(ARGS), mod.revert):
            with self.assertRaisesRegex(RuntimeError, "load_map.*failed"):
                fn()
        for changed in ("spawn", "save_current_level", "destroy"):
            self.assertNotIn(changed, ed.mutations())

    def test_missing_road_aborts_before_any_actor_is_deleted_or_mesh_saved(self):
        old = fe.Actor("StaticMeshActor", "Crew_camera_00")
        old.props["tags"] = [fe.Name("CrewKit")]
        ed = fe.Editor(levels={fe.LEVEL: [old]})
        mod = load_crew(ed)
        with self.assertRaisesRegex(RuntimeError, "JCRoad"):
            mod.apply(ARGS)
        self.assertEqual(ed.mutations(), [])
        self.assertIn(old, ed.actors)

    def test_failed_level_save_aborts(self):
        ed = fe.Editor(save_ok=False)
        mod = load_crew(ed)
        with self.assertRaisesRegex(RuntimeError, "save_current_level"):
            mod.revert()

    def test_failed_mesh_save_aborts(self):
        ed = fe.Editor(save_asset_ok=False)
        mod = load_crew(ed)
        with self.assertRaisesRegex(RuntimeError, "save_loaded_asset"):
            mod.apply(ARGS)
        self.assertNotIn("spawn", ed.mutations())


class ConceptSidecar(unittest.TestCase):
    def test_load_concept_sidecar_needs_the_matching_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "concept.png"
            png.write_bytes(b"png-bytes")
            side = Path(f"{png}.provenance.json")
            record = {"kind": "concept-image", "provider": "fal", "prompt": "a prop",
                      "image_sha256": hashlib.sha256(b"png-bytes").hexdigest()}
            side.write_text(json.dumps(record))
            self.assertEqual(gen_asset.load_concept_sidecar(png)["prompt"], "a prop")
            png.write_bytes(b"a different image")  # image changed after the sidecar was written
            self.assertIsNone(gen_asset.load_concept_sidecar(png))
            side.write_text(json.dumps({"kind": "other"}))
            self.assertIsNone(gen_asset.load_concept_sidecar(png))


if __name__ == "__main__":
    unittest.main()
