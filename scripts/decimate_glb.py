"""Shrink a GLB prop for the game and fix its pivot and size.

Usage: blender -b -P decimate_glb.py -- in.glb out.glb [--target 15000] [--height METRES]

Steps: join all meshes -> move the pivot to bottom-centre (X/Y centre of the bounding box, Z minimum = 0)
-> optional uniform scale so the up (Z in Blender = Y in glTF) extent equals --height metres
-> collapse-decimate to about --target triangles (UVs and the baked textures stay valid)
-> export GLB. Prints one JSON line (tris before/after, final size in metres).

Why: Rodin Gen-2.5 returns ~500,000 triangles at an arbitrary size. A chase-camera crew row needs
~15k per prop at real-world scale with the pivot on the ground. Blender only, no AI model.
"""
import argparse
import json
import sys

import bpy
from mathutils import Matrix, Vector

ap = argparse.ArgumentParser()
ap.add_argument("inp")
ap.add_argument("out")
ap.add_argument("--target", type=int, default=15000, help="triangle goal (default 15000)")
ap.add_argument("--height", type=float, default=None, help="set the up extent to this many metres")
ap.add_argument("--lens", action="store_true",
                help="put the bright front-facing faces (a glowing lamp lens) in their own material slot 1 "
                     "('Lens', same texture) so the editor can swap an emissive material onto it")
ap.add_argument("--lens-lum", type=float, default=0.45, help="--lens: albedo luminance above this counts as lens")
ap.add_argument("--lens-min-z", type=float, default=0.3, help="--lens: ignore faces below this fraction of the height")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.inp)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    sys.exit("no mesh in " + a.inp)
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.active_object
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = obj.data


def tri_count(mesh):
    mesh.calc_loop_triangles()
    return len(mesh.loop_triangles)


before = tri_count(me)
xs = [v.co.x for v in me.vertices]
ys = [v.co.y for v in me.vertices]
zs = [v.co.z for v in me.vertices]
me.transform(Matrix.Translation(Vector((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs)))))
if a.height:
    me.transform(Matrix.Scale(a.height / (max(zs) - min(zs)), 4))

if before > a.target:
    mod = obj.modifiers.new("dec", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = a.target / before
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
me = obj.data
after = tri_count(me)


def base_color_image(mat):
    """The image feeding Base Color (else the first image texture) of a node material, or None."""
    tree = getattr(mat, "node_tree", None)
    if tree is None:
        return None
    for node in tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            link = node.inputs["Base Color"].links
            if link and link[0].from_node.type == "TEX_IMAGE" and link[0].from_node.image:
                return link[0].from_node.image
    return next((n.image for n in tree.nodes if n.type == "TEX_IMAGE" and n.image), None)


def split_lens(mesh, lum_min, min_z_frac):
    """Move front-facing (-Y in Blender = glTF +Z) bright faces to material slot 1. Returns the face count."""
    import numpy as np
    img = base_color_image(mesh.materials[0]) if mesh.materials else None
    uvl = mesh.uv_layers.active
    if img is None or uvl is None:
        return 0
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    n_loops = len(mesh.loops)
    uv = np.empty(n_loops * 2, dtype=np.float32)
    try:
        uvl.uv.foreach_get("vector", uv)
    except Exception:  # older API
        uvl.data.foreach_get("uv", uv)
    uv = uv.reshape(n_loops, 2)
    n_poly = len(mesh.polygons)
    start = np.empty(n_poly, dtype=np.int64)
    total = np.empty(n_poly, dtype=np.int64)
    mesh.polygons.foreach_get("loop_start", start)
    mesh.polygons.foreach_get("loop_total", total)
    if (total != 3).any():
        return 0
    cuv = (uv[start] + uv[start + 1] + uv[start + 2]) / 3.0
    ix = np.clip((cuv[:, 0] % 1.0) * w, 0, w - 1).astype(np.int64)
    iy = np.clip((cuv[:, 1] % 1.0) * h, 0, h - 1).astype(np.int64)
    rgb = px[iy, ix, :3]
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    nrm = np.empty(n_poly * 3, dtype=np.float32)
    mesh.polygon_normals.foreach_get("vector", nrm)
    nrm = nrm.reshape(n_poly, 3)
    cen = np.empty(n_poly * 3, dtype=np.float32)
    mesh.polygons.foreach_get("center", cen)
    cen = cen.reshape(n_poly, 3)
    zs_all = np.array([v.co.z for v in mesh.vertices], dtype=np.float32)
    z_min = zs_all.min() + (zs_all.max() - zs_all.min()) * min_z_frac
    pick = (lum > lum_min) & (nrm[:, 1] < -0.5) & (cen[:, 2] > z_min)
    if pick.sum() < 8:
        return 0
    lens_mat = mesh.materials[0].copy()
    lens_mat.name = "Lens"
    mesh.materials.append(lens_mat)
    idx = np.zeros(n_poly, dtype=np.int32)
    idx[pick] = 1
    mesh.polygons.foreach_set("material_index", idx)
    mesh.update()
    return int(pick.sum())


lens_faces = split_lens(me, a.lens_lum, a.lens_min_z) if a.lens else None
size = obj.dimensions
bpy.ops.export_scene.gltf(filepath=a.out, export_format="GLB", use_selection=True)
print("DECIMATE_RESULT " + json.dumps({
    "tris_before": before, "tris_after": after, "lens_faces": lens_faces,
    "size_m": [round(size.x, 3), round(size.y, 3), round(size.z, 3)],
    "blender_axes": "X right, Y depth, Z up (glTF Y up)",
}))
