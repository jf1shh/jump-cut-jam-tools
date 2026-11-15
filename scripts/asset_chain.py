#!/usr/bin/env python3
"""One command: prompt (or reference image) -> game-ready Unreal prop. See stages/02_build/references/asset-chain.md.

  asset_chain.py --name crate --prompt "weathered wooden crate" --class prop
  asset_chain.py --queue work/queue.yaml --workers 4
  asset_chain.py --list-engines
"""
import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chain import engines as E  # noqa: E402
from chain import pipeline as P  # noqa: E402
from chain.licenses import LicenceGate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GPU_LOCK = Path.home() / ".cache/megajam/gpu.lock"  # machine-wide: any --out-dir shares one GPU
PROCEDURAL = ROOT / "scripts/procedural_props.py"  # Blender script; owned by another ticket, only called from here
DEFAULT_TRIES = 2
# Thin, flag-like and spoked shapes shred in the AI chain (mock 11: balloon ribbon, flag, pinwheel).
# _config/reference/canon/ai3d-acceptance-checklist.md says to go straight to a coded mesh for them.
THIN_KINDS = ("flag", "ribbon", "pinwheel", "fan")


def detach(script, argv, log, done, python=None, nohup="nohup"):
    """Re-run `script argv` under nohup in its own session; return the wrapper pid.

    Writes `log` (stdout+stderr), `done`.pid (the wrapper pid, so a waiter can tell a dead driver from a slow one)
    and, when the job ends, `done` containing "exit=N" (atomic rename). A stale done-file is removed first.
    Wait with `<script> --wait DONE`, `waitfor --file DONE --match exit=`, or Monitor on the done-file.
    """
    log, done = Path(log), Path(done)
    for p in (log, done):
        p.parent.mkdir(parents=True, exist_ok=True)
    pidf = Path(str(done) + ".pid")
    done.unlink(missing_ok=True)
    cmd = [python or sys.executable, str(script), *argv]
    # Each run writes its own `done.<pid>` and publishes to `done` only while `done.pid` still names it, so a
    # newer run on the same done-file is never answered with an older run's verdict.
    wrapper = ('"$@" >>"$LOG" 2>&1 </dev/null; rc=$?; '
               'printf "exit=%s\\n" "$rc" >"$DONE.$$.tmp" && mv "$DONE.$$.tmp" "$DONE.$$"; '
               'if [ "$(cat "$DONE.pid" 2>/dev/null)" = "$$" ]; then '
               'cp "$DONE.$$" "$DONE.$$.pub" && mv "$DONE.$$.pub" "$DONE"; fi')
    env = {**os.environ, "LOG": str(log), "DONE": str(done)}
    proc = subprocess.Popen([nohup, "sh", "-c", wrapper, "sh", *cmd], env=env, start_new_session=True,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    Path(f"{done}.{proc.pid}").unlink(missing_ok=True)  # a leftover from an older run that had this pid
    pidf.write_text(f"{proc.pid}\n")
    return proc.pid


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:  # a zombie is dead for our purposes
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return True


def wait_done(done, timeout=3600.0, interval=2.0, out=print):
    """Block until `done` exists (return its exit code) or the driver pid is gone without one (return 3).
    Prints the pid it is watching at arm time. Timeout returns 4."""
    done = Path(done)
    pidf = Path(str(done) + ".pid")
    pid = int(pidf.read_text().strip()) if pidf.is_file() else None
    out(f"waiting on {done} (driver pid {pid if pid else 'unknown'})")
    end = time.monotonic() + timeout
    watch = Path(f"{done}.{pid}") if pid is not None else done  # armed on one run: only its own verdict counts
    while True:
        # A per-run file is trusted only once its wrapper has exited (it writes the file as its last act), so a
        # stale done.<pid> left by an older run with the same pid can never answer a live run.
        if watch.is_file() and (pid is None or not pid_alive(pid)):
            text = watch.read_text().strip()
            out(f"done: {text}")
            try:
                return int(text.split("=", 1)[1])
            except (IndexError, ValueError):
                return 1
        if pid is not None and not pid_alive(pid) and not watch.is_file():  # re-check: it may have just finished
            out(f"driver pid {pid} is gone and wrote no done-file; read its log")
            return 3
        if time.monotonic() >= end:
            out(f"timed out after {timeout:g}s; driver pid {pid} still running")
            return 4
        time.sleep(interval)


def add_detach_args(ap, default_stem):
    ap.add_argument("--detach", action="store_true",
                    help="run in the background under nohup; print pid, log and done-file, then return at once")
    ap.add_argument("--wait", metavar="DONE", help="wait for a detached run's done-file (exits with the job's exit code; 3 = driver died)")
    ap.add_argument("--wait-timeout", type=float, default=3600.0)
    ap.add_argument("--detach-log", help=f"detached log (default work/{default_stem}.log)")
    ap.add_argument("--done-file", help=f"detached done-file (default work/{default_stem}.done)")


def handle_detach(a, script, argv, stem):
    """Shared --wait / --detach handling. Returns an exit code, or None to carry on and run the job."""
    if a.wait:
        return wait_done(a.wait, a.wait_timeout)
    if not a.detach:
        return None
    log = a.detach_log or str(ROOT / "work" / f"{stem}.log")
    done = a.done_file or str(ROOT / "work" / f"{stem}.done")
    cut = argv.index("--") if "--" in argv else len(argv)
    head, tail = argv[:cut], argv[cut:]  # tail starts with "--" when there is one
    child, it = [], iter(head)
    for t in it:  # only our own flags are stripped; everything after `--` is the user's command, untouched
        if t == "--detach":
            continue
        if t in ("--detach-log", "--done-file", "--wait-timeout"):
            next(it, None)
            continue
        if t.startswith(("--detach-log=", "--done-file=", "--wait-timeout=")):
            continue
        child.append(t)
    child += tail
    try:
        pid = detach(script, child, log, done)
    except RuntimeError as exc:
        print(f"detach refused: {exc}", file=sys.stderr)
        return 2
    print(f"detached pid {pid}\nlog  {log}\ndone {done}\n"
          f"wait: {Path(script).name} --wait {done}   (or: waitfor --file {done} --match exit=)")
    return 0


def gpu_preflight():
    p = subprocess.run(["gpu-preflight"], capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip()[-300:]


# ---- guarded run: bounded retries, coded fallback, one clear line ----

def procedural_props(path=PROCEDURAL):
    """Names the coded-prop script can build. Read from its `builders = {...}` dict with ast: the script
    imports bpy, so it cannot be imported here."""
    try:
        tree = ast.parse(Path(path).read_text())
    except (OSError, SyntaxError):
        return []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "builders" for t in node.targets)
                and isinstance(node.value, ast.Dict)):
            return [k.value for k in node.value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]
    return []


