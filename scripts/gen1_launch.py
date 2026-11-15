#!/usr/bin/env python3
"""GEN 1 in one command: the art-pack plan (hub 114/115) through the repo adapters only.

    python3 scripts/gen1_launch.py            # DRY RUN (default): checks and prints, spends nothing
    python3 scripts/gen1_launch.py --go       # run it; re-run the same command to resume after a failure

Plan: 3 directions x 4 subjects = 12 concepts on gpt, the same 12 on fal schnell (backup), then 6 props
through gen_asset.py --3d-provider meshy, plus SM_WaterTower_rodin on hyper3d. No Grok, no local AI.
Lanes run in parallel (gpt, fal, 3D). Each job writes its own provenance sidecar (concept.png.provenance.json
or <glb>.provenance.json, with the licence verdict) and rows in the asset-pipeline log via gen_asset.py.
A job whose sidecar already exists is skipped, so a second run only redoes what failed. Status goes to
work/gen1-status.json. Every job has a timeout and fails loudly; the exit code is 1 if any job failed.

Gate: refuses unless `greybox_gate.py check` passes (use --no-gate only for the dry run's own self-test).
Nothing here ships an asset: Rodin output waits for the owner's OK (stages/05_devlog / ledger).
"""
import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import gen_asset  # noqa: E402

GAME = Path.home() / "Projects/megajam-game/JumpCut.uproject"
OUT = "work/generated"
CONCEPT_OUT = f"{OUT}/concepts"
STATUS = ROOT / "work/gen1-status.json"
RUN = subprocess.run  # tests swap this for a fake: no process, no cloud
CONCEPT_TIMEOUT = 900
PROP_TIMEOUT = 1800

DIRECTIONS = {
    "A": "flat-shaded chunky low-poly stage set, hand-painted plywood flats with visible grain, gaffer tape and scaffold braces, hard amber tungsten key light #FFB04A against a pure black backstage void",
    "B": "1:24 hobby-model diorama, smooth bevelled toy shapes and painted resin surfaces, soft warm tungsten light with soft contact shadows, slight tilt-shift tabletop backlot look",
    "C": "70s poster graphic, bold simplified silhouettes with strong coloured rim light, high contrast and print grain, palette limited to amber #FFB04A, steel blue #5B86C9, sodium #FF9A3C, fire #FF5A1F",
}
SUBJECTS = [
    ("s1_mainstreet", "toy-scale 1970s backlot Main Street, wide view, with a wooden water tower"),
    ("s2_chase", "toy-scale 1970s backlot street, day-for-night, under a rail trestle"),
    ("s3_depot", "toy-scale 1970s backlot fuel depot with a timber bridge and a gas holder"),
    ("hero_car", "1970s muscle car, no badge, mid-jump, three-quarter view"),
]
PROPS = [  # (name, prompt, 3d provider)
    ("SM_StudioLight", "1970s tungsten studio lamp with barn doors on a tripod stand", "meshy"),
    ("SM_ClapperSign", "oversized film clapperboard on a wooden post, blank slate", "meshy"),
    ("SM_Barrel", "dented steel oil drum, plain paint, no stencil text", "meshy"),
    ("SM_WaterTower", "wooden water tower on four timber legs with cross braces", "meshy"),
    ("SM_PropTruck", "1970s flatbed prop truck, boxy cab, no badge", "meshy"),
    ("SM_CameraCrane", "film camera crane on a tracked dolly base, counterweight arm", "meshy"),
    ("SM_WaterTower_rodin", "wooden water tower on four timber legs with cross braces", "hyper3d"),
]
TAIL = "toy-scale 1970s backlot prop"


