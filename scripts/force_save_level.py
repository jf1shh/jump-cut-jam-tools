#!/usr/bin/env python3
"""Force-save the dirty level (and optional assets) through the Unreal MCP python tool, then VERIFY ON DISK.

Why (mock jam 10, "Playable gate failure"): level edits made over MCP were never written to the .umap.
save_assets said "already saved" (it skips packages it thinks are clean), so the packaged build shipped the
old level. This helper never trusts the editor's answer. It checks the file.

  force_save_level.py [--level /Game/Maps/L_Main] [--umap PATH] [--expect-actor LABEL]... [--asset /Game/X]...
  force_save_level.py --list-tools

Steps:
  1. In the editor: read the level's package file, actor count and dirty state. Hash the file on disk (before).
  2. In the editor: mark the level package dirty, then save with only_if_is_dirty=False (a forced save),
     save the level, save all dirty packages, and force-save each --asset.
  3. On disk: the .umap must exist, start with the UE package magic, have a newer mtime AND a different hash
     (use --allow-unchanged only when you made no edits on purpose).
  4. In the editor: reload the level fresh (load an empty map, then the level) and require the same actor
     count as before the save, plus every --expect-actor label.

Exit: 0 verified; 1 verification failed or the editor reported an error (do NOT package); 2 usage error or
editor unreachable. Only the lead agent calls Unreal MCP (AGENTS.md). Never run this from a ticket: it needs
a live editor. Real-editor check: stages/02_build/references/force-save-level.md.

If step 3 fails twice, escalate by hand with AssetTools.duplicate_asset (see the doc); this script does not
duplicate the map on its own because that would leave a second .umap in the project.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_call import McpError, EXIT_TOOL, EXIT_CONN  # noqa: E402
from step_shot import code_args, code_key, make_client, pick_python_tool, render, result_text  # noqa: E402

UMAP_MAGIC = bytes.fromhex("c1832a9e")  # UE package tag 0x9E2A83C1, little-endian on disk
MARK = "FORCE_SAVE"

_COMMON = '''import json
import uuid
import unreal
PARAMS = @@PARAMS@@
P = json.loads(PARAMS)
_OUT = []  # UE 5.9's execute_python returns only the last expression's value (returnValue), not stdout
def _ok(msg):
    _OUT.append("FORCE_SAVE_OK " + msg)
    print("FORCE_SAVE_OK " + msg)
def _err(msg):
    _OUT.append("FORCE_SAVE_ERROR " + msg)
    print("FORCE_SAVE_ERROR " + msg)
def _dirty(obj, pkg):
    # 5.8 Package has mark_package_dirty; 5.9 Python does not (mock jam 16), but Object.modify(True) dirties the package.
    if hasattr(pkg, "mark_package_dirty"):
        pkg.mark_package_dirty()
    else:
        obj.modify(True)

def _info():
    ls = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = ed.get_editor_world()
    pkg = world.get_outer().get_path_name().split(".")[0]  # always the OPEN level, never P["level"]
    labels = sorted(a.get_actor_label() for a in actors.get_all_level_actors())
    return ls, ed, actors, world, pkg, labels
def _file(pkg, ext=".umap"):
    pn = getattr(unreal, "PackageName", None)  # UE 5.9 Python has no unreal.PackageName (mock 15)
    if pn is not None:
        path = pn.long_package_name_to_filename(pkg, ext)
    elif pkg.startswith("/Game/"):
        path = unreal.Paths.project_content_dir().rstrip("/") + "/" + pkg[len("/Game/"):] + ext
    else:
        raise RuntimeError("cannot map " + pkg + " to a file: no unreal.PackageName and not under /Game/")
    return unreal.Paths.convert_relative_path_to_full(path)
def _external(actors):
    """Actors that live in their own __ExternalActors__ package (One File Per Actor)."""
    out = []
    everyone = list(actors.get_all_level_actors())
    for a in everyone:
        try:
            if a.is_package_external():
                out.append(a)
        except AttributeError:
            # API not exposed in this build: do not guess "none are external". Treat every actor as possibly
            # external so their packages are saved and the host still hashes __ExternalActors__.
            _err("Actor.is_package_external is missing in this build (AttributeError); treating every actor as possibly external")
            return everyone, True
        except Exception as e:
            _err("is_package_external failed on %s: %s" % (a.get_actor_label(), e))
            return everyone, True
    return out, False
def _external_dir(pkg):
    parts = pkg.strip("/").split("/", 1)
    if parts[0] != "Game" or len(parts) < 2:
        return None
    return unreal.Paths.convert_relative_path_to_full(
        unreal.Paths.combine([unreal.Paths.project_content_dir(), "__ExternalActors__", parts[1]]))
'''

PROBE_SCRIPT = _COMMON + '''
def run():
    ls, ed, actors, world, pkg, labels = _info()
    files = {}
    for a in P.get("assets", []):
        for ext in (".uasset", ".umap"):
            f = _file(a, ext)
            if unreal.Paths.file_exists(f):
                files[a] = f
                break
        else:
            files[a] = _file(a, ".uasset")
    ext, unknown = _external(actors)
    ext_n = len(ext)
    _ok(json.dumps({"level": pkg, "open_level": pkg, "file": _file(pkg), "actors": len(labels), "labels": labels,
                    "asset_files": files, "external_actors": ext_n, "external_unknown": unknown,
                    "external_dir": _external_dir(pkg) if ext_n else None}))
try:
    run()
except Exception as e:
    _err("%s: %s" % (type(e).__name__, e))
'''

SAVE_SCRIPT = _COMMON + '''
def run():
    ls, ed, actors, world, pkg, labels = _info()
    _dirty(world, world.get_outer())  # the editor may think the level is clean; make it save anyway
    done = []
    # One File Per Actor: placed actors live in __ExternalActors__ packages the editor may call clean.
    ext_pkgs, seen = [], set()
    for a in _external(actors)[0]:
        p = a.get_package()
        if p.get_path_name() in seen:
            continue
        seen.add(p.get_path_name())
        _dirty(a, p)
        ext_pkgs.append(p)
    if ext_pkgs and not unreal.EditorLoadingAndSavingUtils.save_packages(ext_pkgs, False):
        done.append("save_packages returned False for external actors")
    # only_if_is_dirty=False is the forced save. This is the call save_assets skipped as "already saved".
    if not unreal.EditorAssetLibrary.save_loaded_asset(world, False):
        done.append("save_loaded_asset returned False")
    if not ls.save_current_level():
        done.append("save_current_level returned False")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    for a in P.get("assets", []):
        if not unreal.EditorAssetLibrary.save_asset(a, False):
            done.append("asset not saved: " + a)
    _ok(json.dumps({"level": pkg, "actors": len(labels), "external_saved": len(ext_pkgs), "notes": done}))
try:
    run()
except Exception as e:
    _err("%s: %s" % (type(e).__name__, e))
'''

RELOAD_SCRIPT = _COMMON + '''
def run():
    ls, ed, actors, world, pkg, labels = _info()
    # Leave the level so the reload below reads the file, not memory. If either step fails, there is no proof.
    # A fresh scratch name every run: new_level refuses (returns False) when a package already exists there.
    # (uuid is imported at the top: 5.9 execute_python rejects imports inside a function.)
    if not ls.new_level("/Temp/ForceSaveScratch_" + uuid.uuid4().hex[:12]):
        _err("new_level failed; still on the open level, so a reload would prove nothing")
        return
    if not ls.load_level(pkg):
        _err("load_level(%s) failed" % pkg)
        return
    ls2, ed2, actors2, world2, pkg2, labels2 = _info()
    if pkg2 != pkg:
        _err("after the reload the open level is %s, expected %s" % (pkg2, pkg))
        return
    _ok(json.dumps({"level": pkg2, "actors": len(labels2), "labels": labels2}))
try:
    run()
except Exception as e:
    _err("%s: %s" % (type(e).__name__, e))
'''


class VerifyError(McpError):
    """The editor answered, but the proof on disk or after reload failed."""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def disk_state(path):
    """(mtime_ns, sha256, size) or None when the file is missing."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_mtime_ns, sha256(path), st.st_size)