def _words(text):
    return [w for w in re.split(r"[^a-z0-9]+", (text or "").lower()) if w]


def thin_kind(spec):
    """The thin kind ('flag', 'pinwheel', ...) the spec names, or None. Head noun (last word of the name) only,
    plural allowed: the same word match_procedural uses, so `flag_pole` (a pole) is not a flag."""
    # Name only: a prompt like "no flags or ribbons" or "a flag painted on it" must not trip the rule.
    words = _words(spec.get("name"))
    if not words:
        return None
    last = words[-1]
    last = last[:-1] if last.endswith("s") and len(last) > 3 else last
    return last if last in THIN_KINDS else None


def match_procedural(spec, known):
    """A coded prop for this spec: exact name, then a word of the name, then a word of the prompt. Else None."""
    name = (spec.get("name") or "").lower()
    if name in known:
        return name
    # Name only, and only its head noun (last word): "red_crate" is a crate, but "crate_lid" is a lid and
    # "fence_flag" is a flag; neither may ship a whole coded crate or fence. A prop merely mentioned in the
    # prompt ("pinwheel stuck in a crate") is not the asset either.
    words = _words(name)
    if not words:
        return None
    last = words[-1]
    return next((w for w in (last, last[:-1] if last.endswith("s") else None) if w and w in known), None)


def build_procedural(prop, out_dir, blender="blender", timeout=600):
    """Run scripts/procedural_props.py in Blender for one prop; return the GLB path. Raises RuntimeError."""
    out_dir = Path(out_dir)
    cmd = [blender, "-b", "-P", str(PROCEDURAL), "--", str(out_dir), "--only", prop]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"coded prop {prop}: {exc}") from exc
    glb = out_dir / f"{prop}.glb"
    if p.returncode != 0 or not glb.is_file():
        raise RuntimeError(f"coded prop {prop}: blender exit {p.returncode}, no GLB")
    return glb


def _aspect(text):
    if not text:
        return None
    import asset_preview as AP
    return AP.parse_aspect(text)


