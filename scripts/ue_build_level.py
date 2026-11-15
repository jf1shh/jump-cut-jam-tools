"""Build L_MockJam7: a greybox room (floor + 4 walls), a PlayerStart, and the
imported SM_Beacon/SM_Orb placed inside it, tagged per
stages/00_prep/references/pre-jam-mechanic-toolkit.md's QAObjective/PlayerStart convention.

INTENDED RUNTIME: headless, via UnrealEditor-Cmd -ExecCmds="py <this file>"
against a real .uproject (same pattern as scripts/ue_import_asset.py --
see that file's docstring for the exact invocation and the `; quit` gotcha:
UnrealEditor-Cmd's `py` command consumes the rest of the ExecCmds line as its
own argument string, so appending `; quit` breaks argparse instead of running
a second console command -- do not add `; quit` here either).

Optional `--plan /abs/path/plan.json` (from `scripts/layout_spec.py build`, see stages/02_build/references/layout-spec/README.md)
builds the planned rooms, doors and objective instead of the fixed room. Without it nothing changes.

Level-authoring gotchas this script accounts for (stages/00_prep/references/mock-jam-6-tooling-plan.md
gotchas log):
  - LevelEditorSubsystem.new_level(path) silently no-ops if a level asset
    already exists at that path. This script calls new_level only when the
    target path has no existing asset, and otherwise load_level()s it, then
    asserts get_editor_world().get_path_name() matches before placing anything.
  - get_editor_world() lives on UnrealEditorSubsystem, not EditorActorSubsystem.
  - Every file path this script touches must be absolute (UnrealEditor-Cmd's
    cwd is the engine's own Binaries/Linux/, not the shell's cwd).
"""

import argparse
import json
import sys

try:
    import unreal
except ImportError:
    unreal = None

LEVEL_PATH = "/Game/MockJam7/L_MockJam7"
OBJECTIVE_TAG = "QAObjective"

ROOM_HALF_SIZE = 500.0  # cm
WALL_HEIGHT = 300.0
FLOOR_Z = 0.0


def _get_subsystems():
    editor_subsys = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    actor_subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level_subsys = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    return editor_subsys, actor_subsys, level_subsys


def _ensure_level(level_subsys, editor_subsys, level_path):
    exists = unreal.EditorAssetLibrary.does_asset_exist(level_path)
    if exists:
        level_subsys.load_level(level_path)
    else:
        level_subsys.new_level(level_path)
    current = editor_subsys.get_editor_world().get_path_name()
    if level_path not in current:
        raise RuntimeError(
            f"Level mismatch after load/new: expected '{level_path}', editor world is '{current}'"
        )
    print(f"LEVEL_OK path={level_path} editor_world={current}")


def _spawn_cube(actor_subsys, location, scale, label):
    cube_class = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    actor = actor_subsys.spawn_actor_from_object(cube_class, location)
    actor.set_actor_scale3d(scale)
    actor.set_actor_label(label)
    return actor


def _place_default_lighting(actor_subsys):
    # Levels built by this script had no light source at all -- fine for the headless
    # agent playtest (Task C4, which runs -nullrhi and never renders a frame), but a
    # human playtesting the packaged build on real hardware saw a fully black screen
    # (mock jam 7, 2026-10-30). A directional light + sky light is the minimum any
    # future generated level needs to actually be visible.
    directional = actor_subsys.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0.0, 0.0, WALL_HEIGHT)
    )
    directional.set_actor_label("DirectionalLight")
    # Keyword args on purpose: unreal.Rotator's positional order is (roll, pitch, yaw), so
    # Rotator(-45, 30, 0) put the sun at pitch +30 (below the horizon) and the packaged game
    # rendered pure black even with every light present (mock jam 7, 2026-10-30).
    directional.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-45.0, yaw=30.0), False)
    directional_component = directional.get_component_by_class(unreal.DirectionalLightComponent)
    directional_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    directional_component.set_editor_property("atmosphere_sun_light", True)

    # A real-time-capture sky light needs a SkyAtmosphere to capture; without one the packaged
    # game shows a red "requires at least a SkyAtmosphere" error and a black sky.
    atmosphere = actor_subsys.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0.0, 0.0, 0.0))
    atmosphere.set_actor_label("SkyAtmosphere")

    sky = actor_subsys.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, WALL_HEIGHT))
    sky.set_actor_label("SkyLight")
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    # Don't bake the capture here: this script runs headless (-nullrhi, no real GPU/RHI),
    # so recapture_sky() produces invalid/empty capture data that the packaged game then
    # got stuck on at runtime (mock jam 7, 2026-10-30 -- black screen, pegged CPU, log frozen
    # right after level load). Real-time capture makes the sky light redo the capture itself
    # every frame using the actual runtime renderer, so no baked data from the editor is needed.
    sky_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    sky_component.set_editor_property("real_time_capture", True)


