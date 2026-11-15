#!/usr/bin/env python3
"""Headless agent-administered playtest: start a real PIE session, steer the
player pawn toward a QAObjective-tagged actor by direct vector every tick
(standing in for player input, not nav pathing), and report whether the
distance closed over a fixed number of ticks.

INTENDED RUNTIME: same embedded-editor-Python constraint as scripts/qa_harness.py.
Run headless:

    timeout 90 UnrealEditor-Cmd <Project>.uproject \\
        -ExecCmds="py scripts/agent_playtest.py --map /Game/Maps/L_One \\
                   --objective-tag QAObjective --max-ticks 180 \\
                   --csv-log stages/03_playtest/output/qa-playtest-log.csv" \\
        -unattended -nosplash -nullrhi -stdout -FullStdOutLogOutput
    pkill -9 -f "UnrealEditor-Cmd.*<project>"   # always; no in-script quit

Pass ABSOLUTE paths for --csv-log -- UnrealEditor-Cmd's cwd is its own
Engine/Binaries/Linux/ folder, not the shell's cwd at launch (same gotcha
documented for qa_harness.py's --out-dir/--csv-log in
stages/00_prep/references/mock-jam-6-tooling-plan.md's gotchas log).

LIVE-VERIFIED PATTERN (mock jam 6, Task C4 Tier 1, 2026-10-29, as a one-off
spike never committed as a reusable script until now -- this file formalizes
it): `LevelEditorSubsystem.editor_request_begin_play()` starts a real PIE
session in the same process; `is_in_play_in_editor()` goes True on the next
tick. The live PIE world comes from `UnrealEditorSubsystem.get_game_world()`
-- NOT `LevelEditorSubsystem`, which has no such method -- because
`GameplayStatics.get_player_pawn(editor_world, 0)` silently returns None
during PIE (the editor world's actor list goes empty while playing; the real
pawn lives in the separate `UEDPIE_0_<Level>` game world). From that world,
`GameplayStatics.get_player_pawn(game_world, 0)` finds the real pawn and
`pawn.add_movement_input(direction, 1.0)` actually moves it. End with
`editor_request_end_play()`.

Like qa_harness.py, this never blocks waiting for its own result: it
registers one `register_slate_pre_tick_callback` state machine (load map ->
settle -> begin play -> wait for PIE -> steer toward the objective for
max-ticks real ticks -> end play -> report) and returns immediately. All
real work happens across later real ticks until `timeout` + `pkill` end the
process, same convention as every other script in this repo.
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


SETTLE_FRAMES = 5
PIE_START_TIMEOUT_TICKS = 60
OBJECTIVE_TAG_DEFAULT = "QAObjective"


def _require_unreal():
    if unreal is None:
        raise RuntimeError(
            "The 'unreal' module is not available. Run this script inside the "
            "UE Editor's Python environment, not with a system python3."
        )


def _distance(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5


def run_agent_playtest(map_path, objective_tag, max_ticks, on_complete, diag=False):
    """Registers one non-blocking tick-driven state machine: load -> settle ->
    begin_play -> wait-for-pie -> steer -> end_play -> report. Returns
    immediately; on_complete(result_dict) fires from inside the final tick.
    """
    _require_unreal()
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

    state = {
        "phase": "load",
        "settle_count": 0,
        "pie_wait_count": 0,
        "steer_count": 0,
        "start_distance": None,
        "end_distance": None,
        "objective_loc": None,
        "result": None,
        "total_delta": 0.0,
    }

    def _finish(note):
        start_d = state["start_distance"]
        end_d = state["end_distance"]
        closed = start_d is not None and end_d is not None and end_d < start_d
        result = {
            "map": map_path,
            "objective_tag": objective_tag,
            "ticks": state["steer_count"],
            "start_distance": start_d,
            "end_distance": end_d,
            "pass": closed,
            "note": note,
        }
        print(
            f"{map_path}: agent_playtest start_distance={start_d} end_distance={end_d} "
            f"ticks={state['steer_count']} pass={closed} note={note}"
        )
        state["result"] = result
        unreal.unregister_slate_pre_tick_callback(handle["value"])
        on_complete(result)

    def _on_tick(delta_seconds):
        phase = state["phase"]
        if phase == "load":
            loaded = level_subsystem.load_level(map_path)
            if not loaded:
                _finish("FAIL(load_level returned False)")
                return
            state["settle_count"] = 0
            state["phase"] = "settle"
        elif phase == "settle":
            state["settle_count"] += 1
            if state["settle_count"] >= SETTLE_FRAMES:
                actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
                objectives = [a for a in actor_subsystem.get_all_level_actors() if objective_tag in a.tags]
                if not objectives:
                    _finish(f"skipped(no-{objective_tag}-tagged-actors)")
                    return
                state["objective_loc"] = objectives[0].get_actor_location()
                level_subsystem.editor_request_begin_play()
                state["pie_wait_count"] = 0
                state["phase"] = "wait_for_pie"
        elif phase == "wait_for_pie":
            state["pie_wait_count"] += 1
            if level_subsystem.is_in_play_in_editor():
                state["phase"] = "steer"
                return
            if state["pie_wait_count"] >= PIE_START_TIMEOUT_TICKS:
                _finish("FAIL(PIE never started)")
        elif phase == "steer":
            state["total_delta"] += delta_seconds
            game_world = editor_subsystem.get_game_world()
            pawn = unreal.GameplayStatics.get_player_pawn(game_world, 0)
            if pawn is None:
                _finish("FAIL(no player pawn in game world)")
                return
            pawn_loc = pawn.get_actor_location()
            if diag and state["start_distance"] is None:
                state["start_distance"] = _distance(pawn_loc, state["objective_loc"])
                movement_comps = [
                    c.get_class().get_name()
                    for c in pawn.get_components_by_class(unreal.MovementComponent)
                ]
                print(f"DIAG pawn_class={pawn.get_class().get_name()} movement_components={movement_comps}")
            elif state["start_distance"] is None:
                state["start_distance"] = _distance(pawn_loc, state["objective_loc"])
            dx = state["objective_loc"].x - pawn_loc.x
            dy = state["objective_loc"].y - pawn_loc.y
            planar_dist = (dx ** 2 + dy ** 2) ** 0.5
            if planar_dist > 0:
                direction = unreal.Vector(dx / planar_dist, dy / planar_dist, 0.0)
                pawn.add_movement_input(direction, 1.0)
            if diag and state["steer_count"] % 30 == 0:
                vel = pawn.get_velocity()
                print(
                    f"DIAG tick={state['steer_count']} slate_delta_seconds={delta_seconds} "
                    f"total_delta={state['total_delta']:.4f} pawn_loc={pawn_loc} velocity={vel} "
                    f"planar_dist_remaining={planar_dist:.2f}"
                )
            state["steer_count"] += 1
            if state["steer_count"] >= max_ticks:
                state["end_distance"] = _distance(pawn.get_actor_location(), state["objective_loc"])
                level_subsystem.editor_request_end_play()
                _finish("ran-to-max-ticks")

    handle = {"value": None}
    handle["value"] = unreal.register_slate_pre_tick_callback(_on_tick)


def _write_csv_log(result, csv_path):
    file_exists = os.path.isfile(csv_path)
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["timestamp_iso", "map", "objective_tag", "ticks", "start_distance", "end_distance", "pass", "note"]
            )
        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        writer.writerow(
            [
                timestamp_iso,
                result["map"],
                result["objective_tag"],
                result["ticks"],
                result["start_distance"],
                result["end_distance"],
                result["pass"],
                result["note"],
            ]
        )


def _parse_cli_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", required=True, help="A /Game level path to play-test")
    parser.add_argument("--objective-tag", default=OBJECTIVE_TAG_DEFAULT, help="Actor tag to steer toward")
    parser.add_argument("--max-ticks", type=int, default=180, help="Real PIE ticks to steer for (default 180)")
    parser.add_argument(
        "--csv-log",
        default="stages/03_playtest/output/qa-playtest-log.csv",
        help="CSV log path, appended to (default stages/03_playtest/output/qa-playtest-log.csv) -- pass an ABSOLUTE path",
    )
    parser.add_argument(
        "--diag",
        action="store_true",
        help="Print extra LogPython diagnostics (pawn class/movement components, periodic "
        "velocity+position every 30 ticks). Off by default; turn on when `pass=True` looks "
        "suspicious (see the weak-movement gotcha in stages/00_prep/references/mock-jam-6-tooling-plan.md).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    cli_args = _parse_cli_args(sys.argv[1:])

    def _on_complete(result):
        _write_csv_log(result, cli_args.csv_log)

    run_agent_playtest(
        cli_args.map, cli_args.objective_tag, cli_args.max_ticks, _on_complete, diag=cli_args.diag
    )
    # Returns immediately -- the state machine above does its work across
    # later real ticks, writing the CSV from inside the final tick callback.
    # No blocking, no explicit quit: rely on `timeout` + `pkill` like every
    # other script in this repo.
