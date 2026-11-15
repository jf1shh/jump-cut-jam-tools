#!/usr/bin/env python3
"""Desktop-side orchestrator for taking a screenshot of the Legion Go S's real physical
display over SSH.

Plain SSH + PowerShell screen capture lands in SSH's own non-interactive session 0 and
captures nothing useful - the same session-isolation problem legion_remote_launch.ps1 solves
for launching the game, solved here the same way: register a Scheduled Task with Interactive
logon so the capture script (legion_screenshot.ps1) runs in the real interactive session that
owns the physical display.

Added mock jam 9 (SkyAtmosphere warning verification): the owner reported on-screen-only red
warning text that never writes to the packaged build's log file, so legion_playtest.py's
log-based checks couldn't confirm the fix. Three SSH/SCP round trips, each a single -File or
fixed -Command invocation (no PowerShell $variable interpolation over the SSH boundary - a
documented escaping gotcha, see legion_playtest.py):
  1. scp legion_screenshot.ps1 to the remote scratch dir.
  2. Register (or re-register, -Force) a Scheduled Task pointed at it with Interactive logon,
     trigger it, poll until the output PNG's timestamp is newer than the trigger time.
  3. scp the PNG back to a local path.

EXAMPLE:
    ./scripts/legion_capture_screenshot.py --out /tmp/legion_screenshot.png
"""

import argparse
import subprocess
import sys
import time

DEFAULT_HOST = "device-host"
CAPTURE_SCRIPT = "legion_screenshot.ps1"
REMOTE_SCRATCH_DIR = "C:/Dev/.legion_playtest_scratch"
REMOTE_OUT_PATH = f"{REMOTE_SCRATCH_DIR}/screenshot.png"


# Same limits as legion_preflight: mock jam 10 hung 45 minutes on an uncapped ssh, and without BatchMode
# a broken key waits at a password prompt. This script is now on the critical path of every Legion run.
SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
            "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=3"]
CALL_TIMEOUT = 60  # seconds per ssh/scp call


def run(cmd, **kw):
    cmd = [cmd[0], *SSH_OPTS, *cmd[1:]] if cmd and cmd[0] in ("ssh", "scp") else list(cmd)
    kw.setdefault("timeout", CALL_TIMEOUT)
    print(f"+ {' '.join(cmd)}", file=sys.stderr)
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


def deploy_and_register(host, task_name):
    local_ps1 = __file__.rsplit("/", 1)[0] + f"/{CAPTURE_SCRIPT}"
    run(["ssh", host, f"powershell -Command \"New-Item -ItemType Directory -Force -Path {REMOTE_SCRATCH_DIR} | Out-Null\""])
    remote_ps1 = f"{REMOTE_SCRATCH_DIR}/{CAPTURE_SCRIPT}"
    run(["scp", local_ps1, f"{host}:{remote_ps1}"])
    # Register with a fixed -Command string (no interpolated path/time values) to sidestep
    # the bash -> ssh -> PowerShell $-escaping gotcha legion_playtest.py's docstring warns
    # about; the only variable part (remote_ps1, REMOTE_OUT_PATH) is a plain path, safe here.
    register_cmd = (
        f"$action = New-ScheduledTaskAction -Execute 'powershell.exe' "
        f"-Argument '-WindowStyle Hidden -ExecutionPolicy Bypass -File \"{remote_ps1}\" -OutPath \"{REMOTE_OUT_PATH}\"'; "
        f"$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(5); "
        f"$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited; "
        # The Legion Go S is a handheld: default task settings refuse to start on battery
        # (the task sits 'Queued' forever) and kill it when unplugged (mock 17, 2026-11-11).
        f"$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; "
        f"Register-ScheduledTask -TaskName {task_name} -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null"
    )
    run(["ssh", host, f'powershell -Command "{register_cmd}"'])


