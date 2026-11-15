import contextlib
import copy
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import layout_spec as ls  # noqa: E402

EXAMPLE = os.path.join(ROOT, "stages", "02_build", "references", "layout-spec", "example-layout.json")


def example():
    with open(EXAMPLE, encoding="utf-8") as fh:
        return json.load(fh)


def metrics():
    return ls.load_metrics()


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = ls.main(argv)
    return rc, out.getvalue(), err.getvalue()


class Findings(unittest.TestCase):
    def assertFinding(self, layout, text):
        found = ls.check_layout(layout, metrics())
        self.assertTrue(any(text in line for line in found), f"{text!r} not in {found}")

    def test_example_is_clean(self):
        self.assertEqual(ls.check_layout(example(), metrics()), [])

    def test_level_path_must_be_practice(self):
        lay = example()
        lay["level_path"] = "/Game/Maps/L_Main"
        self.assertFinding(lay, "level_path")

    def test_narrow_corridor(self):
        lay = example()
        lay["rooms"][1]["h"] = 150
        self.assertFinding(lay, "corridor C")

    def test_small_room(self):
        lay = example()
        lay["rooms"][0].update(w=200, h=200)
        self.assertFinding(lay, "room A")

    def test_low_wall(self):
        lay = example()
        lay["rooms"][0]["height"] = 200
        self.assertFinding(lay, "wall height")

    def test_overlapping_rooms(self):
        lay = example()
        lay["rooms"][2]["x"] = 1000
        self.assertFinding(lay, "overlap")

    def test_touching_rooms_are_fine(self):
        self.assertFalse(any("overlap" in f for f in ls.check_layout(example(), metrics())))

    def test_door_too_narrow_short_wide(self):
        for key, val, text in (("width", 80, "width"), ("width", 600, "width"), ("height", 190, "height")):
            lay = example()
            lay["doors"][0][key] = val
            with self.subTest(key=key, val=val):
                self.assertFinding(lay, text)

    def test_door_taller_than_wall(self):
        lay = example()
        lay["doors"][0]["height"] = 400
        self.assertFinding(lay, "taller than the wall")

    def test_door_near_wall_end(self):
        lay = example()
        lay["doors"][0]["offset"] = 220
        self.assertFinding(lay, "inside the wall ends")

    def test_door_to_non_touching_room(self):
        lay = example()
        lay["doors"][0]["to"] = "B"
        self.assertFinding(lay, "do not share the wall")

    def test_door_to_unknown_room(self):
        lay = example()
        lay["doors"][0]["to"] = "Z"
        self.assertFinding(lay, "does not exist")

    def test_unreachable_objective(self):
        lay = example()
        del lay["doors"][1]
        self.assertFinding(lay, "cannot be reached")

    def test_start_outside(self):
        lay = example()
        lay["start"] = {"x": -900, "y": 0}
        self.assertFinding(lay, "start is not inside")

    def test_declared_length_and_time_must_match(self):
        lay = example()
        lay["paths"][0]["length_cm"] = 900
        self.assertFinding(lay, "declared length")
        lay = example()
        lay["paths"][0]["walk_time_s"] = 5.0
        self.assertFinding(lay, "declared walk time")

    def test_path_through_a_wall_gap_between_rooms(self):
        lay = example()
        lay["paths"][0]["points"] = [[-200, 0], [600, 500], [1200, 0]]
        lay["paths"][0].pop("length_cm")
        lay["paths"][0].pop("walk_time_s")
        self.assertFinding(lay, "leaves every room")

    def test_main_walk_time_target(self):
        lay = example()
        lay["targets"]["main_walk_time_s"] = [10, 20]
        self.assertFinding(lay, "outside target")
        lay = example()
        lay["paths"][0]["id"] = "side"
        self.assertFinding(lay, "no path with id 'main'")

    def test_gap_and_ledge_limits(self):
        lay = example()
        lay["gaps"] = [{"id": "g1", "width": 400}]
        lay["ledges"] = [{"id": "l1", "height": 200}]
        self.assertFinding(lay, "gap g1")
        self.assertFinding(lay, "ledge l1")
        lay["gaps"] = [{"id": "g1", "width": 250}]
        lay["ledges"] = [{"id": "l1", "height": 100}]
        self.assertEqual(ls.check_layout(lay, metrics()), [])

    def test_bad_shapes_report_not_crash(self):
        for bad in ({}, {"level_path": "/Game/Mock", "rooms": [{"id": "A"}]},
                    {"level_path": "/Game/Mock", "rooms": [{"id": "A", "x": 0, "y": 0, "w": 400, "h": 400}]}):
            with self.subTest(bad=bad):
                self.assertTrue(ls.check_layout(bad, metrics()))

    def test_path_through_solid_wall_between_doors(self):
        # review r1 #1: y=140 crosses x=300 and x=900 where the doors only cover y -100..100
        lay = example()
        lay["start"], lay["objective"] = {"x": -200, "y": 140}, {"x": 1200, "y": 140}
        lay["paths"][0]["points"] = [[-200, 140], [1200, 140]]
        self.assertFinding(lay, "no door gap")

    def test_path_through_door_gap_is_fine_and_edge_touch_is_not(self):
        lay = example()
        lay["paths"][0].update(points=[[-200, 90], [1200, 90]], length_cm=1400, walk_time_s=2.8)
        lay["start"], lay["objective"] = {"x": -200, "y": 90}, {"x": 1200, "y": 90}
        self.assertEqual(ls.check_layout(lay, metrics()), [])
        lay["paths"][0]["points"] = [[-200, 110], [1200, 110]]
        lay["start"], lay["objective"] = {"x": -200, "y": 110}, {"x": 1200, "y": 110}
        self.assertFinding(lay, "no door gap")

    def test_path_waypoint_on_a_wall_line_outside_a_door(self):
        lay = example()
        lay["paths"][0].update(points=[[-200, 0], [300, 140], [1200, 0]])
        lay["paths"][0].pop("length_cm")
        lay["paths"][0].pop("walk_time_s")
        self.assertFinding(lay, "no door gap")

    def test_main_path_must_run_start_to_objective(self):
        # review r1 #2
        lay = example()
        lay["paths"][0].update(points=[[-250, 0], [250, 0]], length_cm=500, walk_time_s=1.0)
        lay["targets"]["main_walk_time_s"] = [0.5, 1.5]
        self.assertFinding(lay, "first point")
        self.assertFinding(lay, "last point")

    def test_door_needs_to(self):
        # review r1 #3: a door onto nothing would cut a hole in an outer wall
        lay = example()
        lay["doors"].append({"room": "A", "side": "W", "offset": 0, "width": 200, "height": 240})
        self.assertFinding(lay, "'to'")

    def test_shared_wall_needs_equal_heights_and_door_fits_both(self):
        # review r1 #4 and #5
        lay = example()
        lay["rooms"][0]["height"] = 400
        lay["rooms"][1]["height"] = 250
        lay["doors"][0]["height"] = 300
        self.assertFinding(lay, "different heights")
        self.assertFinding(lay, "taller than the wall of room C")

    def test_equal_heights_build_the_same_whatever_the_room_order(self):
        lay = example()
        for r in lay["rooms"]:
            r["height"] = 400
        rev = copy.deepcopy(lay)
        rev["rooms"].reverse()

        def spans(plan):
            """Merged wall spans per (line, thickness axis, height): pieces may split differently by order."""
            out = {}
            for c in plan["cubes"]:
                if not c["label"].startswith("Wall_"):
                    continue
                x, y, _ = c["loc"]
                sx, sy, sz = c["scale"]
                along_x = sx > sy
                line, mid, length = (y, x, sx * 100) if along_x else (x, y, sy * 100)
                out.setdefault((along_x, round(line), round(sz * 100)), []).append((mid - length / 2, mid + length / 2))
            for k, v in out.items():
                v.sort()
                merged = [list(v[0])]
                for a, b in v[1:]:
                    if a <= merged[-1][1] + 0.01:
                        merged[-1][1] = max(merged[-1][1], b)
                    else:
                        merged.append([a, b])
                out[k] = [(round(a, 1), round(b, 1)) for a, b in merged]
            return out

        self.assertEqual(spans(ls.build_plan(lay, metrics())), spans(ls.build_plan(rev, metrics())))

    # ---- review r2 ----
    def test_sketch_is_not_mirrored_against_ue(self):
        # UE top view: +X right, +Y down. A room with larger y must be drawn LOWER on the page.
        lay = example()
        lay["rooms"].append({"id": "D", "x": 0, "y": 600, "w": 600, "h": 600})
        svg = ls.render_svg(lay, metrics())
        import re
        ys = {m.group(2): float(m.group(1)) for m in re.finditer(r'<text x="[\d.]+" y="([\d.]+)">(\w) \d', svg)}
        self.assertLess(ys["A"], ys["D"], "room at y=0 must be above the room at y=600 on the page")

    # ---- review r3 ----
    def test_axis_note_fits_inside_small_svg(self):
        import re
        lay = {"units": "cm", "level_path": "/Game/Mock/L_Small",
               "rooms": [{"id": "A", "x": 0, "y": 0, "w": 600, "h": 600}],
               "start": {"x": -100, "y": 0}, "objective": {"x": 100, "y": 0}}
        self.assertEqual(ls.check_layout(lay, metrics()), [])
        for layout in (lay, example()):
            svg = ls.render_svg(layout, metrics())
            w = float(re.search(r'<svg[^>]* width="([\d.]+)"', svg).group(1))
            m = re.search(r'<text x="(-?[\d.]+)" y="14">(\+X right[^<]*)</text>', svg)
            self.assertGreaterEqual(float(m.group(1)), 0)
            self.assertLessEqual(float(m.group(1)) + len(m.group(2)) * 5.5, w)

    def test_n_side_is_the_low_y_side(self):
        r = {"id": "A", "x": 0, "y": 0, "w": 600, "h": 400}
        self.assertEqual(ls.side_geom(r, "N")[1], -200)
        self.assertEqual(ls.side_geom(r, "S")[1], 200)

    def test_start_and_objective_keep_capsule_clearance(self):
        lay = example()
        lay["start"] = {"x": -298, "y": 0}
        lay["paths"][0]["points"][0] = [-298, 0]
        lay["paths"][0].pop("length_cm"), lay["paths"][0].pop("walk_time_s")
        self.assertFinding(lay, "start is 2 cm from a wall")
        lay = example()
        lay["start"] = {"x": -280, "y": 250}
        lay["paths"][0]["points"] = [[-280, 250], [-280, 0], [1200, 0]]
        lay["paths"][0].pop("length_cm"), lay["paths"][0].pop("walk_time_s")
        self.assertFinding(lay, "start is 20 cm from a wall")
        lay = example()
        lay["objective"] = {"x": 1470, "y": 0}
        lay["paths"][0]["points"][-1] = [1470, 0]
        self.assertFinding(lay, "objective is")

    def test_clearance_is_measured_to_the_wall_not_the_door_gap(self):
        lay = example()  # 60 cm from the A-C wall but straight in front of the door gap: fine
        lay["start"] = {"x": 240, "y": 0}
        lay["paths"][0]["points"][0] = [240, 0]
        lay["paths"][0].pop("length_cm"), lay["paths"][0].pop("walk_time_s")
        lay["targets"]["main_walk_time_s"] = [1, 6]
        self.assertEqual(ls.check_layout(lay, metrics()), [])

    def test_null_and_odd_optional_values_report_instead_of_crashing(self):
        for key, val in (("doors", None), ("gaps", None), ("gaps", [300]), ("targets", None),
                         ("targets", 5), ("ledges", "x"), ("paths", None)):
            lay = example()
            lay[key] = val
            with self.subTest(key=key, val=val):
                found = ls.check_layout(lay, metrics())  # must not raise
                self.assertIsInstance(found, list)
        lay = example()
        lay["targets"] = {"main_walk_time_s": ["2", "6"]}
        self.assertFinding(lay, "two numbers")
        lay = example()
        lay["gaps"], lay["ledges"], lay["targets"] = None, None, None
        self.assertEqual(ls.check_layout(lay, metrics()), [])

    def test_null_lists_exit_1_with_fail_lines_not_a_traceback(self):
        lay = example()
        lay["gaps"] = [300]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.json")
            with open(p, "w") as fh:
                json.dump(lay, fh)
            rc, out, _ = run(["check", p])
        self.assertEqual(rc, 1)
        self.assertIn("FAIL gaps", out)

    def test_door_margin_applies_to_the_neighbour_side_too(self):
        lay = example()
        lay["doors"][0].update(width=250, offset=25)  # gap y -100..150 ends on C's corner
        self.assertFinding(lay, "room C too")

    def test_orb_stays_in_the_start_room(self):
        lay = example()
        lay["start"] = {"x": 200, "y": 200}
        lay["paths"][0]["points"] = [[200, 200], [200, 0], [1200, 0]]
        lay["paths"][0].pop("length_cm"), lay["paths"][0].pop("walk_time_s")
        self.assertEqual(ls.check_layout(lay, metrics()), [])
        orb = ls.build_plan(lay, metrics())["orb"]
        self.assertEqual(ls.room_of({"x": orb[0], "y": orb[1]}, lay["rooms"]), "A")
        self.assertGreaterEqual(ls.wall_distance(lay, orb[0], orb[1]), 39)

    def test_example_plan_orb_keeps_the_old_offset(self):
        self.assertEqual(ls.build_plan(example(), metrics())["orb"], [-50, 150, 0.0])

    def test_duplicate_room_ids(self):
        lay = example()
        lay["rooms"][1]["id"] = "A"
        self.assertFinding(lay, "duplicate id")


