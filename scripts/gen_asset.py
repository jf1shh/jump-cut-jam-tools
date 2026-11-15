#!/usr/bin/env python3
"""CLI that drives local Nexus image/3D tools to produce one game-ready asset."""
import argparse
import csv
import json
import os
import hashlib
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import providers as concept_providers  # noqa: E402
from providers import meshy as meshy_provider  # noqa: E402
from providers import fal as fal_provider  # noqa: E402
from providers import hyper3d as hyper3d_provider  # noqa: E402
from providers import tripo as tripo_provider  # noqa: E402
from providers import fal_tts as fal_tts_provider  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
BLOCKED_RE = re.compile(r"uc2|ut2004", re.IGNORECASE)
# Non-commercial models can't back a prize entry (Rule 15(b)): Qwen-Image 2.1 is "qwen-research",
# 4x-UltraSharp is CC BY-NC-SA 4.0; Hunyuan3D outputs are territory-restricted (license 5(c)); 3D is TripoSplat (MIT) only. See stages/00_prep/references/license-check-modly-foundrylab.md.
BANNED_MODEL_RE = re.compile(r"qwen-image|ultrasharp|hunyuan", re.IGNORECASE)
THREED_CHECKPOINT_ENV = "NEXUS_THREED_IMAGE_CHECKPOINT"
THREED_CHECKPOINT = "krea-2-turbo"
THREED_MODEL = "triposplat"  # passed as nexus-3d --model; plain nexus-3d defaults to Hunyuan (banned)
# Cloud 3D providers `--3d-provider auto` tries, left to right, before local TripoSplat. Each is used only when its
# key and *_TERMS_REVIEWED date are set and its host answers a TCP connect; otherwise it is skipped at once.
THREED_CLOUD_ORDER = ("meshy", "tripo", "hyper3d", "fal")


# Most restrictive matching row wins in licence_verdict; an unknown or missing verdict ranks as "unclear".
VERDICT_RANK = {"ok": 0, "ok-with-credit": 1, "unclear": 2, "no": 3}


def licence_verdict(name, table_path=None, flag="--provider"):
    """Licence verdict for a provider name from config/asset-licenses.json (never spends quota).

    Refuses up front ("no") when the name matches BANNED_MODEL_RE (hunyuan, qwen-image, ultrasharp: the same
    set as ALWAYS_BANNED in scripts/chain/licenses.py), whatever the table says. Otherwise matches each entry's
    regex against the provider name and the `FLAG NAME` form (`--provider` for images, `--3d-provider` for 3D, so an
    image-only entry never covers the 3D lane) and takes the STRICTEST verdict over every matching row
    (no > unclear > ok-with-credit > ok), so a loose row cannot hide a stricter one. Returns "ok",
    "ok-with-credit", "unclear", "no" or "not listed" (the gate refuses unlisted engines).
    """
    import json
    import re
    texts = (f"{flag} {name}", name)
    if any(BANNED_MODEL_RE.search(t) for t in texts):
        return "no"
    path = Path(table_path) if table_path else REPO_ROOT / "config" / "asset-licenses.json"
    try:
        entries = json.loads(path.read_text())["entries"]
    except (OSError, ValueError, KeyError):
        return "table unreadable"
    verdicts = []
    for text in texts:
        for entry in entries:
            try:
                hit = re.search(entry.get("match", ""), text, re.I) if entry.get("match") else None
            except re.error:
                hit = None
            if hit:
                verdicts.append(str(entry.get("verdict", "")).lower() or "missing")
    if not verdicts:
        return "not listed"
    return max(verdicts, key=lambda v: VERDICT_RANK.get(v, VERDICT_RANK["unclear"]))


def threed_cloud_providers(environ, roots):
    """name -> adapter. Looked up through the modules so tests can patch each class."""
    return {"meshy": meshy_provider.MeshyProvider(environ=environ, allowed_roots=roots),
            "tripo": tripo_provider.TripoProvider(environ=environ, allowed_roots=roots),
            "hyper3d": hyper3d_provider.Hyper3DProvider(environ=environ, allowed_roots=roots),
            "fal": fal_provider.Fal3DProvider(environ=environ, allowed_roots=roots)}


