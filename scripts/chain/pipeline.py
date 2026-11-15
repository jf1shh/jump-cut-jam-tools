"""Queue runner: lanes, resume-by-hash, licence gate, provenance, CSV log, credits, UE manifest, QA."""
import csv
import hashlib
import json
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .engines import BUDGETS, ORDER, StageError
from .licenses import LicenceError

NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
BLOCKED_RE = re.compile(r"uc2|ut2004", re.IGNORECASE)
STAGES = ("image", "3d", "texture", "cleanup")
CSV_HEADER = ["timestamp_iso", "name", "stage", "seconds", "exit_code", "output_path", "human_review"]
CREDITS_BEGIN, CREDITS_END = "<!-- chain:begin -->", "<!-- chain:end -->"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha_text(*parts):
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()


def load_queue(path):
    """JSON or YAML list of asset dicts (or {"assets": [...]})."""
    text = Path(path).read_text()
    if str(path).endswith((".yaml", ".yml")):
        import yaml
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("assets", [])
    if not isinstance(data, list):
        raise ValueError("queue must be a list of assets")
    return data


def validate_spec(spec):
    name = spec.get("name", "")
    if not NAME_RE.match(name):
        raise ValueError(f"asset name {name!r} is not filename-safe")
    if bool(spec.get("prompt")) == bool(spec.get("image")):
        raise ValueError(f"{name}: give exactly one of prompt / image")
    if spec.get("kind", "prop") != "prop":
        raise ValueError(f"{name}: only kind=prop is supported in this version (characters/rig = PR 2)")
    if spec.get("class", "prop") not in BUDGETS and not spec.get("tri_budget"):
        raise ValueError(f"{name}: unknown class {spec.get('class')!r}; use {', '.join(BUDGETS)}")


class Lanes:
    """gpu is always exactly 1 (thread semaphore + a cross-process file lock); cloud/cpu are bounded."""

    def __init__(self, lockfile, cloud=4, cpu=3, preflight=None):
        self.sems = {"gpu": threading.Semaphore(1), "cloud": threading.Semaphore(cloud), "cpu": threading.Semaphore(cpu)}
        self.lockfile = Path(lockfile)
        self.preflight = preflight
        self.active = {"gpu": 0, "cloud": 0, "cpu": 0}
        self.peak = dict(self.active)
        self._m = threading.Lock()

    @contextmanager
    def hold(self, lane):
        with self.sems[lane]:
            lockf = None
            if lane == "gpu":
                import fcntl
                self.lockfile.parent.mkdir(parents=True, exist_ok=True)
                lockf = open(self.lockfile, "w")
                try:
                    fcntl.flock(lockf, fcntl.LOCK_EX)
                    if self.preflight:
                        try:
                            ok, detail = self.preflight()
                        except Exception as exc:  # e.g. gpu-preflight not installed
                            ok, detail = False, f"preflight failed to run: {exc}"
                        if not ok:
                            raise StageError(f"gpu-preflight not clear: {detail}")
                except BaseException:
                    lockf.close()
                    raise
            with self._m:
                self.active[lane] += 1
                self.peak[lane] = max(self.peak[lane], self.active[lane])
            try:
                yield
            finally:
                with self._m:
                    self.active[lane] -= 1
                if lockf:
                    lockf.close()


