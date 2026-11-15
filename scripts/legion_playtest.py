#!/usr/bin/env python3
"""Desktop-side orchestrator for the package -> deploy -> launch -> verify loop against the
packaged build already on the Legion Go S.

Replaces the ad-hoc, multi-step SSH command sequence from the mock jam 7 sessions (copy a
.ps1 over, extract a zip by hand, create/fix a Scheduled Task, poll Get-Process, grep a log -
see .handoff/loop-157067/HANDOFF.md and stages/00_prep/references/mock-jam-6-tooling-plan.md's gotchas log) with one
command. Does NOT run package-and-push.ps1 itself - that part already works and still needs to
be run (or re-run after a code change) separately on the Legion before this script has a zip to
deploy. This script starts from an existing zip.

Three SSH round trips, each a single `-File` invocation (never an inline `-Command` with
PowerShell $variables - those get mangled by escaping across bash -> ssh -> powershell, a
documented gotcha):
  1. scp scripts/legion_remote_launch.ps1 to the remote, run it -> extracts the zip fresh,
     (re)registers the launch Scheduled Task, returns exe/log paths as JSON.
  2. Trigger the task and poll `Get-Process <GameName>` a few times to confirm it started and
     is still responding (not a silent exit).
  3. Grep the log for LoadMap/LogWorld/LogLoad: (did the level actually load), any Error:
     lines, and an optional --win-marker string (e.g. "SIGNAL DELIVERED").

Before step 1, a preflight stops (exit 2, one plain line) if the Legion screen is locked
(LockApp.exe awake or LogonUI.exe up), and stops any UnrealGame.exe / <GameName>.exe left from
an earlier run (mock jam 14: a leftover game made the next `schtasks /Run` fail with exit 1).

Exit code is 0 only if the process started, stayed responding through the poll window, the
level load markers were found, and no win-marker check was requested-and-missed.

EXAMPLE:
    ./scripts/legion_playtest.py \\
        --remote-zip 'C:\\Dev\\MockJam7Game\\Packaged\\SilentBlade_MockJam7.zip' \\
        --game-name MockJam7Game --win-marker 'SIGNAL DELIVERED'
"""

import argparse
import base64
import json
import subprocess
import sys
import time

DEFAULT_HOST = "device-host"
LAUNCH_SCRIPT = "legion_remote_launch.ps1"
REMOTE_SCRATCH_DIR = "C:/Dev/.legion_playtest_scratch"


def run(cmd, **kw):
    print(f"+ {' '.join(cmd)}", file=sys.stderr)
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


def ssh_powershell_file(host, remote_ps1, args):
    cmd = [
        "ssh", host,
        f"powershell -ExecutionPolicy Bypass -File {remote_ps1} " + " ".join(args),
    ]
    return run(cmd)


# ---------- launch preflight (mock jam 14) ----------
# The Legion locks its screen on idle. LockApp.exe then owns the console and a launched game gets no
# picture and no input. LockApp.exe also stays loaded after an unlock, but SUSPENDED (every thread's
# WaitReason is Suspended; seen on the Legion 2026-11-10), so "the process exists" is not enough:
# count its threads that are not suspended. LogonUI.exe is the sign-in screen (what legion_preflight
# already checks). Encoded command: no $variables cross bash -> ssh -> powershell unescaped.
LOCK_PS = (
    '$a = Get-Process LockApp -ErrorAction SilentlyContinue; '
    '$live = 0; if ($a) { $live = @($a.Threads | Where-Object { $_.WaitReason -ne "Suspended" }).Count }; '
    '$ui = @(Get-Process LogonUI -ErrorAction SilentlyContinue).Count; '
    '"LOCKAPP_LIVE=$live LOGONUI=$ui"'
)
LOCKED_MSG = ("The Legion screen is locked. Unlock the Legion screen (sign in on it, leave it on the desktop), "
              "then run this again.")
# A game left running from the last run makes the next schtasks /Run fail (exit 1, mock jam 14).
LEFTOVER_EXES = ("UnrealGame.exe",)
TASKKILL_NOT_FOUND = 128


def encoded_powershell(script):
    return "powershell -NoProfile -NonInteractive -EncodedCommand " + base64.b64encode(
        script.encode("utf-16-le")).decode("ascii")


