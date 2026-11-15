import importlib.util
import math
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import fake_editor as fe  # noqa: E402
os.environ["DECAL_LOG"] = os.path.join(tempfile.gettempdir(), "decal_test.log")
os.environ["DECAL_MODE"] = "dry"
_spec = importlib.util.spec_from_file_location("ue_decals_road", os.path.join(ROOT, "scripts", "ue_decals_road.py"))
dec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dec)


def rows():
    return [dict(stunt_m=a, mark_m=b, preset=p) for a, b, p in zip(dec.S1_STUNTS_M, dec.S1_MARKS_M, dec.S1_PRESETS)]


class Plan(unittest.TestCase):
    def test_tape_x_in_every_lane_just_past_each_mark(self):
        plan = [p for p in dec.plan_decals(rows()) if p["kind"] == "tape"]
        self.assertEqual(len(plan), 18)
        for m in dec.S1_MARKS_M:
            lanes = sorted(p["lat"] for p in plan if abs(p["dist"] - (m + 1.5)) < 0.01)
            self.assertEqual(lanes, [-4.0, 0.0, 4.0])
        self.assertEqual({p["variant"] for p in plan}, {0, 1, 2})

    def test_skids_start_after_the_stunt_and_stay_on_the_road(self):
        plan = [p for p in dec.plan_decals(rows()) if p["kind"] == "skid"]
        self.assertEqual(len(plan), 6)
        for p, s in zip(plan, dec.S1_STUNTS_M):
            self.assertGreater(p["dist"] - p["size_m"] / 2, s)
            self.assertIn(p["lat"], dec.LANES_M)
        self.assertEqual({p["variant"] for p in plan}, {0, 1})

    def test_ramp_row_puts_the_skid_after_the_landing(self):
        plan = dec.plan_decals([dict(stunt_m=100.0, mark_m=140.0, preset="Ramp")], kinds=["skid"], ramp_land_m=40.0, skid_len_m=8.0)
        self.assertAlmostEqual(plan[0]["dist"] - 4.0, 140.0)

    def test_cones_sit_at_the_kerb_not_on_the_right_sign_spot(self):
        plan = [p for p in dec.plan_decals(rows()) if p["kind"] == "cone"]
        self.assertEqual(len(plan), 24)
        for p in plan:
            self.assertAlmostEqual(abs(p["lat"]), dec.KERB_M)
            self.assertLess(abs(p["lat"]), 7.0)  # inside the road edge, short of the 10.4 m MARK sign

    def test_kinds_filter_and_seed(self):
        self.assertEqual({p["kind"] for p in dec.plan_decals(rows(), kinds=["cone"])}, {"cone"})
        self.assertEqual(dec.plan_decals(rows(), seed=3), dec.plan_decals(rows(), seed=3))

    def test_surge_distance_matches_the_table(self):
        self.assertEqual([round(dec.dist_at(t, 18.0, [(35.0, 6.0)])) for t in (7, 9, 35, 37)], [126, 162, 648, 684])


def ue_axes(roll, pitch, yaw):
    """World directions of a component's local X, Y, Z for Rotator(roll, pitch, yaw): the rows of Core's FRotationTranslationMatrix
    (RotationTranslationMatrix.h:72-84)."""
    sp, sy, sr = (math.sin(math.radians(a)) for a in (pitch, yaw, roll))
    cp, cy, cr = (math.cos(math.radians(a)) for a in (pitch, yaw, roll))
    return ((cp * cy, cp * sy, sp),
            (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp),
            (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp))


