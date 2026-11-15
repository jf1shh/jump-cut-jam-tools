#!/usr/bin/env python3
"""Drafts a dated dev-log entry from this repo's git log, screenshots/video,
and free-text notes, following _config/reference/templates/dev-log-entry.md.

Jam-week usage (one run, ~15 minutes to edit the draft, per PLAN.md's
"Dev log tooling" line):

    python3 scripts/gen_devlog.py --notes-file /tmp/tonights-notes.txt
    python3 scripts/gen_devlog.py --since 2026-11-12 --until 2026-11-13 --dry-run
    python3 scripts/gen_devlog.py --since HEAD~5

With no --since, it looks at the most recent stages/05_devlog/output/*.md entry's
Build/version line and resumes from that commit. On the first-ever entry
there is nothing to resume from, so --since is required.

It drafts "What shipped today" from commit subjects, lists screenshot/video
files whose mtime falls in the commit range, adds "Evidence from this window"
(scripts/evidence_index.py: screenshots, videos, playtest frames, scorecards,
itch builds since the window start) and "Decisions since the last entry"
(every stages/05_devlog/output/decisions.md row whose D-NNN id no other dated entry
mentions yet). The AI disclosure gets the providers the asset log recorded in
the window as a hint.

Sections that need the owner's own voice ("What's next", "One thing that
surprised us", confirming the AI disclosure) stay as placeholders marked
OWNER-FILL unless --notes/--notes-file fills the first two. Before posting:
    grep -n OWNER-FILL stages/05_devlog/output/YYYY-MM-DD.md   # must print nothing
"""
import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEVLOG_DIR = Path("stages/05_devlog/output")
DECISIONS_FILE = "decisions.md"  # inside DEVLOG_DIR
ASSET_LOG = Path("stages/02_build/output/asset-pipeline-log.csv")
OWNER_FILL = "OWNER-FILL"
DATED_ENTRY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
DECISION_ROW_RE = re.compile(r"^\|\s*(D-\d{3,})\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$")
DECISION_ID_RE = re.compile(r"\bD-\d{3,}\b")
DEFAULT_MEDIA_DIRS = ["work/generated"]
MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".mp4", ".mov"}
# A Build/version section starts at a LINE that begins with the label: the "## Build/version" heading (generated
# entries), optionally with a colon, or the template's "- **Build/version:**" bullet. Prose or a commit
# subject that merely mentions Build/version mid-line never starts a section. The section runs to the next
# heading; its first backticked hash is the resume point (a non-hash tag such as a zip name means none).
BUILD_SECTION_RE = re.compile(r"^[ \t]*(?:#+[ \t]*|[-*][ \t]+)?\**Build/version\b", re.IGNORECASE | re.MULTILINE)
NEXT_HEADING_RE = re.compile(r"^#", re.MULTILINE)
BUILD_HASH_RE = re.compile(r"`([0-9a-f]{7,40})`", re.IGNORECASE)
CONVENTIONAL_PREFIX_RE = re.compile(r"^([a-zA-Z]+):\s*(.+)$")
FIELD_SEP = "\x1f"


def parse_args():
    parser = argparse.ArgumentParser(description="Draft a dated dev-log entry from git log, screenshots, and notes.")
    parser.add_argument("--since", help="git ref or date to start from (default: last devlog entry's build commit)")
    parser.add_argument("--until", default="HEAD", help="git ref or date to end at (default: HEAD)")
    parser.add_argument("--notes", help="free text for 'what's next' / 'one thing that surprised us'; blank line splits the two")
    parser.add_argument("--notes-file", help="file with the same free text as --notes")
    parser.add_argument(
        "--media-dir", dest="media_dirs", action="append",
        help="directory to scan for new screenshots/video; repeatable (default: work/generated)",
    )
    parser.add_argument("--build-tag", help="override the build/version string (default: git rev-parse --short HEAD)")
    parser.add_argument("--date", help="override the entry date, YYYY-MM-DD (default: today)")
    parser.add_argument("--force", action="store_true", help="overwrite an existing entry for the same date (default: refuse)")
    parser.add_argument("--dry-run", action="store_true", help="print the draft instead of writing stages/05_devlog/output/YYYY-MM-DD.md")
    parser.add_argument(
        "--evidence-dir", dest="evidence_dirs", action="append",
        help="directory for scripts/evidence_index.py to scan; repeatable (default: stages, work)",
    )
    parser.add_argument("--no-evidence", action="store_true", help="skip the evidence section")
    return parser.parse_args()


