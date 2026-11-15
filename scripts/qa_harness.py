#!/usr/bin/env python3
"""Headless QA pass over a list of levels: load each one, take a fixed-camera
screenshot, and measure real frame time against a target FPS budget.

INTENDED RUNTIME: like scripts/ue_import_asset.py, this only works inside the
Unreal Editor's embedded Python interpreter. Run headless (LIVE-VERIFIED
pattern, UE 5.8, 2026-10-28 -- see _config/reference/engine-reference/unreal/python-scripting.md):

    timeout 90 UnrealEditor-Cmd <Project>.uproject \\
        -ExecCmds="py scripts/qa_harness.py --map /Game/Maps/L_One --map /Game/Maps/L_Two \\
                   --out-dir stages/03_playtest/output/qa-screenshots --budget-fps 60" \\
        -unattended -nosplash -stdout -FullStdOutLogOutput
    pkill -9 -f "UnrealEditor-Cmd.*<project>"   # always; no in-script quit, see above

TEST ENVIRONMENT: do not point this at anything under this repo pre-jam (Rule
7(h): no levels/gameplay/art before the contest period). Test against
~/Projects/ue-mcp-verify or another scratch .uproject.

FRAME-TIME MEASUREMENT (LIVE-VERIFIED, UE 5.8, 2026-10-28):
unreal.AutomationLibrary.get_stat_inc_average("FrameTime") (and the other
candidate stat names tried: Frame, Unit, GameThreadTime, RenderThreadTime,
GPU) all returned 0.0 even after real engine frames had ticked -- the exact
stat name AutomationLibrary expects is still unconfirmed. This script does
NOT use that API. Instead it measures frame time directly from
unreal.register_slate_pre_tick_callback, which confirmed-live fires once per
real engine frame with that frame's delta_seconds.

IMPORTANT, LIVE-VERIFIED GOTCHA: a one-shot `py <path>` script runs
synchronously on the game thread and does NOT itself cause additional
frames to tick -- real frames only advance once the script returns control
to the editor's own loop. A first version of this script tried to
busy-wait for tick-callback data with a `time.sleep()` loop inside the
script; that blocks the same game thread the ticks need, so the callback
never fired and every map timed out with fps=None (confirmed live, 2026-10-28).
The fix: this script does no blocking at all. `run_qa_pass` registers ONE
tick callback that drives a small state machine (load map -> settle frames
-> screenshot -> sample SAMPLE_FRAMES of real delta_seconds -> advance to
the next map) and returns immediately; all the actual work happens inside
later real ticks, across the run of the editor process until `timeout` +
`pkill` end it (no explicit quit, same as every other script in this repo).
Results are written to the CSV log from inside the final tick callback
invocation, not from the bottom of the file.

CAMERA LOOKUP: finding a tagged CameraActor per map is UNVERIFIED -- no real
map with placed cameras exists pre-jam to test against. The lookup is wrapped
so a missing/renamed API degrades to `camera=None` (screenshot from the
active viewport) with a printed warning, matching the wrapping style in
scripts/ue_import_asset.py.

THREE ADDITIONAL CHECKS (UNVERIFIED, added for Phase B of
stages/00_prep/references/mock-jam-6-tooling-plan.md -- no real pre-jam level exists yet to test
any of them against; each is wrapped so a missing/renamed API degrades to a
printed warning + a "skipped" result, never a crash, same convention as the
frame-time measurement above). Mock jam 6 (Task C3) either confirms or
corrects them live:
  - _check_reachability(): can the nav system path from a PlayerStart to
    every actor tagged QAObjective? Requires a level-building convention
    (the QAObjective tag + a placed PlayerStart) this plan introduces, not
    one that exists yet.
  - _check_movement_setup(): static CDO inspection of the level's
    DefaultPawnClass -- does it actually have a movement component? This is
    the check that would have caught mock jam 5's bug 1 (bare Pawn,
    AddMovementInput silently a no-op) before a human had to play the build.
    Deliberately static, not runtime -- Task C4's agent playtest covers "does
    it move when played"; this one is not redundant with that.
  - _check_materials_and_textures(): flags any StaticMesh under /Game whose
    only material has no bound texture parameter -- the mock-jam-5 bug-2
    signature. Independent of ue_import_asset.py's _assert_real_material:
    this runs against whatever is already in the project regardless of which
    tool put it there, so it also catches a flat-material mesh placed by hand
    or imported some other way. Deliberately duplicates that heuristic rather
    than importing across the process boundary (this script runs inside a
    separate headless editor invocation) -- a shared module is a reasonable
    future refactor, out of scope here.
"""

import argparse
import csv
import os
import sys
import time

try:
    import unreal
