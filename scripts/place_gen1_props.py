#!/usr/bin/env python3
"""Place the GEN 1 A-direction props in the open level (L_Scene01) as roadside dressing. Editor up, Lead only.

    python3 scripts/place_gen1_props.py        # replaces every actor labelled Prop_* / PropText_* ; then `mx.py save`

Props sit OUTSIDE the 1400 cm floor strip (|y| >= 950): no lane is touched. Meshes import ~190 cm on the longest
side with the pivot at the centre, so each gets a scale and is dropped so its bottom sits on the ground plane (z=-150).
Flat props (barrel, truck) and the box-built clapper use our own M_FlatColor instances (colours given in sRGB,
converted to linear here), because the imported glTF material read near-white. The clapper is boxes + our own text.
"""
import subprocess  # NB: unreal.Rotator is (roll, pitch, yaw) - yaw is the LAST arg
import sys
from pathlib import Path

MX = Path.home() / ".local/state/megajam-mx/mx.py"

GROUND = -150  # Ground_Plane top (origin -200, half-height 50); the 1400 cm Floor_Strip top is 0 but props stay off it

# (label, mesh asset, x, y, yaw, scale, flat sRGB colour or None)
PLACEMENTS = [
    ("Prop_Truck_1", "/Game/Staging/Gen1/SM_PropTruck_flat/StaticMeshes/SM_PropTruck", 4200, -1000, 0, 2.7, (0.34, 0.31, 0.26)),
    ("Prop_Barrel_1", "/Game/Staging/Gen1/SM_Barrel_flat/StaticMeshes/SM_Barrel", 2600, 950, 0, 0.46, (0.30, 0.31, 0.33)),
    ("Prop_Barrel_2", "/Game/Staging/Gen1/SM_Barrel_flat/StaticMeshes/SM_Barrel", 2750, 1010, 40, 0.46, (0.30, 0.31, 0.33)),
    ("Prop_Barrel_3", "/Game/Staging/Gen1/SM_Barrel_flat/StaticMeshes/SM_Barrel", 8800, -980, 10, 0.46, (0.30, 0.31, 0.33)),
    ("Prop_Light_1", "/Game/Staging/Gen1/SM_StudioLight/StaticMeshes/SM_StudioLight", 1800, 1000, 200, 1.3, None),
    ("Prop_Light_2", "/Game/Staging/Gen1/SM_StudioLight/StaticMeshes/SM_StudioLight", 7000, -1000, -20, 1.3, None),
    ("Prop_Crane_1", "/Game/Staging/Gen1/SM_CameraCrane/StaticMeshes/SM_CameraCrane", 5600, 1250, 180, 3.5, None),
    ("Prop_WaterTower_1", "/Game/Staging/Gen1/SM_WaterTower/StaticMeshes/SM_WaterTower", 24000, 2600, 0, 5.3, None),
    ("Prop_Barrel_4", "/Game/Staging/Gen1/SM_Barrel_flat/StaticMeshes/SM_Barrel", 1100, 960, 20, 0.46, (0.30, 0.31, 0.33)),
    ("Prop_Barrel_5", "/Game/Staging/Gen1/SM_Barrel_flat/StaticMeshes/SM_Barrel", 1900, -960, 70, 0.46, (0.30, 0.31, 0.33)),
    ("Prop_Light_3", "/Game/Staging/Gen1/SM_StudioLight/StaticMeshes/SM_StudioLight", 1300, -1050, 160, 1.3, None),
    ("Prop_Light_4", "/Game/Staging/Gen1/SM_StudioLight/StaticMeshes/SM_StudioLight", 3300, 1050, 200, 1.3, None),
]

# clapper from boxes (cube = 100 cm): (label, local dx, dy, dz centre, scale xyz, sRGB colour)
CLAPPER_AT = (700, -1000, 0)  # x, y, yaw; board face looks toward -X (the approaching car)
CLAPPER_BOXES = [
    ("Prop_Clapper_Board", 0, 0, 90, (0.05, 1.6, 1.0), (0.06, 0.06, 0.07)),
    ("Prop_Clapper_Arm", 0, 0, 158, (0.07, 1.64, 0.2), (0.85, 0.85, 0.85)),
    ("Prop_Clapper_Stripe1", -4, -50, 158, (0.075, 0.24, 0.205), (0.05, 0.05, 0.05)),
    ("Prop_Clapper_Stripe2", -4, 0, 158, (0.075, 0.24, 0.205), (0.05, 0.05, 0.05)),
    ("Prop_Clapper_Stripe3", -4, 50, 158, (0.075, 0.24, 0.205), (0.05, 0.05, 0.05)),
]

