import unreal

mesh = unreal.load_asset("/Game/Characters/Nami/Nami_rigged_all.Nami_rigged_all")
if mesh:
    mats = mesh.get_editor_property("materials")
    unreal.log(f"slots={len(mats)}")
    for i, m in enumerate(mats):
        slot = m.get_editor_property("material_slot_name")
        mi = m.get_editor_property("material_interface")
        unreal.log(f"  [{i}] slot={slot} mat={mi.get_name() if mi else None}")