def _ssh_rc(host, cmd, timeout=60):
    """(rc, stdout, stderr) without raising, like the other preflight helpers."""
    try:
        p = subprocess.run(["ssh", "-o", "ConnectTimeout=10", host, cmd], capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"
    return p.returncode, p.stdout, p.stderr


def parse_lock(out):
    """True / False from the LOCK_PS line; None when the line is missing (the check itself failed)."""
    for line in (out or "").splitlines():
        if line.startswith("LOCKAPP_LIVE="):
            vals = dict(kv.split("=", 1) for kv in line.split() if "=" in kv)
            try:
                return int(vals["LOCKAPP_LIVE"]) > 0 or int(vals.get("LOGONUI", "0")) > 0
            except (KeyError, ValueError):
                return None
    return None


def legion_locked(host, ssh_fn=None):
    rc, out, err = (ssh_fn or _ssh_rc)(host, encoded_powershell(LOCK_PS))
    locked = parse_lock(out) if rc == 0 else None
    if locked is None:
        raise RuntimeError(f"could not check the Legion lock screen over ssh (exit {rc}): {(err or '').strip()[-160:]}")
    return locked


def kill_leftover_games(host, game_name, ssh_fn=None):
    """Stop any game exe still running from an earlier run. Returns the names that were stopped."""
    ssh_fn = ssh_fn or _ssh_rc
    names = list(LEFTOVER_EXES)
    if game_name and f"{game_name}.exe".lower() not in (n.lower() for n in names):
        names.append(f"{game_name}.exe")
    stopped = []
    for name in names:
        rc, _, err = ssh_fn(host, f"taskkill /F /T /IM {name}")
        if rc == 0:
            stopped.append(name)
        elif rc != TASKKILL_NOT_FOUND:
            raise RuntimeError(f"a leftover {name} is still running on the Legion and taskkill failed "
                               f"(exit {rc}): {(err or '').strip()[-160:]}")
    return stopped


def preflight_launch(host, game_name, ssh_fn=None, sleep=time.sleep):
    """Before any deploy: fail fast on a locked screen, then clear a leftover game."""
    if legion_locked(host, ssh_fn):
        raise RuntimeError(LOCKED_MSG)
    stopped = kill_leftover_games(host, game_name, ssh_fn)
    if stopped:
        print(f"  stopped leftover {', '.join(stopped)} on {host}", file=sys.stderr)
        sleep(2)  # let Windows release the exe files before the zip is extracted over them
    return stopped


def deploy_and_register(host, remote_zip, game_name, task_name):
    preflight_launch(host, game_name)
    local_ps1 = __file__.rsplit("/", 1)[0] + f"/{LAUNCH_SCRIPT}"
    run(["ssh", host, f"powershell -Command \"New-Item -ItemType Directory -Force -Path {REMOTE_SCRATCH_DIR} | Out-Null\""])
    remote_ps1 = f"{REMOTE_SCRATCH_DIR}/{LAUNCH_SCRIPT}"
    run(["scp", local_ps1, f"{host}:{remote_ps1}"])
    # -File arguments are split by the remote shell's own argv rules, not PowerShell's
    # parser - double quotes are stripped there, single quotes are NOT and pass through
    # literally into the parameter value (confirmed: caused a "Zip not found: 'C:\...'"
    # error, the literal quotes included). Use double quotes here, never single.
    result = ssh_powershell_file(
        host, remote_ps1,
        [f'-ZipPath "{remote_zip}"', f"-GameName {game_name}", f"-TaskName {task_name}"],
    )
    payload = result.stdout.strip().splitlines()[-1]
    return json.loads(payload)


def trigger_and_poll(host, task_name, game_name, poll_seconds, poll_interval):
    run(["ssh", host, f"schtasks /Run /TN {task_name}"])
    deadline = time.monotonic() + poll_seconds
    last_seen_alive = False
    while time.monotonic() < deadline:
        time.sleep(poll_interval)
        check = run([
            "ssh", host,
            f"powershell -Command \"Get-Process {game_name} -ErrorAction SilentlyContinue | "
            "Select-Object Id,Responding | ConvertTo-Json -Compress\"",
        ])
        out = check.stdout.strip()
        if not out:
            print(f"  [{poll_interval}s] process not found (exited or not started yet)", file=sys.stderr)
            last_seen_alive = False
            continue
        procs = json.loads(out)
        # A C++ project's package has a stub Game.exe that starts the real
        # Binaries/Win64/Game.exe, so Get-Process can return a list (mock 17).
        if isinstance(procs, dict):
            procs = [procs]
        last_seen_alive = bool(procs) and all(p.get("Responding") for p in procs)
        for p in procs:
            print(f"  pid={p.get('Id')} responding={p.get('Responding')}", file=sys.stderr)
    return last_seen_alive


def check_log(host, log_path, win_marker):
    pattern = "LoadMap|LogWorld|LogLoad:|Error:"
    if win_marker:
        pattern += f"|{win_marker}"
    result = subprocess.run(
        ["ssh", host, f"powershell -Command \"Get-Content '{log_path}' -ErrorAction SilentlyContinue | Select-String -Pattern '{pattern}'\""],
        text=True, capture_output=True,
    )
    lines = result.stdout.strip().splitlines()
    loaded = any("LoadMap" in l or "LogWorld" in l or "LogLoad:" in l for l in lines)
    errors = [l for l in lines if "Error:" in l]
    win_found = bool(win_marker) and any(win_marker in l for l in lines)
    return loaded, errors, win_found, lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=DEFAULT_HOST, help=f"SSH alias for the Legion (default: {DEFAULT_HOST})")
    ap.add_argument("--remote-zip", required=True, help="Path to the zip on the Legion, as package-and-push.ps1 produced it")
    ap.add_argument("--game-name", required=True, help="Must match <GameName>.exe at the zip root")
    ap.add_argument("--task-name", default="MegaJamLaunchGame")
    ap.add_argument("--win-marker", default="", help="String to look for in the log as proof the playtest objective fired")
    ap.add_argument("--poll-seconds", type=int, default=25, help="How long to watch the process after launch")
    ap.add_argument("--poll-interval", type=int, default=5)
    args = ap.parse_args()

    print("== Deploying + registering launch task ==", file=sys.stderr)
    try:
        deployed = deploy_and_register(args.host, args.remote_zip, args.game_name, args.task_name)
    except RuntimeError as e:  # preflight: locked screen or a leftover game that would not stop
        print(f"STOP: {e}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(deployed, indent=2), file=sys.stderr)

    print("== Launching + polling ==", file=sys.stderr)
    stayed_alive = trigger_and_poll(args.host, args.task_name, args.game_name, args.poll_seconds, args.poll_interval)

    print("== Checking log ==", file=sys.stderr)
    loaded, errors, win_found, matches = check_log(args.host, deployed["logPath"], args.win_marker)
    for line in matches:
        print(f"  {line}", file=sys.stderr)

    ok = stayed_alive and loaded and not errors and (not args.win_marker or win_found)
    print(json.dumps({
        "stayedAlive": stayed_alive,
        "levelLoaded": loaded,
        "errorLines": len(errors),
        "winMarkerFound": win_found if args.win_marker else None,
        "ok": ok,
    }))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
