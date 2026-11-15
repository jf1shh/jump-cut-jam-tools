"""rig_bones and rig_timelog: pure Python, no Blender."""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import rig_bones  # noqa: E402
import rig_timelog  # noqa: E402


class Layout(unittest.TestCase):
    def test_layout_is_valid(self):
        self.assertEqual(rig_bones.validate(rig_bones.layout(1.8)), [])

    def test_all_retarget_chain_bones_present(self):
        self.assertEqual(rig_bones.missing_chain_bones(rig_bones.layout()), [])

    def test_mannequin_names(self):
        names = {b["name"] for b in rig_bones.layout()}
        for n in ("root", "pelvis", "spine_01", "spine_05", "neck_01", "head", "upperarm_l", "hand_r",
                  "thigh_l", "calf_r", "foot_l", "ball_r", "clavicle_l"):
            self.assertIn(n, names)

    def test_sides_mirror(self):
        by = {b["name"]: b for b in rig_bones.layout(2.0)}
        for stem in ("clavicle", "upperarm", "lowerarm", "hand", "thigh", "calf", "foot", "ball"):
            l, r = by[f"{stem}_l"], by[f"{stem}_r"]
            self.assertEqual(r["head"], (l["head"][0], -l["head"][1], l["head"][2]))
            self.assertEqual(r["parent"], l["parent"].replace("_l", "_r"))
            self.assertGreater(l["head"][1], 0 if stem != "clavicle" else 0.0)

    def test_height_scales_and_head_tops_out(self):
        top = max(b["tail"][2] for b in rig_bones.layout(1.8))
        self.assertAlmostEqual(top, 1.8 * 0.99, places=4)
        self.assertAlmostEqual(max(b["tail"][2] for b in rig_bones.layout(3.6)), 2 * top, places=4)

    def test_bad_height(self):
        with self.assertRaises(ValueError):
            rig_bones.layout(0)

    def test_validate_catches_problems(self):
        bones = rig_bones.layout()
        self.assertTrue(rig_bones.validate(bones + [dict(bones[1])]))            # duplicate
        self.assertTrue(rig_bones.validate(list(reversed(bones))))               # child before parent
        flat = [dict(bones[0]), {**bones[1], "tail": bones[1]["head"]}]
        self.assertTrue(any("zero-length" in p for p in rig_bones.validate(flat)))
        two_roots = [dict(bones[0]), {**bones[1], "parent": None}]
        self.assertTrue(any("root" in p for p in rig_bones.validate(two_roots)))

    def test_renamed_keeps_links(self):
        bones = rig_bones.renamed(rig_bones.layout(), {"pelvis": "Hips"})
        self.assertEqual(rig_bones.validate(bones), [])
        self.assertIn("Hips", {b["name"] for b in bones})
        self.assertEqual(next(b for b in bones if b["name"] == "spine_01")["parent"], "Hips")


