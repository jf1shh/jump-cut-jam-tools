#!/usr/bin/env python3
"""UE5 mannequin ("Manny/Quinn") bone layout for the rig dry run. Pure Python, no Blender, no GPU.

The layout is a reduced mannequin skeleton: the same bone NAMES and parent links as the UE5 mannequin
(root, pelvis, spine_01..05, neck_01/02, head, clavicle/upperarm/lowerarm/hand, thigh/calf/foot/ball), with no
fingers, twist or IK helper bones. Positions are fractions of the character height for a person standing
upright with arms hanging down (the shape of the `character` prop in procedural_props.py: +X forward,
+Y = the character's left, origin at the feet).

Whether Unreal accepts this reduced skeleton on the real mannequin skeleton is UNTESTED until the timed run
(stages/02_build/references/character-rig/dry-run-plan.md, path B). Used by rig_mannequin.py (Blender) and tests/test_rig_bones.py.

  python3 scripts/rig_bones.py [--height 1.8]     # prints the bone table as JSON
"""
import argparse
import json
import re
import sys

# (name, parent, head (x, y, z), tail (x, y, z)) in height fractions; sides are written for the LEFT (+Y)
# and mirrored to _r by layout().
_CENTRE = [
    ("root", None, (0, 0, 0.0), (0, 0, 0.04)),
    ("pelvis", "root", (0, 0, 0.52), (0, 0, 0.56)),
    ("spine_01", "pelvis", (0, 0, 0.56), (0, 0, 0.605)),
    ("spine_02", "spine_01", (0, 0, 0.605), (0, 0, 0.65)),
    ("spine_03", "spine_02", (0, 0, 0.65), (0, 0, 0.695)),
    ("spine_04", "spine_03", (0, 0, 0.695), (0, 0, 0.73)),
    ("spine_05", "spine_04", (0, 0, 0.73), (0, 0, 0.765)),
    ("neck_01", "spine_05", (0, 0, 0.765), (0, 0, 0.785)),
    ("neck_02", "neck_01", (0, 0, 0.785), (0, 0, 0.805)),
    ("head", "neck_02", (0, 0, 0.805), (0, 0, 0.99)),
]
_SIDE = [  # left side only
    ("clavicle_l", "spine_05", (0, 0.02, 0.74), (0, 0.15, 0.74)),
    ("upperarm_l", "clavicle_l", (0, 0.215, 0.74), (0, 0.215, 0.60)),
    ("lowerarm_l", "upperarm_l", (0, 0.215, 0.60), (0, 0.215, 0.46)),
    ("hand_l", "lowerarm_l", (0, 0.215, 0.46), (0, 0.215, 0.40)),
    ("thigh_l", "pelvis", (0, 0.065, 0.52), (0, 0.065, 0.27)),
    ("calf_l", "thigh_l", (0, 0.065, 0.27), (0, 0.065, 0.045)),
    ("foot_l", "calf_l", (0, 0.065, 0.045), (0.06, 0.065, 0.02)),
    ("ball_l", "foot_l", (0.06, 0.065, 0.02), (0.12, 0.065, 0.02)),
]

# Chains the IK Retargeter's auto chain mapping looks for on a biped (names from the UE5 mannequin).
RETARGET_CHAINS = {
    "spine": ["pelvis", "spine_01", "spine_02", "spine_03"],
    "neck": ["neck_01"],
    "head": ["head"],
    "left_arm": ["clavicle_l", "upperarm_l", "lowerarm_l", "hand_l"],
    "right_arm": ["clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"],
    "left_leg": ["thigh_l", "calf_l", "foot_l", "ball_l"],
    "right_leg": ["thigh_r", "calf_r", "foot_r", "ball_r"],
}


def _mirror(name):
    return name[:-2] + "_r" if name.endswith("_l") else name


