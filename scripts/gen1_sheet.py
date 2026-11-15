#!/usr/bin/env python3
"""Contact sheet of the gen1_turntable.py shots: one row per prop, 4 angles. Output: stages/02_build/output/gen1-turntable-sheet.png"""
import glob
import os
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "work/gen1-import/turntable"
OUT = ROOT / "stages/02_build/output/gen1-turntable-sheet.png"
W, H = 400, 260

fs = sorted(glob.glob(str(D / "*.png")))
names = sorted({os.path.basename(f).split("-", 1)[1].rsplit("_y", 1)[0] for f in fs})
sheet = Image.new("RGB", (W * 4, H * len(names)))
for r, n in enumerate(names):
    for c, y in enumerate((0, 90, 180, 270)):
        hit = glob.glob(f"{D}/*-{n}_y{y}.png")
        if not hit:
            continue
        im = Image.open(hit[0]).convert("RGB")
        im.thumbnail((W, H))
        sheet.paste(im, (c * W, r * H))
sheet.save(OUT)
print(OUT, sheet.size)
