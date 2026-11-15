"""Usage: blender -b -P cleanup_glb.py -- in.glb out.glb [--min-area 0.03] [--solid] [--voxel 0.012] [--target 8000] [--tex 1024]
Stages: weld -> drop small/thin islands -> (optional) solid voxel remesh -> bake albedo from original -> decimate -> export."""
import bpy, bmesh, sys, math, argparse
from mathutils import Vector
ap=argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("out")
ap.add_argument("--min-area",type=float,default=0.03,help="drop islands below this fraction of the largest island area")
ap.add_argument("--solid",action="store_true"); ap.add_argument("--voxel",type=float,default=0.012)
ap.add_argument("--thicken",type=float,default=0.0,help="solidify thickness (fraction of size) before remesh")
ap.add_argument("--target",type=int,default=8000); ap.add_argument("--tex",type=int,default=1024)
ap.add_argument("--open",type=int,default=0,help="face-graph opening radius: removes ribbons narrower than ~2*N faces")
ap.add_argument("--black-thr",type=float,default=0.10)
ap.add_argument("--spike",type=float,default=0.0,help="delete proxy verts thinner than this fraction of size")
ap.add_argument("--clip",type=float,default=0.0,help="crop to the 2-98 percentile box padded by this fraction (boxy props)")
ap.add_argument("--clip-pct",type=float,default=2.0)
ap.add_argument("--bottom-pct",type=float,default=0.0,help="override the lower Z bound with this percentile (cuts ragged bases)")
ap.add_argument("--fill",action="store_true",help="cap holes left by clipping")
ap.add_argument("--smooth",type=int,default=2)
a=ap.parse_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.inp)
objs=[o for o in bpy.context.scene.objects if o.type=="MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
if len(objs)>1: bpy.ops.object.join()
src=bpy.context.active_object; src.name="src"
size=max(src.dimensions)
# weld + islands
bm=bmesh.new(); bm.from_mesh(src.data)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=size*1e-5)
bm.faces.ensure_lookup_table()
seen=set(); isl=[]
for f in bm.faces:
    if f.index in seen: continue
    st=[f]; seen.add(f.index); fs=[]; ar=0
    while st:
        x=st.pop(); fs.append(x); ar+=x.calc_area()
        for e in x.edges:
            for y in e.link_faces:
                if y.index not in seen: seen.add(y.index); st.append(y)
    isl.append((ar,fs))
big=max(i[0] for i in isl)
kill=[f for ar,fs in isl if ar<big*a.min_area for f in fs]
print("islands",len(isl),"killed faces",len(kill))
bmesh.ops.delete(bm,geom=kill,context="FACES")
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
if a.open>0:
    bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    adj=[[y.index for e in f.edges for y in e.link_faces if y is not f] for f in bm.faces]
    nbd=[sum(1 for e in f.edges if e.is_boundary) for f in bm.faces]
    alive=set(range(len(bm.faces)))
    for _ in range(a.open):
        alive={i for i in alive if nbd[i]==0 and all(j in alive for j in adj[i]) or (nbd[i]>0 and False)}
    core=set(alive)
    # regrow inside original faces
    for _ in range(a.open+1):
        add={j for i in alive for j in adj[i]}
        alive|=add
    dead=[bm.faces[i] for i in range(len(bm.faces)) if i not in alive]
    print("opening kills",len(dead),"core",len(core))
    bmesh.ops.delete(bm,geom=dead,context="FACES")
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
    bm.faces.ensure_lookup_table()
    # keep largest island again
    seen=set(); isl=[]
    for f in bm.faces:
        if f.index in seen: continue
        st=[f]; seen.add(f.index); fs=[]
        while st:
            x=st.pop(); fs.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in seen: seen.add(y.index); st.append(y)
        isl.append(fs)
    isl.sort(key=len,reverse=True)
    bmesh.ops.delete(bm,geom=[f for fs in isl[1:] if len(fs)<len(isl[0])*0.05 for f in fs],context="FACES")
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
bm.to_mesh(src.data); bm.free()
src.data.update()
if not a.solid:
    # light cleanup only
    bm=bmesh.new(); bm.from_mesh(src.data)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(src.data); bm.free()
    work=src