def layout(height=1.8):
    """Return the bones in parent-before-child order as dicts: name, parent, head, tail (metres)."""
    if height <= 0:
        raise ValueError("height must be > 0")
    rows = list(_CENTRE)
    for name, parent, h, t in _SIDE:
        rows.append((name, parent, h, t))
    for name, parent, h, t in _SIDE:
        rows.append((_mirror(name), _mirror(parent) if parent else None,
                     (h[0], -h[1], h[2]), (t[0], -t[1], t[2])))
    # clavicle's parent is a centre bone and stays unmirrored; _mirror leaves names without _l alone
    return [{"name": n, "parent": p,
             "head": tuple(round(c * height, 6) for c in h),
             "tail": tuple(round(c * height, 6) for c in t),
             "radius": round(radius_for(n) * height, 6)} for n, p, h, t in rows]


# Skinning radius per bone as a fraction of height: the half-thickness of the body part the bone drives.
# nearest_bone() ranks bones by (distance to the bone segment - radius), so a wide torso box goes to the spine
# and not to a thin clavicle or thigh segment next to its corner. Works for mannequin and Rigify DEF- names.
_RADIUS = [  # (regex on the lowercase name, fraction of height); first match wins
    (r"^root$", 0.0),
    (r"head|spine[._]006", 0.10),
    (r"neck|spine[._]00[45]", 0.04),
    (r"^(def-)?pelvis$|^def-spine$", 0.12),
    (r"spine", 0.14),
    (r"pelvis|clavicle|shoulder", 0.03),
    (r"thigh|calf|shin", 0.06),
    (r"foot|ball|toe", 0.05),
    (r"upperarm|lowerarm|upper_arm|forearm", 0.05),
    (r"hand", 0.04),
]


def radius_for(name, height=1.0):
    n = name.lower()
    for pattern, frac in _RADIUS:
        if re.search(pattern, n):
            return frac * height
    return 0.0


# Body groups for the coverage check (mannequin names and Rigify DEF- names); first match wins.
_GROUPS = [  # arms and legs first: "forearm" would otherwise match the head pattern's "ear"
    ("arms", r"clavicle|shoulder|upperarm|lowerarm|upper_arm|forearm|hand|thumb|f_(index|middle|ring|pinky)|palm"),
    ("legs", r"thigh|calf|shin|foot|ball|toe|heel"),
    ("head", r"head|neck|spine[._]00[456]|face|teeth|tongue|eye|jaw|ear|nose|lip|brow|lid|cheek|chin|forehead|temple"),
    ("core", r"pelvis|spine|breast"),
]
# Smallest share of all vertices each body group should hold on a humanoid. Below it the group has almost no
# geometry although the body part exists, so the rig would not move it (found in review round 2: arms and torso
# skinned to the wrong bones while the old check still printed unweighted=0).
MIN_SHARE = {"core": 0.10, "arms": 0.05, "legs": 0.10, "head": 0.03}


def group_of(name):
    n = name.lower()
    for group, pattern in _GROUPS:
        if re.search(pattern, n):
            return group
    return None


def group_counts(vertex_bones):
    """vertex_bones: the bone name that owns each vertex (None = unweighted).
    Returns counts for core, arms, legs, head, other, none."""
    counts = {"core": 0, "arms": 0, "legs": 0, "head": 0, "other": 0, "none": 0}
    for name in vertex_bones:
        counts["none" if name is None else (group_of(name) or "other")] += 1
    return counts


# Rigify metarig bones fitted to the layout before generating, so the rig's joints sit where the character's are.
# (metarig bone, (layout bone, end), (layout bone, end)): head and tail taken from the layout; `.L` rows are
# mirrored to `.R`. Fingers, face, breast and heel bones are left alone (not skinned, see rigify_skin_bone).
_RIGIFY_FIT = [
    ("spine", ("pelvis", "head"), ("spine_01", "head")),
    ("spine.001", ("spine_01", "head"), ("spine_02", "head")),
    ("spine.002", ("spine_02", "head"), ("spine_03", "head")),
    ("spine.003", ("spine_03", "head"), ("spine_05", "head")),
    ("spine.004", ("spine_05", "head"), ("neck_01", "head")),
    ("spine.005", ("neck_01", "head"), ("neck_02", "head")),
    ("spine.006", ("neck_02", "head"), ("head", "tail")),
    ("pelvis.L", ("pelvis", "head"), ("thigh_l", "head")),
    ("thigh.L", ("thigh_l", "head"), ("thigh_l", "tail")),
    ("shin.L", ("calf_l", "head"), ("calf_l", "tail")),
    ("foot.L", ("foot_l", "head"), ("foot_l", "tail")),
    ("toe.L", ("ball_l", "head"), ("ball_l", "tail")),
    ("shoulder.L", ("clavicle_l", "head"), ("clavicle_l", "tail")),
    ("upper_arm.L", ("upperarm_l", "head"), ("upperarm_l", "tail")),
    ("forearm.L", ("lowerarm_l", "head"), ("lowerarm_l", "tail")),
    ("hand.L", ("hand_l", "head"), ("hand_l", "tail")),
]


