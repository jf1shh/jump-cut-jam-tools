#!/usr/bin/env python3
"""Pre-flight for the Legion Go S before a recording / playtest run.

Mock jam 10 lost ~45 min to an ssh timeout and more to OBS / firewall / stale-task surprises.
This checks all of it in about two ssh round trips and prints ONE plain line per failed check.
Exit 0 = all good, 1 = at least one check failed. It only READS the Legion, with one narrow
exception: --remove-stale deletes leftover scheduled tasks named MJTool* (the ones
legion_record.py creates). It never adds a firewall rule; it prints the command for the owner.

Checks: ssh reachable; OBS installed; OBS websocket answering (port 4455); an enabled inbound
Windows Firewall allow rule for the packaged game exe; no stale MJ* scheduled tasks; the console
session is active and the screen is not locked.

EXAMPLE:
    ./scripts/legion_preflight.py --exe-name UnrealGame.exe --exe-path 'C:\\Dev\\Game\\Packaged\\agent_test\\Game.exe'
"""

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_HOST = "device-host"
PS1 = "legion_preflight.ps1"
REMOTE_DIR = "C:/Dev/.legion_playtest_scratch"
SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
            "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=3"]
SSH_TIMEOUT = 40  # hard cap per call; mock jam 10 hung for 45 min with no cap
TOOL_TASK_PREFIX = "MJTool"  # only tasks with this prefix are ours to delete

# Probe shot: a real desktop or game frame has far more than this many distinct colours; a locked
# console (or a capture that came back black) has a handful. One probe shot stops a run at once
# instead of 47 black frames (mock jam 11, gaps 14, 21, 34).
PROBE_MIN_COLOURS = 50
MSG_LOCKED = "Legion is locked: unlock it by hand (the console locks itself after idle time), then re-run."
MSG_BLACK = "capture is black: re-run once before suspecting the build."


def run(cmd, timeout=SSH_TIMEOUT):
    """Run a command; never raises. Returns (returncode, stdout, stderr)."""
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"
    except OSError as e:
        return 127, "", str(e)


def ssh(host, remote_cmd, timeout=SSH_TIMEOUT):
    return run(["ssh", *SSH_OPTS, host, remote_cmd], timeout)


def firewall_command(exe_path):
    return ('New-NetFirewallRule -DisplayName "MegaJam game" -Direction Inbound -Action Allow '
            f'-Profile Any -Program "{exe_path}"   # run once, in an ADMIN PowerShell on the Legion')


def aslist(v):
    """PowerShell's ConvertTo-Json turns one-item lists into scalars and empty ones into null."""
    if v is None:
        return []
    return [v] if isinstance(v, str) else list(v)


def normalize(facts):
    facts = dict(facts)
    for k in ("firewallPrograms", "firewallBlocked", "mjTasks"):
        facts[k] = aslist(facts.get(k))
    return facts


def _norm(p):
    return str(p).replace("/", "\\").strip().lower()


def _matches(programs, exe_name, exe_path):
    for prog in aslist(programs):
        if "<" in str(prog) or "..." in str(prog):
            continue  # the placeholder path we print when the real one is unknown never counts
        if exe_path:
            if _norm(prog) == _norm(exe_path):
                return True
        elif _norm(prog).endswith("\\" + exe_name.lower()):
            return True
    return False


def firewall_ok(programs, exe_name, exe_path, blocked=None):
    """True if an allow rule (already limited to the active profile by the ps1) covers the exe
    and no enabled inbound BLOCK rule does; in Windows Firewall a block rule always wins."""
    if _matches(blocked, exe_name, exe_path):
        return False
    return _matches(programs, exe_name, exe_path)


def evaluate(facts, exe_name, exe_path="", allow_obs_stopped=False, check_firewall=True):
    """Pure function: facts dict (from legion_preflight.ps1) -> list of failure lines."""
    fails = []
    if not facts.get("obsInstalled"):
        fails.append("OBS is not installed on the Legion (winget install --id OBSProject.OBSStudio -e).")
    if not facts.get("obsWebsocket") and not allow_obs_stopped:
        fails.append("OBS websocket is not answering on port 4455 (start OBS; legion_record.py starts it for you).")
    if not check_firewall:
        pass
    elif _matches(facts.get("firewallBlocked"), exe_name, exe_path):
        fails.append(f"An inbound firewall BLOCK rule covers {exe_name}; a block rule beats any allow rule. "
                     "The owner must remove or disable it on the Legion.")
    elif not firewall_ok(facts.get("firewallPrograms"), exe_name, exe_path):
        target = exe_path or f"C:\\<folder of the packaged game>\\{exe_name}"
        fails.append(f"No inbound firewall allow rule for {exe_name}; the owner must run once: "
                     + firewall_command(target))
    tasks = aslist(facts.get("mjTasks"))
    if tasks:
        fails.append("Stale scheduled tasks: " + ", ".join(tasks)
                     + f" (rerun with --remove-stale to delete the {TOOL_TASK_PREFIX}* ones; others are the owner's).")
    if not facts.get("consoleActive"):
        fails.append("No active console session on the Legion (user logged out or disconnected).")
    elif facts.get("locked"):
        fails.append("Legion is locked: unlock it by hand before recording (OBS cannot start on a locked console).")
    return fails


