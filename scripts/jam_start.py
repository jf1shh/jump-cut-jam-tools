#!/usr/bin/env python3
"""Jam start kit: one checked command for the 21:00 PT project setup.

    jam_start.py NAME DIR [--dry-run] [--force]
    jam_start.py --check-stage STAGEDIR

Setup (tooling and config only; no game content, Blueprints or C++, Rule 7(h)):
  a. writes the content-only UE project via new-mock-project.py (uproject, .mcp.json, Config/*.ini)
  b. merges Diversion ignore lines into DIR/.dvignore (work/, Content/Developers/, Content/Collections/,
     Packaged/); existing lines are kept, nothing is duplicated
  c. ensures limited culture staging in DIR/Config/DefaultGame.ini, section
     [/Script/UnrealEd.ProjectPackagingSettings] (explicit, matches the BaseGame.ini default; it does NOT
     shrink the staged ICU data by itself, see --check-stage below):
       --languages en    (default) InternationalizationPreset=English and +CulturesToStage=en
       --languages efigs InternationalizationPreset=EFIGS and +CulturesToStage= en, fr, it, de, es
     The jam submission must stay English-only (Official Rules, entry requirement (i): all submission
     content, including in-game text, audio and video, in English). efigs is for a post-jam update only.
     Merging only adds lines; switching modes on an existing file needs the old lines removed by hand.
  d. writes DIR/IDENTITY.md and DIR/CONTEXT.md (ICM layers 0 and 1) if missing; never overwrites them
  e. records the absolute DIR in ~/.config/megajam/jam-path (override the file with MEGAJAM_JAM_PATH_FILE);
     a different existing path is only replaced with --force
  f. prints the next command (HANDOFF_MAX_RESTARTS=300 proj start megajam) and a one-line checklist

new-mock-project.py runs in --force (merge) mode only for a new project. If NAME.uproject already exists
(a day-2 rerun) step a is skipped so the game's maps and settings are never reset. --force here lets
e. replace a different jam path. --dry-run writes nothing. Idempotent: a second run reports everything unchanged.

--check-stage STAGEDIR (after the first package): counts files under
STAGEDIR/Engine/Content/Internationalization and warns (exit 1) above ~3000 files. A correct English
icudt78l copy is ~781 files; mock 17's 29,035 came from scripts/package-and-push.ps1 copying the whole
engine Internationalization tree (all presets) instead of English only.
"""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DVIGNORE_LINES = ["work/", "Content/Developers/", "Content/Collections/", "Packaged/"]
PACKAGING_SECTION = "[/Script/UnrealEd.ProjectPackagingSettings]"
LANGUAGES = {"en": ("English", ["en"]), "efigs": ("EFIGS", ["en", "fr", "it", "de", "es"])}


def packaging_template(languages="en"):
    preset, cultures = LANGUAGES[languages]
    lines = [PACKAGING_SECTION, f"InternationalizationPreset={preset}"] + [f"+CulturesToStage={c}" for c in cultures]
    return "\n".join(lines) + "\n"


JAM_WINDOW = "2026-11-11 21:00 PT to 2026-11-15 17:59 PT"
NEXT_CMD = "HANDOFF_MAX_RESTARTS=300 proj start megajam"
ICU_WARN_FILES = 3000  # English icudt78l is ~781 files; the whole engine tree (all presets) is ~29k (mock 17)
I18N_REL = Path("Engine/Content/Internationalization")


