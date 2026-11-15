"""Procedural low-poly wooden props -> GLB. Run:
  blender -b -P procedural_props.py -- OUT_DIR [--only crate|barrel|fence|character]
Origin bottom-centre, 1 unit = 1 m, one material, 1024px baked atlas embedded.
Atlas: V 0.25..1 = wood grain (grain along U); V<0.25: left = metal band, right = nail iron.
character: fallback placeholder person (no atlas): three flat-colour materials (skin, shirt, trousers),
origin at the feet, facing +X. Options: --skin/--shirt/--trousers '#RRGGBB', --height METRES."""
import bpy, bmesh, sys, os, math, random, argparse, re
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--only", choices=["crate", "barrel", "fence", "character"])
ap.add_argument("--skin", default="#E0AC85", help="character skin colour #RRGGBB")
ap.add_argument("--shirt", default="#D9382B", help="character shirt colour #RRGGBB")
ap.add_argument("--trousers", default="#2B4A8C", help="character trousers colour #RRGGBB")
ap.add_argument("--height", type=float, default=1.7, help="character height in metres")
args = ap.parse_args(argv)
for _opt in ("skin", "shirt", "trousers"):  # strict: int(x, 16) alone would accept signs and spaces
    if not re.fullmatch(r"#?[0-9A-Fa-f]{6}", getattr(args, _opt)):
        raise SystemExit(f"bad --{_opt} {getattr(args, _opt)!r}: want #RRGGBB")
if not (0.3 <= args.height <= 5.0):  # also rejects nan; catches cm / Unreal units by mistake
    raise SystemExit(f"bad --height {args.height!r}: want metres between 0.3 and 5.0")
OUT = args.out
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- texture
def vnoise(H, W, fy, fx, rng):
    g = rng.random((int(H * fy) + 3, int(W * fx) + 3))
    ys = np.arange(H) * fy; xs = np.arange(W) * fx
    y0 = ys.astype(int); x0 = xs.astype(int)
    ty = ys - y0; tx = xs - x0
    ty = ty * ty * (3 - 2 * ty); tx = tx * tx * (3 - 2 * tx)
    a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
    TX = tx[None, :]; TY = ty[:, None]
    return (a * (1 - TX) + b * TX) * (1 - TY) + (c * (1 - TX) + d * TX) * TY

def fbm(H, W, fy, fx, rng, octs=4):
    s = 0; amp = 1; tot = 0
    for _ in range(octs):
        s = s + amp * vnoise(H, W, fy, fx, rng); tot += amp
        fy *= 2; fx *= 2; amp *= 0.5
    return s / tot

def make_atlas(seed, dark, light):
    rng = np.random.default_rng(seed)
    N = 1024; H = 768
    yy = np.arange(H)[:, None] * np.ones((1, N)); xx = np.ones((H, 1)) * np.arange(N)[None, :]
    phase = (yy + fbm(H, N, 1 / 90, 1 / 500, rng, 4) * 110) 
    kn = np.zeros((H, N))
    for _ in range(5):
        cx = rng.uniform(0, N); cy = rng.uniform(40, H - 40)
        d2 = ((xx - cx) / 70) ** 2 + ((yy - cy) / 18) ** 2
        phase = phase + 40 * np.exp(-d2); kn += np.exp(-d2 * 2.2)
    period = 40
    rings = 0.5 + 0.5 * np.sin(phase / period * 2 * math.pi)
    streak = fbm(H, N, 1 / 1.6, 1 / 260, rng, 3)
    low = fbm(H, N, 1 / 200, 1 / 300, rng, 2)
    t = np.clip(0.30 * rings ** 1.4 + 0.45 * streak + 0.25 * low, 0, 1)
    t = np.clip((t - 0.15) * 1.35, 0, 1)
    t = np.floor(t * 9) / 9 * 0.35 + t * 0.65   # light posterize, stylized
    t = np.clip(t - 0.35 * np.clip(kn, 0, 1), 0, 1)
    dark = np.array(dark); light = np.array(light)
    wood = dark[None, None, :] * (1 - t[..., None]) + light[None, None, :] * t[..., None]
    img = np.ones((N, N, 4))
    img[256:, :, :3] = wood
    m = fbm(256, 512, 1 / 3, 1 / 60, rng, 3)
    img[:256, :512, :3] = (np.array([0.30, 0.31, 0.34]) * (0.85 + 0.3 * m[..., None]))
    img[:256, 512:, :3] = (np.array([0.13, 0.125, 0.13]) * (0.85 + 0.3 * m[..., None]))
    return np.clip(img, 0, 1)