class DecalMath(unittest.TestCase):
    """DeferredDecal.usf:152-158: UV = (local Z, local Y), local X is the projection axis."""

    def test_skid_streaks_run_along_the_road_by_default(self):
        for heading in (0.0, 30.0, -75.0, 180.0):
            axes = ue_axes(*dec.decal_rotation_deg(heading, 0.0, "skid"))
            self.assertAlmostEqual(axes[0][2], -1.0)  # projection axis points straight down
            want = (math.cos(math.radians(heading)), math.sin(math.radians(heading)))
            self.assertAlmostEqual(axes[2][0], want[0])  # local Z = image X (U) = along the road
            self.assertAlmostEqual(axes[2][1], want[1])
            self.assertAlmostEqual(axes[1][0] * want[0] + axes[1][1] * want[1], 0.0)  # local Y (V) is across it

    def test_skid_offset_knob_only_turns_skids(self):
        self.assertEqual(dec.decal_rotation_deg(10.0, 2.0, "skid", 90.0), (0.0, -90.0, 102.0))
        self.assertEqual(dec.decal_rotation_deg(10.0, 2.0, "tape", 90.0), (0.0, -90.0, 12.0))
        self.assertEqual(dec.decal_rotation_deg(10.0, 2.0, "skid"), (0.0, -90.0, 12.0))

    def test_skid_extents_keep_the_2_to_1_texture_undistorted(self):
        depth, y_half, z_half = dec.decal_half_extents_cm("skid", 8.0)
        self.assertEqual((depth, y_half, z_half), (40.0, 200.0, 400.0))  # 8 m along (Z, 1024 px) x 4 m across (Y, 512 px)
        self.assertAlmostEqual((1024 / (2 * z_half)) / (512 / (2 * y_half)), 1.0)  # same pixels per cm both ways

    def test_tape_is_square(self):
        depth, y_half, z_half = dec.decal_half_extents_cm("tape", 1.6)
        self.assertEqual((depth, y_half, z_half), (40.0, 80.0, 80.0))


def load_decals(editor, mode="dry"):
    return fe.load_script("scripts/ue_decals_road.py", "ue_decals_road_fake", editor, "DECAL_MODE", mode)


class Guards(fe.QuietCase):
    """apply / revert against a fake editor: never throw away unsaved edits, stop before changing anything on a bad level."""

    def setUp(self):
        super().setUp()
        self.old_level = os.environ.pop("DECAL_LEVEL", None)

    def tearDown(self):
        if self.old_level is not None:
            os.environ["DECAL_LEVEL"] = self.old_level

    def test_dry_changes_nothing(self):
        ed = fe.Editor()
        load_decals(ed, "dry")
        self.assertEqual(ed.calls, [])

    def test_same_level_open_is_not_reloaded_and_dirty_edits_survive(self):
        ed = fe.Editor(dirty=[fe.LEVEL])  # unsaved lead edits in the open level
        mod = load_decals(ed)
        mod.apply(["cone"])
        self.assertNotIn("load_map", ed.mutations())
        self.assertEqual(ed.discarded, [])
        self.assertEqual(len(ed.tagged(mod.TAG)), 24)
        self.assertIn("save_current_level", ed.mutations())  # the save writes the lead's edits out with ours

    def test_revert_same_level_no_reload_and_only_tagged_actors_go(self):
        ed = fe.Editor(dirty=[fe.LEVEL])
        mod = load_decals(ed)
        mod.apply(["cone"])
        keep = fe.Actor("StaticMeshActor", "LeadsCube")
        ed.actors.append(keep)
        ed.dirty = [fe.LEVEL]
        mod.revert()
        self.assertEqual(ed.tagged(mod.TAG), [])
        self.assertIn(keep, ed.actors)
        self.assertEqual([a.label for a in ed.actors], ["JCRoad", "LeadsCube"])
        self.assertNotIn("load_map", ed.mutations())
        self.assertEqual(ed.discarded, [])

    def test_apply_twice_leaves_the_same_actors(self):
        ed = fe.Editor()
        mod = load_decals(ed)
        mod.apply(None)
        first = sorted(a.label for a in ed.tagged(mod.TAG))
        mod.apply(None)
        self.assertEqual(sorted(a.label for a in ed.tagged(mod.TAG)), first)
        self.assertEqual(len(first), 18 + 6 + 24)

    def test_other_level_open_and_dirty_aborts_with_nothing_changed(self):
        ed = fe.Editor(open_level="/Game/Maps/L_Other",
                       levels={"/Game/Maps/L_Other": [], fe.LEVEL: [fe.make_road()]}, dirty=["/Game/Maps/L_Other"])
        mod = load_decals(ed)
        for fn in (lambda: mod.apply(None), mod.revert):
            with self.assertRaisesRegex(RuntimeError, "unsaved changes"):
                fn()
        self.assertEqual(ed.calls, [])
        self.assertEqual(ed.open, "/Game/Maps/L_Other")
        self.assertEqual(ed.dirty, ["/Game/Maps/L_Other"])
        self.assertEqual(ed.discarded, [])

    def test_other_level_open_and_clean_is_loaded(self):
        ed = fe.Editor(open_level="/Game/Maps/L_Other", levels={"/Game/Maps/L_Other": [], fe.LEVEL: [fe.make_road()]})
        mod = load_decals(ed)
        mod.apply(["cone"])
        self.assertEqual(ed.open, fe.LEVEL)
        self.assertEqual(ed.mutations().count("load_map"), 1)
        self.assertEqual(len(ed.tagged(mod.TAG)), 24)

    def test_load_map_returning_none_aborts(self):
        ed = fe.Editor(open_level="/Game/Maps/L_Other", levels={"/Game/Maps/L_Other": []}, load_ok=False)
        mod = load_decals(ed)
        for fn in (lambda: mod.apply(None), mod.revert):
            with self.assertRaisesRegex(RuntimeError, "load_map.*failed"):
                fn()
        for changed in ("spawn", "save_current_level", "destroy"):
            self.assertNotIn(changed, ed.mutations())

    def test_missing_road_aborts_before_any_actor_is_deleted(self):
        old = fe.Actor("DecalActor", "RoadDressing_old")
        old.props["tags"] = [fe.Name("RoadDressing")]
        ed = fe.Editor(levels={fe.LEVEL: [old]})
        mod = load_decals(ed)
        with self.assertRaisesRegex(RuntimeError, "JCRoad"):
            mod.apply(None)
        self.assertEqual(ed.mutations(), [])
        self.assertIn(old, ed.actors)

    def test_failed_level_save_aborts(self):
        ed = fe.Editor(save_ok=False)
        mod = load_decals(ed)
        with self.assertRaisesRegex(RuntimeError, "save_current_level"):
            mod.revert()

    def test_material_compile_errors_abort_and_drop_the_broken_asset(self):
        ed = fe.Editor(existing_assets=False, recompile_errors=["[Opacity] bad node"])
        mod = load_decals(ed)
        with self.assertRaisesRegex(RuntimeError, "did not compile.*bad node"):
            mod.make_material()
        self.assertEqual(ed.deleted_assets, ["/Game/Materials/Road/M_RoadDecal"])
        self.assertNotIn("save_asset", ed.mutations())

    def test_failed_asset_save_aborts(self):
        ed = fe.Editor(save_asset_ok=False)
        mod = load_decals(ed)
        with self.assertRaisesRegex(RuntimeError, "save_loaded_asset"):
            mod.import_textures()


