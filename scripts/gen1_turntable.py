#!/usr/bin/env python3
"""Turntable thumbs for the GEN 1 props (run AFTER gen1_import.py, with the editor up OFF-SCREEN via
scripts/launch-editor.sh; the Lead is the only MCP caller).

    python3 scripts/gen1_turntable.py [--dest /Game/Staging/Gen1] [--outdir DIR] [NAME ...]

For each static mesh under --dest: spawns a temporary actor 40 km above the map origin (nothing else is near),
reads its bounds, takes 4 shots (yaw 0/90/180/270) with `mx.py shot`, destroys the actor. The level is never
saved by this script. Writes a contact sheet row per prop into stages/02_build/output/gen1-import-report.md
(appended section "Turntable thumbs") when --report is given.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MX = Path.home() / ".local/state/megajam-mx/mx.py"
STAGE = (0.0, 0.0, 40000.0)

LIST_PY = """
import unreal, json
reg = unreal.AssetRegistryHelpers.get_asset_registry()
assets = reg.get_assets_by_path('%(dest)s', recursive=True)
json.dumps([str(a.package_name) + '.' + str(a.asset_name) for a in assets if str(a.asset_class_path.asset_name) == 'StaticMesh'])
"""

SPAWN_PY = """
import unreal, json
mesh = unreal.load_asset('%(path)s')
act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(%(x)s, %(y)s, %(z)s))
act.set_actor_label('GEN1_TURNTABLE_TMP')
act.static_mesh_component.set_static_mesh(mesh)
o, e = act.get_actor_bounds(False)
json.dumps({'origin': [o.x, o.y, o.z], 'extent': [e.x, e.y, e.z]})
"""

KILL_PY = """
import unreal
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == 'GEN1_TURNTABLE_TMP':
        a.destroy_actor()
'cleared'
"""


def mx(*args, stdin=None):
    # `mx.py py CODE` takes the code inline (a path is NOT read); it returns the last expression, print() is lost
    if stdin is not None and args[:2] == ("py", "-"):
        args, stdin = ("py", stdin), None
    r = subprocess.run([sys.executable, str(MX), *args], input=stdin, capture_output=True, text=True, timeout=180)
    if r.returncode:
        raise RuntimeError(f"mx.py {' '.join(args[:2])} failed: {r.stdout[-300:]} {r.stderr[-300:]}")
    return r.stdout


def last_json(text):
    for line in reversed(text.strip().splitlines()):
        line = line.strip().strip('"').replace('\\"', '"')
        if line.startswith(("{", "[")):
            return json.loads(line)
    raise ValueError("no JSON in: " + text[-200:])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--dest", default="/Game/Staging/Gen1")
    ap.add_argument("--outdir", default=str(ROOT / "work/gen1-import/turntable"))
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    Path(a.outdir).mkdir(parents=True, exist_ok=True)
    meshes = last_json(mx("py", "-", stdin=LIST_PY % {"dest": a.dest}))
    if a.names:
        meshes = [m for m in meshes if any(m.split(".")[-1].endswith(n) for n in a.names)]
    rows = []
    for path in sorted(meshes):
        name = path.split(".")[-1]
        try:
            b = last_json(mx("py", "-", stdin=SPAWN_PY % {"path": path, "x": STAGE[0], "y": STAGE[1], "z": STAGE[2]}))
            ox, oy, oz = b["origin"]
            ex, ey, ez = b["extent"]
            r = max(ex, ey, ez) * 2.6 + 50
            shots = []
            for yaw in (0, 90, 180, 270):
                import math
                # camera sits on a circle around the prop, looks back at it, a little above
                cx = ox - r * math.cos(math.radians(yaw))
                cy = oy - r * math.sin(math.radians(yaw))
                cz = oz + r * 0.35
                pitch = -math.degrees(math.atan2(cz - oz, r))
                out = mx("shot", f"{name}_y{yaw}", json.dumps({"location": f"{cx:.0f},{cy:.0f},{cz:.0f}",
                                                                "rotation": f"{pitch:.1f},{yaw},0",
                                                                "outdir": a.outdir}))
                shots.append(out.strip().splitlines()[-1])
            rows.append((name, shots))
            print(f"OK {name}: {len(shots)} shots")
        except Exception as exc:  # noqa: BLE001 - one prop must not stop the rest
            print(f"FAIL {name}: {exc}")
            rows.append((name, []))
        finally:
            try:
                mx("py", "-", stdin=KILL_PY)
            except Exception as exc:  # noqa: BLE001
                print(f"WARN could not clear temp actor: {exc}")
    if a.report and rows:
        rep = ROOT / "stages/02_build/output/gen1-import-report.md"
        lines = ["", "## Turntable thumbs", ""] + [f"- {n}: " + (", ".join(s) if s else "FAILED") for n, s in rows]
        with open(rep, "a") as f:
            f.write("\n".join(lines) + "\n")
    return 0 if all(s for _, s in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
