import bpy, sys, math
from mathutils import Vector
glb, out = sys.argv[sys.argv.index("--")+1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs=[o for o in bpy.context.scene.objects if o.type=="MESH"]
mn=Vector((1e9,)*3); mx=Vector((-1e9,)*3)
for o in objs:
    for c in o.bound_box:
        w=o.matrix_world@Vector(c)
        mn=Vector(map(min,mn,w)); mx=Vector(map(max,mx,w))
ctr=(mn+mx)/2; size=max(mx-mn)
sc=bpy.context.scene
w=bpy.data.worlds.new("w"); w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.8,0.8,0.82,1); w.node_tree.nodes["Background"].inputs[1].default_value=1.0
sc.world=w
cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.lens=60
sun=bpy.data.objects.new("s",bpy.data.lights.new("s","SUN")); sun.data.energy=3
sun.rotation_euler=(math.radians(50),0,math.radians(30)); sc.collection.objects.link(sun)
sc.render.engine="CYCLES"; sc.cycles.device="CPU"; sc.cycles.samples=24
sc.render.resolution_x=sc.render.resolution_y=800
views=[("a",35),("b",145),("c",250)]
import os
for n,az in views:
    d=size*3.2; a=math.radians(az); el=math.radians(25)
    cam.location=ctr+Vector((d*math.cos(el)*math.sin(a),-d*math.cos(el)*math.cos(a),d*math.sin(el)))
    cam.rotation_euler=(ctr-cam.location).to_track_quat("-Z","Y").to_euler()
    sc.render.filepath=out+f"_{n}.png"; bpy.ops.render.render(write_still=True)
