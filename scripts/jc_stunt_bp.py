"""Give BP_Stunt_FalseFront one visible cube tagged JCPart0 (hazard part 0). Re-runnable. Prints JC_STUNT_OK / JC_STUNT_WARN."""
import unreal

BP = "/Game/Blueprints/Stunts/BP_Stunt_FalseFront"
out = []
bp = unreal.EditorAssetLibrary.load_asset(BP)
if bp is None:
    out.append("JC_STUNT_WARN blueprint missing")
else:
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    names = [str(lib.get_display_name(sub.k2_find_subobject_data_from_handle(h))) for h in handles]
    if any("Part0" in n for n in names):
        out.append("JC_STUNT_OK part exists already")
    else:
        root = handles[0]
        params = unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.StaticMeshComponent, blueprint_context=bp)
        h, fail = sub.add_new_subobject(params)
        if str(fail):
            out.append("JC_STUNT_WARN add failed: %s" % fail)
        else:
            sub.rename_subobject(h, "Part0")
            comp = lib.get_object(sub.k2_find_subobject_data_from_handle(h))
            comp.set_editor_property("static_mesh", unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
            comp.set_editor_property("component_tags", ["JCPart0"])
            comp.set_editor_property("relative_scale3d", unreal.Vector(3.0, 2.0, 2.0))
            unreal.BlueprintEditorLibrary.compile_blueprint(bp)
            unreal.EditorAssetLibrary.save_asset(BP)
            out.append("JC_STUNT_OK Part0 cube added, tagged JCPart0")
"\n".join(out)
