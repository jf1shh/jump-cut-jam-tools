import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location("jam_start", os.path.join(ROOT, "scripts", "jam_start.py"))
js = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(js)


class JamStart(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pf = self.root / "cfg" / "jam-path"
        self.game = self.root / "game"
        old = os.environ.get("MEGAJAM_JAM_PATH_FILE")
        os.environ["MEGAJAM_JAM_PATH_FILE"] = str(self.pf)
        self.addCleanup(lambda: os.environ.pop("MEGAJAM_JAM_PATH_FILE") if old is None
                        else os.environ.__setitem__("MEGAJAM_JAM_PATH_FILE", old))

    def run_main(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = js.main(list(args))
        return code, buf.getvalue()

    def test_full_run_and_idempotent(self):
        code, out = self.run_main("JamEntry", str(self.game))
        self.assertEqual(code, 0)
        self.assertIn("HANDOFF_MAX_RESTARTS=300 proj start megajam", out)
        dv = (self.game / ".dvignore").read_text().splitlines()
        for e in js.DVIGNORE_LINES:
            self.assertEqual(dv.count(e), 1)
        ini = (self.game / "Config" / "DefaultGame.ini").read_text()
        self.assertIn("[/Script/UnrealEd.ProjectPackagingSettings]", ini)
        self.assertEqual(ini.count("InternationalizationPreset=English"), 1)
        self.assertEqual(ini.count("+CulturesToStage=en"), 1)
        self.assertIn("GameFeatureData", ini)  # mock-project rule preserved
        self.assertIn("Layer 0", (self.game / "IDENTITY.md").read_text())
        self.assertNotIn("Template for", (self.game / "IDENTITY.md").read_text())
        self.assertEqual(self.pf.read_text().strip(), str(self.game.resolve()))
        before = {p: p.read_text() for p in self.game.rglob("*") if p.is_file()}
        code, out = self.run_main("JamEntry", str(self.game))
        self.assertEqual(code, 0)
        after = {p: p.read_text() for p in self.game.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_dvignore_keeps_existing_lines(self):
        self.game.mkdir()
        (self.game / ".dvignore").write_text("Binaries/\n/work/\nSaved/")
        self.run_main("JamEntry", str(self.game))
        dv = (self.game / ".dvignore").read_text().splitlines()
        self.assertEqual(dv[:3], ["Binaries/", "/work/", "Saved/"])
        self.assertNotIn("work/", dv)  # "/work/" already counts
        self.assertIn("Packaged/", dv)

    def test_staging_merges_into_existing_section(self):
        ini = self.game / "Config" / "DefaultGame.ini"
        ini.parent.mkdir(parents=True)
        ini.write_text("[/Script/UnrealEd.ProjectPackagingSettings]\nBuildConfiguration=PPBC_Shipping\n"
                       "+CulturesToStage=en\n")
        self.run_main("JamEntry", str(self.game), "--force")
        text = ini.read_text()
        self.assertEqual(text.count("+CulturesToStage=en"), 1)
        self.assertEqual(text.count("[/Script/UnrealEd.ProjectPackagingSettings]"), 1)
        self.assertIn("BuildConfiguration=PPBC_Shipping", text)
        self.assertIn("InternationalizationPreset=English", text)

    def test_efigs_mode(self):
        self.run_main("JamEntry", str(self.game), "--languages", "efigs")
        ini = (self.game / "Config" / "DefaultGame.ini").read_text()
        self.assertIn("InternationalizationPreset=EFIGS", ini)
        for c in ("en", "fr", "it", "de", "es"):
            self.assertEqual(ini.count(f"+CulturesToStage={c}\n"), 1)
        before = ini
        self.run_main("JamEntry", str(self.game), "--languages", "efigs")
        self.assertEqual((self.game / "Config" / "DefaultGame.ini").read_text(), before)

    def test_default_is_english_only(self):
        self.run_main("JamEntry", str(self.game))
        ini = (self.game / "Config" / "DefaultGame.ini").read_text()
        self.assertNotIn("EFIGS", ini)
        self.assertNotIn("CulturesToStage=fr", ini)

    def test_existing_identity_not_overwritten(self):
        self.game.mkdir()
        (self.game / "IDENTITY.md").write_text("mine\n")
        self.run_main("JamEntry", str(self.game))
        self.assertEqual((self.game / "IDENTITY.md").read_text(), "mine\n")
        self.assertTrue((self.game / "CONTEXT.md").exists())

    def test_dry_run_writes_nothing(self):
        code, out = self.run_main("JamEntry", str(self.game), "--dry-run")
        self.assertEqual(code, 0)
        self.assertFalse(self.game.exists())
        self.assertFalse(self.pf.exists())
        self.assertIn("would be created", out)

    def test_jam_path_conflict_needs_force(self):
        self.pf.parent.mkdir(parents=True)
        self.pf.write_text("/somewhere/else\n")
        code, _ = self.run_main("JamEntry", str(self.game))
        self.assertEqual(code, 1)
        self.assertFalse(self.game.exists())  # refused before writing anything
        self.assertEqual(self.pf.read_text(), "/somewhere/else\n")
        code, _ = self.run_main("JamEntry", str(self.game), "--force")
        self.assertEqual(code, 0)
        self.assertEqual(self.pf.read_text().strip(), str(self.game.resolve()))

    def test_bad_name_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.run_main("bad-name", str(self.game))

    def stage(self, n):
        d = self.root / "stage" / "Engine" / "Content" / "Internationalization"
        d.mkdir(parents=True)
        for i in range(n):
            (d / f"f{i}.dat").write_text("x")
        return str(self.root / "stage")

    def test_check_stage(self):
        buf = []
        self.assertTrue(js.check_stage(self.stage(40), out=buf.append)[1])
        self.assertIn("OK", buf[0])

    def test_check_stage_warns_on_full_icu(self):
        code, out = self.run_main("--check-stage", self.stage(js.ICU_WARN_FILES + 1))
        self.assertEqual(code, 1)
        self.assertIn("WARN", out)

    def test_threshold_is_3000(self):
        self.assertEqual(js.ICU_WARN_FILES, 3000)
        buf = []
        self.assertTrue(js.check_stage(self.stage(781), out=buf.append)[1])

    def test_rerun_keeps_game_maps_and_settings(self):
        self.run_main("JamEntry", str(self.game))
        eng = self.game / "Config" / "DefaultEngine.ini"
        eng.write_text(eng.read_text().replace("L_MainLevel", "L_MyGameLevel"))
        up = self.game / "JamEntry.uproject"
        up_before = up.read_text()
        code, out = self.run_main("JamEntry", str(self.game))
        self.assertEqual(code, 0)
        self.assertIn("L_MyGameLevel", eng.read_text())
        self.assertNotIn("L_MainLevel", eng.read_text())
        self.assertEqual(up.read_text(), up_before)

    def test_identity_uses_master_templates(self):
        self.run_main("JamEntry", str(self.game))
        ident = (self.game / "IDENTITY.md").read_text()
        ctx = (self.game / "CONTEXT.md").read_text()
        tpl = js.TEMPLATES
        self.assertTrue(ident.startswith("# JamEntry"))
        self.assertIn("Layer 0", ident)
        self.assertEqual(ident, "\n".join(l for l in (tpl / "game-project-identity.md").read_text().splitlines() if not l.startswith("> Template for")).__add__("\n").replace("<GAME NAME>", "JamEntry").replace("<Name>", "JamEntry").replace("~/Projects/megajam-game", str(self.game.resolve())))
        self.assertIn("Routing table", ctx)

    def test_template_missing_falls_back_inline(self):
        old = js.TEMPLATES
        js.TEMPLATES = self.root / "no-templates"
        self.addCleanup(setattr, js, "TEMPLATES", old)
        self.run_main("JamEntry", str(self.game))
        self.assertIn("2026-11-11 21:00 PT", (self.game / "IDENTITY.md").read_text())
        self.assertIn("Packaged/", (self.game / "CONTEXT.md").read_text())

    def test_check_stage_missing_tree(self):
        code, out = self.run_main("--check-stage", str(self.root / "nope"))
        self.assertEqual(code, 1)
        self.assertIn("not found", out)


if __name__ == "__main__":
    unittest.main()
