#!/usr/bin/env python3
"""One command to record the packaged game on the Legion Go S and check the video.

Does, in order (retrying the whole take once if it fails):
  1. Start OBS (no flags; --minimize-to-tray / --disable-updater hung it in mock jam 10) from an
     Interactive-logon scheduled task named MJToolObsStart, then wait for the websocket (15-35 s
     seen; we allow 90 s). Skipped if OBS already answers.
  2. Deploy + launch the game with the existing legion_playtest.deploy_and_register
     (-> legion_remote_launch.ps1), then trigger its task.
  3. Run the existing legion_obs_record_test.ps1 for N seconds (it drives the OBS websocket).
     With --sequence FILE, the input steps play DURING this window (see below).
  4. Close the game and OBS the polite way (a console-session task calls CloseMainWindow, then Stop-Process only if still alive),
     so Windows shows no "process terminated" / taskkill error dialog.
  5. scp the mp4 back and run an ffmpeg frame check at several timestamps: black, flat or
     undecodable frames fail the take.

--sequence FILE plays the game while it records, instead of filming the idle start screen. FILE is a
visual_playtest sequence (same JSON; checked by visual_playtest.validate_steps). Only input matters:
key/keys, click, move and wait run; "declare" and "shot" are dropped; a "burst" becomes a wait of its
seconds (same pacing, no capture), so a visual_playtest sequence can be reused as is. The steps run
through visual_playtest's LegionBackend.play (the Interactive scheduled task that runs
visual_playtest_input.ps1 in the console session), in a thread started after the warmup, right before
the recording call, behind a LEAD_IN wait so OBS is already recording. --seconds must cover
HEAD + LEAD_IN + the steps' keys and waits + TAIL, or the command stops before touching the Legion (it is
not extended: the jam video must be 30-60 s, so you choose). An input-run error fails the take.
The input script brings the game to the front before its first step and reports that Legion clock time
(FOCUSED); the OBS script reports the time of StartRecord. After the fetch, ffmpeg writes
<name>_trimmed.mp4 next to the original, starting CUT_MARGIN s after the game came to the front (re-encoded,
so the cut is frame-accurate). That is the submission candidate; the original is kept. A missing time or a
failed cut only skips the trim with a note; a trimmed length outside 30-60 s is a warning.

Refuses to run if legion_preflight.py fails (skip with --skip-preflight).
Exit 0 = a good mp4 is on disk (path printed on stdout; with --sequence and a trim, the trimmed submission
candidate and the untrimmed original, one labelled line each); 1 = both takes failed; 2 = bad --sequence or
--seconds too short.

EXAMPLE:
    ./scripts/legion_record.py --remote-zip 'C:\\Dev\\Game\\Packaged\\SilentBlade_Game.zip' \\
        --game-name Game --seconds 40 --out-dir /tmp/video
    ./scripts/legion_record.py --remote-zip 'C:\\Dev\\Game\\Packaged\\SilentBlade_Game.zip' \\
        --game-name Game --seconds 60 --sequence work/vp/seq2.json --out-dir /tmp/video
"""

import argparse
import importlib.util
import json
import math
import os
import re
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pre = _load("legion_preflight")
playtest = _load("legion_playtest")
vp = _load("visual_playtest")

RECORD_PS1 = "legion_obs_record_test.ps1"
OBS_DIR = r"C:\Program Files\obs-studio\bin\64bit"
OBS_TASK = "MJToolObsStart"
OBS_PORT = 4455
SCRATCH = pre.REMOTE_DIR
LEAD_IN = 5   # s of wait in front of --sequence steps: the input task must start after OBS's StartRecord
TAIL = 3      # s of recording kept after the last step (per-step focus overhead, last key release on camera)
# s of recording before the game is in front, trimmed off. The input task's ~6 ssh/scp/schtasks round trips
# took ~10 s live (mock 16) and run alongside the OBS script's own ~3 round trips before StartRecord; the
# start-of-run focus adds up to ~3 s (6 tries) and the cut margin 0.5 s. 10 covers that with some room.
HEAD = 10
CUT_MARGIN = 0.5   # s cut after the FOCUSED time, so the focus switch itself is not in the first frame
VIDEO_MIN, VIDEO_MAX = 30, 60   # jam gameplay video length, s


