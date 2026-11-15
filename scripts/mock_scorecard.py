#!/usr/bin/env python3
"""Mock-jam scorecard: one row per mock, filled from that mock's evidence (stages/00_prep/references/mock-scorecard.md).

  mock_scorecard.py --mock 10 --data stages/00_prep/output/mock-scorecard-10.json --findings stages/00_prep/output/mock-jam-findings-10.md \\
      --update stages/00_prep/references/mock-scorecard.md
  mock_scorecard.py --mock 11 --repo ~/Projects/megajam-mock --findings stages/00_prep/output/mock-jam-findings-11.md \\
      --step-shots work/step-shots --playtest work/playtest --assets work/assets \\
      --butler-log work/butler.log --agent-gate work/agent-gate.txt --data stages/00_prep/output/mock-scorecard-11.json

Evidence read (each optional; a missing source shows as n/a, never as a pass):
  --repo         git log of the mock repo: first packaging commit INSIDE kickoff..hard stop (the repo is shared
                 by all mocks; commits outside the window are ignored; needs kickoff + hard stop)
  --findings     stages/00_prep/output/mock-jam-findings-N.md: "Start:" and "Hard stop:" lines (PT) = kickoff and hard stop
  --step-shots   <dir>/steps.md from step_shot.py: pass = every verdict starts with OK/PASS/GOOD;
                 a verdict starting FAIL*/BAD/BROKEN = fail; anything else (incl. pending) = n/a
  --assets       preview.json files (asset_preview.py), searched recursively: pass = every "ok" is true
  --playtest     <dir> from visual_playtest.py. With checklist.md present, `visual_playtest.verify` decides
                 (human verdicts and overrides count; a run-wide verify failure = fail, motion n/a);
                 without it only auto results exist: shown as "pass (auto only)" / fail / n/a, never as a human pass.
                 The "motion" item is the clip motion check.
  --butler-log   text with an ISO timestamp at the start of lines; first "push" line at/after kickoff = packaged
  --agent-gate   saved output of `agent_playtest_cli.py gate`: "GATE PASS" / "GATE FAIL"
  --data         JSON of HAND-ENTERED facts, which also override anything derived. Keys:
                 kickoff, hard_stop, first_packaged_at, first_playable_packaged_at (ISO with offset),
                 props_real, props_primitive (ints), agent_won_by_real_play (true/false),
                 bugs_missed (list of strings), overran (true/false/yes/no; null or absent = n/a, never guessed from git), gates (name -> pass|fail|n/a), notes.

Output: a markdown table row on stdout, or --update FILE replaces/appends that mock's row between the
`<!-- rows:start -->` and `<!-- rows:end -->` markers. --json prints the row as JSON instead.
Standard library only. Exit 0 ok, 2 usage/input error.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    PT = ZoneInfo("America/Los_Angeles")
except Exception:  # pragma: no cover - no tz database
    PT = None

GATES = ("step_shots", "asset_previews", "playtest", "clip_motion", "agent_playtester")
GATE_TITLES = {"step_shots": "Step shots", "asset_previews": "Asset previews", "playtest": "Playtest",
               "clip_motion": "Clip motion", "agent_playtester": "Agent playtester"}
START_MARK, END_MARK = "<!-- rows:start -->", "<!-- rows:end -->"
# Narrow on purpose: "add package.json", "fix packaging script", "nothing shipped yet" are not builds.
PACKAGE_RE = re.compile(r"\b(packaged build|package[ -]build|package[ -]and[ -]push|butler push)\b", re.I)
# A butler log line counts as a real upload only with a success word and no failure word.
PUSH_OK_RE = re.compile(r"\b(ok|success|succeeded|finished|done|live|complete|completed|processing)\b", re.I)
PUSH_BAD_RE = re.compile(r"\b(fail|failed|failure|error|errors|invalid|denied|unauthori[sz]ed|refused|cancel\w*|abort\w*)\b|\([45]\d\d\)|\b(?:http|status|code)\D{0,3}[45]\d\d\b", re.I)
# visual_playtest.analyze() never auto-judges these; only a person reading checklist.md does.
HUMAN_ONLY = {"objects", "endscreen"}
AUTO_ONLY = "auto only, no human look"
STAMP_RE = re.compile(r"^\W*(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}(?::\d{2})?)(Z|[+-]\d{2}:?\d{2})?")
ROW_COLS = ["Mock", "Kickoff to first packaged", "Kickoff to first playable packaged"] + \
    [GATE_TITLES[g] for g in GATES] + ["Real props / primitives", "Won by real play", "Bugs gates missed", "Overran", "Notes"]


def parse_when(text, default_tz=PT):
    """ISO string (with or without offset; no offset = Pacific) -> aware datetime, or None."""
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(str(text).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None and default_tz is not None:
        dt = dt.replace(tzinfo=default_tz)
    # Fixed offset (the log's own, or Pacific's offset at that instant) instead of a ZoneInfo: datetimes that
    # share one ZoneInfo object subtract by wall clock, an hour off across the DST change, while fixed
    # offsets that differ subtract by real time. The written offset is kept for display.
    return dt.astimezone(timezone(dt.utcoffset())) if dt.tzinfo else dt


def parse_strict(text, name):
    """Hand-entered time: None/empty = not entered; a value that does not parse is an error, not n/a."""
    if text in (None, ""):
        return None
    dt = parse_when(text)
    if dt is None:
        raise ValueError(f"data.{name}: {text!r} is not an ISO time like 2026-11-07T22:55:00-08:00")
    return dt


def local(dt):
    """Pacific ISO string for display (stored times are UTC)."""
    return dt.astimezone(PT).isoformat() if dt and PT else (dt.isoformat() if dt else None)


def fmt_delta(start, end):
    if not start or not end:
        return "n/a"
    secs = (end - start).total_seconds()
    if secs < 0:
        return "n/a (before kickoff)"
    h, m = divmod(int(secs // 60), 60)
    return f"{h} h {m:02d} min"


def read_findings_times(path):
    """Start / Hard stop lines like 'Start: Sat 2026-11-07 21:02 PT.' -> (kickoff, hard_stop)."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return None, None

    def grab(label):
        m = re.search(rf"{label}:\s*(?:\w+\s+)?(\d{{4}}-\d{{2}}-\d{{2}})\s+(\d{{2}}:\d{{2}})", text, re.I)
        return parse_when(f"{m.group(1)}T{m.group(2)}") if m else None
    return grab("Start"), grab("Hard stop")


