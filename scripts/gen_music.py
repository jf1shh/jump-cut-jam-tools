#!/usr/bin/env python3
"""CLI that drives Nexus's local ACE-Step music generator and logs timing.

Thin wrapper over the Nexus repo's own `scripts/nexus_music.py` client (no
`nexus-music` command is installed on PATH the way `nexus-image`/`nexus-3d`
are - a Nexus-side gap, not fixed here; override with --music-script or
NEXUS_MUSIC_SCRIPT if the repo moves). Nexus's backend owns provenance for
the generated file; this script only adds the asset-pipeline-style CSV log.
"""
import argparse
import csv
import os
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_MUSIC_SCRIPT = Path.home() / "Projects" / "nexus" / "scripts" / "nexus_music.py"


def parse_args():
    parser = argparse.ArgumentParser(description="Generate one local ACE-Step track via Nexus.")
    parser.add_argument("prompt", help="style description, e.g. 'dusty lofi, rain, warm keys'")
    parser.add_argument("--out", required=True, help="output FLAC path")
    parser.add_argument("--duration", type=int, default=90, help="seconds, 10-120 (default 90)")
    parser.add_argument("--bpm", type=int, help="40-240")
    parser.add_argument("--key", help='e.g. "C minor"')
    parser.add_argument("--lyrics", help="UTF-8 lyrics file; selects vocals (default: instrumental)")
    parser.add_argument(
        "--structure",
        help="instrumental only: bracket structure tags for ACE-Step's energy "
             "roadmap, e.g. '[Intro] [Chorus] [Outro]'",
    )
    parser.add_argument("--seed", type=int, help="omit for random; 0 is reproducible")
    parser.add_argument("--log", default="stages/02_build/output/audio-pipeline-log.csv", help="CSV append log path")
    parser.add_argument(
        "--music-script",
        default=os.environ.get("NEXUS_MUSIC_SCRIPT", str(DEFAULT_MUSIC_SCRIPT)),
        help="path to Nexus's nexus_music.py client",
    )
    return parser.parse_args()


def ensure_csv_header(log_path: Path):
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", newline="") as f:
            csv.writer(f).writerow(["timestamp_iso", "out", "duration_s", "seconds", "exit_code"])


def append_row(log_path: Path, out, duration, seconds, exit_code):
    with log_path.open("a", newline="") as f:
        csv.writer(f).writerow([
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            out, duration, f"{seconds:.2f}", exit_code,
        ])


def main():
    args = parse_args()

    music_script = Path(args.music_script)
    if not music_script.exists():
        print(f"nexus_music.py not found at {music_script} (set --music-script or NEXUS_MUSIC_SCRIPT)", file=sys.stderr)
        sys.exit(2)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log_path = Path(args.log)
    ensure_csv_header(log_path)

    cmd = [sys.executable, str(music_script), args.prompt, "--out", str(out_path), "--duration", str(args.duration), "--json"]
    if args.bpm:
        cmd += ["--bpm", str(args.bpm)]
    if args.key:
        cmd += ["--key", args.key]
    if args.lyrics:
        cmd += ["--lyrics", args.lyrics]
    else:
        cmd.append("--instrumental")
        if args.structure:
            cmd += ["--structure", args.structure]
    if args.seed is not None:
        cmd += ["--seed", str(args.seed)]

    start = time.monotonic()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.monotonic() - start
    append_row(log_path, str(out_path), args.duration, elapsed, result.returncode)

    if result.returncode != 0:
        print(f"music generation failed (exit {result.returncode}):\n{result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)

    print(f"track: {out_path}")
    print(f"  seconds: {elapsed:.2f}")
    sys.exit(0)


if __name__ == "__main__":
    main()
