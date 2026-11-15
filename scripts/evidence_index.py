#!/usr/bin/env python3
"""Lists the jam's evidence (screenshots, videos, playtest frames, scorecards, itch builds)
with a timestamp and a path, for the dev log (Glass Box) and stages/05_devlog/output/evidence.md.

    python3 scripts/evidence_index.py                      # markdown to stdout
    python3 scripts/evidence_index.py --out stages/05_devlog/output/evidence.md
    python3 scripts/evidence_index.py --since 2026-11-12T05:00:00Z --format json
    python3 scripts/evidence_index.py --dir stages --dir work --dir /mnt/legion-captures

What it reads (no network, ever):
- files under each --dir (default: stages, work), classified by extension and path;
- itch build ids from stages/05_devlog/output/builds.csv (one row per butler push; see the header) and from
  "build #NNNNNNN" mentions in the repo's markdown (mock-jam findings and readiness notes).

Timestamps: a tracked file's last commit time (one `git log` over the scanned dirs), else the file's
mtime; --no-git uses mtime only. All times are UTC, ISO 8601. Output is sorted by (time, category, path)
and carries no "generated at" stamp, so the same tree gives the same bytes.
"""
import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DIRS = ["stages", "work"]
DEFAULT_BUILDS_CSV = "stages/05_devlog/output/builds.csv"
DEFAULT_OUT = "stages/05_devlog/output/evidence.md"
BUILDS_HEADER = ["timestamp_iso", "tag", "commit", "itch_target", "itch_build", "note"]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
PLAYTEST_HINTS = ("playtest", "frames", "frame_", "visual_playtest")
SKIP_PARTS = {"__pycache__", ".git", "engine-reference", "node_modules"}
CATEGORY_ORDER = ["build", "scorecard", "video", "playtest-frame", "screenshot"]
CATEGORY_TITLES = {
    "build": "Builds (itch)",
    "scorecard": "Scorecards",
    "video": "Videos",
    "playtest-frame": "Playtest frames",
    "screenshot": "Screenshots",
}
BUILD_MENTION_RE = re.compile(r"build\s+\**#(\d{6,9})\**", re.IGNORECASE)
ITCH_TARGET_RE = re.compile(r"`?([\w-]+/[\w-]+:[\w-]+)`?")


@dataclass(frozen=True)
class Item:
    category: str
    timestamp: str  # ISO 8601 UTC, "YYYY-MM-DDTHH:MM:SSZ"
    path: str       # repo-relative where possible; "file:line" for build mentions
    detail: str = ""


