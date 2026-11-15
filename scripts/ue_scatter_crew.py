"""Crew-row kit placer for Jump Cut (UE 5.9 editor Python). Written by PROPS-1; NOT run by PROPS-1.

What it does (CREW_MODE=apply, the default), in the open editor:
  1. imports the six Rodin props (SM_Crew_Camera, _Fresnel, _DirChair, _AppleBoxes, _Sandbags, _Extras) from
     CREW_GLB_DIR into /Game/Meshes/Props/Crew/ (skips any that are already there), Nanite OFF (the imported glTF
     material is not Nanite-safe, see the lead's M_GltfDefault_Nanite fix; each prop is only ~15k tris);
  2. makes sure /Game/Maps/L_Scene01 is the open level (see "Level safety" below) and places a film-crew row on the LEFT shoulder (negative lateral), thickest at each
     stunt mark and thin in between: a camera on a tripod, two fresnel lights aimed at the stunt, director's chairs,
     apple boxes, sandbags and a cardboard-extras group per mark, plus sparse filler;
  3. tags every actor `CrewKit`, puts it in the outliner folder `Crew`, no collision, shadows off except the
     camera and the lights, a draw-distance cull per prop, then saves the level.

Kill switch: CREW_MODE=revert deletes exactly the actors tagged `CrewKit` (and saves). CREW_MODE=dry prints the
layout and changes nothing (also runs outside the editor: `python3 ue_scatter_crew.py` -> selftest table).
Partial kill (frame-rate line "1% low < 30 -> tripod + stand only"): CREW_KINDS=camera,fresnel then re-run apply
(apply always clears the old CrewKit actors first, so it is safe to repeat).

Level safety (apply and revert): LoadMap does NOT prompt to save (Engine/Source/Editor/UnrealEd/Public/FileHelpers.h:57-64), so
the script never reloads blindly. If CREW_LEVEL is already the open level it is NOT reloaded (unsaved edits stay, and the final
save writes them out with ours). If another level is open and any map package is dirty
(EditorLoadingAndSavingUtils.get_dirty_map_packages: world, built data and external actor packages) it aborts before changing
anything. A load_map that returns None, a missing JCRoad and a failed save abort too; JCRoad is checked before any old actor
is deleted or any mesh imported.

Why the LEFT shoulder: each stunt's "MARK n" sign (JCStunt.cpp) stands on the RIGHT at lateral 10.4 m; the crew
stays clear of it. CREW_SIDE=right|both exists, and keeps 4 m clear of every sign on the right.

Road facts used (build_road.py, JCRoad.h, pace-values.md): straight spline along +X, JCRoad actor label `JCRoad`,
half width 7 m, lanes at -4/0/+4 m, kerb to 6.6 m, cyclorama wall at +-28 m, ground top z = -150 cm.
Stunt distances D(TOn) and mark distances MarkD come live from DT_Stunts_S1/S2 when the table can be read
(TOn, TMark, Surge, Of columns; D(T) = BaseSpeed*T + the Surge step) and otherwise from the S1 constants below.

Props (GLB, metres, pivot at the base centre, front = glTF +Z). The Fresnel's lens is material slot 1 ("Lens"):
swap an emissive beam material onto that slot. ORIENTATION: the glTF -> UE axis mapping was not seen live. The
default assumes the model front lands on UE +Y (CREW_FRONT_YAW_DEG=90). If the first shot shows cameras and lights
facing wrong, CREW_MODE=revert, set CREW_FRONT_YAW_DEG (0, 90, 180 or -90), run apply again.

Env knobs (all optional): CREW_MODE apply|revert|dry; CREW_LEVEL (/Game/Maps/L_Scene01); CREW_SIDE left|right|both;
CREW_SEED (1970); CREW_SCALE (1.5, all props); CREW_DENSITY (1.0, thins fillers and the optional items; 0..1);
CREW_KINDS (all); CREW_GROUND_Z cm (-150); CREW_FRONT_YAW_DEG (90); CREW_GLB_DIR; CREW_DEST; CREW_MARKS_M and
CREW_STUNTS_M (comma lists, override the table); CREW_ROAD_M (road length m, 720); CREW_LOG (log file).
"""
import json
import math
import os
import random
import sys
import time

try:
    import unreal
except ImportError:  # outside the editor: dry run / unit tests only
    unreal = None