def check_model_allowed(model):
    """Return an error message if the model is banned, else None."""
    if model and BANNED_MODEL_RE.search(model):
        return (f"model {model!r} is non-commercial (qwen-image* = qwen-research, ultrasharp = CC BY-NC-SA, hunyuan3d* = territory clause) "
                f"and cannot back a jam entry (Rule 15(b)); use krea-2-turbo")
    return None


ENV_FILE = Path.home() / ".config" / "megajam.env"
ENV_LINE_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def load_env_file(path=ENV_FILE, warn=None):
    """Read KEY=VALUE lines from a private env file. No shell evaluation, never prints values.

    Returns {} (and warns, naming only the path and mode) when the file is group/world accessible,
    not a regular file, or not owned by this user. A missing file is silently {}.
    """
    warn = warn or (lambda msg: print(msg, file=sys.stderr))
    path = Path(path)
    try:
        st = path.stat()
    except OSError:
        return {}
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
        warn(f"{path}: ignored (not a regular file owned by you)")
        return {}
    if st.st_mode & 0o077:
        warn(f"{path}: ignored, mode {stat.S_IMODE(st.st_mode):04o} lets others read it; run: chmod 600 {path}")
        return {}
    try:
        text = path.read_text(encoding="utf-8-sig")  # tolerate a BOM from Windows-style editors
    except (OSError, UnicodeDecodeError):
        warn(f"{path}: ignored (unreadable)")
        return {}
    values = {}
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = ENV_LINE_RE.match(line)
        if not m:
            warn(f"{path}: line {number} skipped (not KEY=VALUE, no spaces around '=')")
            continue
        value = m.group(2).strip()
        q = re.match(r"""^(["'])(.*?)\1(?:\s+#.*)?$""", value)
        if q:
            value = q.group(2)
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        values[m.group(1)] = value
    return values


def merged_env(environ=None, path=ENV_FILE, warn=None):
    """File values first, then real environment variables on top (real env wins).

    An empty real variable counts as unset, so it cannot hide the file's value; we warn (name only).
    """
    warn = warn or (lambda msg: print(msg, file=sys.stderr))
    environ = os.environ if environ is None else environ
    from_file = load_env_file(path, warn)
    env = {**from_file, **environ}
    for key, value in from_file.items():
        if environ.get(key) == "":
            warn(f"{key} is set but empty in the environment; using the value from {path}")
            env[key] = value
    return env


