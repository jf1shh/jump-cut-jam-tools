"""Headless: import the Jump Cut audio kit (KIT_DIR=/abs/.../jam-audio/sfx, 13 SW_Jam_*.wav) into /Game/Audio/Sfx, set each
SoundWave Volume + Looping from MANIFEST.md, add the slots to DA_Tuning_Default.SoundSlots (existing slots kept; S_Cut_Stinger
only when unset) and set DA_Car_*.EngineLoop / EnginePitch (0.8, 1.4).
Prints KIT_* lines and appends them to SFX_REPORT=/abs/file when set (print() is swallowed under -nullrhi).
Run via UnrealEditor-Cmd -ExecCmds="py <this>" (editor closed)."""
import os
import traceback
import unreal

DEST = "/Game/Audio/Sfx"
TUNING = "/Game/Data/Tuning/DA_Tuning_Default"
STINGER = "/Game/Audio/Music/SW_Jam_Cut_Stinger"
# stem -> (SoundWave Volume, looping), from MANIFEST.md "Files" table.
KIT = {
    "SW_Jam_Engine_Loop": (0.84, True),
    "SW_Jam_TireChirp_01": (0.15, False),
    "SW_Jam_TireChirp_02": (0.15, False),
    "SW_Jam_TireChirp_03": (0.14, False),
    "SW_Jam_Crash": (0.95, False),
    "SW_Jam_Crash_Thud": (0.56, False),
    "SW_Jam_Crash_Clapper": (0.93, False),
    "SW_Jam_NearMiss_Wide": (0.48, False),
    "SW_Jam_NearMiss_Close": (0.53, False),
    "SW_Jam_NearMiss_Perfect": (0.77, False),
    "SW_Jam_Projector_Whir_Loop": (0.48, True),
    "SW_Jam_Grade_Stamp": (0.45, False),
    "SW_Jam_NewBest_Sting": (0.48, False),
}
SLOTS = {
    "S_Crash": "SW_Jam_Crash",
    "S_Crash_Thud": "SW_Jam_Crash_Thud",
    "S_Clapper": "SW_Jam_Crash_Clapper",
    "S_NearMiss_Wide": "SW_Jam_NearMiss_Wide",
    "S_NearMiss_Close": "SW_Jam_NearMiss_Close",
    "S_NearMiss_Perfect": "SW_Jam_NearMiss_Perfect",
    "S_GradeStamp": "SW_Jam_Grade_Stamp",
    "S_NewBest": "SW_Jam_NewBest_Sting",
    "S_TireChirpA": "SW_Jam_TireChirp_01",
    "S_TireChirpB": "SW_Jam_TireChirp_02",
    "S_TireChirpC": "SW_Jam_TireChirp_03",
    "S_ProjectorWhir": "SW_Jam_Projector_Whir_Loop",
}


def say(line):
    print(line)
    if os.environ.get("SFX_REPORT"):
        with open(os.environ["SFX_REPORT"], "a") as fh:
            fh.write(line + "\n")


def is_set(v):
    return v is not None and str(v) not in ("", "None")


try:
    tasks = []
    for stem in KIT:
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(os.environ["KIT_DIR"], stem + ".wav"))
        t.set_editor_property("destination_path", DEST)
        t.set_editor_property("destination_name", stem)
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", True)
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    waves = {}
    for stem, (vol, loop) in KIT.items():
        sw = unreal.EditorAssetLibrary.load_asset(f"{DEST}/{stem}")
        sw.set_editor_property("volume", vol)
        sw.set_editor_property("looping", loop)
        unreal.EditorAssetLibrary.save_loaded_asset(sw)
        waves[stem] = sw
        say(f"KIT_IMPORT {stem} dur={sw.get_editor_property('duration'):.3f} vol={sw.get_editor_property('volume'):.2f} loop={sw.get_editor_property('looping')}")

    tun = unreal.EditorAssetLibrary.load_asset(TUNING)
    slots = {str(k): v for k, v in dict(tun.get_editor_property("sound_slots")).items()}
    for stale in [k for k in slots if k.startswith("S_TireChirp") and k not in SLOTS]:
        del slots[stale]  # old _NN-suffixed chirp keys (FName number split merged them)
    for slot, stem in SLOTS.items():
        slots[slot] = waves[stem]
    if not is_set(slots.get("S_Cut_Stinger")):
        slots["S_Cut_Stinger"] = unreal.EditorAssetLibrary.load_asset(STINGER)
    tun.set_editor_property("sound_slots", slots)
    unreal.EditorAssetLibrary.save_loaded_asset(tun)
    say("KIT_SLOTS " + " ".join(sorted(slots.keys())))

    cars = [p for p in unreal.EditorAssetLibrary.list_assets("/Game/Data", recursive=True) if "/DA_Car_" in p]
    if not cars:
        say("KIT_CAR none (no DA_Car_* under /Game/Data)")
    for path in sorted(cars):
        car = unreal.EditorAssetLibrary.load_asset(path.split(".")[0])
        car.set_editor_property("engine_loop", waves["SW_Jam_Engine_Loop"])
        car.set_editor_property("engine_pitch", unreal.Vector2D(0.8, 1.4))
        unreal.EditorAssetLibrary.save_loaded_asset(car)
        p = car.get_editor_property("engine_pitch")
        say(f"KIT_CAR {car.get_name()} {car.get_editor_property('engine_loop').get_name()} ({p.x:.2f}, {p.y:.2f})")
except Exception:  # noqa: BLE001
    say("KIT_ERROR " + traceback.format_exc().replace("\n", " | "))
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