def _rest_on_floor(actor):
    # Generated meshes import with a centred pivot, so spawning at z=0 buries the bottom half.
    # Lift by however far the bounds' bottom sits below the floor, whatever the pivot is.
    origin, extent = actor.get_actor_bounds(False)
    loc = actor.get_actor_location()
    loc.z += FLOOR_Z - (origin.z - extent.z)
    actor.set_actor_location(loc, False, False)


def _spawn_mesh_actor(actor_subsys, mesh_path, location, label, tag=None, collision_profile=None, scale=1.0):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        raise RuntimeError(f"Could not load mesh asset at {mesh_path}")
    actor = actor_subsys.spawn_actor_from_object(mesh, location)
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    _rest_on_floor(actor)
    if tag:
        actor.tags = [tag]
    if collision_profile:
        mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
        mesh_component.set_collision_profile_name(collision_profile)
    return actor


PLAN_FORMAT = "megajam-layout-plan/1"  # written by scripts/layout_spec.py build


def load_plan(path):
    """Read a layout plan JSON (scripts/layout_spec.py build) and check its shape; raise ValueError if wrong."""
    with open(path, encoding="utf-8") as fh:
        plan = json.load(fh)
    if not isinstance(plan, dict) or plan.get("format") != PLAN_FORMAT:
        raise ValueError(f"{path}: not a {PLAN_FORMAT} file")
    if not str(plan.get("level_path", "")).startswith("/Game/Mock"):
        raise ValueError(f"{path}: level_path must start with /Game/Mock (practice levels only, Rule 7(h))")
    if not plan.get("cubes"):
        raise ValueError(f"{path}: plan has no cubes")
    for key in ("player_start", "objective"):
        if not (isinstance(plan.get(key), list) and len(plan[key]) == 3):
            raise ValueError(f"{path}: {key} must be [x, y, z]")
    if plan.get("orb") is not None and not (isinstance(plan["orb"], list) and len(plan["orb"]) == 3):
        raise ValueError(f"{path}: orb must be [x, y, z]")
    for c in plan["cubes"]:
        if not (isinstance(c.get("label"), str) and len(c.get("loc", [])) == 3 and len(c.get("scale", [])) == 3):
            raise ValueError(f"{path}: bad cube entry {c!r}")
    return plan


FALLBACK_BEACON = "/Engine/BasicShapes/Cube"
FALLBACK_ORB = "/Engine/BasicShapes/Sphere"


def _mesh_or_fallback(path, fallback):
    """Plan mode only: a mesh that is not in the project (or not given) becomes an engine basic shape."""
    if path and unreal.EditorAssetLibrary.does_asset_exist(path):
        return path
    print(f"MESH_FALLBACK wanted={path!r} using={fallback}")
    return fallback


