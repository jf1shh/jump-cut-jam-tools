import json, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import gen1_import as g


class T(unittest.TestCase):
    @staticmethod
    def glb():
        import struct
        j = json.dumps({"materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}]}).encode()
        j += b" " * (-len(j) % 4)
        return struct.pack("<4sII", b"glTF", 2, 20 + len(j)) + struct.pack("<I4s", len(j), b"JSON") + j

    def test_flatten(self):
        with tempfile.TemporaryDirectory() as td:
            src, dst = Path(td) / "a.glb", Path(td) / "b.glb"
            src.write_bytes(self.glb())
            g.flatten_glb(src, dst, (0.1, 0.2, 0.3, 1.0))
            data = dst.read_bytes()
            doc = json.loads(data[20:20 + int.from_bytes(data[12:16], "little")])
            pbr = doc["materials"][0]["pbrMetallicRoughness"]
            self.assertNotIn("baseColorTexture", pbr)
            self.assertEqual(pbr["baseColorFactor"], [0.1, 0.2, 0.3, 1.0])

    def test_board_and_props(self):
        with tempfile.TemporaryDirectory() as td:
            gen = Path(td)
            for p in ("gpt", "fal"):
                d = gen / "concepts" / f"concept_A_s1_mainstreet_{p}"
                d.mkdir(parents=True)
                (d / "concept.png").write_bytes(b"x")
            found = g.concepts(gen)
            self.assertEqual(list(found), [("A", "s1_mainstreet")])
            self.assertEqual(sorted(found[("A", "s1_mainstreet")]), ["fal", "gpt"])
            b = gen / "board" / "b.md"
            self.assertEqual(g.write_board(found, b), 1)
            self.assertIn("../concepts/", b.read_text())
            for n, side in (("SM_Barrel", True), ("SM_WaterTower_rodin", True), ("SM_NoSide", False)):
                (gen / n).mkdir()
                (gen / n / f"{n}.glb").write_bytes(self.glb())
                if side:
                    (gen / n / f"{n}.glb.provenance.json").write_text("{}")
            items = g.props(gen)
            self.assertEqual({i["name"]: i["hold"] for i in items}, {"Barrel": False, "NoSide": False, "WaterTower_rodin": True})
            self.assertTrue([i for i in items if i["name"] == "Barrel"][0]["flat"])
            self.assertEqual(g.refused(items), ["NoSide: no provenance sidecar"])

    def test_finish_flags(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            side = td / "s.json"
            side.write_text("{}")
            items = [{"name": "A", "sidecar": side, "hold": True}, {"name": "B", "sidecar": None, "hold": False}]
            rows = [{"name": "A", "warnings": ["scale"]}, {"name": "B", "error": "boom"}]
            self.assertEqual(g.finish(rows, items, td, td / "r.md"), (1, 1))
            self.assertTrue((td / "work/gen1-import/SM_A.provenance.json").exists())
            self.assertIn("HOLD", (td / "r.md").read_text())

    def test_run_editor_never_pipes(self):
        seen = {}

        def fake(cmd, **kw):
            seen.update(kw)
            Path(json.loads(Path(kw["env"]["GEN1_MANIFEST"]).read_text())["result"]).write_text("[]")
        with tempfile.TemporaryDirectory() as td:
            old = g.subprocess.run
            g.subprocess.run = lambda *a, **k: None  # the systemctl stop
            try:
                g.run_editor([], "/Game/X/", Path(td), Path(td), run=fake)
            finally:
                g.subprocess.run = old
        self.assertNotIn("capture_output", seen)
        self.assertIn("timeout", seen)

    def test_cleanup_target_guard(self):
        with tempfile.TemporaryDirectory() as td:
            game = Path(td)
            (game / "Content" / "Maps").mkdir(parents=True)
            (game / "Content" / "Staging" / "Gen1").mkdir(parents=True)
            for bad in ("/Game/", "/Game", "/Game/Maps/", "/Game/Staging/", "/Game/Staging", "/Game/Staging/..",
                        "/Game/Staging/../Maps", "/Game/Staging/Gen1/../..", "/Game/StagingX/Gen1", "Game/Staging/Gen1", "",
                        "/Game/Staging/.", "/Game/Staging//"):
                with self.assertRaises(ValueError, msg=bad):
                    g.cleanup_target(game, bad)
            self.assertEqual(g.cleanup_target(game, "/Game/Staging/Gen1"), (game / "Content/Staging/Gen1").resolve())
            self.assertEqual(g.cleanup_target(game, "/Game/Staging/Gen1/"), (game / "Content/Staging/Gen1").resolve())
            self.assertEqual(g.cleanup_target(game, "/Game/Staging/_dryrun/"), (game / "Content/Staging/_dryrun").resolve())

    def test_cleanup_refused_before_any_work(self):
        with tempfile.TemporaryDirectory() as td:
            game = Path(td)
            (game / "Content" / "Maps").mkdir(parents=True)
            (game / "Content" / "Maps" / "keep.umap").write_text("x")
            for bad in ("/Game/", "/Game/Maps/", "/Game/Staging/../Maps"):
                self.assertEqual(g.main(["--placeholder", "x.glb", "--dest", bad, "--cleanup", "--game", str(game)]), 2)
            self.assertTrue((game / "Content" / "Maps" / "keep.umap").exists())

    def test_cleanup_deletes_only_below_staging(self):
        with tempfile.TemporaryDirectory() as td:
            game = Path(td)
            (game / "Content" / "Maps").mkdir(parents=True)
            (game / "Content" / "Maps" / "keep.umap").write_text("x")
            gen1 = game / "Content" / "Staging" / "Gen1"
            gen1.mkdir(parents=True)
            (gen1 / "a.uasset").write_text("x")
            (game / "Content" / "Staging" / "Other").mkdir()
            g.shutil.rmtree(g.cleanup_target(game, "/Game/Staging/Gen1"))
            self.assertFalse(gen1.exists())
            self.assertTrue((game / "Content" / "Staging" / "Other").exists())
            self.assertTrue((game / "Content" / "Maps" / "keep.umap").exists())

    def test_cleanup_refuses_symlink_escape(self):
        with tempfile.TemporaryDirectory() as td:
            game = Path(td) / "game"
            outside = Path(td) / "outside"
            (game / "Content" / "Staging").mkdir(parents=True)
            outside.mkdir()
            (game / "Content" / "Staging" / "Link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                g.cleanup_target(game, "/Game/Staging/Link")


if __name__ == "__main__":
    unittest.main()
