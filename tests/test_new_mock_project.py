import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location("new_mock_project", os.path.join(ROOT, "scripts", "new-mock-project.py"))
nmp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nmp)

RULE = 'PrimaryAssetType="GameFeatureData",AssetBaseClass="/Script/GameFeatures.GameFeatureData"'


class NewMockProject(unittest.TestCase):
    def gen(self, tmp, *extra):
        target = Path(tmp) / "proj"
        code = nmp.main(["MockTen", str(target), *extra])
        return code, target

    def test_generates_rule_url_plugins_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, t = self.gen(tmp)
            self.assertEqual(code, 0)
            ini = (t / "Config" / "DefaultGame.ini").read_text()
            self.assertIn("[/Script/Engine.AssetManagerSettings]", ini)
            self.assertIn("+PrimaryAssetTypesToScan=(" + RULE, ini)
            self.assertIn("CookRule=AlwaysCook", ini)
            mcp = json.loads((t / ".mcp.json").read_text())
            self.assertEqual(mcp["mcpServers"]["unreal-mcp"]["url"], "http://127.0.0.1:8010/mcp")
            self.assertEqual(mcp["mcpServers"]["unreal-mcp"]["type"], "http")
            up = json.loads((t / "MockTen.uproject").read_text())
            self.assertEqual(up["EngineAssociation"], "")
            self.assertNotIn("Modules", up)
            self.assertEqual([p["Name"] for p in up["Plugins"]],
                             ["ModelingToolsEditorMode", "ModelContextProtocol", "AllToolsets"])
            for p in up["Plugins"]:
                self.assertTrue(p["Enabled"])
                self.assertEqual(p["TargetAllowList"], ["Editor"])
            eng = (t / "Config" / "DefaultEngine.ini").read_text()
            self.assertIn("GameDefaultMap=/Game/Maps/L_MainLevel", eng)
            self.assertIn("EditorStartupMap=/Game/Maps/L_MainLevel", eng)

    def test_idempotent_and_no_clobber(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, t = self.gen(tmp)
            code, _ = self.gen(tmp)
            self.assertEqual(code, 0)
            (t / "Config" / "DefaultGame.ini").write_text("; edited\n")
            code, _ = self.gen(tmp)
            self.assertEqual(code, 1)
            self.assertEqual((t / "Config" / "DefaultGame.ini").read_text(), "; edited\n")
            code, _ = self.gen(tmp, "--force")
            self.assertEqual(code, 0)
            self.assertIn(RULE, (t / "Config" / "DefaultGame.ini").read_text())

    def test_force_merges_and_keeps_other_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, t = self.gen(tmp)
            eng = t / "Config" / "DefaultEditorPerProjectUserSettings.ini"  # the port pin lives here
            eng.write_text("[/Script/Engine.RendererSettings]\nr.Foo=1\n\n"
                           "[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]\n"
                           "ServerPortNumber=9999\nHandPin=yes\n")
            (t / "Config" / "DefaultGame.ini").write_text("[/Script/Engine.AssetManagerSettings]\nMine=1\n")
            up = t / "MockTen.uproject"
            data = json.loads(up.read_text())
            data["EngineAssociation"] = "5.8"
            data["Plugins"].append({"Name": "Mine", "Enabled": True})
            up.write_text(json.dumps(data))
            code, _ = self.gen(tmp, "--force")
            self.assertEqual(code, 0)
            text = eng.read_text()
            self.assertIn("r.Foo=1", text)
            self.assertIn("HandPin=yes", text)
            self.assertIn("ServerPortNumber=8010", text)
            self.assertNotIn("9999", text)
            self.assertIn("GameDefaultMap=/Game/Maps/L_MainLevel",
                          (t / "Config" / "DefaultEngine.ini").read_text())
            game = (t / "Config" / "DefaultGame.ini").read_text()
            self.assertIn("Mine=1", game)
            self.assertIn(RULE, game)
            merged = json.loads(up.read_text())
            self.assertEqual(merged["EngineAssociation"], "5.8")
            names = [p["Name"] for p in merged["Plugins"]]
            self.assertIn("Mine", names)
            self.assertEqual(len(names), len(set(names)))
            code, _ = self.gen(tmp, "--force")  # second merge is a no-op
            self.assertEqual(code, 0)
            self.assertEqual(eng.read_text(), text)

    def test_force_all_replaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, t = self.gen(tmp)
            (t / "Config" / "DefaultEngine.ini").write_text("HandPin=yes\n")
            self.gen(tmp, "--force-all")
            self.assertNotIn("HandPin", (t / "Config" / "DefaultEngine.ini").read_text())

    def test_port_follows_mcp_url_and_no_duplicate_plugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, t = self.gen(tmp, "--mcp-url", "http://127.0.0.1:8011/mcp",
                            "--extra-plugin", "X", "--extra-plugin", "X")
            self.assertIn("ServerPortNumber=8011",
                          (t / "Config" / "DefaultEditorPerProjectUserSettings.ini").read_text())
            names = [p["Name"] for p in json.loads((t / "MockTen.uproject").read_text())["Plugins"]]
            self.assertEqual(names.count("X"), 1)

    def test_force_does_not_duplicate_editor_saved_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, t = self.gen(tmp)
            ini = t / "Config" / "DefaultGame.ini"
            ini.write_text('[/Script/Engine.AssetManagerSettings]\n!PrimaryAssetTypesToScan=ClearArray\n'
                           '+PrimaryAssetTypesToScan=(PrimaryAssetType="GameFeatureData",'
                           'AssetBaseClass="/Script/GameFeatures.GameFeatureData",Directories=,'
                           'SpecificAssets=,Rules=(Priority=-1,bApplyRecursively=True,CookRule=AlwaysCook))\n')
            for _ in range(2):
                self.gen(tmp, "--force")
            self.assertEqual(ini.read_text().count('PrimaryAssetType="GameFeatureData"'), 1)

    def test_bad_mcp_url_is_a_clean_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            for url in ("http://127.0.0.1/mcp", "http://127.0.0.1:80100/mcp", "https://x:8010/mcp", "nonsense",
                        'http://127.0.0.1:8010/m"cp', "http://127.0.0.1:8010/m\\cp", "http://127.0.0.1:8010/m\ncp"):
                with self.assertRaises(SystemExit, msg=url):
                    nmp.main(["MockTen", str(Path(tmp) / "p"), "--mcp-url", url])

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, t = self.gen(tmp, "--dry-run")
            self.assertEqual(code, 0)
            self.assertFalse(t.exists())

    def test_hyphen_name_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                nmp.main(["bad-name", str(Path(tmp) / "p")])

    def test_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, t = self.gen(tmp, "--level", "L_Arena", "--extra-plugin", "EditorToolsets")
            up = json.loads((t / "MockTen.uproject").read_text())
            self.assertEqual(up["Plugins"][-1]["Name"], "EditorToolsets")
            self.assertIn("L_Arena", (t / "Config" / "DefaultEngine.ini").read_text())


if __name__ == "__main__":
    unittest.main()
