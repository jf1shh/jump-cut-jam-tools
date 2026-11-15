"""JumpCut data + input assets, created inside the editor (run with: mx.py py scripts/jc_make_data.py).

Re-runnable: existing assets are reused and their properties re-set. Prints JC_DATA_OK / JC_DATA_WARN lines and
one JC_DATA_SUMMARY line with the Asset Manager count per type. Names follow data-schema.md.
Tonight: Tuning, Scene 01 (all six S1 rows), car Number7, stunt preset FalseFront (+ BP_Stunt_FalseFront),
IA_* input actions and IMC_Default (keyboard + mouse + gamepad).
"""
import json
import unreal

_OUT = []


def say(kind, msg):
    line = "JC_DATA_%s %s" % (kind, msg)
    _OUT.append(line)
    print(line)


AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary

S1_CSV = (
    "Name,Of,Preset,TOn,TOff,Tier,Tel,Lanes,Block,Line,Curve,C0,C1,C2,Shot,Band,MustCut,TMark,Surge,Cam\n"
    "S1-1,,FalseFront,7.0,7.5,Easy,2.5,CR,,C>L,Fall,-1.0,1.0,90,3,1.0,False,9.0,0,A\n"
    "S1-2,,PropTruck,12.0,12.5,Easy,2.5,LC,,R,Slide,-2.5,0.75,0,3,1.0,False,14.0,0,B\n"
    "S1-3,,LightRig,17.0,17.8,TimedGap,2.5,RC,L,C>R,Swing,-0.5,1.2,0.6,3,1.0,False,19.0,0,C\n"
    "S1-4,,WaterTower,22.0,24.0,None,2.5,LCR,LCR,,Fall,0.0,2.0,90,1,0,True,26.0,0,B\n"
    "S1-5,,Drums,30.0,30.5,Easy,2.5,RC,,C>L,Roll,-1.5,0.5,0,3,1.0,False,32.0,0,A\n"
    "S1-6,,Facade,35.0,36.7,TwoHop,2.5,LC,,L>C>R,Sweep,0.7,0.75,0,3,1.0,False,37.0,6,BC\n"
    "S1-6b,S1-6,Scaffold,,,,,CR,,,Sweep,-1.4,0.75,1.5,,,,,,\n"
)


def asset(path, cls, factory):
    """Load the asset at path or create it. Returns the asset or None."""
    if EAL.does_asset_exist(path):
        return EAL.load_asset(path)
    folder, name = path.rsplit("/", 1)
    a = AT.create_asset(name, folder, cls, factory)
    if a is None:
        say("WARN", "could not create " + path)
    return a


def cpp_class(name):
    return unreal.load_class(None, "/Script/JumpCut." + name)


def data_asset(path, cls_name):
    cls = cpp_class(cls_name)
    if cls is None:
        say("WARN", "no C++ class " + cls_name + " (is the module compiled and loaded?)")
        return None
    f = unreal.DataAssetFactory()
    f.set_editor_property("data_asset_class", cls)
    return asset(path, cls, f)


def setp(obj, prop, value):
    try:
        obj.set_editor_property(prop, value)
    except Exception as e:  # noqa: BLE001 (report and carry on, one bad field must not stop the script)
        say("WARN", "set %s.%s failed: %s" % (obj.get_name(), prop, e))


def save(path):
    EAL.save_asset(path, only_if_is_dirty=False)


def make_input():
    out = {}
    fac_cls = getattr(unreal, "InputAction_Factory", None) or getattr(unreal, "InputActionFactory", None)
    if fac_cls is None:
        say("WARN", "no InputAction factory class in this build")
        return out
    for name, vt in (("IA_LaneLeft", None), ("IA_LaneRight", None), ("IA_Hold", None),
                     ("IA_Cancel", None), ("IA_Rev", None), ("IA_Pause", None)):
        p = "/Game/Input/" + name
        a = asset(p, unreal.InputAction, fac_cls())
        if a is not None:
            setp(a, "value_type", unreal.InputActionValueType.BOOLEAN)
            save(p)
        out[name] = a
    return out


