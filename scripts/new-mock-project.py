#!/usr/bin/env python3
"""Write a ready content-only UE 5.9 (5.8.4 fallback) mock-jam project: NAME DIR.

DIR must be the folder the Claude session is rooted at (for mocks: ~/Projects/megajam-mock),
because Claude Code loads .mcp.json only from the session root.
Creates DIR/NAME.uproject, DIR/.mcp.json, DIR/Config/DefaultGame.ini (the GameFeatureData
cook rule), DIR/Config/DefaultEngine.ini (named first level) and
DIR/Config/DefaultEditorPerProjectUserSettings.ini (the MCP port pin; the editor reads it there).
After launching the editor, `--verify-port 8010 --verify-only` curls the MCP endpoint (405 = up). Templates live in
templates/mock-project/. Idempotent: identical files are left alone, differing files are
skipped unless --force (merges only this tool's keys) or --force-all (replaces). --dry-run writes nothing. Tooling only; no game content.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from string import Template
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates" / "mock-project"
MCP_URL = "http://127.0.0.1:8010/mcp"
# Same three plugins as the dress-rehearsal project (stages/00_prep/references/jam-day-runbook.md section 2).
# Editor-only so the Win64 package does not need a C++ toolchain (mock jam 3, finding 2).
JAM_PLUGINS = ["ModelingToolsEditorMode", "ModelContextProtocol", "AllToolsets"]
# A hyphen breaks the auto-generated Target.cs (mock jam 3, finding 1).
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def plugin_list(extra):
    names = list(dict.fromkeys(JAM_PLUGINS + list(extra)))
    entries = [{"Name": n, "Enabled": True, "TargetAllowList": ["Editor"]} for n in names]
    return json.dumps(entries, indent="\t").replace("\n", "\n\t")


def render(name, level, mcp_url, extra_plugins):
    values = {
        "plugins": plugin_list(extra_plugins),
        "mcp_url": json.dumps(mcp_url)[1:-1],  # JSON-escaped; check_mcp_url also refuses quotes
        "level_path": f"/Game/Maps/{level}",
        "mcp_port": check_mcp_url(mcp_url),
    }
    out = {}
    for tmpl, dest in (
        ("project.uproject.tmpl", f"{name}.uproject"),
        ("mcp.json.tmpl", ".mcp.json"),
        ("DefaultGame.ini.tmpl", "Config/DefaultGame.ini"),
        ("DefaultEngine.ini.tmpl", "Config/DefaultEngine.ini"),
    ):
        out[dest] = Template((TEMPLATES / tmpl).read_text()).safe_substitute(values)
    # The port pin is read from the per-project user settings ini, not DefaultEngine.ini (mock 11: wrong ini
    # cost 9 reruns). Drop it from the engine ini even if the template still carries it.
    for sec in (MCP_SECTION, MCP_SECTION_59):
        out["Config/DefaultEngine.ini"] = strip_section(out["Config/DefaultEngine.ini"], sec)
    out[PORT_INI] = Template(PORT_INI_TMPL).safe_substitute(values)
    json.loads(out[f"{name}.uproject"])  # fail loudly if a template breaks the JSON
    json.loads(out[".mcp.json"])
    return out


MCP_SECTION = "[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]"  # UE 5.8.4 name
MCP_SECTION_59 = "[/Script/ModelContextProtocol.ModelContextProtocolSettings]"  # UE 5.9 name (old one is redirected, with a warning)
PORT_INI = "Config/DefaultEditorPerProjectUserSettings.ini"
PORT_INI_TMPL = f"""; Pin the MCP port (stages/00_prep/references/jam-day-runbook.md section 2). Leave Auto Start Server off.
; Both names are written: 5.9 reads the first, the 5.8.4 fallback reads the second. AllToolsets is a plugin
; in the .uproject, not an ini setting.
{MCP_SECTION_59}
ServerPortNumber=$mcp_port

{MCP_SECTION}
ServerPortNumber=$mcp_port
"""


def strip_section(text, header):
    """Remove `header` and its lines (plus the comment lines right above it) from an ini text."""
    lines = text.splitlines()
    if header not in [ln.strip() for ln in lines]:
        return text
    at = [ln.strip() for ln in lines].index(header)
    end = at + 1
    while end < len(lines) and not lines[end].strip().startswith("["):
        end += 1
    start = at
    while start > 0 and lines[start - 1].strip().startswith(";"):
        start -= 1
    kept = lines[:start] + lines[end:]
    while kept and not kept[-1].strip():
        kept.pop()
    return "\n".join(kept) + "\n"


def verify_port(port, timeout=60.0, interval=2.0, out=print):
    """True once http://127.0.0.1:PORT/mcp answers with any HTTP status (405 = up). False on timeout."""
    import time
    import urllib.error
    import urllib.request
    url = f"http://127.0.0.1:{port}/mcp"
    end = time.monotonic() + timeout
    while True:
        try:
            urllib.request.urlopen(url, timeout=2)
            status = 200
        except urllib.error.HTTPError as exc:
            status = exc.code
        except (urllib.error.URLError, OSError):
            status = None
        if status is not None:
            out(f"MCP port {port} is up (HTTP {status})")
            return True
        if time.monotonic() >= end:
            out(f"MCP port {port} did not answer within {timeout:g}s; is the editor running with "
                f"-ModelContextProtocolPort={port}?")
            return False
        time.sleep(interval)


def array_id(line):
    """Identity of a '+' array line. Asset-type rules match on PrimaryAssetType, so the
    editor's own saved form of the rule counts as the same entry; others match exactly."""
    m = re.match(r'\+PrimaryAssetTypesToScan=\(.*?PrimaryAssetType="([^"]+)"', line)
    return ("PrimaryAssetTypesToScan", m.group(1)) if m else line


