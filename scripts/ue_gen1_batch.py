"""In-editor batch import for GEN 1 props (run by scripts/gen1_import.py, never by hand over MCP).

Run headless:  UnrealEditor-Cmd JumpCut.uproject -ExecCmds="py scripts/ue_gen1_batch.py" with GEN1_MANIFEST=MANIFEST.json GEN1_SCRIPTS=scripts -unattended
MANIFEST.json: {"dest": "/Game/Staging/Gen1/", "result": "/abs/result.json",
                "items": [{"name": "Barrel", "glb": "/abs/SM_Barrel.glb", "hold": false}]}
Each item goes through ue_import_asset.import_asset (collision, LOD, PBR check), then the static mesh is measured:
size in cm, pivot offset from the base, simple-collision shapes. Prints one GEN1_IMPORT line per item and writes
the same rows to the result file. Warnings are listed per item; nothing here ships an asset.
"""
import json
import os
import sys

import unreal

SIZE_MIN_CM, SIZE_MAX_CM = 10.0, 3000.0  # longest side outside this is probably the wrong scale
PIVOT_TOL = 0.15  # base should sit within 15% of the height from the pivot


def measure(path):
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    row = {"asset": path, "warnings": []}
    if not isinstance(mesh, unreal.StaticMesh):
        row["warnings"].append("not a StaticMesh (skeletal or missing)")
        return row
    b = mesh.get_bounds()
    o, e = b.origin, b.box_extent
    size = [round(2 * e.x, 1), round(2 * e.y, 1), round(2 * e.z, 1)]
    base_off = round(o.z - e.z, 1)  # 0 = pivot on the base; negative = pivot above the base
    row.update(size_cm=size, pivot_base_offset_cm=base_off, centre_xy=[round(o.x, 1), round(o.y, 1)])
    longest = max(size)
    if not SIZE_MIN_CM <= longest <= SIZE_MAX_CM:
        row["warnings"].append(f"scale: longest side {longest} cm")
    if abs(base_off) > PIVOT_TOL * max(size[2], 1.0) and abs(o.z) > PIVOT_TOL * max(size[2], 1.0):
        row["warnings"].append(f"pivot: base is {base_off} cm from the origin")
    try:
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        shapes = sub.get_simple_collision_count(mesh) + sub.get_convex_collision_count(mesh)
    except Exception as exc:  # noqa: BLE001
        shapes = None
        row["warnings"].append(f"collision count unavailable ({exc})")
    row["collision_shapes"] = shapes
    if shapes == 0:
        row["warnings"].append("no collision")
    return row


def main(manifest_path):
    sys.path.insert(0, os.environ["GEN1_SCRIPTS"])
    import ue_import_asset  # noqa: E402
    man = json.load(open(manifest_path))
    rows = []
    for it in man["items"]:
        row = {"name": it["name"], "glb": it["glb"], "hold": bool(it.get("hold"))}
        try:
            summary = ue_import_asset.import_asset(it["glb"], man["dest"], it["name"], "prop",
                                                   require_pbr=not it.get("allow_flat"))
            row["summary"] = summary
            if summary.startswith("FAILED"):
                row["error"] = summary
            else:
                path = summary.split("Created ", 1)[1].split(" |", 1)[0].split(" (+", 1)[0].strip()
                row.update(measure(path))
        except Exception as exc:  # noqa: BLE001 - one bad prop must not stop the batch
            row["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
        print("GEN1_IMPORT " + json.dumps(row))
    json.dump(rows, open(man["result"], "w"), indent=1)
    print(f"GEN1_IMPORT_DONE {len(rows)} items, {sum(1 for r in rows if r.get('error'))} errors")


try:
    main(os.environ["GEN1_MANIFEST"])
finally:  # always leave: a stuck headless editor would hold the project
    unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