def count_colours(path, limit=PROBE_MIN_COLOURS, step=3):
    """Distinct RGB colours in a sample of the PNG's pixels; stops counting at `limit`."""
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("visual_playtest", here / "visual_playtest.py")
    vp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vp)
    w, h, rgb = vp.read_png(path)
    bpp = len(rgb) // (w * h)  # read_png gives packed pixels
    seen = set()
    for i in range(0, w * h, step):
        seen.add(rgb[i * bpp:i * bpp + 3])
        if len(seen) >= limit:
            break
    return len(seen)


def console_locked(host, ssh_fn=None):
    """True if LogonUI.exe (the lock / sign-in screen) is running on the Legion."""
    rc, out, _ = (ssh_fn or ssh)(host, 'tasklist /FI "IMAGENAME eq LogonUI.exe" /NH')
    return rc == 0 and "logonui.exe" in out.lower()


def probe_message(host, shoot, ssh_fn=None, count=count_colours):
    """One cheap look before a capture or recording. Returns None when the screen is real, else ONE
    plain line. `shoot()` takes one screenshot of the Legion and returns its local PNG path."""
    if console_locked(host, ssh_fn):
        return MSG_LOCKED
    try:
        path = shoot()
    except Exception as e:  # noqa: BLE001 - a failed probe must also stop the run, in one line
        return f"probe shot failed ({str(e).strip()[-120:]}); cannot tell whether the Legion is locked."
    try:
        n = count(path)
    except Exception as e:  # noqa: BLE001 - a cut-short PNG raises zlib.error / struct.error, not just ValueError
        return f"probe shot is not a readable image ({str(e)[:80]}); re-run once, the copy may have been cut short."
    finally:
        cleanup_probe(path)
    return MSG_BLACK if n < PROBE_MIN_COLOURS else None


def cleanup_probe(path):
    """Delete the temp folder take_probe made (legion_probe_*), never any other folder."""
    d = Path(str(path)).parent
    if d.name.startswith("legion_probe_"):
        shutil.rmtree(d, ignore_errors=True)


def collect(host, obs_port=4455):
    """Return (facts, failure_line). Two round trips: ssh reachable, then the ps1."""
    rc, out, err = ssh(host, "echo ok", timeout=20)
    if rc != 0 or "ok" not in out:
        why = (err.strip().splitlines() or [f"exit {rc}"])[-1]
        return None, f"ssh to '{host}' failed ({why}); check the Legion is awake and on the network."
    local = Path(__file__).resolve().parent / PS1
    remote = f"{REMOTE_DIR}/{PS1}"
    ssh(host, f'powershell -Command "New-Item -ItemType Directory -Force -Path {REMOTE_DIR} | Out-Null"')
    rc, _, err = run(["scp", *SSH_OPTS, str(local), f"{host}:{remote}"])
    if rc != 0:
        return None, f"could not copy {PS1} to the Legion ({err.strip()[-120:]})."
    rc, out, err = ssh(host, f"powershell -ExecutionPolicy Bypass -File {remote} -ObsPort {obs_port}", timeout=90)
    try:
        return normalize(json.loads(out.strip().splitlines()[-1])), None
    except (ValueError, IndexError, AttributeError):
        return None, f"preflight script on the Legion gave no readable result (exit {rc}: {(err or out).strip()[-120:]})."


def remove_stale(host, tasks):
    removed = []
    for name in aslist(tasks):
        if name.startswith(TOOL_TASK_PREFIX):
            rc, _, _ = ssh(host, f"schtasks /Delete /TN {name} /F")
            if rc == 0:
                removed.append(name)
    return removed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--exe-name", required=True,
                    help="the game exe, <GameName>.exe (no default: UnrealGame.exe is the wrong-exe trap)")
    ap.add_argument("--no-firewall", action="store_true",
                    help="skip the firewall check (legion_record checks the real exe path after deploy)")
    ap.add_argument("--exe-path", default="", help="full Windows path; if given, the rule must match it exactly")
    ap.add_argument("--allow-obs-stopped", action="store_true", help="do not fail when OBS is not running")
    ap.add_argument("--remove-stale", action="store_true", help=f"delete leftover {TOOL_TASK_PREFIX}* tasks, then re-check")
    ap.add_argument("--obs-port", type=int, default=4455)
    args = ap.parse_args(argv)

    facts, fail = collect(args.host, args.obs_port)
    if fail:
        print(fail)
        return 1
    if args.remove_stale:
        removed = remove_stale(args.host, aslist(facts.get("mjTasks")))
        if removed:
            print("removed stale tasks: " + ", ".join(removed), file=sys.stderr)
            facts, fail = collect(args.host, args.obs_port)
            if fail:
                print(fail)
                return 1
    fails = evaluate(facts, args.exe_name, args.exe_path, args.allow_obs_stopped, not args.no_firewall)
    for line in fails:
        print(line)
    if not fails:
        print("preflight ok", file=sys.stderr)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
