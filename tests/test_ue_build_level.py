import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import layout_spec as ls  # noqa: E402
import ue_build_level as ubl  # noqa: E402

EXAMPLE = os.path.join(ROOT, "stages", "02_build", "references", "layout-spec", "example-layout.json")


class Vec:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = x, y, z


class FakeActor:
    def __init__(self, loc):
        self.loc, self.label, self.tags, self.scale = loc, None, [], None

    def set_actor_label(self, label):
        self.label = label

    def set_actor_scale3d(self, scale):
        self.scale = scale

    def get_actor_bounds(self, _only_colliding):
        return Vec(self.loc.x, self.loc.y, 0.0), Vec(10, 10, 10)  # sits on the floor already

    def get_actor_location(self):
        return self.loc

    def set_actor_location(self, loc, *_):
        self.loc = loc

    def get_component_by_class(self, _cls):
        return mock.MagicMock()

    def set_actor_rotation(self, *_):
        pass


def make_fake_unreal():
    fake = mock.MagicMock()
    fake.Vector = Vec
    fake.spawned = []

    def spawn(_what, loc):
        actor = FakeActor(loc)
        fake.spawned.append(actor)
        return actor

    actor_subsys = mock.MagicMock()
    actor_subsys.spawn_actor_from_object.side_effect = spawn
    actor_subsys.spawn_actor_from_class.side_effect = spawn
    level_subsys = mock.MagicMock()
    editor_subsys = mock.MagicMock()
    fake.state = {"path": None}

    def new_level(path):
        fake.state["path"] = path

    level_subsys.new_level.side_effect = new_level
    editor_subsys.get_editor_world.return_value.get_path_name.side_effect = lambda: fake.state["path"] or ""
    subsystems = {fake.UnrealEditorSubsystem: editor_subsys, fake.EditorActorSubsystem: actor_subsys,
                  fake.LevelEditorSubsystem: level_subsys}
    fake.get_editor_subsystem.side_effect = lambda cls: subsystems[cls]
    fake.existing = set()  # asset paths that "exist" in the fake project (levels start absent)
    fake.EditorAssetLibrary.does_asset_exist.side_effect = lambda p: p in fake.existing
    fake.EditorAssetLibrary.save_asset.return_value = True
    return fake


def build(plan=None, existing=(), beacon="/Game/B", orb="/Game/O"):
    fake = make_fake_unreal()
    fake.existing.update(existing)
    with mock.patch.object(ubl, "unreal", fake):
        ubl.build_level(beacon, orb, plan)
    return fake


class DefaultPathUnchanged(unittest.TestCase):
    def test_default_cli_args(self):
        args = ubl._parse_cli_args([])
        self.assertIsNone(args.plan)
        self.assertTrue(args.beacon_mesh.endswith("SM_Beacon"))
        self.assertTrue(args.orb_mesh.endswith("SM_Orb"))

    def test_fixed_room_still_built(self):
        fake = build()
        labels = [a.label for a in fake.spawned]
        for want in ("Floor", "Wall_North", "Wall_South", "Wall_East", "Wall_West", "PlayerStart", "Beacon", "PlayerOrb"):
            self.assertIn(want, labels)
        fake.EditorAssetLibrary.save_asset.assert_called_once_with(ubl.LEVEL_PATH, only_if_is_dirty=False)
        start = next(a for a in fake.spawned if a.label == "PlayerStart")
        self.assertEqual((start.loc.x, start.loc.y, start.loc.z), (-300.0, 0.0, 50.0))
        beacon = next(a for a in fake.spawned if a.label == "Beacon")
        self.assertEqual((beacon.loc.x, beacon.loc.y), (300.0, 0.0))
        self.assertEqual(beacon.tags, [ubl.OBJECTIVE_TAG])
        orb = next(a for a in fake.spawned if a.label == "PlayerOrb")
        self.assertEqual((orb.loc.x, orb.loc.y), (-150.0, 150.0))