def run_script(cli, tool, template, params, what):
    """Run an in-editor script; return the JSON it printed after FORCE_SAVE_OK."""
    res = cli.call(tool["name"], code_args(tool, render(template, params), cli))
    text = unwrap(result_text(res))
    found, errors = {}, []
    # A marker followed by a quote is our own source echoed back (print("FORCE_SAVE_OK " + msg)); skip it.
    # The lookahead (not a consumed group) keeps the skipped echo from swallowing a real marker on the same line.
    for m in re.finditer(r'FORCE_SAVE_(OK|ERROR)\b(?! ?\\*")[ ]?([^\n]*)', text):
        if m.group(1) == "ERROR":
            errors.append(re.split(r'\\n|"\s*[,}\]]$', m.group(2))[0].strip())
        else:
            found.setdefault("OK", m.group(2).strip())
    # An ERROR line with no OK line is fatal. An ERROR line next to an OK line is a warning the script chose
    # to continue past (for example a missing API it worked around); it is passed up as "_warnings".
    if errors and "OK" not in found:
        raise VerifyError(f"{what} failed in the editor: {errors[0]}")
    if "OK" not in found:
        raise VerifyError(f"{what}: python tool {tool['name']} did not report FORCE_SAVE_OK "
                          f"(it may have run nothing). Reply: {text[:300] or res}")
    try:
        data, _ = json.JSONDecoder().raw_decode(found["OK"])
    except ValueError:
        raise VerifyError(f"{what}: could not read the editor's answer: {found['OK'][:200]}")
    if errors and isinstance(data, dict):
        data["_warnings"] = errors
    return data


