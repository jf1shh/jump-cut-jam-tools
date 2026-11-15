#!/usr/bin/env python3
"""Import a locally-generated GLB asset into a UE 5.8 project, following this
repo's naming conventions (CLAUDE.md: SM_ for static mesh, SK_ for skeletal
mesh, MI_ for material instance).

INTENDED RUNTIME: this file only works inside the Unreal Editor's embedded
Python interpreter (the `unreal` module is provided by the Editor Scripting
Utilities / Python Editor Script Plugin, not a pip package). Two ways to run it:

  1. Headless, from a shell, against a real .uproject (LIVE-VERIFIED, UE 5.8,
     2026-10-28 — see _config/reference/engine-reference/unreal/python-scripting.md):
       timeout 60 UnrealEditor-Cmd <Project>.uproject \\
           -ExecCmds="py scripts/ue_import_asset.py --glb path/to.glb --dest /Game/Props/ \\
                      --name Crate --type prop" -unattended -nosplash -stdout \\
           -FullStdOutLogOutput
     `-ExecutePythonScript=` does not work on this build/config (no LogPython
     output). `-ExecCmds` commands are semicolon-separated, not comma; without
     an explicit `; quit` the editor process stays alive and must be killed
     (`pkill -9 -f "UnrealEditor-Cmd.*<project>"`) or run under `timeout`.
  2. Interactively, pasted into the Editor's Python console (Window > Developer
     Tools > Output Log, Python tab), then call:
       import_asset("path/to.glb", "/Game/Props/", "Crate", "prop")

3. AUDIO, with the editor OPEN (one command from a plain shell, no `unreal` module needed):
       python3 scripts/ue_import_asset.py --live --project PROJECT_DIR --wav path/to.wav --dest /Game/Audio/ --name Jump
   The real editor has no Python tool and no audio import tool, so `--live` uses its watch folder: it turns
   off the editor's import prompt over MCP (the editor must have been started with the MCP port, see
   scripts/launch-editor.sh), copies the file to PROJECT_DIR/Content/Audio/S_Jump.wav, and waits (up to
   --wait s, about a minute in practice) for the editor to import and save S_Jump. The headless mode (1)
   refuses to run while an editor has the project open, because two editors on one project clash; use
   `--live`. `--live` is audio only: meshes keep the headless path (it carries the PBR check).
   `--live` takes .wav only; the headless mode (1) also imports an .ogg via `--wav file.ogg`.
   Only the lead agent calls Unreal MCP (AGENTS.md), so only the lead runs `--live`.
   Docs: _config/reference/canon/jam-import-and-materials.md.

TEST ENVIRONMENT: do not point this at anything under this repo (no gameplay,
levels, or art belong in megajam pre-jam). The owner's existing scratch project
`~/Projects/ue-mcp-verify` (used for a prior Unreal MCP gate test) is an
appropriate place to test this script against a real .uproject.

glTF/GLB import support (LIVE-VERIFIED, UE 5.8, 2026-10-28):
`AssetImportTask` + `AssetToolsHelpers.get_asset_tools().import_asset_tasks()`
on a `.glb` does route through Interchange and produces material, textures and
static mesh. The Interchange glTF pipeline does not honor `destination_path` as
a flat final folder — it nests output under
`<destination_path>/<source_glb_basename>/StaticMeshes/<destination_name>` (and
`.../Materials/`, `.../Textures/`). `destination_name` (the leaf name) is
honored. The final asset path is resolved below from the task's
`imported_object_paths`, not assumed from `destination_path` + `destination_name`.
Full details: _config/reference/engine-reference/unreal/python-scripting.md.

API CONFIDENCE NOTE:
The `unreal` Python API calls below (AssetImportTask / AssetToolsHelpers /
MaterialEditingLibrary for import; add_simple_collisions with NDOP18 for
collision, counted with get_simple_ + get_convex_collision_count; StaticMeshEditorSubsystem.set_lod_group for LOD) are
all LIVE-VERIFIED against UE 5.8 as of 2026-10-28 — see
_config/reference/engine-reference/unreal/python-scripting.md for the resolved API points,
including the two that previously had wrong/non-existent names
(`ScriptingCollisionShapeType.CONVEX*` does not exist; `StaticMesh.post_edit_change()`
is not Python-exposed). Every call is still wrapped so a future engine-version
API rename degrades to a printed warning instead of a crash.
"""