def run(cmd, timeout=pre.SSH_TIMEOUT):
    return pre.run(cmd, timeout)


def ssh(host, remote_cmd, timeout=pre.SSH_TIMEOUT):
    return run(["ssh", *pre.SSH_OPTS, host, remote_cmd], timeout)


def log(msg):
    print(msg, file=sys.stderr)


def _capped_playtest_run(cmd, **kw):
    """Stand-in for legion_playtest.run: same contract (raise on failure, .stdout) but with the
    ssh/scp keepalive options and a hard timeout, so a stalled deploy cannot hang us."""
    full = [cmd[0], *pre.SSH_OPTS, *cmd[1:]] if cmd[0] in ("ssh", "scp") else list(cmd)
    log(f"+ {' '.join(full)}")
    rc, out, err = pre.run(full, 300)
    if rc != 0:
        raise RuntimeError(f"{cmd[0]} failed (exit {rc}): {err.strip()[-160:]}")
    return SimpleNamespace(stdout=out, stderr=err, returncode=rc)


playtest.run = _capped_playtest_run


def game_process(game_name, env=None):
    """Windows process to watch and close. Normally the game name. MJ_GAME_PROC overrides it for a
    content-only package, where the stub exe is blocked and the engine exe is launched directly."""
    proc = (os.environ if env is None else env).get("MJ_GAME_PROC")
    if not proc:
        return game_name
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", proc):
        raise ValueError(f"MJ_GAME_PROC {proc!r} must be letters, digits, _ . - only")
    return proc


ENGINE_EXE = "UnrealGame.exe"
ENGINE_REL = "Engine\\Binaries\\Win64\\" + ENGINE_EXE


def content_only(proc):
    """Only the engine exe (content-only package) gets the task repoint. Any other override, such as
    the game's own name or Game-Win64-Shipping for a C++ package, just changes which process is watched."""
    return proc.lower() == "unrealgame"


def engine_launch_cmd(task_name, game_name):
    """Point the game task at Engine\\Binaries\\Win64\\UnrealGame.exe next to the deployed stub exe."""
    return ('powershell -Command "$t=Get-ScheduledTask %s; $d=Split-Path $t.Actions[0].Execute; '
            '$a=New-ScheduledTaskAction -Execute (Join-Path $d Engine\\Binaries\\Win64\\UnrealGame.exe) '
            '-Argument ..\\..\\..\\%s\\%s.uproject -WorkingDirectory (Join-Path $d Engine\\Binaries\\Win64); '
            'Set-ScheduledTask -TaskName %s -Action $a | Out-Null"' % (task_name, game_name, game_name, task_name))


def game_alive(host, name):
    rc, out, _ = ssh(host, f'powershell -Command "Get-Process {name} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"')
    return rc == 0 and bool(out.strip())


# ---------- OBS ----------

def obs_up(host, port=OBS_PORT):
    rc, out, _ = ssh(host, f'powershell -Command "Test-NetConnection 127.0.0.1 -Port {port} -InformationLevel Quiet"')
    return rc == 0 and out.strip().lower().endswith("true")


def start_obs(host, wait_s=90, interval=3, sleep=time.sleep, on_launch=None):
    """Return True if we started OBS, False if it was already up. Raises if it never answers.
    on_launch() is called right before the launch, so the caller knows OBS is ours even if the
    websocket wait later times out."""
    if obs_up(host):
        return False
    # One quoted /TR argument with NO inner quotes (they would split it at "Program Files").
    # cmd's `cd /d` takes the rest of the line as the path, spaces included, and OBS needs its
    # own folder as the working directory.
    tr = f"cmd /c cd /d {OBS_DIR} && obs64.exe --disable-shutdown-check"
    rc, _, err = ssh(host, f'schtasks /Create /TN {OBS_TASK} /TR "{tr}" /SC ONCE /ST 00:00 /IT /F')
    if rc != 0:
        raise RuntimeError(f"could not create the OBS task: {err.strip()[-120:]}")
    if on_launch:
        on_launch()
    rc, _, err = ssh(host, f"schtasks /Run /TN {OBS_TASK}")
    if rc != 0:
        raise RuntimeError(f"could not start the OBS task: {err.strip()[-120:]}")
    waited = 0
    while waited < wait_s:
        sleep(interval)
        waited += interval
        if obs_up(host):
            log(f"OBS websocket up after ~{waited}s")
            sleep(2)  # let the scene finish loading before we send requests
            return True
    raise RuntimeError(f"OBS websocket did not answer within {wait_s}s")


