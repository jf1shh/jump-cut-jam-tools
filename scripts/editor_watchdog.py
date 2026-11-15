#!/usr/bin/env python3
"""Editor watchdog: save and snapshot on a timer; if the editor dies, say why and relaunch it.

Mock jam 10 lost 55 minutes to a SIGTERM with unsaved work. Each tick:
  editor alive -> MCP save-all, then snapshot-commit in the project (a failed save is logged, the
                  commit still runs so on-disk work is kept)
  editor dead  -> log why (journal lines for oomd/kill/the scope), copy Saved/Logs and Saved/Crashes
                  to stages/04_ship/output/crash-logs/<ts>/, snapshot-commit, relaunch with launch-editor.sh,
                  print what was restored.

  editor_watchdog.py --project /abs/Project --uproject /abs/Project/X.uproject --editor /abs/UnrealEditor \
      --pid 12345 --interval-min 5

Without --pid it launches the editor first. Foreground only: it starts no background job; run it under
claude-loop/systemd yourself. Never run it from a ticket worker against a real editor.
Test hooks: --launcher PATH (default scripts/launch-editor.sh), --journal-cmd "CMD" (default journalctl
--user), --max-ticks N, --interval-sec S (overrides minutes).
"""
import argparse
import datetime
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mcp_call import McpClient, McpError, snapshot_commit  # noqa: E402

WHY = re.compile(r"oom|out of memory|killed|SIGTERM|SIGKILL|megajam-job|UnrealEditor|Terminated", re.I)


def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] watchdog: {msg}", flush=True)


def proc_start(pid):
    """Process start time (clock ticks since boot, /proc stat field 22), or None if unreadable."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return None


def pid_alive(pid, start=None):
    """Alive and not a zombie. With start (from proc_start), a reused pid counts as dead."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            fields = f.read().rsplit(")", 1)[1].split()
        if fields[0] == "Z":
            return False
        return start is None or fields[19] == start
    except (OSError, IndexError):
        return False


def reap_status(pid):
    """If pid is our child, return its exit description; otherwise None."""
    try:
        done, st = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return None
    if done == 0:
        return None
    if os.WIFSIGNALED(st):
        return f"killed by signal {os.WTERMSIG(st)}"
    return f"exit code {os.WEXITSTATUS(st)}"


def why_died(pid, journal_cmd):
    parts = []
    status = reap_status(pid)
    if status:
        parts.append(status)
    try:
        r = subprocess.run(journal_cmd, capture_output=True, text=True, timeout=20)
        hits = [l for l in r.stdout.splitlines() if WHY.search(l)][-5:]
        parts.extend(hits)
    except (OSError, subprocess.SubprocessError) as e:
        parts.append(f"journal unavailable: {e}")
    return parts or ["no exit status or journal line found (not our child; journal empty)"]


def preserve_crash_logs(project, root):
    ts = datetime.datetime.now().strftime("%Y-%m-%dT%H%M")
    dest = os.path.join(root, "stages", "04_ship", "output", "crash-logs", ts)
    copied = []
    for sub in ("Logs", "Crashes"):
        src = os.path.join(project, "Saved", sub)
        if os.path.isdir(src):
            try:
                shutil.copytree(src, os.path.join(dest, sub), dirs_exist_ok=True, ignore_dangling_symlinks=True)
            except (shutil.Error, OSError) as e:  # a vanished/unreadable file must not stop the relaunch
                log(f"  crash-log copy of {sub} incomplete: {str(e)[:200]}")
            copied.append(sub)
    return dest if copied else None, copied


BIND_ERROR_EXIT = 9  # launch-editor.sh: "HttpListener unable to bind" (the old editor still held :8010)
BIND_RETRY_WAIT = 5  # seconds before the one retry; the launcher's own advice is "wait a few seconds"