def preview_check(expect_aspect=None, blender=None, aspects=None):
    """Default shape check: asset_preview.preview_one, any error flag rejects. Needs Blender, no GPU.
    `aspects` maps asset name -> aspect text ("1:4") and overrides `expect_aspect` for that asset.
    With no Blender on PATH the check is skipped (passes)."""
    def check(result):
        import asset_preview as AP  # lazy: keeps --list-engines free of the render code
        exe = AP.find_blender(blender)
        glb = Path(result["manifest"]).parent / "game" / f"{result['name']}.glb"
        if not exe or not glb.is_file():
            return True, ""
        own = (aspects or {}).get(result["name"])  # validated per asset by _check_spec before any work started
        try:
            res = AP.preview_one(glb, exe, out_dir=glb.parent.parent, expect_aspect=_aspect(own) if own else expect_aspect)
        except RuntimeError as exc:
            return False, f"preview failed: {exc}"
        # Errors reject; so do the two warnings that mark a shredded or paper-thin AI mesh.
        errs = [f"{f['code']}: {f['msg']}" for f in res["flags"]
                if f["level"] == "error" or f["code"] in ("non_manifold", "flat_mesh")]
        return (not errs), "; ".join(errs)
    return check


def _forget_ai_stages(chain, name):
    """Drop cached 3d/texture/cleanup records so the next try regenerates the mesh instead of re-serving it."""
    st = Path(chain.out_root) / name / "state.json"
    if st.is_file():
        state = json.loads(st.read_text())
        for k in ("3d", "texture", "cleanup"):
            state.pop(k, None)
        st.write_text(json.dumps(state, indent=1))


def _purge_shipped(workdir, state=False):
    """Remove everything that reads as 'this asset shipped' (mesh, UE manifest, qa, provenance, preview)."""
    shutil.rmtree(workdir / "game", ignore_errors=True)
    names = ["ue_import_manifest.json", "ue_import_manifest.py", "qa.json", "provenance.json", "preview.json",
             "preview.png"] + (["state.json"] if state else [])
    for n in names:
        (workdir / n).unlink(missing_ok=True)


def _check_spec(chain, spec):
    """The same gate run_asset applies before it touches disk. Returns an error line, or None if the spec is fine.
    Every path (thin shortcut, fallback) must pass this before any disk write."""
    if not isinstance(spec, dict):
        return f"queue entry {spec!r} is not a mapping (name, prompt, ...)"
    try:
        P.validate_spec(spec)
    except (ValueError, TypeError, AttributeError) as exc:
        return str(exc)
    if spec.get("aspect"):
        # YAML 1.1 reads an unquoted 1:4 as the base-60 number 64, so insist on text and name the entry.
        try:
            if not isinstance(spec["aspect"], str):
                raise ValueError(f"got {spec['aspect']!r}; quote it in the queue file, e.g. aspect: \"1:4\"")
            try:
                _aspect(spec["aspect"])
            except ValueError:
                raise ValueError(f"wants A:B or A:B:tol, got {spec['aspect']!r}") from None
        except ValueError as exc:
            return f"{spec['name']}: bad aspect ({exc})"
    root = Path(chain.out_root).resolve()
    workdir = (root / spec["name"]).resolve()
    if P.BLOCKED_RE.search(str(workdir)):
        return f"{workdir} touches a UC2/UT2004 path; refusing"
    if workdir.parent != root:
        return f"{spec['name']!r} resolves outside the output folder; refusing"
    return None


def ship_fallback(chain, spec, prop, reason, build=build_procedural):
    """Build the coded `prop` for `spec`; record in provenance.json and the asset log that the shipped mesh is
    the coded fallback, not the AI one. Stale AI manifests are removed so nothing points at a shredded mesh."""
    name = spec["name"]
    workdir = (Path(chain.out_root) / name).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".fallback-", dir=workdir))
    try:
        built = Path(build(prop, tmp))  # build first; a failure raises with whatever shipped before untouched
        staged = tmp / f"{name}.glb"
        if built.resolve() != staged.resolve():  # the asset may be named exactly like the prop
            shutil.copyfile(built, staged)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    _purge_shipped(workdir, state=True)
    (workdir / "game").mkdir(parents=True, exist_ok=True)
    out = workdir / "game" / f"{name}.glb"
    shutil.move(str(staged), out)
    shutil.rmtree(tmp, ignore_errors=True)
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    prov = {"name": name, "spec": spec, "shipped_mesh": "procedural-fallback", "procedural_prop": prop,
            "ai_failure": reason, "output": str(out), "output_sha256": sha,
            "note": "shipped mesh is the coded fallback from scripts/procedural_props.py, not the AI one",
            "stages": {"fallback": {"engine": "procedural", "credit": None, "output": str(out), "output_sha256": sha}}}
    (workdir / "provenance.json").write_text(json.dumps(prov, indent=1))
    chain._log_row(name, f"fallback:procedural:{prop}", 0, 0, str(out))
    return {"ok": True, "name": name, "workdir": str(workdir), "fallback": prop, "glb": str(out),
            "provenance": str(workdir / "provenance.json")}