class Nearest(unittest.TestCase):
    def test_distance_to_segment(self):
        self.assertAlmostEqual(rig_bones.distance_to_segment((1, 1, 0), (0, 0, 0), (2, 0, 0)), 1.0)
        self.assertAlmostEqual(rig_bones.distance_to_segment((3, 0, 0), (0, 0, 0), (2, 0, 0)), 1.0)  # past the end
        self.assertAlmostEqual(rig_bones.distance_to_segment((1, 0, 0), (1, 0, 0), (1, 0, 0)), 0.0)  # zero length

    def test_nearest_bone_regions(self):
        bones = rig_bones.layout(1.8)
        self.assertEqual(rig_bones.nearest_bone((0, 0.39, 1.2), bones), "upperarm_l")
        self.assertEqual(rig_bones.nearest_bone((0, -0.39, 1.2), bones), "upperarm_r")
        self.assertEqual(rig_bones.nearest_bone((0, 0.39, 0.9), bones), "lowerarm_l")
        self.assertEqual(rig_bones.nearest_bone((0, 0, 1.7), bones), "head")
        self.assertEqual(rig_bones.nearest_bone((0, 0.117, 0.7), bones), "thigh_l")

    def test_wide_torso_corners_go_to_spine_not_limbs(self):
        """Review r2: corners of the wide torso/hip boxes used to go to clavicles and thighs (core got 0)."""
        bones = rig_bones.layout(1.8)
        for z in (0.95, 1.1, 1.25):
            for y in (0.26, -0.26):
                self.assertTrue(rig_bones.nearest_bone((0.05, y, z), bones).startswith(("spine", "pelvis")),
                                (y, z))

    def test_radius_for_names(self):
        self.assertEqual(rig_bones.radius_for("root", 2.0), 0.0)
        self.assertAlmostEqual(rig_bones.radius_for("spine_03", 2.0), 0.28)
        self.assertAlmostEqual(rig_bones.radius_for("DEF-upper_arm.L.001", 1.0), 0.05)
        self.assertAlmostEqual(rig_bones.radius_for("DEF-spine.006", 1.0), 0.10)
        self.assertEqual(rig_bones.radius_for("unknown_bone"), 0.0)

    def test_generic_root_is_skipped_too(self):
        """Review r3: Bone_Root (generic names) was not skipped, so floor points bound to it."""
        generic = rig_bones.renamed(rig_bones.layout(), {"root": "Bone_Root"})
        self.assertNotEqual(rig_bones.nearest_bone((0, 0, 0.0), generic), "Bone_Root")
        self.assertEqual(rig_bones.nearest_bone((0, 0.06, 0.1), generic), "calf_l")

    def test_front_back_check(self):
        body = [(0.0, 0.0, 0.4)] * 5                                  # lower leg (ankle line) at x=0
        fwd = body + [(0.16, 0.0, 0.0), (-0.07, 0.0, 0.0)]            # toes forward of the heels
        back = body + [(0.07, 0.0, 0.0), (-0.16, 0.0, 0.0)]           # the same mesh turned 180 degrees
        even = body + [(0.1, 0.0, 0.0), (-0.1, 0.0, 0.0)]
        self.assertEqual(rig_bones.front_back_problem(fwd, 1.8), (None, None))
        problem, note = rig_bones.front_back_problem(back, 1.8)
        self.assertIn("backwards", problem)
        self.assertIsNone(note)
        problem, note = rig_bones.front_back_problem(even, 1.8)
        self.assertIsNone(problem)
        self.assertIn("assumed", note)  # unverifiable is said plainly, not silently accepted
        self.assertIn("assumed", rig_bones.front_back_problem(body, 1.8)[1])

    def test_root_never_chosen_by_default(self):
        self.assertNotEqual(rig_bones.nearest_bone((0, 0, 0), rig_bones.layout()), "root")

    def test_cli_prints_json(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = rig_bones.main(["--height", "1.5"])
        self.assertEqual(rc, 0)
        data = json.loads(out.getvalue())
        self.assertEqual(data["problems"], [])
        self.assertEqual(data["height"], 1.5)


class Coverage(unittest.TestCase):
    def test_group_of_both_naming_schemes(self):
        for name, group in (("pelvis", "core"), ("spine_03", "core"), ("DEF-spine.003", "core"),
                            ("upperarm_l", "arms"), ("DEF-forearm.L.001", "arms"),  # forearm is not a head bone
                            ("DEF-hand.R", "arms"), ("calf_r", "legs"), ("DEF-shin.L.001", "legs"),
                            ("head", "head"), ("neck_02", "head"), ("DEF-spine.006", "head"),
                            ("DEF-ear.L.002", "head"), ("Bone_Upperarm_L", "arms"), ("Bone_Spine_01", "core")):
            self.assertEqual(rig_bones.group_of(name), group, name)
        self.assertIsNone(rig_bones.group_of("root"))

    def test_group_counts_and_problems(self):
        owners = ["spine_01"] * 30 + ["upperarm_l"] * 20 + ["thigh_l"] * 40 + ["head"] * 10
        counts = rig_bones.group_counts(owners)
        self.assertEqual((counts["core"], counts["arms"], counts["legs"], counts["head"]), (30, 20, 40, 10))
        self.assertEqual(rig_bones.coverage_problems(counts), [])

    def test_empty_group_is_reported(self):
        """The review-r2 failure: torso vertices all on limb bones, core = 0, old check still said fine."""
        counts = rig_bones.group_counts(["clavicle_l"] * 40 + ["thigh_l"] * 40 + ["upperarm_l"] * 10 + ["head"] * 10)
        problems = rig_bones.coverage_problems(counts)
        self.assertTrue(any(p.startswith("core holds 0 of 100") for p in problems), problems)

    def test_unweighted_is_reported(self):
        counts = rig_bones.group_counts(["spine_01"] * 50 + [None] * 5 + ["thigh_l"] * 30 + ["upperarm_l"] * 10
                                        + ["head"] * 5)
        self.assertTrue(any("no bone" in p for p in rig_bones.coverage_problems(counts)))
        self.assertEqual(rig_bones.coverage_problems({}), ["no vertices"])

    def test_check_input_box(self):
        self.assertIsNone(rig_bones.check_input_box((0.44, 0.93, 1.8), 0.0))          # the +X prop
        self.assertIn("faces -Y", rig_bones.check_input_box((0.93, 0.44, 1.8), 0.0))  # faces -Y
        self.assertIn("feet", rig_bones.check_input_box((0.44, 0.93, 1.8), -0.5))
        self.assertIn("tall", rig_bones.check_input_box((0.44, 0.93, 1.8), 0.0, expected_height=1.5))
        self.assertIn("no height", rig_bones.check_input_box((0.4, 0.9, 0.0), 0.0))


class Alignment(unittest.TestCase):
    def setUp(self):
        self.bones = rig_bones.layout(1.8)
        # a vertex cloud centred on each bone's midpoint, owned by that bone
        self.points, self.owners = [], []
        for b in self.bones:
            mid = tuple((h + t) / 2 for h, t in zip(b["head"], b["tail"]))
            for _ in range(10):
                self.points.append(mid)
                self.owners.append(b["name"])

    def test_rotate_z(self):
        x, y, z = rig_bones.rotate_z((1.0, 0.0, 2.0), 90)
        self.assertAlmostEqual(x, 0.0)
        self.assertAlmostEqual(y, 1.0)
        self.assertEqual(z, 2.0)
        self.assertEqual(rig_bones.validate(rig_bones.rotate_bones(self.bones, -90)), [])

    def test_aligned_rig_has_no_problems(self):
        stats = rig_bones.alignment_stats(self.bones, self.owners, self.points)
        self.assertEqual(rig_bones.alignment_problems(stats, 1.8), [])
        self.assertLess(max(d for _, d in stats.values()), 1e-9)

    def test_rig_turned_apart_from_its_mesh_is_caught(self):
        """Review r2 round 3: bones turned -90 while the vertices stayed: every vertex still has a bone."""
        turned = rig_bones.rotate_bones(self.bones, -90)
        stats = rig_bones.alignment_stats(turned, self.owners, self.points)
        problems = rig_bones.alignment_problems(stats, 1.8)
        self.assertTrue(any(p.startswith("upperarm_l ") for p in problems), problems)
        self.assertEqual(rig_bones.group_counts(self.owners)["none"], 0)  # coverage alone would not notice

    def test_small_bones_and_unweighted_are_ignored(self):
        stats = rig_bones.alignment_stats(self.bones, ["head"] * 3 + [None] * 3, [(9, 9, 9)] * 6)
        self.assertEqual(stats, {})


class RigifyFit(unittest.TestCase):
    def test_targets_cover_trunk_and_both_sides(self):
        targets = rig_bones.rigify_fit_targets(rig_bones.layout(1.8))
        for name in ("spine", "spine.006", "pelvis.L", "pelvis.R", "thigh.L", "shin.R", "foot.L", "toe.R",
                     "shoulder.L", "upper_arm.R", "forearm.L", "hand.R"):
            self.assertIn(name, targets)
        self.assertGreater(targets["upper_arm.L"][0][1], 0)  # left = +Y in layout coordinates
        self.assertLess(targets["upper_arm.R"][0][1], 0)
        for head, tail in targets.values():
            self.assertNotEqual(head, tail)

    def test_knee_forward_elbow_back(self):
        t = rig_bones.rigify_fit_targets(rig_bones.layout(1.8))
        self.assertGreater(t["shin.L"][0][0], 0)       # knee nudged forward (+X)
        self.assertLess(t["forearm.L"][0][0], 0)       # elbow nudged back
        self.assertEqual(t["shin.L"][0], t["thigh.L"][1])  # the nudge is shared so connected bones agree
        self.assertEqual(t["thigh.R"][1][1], -t["thigh.L"][1][1])

    def test_rigify_skin_bone(self):
        for name in ("DEF-spine", "DEF-spine.003", "DEF-thigh.L.001", "DEF-upper_arm.R", "DEF-hand.L", "DEF-toe.R"):
            self.assertTrue(rig_bones.rigify_skin_bone(name), name)
        for name in ("DEF-breast.L", "DEF-f_index.01.L", "DEF-jaw", "DEF-ear.L", "ORG-spine", "root"):
            self.assertFalse(rig_bones.rigify_skin_bone(name), name)


class Timelog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = str(Path(self.tmp.name) / "t.jsonl")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = rig_timelog.main(list(argv))
        return rc, out.getvalue(), err.getvalue()

    def test_table_minutes(self):
        self.assertEqual(self.run_cli(self.log, "start", "--at", "2026-11-10T10:00:00+00:00")[0], 0)
        self.run_cli(self.log, "mark", "A1 rig", "--at", "2026-11-10T10:12:30+00:00", "--note", "ok")
        self.run_cli(self.log, "mark", "A2 import", "--at", "2026-11-10T10:30:00+00:00")
        rc, out, _ = self.run_cli(self.log, "table")
        self.assertEqual(rc, 0)
        self.assertIn("| A1 rig | 12.5 | 12.5 | ok |", out)
        self.assertIn("| A2 import | 17.5 | 30.0 |  |", out)
        self.assertIn("**30.0**", out)

    def test_errors(self):
        self.assertEqual(self.run_cli(self.log, "mark", "x")[0], 2)              # not started
        self.run_cli(self.log, "start", "--at", "2026-11-10T10:00:00+00:00")
        self.assertEqual(self.run_cli(self.log, "start")[0], 2)                  # twice
        self.assertEqual(self.run_cli(self.log, "mark")[0], 2)                   # no label
        self.assertEqual(self.run_cli(self.log, "mark", "early", "--at", "2026-11-10T09:00:00+00:00")[0], 2)

    def test_backdated_mark_is_inserted_in_order(self):
        self.run_cli(self.log, "start", "--at", "2026-11-10T10:00:00+00:00")
        self.run_cli(self.log, "mark", "late", "--at", "2026-11-10T10:30:00+00:00")
        self.assertEqual(self.run_cli(self.log, "mark", "forgot", "--at", "2026-11-10T10:10:00+00:00")[0], 0)
        _, out, _ = self.run_cli(self.log, "table")
        self.assertLess(out.index("forgot"), out.index("late"))
        self.assertIn("| forgot | 10.0 | 10.0 |", out)
        self.assertIn("| late | 20.0 | 30.0 |", out)

    def test_pipe_in_label_and_note_is_escaped(self):
        self.run_cli(self.log, "start", "--at", "2026-11-10T10:00:00+00:00")
        self.run_cli(self.log, "mark", "a|b", "--note", "x|y", "--at", "2026-11-10T10:05:00+00:00")
        _, out, _ = self.run_cli(self.log, "table")
        self.assertIn("| a\\|b | 5.0 | 5.0 | x\\|y |", out)

    def test_table_needs_two_marks(self):
        self.assertIn("need", rig_timelog.render_table([]))


if __name__ == "__main__":
    unittest.main()
