#!/usr/bin/env python3
"""Rig a humanoid with Blender's bundled Rigify add-on (local, free, CPU only) and export an FBX for Unreal.

  blender -b -P scripts/rig_rigify.py -- OUT_DIR [--input CHAR.glb] [--height 1.8]

Steps: import (or build) the character, add Rigify's human metarig scaled to the character height, generate
the rig, bind the mesh with automatic weights (nearest-bone fallback from rig_bones.py when heat weights miss),
export `character_rigify.fbx` with deform bones only (DEF-* bones, leaf bones off). The bone names are NOT the
mannequin's, so this is the path that needs the IK Retargeter (path A in stages/02_build/references/character-rig/dry-run-plan.md).

The metarig is not fitted to the character beyond scale: how well Rigify's default proportions match the box
character, and whether the DEF-* skeleton imports cleanly into Unreal, are UNTESTED until the timed run.

Prints:  RIGIFY bones=N deform=N verts=N auto_missed=N unweighted=N secs=S fbx=PATH
"""
import argparse
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rig_bones  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(prog="rig_rigify.py")
    ap.add_argument("out_dir")
    ap.add_argument("--input")
    ap.add_argument("--height", type=float, default=1.8)
    args = ap.parse_args(argv)
    import bpy

    t0 = time.perf_counter()
    os.makedirs(args.out_dir, exist_ok=True)
    src = args.input
    if not src:
        subprocess.run(["blender", "-b", "-P", os.path.join(HERE, "procedural_props.py"), "--",
                        args.out_dir, "--only", "character", "--height", str(args.height)],
                       check=True, stdout=subprocess.DEVNULL)
        src = os.path.join(args.out_dir, "character.glb")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if src.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=src)
    else:
        bpy.ops.import_scene.gltf(filepath=src)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no mesh in " + src)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    mesh = bpy.context.view_layer.objects.active
    rig_bones.strip_old_rig(bpy, mesh)  # an --input that is already rigged must not keep its old rig
    mesh.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    problem = rig_bones.check_input_box(tuple(mesh.dimensions), min(v.co.z for v in mesh.data.vertices))
    if problem:
        raise SystemExit("input refused: " + problem)
    height = mesh.dimensions.z
    problem, note = rig_bones.front_back_problem([tuple(v.co) for v in mesh.data.vertices], height)
    if problem:
        raise SystemExit("input refused: " + problem.replace("give --input-facing -X if it faces -X",
                                                              "turn it to face +X first"))
    if note:
        print("NOTE " + note)
    # the prop faces +X; Rigify's metarig faces -Y: turn the mesh to match
    mesh.rotation_mode = "XYZ"  # glTF imports use quaternion mode, where rotation_euler is ignored
    mesh.rotation_euler = (0.0, 0.0, math.radians(-90))
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    if mesh.dimensions.x < mesh.dimensions.y:
        raise SystemExit("internal error: mesh was not turned to face -Y")

    bpy.ops.preferences.addon_enable(module="rigify")
    bpy.ops.object.armature_human_metarig_add()
    meta = bpy.context.view_layer.objects.active
    meta_h = max(c[2] for b in meta.data.bones for c in (b.head_local, b.tail_local))
    scale = height / meta_h
    meta.scale = (scale, scale, scale)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # fit the metarig's trunk and limb bones to the character's layout (layout +X forward -> -Y forward: (x,y)->(y,-x))
    from mathutils import Vector
    targets = rig_bones.rigify_fit_targets(rig_bones.layout(height))
    missing = [n for n in targets if n not in meta.data.bones]
    if missing:
        raise SystemExit("metarig has no bone(s): " + ", ".join(missing))
    bpy.ops.object.mode_set(mode="EDIT")
    for name, (h, t) in targets.items():
        eb = meta.data.edit_bones[name]
        eb.head, eb.tail = Vector((h[1], -h[0], h[2])), Vector((t[1], -t[0], t[2]))
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.pose.rigify_generate()
    rig = bpy.context.view_layer.objects.active
    if rig is None or rig is meta:
        rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE" and o is not meta)
    bpy.data.objects.remove(meta)

    # only trunk, limb, hand and foot bones deform: the metarig's face, finger and breast bones are not fitted to
    # this character and would grab vertices (and are dropped from the deform-only FBX)
    for b in rig.data.bones:
        b.use_deform = b.use_deform and rig_bones.rigify_skin_bone(b.name)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    def count_unweighted():
        return sum(1 for v in mesh.data.vertices if not any(g.weight > 0 for g in v.groups))

    auto_missed = count_unweighted()
    skin = [{"name": b.name, "head": tuple(b.head_local), "tail": tuple(b.tail_local),
             "radius": rig_bones.radius_for(b.name, height)}
            for b in rig.data.bones if b.use_deform and rig_bones.rigify_skin_bone(b.name)]
    if not skin:
        raise SystemExit("rigify produced no DEF- trunk/limb bones to skin")
    if auto_missed:  # same radius-based nearest-bone fallback as rig_mannequin.py, over the skinned DEF- bones
        for v in mesh.data.vertices:
            if not any(g.weight > 0 for g in v.groups):
                name = rig_bones.nearest_bone(tuple(v.co), skin, skip=())
                mesh.vertex_groups[name].add([v.index], 1.0, "REPLACE")

    def measure():
        """coverage and alignment of the current weights (each bone must lie near the vertices it moves)"""
        owners = rig_bones.vertex_owner_names(mesh)
        cover = rig_bones.group_counts(owners)
        align = rig_bones.alignment_stats(skin, owners, [tuple(v.co) for v in mesh.data.vertices])
        return (cover, rig_bones.coverage_problems(cover), rig_bones.alignment_problems(align, height),
                max((d for _, d in align.values()), default=0.0))

    cover, cover_problems, align_problems, align_max = measure()
    weights = "heat" if not auto_missed else ("nearest" if auto_missed == len(mesh.data.vertices) else "heat+nearest")
    if (cover_problems or align_problems) and weights != "nearest":
        # Blender's heat weights are fragile on loose pieces: redo the whole skin deterministically
        rig_bones.assign_nearest(mesh, skin, skip=())
        weights = "nearest (heat result failed the checks)"
        cover, cover_problems, align_problems, align_max = measure()
    unweighted = count_unweighted()

    fbx = os.path.join(args.out_dir, "character_rigify.fbx")
    print(f"RIGIFY bones={len(rig.data.bones)} deform={sum(1 for b in rig.data.bones if b.use_deform)} "
          f"verts={len(mesh.data.vertices)} auto_missed={auto_missed} unweighted={unweighted} "
          f"cover_core={cover['core']} cover_arms={cover['arms']} cover_legs={cover['legs']} "
          f"cover_head={cover['head']} cover_other={cover['other']} height={height:.3f} "
          f"align_max_m={align_max:.3f} weights={weights.split()[0]} secs={time.perf_counter() - t0:.2f} fbx={fbx}")
    if cover_problems:  # do not write an FBX that would look fine and not move the body
        print("COVERAGE FAIL: " + "; ".join(cover_problems))
        sys.exit(3)
    if align_problems:
        print("ALIGNMENT FAIL: " + "; ".join(align_problems))
        sys.exit(4)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    rig.select_set(True)
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, add_leaf_bones=False,
                             axis_forward="-Y", axis_up="Z", apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", object_types={"ARMATURE", "MESH"},
                             use_armature_deform_only=True, bake_anim=False, path_mode="COPY",
                             embed_textures=True)


if __name__ == "__main__":
    rig_bones.run_main(main)
