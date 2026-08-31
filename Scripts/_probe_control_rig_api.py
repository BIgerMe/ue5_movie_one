import unreal

mesh = unreal.load_asset("/Game/Characters/Nami/body1.body1")
factory = unreal.ControlRigBlueprintFactory()
methods = [m for m in dir(factory) if not m.startswith("_")]
unreal.log("Factory methods: " + ", ".join(methods[:40]))

if hasattr(factory, "create_control_rig_from_skeletal_mesh_or_skeleton"):
    cr = factory.create_control_rig_from_skeletal_mesh_or_skeleton(mesh, False)
    unreal.log(f"Created CR: {cr.get_path_name() if cr else None}")