def close_process(host, name, sleep=time.sleep):
    """Ask nicely first; force only if it is still alive. No taskkill, no error dialog.

    CloseMainWindow only works from the session that owns the window, and ssh runs in another
    session (MainWindowHandle is 0 there). So the polite request goes through a scheduled task
    that runs in the console session. If the process is still alive after a grace wait,
    Stop-Process ends it."""
    close_task = f"MJToolClose{name}"
    # no $variables or inner quotes: they get mangled across bash -> ssh -> schtasks -> powershell
    tr = f"powershell -NoProfile -Command (Get-Process {name} -ErrorAction SilentlyContinue).CloseMainWindow()"
    rc, _, _ = ssh(host, f'schtasks /Create /TN {close_task} /TR "{tr}" /SC ONCE /ST 00:00 /IT /F')
    if rc == 0:
        ssh(host, f"schtasks /Run /TN {close_task}")
    try:
        for _ in range(6):
            sleep(2)
            rc, out, _ = ssh(host, f'powershell -Command "Get-Process {name} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"')
            if rc == 0 and not out.strip():
                return True
        ssh(host, f'powershell -Command "Stop-Process -Name {name} -Force -ErrorAction SilentlyContinue"')
        return False
    finally:
        ssh(host, f"schtasks /Delete /TN {close_task} /F")


def remove_task(host, name):
    ssh(host, f"schtasks /Delete /TN {name} /F")


# ---------- recording ----------

def parse_record_json(text):
    """The record script may print 'FAIL ...' lines before its JSON object."""
    lines = text.splitlines()
    fails = [l for l in lines if l.startswith("FAIL")]
    for i, l in enumerate(lines):
        if l.strip() == "{":
            try:
                return json.loads("\n".join(lines[i:])), fails
            except ValueError:
                break
    return None, fails


def record(host, seconds, replay_seconds):
    """Record and return the remote video path."""
    return record_run(host, seconds, replay_seconds)["recordFile"]


def record_run(host, seconds, replay_seconds):
    """Record; return the OBS script's JSON (recordFile, startRecordFileTimeUtc, stats)."""
    ps1 = HERE / RECORD_PS1
    remote = f"{SCRATCH}/{RECORD_PS1}"
    ssh(host, f'powershell -Command "New-Item -ItemType Directory -Force -Path {SCRATCH} | Out-Null"')
    rc, _, err = run(["scp", *pre.SSH_OPTS, str(ps1), f"{host}:{remote}"])
    if rc != 0:
        raise RuntimeError(f"scp of {RECORD_PS1} failed: {err.strip()[-120:]}")
    rc, out, err = ssh(host, f"powershell -ExecutionPolicy Bypass -File {remote} -RecSeconds {seconds} -ReplaySeconds {replay_seconds}",
                       timeout=seconds + replay_seconds + 120)
    data, fails = parse_record_json(out)
    if not data or not data.get("recordFile"):
        raise RuntimeError(f"OBS recording gave no file (exit {rc}; {'; '.join(fails) or (err or out).strip()[-120:]})")
    return data