def unwrap(text):
    """Some MCP servers return the tool output JSON-wrapped ({"success":..,"output":".."}). Decode it properly."""
    try:
        outer = json.loads(text)
    except ValueError:
        return text
    if isinstance(outer, dict):
        # First NON-EMPTY string: a 5.9 reply may carry an empty "output" next to the real "returnValue".
        for k in ("output", "result", "stdout", "text", "returnValue"):
            if isinstance(outer.get(k), str) and outer[k]:
                return outer[k]
    return text


def tree_state(path):
    """(max mtime_ns, sha256 of names+contents, file count) for a folder; None when missing."""
    if not path or not os.path.isdir(path):
        return None
    h, newest, n = hashlib.sha256(), 0, 0
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for name in sorted(files):
            p = os.path.join(root, name)
            h.update(os.path.relpath(p, path).encode() + b"\0")
            h.update(sha256(p).encode())
            newest = max(newest, os.stat(p).st_mtime_ns)
            n += 1
    return (newest, h.hexdigest(), n)


def check_changed(label, before, after, allow_unchanged):
    """Raise unless `after` shows a write newer than `before`, and (unless allow_unchanged) different content.
    allow_unchanged only relaxes the hash check: the mtime must always move, or nothing was written."""
    if after is None:
        raise VerifyError(f"after the forced save there is nothing on disk for {label}")
    if before is None:
        return
    if after[0] <= before[0]:
        raise VerifyError(f"{label}: mtime did not move; the save did not write it. Do NOT package. "
                          "Retry once, then use the duplicate_asset escalation in stages/02_build/references/force-save-level.md")
    if allow_unchanged:
        return
    if after[1] == before[1]:
        raise VerifyError(f"{label} was rewritten but its contents are identical to before the save. "
                          "If you made edits, they were not saved. If you made none, use --allow-unchanged.")