def make_material(name, seed, dark, light):
    arr = make_atlas(seed, dark, light)
    img = bpy.data.images.new(f"{name}_atlas", 1024, 1024, alpha=False)
    img.pixels.foreach_set(arr.astype(np.float32).ravel())
    path = os.path.join(OUT, f"{name}_atlas.png")
    img.filepath_raw = path; img.file_format = "PNG"; img.save()
    mat = bpy.data.materials.new(f"{name}_mat"); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Metallic"].default_value = 0.0
    return mat

# ---------------------------------------------------------------- geometry accumulation
SU = 1 / 2.4                     # texture fraction per metre
U0, UW, V0, VH = 0.01, 0.98, 0.26, 0.73
METAL_UV = (0.25, 0.1); NAIL_UV = (0.75, 0.1)

class Acc:
    def __init__(self): self.V = []; self.F = []; self.UV = []
    def add(self, V, F, UV, M):
        b = len(self.V)
        self.V += [tuple(M @ Vector(v)) for v in V]
        self.F += [[b + i for i in f] for f in F]
        self.UV += UV

def fit(uvl, rng):
    pts = [p for f in uvl for p in f]
    us = [p[0] for p in pts]; vs = [p[1] for p in pts]
    eu = (max(us) - min(us)) * SU; ev = (max(vs) - min(vs)) * SU
    s = min(1.0, UW / max(eu, 1e-6), VH / max(ev, 1e-6))
    ou = rng.random() * max(0, UW - eu * s); ov = rng.random() * max(0, VH - ev * s)
    return [[(U0 + (u - min(us)) * SU * s + ou, V0 + (v - min(vs)) * SU * s + ov) for u, v in f] for f in uvl]

def const_uv(F, uv): return [[uv] * len(f) for f in F]

def bm_geom(bm, bev, seg=1):
    if bev > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bev, segments=seg, affect='EDGES', profile=0.5, offset_type='OFFSET')
    bm.normal_update(); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    V = [tuple(v.co) for v in bm.verts]
    F = [[v.index for v in f.verts] for f in bm.faces]
    N = [tuple(f.normal) for f in bm.faces]
    bm.free()
    return V, F, N

def wood_uv(V, F, N, g):
    out = []
    for f, n in zip(F, N):
        dom = max(range(3), key=lambda i: abs(n[i]))
        others = [i for i in range(3) if i != g]
        if dom == g: a, b = others
        else: a, b = g, [i for i in range(3) if i not in (g, dom)][0]
        out.append([(V[i][a], V[i][b]) for i in f])
    return out

def add_geom(acc, V, F, N, mat, g, M, rng):
    if mat == 'wood': UV = fit(wood_uv(V, F, N, g), rng)
    elif mat == 'metal': UV = const_uv(F, METAL_UV)
    else: UV = const_uv(F, NAIL_UV)
    acc.add(V, F, UV, M)

def add_box(acc, rng, center, size, g=0, bev=0.008, mat='wood', M=None, seg=1):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    V, F, N = bm_geom(bm, min(bev, min(size) * 0.4), seg)
    T = Matrix.Translation(center) @ (M if M is not None else Matrix.Identity(4))
    add_geom(acc, V, F, N, mat, g, T, rng)

def add_prism(acc, rng, center, profile, t, bev=0.004, g=2):
    """profile: list of (x,z) outline; extruded along y (thickness t)."""
    bm = bmesh.new()
    fr = [bm.verts.new((x, -t / 2, z)) for x, z in profile]
    bk = [bm.verts.new((x, t / 2, z)) for x, z in profile]
    bm.faces.new(fr[::-1]); bm.faces.new(bk)
    n = len(profile)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((fr[i], fr[j], bk[j], bk[i]))
    V, F, N = bm_geom(bm, bev, 1)
    add_geom(acc, V, F, N, 'wood', g, Matrix.Translation(center), rng)

