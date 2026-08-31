import unreal

mesh = unreal.load_asset("/Game/Characters/Nami/Standing/body.body")
if mesh:
    b = mesh.get_bounding_box()
    mn, mx = b.min, b.max
    unreal.log(f"Standing/body bounds min={mn} max={mx} height_z={mx.z - mn.z}")
else:
    unreal.log_error("Standing/body not found")

sk = unreal.load_asset("/Game/Characters/Nami/body1.body1")
if sk:
    b = sk.get_bounding_box()
    unreal.log(f"body1 skeletal bounds min={b.min} max={b.max} height_z={b.max.z - b.min.z}")
