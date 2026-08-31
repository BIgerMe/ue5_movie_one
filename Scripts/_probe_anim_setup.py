import unreal

mesh = unreal.load_asset("/Game/Characters/Nami/body1.body1")
props = [p for p in dir(mesh) if "anim" in p.lower() or "post" in p.lower() or "rig" in p.lower()]
unreal.log("mesh props: " + ", ".join(props[:30]))

abp_path = "/Game/Free_Magic/Demo/Characters/Mannequins/Rigs/ABP_Manny_PostProcess.ABP_Manny_PostProcess"
abp = unreal.load_asset(abp_path)
unreal.log(f"PostProcess ABP class: {abp.get_class().get_name() if abp else None}")
if abp:
    unreal.log(f"Generated: {abp.get_class().get_path_name()}")

cr = unreal.load_asset("/Game/Free_Magic/Demo/Characters/Mannequins/Rigs/CR_Mannequin_Procedural.CR_Mannequin_Procedural")
if cr:
    keys = cr.hierarchy.get_all_keys()
    unreal.log(f"CR_Mannequin elements: {len(keys)}")
