#!/usr/bin/env python3
"""Contact sheets for GEN 1, so the picks can be made in one look.

    python3 scripts/gen1_contact.py                 # build from work/generated (re-run as results land)
    python3 scripts/gen1_contact.py --placeholders  # dry run: fake images in a temp dir, nothing real touched

Output (work/generated/sheets/, or the temp dir): one PNG per subject (s1_mainstreet, s2_chase, s3_depot,
hero_car): a row per direction A/B/C, gpt on the left and fal on the right, labelled; plus props.png with
the 7 props (6 meshy + the Rodin water tower, labelled "rodin: owner OK needed"). A job that has not landed
shows a grey PENDING tile; a job recorded FAILED in work/gen1-status.json shows a red tile with the reason.
Read-only on the generated assets; it only writes the sheets.
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import gen1_launch as g  # noqa: E402

TILE = (512, 288)
PAD, HEAD = 8, 26
BG = (24, 24, 28)


def _font(size):
    for p in ("/usr/share/fonts/TTF/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def find_image(job, root):
    """Best picture for a job: concept.png for concepts; for props a turntable/thumb/preview if any, else concept.png."""
    d = (root / g.CONCEPT_OUT / job["name"]) if job["lane"] in ("gpt", "fal") else (root / g.OUT / job["name"])
    if job["lane"] in ("gpt", "fal"):
        p = d / "concept.png"
        return p if p.exists() else None
    if not d.exists():
        return None
    for pat in ("*turntable*.png", "*thumb*.png", "*preview*.png", "*render*.png", "concept.png"):
        hit = sorted(d.rglob(pat))
        if hit:
            return hit[0]
    return None


def tile(img_path, label, state, size=TILE):
    t = Image.new("RGB", size, BG)
    dr = ImageDraw.Draw(t)
    if img_path:
        im = Image.open(img_path).convert("RGB")
        im.thumbnail(size)
        t.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2))
    else:
        failed = state.get("state") == "FAILED"
        dr.rectangle([0, 0, size[0] - 1, size[1] - 1], fill=(90, 24, 24) if failed else (48, 48, 52))
        msg = "FAILED: " + state.get("detail", "")[:60] if failed else "PENDING"
        dr.text((12, size[1] // 2 - 8), msg, fill=(255, 255, 255), font=_font(18))
    return t


def sheet(rows, cols, title):
    """rows: list of lists of (img_path, label, state) tuples; cols = column count."""
    f, fb = _font(15), _font(22)
    w = cols * (TILE[0] + PAD) + PAD
    h = 40 + len(rows) * (TILE[1] + HEAD + PAD) + PAD
    out = Image.new("RGB", (w, h), BG)
    dr = ImageDraw.Draw(out)
    dr.text((PAD, 8), title, fill=(255, 176, 74), font=fb)
    y = 40
    for row in rows:
        for c, (p, label, state) in enumerate(row):
            x = PAD + c * (TILE[0] + PAD)
            dr.text((x, y + 4), label, fill=(230, 230, 230), font=f)
            out.paste(tile(p, label, state), (x, y + HEAD))
        y += TILE[1] + HEAD + PAD
    return out


def build(root, out_dir, recorded):
    lanes = g.jobs()
    by_name = {j["name"]: j for items in lanes.values() for j in items}
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for key, subject in g.SUBJECTS:
        rows = []
        for d in g.DIRECTIONS:
            row = []
            for prov in ("gpt", "fal"):
                j = by_name[f"concept_{d}_{key}_{prov}"]
                row.append((find_image(j, root), f"{d} / {prov}", recorded.get(j["name"], {})))
            rows.append(row)
        p = out_dir / f"{key}.png"
        sheet(rows, 2, f"{key}: {subject[:70]}").save(p)
        written.append(p)
    # Hub picks (2026-11-12): direction A everywhere; hero car and S3 depot redone on fal (v3).
    picks = []
    for label, name in (("S1 A/fal", "concept_A_s1_mainstreet_fal"), ("S2 A/fal", "concept_A_s2_chase_fal"),
                        ("S3 A/fal v3", "concept_A_s3_depot_fal_v3"), ("hero A/fal v3", "concept_A_hero_car_fal_v3")):
        img = root / g.CONCEPT_OUT / name / "concept.png"
        picks.append((img if img.exists() else None, label, recorded.get(name, {})))
    p = out_dir / "picks_A.png"
    sheet([picks], 4, "direction A picks").save(p)
    written.append(p)
    prop_tiles = []
    for name, _prompt, p3 in g.PROPS:
        j = by_name[name]
        label = name + ("  (rodin: owner OK needed)" if p3 == "hyper3d" else f"  ({p3})")
        prop_tiles.append((find_image(j, root), label, recorded.get(name, {})))
    rows = [prop_tiles[i:i + 4] for i in range(0, len(prop_tiles), 4)]
    p = out_dir / "props.png"
    sheet(rows, 4, "props (3D lane)").save(p)
    written.append(p)
    return written


def placeholders(root):
    """Fake the landed files for a dry run: every other concept and the first 4 props exist; one concept FAILED."""
    lanes = g.jobs()
    recorded = {}
    n = 0
    for items in lanes.values():
        for j in items:
            n += 1
            if j["lane"] in ("gpt", "fal"):
                p = root / g.CONCEPT_OUT / j["name"] / "concept.png"
            else:
                p = root / g.OUT / j["name"] / "concept.png"
            if n % 2 == 0 and j["lane"] != "3d" or (j["lane"] == "3d" and n % 3 != 0):
                p.parent.mkdir(parents=True, exist_ok=True)
                im = Image.new("RGB", (1024, 576), ((n * 37) % 200 + 30, (n * 91) % 200 + 30, (n * 53) % 200 + 30))
                ImageDraw.Draw(im).text((30, 30), j["name"], fill=(255, 255, 255), font=_font(40))
                im.save(p)
            elif n % 7 == 0:
                recorded[j["name"]] = {"state": "FAILED", "detail": "timeout 900s"}
    return recorded


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--placeholders", action="store_true", help="dry run in a temp dir with fake images")
    a = ap.parse_args()
    if a.placeholders:
        root = Path(tempfile.mkdtemp(prefix="gen1-contact-"))
        recorded = placeholders(root)
        out_dir = root / "sheets"
    else:
        root = ROOT
        try:
            recorded = json.loads(g.STATUS.read_text())
        except (OSError, ValueError):
            recorded = {}
        out_dir = ROOT / g.OUT / "sheets"
    for p in build(root, out_dir, recorded):
        print(p)


if __name__ == "__main__":
    main()
