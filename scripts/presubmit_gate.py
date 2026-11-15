#!/usr/bin/env python3
"""Pre-submit gate: fail if any visible actor still shows a default grid or checker material.

Reads the output of scripts/ue_verify_level.py (the VERIFY_ACTOR_JSON= lines) from a file or stdin. It does not
talk to the editor. Standard library only.

  presubmit_gate.py LOGFILE            # or '-' for stdin
  presubmit_gate.py LOGFILE --json     # machine-readable result

Exit: 0 pass, 1 at least one visible actor on a default material, 2 no actor records found (cannot judge) or
bad usage. "No records" is never a pass: an empty log means the verify run failed, not that the level is clean.

Why: mock jam 10 shipped a grey checker floor. A video claims Epic screens such entries out; the official rules
digest says nothing of the sort (see _config/reference/canon/jam-agent-lint-rules.md), so this is a quality gate, not a rule gate.
The material markers are UNTESTED against real engine paths until the verify run is done in the editor.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Importing off-editor is safe: ue_verify_level only runs main() when `unreal` imports.
import ue_verify_level  # noqa: E402

PREFIX = "VERIFY_ACTOR_JSON="


def parse_records(text):
    """Records from VERIFY_ACTOR_JSON= lines. The marker may follow any prefix (UE writes
    '[2026.11.09-19.13.42:749][  0]LogPython: ')."""
    recs = []
    for line in text.splitlines():
        i = line.find(PREFIX)
        if i >= 0:
            try:
                rec = json.loads(line[i + len(PREFIX):].strip())
            except ValueError:
                continue
            if isinstance(rec, dict) and "label" in rec:
                recs.append(rec)
    return recs


def expected_count(text):
    """(count or None, done?) from the VERIFY_ACTOR_COUNT= and VERIFY_DONE lines, prefix-tolerant."""
    m = re.search(r"VERIFY_ACTOR_COUNT=(\d+)", text)
    done = re.search(r"VERIFY_DONE\s*$", text, re.M) is not None
    return (int(m.group(1)) if m else None), done


def check(records):
    """Return [(label, material_path)] for every visible actor on a default material."""
    bad = []
    for r in records:
        if r.get("visible", True) is False:
            continue
        for m in ue_verify_level.default_material_hits(r):
            bad.append((r["label"], m))
    return bad


def run(text, as_json=False, out=None):
    out = out or sys.stdout
    records = parse_records(text)
    if not records:
        print("GATE_ERROR no VERIFY_ACTOR_JSON lines found: run ue_verify_level.py in the editor first", file=out)
        return 2
    want, done = expected_count(text)
    if not done or want is None or want != len(records):
        print(f"GATE_ERROR incomplete log: VERIFY_DONE={'yes' if done else 'no'} expected={want} "
              f"records={len(records)}; re-run the verify (a cut log could hide the bad actor)", file=out)
        return 2
    bad = check(records)
    if as_json:
        print(json.dumps({"actors": len(records), "pass": not bad,
                          "violations": [{"label": a, "material": m} for a, m in bad]}), file=out)
    else:
        for label, mat in bad:
            print(f"GATE_FAIL {label} shows default material {mat}", file=out)
        print(f"GATE_{'FAIL' if bad else 'PASS'} actors={len(records)} violations={len(bad)}", file=out)
    return 1 if bad else 0


def main(argv):
    args = [a for a in argv if a != "--json"]
    if len(args) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    try:
        if args[0] == "-":
            text = sys.stdin.read()
        else:
            with open(args[0], encoding="utf-8", errors="replace") as fh:
                text = fh.read()
    except OSError as e:
        print(f"GATE_ERROR cannot read {args[0]}: {e}", file=sys.stderr)
        return 2
    return run(text, as_json="--json" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
