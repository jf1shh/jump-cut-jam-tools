"""S1-2..S1-6 greybox looks: one BP_Stunt_<Name> per preset (cubes tagged JCPart<i>, a point light tagged JCKeyLight),
wired into DA_Stunt_<Name>. Re-runnable. Needs jc_make_data.py first. Returns JC_S1_OK / JC_S1_WARN lines."""
import unreal

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
# name: (display name, [(part scale x,y,z) in cube units of 1 m ...])   part 0 = the stunt row, part 1 = its extra-part row
SPEC = {
    "PropTruck": ("Prop Truck", [(6.0, 2.4, 2.8)]),
    "LightRig": ("Light Rig", [(1.0, 2.5, 5.0)]),
    "WaterTower": ("Water Tower", [(2.5, 2.5, 6.0)]),
    "Drums": ("Drum Stack", [(1.2, 1.2, 1.6)]),
    "Facade": ("Facade and Scaffold", [(0.4, 4.0, 5.0), (1.0, 3.0, 3.0)]),
}
out = []


def build(name, parts):
    path = "/Game/Blueprints/Stunts/BP_Stunt_" + name
    if EAL.does_asset_exist(path):
        bp = EAL.load_asset(path)
    else:
        f = unreal.BlueprintFactory()
        f.set_editor_property("parent_class", unreal.load_class(None, "/Script/JumpCut.JCStunt"))
        bp = AT.create_asset("BP_Stunt_" + name, "/Game/Blueprints/Stunts", unreal.Blueprint, f)
    if bp is None:
        out.append("JC_S1_WARN %s: no blueprint" % name)
        return None
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    have = [str(lib.get_display_name(sub.k2_find_subobject_data_from_handle(h))) for h in handles]
    root = handles[0]

    def add(cls, nm):
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=bp))
        if str(fail):
            out.append("JC_S1_WARN %s: add %s failed %s" % (name, nm, fail))
            return None
        sub.rename_subobject(h, nm)
        return lib.get_object(sub.k2_find_subobject_data_from_handle(h))

    for i, sc in enumerate(parts):
        if any(("Part%d" % i) in n for n in have):
            continue
        c = add(unreal.StaticMeshComponent, "Part%d" % i)
        if c:
            c.set_editor_property("static_mesh", unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
            c.set_editor_property("component_tags", ["JCPart%d" % i])
            c.set_editor_property("relative_scale3d", unreal.Vector(*sc))
    if not any("KeyLight" in n for n in have):
        l = add(unreal.PointLightComponent, "KeyLight")
        if l:
            l.set_editor_property("component_tags", ["JCKeyLight"])
            l.set_editor_property("intensity", 0.0)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_asset(path)
    return bp


for name, (disp, parts) in SPEC.items():
    bp = build(name, parts)
    da_path = "/Game/Data/Stunts/DA_Stunt_" + name
    da = EAL.load_asset(da_path)
    if bp is None or da is None:
        out.append("JC_S1_WARN %s: missing bp or preset" % name)
        continue
    da.set_editor_property("display_name", disp)
    da.set_editor_property("stunt_class", bp.generated_class())
    EAL.save_asset(da_path)
    out.append("JC_S1_OK " + name)
"\n".join(out)
