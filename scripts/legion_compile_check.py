#!/usr/bin/env python3
"""legion_compile_check: fast Win64 compile-only check on the Legion (minutes, not a 78-min package).

Why: Linux clang accepts code MSVC rejects (e.g. C4458 local hides member, dv.33/B8). Only a
Win64 compile finds those. This syncs Source/ Config/ Plugins/ + the .uproject of the planned
commit into the warm Legion project folder, then runs UBT for JumpCutEditor Win64 Development.

    python3 scripts/legion_compile_check.py PROJECT [--dry-run] [--target JumpCutEditor]

Runs scripts/shadow_lint.py first (seconds). Exit 0 = compiled, 1 = MSVC errors (printed), 2 = infra.
Uses the same ssh/scp options and warm folder as legion_ship.py; does not touch Packaged/ or push.
"""
import argparse
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import legion_ship as ls  # noqa: E402

SYNC_DIRS = ("Source", "Config", "Plugins")
ERR = re.compile(r"(error C\d+|error LNK\d+|fatal error|\berror:|Result: Failed)", re.I)


def pack(proj_dir, dest):
    def skip(ti):
        parts = Path(ti.name).parts
        if any(p in ("Binaries", "Intermediate", "Saved") for p in parts[1:]):
            return None
        return ti
    with tarfile.open(dest, "w") as tf:
        for u in proj_dir.glob("*.uproject"):
            tf.add(u, arcname=f"{proj_dir.name}/{u.name}")
        for d in SYNC_DIRS:
            if (proj_dir / d).is_dir():
                tf.add(proj_dir / d, arcname=f"{proj_dir.name}/{d}", filter=skip)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--host", default="device-host")
    ap.add_argument("--ssh", default="ssh")
    ap.add_argument("--scp", default="scp")
    ap.add_argument("--remote-root", default=r"C:\Dev\megajam-game-b8")
    ap.add_argument("--engine", default=r"C:\Dev\UE_5.9")
    ap.add_argument("--target", default="JumpCutEditor")
    ap.add_argument("--log", default="~/.local/state/megajam/legion_compile_check.log")
    ap.add_argument("--no-lint", action="store_true")
    a = ap.parse_args(argv)
    ctx = ls.Ctx(argparse.Namespace(**{**vars(a), "log_dir": "/tmp", "state_dir": "/tmp"}))
    uproject = ls.find_uproject(a.project)
    proj_dir = uproject.parent
    r_proj = ls.win(a.remote_root, proj_dir.name)
    r_in = ls.win(a.remote_root, "_cc_incoming")
    r_tar = ls.win(a.remote_root, "_cc_upload.tar")

    if not a.no_lint:
        here = Path(__file__).resolve().parent / "shadow_lint.py"
        p = subprocess.run([sys.executable, "-I", str(here), str(proj_dir / "Source")])
        if p.returncode:
            print("shadow_lint hits: fix or use --no-lint")
            return 1
    # A fresh stable root (first build in a new --remote-root) does not exist yet; scp cannot create it.
    ctx.remote(f'if not exist "{ls.win(a.remote_root)}" mkdir "{ls.win(a.remote_root)}"', "mkdir-root")
    with tempfile.TemporaryDirectory(prefix="legion_cc_") as td:
        arc = Path(td) / "cc.tar"
        if a.dry_run:
            print(f"  [tar] {SYNC_DIRS} + .uproject of {proj_dir} -> {arc}")
        else:
            pack(proj_dir, arc)
        ctx.local(ctx.scp + [str(arc), f"{a.host}:{ls.fwd(r_tar)}"], "scp")
    ctx.remote(f'if exist "{r_in}" rmdir /s /q "{r_in}"', "clean")
    ctx.remote(f'mkdir "{r_in}"', "mkdir")
    rc, out = ctx.remote(f'tar -xf "{r_tar}" -C "{r_in}"', "unpack")
    if rc:
        print("unpack failed:", out[-300:])
        return 2
    for d in SYNC_DIRS:  # mirror so deleted files vanish; Binaries/Intermediate untouched
        src = ls.win(r_in, proj_dir.name, d)
        rc, out = ctx.remote(
            f'if exist "{src}" robocopy "{src}" "{ls.win(r_proj, d)}" /MIR /XD Binaries Intermediate Saved '
            f'/NFL /NDL /NJH /NJS /NP', f"mirror-{d}")
        if rc >= 8:
            print(f"mirror {d} failed:", out[-300:])
            return 2
    ctx.remote(f'copy /y "{ls.win(r_in, proj_dir.name, uproject.name)}" "{ls.win(r_proj, uproject.name)}"', "uproject")
    ctx.remote(f'rmdir /s /q "{r_in}" & del /q "{r_tar}"', "cleanup")
    build = (f'"{ls.win(a.engine, "Engine", "Build", "BatchFiles", "Build.bat")}" {a.target} Win64 Development '
             f'-project="{ls.win(r_proj, uproject.name)}" -WaitMutex -NoHotReload')
    log = Path(a.log).expanduser()
    rc = ctx.remote_stream(build, "ubt", log)
    if a.dry_run:
        return 0
    text = log.read_text(errors="replace")
    errs = [ln for ln in text.splitlines() if ERR.search(ln) and "0 error" not in ln]
    if rc != 0 or errs:
        print(f"COMPILE FAILED (exit {rc}); {len(errs)} error line(s):")
        print("\n".join(errs[:20]))
        return 1
    print(f"COMPILE OK (Win64 {a.target}); log {log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