def threed_env(environ):
    """Env for the 3D stage: pin nexus-3d's image checkpoint so it can't fall back to Qwen."""
    env = dict(environ)
    env.setdefault(THREED_CHECKPOINT_ENV, THREED_CHECKPOINT)
    return env


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a game-ready 3D asset via local Nexus tools.")
    parser.add_argument("--name", help="asset id (letters, digits, _, - only)")
    parser.add_argument("--provider", default="auto", choices=["auto", *concept_providers.AUTO_ORDER],
                        help="concept-image provider; auto tries "
                             + ", ".join(concept_providers.AUTO_ORDER) + " in order (see _config/reference/ai-providers.md)")
    parser.add_argument("--3d-provider", dest="threed_provider", default="auto", choices=["auto", "local", *THREED_CLOUD_ORDER],
                        help="3D provider; auto = speed-first: each configured cloud provider in order ("
                             + ", ".join(THREED_CLOUD_ORDER) + "), local TripoSplat as the fallback (local only when none "
                             "is configured); a forced choice never falls back (each needs its key + *_TERMS_REVIEWED, see _config/reference/ai-providers.md)")
    parser.add_argument("--providers-check", action="store_true",
                        help="print one status line per provider (spends no quota) and exit")
    parser.add_argument("--meshy-balance", action="store_true",
                        help="print Meshy's credit balance as JSON (one GET, spends no credits) and exit")
    parser.add_argument("--target-polycount", type=int, default=None,
                        help="Meshy only: remesh to about this many triangles (100..300000); default Meshy's own")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--prompt", help="text prompt passed to nexus-image to generate a concept PNG")
    group.add_argument("--image", help="existing reference PNG, skips concept generation")
    group.add_argument("--tts", metavar="TEXT",
                       help="voice line mode: speak TEXT with a fal TTS model into <out-dir>/<name>/<name>.<ext> "
                            "(+ provenance sidecar); no image or 3D stage runs")
    parser.add_argument("--tts-engine", default="auto", choices=["auto", *fal_tts_provider.AUTO_ORDER],
                        help="fal TTS model; auto tries " + ", ".join(fal_tts_provider.AUTO_ORDER) + " in order")
    parser.add_argument("--tts-voice", default=None, help="voice preset (gemini e.g. Algenib, Fenrir; minimax voice_id)")
    parser.add_argument("--tts-style", default=None, help="gemini delivery direction in plain words")
    parser.add_argument("--tts-minimax-voice", default=None,
                        help="minimax voice_id used when auto falls back from gemini (default: the minimax default voice)")
    parser.add_argument("--tts-quality", default="pro", choices=sorted(fal_tts_provider.GEMINI_QUALITY),
                        help="gemini model: pro (better) or flash (faster)")
    parser.add_argument("--tts-temperature", type=float, default=None, help="gemini delivery variety (default 1.0)")
    parser.add_argument("--tts-emotion", default=None, choices=fal_tts_provider.MINIMAX_EMOTIONS,
                        help="minimax emotion preset")
    parser.add_argument(
        "--model", default="krea-2-turbo",
        help="forwarded as nexus-image's --model (default krea-2-turbo: commercial-OK under $1M "
             "revenue, unlike Nexus's own default Qwen-Image 2.1, which is non-commercial-only and "
             "can't back a cash-prize entry under Rule 15(b) — see stages/00_prep/references/license-check-modly-foundrylab.md)",
    )
    parser.add_argument("--concept-only", action="store_true",
                        help="stop after the concept image (needs --prompt): no 3D stage, no GLB; writes concept.png.provenance.json")
    parser.add_argument("--image-size", default=None, metavar="WxH",
                        help="fal concept image size in pixels, e.g. 2048x512 for a wide matte painting "
                             "(multiples of 16, 256..2048, up to 2 megapixels; needs --provider fal and --prompt; default 1024x1024)")
    parser.add_argument("--profile", default=None, help="forwarded as nexus-3d's --profile")
    parser.add_argument("--qa-kind", default="prop", choices=["prop", "character"], help="forwarded as nexus-3d's --qa-kind")
    parser.add_argument("--out-dir", default="work/generated", help="asset output root")
    parser.add_argument("--log", default="stages/02_build/output/asset-pipeline-log.csv", help="CSV append log path")
    args = parser.parse_args()
    if args.concept_only and not args.prompt:
        parser.error("--concept-only needs --prompt")
    if args.image_size:
        m = re.fullmatch(r"(\d+)x(\d+)", args.image_size)
        if not (args.prompt and args.provider == "fal"):
            parser.error("--image-size needs --prompt and --provider fal")
        if not m:
            parser.error("--image-size must look like 2048x512")
        w, h = int(m.group(1)), int(m.group(2))
        if not (256 <= w <= 2048 and 256 <= h <= 2048 and w % 16 == 0 and h % 16 == 0 and w * h <= 2 * 1024 * 1024):
            parser.error("--image-size: each side 256..2048 and a multiple of 16, at most 2 megapixels")
        args.image_size = (w, h)
    if not (args.providers_check or args.meshy_balance) and not (args.name and (args.prompt or args.image or args.tts)):
        parser.error("--name and one of --prompt/--image/--tts are required (unless --providers-check or --meshy-balance)")
    return args


def ensure_csv_header(log_path: Path):
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", newline="") as f:
            csv.writer(f).writerow(["timestamp_iso", "name", "stage", "seconds", "exit_code", "output_path", "human_review"])


def append_row(log_path: Path, name, stage, seconds, exit_code, output_path):
    with log_path.open("a", newline="") as f:
        csv.writer(f).writerow([
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            name, stage, f"{seconds:.2f}", exit_code, output_path, "",  # human_review: tick by hand (Krea 4.2 content filter)
        ])