TAG = "CrewKit"
FOLDER = "Crew"
DEST = os.environ.get("CREW_DEST", "/Game/Meshes/Props/Crew")
GLB_DIR = os.environ.get("CREW_GLB_DIR", "~/Projects/megajam/work/generated")
LOG_PATH = os.environ.get("CREW_LOG", "~/.local/state/megajam/props1-work/scatter_crew.log")

# kind -> mesh name, footprint radius (m, before CREW_SCALE), casts shadow, draw distance (m)
KINDS = {
    "camera":  dict(mesh="SM_Crew_Camera",     radius=0.9, shadow=True,  cull=140.0),
    "fresnel": dict(mesh="SM_Crew_Fresnel",    radius=0.8, shadow=True,  cull=140.0),
    "chair":   dict(mesh="SM_Crew_DirChair",   radius=0.6, shadow=False, cull=90.0),
    "boxes":   dict(mesh="SM_Crew_AppleBoxes", radius=0.5, shadow=False, cull=70.0),
    "sandbag": dict(mesh="SM_Crew_Sandbags",   radius=0.5, shadow=False, cull=70.0),
    "extras":  dict(mesh="SM_Crew_Extras",     radius=1.1, shadow=False, cull=110.0),
}
# Fallback S1 numbers (pace-values.md, 2026-11-12): D(TOn) and MarkD in metres.
S1_STUNTS_M = [126.0, 216.0, 306.0, 396.0, 540.0, 648.0]
S1_MARKS_M = [162.0, 252.0, 342.0, 468.0, 576.0, 684.0]
ROAD_HALF_M = 7.0
SIGN_LAT_M = 10.4  # JCStunt MARK sign, right side


