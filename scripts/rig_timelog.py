#!/usr/bin/env python3
"""Stopwatch for the timed rig run: one mark per finished step, a markdown table at the end. Standard library only.

  rig_timelog.py LOG start                       # first mark (time zero)
  rig_timelog.py LOG mark "A3 retarget anims" [--note "bone scale 100x"]   # step finished now
  rig_timelog.py LOG table                       # markdown: step, minutes since the previous mark, cumulative

LOG is a JSON-lines file kept OUTSIDE the repo (for example $CLAUDE_JOB_DIR/tmp/rig/timelog.jsonl). Each mark
stores the wall clock, so the table shows the real time between steps, waiting included. Use `--at ISO` to
back-date a mark you forgot (UTC or with offset).
"""
import argparse
import datetime
import json
import sys
from pathlib import Path


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def parse_time(text):
    t = datetime.datetime.fromisoformat(text)
    return t if t.tzinfo else t.replace(tzinfo=datetime.timezone.utc)


def read_marks(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def add_mark(path, label, note="", at=None):
    """Insert a mark in time order (a back-dated mark lands between earlier ones). The start mark stays first."""
    marks = read_marks(path)
    t = at or now()
    if marks and t < parse_time(marks[0]["at"]):
        raise ValueError("mark is earlier than the start mark")
    marks.append({"at": t.isoformat(), "label": label, "note": note})
    marks.sort(key=lambda m: parse_time(m["at"]))  # stable: equal times keep insertion order
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("".join(json.dumps(m) + "\n" for m in marks), encoding="utf-8")


def render_table(marks):
    """Markdown table; the first mark is time zero and gets no row of its own."""
    if len(marks) < 2:
        return "(need a start mark and at least one step mark)"
    rows = ["| Step | Minutes | Cumulative | Note |", "|---|---|---|---|"]
    t0 = prev = parse_time(marks[0]["at"])
    for m in marks[1:]:
        t = parse_time(m["at"])
        label, note = (str(m.get(k, "")).replace("|", "\\|") for k in ("label", "note"))
        rows.append(f"| {label} | {(t - prev).total_seconds() / 60:.1f} | "
                    f"{(t - t0).total_seconds() / 60:.1f} | {note} |")
        prev = t
    rows.append(f"| **Total** | **{(prev - t0).total_seconds() / 60:.1f}** | | |")
    return "\n".join(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("log")
    ap.add_argument("action", choices=["start", "mark", "table"])
    ap.add_argument("label", nargs="?")
    ap.add_argument("--note", default="")
    ap.add_argument("--at", help="ISO time to use instead of now")
    args = ap.parse_args(argv)
    try:
        if args.action == "start":
            if read_marks(args.log):
                print("log already started; use a new file", file=sys.stderr)
                return 2
            add_mark(args.log, "start", at=parse_time(args.at) if args.at else None)
        elif args.action == "mark":
            if not args.label:
                print("mark needs a label", file=sys.stderr)
                return 2
            if not read_marks(args.log):
                print("run start first", file=sys.stderr)
                return 2
            add_mark(args.log, args.label, args.note, parse_time(args.at) if args.at else None)
        else:
            print(render_table(read_marks(args.log)))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
