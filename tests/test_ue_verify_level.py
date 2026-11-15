import contextlib
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import ue_verify_level as v  # noqa: E402


class FakeComp:
    def __init__(self, mats, coll="ECollisionEnabled.QUERY_AND_PHYSICS"):
        self.mats, self.coll = mats, coll

    def get_materials(self):
        return [FakeMat(m) for m in self.mats]

    def get_collision_enabled(self):
        if self.coll == "boom":
            raise RuntimeError("no api")
        return self.coll


class FakeMat:
    def __init__(self, p):
        self.p = p

    def get_path_name(self):
        return self.p


class FakeCls:
    def __init__(self, path):
        self.path = path

    def get_name(self):
        return self.path.rsplit("/", 1)[-1]

    def get_path_name(self):
        return self.path


class FakeActor:
    def __init__(self, label, comp=None, cls="/Script/Engine.StaticMeshActor", hidden=False, props=None):
        self.label, self.comp, self.cls, self.hidden, self.props = label, comp, cls, hidden, props or {}
        for k in self.props:
            setattr(self, k, 0)

    def get_actor_label(self):
        return self.label

    def get_class(self):
        return FakeCls(self.cls)

    def is_temporarily_hidden_in_editor(self):
        return self.hidden

    def get_component_by_class(self, _c):
        return self.comp

    def get_editor_property(self, n):
        return self.props[n]


class Material(unittest.TestCase):
    def test_defaults_flagged(self):
        for p in ("/Engine/EngineMaterials/WorldGridMaterial", "/Game/T/M_Checker_Floor", "/Engine/EngineMaterials/DefaultMaterial"):
            self.assertTrue(v.is_default_material(p), p)

    def test_custom_not_flagged(self):
        self.assertFalse(v.is_default_material("/Game/Jam/M_Hero"))
        self.assertFalse(v.is_default_material(""))
        self.assertFalse(v.is_default_material(None))


class Traps(unittest.TestCase):
    def test_stale_actor(self):
        recs = [{"label": "Door1", "bp": "/Game/BP_Door.BP_Door_C"}, {"label": "Floor", "bp": ""}]
        self.assertEqual(v.stale_candidates(recs, [" /Game/BP_Door.BP_Door_C ", ""]), ["Door1"])
        self.assertEqual(v.stale_candidates(recs, []), [])

    def test_zero_defaults(self):
        rec = {"numeric": {"DecalSize": 0, "Health": 5, "Speed": 0.0, "Flag": 0, "Impulse": False}}
        self.assertEqual(v.zero_defaults(rec), ["DecalSize", "Speed"])

    def test_collision_unknown_is_not_pass(self):
        recs = [{"label": "Wall", "gameplay": True, "collision": None, "materials": []},
                {"label": "Ghost", "gameplay": True, "collision": False, "materials": []},
                {"label": "Ok", "gameplay": True, "collision": True, "materials": []}]
        rules = {(r, lab) for r, lab, _ in v.findings(recs)}
        self.assertIn(("unknown-collision", "Wall"), rules)
        self.assertIn(("no-collision", "Ghost"), rules)
        self.assertFalse([x for x in rules if x[1] == "Ok"])

    def test_findings_default_material_and_stale(self):
        recs = [{"label": "Floor", "materials": ["/Engine/EngineMaterials/WorldGridMaterial"], "bp": ""},
                {"label": "D", "materials": [], "bp": "/Game/BP_D.BP_D_C"}]
        got = {r for r, _, _ in v.findings(recs, ["/Game/BP_D.BP_D_C"])}
        self.assertEqual(got, {"default-material", "stale-actor"})


class Lint(unittest.TestCase):
    def names(self, text, brief=False):
        return [r for r, _, _ in v.lint_text(text, brief)]

    def test_graph_rules(self):
        txt = "Begin Object Class=K2Node_Event EventTick\nK2Node_InputAxisEvent Name=MoveFwd\nCustom HLSL here"
        self.assertEqual(sorted(self.names(txt)), ["event-tick", "legacy-input", "raw-hlsl"])

    def test_enhanced_input_clean(self):
        self.assertEqual(self.names("K2Node_EnhancedInputAction IA_Move\nOnComponentBeginOverlap"), [])

    def test_delay_chain_needs_two(self):
        self.assertEqual(self.names("K2Node_Delay A"), [])
        res = v.lint_text("K2Node_Delay A\nthen\nK2Node_Delay B", False)
        self.assertEqual([r[0] for r in res], ["delay-chain"])
        self.assertEqual(res[0][1], 3)

    def test_brief_rules(self):
        txt = "Put a box on the player's head. Check every frame. Bind widget WBP_HUD."
        self.assertEqual(sorted(self.names(txt, brief=True)), ["tick-ask", "vague-target", "widget-binding"])
        self.assertEqual(self.names("Edit /Game/BP_Hero.BP_Hero: add a box.", brief=True), [])


