#!/usr/bin/env python3
"""GEN 1 redo (hub pick 2026-11-12): direction A only, fal. Hero car mid-jump; S3 depot with gas holder + timber bridge."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import gen1_launch as g  # noqa: E402

STYLE = g.DIRECTIONS["A"]
REDO = {
    "concept_A_hero_car_fal_v3": "1970s muscle car caught MID-JUMP, all four wheels off the ground, nose up, three-quarter view, "
                                 "smooth featureless blank-faced grille with no emblem, completely blank plate-less bumper, no badge or logo anywhere, invented boxy car shape unlike any real make, side view of the car in the air",
    "concept_A_s3_depot_fal_v3": "toy-scale 1970s backlot fuel depot, wide view, with one large round gas-holder tank clearly "
                                 "visible and a timber plank bridge crossing in the foreground, plain unpainted tank with no emblem, no star, no symbol, set in a pure black void with amber light only",
}


def main():
    """The paid fal generations. Only runs as a script, never on import."""
    rc = 0
    for name, subject in REDO.items():
        cmd = ["python3", "scripts/gen_asset.py", "--name", name, "--provider", "fal", "--concept-only",
               "--prompt", f"{subject}. {STYLE}. No text, no logos, no third-party IP.", "--out-dir", g.CONCEPT_OUT]
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=g.CONCEPT_TIMEOUT)
        print(name, "rc", p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1:], flush=True)
        rc |= p.returncode
    return rc


if __name__ == "__main__":
    sys.exit(main())