import argparse
import json
import os
import re
import sys

try:
    import unreal
except ImportError:
    unreal = None  # Allows this file to be imported/linted outside the editor.


PREFIX_BY_TYPE = {
    "prop": "SM_",
    "character": "SK_",
}
SOUND_PREFIX = "S_"  # CLAUDE.md: Sound Cue/Wave
# Headless import_sound takes both: a plain AssetImportTask on an .ogg yields a SoundWave
# (LIVE-VERIFIED UE 5.9, 2026-11-10, stages/02_build/output/asset-test-ue59-2026-11-10.md; all Kenney audio is .ogg).
# The --live watch-folder route is verified for .wav only, so it keeps refusing .ogg.
HEADLESS_SOUND_EXTS = (".wav", ".ogg")
EXIT_REFUSED = 3  # headless run refused because an editor already has the project open
LIVE_WAIT = 120.0  # seconds to wait for the editor's auto-import (one sample took ~57 s)

# Convention from CLAUDE.md: one master material per hero look, named M_<Hero>.
# No art exists pre-jam, so this is almost always absent; that's expected, not
# an error.
DEFAULT_MASTER_MATERIAL_PATH = "/Game/Materials/M_Hero"


def _require_unreal():
    if unreal is None:
        raise RuntimeError(
            "The 'unreal' module is not available. Run this script inside the "
            "UE Editor's Python environment (UnrealEditor-Cmd -run=pythonscript, "
            "or the in-editor Python console), not with a system python3."
        )


def _normalize_dest_path(dest_path: str) -> str:
    dest_path = dest_path.strip()
    if not dest_path.startswith("/Game"):
        raise ValueError(f"dest_path must start with /Game, got: {dest_path!r}")
    if not dest_path.endswith("/"):
        dest_path += "/"
    return dest_path


def _import_via_asset_import_task(glb_path: str, dest_path: str, asset_name: str):
    """Runs the GLB through Interchange via the legacy-shaped AssetImportTask
    entry point. Leaving `factory` unset lets Interchange pick the pipeline for
    the .glb extension (there is no FBX-style legacy glTF factory to set
    explicitly). This entry point (unreal.AssetImportTask +
    AssetToolsHelpers.get_asset_tools().import_asset_tasks) is the long-standing
    documented way to drive editor import from Python and is expected to still
    route through Interchange in 5.8, but that routing itself is UNVERIFIED
    against this repo's _config/reference/engine-reference/unreal/.
    """
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", glb_path)
    task.set_editor_property("destination_path", dest_path.rstrip("/"))
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    # factory left as None/default: Interchange resolves the pipeline from the
    # .glb extension rather than a factory class we'd have to name explicitly.

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    imported_paths = list(task.get_editor_property("imported_object_paths") or [])
    return imported_paths


def _collision_shape_count(static_mesh):
    """Number of simple-collision shapes on `static_mesh`, or None if no count API answers.

    LIVE-VERIFIED (UE 5.9, 2026-11-11): `get_simple_collision_count()` counts only boxes, spheres and
    capsules (StaticMeshEditorSubsystem.cpp, GetSimpleCollisionCount). It never counts convex hulls, and
    both Interchange's import collision and our NDOP18 k-DOP are convex hulls, so it read 0 on every
    prop while the collision was there. Add `get_convex_collision_count()` to get the real number.
    """
    apis = []
    try:
        apis.append(unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem))
    except Exception:  # noqa: BLE001 - editor API surface
        pass
    apis.append(getattr(unreal, "EditorStaticMeshLibrary", None))  # deprecated in 5.9, still answers
    for api in apis:
        try:
            simple = api.get_simple_collision_count(static_mesh)
            convex = api.get_convex_collision_count(static_mesh)
        except Exception:  # noqa: BLE001 - try the next API
            continue
        if simple is not None and convex is not None and simple >= 0 and convex >= 0:
            return simple + convex
    return None