def add_nail(acc, pos, direction, r=0.012, h=0.007, mat='nail'):
    segs = 6
    V = [(r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), 0) for i in range(segs)]
    V += [(0.78 * r * math.cos(2 * math.pi * i / segs), 0.78 * r * math.sin(2 * math.pi * i / segs), h) for i in range(segs)]
    F = [[i, (i + 1) % segs, segs + (i + 1) % segs, segs + i] for i in range(segs)] + [list(range(segs, 2 * segs))]
    R = Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized()).to_matrix().to_4x4()
    acc.add(V, F, const_uv(F, NAIL_UV), Matrix.Translation(pos) @ R)

def basis(ex, ey, ez):
    m = Matrix.Identity(4)
    for i, v in enumerate((ex, ey, ez)):
        m[0][i], m[1][i], m[2][i] = v[0], v[1], v[2]
    return m

# ---------------------------------------------------------------- crate
def build_crate(rng):
    acc = Acc(); S = 0.8; p = 0.08; H = 0.8; off = S / 2 - p / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(acc, rng, (sx * off, sy * off, H / 2), (p, p, H), g=2, bev=0.01)
    add_box(acc, rng, (0, 0, 0.025), (S - 0.04, S - 0.04, 0.03), g=0, bev=0.004)
    # lid: 4 planks along x
    gap = 0.012; w = (S - 3 * gap) / 4
    for i in range(4):
        y = -S / 2 + w / 2 + i * (w + gap)
        add_box(acc, rng, (0, y, H + 0.015), (S, w, 0.03), g=0, bev=0.006)
    # side planks (horizontal) + diagonal brace + nails
    z0, z1, pg = 0.04, 0.79, 0.008; ph = (z1 - z0 - 3 * pg) / 4
    for k, n in enumerate([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]):
        n = Vector(n); t = Vector((-n.y, n.x, 0)); up = Vector((0, 0, 1))
        for i in range(4):
            z = z0 + ph / 2 + i * (ph + pg)
            c = n * 0.365 + Vector((0, 0, z))
            size = (0.03, 0.655, ph) if abs(n.x) > 0 else (0.655, 0.03, ph)
            add_box(acc, rng, c, size, g=1 if abs(n.x) > 0 else 0, bev=0.006)
        a = math.atan2(z1 - z0, 0.64) * (1 if k % 2 == 0 else -1)
        d = t * math.cos(a) + up * math.sin(a)
        ez = n; ey = ez.cross(d)
        ctr = n * 0.39 + Vector((0, 0, (z0 + z1) / 2))
        add_box(acc, rng, ctr, (0.9, 0.075, 0.02), g=0, bev=0.005, M=basis(d, ey, ez))
        for e in (-1, 1):
            for lat in (-0.012, 0.012):
                pos = ctr + d * (e * 0.4) + ey * lat + n * 0.01
                add_nail(acc, pos, n)
    return acc

