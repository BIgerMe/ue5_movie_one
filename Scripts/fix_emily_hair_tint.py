import unreal

CONTENT_BASE = "/Game/Characters/Emily"
TINT_PARAM = "TintColor"

# Stronger purple: lower green channel, keep high blue/magenta
HAIR_TINTS = {
    "F00_000_Hair_00_HAIR_01": unreal.LinearColor(1.0, 0.68, 1.0, 1.0),
    "F00_000_HairBack_00_HAIR": unreal.LinearColor(1.0, 0.60, 1.0, 1.0),
    "F00_000_Hair_00_HAIR_02": unreal.LinearColor(0.95, 0.65, 1.0, 1.0),
}


def log(msg):
    unreal.log(f"[EmilyHair] {msg}")


log("=== Emily hair tint adjust ===")
mel = unreal.MaterialEditingLibrary
for mat_name, tint in HAIR_TINTS.items():
    material = unreal.load_asset(f"{CONTENT_BASE}/{mat_name}.{mat_name}")
    if not material:
        unreal.log_warning(f"Missing: {mat_name}")
        continue
    mel.set_material_instance_vector_parameter_value(material, TINT_PARAM, tint)
    mel.update_material_instance(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    log(f"{mat_name} tint -> ({tint.r:.2f}, {tint.g:.2f}, {tint.b:.2f})")

log("=== Done ===")