def fetch(host, remote_path, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    local = out_dir / (re.split(r"[\\/]", remote_path)[-1])
    rc, _, err = run(["scp", *pre.SSH_OPTS, f"{host}:{remote_path.replace(chr(92), '/')}", str(local)], timeout=300)
    if rc != 0 or not local.exists():
        raise RuntimeError(f"scp of the video failed: {err.strip()[-120:]}")
    return local


# ---------- input during the recording (--sequence) ----------

def load_input_steps(path):
    """visual_playtest JSON -> the input steps to play while recording (LEAD_IN wait first).
    Raises ValueError (bad JSON, bad step, no input) or OSError (unreadable file)."""
    steps = vp.validate_steps(json.loads(Path(path).read_text(encoding="utf-8")))
    out = [{"op": "wait", "seconds": LEAD_IN}]
    for s in steps:
        if s["op"] == "burst":
            out.append({"op": "wait", "seconds": vp.burst_params(s)[1]})
        elif s["op"] in ("key", "click", "move", "wait"):
            out.append(s)
    if not any(s["op"] in ("key", "click", "move") for s in out):
        raise ValueError("sequence sends no input (key, click or move); nothing would be played")
    return out


def seconds_needed(steps):
    """Recording length that covers HEAD (trimmed off) + the input steps (LEAD_IN included) + TAIL, whole s."""
    return HEAD + math.ceil(vp.sequence_seconds(steps)) + TAIL


def start_input(args, steps, out_dir, backend=None):
    """Play the steps on the Legion in a background thread through visual_playtest's LegionBackend.play.
    Returns join(), which waits for the run and returns None or one error line."""
    backend = backend or vp.LegionBackend(args.host, args.remote_zip, args.game_name, args.task_name)
    box = {}

    def go():
        try:
            backend.play(steps, out_dir)
        except Exception as e:  # noqa: BLE001 - reported by join()
            box["err"] = str(e)

    t = threading.Thread(target=go, daemon=True)
    t.start()

    def join():
        t.join(vp.sequence_seconds(steps) + 180)
        if t.is_alive():
            return "the input run did not finish"
        return box.get("err")
    return join


def read_focused(out_dir):
    """FILETIME the input script wrote to FOCUSED (game in front, before the first step), or None."""
    try:
        m = re.search(r"FOCUSED\s+(\d+)", (Path(out_dir) / "FOCUSED").read_text(encoding="utf-8-sig"))
    except OSError:
        return None
    return int(m.group(1)) if m else None


# ---------- head trim (--sequence) ----------

def trimmed_path(video):
    return Path(video).with_name(Path(video).stem + "_trimmed.mp4")


def trim_start(start_ft, focused_ft):
    """Seconds to cut from the video head: CUT_MARGIN after the game came to the front. Both are Windows
    FILETIMEs (100 ns) from the Legion clock. None if the game was in front before StartRecord (no cut)."""
    head = (focused_ft - start_ft) / 1e7
    return head + CUT_MARGIN if head > 0 else None


def trim_cmd(src, dst, start):
    """Re-encode from `start`: -ss before -i with a re-encode cuts on the exact frame. Size and fps are kept
    (no scale or fps filter); x264 + AAC is what the jam upload expects."""
    return ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(src),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(dst)]


def trim_head(video, start_ft, focused_ft):
    """Write trimmed_path(video) starting on the game. Returns note lines; never fails the take."""
    out = trimmed_path(video)
    out.unlink(missing_ok=True)  # never leave a stale cut that main() would print as the candidate
    if start_ft is None or focused_ft is None:
        missing = "StartRecord time (OBS script)" if start_ft is None else "FOCUSED time (input script)"
        return [f"WARNING: no head trim, the {missing} is missing; the untrimmed video may open on another window"]
    start = trim_start(start_ft, focused_ft)
    if start is None:
        return ["no head trim needed: the game was in front before OBS started recording"]
    rc, _, err = run(trim_cmd(video, out, start), timeout=600)
    dur = probe_duration(out) if rc == 0 and out.exists() else 0.0
    if dur <= 0:
        out.unlink(missing_ok=True)
        return [f"WARNING: head trim at {start:.2f} s failed (ffmpeg exit {rc}: {err.strip()[-120:]}); "
                "only the untrimmed video is on disk"]
    notes = [f"cut {start:.2f} s of head: {out} is {dur:.1f} s"]
    if not VIDEO_MIN <= dur <= VIDEO_MAX:
        notes.append(f"WARNING: the trimmed video is {dur:.1f} s; the jam video must be {VIDEO_MIN}-{VIDEO_MAX} s")
    return notes


# ---------- frame check ----------

