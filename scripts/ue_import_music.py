"""Headless: import the synthesized loop as a looping SoundWave and set it as DA_Tuning_Default.Music.
Env: MUSIC_WAV=/abs/loop.wav. Prints MUSIC_IMPORT lines. Run via UnrealEditor-Cmd -ExecCmds="py <this>" (editor closed)."""
import os
import unreal

DEST, NAME = "/Game/Audio/Music", "SW_Jam_Loop"
TUNING = "/Game/Data/Tuning/DA_Tuning_Default"
try:
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", os.environ["MUSIC_WAV"])
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", NAME)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    wave = unreal.EditorAssetLibrary.load_asset(f"{DEST}/{NAME}")
    wave.set_editor_property("looping", True)
    unreal.EditorAssetLibrary.save_loaded_asset(wave)
    tun = unreal.EditorAssetLibrary.load_asset(TUNING)
    tun.set_editor_property("music", wave)
    st = os.environ.get("STINGER_WAV")
    if st:  # one-shot (not looping) stinger in the named slot the CUT hook plays
        t2 = unreal.AssetImportTask()
        t2.set_editor_property("filename", st)
        t2.set_editor_property("destination_path", DEST)
        t2.set_editor_property("destination_name", "SW_Jam_Cut_Stinger")
        t2.set_editor_property("automated", True)
        t2.set_editor_property("replace_existing", True)
        t2.set_editor_property("save", True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t2])
        sw = unreal.EditorAssetLibrary.load_asset(f"{DEST}/SW_Jam_Cut_Stinger")
        slots = dict(tun.get_editor_property("sound_slots"))
        slots["S_Cut_Stinger"] = sw
        tun.set_editor_property("sound_slots", slots)
        print(f"MUSIC_IMPORT stinger ok dur={sw.get_editor_property('duration'):.2f} slots={list(slots.keys())}")
    unreal.EditorAssetLibrary.save_loaded_asset(tun)
    print(f"MUSIC_IMPORT ok wave={wave.get_name()} dur={wave.get_editor_property('duration'):.2f} looping={wave.get_editor_property('looping')} tuning.music={tun.get_editor_property('music').get_name()}")
except Exception as exc:  # noqa: BLE001
    print(f"MUSIC_IMPORT FAIL {exc!r}")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
