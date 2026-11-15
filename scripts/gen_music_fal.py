#!/usr/bin/env python3
"""CLI for cloud music on fal (ElevenLabs Music, Stable Audio 2.5 fallback) and its vocal gate (speech-to-text).

Thin wrapper over providers/fal.py `FalMusicProvider`. Every paid call goes through one guard:
  * the same gate as every cloud adapter: FAL_KEY and FAL_TERMS_REVIEWED from ~/.config/megajam.env (never printed);
  * the charge is RESERVED in the ONE live ledger ~/.local/state/megajam/cloud-spend-ledger.csv (outside git, shared by
    every worktree, a FIXED path: no flag or environment variable can point the budget elsewhere; the tracked CSV under
    stages/02_build/output/ is only a copy) BEFORE the request is sent (under a
    file lock, so two runs cannot both pass the cap), updated with the request id the moment fal accepts it, and finished
    after the download. A kill, Ctrl-C, SIGTERM or crash at any point therefore still leaves the spend counted;
  * a hard budget in code: HARD_CAP $15 and STOP_AT $12 over ALL rows in the ledger (the --campaign name is only a
    label). --cap / --stop-at can only lower them. Past STOP_AT only the lead raises the line, by writing a number
    (at most HARD_CAP) into STOP_APPROVAL_FILE;
  * prices: table (fal llms.txt pages) is the floor; the live pricing API is used only if positive, in the model's own
    unit and not lower (so a 0 price can never make a paid call look free);
  * a `<audio>.provenance.json` sidecar per take and one row in asset-pipeline-log.csv (stage "music:fal").

  gen_music_fal.py price                               # live unit prices, spends nothing
  gen_music_fal.py plan drive                          # print a preset's composition plan and its cost, spends nothing
  gen_music_fal.py gen --job drive_a --preset drive --out work/audio/music/drive_a
  gen_music_fal.py gen --job loop_x --model stable --accept-unverified-licence --prompt "..." --seconds 34 --out ...
  gen_music_fal.py fetch --job drive_a --request-id ID --out work/audio/music/drive_a   # re-download, bills nothing
  gen_music_fal.py vocal-check take.wav --job vc_drive_a   # speech-to-text on the take; exit 6 if sung words found

`--out` is a stem: the extension (.wav / .mp3) is chosen from what fal returns. Keep outputs under work/audio/ (git-
ignored) or outside the repo. Presets are the "Jump Cut" 70s funk score sections (112 BPM); --plan-file takes any
composition plan JSON. Only music (and its vocal check) is ledgered here: fal image / 3D / TTS spend is not.
Exit codes: 0 ok, 1 call failed, 2 not configured / bad input, 4 would pass the hard cap, 5 would pass the stop line
(ask the lead), 6 vocal gate failed.
"""
import argparse
import contextlib
import csv
import fcntl
import json
import math
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_asset  # noqa: E402  (merged_env, ensure_csv_header, append_row)
from providers import ProviderError  # noqa: E402
from providers import fal as fal_provider  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
ASSET_LOG = REPO / "stages/02_build/output/asset-pipeline-log.csv"
STATE_DIR = Path.home() / ".local/state/megajam"
# The LIVE ledger (and its lock) live at ONE fixed path outside any git checkout: every worktree of this repo shares the
# same budget, and a `git checkout` / `reset` can never rewind the spend. The tracked CSV in the repo is only a copy
# (REPO_LEDGER_COPY) refreshed after every write to the LIVE ledger, for the record and the PR diff.
LIVE_LEDGER = STATE_DIR / "cloud-spend-ledger.csv"
REPO_LEDGER_COPY = REPO / "stages/02_build/output/cloud-spend-ledger.csv"
# The ledger every function below reads and writes. It is LIVE_LEDGER and nothing in the environment or on the command
# line can change it (an override would be a fresh $15 budget: round-3 review). Unit tests patch this name, nothing else.
SPEND_LEDGER = LIVE_LEDGER
STOP_APPROVAL_FILE = STATE_DIR / "music-stop-approval.txt"
HARD_CAP = 15.0   # USD, all music spend, all campaigns. Code constant on purpose: flags may only lower it.
STOP_AT = 12.0    # USD: past this, stop and ask the lead; the lead raises it (<= HARD_CAP) via STOP_APPROVAL_FILE.
LEDGER_FIELDS = ["timestamp_iso", "campaign", "job", "provider", "model", "audio_seconds", "cost_usd_est",
                 "cost_basis", "request_id", "status", "output_path", "licence_note", "terms_gate", "note", "row_id"]
MODELS = {"eleven": fal_provider.MUSIC_MODEL, "stable": fal_provider.MUSIC_FALLBACK_MODEL}
DEFAULT_FORMATS = "pcm_44100,mp3_44100_192,mp3_44100_128"  # best first; the next one only if fal rejects the submit

GLOBAL_POSITIVE = ["1970s cop-show car-chase funk score", "112 BPM", "wah-wah guitar", "punchy drum breaks",
                   "Fender bass", "brass stabs", "clavinet", "analog tape warmth", "instrumental"]
