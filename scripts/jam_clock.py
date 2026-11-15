#!/usr/bin/env python3
"""Jam clock: counts down to the contest deadline and forces the endgame.

Mock 10 ran past its hard stop because nothing enforced it. This does.

  jam_clock.py start [--deadline ISO]   write the deadline, then run the loop (foreground)
  jam_clock.py status                   print time left and the current phase
  jam_clock.py tick                     evaluate once (cron / manual / tests)
  jam_clock.py check                    exit code for the agent to poll: 0 ok, 10 force-package,
                                        11 final, 12 past deadline

Phases (time left -> phase):
  > 60 min   WORK      normal
  <= 60 min  PACKAGE   FORCE_PACKAGE marker: stop feature work, package + upload now
  <= 15 min  FINAL     FINAL marker: only itch page / text edits allowed
  <= 0       EXPIRED   deadline passed

Markers are files in the state dir; each holds JSON with the instruction text, so an agent that
polls `check` (or reads the file) gets the order in plain words. If a nudge command is set
(--nudge-cmd or $JAM_CLOCK_NUDGE_CMD), it is run once per marker with the message on stdin and
$JAM_CLOCK_MESSAGE; its failure never blocks the marker. The default deadline is the Official Rules
close: 2026-11-15 20:59 ET (= 17:59 PT = 2026-11-16T01:59:00Z).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_DEADLINE = "2026-11-16T01:59:00+00:00"
PACKAGE_MIN = 60
FINAL_MIN = 15
STALE_AFTER = timedelta(hours=12)  # a plain `start` may replace a deadline dead longer than this
MARKERS = ("FORCE_PACKAGE", "FINAL", "EXPIRED")
EXIT_OK, EXIT_PACKAGE, EXIT_FINAL, EXIT_EXPIRED = 0, 10, 11, 12

MESSAGES = {
    "FORCE_PACKAGE": (
        "JAM CLOCK T-{m} min: STOP feature work now. Run package + upload immediately. "
        "Only fixes needed to make the package ship are allowed."
    ),
    "FINAL": (
        "JAM CLOCK T-{m} min: FINAL. No code, level or asset changes and no new builds. "
        "Only itch page and text edits are allowed."
    ),
    "EXPIRED": (
        "JAM CLOCK: the deadline has PASSED. Nothing more may ship. "
        "Stop all work; do not build, upload or edit."
    ),
}


def state_dir(arg: str | None = None) -> Path:
    if arg:
        return Path(arg)
    if os.environ.get("JAM_CLOCK_DIR"):
        return Path(os.environ["JAM_CLOCK_DIR"])
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "megajam-jam-clock"


def parse_deadline(text: str) -> datetime:
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("deadline needs a timezone offset, e.g. 2026-11-15T20:59:00-05:00")
    return dt.astimezone(timezone.utc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def write_deadline(sdir: Path, deadline: datetime) -> None:
    sdir.mkdir(parents=True, exist_ok=True)
    try:
        if read_deadline(sdir) == deadline:
            return  # same deadline (daemon restart): keep markers, so no repeat nudges
    except (OSError, ValueError):
        pass
    # Atomic: a concurrent reader sees the old file or the new one, never an empty one.
    tmp = sdir / f"deadline.{os.getpid()}.tmp"
    tmp.write_text(json.dumps({"deadline": deadline.isoformat()}) + "\n")
    os.replace(tmp, sdir / "deadline.json")
    # A new deadline means a new run: old markers would mislead. Clear them only after the
    # new deadline is in place.
    for name in MARKERS:
        (sdir / name).unlink(missing_ok=True)


def read_deadline(sdir: Path) -> datetime:
    f = sdir / "deadline.json"
    if not f.exists():
        raise FileNotFoundError(f"no deadline set in {sdir}; run `jam_clock.py start` first")
    try:
        return parse_deadline(json.loads(f.read_text())["deadline"])
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError) as e:
        raise ValueError(f"bad deadline.json in {sdir}: {e!r}") from e


def phase(left: timedelta) -> str:
    mins = left.total_seconds() / 60
    if mins <= 0:
        return "EXPIRED"
    if mins <= FINAL_MIN:
        return "FINAL"
    if mins <= PACKAGE_MIN:
        return "PACKAGE"
    return "WORK"


def fmt_left(left: timedelta) -> str:
    secs = int(left.total_seconds())
    sign = "-" if secs < 0 else ""
    secs = abs(secs)
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    parts = ([f"{d}d"] if d else []) + [f"{h:02d}h", f"{m:02d}m", f"{s:02d}s"]
    return sign + " ".join(parts)


def status_line(sdir: Path, now: datetime | None = None) -> str:
    now = now or _now()
    deadline = read_deadline(sdir)
    left = deadline - now
    marks = [n for n in MARKERS if (sdir / n).exists()]
    return (f"{phase(left)}  time left {fmt_left(left)}  deadline {deadline.isoformat()}"
            f"  markers: {','.join(marks) or 'none'}")


def run_nudge(cmd: str | None, message: str, runner=subprocess.run) -> bool:
    if not cmd:
        return False
    try:
        r = runner(cmd, shell=True, input=message, text=True, timeout=60,
                   env={**os.environ, "JAM_CLOCK_MESSAGE": message},
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _mark(sdir: Path, name: str, left: timedelta, now: datetime, cmd, runner) -> None:
    path = sdir / name
    if path.exists():
        return
    msg = MESSAGES[name].format(m=max(0, int(left.total_seconds() // 60)))
    body = {"marker": name, "written_at": now.isoformat(), "message": msg, "nudged": False}
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(body, indent=2) + "\n")
    try:
        os.link(tmp, path)  # exclusive create: one concurrent ticker wins, and only it nudges
    except FileExistsError:
        return
    finally:
        tmp.unlink(missing_ok=True)
    if run_nudge(cmd, msg, runner):
        body["nudged"] = True
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(body, indent=2) + "\n")
        tmp.replace(path)


def tick(sdir: Path, now: datetime | None = None, nudge_cmd: str | None = None,
         runner=None, deadline: datetime | None = None) -> str:
    """Evaluate once. Writes any marker now due (idempotent). Returns the phase."""
    now = now or _now()
    runner = runner or subprocess.run
    left = (deadline or read_deadline(sdir)) - now
    p = phase(left)
    # Late start (or late tick) still writes every marker that is due, earliest first.
    # The package order is stale once FINAL starts (no new builds), so it is never issued late.
    if p == "PACKAGE":
        _mark(sdir, "FORCE_PACKAGE", left, now, nudge_cmd, runner)
    if p == "FINAL":
        _mark(sdir, "FINAL", left, now, nudge_cmd, runner)
    if p == "EXPIRED":  # after the deadline the FINAL leave-to-edit is void too
        _mark(sdir, "EXPIRED", left, now, nudge_cmd, runner)
    return p


def check_code(sdir: Path, now: datetime | None = None) -> int:
    """Exit code for polling agents. Based on the clock, not only on marker files."""
    p = phase(read_deadline(sdir) - (now or _now()))
    return {"WORK": EXIT_OK, "PACKAGE": EXIT_PACKAGE, "FINAL": EXIT_FINAL,
            "EXPIRED": EXIT_EXPIRED}[p]


def loop(sdir: Path, nudge_cmd, interval: float, now_fn=_now, sleep=time.sleep) -> None:
    last = None  # last good deadline: a half-written deadline.json must not kill the daemon
    while True:
        try:
            last = read_deadline(sdir)
        except (OSError, ValueError):
            if last is None:
                sleep(interval)
                continue
        p = tick(sdir, now_fn(), nudge_cmd, deadline=last)
        if p == "EXPIRED":
            return
        sleep(interval)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--state-dir", help="default: $JAM_CLOCK_DIR or ~/.local/state/megajam-jam-clock")
    sub = ap.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("start", help="set the deadline and run the loop")
    st.add_argument("--deadline", default=None,
                    help="ISO time with offset; default: keep the existing one, else the contest close")
    st.add_argument("--nudge-cmd", default=os.environ.get("JAM_CLOCK_NUDGE_CMD"))
    st.add_argument("--interval", type=float, default=30.0, help="seconds between ticks")
    st.add_argument("--no-loop", action="store_true", help="set the deadline and tick once")
    tk = sub.add_parser("tick", help="evaluate once")
    tk.add_argument("--nudge-cmd", default=os.environ.get("JAM_CLOCK_NUDGE_CMD"))
    sub.add_parser("status", help="print time left")
    sub.add_parser("check", help="exit 0 ok / 10 package / 11 final / 12 expired")
    a = ap.parse_args(argv)
    sdir = state_dir(a.state_dir)
    try:
        if a.cmd == "start":
            if a.deadline:
                write_deadline(sdir, parse_deadline(a.deadline))
            else:
                try:
                    old = read_deadline(sdir)  # restart: keep what is already set...
                    age = _now() - old
                    if age > STALE_AFTER:  # ...unless it is long dead (a finished mock)
                        print(f"jam_clock: stored deadline {old.isoformat()} ended "
                              f"{fmt_left(age)} ago; replacing it with the contest close",
                              file=sys.stderr)
                        write_deadline(sdir, parse_deadline(DEFAULT_DEADLINE))
                    elif age >= timedelta(0):
                        # Just passed: this is a restart of the same run. Never revive or
                        # replace it silently; `check` keeps saying stop.
                        # Leave the state dir right even with no daemon running: write the
                        # EXPIRED marker (and nudge once) before refusing.
                        tick(sdir, nudge_cmd=a.nudge_cmd)
                        print(f"jam_clock: deadline {old.isoformat()} passed; "
                              f"pass --deadline to start a new run", file=sys.stderr)
                        return 2
                except (FileNotFoundError, ValueError):
                    write_deadline(sdir, parse_deadline(DEFAULT_DEADLINE))
            print(status_line(sdir))
            if a.no_loop:
                tick(sdir, nudge_cmd=a.nudge_cmd)
            else:
                loop(sdir, a.nudge_cmd, a.interval)
            print(status_line(sdir))
        elif a.cmd == "tick":
            tick(sdir, nudge_cmd=a.nudge_cmd)
            print(status_line(sdir))
        elif a.cmd == "status":
            print(status_line(sdir))
        elif a.cmd == "check":
            code = check_code(sdir)
            print({0: "OK", 10: "FORCE_PACKAGE", 11: "FINAL", 12: "EXPIRED"}[code])
            return code
    except (FileNotFoundError, ValueError) as e:
        print(f"jam_clock: {e}", file=sys.stderr)
        if a.cmd == "check":
            print("EXPIRED (clock unreadable: STOP)")
            return EXIT_EXPIRED  # fail closed: an unreadable clock is never "keep working"
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