def rigify_fit_targets(bones, bend=0.01):
    """{metarig bone name: (head, tail)} in layout coordinates (+X forward). The knee is nudged forward and the
    elbow back by `bend` x height so Rigify's limb IK has a bend direction; limbs stay otherwise as laid out."""
    by = {b["name"]: b for b in bones}
    height = max(b["tail"][2] for b in bones)
    nudge = {("calf_l", "head"): (bend * height, 0, 0), ("thigh_l", "tail"): (bend * height, 0, 0),
             ("lowerarm_l", "head"): (-bend * height, 0, 0), ("upperarm_l", "tail"): (-bend * height, 0, 0)}

    def point(ref, mirror):
        name, end = ref
        if mirror:
            name = name[:-2] + "_r" if name.endswith("_l") else name
        p = list(by[name][end])
        dx, dy, dz = nudge.get((ref[0], ref[1]), (0, 0, 0))
        return (p[0] + dx, p[1] + (-dy if mirror else dy), p[2] + dz)

    out = {}
    for meta, h, t in _RIGIFY_FIT:
        out[meta] = (point(h, False), point(t, False))
        if meta.endswith(".L"):
            out[meta[:-2] + ".R"] = (point(h, True), point(t, True))
    return out


_RIGIFY_SKIN = re.compile(r"^def-(spine|pelvis|thigh|shin|foot|toe|shoulder|upper_arm|forearm|hand)([._]|$)")


def rigify_skin_bone(name):
    """True for the Rigify deform bones this fitted rig skins (trunk, limbs, hands, feet; no fingers/face/breast)."""
    return bool(_RIGIFY_SKIN.match(name.lower()))


def rotate_z(point, degrees):
    """Rotate a 3-tuple about the Z axis through the origin (counter-clockwise seen from +Z)."""
    import math
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return (point[0] * c - point[1] * s, point[0] * s + point[1] * c, point[2])


def rotate_bones(bones, degrees):
    """Copy of the bones turned about Z. Bone positions must be turned with the mesh, never after binding."""
    return [{**b, "head": rotate_z(b["head"], degrees), "tail": rotate_z(b["tail"], degrees)} for b in bones]


# A bone should sit inside or near the vertices it moves. Largest allowed distance from a bone's midpoint to the
# centre of the vertices it owns, as a fraction of the character height (0.15 = 27 cm on a 1.8 m person). The
# fallback prop's healthy worst case is 0.236 m (its leg is one box, no knee); a rig turned 90 degrees apart from
# its mesh measured 0.56 m, so 0.15 separates the two with room.
ALIGN_LIMIT = 0.15
ALIGN_MIN_VERTS = 8


def alignment_stats(bones, owners, points):
    """{bone: (vertex count, distance from the bone midpoint to the centre of its vertices)} for bones that own
    at least ALIGN_MIN_VERTS vertices. owners[i] is the bone name of points[i] (None = no bone)."""
    sums = {}
    for name, p in zip(owners, points):
        if name is None:
            continue
        n, x, y, z = sums.get(name, (0, 0.0, 0.0, 0.0))
        sums[name] = (n + 1, x + p[0], y + p[1], z + p[2])
    by = {b["name"]: b for b in bones}
    stats = {}
    for name, (n, x, y, z) in sums.items():
        if n < ALIGN_MIN_VERTS or name not in by:
            continue
        b = by[name]
        mid = [(h + t) / 2 for h, t in zip(b["head"], b["tail"])]
        stats[name] = (n, sum((m - c / n) ** 2 for m, c in zip(mid, (x, y, z))) ** 0.5)
    return stats


