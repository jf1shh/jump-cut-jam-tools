"""Blender headless cleanup for one prop. Runs INSIDE Blender:

  blender -b -P blender_cleanup.py -- in.glb OUTDIR NAME --budget 5000 [--height 1.0] [--thumb]

Steps: join meshes, apply transforms, scale (longest axis -> --height metres if given), pivot to base
centre (origin on the floor), weld, decimate to the tri budget, UV check (smart-project if missing),
convex collision hull (UCX_<name>_00, UE FBX convention), PBR material slot M_<name>.
Writes OUTDIR/NAME.glb (metres), OUTDIR/NAME.fbx (mesh + UCX hull, cm), OUTDIR/cleanup_report.json,
and optionally OUTDIR/thumb.png.
"""
import argparse
import json
import math
import sys

import bmesh
import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("inp")
ap.add_argument("outdir")
ap.add_argument("name")
ap.add_argument("--budget", type=int, default=5000)
ap.add_argument("--height", type=float, default=0.0)
ap.add_argument("--thumb", action="store_true")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.inp)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    raise SystemExit("no mesh in input")
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
for o in meshes:  # unparent but keep the world pose (parent rotation/scale is baked in)
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.active_object
obj.name = a.name
obj.data.name = a.name

# weld
bm = bmesh.new()
bm.from_mesh(obj.data)
size0 = max(obj.dimensions) or 1.0
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=size0 * 1e-5)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.to_mesh(obj.data)
bm.free()
tris_in = len(obj.data.polygons)

# scale to target size (metres)
scale = 1.0
if a.height > 0 and max(obj.dimensions) > 0:
    scale = a.height / max(obj.dimensions)
    obj.scale = (scale, scale, scale)
    bpy.ops.object.transform_apply(scale=True)

# decimate to budget
if len(obj.data.polygons) > a.budget:
    mod = obj.modifiers.new("dec", "DECIMATE")
    mod.ratio = max(0.01, a.budget / len(obj.data.polygons))
    bpy.ops.object.modifier_apply(modifier=mod.name)

# pivot to base centre
corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(c[i] for c in corners) for i in range(3)))
mx = Vector((max(c[i] for c in corners) for i in range(3)))
pivot = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
obj.data.transform(__import__("mathutils").Matrix.Translation(-pivot))
obj.location = (0, 0, 0)
dims = obj.dimensions.copy()

# UV check
me = obj.data
if not me.uv_layers:
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    uv_status = "generated"
else:
    uv_status = "present"
uv = me.uv_layers.active.data
out_of_range = sum(1 for d in uv if not (-0.001 <= d.uv.x <= 1.001 and -0.001 <= d.uv.y <= 1.001))
uv_report = {"status": uv_status, "loops": len(uv), "out_of_0_1": out_of_range}

# PBR material slot M_<name>: keep the texture-carrying material, rename it
if not me.materials:
    me.materials.append(bpy.data.materials.new("M_" + a.name))
mat = me.materials[0]
mat.name = "M_" + a.name
while len(me.materials) > 1:
    me.materials.pop(index=len(me.materials) - 1)
has_tex = bool(mat.use_nodes and any(n.type == "TEX_IMAGE" for n in mat.node_tree.nodes))

tris = len(me.polygons)

# collision hull (UCX_ prefix is what UE's FBX importer turns into convex collision)
hull_me = bpy.data.meshes.new("UCX_%s_00" % a.name)
bm = bmesh.new()
bm.from_mesh(me)
res = bmesh.ops.convex_hull(bm, input=bm.verts[:])
bmesh.ops.delete(bm, geom=res["geom_interior"] + res["geom_unused"], context="VERTS")
bm.to_mesh(hull_me)
bm.free()
hull = bpy.data.objects.new("UCX_%s_00" % a.name, hull_me)
bpy.context.scene.collection.objects.link(hull)

import os
os.makedirs(a.outdir, exist_ok=True)
glb_path = os.path.join(a.outdir, a.name + ".glb")
fbx_path = os.path.join(a.outdir, a.name + ".fbx")

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", use_selection=True)
hull.select_set(True)
bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True, global_scale=1.0,
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                         axis_forward="-Y", axis_up="Z", path_mode="COPY", embed_textures=True)

thumb = None
if a.thumb:
    try:
        sc = bpy.context.scene
        hull.hide_render = True
        cam = bpy.data.objects.new("c", bpy.data.cameras.new("c"))
        sc.collection.objects.link(cam)
        sc.camera = cam
        d = max(dims) * 2.2 + 0.01
        cam.location = (d * 0.8, -d * 0.9, dims.z * 0.5 + d * 0.5)
        look = Vector((0, 0, dims.z * 0.5)) - cam.location
        cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
        sun = bpy.data.objects.new("s", bpy.data.lights.new("s", "SUN"))
        sun.data.energy = 3
        sun.rotation_euler = (math.radians(50), 0, math.radians(30))
        sc.collection.objects.link(sun)
        sc.render.engine = "BLENDER_WORKBENCH"
        sc.display.shading.light = "STUDIO"
        sc.display.shading.color_type = "TEXTURE"
        sc.render.resolution_x = sc.render.resolution_y = 512
        thumb = os.path.join(a.outdir, "thumb.png")
        sc.render.filepath = thumb
        bpy.ops.render.render(write_still=True)
    except Exception as exc:  # thumbnail is best effort
        print("thumb failed:", exc)
        thumb = None

report = {
    "name": a.name, "tris_in": tris_in, "tris": tris, "budget": a.budget, "scale": scale,
    "bbox_m": [round(v, 5) for v in dims], "pivot": "base-centre", "uv": uv_report,
    "material": mat.name, "has_texture": has_tex, "collision": "UCX_%s_00" % a.name,
    "collision_tris": len(hull_me.polygons), "lods": ["LOD0"],
    "glb": glb_path, "fbx": fbx_path, "thumb": thumb,
}
with open(os.path.join(a.outdir, "cleanup_report.json"), "w") as f:
    json.dump(report, f, indent=1)
print("CLEANUP_OK", json.dumps(report))