# ---------------------------------------------------------------- barrel
def build_barrel(rng):
    acc = Acc(); H = 0.9; N = 12; Rm = 0.36; Re = 0.30; T = 0.035; nz = 6
    prof = lambda h: Re + (Rm - Re) * (1 - (2 * h / H) ** 2)
    hs = [-H / 2 + H * k / nz for k in range(nz + 1)]
    hw = math.pi / N * 0.965; ca = 0.02
    for s in range(N):
        a = 2 * math.pi * (s + 0.5) / N
        V = []; UV = []; F = []
        sec = [(-hw + ca, 0, 1), (hw - ca, 0, 1), (hw, -0.008, 1), (hw, 0, 0), (-hw, 0, 0), (-hw, -0.008, 1)]
        meta = []
        for k, h in enumerate(hs):
            ro = prof(h)
            for (da, dr, outer) in sec:
                r = ro + dr if outer else ro - T
                th = a + da
                V.append((r * math.cos(th), r * math.sin(th), h + H / 2)); meta.append((h + H / 2, da * r, r))
        for k in range(nz):
            for j in range(6):
                j2 = (j + 1) % 6
                F.append([k * 6 + j, k * 6 + j2, (k + 1) * 6 + j2, (k + 1) * 6 + j])
                radial_face = j in (2, 4)
                uvf = []
                for idx in F[-1]:
                    z, lat, r = meta[idx]
                    uvf.append((z, r if radial_face else lat))
                UV.append(uvf)
        for kk in (0, nz):
            F.append([kk * 6 + j for j in range(6)])
            UV.append([(meta[kk * 6 + j][1], meta[kk * 6 + j][2]) for j in range(6)])
        acc.add(V, F, fit(UV, rng), Matrix.Identity(4))
    # lids
    def disc(zc, r, th):
        sg = 24; V = [(r * math.cos(2 * math.pi * i / sg), r * math.sin(2 * math.pi * i / sg), zc + dz) for dz in (-th / 2, th / 2) for i in range(sg)]
        F = [[i, (i + 1) % sg, sg + (i + 1) % sg, sg + i] for i in range(sg)] + [list(range(sg - 1, -1, -1)), list(range(sg, 2 * sg))]
        UV = [[(V[i][0], V[i][1]) if f == F[-1] or f == F[-2] else (V[i][0] * 3, V[i][2]) for i in f] for f in F]
        acc.add(V, F, fit(UV, rng), Matrix.Identity(4))
    rl = (Re - T) * math.cos(math.pi / N) - 0.004
    disc(H - 0.08, rl, 0.03); disc(0.05, rl, 0.03)
    # hoops
    for hz, wd in ((0.07, 0.055), (0.25, 0.045), (0.65, 0.045), (0.83, 0.055)):
        hc = hz - H / 2
        rr = max(prof(hc - wd / 2), prof(hc), prof(hc + wd / 2)) + 0.001
        ri, ro = rr, rr + 0.016; sg = 20
        z0, z1 = hz - wd / 2, hz + wd / 2
        V = []; 
        for i in range(sg):
            c, s_ = math.cos(2 * math.pi * i / sg), math.sin(2 * math.pi * i / sg)
            for r, z in ((ri, z0), (ro, z0), (ro, z1), (ri, z1)): V.append((r * c, r * s_, z))
        F = [[i * 4 + j, i * 4 + (j + 1) % 4, ((i + 1) % sg) * 4 + (j + 1) % 4, ((i + 1) % sg) * 4 + j] for i in range(sg) for j in range(4)]
        acc.add(V, F, const_uv(F, METAL_UV), Matrix.Identity(4))
    return acc

# ---------------------------------------------------------------- fence
def build_fence(rng):
    acc = Acc(); px = 1.0; ph = 1.25; pw = 0.1
    for sx in (-1, 1):
        add_box(acc, rng, (sx * px, 0, ph / 2), (pw, pw, ph), g=2, bev=0.012)
        add_box(acc, rng, (sx * px, 0, ph + 0.015), (pw + 0.03, pw + 0.03, 0.03), g=0, bev=0.01)
    rails = (0.38, 0.88)
    for z in rails:
        add_box(acc, rng, (0, 0, z), (1.92, 0.04, 0.09), g=0, bev=0.007)
    n = 10; w = 0.12; span = 2 * px - pw; gap = (span - n * w) / (n + 1); t = 0.025; y = -0.0325
    for i in range(n):
        x = -span / 2 + gap + w / 2 + i * (w + gap)
        top = 1.05 + rng.uniform(-0.025, 0.025); z0 = 0.06
        prof_ = [(-w / 2, z0), (w / 2, z0), (w / 2, top - 0.045), (0, top), (-w / 2, top - 0.045)]
        add_prism(acc, rng, (x, y, 0), prof_, t, bev=0.004)
        for z in rails:
            add_nail(acc, (x, y - t / 2, z), (0, -1, 0), r=0.014, h=0.008)
    return acc

# ---------------------------------------------------------------- character (fallback hero)
def hex_to_linear(h):
    h = h.lstrip("#")
    if len(h) != 6: raise SystemExit(f"bad colour {h!r}: want #RRGGBB")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]