def _add_ndop18_collision(static_mesh):
    """Add one NDOP18 k-DOP hull. Returns (status, ok). `add_simple_collisions` returns the new shape's
    index, or -1 (INDEX_NONE) when the engine could not build one; that used to be ignored."""
    shape = getattr(getattr(unreal, "ScriptingCollisionShapeType", None), "NDOP18", None)
    if shape is None:
        # LIVE-VERIFIED (UE 5.8): there is no CONVEX / CONVEX_DECOMPOSITION member; NDOP18 is the one we use.
        print("WARNING: unreal.ScriptingCollisionShapeType.NDOP18 not found; skipping collision generation.")
        return "skipped(no-enum-member)", False
    adders = []
    try:
        adders.append(unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem))
    except Exception:  # noqa: BLE001
        pass
    adders.append(getattr(unreal, "EditorStaticMeshLibrary", None))
    for api in adders:
        add = getattr(api, "add_simple_collisions", None)
        if add is None:
            continue
        index = add(static_mesh, shape)
        if index is not None and index < 0:
            print("WARNING: add_simple_collisions(NDOP18) returned -1: the engine built no collision shape.")
            return "failed(NDOP18 returned -1)", False
        return "convex(NDOP18)", True
    print("WARNING: add_simple_collisions unavailable in this editor build; skipping collision generation.")
    return "skipped(api-missing)", False


def _apply_static_mesh_setup(static_mesh) -> str:
    """Collision + LOD setup for a freshly imported static mesh. Returns a short status string for the
    summary line, e.g. `collision=convex(NDOP18) shapes=1, lod=auto(SmallProp LODGroup)`.

    Collision: if the import already gave the mesh simple collision (Interchange builds a convex hull by
    default in 5.9), keep it instead of stacking a second, overlapping hull on top. Otherwise add an
    NDOP18 hull. Either way the shapes are counted again AFTER the LOD rebuild, so the summary reports
    what will be saved, and a mesh left with no collision says `collision=NONE(...)` and warns loudly.
    Every engine call is guarded so an API rename degrades to a warning, not a crash.
    """
    before = _collision_shape_count(static_mesh)
    if before:
        collision = "kept(import)"
    else:
        collision, _ = _add_ndop18_collision(static_mesh)

    # LOD: LIVE-VERIFIED (UE 5.8, 2026-10-28) - unreal.StaticMesh has no
    # Python-exposed post_edit_change(), so the plain
    # set_editor_property("lod_group", ...) approach never rebuilds LODs.
    # unreal.StaticMeshEditorSubsystem.set_lod_group() is the confirmed 5.8
    # entry point: it both sets the LODGroup and triggers the engine-side
    # rebuild that property assignment alone does not.
    try:
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        subsystem.set_lod_group(static_mesh, "SmallProp")
        lod = "lod=auto(SmallProp LODGroup)"
    except Exception as exc:  # noqa: BLE001 - editor API surface, keep this non-fatal
        print(f"WARNING: could not set LODGroup for auto LOD generation ({exc}); "
              "skipping LOD setup.")
        lod = "lod=skipped(api-missing)"

    after = _collision_shape_count(static_mesh)
    if after is None:
        collision_status = f"collision={collision} shapes=unknown"
    elif after == 0:
        print(f"WARNING: {getattr(static_mesh, 'get_name', lambda: 'mesh')()} has NO simple collision after "
              f"setup ({collision}); players and physics will pass through it.")
        collision_status = f"collision=NONE({collision})"
    else:
        collision_status = f"collision={collision} shapes={after}"
    return f"{collision_status}, {lod}"


