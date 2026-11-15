import unreal
P="/Game/Materials"; N="M_Ground"
at=unreal.AssetToolsHelpers.get_asset_tools()
if not unreal.EditorAssetLibrary.does_asset_exist(P+"/"+N):
    m=at.create_asset(N,P,unreal.Material,unreal.MaterialFactoryNew())
    ml=unreal.MaterialEditingLibrary
    c=ml.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-300,0)
    c.set_editor_property("constant",unreal.LinearColor(0.045,0.05,0.045,1))
    ml.connect_material_property(c,"",unreal.MaterialProperty.MP_BASE_COLOR)
    ml.recompile_material(m); unreal.EditorAssetLibrary.save_asset(P+"/"+N)
m=unreal.load_asset(P+"/"+N)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label()=="Ground_Plane":
        a.static_mesh_component.set_material(0,m)
raise RuntimeError("MATOK")