def build_character(height):
    """Chunky stylised person from bevelled boxes. +X is forward, origin at the feet.
    Returns (verts, faces, face_material_index). Material 0=skin 1=shirt 2=trousers."""
    H = height; V = []; F = []; MI = []
    def box(cx, cy, z0, z1, sx, sy, mi, bev=0.012):
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * sx * H, v.co.y * sy * H, v.co.z * (z1 - z0) * H))
        vv, ff, _ = bm_geom(bm, min(bev * H, min(sx * H, sy * H, (z1 - z0) * H) * 0.3), 1)
        b = len(V); off = Vector((cx * H, cy * H, (z0 + z1) / 2 * H))
        V.extend(tuple(Vector(v) + off) for v in vv)
        for f in ff: F.append([b + i for i in f]); MI.append(mi)
    for s in (-1, 1):
        box(0.01, s * 0.065, 0.00, 0.045, 0.16, 0.11, 2)        # shoes, toe forward
        box(0, s * 0.065, 0.045, 0.46, 0.11, 0.105, 2)           # legs
        box(0, s * 0.215, 0.46, 0.74, 0.085, 0.085, 1)           # sleeves/arms (gap to torso)
        box(0, s * 0.215, 0.405, 0.46, 0.075, 0.075, 0)          # hands
    box(0, 0, 0.44, 0.76, 0.14, 0.30, 1)                         # torso
    box(0, 0, 0.76, 0.80, 0.07, 0.08, 0)                         # neck
    box(0, 0, 0.79, 0.985, 0.20, 0.22, 0, bev=0.025)             # head
    box(-0.015, 0, 0.925, 1.00, 0.215, 0.235, 2, bev=0.02)       # hair cap, trousers colour; tops out at H
    box(0.108, 0, 0.865, 0.905, 0.03, 0.045, 0, bev=0.006)       # nose marks facing +X
    return V, F, MI

def make_character_object(height, skin, shirt, trousers):
    V, F, MI = build_character(height)
    me = bpy.data.meshes.new("character"); me.from_pydata(V, [], F)
    for name, hexc in (("skin", skin), ("shirt", shirt), ("trousers", trousers)):
        m = bpy.data.materials.new(f"character_{name}"); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = hex_to_linear(hexc)
        b.inputs["Roughness"].default_value = 0.9
        me.materials.append(m)
    for p, mi in zip(me.polygons, MI): p.material_index = mi; p.use_smooth = False
    me.update()
    ob = bpy.data.objects.new("character", me); bpy.context.scene.collection.objects.link(ob)
    return ob, V, F

# ---------------------------------------------------------------- finalize + export
def finish(name, acc, mat):
    me = bpy.data.meshes.new(name); me.from_pydata(acc.V, [], acc.F)
    uvl = me.uv_layers.new(name="UVMap")
    li = 0
    for f, uvs in zip(me.polygons, acc.UV):
        for u in uvs:
            uvl.data[li].uv = u; li += 1
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(38))
    bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob

builders = {"crate": (build_crate, 11, (0.33, 0.19, 0.08), (0.72, 0.50, 0.26)),
            "barrel": (build_barrel, 22, (0.24, 0.13, 0.06), (0.58, 0.36, 0.18)),
            "fence": (build_fence, 33, (0.30, 0.25, 0.20), (0.66, 0.58, 0.46))}
for name, (fn, seed, dk, lt) in builders.items():
    if args.only and args.only != name: continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rng = random.Random(seed)
    mat = make_material(name, seed, dk, lt)
    acc = fn(rng)
    ob = finish(name, acc, mat)
    tris = sum(len(f) - 2 for f in acc.F)
    mn = min(v[2] for v in acc.V)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    path = os.path.join(OUT, f"{name}.glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=True)
    xs = [v[0] for v in acc.V]; ys = [v[1] for v in acc.V]; zs = [v[2] for v in acc.V]
    print(f"PROP {name}: tris={tris} verts={len(acc.V)} bbox=({max(xs)-min(xs):.2f} x {max(ys)-min(ys):.2f} x {max(zs)-min(zs):.2f}) m zmin={mn:.3f} -> {path}")

# character: flat colours, no atlas, so it is exported on its own (not part of `builders`)
if args.only in (None, "character"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ob, V, F = make_character_object(args.height, args.skin, args.shirt, args.trousers)
    tris = sum(len(f) - 2 for f in F)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    path = os.path.join(OUT, "character.glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=True)
    xs = [v[0] for v in V]; ys = [v[1] for v in V]; zs = [v[2] for v in V]
    print(f"PROP character: tris={tris} verts={len(V)} bbox=({max(xs)-min(xs):.2f} x {max(ys)-min(ys):.2f} x {max(zs)-min(zs):.2f}) m zmin={min(zs):.3f} -> {path}")