except ImportError:
    unreal = None  # Allows this file to be imported/linted outside the editor.


SAMPLE_FRAMES = 60
SETTLE_FRAMES = 5
CAMERA_TAG = "QACamera"
OBJECTIVE_TAG = "QAObjective"
PLAYER_START_CLASS_NAME = "PlayerStart"
MOVEMENT_COMPONENT_CLASSES = ("FloatingPawnMovement", "CharacterMovementComponent")


def _require_unreal():
    if unreal is None:
        raise RuntimeError(
            "The 'unreal' module is not available. Run this script inside the "
            "UE Editor's Python environment, not with a system python3."
        )


def _find_qa_camera():
    """Looks for a CameraActor tagged QACamera in the current level. Returns
    None (active-viewport screenshot) if none is found or the lookup API
    isn't available on this engine build -- see the CAMERA LOOKUP note above.
    """
    try:
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in actor_subsystem.get_all_level_actors():
            if isinstance(actor, unreal.CameraActor) and CAMERA_TAG in actor.tags:
                return actor
    except Exception as e:
        print(f"WARNING: QA camera lookup failed ({e}); falling back to active viewport.")
    return None


def _check_reachability():
    """Soft-lock check: can the nav system path from a PlayerStart to every actor tagged
    QAObjective? UNVERIFIED in this repo -- no real map with a nav mesh and tagged objectives
    exists pre-jam to test against (same caveat as _find_qa_camera's CAMERA LOOKUP note). Wrapped
    so a missing API degrades to a printed warning + reachability=skipped, never a crash, matching
    this file's existing convention. Requires the level to tag win-condition actors QAObjective
    and have a PlayerStart placed -- a convention this plan introduces, not one that exists yet
    (see also stages/00_prep/references/pre-jam-mechanic-toolkit.md).
    """
    try:
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        all_actors = actor_subsystem.get_all_level_actors()
        player_starts = [a for a in all_actors if a.get_class().get_name() == PLAYER_START_CLASS_NAME]
        objectives = [a for a in all_actors if OBJECTIVE_TAG in a.tags]
        if not player_starts:
            return {"reachability": "skipped(no-player-start-found)"}
        if not objectives:
            return {"reachability": "skipped(no-QAObjective-tagged-actors)"}
        nav_sys = unreal.NavigationSystemV1.get_navigation_system(editor_subsystem.get_editor_world())
        if nav_sys is None:
            return {"reachability": "skipped(no-nav-system)"}
        start_loc = player_starts[0].get_actor_location()
        unreachable = []
        for obj in objectives:
            path = nav_sys.find_path_to_location_synchronously(
                editor_subsystem.get_editor_world(), start_loc, obj.get_actor_location()
            )
            is_valid = getattr(path, "is_valid", lambda: False)() if path else False
            if not is_valid:
                unreachable.append(obj.get_name())
        if unreachable:
            return {"reachability": f"FAIL(unreachable={unreachable})"}
        return {"reachability": f"pass({len(objectives)} objectives reachable)"}
    except Exception as exc:  # noqa: BLE001 - editor API surface, keep this non-fatal
        print(f"WARNING: reachability check failed ({exc}); skipping.")
        return {"reachability": "skipped(api-missing)"}


def _check_movement_setup():
    """Possession + movement-component check -- the mock-jam-5 bug-1 signature was a bare
    /Script/Engine.Pawn (BlueprintTools.get_parent) with EventTick calling AddMovementInput every
    tick but no FloatingPawnMovement/CharacterMovementComponent to consume it, so the call was a
    silent no-op. This check verifies, for the current level's GameMode, that:
      1. DefaultPawnClass is set to something other than the engine default DefaultPawn/None, and
      2. that pawn class (or its parent chain) actually has a movement component.
    Deliberately a static/CDO check, not a runtime one -- it catches "this pawn structurally cannot
    move" cheaply and early, while Task C4's agent playtest catches "the pawn can move but something
    else still blocks it" at runtime. Keep both; they're not redundant.
    UNVERIFIED against a real pre-jam level (none exists yet); wrapped per this file's convention.
    """
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        game_mode = world.get_world_settings().get_editor_property("default_game_mode")
        if game_mode is None:
            return {"movement": "skipped(no-default-game-mode-on-world-settings)"}
        gamemode_cdo = unreal.get_default_object(game_mode)
        pawn_class = gamemode_cdo.get_editor_property("default_pawn_class")
        if pawn_class is None:
            return {"movement": "FAIL(DefaultPawnClass is None - nothing to possess)"}
        generated_cdo = unreal.get_default_object(pawn_class)
        has_movement = any(
            generated_cdo.get_component_by_class(getattr(unreal, cls_name, type(None))) is not None
            for cls_name in MOVEMENT_COMPONENT_CLASSES
        )
        if not has_movement:
            return {
                "movement": f"FAIL(pawn class {pawn_class.get_name()} has no "
                             f"{MOVEMENT_COMPONENT_CLASSES} component - AddMovementInput would be a no-op)"
            }
        return {"movement": f"pass(DefaultPawnClass={pawn_class.get_name()}, movement component present)"}
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: movement/possession check failed ({exc}); skipping.")
        return {"movement": "skipped(api-missing)"}


