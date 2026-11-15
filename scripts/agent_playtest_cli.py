#!/usr/bin/env python3
"""Closed-loop playtester: small commands an agent calls turn by turn on the packaged build on the
Legion (real OS input, real screen capture), the way a human QA tester plays. See stages/03_playtest/references/agent-playtest.md.

  start  --remote-zip Z --game-name G   deploy + launch the build, open a session folder
  look   [--label L]                    screenshot -> prints the PNG path (Read it, then decide)
  press  KEYS [--hold S] [--gap S] [--together]   real key presses ("w", "w,a", "space"; --together holds them at once); then a look frame
  mouse  --click left|right [--x --y] | --move DX DY      real mouse input; then a look frame
  clip   SECONDS                        OBS video of the live game -> prints the mp4 path
  state  [--lines N]                    tail of the game log
  mark   win|lose|restart --evidence F [F...] [--note T]   claim a milestone, with the frames/clips
  gate   [--report FILE]                exit 0 only if win AND lose AND restart are evidenced by real play
  stop                                  close the game (and OBS if we started it)

Session folder: --session DIR or $AGENT_PLAYTEST_DIR (default ./playtest-session). Every command appends a
line to DIR/journal.jsonl; `gate` reads only that journal and the files it points at.

HONEST LIMIT: the gate proves a trail exists (real input was sent, frames/clips were captured after it,
the agent marked win, lose and restart with files that exist and were captured in this session). It cannot
see whether a frame really shows a win. The agent states that in the report; the human still reads it.

Each command is one ssh round trip or more (~10-20 s for look/press): this is a turn-by-turn tool.
Never run from a ticket worker: the hub runs it on the real Legion.
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return mod


vp = _load("visual_playtest")
SESSION_FILE = "session.json"
JOURNAL = "journal.jsonl"
MILESTONES = ("win", "lose", "restart")
REPORT_SECTIONS = ("Verdict", "Win", "Lose", "Restart", "Edges", "Confusing", "Stuck", "Glitches", "Fun score", "Clarity score")
LOG_TAIL_DEFAULT = 40


def log(msg):
    print(msg, file=sys.stderr)


class Session:
    """A folder holding session.json (what we are playing) and journal.jsonl (everything we did)."""

    def __init__(self, root, now=time.time):
        self.root = Path(root)
        self.now = now

    def init(self, **cfg):
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / SESSION_FILE).write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        (self.root / JOURNAL).write_text("", encoding="utf-8")

    def archive(self, stamp):
        """Move journal, frames and clips into archive-<stamp>/ so a fresh start never reuses file names."""
        dest = self.root / f"archive-{stamp}"
        dest.mkdir(parents=True, exist_ok=True)
        for name in (JOURNAL, SESSION_FILE, "frames", "clips"):
            if (self.root / name).exists():
                (self.root / name).rename(dest / name)

    @property
    def cfg(self):
        p = self.root / SESSION_FILE
        if not p.exists():
            raise RuntimeError(f"no session in {self.root}; run `start` first")
        return json.loads(p.read_text(encoding="utf-8"))

    def update(self, **kv):
        cfg = self.cfg
        cfg.update(kv)
        (self.root / SESSION_FILE).write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    def append(self, kind, **fields):
        entry = {"t": round(self.now(), 2), "kind": kind, **fields}
        with open(self.root / JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def entries(self):
        p = self.root / JOURNAL
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

    def next_shot_name(self, label):
        n = sum(1 for e in self.entries() if e["kind"] in ("look", "press", "mouse")) + 1
        return f"{n:03d}_{label}"


# ---------- steps ----------

def parse_keys(text):
    keys = [k.strip().lower() for k in re.split(r"[,\s]+", text) if k.strip()]
    if not keys:
        raise ValueError("no keys given")
    bad = [k for k in keys if k not in vp.KEYS]
    if bad:
        raise ValueError(f"unknown key(s) {' '.join(bad)}; use one of {' '.join(sorted(vp.KEYS))}")
    return keys


def clean_label(label):
    label = re.sub(r"[^A-Za-z0-9_-]+", "-", label or "look").strip("-")
    return label or "look"


def key_steps(keys, hold, gap, together=False):
    """Keys one after another, or (together=True) all held at once in one step (steer while holding space)."""
    if not 0 < hold <= 10:
        raise ValueError("--hold must be above 0 and at most 10 seconds")
    if together:
        if len(keys) < 2 or len(set(keys)) != len(keys):
            raise ValueError("--together needs two or more different keys, e.g. space,d")
        return [{"op": "key", "keys": list(keys), "hold": hold}]
    steps = []
    for i, k in enumerate(keys):
        if i and gap:
            steps.append({"op": "wait", "seconds": gap})
        steps.append({"op": "key", "key": k, "hold": hold})
    return steps


def run_steps(sess, backend, steps, label, kind, extra=None):
    """Run steps on the Legion (input first, then one capture) and return the fetched PNG path."""
    name = sess.next_shot_name(clean_label(label))
    full = list(steps) + [{"op": "wait", "seconds": 0.4}, {"op": "shot", "label": name}]
    frames = sess.root / "frames"
    before = set(frames.glob("*.png")) if frames.exists() else set()
    backend.play(full, frames)
    new = sorted(set(frames.glob("*.png")) - before)
    if not new:
        raise RuntimeError("the Legion run finished but returned no frame")
    png = new[-1]
    fg = None
    mf = frames / "manifest.json"
    if mf.exists():
        try:
            data = vp.normalize_manifest(json.loads(mf.read_text(encoding="utf-8-sig")))
            fg = bool(data[-1].get("foreground")) if data else None
        except (ValueError, KeyError, IndexError, TypeError):
            fg = None
    sess.append(kind, file=str(png.relative_to(sess.root)), steps=steps, game_in_front=fg, **(extra or {}))
    return png, fg


def backend_for(sess, make=None):
    cfg = sess.cfg
    make = make or vp.LegionBackend
    b = make(cfg["host"], cfg["remote_zip"], cfg["game_name"], cfg.get("task_name", "MegaJamLaunchGame"))
    # Lock / black-screen probe on launch, as in visual_playtest run (mock jam 11 gaps 14, 15, 21).
    b.probe = lambda: vp.legion_probe(cfg["host"])
    return b


# ---------- commands ----------

def cmd_start(a, sess, make=None, record_mod=None):
    cfg = dict(host=a.host, remote_zip=a.remote_zip, game_name=a.game_name, task_name=a.task_name)
    has_history = bool(sess.entries())
    relaunch = has_history and not a.fresh
    if relaunch:
        old = sess.cfg
        if (old.get("remote_zip"), old.get("game_name")) != (a.remote_zip, a.game_name):
            raise ValueError("this session already has history for a different build; "
                             "use a new --session folder, or --fresh to archive the old history")
        sess.update(**cfg)
    else:
        if has_history:  # --fresh: keep the old evidence, out of the way
            sess.archive(int(sess.now()))
        sess.init(**cfg, log_path=None, started=sess.now())
    b = backend_for(sess, make)
    b.warmup = a.warmup
    if a.skip_probe:
        b.probe = None
    check = getattr(b, "check_lock", None)
    if check:
        check()  # a locked console stops here, before a "relaunch" entry is journaled for a launch that never ran
    # Journal first: a slow launch can raise "not running" and still come up as a fresh run seconds later.
    sess.append("relaunch" if relaunch else "start", game=a.game_name, zip=a.remote_zip)
    b.launch()
    print(f"session {sess.root}\ngame {a.game_name} is running"
          + (" again (history kept, numbering continues)" if relaunch else "") + ". Next: look")
    return 0


def cmd_look(a, sess, make=None, **_):
    png, fg = run_steps(sess, backend_for(sess, make), [], a.label, "look")
    print(png)
    if fg is False:
        log("WARNING: the game was not the front window in this frame; the picture may show something else")
    return 0


def cmd_press(a, sess, make=None, **_):
    together = getattr(a, "together", False)
    steps = key_steps(parse_keys(a.keys), a.hold, a.gap, together)
    png, fg = run_steps(sess, backend_for(sess, make), steps, a.label or "after-" + "-".join(parse_keys(a.keys)), "press",
                        {"keys": parse_keys(a.keys), "hold": a.hold, **({"together": True} if together else {})})
    print(png)
    if fg is False:
        log("WARNING: the game was not the front window; the keys may have gone elsewhere")
    return 0


def cmd_mouse(a, sess, make=None, **_):
    if a.click:
        step = {"op": "click", "button": a.click}
        if a.x is not None or a.y is not None:
            if a.x is None or a.y is None:
                raise ValueError("give both --x and --y, or neither")
            step.update(x=a.x, y=a.y)
        extra = {"click": a.click}
    elif a.move:
        step = {"op": "move", "dx": a.move[0], "dy": a.move[1]}
        extra = {"move": list(a.move)}
    else:
        raise ValueError("give --click or --move DX DY")
    png, fg = run_steps(sess, backend_for(sess, make), [step], a.label or "after-mouse", "mouse", extra)
    print(png)
    if fg is False:
        log("WARNING: the game was not the front window after this input (it may have crashed or quit); run state, then redo it")
    return 0


def cmd_clip(a, sess, make=None, record_mod=None):
    rec = record_mod or _load("legion_record")
    cfg = sess.cfg
    host = cfg["host"]
    if not 3 <= a.seconds <= 120:
        raise ValueError("clip seconds must be 3 to 120")
    if not cfg.get("obs_ours") and not rec.obs_up(host):
        started = []
        rec.start_obs(host, on_launch=lambda: started.append(True))
        if started:
            sess.update(obs_ours=True)
    b = backend_for(sess, make)
    # Check the game before AND after the take (as legion_record.one_take does), and that it is the front
    # window at both ends: OBS records the whole display, so another window in front is not the game.
    alive_before = bool(b.alive())
    _p, fg_before = run_steps(sess, b, [], "clipcheck-before", "look")
    remote = rec.record(host, a.seconds, 3)
    alive_after = bool(b.alive())
    _p, fg_after = run_steps(sess, b, [], "clipcheck-after", "look")
    alive = alive_before and alive_after
    front = fg_before is True and fg_after is True
    local = rec.fetch(host, remote, sess.root / "clips")
    ok, problems = rec.check_video(local, min_seconds=a.seconds * 0.8)
    sess.append("clip", file=str(Path(local).relative_to(sess.root)), seconds=a.seconds, video_ok=bool(ok),
                game_alive=alive, game_in_front=front, problems=problems)
    print(local)
    for p in problems:
        log(f"clip problem: {p}")
    if not alive:
        log("clip problem: the game was not running for the whole clip; a clip of the desktop is not evidence")
    if not front:
        log("clip problem: the game was not the front window at the start or end of the clip (OBS or a dialog may be "
            "in front); send a harmless key with `press` to bring it forward, then clip again")
    return 0 if ok and alive and front else 1


def cmd_state(a, sess, make=None, **_):
    b = backend_for(sess, make)
    cfg = sess.cfg
    alive = b.alive()
    if not cfg.get("log_path"):
        try:
            rc, out, _e = b.ssh(f'powershell -Command "Get-ChildItem C:/Dev -Recurse -Filter {cfg["game_name"]}.log -ErrorAction SilentlyContinue | '
                                'Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName"')
            if rc == 0 and out.strip():
                sess.update(log_path=out.strip().splitlines()[-1].strip())
        except Exception as e:  # noqa: BLE001 - state is best effort
            log(f"could not find the log: {e}")
    lp = sess.cfg.get("log_path")
    print(f"game_running: {alive}")
    if lp:
        rc, out, _e = b.ssh(f'powershell -Command "Get-Content -Tail {int(a.lines)} \'{lp}\'"')
        print(out.rstrip() if rc == 0 else f"(could not read {lp})")
    else:
        print("(game log not found)")
    sess.append("state", alive=alive)
    return 0


def cmd_mark(a, sess, **_):
    files = []
    for f in a.evidence:
        p = Path(f)
        if not p.is_absolute():
            # session folder first (the doc's examples), then the current directory
            p = sess.root / p if (sess.root / p).exists() else Path.cwd() / p
        try:
            rel = p.resolve().relative_to(sess.root.resolve())
        except ValueError:
            raise ValueError(f"evidence {f} is not inside the session folder {sess.root}") from None
        if not p.is_file():
            raise ValueError(f"evidence file {f} does not exist")
        files.append(str(rel))
    sess.append("mark", event=a.event, evidence=files, note=a.note or "")
    print(f"marked {a.event} with {len(files)} file(s)")
    return 0


def cmd_stop(a, sess, make=None, record_mod=None):
    b = backend_for(sess, make)
    clean = b.close()
    if sess.cfg.get("obs_ours"):
        rec = record_mod or _load("legion_record")
        rec.close_process(sess.cfg["host"], "obs64")
    sess.append("stop", clean=clean)
    print("stopped" + ("" if clean else " (had to force it)"))
    return 0


# ---------- gate ----------

def evaluate(sess):
    """Return a list of problems; empty means the gate passes."""
    problems, _warnings = evaluate_full(sess)
    return problems


def mark_problems(sess, entries, i, e, captured, first_input):
    """Why mark entry i (at journal index i) is not usable evidence; empty list = usable."""
    ev = e.get("evidence") or []
    if not ev:
        return [f"{e['event']}: the mark has no evidence files"]
    out = []
    for f in ev:
        if f not in captured:
            out.append(f"{e['event']}: evidence {f} was not captured by look/press/mouse/clip in this session")
            continue
        ci = captured[f]
        c = entries[ci]
        if ci > i:
            out.append(f"{e['event']}: evidence {f} was captured after the mark")
        elif first_input is None or ci < first_input:
            out.append(f"{e['event']}: evidence {f} was captured before any real input (a title frame is not play)")
        if not (sess.root / f).is_file():
            out.append(f"{e['event']}: evidence {f} is missing on disk")
        if c["kind"] == "clip" and c.get("video_ok") is not True:
            out.append(f"{e['event']}: clip {f} failed its video check (black or flat frames)")
        if c["kind"] == "clip" and c.get("game_alive") is not True:
            out.append(f"{e['event']}: clip {f} was recorded while the game was not known to be running")
        if c.get("game_in_front") is not True:
            what = "clip" if c["kind"] == "clip" else "frame"
            out.append(f"{e['event']}: {what} {f} was taken with the game not known to be in front")
    return out


def evaluate_full(sess):
    """(problems, warnings). The latest usable mark per milestone counts; older bad marks only warn."""
    problems, warnings = [], []
    entries = sess.entries()
    captured = {}
    for i, e in enumerate(entries):
        if e["kind"] in ("look", "press", "mouse", "clip") and e.get("file"):
            captured[e["file"]] = i
    inputs = [i for i, e in enumerate(entries) if e["kind"] in ("press", "mouse")]
    first_input = inputs[0] if inputs else None
    chosen = {}
    for m in MILESTONES:
        marks = [(i, e) for i, e in enumerate(entries) if e["kind"] == "mark" and e.get("event") == m]
        if not marks:
            problems.append(f"no `mark {m}` in the journal")
            continue
        results = [(i, e, mark_problems(sess, entries, i, e, captured, first_input)) for i, e in marks]
        good = [r for r in results if not r[2]]
        if good:
            chosen[m] = good[-1]
            warnings += [f"older bad mark ignored: {p}" for _, _, ps in results if ps for p in ps]
        else:
            problems += results[-1][2]
    if len(inputs) < 5:
        problems.append(f"only {len(inputs)} input commands; reaching a win by real play takes more than that")
    last_launch = max((i for i, e in enumerate(entries) if e["kind"] in ("start", "relaunch")), default=-1)
    if any(e.get("game_in_front") is False for i, e in enumerate(entries) if e["kind"] in ("press", "mouse") and i > last_launch):
        problems.append("the game was not the front window after an input in the current run (crash, quit or lost focus: "
                        "a finding to report); relaunch with `start` or redo that step")
    if len(chosen) == len(MILESTONES):
        sets = {m: set(chosen[m][1]["evidence"]) for m in MILESTONES}
        for a, b in (("win", "lose"), ("win", "restart"), ("lose", "restart")):
            shared = sets[a] & sets[b]
            if shared:
                problems.append(f"{a} and {b} share evidence {sorted(shared)[0]}; each milestone needs its own frame or clip")
        newest_lose = max(captured[f] for f in sets["lose"])
        oldest_restart = min(captured[f] for f in sets["restart"])
        if oldest_restart <= newest_lose:
            problems.append("restart evidence was not captured after the lose evidence")
        elif any(entries[i]["kind"] == "relaunch" for i in range(newest_lose, oldest_restart)):
            problems.append("the game was relaunched between the lose and restart evidence; restart must happen in game, not by `start`")
    return problems, warnings


def check_report(path):
    p = Path(path)
    if not p.is_file():
        return [f"report {path} does not exist"]
    text = p.read_text(encoding="utf-8", errors="replace")
    problems = []
    for s in REPORT_SECTIONS:
        if not re.search(rf"^#+\s*{re.escape(s)}", text, re.M | re.I):
            problems.append(f"report is missing the '{s}' section")
    for name in ("Fun score", "Clarity score"):
        m = re.search(rf"{name}\D{{0,20}}([0-9]+)\s*/\s*5", text, re.I)
        if not m or not 1 <= int(m.group(1)) <= 5:
            problems.append(f"report needs '{name}: N/5' with N from 1 to 5")
    if re.search(r"\bTODO\b|<fill", text, re.I):
        problems.append("report still has TODO / <fill> placeholders")
    return problems


def cmd_gate(a, sess, **_):
    problems, warnings = evaluate_full(sess)
    for w in warnings:
        log(f"note: {w}")
    if a.report:
        problems += check_report(a.report)
    if problems:
        print("GATE FAIL")
        for p in problems:
            print(f"- {p}")
        return 1
    print("GATE PASS: win, lose and restart are evidenced by real play. A human still reads the report.")
    return 0


# ---------- cli ----------

def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", default=os.environ.get("AGENT_PLAYTEST_DIR", "playtest-session"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("--host", default="device-host")
    s.add_argument("--remote-zip", required=True)
    s.add_argument("--game-name", required=True)
    s.add_argument("--task-name", default="MegaJamLaunchGame")
    s.add_argument("--warmup", type=int, default=vp.WARMUP_DEFAULT,
                   help=f"seconds to wait after launch (default {vp.WARMUP_DEFAULT}; extended while the screen is black)")
    s.add_argument("--skip-probe", action="store_true", help="skip the lock / black-screen probe shots")
    s.add_argument("--fresh", action="store_true", help="archive any earlier history in this session folder and begin again")
    s = sub.add_parser("look")
    s.add_argument("--label", default="look")
    s = sub.add_parser("press")
    s.add_argument("keys")
    s.add_argument("--hold", type=float, default=0.1)
    s.add_argument("--gap", type=float, default=0.2)
    s.add_argument("--together", action="store_true", help="hold all KEYS at once (e.g. space,d) instead of one after another")
    s.add_argument("--label", default="")
    s = sub.add_parser("mouse")
    s.add_argument("--click", choices=["left", "right"])
    s.add_argument("--x", type=int)
    s.add_argument("--y", type=int)
    s.add_argument("--move", type=int, nargs=2, metavar=("DX", "DY"))
    s.add_argument("--label", default="")
    s = sub.add_parser("clip")
    s.add_argument("seconds", type=int)
    s = sub.add_parser("state")
    s.add_argument("--lines", type=int, default=LOG_TAIL_DEFAULT)
    s = sub.add_parser("mark")
    s.add_argument("event", choices=MILESTONES)
    s.add_argument("--evidence", nargs="+", required=True)
    s.add_argument("--note", default="")
    s = sub.add_parser("gate")
    s.add_argument("--report")
    sub.add_parser("stop")
    return ap


COMMANDS = {"start": cmd_start, "look": cmd_look, "press": cmd_press, "mouse": cmd_mouse, "clip": cmd_clip,
            "state": cmd_state, "mark": cmd_mark, "gate": cmd_gate, "stop": cmd_stop}


def main(argv=None, make=None, record_mod=None, now=time.time):
    a = build_parser().parse_args(argv)
    sess = Session(a.session, now=now)
    try:
        return COMMANDS[a.cmd](a, sess, make=make, record_mod=record_mod)
    except (ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