def trigger_and_wait(host, task_name, poll_seconds, poll_interval):
    # Capture the remote clock, not the local one, so a trigger-time comparison against
    # the PNG's LastWriteTime isn't thrown off by clock skew between machines.
    before = run(["ssh", host, "powershell -Command \"(Get-Date).ToFileTimeUtc()\""]).stdout.strip()
    run(["ssh", host, f"schtasks /Run /TN {task_name}"])
    deadline = time.monotonic() + poll_seconds
    while time.monotonic() < deadline:
        time.sleep(poll_interval)
        check = run([
            "ssh", host,
            "powershell -Command \""
            f"if (Test-Path '{REMOTE_OUT_PATH}') {{ (Get-Item '{REMOTE_OUT_PATH}').LastWriteTimeUtc.ToFileTimeUtc() }} else {{ 0 }}"
            "\"",
        ])
        written_at = check.stdout.strip()
        print(f"  remote PNG write-time={written_at} (need > {before})", file=sys.stderr)
        if written_at and int(written_at) > int(before):
            return True
    return False


def fetch(host, local_out):
    run(["scp", f"{host}:{REMOTE_OUT_PATH}", local_out])


def _load_preflight():
    import importlib.util
    from pathlib import Path
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("legion_preflight", here / "legion_preflight.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def take_probe(host, task_name="MegaJamScreenshot", poll_seconds=20, poll_interval=2):
    """One screenshot into a temp file, for the lock / black-screen check. Returns the local path;
    raises RuntimeError if no fresh capture appeared."""
    import tempfile
    deploy_and_register(host, task_name)
    if not trigger_and_wait(host, task_name, poll_seconds, poll_interval):
        raise RuntimeError(f"no fresh screenshot appeared within {poll_seconds}s")
    path = tempfile.mkdtemp(prefix="legion_probe_") + "/probe.png"
    try:
        fetch(host, path)
    except BaseException:
        _load_preflight().cleanup_probe(path)  # no orphaned screenshots on the error path
        raise
    return path  # the reader (legion_preflight.probe_message) deletes the folder after counting


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=DEFAULT_HOST, help=f"SSH alias for the Legion (default: {DEFAULT_HOST})")
    ap.add_argument("--out", required=True, help="Local path to save the screenshot PNG to")
    ap.add_argument("--task-name", default="MegaJamScreenshot")
    ap.add_argument("--poll-seconds", type=int, default=20, help="How long to wait for a fresh screenshot")
    ap.add_argument("--poll-interval", type=int, default=2)
    ap.add_argument("--skip-lock-check", action="store_true",
                    help="do not stop on a locked or black Legion (the shot is saved either way)")
    args = ap.parse_args(argv)
    pre = _load_preflight()

    if not args.skip_lock_check and pre.console_locked(args.host):
        print(f"ERROR: {pre.MSG_LOCKED}", file=sys.stderr)
        return 1

    print("== Deploying + registering screenshot task ==", file=sys.stderr)
    deploy_and_register(args.host, args.task_name)

    print("== Triggering + waiting for a fresh screenshot ==", file=sys.stderr)
    fresh = trigger_and_wait(args.host, args.task_name, args.poll_seconds, args.poll_interval)
    if not fresh:
        print(f"ERROR: no fresh screenshot appeared within {args.poll_seconds}s", file=sys.stderr)
        return 1

    print("== Fetching screenshot ==", file=sys.stderr)
    fetch(args.host, args.out)
    if not args.skip_lock_check:
        # the shot is its own probe: a locked console captures as (near) one colour
        try:
            n = pre.count_colours(args.out)
        except Exception as e:  # noqa: BLE001 - a cut-short PNG raises zlib.error / struct.error
            print(f"ERROR: the screenshot is not a readable image ({str(e)[:80]}); re-run once, "
                  "the copy may have been cut short", file=sys.stderr)
            return 1
        if n < pre.PROBE_MIN_COLOURS:
            print(f"ERROR: {pre.MSG_BLACK}", file=sys.stderr)
            return 1
    print(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
