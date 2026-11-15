#!/usr/bin/env python3
"""Apply a scene's look preset (look bible 2/3, lighting-post.md section 0-1) to the open level, over Unreal MCP.

  look_apply.py SCENE [--fog] [--saturation-floor X] [--dry-run]

SCENE is 1, 2 or 3. Idempotent: it finds KeyLight / RimLight / SkyLight / LookPP (and LookFog with --fog) by label,
creates RimLight / LookPP / LookFog if missing, and sets every value from the preset. It does not delete anything
and does not save the level: run scripts/force_save_level.py after it (it verifies the .umap on disk).

  --fog                 also set the scene's exponential height fog (look step 7; volumetric fog stays off)
  --saturation-floor X  set SaturationFloor on /Game/Data/Tuning/DA_Tuning_Default and save that asset (step 12)
  --key-lux X           override the preset's key light intensity (lux), for exposure tuning
  --dry-run             print the preset and the editor script; touch nothing

Colours go through keyword args (unreal.Color(r=, g=, b=)), because positional unreal.Color reads as B,G,R,A.
The editor script reads every light colour back, so the output shows what the editor really stored.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MX_CANDIDATES = [HERE / "mx.py", Path.home() / ".local/state/megajam-mx/mx.py"]
TUNING_DA = "/Game/Data/Tuning/DA_Tuning_Default"

# lighting-post.md section 1. Rotations are (pitch, yaw). Intensities: directional = lux.
# S2/S3 keys are still the bible values; S1 needed 2x, so re-measure them (road value) once their greybox exists.
PRESETS = {
    1: {
        "name": "S1 Rehearsal",
        # 24 lux, not the bible's 12: measured 2026-11-12 on L_Scene01 (bias 9, MI_Look_Road): 12 lux -> road 24% HSV
        # value (mud), 24 -> 43.6% (target 40-45%), 30 -> 51%. Clipping under 1% (HUD only) at all three.
        "key": {"color": "#FFB04A", "lux": 24.0, "rot": (-32, 25)},
        "rim": {"color": "#5B86C9", "lux": 2.5, "rot": (-20, 200)},
        "sky": {"color": "#5A4A3A", "intensity": 0.30},
        "fog": {"density": 0.020, "falloff": 0.20, "inscatter": "#3A2614", "start": 2500.0, "max_opacity": 0.85,
                "dir_inscatter": "#FFB04A", "dir_exponent": 8.0, "dir_start": 2000.0},
        "post": {"white_temp": 7000.0, "white_tint": 0.0, "shadows_gain": (0.95, 0.90, 0.85),
                 "highlights_gain": (1.05, 1.0, 0.92), "contrast": 1.08, "toe": 0.60, "shoulder": 0.26,
                 "black_clip": 0.0, "white_clip": 0.04, "bloom": 0.6, "bloom_threshold": 1.5, "vignette": 0.25,
                 "mb_amount": 0.3, "mb_max": 2.0, "exposure_bias": 9.0},
    },
    2: {
        "name": "S2 The Chase",
        "key": {"color": "#5B86C9", "lux": 6.0, "rot": (-40, 160)},
        "rim": {"color": "#9DB4D8", "lux": 2.0, "rot": (-15, 340)},
        "sky": {"color": "#2A3A5A", "intensity": 0.35},
        "fog": {"density": 0.025, "falloff": 0.20, "inscatter": "#142033", "start": 2000.0, "max_opacity": 0.85,
                "dir_inscatter": None, "dir_exponent": 8.0, "dir_start": 2000.0},
        "post": {"white_temp": 5800.0, "white_tint": 0.0, "shadows_gain": (0.85, 0.90, 1.05),
                 "highlights_gain": (1.0, 0.98, 0.95), "contrast": 1.12, "toe": 0.60, "shoulder": 0.26,
                 "black_clip": 0.0, "white_clip": 0.04, "bloom": 0.7, "bloom_threshold": 1.5, "vignette": 0.25,
                 "mb_amount": 0.3, "mb_max": 2.0, "exposure_bias": 9.0},
    },
    3: {
        "name": "S3 The Finale",
        "key": {"color": "#FF5A1F", "lux": 10.0, "rot": (-18, 40)},
        "rim": {"color": "#FF7A30", "lux": 4.0, "rot": (-10, 210)},
        "sky": {"color": "#4A2A22", "intensity": 0.25},
        "fog": {"density": 0.030, "falloff": 0.15, "inscatter": "#3A120A", "start": 1500.0, "max_opacity": 0.90,
                "dir_inscatter": "#FF5A1F", "dir_exponent": 6.0, "dir_start": 1500.0},
        "post": {"white_temp": 7400.0, "white_tint": 0.03, "shadows_gain": (1.05, 0.88, 0.85),
                 "highlights_gain": (1.06, 0.97, 0.90), "contrast": 1.15, "toe": 0.62, "shoulder": 0.26,
                 "black_clip": 0.0, "white_clip": 0.04, "bloom": 0.7, "bloom_threshold": 1.5, "vignette": 0.30,
                 "mb_amount": 0.3, "mb_max": 2.0, "exposure_bias": 9.0},
    },
}

# Section 0 rules that hold for every scene.
SHADOW_DISTANCE_CM = 6000.0

EDITOR_SCRIPT = r'''
import unreal, json
P = json.loads(__PRESET__)
L = unreal.EditorLevelLibrary
acts = {a.get_actor_label(): a for a in L.get_all_level_actors()}
out, errs = [], []

def rgb(h):
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def color(h):
    r, g, b = rgb(h)
    return unreal.Color(r=r, g=g, b=b, a=255)

def lin(h):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return unreal.LinearColor(f(r / 255.0), f(g / 255.0), f(b / 255.0), 1.0)

def put(obj, prop, val, tag):
    try:
        obj.set_editor_property(prop, val)
    except Exception as e:
        errs.append('%s.%s: %s' % (tag, prop, str(e)[:120]))

def back(c):
    v = c.get_editor_property('light_color')
    return '#%02X%02X%02X' % (v.r, v.g, v.b)

def directional(label, spec, shadows):
    a = acts.get(label)
    if a is None:
        a = L.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500))
        a.set_actor_label(label)
        out.append('spawned ' + label)
    pitch, yaw = spec['rot']
    a.set_actor_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw), False)
    c = a.light_component
    put(c, 'mobility', unreal.ComponentMobility.MOVABLE, label)
    put(c, 'intensity', float(spec['lux']), label)
    put(c, 'light_color', color(spec['color']), label)
    put(c, 'cast_shadows', shadows, label)
    put(c, 'atmosphere_sun_light', False, label)
    if shadows:
        put(c, 'dynamic_shadow_distance_movable_light', P['shadow_distance'], label)
    out.append('%s %s %.1f lux rot(%d,%d) shadows=%s' % (label, back(c), c.get_editor_property('intensity'), pitch, yaw, shadows))

if 'KeyLight' not in acts:
    errs.append('KeyLight actor missing (expected from the greybox); spawning one')
directional('KeyLight', P['key'], True)
directional('RimLight', P['rim'], False)

sky = acts.get('SkyLight')
if sky is None:
    errs.append('SkyLight actor missing; skipped')
else:
    sc = sky.light_component
    put(sc, 'intensity', float(P['sky']['intensity']), 'SkyLight')
    put(sc, 'light_color', color(P['sky']['color']), 'SkyLight')
    put(sc, 'real_time_capture', False, 'SkyLight')
    out.append('SkyLight %s %.2f' % (back(sc), sc.get_editor_property('intensity')))

pp = acts.get('LookPP')
if pp is None:
    pp = L.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    pp.set_actor_label('LookPP')
    out.append('spawned LookPP')
pp.set_editor_property('unbound', True)
s = pp.settings
q = P['post']
v4 = lambda t: unreal.Vector4(t[0], t[1], t[2], 1.0)
vals = {
    'auto_exposure_method': unreal.AutoExposureMethod.AEM_MANUAL,
    'auto_exposure_bias': q['exposure_bias'],
    'white_temp': q['white_temp'],
    'white_tint': q['white_tint'],
    'color_gain_shadows': v4(q['shadows_gain']),
    'color_gain_highlights': v4(q['highlights_gain']),
    'color_contrast': unreal.Vector4(1.0, 1.0, 1.0, q['contrast']),
    'film_toe': q['toe'],
    'film_shoulder': q['shoulder'],
    'film_black_clip': q['black_clip'],
    'film_white_clip': q['white_clip'],
    'bloom_intensity': q['bloom'],
    'bloom_threshold': q['bloom_threshold'],
    'vignette_intensity': q['vignette'],
    'motion_blur_amount': q['mb_amount'],
    'motion_blur_max': q['mb_max'],
}
for k, v in vals.items():
    put(s, 'override_' + k, True, 'LookPP')
    put(s, k, v, 'LookPP')
pp.set_editor_property('settings', s)
s2 = pp.settings
out.append('LookPP temp %.0f contrast %.2f toe %.2f bloom %.2f/%.2f vignette %.2f mb %.2f bias %.1f' % (
    s2.white_temp, s2.color_contrast.w, s2.film_toe, s2.bloom_intensity, s2.bloom_threshold,
    s2.vignette_intensity, s2.motion_blur_amount, s2.auto_exposure_bias))

if P.get('fog'):
    f = P['fog']
    fog = acts.get('LookFog')
    if fog is None:
        fog = L.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0))
        fog.set_actor_label('LookFog')
        out.append('spawned LookFog')
    fc = fog.component
    put(fc, 'volumetric_fog', False, 'LookFog')
    put(fc, 'fog_density', f['density'], 'LookFog')
    put(fc, 'fog_height_falloff', f['falloff'], 'LookFog')
    put(fc, 'fog_inscattering_luminance', lin(f['inscatter']), 'LookFog')
    put(fc, 'start_distance', f['start'], 'LookFog')
    put(fc, 'fog_max_opacity', f['max_opacity'], 'LookFog')
    if f['dir_inscatter']:
        put(fc, 'directional_inscattering_luminance', lin(f['dir_inscatter']), 'LookFog')
        put(fc, 'directional_inscattering_exponent', f['dir_exponent'], 'LookFog')
        put(fc, 'directional_inscattering_start_distance', f['dir_start'], 'LookFog')
    else:
        put(fc, 'directional_inscattering_luminance', unreal.LinearColor(0, 0, 0, 1), 'LookFog')
    out.append('LookFog density %.3f start %.0f' % (fc.get_editor_property('fog_density'), fc.get_editor_property('start_distance')))

if P.get('saturation_floor') is not None:
    da = unreal.load_asset(P['tuning_da'])
    if da is None:
        errs.append('tuning DA not found: ' + P['tuning_da'])
    else:
        put(da, 'saturation_floor', float(P['saturation_floor']), 'Tuning')
        unreal.EditorAssetLibrary.save_loaded_asset(da, False)
        out.append('Tuning saturation_floor %.2f (saved)' % da.get_editor_property('saturation_floor'))

json.dumps({'ok': not errs, 'out': out, 'errors': errs})
'''


def build(scene, fog, saturation_floor, key_lux=None):
    p = json.loads(json.dumps(PRESETS[scene]))
    if key_lux is not None:
        p["key"]["lux"] = key_lux
    p["shadow_distance"] = SHADOW_DISTANCE_CM
    if not fog:
        p["fog"] = None
    p["saturation_floor"] = saturation_floor
    p["tuning_da"] = TUNING_DA
    return p, EDITOR_SCRIPT.replace("__PRESET__", repr(json.dumps(p)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scene", type=int, choices=sorted(PRESETS))
    ap.add_argument("--fog", action="store_true")
    ap.add_argument("--saturation-floor", type=float, default=None)
    ap.add_argument("--key-lux", type=float, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.saturation_floor is not None and not 0.0 <= a.saturation_floor <= 1.0:
        ap.error("--saturation-floor must be between 0 and 1")
    if a.key_lux is not None and not 0.0 < a.key_lux <= 100.0:
        ap.error("--key-lux must be in (0, 100]")
    preset, code = build(a.scene, a.fog, a.saturation_floor, a.key_lux)
    if a.dry_run:
        print(json.dumps(preset, indent=1))
        print("--- editor script (%d lines) ---" % code.count("\n"))
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
    return 0 if '"ok": true' in text or "'ok': True" in text or '\\"ok\\": true' in text else 1


if __name__ == "__main__":
    sys.exit(main())
