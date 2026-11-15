import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import seam_test  # noqa: E402


def noise_tileable(n=64, seed=1):
    """Periodic noise: sum of sines with whole periods, so it wraps perfectly."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:n, 0:n] / n
    v = np.zeros((n, n))
    for _ in range(8):
        fx, fy = rng.integers(1, 6, 2)
        v += rng.random() * np.sin(2 * np.pi * (fx * x + fy * y) + rng.random() * 6)
    v = (v - v.min()) / (v.max() - v.min()) * 200 + 20
    return np.stack([v, v * 0.9, v * 0.8], axis=2)


def gradient(n=64):
    """A ramp: left edge dark, right edge bright. Seam is obvious."""
    row = np.linspace(0, 255, n)
    return np.stack([np.tile(row, (n, 1))] * 3, axis=2)


class SeamTest(unittest.TestCase):
    def test_tileable_passes(self):
        r = seam_test.measure(noise_tileable())
        self.assertLess(r["seam_ratio"], 1.2)
        self.assertTrue(r["pass"])

    def test_ramp_fails(self):
        r = seam_test.measure(gradient())
        self.assertGreater(r["seam_ratio"], 5)
        self.assertFalse(r["pass"])

    def test_flat_image_is_clean(self):
        r = seam_test.measure(np.full((32, 32, 3), 100.0))
        self.assertEqual(r["seam_ratio"], 0.0)
        self.assertTrue(r["pass"])

    def test_blotchy_tile_flagged(self):
        img = np.full((64, 64, 3), 40.0)
        img[:32, :32] = 220.0  # one big bright quadrant, wraps fine inside? no: edges differ
        img = np.roll(img, 16, axis=(0, 1))
        r = seam_test.measure(img, max_ratio=100)
        self.assertGreater(r["blotch"], seam_test.MAX_BLOTCH)
        self.assertFalse(r["pass"])

    def test_one_bad_axis_is_not_averaged_away(self):
        # grain: columns alternate 40/140 (big normal dx); top-bottom ramp of 40
        # levels makes a hard line at the vertical wrap while dy is tiny.
        n = 64
        cols = np.where(np.arange(n) % 2 == 0, 40.0, 140.0)
        ramp = np.linspace(0, 40, n)
        img = cols[None, :] + ramp[:, None]
        img = np.stack([img] * 3, axis=2)
        r = seam_test.measure(img)
        self.assertGreater(r["seam_ratio"], 1.5)
        self.assertFalse(r["pass"])

    def test_blotch_does_not_depend_on_brightness(self):
        rng = np.random.default_rng(3)
        pat = np.kron(rng.normal(0, 10, (4, 4)), np.ones((16, 16)))
        dark = np.stack([np.clip(30 + pat, 0, 255)] * 3, axis=2)
        light = np.stack([np.clip(130 + pat, 0, 255)] * 3, axis=2)
        a = seam_test.blotch(dark)
        b = seam_test.blotch(light)
        self.assertAlmostEqual(a, b, delta=0.5)

    def test_16bit_greyscale_map_is_not_flattened(self):
        from PIL import Image
        row = np.linspace(16000, 48000, 64).astype("uint16")
        arr = np.tile(row, (64, 1))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "height16.png")
            Image.fromarray(arr).save(p)  # mode I;16
            img = seam_test.load(p)
            self.assertGreater(img.max() - img.min(), 100)
            self.assertFalse(seam_test.measure(img)["pass"])

    def test_grainy_tile_with_step_at_wrap_fails(self):
        rng = np.random.default_rng(5)
        n = 256
        img = 120 + rng.normal(0, 25, (n, n))
        img[:, n // 2:] += 30  # left half darker, right half brighter: wrap jumps by 30
        img = np.stack([img] * 3, axis=2)
        self.assertFalse(seam_test.measure(img, max_blotch=1000)["pass"])

    def test_grainy_tile_without_step_passes(self):
        rng = np.random.default_rng(6)
        img = np.stack([120 + rng.normal(0, 25, (256, 256))] * 3, axis=2)
        self.assertTrue(seam_test.measure(img)["pass"])

    def test_short_cut_object_at_wrap_fails(self):
        rng = np.random.default_rng(7)
        n = 512
        img = 100 + rng.normal(0, 8, (n, n))
        img[100:112, n - 6:] = 220  # a stone cut by the right border, not continued at the left
        img = np.stack([img] * 3, axis=2)
        self.assertFalse(seam_test.measure(img)["pass"])

    def test_misaligned_fine_stripes_fail(self):
        n = 512
        y, x = np.mgrid[0:n, 0:n]
        img = 120 + 60 * np.sin(2 * np.pi * (y / 8.0 + x / (2.0 * n)))  # phase drifts half a period
        img = np.stack([img] * 3, axis=2)
        self.assertFalse(seam_test.measure(img)["pass"])

    def test_sharp_line_in_smooth_tile_fails(self):
        n = 128
        y, x = np.mgrid[0:n, 0:n] / n
        v = 120 + 30 * np.sin(2 * np.pi * (x + 2 * y)) + 25 * np.sin(2 * np.pi * (2 * x - y))
        v = v + np.linspace(0, 30, n)[:, None]  # 30-level line at the top/bottom wrap
        r = seam_test.measure(np.stack([v] * 3, axis=2))
        self.assertGreater(r["seam_ratio"], 1.5, r)
        self.assertFalse(r["pass"])

    def test_float_map_0_to_1_is_scaled(self):
        from PIL import Image
        row = np.where(np.arange(64) < 32, 0.3, 0.7).astype("float32")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "rough.tiff")
            Image.fromarray(np.tile(row, (64, 1)), mode="F").save(p)
            img = seam_test.load(p)
            self.assertGreater(img.max(), 150)
            self.assertFalse(seam_test.measure(img)["pass"])

    def test_dark_16bit_map_is_still_scaled(self):
        from PIL import Image
        arr = np.tile(np.where(np.arange(64) < 32, 40, 200).astype("uint16"), (64, 1))  # max <= 255
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "h16.png")
            Image.fromarray(arr).save(p)
            self.assertLess(seam_test.load(p).max(), 5)  # 200/257 ~ 0.8: it is a 16-bit map

    def test_near_flat_falloff_is_not_a_false_fail(self):
        n = 512
        row = np.linspace(120, 122, n)
        img = np.stack([np.tile(row, (n, 1))] * 3, axis=2)
        r = seam_test.measure(img)
        self.assertTrue(r["pass"], r)

    def test_no_big_copies(self):
        import tracemalloc
        img = np.random.default_rng(8).random((512, 512, 3)).astype("float32") * 255
        tracemalloc.start()
        seam_test.measure(img)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.assertLess(peak, 12 * img.nbytes)

    def test_broken_file_does_not_hide_good_results(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            good, broken = Path(d, "good.png"), Path(d, "broken.png")
            Image.fromarray(noise_tileable().astype("uint8")).save(good)
            broken.write_bytes(b"not an image")
            p = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "seam_test.py"), str(good), str(broken), "--json"],
                capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            out = json.loads(p.stdout)
            self.assertTrue(out[str(good)]["pass"])
            self.assertIn("error", out[str(broken)])

    def test_too_small(self):
        with self.assertRaises(ValueError):
            seam_test.measure(np.zeros((2, 2, 3)))

    def test_cli_png_roundtrip_and_exit_codes(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            good, bad = Path(d, "good.png"), Path(d, "bad.png")
            Image.fromarray(noise_tileable().astype("uint8")).save(good)
            Image.fromarray(gradient().astype("uint8")).save(bad)
            run = lambda *a: subprocess.run(  # noqa: E731
                [sys.executable, str(ROOT / "scripts" / "seam_test.py"), *a],
                capture_output=True, text=True)
            p = run(str(good), "--json")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertTrue(json.loads(p.stdout)[str(good)]["pass"])
            self.assertEqual(run(str(good), str(bad)).returncode, 1)
            self.assertEqual(run(str(Path(d, "missing.png"))).returncode, 2)


if __name__ == "__main__":
    unittest.main()
