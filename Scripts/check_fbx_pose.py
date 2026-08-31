import bpy

fbx = r"E:\game\epic_assets_other\nami\Nami+OP.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
for obj in sorted(bpy.data.objects, key=lambda o: o.name):
    if obj.type == "MESH":
        vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
        zs = [v.z for v in vs]
        print("mesh", obj.name, "z", round(min(zs), 3), round(max(zs), 3), "h", round(max(zs) - min(zs), 3))
