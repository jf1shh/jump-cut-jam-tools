#!/usr/bin/env python3
"""One command from the PC: sync a UE project to the Legion, package it, check the exe, push to itch.

    python3 scripts/legion_ship.py PROJECT [--dry-run]

PROJECT is the folder holding the .uproject (or the .uproject itself).

Step 0 is a preflight (seconds): ssh, engine path, disk, leftover game processes, butler, itch DNS.
It fails fast, one line per problem, before the long sync/package. --dry-run runs it for real
(read-only). --from-step N resumes at step N. The push runs from the PC's butler by default
(--push-from legion for the old path). See stages/04_ship/references/legion-ship.md.

Steps (each timed; the summary line prints minutes per step):
  1 sync     tar the project (no Saved/Intermediate/DerivedDataCache/Packaged/.git), scp it to the
             Legion and unpack over the previous copy (so the remote DerivedDataCache survives);
             also ships scripts/package-and-push.ps1 and _config/reference/NOTICE.txt.
  2 package  ssh: run package-and-push.ps1 WITHOUT -ItchTarget (this script pushes, after the
             check). Its output is streamed live and tee'd to a local log file, so a failed
             package never leaves "no log" (mock jam 10, package #1).
  3 check    ssh: the staged exe must be sane. The root <GameName>.exe must exist. Content-only
             project (no Source folder): the stub launches Engine\\Binaries\\Win64\\UnrealGame.exe,
             so that must exist and must NOT have been renamed to .decoy-disabled. Project with
             Source: Binaries\\Win64\\<GameName>.exe must exist and the UnrealGame.exe decoy must be
             gone. A failed check stops the run; nothing is pushed.
  4 push     PC (default): tar+scp the staged root to the PC, butler push <copy> jf1shh/megajam-pretest:win64
             Legion (--push-from legion): ssh butler push <staged root> <target>
  5 status   butler status (same side as the push) until the build is no longer processing.

The packaging script must have the content-only fix from PR #97 (only rename the decoy when the
project has a Source folder). The local copy is checked for it; if it lacks it, the script is read
from --ps1-ref (default origin/mock10-findings). This script never edits the .ps1.

Remote commands go through cmd.exe (the Legion's default ssh shell). No PowerShell $variables are
sent over ssh, to avoid the escaping trouble seen in legion_playtest.py.
"""
import argparse
import base64
import ipaddress
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = "jf1shh/megajam-pretest:win64"
DEFAULT_BUTLER = r"C:\Users\shino\butler\butler.exe"
# Engine roots tried, in order, when --engine is not given (mock 11: the Legion has C:\Dev\UE_5.8).
ENGINE_CANDIDATES = (r"C:\Dev\UE_5.8", r"C:\UE_5.8")
MANIFEST_LINE = re.compile(r"^(.+)\|(\d+)\|([0-9a-fA-F]{64})$")
# Skipped only at the project root (Content/.../Build is real content) and, for the plugin-level
# ones, directly under Plugins/<Name>/.
# Root Build/ is NOT excluded: it holds project resources (Build/Windows/Application.ico).
EXCLUDE_DIRS = {"Binaries", "Saved", "Intermediate", "DerivedDataCache", "Packaged", ".git", ".vs", ".idea"}
PLUGIN_EXCLUDE_DIRS = {"Saved", "Intermediate"}
# Kept on the Legion across syncs (cook cache, build output); everything else is mirrored.
REMOTE_KEEP_DIRS = ("DerivedDataCache", "Saved", "Intermediate", "Packaged", "Binaries")
PENDING_WORDS = ("processing", "queued", "pending", "uploading", "waiting")
ERROR_WORDS = ("error", "failed", "fatal", "denied", "not found", "no such", "unauthorized", "invalid")
DONE_WORDS = ("processed", "finished", "complete", "ready", "up to date", "live")
# Debug symbols never ship (mock jam 16: a 2.5 GB .pdb in the stage). package-and-push.ps1 moves them to
# Packaged\Symbols; the fetch skips them too, so an older stage or .ps1 cannot push them to itch.
SYMBOL_EXTS = (".pdb", ".debug", ".sym")
FIX_MARKER = "$hasSource"  # the content-only guard in package-and-push.ps1 (PR #97)


class ShipError(Exception):
    pass


def win(*parts):
    return "\\".join(p.strip("\\") if i else p.rstrip("\\") for i, p in enumerate(parts))


def fwd(path):
    return path.replace("\\", "/")


class Ctx:
    def __init__(self, args):
        self.a = args
        self.dry = args.dry_run
        self.ssh = shlex.split(args.ssh)
        self.scp = shlex.split(args.scp)
        self.sleep = time.sleep
        self.steps = []  # (name, seconds)
        self.log = None
        self.fetch_dir = Path(args.log_dir).expanduser() / "stage"
        self.state_file = Path(args.state_dir).expanduser() / "stage.packaged-state"

    def say(self, msg):
        print(msg, flush=True)

    def remote(self, cmd, label, stdout_only=False):
        """Run one remote cmd.exe command; return (rc, stdout+stderr), or stdout alone with
        stdout_only (for output that gets parsed: ssh warnings land on stderr). Dry run only prints it."""
        full = self.ssh + [self.a.host, cmd]
        self.say(f"  [{label}] {' '.join(shlex.quote(x) for x in full)}")
        if self.dry:
            return 0, ""
        p = subprocess.run(full, capture_output=True, text=True, errors="replace")
        return p.returncode, p.stdout if stdout_only else p.stdout + p.stderr

    def probe(self, cmd, label, timeout=15):
        """Read-only remote command for preflight. Runs even in --dry-run (that is the point of
        validating paths on the Legion). Returns (rc, output); rc 124 on timeout."""
        full = self.ssh + [self.a.host, cmd]
        self.say(f"  [{label}] {' '.join(shlex.quote(x) for x in full)}")
        try:
            p = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return 124, f"timed out after {timeout}s"
        except OSError as e:
            return 127, str(e)
        return p.returncode, p.stdout + p.stderr

    def remote_stream(self, cmd, label, logfile):
        """Run a remote command, echo every line live and tee it into logfile."""
        full = self.ssh + [self.a.host, cmd]
        self.say(f"  [{label}] {' '.join(shlex.quote(x) for x in full)}")
        if self.dry:
            return 0
        logfile.parent.mkdir(parents=True, exist_ok=True)
        with open(logfile, "w", encoding="utf-8", errors="replace") as fh:
            fh.write(f"$ {' '.join(full)}\n")
            fh.flush()
            p = subprocess.Popen(full, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                 errors="replace", bufsize=1)
            for line in p.stdout:
                sys.stdout.write("    | " + line)
                fh.write(line)
                fh.flush()
            p.stdout.close()
            rc = p.wait()
            fh.write(f"\n[exit {rc}]\n")
        return rc

    def local(self, argv, label):
        self.say(f"  [{label}] {' '.join(shlex.quote(x) for x in argv)}")
        if self.dry:
            return
        p = subprocess.run(argv, capture_output=True, text=True)
        if p.returncode != 0:
            raise ShipError(f"{label} failed (exit {p.returncode}): {(p.stderr or p.stdout).strip()[-400:]}")


