#!/usr/bin/env python3
"""asset_preview.py - render a visual contact sheet for a generated asset before it goes in the game.

    scripts/asset_preview.py PATH [PATH ...] [--ref auto|cube|human] [--out DIR] [--blender BIN]

PATH is a .glb/.gltf/.fbx file, an asset folder (``crate/`` with ``game/crate.glb``), or a folder of
asset folders (``work/generated/smoke-20261107``). For each asset it writes ``<asset>/preview.png`` (4
views on a neutral background with a scale reference, plus the texture maps) and
``<asset>/preview.json`` (bounds in metres, triangle count, materials/textures, flags), and prints
the PNG path so the agent can Read it and judge shape, scale and materials before import.

Blender runs in background mode with Cycles on the CPU only, so it never touches the GPU. The same
file is the Blender-side script (``--python`` with ``-- --inner ARGS.json``); everything outside
``_inner_main`` is pure Python and unit-testable without Blender.

Exit code: 0 all assets fine (warnings allowed), 1 at least one asset has an error flag or failed to
render, 2 bad usage.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MODEL_EXTS = (".glb", ".gltf", ".fbx")
ROLES = ("albedo", "normal", "ao")
VIEWS = (("front", (0, -1, 0)), ("side", (1, 0, 0)), ("back", (0, 1, 0)), ("3/4", (1, -1, 0.7)))
TILE = 480
THUMB = 240
MAX_M = 20.0  # bigger than this is almost certainly a units bug
MIN_M = 0.02  # smaller than 2 cm too
RENDER_TIMEOUT_S = 120


# ---------------------------------------------------------------- pure logic (tested without Blender)

def compute_flags(stats: dict, max_m: float = MAX_M, min_m: float = MIN_M) -> list[dict]:
    """Turn raw mesh stats into flags. Each flag: {code, level: error|warning, msg}."""
    flags: list[dict] = []

    def add(code: str, level: str, msg: str) -> None:
        flags.append({"code": code, "level": level, "msg": msg})

    size = [float(v) for v in stats.get("size_m") or (0, 0, 0)]
    tris = int(stats.get("tris") or 0)
    empty = int(stats.get("mesh_objects") or 0) == 0 or tris == 0
    if empty:
        add("empty_mesh", "error", "no mesh geometry (no mesh objects or 0 triangles)")
    else:
        biggest, smallest = max(size), min(size)
        if biggest < 1e-6:
            add("zero_size", "error", "bounding box has zero size")
        else:
            if smallest < 1e-6:
                add("flat_mesh", "warning", "one bounding-box axis is zero (flat mesh)")
            if biggest > max_m:
                add("scale_too_big", "error", f"largest side {biggest:.2f} m is over {max_m:g} m (units bug?)")
            elif biggest < min_m:
                add("scale_too_small", "error", f"largest side {biggest * 100:.2f} cm is under {min_m * 100:g} cm (units bug?)")
        if int(stats.get("non_manifold_edges") or 0) > 0:
            add("non_manifold", "warning", f"{stats['non_manifold_edges']} non-manifold edges after merging seam vertices")
        if not stats.get("materials"):
            add("no_material", "warning", "mesh has no material")

    textures = stats.get("textures") or []
    missing = [t.get("name") or t.get("role") for t in textures if not t.get("exists", True)]
    if missing:
        add("missing_textures", "error", "texture file/data missing: " + ", ".join(str(m) for m in missing))
    elif not textures and not empty:
        add("no_textures", "warning", "no texture maps used by the materials and none beside the model")
    return flags


def parse_aspect(text: str) -> tuple[float, float, float]:
    """'A:B' or 'A:B:tol' -> (A, B, tol). A = footprint width (longer of X/Y), B = height (Z). tol is relative, default 0.25."""
    parts = text.split(":")
    if len(parts) not in (2, 3):
        raise ValueError(f"--expect-aspect wants A:B or A:B:tol, got {text!r}")
    try:
        a, b = float(parts[0]), float(parts[1])
        tol = float(parts[2]) if len(parts) == 3 else 0.25
    except ValueError:
        raise ValueError(f"--expect-aspect wants numbers, got {text!r}") from None
    if a <= 0 or b <= 0 or tol < 0:
        raise ValueError("--expect-aspect needs A>0, B>0, tol>=0")
    return a, b, tol


MIN_DEPTH = 0.25  # short footprint side / long side; on by default with --expect-aspect; 0 or --allow-thin turns it off


def aspect_flag(size_m, expect: tuple[float, float, float], min_depth: float = MIN_DEPTH) -> dict | None:
    """Error flag when width:height is off from A:B by more than tol (relative), or the footprint is thin
    (min(X,Y)/max(X,Y) under min_depth). A flat balloon or a flat relief fails this."""
    a, b, tol = expect
    width, height = max(size_m[0], size_m[1]), size_m[2]
    depth = min(size_m[0], size_m[1])
    if min_depth > 0 and width > 1e-6 and height > 1e-6 and depth / width < min_depth:
        return {"code": "aspect_mismatch", "level": "error",
                "msg": f"thin footprint: short side is {depth / width:.2f} of the long side (min {min_depth:g}); "
                       f"pass --allow-thin if the prop is meant to be thin (door, sign, fence); "
                       f"a flat relief? bounds {size_m[0]:.3f}x{size_m[1]:.3f}x{size_m[2]:.3f} m"}
    want = a / b
    if height < 1e-6:
        return {"code": "aspect_mismatch", "level": "error",
                "msg": f"height is zero, expected width:height {a:g}:{b:g}"}
    got = width / height
    if abs(got - want) > tol * want:
        return {"code": "aspect_mismatch", "level": "error",
                "msg": f"width:height is {got:.2f} but expected {a:g}:{b:g} ({want:.2f}) +/-{tol:.0%} "
                       f"(bounds {size_m[0]:.3f}x{size_m[1]:.3f}x{size_m[2]:.3f} m)"}
    return None


def pick_ref(size_m, mode: str = "auto") -> tuple[str, float]:
    """Scale reference: ('human', 1.8) or ('cube', metres). auto picks something the same order as the asset."""
    biggest = max(size_m) if size_m else 0.0
    if mode == "human":
        return "human", 1.8
    if mode == "cube":
        return "cube", 1.0
    if biggest >= 1.2:
        return "human", 1.8
    if biggest >= 0.4:
        return "cube", 1.0
    return "cube", 0.1


def has_model(d: Path) -> bool:
    return any(p.is_file() and p.suffix.lower() in MODEL_EXTS for p in d.iterdir())


def asset_root(model: Path) -> Path:
    return model.parent.parent if model.parent.name == "game" else model.parent


COLLISION_PREFIXES = ("ucx_", "ubx_", "usp_", "ucp_")  # Unreal collision hulls, not part of the visible asset


def is_collision_name(name: str) -> bool:
    return name.lower().startswith(COLLISION_PREFIXES)


def _stem_key(p: Path) -> str:
    """Asset name of a model file: 'crate.high.glb' and 'crate.fbx' both belong to 'crate'."""
    s = p.stem
    return s[:-5] if s.lower().endswith(".high") else s


def _rank(p: Path):
    return (".high." in p.name.lower(), p.parent.name != "game", p.suffix.lower() == ".fbx", p.name)


def _models_in(d: Path) -> list[Path]:
    return sorted(p for p in d.iterdir() if p.is_file() and p.suffix.lower() in MODEL_EXTS) if d.is_dir() else []


def plan_assets(path: Path) -> list[tuple[Path, Path, str]]:
    """Work out what to preview: a list of (model, output dir, file prefix).

    - a model file: itself, output beside its asset folder as preview.png;
    - an asset folder (game/<name>.glb, raw.glb, raw.high.glb): one model, the game-ready one first;
    - a flat folder of different models (crate.glb, barrel.glb): one sheet per model, named
      ``<name>_preview.png`` so they do not overwrite each other;
    - a folder of any of those: all of the above.
    """
    path = Path(path)
    if path.is_file():
        return [(path, asset_root(path), "")] if path.suffix.lower() in MODEL_EXTS else []
    out: list[tuple[Path, Path, str]] = []
    for dirpath, dirnames, _files in os.walk(path):
        dirnames.sort()
        d = Path(dirpath)
        if d.name == "game" and d != path:
            continue  # handled with its parent
        models = _models_in(d) + ([m for m in _models_in(d / "game")] if (d / "game").is_dir() else [])
        if d.name == "game":
            models = _models_in(d)
        if not models:
            continue
        root = asset_root(models[0]) if d.name == "game" else d
        groups: dict[str, list[Path]] = {}
        for m in models:
            groups.setdefault(_stem_key(m), []).append(m)
        named = [k for k in groups if k.lower() != "raw"]
        if len(named) <= 1:  # one asset folder: raw / raw.high / game/<name> are variants of it
            groups = {"": [m for g in groups.values() for m in g]}
        for key, ms in groups.items():
            out.append((min(ms, key=_rank), root, f"{key}_" if key and len(groups) > 1 else ""))
    return out


def find_assets(path: Path) -> list[Path]:
    """The model files plan_assets would preview."""
    return [m for m, _o, _p in plan_assets(path)]


def dedupe_outputs(plan: list[tuple[Path, Path, str]]) -> list[tuple[Path, Path, str]]:
    """Two models must never write the same preview.png: give clashes a prefix from the file name."""
    # resolve first: 'work/x' and '/abs/work/x' are the same folder; the same model listed twice is one job
    uniq: dict[Path, tuple[Path, Path, str]] = {}
    for m, o, p in plan:
        uniq.setdefault(m.resolve(), (m.resolve(), o.resolve(), p))
    plan = list(uniq.values())
    seen: dict[tuple[Path, str], int] = {}
    for _m, o, p in plan:
        seen[(o, p)] = seen.get((o, p), 0) + 1
    fixed: list[tuple[Path, Path, str]] = []
    used: set[tuple[Path, str]] = set()
    for m, o, p in plan:
        if seen[(o, p)] > 1:
            try:
                rel = m.relative_to(o)  # crate.glb vs game/crate.glb stay different
            except ValueError:
                rel = Path(m.name)
            p = "_".join(rel.parts).replace(".", "_") + "_"
            base, n = p, 1
            while (o, p) in used:
                n += 1
                p = f"{base}{n}_"
        used.add((o, p))
        fixed.append((m, o, p))
    return fixed


def sidecar_textures(model: Path, have_roles: set[str]) -> list[dict]:
    """Pipeline maps stored beside the model (``raw.albedo.png`` etc.), for roles the model doesn't embed."""
    found = []
    for role in ROLES:
        if role in have_roles:
            continue
        for d in (model.parent, asset_root(model)):
            for stem in (model.stem, "raw"):
                p = d / f"{stem}.{role}.png"
                if p.is_file():
                    entry = {"role": role, "name": p.name, "source": "sidecar", "path": str(p), "exists": True}
                    try:
                        from PIL import Image
                        with Image.open(p) as im:
                            entry["size"] = list(im.size)
                    except Exception:  # noqa: BLE001 - unreadable png: show it as missing
                        entry["exists"] = False
                    found.append(entry)
                    break
            else:
                continue
            break
    return found


