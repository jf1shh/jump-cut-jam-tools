#!/usr/bin/env python3
"""Grey-box gate: asset generation stays blocked until a primitives-only build was won, lost and restarted.

  greybox_gate.py record --project "$UPROJECT" --won --lost --restarted [--run ID] [--note TEXT]
  greybox_gate.py check --project "$UPROJECT" [--run ID]      exit 0 if proven for that project, else 13
  greybox_gate.py status [--project PATH]                     with --project: the proven line or "not proven";
                                                              without: the stored marker (project, run, time),
                                                              marked "project not checked"
  greybox_gate.py clear                                       delete the marker

FAIL CLOSED: only exit 0 means "go". Any other exit code (13 blocked, 2 usage, a python error) means stop.
`check` without --project exits 2.

The marker stores the resolved absolute path of the game's .uproject; `check` passes only for the same path,
so a mock project's marker can never open the jam project. It does not expire (a proven loop stays proven);
one dated in the future is rejected. --run is an optional extra label: if given to check it must match.
The marker lives in <repo>/.handoff/greybox (anchored on the git common dir, so every worktree and cwd of
this repo reads the same file; $GREYBOX_GATE_DIR or --state-dir overrides).
The claim behind the rule (loop first, art later) is from videos and is UNTESTED here; see
_config/reference/canon/jam-grey-box-first.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

EXIT_OK, EXIT_BLOCKED, EXIT_USAGE = 0, 13, 2
MARKER = "greybox_proven.json"
REQUIRED = ("won", "lost", "restarted")
HHMM = re.compile(r"^\d\d:\d\d$")


def repo_root() -> Path:
    here = Path(__file__).resolve().parent
    try:
        out = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                             cwd=here, capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip()).parent
    except (OSError, subprocess.SubprocessError):
        pass
    return here.parent


def state_dir(arg=None) -> Path:
    if arg or os.environ.get("GREYBOX_GATE_DIR"):
        return Path(arg or os.environ["GREYBOX_GATE_DIR"])
    return repo_root() / ".handoff" / "greybox"


def norm_project(project: str) -> str:
    return str(Path(project).expanduser().resolve())


def record(d: Path, won: bool, lost: bool, restarted: bool, project: str, note: str = "", run: str = "",
           now: datetime | None = None) -> dict:
    missing = [n for n, v in zip(REQUIRED, (won, lost, restarted)) if not v]
    if missing:
        raise ValueError("cannot record: not yet seen: " + ", ".join(missing))
    if not project:
        raise ValueError("cannot record: --project PATH is required")
    now = now or datetime.now().astimezone()
    data = {"proven_at": now.isoformat(timespec="seconds"), "hhmm": now.strftime("%H:%M"),
            "project": norm_project(project), "run": run, "note": note}
    d.mkdir(parents=True, exist_ok=True)
    (d / MARKER).write_text(json.dumps(data), encoding="utf-8")
    return data


def load(d: Path, project: str, run: str = "", now: datetime | None = None, skip_project: bool = False):
    p = d / MARKER
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        hhmm, stamp = data.get("hhmm"), data.get("proven_at")
        if not (isinstance(hhmm, str) and HHMM.match(hhmm) and isinstance(stamp, str)):
            return None
        when = datetime.fromisoformat(stamp)
        if when.tzinfo is None:
            return None
        if when - (now or datetime.now().astimezone()) > timedelta(0):
            return None  # dated in the future
        if not skip_project and (not project or data.get("project") != norm_project(project)):
            return None
        if run and data.get("run") != run:
            return None
    except (OSError, ValueError, TypeError):
        return None
    return data


def clear(d: Path) -> bool:
    p = d / MARKER
    if p.is_file():
        p.unlink()
        return True
    return False


def line(data: dict) -> str:
    return f"grey-box loop proven at {data['hhmm']}"


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--state-dir", default=argparse.SUPPRESS)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", parents=[common])
    for n in REQUIRED:
        r.add_argument(f"--{n}", action="store_true")
    r.add_argument("--note", default="")
    r.add_argument("--run", default="")
    r.add_argument("--project", required=True, help="path of the game's .uproject (e.g. \"$UPROJECT\")")
    c = sub.add_parser("check", parents=[common])
    c.add_argument("--run", default="")
    c.add_argument("--project", required=True, help="path of the game's .uproject (e.g. \"$UPROJECT\")")
    s = sub.add_parser("status", parents=[common])
    s.add_argument("--project", default="")
    sub.add_parser("clear", parents=[common])
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    d = state_dir(getattr(a, "state_dir", None))
    if a.cmd == "record":
        try:
            print(line(record(d, a.won, a.lost, a.restarted, a.project, a.note, a.run)))
        except ValueError as e:
            print(e, file=sys.stderr)
            return EXIT_USAGE
        return EXIT_OK
    if a.cmd == "clear":
        print("marker cleared" if clear(d) else "no marker")
        return EXIT_OK
    if a.cmd == "status" and not a.project:
        raw = load(d, "", skip_project=True)
        if raw:
            print(f"{line(raw)} (project {raw.get('project')}, run {raw.get('run') or '-'}; project not checked)")
        else:
            print("not proven")
        return EXIT_OK
    data = load(d, a.project, getattr(a, "run", ""))
    if a.cmd == "status":
        print(line(data) if data else "not proven")
        return EXIT_OK
    if data:
        print(line(data))
        return EXIT_OK
    print("BLOCKED: no asset generation until the grey-box loop is won, lost and restarted", file=sys.stderr)
    return EXIT_BLOCKED


if __name__ == "__main__":
    sys.exit(main())