def save_and_check(cli, tool, params, snapshot, before, path, assets, asset_files, ext_n, ext_dir, unknown,
                   allow_unchanged, settle, out):
    """Step 2 and 3: force-save, then require the disk to show it. Returns the new .umap disk_state."""
    b = before["level"]
    saved = run_script(cli, tool, SAVE_SCRIPT, params, "forced save")
    for w in saved.get("_warnings", []):
        out(f"warning from editor: {w}")
    if saved.get("notes"):  # a save call that returned False: trust it over any file that happens to look fine
        raise VerifyError("the editor reported a failed save: " + "; ".join(saved["notes"]))
    deadline = time.time() + settle
    after = snapshot()
    # The writes can land a moment after the call returns; wait for a change, up to `settle` seconds.
    while time.time() < deadline and after == before:
        time.sleep(0.2)
        after = snapshot()

    a = after["level"]
    if a is None:
        raise VerifyError(f"after the forced save there is no file at {path}")
    with open(path, "rb") as f:
        if f.read(4) != UMAP_MAGIC:
            raise VerifyError(f"{path} does not start with the Unreal package header; it is not a valid .umap")
    if a[2] == 0:
        raise VerifyError(f"{path} is empty after the save")
    check_changed(path, b, a, allow_unchanged)
    t = after["tree"]
    if ext_n and (t is None or t[2] < ext_n):
        raise VerifyError(f"the level has {ext_n} external actors but {ext_dir} holds "
                          f"{0 if t is None else t[2]} files. Their edits are not on disk.")
    if ext_n or (unknown and t is not None):
        check_changed(ext_dir, before["tree"], t, allow_unchanged)
    for name in assets:
        check_changed(asset_files[name], before["assets"][name], after["assets"][name], allow_unchanged)
    out(f"disk ok: sha256 {a[1][:12]}, {a[2]} bytes"
        + (f"; {t[2]} external actor files" if t and (ext_n or unknown) else "")
        + (f"; {len(assets)} asset(s)" if assets else ""))
    return a