def find_uproject(project):
    p = Path(project).expanduser().resolve()
    if p.is_file() and p.suffix == ".uproject":
        return p
    if p.is_dir():
        found = sorted(p.glob("*.uproject"))
        if len(found) == 1:
            return found[0]
        if len(found) > 1:
            raise ShipError(f"more than one .uproject in {p}: {[f.name for f in found]}")
    raise ShipError(f"no .uproject found at {p}")


def resolve_ps1(a):
    """Return the text of a package-and-push.ps1 that has the content-only fix, and its source label."""
    local = Path(a.ps1)
    if local.is_file() and FIX_MARKER in local.read_text(encoding="utf-8", errors="replace"):
        return local.read_text(encoding="utf-8"), str(local)
    if a.ps1_ref:
        p = subprocess.run(["git", "-C", str(REPO), "show", f"{a.ps1_ref}:scripts/package-and-push.ps1"],
                           capture_output=True, text=True)
        if p.returncode == 0 and FIX_MARKER in p.stdout:
            return p.stdout, f"git:{a.ps1_ref}"
    raise ShipError(
        f"package-and-push.ps1 lacks the content-only fix ({FIX_MARKER}): neither {a.ps1} nor "
        f"{a.ps1_ref}:scripts/package-and-push.ps1 has it. Merge PR #97 or pass --ps1 / --ps1-ref.")


def make_archive(proj_dir, dest, notice, ps1_text):
    """tar of the project + the shipping scripts. Layout: <ProjName>/..., _ship/scripts, _ship/docs."""
    def skip(ti):
        parts = Path(ti.name).parts
        if len(parts) > 1 and parts[1] in EXCLUDE_DIRS:
            return None
        if len(parts) > 3 and parts[1] == "Plugins" and parts[3] in PLUGIN_EXCLUDE_DIRS:
            return None
        return ti

    with tarfile.open(dest, "w") as tf:
        tf.add(proj_dir, arcname=proj_dir.name, filter=skip)
        ps1_tmp = Path(dest).with_suffix(".ps1")
        ps1_tmp.write_text(ps1_text, encoding="utf-8")
        tf.add(ps1_tmp, arcname="_ship/scripts/package-and-push.ps1")
        tf.add(notice, arcname="_ship/_config/reference/NOTICE.txt")
        ps1_tmp.unlink()


SOURCE_STAMP = "SOURCE-STAMP.txt"  # in the remote _ship dir: what the last sync packed


def cmd_echo(text):
    """text made safe for a cmd.exe `echo ...>` (parentheses are special there)."""
    return text.replace("(", "^(").replace(")", "^)")


def source_stamp(ctx, proj_dir):
    """The dv commit (+ dirty-path count) of proj_dir now, taken when the tar is packed. A package step runs
    ~70 min, and commits made meanwhile are not in the build, so this must never be read at stamp time
    (b9b was stamped dv.68 while it packed dv.65). Returns None when dv fails; the stamp never fails the ship."""
    try:
        p = subprocess.run(["dv", "log", "-n", "1"], cwd=proj_dir, capture_output=True, text=True, timeout=30)
        m = re.search(r"commit (dv\.commit\.\d+)", p.stdout)
        dirty = subprocess.run(["dv", "status"], cwd=proj_dir, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError) as e:
        ctx.say(f"  WARNING: source stamp skipped: {e}")
        return None
    dirty_n = re.search(r"Total modified paths: (\d+)", dirty)
    commit = m.group(1) if m else "unknown"
    note = f" (+{dirty_n.group(1)} uncommitted paths in the tar)" if dirty_n else ""
    return f"{commit}{note} synced {datetime.now():%Y-%m-%d %H:%M:%S}"


def stamp_build(ctx, remote_ship, remote_stage, src):
    """Write BUILD.txt next to the staged exe: the source stamp from the sync + the staging time.
    A resumed run (--from-step 2+) has no sync of its own, so it reads the stamp that sync left on the Legion."""
    if src is None:
        rc, out = ctx.remote(f'type "{remote_ship}\\{SOURCE_STAMP}"', "read-source-stamp", stdout_only=True)
        src = out.strip() if rc == 0 and out.strip() else None
    if src is None:
        ctx.say("  WARNING: no source stamp from a sync; BUILD.txt says the source is unknown")
        src = "unknown source (no sync stamp)"
    text = f"{src} staged {datetime.now():%Y-%m-%d %H:%M:%S}"
    ctx.say(f"  BUILD STAMP: {text}")
    ctx.remote(f'echo {cmd_echo(text)}> "{remote_stage}\\BUILD.txt"', "stamp")