def run_git(args):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"git {' '.join(args)} failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def is_git_ref(ref):
    result = subprocess.run(["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], capture_output=True, text=True)
    return result.returncode == 0


def dated_entries(skip_date=None):
    """stages/05_devlog/output/YYYY-MM-DD.md files, oldest first. decisions.md, evidence.md and templates are not entries."""
    if not DEVLOG_DIR.is_dir():
        return []
    return sorted(
        p for p in DEVLOG_DIR.glob("*.md")
        if DATED_ENTRY_RE.match(p.name) and p.stem != skip_date
    )


def find_last_build_ref():
    entries = dated_entries()
    if not entries:
        return None
    text = entries[-1].read_text()
    starts = list(BUILD_SECTION_RE.finditer(text))
    if not starts:
        return None
    last = starts[-1]
    rest = text[last.end():]
    if last.group(0).lstrip().startswith("#"):
        # heading form: the section runs to the next heading
        heading = NEXT_HEADING_RE.search(rest)
        if heading:
            rest = rest[:heading.start()]
    else:
        # bullet or plain-line form: the section is that one line, so later bullets never count
        rest = rest.split("\n", 1)[0]
    match = BUILD_HASH_RE.search(rest)
    return match.group(1) if match else None


def resolve_range(since, until):
    """Returns (git_log_range_args, mode) where mode is 'ref' or 'date'."""
    if since and is_git_ref(since):
        return [f"{since}..{until}"], "ref"
    args = []
    if since:
        args.append(f"--since={since}")
    if until and until != "HEAD":
        args.append(f"--until={until}")
    return args, "date"


def fetch_commits(range_args):
    log_format = f"%H{FIELD_SEP}%P{FIELD_SEP}%ci{FIELD_SEP}%s"
    raw = run_git(["log", f"--format={log_format}", *range_args])
    commits = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        commit_hash, parents, committed_at, subject = line.split(FIELD_SEP, 3)
        commits.append({
            "hash": commit_hash,
            "is_merge": len(parents.split()) > 1,
            "committed_at": datetime.strptime(committed_at, "%Y-%m-%d %H:%M:%S %z"),
            "subject": subject,
        })
    return commits


def group_commits(commits):
    direct = [c for c in commits if not c["is_merge"]]
    merges = [c for c in commits if c["is_merge"]]

    prefixed = {}
    unprefixed = []
    for c in direct:
        match = CONVENTIONAL_PREFIX_RE.match(c["subject"])
        if match:
            prefixed.setdefault(match.group(1).lower(), []).append((c, match.group(2)))
        else:
            unprefixed.append(c)

    bullets = []
    if len(prefixed) >= 2 and len(unprefixed) <= len(direct) // 2:
        for prefix in sorted(prefixed):
            for c, rest in prefixed[prefix]:
                bullets.append(f"- **{prefix}:** {rest} (`{c['hash'][:7]}`)")
        for c in unprefixed:
            bullets.append(f"- {c['subject']} (`{c['hash'][:7]}`)")
    else:
        for c in direct:
            bullets.append(f"- {c['subject']} (`{c['hash'][:7]}`)")

    if merges:
        bullets.append(f"- Merged {len(merges)} pull request(s): " + ", ".join(c["subject"] for c in merges))

    return bullets


def find_media_files(media_dirs, window_start, window_end):
    found = []
    for raw_dir in media_dirs:
        directory = Path(raw_dir)
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in MEDIA_EXTS:
                continue
            mtime = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
            if window_start and mtime < window_start:
                continue
            if window_end and mtime > window_end:
                continue
            found.append(str(path))
    return sorted(found)


def load_decisions(path=None):
    """Rows of the decisions table: [{'id','date','who','what','why','link'}], in file order."""
    path = Path(path) if path else DEVLOG_DIR / DECISIONS_FILE
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text().splitlines():
        match = DECISION_ROW_RE.match(line.strip())
        if match:
            rows.append(dict(zip(("id", "date", "who", "what", "why", "link"), (g.strip() for g in match.groups()))))
    return rows


def decisions_not_yet_logged(decisions, entry_date):
    """Decisions dated on or before entry_date whose ID no other dated entry mentions."""
    mentioned = set()
    for entry in dated_entries(skip_date=entry_date):
        mentioned.update(DECISION_ID_RE.findall(entry.read_text()))
    return [d for d in decisions if d["id"] not in mentioned and d["date"][:10] <= entry_date]


def asset_log_providers(window_start, log_path=None):
    """Distinct 'stage:provider' values (e.g. image:gpt, 3d:meshy) in the asset log at or after window_start."""
    log_path = Path(log_path) if log_path else ASSET_LOG
    if window_start is None or not log_path.is_file():
        return []
    import csv
    found = set()
    with log_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            stage = (row.get("stage") or "").strip()
            stamp = (row.get("timestamp_iso") or "").strip()
            if ":" not in stage or not stamp:
                continue
            try:
                when = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            except ValueError:
                continue
            if when.tzinfo is None:
                when = when.astimezone()
            if when >= window_start and row.get("exit_code", "").strip() in ("0", ""):
                found.add(stage)
    return sorted(found)


def load_notes(notes, notes_file):
    if notes_file:
        notes = Path(notes_file).read_text()
    if not notes:
        return None, None
    parts = notes.strip().split("\n\n", 1)
    whats_next = parts[0].strip()
    surprised = parts[1].strip() if len(parts) > 1 else None
    return whats_next or None, surprised


def render_decisions(decisions):
    if not decisions:
        return ["- None logged in `stages/05_devlog/output/decisions.md` since the last entry."]
    out = []
    for d in decisions:
        line = f"- **{d['id']}** ({d['date']}, {d['who']}): {d['what']}."
        if d["why"]:
            line += f" Why: {d['why']}."
        if d["link"]:
            line += f" ({d['link']})"
        out.append(line)
    return out


def render_entry(entry_date, build_tag, shipped_bullets, whats_next, surprised, media_files,
                 decisions=None, evidence=None, ai_hints=None):
    whats_next = whats_next or f"<!-- {OWNER_FILL} (owner's voice): tomorrow's top slice or two -->"
    surprised = surprised or f"<!-- {OWNER_FILL} (owner's voice): a genuine 'huh, didn't expect that' -->"
    if not shipped_bullets:
        shipped_bullets = ["<!-- fill in: no commits found in this range -->"]

    lines = [
        f"# Dev log entry — {entry_date}",
        "",
        "## What shipped today",
        *shipped_bullets,
    ]
    if media_files:
        lines.append("")
        lines.append("Screenshots/video from this window:")
        for path in media_files:
            lines.append(f"- {path}")
    if evidence is not None:
        import evidence_index
        lines += ["", "Evidence from this window (`scripts/evidence_index.py`):"]
        lines += evidence_index.render_bullets(evidence) if evidence else ["- none found"]
    if decisions is not None:
        lines += ["", "## Decisions since the last entry", *render_decisions(decisions)]
    hint = ", ".join(f"`{h}`" for h in ai_hints) if ai_hints else "none recorded"
    lines += [
        "",
        "## What's next",
        whats_next,
        "",
        "## One thing that surprised us",
        surprised,
        "",
        "## AI disclosure",
        "Drafted by scripts/gen_devlog.py. Asset-log providers in this window: " + hint + ".",
        f"<!-- {OWNER_FILL}: confirm which AI tools and models did what today; the full tool list is "
        "stages/05_devlog/references/ai-disclosure-draft.md -->",
        "",
        "## Build/version",
        f"`{build_tag}` ({entry_date})",
        "",
    ]
    return "\n".join(lines)


def main():
    args = parse_args()

    since = args.since or find_last_build_ref()
    if not since:
        print(
            "No --since given and no prior stages/05_devlog/output entry to resume from. "
            "Pass --since <git-ref-or-date> explicitly (e.g. for the first entry).",
            file=sys.stderr,
        )
        sys.exit(2)

    range_args, mode = resolve_range(since, args.until)
    commits = fetch_commits(range_args)
    shipped_bullets = group_commits(commits)

    if commits:
        window_start = min(c["committed_at"] for c in commits)
        window_end = max(c["committed_at"] for c in commits)
    else:
        window_start, window_end = None, None

    media_dirs = args.media_dirs or DEFAULT_MEDIA_DIRS
    media_files = find_media_files(media_dirs, window_start, window_end)

    whats_next, surprised = load_notes(args.notes, args.notes_file)

    entry_date = args.date or datetime.now().strftime("%Y-%m-%d")
    build_tag = args.build_tag or run_git(["rev-parse", "--short", "HEAD"]).strip()

    evidence = None
    if not args.no_evidence and window_start is not None:
        import evidence_index
        evidence = evidence_index.filter_since(evidence_index.collect(".", args.evidence_dirs), window_start)
    decisions = decisions_not_yet_logged(load_decisions(), entry_date)
    ai_hints = asset_log_providers(window_start)

    draft = render_entry(entry_date, build_tag, shipped_bullets, whats_next, surprised, media_files,
                         decisions=decisions, evidence=evidence, ai_hints=ai_hints)

    if args.dry_run:
        print(draft)
        return

    DEVLOG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DEVLOG_DIR / f"{entry_date}.md"
    if out_path.exists() and not args.force:
        print(
            f"{out_path} already exists; not overwriting. Edit it by hand, pass --date for another day, "
            "or --force to replace it.",
            file=sys.stderr,
        )
        sys.exit(2)
    out_path.write_text(draft)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