class Chain:
    def __init__(self, registry, gate, out_root, log_path, credits_path, lanes, orders=None,
                 engine_override=None, manifest_dest="/Game/Props", warn=print):
        self.reg, self.gate = registry, gate
        self.out_root, self.log_path, self.credits_path = Path(out_root), Path(log_path), Path(credits_path)
        self.lanes, self.orders = lanes, orders or ORDER
        self.override = engine_override or {}
        self.manifest_dest, self.warn = manifest_dest, warn
        self._csv_lock = threading.Lock()

    # ---- logging ----
    def _log_row(self, name, stage, seconds, code, output):
        with self._csv_lock:
            new = not self.log_path.exists() or self.log_path.stat().st_size == 0
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", newline="") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(CSV_HEADER)
                w.writerow([datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), name, f"chain:{stage}",
                            f"{seconds:.2f}", code, output, ""])

    @staticmethod
    def _outputs_intact(rec):
        """Every recorded output exists and still has its recorded hash (hand-swapped or deleted files rerun)."""
        files = rec.get("outputs") or {rec["output"]: rec.get("output_sha256")}
        if rec["output"] not in files:
            return False
        return all(Path(p).is_file() and sha256_file(p) == h for p, h in files.items())

    # ---- engine choice ----
    def _candidates(self, spec, stage):
        if stage == "image" and spec.get("image"):
            return ["reference-image"], True
        want = (spec.get("engines") or {}).get(stage) or self.override.get(stage) or "auto"
        if want == "auto":
            return list(self.orders[stage]), False
        return [want], True

    def _run_stage(self, spec, stage, state, st_path, inputs, workdir, params):
        name = spec["name"]
        in_hash = [sha256_file(p) for p in inputs.values() if Path(p).is_file()]
        key = sha_text(stage, params, in_hash)
        prev = state.get(stage)
        names, explicit = self._candidates(spec, stage)
        if (prev and prev["key"] == key and self._outputs_intact(prev)
                and (not explicit or prev["engine"] == names[0])):
            cached = self.reg.get((stage, prev["engine"]))
            try:  # re-check the gate on every resume: a later refusal must not ship cached output
                prev["licence"] = self.gate.check(stage, prev["engine"], cached.aliases if cached else ())
            except LicenceError as exc:
                self._log_row(name, f"{stage}:{prev['engine']}", 0, 3, "refused")
                raise StageError(f"{stage}: cached output refused by licence gate: {exc}")
            state[stage] = prev
            st_path.write_text(json.dumps(state, indent=1))
            self._log_row(name, f"{stage}:{prev['engine']}:skipped", 0, 0, prev["output"])
            return prev
        errors = []
        for eng_name in names:
            eng = self.reg.get((stage, eng_name))
            if eng is None:
                errors.append(f"{eng_name}: unknown engine")
                if explicit:
                    break
                continue
            try:
                lic = self.gate.check(stage, eng_name, eng.aliases)
            except LicenceError as exc:
                errors.append(str(exc))
                self._log_row(name, f"{stage}:{eng_name}", 0, 3, "refused")
                if explicit:
                    break
                continue
            t0 = time.monotonic()
            try:
                with self.lanes.hold(eng.lane):
                    res = eng.run({"spec": spec, "workdir": workdir, "inputs": inputs})
            except (StageError, OSError, subprocess.SubprocessError) as exc:
                errors.append(f"{eng_name}: {exc}")
                self._log_row(name, f"{stage}:{eng_name}", time.monotonic() - t0, 1, "")
                if explicit:
                    break
                continue
            secs = time.monotonic() - t0
            out = Path(res["output"])
            outs = [Path(p) for p in res.get("outputs", [out])]
            if stage == "cleanup":  # game/ belongs to cleanup alone: pin every file in it
                outs = sorted(p for p in out.parent.iterdir() if p.is_file())
            rec = {"key": key, "engine": eng_name, "output": str(out), "seconds": round(secs, 2),
                   "output_sha256": sha256_file(out) if out.is_file() else "", "licence": lic,
                   "outputs": {str(p): sha256_file(p) for p in outs if p.is_file()}}
            if "report" in res:
                rec["report"] = res["report"]
            state[stage] = rec
            st_path.write_text(json.dumps(state, indent=1))
            self._log_row(name, f"{stage}:{eng_name}", secs, 0, str(out))
            return rec
        raise StageError(f"{stage} failed: " + "; ".join(errors))

    # ---- one asset ----
    def run_asset(self, spec):
        validate_spec(spec)
        name = spec["name"]
        workdir = (self.out_root / name).resolve()
        if BLOCKED_RE.search(str(workdir)):
            raise ValueError(f"{workdir} touches a UC2/UT2004 path; refusing")
        workdir.mkdir(parents=True, exist_ok=True)
        st_path = workdir / "state.json"
        state = json.loads(st_path.read_text()) if st_path.exists() else {}
        inputs = {}
        params = {
            "image": {"prompt": spec.get("prompt"), "ref": spec.get("image")},
            "3d": {}, "texture": {},
            "cleanup": {"budget": spec.get("tri_budget") or BUDGETS.get(spec.get("class", "prop")),
                        "height": spec.get("height_m")},
        }
        t_all = time.monotonic()
        for stage in STAGES:
            rec = self._run_stage(spec, stage, state, st_path, inputs, workdir, params[stage])
            inputs[stage] = rec["output"]
        game = Path(state["cleanup"]["output"]).parent
        report = state["cleanup"]["report"]
        manifest = self._write_manifest(spec, workdir, game, report)
        qa = self._write_qa(spec, workdir, report, state)
        prov = self._write_provenance(spec, workdir, state, time.monotonic() - t_all)
        self._log_row(name, "total", time.monotonic() - t_all, 0, str(manifest))
        return {"name": name, "workdir": str(workdir), "manifest": str(manifest), "qa": qa, "provenance": str(prov)}

    # ---- stage 6/7 ----
    def _write_manifest(self, spec, workdir, game, report):
        name = spec["name"]
        entry = {"name": name, "type": "prop", "dest": f"{self.manifest_dest}/{name}",
                 "fbx": str(game / f"{name}.fbx"), "glb": str(game / f"{name}.glb"),
                 "collision": "UCX hull inside the FBX (convex); fallback: add_simple_collisions",
                 "lods": report["lods"], "material_slot": report["material"],
                 "has_texture": report.get("has_texture", False), "require_pbr": True}
        mj = workdir / "ue_import_manifest.json"
        mj.write_text(json.dumps({"assets": [entry]}, indent=1))
        py = workdir / "ue_import_manifest.py"
        py.write_text(
            '"""Run inside the UE 5.8 editor (Python console or -ExecCmds). Imports this asset via scripts/ue_import_asset.py."""\n'
            "import importlib.util, json\n"
            f"M = json.load(open({str(mj)!r}))\n"
            f"spec = importlib.util.spec_from_file_location('ue_import_asset', {str(Path(__file__).resolve().parent.parent / 'ue_import_asset.py')!r})\n"
            "mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\n"
            "for a in M['assets']:\n"
            "    print(mod.import_asset(a['fbx'], a['dest'] + '/', a['name'], a['type'], require_pbr=a['require_pbr']))\n")
        return mj

    def _write_qa(self, spec, workdir, report, state):
        credits = [s["licence"]["credit"] for s in state.values() if s["licence"]["credit"]]
        engines = ", ".join(f"{k}={v['engine']}({v['licence']['verdict']})" for k, v in state.items())
        qa = {"name": spec["name"], "tris": report["tris"], "budget": report["budget"],
              "within_budget": report["tris"] <= report["budget"], "bbox_m": report["bbox_m"],
              "uv": report["uv"], "thumb": report.get("thumb"), "has_texture": report.get("has_texture", False),
              "warnings": [] if report.get("has_texture", False) else ["no texture bound: UE import fails loudly (require_pbr)"],
              "licence_line": engines + (" | credit: " + "; ".join(credits) if credits else "")}
        (workdir / "qa.json").write_text(json.dumps(qa, indent=1))
        return qa

    def _write_provenance(self, spec, workdir, state, seconds):
        prov = {"name": spec["name"], "spec": spec, "created": datetime.now(timezone.utc).isoformat(),
                "total_seconds": round(seconds, 2), "licence_source": self.gate.source,
                "stages": {k: {"engine": v["engine"], "seconds": v["seconds"], "licence_verdict": v["licence"]["verdict"],
                               "credit": v["licence"]["credit"], "output": v["output"], "output_sha256": v["output_sha256"],
                               "outputs": v.get("outputs", {})}
                           for k, v in state.items()}}
        p = workdir / "provenance.json"
        p.write_text(json.dumps(prov, indent=1))
        return p

    # ---- queue ----
    def run_queue(self, specs, workers=4):
        names = [sp.get("name") for sp in specs]
        dups = sorted({str(n) for n in names if names.count(n) > 1})
        if dups:
            raise ValueError(f"duplicate asset names in queue: {', '.join(dups)}")

        def one(spec):
            try:
                return {"ok": True, **self.run_asset(spec)}
            except Exception as exc:  # one bad asset must never kill the batch
                self._log_row(spec.get("name", "?"), "total", 0, 1, "")
                return {"ok": False, "name": spec.get("name", "?"), "error": str(exc)}

        with ThreadPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(one, specs))
        self.write_credits()
        return results

    def write_credits(self):
        lines = ["| Asset | Stage | Engine | Credit |", "|---|---|---|---|"]
        for p in sorted(self.out_root.glob("*/provenance.json")):
            prov = json.loads(p.read_text())
            for stage, s in prov["stages"].items():
                if s["credit"]:
                    lines.append(f"| {prov['name']} | {stage} | {s['engine']} | {s['credit']} |")
        if len(lines) == 2:
            lines.append("| (none needed) | | | |")
        block = f"{CREDITS_BEGIN}\n" + "\n".join(lines) + f"\n{CREDITS_END}"
        text = self.credits_path.read_text() if self.credits_path.exists() else "# Credits\n\nGenerated by scripts/asset_chain.py; do not edit between the markers.\n\n"
        if CREDITS_BEGIN in text and CREDITS_END in text:
            head, rest = text.split(CREDITS_BEGIN, 1)
            tail = rest.split(CREDITS_END, 1)[1]
            text = head + block + tail
        else:
            text = text.rstrip("\n") + "\n\n" + block + "\n"
        self.credits_path.parent.mkdir(parents=True, exist_ok=True)
        self.credits_path.write_text(text)
