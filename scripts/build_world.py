#!/usr/bin/env python3
"""Run the level build, then check the scales of what it placed. Can run detached.

  build_world.py --placements work/world_placements.json -- UnrealEditor-Cmd P.uproject -ExecCmds="py ..."
  build_world.py --detach --placements ... -- <build command>     # returns at once; see below
  build_world.py --wait work/build_world.done                     # block until the detached run ends
  build_world.py --check-only --placements work/world_placements.json --max-scale 10

The build command is whatever follows `--` (headless editor, MCP script, ...). Everything after it is
passed through untouched. The scale check reads the level-copy placement list the build wrote:
a JSON list (or {"actors": [...]}) of {"name", "scale": 2.0 | [x,y,z], "bounds_m": [x,y,z] (mesh size at
scale 1, read from the mesh), "expect_size_m": 1.2 | [x,y,z]} (last two optional). It fails (exit 1) when a
scale has a zero axis, is over --max-scale (50) or under its inverse, when bounds_m x scale is over
--max-size (100 m), or when that final size misses expect_size_m by more than --size-tol (25%): the last
one catches a stale scale left on a reshaped mesh. Lopsided scales (blockout floors, walls) are fine.

--detach runs under nohup in its own session (so a claude-loop handoff that kills the session's
process tree does not kill the build). It prints the driver pid, writes the log and a done-file
holding "exit=N". Wait with `--wait DONE` (watches the pid too, exits 3 if the driver died with no
done-file), `waitfor --file DONE --match exit=`, or Monitor on the done-file.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asset_chain import add_detach_args, handle_detach  # noqa: E402

DEFAULT_MAX_SCALE = 50.0  # blockout floors/walls are legitimately 20x or more
DEFAULT_MAX_SIZE = 100.0  # metres, longest side of an actor after scale (needs bounds_m)
DEFAULT_SIZE_TOL = 0.25   # relative, for expect_size_m


def _components(scale):
    if isinstance(scale, (int, float)):
        return [float(scale)] * 3
    vals = [float(v) for v in scale]
    if len(vals) != 3:
        raise ValueError(f"scale needs 1 or 3 numbers, got {scale!r}")
    return vals


def check_scales(actors, max_scale=DEFAULT_MAX_SCALE, max_size=DEFAULT_MAX_SIZE, size_tol=DEFAULT_SIZE_TOL):
    """Return problem strings for placed actors with a silly scale or size.

    Per actor: "scale" (number or [x,y,z]); optional "bounds_m" (the mesh size at scale 1, metres, read from
    the mesh, not the actor) and optional "expect_size_m" (the longest side it should end up, or [x,y,z]).
    Scale alone cannot tell a stale 3,3,3 on a reshaped mesh from a good one, so the final size
    (bounds_m x scale) is what gets compared. Lopsided scales are fine: blockout floors and walls are.
    """
    problems = []
    for i, actor in enumerate(actors):
        name = actor.get("name", f"#{i}")
        if "scale" not in actor:
            continue
        try:
            comps = _components(actor["scale"])
            bounds = _components(actor["bounds_m"]) if "bounds_m" in actor else None
            expect = actor.get("expect_size_m")
            expect = None if expect is None else (_components(expect) if isinstance(expect, list) else float(expect))
        except (TypeError, ValueError) as exc:
            problems.append(f"{name}: unreadable scale/bounds/expect ({exc})")
            continue
        mags = [abs(c) for c in comps]
        if min(mags) < 1e-6:
            problems.append(f"{name}: scale {comps} has a zero axis (flat)")
            continue
        if max(mags) > max_scale:
            problems.append(f"{name}: scale {comps} is over {max_scale:g}")
        elif min(mags) < 1.0 / max_scale:
            problems.append(f"{name}: scale {comps} is under {1.0 / max_scale:g}")
        if expect is not None and bounds is None:
            problems.append(f"{name}: expect_size_m needs bounds_m (read the mesh bounds into the placements)")
            continue
        if bounds is None:
            continue
        final = [abs(b) * m for b, m in zip(bounds, mags)]
        if max(final) > max_size:
            problems.append(f"{name}: final size {max(final):.1f} m is over {max_size:g} m")
        if expect is None:
            continue
        if isinstance(expect, float):
            got, want = max(final), expect
            if want <= 0 or abs(got - want) > size_tol * want:
                problems.append(f"{name}: longest side {got:.2f} m but expected {want:g} m (stale scale on a reshaped mesh?)")
        else:
            for axis, got, want in zip("xyz", final, expect):
                if want <= 0 or abs(got - want) > size_tol * want:
                    problems.append(f"{name}: {axis} size {got:.2f} m but expected {want:g} m (stale scale on a reshaped mesh?)")
    return problems


def load_actors(path):
    data = json.loads(Path(path).read_text())
    actors = data.get("actors") if isinstance(data, dict) else data
    if not isinstance(actors, list):
        raise ValueError("placements file must be a JSON list or {\"actors\": [...]}")
    return actors


def parse_args(argv):
    argv = list(argv)
    cmd = []
    if "--" in argv:
        i = argv.index("--")
        argv, cmd = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--placements", help="level-copy placement JSON to scale-check after the build")
    ap.add_argument("--max-scale", type=float, default=DEFAULT_MAX_SCALE)
    ap.add_argument("--max-size", type=float, default=DEFAULT_MAX_SIZE, help="metres, longest side after scale (needs bounds_m)")
    ap.add_argument("--size-tol", type=float, default=DEFAULT_SIZE_TOL, help="relative tolerance for expect_size_m")
    ap.add_argument("--check-only", action="store_true", help="skip the build command, just scale-check --placements")
    add_detach_args(ap, "build_world")
    a = ap.parse_args(argv)
    a.cmd = cmd
    if not a.wait and not a.check_only and not cmd:
        ap.error("give the build command after `--`, or --check-only, or --wait DONE")
    if a.check_only and not a.placements:
        ap.error("--check-only needs --placements")
    if a.max_scale <= 1 or a.max_size <= 0 or a.size_tol < 0:
        ap.error("--max-scale must be over 1, --max-size positive, --size-tol not negative")
    return a


def main(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    a = parse_args(raw)
    rc = handle_detach(a, Path(__file__).resolve(), raw, "build_world")
    if rc is not None:
        return rc
    if a.cmd and not a.check_only:
        r = subprocess.run(a.cmd)
        if r.returncode != 0:
            print(f"build_world: build command failed (exit {r.returncode})", file=sys.stderr)
            return r.returncode
    if a.placements:
        try:
            problems = check_scales(load_actors(a.placements), a.max_scale, a.max_size, a.size_tol)
        except (OSError, ValueError) as exc:
            print(f"build_world: cannot read placements {a.placements}: {exc}", file=sys.stderr)
            return 2
        for p in problems:
            print(f"SCALE {p}", file=sys.stderr)
        if problems:
            print(f"build_world: {len(problems)} scale problem(s); fix the level before shipping", file=sys.stderr)
            return 1
        print("build_world: scale check ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