class PlacedDecals(fe.QuietCase):
    """What apply really hands to the engine for a straight +X road (heading 0)."""

    def apply(self, kinds):
        ed = fe.Editor()
        mod = load_decals(ed)
        mod.apply(kinds)
        return ed, mod

    def test_skid_actors_are_pitched_down_yawed_along_the_road_and_2_to_1(self):
        ed, mod = self.apply(["skid"])
        skids = [a for a in ed.tagged(mod.TAG) if "_skid_" in a.label]
        self.assertEqual(len(skids), 6)
        for a in skids:
            roll, pitch, yaw = a.rot.as_tuple()
            self.assertEqual((roll, pitch), (0.0, -90.0))
            self.assertLessEqual(abs(yaw), 4.0)  # heading 0 plus the planner's +-4 deg jitter, no 90 deg turn
            axes = ue_axes(roll, pitch, yaw)
            self.assertGreater(axes[2][0], 0.99)  # image X runs down the road (+X)
            self.assertEqual(a.comps[fe.DecalComponent].props["decal_size"].as_tuple(), (40.0, 200.0, 400.0))

    def test_tape_actors_are_square(self):
        ed, mod = self.apply(["tape"])
        tapes = [a for a in ed.tagged(mod.TAG) if "_tape_" in a.label]
        self.assertEqual(len(tapes), 18)
        for a in tapes:
            self.assertEqual(a.comps[fe.DecalComponent].props["decal_size"].as_tuple(), (40.0, 80.0, 80.0))

    def test_every_spawned_actor_is_tagged(self):
        ed, mod = self.apply(None)
        spawned = [a for a in ed.actors if a.label.startswith("RoadDressing_")]
        self.assertEqual(len(spawned), len(ed.tagged(mod.TAG)))
        self.assertEqual(len(spawned), 18 + 6 + 24)


if __name__ == "__main__":
    unittest.main()