def exe_check(ctx, remote_stage, game, content_only):
    """Return a list of problems (empty = sane). Each probe is one `if exist` over ssh."""
    unreal = win(remote_stage, "Engine", "Binaries", "Win64", "UnrealGame.exe")
    decoy = unreal + ".decoy-disabled"
    probes = [(win(remote_stage, f"{game}.exe"), True, f"root stub {game}.exe")]
    own = win(remote_stage, game, "Binaries", "Win64", f"{game}.exe")
    if content_only:
        # The stub's target: Engine\Binaries\Win64\UnrealGame.exe on an installed engine, or a project-named
        # <game>\Binaries\Win64\<game>.exe when a source engine builds the target (UE 5.9, mock jam 16).
        # One of the two must exist.
        probes += [((unreal, own), True, f"the stub's target (UnrealGame.exe or {game}\\Binaries\\Win64\\{game}.exe)"),
                   (decoy, False, "UnrealGame.exe.decoy-disabled (content-only must not be renamed)")]
    else:
        probes += [(own, True, f"{game}\\Binaries\\Win64\\{game}.exe"),
                   (unreal, False, "UnrealGame.exe decoy (must be disabled)")]
    problems = []
    for path, want, what in probes:
        hits = []
        for one in (path if isinstance(path, tuple) else (path,)):  # a tuple: any one of them is enough
            rc, out = ctx.remote(f'if exist "{one}" (echo EXISTS) else (echo MISSING)', "check")
            if ctx.dry:
                continue
            if rc != 0 or not ("EXISTS" in out or "MISSING" in out):
                problems.append(f"{what}: probe failed (exit {rc}): {out.strip()[-200:]}")
                hits = None
                break
            hits.append("EXISTS" in out and "MISSING" not in out)
        if ctx.dry or hits is None:
            continue
        if any(hits) != want:
            problems.append(f"{what}: {'missing' if want else 'present but must not be'}")
    return problems


def publish_target_state(ctx, pub):
    """One remote probe of the --publish-root target: 'MISSING', 'EMPTY' or 'NONEMPTY'. The state token on stdout
    decides, whatever the exit code: the EMPTY branch echoes after a failing findstr (errorlevel 1) and cmd's echo
    does not reset it, so a healthy probe of an empty folder can exit 1. A probe that prints none of the three
    (ssh down, cmd error) raises ShipError (never guess: robocopy /MIR would replace the folder)."""
    rc, out = ctx.remote(f'if exist "{pub}" (dir /b /a "{pub}" 2>nul | findstr "^" >nul && (echo NONEMPTY) '
                         f'|| (echo EMPTY)) else (echo MISSING)', "publish-check", stdout_only=True)
    if ctx.dry:
        return "MISSING"
    seen = {ln.strip() for ln in out.splitlines()}
    for state in ("NONEMPTY", "EMPTY", "MISSING"):
        if state in seen:
            return state
    raise ShipError(f"could not check the publish target {pub} (exit {rc}): {out.strip()[-200:]}")


def _table_build_state(text):
    """Parse butler's status table. A processed build is '√ #<id>' in the BUILD column; '#<id>' without
    the tick, or an empty cell, means still processing. Returns None when there is no table."""
    col = None
    states = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if col is None:
            if any(c.upper() == "BUILD" for c in cells):
                col = [c.upper() for c in cells].index("BUILD")
            continue
        if col < len(cells):
            cell = cells[col]
            done = re.search(r"#\d+", cell) and re.search(r"[√✓✔]", cell)
            states.append("done" if done else "pending")
    if not states:
        return None
    return "pending" if "pending" in states else "done"


def status_state(text):
    """'error' on error text, 'pending' while processing, 'done' only on a positive marker.
    Anything unrecognised stays 'pending' (keep polling, then time out) rather than guessing success."""
    low = text.lower()
    if any(w in low for w in ERROR_WORDS):
        return "error"
    table = _table_build_state(text)
    if table:
        return table
    if any(w in low for w in PENDING_WORDS):
        return "pending"
    if any(w in low for w in DONE_WORDS):
        return "done"
    return "pending"


def status_done(text):
    return status_state(text) == "done"


def cmdq(cmd):
    """cmd /c strips the first and last quote when a command starts with a quote and has more than
    two; wrapping the whole command in one more pair keeps the inner quotes intact."""
    return f'"{cmd}"' if cmd.startswith('"') else cmd


def remote_manifest(ctx, r_stage):
    """{rel path (forward slashes): (size, sha256)} of the staged build, hashed on the Legion.
    None when the Legion cannot produce one (the caller then copies everything)."""
    # Any error (a locked file, a path too long to hash) must end the script with exit 1 and no end marker,
    # never leave a file silently out. The last line, #END|<n>, is the file COUNT from the directory listing,
    # taken before hashing, so the caller can check every file came back.
    ps = ("$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue';"
          "try{[Console]::OutputEncoding=(New-Object Text.UTF8Encoding $false);"
          f"$r='{r_stage}';$n=$r.TrimEnd('\\').Length+1;"
          "$f=@(Get-ChildItem -LiteralPath $r -Recurse -File -Force|Where-Object{$_.Extension -notin "
          + ",".join(f"'{e}'" for e in SYMBOL_EXTS) + "});"
          "foreach($x in $f){$x.FullName.Substring($n).Replace('\\','/')+'|'+$x.Length+'|'+"
          "(Get-FileHash -LiteralPath $x.FullName -Algorithm SHA256).Hash.ToLower()};"
          "'#END|'+$f.Count}catch{[Console]::Error.WriteLine($_.Exception.Message);exit 1}")
    enc = base64.b64encode(ps.encode("utf-16-le")).decode()
    rc, out = ctx.remote(f"powershell -NoProfile -NonInteractive -EncodedCommand {enc}", "stage-manifest",
                         stdout_only=True)
    if rc != 0:
        return None
    man = {}
    parsed = 0
    expected = None
    for line in out.lstrip("﻿").splitlines():
        line = line.strip().lstrip("﻿")
        if not line:
            continue
        end = re.fullmatch(r"#END\|(\d+)", line)
        if end:
            expected = int(end.group(1))
            continue
        if expected is not None:  # nothing may follow the end marker
            return None
        m = MANIFEST_LINE.match(line)
        if not m:  # a broken line (hash failure, stray warning) would silently drop a file: no manifest
            return None
        rel = m.group(1)
        if rel.startswith("/") or ".." in rel.split("/") or ":" in rel:
            return None
        if not rel.isascii():  # code-page garble over ssh, and tar -T list encoding: whole copy is safe
            return None
        man[rel] = (int(m.group(2)), m.group(3).lower())
        parsed += 1
    if expected is None or parsed != expected or len(man) != parsed:  # missing marker or a lost file
        return None
    return man or None