def add_key(imc, action, key_name):
    if action is None:
        return
    try:
        key = unreal.Key()
        key.set_editor_property("key_name", key_name)
        imc.map_key(action, key)
    except Exception as e:  # noqa: BLE001
        say("WARN", "map_key %s -> %s failed: %s" % (action.get_name(), key_name, e))


def make_imc(acts):
    fac_cls = getattr(unreal, "InputMappingContext_Factory", None) or getattr(unreal, "InputMappingContextFactory", None)
    if fac_cls is None:
        say("WARN", "no InputMappingContext factory class in this build")
        return None
    p = "/Game/Input/IMC_Default"
    imc = asset(p, unreal.InputMappingContext, fac_cls())
    if imc is None:
        return None
    try:
        imc.unmap_all()  # re-runnable: rebuild the mappings from scratch
    except Exception as e:  # noqa: BLE001
        say("WARN", "unmap_all failed: " + str(e))
    L, R, H, C, V, P = (acts[k] for k in ("IA_LaneLeft", "IA_LaneRight", "IA_Hold", "IA_Cancel", "IA_Rev", "IA_Pause"))
    # Keyboard and mouse
    for k in ("A", "Left"):
        add_key(imc, L, k)
    for k in ("D", "Right"):
        add_key(imc, R, k)
    for k in ("LeftMouseButton", "SpaceBar"):
        add_key(imc, H, k)
    for k in ("RightMouseButton", "X"):
        add_key(imc, C, k)
    add_key(imc, V, "W")
    add_key(imc, V, "Up")
    for k in ("Escape", "P"):
        add_key(imc, P, k)
    # Gamepad: the stick is read as digital left/right (a tap), d-pad too
    for k in ("Gamepad_DPad_Left", "Gamepad_LeftStick_Left", "Gamepad_LeftShoulder"):
        add_key(imc, L, k)
    for k in ("Gamepad_DPad_Right", "Gamepad_LeftStick_Right", "Gamepad_RightShoulder"):
        add_key(imc, R, k)
    for k in ("Gamepad_FaceButton_Bottom", "Gamepad_RightTrigger"):
        add_key(imc, H, k)
    for k in ("Gamepad_FaceButton_Right", "Gamepad_LeftTrigger"):
        add_key(imc, C, k)
    add_key(imc, V, "Gamepad_FaceButton_Left")
    add_key(imc, P, "Gamepad_Special_Right")
    save(p)
    return imc


def make_stunt_bp():
    """BP_Stunt_FalseFront: Blueprint child of AJCStunt (abstract in C++, so a Blueprint child is the only way)."""
    p = "/Game/Blueprints/Stunts/BP_Stunt_FalseFront"
    if EAL.does_asset_exist(p):
        return EAL.load_asset(p)
    parent = cpp_class("JCStunt")
    if parent is None:
        say("WARN", "no C++ class JCStunt")
        return None
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", parent)
    bp = AT.create_asset("BP_Stunt_FalseFront", "/Game/Blueprints/Stunts", unreal.Blueprint, f)
    if bp is None:
        say("WARN", "could not create BP_Stunt_FalseFront")
    else:
        save(p)
    return bp