def env_f(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


def log(*parts):
    line = time.strftime("%H:%M:%S ") + " ".join(str(p) for p in parts)
    print("[crew] " + line)
    try:
        with open(LOG_PATH, "a") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


# ----------------------------------------------------------------------------------------------------------
# Pure layout (no unreal): easy to test and to dry-run
# ----------------------------------------------------------------------------------------------------------
def dist_at(t, base_speed, surges, surge_time=3.0):
    """Road distance (m) at scene time t: base speed plus each row's Surge step over [TOn-surge_time, TOn)."""
    d = base_speed * t
    for t_on, surge in surges:
        d += surge * max(0.0, min(t, t_on) - (t_on - surge_time))
    return d


def plan_layout(stunts_m, marks_m, road_m=720.0, side="left", seed=1970, density=1.0, kinds=None):
    """Return a list of placements: dict(kind, dist, lat, face=(dist, lat) | None, yaw_jit, scale_jit, cluster).

    dist = road distance (m), lat = lateral offset (m, + = right of travel). `face` is the road point the front
    of the prop should point at (None = random yaw). Thickest at each mark, sparse between, nothing in lanes.
    """
    rng = random.Random(seed)
    kinds = set(kinds) if kinds else set(KINDS)
    placed = []

    def sides_for(i):
        if side == "right":
            return 1
        if side == "both":
            return 1 if i % 2 else -1
        return -1

    def keep_clear_of_signs(dist, lat):
        """Right-side props stay 4.5 m (along the road) away from every MARK sign."""
        if lat <= 0 or not (SIGN_LAT_M - 2.0 < lat < SIGN_LAT_M + 2.0):
            return dist
        for m in marks_m:
            if abs(dist - m) < 4.5:
                return m + 4.5 if dist >= m else m - 4.5
        return dist

    def add(kind, dist, lat, face=None, yaw_jit=0.0, cluster=-1, optional=False):
        if kind not in kinds:
            return
        if optional and rng.random() > density:
            return
        dist = keep_clear_of_signs(dist, lat)
        if not (2.0 <= dist <= road_m + 12.0):
            return
        r = KINDS[kind]["radius"]
        for _ in range(5):  # nudge outwards (away from the lanes) until it no longer overlaps
            clash = any(math.hypot(p["dist"] - dist, p["lat"] - lat) < (KINDS[p["kind"]]["radius"] + r) * 1.1 for p in placed)
            if not clash:
                break
            lat += 0.8 if lat > 0 else -0.8
        else:
            return
        placed.append(dict(kind=kind, dist=round(dist, 2), lat=round(lat, 2), face=face,
                           yaw_jit=yaw_jit, scale_jit=round(1.0 + rng.uniform(-0.08, 0.08), 3), cluster=cluster))

    for i, (s_d, m_d) in enumerate(zip(stunts_m, marks_m)):
        s = sides_for(i)
        road_mark = (m_d, 0.0)
        road_stunt = (s_d, 0.0)
        # crew camera just before the mark, filming the landing
        add("camera", m_d - 3.0, s * 10.8, face=road_mark, yaw_jit=4.0, cluster=i)
        # two fresnels, both aimed at the stunt: one at the stunt, one in the mark cluster
        add("fresnel", s_d - 5.0, s * 10.5, face=road_stunt, yaw_jit=3.0, cluster=i)
        add("fresnel", m_d - 9.0, s * 11.2, face=road_stunt, yaw_jit=3.0, cluster=i)
        # chairs beside the camera, facing the road
        add("chair", m_d - 5.6, s * 12.6, face=(m_d - 4.0, 0.0), yaw_jit=18.0, cluster=i)
        add("chair", m_d - 4.2, s * 12.9, face=(m_d - 2.0, 0.0), yaw_jit=18.0, cluster=i)
        # apple boxes by the camera and by the chairs
        add("boxes", m_d - 1.2, s * 10.3, yaw_jit=180.0, cluster=i)
        add("boxes", m_d + 2.8, s * 11.5, yaw_jit=180.0, cluster=i, optional=True)
        # sandbags weighting the tripod and the stands
        add("sandbag", m_d - 3.0 + 1.0, s * 10.0, yaw_jit=180.0, cluster=i)
        add("sandbag", s_d - 5.0 + 0.9, s * 10.1, yaw_jit=180.0, cluster=i, optional=True)
        add("sandbag", m_d - 9.0 + 0.9, s * 10.9, yaw_jit=180.0, cluster=i, optional=True)
        # cardboard extras group behind the camera, facing the road
        add("extras", m_d + 8.0, s * 14.0, face=(m_d + 8.0, 0.0), yaw_jit=10.0, cluster=i)

    # sparse filler between the clusters: chance falls with distance from the nearest mark
    step = 16.0
    d = 14.0
    while d < road_m:
        dm = min(abs(d - m) for m in marks_m) if marks_m else 999.0
        p = (0.06 + 0.5 * math.exp(-((dm / 45.0) ** 2))) * density
        if dm > 15.0 and rng.random() < p:
            kind = rng.choice(["chair", "boxes", "boxes", "sandbag", "sandbag", "sandbag", "chair"])
            s = sides_for(rng.randrange(1000)) if side == "both" else sides_for(0)
            add(kind, d + rng.uniform(-3, 3), s * rng.uniform(10.5, 15.0),
                face=(d, 0.0) if kind == "chair" else None, yaw_jit=25.0 if kind == "chair" else 180.0, cluster=-1)
        d += step
    return placed


def selftest_table(plan):
    rows = {}
    for p in plan:
        rows.setdefault(p["cluster"], {}).setdefault(p["kind"], 0)
        rows[p["cluster"]][p["kind"]] += 1
    lines = []
    for c in sorted(rows):
        lines.append(("cluster %d" % c if c >= 0 else "filler   ") + "  " + ", ".join("%s %d" % kv for kv in sorted(rows[c].items())))
    lines.append("total %d" % len(plan))
    return "\n".join(lines)


# ----------------------------------------------------------------------------------------------------------
# Editor part
# ----------------------------------------------------------------------------------------------------------
def read_marks(level_name):
    """(stunts_m, marks_m, source) from DT_Stunts_S1/S2, else the S1 constants. Env lists override everything."""
    e_s, e_m = os.environ.get("CREW_STUNTS_M"), os.environ.get("CREW_MARKS_M")
    if e_s and e_m:
        return [float(x) for x in e_s.split(",")], [float(x) for x in e_m.split(",")], "env"
    if unreal is not None:
        dt_path = "/Game/Data/Scenes/DT_Stunts_S2" if "Scene02" in level_name else "/Game/Data/Scenes/DT_Stunts_S1"
        try:
            dt = unreal.EditorAssetLibrary.load_asset(dt_path)
            lib = unreal.DataTableFunctionLibrary
            col = lambda c: list(lib.get_data_table_column_as_string(dt, c))  # noqa: E731
            t_on, t_mark, surge, of = col("TOn"), col("TMark"), col("Surge"), col("Of")
            base = env_f("CREW_BASE_SPEED", 18.0)
            rows = [(float(a), float(b), float(c or 0)) for a, b, c, o in zip(t_on, t_mark, surge, of)
                    if not str(o).strip() or str(o).strip() == "None"]
            surges = [(a, c) for a, b, c in rows if c]
            if rows:
                stunts = [round(dist_at(a, base, surges), 1) for a, b, c in rows]
                marks = [round(dist_at(b, base, surges), 1) for a, b, c in rows]
                return stunts, marks, "datatable " + dt_path
        except Exception as exc:  # noqa: BLE001 - editor API surface
            log("datatable read failed (%s); using the S1 constants" % exc)
    return list(S1_STUNTS_M), list(S1_MARKS_M), "S1 constants (pace-values 2026-11-12)"


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


def find_mesh(name):
    """Asset path of SM name under DEST (Interchange nests it as DEST/<glb>/StaticMeshes/<name>), or None."""
    for path in unreal.EditorAssetLibrary.list_assets(DEST, recursive=True, include_folder=False):
        if path.rsplit("/", 1)[-1].split(".")[0] == name:
            return path.split(".")[0]
    return None


def import_mesh(name):
    glb = os.path.join(GLB_DIR, name, name + ".glb")
    if not os.path.isfile(glb):
        raise FileNotFoundError(glb)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", glb)
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    path = find_mesh(name)
    if not path:
        raise RuntimeError("import of %s produced no StaticMesh under %s (imported: %s)" % (
            name, DEST, list(task.get_editor_property("imported_object_paths") or [])))
    return path


def nanite_off(mesh):
    """Turn Nanite off on a mesh (the imported glTF material is not Nanite-safe). Returns True when it reads off."""
    try:
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        ns = sub.get_nanite_settings(mesh)
        if ns.enabled:
            ns.enabled = False
            sub.set_nanite_settings(mesh, ns, True)
    except Exception:  # noqa: BLE001
        try:
            ns = mesh.get_editor_property("nanite_settings")
            ns.enabled = False
            mesh.set_editor_property("nanite_settings", ns)
        except Exception as exc:  # noqa: BLE001
            log("WARN nanite off failed on %s: %s" % (mesh.get_name(), exc))
    try:
        return not mesh.get_editor_property("nanite_settings").enabled
    except Exception:  # noqa: BLE001
        return False


def ensure_meshes(kinds):
    meshes = {}
    for kind in kinds:
        name = KINDS[kind]["mesh"]
        path = find_mesh(name)
        if path:
            log("mesh exists", path)
        else:
            path = import_mesh(name)
            log("imported", path)
        mesh = unreal.EditorAssetLibrary.load_asset(path)
        off = nanite_off(mesh)
        save_asset(mesh, path)
        log("%s nanite_off=%s" % (name, off))
        meshes[kind] = mesh
    return meshes


def actors_with_tag(tag):
    out = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if any(str(t) == tag for t in a.get_editor_property("tags")):
                out.append(a)
        except Exception:  # noqa: BLE001
            pass
    return out


def revert():
    ensure_level_open(os.environ.get("CREW_LEVEL", "/Game/Maps/L_Scene01"))
    old = actors_with_tag(TAG)
    for a in old:
        unreal.EditorLevelLibrary.destroy_actor(a)
    save_level()
    log("REVERT: deleted %d actors tagged %s; level saved" % (len(old), TAG))


def apply(plan_args):
    level = os.environ.get("CREW_LEVEL", "/Game/Maps/L_Scene01")
    ensure_level_open(level)
    # JCRoad first: in the wrong level, stop before any asset is imported or any old actor is deleted
    road = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}.get("JCRoad")
    if road is None:
        abort("no actor labelled JCRoad in %s; nothing was changed" % level)
    stunts, marks, source = read_marks(level)
    log("level", level, "marks from", source, "stunts", stunts, "marks", marks)
    kinds = plan_args["kinds"] or list(KINDS)
    plan = plan_layout(stunts, marks, road_m=env_f("CREW_ROAD_M", 720.0), side=plan_args["side"],
                       seed=int(env_f("CREW_SEED", 1970)), density=plan_args["density"], kinds=kinds)
    meshes = ensure_meshes(sorted({p["kind"] for p in plan}))
    for a in actors_with_tag(TAG):
        unreal.EditorLevelLibrary.destroy_actor(a)

    spline = road.get_component_by_class(unreal.SplineComponent)
    world = unreal.SplineCoordinateSpace.WORLD

    def road_xy(dist_m, lat_m):
        loc = spline.get_location_at_distance_along_spline(dist_m * 100.0, world)
        right = spline.get_right_vector_at_distance_along_spline(dist_m * 100.0, world)
        return loc.x + right.x * lat_m * 100.0, loc.y + right.y * lat_m * 100.0

    ground_z = env_f("CREW_GROUND_Z", -150.0)
    front_yaw = env_f("CREW_FRONT_YAW_DEG", 90.0)
    scale = env_f("CREW_SCALE", 1.5)
    rng = random.Random(int(env_f("CREW_SEED", 1970)) + 1)
    counts = {}
    layout = []
    for i, p in enumerate(plan):
        spec = KINDS[p["kind"]]
        x, y = road_xy(p["dist"], p["lat"])
        if p["face"] is not None:
            tx, ty = road_xy(*p["face"])
            want = math.degrees(math.atan2(ty - y, tx - x))
        else:
            want = rng.uniform(-180.0, 180.0)
        want += rng.uniform(-p["yaw_jit"], p["yaw_jit"]) if p["face"] is not None else 0.0
        yaw = want - front_yaw
        s = scale * p["scale_jit"]
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(x, y, ground_z), unreal.Rotator(0.0, 0.0, yaw))
        actor.set_actor_label("Crew_%s_%02d" % (p["kind"], i))
        actor.set_actor_scale3d(unreal.Vector(s, s, s))
        actor.set_editor_property("tags", [unreal.Name(TAG)])
        try:
            actor.set_folder_path(FOLDER)
        except Exception:  # noqa: BLE001
            pass
        comp = actor.static_mesh_component
        comp.set_static_mesh(meshes[p["kind"]])
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_collision_profile_name("NoCollision")
        comp.set_cast_shadow(bool(spec["shadow"]))
        try:
            comp.set_editor_property("ld_max_draw_distance", float(spec["cull"]) * 100.0)
        except Exception:  # noqa: BLE001
            pass
        counts[p["kind"]] = counts.get(p["kind"], 0) + 1
        layout.append(dict(label=actor.get_actor_label(), kind=p["kind"], dist_m=p["dist"], lat_m=p["lat"],
                           x=round(x, 1), y=round(y, 1), yaw=round(yaw, 1), scale=round(s, 3), cluster=p["cluster"]))
    save_level()
    out = os.path.splitext(LOG_PATH)[0] + "_layout.json"
    try:
        with open(out, "w") as fh:
            json.dump(layout, fh, indent=1)
    except OSError:
        pass
    log("APPLIED %d actors %s | scale %.2f front_yaw %.0f ground_z %.0f | level saved | layout %s" % (
        len(layout), counts, scale, front_yaw, ground_z, out))
    log("Fresnel lens = material slot 1 ('Lens') on SM_Crew_Fresnel: swap the emissive beam material onto it.")