def _check_materials_and_textures(content_root="/Game"):
    """Finds every StaticMesh under content_root and flags any whose only material has no bound
    texture parameter -- the mock-jam-5 bug-2 signature (StaticMeshTools.get_material_slots showing
    one generic Material_0, no texture asset in the mesh's folder). Independent of Phase A's
    ue_import_asset.py-side assertion (_assert_real_material): this runs against on-disk content
    regardless of which tool produced it, so it also catches a flat-material mesh placed by hand or
    imported some other way. Deliberately duplicates that same texture-parameter heuristic rather
    than importing it across the process boundary (this script runs inside a different headless
    editor invocation than the import script); sharing code would mean a shared module both scripts
    import, which is a reasonable future refactor but out of scope for this plan.
    """
    try:
        asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
        asset_data_list = asset_registry.get_assets_by_path(content_root, recursive=True)
        flat_material_meshes = []
        checked = 0
        for asset_data in asset_data_list:
            if asset_data.asset_class_path.asset_name != "StaticMesh":
                continue
            mesh = asset_data.get_asset()
            if mesh is None:
                continue
            checked += 1
            materials = mesh.get_editor_property("static_materials") or []
            has_texture = False
            for slot in materials:
                mat_iface = slot.get_editor_property("material_interface")
                if mat_iface is None:
                    continue
                try:
                    if unreal.MaterialEditingLibrary.get_texture_parameter_names(mat_iface):
                        has_texture = True
                        break
                except Exception:
                    continue
            if not has_texture:
                flat_material_meshes.append(str(asset_data.package_name))
        if flat_material_meshes:
            return {"materials": f"FAIL(no-texture meshes: {flat_material_meshes})"}
        return {"materials": f"pass({checked} static meshes checked, all have a textured material)"}
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: material/texture check failed ({exc}); skipping.")
        return {"materials": "skipped(api-missing)"}


def run_qa_pass(map_paths, out_dir, budget_fps, on_complete, content_root="/Game"):
    """Registers one non-blocking tick-driven state machine that walks
    map_paths in order (load -> settle SETTLE_FRAMES -> screenshot -> sample
    SAMPLE_FRAMES of real delta_seconds -> next map), then calls
    on_complete(results) from inside the final tick. Returns immediately --
    see the IMPORTANT gotcha in the module docstring for why this cannot
    block and wait for its own results instead.
    """
    _require_unreal()
    os.makedirs(out_dir, exist_ok=True)
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

    maps = [m.strip() for m in map_paths if m.strip()]
    state = {
        "idx": 0,
        "phase": "load",
        "settle_count": 0,
        "frame_deltas": [],
        "camera": None,
        "screenshot_path": None,
        "results": [],
    }

    def _start_current_map():
        map_path = maps[state["idx"]]
        loaded = level_subsystem.load_level(map_path)
        if not loaded:
            print(f"FAILED to load {map_path}")
            state["results"].append(
                {
                    "map": map_path,
                    "loaded": False,
                    "screenshot": None,
                    "frame_time_ms": None,
                    "fps": None,
                    "budget_fps": budget_fps,
                    "pass": False,
                    "note": "load_level returned False",
                }
            )
            state["idx"] += 1
            state["phase"] = "load"
            return
        state["settle_count"] = 0
        state["frame_deltas"] = []
        state["phase"] = "settle"

    def _finish_current_map():
        map_path = maps[state["idx"]]
        deltas = state["frame_deltas"]
        if deltas:
            avg_seconds = sum(deltas) / len(deltas)
            frame_time_ms = avg_seconds * 1000.0
            fps = 1.0 / avg_seconds if avg_seconds > 0 else None
        else:
            frame_time_ms, fps = None, None
        passed = fps is not None and fps >= budget_fps
        note = "camera=active_viewport" if state["camera"] is None else f"camera={CAMERA_TAG}"

        checks = {}
        checks.update(_check_reachability())
        checks.update(_check_movement_setup())
        checks.update(_check_materials_and_textures(content_root))

        print(f"{map_path}: fps={fps} budget={budget_fps} pass={passed} screenshot={state['screenshot_path']}")
        for name, result in checks.items():
            print(f"{map_path}: {name}={result}")

        result_row = {
            "map": map_path,
            "loaded": True,
            "screenshot": state["screenshot_path"],
            "frame_time_ms": frame_time_ms,
            "fps": fps,
            "budget_fps": budget_fps,
            "pass": passed,
            "note": note,
        }
        result_row.update(checks)
        state["results"].append(result_row)
        state["idx"] += 1
        state["phase"] = "load"

    def _on_tick(delta_seconds):
        if state["idx"] >= len(maps):
            unreal.unregister_slate_pre_tick_callback(handle["value"])
            on_complete(state["results"])
            return

        phase = state["phase"]
        if phase == "load":
            _start_current_map()
        elif phase == "settle":
            state["settle_count"] += 1
            if state["settle_count"] >= SETTLE_FRAMES:
                map_path = maps[state["idx"]]
                safe_name = map_path.strip("/").replace("/", "_")
                screenshot_path = os.path.join(out_dir, f"{safe_name}.png")
                camera = _find_qa_camera()
                unreal.AutomationLibrary.take_high_res_screenshot(
                    1920, 1080, screenshot_path, camera=camera, force_game_view=True
                )
                state["camera"] = camera
                state["screenshot_path"] = screenshot_path
                state["phase"] = "measure"
        elif phase == "measure":
            state["frame_deltas"].append(delta_seconds)
            if len(state["frame_deltas"]) >= SAMPLE_FRAMES:
                _finish_current_map()

    handle = {"value": None}
    handle["value"] = unreal.register_slate_pre_tick_callback(_on_tick)