def probe_duration(path):
    rc, out, _ = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], timeout=30)
    try:
        return float(out.strip())
    except ValueError:
        return 0.0


def frame_stats(path, t):
    """(mean, stddev) of a 64x36 gray frame at t seconds, or None if it cannot be decoded."""
    import subprocess
    try:
        p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
                            "-vf", "scale=64:36,format=gray", "-f", "rawvideo", "-"],
                           capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    px = p.stdout
    if len(px) != 64 * 36:
        return None
    mean = sum(px) / len(px)
    sd = math.sqrt(sum((v - mean) ** 2 for v in px) / len(px))
    return mean, sd


def check_video(path, points=(0.1, 0.3, 0.5, 0.7, 0.9), min_seconds=0.0):
    """Return (ok, problems). A frame is bad if it cannot be decoded or is flat (one colour:
    all black, or a solid error / crash screen). The take passes if at least half the frames are good."""
    dur = probe_duration(path)
    if dur <= 0:
        return False, ["video has no readable duration (corrupt or empty)"]
    problems = []
    if min_seconds and dur < min_seconds:
        problems.append(f"video is {dur:.1f}s, expected at least {min_seconds:.1f}s")
    good = 0
    for frac in points:
        t = dur * frac
        st = frame_stats(path, t)
        if st is None:
            problems.append(f"frame at {t:.1f}s could not be decoded")
        elif st[1] < 3.0:
            kind = "black" if st[0] < 12 else "flat (single colour)"
            problems.append(f"frame at {t:.1f}s is {kind}")
        else:
            good += 1
    ok = good * 2 >= len(points) and not (min_seconds and dur < min_seconds)
    return ok, problems


# ---------- orchestration ----------