def launch(launcher, editor, uproject, relaunch=False, sleep=None, bind_retry_wait=BIND_RETRY_WAIT):
    """Return the editor pid. Exit 0 (up), 5 (alive, port not up yet) and 3 (already running) all carry a
    live pid on stdout and are adopted. Exit 9 (port bind race: the launcher already stopped the new editor)
    is retried once after bind_retry_wait seconds, so one lost race does not cost a whole watchdog cycle or
    a restart from the budget. Anything else raises."""
    # The launcher's GPU gate stays on. A relaunch gets a short GPU-gate wait (PREFLIGHT_WAIT=30) so a busy
    # GPU fails that cycle fast; the first launch keeps the launcher's own PREFLIGHT_WAIT default (120 s).
    # The MCP-port wait (WAIT_TIMEOUT, launcher default 300 s since PR 149) is never changed here.
    env = dict(os.environ)
    if relaunch:
        env["PREFLIGHT_WAIT"] = os.environ.get("PREFLIGHT_WAIT", "30")
    for attempt in (1, 2):
        r = subprocess.run([launcher, editor, uproject], capture_output=True, text=True, env=env)
        if r.returncode != BIND_ERROR_EXIT or attempt == 2:
            break
        log(f"  launcher exit 9 (port bind race); retrying once in {bind_retry_wait:g}s: {r.stderr.strip()[-200:]}")
        (sleep or time.sleep)(bind_retry_wait)
    lines = r.stdout.strip().splitlines()
    pid = int(lines[-1]) if lines and lines[-1].strip().isdigit() else None
    if r.returncode in (0, 3, 5) and pid:
        if r.returncode != 0:
            log(f"  launcher exit {r.returncode} (editor alive, tracking pid {pid}): {r.stderr.strip()[-200:]}")
        return pid
    raise RuntimeError(f"launcher exit {r.returncode}: {r.stderr.strip()[-300:]}")


def restored_summary(project):
    last = subprocess.run(["git", "-C", project, "log", "-1", "--format=%h %s (%cr)"],
                          capture_output=True, text=True).stdout.strip()
    auto = os.path.join(project, "Saved", "Autosaves")
    n = sum(len(f) for _, _, f in os.walk(auto)) if os.path.isdir(auto) else 0
    return f"last snapshot: {last or 'none'}; autosave files on disk: {n}"


def tick(a, state):
    if pid_alive(state["pid"], state.get("start")):
        try:
            McpClient(a.mcp_url, a.mcp_timeout).save_all()
            log("save-all ok")
        except McpError as e:
            log(f"save-all FAILED: {e}")
        try:
            h = snapshot_commit(a.project)
            log(f"snapshot {h}" if h else "snapshot: nothing changed")
        except McpError as e:
            log(f"snapshot FAILED: {e}")
        return
    log(f"editor pid {state['pid']} is GONE")
    for line in why_died(state["pid"], shlex.split(a.journal_cmd)):
        log(f"  why: {line}")
    try:
        dest, copied = preserve_crash_logs(a.project, a.repo_root)
    except Exception as e:  # noqa: BLE001 - nothing here may block the relaunch
        dest, copied = None, []
        log(f"  crash-log copy FAILED: {e}")
    log(f"  crash logs copied to {dest}: {copied}" if dest else "  no Saved/Logs or Saved/Crashes to copy")
    try:
        h = snapshot_commit(a.project, "snapshot: before relaunch after editor death")
        log(f"  snapshot {h}" if h else "  snapshot: nothing changed")
    except McpError as e:
        log(f"  snapshot FAILED: {e}")
    state["restarts"] += 1
    if state["restarts"] > a.max_restarts:
        log(f"  restart budget {a.max_restarts} used up; not relaunching")
        state["stop"] = True
        return
    try:
        state["pid"] = launch(a.launcher, a.editor, a.uproject, relaunch=True)
        state["start"] = proc_start(state["pid"])
    except (RuntimeError, ValueError, OSError) as e:
        log(f"  relaunch FAILED: {e}")
        return
    log(f"  relaunched, new pid {state['pid']}; {restored_summary(a.project)}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--project", required=True, help="project dir (a git repo)")
    p.add_argument("--uproject", required=True)
    p.add_argument("--editor", required=True)
    p.add_argument("--pid", type=int, default=None)
    p.add_argument("--interval-min", type=float, default=5)
    p.add_argument("--interval-sec", type=float, default=None)
    p.add_argument("--max-ticks", type=int, default=0, help="0 = forever")
    p.add_argument("--max-restarts", type=int, default=20)
    p.add_argument("--mcp-url", default=None)
    p.add_argument("--mcp-timeout", type=float, default=60)
    p.add_argument("--launcher", default=os.path.join(HERE, "launch-editor.sh"))
    p.add_argument("--journal-cmd", default="journalctl --user --since -10min --no-pager -q")
    p.add_argument("--repo-root", default=os.path.dirname(HERE), help="where stages/04_ship/output/crash-logs/ goes")
    a = p.parse_args(argv)
    state = {"pid": a.pid, "restarts": 0, "stop": False}
    if state["pid"] is None:
        state["pid"] = launch(a.launcher, a.editor, a.uproject)
        log(f"launched editor pid {state['pid']}")
    state["start"] = proc_start(state["pid"])
    wait = a.interval_sec if a.interval_sec is not None else a.interval_min * 60
    n = 0
    while not state["stop"]:
        tick(a, state)
        n += 1
        if a.max_ticks and n >= a.max_ticks:
            break
        time.sleep(wait)
    return 0


if __name__ == "__main__":
    sys.exit(main())