else:
    # solid proxy: thicken shells, voxel remesh, bake colour from src
    proxy=src.copy(); proxy.data=src.data.copy(); proxy.name="proxy"; bpy.context.scene.collection.objects.link(proxy)
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active=proxy; proxy.select_set(True)
    for m in list(proxy.data.materials): pass
    proxy.data.materials.clear()
    if a.thicken>0:
        md=proxy.modifiers.new("sol","SOLIDIFY"); md.thickness=size*a.thicken; md.offset=0; md.use_even_offset=True
        bpy.ops.object.modifier_apply(modifier="sol")
    proxy.data.remesh_voxel_size=size*a.voxel
    bpy.ops.object.voxel_remesh()
    if a.clip!=0:
        import numpy as np
        bm=bmesh.new(); bm.from_mesh(proxy.data)
        P=np.array([v.co[:] for v in bm.verts]); lo=np.percentile(P,a.clip_pct,axis=0); hi=np.percentile(P,100-a.clip_pct,axis=0)
        pad=(hi-lo)*a.clip; lo-=pad; hi+=pad
        if a.bottom_pct>0: lo[2]=np.percentile(P[:,2],a.bottom_pct)
        out=[v for v in bm.verts if any(v.co[i]<lo[i] or v.co[i]>hi[i] for i in range(3))]
        print("clip: verts outside",len(out))
        bmesh.ops.delete(bm,geom=out,context="VERTS")
        bm.faces.ensure_lookup_table(); seen=set(); isl=[]
        for f in bm.faces:
            if f.index in seen: continue
            st=[f]; seen.add(f.index); fs=[]
            while st:
                x=st.pop(); fs.append(x)
                for e in x.edges:
                    for y in e.link_faces:
                        if y.index not in seen: seen.add(y.index); st.append(y)
            isl.append(fs)
        isl.sort(key=len,reverse=True)
        bmesh.ops.delete(bm,geom=[f for fs in isl[1:] for f in fs],context="FACES")
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
        bm.to_mesh(proxy.data); bm.free(); proxy.data.update()
        if a.fill:
            bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.fill_holes(sides=0); bpy.ops.object.mode_set(mode="OBJECT")
    if a.spike>0:
        from mathutils.kdtree import KDTree
        bm=bmesh.new(); bm.from_mesh(proxy.data); bm.verts.ensure_lookup_table()
        kd=KDTree(len(bm.verts))
        for v in bm.verts: kd.insert(v.co,v.index)
        kd.balance(); R=size*a.spike
        cnt=[len(kd.find_range(v.co,R)) for v in bm.verts]
        srt=sorted(cnt); med=srt[len(srt)//2]; thr=med*0.45
        bad=[f for f in bm.faces if sum(1 for v in f.verts if cnt[v.index]<thr)>=2]
        print("spike: median nbrs",med,"thr",thr,"faces",len(bad))
        bmesh.ops.delete(bm,geom=bad,context="FACES")
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
        bm.faces.ensure_lookup_table(); seen=set(); isl=[]
        for f in bm.faces:
            if f.index in seen: continue
            st=[f]; seen.add(f.index); fs=[]
            while st:
                x=st.pop(); fs.append(x)
                for e in x.edges:
                    for y in e.link_faces:
                        if y.index not in seen: seen.add(y.index); st.append(y)
            isl.append(fs)
        isl.sort(key=len,reverse=True)
        bmesh.ops.delete(bm,geom=[f for fs in isl[1:] for f in fs],context="FACES")
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
        bm.to_mesh(proxy.data); bm.free(); proxy.data.update()
    for i in range(a.smooth):
        md=proxy.modifiers.new("sm","CORRECTIVE_SMOOTH"); 
        bpy.ops.object.modifier_apply(modifier="sm")
    if a.target:
        md=proxy.modifiers.new("dec","DECIMATE"); md.ratio=min(1.0,a.target/max(1,len(proxy.data.polygons)))
        bpy.ops.object.modifier_apply(modifier="dec")
    # UV
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
    img=bpy.data.images.new("alb",a.tex,a.tex)
    mat=bpy.data.materials.new("Crate"); mat.use_nodes=True; nt=mat.node_tree
    tn=nt.nodes.new("ShaderNodeTexImage"); tn.image=img; nt.nodes.active=tn
    nt.links.new(tn.outputs[0],nt.nodes["Principled BSDF"].inputs["Base Color"])
    proxy.data.materials.append(mat)
    sc=bpy.context.scene; sc.render.engine="CYCLES"; sc.cycles.device="CPU"; sc.cycles.samples=1
    sc.render.bake.use_selected_to_active=True; sc.render.bake.cage_extrusion=size*0.05; sc.render.bake.max_ray_distance=size*0.08
    sc.render.bake.margin=16; sc.render.bake.use_pass_direct=False; sc.render.bake.use_pass_indirect=False
    bpy.ops.object.select_all(action="DESELECT"); src.select_set(True); proxy.select_set(True)
    bpy.context.view_layer.objects.active=proxy
    # heal near-black (unbaked) texels in the source albedo by iterative neighbour fill
    import numpy as np
    for m in src.data.materials:
        for n in (m.node_tree.nodes if m and m.use_nodes else []):
            if n.type=="TEX_IMAGE" and n.image:
                im=n.image; w,h=im.size; px=np.array(im.pixels[:],dtype=np.float32).reshape(h,w,4)
                bad=px[...,:3].max(axis=2)<a.black_thr
                print("black texels",int(bad.sum()),"of",w*h)
                good=~bad; rgb=px[...,:3].copy()
                for it in range(60):
                    if good.all(): break
                    acc=np.zeros_like(rgb); cnt=np.zeros((h,w),np.float32)
                    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
                        g=np.roll(good,(dy,dx),(0,1)); c=np.roll(rgb,(dy,dx),(0,1))
                        acc+=c*g[...,None]; cnt+=g
                    fill=(~good)&(cnt>0)
                    rgb[fill]=acc[fill]/cnt[fill][:,None]; good|=fill
                px[...,:3]=rgb; im.pixels[:]=px.ravel(); im.update()
    # make src emissive-free: bake DIFFUSE colour from its base-colour texture
    bpy.ops.object.bake(type="DIFFUSE",pass_filter={"COLOR"})
    bpy.data.objects.remove(src)
    work=proxy
    for p in work.data.polygons: p.use_smooth=True
bpy.ops.object.select_all(action="DESELECT"); work.select_set(True)
bpy.ops.export_scene.gltf(filepath=a.out,export_format="GLB",use_selection=True,export_image_format="JPEG" if False else "AUTO")
print("RESULT verts",len(work.data.vertices),"faces",len(work.data.polygons))
