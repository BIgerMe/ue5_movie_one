import os
import unreal

CONTENT_BASE = "/Game/Characters/Emily"
TEXTURES_DIR = r"G:\app\UE_5.8\assets\模型使用\Content\Characters\Emily\Textures"

MATERIAL_TEXTURE_MAP = {
    "F00_000_00_EyeExtra_01_EYE": "F00_000_00_EyeExtra_01",
    "F00_000_00_EyeHighlight_00_EYE": "F00_000_EyeHighlight_00",
    "F00_000_00_EyeIris_00_EYE": "F00_000_EyeIris_00",
    "F00_000_00_EyeWhite_00_EYE": "F00_000_EyeWhite_00",
    "F00_000_00_FaceBrow_00_FACE": "F00_000_FaceBrow_00",
    "F00_000_00_FaceEyelash_00_FACE": "F00_000_FaceEyelash_00",
    "F00_000_00_FaceEyeline_00_FACE": "F00_000_FaceEyeline_00",
    "F00_000_00_FaceMouth_00_FACE": "F00_000_FaceMouth_00",
    "F00_000_00_Face_00_SKIN": "F00_000_Face_00",
    "F00_000_HairBack_00_HAIR": "F00_000_HairBack_00",
    "F00_000_Hair_00_HAIR_01": "F00_000_Hair_00_01",
    "F00_000_Hair_00_HAIR_02": "F00_000_Hair_00_02",
    "F00_002_02_Body_00_SKIN": "F00_002_02_Body_00",
    "F00_002_03_Tops_01_CLOTH": "F00_002_03_Tops_01",
    "F00_004_01_Shoes_01_CLOTH": "F00_004_01_Shoes_01",
}


def import_textures():
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    for filename in sorted(os.listdir(TEXTURES_DIR)):
        if not filename.lower().endswith(".png"):
            continue
        full_path = os.path.join(TEXTURES_DIR, filename)
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", full_path)
        task.set_editor_property("destination_path", CONTENT_BASE + "/Textures")
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)
        task.set_editor_property("replace_existing", True)
        asset_tools.import_asset_tasks([task])
        paths = task.get_editor_property("imported_object_paths")
        unreal.log(f"Imported texture {filename}: {paths}")


def set_texture_on_material(material, texture):
    param_names = unreal.MaterialEditingLibrary.get_texture_parameter_names(material)
    unreal.log(f"  Params on {material.get_name()}: {list(param_names)}")

    candidates = ["DiffuseColorMap", "BaseColorTexture", "Texture", "DiffuseTexture", "BaseColor", "Albedo"]
    for name in candidates:
        if name in [str(p) for p in param_names]:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(material, name, texture)
            return True

    if len(param_names) > 0:
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(material, str(param_names[0]), texture)
        return True

    parent = unreal.load_asset("/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial")
    if parent:
        unreal.MaterialEditingLibrary.set_material_instance_parent(material, parent)
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(material, "Texture", texture)
        return True

    return False


def fix_materials():
    fixed = 0
    for mat_name, tex_name in MATERIAL_TEXTURE_MAP.items():
        material = unreal.load_asset(f"{CONTENT_BASE}/{mat_name}.{mat_name}")
        texture = unreal.load_asset(f"{CONTENT_BASE}/Textures/{tex_name}.{tex_name}")
        if not material:
            unreal.log_warning(f"Missing material: {mat_name}")
            continue
        if not texture:
            unreal.log_warning(f"Missing texture: {tex_name}")
            continue
        if set_texture_on_material(material, texture):
            unreal.MaterialEditingLibrary.update_material_instance(material)
            unreal.EditorAssetLibrary.save_loaded_asset(material)
            fixed += 1
            unreal.log(f"Fixed material: {mat_name} -> {tex_name}")
    return fixed


unreal.log("=== Emily material fix start ===")
import_textures()
fixed_count = fix_materials()
unreal.log(f"=== Emily material fix done: {fixed_count} materials ===")