class PlanPath(unittest.TestCase):
    def plan(self):
        with open(EXAMPLE, encoding="utf-8") as fh:
            return ls.build_plan(json.load(fh), ls.load_metrics())

    def test_plan_builds_cubes_start_and_beacon_at_plan_positions(self):
        plan = self.plan()
        fake = build(plan)
        labels = [a.label for a in fake.spawned]
        for c in plan["cubes"]:
            self.assertIn(c["label"], labels)
        self.assertNotIn("Wall_North", labels)
        start = next(a for a in fake.spawned if a.label == "PlayerStart")
        self.assertEqual((start.loc.x, start.loc.y, start.loc.z), (-200, 0, 50.0))
        beacon = next(a for a in fake.spawned if a.label == "Beacon")
        self.assertEqual((beacon.loc.x, beacon.loc.y), (1200, 0))
        self.assertEqual(beacon.tags, [ubl.OBJECTIVE_TAG])
        orb = next(a for a in fake.spawned if a.label == "PlayerOrb")
        self.assertEqual((orb.loc.x, orb.loc.y), (-50, 150))

    def loaded(self, fake):
        return [c.args[0] for c in fake.EditorAssetLibrary.load_asset.call_args_list]

    # Every wall/floor cube also loads the Cube shape, so count loads: cubes (+1 when the beacon falls back).
    def test_missing_meshes_fall_back_to_basic_shapes_in_plan_mode(self):
        plan = self.plan()
        loaded = self.loaded(build(plan))  # /Game/B and /Game/O are not in the fake project
        self.assertEqual(loaded.count(ubl.FALLBACK_BEACON), len(plan["cubes"]) + 1)
        self.assertEqual(loaded.count(ubl.FALLBACK_ORB), 1)
        self.assertNotIn("/Game/B", loaded)

    def test_mesh_args_may_be_empty_in_plan_mode(self):
        plan = self.plan()
        loaded = self.loaded(build(plan, beacon=None, orb=""))
        self.assertEqual(loaded.count(ubl.FALLBACK_BEACON), len(plan["cubes"]) + 1)
        self.assertEqual(loaded.count(ubl.FALLBACK_ORB), 1)

    def test_existing_meshes_are_used_in_plan_mode(self):
        plan = self.plan()
        loaded = self.loaded(build(plan, existing={"/Game/B", "/Game/O"}))
        self.assertIn("/Game/B", loaded)
        self.assertIn("/Game/O", loaded)
        self.assertEqual(loaded.count(ubl.FALLBACK_BEACON), len(plan["cubes"]))
        self.assertNotIn(ubl.FALLBACK_ORB, loaded)

    def test_no_plan_still_loads_the_named_meshes_without_fallback(self):
        loaded = self.loaded(build())
        self.assertIn("/Game/B", loaded)
        self.assertEqual(loaded.count(ubl.FALLBACK_BEACON), 5)  # floor + 4 walls only

    def test_orb_comes_from_the_plan_and_old_plans_keep_the_offset(self):
        plan = self.plan()
        plan["orb"] = [10.0, 20.0, 0.0]
        orb = next(a for a in build(plan).spawned if a.label == "PlayerOrb")
        self.assertEqual((orb.loc.x, orb.loc.y), (10.0, 20.0))
        del plan["orb"]
        orb = next(a for a in build(plan).spawned if a.label == "PlayerOrb")
        self.assertEqual((orb.loc.x, orb.loc.y), (-50, 150))
        plan["orb"] = [1, 2]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "p.json")
            with open(p, "w") as fh:
                json.dump(plan, fh)
            with self.assertRaises(ValueError):
                ubl.load_plan(p)

    def test_plan_saves_its_own_level_path(self):
        plan = self.plan()
        fake = build(plan)
        fake.EditorAssetLibrary.save_asset.assert_called_once_with(plan["level_path"], only_if_is_dirty=False)

    def write(self, data):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = os.path.join(d.name, "plan.json")
        with open(p, "w") as fh:
            json.dump(data, fh)
        return p

    def test_load_plan_accepts_good_and_rejects_bad(self):
        good = self.plan()
        self.assertEqual(ubl.load_plan(self.write(good))["level_path"], good["level_path"])
        bad_cases = [
            {**good, "format": "other"},
            {**good, "level_path": "/Game/Maps/L_Main"},
            {**good, "cubes": []},
            {**good, "player_start": [1, 2]},
            {**good, "cubes": [{"label": "x"}]},
        ]
        for bad in bad_cases:
            with self.subTest(bad=list(bad)[:0] or str(bad)[:60]):
                with self.assertRaises(ValueError):
                    ubl.load_plan(self.write(bad))

    def test_plan_flag_parsed(self):
        self.assertEqual(ubl._parse_cli_args(["--plan", "/x/p.json"]).plan, "/x/p.json")


if __name__ == "__main__":
    unittest.main()