def sha256_of(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def nexus_revision():
    """Git HEAD of the Nexus checkout behind nexus-image/nexus-3d, or None."""
    script = shutil.which("nexus-3d") or shutil.which("nexus-image")
    if not script:
        return None
    result = subprocess.run(["git", "-C", str(Path(script).resolve().parent), "rev-parse", "HEAD"],
                            capture_output=True, text=True)
    return result.stdout.strip() or None


def load_concept_sidecar(image_path: Path):
    """A concept PNG made earlier by --concept-only has `<png>.provenance.json`. Return that record
    when it still describes this exact image (sha256 match), so the 3D run (`--image concept.png`,
    after a human looked at it) keeps the prompt and provider in the GLB's provenance. Else None."""
    try:
        data = json.loads(Path(f"{image_path}.provenance.json").read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("kind") != "concept-image" or not data.get("provider"):
        return None
    if data.get("image_sha256") != sha256_of(image_path):
        return None
    return data


def write_provenance(glb_path: Path, args, image_path: Path, commands, env, concept=None, threed=None, prompt=None):
    """Write <glb>.provenance.json. Nexus only writes sidecars for UC2-gated paths, so the jam's
    provenance trail (which provider made the concept image, which licensed models) lives here.
    `concept` is the generate_concept() result, or None when --image skipped generation.
    `threed` is {"provider","model","task_id","licence_gate"} from the 3D stage (None = local TripoSplat)."""
    threed = threed or {"provider": "local", "model": THREED_MODEL, "task_id": None, "licence_gate": None}
    threed_local = threed["provider"] == "local"
    provider = concept["provider"] if concept else None
    prompt = prompt if prompt is not None else args.prompt
    record = {
        "schema_version": 1,
        "tool": "megajam/scripts/gen_asset.py",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "name": args.name,
        "local_only": provider in (None, "local") and threed_local,
        "nexus_revision": nexus_revision(),
        "prompt": prompt,
        "image_provider": provider,
        "image_provider_model": concept.get("model") if concept else None,
        "image_model_id": concept.get("model") if concept else None,
        "image_licence_gate": concept.get("licence_gate") if concept else None,
        "image_provider_attempts": concept["attempts"] if concept else [],
        "image_model": args.model if (provider == "local" or (concept is None and args.prompt)) else None,
        "source_image": None if args.prompt else str(image_path),
        "source_image_sha256": sha256_of(image_path),
        "threed_model": THREED_MODEL if threed_local else threed["model"],
        "threed_provider": threed["provider"],
        "threed_provider_model": threed["model"],
        "threed_provider_task_id": threed["task_id"],
        "threed_licence_gate": threed["licence_gate"],
        "threed_image_checkpoint": env.get(THREED_CHECKPOINT_ENV) if threed_local else None,
        "commands": commands,
        "glb": str(glb_path),
        "glb_sha256": sha256_of(glb_path),
    }
    sidecar = Path(f"{glb_path}.provenance.json")
    sidecar.write_text(json.dumps(record, indent=2) + "\n")
    return sidecar


def run_stage(cmd, stage, log_path, name, output_path, env=None, fatal=True):
    start = time.monotonic()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 2:
        time.sleep(20)
        start = time.monotonic()
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    elapsed = time.monotonic() - start
    append_row(log_path, name, stage, elapsed, result.returncode, output_path)
    if result.returncode != 0:
        # nexus-* --json reports errors on stdout, so show both streams.
        print(f"{stage} stage failed (exit {result.returncode}):\n{result.stderr}{result.stdout}",
              file=sys.stderr)
        if not fatal:
            return elapsed, None
        sys.exit(1)
    parsed = {}  # success; None is reserved for a non-fatal failure
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                pass
    return elapsed, parsed


def run_local_3d(image_path, glb_path, args, log_path, env, fatal):
    """Local TripoSplat via nexus-3d. Returns (ok, seconds, cmd). Non-fatal failures let auto try Meshy."""
    # --game-ready chains nexus-3d's own handoff step internally; the top-level
    # nexus_3d.py CLI has no --qa-kind flag (only `nexus-3d handoff` does), so
    # --qa-kind isn't forwarded here.
    cmd = ["nexus-3d", "--image", str(image_path), "--out", str(glb_path),
           "--game-ready", "--model", THREED_MODEL]
    if args.profile is not None:
        cmd += ["--profile", args.profile]
    cmd.append("--json")
    try:
        elapsed, parsed = run_stage(cmd, "3d:local", log_path, args.name, str(glb_path), env=env, fatal=fatal)
    except OSError as exc:  # nexus-3d missing: "down"
        if fatal:
            raise
        print(f"3d:local unavailable ({exc})", file=sys.stderr)
        append_row(log_path, args.name, "3d:local", 0, 1, str(glb_path))
        return False, 0.0, cmd
    return parsed is not None, elapsed, cmd


def three_d_stage(args, image_path, glb_path, log_path, env, provider_env, stage_seconds, commands):
    """Run the 3D stage per --3d-provider. Returns the `threed` sidecar record (None = local TripoSplat)."""
    choice = args.threed_provider
    # Upload allow-list: the repo, plus the concept image this run generated itself. Never derived from --out-dir.
    roots = [REPO_ROOT] + ([Path(image_path).resolve().parent] if args.prompt else [])
    # Speed-first (owner 2026-11-07): auto tries each cloud provider that is configured and reachable, then local
    # TripoSplat. A forced provider never falls back. `local` never builds or contacts a cloud adapter (not even TCP).
    if choice == "local":
        cloud, order = {}, ["local"]
    else:
        cloud = threed_cloud_providers(provider_env, roots)
        order = list(THREED_CLOUD_ORDER) + ["local"] if choice == "auto" else [choice]
    for name in order:
        last = name == order[-1]
        if name == "local":
            ok, elapsed, cmd = run_local_3d(image_path, glb_path, args, log_path, env, fatal=last)
            commands.append(cmd)
            if ok:
                stage_seconds["3d (local)"] = elapsed
                return None
            continue
        provider = cloud[name]
        status, detail = provider.check()  # key/terms gate first: an unconfigured provider costs no network at all
        if status != meshy_provider.READY:
            if choice == "auto":  # skipped, not attempted: no log row, never stalls auto
                print(f"3d: {name} skipped ({status}: {detail})", file=sys.stderr)
                continue
            append_row(log_path, args.name, f"3d:{name}", 0, 1, str(glb_path))
            print(f"3d stage failed: {name} {status} ({detail})", file=sys.stderr)
            sys.exit(1)
        start = time.monotonic()
        raw_path = glb_path.with_name(f"{glb_path.stem}.{name}_raw.glb")
        err = None
        try:
            poly = getattr(args, "target_polycount", None)
            extra = {"target_polycount": poly} if name == "meshy" and poly is not None else {}
            info = provider.generate_3d(image_path, raw_path, **extra)
        except concept_providers.ProviderError as exc:
            err = str(exc)
        if err is None:
            append_row(log_path, args.name, f"3d:{name}", time.monotonic() - start, 0, str(raw_path))
            # Same game-ready/QA tail as the local path: nexus-3d handoff (CPU only), never ship the raw GLB.
            hand = ["nexus-3d", "handoff", "--glb", str(raw_path), "--out", str(glb_path),
                    "--qa-kind", args.qa_kind, "--json"]
            if args.profile is not None:
                hand[4:4] = ["--profile", args.profile]
            try:
                _, parsed = run_stage(hand, "3d:handoff", log_path, args.name, str(glb_path), env=env, fatal=False)
            except OSError as exc:
                parsed, err = None, f"nexus-3d missing ({exc})"
            if parsed is None and err is None:
                err = "nexus-3d handoff failed"
        else:
            append_row(log_path, args.name, f"3d:{name}", time.monotonic() - start, 1, str(raw_path))
        if err is not None:
            raw_path.unlink(missing_ok=True)  # no cloud model without a provenance record stays on disk
            print(f"3d: {name} path failed ({err})" + ("" if last else "; trying the next 3D provider"), file=sys.stderr)
            if last:
                sys.exit(1)
            continue
        elapsed = time.monotonic() - start
        commands.extend([info["command"], hand])
        stage_seconds[f"3d ({name})"] = elapsed
        record = {"provider": name, "model": info["model"], "task_id": info["task_id"],
                  "licence_gate": info["licence_gate"]}
        if "target_polycount" in info:
            record["target_polycount"] = info["target_polycount"]
        return record
    sys.exit(1)  # local was last and non-fatal run_local_3d cannot happen; defensive


def write_tts_provenance(audio_path: Path, args, info, used=None):
    """<audio>.provenance.json for a --tts voice line: what was said, by which model and voice, with which
    direction. Voice lines are AI-generated content (Rule 15(c)): list them in the AI disclosure, not as sourced."""
    record = {
        "schema_version": 1,
        "tool": "megajam/scripts/gen_asset.py --tts",
        "kind": "voice_line",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "name": args.name,
        "local_only": False,
        "ai_generated": True,
        "text": args.tts,
        "provider": "fal",
        "engine": info["engine"],
        "model": info["model"],
        "settings": info["settings"],
        "voice": (used or {}).get("voice"),
        "style": (used or {}).get("style"),
        "requested": {"voice": args.tts_voice, "style": args.tts_style, "engine": args.tts_engine},
        "notes": (used or {}).get("notes", []),
        "request_id": info.get("request_id"),
        "licence_gate": info.get("licence_gate"),
        "commands": [info["command"]],
        "output_sha256": sha256_of(audio_path),
    }
    sidecar = Path(f"{audio_path}.provenance.json")
    sidecar.write_text(json.dumps(record, indent=2) + "\n")
    return sidecar


def tts_engine_options(args, engine, first):
    """Per-engine voice/style. --tts-voice and --tts-style are Gemini options: in auto mode a fallback engine never
    receives them (a Gemini voice name is not a MiniMax voice_id); it gets --tts-minimax-voice or its default.
    A forced engine takes --tts-voice as written. Returns (voice, style, notes)."""
    notes = []
    if engine == "gemini":
        return args.tts_voice, args.tts_style, notes
    if first and args.tts_engine != "auto":
        if args.tts_style:
            notes.append("style not applied: minimax has no delivery-direction input")
        return args.tts_voice, None, notes
    voice = getattr(args, "tts_minimax_voice", None)
    if args.tts_voice:
        notes.append(f"voice {args.tts_voice!r} is a gemini voice, not sent to minimax; used "
                     f"{voice or fal_tts_provider.DEFAULT_VOICE['minimax']!r}")
    if args.tts_style:
        notes.append("style not applied: minimax has no delivery-direction input")
    return voice, None, notes


def run_tts(args, asset_dir, log_path, provider_env, provider=None):
    """--tts mode. Returns the exit code. auto tries each engine once; a forced engine never falls back."""
    provider = provider or fal_tts_provider.FalTTSProvider(environ=provider_env, allowed_roots=[REPO_ROOT])
    status, detail = provider.gate()
    if status != concept_providers.READY:
        print(f"--tts: fal not configured: {detail}", file=sys.stderr)
        append_row(log_path, args.name, "tts:fal", 0, 1, "")
        return 1
    engines = list(fal_tts_provider.AUTO_ORDER) if args.tts_engine == "auto" else [args.tts_engine]
    for index, engine in enumerate(engines):
        start = time.monotonic()
        voice, style, notes = tts_engine_options(args, engine, index == 0)
        try:
            info = provider.synthesize(args.tts, asset_dir / args.name, engine=engine, voice=voice,
                                       style=style, quality=args.tts_quality,
                                       temperature=args.tts_temperature, emotion=args.tts_emotion)
        except (concept_providers.ProviderError, ValueError) as exc:
            append_row(log_path, args.name, f"tts:{engine}", time.monotonic() - start, 1, "")
            print(f"--tts {engine} failed: {exc}", file=sys.stderr)
            continue
        audio_path = Path(info["path"])
        append_row(log_path, args.name, f"tts:{engine}", time.monotonic() - start, 0, str(audio_path))
        used = {"voice": info["settings"].get("voice") or (info["settings"].get("voice_setting") or {}).get("voice_id"),
                "style": info["settings"].get("style_instructions"), "notes": notes}
        sidecar = write_tts_provenance(audio_path, args, info, used)
        print(f"voice line: {args.name}")
        print(f"  audio: {audio_path}")
        print(f"  model: {info['model']} ({engine})")
        print(f"  provenance: {sidecar}")
        return 0
    return 1


def main():
    args = parse_args()
    # Provider secrets (XAI_API_KEY ...) come from the env file but stay out of os.environ, so
    # child processes (nexus-*, codex) never inherit them.
    provider_env = merged_env()

    if args.providers_check:
        for line in concept_providers.providers_check(concept_providers.default_providers(args.model, environ=provider_env)):
            print(f"{line} | licence: {licence_verdict(line.split(':', 1)[0])}")
        for name, provider in threed_cloud_providers(provider_env, [REPO_ROOT]).items():
            status, detail = provider.check()
            print(f"{name} (3d): {status} - {detail} | licence: {licence_verdict(name, flag="--3d-provider")}")
        status, detail = fal_tts_provider.FalTTSProvider(environ=provider_env, allowed_roots=[REPO_ROOT]).check()
        print(f"fal (tts): {status} - {detail}")
        sys.exit(0)

    if args.meshy_balance:
        try:
            print(json.dumps(threed_cloud_providers(provider_env, [REPO_ROOT])["meshy"].balance()))
        except concept_providers.ProviderError as exc:
            print(f"meshy balance failed: {exc}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if not NAME_RE.match(args.name):
        print(f"--name {args.name!r} is not filename-safe (letters, digits, _, - only)", file=sys.stderr)
        sys.exit(2)

    err = check_model_allowed(args.model)
    if err:
        print(f"--model: {err}", file=sys.stderr)
        sys.exit(2)

    env = threed_env(os.environ)
    err = check_model_allowed(env[THREED_CHECKPOINT_ENV])
    if err:
        print(f"{THREED_CHECKPOINT_ENV}: {err}", file=sys.stderr)
        sys.exit(2)

    out_dir = Path(args.out_dir).resolve()
    if BLOCKED_RE.search(str(out_dir)):
        print(f"--out-dir resolves to {out_dir}, which touches a UC2/UT2004 path; refusing", file=sys.stderr)
        sys.exit(2)

    asset_dir = out_dir / args.name
    asset_dir.mkdir(parents=True, exist_ok=True)

    log_path = Path(args.log)
    ensure_csv_header(log_path)

    if args.tts:
        sys.exit(run_tts(args, asset_dir, log_path, provider_env))

    stage_seconds = {}
    commands = []

    concept = None
    reused_prompt = None  # prompt of a concept made earlier by --concept-only (--image path)
    if args.prompt:
        concept_path = asset_dir / "concept.png"
        provider_set = concept_providers.default_providers(args.model, environ=provider_env)
        if args.image_size:
            provider_set["fal"].image_size = {"width": args.image_size[0], "height": args.image_size[1]}
        try:
            concept = concept_providers.generate_concept(args.provider, args.prompt, concept_path, provider_set)
        except concept_providers.ProviderError as exc:
            for a in getattr(exc, "attempts", []):
                append_row(log_path, args.name, f"image:{a['provider']}", a["seconds"],
                           0 if a["outcome"] == "ok" else 1, str(concept_path))
            print(f"image stage failed: {exc}", file=sys.stderr)
            sys.exit(1)
        for a in concept["attempts"]:
            append_row(log_path, args.name, f"image:{a['provider']}", a["seconds"],
                       0 if a["outcome"] == "ok" else 1, str(concept_path))
        commands.append(concept["command"])
        stage_seconds[f"image ({concept['provider']})"] = concept["seconds"]
        image_path = concept_path
    else:
        image_path = Path(args.image)
        prior = load_concept_sidecar(image_path)
        if prior:
            concept = {"provider": prior["provider"], "model": prior.get("model"),
                       "licence_gate": prior.get("licence_gate"), "attempts": prior.get("attempts", [])}
            commands.extend(prior.get("commands", []))
            reused_prompt = prior.get("prompt")

    if args.concept_only:
        side = Path(f"{image_path}.provenance.json")
        side.write_text(json.dumps({
            "name": args.name, "kind": "concept-image", "prompt": args.prompt,
            "provider": concept["provider"], "model": concept.get("model"),
            "image_model_id": concept.get("model"),  # hub 142 rule: the concept model id is always written out
            "licence_verdict": licence_verdict(concept["provider"]),
            "licence_gate": concept.get("licence_gate"),
            "image_size": args.image_size,
            "image_sha256": sha256_of(image_path),
            "attempts": concept["attempts"], "commands": commands,
            "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
        }, indent=2) + "\n")
        append_row(log_path, args.name, "total", sum(stage_seconds.values()), 0, str(image_path))
        print(f"concept: {args.name} -> {image_path}\n  provenance: {side}")
        sys.exit(0)

    glb_path = asset_dir / f"{args.name}.glb"

    threed = three_d_stage(args, image_path, glb_path, log_path, env, provider_env, stage_seconds, commands)
    sidecar = write_provenance(glb_path, args, image_path, commands, env, concept, threed, prompt=reused_prompt)

    total = sum(stage_seconds.values())
    append_row(log_path, args.name, "total", total, 0, str(glb_path))

    print(f"asset: {args.name}")
    for stage, seconds in stage_seconds.items():
        print(f"  {stage}: {seconds:.2f}s")
    print(f"  total: {total:.2f}s")
    print(f"  output: {glb_path}")
    print(f"  provenance: {sidecar}")

    sys.exit(0)


if __name__ == "__main__":
    main()
