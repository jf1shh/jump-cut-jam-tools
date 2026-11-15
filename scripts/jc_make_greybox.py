"""JumpCut greybox level L_Scene01 (run with: mx.py py scripts/jc_make_greybox.py).

Straight road along +X (Scene 1 wraps at X 684 m): AJCRoad with a 2-point drive spline, a floor strip, one
directional light, a sky light, a player start. Stunts come from DA_Scene_01, not from placement.
Re-runnable: creates the level once, otherwise opens it and re-places nothing that already exists (by label).
Prints JC_GREYBOX_OK / JC_GREYBOX_WARN lines.
"""
import unreal

LEVEL = "/Game/Maps/L_Scene01"
ROAD_LEN_CM = 72000.0  # 720 m, past the wrap at 684 m
_OUT = []


def say(kind, msg):
    line = "JC_GREYBOX_%s %s" % (kind, msg)
    _OUT.append(line)
    print(line)


def has(actors, label):
    return any(a.get_actor_label() == label for a in actors)


def run():
    ls = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
        if not ls.load_level(LEVEL):
            say("WARN", "load_level failed")
            return
    else:
        unreal.EditorAssetLibrary.make_directory("/Game/Maps")
        if not ls.new_level(LEVEL):
            say("WARN", "new_level failed")
            return
    actors = list(eas.get_all_level_actors())

    if not has(actors, "JCRoad"):
        road_cls = unreal.load_class(None, "/Script/JumpCut.JCRoad")
        if road_cls is None:
            say("WARN", "no C++ class JCRoad")
        else:
            road = eas.spawn_actor_from_class(road_cls, unreal.Vector(0, 0, 0))
            road.set_actor_label("JCRoad")
            road.tags = [unreal.Name("DriveSpline")]
            spline = road.get_editor_property("drive_spline")
            if spline is not None:
                spline.clear_spline_points(True)
                spline.add_spline_point(unreal.Vector(0, 0, 0), unreal.SplineCoordinateSpace.WORLD, True)
                spline.add_spline_point(unreal.Vector(ROAD_LEN_CM, 0, 0), unreal.SplineCoordinateSpace.WORLD, True)
                spline.update_spline()
            say("OK", "JCRoad placed")

    if not has(actors, "Floor_Strip"):
        cube = unreal.load_asset("/Engine/BasicShapes/Cube")
        floor = eas.spawn_actor_from_object(cube, unreal.Vector(ROAD_LEN_CM / 2.0, 0, -50))
        floor.set_actor_label("Floor_Strip")
        floor.set_actor_scale3d(unreal.Vector(ROAD_LEN_CM / 100.0, 14.0, 1.0))  # 720 m x 14 m x 1 m
        say("OK", "Floor_Strip placed")

    if not has(actors, "Ground_Plane"):
        cube = unreal.load_asset("/Engine/BasicShapes/Cube")
        gnd = eas.spawn_actor_from_object(cube, unreal.Vector(ROAD_LEN_CM / 2.0, 0, -200))
        gnd.set_actor_label("Ground_Plane")
        gnd.set_actor_scale3d(unreal.Vector(ROAD_LEN_CM / 100.0 + 400.0, 800.0, 1.0))  # fills below the horizon (N1)
        say("OK", "Ground_Plane placed")

    if not has(actors, "KeyLight"):
        sun = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 1000))
        sun.set_actor_label("KeyLight")
        sun.set_actor_rotation(unreal.Rotator(0, -45, 30), False)
        say("OK", "KeyLight placed")

    if not has(actors, "SkyLight"):
        sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 1200))
        sky.set_actor_label("SkyLight")
        say("OK", "SkyLight placed")
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "SkyLight":
            try:
                a.get_component_by_class(unreal.SkyLightComponent).set_editor_property("real_time_capture", True)
            except Exception as e:
                say("WARN", "sky light real_time_capture: %s" % e)

    if not has(actors, "SkyAtmosphere"):
        atm = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 1300))
        atm.set_actor_label("SkyAtmosphere")
        say("OK", "SkyAtmosphere placed")

    if not has(actors, "PlayerStart"):
        ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 100))
        ps.set_actor_label("PlayerStart")
        say("OK", "PlayerStart placed")

    ls.save_current_level()
    say("OK", "level saved (force_save_level.py will verify on disk)")


try:
    run()
except Exception as exc:  # noqa: BLE001
    say("WARN", "script aborted: %r" % (exc,))
"\n".join(_OUT)
