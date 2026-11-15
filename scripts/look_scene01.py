#!/usr/bin/env python3
"""Look pass for L_Scene01 (hub lock): black backstage void, amber tungsten key, steel-blue fill/rim,
road not blown out. Run with the editor open: python3 scripts/look_scene01.py  (idempotent).
NB: light_color via unreal.Color reads as BGR here, so the values below are written (B,G,R).
"""
import subprocess
import sys
from pathlib import Path

MX = Path.home() / ".local/state/megajam-mx/mx.py"

PY = """
import unreal
L = unreal.EditorLevelLibrary
acts = {a.get_actor_label(): a for a in L.get_all_level_actors()}
out = []
# 1. black void: no atmosphere, no sky colour
for a in list(acts.values()):
    if a.get_class().get_name() in ('SkyAtmosphere', 'ExponentialHeightFog', 'VolumetricCloud'):
        a.destroy_actor(); out.append('del ' + a.get_actor_label())
sky = acts['SkyLight'].light_component
sky.set_editor_property('intensity', 0.5)
sky.set_editor_property('light_color', unreal.Color(140, 100, 70, 255))
sky.set_editor_property('real_time_capture', False)
# 2. amber tungsten key
k = acts['KeyLight']
k.set_actor_rotation(unreal.Rotator(0, -32, 25), False)
kc = k.light_component
kc.set_editor_property('intensity', 8.0)
kc.set_editor_property('light_color', unreal.Color(74, 176, 255, 255))
# 3. steel-blue rim/fill (second directional, from the opposite side, low)
rim = acts.get('RimLight')
if rim is None:
    rim = L.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(0, -20, 200))
    rim.set_actor_label('RimLight')
rim.set_actor_rotation(unreal.Rotator(0, -20, 200), False)
rc = rim.light_component
rc.set_editor_property('intensity', 3.0)
rc.set_editor_property('light_color', unreal.Color(201, 134, 91, 255))
rc.set_editor_property('atmosphere_sun_light', False)
kc.set_editor_property('atmosphere_sun_light', False)
# 4. manual exposure so the road does not blow out
pp = acts.get('LookPP')
if pp is None:
    pp = L.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    pp.set_actor_label('LookPP')
pp.set_editor_property('unbound', True)
s = pp.settings
s.set_editor_property('override_auto_exposure_method', True)
s.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL)
s.set_editor_property('override_auto_exposure_bias', True)
s.set_editor_property('auto_exposure_bias', 9.0)
s.set_editor_property('override_bloom_intensity', True)
s.set_editor_property('bloom_intensity', 0.6)
s.set_editor_property('override_vignette_intensity', True)
s.set_editor_property('vignette_intensity', 0.6)
pp.set_editor_property('settings', s)
# 5. palette lock (art-pack-gen1 / style guide): road dark asphalt, ground = void #0E0D0C, via our own M_FlatColor
def lin(c):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return unreal.LinearColor(f(c[0]), f(c[1]), f(c[2]), 1.0)
master = unreal.load_asset('/Game/Staging/Materials/M_FlatColor')
def mi(name, c):
    path = '/Game/Staging/Materials/' + name
    m = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/Staging/Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    m.set_editor_property('parent', master)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(m, 'Color', lin(c))
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m
acts['Floor_Strip'].static_mesh_component.set_material(0, mi('MI_Look_Road', (0.30, 0.29, 0.30)))
acts['Ground_Plane'].static_mesh_component.set_material(0, mi('MI_Look_Void', (0.055, 0.05, 0.047)))
out.append('road+void set')
str(out)
"""


def main():
    r = subprocess.run([sys.executable, str(MX), "py", PY], capture_output=True, text=True, timeout=240)
    print(r.stdout.strip()[-1500:] or r.stderr.strip()[-800:])
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
