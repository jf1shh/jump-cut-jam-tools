#!/usr/bin/env python3
"""Build M_Car (clear coat) and point DA_Car_Number7 at it with the look-bible livery.

Look bible step 2 (materials.md section 4): cream body #F1E5C8, signal-red stripes #C8312F, black trim #1A1A1A.
The car is built from engine primitives in C++ (AJCCarPawn::StyleGreybox), one dynamic instance per part, so
M_Car is a plain parameter material: the code sets Color, Roughness, Metallic, ClearCoat, ClearCoatRoughness and
Emissive per part. Emissive = Color * Emissive (tail lights).

Runs inside the live editor through mx.py (the only Unreal MCP caller runs it). Idempotent: an existing M_Car is
rebuilt in place (expressions cleared) so re-runs never stack nodes. Prints one JSON line with "ok".

  python3 scripts/car_material.py [--dry-run]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MX_CANDIDATES = [HERE / "mx.py", Path.home() / ".local/state/megajam-mx/mx.py"]

MAT_DIR = "/Game/Materials/Car"
MAT_NAME = "M_Car"
DA_PATH = "/Game/Data/Cars/DA_Car_Number7"

# Linear values from materials.md section 4 (sRGB hex in the comment).
LIVERY = {
    "livery_body": (0.88, 0.79, 0.58),     # #F1E5C8 cream
    "livery_stripes": (0.58, 0.03, 0.03),  # #C8312F signal red
    "livery_trim": (0.010, 0.010, 0.010),  # #1A1A1A
}

# Parameter defaults = the body paint, so a bare M_Car preview already looks like the car.
SCALARS = [
    ("Roughness", 0.35, "MP_ROUGHNESS"),
    ("Metallic", 0.0, "MP_METALLIC"),
    ("ClearCoat", 1.0, "MP_CUSTOM_DATA0"),
    ("ClearCoatRoughness", 0.08, "MP_CUSTOM_DATA1"),
]

EDITOR_CODE = r'''
import unreal, json
MAT_DIR, MAT_NAME, DA_PATH = %(mat_dir)r, %(mat_name)r, %(da_path)r
LIVERY, SCALARS = %(livery)r, %(scalars)r
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
path = MAT_DIR + "/" + MAT_NAME
out = {"ok": False}
if eal.does_asset_exist(path):
    m = unreal.load_asset(path)
    mel.delete_all_material_expressions(m)
    out["material"] = "rebuilt"
else:
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(MAT_NAME, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    out["material"] = "created"
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_CLEAR_COAT)
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
col = mel.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -600, -200)
col.set_editor_property("parameter_name", "Color")
b = LIVERY["livery_body"]
col.set_editor_property("default_value", unreal.LinearColor(b[0], b[1], b[2], 1.0))
mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
y = 0
for name, val, prop in SCALARS:
    s = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, y)
    s.set_editor_property("parameter_name", name)
    s.set_editor_property("default_value", val)
    mel.connect_material_property(s, "", getattr(unreal.MaterialProperty, prop))
    y += 120
em = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, y)
em.set_editor_property("parameter_name", "Emissive")
em.set_editor_property("default_value", 0.0)
mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, y)
mel.connect_material_expressions(col, "", mul, "A")
mel.connect_material_expressions(em, "", mul, "B")
mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(m)
out["saved_material"] = bool(eal.save_asset(path, only_if_is_dirty=False))
out["shading_model"] = str(m.get_editor_property("shading_model"))
out["params"] = sorted(str(p) for p in mel.get_scalar_parameter_names(m)) + sorted(str(p) for p in mel.get_vector_parameter_names(m))

da = unreal.load_asset(DA_PATH)
if da is None:
    out["error"] = "DA not found: " + DA_PATH
else:
    da.set_editor_property("material", m)
    for prop, v in LIVERY.items():
        da.set_editor_property(prop, unreal.LinearColor(v[0], v[1], v[2], 1.0))
    out["saved_da"] = bool(eal.save_asset(DA_PATH, only_if_is_dirty=False))
    da = unreal.load_asset(DA_PATH)
    mat = da.get_editor_property("material")
    out["da_material"] = mat.get_path_name() if mat else None
    out["da_livery"] = {p: [round(c, 3) for c in (da.get_editor_property(p).r, da.get_editor_property(p).g, da.get_editor_property(p).b)] for p in LIVERY}
    out["ok"] = out["saved_material"] and out["saved_da"] and out["da_material"] is not None and out["da_material"].startswith(path)
print(json.dumps(out))
'''


def build_code():
    return EDITOR_CODE % {
        "mat_dir": MAT_DIR, "mat_name": MAT_NAME, "da_path": DA_PATH,
        "livery": LIVERY, "scalars": SCALARS,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="print the editor script and exit")
    a = ap.parse_args(argv)
    code = build_code()
    if a.dry_run:
        print(code)
        return 0
    mx = next((m for m in MX_CANDIDATES if m.exists()), None)
    if mx is None:
        print("mx.py not found in: " + ", ".join(map(str, MX_CANDIDATES)), file=sys.stderr)
        return 2
    r = subprocess.run([sys.executable, str(mx), "py", code], capture_output=True, text=True, timeout=240)
    text = r.stdout.strip() or r.stderr.strip()
    print(text[-3000:])
    if r.returncode != 0:
        return r.returncode
    return 0 if '"ok": true' in text or '\\"ok\\": true' in text else 1


if __name__ == "__main__":
    sys.exit(main())
