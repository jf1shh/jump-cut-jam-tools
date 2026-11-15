"""Headless: import the synthesized action sounds (SFX_DIR=/abs/dir with sfx_*.wav) and add them to DA_Tuning_Default.SoundSlots
as S_Pause, S_Resume, S_Wrap, S_NoFilm, S_ShotKept, S_Cut. SFX_SLOTS=S_Cut,... limits it to those slots.
Prints SFX_IMPORT lines, and appends them to SFX_REPORT=/abs/file when set (print() is swallowed under -nullrhi).
Run via UnrealEditor-Cmd -ExecCmds="py <this>" (editor closed)."""
import os
import unreal

DEST = "/Game/Audio/Sfx"
TUNING = "/Game/Data/Tuning/DA_Tuning_Default"
MAP = {"sfx_pause": "S_Pause", "sfx_resume": "S_Resume", "sfx_wrap": "S_Wrap", "sfx_nofilm": "S_NoFilm", "sfx_keep": "S_ShotKept", "sfx_cut": "S_Cut"}
ONLY = {x for x in os.environ.get("SFX_SLOTS", "").split(",") if x}


def say(line):
    print(line)
    if os.environ.get("SFX_REPORT"):
        with open(os.environ["SFX_REPORT"], "a") as fh:
            fh.write(line + "\n")



try:
    tun = unreal.EditorAssetLibrary.load_asset(TUNING)
    slots = dict(tun.get_editor_property("sound_slots"))
    for base, slot in MAP.items():
        if ONLY and slot not in ONLY:
            continue
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(os.environ["SFX_DIR"], base + ".wav"))
        t.set_editor_property("destination_path", DEST)
        t.set_editor_property("destination_name", "SW_Jam_" + slot)
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        sw = unreal.EditorAssetLibrary.load_asset(f"{DEST}/SW_Jam_{slot}")
        slots[slot] = sw
        say(f"SFX_IMPORT {slot} dur={sw.get_editor_property('duration'):.2f}")
    tun.set_editor_property("sound_slots", slots)
    unreal.EditorAssetLibrary.save_loaded_asset(tun)
    say(f"SFX_IMPORT ok slots={sorted(slots.keys())}")
except Exception as exc:  # noqa: BLE001
    say(f"SFX_IMPORT FAIL {exc!r}")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