class Plan(unittest.TestCase):
    def test_plan_has_floors_walls_lintels_and_points(self):
        plan = ls.build_plan(example(), metrics())
        labels = [c["label"] for c in plan["cubes"]]
        self.assertEqual(plan["format"], ls.PLAN_FORMAT)
        self.assertEqual(sum(1 for x in labels if x.startswith("Floor_")), 3)
        self.assertEqual(sum(1 for x in labels if x.startswith("Lintel_")), 2)
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(plan["player_start"], [-200, 0, 50.0])
        self.assertEqual(plan["objective"], [1200, 0, 0.0])

    def test_door_gap_is_open_and_walls_never_share_a_span(self):
        plan = ls.build_plan(example(), metrics())
        east = [c for c in plan["cubes"] if c["label"].startswith("Wall_") and c["loc"][0] == 300.0]
        spans = sorted((c["loc"][1] - c["scale"][1] * 50, c["loc"][1] + c["scale"][1] * 50) for c in east)
        for (a0, a1), (b0, _) in zip(spans, spans[1:]):
            self.assertLessEqual(a1, b0 + 0.01, "walls overlap on the same line")
        self.assertFalse(any(a0 < 0 < a1 for a0, a1 in spans), "door gap at y=0 is walled")

    def test_floor_matches_existing_script_shape(self):
        plan = ls.build_plan(example(), metrics())
        floor = next(c for c in plan["cubes"] if c["label"] == "Floor_A")
        self.assertEqual(floor["loc"], [0, 0, -5.0])
        self.assertEqual(floor["scale"], [6.0, 6.0, 0.1])

    def test_not_built_lists_gaps(self):
        lay = example()
        lay["gaps"] = [{"id": "g1", "width": 200}]
        self.assertEqual(ls.build_plan(lay, metrics())["not_built"], ["gaps:g1"])


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def test_check_ok_exit_0(self):
        rc, out, _ = run(["check", EXAMPLE])
        self.assertEqual(rc, 0)
        self.assertIn("LAYOUT_CHECK OK", out)

    def test_check_fail_exit_1(self):
        lay = example()
        lay["doors"][0]["width"] = 50
        with open(self.path("bad.json"), "w") as fh:
            json.dump(lay, fh)
        rc, out, _ = run(["check", self.path("bad.json")])
        self.assertEqual(rc, 1)
        self.assertIn("FAIL door", out)

    def test_bad_input_exit_2(self):
        with open(self.path("x.json"), "w") as fh:
            fh.write("{nope")
        for argv in (["check", self.path("missing.json")], ["check", self.path("x.json")],
                     ["check", EXAMPLE, "--metrics", self.path("missing.json")]):
            with self.subTest(argv=argv):
                self.assertEqual(run(argv)[0], 2)

    def test_render_round_trip_and_check_on_svg(self):
        svg = self.path("l.svg")
        self.assertEqual(run(["render", EXAMPLE, "-o", svg])[0], 0)
        text = open(svg, encoding="utf-8").read()
        for needle in ("<svg", "scale bar 500 cm", "main: 1400 cm, 2.8 s", 'id="layout-spec"'):
            self.assertIn(needle, text)
        self.assertEqual(ls.load_layout(svg), example())
        self.assertEqual(run(["check", svg])[0], 0)

    def test_svg_without_block_is_exit_2(self):
        with open(self.path("e.svg"), "w") as fh:
            fh.write("<svg/>")
        self.assertEqual(run(["check", self.path("e.svg")])[0], 2)

    def test_build_writes_plan_and_refuses_bad_layout(self):
        plan = self.path("plan.json")
        self.assertEqual(run(["build", EXAMPLE, "-o", plan])[0], 0)
        self.assertEqual(json.load(open(plan))["format"], ls.PLAN_FORMAT)
        lay = copy.deepcopy(example())
        lay["level_path"] = "/Game/Real/L_Entry"
        with open(self.path("bad.json"), "w") as fh:
            json.dump(lay, fh)
        out_path = self.path("never.json")
        rc, _, _ = run(["build", self.path("bad.json"), "-o", out_path])
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(out_path))

    def test_metrics_file_can_be_swapped(self):
        m = json.load(open(ls.DEFAULT_METRICS))
        m["door_min_width_cm"] = 250
        with open(self.path("m.json"), "w") as fh:
            json.dump(m, fh)
        self.assertEqual(run(["check", EXAMPLE, "--metrics", self.path("m.json")])[0], 1)


if __name__ == "__main__":
    unittest.main()
