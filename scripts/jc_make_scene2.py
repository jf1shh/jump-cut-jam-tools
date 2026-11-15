"""Scene 2 "Chase" greybox: duplicate L_Scene01 -> L_Scene02, DT_Stunts_S2, DA_Scene_02. Re-runnable.
Run headless: UnrealEditor-Cmd JumpCut.uproject -run=pythonscript -script=THIS -nullrhi -unattended -nosplash -stdout
Writes the result lines to the file named by env JC_OUT (default /tmp/jc_scene2.out)."""
import os
import unreal

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
out = []

S2_CSV = (
    "Name,Of,Preset,TOn,TOff,Tier,Tel,Lanes,Block,Line,Curve,C0,C1,C2,Shot,Band,MustCut,TMark,Surge,Cam\n"
    "S2-1,,Drums,7.0,7.5,Easy,2.5,RC,,C>L,Roll,-1.5,0.5,0,3,1.0,False,9.0,0,A\n"
    "S2-2,,PropTruck,12.0,12.5,Easy,2.5,LC,,R,Slide,-2.5,0.75,0,3,1.0,False,14.0,0,B\n"
    "S2-3,,FalseFront,17.0,17.5,Easy,2.5,CR,,C>L,Fall,-1.0,1.0,90,3,1.0,False,19.0,0,C\n"
    "S2-4,,WaterTower,22.0,24.0,None,2.5,LCR,LCR,,Fall,0.0,2.0,90,1,0,True,26.0,0,B\n"
    "S2-5,,LightRig,30.0,30.8,TimedGap,2.5,RC,L,C>R,Swing,-0.5,1.2,0.6,3,1.0,False,32.0,0,A\n"
    "S2-6,,Facade,35.0,36.7,TwoHop,2.5,LC,,L>C>R,Sweep,0.7,0.75,0,3,1.0,False,37.0,6,BC\n"
    "S2-6b,S2-6,Scaffold,,,,,CR,,,Sweep,-1.4,0.75,1.5,,,,,,\n"
)

if not EAL.does_asset_exist("/Game/Maps/L_Scene02"):
    out.append("dup level=%s" % EAL.duplicate_asset("/Game/Maps/L_Scene01", "/Game/Maps/L_Scene02"))
    out.append("save level=%s" % EAL.save_asset("/Game/Maps/L_Scene02", only_if_is_dirty=False))

dt_path = "/Game/Data/Scenes/DT_Stunts_S2"
if EAL.does_asset_exist(dt_path):
    dt = EAL.load_asset(dt_path)
else:
    f = unreal.DataTableFactory()
    f.set_editor_property("struct", unreal.JCStuntRow.static_struct())
    dt = AT.create_asset("DT_Stunts_S2", "/Game/Data/Scenes", unreal.DataTable, f)
ok = unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(dt, S2_CSV)
out.append("csv ok=%s rows=%d" % (ok, len(unreal.DataTableFunctionLibrary.get_data_table_row_names(dt))))
EAL.save_asset(dt_path)

da_path = "/Game/Data/Scenes/DA_Scene_02"
if EAL.does_asset_exist(da_path):
    da = EAL.load_asset(da_path)
else:
    da = EAL.duplicate_asset("/Game/Data/Scenes/DA_Scene_01", da_path) and EAL.load_asset(da_path)
for k, v in (("number", 2), ("title", "Chase"), ("display_name", "Chase"), ("base_speed", 18.0), ("stunts", dt),
             ("level", EAL.load_asset("/Game/Maps/L_Scene02")), ("clapper_waits_for_press", False),
             ("first_prompt_stunt", "S2-1"), ("free_take_stunt", "S2-1"), ("sort_order", 2)):
    da.set_editor_property(k, v)
out.append("da saved=%s" % EAL.save_asset(da_path))
open(os.environ.get("JC_OUT", "/tmp/jc_scene2.out"), "w").write("\n".join(out))
