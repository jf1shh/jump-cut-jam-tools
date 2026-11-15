#!/usr/bin/env python3
"""Seam test for a tileable texture: gives a number, not a feeling.

Recipe: stages/02_build/references/look-kit/tileable-textures.md. Practice tooling only (Rule 7(h)).

What a viewer sees at a tile join is a low-frequency step in brightness or
colour along the edge, not pixel grain. So the metric works on averages:

* Look across a boundary between two strips of K pixel lines. Average each
  strip, take the difference, then average that difference along the edge in
  windows of L pixels. Pixel noise averages out; a step or a cut object does
  not (a short cut of 12 px in a 512 px edge is still caught, because the
  windows are short, not the whole edge).
* The wrap boundary (last strip next to first strip) is exactly what a 50 %
  offset puts in the middle of the image and what UV x2 puts at every join,
  so one number covers both checks. No big copy of the image is made.
* seam_step = the largest windowed step at the wrap, in 0-255 levels.
  ref_step   = the 99th percentile of the same windowed step at every other
               boundary of the tile (what the texture itself does naturally).
  seam_ratio = seam_step / max(ref_step, FLOOR). The floor (levels) means a
               smooth, evenly lit tile is not failed for a step nobody can see.
* Two measures per axis, the worse one counts: the strip step above (signed
  average, grain cancels) and a pixel jump (K=1, |jump| averaged in windows),
  which catches a sharp line in a smooth tile and a fine pattern that does not
  line up at the wrap. Done per colour channel too.
* blotch = std of 4x4 block means of luminance, in 0-255 levels (absolute, so
  dark tiles are not punished). A blotchy tile shows its repeat as spots.

16-bit (always /257) and float greyscale maps (0..1, or larger) are scaled to 0-255.
A file that cannot be read is reported and the rest still run (exit 2).

Limits (--max-ratio 1.5, --max-blotch 30, FLOOR 4) are a starting guess,
UNTESTED until the look-kit measured run.

Usage:  python3 scripts/seam_test.py TEXTURE.png [...] [--json]
Exit code: 0 all pass, 1 any fail, 2 any unreadable file.
"""
import argparse
import json
import sys

import numpy as np

MAX_RATIO = 1.5
MAX_BLOTCH = 30.0  # levels on 0-255; a guess, UNTESTED
FLOOR = 4.0        # levels; a guess, UNTESTED
HIGH_MODES = ("I", "I;16", "I;16L", "I;16B", "F")


def load(path):
    """Return float32 array (h, w, channels) scaled to 0-255."""
    from PIL import Image
    with Image.open(path) as im:
        if im.mode in HIGH_MODES:
            a = np.asarray(im, dtype=np.float32)[:, :, None]
            top = float(a.max())
            if im.mode.startswith("I;16"):
                a = a * (255.0 / 65535.0)  # 16-bit by definition, even if the map is dark
            elif im.mode == "F" and top <= 1.0:
                a = a * 255.0  # float map in 0..1
            elif top > 255:
                a = a * (255.0 / (65535.0 if top <= 65535 else top))
            return a
        return np.asarray(im.convert("RGB"), dtype=np.float32)


def _steps(plane, k, win, abs_first=False):
    """plane: (h, w). Returns (wrap, interior): windowed |strip step| along
    the second axis; wrap is 1-D (per window), interior 2-D.
    abs_first=False: average the signed step in the window, then abs (cancels
    grain; catches steps and cut objects). abs_first=True: average |step|
    (does not cancel; catches fine patterns that do not line up)."""
    h, w = plane.shape
    c = np.zeros((h, w + 1), dtype=np.float64)
    np.cumsum(plane, axis=1, out=c[:, 1:])
    js = np.arange(k, w - k + 1)
    left = (c[:, js] - c[:, js - k]) / k
    right = (c[:, js + k] - c[:, js]) / k
    d = right - left
    wrap = (c[:, k] / k) - ((c[:, w] - c[:, w - k]) / k)  # first strip - last strip

    def smooth(x):
        if abs_first:
            x = np.abs(x)
        cs = np.zeros((x.shape[0] + 1,) + x.shape[1:], dtype=np.float64)
        np.cumsum(x, axis=0, out=cs[1:])
        return np.abs((cs[win:] - cs[:-win]) / win)

    return smooth(wrap), smooth(d)


def _axis_numbers(plane):
    """(seam, ref, ratio) for one axis: the worse of the two measures.
    strip step (k=4, signed): grain-proof. pixel jump (k=1, abs): a sharp line
    in a smooth tile and a misaligned fine pattern both show up here."""
    h, w = plane.shape
    win = min(h, max(4, h // 32))
    best = (0.0, 0.0, 0.0)
    for k, abs_first in ((max(1, min(4, w // 8)), False), (1, True)):
        wrap, inner = _steps(plane, k, win, abs_first)
        seam = float(wrap.max())
        ref = float(np.percentile(inner, 99)) if inner.size else 0.0
        ratio = seam / max(ref, FLOOR)
        if ratio >= best[2]:
            best = (seam, ref, ratio)
    return best


def seam_numbers(img):
    """Worst (seam_step, ref_step, ratio) over both axes and all channels."""
    h, w = img.shape[:2]
    if h < 4 or w < 4:
        raise ValueError("image too small (need at least 4x4)")
    worst = (0.0, 0.0, 0.0)
    for ch in range(img.shape[2]):
        plane = img[:, :, ch]
        for p in (plane, plane.T):  # columns, then rows
            seam, ref, ratio = _axis_numbers(np.ascontiguousarray(p))
            if ratio >= worst[2]:
                worst = (seam, ref, ratio)
    return worst


def blotch(img):
    lum = img.mean(axis=2)
    h, w = lum.shape
    gh, gw = (h // 4) * 4, (w // 4) * 4
    blocks = lum[:gh, :gw].reshape(4, gh // 4, 4, gw // 4).mean(axis=(1, 3))
    return float(blocks.std())


def measure(img, max_ratio=MAX_RATIO, max_blotch=MAX_BLOTCH):
    img = np.asarray(img, dtype=np.float32)
    seam, ref, ratio = seam_numbers(img)
    b = blotch(img)
    return {
        "seam_ratio": round(ratio, 4),
        "seam_step": round(seam, 4),
        "ref_step": round(ref, 4),
        "blotch": round(b, 4),
        "max_ratio": max_ratio,
        "max_blotch": max_blotch,
        "pass": bool(ratio <= max_ratio and b <= max_blotch),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("images", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-ratio", type=float, default=MAX_RATIO)
    ap.add_argument("--max-blotch", type=float, default=MAX_BLOTCH)
    args = ap.parse_args(argv)
    results, errors, bad = {}, {}, False
    for p in args.images:
        try:
            results[p] = measure(load(p), args.max_ratio, args.max_blotch)
        except Exception as e:  # unreadable file, too small, not an image
            errors[p] = str(e)
            print(f"error: {p}: {e}", file=sys.stderr)
            continue
        bad = bad or not results[p]["pass"]
    if args.json:
        out = dict(results)
        for p, msg in errors.items():
            out[p] = {"error": msg}
        print(json.dumps(out, indent=2))
    else:
        for p, r in results.items():
            print(f"{'PASS' if r['pass'] else 'FAIL'} {p}: seam_ratio={r['seam_ratio']} "
                  f"(step {r['seam_step']} vs ref {r['ref_step']}) blotch={r['blotch']}")
    if errors:
        return 2
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