def main():
    mode = os.environ.get("CREW_MODE", "apply" if unreal else "dry").lower()
    kinds = [k.strip() for k in os.environ.get("CREW_KINDS", "").split(",") if k.strip()] or None
    bad = [k for k in (kinds or []) if k not in KINDS]
    if bad:
        raise SystemExit("CREW_KINDS has unknown kind(s) %s; known: %s" % (bad, sorted(KINDS)))
    args = dict(side=os.environ.get("CREW_SIDE", "left").lower(), density=max(0.0, min(1.0, env_f("CREW_DENSITY", 1.0))),
                kinds=kinds)
    if args["side"] not in ("left", "right", "both"):
        raise SystemExit("CREW_SIDE must be left, right or both")
    if mode == "revert":
        if unreal is None:
            raise SystemExit("revert needs the Unreal editor")
        revert()
    elif mode == "dry":
        if unreal is not None:
            stunts, marks, source = read_marks(os.environ.get("CREW_LEVEL", "/Game/Maps/L_Scene01"))
        else:
            stunts, marks, source = list(S1_STUNTS_M), list(S1_MARKS_M), "S1 constants"
        plan = plan_layout(stunts, marks, road_m=env_f("CREW_ROAD_M", 720.0), side=args["side"],
                           seed=int(env_f("CREW_SEED", 1970)), density=args["density"], kinds=kinds)
        log("DRY RUN, nothing changed. marks from", source)
        log("\n" + selftest_table(plan))
    elif mode == "apply":
        if unreal is None:
            raise SystemExit("apply needs the Unreal editor (use CREW_MODE=dry outside it)")
        apply(args)
    else:
        raise SystemExit("CREW_MODE must be apply, revert or dry")


if __name__ == "__main__" or unreal is not None:
    main()