# ---------------------------------------------------------------- Blender side

def _inner_main(args_path: str) -> None:  # pragma: no cover - runs inside Blender
    import math

    import bmesh
    import bpy
    from mathutils import Vector

    a = json.load(open(args_path))
    model, workdir, ref_mode = a["model"], Path(a["workdir"]), a["ref"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ext = Path(model).suffix.lower()
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=model)
    else:
        bpy.ops.import_scene.gltf(filepath=model)
    # UE collision hulls (UCX_/UBX_/USP_/UCP_) ride along in the game FBX; they are not the visible asset
    collision = [o for o in bpy.context.scene.objects if o.type == "MESH" and is_collision_name(o.name)]
    collision_names = [o.name for o in collision]
    for o in collision:
        bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    dg = bpy.context.evaluated_depsgraph_get()

    mn, mx = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    tris = verts = nm_edges = 0
    for o in meshes:
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        verts += len(me.vertices)
        for v in me.vertices:
            w = o.matrix_world @ v.co
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        nm_edges += sum(1 for e in bm.edges if not e.is_manifold)
        bm.free()
        eo.to_mesh_clear()
    if not meshes or tris == 0:
        mn, mx = Vector((0, 0, 0)), Vector((0, 0, 0))

    # materials + textures
    def role_of(node, sock_name: str) -> str:
        s = (sock_name or "").lower()
        if s == "base color":
            return "albedo"
        if s == "normal":
            return "normal"
        if s in ("occlusion", "ao"):
            return "ao"
        if s:
            return "other"  # a known socket that is not albedo/normal/ao (Emission Color, Roughness...)
        n = (node.image.name if node.image else "").lower()
        for r, keys in (("normal", ("normal", "_n.")), ("ao", ("ao", "occlusion")), ("albedo", ("albedo", "diffuse", "color", "basecolor"))):
            if any(k in n for k in keys):
                return r
        return "other"

    def walk(tree, seen):
        for n in tree.nodes:
            if n.type == "TEX_IMAGE":
                yield n, tree
            elif n.type == "GROUP" and n.node_tree and n.node_tree not in seen:
                seen.add(n.node_tree)
                yield from walk(n.node_tree, seen)

    mats, textures, seen_img = [], [], set()
    for m in bpy.data.materials:
        if not any(m.name in [s.material.name for s in o.material_slots if s.material] for o in meshes):
            continue
        entry = {"name": m.name, "textures": []}
        if m.use_nodes and m.node_tree:
            for n, tree in walk(m.node_tree, set()):
                img = n.image
                # follow the links downstream (through Separate Color, Normal Map, Mix...) to the socket it feeds
                role, frontier, visited, reached = "other", [n], set(), False
                while frontier and role == "other":
                    cur = frontier.pop(0)
                    for l in tree.links:
                        if l.from_node != cur or l.to_node in visited:
                            continue
                        visited.add(l.to_node)
                        if l.to_node.type == "NORMAL_MAP":
                            role = "normal"
                        elif l.to_node.type in ("BSDF_PRINCIPLED", "GROUP", "OUTPUT_MATERIAL"):
                            role = role_of(n, l.to_socket.name)
                            reached = True  # it feeds a known socket: never guess from the file name
                        else:
                            frontier.append(l.to_node)
                        if role != "other":
                            break
                if role == "other" and not reached:
                    role = role_of(n, "")  # unlinked image node: guess from its name
                if img is None:
                    textures.append({"role": role, "name": n.name + " (no image)", "source": "node", "exists": False})
                    entry["textures"].append(n.name)
                    continue
                entry["textures"].append(img.name)
                if img.name in seen_img:
                    continue
                seen_img.add(img.name)
                packed = img.packed_file is not None
                path = bpy.path.abspath(img.filepath) if img.filepath else ""
                exists = packed or (bool(path) and os.path.isfile(path)) or len(img.pixels) > 0 and img.size[0] > 0 and img.source == "GENERATED"
                t = {"role": role, "name": img.name, "source": "packed" if packed else "file", "exists": bool(exists),
                     "size": [img.size[0], img.size[1]], "path": path if (path and os.path.isfile(path)) else None}
                if exists and img.size[0] > 0:
                    try:
                        thumb = workdir / f"tex_{len(textures)}.png"
                        c = img.copy()
                        c.scale(THUMB, THUMB)
                        c.filepath_raw = str(thumb)
                        c.file_format = "PNG"
                        c.save()
                        t["thumb"] = str(thumb)
                    except Exception as e:  # noqa: BLE001
                        t["thumb_error"] = str(e)
                elif exists:
                    t["exists"] = False  # file listed but zero-size/unreadable
                textures.append(t)
        mats.append(entry)

    stats = {
        "mesh_objects": len(meshes), "tris": tris, "verts": verts, "non_manifold_edges": nm_edges,
        "bounds_min_m": [round(v, 5) for v in mn], "bounds_max_m": [round(v, 5) for v in mx],
        "size_m": [round(mx[i] - mn[i], 5) for i in range(3)],
        "materials": mats, "textures": textures, "collision_meshes": collision_names,
    }

    # scene: reference object, light, camera
    size = stats["size_m"]
    kind, rsize = pick_ref(size, ref_mode)
    ctr = (mn + mx) / 2

    def mat(name, rgb):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
        return m

    def box(loc, dim, m):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        o = bpy.context.active_object
        o.scale = dim
        o.data.materials.append(m)
        return o

    gap = max(max(size) * 0.25, rsize * 0.2)
    if max(size) < 1e-9:
        gap = rsize * 0.5
    rw = rsize if kind == "cube" else 0.55 * rsize / 1.8
    rx, ry = mx.x + gap + rw / 2, mx.y + gap + rw / 2
    base = mn.z if meshes else 0.0
    if kind == "cube":
        box((rx, ry, base + rsize / 2), (rsize,) * 3, mat("ref", (0.15, 0.45, 0.85)))
        ref_pts = [(rx - rsize / 2, base), (rx + rsize / 2, base + rsize)]
    else:
        s = rsize / 1.8
        m = mat("ref", (0.9, 0.45, 0.1))
        box((rx - .1 * s, ry, base + .425 * s), (.15 * s, .15 * s, .85 * s), m)
        box((rx + .1 * s, ry, base + .425 * s), (.15 * s, .15 * s, .85 * s), m)
        box((rx, ry, base + 1.15 * s), (.4 * s, .22 * s, .6 * s), m)
        box((rx - .27 * s, ry, base + 1.15 * s), (.1 * s, .1 * s, .6 * s), m)
        box((rx + .27 * s, ry, base + 1.15 * s), (.1 * s, .1 * s, .6 * s), m)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=.11 * s, location=(rx, ry, base + 1.69 * s))
        bpy.context.active_object.data.materials.append(m)
        ref_pts = [(rx - .32 * s, base), (rx + .32 * s, base + 1.8 * s)]
    fmn = Vector((min(mn.x, rx - rw / 2), min(mn.y, ry - rw / 2), min(mn.z, base)))
    fmx = Vector((max(mx.x, rx + rw / 2), max(mx.y, ry + rw / 2), max(mx.z, base + rsize)))
    fctr = (fmn + fmx) / 2
    span = max(fmx - fmn)

    sc = bpy.context.scene
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.63, 0.65, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    sc.world = w
    sun = bpy.data.objects.new("s", bpy.data.lights.new("s", "SUN"))
    sun.data.energy = 2.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
    sc.collection.objects.link(sun)
    cam_d = bpy.data.cameras.new("c")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = span * 1.3
    cam_d.clip_start, cam_d.clip_end = span * 0.01, span * 20
    cam = bpy.data.objects.new("c", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 16
    sc.cycles.use_denoising = False
    sc.render.resolution_x = sc.render.resolution_y = TILE
    sc.view_settings.view_transform = "Standard"

    t0 = time.time()
    for i, (vname, d) in enumerate(VIEWS):
        dv = Vector(d).normalized()
        cam.location = fctr + dv * span * 4
        cam.rotation_euler = (fctr - cam.location).to_track_quat("-Z", "Y").to_euler()
        # fit this view: project the box (asset + reference) on the camera plane, centre it, scale to fit
        rot = cam.rotation_euler.to_matrix()
        right, up = rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0))
        pts = [Vector((x, y, z)) - fctr for x in (fmn.x, fmx.x) for y in (fmn.y, fmx.y) for z in (fmn.z, fmx.z)]
        xs, ys = [p.dot(right) for p in pts], [p.dot(up) for p in pts]
        cam.location = cam.location + right * (max(xs) + min(xs)) / 2 + up * (max(ys) + min(ys)) / 2
        cam_d.ortho_scale = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6) * 1.15
        sc.render.filepath = str(workdir / f"view_{i}.png")
        bpy.ops.render.render(write_still=True)
    stats["render_s"] = round(time.time() - t0, 2)
    stats["ref"] = {"kind": kind, "size_m": rsize}
    json.dump(stats, open(workdir / "stats.json", "w"))