def force_save(cli, tool, level=None, umap=None, expect_actors=(), assets=(), allow_unchanged=False,
               settle=2.0, out=print, verify_only=False):
    """Do all four steps. Returns a summary dict; raises VerifyError / McpError on any failure."""
    params = {"assets": list(assets)}
    probe = run_script(cli, tool, PROBE_SCRIPT, params, "reading the level")
    open_level = probe.get("open_level")
    if not open_level:
        raise VerifyError("the editor did not report which level is open")
    if level and level != open_level:
        raise VerifyError(f"--level {level} is not the open level ({open_level}). The save and the reload act on "
                          "the open level. Open that level in the editor first, then run this again.")
    level = open_level
    path = umap or probe.get("file")
    if not path:
        raise VerifyError("the editor did not say where the .umap lives; pass --umap PATH")
    asset_files = probe.get("asset_files") or {}
    missing_files = [a for a in assets if not asset_files.get(a)]
    if missing_files:
        raise VerifyError("the editor did not report a file for: " + ", ".join(missing_files))
    for w in probe.get("_warnings", []):
        out(f"warning from editor: {w}")
    ext_n, ext_dir = probe.get("external_actors") or 0, probe.get("external_dir")
    unknown = bool(probe.get("external_unknown"))  # editor could not tell which actors are external
    if ext_n and not ext_dir:
        raise VerifyError(f"the level has {ext_n} external actors but the editor gave no __ExternalActors__ folder")
    if unknown:
        # Hash the folder regardless. The count rule does not apply: not every actor is external.
        ext_n = 0

    def snapshot():
        return {"level": disk_state(path), "tree": tree_state(ext_dir) if (ext_n or unknown) else None,
                "assets": {a: disk_state(asset_files[a]) for a in assets}}

    before = snapshot()
    b = before["level"]
    out(f"level {level}: {probe['actors']} actors ({ext_n} external); file {path} "
        + ("(missing before)" if b is None else f"sha256 {b[1][:12]}"))

    if verify_only:
        # No save: the file was written by hand (the doc's duplicate_asset escalation). Prove it is a real
        # .umap holding the edits by reloading it and finding the expected actors.
        a = b
        if a is None:
            raise VerifyError(f"there is no file at {path}")
        with open(path, "rb") as f:
            if f.read(4) != UMAP_MAGIC:
                raise VerifyError(f"{path} does not start with the Unreal package header; it is not a valid .umap")
        if a[2] == 0:
            raise VerifyError(f"{path} is empty")
        out(f"verify-only: {path} is a valid .umap, sha256 {a[1][:12]}, {a[2]} bytes (no save was done)")
    else:
        a = save_and_check(cli, tool, params, snapshot, before, path, assets, asset_files, ext_n, ext_dir,
                           unknown, allow_unchanged, settle, out)

    reload = run_script(cli, tool, RELOAD_SCRIPT, params, "reloading the level")
    if reload.get("level") != level:
        raise VerifyError(f"after the reload the open level is {reload.get('level')}, expected {level}")
    if reload["actors"] != probe["actors"]:
        raise VerifyError(f"after reload the level has {reload['actors']} actors, expected {probe['actors']}. "
                          "The saved file does not match what was in the editor.")
    missing = [l for l in expect_actors if l not in reload.get("labels", [])]
    if missing:
        raise VerifyError("after reload these actors are missing: " + ", ".join(missing))
    out(f"reload ok: {reload['actors']} actors" + (f", found {len(expect_actors)} expected" if expect_actors else ""))
    return {"level": level, "file": path, "actors": reload["actors"], "sha256": a[1]}


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--url", default=None)
    p.add_argument("--timeout", type=float, default=120)
    p.add_argument("--python-tool", default=None, help="name of the MCP tool that runs editor Python")
    p.add_argument("--level", default=None, help="long package name, e.g. /Game/Maps/L_Main (default: open level)")
    p.add_argument("--umap", default=None, help="path of the .umap on disk (default: the editor says)")
    p.add_argument("--expect-actor", action="append", default=[], help="actor label that must exist after reload")
    p.add_argument("--asset", action="append", default=[], help="extra /Game/... asset to force-save")
    p.add_argument("--allow-unchanged", action="store_true", help="accept an identical file (no edits expected)")
    p.add_argument("--verify-only", action="store_true",
                   help="do not save; check the .umap on disk and reload it (needs --expect-actor). For the "
                        "hand-copied file in the duplicate_asset escalation")
    p.add_argument("--settle", type=float, default=2.0, help="seconds to wait for the file to change")
    p.add_argument("--list-tools", action="store_true")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        # make_client: on 5.9 tools/list shows only the meta-tools; the proxy looks inside the toolsets (mock 15)
        cli = make_client(a.url, a.timeout)
        tools = cli.list_tools()
        tool = pick_python_tool(tools, a.python_tool)
        if a.list_tools:
            print(f"python tool: {tool['name'] + ' (code arg: ' + code_key(tool) + ')' if tool else 'NONE'}")
            return 0
        if not tool:
            print("force_save_level: no python tool found on the MCP server (try --list-tools, --python-tool)",
                  file=sys.stderr)
            return 2
        if a.verify_only and not a.expect_actor:
            print("force_save_level: --verify-only needs at least one --expect-actor (the reload is the proof)",
                  file=sys.stderr)
            return 2
        res = force_save(cli, tool, a.level, a.umap, a.expect_actor, a.asset, a.allow_unchanged, a.settle,
                         verify_only=a.verify_only)
    except VerifyError as e:
        print(f"force_save_level: NOT VERIFIED: {e}", file=sys.stderr)
        return EXIT_TOOL
    except McpError as e:
        print(f"force_save_level: {e}", file=sys.stderr)
        return e.exit_code
    print(f"VERIFIED {res['level']} -> {res['file']} ({res['actors']} actors, sha256 {res['sha256'][:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