def _create_material_instance(base_name: str, dest_path: str) -> str:
    """Creates MI_<base_name> parented to the repo's conventional master
    material if one exists; otherwise skips with a warning (expected pre-jam,
    since no art/materials exist yet).
    """
    if not unreal.EditorAssetLibrary.does_asset_exist(DEFAULT_MASTER_MATERIAL_PATH):
        print(f"WARNING: no master material at {DEFAULT_MASTER_MATERIAL_PATH}; "
              "skipping material instance creation.")
        return "material_instance=skipped(no-master-material)"

    master_material = unreal.EditorAssetLibrary.load_asset(DEFAULT_MASTER_MATERIAL_PATH)
    mi_name = f"MI_{base_name}"
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = asset_tools.create_asset(
        mi_name,
        dest_path.rstrip("/"),
        unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew(),
    )
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, master_material)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return f"material_instance={dest_path.rstrip('/')}/{mi_name}"


def _assert_real_material(static_mesh, asset_name: str) -> str:
    """Fails loudly (raises) if the imported mesh has no real PBR material — i.e. exactly the
    mock-jam-5 bug-2 signature (StaticMeshTools.get_material_slots showing one generic slot, no
    texture asset). Call this right after import, before any Blueprint wiring happens, so a process
    slip (e.g. an MCP import tool used instead of this script) is caught here even when this
    script *was* used correctly — this guards the embedding step, not just the tool choice.
    """
    # A SkeletalMesh keeps its slots in `materials` (SkeletalMaterial); a StaticMesh in
    # `static_materials` (StaticMaterial). Both slot types expose `material_interface`.
    slots_prop = "materials" if isinstance(static_mesh, unreal.SkeletalMesh) else "static_materials"
    materials = static_mesh.get_editor_property(slots_prop)
    if not materials:
        raise RuntimeError(f"{asset_name}: import produced zero material slots.")
    has_real_material = False
    for slot in materials:
        mat_iface = slot.get_editor_property("material_interface")
        if mat_iface is None:
            continue
        # A real Interchange-generated glTF material instance has texture parameters bound;
        # the engine's flat default does not expose any.
        try:
            tex_params = unreal.MaterialEditingLibrary.get_texture_parameter_names(mat_iface)
        except Exception:
            tex_params = []
        if tex_params:
            has_real_material = True
            break
    if not has_real_material:
        raise RuntimeError(
            f"{asset_name}: no material with a bound texture parameter found "
            f"(got {[s.get_editor_property('material_interface') for s in materials]}). "
            "This is the mock-jam-5 bug-2 signature — check whether this import actually went "
            "through AssetImportTask/Interchange or through a different tool."
        )
    return "material_check=pass(texture-bound material found)"


