"""procedural_props tests: the fallback `character` prop. Runs Blender in background mode (CPU, no GPU),
so the whole class is skipped when Blender is not installed."""
import json
import re
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "procedural_props.py"
BLENDER = shutil.which("blender")
HEIGHT = 1.8
COLOURS = {"skin": "#E0AC85", "shirt": "#D9382B", "trousers": "#2B4A8C"}


def glb_json(path):
    data = Path(path).read_bytes()
    magic, _ver, _total = struct.unpack("<4sII", data[:12])
    assert magic == b"glTF"
    clen, ctype = struct.unpack("<II", data[12:20])
    assert ctype == 0x4E4F534A  # JSON chunk
    return json.loads(data[20:20 + clen])


def srgb_to_linear(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def run(out, *extra):
    return subprocess.run([BLENDER, "-b", "-P", str(SCRIPT), "--", str(out), *extra],
                          capture_output=True, text=True, timeout=180)


@unittest.skipUnless(BLENDER, "blender not installed")
class CharacterProp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.proc = run(cls.tmp.name, "--only", "character", "--height", str(HEIGHT),
                       "--skin", COLOURS["skin"], "--shirt", COLOURS["shirt"],
                       "--trousers", COLOURS["trousers"])
        cls.glb = Path(cls.tmp.name) / "character.glb"
        cls.line = next((l for l in cls.proc.stdout.splitlines() if l.startswith("PROP character")), "")
        if cls.glb.exists():
            cls.gltf = glb_json(cls.glb)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def bbox(self):
        # glTF is Y-up: x forward, y up, z sideways. Union of every POSITION accessor.
        acc = self.gltf["accessors"]
        lo = [1e9] * 3; hi = [-1e9] * 3
        for mesh in self.gltf["meshes"]:
            for prim in mesh["primitives"]:
                a = acc[prim["attributes"]["POSITION"]]
                lo = [min(x, y) for x, y in zip(lo, a["min"])]
                hi = [max(x, y) for x, y in zip(hi, a["max"])]
        return lo, hi

    def test_exports_glb(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr[-500:])
        self.assertTrue(self.glb.exists())
        self.assertTrue(self.line, "no PROP line printed")

    def test_height_argument_is_honoured(self):
        lo, hi = self.bbox()
        self.assertAlmostEqual(hi[1] - lo[1], HEIGHT, delta=0.02)

    def test_origin_at_feet(self):
        lo, _ = self.bbox()
        self.assertAlmostEqual(lo[1], 0.0, delta=0.005)
        self.assertIn("zmin=0.000", self.line)

    def test_taller_than_wide(self):
        lo, hi = self.bbox()
        h = hi[1] - lo[1]; w = hi[2] - lo[2]; d = hi[0] - lo[0]
        self.assertGreater(h, 1.5 * w)   # a person, not a block
        self.assertGreater(h, 3 * d)
        self.assertGreater(w, 0.2 * h)   # arms out from the torso, not a pillar

    def test_faces_plus_x(self):
        lo, hi = self.bbox()
        # nose and toes stick out the front only, so the +X side reaches further from the origin
        self.assertGreater(hi[0], -lo[0])

    def test_sane_tri_count(self):
        tris = int(re.search(r"tris=(\d+)", self.line).group(1))
        self.assertGreater(tris, 100)
        self.assertLess(tris, 2000)

    def test_three_flat_colours(self):
        mats = self.gltf["materials"]
        self.assertEqual(len(mats), 3)
        got = {m["name"]: m["pbrMetallicRoughness"]["baseColorFactor"][:3] for m in mats}
        for name, hexc in COLOURS.items():
            want = srgb_to_linear(hexc)
            for g, w in zip(got[f"character_{name}"], want):
                self.assertAlmostEqual(g, w, delta=0.01)
        self.assertEqual(len({tuple(round(x, 3) for x in c) for c in got.values()}), 3)
        # flat colours: no texture on any material
        for m in mats:
            self.assertNotIn("baseColorTexture", m["pbrMetallicRoughness"])

    def test_every_material_is_used(self):
        used = {p["material"] for m in self.gltf["meshes"] for p in m["primitives"]}
        self.assertEqual(used, {0, 1, 2})

    def test_bad_height_is_rejected(self):
        for bad in ("0", "-1.7", "170", "nan"):
            with tempfile.TemporaryDirectory() as d:
                p = run(d, "--only", "character", "--height", bad)
                self.assertNotEqual(p.returncode, 0, bad)
                self.assertFalse((Path(d) / "character.glb").exists(), bad)

    def test_bad_colour_is_rejected(self):
        for opt in ("--shirt", "--skin", "--trousers"):
            for bad in ("red", "#GG0000", "zzzzzz", "#-1-1-1", "#+f+f+f", "#F F F ", "#12345"):
                with tempfile.TemporaryDirectory() as d:
                    p = run(d, "--only", "character", opt, bad)
                    self.assertNotEqual(p.returncode, 0, (opt, bad))
                    self.assertFalse((Path(d) / "character.glb").exists(), (opt, bad))

    def test_bad_colour_also_rejected_without_only(self):
        with tempfile.TemporaryDirectory() as d:
            p = run(d, "--shirt", "#GG0000")
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(list(Path(d).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