def run_guarded(chain, spec, tries=DEFAULT_TRIES, fallback=None, check=None, known=None, build=build_procedural,
                force_ai=False):
    """Run one asset. Never hands back a shredded mesh: a good AI result, a coded fallback, or ok=False with a
    one-line `error` that says what failed and which fallback to use."""
    known = procedural_props() if known is None else known
    name = spec.get("name", "?") if isinstance(spec, dict) else "?"
    bad = _check_spec(chain, spec)
    if bad:
        return {"ok": False, "name": name, "error": bad}
    kind = thin_kind(spec)
    if kind and not force_ai:
        prop = match_procedural(spec, known)
        if prop and prop != kind:  # a coded prop that is not the thin kind itself is the wrong mesh
            prop = None
        if prop:
            print(f"{name}: {kind} shapes shred in the AI chain; building the coded {prop} instead", file=sys.stderr)
            try:
                return ship_fallback(chain, spec, prop, f"thin kind {kind!r}: AI chain skipped", build)
            except Exception as exc:
                return {"ok": False, "name": name,
                        "error": f"coded {prop} could not be built ({exc}); hand-code it in Blender. "
                                 f"Anything shipped earlier is untouched"}
        return {"ok": False, "name": name,
                "error": f"{kind} shapes shred in the AI chain and no coded {kind} exists; hand-code it in Blender "
                         f"(--force-ai tries the AI chain anyway)"}
    reason = ""
    for attempt in range(1, max(1, tries) + 1):
        try:
            res = chain.run_asset(spec)
        except Exception as exc:
            reason = f"cleanup/chain failed (try {attempt}/{tries}): {exc}"
            _forget_ai_stages(chain, name)  # same as a preview reject: the next try regenerates, not replays
            continue
        ok, why = check(res) if check else (True, "")
        if ok:
            return {"ok": True, **res}
        reason = f"preview rejected the mesh (try {attempt}/{tries}): {why}"
        _forget_ai_stages(chain, name)
    reason = " ".join(reason.split())[:300]
    _purge_shipped(Path(chain.out_root).resolve() / name)  # a rejected mesh must not stay readable as shipped
    prop = match_procedural(spec, known)
    if fallback == "procedural" and prop:
        try:
            res = ship_fallback(chain, spec, prop, reason, build)
            print(f"{name}: AI chain gave up ({reason}); shipped the coded {prop} instead", file=sys.stderr)
            return res
        except Exception as exc:
            return {"ok": False, "name": name, "error": f"{reason}. Coded {prop} fallback also failed ({exc}); hand-code it in Blender"}
    if prop:
        use = f"rerun with --fallback procedural to ship the coded {prop}"
    else:
        use = "no coded prop of that name; hand-code it in Blender"
    return {"ok": False, "name": name, "error": f"{reason}. Fallback: {use}"}