def import_asset(glb_path: str, dest_path: str, base_name: str, asset_type: str, require_pbr: bool = True) -> str:
    """Import `glb_path` into `dest_path` as SM_<base_name> (asset_type="prop")
    or SK_<base_name> (asset_type="character"), then apply this repo's
    collision/LOD/material-instance conventions. Returns the one-line summary
    that is also printed. Callable directly from the editor's Python console.

    `require_pbr` (default True) fails loudly if the imported prop mesh has no
    material with a bound texture parameter — the mock-jam-5 bug-2 signature.
    Pass False only for a deliberate greybox/placeholder import that is not
    art-final.
    """
    _require_unreal()

    if asset_type not in PREFIX_BY_TYPE:
        raise ValueError(f"asset_type must be one of {list(PREFIX_BY_TYPE)}, got {asset_type!r}")
    if not os.path.isfile(glb_path):
        raise FileNotFoundError(f"GLB not found: {glb_path}")

    dest_path = _normalize_dest_path(dest_path)
    asset_name = f"{PREFIX_BY_TYPE[asset_type]}{base_name}"

    imported_paths = _import_via_asset_import_task(glb_path, dest_path, asset_name)

    # LIVE-VERIFIED (UE 5.8, 2026-10-28): Interchange's glTF pipeline does NOT
    # place the result flatly at f"{dest_path}{asset_name}" the way the legacy
    # FBX importer did. It nests output under a subfolder named after the
    # source file, e.g. <dest_path>/<source_basename>/StaticMeshes/<asset_name>
    # (materials go to <dest_path>/<source_basename>/Materials/ instead).
    # destination_name IS honored for the leaf asset name; destination_path is
    # only a root, not the final folder. So find the StaticMesh by inspecting
    # the task's own imported_object_paths rather than assuming a flat path.
    # LIVE-VERIFIED (UE 5.9, 2026-11-10, stages/02_build/output/asset-test-ue59-2026-11-10.md): one source can yield
    # several meshes. A multi-part FBX (Poly Haven crate: body, lid, latch) or an FBX with LOD0-LOD3
    # comes in as separate StaticMeshes, and a GLB with a joint (Kenney door-garage) comes in as a
    # SkeletalMesh even for a prop. So collect every mesh, set each one up by its real class, and
    # never stop at the first hit.
    mesh_paths = _mesh_package_paths(imported_paths)
    if not mesh_paths:
        summary = f"FAILED: import produced no mesh asset under {dest_path} (check Interchange glTF plugin is enabled; imported_object_paths={imported_paths})"
        print(summary)
        return summary
    leaf = lambda path: path.rsplit("/", 1)[-1]  # noqa: E731
    final_asset_path = next((path for path in mesh_paths if leaf(path) == asset_name), mesh_paths[0])

    setup_parts, check_parts = [], []
    if asset_type == "prop":
        for path in mesh_paths:
            mesh = unreal.EditorAssetLibrary.load_asset(path)
            tag = f"{leaf(path)}: " if len(mesh_paths) > 1 else ""
            if isinstance(mesh, unreal.StaticMesh):
                setup_parts.append(tag + _apply_static_mesh_setup(mesh))
            else:
                # EditorStaticMeshLibrary refuses a SkeletalMesh with TypeError ("Cannot nativize
                # 'SkeletalMesh' as 'StaticMesh'"), which used to abort a whole batch.
                setup_parts.append(tag + "skipped(SkeletalMesh: source has joints; no static-mesh "
                                   "collision/LOD; re-export without the rig for a static prop)")
            if require_pbr:
                check_parts.append(tag + _assert_real_material(mesh, leaf(path)))
        material_status = _create_material_instance(base_name, dest_path)
        if check_parts:
            material_status += " | " + "; ".join(check_parts)
    else:
        # Skeletal mesh collision/LOD conventions are out of scope for this
        # script (no character content exists pre-jam); only the import +
        # naming + material-instance step applies.
        setup_parts.append("skipped(character mesh: no SM-specific setup)")
        material_status = _create_material_instance(base_name, dest_path)
    setup_status = "; ".join(setup_parts)

    for path in mesh_paths:
        unreal.EditorAssetLibrary.save_asset(path)

    created = final_asset_path
    if len(mesh_paths) > 1:
        others = [path for path in mesh_paths if path != final_asset_path]
        created += f" (+{len(others)} more mesh(es): {', '.join(others)})"
    summary = f"Created {created} | {setup_status} | {material_status}"
    print(summary)
    return summary


def _mesh_package_paths(imported_paths):
    """Package paths of every StaticMesh/SkeletalMesh in a task's imported_object_paths, in import
    order, without duplicates."""
    found = []
    for obj_path in imported_paths:
        package_path = obj_path.split(".")[0]
        if package_path in found:
            continue
        asset = unreal.EditorAssetLibrary.load_asset(package_path)
        if isinstance(asset, (unreal.StaticMesh, unreal.SkeletalMesh)):
            found.append(package_path)
    return found