def alignment_problems(stats, height, limit=ALIGN_LIMIT):
    """Problems (empty = fine) for bones that sit farther than limit x height from the vertices they move; this is
    what catches a rig turned apart from its mesh while every vertex still has a bone."""
    return [f"{name} is {d:.3f} m from its {n} vertices (limit {limit * height:.3f} m)"
            for name, (n, d) in sorted(stats.items()) if d > limit * height]


def run_main(main):
    """Run a Blender script's main() so a failure really gives a non-zero exit code: `blender -b -P` exits 0 even
    after SystemExit or an uncaught exception, which hid refusals and COVERAGE FAIL from callers."""
    import os
    import traceback
    code = 0
    try:
        main()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (1 if e.code else 0)
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
    except Exception:
        traceback.print_exc()
        code = 1
    if code:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)


def vertex_owner_names(mesh):
    """Bone (vertex group) name with the largest weight for each vertex of a Blender mesh object, None if it has
    none. No bpy import needed: uses mesh.vertex_groups and mesh.data.vertices only."""
    names = {g.index: g.name for g in mesh.vertex_groups}
    owners = []
    for v in mesh.data.vertices:
        best = max(((g.weight, g.group) for g in v.groups if g.weight > 0), default=None)
        owners.append(names.get(best[1]) if best else None)
    return owners


def coverage_problems(counts, min_share=None):
    """Problems (empty = fine) when a body group holds too small a share of the vertices."""
    shares = MIN_SHARE if min_share is None else min_share
    total = sum(counts.values())
    if total == 0:
        return ["no vertices"]
    problems = []
    if counts.get("none"):
        problems.append(f"{counts['none']} of {total} vertices have no bone")
    for group, floor in shares.items():
        share = counts.get(group, 0) / total
        if share < floor:
            problems.append(f"{group} holds {counts.get(group, 0)} of {total} vertices "
                            f"({share:.1%}, want at least {floor:.0%})")
    return problems


def check_input_box(size, min_z, expected_height=None):
    """Problem string, or None, for an input mesh bounding box (size = x, y, z extents in metres).
    The layout assumes a standing person facing +X (arms span along Y), like the fallback prop."""
    sx, sy, sz = size
    if sz <= 0:
        return "mesh has no height"
    if sx > sy * 1.05:
        return (f"mesh is wider in X ({sx:.2f} m) than in Y ({sy:.2f} m): it looks like it faces -Y or +Y; "
                "turn it to face +X (like the character in procedural_props.py) and run again")
    if abs(min_z) > 0.02 * sz:
        return f"feet are not at z=0 (lowest point {min_z:.3f} m); move the mesh so its feet sit on z=0"
    if expected_height and abs(sz - expected_height) > 0.02 * expected_height:
        return f"mesh is {sz:.2f} m tall but the rig height is {expected_height:.2f} m"
    return None


def validate(bones):
    """Return a list of problems (empty list = fine): names unique, one root, parents first, no zero-length bones."""
    problems = []
    seen = set()
    roots = [b["name"] for b in bones if b["parent"] is None]
    if len(roots) != 1:
        problems.append(f"want exactly one root, got {roots}")
    for b in bones:
        n = b["name"]
        if n in seen:
            problems.append(f"duplicate bone {n}")
        if b["parent"] is not None and b["parent"] not in seen:
            problems.append(f"{n}: parent {b['parent']} missing or listed after it")
        if sum((a - c) ** 2 for a, c in zip(b["head"], b["tail"])) < 1e-12:
            problems.append(f"{n}: zero-length bone")
        seen.add(n)
    return problems


def missing_chain_bones(bones):
    """Bones the retarget chains expect that the layout does not have (empty = all present)."""
    names = {b["name"] for b in bones}
    return sorted({n for chain in RETARGET_CHAINS.values() for n in chain} - names)