def _load_nmp():
    spec = importlib.util.spec_from_file_location("new_mock_project", ROOT / "scripts" / "new-mock-project.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def merge_dvignore(existing):
    """Return existing text plus any missing entries (existing lines kept verbatim)."""
    lines = existing.splitlines()
    have = {ln.strip().lstrip("/") for ln in lines}
    missing = [e for e in DVIGNORE_LINES if e not in have]
    if not missing:
        return existing
    if lines and lines[-1].strip():
        lines.append("")
    return "\n".join(lines + missing) + "\n"


def english_staging(existing, nmp, languages="en"):
    return nmp.merge_ini(existing, packaging_template(languages))


TEMPLATES = ROOT / "_config" / "reference" / "templates"


def _template(fname, name, game_dir):
    """Layer 0/1 text from the master template (AGENTS.md), or None if missing."""
    t = TEMPLATES / fname
    if not t.is_file():
        return None
    body = "\n".join(ln for ln in t.read_text().splitlines() if not ln.startswith("> Template for")) + "\n"
    return body.replace("<GAME NAME>", name).replace("<Name>", name).replace("~/Projects/megajam-game", str(game_dir))


def identity_text(name, game_dir):
    return _template("game-project-identity.md", name, game_dir) or f"""# IDENTITY: {name}

This folder is the MegaJam entry's Unreal Engine project (UE 5.9 Preview, 5.8.4 fallback): `{name}.uproject`,
`Config/`, `Content/`. It is the Diversion-versioned game folder.

- Owner: Jared Fisher (solo, with AI agents). A human submits the entry.
- Jam: 2026 Epic AI MegaJam, {JAM_WINDOW}.
- Path: `{game_dir}`
- Tools, canon, rules and the plan live in `~/Projects/megajam` (start with its `AGENTS.md`).
"""


def context_text(name="", game_dir=""):
    return _template("game-project-context.md", name, game_dir) or """# CONTEXT: routing

| Need | Go to |
|---|---|
| Engine, packaging, MCP settings | `Config/` (`DefaultGame.ini`, `DefaultEngine.ini`, `DefaultEditorPerProjectUserSettings.ini`) |
| Game assets and levels | `Content/` (names follow `~/Projects/megajam/CLAUDE.md`) |
| C++ module, if one is added | `Source/` |
| Packaged builds | `Packaged/` (ignored by Diversion; never commit) |
| Scratch and generator output | `work/` (ignored by Diversion) |
| Dev log, evidence, screenshots, rules, plan, scripts | `~/Projects/megajam` (`AGENTS.md`, `RULES.md`, `PLAN.md`, `scripts/`) |

`.dvignore` keeps `work/`, `Content/Developers/`, `Content/Collections/`, `Packaged/` out of version control.
"""


def jam_path_file():
    env = os.environ.get("MEGAJAM_JAM_PATH_FILE")
    return Path(env).expanduser() if env else Path.home() / ".config" / "megajam" / "jam-path"


def jam_path_conflict(game_dir):
    """The different path already recorded, or None."""
    f = jam_path_file()
    if f.exists():
        cur = f.read_text().strip()
        if cur and cur != str(game_dir):
            return cur
    return None


def write_text(path, text, dry_run):
    """Create or update; returns created / updated / unchanged (prefixed 'would be ' in dry-run)."""
    old = path.read_text() if path.exists() else None
    if old == text:
        return "unchanged"
    state = "created" if old is None else "updated"
    if dry_run:
        return "would be " + state
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return state


def check_stage(stage_dir, out=print):
    """Count files in the staged Internationalization tree. Returns (count, ok)."""
    tree = Path(stage_dir).expanduser() / I18N_REL
    if not tree.is_dir():
        out(f"WARN: {tree} not found; is STAGEDIR the staged build root (contains Engine/ and the game folder)?")
        return 0, False
    n = sum(1 for p in tree.rglob("*") if p.is_file())
    if n > ICU_WARN_FILES:
        out(f"WARN: {n} files under {I18N_REL} looks like the whole engine ICU tree (an English icudt78l copy is ~781); "
            "check the ICU copy step in scripts/package-and-push.ps1 copies English/icudt78l only")
        return n, False
    out(f"OK: {n} files under {I18N_REL} (English-sized ICU set)")
    return n, True


def run(name, game_dir, dry_run=False, force=False, out=print, languages="en"):
    """Do steps a-f. Returns (exit code, {item: state})."""
    game_dir = Path(game_dir).expanduser().resolve()
    conflict = jam_path_conflict(game_dir)
    if conflict and not force:
        out(f"refusing: {jam_path_file()} already points at {conflict}; pass --force to replace it")
        return 1, {}
    nmp = _load_nmp()
    if (game_dir / f"{name}.uproject").exists():
        out(f"{name}.uproject exists: skipping new-mock-project.py so the game's maps and settings are kept")
        code = 0
    else:
        code = _new_project(nmp, name, game_dir, dry_run)
    if code != 0:
        out("new-mock-project.py skipped files (see above); fix or rerun with --force")
        return code, {}
    return _finish(name, game_dir, dry_run, languages, nmp)


def _new_project(nmp, name, game_dir, dry_run):
    argv = [name, str(game_dir)] + (["--dry-run"] if dry_run else []) + ["--force"]  # merge only its keys: keeps reruns idempotent
    return nmp.main(argv)


def _finish(name, game_dir, dry_run, languages, nmp):
    res = {}
    dv = game_dir / ".dvignore"
    res[".dvignore"] = write_text(dv, merge_dvignore(dv.read_text() if dv.exists() else ""), dry_run)
    ini = game_dir / "Config" / "DefaultGame.ini"
    res[f"Config/DefaultGame.ini ({languages} staging)"] = write_text(
        ini, english_staging(ini.read_text() if ini.exists() else "", nmp, languages), dry_run)
    for rel, text in (("IDENTITY.md", identity_text(name, game_dir)), ("CONTEXT.md", context_text(name, game_dir))):
        p = game_dir / rel
        res[rel] = "unchanged (kept)" if p.exists() else write_text(p, text, dry_run)
    res["jam-path"] = write_text(jam_path_file(), f"{game_dir}\n", dry_run)
    return 0, res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", nargs="?", help="project name; letters, digits, underscore")
    ap.add_argument("dir", nargs="?", help="game folder to write into")
    ap.add_argument("--dry-run", action="store_true", help="write nothing")
    ap.add_argument("--force", action="store_true", help="replace a different existing jam-path")
    ap.add_argument("--languages", choices=sorted(LANGUAGES), default="en",
                    help="staged cultures: en (default; Preset=English, +CulturesToStage=en) or efigs (Preset=EFIGS, "
                         "en fr it de es; opt-in for a post-jam update only)")
    ap.add_argument("--check-stage", metavar="STAGEDIR", help="count staged ICU files; exit 1 if it looks like full ICU")
    args = ap.parse_args(argv)
    if args.check_stage:
        return 0 if check_stage(args.check_stage)[1] else 1
    if not args.name or not args.dir:
        ap.error("NAME and DIR are required (or use --check-stage STAGEDIR)")
    code, res = run(args.name, args.dir, args.dry_run, args.force, languages=args.languages)
    if code != 0:
        return code
    for item, state in res.items():
        print(f"{state:>28}  {item}")
    print("wrote: " + ", ".join(res) + (" (dry run)" if args.dry_run else ""))
    print(f"next: {NEXT_CMD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