def build_level(beacon_mesh_path, orb_mesh_path, plan=None):
    """Grey-box level. With no plan: the fixed room. With a plan: the layout_spec rooms, doors and objective.

    Plan mode does not need the mock-jam meshes: a missing one becomes /Engine/BasicShapes/Cube (beacon)
    or Sphere (orb). The no-plan path still fails loudly on a missing mesh, as before.
    """
    editor_subsys, actor_subsys, level_subsys = _get_subsystems()
    level_path = plan["level_path"] if plan else LEVEL_PATH
    _ensure_level(level_subsys, editor_subsys, level_path)
    if plan:
        beacon_mesh_path = _mesh_or_fallback(beacon_mesh_path, FALLBACK_BEACON)
        orb_mesh_path = _mesh_or_fallback(orb_mesh_path, FALLBACK_ORB)

    half = ROOM_HALF_SIZE
    wall_h = WALL_HEIGHT

    if plan:
        for c in plan["cubes"]:
            _spawn_cube(actor_subsys, unreal.Vector(*c["loc"]), unreal.Vector(*c["scale"]), c["label"])
        sx, sy, sz = plan["player_start"]
        ox, oy, oz = plan["objective"]
        start_loc, objective_loc = unreal.Vector(sx, sy, sz), unreal.Vector(ox, oy, oz)
        # layout_spec picks a spot inside a room and clear of walls; old plans without "orb" keep the fixed offset
        ax, ay, az = plan.get("orb") or [sx + 150.0, sy + 150.0, 0.0]
        orb_loc = unreal.Vector(ax, ay, az)
    else:
        # Floor: a flat cube, default size 100x100x100cm -> scale to cover the room, thin on Z.
        _spawn_cube(
            actor_subsys,
            unreal.Vector(0.0, 0.0, FLOOR_Z - 5.0),
            unreal.Vector((2 * half) / 100.0, (2 * half) / 100.0, 0.1),
            "Floor",
        )

        wall_specs = [
            ("Wall_North", unreal.Vector(0.0, half, wall_h / 2.0), unreal.Vector((2 * half) / 100.0, 0.1, wall_h / 100.0)),
            ("Wall_South", unreal.Vector(0.0, -half, wall_h / 2.0), unreal.Vector((2 * half) / 100.0, 0.1, wall_h / 100.0)),
            ("Wall_East", unreal.Vector(half, 0.0, wall_h / 2.0), unreal.Vector(0.1, (2 * half) / 100.0, wall_h / 100.0)),
            ("Wall_West", unreal.Vector(-half, 0.0, wall_h / 2.0), unreal.Vector(0.1, (2 * half) / 100.0, wall_h / 100.0)),
        ]
        for label, loc, scale in wall_specs:
            _spawn_cube(actor_subsys, loc, scale, label)
        start_loc = unreal.Vector(-half * 0.6, 0.0, 50.0)
        objective_loc = unreal.Vector(half * 0.6, 0.0, 0.0)
        orb_loc = unreal.Vector(-half * 0.3, 150.0, 0.0)

    player_start = actor_subsys.spawn_actor_from_class(unreal.PlayerStart, start_loc)
    player_start.set_actor_label("PlayerStart")

    _spawn_mesh_actor(actor_subsys, beacon_mesh_path, objective_loc, "Beacon", tag=OBJECTIVE_TAG)
    # PlayerOrb is a decorative placeholder for the player's in-game identity, not level
    # geometry or a win-condition actor (only BP_Beacon is tagged QAObjective) -- give it
    # overlap-only collision so it never physically blocks the pawn, matching BP_Beacon's
    # own deliberate "OverlapAllDynamic" collision profile (stages/00_prep/references/mock-jam-6-tooling-plan.md
    # gotchas log). Without this it defaults to blocking and silently stalls any straight-line
    # movement test that happens to cross its position (root cause of the Task C4 velocity freeze).
    # Generated meshes import at ~200cm across regardless of what they depict; at scale 1 the orb
    # filled the whole view from PlayerStart. 0.3 makes it ~60cm. It sits off to the side
    # (y=150) because on the PlayerStart->beacon line it hid the beacon completely at spawn.
    _spawn_mesh_actor(
        actor_subsys,
        orb_mesh_path,
        orb_loc,
        "PlayerOrb",
        collision_profile="OverlapAllDynamic",
        scale=0.3,
    )

    _place_default_lighting(actor_subsys)

    saved = unreal.EditorAssetLibrary.save_asset(level_path, only_if_is_dirty=False)
    print(f"LEVEL_SAVE_RESULT={saved}")
    print("BUILD_LEVEL_OK")


def _parse_cli_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--beacon-mesh", default="/Game/MockJam7/mj7_beacon/StaticMeshes/SM_Beacon")
    parser.add_argument("--orb-mesh", default="/Game/MockJam7/mj7_orb/StaticMeshes/SM_Orb")
    parser.add_argument("--plan", default=None, help="absolute path to a layout plan from scripts/layout_spec.py build")
    return parser.parse_args(argv)


if __name__ == "__main__" and unreal is not None:
    args = _parse_cli_args(sys.argv[1:])
    build_level(args.beacon_mesh, args.orb_mesh, load_plan(args.plan) if args.plan else None)
