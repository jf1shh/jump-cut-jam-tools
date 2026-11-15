#!/usr/bin/env python3
"""Sourced-asset ledger (Rules 1(d), 15(c)): log every non-original asset, print the credits block.

  sourced_assets.py add --name "Kenney Nature Kit" --url https://kenney.nl/assets/nature-kit \\
      --licence CC0 --author Kenney --files "Content/Sourced/Nature/*"
  sourced_assets.py list
  sourced_assets.py credits

Ledger: stages/02_build/output/sourced-assets.csv (override with --csv). AI-generated content is NOT sourced
(Rule 15(c)) and does not belong here. Do not log anything unlicensed: no licence, no import.
"""
import argparse
import csv
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

WINDOW_OPENS_DATE = "2026-11-12"  # 00:00 ET (Nov 11, 9:00 PM PT), Rule 4
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "stages/02_build/output/sourced-assets.csv"
FIELDS = ["name", "source_url", "licence", "author", "files_used", "date"]
# Licences where the author asks for no credit; we still list them (Rule 1(d) wants every sourced asset).
NO_CREDIT = {"fab standard", "fab standard license", "epic content license", "ue eula"}


CC0_LINE = re.compile(
    r"(?:(?:creative commons[ -])?(?:cc[ -]?)?(?:0|zero)|public domain)"
    r"(?:[ -](?:v?1\.0|universal|public domain dedication|licen[cs]e))*"
)


def today_et():
    """Today's date in the contest's clock (ET), whatever this machine's timezone is."""
    return datetime.fromtimestamp(time.time(), ZoneInfo("America/New_York")).date().isoformat()


def read_rows(path):
    """All ledger rows. Tolerates a BOM (spreadsheet 'CSV UTF-8') and padded header names."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            reader.fieldnames = [h.strip() for h in reader.fieldnames]
        # Keep hand-added columns too, so a rewrite never deletes them.
        return [{**{k: (r.get(k) or "") for k in FIELDS},
                 **{k: (v or "") for k, v in r.items() if k and k not in FIELDS}} for r in reader]


def norm_url(url):
    """Duplicate-check key: https, lowercase host, no fragment, no trailing slash."""
    u = urlsplit(url.strip())
    scheme = "https" if u.scheme in ("http", "https") else u.scheme
    return urlunsplit((scheme, u.netloc.lower(), u.path.rstrip("/"), u.query, ""))


def window_warning(when):
    """Warning text if `when` (YYYY-MM-DD) is before the contest window (Rule 7(h)), else None."""
    if when < WINDOW_OPENS_DATE:
        return (f"WARNING: {when} is before the contest window opens ({WINDOW_OPENS_DATE} 00:00 ET = "
                "Nov 11 9:00 PM PT). This ledger is evidence for Rule 7(h); do not import before the window.")
    return None


def add_row(path, name, url, licence, author, files, when=None):
    """Add one entry. Returns the row. Raises ValueError on a missing field, bad date or duplicate."""
    when = (when or today_et()).strip()
    try:
        if date.fromisoformat(when).isoformat() != when:
            raise ValueError
    except ValueError:
        raise ValueError(f"date must be YYYY-MM-DD, got {when!r}") from None
    row = {"name": name.strip(), "source_url": url.strip(), "licence": licence.strip(),
           "author": author.strip(), "files_used": files.strip(), "date": when}
    for key in ("name", "source_url", "licence", "author"):
        if not row[key]:
            raise ValueError(f"{key} is required (Rule 15(c): sourced assets must be licensed and listed)")
    if not row["source_url"].startswith(("http://", "https://")):
        raise ValueError("source_url must be an http(s) link")
    rows = read_rows(path)
    for r in rows:
        if r["name"].lower() == row["name"].lower() and norm_url(r["source_url"]) == norm_url(row["source_url"]):
            raise ValueError(f"already logged: {row['name']}")
    rows.append(row)
    # Rewrite the whole file: immune to a missing final newline or a BOM in a hand-edited ledger.
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        extra = [k for r in rows for k in r if k not in FIELDS]
        w = csv.DictWriter(f, fieldnames=FIELDS + list(dict.fromkeys(extra)), restval="")
        w.writeheader()
        w.writerows(rows)
    return row


def needs_credit(licence):
    lic = licence.strip().lower()
    # Whole-line match only: a mixed bundle ("CC0 textures, CC BY 4.0 models") still needs credit.
    if CC0_LINE.fullmatch(lic):
        return False
    return lic not in NO_CREDIT


def credits_block(rows):
    """Plain text for the itch.io page / submission form."""
    if not rows:
        return "Sourced assets: none. All art and audio were created during the contest period.\n"
    lines = ["Sourced (non-original) assets, listed per Official Rules 1(d) and 15(c):", ""]
    must = [r for r in rows if needs_credit(r["licence"])]
    free = [r for r in rows if not needs_credit(r["licence"])]
    if must:
        lines.append("Credit required by licence:")
        lines += [f"- {r['name']} by {r['author']} ({r['licence']}) {r['source_url']}" for r in must]
        lines.append("")
    if free:
        lines.append("No credit required, listed for completeness:")
        lines += [f"- {r['name']} by {r['author']} ({r['licence']}) {r['source_url']}" for r in free]
        lines.append("")
    lines.append("These assets are not original work and are not claimed for Visuals or Audio scoring.")
    return "\n".join(lines) + "\n"


def list_text(rows):
    if not rows:
        return "(ledger is empty)\n"
    out = [f"{len(rows)} sourced asset(s):"]
    for r in rows:
        out.append(f"- {r['date']}  {r['name']} | {r['licence']} | {r['author']} | files: {r['files_used'] or '-'}")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default=str(DEFAULT_CSV))
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--name", required=True)
    a.add_argument("--url", required=True)
    a.add_argument("--licence", required=True)
    a.add_argument("--author", required=True)
    a.add_argument("--files", default="", help="project paths or asset names that use it")
    a.add_argument("--date", help="YYYY-MM-DD (default today)")
    sub.add_parser("list")
    sub.add_parser("credits")
    args = ap.parse_args(argv)
    if args.cmd == "add":
        try:
            row = add_row(args.csv, args.name, args.url, args.licence, args.author, args.files, args.date)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        warn = window_warning(row["date"])
        if warn:
            print(warn, file=sys.stderr)
        print(f"logged: {row['name']} ({row['licence']})")
    elif args.cmd == "list":
        sys.stdout.write(list_text(read_rows(args.csv)))
    else:
        sys.stdout.write(credits_block(read_rows(args.csv)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