def distance_to_segment(p, a, b):
    """Distance from point p to the segment a-b (3-tuples)."""
    ab = [y - x for x, y in zip(a, b)]
    ap = [y - x for x, y in zip(a, p)]
    denom = sum(c * c for c in ab)
    t = 0.0 if denom == 0 else max(0.0, min(1.0, sum(x * y for x, y in zip(ap, ab)) / denom))
    return sum((pc - (ac + t * dc)) ** 2 for pc, ac, dc in zip(p, a, ab)) ** 0.5


def assign_nearest(mesh, bones, skip=("root", "bone_root")):
    """Throw away every weight on a Blender mesh object and give each vertex weight 1 on its nearest bone's group.
    Used when Blender's heat weights fail the coverage or alignment checks (they are fragile on loose pieces)."""
    count = len(mesh.data.vertices)
    for group in mesh.vertex_groups:
        group.remove(range(count))
    for v in mesh.data.vertices:
        mesh.vertex_groups[nearest_bone(tuple(v.co), bones, skip)].add([v.index], 1.0, "REPLACE")


def front_back_problem(points, height):
    """(problem, note) for a mesh meant to face +X. Floor-level slice: the feet reach farther forward of the
    lower-leg line (the ankle) than back (toes beyond heels). Backwards -> a problem; feet too symmetric to tell ->
    a note saying front/back is assumed, not checked. Sideways facing is check_input_box's job."""
    floor = [p[0] for p in points if p[2] < 0.06 * height]
    upper = [p[0] for p in points if 0.06 * height <= p[2] < 0.5 * height]  # the leg line above the foot
    if not floor or not upper:
        return None, "front/back assumed +X, not checked (no floor or leg vertices)"
    ref = sum(upper) / len(upper)
    fwd, back = max(floor) - ref, ref - min(floor)
    if abs(fwd - back) < 0.01 * height:
        return None, "front/back assumed +X, not checked (feet reach equally far forward and back)"
    if back > fwd:
        return ("feet reach farther behind the body than in front (toes beyond heels at -X): the mesh looks "
                "backwards; give --input-facing -X if it faces -X"), None
    return None, None


def nearest_bone(point, bones, skip=("root", "bone_root")):
    """Name of the bone closest to point by (distance to its head-tail segment - its radius); ties go to the
    earlier bone. Fallback skinning where Blender's automatic weights fail (loose boxes, no shared edges). The
    radius lets a wide torso box win the spine over thin limb segments next to its corners."""
    best, best_d = None, None
    for b in bones:
        if b["name"].lower() in skip:  # skip names are lowercase: mannequin "root" and generic "Bone_Root"
            continue
        d = distance_to_segment(point, b["head"], b["tail"]) - b.get("radius", 0.0)
        if best_d is None or d < best_d - 1e-12:
            best, best_d = b["name"], d
    return best


def strip_old_rig(bpy, mesh):
    """Remove any rig the input already carries (armature objects, armature modifiers, vertex groups) so the new
    bind starts clean and the export holds exactly one armature. Takes the bpy module so this file stays importable
    without Blender. Call after joining, before parent=None / transform_apply."""
    for mod in [m for m in mesh.modifiers if m.type == "ARMATURE"]:
        mesh.modifiers.remove(mod)
    mesh.vertex_groups.clear()
    for ob in [o for o in bpy.data.objects if o.type == "ARMATURE"]:
        bpy.data.objects.remove(ob, do_unlink=True)
    for data in [a for a in bpy.data.armatures if a.users == 0]:
        bpy.data.armatures.remove(data)


def renamed(bones, mapping):
    """Copy of the bones with names (and parent links) mapped; names not in the mapping stay unchanged."""
    return [{**b, "name": mapping.get(b["name"], b["name"]),
             "parent": mapping.get(b["parent"], b["parent"]) if b["parent"] else None} for b in bones]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--height", type=float, default=1.8, help="character height in metres")
    args = ap.parse_args(argv)
    bones = layout(args.height)
    problems = validate(bones)
    json.dump({"height": args.height, "bones": bones, "problems": problems}, sys.stdout, indent=1)
    print()
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