def import_sound(wav_path: str, dest_path: str, base_name: str) -> str:
    """Import a .wav or .ogg as S_<base_name> (a SoundWave) under `dest_path` and save it. Runs inside an editor:
    the headless commandlet or an editor's Python console. (`--live` does not use it: the open editor has no
    Python tool, so `live_import_sound` uses the watch-folder route.) Returns the package path of the SoundWave.
    Raises if nothing imported (the caller turns that into an error line)."""
    _require_unreal()
    if not os.path.isfile(wav_path):
        raise FileNotFoundError(f"sound file not found: {wav_path}")
    if not wav_path.lower().endswith(HEADLESS_SOUND_EXTS):
        raise ValueError(f"only .wav or .ogg imports are supported, got: {wav_path}")
    dest_path = _normalize_dest_path(dest_path)
    asset_name = f"{SOUND_PREFIX}{base_name}"
    imported_paths = _import_via_asset_import_task(wav_path, dest_path, asset_name)
    for obj_path in imported_paths:
        package_path = obj_path.split(".")[0]
        if isinstance(unreal.EditorAssetLibrary.load_asset(package_path), unreal.SoundWave):
            unreal.EditorAssetLibrary.save_asset(package_path)
            print(f"Created {package_path} | sound")
            return package_path
    raise RuntimeError(f"import produced no SoundWave under {dest_path} (imported_object_paths={imported_paths})")


class LiveError(Exception):
    def __init__(self, msg, exit_code=1):
        super().__init__(msg)
        self.exit_code = exit_code


def _read_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return [a.decode("utf-8", "replace") for a in f.read().split(b"\0") if a]
    except OSError:
        return []