GLOBAL_NEGATIVE = ["vocals", "lyrics", "singing", "humming", "choir", "spoken words", "EDM", "trap",
                   "orchestral strings", "hiss"]
BAR_MS = 2134  # one bar at the 112.46 BPM fal's model actually played when asked for 112 (measured on take 1)


class Refuse(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def section(name, ms, positive, negative=()):
    return {"section_name": name, "positive_local_styles": list(positive), "negative_local_styles": list(negative),
            "duration_ms": int(ms), "lines": []}


def preset_plan(name, key=None):
    """Composition plan for a preset (music spec: hub141 road-to-30 section 2, plus the lead's 11-12 note: DRIVE-A
    sparser, DRIVE-B clearly bigger). Section lengths are whole bars (BAR_MS) so loops cut on the bar grid, and each
    plan stays under a whole number of billed minutes. `key` ("F minor") pins hold/stinger takes to the drive."""
    pos = list(GLOBAL_POSITIVE) + ([f"key of {key}"] if key else [])
    intro = section("INTRO", 2 * BAR_MS, ["single brass hit", "drum pickup fill", "builds into the groove"])
    a = section("DRIVE-A", 16 * BAR_MS, ["sparse groove, restrained, plenty of space", "bass, drums and clavinet only",
                                         "tight pocket, locked to the beat"],
                ["brass", "lead guitar", "wah-wah", "busy fills"])
    b = section("DRIVE-B", 16 * BAR_MS, ["full brass section stabs and swells", "wah-wah guitar lead up front",
                                         "drums open with hi-hat and fills", "big, hotter, much more energy, louder"])
    a2 = section("DRIVE-A'", 16 * BAR_MS, ["return of the sparse groove", "bass, drums and clavinet only"],
                 ["brass", "lead guitar", "wah-wah"])
    tag = section("TAG", 4 * BAR_MS, ["final brass stab ending", "hits on the one", "short tail"])
    hold = section("HOLD", 16 * BAR_MS, ["same key and tempo, half-time feel", "muted wah guitar", "suspense", "low-passed",
                                         "sustained tense bass"], ["brass stabs", "bright", "busy drums", "vocals"])

    def cut(n):
        return section(f"CUT-{n}", 2 * BAR_MS, ["reverse cymbal swell into one hard brass stab", "dry, abrupt stop"],
                       ["melody", "vocals", "long tail"])

    def wrap(n):
        return section(f"WRAP-{n}", 3 * BAR_MS, ["triumphant brass stab ending", "rising run into a final chord",
                                                  "short decay"], ["vocals"])
    sections = {
        "drive": [intro, a, b, a2, tag],  # 115.2 s: two billed minutes
        "drive-test": [section("INTRO", 4000, intro["positive_local_styles"]),
                       section("DRIVE-A", 34000, ["steady groove", "bass, drums and clavinet only"], ["brass", "lead guitar"]),
                       section("DRIVE-B", 14000, ["brass stabs", "wah-wah guitar lead", "hotter, more energy"]),
                       section("TAG", 6000, tag["positive_local_styles"])],  # the 58 s probe of 2026-11-12
        "hold-pack": [hold, cut(1), wrap(1), cut(2), wrap(2)],  # 55.5 s: ONE billed minute, a hold + 2 cuts + 2 wraps
    }
    if name not in sections:
        raise SystemExit(f"unknown preset {name!r}; choose from {', '.join(sections)}")
    return {"positive_global_styles": pos, "negative_global_styles": list(GLOBAL_NEGATIVE), "sections": sections[name]}


def plan_seconds(plan):
    return sum(s["duration_ms"] for s in plan["sections"]) / 1000.0


# --- the spend ledger: lock, reserve, update --------------------------------------------------------------------------
@contextlib.contextmanager
def ledger_lock(path):
    """Exclusive lock for the whole read-check-write on the ledger (a lock file beside it; released on any exit)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + ".lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _is_live(path):
    return Path(path).resolve() == Path(LIVE_LEDGER).resolve()


def _parse_ledger(path):
    """Strictly parse an existing ledger file (see read_rows for what is corrupt)."""
    try:
        with open(path, newline="") as f:
            reader = csv.reader(f)
            if next(reader, None) != LEDGER_FIELDS:
                raise Refuse(2, f"the spend ledger {path} is empty or its header is not the ledger header; restore the "
                                f"real ledger by hand before any spend")
            rows = []
            for cells in reader:
                if not cells:
                    continue  # a blank line
                if len(cells) != len(LEDGER_FIELDS):
                    raise Refuse(2, f"the spend ledger {path} has a row with {len(cells)} cells instead of "
                                    f"{len(LEDGER_FIELDS)} (line {reader.line_num}); fix it by hand before any spend")
                rows.append(dict(zip(LEDGER_FIELDS, cells)))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise Refuse(2, f"the spend ledger {path} is not readable as CSV ({exc}); fix it by hand before any spend")
    return rows


def _row_key(row):
    """What identifies a ledger row across the live ledger and its export: its row_id (a legacy row without one: all cells)."""
    return row.get("row_id") or tuple(row.get(k, "") for k in LEDGER_FIELDS)


def _read_export(live):
    """(export path, its rows) for the tracked repo export, read with the same strict reader; (None, []) when there is
    nothing to compare with (no export configured, or the live ledger IS the export). A missing export file is simply no
    rows. A symlink or corrupt export refuses too: it is the record the live ledger is checked against."""
    copy = Path(REPO_LEDGER_COPY) if REPO_LEDGER_COPY else None
    if copy is None or copy.resolve() == Path(live).resolve():
        return None, []
    try:
        return copy, read_rows(copy)
    except Refuse as exc:
        raise Refuse(exc.code, f"the repo export {copy} is not a usable ledger, and the live ledger is checked against it "
                               f"({exc}); fix it by hand before any spend (git checkout -- {shlex.quote(str(copy))} "
                               f"restores the committed copy)")


def _refuse_if_behind_export(live, rows, copy, prior):
    """On the live ledger only. Every row of the export must also be in the live ledger: exports are copies of live rows
    written in the same locked write, so on one machine the live ledger is always a superset of every export. An export
    row the live ledger lacks means the live file was lost (the $15 is NOT fresh), restored from an older copy, or belongs
    to another machine that shares the FAL_KEY and has not spent the export's share: either way the next write would
    overwrite the export's bigger record with a smaller one. Refuse (exit 2) and say how to put it right. A deliberate
    first ledger needs the export to be empty too (absent or header-only), which is visible in git."""
    have = {_row_key(r) for r in rows}
    missing = [r for r in prior if _row_key(r) not in have]
    if not missing:
        return
    total = round(sum(row_cost(r) for r in missing), 2)
    if not rows:
        what = (f"the live spend ledger {live} is missing or has no rows, but the repo export {copy} shows ${total:.2f} of "
                f"prior spend in {len(missing)} rows")
    else:
        ids = ", ".join(str(r.get("row_id") or "(no row_id)") for r in missing[:5]) + (" ..." if len(missing) > 5 else "")
        what = (f"the live spend ledger {live} is BEHIND the repo export {copy}: it lacks {len(missing)} of the export's "
                f"rows (${total:.2f}; row_id {ids})")
    if have <= {_row_key(r) for r in prior}:  # the export holds every row the live ledger has: copying it loses nothing
        fix = (f"restore it by hand before any spend:\n  install -D -m 600 {shlex.quote(str(copy))} {shlex.quote(str(live))}\n"
               f"(if you work from several worktrees, use the export with the most rows: git worktree list)")
    else:  # the live ledger also has rows the export lacks (another worktree or machine spent): a copy would drop them
        fix = ("the live ledger also has rows the export lacks, so do NOT copy the export over it: append the missing rows "
               "from the export (use the export with the most rows across git worktree list) to the live ledger by hand, "
               "same header and columns, before any spend")
    raise Refuse(2, f"{what}; {fix}\n(to start a fresh ledger on purpose, empty the export down to its header line first)")


def read_rows(path):
    """The ledger's rows. No file yet = an empty ledger, but only if the repo export shows no prior spend either (the very
    first run). A file that is a symlink or not a plain file, whose first line is not EXACTLY the LEDGER_FIELDS header (an
    empty file included), or with a row that does not have exactly one cell per column, is corrupt: Refuse(2), never a
    silent $0 (a hand-made, stale or lost file must not become a fresh budget). The LIVE ledger is also checked against the
    tracked export on every read: an export row_id the live ledger lacks refuses (_refuse_if_behind_export)."""
    path = Path(path)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise Refuse(2, f"the spend ledger {path} is a symlink or not a plain file; replace it with the real ledger by hand "
                        f"before any spend")
    if not _is_live(path):
        return _parse_ledger(path) if path.exists() else []
    # The export is read FIRST: a writer refreshes the live ledger and only then the export, so a live snapshot taken after
    # the export snapshot always holds every row of it, even when a write lands between the two reads (no lock on this path).
    copy, prior = _read_export(path)
    rows = _parse_ledger(path) if path.exists() else []
    if prior:
        _refuse_if_behind_export(path, rows, copy, prior)
    return rows


def _atomic_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in LEDGER_FIELDS})
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_rows(path, rows):
    """Atomic rewrite (temp file + rename): a reader or a kill never sees a half-written ledger. After the live ledger
    is written, the tracked repo copy is refreshed best-effort (an export; the same bytes whichever worktree writes it;
    read back only to refuse a lost, reset or behind live ledger). Only the LIVE ledger is exported, and never an empty
    one over a copy that may hold the record: any other path (a test or probe ledger) never touches the export."""
    _atomic_csv(path, rows)
    copy = REPO_LEDGER_COPY
    if copy and rows and Path(path).resolve() == Path(LIVE_LEDGER).resolve() and Path(copy).resolve() != Path(path).resolve():
        with contextlib.suppress(OSError):
            _atomic_csv(copy, rows)


def row_cost(row):
    """USD of one ledger row. A cost that is missing, empty, or not a finite number >= 0 is a corrupt ledger: stop, never
    guess (and never read it as $0)."""
    cell = row.get("cost_usd_est")
    raw = cell.strip() if isinstance(cell, str) else cell
    try:
        value = float(raw) if raw else float("nan")  # None / "" / whitespace: nothing to parse
    except (TypeError, ValueError):
        value = float("nan")
    if not math.isfinite(value) or value < 0:
        raise Refuse(2, f"the spend ledger has a corrupt cost {raw!r} (job {row.get('job')!r}); fix it by hand before any spend")
    return value


def spent_total(path=None):
    """USD already spent or reserved: every row, every campaign."""
    return round(sum(row_cost(r) for r in read_rows(path or SPEND_LEDGER)), 4)


def update_row(row_id, **fields):
    """Change fields of one ledger row, under the lock. A missing row is an error (never silently lose a charge)."""
    ledger = SPEND_LEDGER
    with ledger_lock(ledger):
        rows = read_rows(ledger)
        hit = [r for r in rows if r.get("row_id") == row_id]
        if not hit:
            raise KeyError(f"ledger row {row_id} not found")
        for k, v in fields.items():
            hit[0][k] = f"{v:.4f}" if k == "cost_usd_est" else v
        write_rows(ledger, rows)


def limits(cap_flag=None, stop_flag=None, approval_file=None):
    """(cap, stop line). The code constants win; the flags and the lead's approval file are applied as documented."""
    cap = min(HARD_CAP, max(0.0, cap_flag)) if cap_flag is not None else HARD_CAP  # --cap 0 means "spend nothing"
    stop = STOP_AT
    approval = approval_file or STOP_APPROVAL_FILE
    try:
        raised = float(Path(approval).read_text().strip().split()[0])
        if STOP_AT < raised <= HARD_CAP:
            stop = raised
    except (OSError, ValueError, IndexError):
        pass
    if stop_flag is not None:
        stop = min(stop, max(0.0, stop_flag))
    return cap, min(stop, cap)