PY = """
import unreal, math
L = unreal.EditorLevelLibrary
MAT = '/Game/Staging/Materials/M_FlatColor'
if not unreal.EditorAssetLibrary.does_asset_exist(MAT):
    unreal.EditorAssetLibrary.make_directory('/Game/Staging/Materials')
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_FlatColor', '/Game/Staging/Materials', unreal.Material, unreal.MaterialFactoryNew())
    ML = unreal.MaterialEditingLibrary
    p = ML.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -400, 0)
    p.set_editor_property('parameter_name', 'Color')
    p.set_editor_property('default_value', unreal.LinearColor(0.05, 0.05, 0.05, 1))
    r = ML.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 200)
    r.set_editor_property('r', 0.8)
    ML.connect_material_property(p, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    ML.connect_material_property(r, '', unreal.MaterialProperty.MP_ROUGHNESS)
    ML.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
master = unreal.load_asset(MAT)

def lin(c):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return unreal.LinearColor(f(c[0]), f(c[1]), f(c[2]), 1.0)

cache = {}
def mi_for(c):
    key = '%%.2f_%%.2f_%%.2f' %% c
    if key in cache: return cache[key]
    name = 'MI_Flat_' + key.replace('.', '')
    path = '/Game/Staging/Materials/' + name
    mi = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/Staging/Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property('parent', master)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, 'Color', lin(c))
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    cache[key] = mi
    return mi

for a in L.get_all_level_actors():
    if a.get_actor_label().startswith('Prop_') or a.get_actor_label().startswith('PropText_'):
        a.destroy_actor()
out = []
def drop(act, x, y):
    o, e = act.get_actor_bounds(False)
    act.set_actor_location(unreal.Vector(x, y, %(ground)d - (o.z - e.z)), False, False)
    return e.z * 2

for label, path, x, y, yaw, s, col in %(rows)r:
    mesh = unreal.load_asset(path)
    if not mesh:
        out.append(label + ': MESH MISSING'); continue
    act = L.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, 0), unreal.Rotator(0, 0, yaw))
    act.set_actor_label(label)
    act.static_mesh_component.set_static_mesh(mesh)
    act.set_actor_scale3d(unreal.Vector(s, s, s))
    if col:
        act.static_mesh_component.set_material(0, mi_for(col))
    out.append('%%s h=%%d' %% (label, drop(act, x, y)))

cube = unreal.load_asset('/Engine/BasicShapes/Cube')
cx, cy, cyaw = %(cat)r
ca, sa = math.cos(math.radians(cyaw)), math.sin(math.radians(cyaw))
for label, dx, dy, dz, sc, col in %(boxes)r:
    wx, wy = cx + dx * ca - dy * sa, cy + dx * sa + dy * ca
    b = L.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(wx, wy, dz + %(ground)d), unreal.Rotator(0, 0, cyaw))
    b.set_actor_label(label)
    b.static_mesh_component.set_static_mesh(cube)
    b.set_actor_scale3d(unreal.Vector(*sc))
    b.static_mesh_component.set_material(0, mi_for(col))
    out.append(label)
# our own clapper text on the board face (faces -X, toward the approaching car)
t = L.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(cx - 6, cy, 95 + %(ground)d), unreal.Rotator(0, 0, 180))
t.set_actor_label('PropText_Clapper')
c = t.text_render
c.set_text('JUMP CUT\\nSCENE 1\\nTAKE 1')
c.set_world_size(26.0)
c.set_text_render_color(unreal.Color(240, 240, 240, 255))
c.set_editor_property('horizontal_alignment', unreal.HorizTextAligment.EHTA_CENTER)
c.set_editor_property('vertical_alignment', unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
str(out)
"""


def main():
    code = PY % {"ground": GROUND, "rows": PLACEMENTS, "cat": CLAPPER_AT, "boxes": CLAPPER_BOXES}
    r = subprocess.run([sys.executable, str(MX), "py", code], capture_output=True, text=True, timeout=240)
    print(r.stdout.strip()[-1500:] or r.stderr.strip()[-800:])
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