class EditorSide(unittest.TestCase):
    def setUp(self):
        class U:
            StaticMeshComponent = object
        v.unreal = U

    def tearDown(self):
        v.unreal = None

    def test_record_plain_mesh(self):
        a = FakeActor("Floor", FakeComp(["/Engine/EngineMaterials/WorldGridMaterial"]))
        r = v.actor_record(a)
        self.assertEqual((r["label"], r["visible"], r["gameplay"], r["collision"]), ("Floor", True, True, True))
        self.assertEqual(r["bp"], "")
        self.assertTrue(v.default_material_hits(r))

    def test_record_blueprint_with_zero(self):
        a = FakeActor("Gun", None, cls="/Game/BP_Gun.BP_Gun_C", props={"DecalSize": 0})
        a.DecalSize = 0
        r = v.actor_record(a)
        self.assertEqual(r["bp"], "/Game/BP_Gun.BP_Gun_C")
        self.assertEqual(v.zero_defaults(r), ["DecalSize"])

    def test_unreadable_collision_is_unknown(self):
        r = v.actor_record(FakeActor("W", FakeComp([], coll="boom")))
        self.assertIsNone(r["collision"])

    def test_hidden(self):
        self.assertFalse(v.actor_record(FakeActor("H", hidden=True))["visible"])


class ReviewFixes(unittest.TestCase):
    def setUp(self):
        class U:
            StaticMeshComponent = object
        v.unreal = U

    def tearDown(self):
        v.unreal = None

    def test_unassigned_slot_is_default_grid(self):
        a = FakeActor("Floor", FakeComp([None]))
        a.comp.get_materials = lambda: [None]
        r = v.actor_record(a)
        self.assertTrue(v.default_material_hits(r))

    def test_second_mesh_component_read(self):
        a = FakeActor("BP_Room", None)
        a.get_components_by_class = lambda _c: [FakeComp(["/Game/Jam/M_Wall"]),
                                                FakeComp(["/Engine/EngineMaterials/WorldGridMaterial"])]
        r = v.actor_record(a)
        self.assertEqual(len(v.default_material_hits(r)), 1)
        self.assertEqual(len(r["materials"]), 2)

    def test_collision_across_components(self):
        a = FakeActor("X", None)
        no = "ECollisionEnabled.NO_COLLISION"
        a.get_components_by_class = lambda _c: [FakeComp([]), FakeComp([], coll=no)]
        self.assertIs(v.actor_record(a)["collision"], True)  # solid body + decorative shell blocks
        a.get_components_by_class = lambda _c: [FakeComp([], coll=no), FakeComp([], coll=no)]
        self.assertIs(v.actor_record(a)["collision"], False)
        a.get_components_by_class = lambda _c: [FakeComp([], coll=no), FakeComp([], coll="boom")]
        self.assertIsNone(v.actor_record(a)["collision"])  # unknown is not a pass

    def test_hidden_component_skipped(self):
        class Vis(FakeComp):
            def __init__(self, mats, vis=True, hig=False):
                super().__init__(mats)
                self.vis, self.hig = vis, hig

            def is_visible(self):
                return self.vis

            def get_editor_property(self, n):
                return self.hig
        grid = "/Engine/EngineMaterials/WorldGridMaterial"
        a = FakeActor("Trigger", None)
        a.get_components_by_class = lambda _c: [Vis(["/Game/M_Crystal"]), Vis([grid], vis=False),
                                                Vis([grid], hig=True)]
        r = v.actor_record(a)
        self.assertEqual(r["materials"], ["/Game/M_Crystal"])
        self.assertEqual(v.default_material_hits(r), [])
        a.get_components_by_class = lambda _c: [Vis([grid])]  # visible grid still caught
        self.assertTrue(v.default_material_hits(v.actor_record(a)))

    def test_exported_delay_nodes_lint(self):
        node = ('Begin Object Class=/Script/BlueprintGraph.K2Node_CallFunction Name="N{}"\n'
                '  FunctionReference=(MemberParent="x",MemberName="Delay")\nEnd Object\n')
        self.assertIn("delay-chain", [r for r, _, _ in v.lint_text(node.format(1) + node.format(2))])
        self.assertEqual([r for r, _, _ in v.lint_text(node.format(1))], [])
        rt = node.replace('"Delay"', '"RetriggerableDelay"')
        self.assertIn("delay-chain", [r for r, _, _ in v.lint_text(node.format(1) + rt.format(2))])

    def test_stale_path_forms(self):
        recs = [{"label": "D", "bp": "/Game/BP_Door.BP_Door_C"}]
        for form in ("/Game/BP_Door", "/Game/BP_Door.BP_Door", "/Game/BP_Door.BP_Door_C"):
            self.assertEqual(v.stale_candidates(recs, [form]), ["D"], form)
        self.assertEqual(v.stale_candidates(recs, ["/Game/BP_Other"]), [])


class Cli(unittest.TestCase):
    def run_cli(self, text, *extra):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(text)
        self.addCleanup(os.unlink, f.name)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = v.cli(["--lint", f.name, *extra])
        return code, buf.getvalue()

    def test_exit_codes(self):
        code, out = self.run_cli("EventTick")
        self.assertEqual(code, 1)
        self.assertIn("LINT_DONE findings=1", out)
        self.assertEqual(self.run_cli("fine")[0], 0)

    def test_usage(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(v.cli([]), 2)


if __name__ == "__main__":
    unittest.main()