def jobs():
    """Return {lane: [job]}; a job is {name, cmd, done (sidecar path), timeout, lane, licence_lane}."""
    lanes = {"gpt": [], "fal": [], "3d": []}
    for prov in ("gpt", "fal"):
        for d, style in DIRECTIONS.items():
            for key, subject in SUBJECTS:
                name = f"concept_{d}_{key}_{prov}"
                prompt = f"{subject}. {style}. No text, no logos, no third-party IP."
                cmd = ["python3", "scripts/gen_asset.py", "--name", name, "--provider", prov, "--concept-only",
                       "--prompt", prompt, "--out-dir", CONCEPT_OUT]
                lanes[prov].append({"name": name, "cmd": cmd, "timeout": CONCEPT_TIMEOUT, "lane": prov,
                                    "done": ROOT / CONCEPT_OUT / name / "concept.png.provenance.json",
                                    "licence": ("--provider", prov)})
    for name, prompt, p3 in PROPS:
        cmd = ["python3", "scripts/gen_asset.py", "--name", name, "--provider", "fal", "--3d-provider", p3,
               "--prompt", f"{prompt}, {TAIL}", "--qa-kind", "prop", "--out-dir", OUT]
        lanes["3d"].append({"name": name, "cmd": cmd, "timeout": PROP_TIMEOUT, "lane": "3d",
                            "done": ROOT / OUT / name / f"{name}.glb.provenance.json",
                            "licence": ("--3d-provider", p3)})
    return lanes


def licence_problems(all_jobs):
    bad = []
    for flag, prov in sorted({j["licence"] for j in all_jobs}):
        verdict = gen_asset.licence_verdict(prov, flag=flag)
        if verdict not in ("ok", "ok-with-credit"):
            bad.append(f"{flag} {prov}: licence {verdict}")
    for j in all_jobs:
        if "grok" in " ".join(j["cmd"]).lower():
            bad.append(f"{j['name']}: grok in the plan")
    return bad


def provider_problems(environ):
    bad = []
    concept = gen_asset.concept_providers.default_providers("krea-2-turbo", environ=environ)
    for prov in ("gpt", "fal"):
        status, detail = concept[prov].check()
        if status != "ready":
            bad.append(f"concept {prov}: {status} ({detail})")
    for name, provider in gen_asset.threed_cloud_providers(environ, [ROOT]).items():
        if name in ("meshy", "hyper3d"):
            status, detail = provider.check()
            if status != "ready":
                bad.append(f"3d {name}: {status} ({detail})")
    return bad


def _save(results):
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(results, indent=2) + "\n")


def status_line(lanes=None):
    """One line per call: per lane done/running/failed/todo (done = sidecar on disk, the source of truth)."""
    lanes = lanes or jobs()
    try:
        recorded = json.loads(STATUS.read_text())
    except (OSError, ValueError):
        recorded = {}
    parts = []
    for lane, items in lanes.items():
        done = sum(1 for j in items if j["done"].exists())
        running = [j["name"] for j in items if not j["done"].exists() and recorded.get(j["name"], {}).get("state") == "running"]
        failed = [j["name"] for j in items if not j["done"].exists() and recorded.get(j["name"], {}).get("state") == "FAILED"]
        todo = len(items) - done - len(running) - len(failed)
        parts.append(f"{lane} {done}/{len(items)} done, {len(running)} running, {len(failed)} failed, {todo} todo"
                     + (f" [failed: {', '.join(failed)}]" if failed else ""))
    return "GEN1: " + " | ".join(parts)