def read_local_manifest(path):
    """The manifest saved after the last good fetch; None when missing or unreadable."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return {k: (int(v[0]), str(v[1])) for k, v in data["files"].items()}
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError):
        return None


def write_local_manifest(path, man):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps({"version": 1, "files": {k: list(v) for k, v in sorted(man.items())}}),
                   encoding="utf-8")
    os.replace(tmp, path)


def changed_files(new, old, dest):
    """Files to copy: new, different in size/hash from the last fetch, or missing/wrong size in dest."""
    out = []
    for rel, (size, digest) in sorted(new.items()):
        f = dest.joinpath(*rel.split("/"))
        if old.get(rel) != (size, digest) or not f.is_file() or f.stat().st_size != size:
            out.append(rel)
    return out


def fetch_stage(ctx, r_stage, r_ship):
    """Copy the staged build from the Legion to ctx.fetch_dir on the PC (tar over scp: the stage is
    thousands of small files). Returns the local folder.
    A manifest (path, size, sha256) of the last fetch is kept beside the folder; the next run copies only
    the files that changed and deletes the ones that vanished. --full, or a missing/unreadable manifest,
    or none from the Legion, copies everything and replaces the earlier copy."""
    r_tar = win(r_ship, "stage.tar")
    dest = ctx.fetch_dir
    mpath = dest.parent / (dest.name + ".manifest.json")
    ctx.say("4/5 fetch the staged build to the PC")
    new = remote_manifest(ctx, r_stage)
    old = None
    if ctx.dry:
        ctx.say(f"  [manifest] compare with {mpath}; copy only changed files unless --full")
        ctx.say(f"  [scp] {ctx.a.host}:{fwd(r_tar)} -> {dest}.tar, then unpack to {dest}")
        return dest
    if ctx.a.full:
        ctx.say("  --full: copying the whole staged build")
    elif new is None:
        ctx.say("  no manifest from the Legion: copying the whole staged build")
    else:
        old = read_local_manifest(mpath)
        if old is None:
            ctx.say("  no usable manifest from the last fetch: copying the whole staged build")
        elif not dest.is_dir():
            old = None
            ctx.say("  the last fetched copy is gone: copying the whole staged build")
    delta = new is not None and old is not None
    names = changed_files(new, old, dest) if delta else []
    dest.parent.mkdir(parents=True, exist_ok=True)
    mpath.unlink(missing_ok=True)  # first: an interrupted fetch must not leave a manifest that lies
    if delta:
        gone = sorted(set(old) - set(new))
        for rel in gone:
            f = dest.joinpath(*rel.split("/"))
            f.unlink(missing_ok=True)
            for parent in f.parents:  # prune folders this removal emptied
                if parent == dest:
                    break
                try:
                    parent.rmdir()
                except OSError:
                    break
        for rel in names:  # a folder became a file, or a file became a folder
            f = dest.joinpath(*rel.split("/"))
            if f.is_dir():
                shutil.rmtree(f)
            for parent in f.parents:
                if parent == dest:
                    break
                if parent.is_file() or parent.is_symlink():
                    parent.unlink()
        if not names:
            ctx.say(f"  nothing changed: all {len(new)} files already on the PC, copied 0, removed {len(gone)}")
            write_local_manifest(mpath, new)
            return dest
        ctx.say(f"  changed: copying {len(names)} of {len(new)} files, removed {len(gone)}")
    local_tar = dest.with_suffix(".tar")
    if delta:
        r_list = win(r_ship, "stage-files.txt")
        with tempfile.TemporaryDirectory(prefix="legion_ship_") as td:
            lst = Path(td) / "stage-files.txt"
            lst.write_text("\n".join(names) + "\n", encoding="utf-8")
            ctx.local(ctx.scp + [str(lst), f"{ctx.a.host}:{fwd(r_list)}"], "scp-stage-list")
        tar_cmd = f'tar -cf "{r_tar}" -C "{r_stage}" -T "{r_list}"'
    else:
        excl = " ".join(f'--exclude=*{e}' for e in SYMBOL_EXTS)
        tar_cmd = f'tar -cf "{r_tar}" {excl} -C "{r_stage}" .'
    rc, out = ctx.remote(tar_cmd, "stage-tar")
    if rc != 0:
        raise ShipError(f"remote tar of the stage failed (exit {rc}): {out.strip()[-300:]}")
    try:
        ctx.local(ctx.scp + [f"{ctx.a.host}:{fwd(r_tar)}", str(local_tar)], "scp-stage")
        if not delta and dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(exist_ok=True)
        with tarfile.open(local_tar) as tf:
            if hasattr(tarfile, "data_filter"):
                tf.extractall(dest, filter="data")
            else:
                tf.extractall(dest)
    except (tarfile.TarError, OSError) as e:
        raise ShipError(f"fetching the stage failed: {e}")
    finally:
        local_tar.unlink(missing_ok=True)
    ctx.remote(f'del /q "{r_tar}"', "stage-tar-cleanup")
    if new is not None:
        bad = [r for r, (size, _) in new.items()
               if not dest.joinpath(*r.split("/")).is_file() or dest.joinpath(*r.split("/")).stat().st_size != size]
        if bad:
            raise ShipError(f"fetched copy does not match the Legion manifest ({len(bad)} files, e.g. {bad[0]}); "
                            f"rerun with --full")
        write_local_manifest(mpath, new)
    return dest


ITCH_API_HOST = "api.itch.io"
DNS_TIMEOUT = 8


def resolve_host(name):
    """Resolve name or raise OSError. getaddrinfo has no timeout of its own, so run it in a daemon
    thread and give up after DNS_TIMEOUT seconds (a hung resolver must not eat the 30 s budget)."""
    box = {}

    def work():
        try:
            infos = socket.getaddrinfo(name, 443)
            if all(_sinkhole(i[4][0]) for i in infos):
                box["err"] = OSError(f"{name} resolves only to a sinkhole address (blocked by the DNS server?)")
            else:
                box["ok"] = True
        except OSError as e:
            box["err"] = e

    t = threading.Thread(target=work, daemon=True)
    t.start()
    t.join(DNS_TIMEOUT)
    if "ok" in box:
        return
    raise box.get("err") or OSError(f"no answer after {DNS_TIMEOUT}s")


def nslookup_ok(text):
    """Judge the answer, not the header: Windows nslookup prints 'DNS request timed out' for the
    reverse lookup of its own server (no PTR record) and still answers the real query. A resolved
    name is a 'Name:' line; failure words (can't find, Non-existent...) override it."""
    low = text.lower()
    if any(w in low for w in ("can't find", "non-existent", "server failed", "refused", "unknown host")):
        return False
    m = re.search(r"^\s*name:\s*\S", low, re.M)
    if not m:
        return False
    # A Pi-hole sinkholes a blocked name to 0.0.0.0 / :: : only real addresses count.
    ips = re.findall(r"\d{1,3}(?:\.\d{1,3}){3}|[0-9a-f]*:[0-9a-f:]*[0-9a-f:]", low[m.end():])
    return any(not _sinkhole(ip) for ip in ips)


def _sinkhole(ip):
    try:
        addr = ipaddress.ip_address(ip.split("%")[0])
    except ValueError:
        return True
    # api.itch.io is never on a private/LAN/link-local address: that is a Pi-hole answering a blocked
    # name (default 0.0.0.0, or BLOCKINGMODE=IP with its own LAN address).
    return addr.is_unspecified or addr.is_loopback or addr.is_private or addr.is_link_local


def running_images(tasklist_csv):
    """Lower-cased image names from `tasklist /FO CSV /NH` output."""
    return {m.group(1).lower() for m in re.finditer(r'^"([^"]+)"', tasklist_csv, re.M)}


def leftover_images(game):
    return {"unrealgame.exe", f"{game}.exe".lower(), f"{game}-win64-shipping.exe".lower()}


def free_bytes_from_dir(text):
    m = re.findall(r"([\d,.\s]+)\s+bytes free", text)
    if not m:
        return None
    digits = re.sub(r"\D", "", m[-1])
    return int(digits) if digits else None


def _existing_ancestor(path):
    p = Path(path).expanduser()
    while not p.exists() and p != p.parent:
        p = p.parent
    return p


def read_stage_state(ctx):
    try:
        return ctx.state_file.read_text().strip()
    except OSError:
        return ""


def write_stage_state(ctx, value):
    if ctx.dry:
        return
    ctx.state_file.parent.mkdir(parents=True, exist_ok=True)
    ctx.state_file.write_text(value + "\n")


def engine_runuat(root):
    return win(root, "Engine", "Build", "BatchFiles", "RunUAT.bat")


def resolve_engine(ctx):
    """Set ctx.a.engine when --engine was not given: probe ENGINE_CANDIDATES on the Legion, first hit wins.
    An explicit --engine is left alone. Returns None on success, else the problem text."""
    a = ctx.a
    if a.engine:
        return None
    tried = ", ".join(ENGINE_CANDIDATES)
    for root in ENGINE_CANDIDATES:
        rc, out = ctx.probe(f'if exist "{engine_runuat(root)}" (echo EXISTS) else (echo MISSING)', "engine")
        if rc == 0 and "EXISTS" in out and "MISSING" not in out:
            a.engine = root
            ctx.say(f"  engine: {root}")
            return None
        if rc != 0 or not ("EXISTS" in out or "MISSING" in out):
            # An unanswered preferred path must not let a lower one win: stop, do not guess.
            return f"engine probe failed for {root} (exit {rc}: {out.strip()[-80:]}); tried {tried}; rerun or pass --engine"
    return f"engine path wrong on the Legion: no RunUAT.bat under any of: {tried}; pass --engine"


def preflight(ctx, game, r_stage, from_step, marker):
    """Cheap checks that fail in seconds instead of after the 12-minute package step.
    Prints one line per problem and raises ShipError listing them. Read-only: it also runs under
    --dry-run (only the --kill-leftovers kill is skipped there)."""
    a = ctx.a
    problems = []
    to_kill = []
    ctx.say("0/5 preflight")

    def bad(msg):
        problems.append(msg)
        ctx.say(f"  PREFLIGHT FAIL: {msg}")

    def exists(path, label):
        rc, out = ctx.probe(f'if exist "{path}" (echo EXISTS) else (echo MISSING)', label)
        if rc != 0 or not ("EXISTS" in out or "MISSING" in out):
            return None, out
        return ("EXISTS" in out and "MISSING" not in out), out

    # A status-only resume from the PC (--from-step 5) runs butler on the PC and needs nothing on the Legion.
    pc_status_only = from_step == 5 and a.push_from == "pc"
    if not pc_status_only:
        rc, out = ctx.probe("echo OK", "ssh")
        if rc != 0 or "OK" not in out:
            bad(f"ssh to {a.host} failed (exit {rc}): {out.strip()[-120:] or 'no output'}")
            raise ShipError(f"preflight failed: {problems[0]}")

    if from_step <= 2:
        if not a.engine:
            err = resolve_engine(ctx)
            if err:
                bad(err)
        else:
            runuat = engine_runuat(a.engine)
            got, out = exists(runuat, "engine")
            if got is None:
                bad(f"engine probe failed: {out.strip()[-120:]}")
            elif not got:
                bad(f"engine path wrong on the Legion: {runuat} does not exist (--engine {a.engine})")
        # The root may not exist yet (sync's mkdir creates it): walk up to the nearest existing parent.
        free, out, not_found = None, "", True
        probe_path = a.remote_root.rstrip("\\")
        while True:
            rc, out = ctx.probe(f'dir /-c "{probe_path}\\"', "disk")
            free = free_bytes_from_dir(out) if rc == 0 else None
            not_found = not_found and "file not found" in out.lower()
            parent = probe_path.rpartition("\\")[0]
            if free is not None or not parent or parent == probe_path:
                break
            probe_path = parent
        if free is None and not_found:
            ctx.say(f"  [note] {a.remote_root} does not exist yet on the Legion; disk check skipped (sync creates it)")
        elif free is None:
            bad(f"cannot read free disk for {a.remote_root} on the Legion: {out.strip()[-120:]}")
        elif free < a.min_free_gb * 2**30:
            bad(f"Legion disk low: {free / 2**30:.1f} GB free on {a.remote_root}, need {a.min_free_gb} GB")
    elif not pc_status_only:
        got, out = exists(win(r_stage, f"{game}.exe"), "stage")
        if not got:
            bad(f"--from-step {from_step} needs the packaged build, but {win(r_stage, f'{game}.exe')} "
                f"is not on the Legion; start at step 2")
        else:
            # The stage can be left by a package step that failed AFTER RunUAT staged it (zip over the
            # gate, NOTICE missing): only a stage whose package step finished OK carries the marker.
            # The PC also keeps its own record, written "invalid" BEFORE the remote marker is touched,
            # so a marker the Legion failed to delete (ssh drop) is still not trusted.
            got, out = exists(marker, "stage-marker")
            if got and read_stage_state(ctx) != "ok":
                bad(f"--from-step {from_step}: the last ship on this PC did not finish packaging cleanly "
                    f"({ctx.state_file}); the marker on the Legion cannot be trusted; start at step 2")
            elif not got:
                bad(f"--from-step {from_step}: the packaged build on the Legion is not marked as finished "
                    f"by a successful package step ({marker} missing; a failed package leaves a rejected "
                    f"or old build); start at step 2")

    if from_step <= 3:
        rc, out = ctx.probe('tasklist /FO CSV /NH', "procs")
        if rc != 0:
            bad(f"cannot list processes on the Legion (exit {rc}): {out.strip()[-120:]}")
        else:
            left = sorted(running_images(out) & leftover_images(game))
            if left and a.kill_leftovers:
                to_kill = left  # killed below, only once every read-only check has passed
            elif left:
                bad(f"leftover game processes running on the Legion: {', '.join(left)} "
                    f"(close them, or pass --kill-leftovers)")

    if from_step <= 5:
        if a.push_from == "pc":
            if not shutil.which(a.pc_butler):  # also true only for an executable file path
                bad(f"butler not found or not executable on the PC: {a.pc_butler} (--pc-butler)")
            if from_step <= 4:
                anc = _existing_ancestor(ctx.fetch_dir.parent)
                free = shutil.disk_usage(anc).free
                if free < a.min_free_gb * 2**30:
                    bad(f"PC disk low: {free / 2**30:.1f} GB free at {anc}, need {a.min_free_gb} GB")
            try:
                resolve_host(ITCH_API_HOST)
            except OSError as e:
                bad(f"DNS: the PC cannot resolve {ITCH_API_HOST} ({e}); the itch push would fail")
        else:
            got, out = exists(a.butler, "butler")
            if got is None:
                bad(f"butler probe failed: {out.strip()[-120:]}")
            elif not got:
                bad(f"butler missing on the Legion: {a.butler} (--butler)")
            rc, out = ctx.probe(f"nslookup {ITCH_API_HOST}", "dns")
            if rc != 0 or not nslookup_ok(out):
                bad(f"DNS: the Legion cannot resolve {ITCH_API_HOST}; the itch push would fail "
                    f"({out.strip()[-100:]})")

    if problems:
        raise ShipError(f"preflight failed ({len(problems)}): " + " | ".join(problems))
    if to_kill and ctx.dry:
        ctx.say(f"  [dry-run] would kill leftover processes: {', '.join(to_kill)}")
    elif to_kill:
        for name in to_kill:
            ctx.probe(f'taskkill /F /T /IM "{name}"', "kill")
        rc, out = ctx.probe('tasklist /FO CSV /NH', "procs-recheck")
        still = sorted(running_images(out) & leftover_images(game)) if rc == 0 else to_kill
        if still:
            bad(f"could not kill leftover processes on the Legion: {', '.join(still)}")
            raise ShipError(f"preflight failed (1): {problems[0]}")
    ctx.say("  preflight ok")


def timed(ctx, name, fn):
    t0 = time.monotonic()
    try:
        return fn()
    finally:
        ctx.steps.append((name, time.monotonic() - t0))


def summary(ctx, ok, note):
    parts = " ".join(f"{n} {s / 60:.1f}m" for n, s in ctx.steps)
    total = sum(s for _, s in ctx.steps) / 60
    return f"{'SHIPPED' if ok else 'STOPPED'}: {note} | {parts} | total {total:.1f}m"


def ship(ctx):
    a = ctx.a
    uproject = find_uproject(a.project)
    proj_dir = uproject.parent
    game = a.game_name or uproject.stem
    team = a.team
    for label, val in (("game name", game), ("team", team), ("project folder", proj_dir.name)):
        if re.search(r"\s", val) or not val:
            raise ShipError(f"{label} {val!r} must be one token with no spaces (remote cmd quoting)")
    content_only = not (proj_dir / "Source").is_dir()
    notice = Path(a.notice)
    if not notice.is_file():
        raise ShipError(f"NOTICE file not found: {notice}")
    ps1_text, ps1_src = resolve_ps1(a)
    ctx.say(f"project {uproject} ({'content-only' if content_only else 'has C++ Source'}); ps1 from {ps1_src}")

    root = a.remote_root
    r_proj = win(root, proj_dir.name)
    r_uproject = win(r_proj, uproject.name)
    r_ship = win(root, "_ship")
    r_ps1 = win(r_ship, "scripts", "package-and-push.ps1")
    r_stage = win(r_proj, "Packaged", "Windows")
    r_tar = win(r_ship, "upload.tar")
    log = Path(a.log_dir).expanduser() / f"{proj_dir.name}-{datetime.now():%Y%m%d-%H%M%S}.log"
    ctx.fetch_dir = Path(a.log_dir).expanduser() / f"stage-{proj_dir.name}"
    start = a.from_step
    # Written after a successful package step, removed before sync/package starts: a resume at step
    # 3+ only trusts a stage that carries it (a failed package can leave a rejected or old build).
    marker = win(r_ship, f"{proj_dir.name}.packaged-ok")
    ctx.state_file = Path(a.state_dir).expanduser() / f"{proj_dir.name}.packaged-state"  # PC-side twin of the marker

    if not a.no_preflight:
        preflight(ctx, uproject.stem, r_stage, start, marker)  # RunUAT names exes after the .uproject
    if start <= 1 and not ctx.dry and not getattr(a, "skip_compile_check", False):
        # Required (hub 2026-11-12): a Win64 compile finds MSVC-only errors in ~1 min, not after a 78 min package.
        ctx.say("0b/5 Win64 compile check (legion_compile_check.py)")
        cc = [sys.executable, "-I", str(Path(__file__).resolve().parent / "legion_compile_check.py"), str(uproject),
              "--host", a.host, "--ssh", a.ssh, "--scp", a.scp, "--remote-root", a.remote_root]
        if a.engine:
            cc += ["--engine", a.engine]
        if subprocess.run(cc).returncode != 0:
            raise ShipError("Win64 compile check failed; not packaging (see output above)")
    if start <= 2 and not a.engine:  # --no-preflight: no probes, so take the first candidate blind
        a.engine = ENGINE_CANDIDATES[0]
    if start > 1:
        ctx.say(f"resuming at step {start}: steps 1-{start - 1} skipped")

    def clear_marker():
        write_stage_state(ctx, "invalid")  # first, so a failed remote delete cannot leave a trusted stage
        rc, out = ctx.remote(f'if exist "{marker}" del /q "{marker}"', "clear-marker")
        if rc != 0:  # a surviving marker would let a rejected new stage pass for a good one
            raise ShipError(f"could not clear the packaged marker {marker} (exit {rc}): {out.strip()[-200:]}; "
                            f"not packaging")

    # 1 sync
    r_src_stamp = win(r_ship, SOURCE_STAMP)
    synced = {"src": None}

    def sync():
        ctx.say("1/5 sync")
        ctx.remote(f'if not exist "{r_ship}" mkdir "{r_ship}"', "mkdir")
        clear_marker()
        # A stale stamp would label a half-synced tree with the previous sync's commit.
        ctx.remote(f'if exist "{r_src_stamp}" del /q "{r_src_stamp}"', "clear-source-stamp")
        synced["src"] = source_stamp(ctx, proj_dir)
        with tempfile.TemporaryDirectory(prefix="legion_ship_") as td:
            arc = Path(td) / "upload.tar"
            if ctx.dry:
                ctx.say(f"  [tar] pack {proj_dir} (skip {sorted(EXCLUDE_DIRS)}) + ps1 + NOTICE -> {arc}")
            else:
                make_archive(proj_dir, arc, notice, ps1_text)
            ctx.local(ctx.scp + [str(arc), f"{a.host}:{fwd(r_tar)}"], "scp")
        # Unpack into a fresh staging dir, then MIRROR it onto the project so files deleted or
        # renamed on the PC are deleted on the Legion too (a stale Source folder would re-trigger the
        # decoy rename; a stale broken asset would still be cooked). The cook cache and old build
        # output dirs are excluded from the mirror (so kept, never copied or deleted).
        r_in = win(root, "_incoming")
        ctx.remote(f'if exist "{r_in}" rmdir /s /q "{r_in}"', "clean-incoming")
        ctx.remote(f'mkdir "{r_in}"', "mkdir-incoming")
        rc, out = ctx.remote(f'tar -xf "{r_tar}" -C "{r_in}"', "unpack")
        if rc != 0:
            raise ShipError(f"remote unpack failed (exit {rc}): {out.strip()[-300:]}")
        keep = " ".join(f'"{win(r_proj, d)}"' for d in REMOTE_KEEP_DIRS)
        for label, src, dst, flags in (
                ("robocopy-mirror", win(r_in, proj_dir.name), r_proj, f"/MIR /XD {keep}"),
                ("robocopy-ship", win(r_in, "_ship"), r_ship, "/E")):
            rc, out = ctx.remote(f'robocopy "{src}" "{dst}" {flags} /NFL /NDL /NJH /NJS /NP', label)
            if rc >= 8:  # robocopy: 0-7 are success codes
                raise ShipError(f"{label} failed (exit {rc}): {out.strip()[-300:]}")
        ctx.remote(f'rmdir /s /q "{r_in}"', "cleanup-incoming")
        if synced["src"]:
            ctx.say(f"  SOURCE STAMP: {synced['src']}")
            ctx.remote(f'echo {cmd_echo(synced["src"])}> "{r_src_stamp}"', "source-stamp")
    if start <= 1:
        timed(ctx, "sync", sync)

    # 2 package
    def package():
        ctx.say(f"2/5 package (log: {log})")
        cmd = (f'powershell -NoProfile -ExecutionPolicy Bypass -File "{r_ps1}" -EnginePath "{a.engine}" '
               f'-ProjectPath "{r_uproject}" -TeamName {team} -GameName {game}')
        clear_marker()
        rc = ctx.remote_stream(cmd, "package", log)
        if rc != 0:
            raise ShipError(f"package-and-push.ps1 failed (exit {rc}); log: {log}")
        rc, out = ctx.remote(f'echo ok> "{marker}"', "mark-packaged")
        if rc != 0:
            raise ShipError(f"could not write the packaged marker {marker} (exit {rc}): {out.strip()[-200:]}")
        write_stage_state(ctx, "ok")
    if start <= 2:
        timed(ctx, "package", package)

    # 3 check
    def check():
        ctx.say("3/5 exe check")
        problems = exe_check(ctx, r_stage, uproject.stem, content_only)  # RunUAT names exes after the .uproject
        if problems:
            raise ShipError("exe check failed, NOT pushing: " + "; ".join(problems))
        stamp_build(ctx, r_ship, r_stage, synced["src"])
        if a.publish_root:
            pub = win(a.publish_root, proj_dir.name, "Packaged", "Windows")
            if pub.rstrip("\\").lower() == r_stage.rstrip("\\").lower():
                raise ShipError(f"--publish-root resolves to the stage itself ({pub}); pick another folder")
            if not a.publish_overwrite and publish_target_state(ctx, pub) == "NONEMPTY":
                raise ShipError(f"publish target {pub} already holds an earlier build and robocopy /MIR would "
                                "replace it; pick another --publish-root, or pass --publish-overwrite to replace it")
            rc, out = ctx.remote(f'robocopy "{r_stage}" "{pub}" /MIR /NFL /NDL /NJH /NJS /NP', "publish")
            if rc >= 8:  # robocopy: 0-7 are success codes
                raise ShipError(f"publish copy to {pub} failed (exit {rc}): {out.strip()[-300:]}")
            ctx.say(f"  PUBLISHED: {pub}")
    if start <= 3:
        timed(ctx, "check", check)

    # 4 push. Default: the Legion only packages; the PC pulls the staged build and runs ITS butler
    # (the Legion's DNS failed for api.itch.io in mock 11). --push-from legion keeps the old path.
    pc = a.push_from == "pc"

    def run_butler(verb, label, stage=None):
        """Run `butler push <stage> <target>` or `butler status <target>` where the push runs;
        return (rc, output)."""
        if pc:
            argv = [shutil.which(a.pc_butler) or a.pc_butler, verb] + ([str(stage)] if stage else []) + [a.target]
            ctx.say(f"  [{label}] {' '.join(shlex.quote(x) for x in argv)}")
            if ctx.dry:
                return 0, ""
            try:
                p = subprocess.run(argv, capture_output=True, text=True)
            except OSError as e:
                raise ShipError(f"cannot run the PC butler {argv[0]}: {e}")
            return p.returncode, p.stdout + p.stderr
        mid = f' "{stage}"' if stage else ""
        return ctx.remote(cmdq(f'"{a.butler}" {verb}{mid} {a.target}'), label)

    def push():
        stage_dir = r_stage
        if pc:
            stage_dir = fetch_stage(ctx, r_stage, r_ship)
        ctx.say(f"4/5 push to {a.target} (from the {'PC' if pc else 'Legion'})")
        rc, out = run_butler("push", "push", stage_dir)
        if not ctx.dry:
            ctx.say("    | " + out.strip().replace("\n", "\n    | "))
        if rc != 0:
            raise ShipError(f"butler push failed (exit {rc})")
    if a.no_push:
        ctx.say("--no-push: stage only. Skipping the itch push and status. The staged build is on the Legion (Packaged\\Windows) and is NOT on itch.")
        return f"{game} staged only (no push); log {log}"
    if start <= 4:
        timed(ctx, "push", push)

    # 5 status
    def status():
        ctx.say("5/5 butler status")
        deadline = time.monotonic() + a.status_timeout
        while True:
            rc, out = run_butler("status", "status")
            if ctx.dry:
                return "dry run"
            state = status_state(out)
            if rc != 0 or state == "error":
                raise ShipError(f"butler status failed (exit {rc}): {out.strip()[-200:]}")
            if state == "done":
                return "processed"
            if time.monotonic() > deadline:
                raise ShipError(f"build still processing after {a.status_timeout / 60:.0f} min; check butler status")
            ctx.sleep(a.status_interval)
    state = timed(ctx, "status", status)
    return f"{game} -> {a.target} ({state}); log {log}"


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="folder with the .uproject, or the .uproject")
    ap.add_argument("--dry-run", action="store_true", help="print every command, run nothing")
    ap.add_argument("--host", default="device-host")
    ap.add_argument("--ssh", default="ssh", help="ssh command (tests point this at a fake)")
    ap.add_argument("--scp", default="scp", help="scp command (tests point this at a fake)")
    ap.add_argument("--remote-root", default=r"C:\Dev")
    ap.add_argument("--engine", default=None,
                    help="UE 5.8 install root on the Legion (default: probe " + " then ".join(ENGINE_CANDIDATES) + ")")
    ap.add_argument("--full", action="store_true",
                    help="step 4 (PC push): copy the whole staged build, ignore the manifest of the last fetch")
    ap.add_argument("--team", default="SecondUnit",
                    help="zip is TEAM_GAME.zip (Rule 10); owner picked team \"Second Unit\" 2026-11-12")
    ap.add_argument("--publish-root", default=None,
                    help="after the exe check, mirror Packaged\\Windows to PUBLISH_ROOT\\<project>\\Packaged\\Windows. Lets every build reuse one --remote-root (its Intermediate survives, so a unique build environment compiles the engine once) while each build still lands in its own folder")
    ap.add_argument("--publish-overwrite", action="store_true",
                    help="allow --publish-root to replace a folder that already holds a build (default: refuse a non-empty target)")
    ap.add_argument("--game-name", help="default: the .uproject name; only names the zip (-GameName)")
    ap.add_argument("--target", default=DEFAULT_TARGET)
    ap.add_argument("--butler", default=DEFAULT_BUTLER, help="butler.exe path on the Legion")
    ap.add_argument("--from-step", type=int, choices=range(1, 6), default=1, metavar="N",
                    help="resume at step N (1 sync, 2 package, 3 check, 4 push, 5 status); earlier steps are skipped")
    ap.add_argument("--push-from", choices=("pc", "device-host"), default="pc",
                    help="where butler runs: the PC (default; the Legion only packages) or the Legion (old path)")
    ap.add_argument("--pc-butler", default="butler", help="butler on the PC (name on PATH or full path)")
    ap.add_argument("--kill-leftovers", action="store_true",
                    help="preflight: kill leftover UnrealGame/<GameName> processes on the Legion instead of failing")
    ap.add_argument("--no-push", action="store_true", help="stage only: sync, package and check, then stop before the itch push (owner rule: no push until the owner passes the build)")
    ap.add_argument("--no-preflight", action="store_true", help="skip the preflight stage")
    ap.add_argument("--skip-compile-check", action="store_true",
                    help="skip the required Win64 compile check (legion_compile_check.py); emergencies only")
    ap.add_argument("--min-free-gb", type=float, default=20, help="preflight: minimum free disk, GB")
    ap.add_argument("--ps1", default=str(REPO / "scripts" / "package-and-push.ps1"))
    ap.add_argument("--ps1-ref", default="origin/mock10-findings", help="git ref to read the ps1 from if --ps1 lacks the fix")
    ap.add_argument("--notice", default=str(REPO / "_config" / "reference" / "NOTICE.txt"))
    ap.add_argument("--log-dir", default="~/.local/state/megajam/legion_ship")
    ap.add_argument("--state-dir", default="~/.local/state/megajam/legion_ship",
                    help="where the packaged-state file lives; keep it durable (not a job tmp dir) so --from-step N "
                         "still trusts the Legion's packaged marker after a tmp clean")
    ap.add_argument("--status-interval", type=float, default=30)
    ap.add_argument("--status-timeout", type=float, default=1200)
    return ap


def main(argv=None):
    ctx = Ctx(build_parser().parse_args(argv))
    try:
        note = ship(ctx)
    except ShipError as e:
        print(summary(ctx, False, str(e)))
        return 1
    print(summary(ctx, True, note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