def reserve(row, est, cap, stop, force=False):
    """Check the budget and append the reserved row in ONE locked step. Returns the row id. Raises Refuse.
    `force=True` is for a charge that has ALREADY happened (a fetch of an unledgered request): it is recorded even
    past the cap, because refusing would leave real spend off the books."""
    if not isinstance(est, (int, float)) or not math.isfinite(est) or est < 0:
        raise Refuse(2, f"refusing: the cost estimate {est!r} is not a finite number >= 0")
    ledger = SPEND_LEDGER
    with ledger_lock(ledger):
        rows = read_rows(ledger)
        spent = 0.0 if force else round(sum(row_cost(r) for r in rows), 4)  # a charge already made is booked, never refused
        if not force and spent + est > cap:
            raise Refuse(4, f"refusing: ${spent + est:.2f} (spent ${spent:.2f} + ${est:.2f}) would pass the hard cap ${cap:.2f}")
        if not force and spent + est > stop:
            raise Refuse(5, f"refusing: ${spent + est:.2f} (spent ${spent:.2f} + ${est:.2f}) would pass the stop line "
                            f"${stop:.2f}; ask the lead, who raises it in {STOP_APPROVAL_FILE}")
        row = dict(row, row_id=uuid.uuid4().hex[:12], cost_usd_est=f"{est:.4f}", status="reserved")
        rows.append(row)
        write_rows(ledger, rows)
        return row["row_id"]