def one_take(args, sleep=time.sleep):
    host = args.host
    # Mark OBS as ours when start_obs actually launches it (before the websocket wait), so a
    # timeout still closes what we launched, and an OBS that was already running is never touched.
    ours = []
    proc = game_process(args.game_name)
    try:
        start_obs(host, sleep=sleep, on_launch=lambda: ours.append(True))
        deployed = playtest.deploy_and_register(host, args.remote_zip, args.game_name, args.task_name)
        exe_path = (deployed or {}).get("exePath")
        exe_name = f"{args.game_name}.exe"
        if content_only(proc):  # content-only package: launch the engine exe directly
            rc, _, err = ssh(host, engine_launch_cmd(args.task_name, args.game_name))
            if rc != 0:  # the task would still start the blocked stub exe
                return False, None, [f"could not point the game task at UnrealGame.exe: {err.strip()[-120:]}"]
            # the firewall rule must cover the exe that really runs, not the stub
            exe_name = ENGINE_EXE
            exe_path = (exe_path.rsplit("\\", 1)[0] + "\\" + ENGINE_REL) if exe_path else None
        if exe_path:  # the firewall rule must cover the exe we actually deployed
            facts, fail = pre.collect(host)
            if fail:
                return False, None, [fail]
            bad = [f for f in pre.evaluate(facts, exe_name, exe_path, True)
                   if "firewall" in f.lower()]
            if bad:
                return False, None, bad
        rc, _, err = ssh(host, f"schtasks /Run /TN {args.task_name}")
        if rc != 0:
            return False, None, [f"could not run the game task: {err.strip()[-120:]}"]
        # The task also has a one-shot "+1 min" trigger; disable it so a short take that closes
        # the game cannot have it relaunch behind the recording (deploy re-registers with -Force).
        ssh(host, f'powershell -Command "Disable-ScheduledTask -TaskName {args.task_name} | Out-Null"')
        sleep(args.warmup)
        if not game_alive(host, proc):
            return False, None, [f"{args.game_name} is not running after launch (crashed or never started)"]
        steps = getattr(args, "input_steps", None)
        focused = None
        if steps:
            with tempfile.TemporaryDirectory() as td:  # the input run's folder (FOCUSED only); not kept
                join = start_input(args, steps, td)
                try:
                    taken = record_run(host, args.seconds, args.replay_seconds)
                finally:
                    input_err = join()  # never close the game under a running input task
                focused = read_focused(td)
            if input_err:
                return False, None, [f"the input sequence failed during the recording: {input_err}"]
        else:
            taken = record_run(host, args.seconds, args.replay_seconds)
        remote_file = taken["recordFile"]
        if not game_alive(host, proc):
            return False, None, [f"{args.game_name} died during the recording; the video is not a valid take"]
        close_process(host, proc, sleep=sleep)
        local = fetch(host, remote_file, args.out_dir)
        ok, problems = check_video(local, min_seconds=args.seconds * 0.8)
        if ok and steps:
            problems += trim_head(local, taken.get("startRecordFileTimeUtc"), focused)
        return ok, local, problems
    finally:
        close_process(host, proc, sleep=sleep)
        if ours and not args.keep_obs:
            close_process(host, "obs64", sleep=sleep)
        remove_task(host, OBS_TASK)
        # Whatever way we left, the game task's one-shot "+1 min" trigger must not fire later.
        ssh(host, f'powershell -Command "Disable-ScheduledTask -TaskName {args.task_name} | Out-Null"')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=pre.DEFAULT_HOST)
    ap.add_argument("--remote-zip", required=True)
    ap.add_argument("--game-name", required=True)
    ap.add_argument("--task-name", default="MegaJamLaunchGame")
    ap.add_argument("--seconds", type=int, default=40, help="how long to record")
    ap.add_argument("--replay-seconds", type=int, default=3, help="replay-buffer wait inside the OBS script (unused output)")
    ap.add_argument("--warmup", type=int, default=30, help="seconds to let the game load before recording "
                    "(30: a cold first start of a packaged game is slow)")
    ap.add_argument("--skip-probe", action="store_true", help="skip the lock / black-screen probe shot")
    ap.add_argument("--out-dir", default="video")
    ap.add_argument("--keep-obs", action="store_true", help="leave OBS open if we started it")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--attempts", type=int, default=2)
    ap.add_argument("--sequence", help="visual_playtest JSON of keys/waits/mouse to PLAY during the recording "
                    "(shot/declare dropped, burst = wait); --seconds must cover it")
    args = ap.parse_args(argv)

    args.input_steps = None
    if args.sequence:
        try:
            args.input_steps = load_input_steps(args.sequence)
        except (OSError, ValueError) as e:
            print(f"--sequence {args.sequence}: {e}")
            return 2
        need = seconds_needed(args.input_steps)
        if args.seconds < need:
            print(f"--seconds {args.seconds} is shorter than the input sequence: {HEAD} s head (trimmed off) + "
                  f"{LEAD_IN} s lead-in + keys and waits + {TAIL} s tail = {need} s. Pass --seconds {need} or more, "
                  "or shorten the sequence.")
            return 2

    if not args.skip_preflight:
        rc = pre.main(["--host", args.host, "--exe-name", f"{args.game_name}.exe", "--no-firewall", "--allow-obs-stopped", "--remove-stale"])
        if rc != 0:
            log("preflight failed; fix the lines above or pass --skip-preflight")
            return 1
    if not args.skip_probe:
        # OBS cannot start on a locked console and a black screen records black: look once first.
        msg = pre.probe_message(args.host, lambda: _load("legion_capture_screenshot").take_probe(args.host))
        if msg:
            if msg == pre.MSG_LOCKED:
                msg += " OBS cannot start on a locked console."
            print(msg)
            return 1

    last = "no attempt ran"
    for n in range(1, args.attempts + 1):
        log(f"== take {n}/{args.attempts} ==")
        try:
            ok, local, problems = one_take(args)
        except Exception as e:  # noqa: BLE001 - report and retry
            last = f"take {n} error: {e}"
            log(last)
            continue
        if ok:
            for p in problems:
                log(f"note: {p}")
            cut = trimmed_path(local)
            if args.input_steps and cut.exists():
                print(f"submission candidate (head trimmed, starts on the game): {cut}")
                print(f"untrimmed original: {local}")
            else:
                print(local)
            return 0
        last = f"take {n} failed" + (f" (video {local})" if local else "") + ": " + "; ".join(problems)
        log(last)
    print(last)
    return 1


if __name__ == "__main__":
    sys.exit(main())