def run_queue_guarded(chain, specs, workers=4, **kw):
    """Chain.run_queue, but each asset goes through run_guarded."""
    names = [sp.get("name") if isinstance(sp, dict) else None for sp in specs]
    dups = sorted({str(n) for n in names if names.count(n) > 1})
    if dups:
        raise ValueError(f"duplicate asset names in queue: {', '.join(dups)}")
    from concurrent.futures import ThreadPoolExecutor

    def one(spec):
        try:
            return run_guarded(chain, spec, **kw)
        except Exception as exc:  # one bad asset must never kill the batch
            nm = spec.get("name", "?") if isinstance(spec, dict) else "?"
            chain._log_row(nm, "total", 0, 1, "")
            return {"ok": False, "name": nm, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        results = list(ex.map(one, specs))
    chain.write_credits()
    return results


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--queue", help="YAML/JSON list of assets (name, prompt|image, class, height_m, engines)")
    ap.add_argument("--name")
    ap.add_argument("--prompt")
    ap.add_argument("--image")
    ap.add_argument("--class", dest="cls", default="prop", help="tri budget class: " + ", ".join(E.BUDGETS))
    ap.add_argument("--height-m", type=float, help="scale longest axis to this many metres")
    ap.add_argument("--engine", action="append", default=[], metavar="STAGE=NAME",
                    help="force an engine for a stage, e.g. image=gpt (default: speed-first auto order)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--cloud-lanes", type=int, default=4)
    ap.add_argument("--cpu-lanes", type=int, default=3)
    ap.add_argument("--out-dir", default=str(ROOT / "work/generated/chain"))
    ap.add_argument("--log", default=str(ROOT / "stages/02_build/output/asset-pipeline-log.csv"))
    ap.add_argument("--credits", default=str(ROOT / "stages/02_build/output/credits.md"))
    ap.add_argument("--licenses", default=str(ROOT / "config/asset-licenses.json"))
    ap.add_argument("--max-tries", type=int, default=DEFAULT_TRIES, metavar="N",
                    help=f"stop retrying a failed cleanup / rejected mesh after N tries (default {DEFAULT_TRIES})")
    ap.add_argument("--fallback", choices=("procedural",),
                    help="when the AI chain gives up, build the prop from scripts/procedural_props.py if one of that "
                         "name/kind exists, and record that the shipped mesh is the coded fallback")
    ap.add_argument("--force-ai", action="store_true",
                    help=f"run the AI chain even for thin kinds ({', '.join(THIN_KINDS)}), which go straight to a coded mesh")
    ap.add_argument("--no-preview-check", action="store_true", help="skip the asset_preview.py check of each result")
    ap.add_argument("--expect-aspect", metavar="A:B[:tol]", help="width:height the result must have (asset_preview aspect/thin check); "
                    "a queue entry's own `aspect: A:B[:tol]` overrides it for that asset")
    ap.add_argument("--list-engines", action="store_true")
    add_detach_args(ap, "asset_chain")
    a = ap.parse_args(argv)
    if not (a.wait or a.list_engines or a.queue or (a.name and (a.prompt or a.image))):
        ap.error("give --queue, or --name with --prompt/--image (or --list-engines)")
    return a


def main(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    a = parse_args(raw)
    rc = handle_detach(a, Path(__file__).resolve(), raw, "asset_chain")
    if rc is not None:
        return rc
    gate = LicenceGate(a.licenses, warn=lambda m: print(m, file=sys.stderr))
    reg = E.build_registry()
    if a.list_engines:
        for stage, names in E.ORDER.items():
            for n in names:
                eng = reg[(stage, n)]
                try:
                    v = gate.check(stage, n, eng.aliases)["verdict"]
                except Exception as exc:
                    v = f"REFUSED ({exc})"
                print(f"{stage:8} {n:12} lane={eng.lane:5} licence={v}")
        return 0
    if a.queue:
        specs = P.load_queue(a.queue)
    else:
        specs = [{"name": a.name, "prompt": a.prompt, "image": a.image, "class": a.cls, "height_m": a.height_m}]
        specs[0] = {k: v for k, v in specs[0].items() if v is not None}
    override = dict(kv.split("=", 1) for kv in a.engine)
    lanes = P.Lanes(GPU_LOCK, cloud=a.cloud_lanes, cpu=a.cpu_lanes, preflight=gpu_preflight)
    chain = P.Chain(reg, gate, a.out_dir, a.log, a.credits, lanes, engine_override=override)
    aspects = {sp["name"]: sp["aspect"] for sp in specs  # per-asset override; checked per asset, never batch-wide
               if isinstance(sp, dict) and sp.get("aspect") and sp.get("name")}
    check = None if a.no_preview_check else preview_check(_aspect(a.expect_aspect), aspects=aspects)
    results = run_queue_guarded(chain, specs, a.workers, tries=a.max_tries, fallback=a.fallback, check=check,
                                force_ai=a.force_ai)
    bad = 0
    for r in results:
        if r["ok"]:
            if r.get("fallback"):
                print(f"OK   {r['name']}: CODED FALLBACK ({r['fallback']}), not the AI mesh: {r['glb']}")
                continue
            q = r["qa"]
            print(f"OK   {r['name']}: {q['tris']} tris (budget {q['budget']}), manifest {r['manifest']}")
        else:
            bad += 1
            print(f"FAIL {r['name']}: {r['error']}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