def run():
    for d in ("Data/Cars", "Data/Scenes", "Data/Stunts", "Data/Modifiers", "Data/Tuning", "Input",
              "Blueprints/Stunts", "Maps"):
        EAL.make_directory("/Game/" + d)

    acts = make_input()
    imc = make_imc(acts)

    tuning = data_asset("/Game/Data/Tuning/DA_Tuning_Default", "JCTuning")
    if tuning is not None:
        setp(tuning, "default_mapping_context", imc)
        for prop, key in (("lane_left_action", "IA_LaneLeft"), ("lane_right_action", "IA_LaneRight"),
                          ("hold_action", "IA_Hold"), ("cancel_action", "IA_Cancel"),
                          ("rev_action", "IA_Rev"), ("pause_action", "IA_Pause")):
            setp(tuning, prop, acts.get(key))
        save("/Game/Data/Tuning/DA_Tuning_Default")

    row_struct = getattr(unreal, "JCStuntRow", None)
    dt_path = "/Game/Data/Scenes/DT_Stunts_S1"
    dt = None
    if row_struct is None:
        say("WARN", "unreal.JCStuntRow missing (struct not exposed to Python)")
    else:
        if EAL.does_asset_exist(dt_path):
            dt = EAL.load_asset(dt_path)
        else:
            f = unreal.DataTableFactory()
            f.set_editor_property("struct", row_struct.static_struct())
            dt = AT.create_asset("DT_Stunts_S1", "/Game/Data/Scenes", unreal.DataTable, f)
        if dt is not None:
            ok = unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(dt, S1_CSV)
            say("OK" if ok else "WARN", "DT_Stunts_S1 fill_from_csv=%s rows=%d" % (
                ok, len(unreal.DataTableFunctionLibrary.get_data_table_row_names(dt))))
            save(dt_path)

    scene = data_asset("/Game/Data/Scenes/DA_Scene_01", "JCSceneData")
    if scene is not None:
        setp(scene, "number", 1)
        setp(scene, "title", "Rehearsal")
        setp(scene, "display_name", "Rehearsal")
        setp(scene, "base_speed", 18.0)
        setp(scene, "stunts", dt)
        lvl = unreal.EditorAssetLibrary.load_asset("/Game/Maps/L_Scene01") if unreal.EditorAssetLibrary.does_asset_exist("/Game/Maps/L_Scene01") else None
        if lvl is not None:
            setp(scene, "level", lvl)
        else:
            say("WARN", "L_Scene01 not built yet: rerun this script after jc_make_greybox.py to set DA_Scene_01.level")
        setp(scene, "clapper_waits_for_press", True)  # S1 waits for the ACTION press (data-schema)
        setp(scene, "first_prompt_stunt", "S1-1")
        setp(scene, "free_take_stunt", "S1-1")
        save("/Game/Data/Scenes/DA_Scene_01")

    car = data_asset("/Game/Data/Cars/DA_Car_Number7", "JCCarData")
    if car is not None:
        setp(car, "display_name", "Number 7")
        save("/Game/Data/Cars/DA_Car_Number7")

    bp = make_stunt_bp()
    preset = data_asset("/Game/Data/Stunts/DA_Stunt_FalseFront", "JCStuntPreset")
    if preset is not None:
        setp(preset, "display_name", "Leaning False Front")
        if bp is not None:
            setp(preset, "stunt_class", bp.generated_class())
        save("/Game/Data/Stunts/DA_Stunt_FalseFront")

    # Placeholder presets for the other S1 rows (same cube BP) so no row logs "preset not found"; real looks come later.
    for name in ("PropTruck", "LightRig", "WaterTower", "Drums", "Facade"):
        ph = data_asset("/Game/Data/Stunts/DA_Stunt_" + name, "JCStuntPreset")
        if ph is not None:
            setp(ph, "display_name", name + " (placeholder)")
            if bp is not None:
                setp(ph, "stunt_class", bp.generated_class())
            save("/Game/Data/Stunts/DA_Stunt_" + name)

    # Asset Manager count per type (the scan config lives in DefaultGame.ini)
    counts = {}
    try:
        am = unreal.AssetManager.get() if hasattr(unreal, "AssetManager") else None
        for t in ("Car", "Scene", "StuntPreset", "Modifier", "Tuning"):
            if am is None:
                break
            ids = am.get_primary_asset_id_list(unreal.PrimaryAssetType(t))
            counts[t] = len(ids)
    except Exception as e:  # noqa: BLE001
        say("WARN", "asset manager count failed: " + str(e))
    say("SUMMARY", json.dumps(counts))


try:
    run()
except Exception as exc:  # noqa: BLE001
    say("WARN", "script aborted: %r" % (exc,))
"\n".join(_OUT)