def iso_utc(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(text):
    """Accepts YYYY-MM-DD, YYYY-MM-DDTHH:MM[:SS], with Z or an offset. Naive means UTC."""
    text = text.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def classify(relpath):
    """Returns the evidence category for a path, or None if it is not evidence."""
    p = Path(relpath)
    if any(part in SKIP_PARTS for part in p.parts):
        return None
    name = p.name.lower()
    ext = p.suffix.lower()
    if "scorecard" in name and ext in {".json", ".md"}:
        return "scorecard"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in IMAGE_EXTS:
        # the stage folder name (stages/03_playtest/...) must not make every image a playtest frame
        parts = p.parts[2:] if len(p.parts) > 2 and p.parts[0] == "stages" else p.parts
        lowered = "/".join(parts).lower()
        if any(hint in lowered for hint in PLAYTEST_HINTS):
            return "playtest-frame"
        return "screenshot"
    return None


def git_timestamps(root, dirs):
    """Maps repo-relative path -> ISO time of the newest commit touching it, in one git call.
    Returns {} if root is not a git checkout or git fails."""
    rel_dirs = [d for d in dirs if not Path(d).is_absolute()]
    if not rel_dirs:
        return {}
    result = subprocess.run(
        ["git", "-C", str(root), "log", "--format=%x1e%cI", "--name-only", "--", *rel_dirs],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return {}
    stamps = {}
    for block in result.stdout.split("\x1e"):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        when = iso_utc(parse_time(lines[0]))
        for path in lines[1:]:
            stamps.setdefault(path.strip(), when)  # git log is newest first
    return stamps


def mtime_iso(path):
    return iso_utc(datetime.fromtimestamp(Path(path).stat().st_mtime, tz=timezone.utc))


def display_path(path, root):
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except ValueError:
        return str(path)


def scan_files(root, dirs, stamps, exclude=()):
    items = []
    excluded = {str(Path(e)) for e in exclude}
    for raw in dirs:
        base = Path(raw) if Path(raw).is_absolute() else Path(root) / raw
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = display_path(path, root)
            if rel in excluded:
                continue
            category = classify(rel)
            if not category:
                continue
            items.append(Item(category, stamps.get(rel) or mtime_iso(path), rel))
    return items


def load_builds_csv(path):
    """Rows of stages/05_devlog/output/builds.csv -> build items. Missing file -> []."""
    path = Path(path)
    if not path.is_file():
        return []
    items = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            stamp = (row.get("timestamp_iso") or "").strip()
            if not stamp:
                continue
            parts = []
            if row.get("itch_build"):
                parts.append(f"itch build #{row['itch_build'].strip().lstrip('#')}")
            for key in ("itch_target", "tag", "commit", "note"):
                if row.get(key, "").strip():
                    parts.append(f"{key}: {row[key].strip()}")
            items.append(Item("build", iso_utc(parse_time(stamp)), str(path), "; ".join(parts)))
    return items


def scan_build_mentions(root, dirs, stamps, exclude=()):
    """'build #2334237' in markdown under dirs -> one build item per build id, from its earliest-dated doc
    (ties: first path). The dev log folder itself is skipped: its entries and logs quote builds, they are
    not where a build was recorded. The time is the doc's, not the push's; builds.csv carries push times."""
    excluded = {str(Path(e)) for e in exclude}
    best = {}
    for raw in dirs:
        base = Path(raw) if Path(raw).is_absolute() else Path(root) / raw
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            rel = display_path(path, root)
            if rel in excluded or any(part in SKIP_PARTS for part in Path(rel).parts):
                continue
            if rel.startswith("stages/05_devlog/output/"):
                continue
            try:
                lines = path.read_text(errors="replace").splitlines()
            except OSError:
                continue
            stamp = None
            for number, line in enumerate(lines, 1):
                for match in BUILD_MENTION_RE.finditer(line):
                    stamp = stamp or stamps.get(rel) or mtime_iso(path)
                    target = ITCH_TARGET_RE.search(line)
                    detail = f"itch build #{match.group(1)}"
                    if target:
                        detail += f"; itch_target: {target.group(1)}"
                    detail += " (mentioned in doc)"
                    item = Item("build", stamp, f"{rel}:{number}", detail)
                    old = best.get(match.group(1))
                    if old is None or (item.timestamp, item.path) < (old.timestamp, old.path):
                        best[match.group(1)] = item
    return list(best.values())


def sort_items(items):
    order = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    return sorted(set(items), key=lambda it: (it.timestamp, order.get(it.category, 99), it.path, it.detail))


def collect(root=".", dirs=None, builds_csv=DEFAULT_BUILDS_CSV, use_git=True, exclude=(DEFAULT_OUT,)):
    dirs = dirs or DEFAULT_DIRS
    stamps = git_timestamps(root, dirs) if use_git else {}
    items = scan_files(root, dirs, stamps, exclude)
    items += scan_build_mentions(root, dirs, stamps, exclude)
    csv_path = Path(builds_csv) if Path(builds_csv).is_absolute() else Path(root) / builds_csv
    items += [Item(i.category, i.timestamp, display_path(i.path, root), i.detail) for i in load_builds_csv(csv_path)]
    return sort_items(items)


def filter_since(items, since):
    """Keeps items at or after `since` (datetime or ISO string)."""
    if since is None:
        return list(items)
    cutoff = iso_utc(parse_time(since) if isinstance(since, str) else since)
    return [it for it in items if it.timestamp >= cutoff]


def render_markdown(items):
    lines = [
        "# Evidence index",
        "",
        "Generated by `python3 scripts/evidence_index.py --out stages/05_devlog/output/evidence.md`; do not edit by hand,",
        "re-run it. Times are UTC: a tracked file's last commit time, else its file time. Builds come from",
        "`stages/05_devlog/output/builds.csv` (one row per butler push) and from `build #N` mentions in the docs.",
        "",
    ]
    counts = {c: sum(1 for it in items if it.category == c) for c in CATEGORY_ORDER}
    lines.append("Totals: " + ", ".join(f"{CATEGORY_TITLES[c].lower()} {counts[c]}" for c in CATEGORY_ORDER) + ".")
    for category in CATEGORY_ORDER:
        rows = [it for it in items if it.category == category]
        lines += ["", f"## {CATEGORY_TITLES[category]}", ""]
        if not rows:
            lines.append("None yet.")
            continue
        lines += ["| Time (UTC) | Path | Detail |", "|---|---|---|"]
        for it in rows:
            detail = it.detail.replace("|", "\\|")
            lines.append(f"| {it.timestamp} | `{it.path}` | {detail} |")
    lines.append("")
    return "\n".join(lines)


def render_bullets(items, limit=40):
    """Short form for a nightly dev log draft."""
    out = [f"- {it.category} · {it.timestamp} · `{it.path}`" + (f" · {it.detail}" if it.detail else "") for it in items[:limit]]
    if len(items) > limit:
        out.append(f"- ...and {len(items) - limit} more (full list: `stages/05_devlog/output/evidence.md`)")
    return out


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="List screenshots, videos, playtest frames, scorecards and itch builds.")
    parser.add_argument("--root", default=".", help="repo root (default: current directory)")
    parser.add_argument("--dir", dest="dirs", action="append", help="directory to scan, repeatable (default: stages, work)")
    parser.add_argument("--builds", default=DEFAULT_BUILDS_CSV, help=f"builds CSV (default: {DEFAULT_BUILDS_CSV})")
    parser.add_argument("--since", help="only items at or after this time (ISO 8601; naive means UTC)")
    parser.add_argument("--no-git", action="store_true", help="use file mtimes only, never git")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    parser.add_argument("--out", help="write here instead of stdout")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    items = collect(args.root, args.dirs, args.builds, use_git=not args.no_git)
    items = filter_since(items, args.since)
    if args.format == "json":
        text = json.dumps([asdict(it) for it in items], indent=2) + "\n"
    else:
        text = render_markdown(items)
    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {args.out} ({len(items)} items)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