def run_job(job, results):
    start = time.monotonic()
    results[job["name"]] = {"state": "running", "seconds": 0}
    _save(results)
    if job["done"].exists():
        results[job["name"]] = {"state": "skipped (already done)", "seconds": 0}
        return
    try:
        p = RUN(job["cmd"], cwd=ROOT, capture_output=True, text=True, timeout=job["timeout"])
        ok = p.returncode == 0 and job["done"].exists()
        tail = (p.stdout + p.stderr).strip().splitlines()[-3:]
        results[job["name"]] = {"state": "ok" if ok else "FAILED", "seconds": round(time.monotonic() - start, 1),
                                "detail": " | ".join(tail)[:300]}
    except subprocess.TimeoutExpired:
        results[job["name"]] = {"state": "FAILED", "seconds": job["timeout"], "detail": f"timeout {job['timeout']}s"}
    print(f"  {results[job['name']]['state']:<22} {job['name']} ({results[job['name']]['seconds']}s)", flush=True)
    _save(results)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--go", action="store_true", help="really run (default is a dry run)")
    ap.add_argument("--status", action="store_true", help="print one status line and exit (reads disk + work/gen1-status.json)")
    ap.add_argument("--no-gate", action="store_true", help="skip the greybox gate check (dry run self-test only)")
    a = ap.parse_args()
    if a.status:
        print(status_line())
        return 0

    lanes = jobs()
    all_jobs = [j for lane in lanes.values() for j in lane]
    problems = licence_problems(all_jobs)
    environ = gen_asset.merged_env()
    problems += provider_problems(environ)
    if not a.no_gate:
        g = subprocess.run([sys.executable, "scripts/greybox_gate.py", "check", "--project", str(GAME)],
                           cwd=ROOT, capture_output=True, text=True)
        if g.returncode != 0:
            problems.append("greybox gate not proven: " + (g.stdout + g.stderr).strip()[-120:])
    pending = [j for j in all_jobs if not j["done"].exists()]
    print(f"GEN 1 plan: {len(lanes['gpt'])} gpt + {len(lanes['fal'])} fal concepts, {len(lanes['3d'])} props "
          f"(3D: {sum(1 for j in lanes['3d'] if 'meshy' in j['cmd'])} meshy, "
          f"{sum(1 for j in lanes['3d'] if 'hyper3d' in j['cmd'])} hyper3d); {len(pending)} still to do")
    for lane, items in lanes.items():
        for j in items:
            print(f"  [{lane}] {'todo' if not j['done'].exists() else 'done'} {j['name']}")
    if problems:
        print("\nNOT READY:")
        for p in problems:
            print(f"  - {p}")
        return 2
    print("\nchecks green: licences ok, providers ready" + ("" if a.no_gate else ", gate proven"))
    if not a.go:
        print("DRY RUN: nothing sent. Re-run with --go to start.")
        return 0
    return run_all(lanes)


ALERT = ROOT / "work" / "gen1-ALERT.txt"
MIN_FINISHED, MAX_FAIL_FRACTION = 2, 0.5


def run_lane(lane, items, results):
    """Run a lane in order; stop it early and ALERT when more than half of the finished jobs failed
    (after at least MIN_FINISHED), so a dead lane (gpt bridge, 3D tail) is seen in seconds, not at the 30 min check."""
    finished = failed = 0
    for j in items:
        run_job(j, results)
        state = results[j["name"]]["state"]
        if state.startswith("skipped"):
            continue
        finished += 1
        failed += state == "FAILED"
        if finished >= MIN_FINISHED and failed / finished > MAX_FAIL_FRACTION:
            msg = (f"GEN1 ALERT: lane {lane} DEAD, {failed}/{finished} jobs failed; stopped it. "
                   f"Last error: {results[j['name']].get('detail', '')[:200]}")
            print(msg, flush=True)
            ALERT.parent.mkdir(parents=True, exist_ok=True)
            with open(ALERT, "a") as fh:
                fh.write(msg + "\n")
            return


def run_all(lanes):
    results = {}
    ALERT.unlink(missing_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = [pool.submit(run_lane, lane, items, results) for lane, items in lanes.items()]
        for f in futs:
            f.result()
    failed = [n for n, r in results.items() if r["state"] == "FAILED"]
    print(f"\nGEN 1 done: {len(results) - len(failed)} ok/skipped, {len(failed)} failed")
    for n in failed:
        print(f"  FAILED {n}: {results[n].get('detail', '')}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