def check_mcp_url(url):
    """Return the port of an http URL with an explicit port 1-65535, else raise ValueError."""
    if any(c in '"\\' or ord(c) < 32 or c.isspace() for c in url):
        raise ValueError("must not contain quotes, backslashes, spaces or control characters")
    parts = urlparse(url)
    if parts.scheme != "http" or not parts.hostname:
        raise ValueError("must be an http:// URL with a host")
    try:
        port = parts.port
    except ValueError:
        port = None
    if port is None or not 1 <= port <= 65535:
        raise ValueError("needs an explicit port from 1 to 65535, e.g. http://127.0.0.1:8010/mcp")
    return port


def merge_ini(existing, template):
    """Apply only the template's keys; keep every other line, section and comment."""
    lines = existing.splitlines()
    section, wanted = None, {}
    for raw in template.splitlines():
        s = raw.strip()
        if not s or s.startswith(";"):
            continue
        if s.startswith("["):
            section = s
            wanted[section] = []
        elif section:
            wanted[section].append(s)
    for sec, entries in wanted.items():
        if sec not in [ln.strip() for ln in lines]:
            if lines and lines[-1].strip():
                lines.append("")
            lines += [sec, *entries]
            continue
        start = [ln.strip() for ln in lines].index(sec) + 1
        end = start
        while end < len(lines) and not lines[end].strip().startswith("["):
            end += 1
        while end > start and not lines[end - 1].strip():
            end -= 1  # insert before trailing blank lines
        for entry in entries:
            block = [ln.strip() for ln in lines[start:end]]
            if entry.startswith("+"):
                if not any(array_id(b) == array_id(entry) for b in block):
                    lines.insert(end, entry)
                    end += 1
                continue
            key = entry.split("=", 1)[0]
            hit = next((i for i, ln in enumerate(block) if ln.split("=", 1)[0] == key), None)
            if hit is None:
                lines.insert(end, entry)
                end += 1
            else:
                lines[start + hit] = entry
    return "\n".join(lines) + "\n"


def merge_file(rel, existing, template):
    if rel.endswith(".ini"):
        return merge_ini(existing, template)
    try:
        cur, new = json.loads(existing), json.loads(template)
    except json.JSONDecodeError as exc:
        raise ValueError(f"existing file is not valid JSON ({exc.msg})")
    if rel.endswith(".uproject"):
        plugins = cur.setdefault("Plugins", [])
        for p in new["Plugins"]:
            plugins[:] = [q for q in plugins if q.get("Name") != p["Name"]] + [p]
    else:
        cur.setdefault("mcpServers", {}).update(new["mcpServers"])
    return json.dumps(cur, indent="\t") + "\n"


def write_all(target, files, dry_run, force):
    results = {}
    for rel, text in files.items():
        path = target / rel
        if path.exists():
            if path.read_text() == text:
                results[rel] = "unchanged"
                continue
            if not force:
                results[rel] = "skipped (differs; --force merges, --force-all replaces)"
                continue
            if force == "all":
                state = "overwritten"
            else:
                try:
                    merged = merge_file(rel, path.read_text(), text)
                except ValueError as exc:
                    results[rel] = f"skipped (cannot merge: {exc})"
                    continue
                if merged == path.read_text():
                    results[rel] = "unchanged"
                    continue
                text, state = merged, "merged"
        else:
            state = "created"
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        results[rel] = ("would be " + state) if dry_run else state
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("name", help="project name; letters, digits, underscore, no hyphen")
    ap.add_argument("dir", help="project folder to write into")
    ap.add_argument("--level", default="L_MainLevel", help="first level name (default L_MainLevel)")
    ap.add_argument("--mcp-url", default=MCP_URL)
    ap.add_argument("--extra-plugin", action="append", default=[], help="add an Editor-only plugin")
    ap.add_argument("--force", action="store_true",
                    help="merge only this tool's keys into files that differ (keeps other settings)")
    ap.add_argument("--force-all", action="store_true", help="replace files that differ wholesale")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify-port", type=int, metavar="PORT",
                    help="with --verify-only (run after launching the editor): curl http://127.0.0.1:PORT/mcp until it "
                         "answers (405 = up); exit 1 if not. Without --verify-only it only prints that command.")
    ap.add_argument("--verify-timeout", type=float, default=60.0, help="seconds to wait for --verify-port (default 60)")
    ap.add_argument("--verify-only", action="store_true", help="with --verify-port: write nothing, only check the port")
    args = ap.parse_args(argv)
    if args.verify_only and not args.verify_port:
        ap.error("--verify-only needs --verify-port")
    if not NAME_RE.match(args.name):
        ap.error("name must start with a letter and use only letters, digits, underscore (no hyphen)")
    if not NAME_RE.match(args.level):
        ap.error("level must be a plain name like L_MainLevel")
    try:
        check_mcp_url(args.mcp_url)
    except ValueError as exc:
        ap.error(f"--mcp-url {exc}")
    if args.verify_only:
        return 0 if verify_port(args.verify_port, args.verify_timeout) else 1
    files = render(args.name, args.level, args.mcp_url, args.extra_plugin)
    results = write_all(Path(args.dir).expanduser(), files, args.dry_run,
                         "all" if args.force_all else args.force)
    for rel, state in results.items():
        print(f"{state:>28}  {rel}")
    if any(s.startswith("skipped") for s in results.values()):
        return 1
    if args.verify_port and not args.dry_run:
        # No editor can be running yet, so polling now would fail a good scaffold. Check after launching.
        print(f"launch the editor, then: new-mock-project.py {args.name} {args.dir} "
              f"--verify-port {args.verify_port} --verify-only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
