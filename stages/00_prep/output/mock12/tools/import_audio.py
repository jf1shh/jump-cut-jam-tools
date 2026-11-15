import unreal, os
tasks=[]
for n in ("splat","win"):
    t=unreal.AssetImportTask()
    t.set_editor_property("filename", f"~/Projects/megajam-mock/work/audio/{n}.wav")
    t.set_editor_property("destination_path","/Game/Slime/Audio")
    t.set_editor_property("destination_name","S_"+n)
    t.set_editor_property("automated",True)
    t.set_editor_property("save",True)
    t.set_editor_property("replace_existing",True)
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for t in tasks:
    unreal.log("IMPORTRESULT %s -> %s" % (t.get_editor_property("filename"), t.get_editor_property("imported_object_paths")))
