"""Engine registry: every stage has swappable engines. One line per stage to flip the speed-first order.

An engine is (stage, name, lane, licence aliases, run). `run(ctx)` returns {"output": Path, ...extra}.
Lanes: "gpu" (strictly one at a time), "cloud" (parallel), "cpu" (parallel, bounded).
Real engines shell out; tests inject fakes through the `overrides` argument of build_registry().
"""
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .licenses import ALWAYS_BANNED

SCRIPTS = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent

# ---- the one-line flips (speed first: local Krea ~100 s beats GPT ~5 min; Grok needs a key) ----
ORDER = {
    "image": ["local", "grok", "gpt"],
    "3d": ["triposplat"],
    "texture": ["passthrough"],
    "cleanup": ["blender"],
}

# polygon budgets per asset class (triangles, LOD0)
BUDGETS = {"prop_small": 1500, "prop": 5000, "prop_large": 15000, "hero_prop": 30000}


class StageError(Exception):
    pass


@dataclass
class Engine:
    stage: str
    name: str
    lane: str
    run: Callable
    aliases: tuple = field(default_factory=tuple)


def _sh(cmd, env=None, timeout=1800):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise StageError(f"{cmd[0]} timed out after {timeout}s")
    if p.returncode != 0:
        raise StageError(f"{cmd[0]} exit {p.returncode}: {(p.stderr or p.stdout)[-400:]}")
    return p.stdout


def _provider_engine(provider):
    def run(ctx):
        sys.path.insert(0, str(SCRIPTS))
        import providers as P  # read-only use of gen_asset's provider module
        import gen_asset as G
        out = ctx["workdir"] / "concept.png"
        provs = P.default_providers("krea-2-turbo", environ=G.merged_env())
        try:
            info = P.generate_concept(provider, ctx["spec"]["prompt"], out, provs, log=lambda *_: None)
        except P.ProviderError as exc:
            # the summary alone ("local=failed") hides why; keep each attempt's detail
            detail = "; ".join(f"{a.get('provider')}: {a.get('detail')}"
                               for a in getattr(exc, "attempts", []) if a.get("detail"))
            raise StageError(f"{exc} [{detail}]" if detail else str(exc))
        return {"output": out, "model": info.get("model", "")}
    return run


def _reference_image(ctx):
    src = Path(ctx["spec"]["image"]).expanduser()
    if not src.is_file():
        raise StageError(f"reference image missing: {src}")
    return {"output": src}


def _triposplat(ctx):
    out = ctx["workdir"] / "raw.glb"
    env = dict(os.environ)
    ck = env.setdefault("NEXUS_THREED_IMAGE_CHECKPOINT", "krea-2-turbo")
    if ALWAYS_BANNED.search(ck):  # same rule as gen_asset.check_model_allowed
        raise StageError(f"NEXUS_THREED_IMAGE_CHECKPOINT={ck!r} is a banned (non-commercial) model")
    _sh(["nexus-3d", "--image", str(ctx["inputs"]["image"]), "--out", str(out),
         "--game-ready", "--model", "triposplat", "--json"], env=env, timeout=1800)
    if not out.is_file():
        raise StageError("nexus-3d produced no GLB")
    return {"output": out}


def _passthrough(ctx):
    # TripoSplat bakes albedo into the GLB already; nothing to do. Swap in a texture engine here later.
    return {"output": ctx["inputs"]["3d"]}


def _blender_cleanup(ctx):
    spec = ctx["spec"]
    budget = int(spec.get("tri_budget") or BUDGETS[spec.get("class", "prop")])
    outdir = ctx["workdir"] / "game"
    cmd = ["blender", "-b", "-P", str(HERE / "blender_cleanup.py"), "--", str(ctx["inputs"]["texture"]),
           str(outdir), spec["name"], "--budget", str(budget), "--thumb"]
    if spec.get("height_m"):
        cmd += ["--height", str(spec["height_m"])]
    _sh(cmd, timeout=900)
    report = outdir / "cleanup_report.json"
    if not report.is_file():
        raise StageError("blender cleanup wrote no report")
    return {"output": outdir / f"{spec['name']}.glb", "report": json.loads(report.read_text())}


def build_registry(overrides=None):
    reg = {
        ("image", "local"): Engine("image", "local", "gpu", _provider_engine("local"), ("krea-2-turbo", "local")),
        ("image", "gpt"): Engine("image", "gpt", "cloud", _provider_engine("gpt"), ("gpt-image", "openai")),
        ("image", "grok"): Engine("image", "grok", "cloud", _provider_engine("grok"), ("xai", "grok-imagine")),
        ("image", "reference-image"): Engine("image", "reference-image", "cpu", _reference_image),
        ("3d", "triposplat"): Engine("3d", "triposplat", "gpu", _triposplat),
        ("texture", "passthrough"): Engine("texture", "passthrough", "cpu", _passthrough),
        ("cleanup", "blender"): Engine("cleanup", "blender", "cpu", _blender_cleanup),
    }
    for key, eng in (overrides or {}).items():
        reg[key] = eng
    return reg
