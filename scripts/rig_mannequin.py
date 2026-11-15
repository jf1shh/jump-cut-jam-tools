#!/usr/bin/env python3
"""Rig a throwaway humanoid in Blender (CPU only, no GPU) and export an FBX for Unreal.

  blender -b -P scripts/rig_mannequin.py -- OUT_DIR [--input CHAR.glb] [--height 1.8]
         [--names mannequin|generic] [--face -Y] [--input-facing +X]

Without --input it builds the fallback `character` prop by running procedural_props.py first (output in
OUT_DIR). Steps: import mesh, join it, turn the MESH to the facing you asked for, build the armature on the turned
mesh from scripts/rig_bones.py, bind, check coverage and alignment, export `character_<names>.fbx` (leaf bones
off, deform bones only). Nothing is turned after binding.

Facing rule (two options, no contradiction):
  --input-facing  which way the INPUT mesh faces (default +X, like the procedural_props character). An input that
                  does not face +X is REFUSED unless you say so here (`--input-facing -Y` accepts it and turns
                  it to +X first). The check can tell sideways from forwards but not +X from -X: say -X if so.
  --face          which way the rigged mesh faces in the exported FBX (default -Y). The mesh and bones are turned
                  together before binding.

  --names mannequin  bones carry the UE5 mannequin names: import onto the mannequin skeleton, no retarget
                     (path B in stages/02_build/references/character-rig/dry-run-plan.md).
  --names generic    same bones with neutral names (Bone_Pelvis...) so the IK Retargeter has to map chains
                     (path A stand-in when Rigify is not used; see rig_rigify.py for the Rigify route).

Prints one line the timing log can read:  RIG names=... bones=N verts=N unweighted=N secs=S fbx=PATH
Practice content only (Rule 7(h)): keep OUT_DIR outside the repo (for example $CLAUDE_JOB_DIR/tmp).
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rig_bones  # noqa: E402


def parse(argv):
    ap = argparse.ArgumentParser(prog="rig_mannequin.py")
    ap.add_argument("out_dir")
    ap.add_argument("--input", help="character mesh (.glb/.fbx); default: the procedural_props character")
    ap.add_argument("--height", type=float, default=1.8,
                    help="height of the generated fallback character; an --input mesh keeps its own height")
    ap.add_argument("--names", choices=["mannequin", "generic"], default="mannequin")
    ap.add_argument("--face", default="-Y", type=str.upper, choices=["+X", "-Y", "+Y", "-X"],
                    help="axis the rigged character faces in the exported FBX (default -Y)")
    ap.add_argument("--input-facing", default="+X", type=str.upper, choices=["+X", "-Y", "+Y", "-X"],
                    help="axis the INPUT mesh faces (default +X; other values are accepted and turned to +X)")
    # argparse reads "-Y" after "--face" as an option, so glue "--face -Y" into "--face=-Y"
    glued = []
    for a in argv:
        if glued and glued[-1] in ("--face", "--input-facing") and a.upper() in ("+X", "-Y", "+Y", "-X"):
            glued[-1] += "=" + a
        else:
            glued.append(a)
    return ap.parse_args(glued)


FACE_DEGREES = {"+X": 0, "-Y": -90, "+Y": 90, "-X": 180}  # z rotation from +X facing to the named facing
INPUT_TURN = {"+X": 0, "-Y": 90, "+Y": -90, "-X": 180}  # z rotation that turns an input facing the key to +X


def turn_mesh(bpy, mesh, degrees):
    """Turn the mesh object alone about Z and apply it (glTF imports use quaternion mode: switch to XYZ first)."""
    import math
    if not degrees:
        return
    mesh.rotation_mode = "XYZ"
    mesh.rotation_euler = (0.0, 0.0, math.radians(degrees))
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)


def generic_name(name):
    """pelvis -> Bone_Pelvis, upperarm_l -> Bone_Upperarm_L, spine_01 -> Bone_Spine_01"""
    return "Bone_" + "_".join(p.upper() if p in ("l", "r") else p.capitalize() for p in name.split("_"))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = parse(argv)
    import bpy
    from mathutils import Vector

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
    mesh.name = "Character"

    # the bone layout assumes a standing person facing +X with feet on z=0: refuse anything else, and fit the
    # bones to the mesh's real height instead of trusting --height
    print(f"FACING input={args.input_facing} output={args.face}")
    turn_mesh(bpy, mesh, INPUT_TURN[args.input_facing])  # --input-facing says how the input faces: turn it to +X
    problem = rig_bones.check_input_box(tuple(mesh.dimensions), min(v.co.z for v in mesh.data.vertices))
    if problem:
        raise SystemExit("input refused: " + problem + " (or pass --input-facing with the axis it faces)")
    height = mesh.dimensions.z
    problem, note = rig_bones.front_back_problem([tuple(v.co) for v in mesh.data.vertices], height)
    if problem:
        raise SystemExit("input refused: " + problem)
    if note:
        print("NOTE " + note)
    bones = rig_bones.layout(height)
    # turn the MESH to the output facing now and turn the bone positions the same way, before any binding: the
    # mesh becomes a child of the armature at bind time, so turning both afterwards turns the mesh twice
    out_turn = FACE_DEGREES[args.face]
    turn_mesh(bpy, mesh, out_turn)
    bones = rig_bones.rotate_bones(bones, out_turn)
    if args.names == "generic":
        bones = rig_bones.renamed(bones, {b["name"]: generic_name(b["name"]) for b in bones})
    problems = rig_bones.validate(bones)
    if problems:
        raise SystemExit("bad bone layout: " + "; ".join(problems))

    arm_data = bpy.data.armatures.new("Armature")
    arm = bpy.data.objects.new("Armature", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    made = {}
    for b in bones:
        eb = arm_data.edit_bones.new(b["name"])
        eb.head, eb.tail = Vector(b["head"]), Vector(b["tail"])
        made[b["name"]] = eb
    for b in bones:
        if b["parent"]:
            made[b["name"]].parent = made[b["parent"]]
            made[b["name"]].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    deform = {b["name"] for b in bones}
    mesh_bones = {g.name for g in mesh.vertex_groups}

    def count_unweighted():
        return sum(1 for v in mesh.data.vertices if not any(g.weight > 0 for g in v.groups))

    auto_missed = count_unweighted()
    if auto_missed:  # heat weights fail on loose boxes: give each such vertex to its nearest bone, weight 1
        for v in mesh.data.vertices:
            if not any(g.weight > 0 for g in v.groups):
                mesh.vertex_groups[rig_bones.nearest_bone(tuple(v.co), bones)].add([v.index], 1.0, "REPLACE")

    def measure():
        """coverage and alignment of the current weights (each bone must lie near the vertices it moves)"""
        owners = rig_bones.vertex_owner_names(mesh)
        cover = rig_bones.group_counts(owners)
        align = rig_bones.alignment_stats(bones, owners, [tuple(v.co) for v in mesh.data.vertices])
        return (cover, rig_bones.coverage_problems(cover), rig_bones.alignment_problems(align, height),
                max((d for _, d in align.values()), default=0.0))

    cover, cover_problems, align_problems, align_max = measure()
    weights = "heat" if not auto_missed else ("nearest" if auto_missed == len(mesh.data.vertices) else "heat+nearest")
    if (cover_problems or align_problems) and weights != "nearest":
        # Blender's heat weights are fragile on loose pieces: redo the whole skin deterministically
        rig_bones.assign_nearest(mesh, bones)
        weights = "nearest (heat result failed the checks)"
        cover, cover_problems, align_problems, align_max = measure()
    unweighted = count_unweighted()

    fbx = os.path.join(args.out_dir, f"character_{args.names}.fbx")
    print(f"RIG names={args.names} bones={len(bones)} groups={len(mesh_bones & deform)} "
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
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, add_leaf_bones=False,
                             axis_forward="-Y", axis_up="Z", apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", object_types={"ARMATURE", "MESH"},
                             use_armature_deform_only=True, bake_anim=False, path_mode="COPY",
                             embed_textures=True)


if __name__ == "__main__":
    rig_bones.run_main(main)