def git_first_packaged(repo, kick, stop):
    """Earliest packaging commit inside [kickoff, hard stop], or None. The mock repo is reused for every
    mock, so commits outside that window belong to other mocks and are ignored. (Overran is therefore
    never derived from git: a commit after the stop may be the next mock's. Enter it by hand.)"""
    if not kick or not stop:
        return None
    try:
        out = subprocess.run(["git", "-C", str(repo), "log", "--format=%aI%x09%s"], capture_output=True,
                             text=True, timeout=30, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    pk = []
    for line in out.splitlines():
        when, _, subj = line.partition("\t")
        dt = parse_when(when)
        if dt and PACKAGE_RE.search(subj) and kick <= dt <= stop:
            pk.append(dt)
    return min(pk) if pk else None


def tri(value, name):
    """Hand-entered yes/no: None stays None (n/a); real bools and clear yes/no words only."""
    if value is None or isinstance(value, bool):
        return value
    word = str(value).strip().lower()
    if word in ("true", "yes", "y", "1"):
        return True
    if word in ("false", "no", "n", "0"):
        return False
    raise ValueError(f"data.{name}: {value!r} is not true/false/yes/no/null")


def butler_first_push(path, kick=None, stop=None):
    """Earliest SUCCESSFUL 'push' line inside [kickoff, hard stop] (the log may also hold other mocks).
    A line needs a success word (ok, finished, live, processing ...) and no failure word (failed, error,
    invalid, 401 ...)."""
    try:
        lines = Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return None
    best = None
    for line in lines:
        m = STAMP_RE.match(line)
        if m and re.search(r"push", line, re.I) and PUSH_OK_RE.search(line) and not PUSH_BAD_RE.search(line):
            dt = parse_when(f"{m.group(1)}T{m.group(2)}{m.group(3) or ''}")
            if dt and (kick is None or dt >= kick) and (stop is None or dt <= stop) and (best is None or dt < best):
                best = dt
    return best


def gate_step_shots(directory):
    p = Path(directory) / "steps.md"
    if not p.is_file():
        return "n/a", "no steps.md"
    rows = []
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        m = re.match(r"^\| (\d{2,}) \| (.*?) \| (.*?) \| (.*) \|$", line)
        if m:
            rows.append(m.group(4).strip())
    if not rows:
        return "n/a", "no step rows"
    # Verdicts are free text, so a pass must be said: start the verdict with OK/PASS/GOOD. FAIL*/BAD/BROKEN
    # (whole words; FAILED counts) is a fail; anything else (incl. "(pending)") was not judged ok.
    # The OK word must stand alone (space, ':' or end), so "Pass-through bug" / "OK-ish" do not count, and
    # a verdict that also names a failure ("Good grief, broken") is not a pass either.
    fail_word = re.compile(r"\b(fail\w*|bad|broken|bug|wrong)\b", re.I)
    good = [v for v in rows if re.match(r"(ok|pass|good)(?=[\s:]|$)", v, re.I) and not fail_word.search(v)]
    bad = [v for v in rows if re.match(r"(fail\w*|bad|broken)\b", v, re.I)]
    detail = f"{len(good)}/{len(rows)} shots judged ok"
    if bad:
        return "fail", detail
    return ("pass" if len(good) == len(rows) else "n/a"), detail + ("" if len(good) == len(rows) else " (rest not judged OK/FAIL)")


def gate_assets(directory):
    files = sorted(Path(directory).rglob("*preview.json")) if Path(directory).is_dir() else []
    if not files:
        return "n/a", "no preview.json"
    ok = 0
    for f in files:
        try:
            ok += bool(json.loads(f.read_text(encoding="utf-8-sig")).get("ok"))
        except (ValueError, OSError):
            pass
    return ("pass" if ok == len(files) else "fail"), f"{ok}/{len(files)} previews ok"


def gate_playtest(directory):
    """(playtest state, motion state) from results.json items."""
    p = Path(directory) / "results.json"
    try:
        items = json.loads(p.read_text(encoding="utf-8-sig"))["items"]
    except (OSError, ValueError, KeyError, TypeError):
        return ("n/a", "no results.json"), ("n/a", "no results.json")

    motion = [i for i in items if i.get("id") == "motion"]
    rest = [i for i in items if i not in motion]

    # With a filled-in checklist.md the real gate (visual_playtest.verify) decides, human verdicts and
    # overrides included. The column must show what that gate decided.
    if (Path(directory) / "checklist.md").is_file():
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import visual_playtest as vp
            ok, problems = vp.verify(directory)
        except Exception as e:  # unreadable gate = not a pass
            return ("n/a", f"verify unavailable: {e}"), ("n/a", "verify unavailable")
        if ok:
            return ("pass", "visual_playtest verify passed"), ("pass", "verify passed")
        # Item problems read "<N>. <item title>: Verdict is ..." (titles may hold colons, so match whole).
        # Anything else is run-wide (changed frame, run id mismatch, edited headings): nothing can be
        # trusted, so playtest fails and motion is n/a, never a pass.
        # Step-review problems read "Step NN: ..." (one per unresolved frame verdict): also per-item, not run-wide.
        item_probs = [pr for pr in problems if re.match(r"(\d+\. |Step \d+: )", pr)]
        if len(item_probs) != len(problems):
            return ("fail", f"verify: run-wide problem: {problems[0][:80]}"), ("n/a", "verify run-wide problem")
        # The motion item is found by id in the run's own results.json (its position = the checklist number),
        # not by the current tool's title: an older run or reworded heading must not hide a motion fail.
        ids = [i.get("id") for i in items]
        mnum = f"{ids.index('motion') + 1}. " if "motion" in ids else None
        m_bad = mnum is not None and any(pr.startswith(mnum) for pr in item_probs)
        r_bad = any(mnum is None or not pr.startswith(mnum) for pr in item_probs)
        return (("fail" if r_bad else "pass"), f"verify: {len(problems)} problem(s)"), \
            (("fail" if m_bad else "pass"), "verify motion item")

    # No checklist.md: nobody has looked at the frames. Every auto-judged item PASS/WARN is "pass", but the
    # detail says AUTO_ONLY and render_row shows "pass (auto only)" so it is never read as a human pass.
    def state(its):
        autos = [str(i.get("auto", "")).upper() for i in its if i.get("id") not in HUMAN_ONLY]
        if not autos:
            return "n/a"
        if "FAIL" in autos:
            return "fail"
        return "pass" if all(x in ("PASS", "WARN") for x in autos) else "n/a"
    ps, ms = state(rest), state(motion)
    return (ps, f"{len(rest)} items, {AUTO_ONLY}"), (ms, f"motion item, {AUTO_ONLY}" if motion else "no motion item")


def gate_agent(path):
    try:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return "n/a", "no gate output"
    if "GATE PASS" in text:
        return "pass", "win/lose/restart evidenced"
    if "GATE FAIL" in text:
        return "fail", "gate failed"
    return "n/a", "unrecognised gate output"


def build_row(mock, args_ns):
    """Collect evidence + hand-entered data into one row dict."""
    a = args_ns
    data = {}
    if a.data:
        data = json.loads(Path(a.data).read_text(encoding="utf-8-sig"))
    kick, stop = read_findings_times(a.findings) if a.findings else (None, None)
    kick = parse_strict(data.get("kickoff"), "kickoff") or kick
    stop = parse_strict(data.get("hard_stop"), "hard_stop") or stop
    pk_commit = git_first_packaged(a.repo, kick, stop) if a.repo else None
    pk_butler = butler_first_push(a.butler_log, kick, stop) if a.butler_log else None
    pk_candidates = [d for d in (pk_butler, pk_commit) if d]
    first_pk = parse_strict(data.get("first_packaged_at"), "first_packaged_at") or \
        (min(pk_candidates) if pk_candidates else None)
    first_playable = parse_strict(data.get("first_playable_packaged_at"), "first_playable_packaged_at")
    bugs = data.get("bugs_missed")
    if bugs is None:
        bugs = []
    if not isinstance(bugs, list) or not all(isinstance(b, str) for b in bugs):
        raise ValueError("data.bugs_missed: must be a list of strings")
    gates, details = {g: "n/a" for g in GATES}, {}
    for g, res in (("step_shots", gate_step_shots(a.step_shots) if a.step_shots else None),
                   ("asset_previews", gate_assets(a.assets) if a.assets else None),
                   ("agent_playtester", gate_agent(a.agent_gate) if a.agent_gate else None)):
        if res:
            gates[g], details[g] = res
    if a.playtest:
        (gates["playtest"], details["playtest"]), (gates["clip_motion"], details["clip_motion"]) = gate_playtest(a.playtest)
    for g, v in (data.get("gates") or {}).items():
        if g not in GATES or v not in ("pass", "fail", "n/a"):
            raise ValueError(f"data.gates: bad entry {g!r}: {v!r}")
        gates[g] = v
        details[g] = "hand-entered"  # replaces any derived note (e.g. "auto only") so it is not mislabelled
    overran = tri(data.get("overran"), "overran")
    won = tri(data.get("agent_won_by_real_play"), "agent_won_by_real_play")
    return {
        "mock": mock,
        "kickoff": local(kick),
        "hard_stop": local(stop),
        "to_first_packaged": fmt_delta(kick, first_pk),
        "to_first_playable_packaged": fmt_delta(kick, first_playable),
        "gates": gates, "gate_details": details,
        "props_real": data.get("props_real"), "props_primitive": data.get("props_primitive"),
        "agent_won_by_real_play": won,
        "bugs_missed": bugs,
        "overran": overran, "notes": data.get("notes", ""),
    }


def yn(v):
    return "n/a" if v is None else ("yes" if v else "no")


def cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def render_row(row):
    props = "n/a" if row["props_real"] is None or row["props_primitive"] is None \
        else f"{row['props_real']} / {row['props_primitive']}"
    bugs = "none entered" if not row["bugs_missed"] else "; ".join(f"{i}. {b}" for i, b in enumerate(row["bugs_missed"], 1))
    cells = [f"Mock {row['mock']}", row["to_first_packaged"], row["to_first_playable_packaged"]] + \
        [row["gates"][g] + (" (auto only)" if row["gates"][g] == "pass" and AUTO_ONLY in row["gate_details"].get(g, "")
                            else "") for g in GATES] + [props, yn(row["agent_won_by_real_play"]), bugs, yn(row["overran"]), row["notes"]]
    return "| " + " | ".join(cell(c) for c in cells) + " |"


def header():
    return "| " + " | ".join(ROW_COLS) + " |\n|" + "---|" * len(ROW_COLS)


def update_file(path, row):
    """Replace this mock's row (or append) between the markers. Raises ValueError if markers are missing."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if START_MARK not in text or END_MARK not in text or text.index(START_MARK) > text.index(END_MARK):
        raise ValueError(f"{path} needs {START_MARK} ... {END_MARK}")
    head, rest = text.split(START_MARK, 1)
    body, tail = rest.split(END_MARK, 1)
    prefix = f"| Mock {row['mock']} |"
    lines = [l for l in body.strip("\n").splitlines() if l.strip()]
    new = render_row(row)
    for i, l in enumerate(lines):
        if l.startswith(prefix):
            lines[i] = new
            break
    else:
        lines.append(new)
    if not lines or not lines[0].startswith("| Mock |"):
        lines = header().splitlines() + [l for l in lines if l.startswith("| Mock ")]

    def key(l):
        m = re.match(r"\| Mock (\d+) \|", l)
        return int(m.group(1)) if m else -1
    lines = lines[:2] + sorted(lines[2:], key=key)
    p.write_text(head + START_MARK + "\n" + "\n".join(lines) + "\n" + END_MARK + tail, encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fill one mock-jam scorecard row from the mock's evidence.")
    ap.add_argument("--mock", type=int, required=True)
    for opt in ("repo", "findings", "step-shots", "assets", "playtest", "butler-log", "agent-gate", "data", "update"):
        ap.add_argument(f"--{opt}", default=None)
    ap.add_argument("--json", action="store_true", help="print the row as JSON")
    a = ap.parse_args(argv)
    try:
        row = build_row(a.mock, a)
        if a.update:
            update_file(a.update, row)
            print(f"updated {a.update} (mock {a.mock})")
        elif a.json:
            print(json.dumps(row, indent=2))
        else:
            print(render_row(row))
    except (OSError, ValueError) as e:
        print(f"mock_scorecard: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
