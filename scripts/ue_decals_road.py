"""Road-dressing decals for Jump Cut (UE 5.9 editor Python). Written by PROPS-1; NOT run by PROPS-1.

DECAL_MODE=apply (default in the editor), in the open editor:
  1. imports T_Decal_TapeX_{A,B,C}_D and T_Decal_Skid_{A,B}_D (RGBA PNG, from DECAL_PNG_DIR) to /Game/Textures/Decals
     (sRGB, clamped, skipped when already there);
  2. makes ONE deferred-decal material /Game/Materials/Road/M_RoadDecal (texture parameter `Decal`: RGB -> Base Color,
     A -> Opacity, Roughness 0.9, no specular, translucent decal blend) and one instance per texture;
  3. makes sure /Game/Maps/L_Scene01 is the open level (see "Level safety" below) and places DecalActors: a gaffer-tape X in
     each lane just past every stunt mark, tyre skids after every stunt (and after ramp rows, DECAL_RAMP_LAND_M past the ramp),
     and traffic cones at the kerb at every mark IF a static mesh with "cone" in its name exists under /Game (else cones are
     skipped and the log says so);
  4. tags every actor `RoadDressing` (outliner folder RoadDressing), then saves the level.
DECAL_MODE=revert deletes exactly the actors tagged RoadDressing and saves. DECAL_MODE=dry prints the plan and changes nothing
(also runs outside the editor: `python3 ue_decals_road.py` prints the plan for the S1 numbers).
DECAL_KINDS=tape,skid,cone (default all) is the partial kill switch: re-run apply, it always clears the old RoadDressing first.

Level safety (apply and revert): LoadMap does NOT prompt to save (Engine/Source/Editor/UnrealEd/Public/FileHelpers.h:57-64), so
the script never reloads blindly. If DECAL_LEVEL is already the open level it is NOT reloaded (unsaved edits stay, and the final
save writes them out with ours). If another level is open and any map package is dirty
(EditorLoadingAndSavingUtils.get_dirty_map_packages: world, built data and external actor packages) it aborts before changing
anything. A load_map that returns None, a missing JCRoad, a material that does not compile and a failed save all abort too,
JCRoad is checked before any old actor is deleted.

Same mark source as scatter_crew.py: DT_Stunts_S1/S2 (TOn, TMark, Surge, Of, Preset; D(T) = BaseSpeed*T + surge step), else the
S1 numbers (stunts 126,216,306,396,540,648 m; marks 162,252,342,468,576,684 m); CREW_STUNTS_M / CREW_MARKS_M override both.

Road facts: JCRoad spline along +X, lanes at -4/0/+4 m, half width 7 m, ground z -150 cm; MARK signs stand right of the road at
10.4 m so cones sit at the kerb (6.3 m), not there.

Texture orientation (UE 5.9, Engine/Shaders/Private/DeferredDecal.usf:152-158: DecalVector = OSPosition*0.5+0.5, then
UV = DecalVector.zyx.xy): image X (U) runs along the decal's local Z, image Y (V) along local Y, local X is the projection axis.
A DecalActor at Rotator(roll 0, pitch -90, yaw psi) has local X straight down, local Y = right of heading psi and local Z =
heading psi (FRotationTranslationMatrix, Core/Public/Math/RotationTranslationMatrix.h:72-84). So with psi = the road heading the
skid streaks (image X) run ALONG the road and DECAL_SKID_YAW_OFFSET stays 0. DecalSize is (depth half, local Y half, local Z
half), so a 2:1 skid PNG (1024x512) gets Y half = half/2 (across the road) and Z half = half (along it); the tape PNG is square
(1024x1024) so both halves are equal. If the first look shows the streaks crossing the road anyway, revert and rerun with
DECAL_SKID_YAW_OFFSET=90 (or -90).

Env knobs: DECAL_MODE, DECAL_KINDS, DECAL_LEVEL (/Game/Maps/L_Scene01), DECAL_SEED (1970), DECAL_PNG_DIR, DECAL_GROUND_Z (-150),
DECAL_TAPE_M (1.6 tape size m), DECAL_SKID_LEN_M (8), DECAL_RAMP_LAND_M (40), DECAL_SKID_YAW_OFFSET (0), DECAL_LOG.
"""
import math
import os
import random
import time

try:
    import unreal
except ImportError:  # outside the editor: dry run / unit tests only
    unreal = None