def _ancestor_pids():
    pids, pid = set(), os.getpid()
    while pid > 1 and pid not in pids:
        pids.add(pid)
        try:
            with open(f"/proc/{pid}/stat") as f:
                pid = int(f.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    return pids


def _project_names(argv):
    """File names of the .uproject files an editor command line names (bare path or -project=PATH)."""
    names = set()
    for a in argv:
        if a.lower().startswith("-project="):
            a = a.split("=", 1)[1]
        if a.endswith(".uproject"):
            names.add(os.path.basename(a))
    return names


def editor_processes(project=None):
    """Other UnrealEditor processes (not us or our parents) as (pid, cmdline). With `project`, only those whose
    command line names that .uproject. Linux /proc only; elsewhere returns [] (no guess)."""
    mine, found = _ancestor_pids(), []
    try:
        entries = os.listdir("/proc")
    except OSError:
        return found
    want = os.path.basename(project) if project else None
    for e in entries:
        if not e.isdigit() or int(e) in mine:
            continue
        argv = _read_cmdline(e)
        if not any(os.path.basename(a).startswith("UnrealEditor") for a in argv[:6]):
            continue
        if want:
            named = _project_names(argv)
            # Paths may be relative to a cwd we cannot see, so compare file names. An editor whose
            # project cannot be read at all (Project Browser, launcher) is a possible clash: keep it.
            if named and want not in named:
                continue
        found.append((int(e), " ".join(argv)))
    return found


def _own_project():
    """The .uproject on our own command line (set when this runs inside UnrealEditor-Cmd), else None."""
    return next((a for a in _read_cmdline("self") if a.endswith(".uproject")), None)


def editor_open_reason(project=None):
    """Why a headless run would clash, or None when no other editor has the project. Tests replace this."""
    procs = editor_processes(project)
    if procs:
        pid, cmd = procs[0]
        return f"an Unreal editor is already running (pid {pid}: {cmd[:120]})"
    return None


def refuse_if_editor_open(project=None):
    """Headless guard. Returns True (after printing why) when the run must stop."""
    reason = editor_open_reason(project or _own_project())
    if not reason:
        return False
    print(f"ue_import_asset: refusing to run headless: {reason}.\n"
          "Two editors on one project clash. With the editor open, import audio with:\n"
          "  python3 scripts/ue_import_asset.py --live --project PROJECT_DIR --wav FILE.wav --dest /Game/Audio/ --name NAME\n"
          "(meshes: close the editor first; the headless path is the only one with the PBR check).",
          file=sys.stderr)
    return True


def _content_dir(project):
    """The project's Content folder, from a project folder or its .uproject file."""
    p = os.path.abspath(project)
    if os.path.isfile(p) and p.endswith(".uproject"):
        p = os.path.dirname(p)
    if not (os.path.isdir(p) and any(f.endswith(".uproject") for f in os.listdir(p))):
        raise LiveError(f"--project must be the project folder (or its .uproject file); no .uproject in {p}", 2)
    return os.path.join(p, "Content")


def _disable_import_prompt(cli):
    """The real editor has no Python and no audio-import tool. It auto-imports files dropped under Content/,
    but only when the "prompt before auto importing" editor setting is off (the default shows a popup and
    imports nothing). Turn it off through the ConfigSettings toolset."""
    from mcp_call import McpError
    from mx import names_in
    from step_shot import result_text
    sets = [t for t in names_in(result_text(cli.call("list_toolsets", {}))) if "configsettings" in t.lower()]
    if not sets:
        raise LiveError("no ConfigSettings toolset on the MCP server (is this the live editor? "
                        "scripts/launch-editor.sh)", 2)
    try:
        res = cli.call("call_tool", {"toolset_name": sets[0], "tool_name": "SetSectionProperties", "arguments": {
            "containerName": "Editor", "categoryName": "General", "sectionName": "LoadingSaving",
            "propertiesJson": json.dumps({"bPromptBeforeAutoImporting": False})}})
    except McpError as e:
        raise LiveError(f"could not turn off the import prompt: {e} "
                        "(is the editor up with the MCP port? scripts/launch-editor.sh)", e.exit_code)
    if "true" not in result_text(res).lower():
        raise LiveError(f"the editor did not accept bPromptBeforeAutoImporting=false: {result_text(res)[:200]}", 1)


def live_import_sound(wav, dest, name, project, url=None, timeout=60, wait=LIVE_WAIT, client=None,
                      poll=2.0, sleep=None, clock=None):
    """Add `wav` to the project while the editor is OPEN. Returns the SoundWave package path.

    Route (proved on the real editor 2026-11-09): switch off the editor's import prompt over MCP, copy the file
    to <project>/Content/<dest>/S_<name>.wav, and wait for the editor to import and save S_<name>.uasset by
    itself (about a minute). Raises LiveError (message ready to print) on any failure. `client`, `sleep` and
    `clock` are test hooks."""
    import shutil
    import time
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from mcp_call import McpClient, McpError
    sleep, clock = sleep or time.sleep, clock or time.monotonic
    wav = os.path.abspath(wav)
    if not os.path.isfile(wav):
        raise LiveError(f"WAV not found: {wav}", 2)
    if not wav.lower().endswith(".wav"):
        raise LiveError(f"only .wav imports are supported, got: {wav}", 2)
    try:
        dest = _normalize_dest_path(dest)
    except ValueError as e:
        raise LiveError(str(e), 2)
    if not dest.startswith("/Game/"):
        raise LiveError(f"--dest must be under /Game/, got: {dest}", 2)
    rel = dest[len("/Game/"):].rstrip("/")
    if rel and any(seg in ("", ".", "..") for seg in rel.split("/")):
        raise LiveError(f"--dest may not contain '..', '.' or empty folder names, got: {dest}", 2)
    if not re.fullmatch(r"[A-Za-z0-9_]+", name or ""):
        raise LiveError(f"--name must be letters, digits and underscores only (no dots, spaces or slashes), "
                        f"got: {name!r}", 2)
    folder =os.path.join(_content_dir(project), *dest[len("/Game/"):].split("/"))
    target = os.path.join(folder, SOUND_PREFIX + name + ".wav")
    uasset = target[:-len(".wav")] + ".uasset"
    package = f"{dest}{SOUND_PREFIX}{name}"
    if os.path.exists(uasset):
        raise LiveError(f"{package} already exists ({uasset}); pick another --name", 2)
    try:
        _disable_import_prompt(client or McpClient(url, timeout))
    except McpError as e:
        raise LiveError(f"{e} (is the editor up with the MCP port? scripts/launch-editor.sh)", e.exit_code)
    os.makedirs(folder, exist_ok=True)
    part = target + ".part"  # the editor must never see a half-copied .wav
    try:
        shutil.copyfile(wav, part)
        os.replace(part, target)
    except BaseException:
        if os.path.exists(part):
            os.remove(part)
        raise
    deadline = clock() + wait
    while clock() < deadline:
        if os.path.isfile(uasset) and os.path.getsize(uasset) > 0:
            return package
        sleep(poll)
    raise LiveError(f"{package} did not appear within {wait:.0f} s. Look in the editor for an \"Import / Don't "
                    f"Import\" popup (the prompt setting may not have taken) and for errors in the Output Log. "
                    f"The copied file is still at {target}.", 1)


def _parse_cli_args(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--glb", help="Path to the source .glb file (headless only)")
    src.add_argument("--wav", help="Path to a .wav file (becomes S_<name>, a SoundWave); "
                                   "headless also takes an .ogg")
    parser.add_argument("--dest", required=True, help="Destination content path, e.g. /Game/Props/")
    parser.add_argument("--name", required=True, help="Base asset name, no prefix (e.g. Crate)")
    parser.add_argument("--type", choices=list(PREFIX_BY_TYPE), help="prop or character (required with --glb)")
    parser.add_argument("--live", action="store_true",
                        help="Add --wav to the OPEN editor's project (watch-folder import; needs --project)")
    parser.add_argument("--project", default=None, help="Project folder (or .uproject) for --live")
    parser.add_argument("--url", default=None, help="MCP endpoint for --live (default http://127.0.0.1:8010/mcp)")
    parser.add_argument("--timeout", type=float, default=60, help="MCP timeout seconds for --live")
    parser.add_argument("--wait", type=float, default=LIVE_WAIT, help="Seconds to wait for the editor's import (--live)")
    parser.add_argument(
        "--require-pbr", dest="require_pbr", action="store_true", default=True,
        help="Fail if the imported prop mesh has no texture-bound material (default: on).",
    )
    parser.add_argument(
        "--no-require-pbr", dest="require_pbr", action="store_false",
        help="Allow a flat-material/greybox import without failing (deliberate placeholder only).",
    )
    a = parser.parse_args(argv)
    if a.glb and not a.type:
        parser.error("--type is required with --glb")
    if a.glb and a.live:
        parser.error("--live imports audio only (--wav). Meshes use the headless path (editor closed).")
    if a.live and not a.project:
        parser.error("--live needs --project (the project folder, so the file can be copied into its Content/)")
    if a.wav and a.type:
        parser.error("--type applies to --glb only; a --wav is always a sound")
    if a.wav and a.live and not a.wav.lower().endswith(".wav"):
        parser.error("--live takes a .wav only (the watch-folder route is verified for .wav); import an .ogg "
                     "headless with the editor closed, or convert it first: ffmpeg -i in.ogg out.wav")
    if a.wav and not a.wav.lower().endswith(HEADLESS_SOUND_EXTS):
        parser.error("--wav must be a .wav or .ogg file")
    return a


def main(argv):
    """Returns an exit code. --live: 0 ok, 1 import failed in the editor, 2 usage/editor unreachable.
    Headless: 3 refused because an editor has the project open."""
    args = _parse_cli_args(argv)
    if args.live:
        try:
            path = live_import_sound(args.wav, args.dest, args.name, args.project, args.url, args.timeout, args.wait)
        except LiveError as e:
            print(f"ue_import_asset: {e}", file=sys.stderr)
            return e.exit_code
        print(f"Created {path}")
        return 0
    if refuse_if_editor_open():
        return EXIT_REFUSED
    if args.wav:
        import_sound(args.wav, args.dest, args.name)
    else:
        import_asset(args.glb, args.dest, args.name, args.type, require_pbr=args.require_pbr)
    return 0


if __name__ == "__main__":
    # `UnrealEditor-Cmd ... -script="scripts/ue_import_asset.py --glb ..."` passes
    # the script's own args through sys.argv alongside engine args; keep this
    # entry point tolerant of being invoked either way by only parsing argv[1:].
    # Exit only on failure: a clean sys.exit(0) inside an editor session is needless.
    _rc = main(sys.argv[1:])
    if _rc:
        sys.exit(_rc)