# --- helpers -----------------------------------------------------------------------------------------------------------
def audio_seconds_of(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        return float(out)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def sniff_ext(path, content_type):
    head = Path(path).read_bytes()[:12]
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return ".wav"
    if head[:3] == b"ID3" or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return ".mp3"
    if head[:4] == b"OggS":
        return ".ogg"
    if "wav" in (content_type or ""):
        return ".wav"
    if "mpeg" in (content_type or "") or "mp3" in (content_type or ""):
        return ".mp3"
    return ".raw"  # e.g. headerless PCM: the caller converts it (ffmpeg -f s16le -ar 44100 -ac 2)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_provider(env):
    return fal_provider.FalMusicProvider(environ=env)


def require_ready(prov):
    status, detail = prov.gate()
    if status != "ready":
        print(f"fal music not ready: {detail}", file=sys.stderr)
        return False
    return True


def estimate(prov, model_id, seconds, check_price=True):
    """(usd estimate, usd per unit, basis). Live price only through unit_price_for (positive, right unit, not below table)."""
    live, unit = None, None
    if check_price:
        try:
            live, unit = prov.price([model_id]).get(model_id, (None, None))
        except (ProviderError, KeyError, TypeError, ValueError, AttributeError) as exc:  # includes a changed schema
            print(f"warning: live price check failed ({exc}); using the table", file=sys.stderr)
    usd, basis = fal_provider.unit_price_for(model_id, live, unit)
    return fal_provider.music_cost_estimate(model_id, seconds, usd), usd, basis


def log_asset_row(job, seconds, code, path):
    gen_asset.ensure_csv_header(ASSET_LOG)
    gen_asset.append_row(ASSET_LOG, job, "music:fal", seconds, code, str(path or ""))


def base_row(args, model_id, prov, seconds, basis):
    return {"timestamp_iso": now_iso(), "campaign": args.campaign, "job": args.job, "provider": "fal", "model": model_id,
            "audio_seconds": f"{seconds:.1f}", "cost_basis": basis, "request_id": "", "output_path": "",
            "licence_note": fal_provider.MUSIC_PRICES[model_id]["terms"], "terms_gate": prov.licence_gate(),
            "note": args.note or ""}


def settle_failure(row_id, info, error, job):
    """Final ledger status for a failed paid call. Only an HTTP 4xx answer to the submit counts as not billed."""
    if info.get("definitive_reject"):
        update_row(row_id, cost_usd_est=0.0, status=f"rejected-not-billed (HTTP {info.get('http_status')})")
        return
    rid = info.get("request_id")
    if rid:
        update_row(row_id, status="failed-after-queue (billing unknown, counted)", request_id=rid)
        print(f"  request {rid} was queued and is billed; to collect its audio without paying again: "
              f"gen_music_fal.py fetch --job {job} --request-id {rid} --out STEM", file=sys.stderr)
    else:
        update_row(row_id, status="submit-uncertain (counted; fal may have queued it)")


# --- commands ----------------------------------------------------------------------------------------------------------
def cmd_price(args, env):
    prov = make_provider(env)
    if not require_ready(prov):
        return 2
    prices = prov.price(list(fal_provider.MUSIC_PRICES))
    for model in fal_provider.MUSIC_PRICES:
        live, unit = prices.get(model, (None, None))
        usd, basis = fal_provider.unit_price_for(model, live, unit)
        print(f"{model}: live {live} per {unit} -> using ${usd} ({basis})")
    return 0


def cmd_usage(args, env):
    """What fal says it billed since --since (needs a key with billing read scope; ours has none: HTTP 403)."""
    prov = make_provider(env)
    if not require_ready(prov):
        return 2
    for model, (qty, cost) in prov.usage(list(fal_provider.MUSIC_PRICES), args.since).items():
        print(f"{model}: quantity {qty}, billed ${cost}")
    return 0


def cmd_plan(args, env):
    plan = preset_plan(args.preset, args.key)
    est = fal_provider.music_cost_estimate(fal_provider.MUSIC_MODEL, plan_seconds(plan))
    print(json.dumps(plan, indent=2))
    print(f"# {plan_seconds(plan):.1f} s -> about ${est:.2f} on {fal_provider.MUSIC_MODEL}", file=sys.stderr)
    return 0


def build_inputs(args):
    """(inputs dict for fal, audio seconds the call will produce)."""
    if args.model == "stable":
        seconds = args.seconds or 34
        prompt = args.prompt or ""
        if args.negative:
            prompt += f". Avoid: {args.negative}"  # Stable Audio 2.5 has no negative prompt field
        return {"prompt": prompt, "seconds_total": int(seconds)}, float(seconds)
    if args.plan_file:
        plan = json.loads(Path(args.plan_file).read_text())
    elif args.preset:
        plan = preset_plan(args.preset, args.key)
    else:
        raise SystemExit("eleven needs --preset or --plan-file")
    return {"composition_plan": plan, "respect_sections_durations": True}, plan_seconds(plan)


def finish_ok(row_id, job, out_stem, tmp, info, model_id, usd, est, basis, seconds, elapsed, args, used_format,
              base_inputs, prov):
    final = Path(out_stem).with_name(Path(out_stem).name + sniff_ext(tmp, info.get("content_type")))
    Path(tmp).replace(final)
    actual = audio_seconds_of(final)
    billed = max(est, fal_provider.music_cost_estimate(model_id, actual, usd)) if actual else est
    update_row(row_id, status="ok", output_path=str(final), cost_usd_est=billed, audio_seconds=f"{actual or seconds:.1f}",
               request_id=info.get("request_id") or "")
    log_asset_row(job, elapsed, 0, final)
    sidecar = final.with_name(final.name + ".provenance.json")
    sidecar.write_text(json.dumps({
        "job": job, "campaign": args.campaign, "provider": "fal", "model": model_id,
        "request_id": info.get("request_id"), "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": dict(base_inputs, **({"output_format": used_format} if used_format else {})),
        "output_content_type": info.get("content_type"), "audio_seconds": actual, "cost_usd_est": billed,
        "cost_basis": basis, "licence_note": fal_provider.MUSIC_PRICES[model_id]["terms"],
        "terms_gate": prov.licence_gate(), "ai_generated": True,
        "rule": "AI-generated, not a sourced asset (Official Rules 15(c)); disclose in the AI field",
        "note": args.note or ""}, indent=2) + "\n")
    print(f"OK {job}: {final} ({actual and round(actual, 1)} s, ${billed:.2f}, format {used_format}, "
          f"{info.get('content_type')}, {elapsed:.0f} s wall)")
    return final


def cmd_gen(args, env):
    model_id = MODELS[args.model]
    if args.model == "stable" and not args.accept_unverified_licence:
        print("stable: fal states no licence text for Stable Audio 2.5, so its commercial terms are NOT verified; "
              "re-run with --accept-unverified-licence once the lead has accepted that", file=sys.stderr)
        return 2
    prov = make_provider(env)
    if not require_ready(prov):
        return 2
    base_inputs, seconds = build_inputs(args)
    try:
        spent = spent_total()  # ledger health first: a corrupt ledger means no spend, and no network call (not even pricing)
    except Refuse as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    est, usd, basis = estimate(prov, model_id, seconds, not args.no_price_check)
    cap, stop = limits(args.cap, args.stop_at)
    print(f"{args.job}: {seconds:.0f} s on {model_id}, estimate ${est:.2f} ({basis}); spent+reserved "
          f"${spent:.2f}, stop line ${stop:.2f}, hard cap ${cap:.2f}", file=sys.stderr)
    if args.dry_run:
        return 4 if spent + est > cap else 5 if spent + est > stop else 0

    out_stem = Path(args.out)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_stem.with_name(out_stem.name + ".dl")
    formats = [f for f in args.output_format.split(",") if f] if args.model == "eleven" else [None]
    start = time.monotonic()
    info, error, used_format, row_id = {}, None, None, None
    try:
        for fmt in formats:
            row_id = reserve(base_row(args, model_id, prov, seconds, basis), est, cap, stop)  # BEFORE the request
            inputs = dict(base_inputs, **({"output_format": fmt} if fmt else {}))
            used_format = fmt
            try:
                info = prov.generate_music(model_id, inputs, tmp, args.timeout,
                                           on_queued=lambda rid, rr=row_id: update_row(rr, request_id=rid, status="queued"))
                error = None
                break
            except ProviderError as exc:
                info, error = getattr(exc, "info", {}) or {}, exc
                settle_failure(row_id, info, exc, args.job)
                if not info.get("definitive_reject"):
                    break  # queued or uncertain: never submit again
                print(f"  {fmt}: rejected by fal (HTTP {info.get('http_status')}); nothing billed; trying the next "
                      f"format", file=sys.stderr)
    except Refuse as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    except BaseException:  # Ctrl-C, SIGTERM (turned into KeyboardInterrupt), anything: the reserved row stays counted
        if row_id:
            with contextlib.suppress(Exception):
                update_row(row_id, status="interrupted (counted; request may be queued, see request_id)")
        raise
    elapsed = time.monotonic() - start
    if error is not None:
        Path(tmp).unlink(missing_ok=True)
        log_asset_row(args.job, elapsed, 1, "")
        print(f"FAILED {args.job}: {error}", file=sys.stderr)
        return 1
    finish_ok(row_id, args.job, out_stem, tmp, info, model_id, usd, est, basis, seconds, elapsed, args, used_format,
              base_inputs, prov)
    return 0


def cmd_fetch(args, env):
    """Re-download a queued (already billed) request's audio. Submits nothing; the ledger row is found by request id.
    The request id and the ledger are checked BEFORE any network call: a bad id is a clean exit 2, and a corrupt ledger
    refuses up front, so audio is never saved for a charge that could not be booked."""
    model_id = MODELS[args.model]
    if not fal_provider.valid_request_id(args.request_id):
        print(f"invalid --request-id {str(args.request_id)[:80]!r}: use the id fal returned (letters, digits, '-' and '_', "
              f"at most 64 characters)", file=sys.stderr)
        return 2
    prov = make_provider(env)
    if not require_ready(prov):
        return 2
    try:
        spent_total()
    except Refuse as exc:
        print(f"{exc}\nnot fetching request {args.request_id}: its charge could not be booked. Nothing was downloaded; "
              f"fix the ledger, then re-run the same command.", file=sys.stderr)
        return exc.code
    out_stem = Path(args.out)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_stem.with_name(out_stem.name + ".dl")
    try:
        info = prov.fetch_music(model_id, args.request_id, tmp, args.timeout)
    except ProviderError as exc:
        print(f"FAILED fetch {args.request_id}: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:  # the provider's own input checks; the id was already validated above
        print(f"refusing fetch: {exc}", file=sys.stderr)
        return 2
    final = out_stem.with_name(out_stem.name + sniff_ext(tmp, info.get("content_type")))
    tmp.replace(final)
    seconds = audio_seconds_of(final)
    est, usd, basis = estimate(prov, model_id, seconds or 60, False)
    cap, stop = limits(args.cap, args.stop_at)
    # The audio is saved. Every ledger step below can still fail (a hand edit mid-run), so ALL of them sit in one try and
    # the notice says which step failed and what that means for the budget.
    step = "reading the ledger"
    try:
        hit = [r for r in read_rows(SPEND_LEDGER) if r.get("request_id") == args.request_id]
        if hit:
            step = "updating the original row"
            update_row(hit[0]["row_id"], status="ok (fetched)", output_path=str(final))
        else:  # the original reservation is missing: count the call again rather than lose it
            # The money is already spent: ledger it FIRST and unconditionally (force), then warn if that is over the line.
            step = "booking the charge"
            rid = reserve(base_row(args, model_id, prov, seconds or 0, basis), est, cap, stop, force=True)
            step = "finishing the booked row"
            update_row(rid, status="ok (fetched, original row missing; counted)", request_id=args.request_id,
                       output_path=str(final))
    except Refuse as exc:
        meaning = {"reading the ledger": f"its charge may be missing: if no row for it exists, about ${est:.2f} is NOT "
                                         f"in the budget",
                   "updating the original row": "its original charge is already booked; only that row was not updated",
                   "booking the charge": f"it is NOT ledgered (about ${est:.2f} is missing from the budget)",
                   "finishing the booked row": f"it is booked only as a reserved row (${est:.2f} counts)"}[step]
        print(f"{exc}\nrequest {args.request_id} was fetched to {final} but {step} failed: {meaning}; fix the ledger and "
              f"tell the lead", file=sys.stderr)
        return exc.code
    try:
        total = spent_total()
    except Refuse as exc:  # the fetch itself is booked; only the cap check could not run
        print(f"warning: the fetch is booked, but the ledger could not be totalled to check the cap ({exc})", file=sys.stderr)
    else:
        if total > cap:
            print(f"WARNING: total ${total:.2f} is now over the hard cap ${cap:.2f}; tell the lead", file=sys.stderr)
    print(f"OK fetched {args.request_id}: {final}")
    return 0


# --- vocal gate --------------------------------------------------------------------------------------------------------
FILLER = ("thank you for watching", "thanks for watching", "thank you", "thanks", "music", "applause", "you", "bye",
          "subtitles by", "the end")


def vocal_verdict(text):
    """Machine vocal gate on a transcript. Filler Whisper invents on instrumentals ("Thank you.", "Music") is ignored;
    3+ remaining words = a sung/spoken phrase = reject; 1-2 = borderline (logged, not rejected)."""
    t = re.sub(r"[\[\(][^\]\)]*[\]\)]|[♪♫]", " ", text.lower())
    t = re.sub(r"[^a-z' ]", " ", t)
    t = " " + re.sub(r"\s+", " ", t).strip() + " "
    for f in FILLER:
        t = t.replace(f" {f} ", " ")
        t = t.replace(f" {f} ", " ")
    words = t.split()
    verdict = "clean" if not words else "borderline" if len(words) <= 2 else "vocals-suspected"
    return {"verdict": verdict, "leftover_words": words, "leftover_word_count": len(words)}


def cmd_vocal_check(args, env):
    src = Path(args.audio)
    if not src.exists() and not src.is_symlink():
        print(f"no such file: {src}", file=sys.stderr)
        return 2
    # The upload guards (symlink, plain file, UC2/UT2004 and protected trees) run on the file the caller NAMED, before
    # ffprobe or ffmpeg touch it: the transcoded temp copy below would pass them whatever the original was.
    problem = fal_provider.audio_path_problem(src)
    if problem:
        print(f"refusing {src}: {problem}; nothing was sent", file=sys.stderr)
        return 2
    prov = make_provider(env)
    if not require_ready(prov):
        return 2
    try:
        spent = spent_total()  # ledger health first, as in gen: a bad ledger means no ffprobe, no pricing GET, no ffmpeg
    except Refuse as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    model_id = fal_provider.STT_MODEL
    seconds = audio_seconds_of(src) or 0.0
    est, usd, basis = estimate(prov, model_id, seconds, not args.no_price_check)
    cap, stop = limits(args.cap, args.stop_at)
    with tempfile.TemporaryDirectory() as td:  # a small mono mp3 is enough for speech-to-text and keeps the upload tiny
        small = Path(td) / "vc.mp3"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", "22050", "-b:a", "64k",
                        str(small)], check=True)
        try:  # ALL local validation of what would be uploaded happens before anything is booked or sent
            inputs = fal_provider.stt_inputs(small, trusted_copy=True)  # the named file passed the guards above
        except ValueError as exc:
            print(f"refusing vocal-check {args.job}: {exc}; nothing was sent or booked", file=sys.stderr)
            return 2
        if args.dry_run:
            print(f"{args.job}: would transcribe {seconds:.0f} s ({small.stat().st_size} bytes), estimate ${est:.2f}; "
                  f"spent+reserved ${spent:.2f}, stop line ${stop:.2f}, hard cap ${cap:.2f}")
            return 4 if spent + est > cap else 5 if spent + est > stop else 0  # the same answer gen --dry-run gives
        start = time.monotonic()
        row_id = None
        try:
            row_id = reserve(base_row(args, model_id, prov, seconds, basis), est, cap, stop)
            info = prov.transcribe(small, args.timeout, inputs=inputs,
                                   on_queued=lambda rid: update_row(row_id, request_id=rid, status="queued"))
        except Refuse as exc:
            print(str(exc), file=sys.stderr)
            return exc.code
        except ValueError as exc:  # a local check that fired after the charge was booked: nothing was sent, so no charge
            if row_id:
                update_row(row_id, cost_usd_est=0.0, status="rejected-not-sent (local check failed)")
            print(f"refusing vocal-check {args.job}: {exc}; nothing was sent", file=sys.stderr)
            return 2
        except ProviderError as exc:
            settle_failure(row_id, getattr(exc, "info", {}) or {}, exc, args.job)
            print(f"FAILED vocal-check {args.job}: {exc}", file=sys.stderr)
            return 1
        except BaseException:
            if row_id:
                with contextlib.suppress(Exception):
                    update_row(row_id, status="interrupted (counted)")
            raise
    result = info.get("result") or {}
    verdict = vocal_verdict(result.get("text") or "")
    update_row(row_id, status=f"ok (vocal gate: {verdict['verdict']})", request_id=info.get("request_id") or "",
               output_path=str(src))
    log_asset_row(args.job, time.monotonic() - start, 0, src)
    report = src.with_name(src.name + ".vocal.json")
    report.write_text(json.dumps({"audio": str(src), "model": model_id, "request_id": info.get("request_id"),
                                  "generated_utc": now_iso(), "cost_usd_est": est, "transcript": result.get("text"),
                                  "chunks": result.get("chunks"), **verdict}, indent=2) + "\n")
    print(f"VOCAL {verdict['verdict'].upper()} {src.name}: transcript {result.get('text')!r}; leftover words "
          f"{verdict['leftover_words']}")
    return 0 if verdict["verdict"] != "vocals-suspected" else 6


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("price", help="print live unit prices (free)")
    us = sub.add_parser("usage", help="what fal billed since a date (free; needs billing scope, ours has none)")
    us.add_argument("--since", required=True, help="YYYY-MM-DD or ISO time")
    pl = sub.add_parser("plan", help="print a preset's composition plan and cost (free)")
    pl.add_argument("preset")
    pl.add_argument("--key", help='pin the key, e.g. "F minor"')

    def common(sp):
        sp.add_argument("--job", required=True, help="short name for the ledger, e.g. drive_a")
        sp.add_argument("--campaign", default="music1", help="label only; the budget covers ALL ledger rows")
        sp.add_argument("--cap", type=float, help=f"lower the hard cap (max ${HARD_CAP:.0f}); cannot raise it")
        sp.add_argument("--stop-at", type=float, help=f"lower the stop line (default ${STOP_AT:.0f}); cannot raise it")
        sp.add_argument("--timeout", type=int, default=fal_provider.MUSIC_TIMEOUT)
        sp.add_argument("--no-price-check", action="store_true")
        sp.add_argument("--dry-run", action="store_true", help="check budget and print the estimate only")
        sp.add_argument("--note")

    g = sub.add_parser("gen", help="queue one music call, download, ledger it (charge reserved first)")
    common(g)
    g.add_argument("--out", required=True, help="output stem (extension is chosen from the file fal returns)")
    g.add_argument("--model", choices=sorted(MODELS), default="eleven")
    g.add_argument("--preset", help="drive | drive-test | hold-pack")
    g.add_argument("--plan-file", help="composition plan JSON (eleven)")
    g.add_argument("--key", help='pin the key, e.g. "F minor"')
    g.add_argument("--prompt", help="stable only: the prompt")
    g.add_argument("--negative", help="stable only: appended as 'Avoid: ...'")
    g.add_argument("--seconds", type=int, help="stable only: clip length")
    g.add_argument("--accept-unverified-licence", action="store_true",
                   help="stable only: fal states no licence text for Stable Audio 2.5; the lead accepted that")
    g.add_argument("--output-format", default=DEFAULT_FORMATS, help="eleven: formats tried in order")
    f = sub.add_parser("fetch", help="re-download an already-billed request's audio (bills nothing)")
    common(f)
    f.add_argument("--request-id", required=True)
    f.add_argument("--out", required=True)
    f.add_argument("--model", choices=sorted(MODELS), default="eleven")
    v = sub.add_parser("vocal-check", help="speech-to-text on a take; exit 6 if sung/spoken words are found")
    common(v)
    v.add_argument("audio")
    return p.parse_args(argv)


def _on_sigterm(signum, frame):
    raise KeyboardInterrupt("SIGTERM")


def main(argv=None):
    args = parse_args(argv)
    signal.signal(signal.SIGTERM, _on_sigterm)
    env = gen_asset.merged_env()
    cmds = {"price": cmd_price, "usage": cmd_usage, "plan": cmd_plan, "gen": cmd_gen, "fetch": cmd_fetch,
            "vocal-check": cmd_vocal_check}
    try:
        return cmds[args.cmd](args, env)
    except Refuse as exc:  # corrupt ledger, non-finite estimate
        print(str(exc), file=sys.stderr)
        return exc.code
    except ProviderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