TAG = "RoadDressing"
FOLDER = "RoadDressing"
PNG_DIR = os.environ.get("DECAL_PNG_DIR", "~/Projects/megajam/work/generated")
TEX_DEST = "/Game/Textures/Decals"
MAT_DIR = "/Game/Materials/Road"
MAT_NAME = "M_RoadDecal"
LOG_PATH = os.environ.get("DECAL_LOG", "~/.local/state/megajam/props1-work/decals_road.log")
TAPES = ["T_Decal_TapeX_A_D", "T_Decal_TapeX_B_D", "T_Decal_TapeX_C_D"]
SKIDS = ["T_Decal_Skid_A_D", "T_Decal_Skid_B_D"]
LANES_M = (-4.0, 0.0, 4.0)
KERB_M = 6.3
S1_STUNTS_M = [126.0, 216.0, 306.0, 396.0, 540.0, 648.0]
S1_MARKS_M = [162.0, 252.0, 342.0, 468.0, 576.0, 684.0]
S1_PRESETS = ["FalseFront", "PropTruck", "LightRig", "WaterTower", "Drums", "Facade"]
DECAL_DEPTH_HALF_CM = 40.0  # half of the projection depth (local X)
SKID_ASPECT = 2.0  # skid PNGs are 1024x512: image X (along the road) is twice image Y (across it)