# ---------------------------------------------------------------- contact sheet (PIL)

def _font(size: int):
    from PIL import ImageFont
    for name in ("DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def make_sheet(name: str, stats: dict, flags: list[dict], workdir: Path, out_png: Path) -> None:
    from PIL import Image, ImageDraw

    bg = (40, 42, 46)
    textures = stats.get("textures") or []
    head_h = 120 + 22 * max(0, len(flags) - 2)
    tex_h = THUMB + 56
    W = TILE * len(VIEWS)
    sheet = Image.new("RGB", (W, head_h + TILE + tex_h), bg)
    dr = ImageDraw.Draw(sheet)
    f_big, f_mid, f_sm = _font(26), _font(18), _font(15)

    sz = stats.get("size_m") or [0, 0, 0]
    errs = [f for f in flags if f["level"] == "error"]
    status, col = ("ERROR", (255, 90, 80)) if errs else ("WARN", (255, 190, 70)) if flags else ("OK", (110, 220, 130))
    dr.text((14, 8), f"{name}   [{status}]", font=f_big, fill=col)
    ref = stats.get("ref") or {}
    dr.text((14, 44), f"size X {sz[0]:.3f} x Y {sz[1]:.3f} x Z {sz[2]:.3f} m   tris {stats.get('tris', 0):,}   "
            f"materials {len(stats.get('materials') or [])}   textures {len(textures)}   "
            f"ref: {ref.get('kind', '?')} {ref.get('size_m', 0):g} m", font=f_mid, fill=(220, 220, 225))
    y = 76
    for fl in flags:
        c = (255, 90, 80) if fl["level"] == "error" else (255, 190, 70)
        dr.text((14, y), f"{fl['level'].upper()}  {fl['code']}: {fl['msg']}", font=f_sm, fill=c)
        y += 22
    if not flags:
        dr.text((14, y), "no flags", font=f_sm, fill=(110, 220, 130))

    for i, (vname, _d) in enumerate(VIEWS):
        p = workdir / f"view_{i}.png"
        if p.is_file():
            sheet.paste(Image.open(p).convert("RGB").resize((TILE, TILE)), (i * TILE, head_h))
        dr.text((i * TILE + 8, head_h + 6), vname, font=f_mid, fill=(30, 30, 30))
    dr.text((8, head_h + TILE + 6), "texture maps", font=f_mid, fill=(220, 220, 225))
    x = 8
    for t in textures[: W // (THUMB + 8)]:
        src = t.get("thumb") or t.get("path")
        box = (x, head_h + TILE + 32)
        if t.get("exists", True) and src and Path(src).is_file():
            im = Image.open(src).convert("RGB")
            im.thumbnail((THUMB, THUMB))
            sheet.paste(im, box)
        else:
            dr.rectangle([box, (box[0] + THUMB - 1, box[1] + THUMB - 1)], outline=(255, 90, 80), width=3)
            dr.text((box[0] + 12, box[1] + THUMB // 2 - 10), "MISSING", font=f_mid, fill=(255, 90, 80))
        s = t.get("size")
        dr.text((x, head_h + TILE + 32 + THUMB + 4), f"{t.get('role', '?')} {s[0]}x{s[1]}" if s else f"{t.get('role', '?')}",
                font=f_sm, fill=(220, 220, 225))
        x += THUMB + 8
    if not textures:
        dr.text((140, head_h + TILE + 8), "(none found)", font=f_sm, fill=(255, 190, 70))
    sheet.save(out_png)


# ---------------------------------------------------------------- driver

def find_blender(explicit: str | None) -> str | None:
    """Resolve the Blender binary; None if the given/env/PATH choice is not an executable file."""
    choice = explicit or os.environ.get("BLENDER") or "blender"
    found = shutil.which(choice)  # handles both a bare name on PATH and a path
    return found if found and Path(found).is_file() else None


def preview_one(model: Path, blender: str, ref_mode: str = "auto", out_dir: Path | None = None,
                timeout: int = RENDER_TIMEOUT_S, prefix: str = "",
                expect_aspect: tuple[float, float, float] | None = None, max_scale: float | None = None,
                min_depth: float = MIN_DEPTH) -> dict:
    """Render one model. Returns the preview.json dict (also written to disk); raises RuntimeError on failure."""
    model = model.resolve()
    out_dir = out_dir or asset_root(model)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="asset_preview_") as td:
        wd = Path(td)
        args = {"model": str(model), "workdir": str(wd), "ref": ref_mode}
        stats = _run_inner(blender, args, wd, timeout)
        stats["textures"] = (stats.get("textures") or []) + sidecar_textures(
            model, {t.get("role") for t in stats.get("textures") or [] if t.get("exists")})
        flags = compute_flags(stats, max_m=max_scale if max_scale else MAX_M)
        if expect_aspect and not any(f["code"] in ("empty_mesh", "zero_size") for f in flags):
            af = aspect_flag(stats["size_m"], expect_aspect, min_depth)
            if af:
                flags.append(af)
        png = out_dir / f"{prefix}preview.png"
        make_sheet(model.stem, stats, flags, wd, png)
    textures_json = [{k: v for k, v in t.items() if k != "thumb"} for t in stats.get("textures") or []]
    result = {
        "asset": model.stem, "model": str(model), "preview_png": str(png),
        "bounds_min_m": stats["bounds_min_m"], "bounds_max_m": stats["bounds_max_m"], "size_m": stats["size_m"],
        "tris": stats["tris"], "verts": stats["verts"], "non_manifold_edges": stats["non_manifold_edges"],
        "materials": stats["materials"], "textures": textures_json, "ref": stats.get("ref"),
        "collision_meshes": stats.get("collision_meshes", []),
        "flags": flags, "ok": not any(f["level"] == "error" for f in flags),
        "seconds": round(time.time() - t0, 1),
    }
    (out_dir / f"{prefix}preview.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def _run_inner(blender: str, args: dict, wd: Path, timeout: int) -> dict:
    _call_blender(blender, args, wd, timeout)
    return json.loads((wd / "stats.json").read_text())


def _call_blender(blender: str, args: dict, wd: Path, timeout: int) -> None:
    ap = wd / "args.json"
    ap.write_text(json.dumps(args))
    cmd = [blender, "-b", "--factory-startup", "--python", str(Path(__file__).resolve()), "--", "--inner", str(ap)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"blender timed out after {timeout}s") from e
    if not (wd / "stats.json").is_file():
        tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-12:])
        raise RuntimeError(f"blender produced no stats (rc={r.returncode}):\n{tail}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render a visual contact sheet + preview.json for generated assets.")
    ap.add_argument("paths", nargs="+", type=Path, help="model file, asset folder, or folder of asset folders")
    ap.add_argument("--ref", choices=("auto", "cube", "human"), default="auto", help="scale reference (default auto)")
    ap.add_argument("--out", type=Path, help="write preview.png/json here instead of beside the asset (single asset only)")
    ap.add_argument("--blender", help="Blender binary (default: $BLENDER or PATH)")
    ap.add_argument("--timeout", type=int, default=RENDER_TIMEOUT_S, help="seconds per Blender call")
    ap.add_argument("--expect-aspect", metavar="A:B[:tol]",
                    help="fail unless width (longer of X/Y) : height (Z) is A:B within tol (relative, default 0.25)")
    ap.add_argument("--min-depth", type=float, default=MIN_DEPTH, metavar="R",
                    help=f"with --expect-aspect: short:long footprint side must be at least R (default {MIN_DEPTH:g}; 0 = off)")
    ap.add_argument("--allow-thin", action="store_true",
                    help="with --expect-aspect: skip the thin-footprint check for props meant to be thin (door, sign, fence)")
    ap.add_argument("--max-scale", type=float, metavar="N", help=f"fail if the longest side is over N metres (default {MAX_M:g})")
    ns = ap.parse_args(argv)
    expect = None
    if ns.expect_aspect:
        try:
            expect = parse_aspect(ns.expect_aspect)
        except ValueError as e:
            ap.error(str(e))
    if ns.max_scale is not None and ns.max_scale <= 0:
        ap.error("--max-scale must be positive")

    plan: list[tuple[Path, Path, str]] = []
    for p in ns.paths:
        if not p.exists():
            print(f"asset_preview: not found: {p}", file=sys.stderr)
            return 2
        found = plan_assets(p)
        if not found:
            print(f"asset_preview: no .glb/.gltf/.fbx under {p}", file=sys.stderr)
            return 2
        plan += found
    plan = dedupe_outputs(plan)
    if ns.out and len(plan) != 1:
        print("asset_preview: --out needs exactly one asset", file=sys.stderr)
        return 2
    blender = find_blender(ns.blender)
    if not blender:
        choice = ns.blender or os.environ.get("BLENDER") or "blender"
        print(f"asset_preview: Blender not found or not executable: {choice} (set $BLENDER or --blender)", file=sys.stderr)
        return 2

    bad = 0
    for m, odir, prefix in plan:
        try:
            res = preview_one(m, blender, ns.ref, ns.out or odir, ns.timeout, prefix, expect, ns.max_scale,
                              0.0 if ns.allow_thin else ns.min_depth)
        except RuntimeError as e:
            print(f"FAIL {m}: {e}", file=sys.stderr)
            bad += 1
            continue
        errs = [f["code"] for f in res["flags"] if f["level"] == "error"]
        warns = [f["code"] for f in res["flags"] if f["level"] == "warning"]
        state = "ERROR " + ",".join(errs) if errs else ("warn " + ",".join(warns) if warns else "ok")
        sz = res["size_m"]
        asp = f"  aspect {max(sz[0], sz[1]) / sz[2]:.2f}" if sz[2] > 1e-6 else ""
        print(f"{res['preview_png']}  [{state}]  {sz[0]:.3f}x{sz[1]:.3f}x{sz[2]:.3f} m{asp}  {res['tris']} tris  {res['seconds']}s")
        for f in res["flags"]:
            if f["code"] in ("aspect_mismatch", "scale_too_big"):
                print(f"  {f['code']}: {f['msg']}", file=sys.stderr)
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    if "--inner" in sys.argv:
        _inner_main(sys.argv[sys.argv.index("--inner") + 1])
    else:
        sys.exit(main())