def _write_csv_log(results, csv_path):
    file_exists = os.path.isfile(csv_path)
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["timestamp_iso", "map", "loaded", "fps", "budget_fps", "pass", "screenshot", "note"]
            )
        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for r in results:
            writer.writerow(
                [
                    timestamp_iso,
                    r["map"],
                    r["loaded"],
                    r["fps"],
                    r["budget_fps"],
                    r["pass"],
                    r["screenshot"],
                    r["note"],
                ]
            )


def _write_checks_csv_log(results, csv_path):
    file_exists = os.path.isfile(csv_path)
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp_iso", "map", "reachability", "movement", "materials"])
        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for r in results:
            writer.writerow(
                [
                    timestamp_iso,
                    r["map"],
                    r.get("reachability"),
                    r.get("movement"),
                    r.get("materials"),
                ]
            )


def _parse_cli_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    # LIVE-VERIFIED (UE 5.8, 2026-10-28): a comma inside a -ExecCmds="..." value
    # is NOT safe, even shell-quoted -- UE's own command-line parser splits
    # -ExecCmds entries on comma too (confirmed: a two-map comma-joined --maps
    # value silently truncated everything after the first comma, dropping
    # --out-dir and failing argparse's required check). So this takes a
    # repeated flag instead of a delimited list.
    parser.add_argument(
        "--map", dest="maps", action="append", required=True, help="A /Game level path; repeat for multiple maps"
    )
    parser.add_argument("--out-dir", required=True, help="Directory to write screenshots into")
    parser.add_argument("--budget-fps", type=float, default=60.0, help="FPS budget per map (default 60)")
    parser.add_argument(
        "--content-root",
        default="/Game",
        help="Scope for the materials/textures check (default /Game, the whole project); "
        "narrow this in a shared scratch project to avoid flagging unrelated prior "
        "phases' or negative-test fixtures' intentionally-untextured meshes",
    )
    parser.add_argument(
        "--csv-log",
        default="stages/03_playtest/output/qa-pipeline-log.csv",
        help="CSV log path, appended to (default stages/03_playtest/output/qa-pipeline-log.csv)",
    )
    parser.add_argument(
        "--checks-csv-log",
        default="stages/03_playtest/output/qa-checks-log.csv",
        help="Reachability/movement/materials CSV log path, appended to (default stages/03_playtest/output/qa-checks-log.csv)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    # Mirrors scripts/ue_import_asset.py: `py <path> --maps ... --out-dir ...`
    # passes the script's own args through sys.argv alongside engine args.
    cli_args = _parse_cli_args(sys.argv[1:])

    def _on_complete(qa_results):
        _write_csv_log(qa_results, cli_args.csv_log)
        _write_checks_csv_log(qa_results, cli_args.checks_csv_log)

    run_qa_pass(
        cli_args.maps,
        cli_args.out_dir,
        cli_args.budget_fps,
        on_complete=_on_complete,
        content_root=cli_args.content_root,
    )
    # Returns immediately -- the state machine above does its work across
    # later real ticks, writing the CSV from inside the final tick callback.
    # No blocking, no explicit quit: rely on `timeout` + `pkill` like every
    # other headless script in this repo.