def env_f(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


def log(*parts):
    line = time.strftime("%H:%M:%S ") + " ".join(str(p) for p in parts)
    print("[decals] " + line)
    try:
        with open(LOG_PATH, "a") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------------------------------------
# Pure plan (no unreal)
# ---------------------------------------------------------------------------------------------------------
def dist_at(t, base_speed, surges, surge_time=3.0):
    d = base_speed * t
    for t_on, surge in surges:
        d += surge * max(0.0, min(t, t_on) - (t_on - surge_time))
    return d


def plan_decals(rows, kinds=None, seed=1970, tape_m=1.6, skid_len_m=8.0, ramp_land_m=40.0, road_m=720.0):
    """rows = [dict(stunt_m, mark_m, preset)]. Returns dict(kind, dist, lat, yaw_jit, size_m, variant) placements.

    tape: one X per lane just past each mark (variants cycle A,B,C; yaw jitter +-12 deg).
    skid: after each stunt (after the landing for a Ramp row), one lane per stunt chosen from the lane the stunt closes
          nearest the centre (alternating -4/0/+4 by seed), variants alternate A,B.
    cone: four per mark at the kerb (both sides, 1.5 m either side of the mark)."""
    rng = random.Random(seed)
    kinds = set(kinds) if kinds else {"tape", "skid", "cone"}
    out = []
    for i, r in enumerate(rows):
        s_d, m_d = r["stunt_m"], r["mark_m"]
        if "tape" in kinds:
            for j, lane in enumerate(LANES_M):
                out.append(dict(kind="tape", dist=round(m_d + 1.5, 2), lat=lane, yaw_jit=rng.uniform(-12, 12),
                                size_m=tape_m, variant=(i + j) % len(TAPES)))
        if "skid" in kinds:
            start = s_d + (ramp_land_m if r.get("preset") == "Ramp" else 3.0)
            lane = LANES_M[(i + rng.randrange(3)) % 3]
            if start + skid_len_m / 2 < road_m:
                out.append(dict(kind="skid", dist=round(start + skid_len_m / 2, 2), lat=lane, yaw_jit=rng.uniform(-4, 4),
                                size_m=skid_len_m, variant=i % len(SKIDS)))
        if "cone" in kinds:
            for side in (-1, 1):
                for off in (-1.5, 1.5):
                    out.append(dict(kind="cone", dist=round(m_d + off, 2), lat=side * KERB_M, yaw_jit=rng.uniform(-180, 180),
                                    size_m=0.0, variant=0))
    return out


def summary(plan):
    counts = {}
    for p in plan:
        counts[p["kind"]] = counts.get(p["kind"], 0) + 1
    return ", ".join("%s %d" % kv for kv in sorted(counts.items())) + " (total %d)" % len(plan)


def decal_rotation_deg(heading_deg, yaw_jit, kind, skid_yaw_offset=0.0):
    """(roll, pitch, yaw) for a DecalActor on the road. Pitch -90 turns local X (the projection axis) straight down; local Z
    then points along yaw, and image X (U) runs along local Z (DeferredDecal.usf:152-158), so yaw = heading puts the streaks
    along the road. skid_yaw_offset is only the manual fallback knob for skids."""
    return 0.0, -90.0, heading_deg + yaw_jit + (skid_yaw_offset if kind == "skid" else 0.0)


def decal_half_extents_cm(kind, size_m):
    """DecalSize = (depth half, local Y half, local Z half), cm. V (image Y) is local Y, U (image X) is local Z, so the 2:1
    skid PNG gets Z half = SKID_ASPECT x Y half (8 m along x 4 m across for size_m 8) and a pixel is square on both axes."""
    half = size_m * 50.0
    if kind == "skid":
        return DECAL_DEPTH_HALF_CM, half / SKID_ASPECT, half
    return DECAL_DEPTH_HALF_CM, half, half


# ---------------------------------------------------------------------------------------------------------
# Editor part
# ---------------------------------------------------------------------------------------------------------
def read_rows(level_name):
    """(rows, source). rows = [dict(stunt_m, mark_m, preset)] from DT_Stunts_S1/S2, else the S1 constants."""
    e_s, e_m = os.environ.get("CREW_STUNTS_M"), os.environ.get("CREW_MARKS_M")
    if e_s and e_m:
        s, m = [float(x) for x in e_s.split(",")], [float(x) for x in e_m.split(",")]
        return [dict(stunt_m=a, mark_m=b, preset="") for a, b in zip(s, m)], "env"
    if unreal is not None:
        path = "/Game/Data/Scenes/DT_Stunts_S2" if "Scene02" in level_name else "/Game/Data/Scenes/DT_Stunts_S1"
        try:
            dt = unreal.EditorAssetLibrary.load_asset(path)
            lib = unreal.DataTableFunctionLibrary
            col = lambda c: list(lib.get_data_table_column_as_string(dt, c))  # noqa: E731
            t_on, t_mark, surge, of, preset = col("TOn"), col("TMark"), col("Surge"), col("Of"), col("Preset")
            base = env_f("CREW_BASE_SPEED", 18.0)
            rows = [(float(a), float(b), float(c or 0), p) for a, b, c, o, p in zip(t_on, t_mark, surge, of, preset)
                    if not str(o).strip() or str(o).strip() == "None"]
            surges = [(a, c) for a, b, c, p in rows if c]
            if rows:
                return [dict(stunt_m=round(dist_at(a, base, surges), 1), mark_m=round(dist_at(b, base, surges), 1), preset=str(p))
                        for a, b, c, p in rows], "datatable " + path
        except Exception as exc:  # noqa: BLE001 - editor API surface
            log("datatable read failed (%s); using the S1 constants" % exc)
    return [dict(stunt_m=a, mark_m=b, preset=p) for a, b, p in zip(S1_STUNTS_M, S1_MARKS_M, S1_PRESETS)], "S1 constants"


def abort(msg):
    """Log and raise: the one way every guard below stops the script."""
    log("ABORT:", msg)
    raise RuntimeError(msg)


def open_level_path():
    """Package path of the level open in the editor, e.g. /Game/Maps/L_Scene01 (same read as force_save_level.py _info)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    return world.get_outer().get_path_name().split(".")[0]


def ensure_level_open(level):
    """Make `level` the open level without ever discarding unsaved edits (LoadMap does not prompt to save).
    Already open -> keep it, no reload. Another level open with dirty map packages -> abort, nothing changed.
    Otherwise load it; a load_map that returns None aborts."""
    level = level.split(".")[0]
    util = unreal.EditorLoadingAndSavingUtils
    if open_level_path() == level:
        log("level", level, "is already open: not reloading it")
        return
    dirty = [p.get_path_name() for p in util.get_dirty_map_packages()]
    if dirty:
        abort("another level is open and has unsaved changes (%s). LoadMap would discard them. Save it in the editor or open %s "
              "yourself, then run this again. Nothing was changed." % (", ".join(dirty), level))
    if util.load_map(level) is None:
        abort("load_map(%s) failed (wrong path?); the open level was left alone. Nothing was changed." % level)


def save_level():
    if not unreal.EditorLoadingAndSavingUtils.save_current_level():
        abort("save_current_level() failed; the edits are in the open level but NOT saved. Save it by hand (Ctrl+S).")


def save_asset(obj, what):
    if not unreal.EditorAssetLibrary.save_loaded_asset(obj):
        abort("save_loaded_asset failed for %s" % what)


def asset_exists(path):
    return unreal.EditorAssetLibrary.does_asset_exist(path)


def import_textures():
    """Import the five PNGs (skip existing). Returns {name: Texture2D}."""
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tex = {}
    for name in TAPES + SKIDS:
        path = "%s/%s" % (TEX_DEST, name)
        if not asset_exists(path):
            png = os.path.join(PNG_DIR, name, name + ".png")
            if not os.path.isfile(png):
                raise FileNotFoundError(png)
            task = unreal.AssetImportTask()
            task.set_editor_property("filename", png)
            task.set_editor_property("destination_path", TEX_DEST)
            task.set_editor_property("destination_name", name)
            task.set_editor_property("automated", True)
            task.set_editor_property("save", True)
            task.set_editor_property("replace_existing", True)
            tools.import_asset_tasks([task])
            log("imported", path)
        t = unreal.EditorAssetLibrary.load_asset(path)
        if t is None:
            abort("no texture at %s after the import" % path)
        for prop, val in (("srgb", True), ("address_x", unreal.TextureAddress.TA_CLAMP),
                          ("address_y", unreal.TextureAddress.TA_CLAMP), ("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)):
            try:
                t.set_editor_property(prop, val)
            except Exception as exc:  # noqa: BLE001
                log("WARN texture prop", prop, exc)
        save_asset(t, path)
        tex[name] = t
    return tex


def make_material():
    """One deferred-decal material; reuses it when it exists."""
    path = "%s/%s" % (MAT_DIR, MAT_NAME)
    if asset_exists(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(MAT_NAME, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    try:
        mat.set_editor_property("decal_blend_mode", unreal.DecalBlendMode.DBM_TRANSLUCENT)
    except Exception as exc:  # noqa: BLE001
        log("WARN decal_blend_mode", exc)
    lib = unreal.MaterialEditingLibrary
    ts = lib.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -500, 0)
    ts.set_editor_property("parameter_name", "Decal")
    rough = lib.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 200)
    rough.set_editor_property("r", 0.9)
    lib.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(ts, "A", unreal.MaterialProperty.MP_OPACITY)
    lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    errs = list(lib.recompile_material(mat))  # returns the compile error strings; empty = compiled
    if errs:
        # a failed deferred-decal material would silently render as the generic grey decal (DecalComponent.cpp:51-62), and
        # a retry would reuse the broken asset, so drop it before stopping
        try:
            unreal.EditorAssetLibrary.delete_asset(path)
        except Exception as exc:  # noqa: BLE001
            log("WARN could not delete the broken material", path, exc)
        abort("%s did not compile: %s" % (path, "; ".join(str(e) for e in errs)))
    save_asset(mat, path)
    log("made", path)
    return mat


def make_instances(mat, textures):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    lib = unreal.MaterialEditingLibrary
    out = {}
    for name, t in textures.items():
        mi_name = "MI_" + name[:-2]  # MI_T_Decal_TapeX_A
        path = "%s/%s" % (MAT_DIR, mi_name)
        mi = unreal.EditorAssetLibrary.load_asset(path) if asset_exists(path) else tools.create_asset(
            mi_name, MAT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        lib.set_material_instance_parent(mi, mat)
        lib.set_material_instance_texture_parameter_value(mi, "Decal", t)
        save_asset(mi, path)
        out[name] = mi
    return out


def find_cone_mesh():
    for path in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False):
        leaf = path.rsplit("/", 1)[-1].split(".")[0]
        if "cone" in leaf.lower() and leaf.startswith("SM_"):
            return unreal.EditorAssetLibrary.load_asset(path.split(".")[0])
    return None


def tagged_actors():
    out = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if any(str(t) == TAG for t in a.get_editor_property("tags")):
                out.append(a)
        except Exception:  # noqa: BLE001
            pass
    return out


def revert():
    ensure_level_open(os.environ.get("DECAL_LEVEL", "/Game/Maps/L_Scene01"))
    old = tagged_actors()
    for a in old:
        unreal.EditorLevelLibrary.destroy_actor(a)
    save_level()
    log("REVERT: deleted %d actors tagged %s; level saved" % (len(old), TAG))


def apply(kinds):
    level = os.environ.get("DECAL_LEVEL", "/Game/Maps/L_Scene01")
    ensure_level_open(level)
    # JCRoad first: in the wrong level, stop before any asset is imported or any old actor is deleted
    road = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}.get("JCRoad")
    if road is None:
        abort("no actor labelled JCRoad in %s; nothing was changed" % level)
    rows, source = read_rows(level)
    log("level", level, "marks from", source, [(r["stunt_m"], r["mark_m"], r["preset"]) for r in rows])
    plan = plan_decals(rows, kinds, int(env_f("DECAL_SEED", 1970)), env_f("DECAL_TAPE_M", 1.6), env_f("DECAL_SKID_LEN_M", 8.0),
                       env_f("DECAL_RAMP_LAND_M", 40.0))
    mis = {}
    if any(p["kind"] in ("tape", "skid") for p in plan):
        mis = make_instances(make_material(), import_textures())
    cone = find_cone_mesh() if any(p["kind"] == "cone" for p in plan) else None
    if any(p["kind"] == "cone" for p in plan) and cone is None:
        log("no static mesh named SM_*cone* under /Game: cones skipped")
    for a in tagged_actors():
        unreal.EditorLevelLibrary.destroy_actor(a)

    spline = road.get_component_by_class(unreal.SplineComponent)
    world = unreal.SplineCoordinateSpace.WORLD
    ground_z = env_f("DECAL_GROUND_Z", -150.0)
    skid_yaw = env_f("DECAL_SKID_YAW_OFFSET", 0.0)

    def road_pose(dist_m, lat_m):
        d = dist_m * 100.0
        loc = spline.get_location_at_distance_along_spline(d, world)
        right = spline.get_right_vector_at_distance_along_spline(d, world)
        fwd = spline.get_direction_at_distance_along_spline(d, world)
        return loc.x + right.x * lat_m * 100.0, loc.y + right.y * lat_m * 100.0, math.degrees(math.atan2(fwd.y, fwd.x))

    placed = {}
    for i, p in enumerate(plan):
        x, y, heading = road_pose(p["dist"], p["lat"])
        if p["kind"] == "cone":
            if cone is None:
                continue
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, ground_z),
                                                                      unreal.Rotator(0.0, 0.0, heading + p["yaw_jit"]))
        else:
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.DecalActor, unreal.Vector(x, y, ground_z + 10.0),
                unreal.Rotator(*decal_rotation_deg(heading, p["yaw_jit"], p["kind"], skid_yaw)))
        # tag first, so a mid-loop error can never leave an actor that revert would miss
        actor.set_actor_label("RoadDressing_%s_%02d" % (p["kind"], i))
        actor.set_editor_property("tags", [unreal.Name(TAG)])
        try:
            actor.set_folder_path(FOLDER)
        except Exception:  # noqa: BLE001
            pass
        if p["kind"] == "cone":
            comp = actor.static_mesh_component
            comp.set_static_mesh(cone)
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            comp.set_cast_shadow(False)
        else:
            names = TAPES if p["kind"] == "tape" else SKIDS
            comp = actor.get_component_by_class(unreal.DecalComponent)
            comp.set_decal_material(mis[names[p["variant"]]])
            comp.set_editor_property("decal_size", unreal.Vector(*decal_half_extents_cm(p["kind"], p["size_m"])))
            try:
                comp.set_editor_property("fade_screen_size", 0.004)
                comp.set_editor_property("sort_order", 2 if p["kind"] == "tape" else 1)
            except Exception:  # noqa: BLE001
                pass
        placed[p["kind"]] = placed.get(p["kind"], 0) + 1
    save_level()
    log("APPLIED %s | skid_yaw_offset %.0f ground_z %.0f | level saved" % (placed, skid_yaw, ground_z))


def main():
    mode = os.environ.get("DECAL_MODE", "apply" if unreal else "dry").lower()
    kinds = [k.strip() for k in os.environ.get("DECAL_KINDS", "").split(",") if k.strip()] or None
    bad = [k for k in (kinds or []) if k not in ("tape", "skid", "cone")]
    if bad:
        raise SystemExit("DECAL_KINDS has unknown kind(s) %s; known: tape, skid, cone" % bad)
    if mode == "revert":
        if unreal is None:
            raise SystemExit("revert needs the Unreal editor")
        revert()
    elif mode == "dry":
        if unreal is not None:
            rows, source = read_rows(os.environ.get("DECAL_LEVEL", "/Game/Maps/L_Scene01"))
        else:
            rows, source = [dict(stunt_m=a, mark_m=b, preset=p) for a, b, p in zip(S1_STUNTS_M, S1_MARKS_M, S1_PRESETS)], "S1 constants"
        plan = plan_decals(rows, kinds, int(env_f("DECAL_SEED", 1970)), env_f("DECAL_TAPE_M", 1.6), env_f("DECAL_SKID_LEN_M", 8.0),
                           env_f("DECAL_RAMP_LAND_M", 40.0))
        log("DRY RUN, nothing changed. marks from", source, "|", summary(plan))
    elif mode == "apply":
        if unreal is None:
            raise SystemExit("apply needs the Unreal editor (use DECAL_MODE=dry outside it)")
        apply(kinds)
    else:
        raise SystemExit("DECAL_MODE must be apply, revert or dry")


if __name__ == "__main__" or unreal is not None:
    main()
