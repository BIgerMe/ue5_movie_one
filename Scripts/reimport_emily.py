import os
import unreal

CONTENT_BASE = "/Game/Characters/Emily"
TEXTURES_CONTENT = CONTENT_BASE + "/Textures"
MASTER_MAT_PATH = CONTENT_BASE + "/M_EmilyUnlit"
FBX_PATH = (
    r"E:\game\epic_assets_down\VaultCache\_Anime_Character_Emily__Free_Dress_Unity_3D_-1d921bb4"
    r"\fbx\anime-characteremily-fre_extracted\source\Emily2_extracted\Emily2\_FBX\Emily.fbx"
)
TEXTURE_SRC = (
    r"E:\game\epic_assets_down\VaultCache\_Anime_Character_Emily__Free_Dress_Unity_3D_-1d921bb4"
    r"\fbx\anime-characteremily-fre_extracted\source\Emily2_extracted\Emily2\Texture"
)
TEXTURES_DISK = r"G:\app\UE_5.8\assets\模型使用\Content\Characters\Emily\Textures"

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

TEXTURE_PARAM_NAME = "BaseColorTex"


def log(msg):
    unreal.log(f"[EmilyReimport] {msg}")


def delete_emily_assets():
    if not unreal.EditorAssetLibrary.does_directory_exist(CONTENT_BASE):
        return
    for asset_path in unreal.EditorAssetLibrary.list_assets(CONTENT_BASE, recursive=True, include_folder=False):
        asset_name = asset_path.split("/")[-1]
        if asset_name in ("Main", "Main.Main"):
            continue
        if unreal.EditorAssetLibrary.delete_asset(asset_path):
            log(f"Deleted: {asset_path}")


def copy_textures_to_disk():
    os.makedirs(TEXTURES_DISK, exist_ok=True)
    skip_patterns = ("_nml", "_spe", "_out", "Shader_", "Matcap_", "Thumbnail")
    copied = 0
    for filename in sorted(os.listdir(TEXTURE_SRC)):
        if not filename.lower().endswith(".png"):
            continue
        if any(p in filename for p in skip_patterns):
            continue
        src = os.path.join(TEXTURE_SRC, filename)
        dst = os.path.join(TEXTURES_DISK, filename)
        with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
            fdst.write(fsrc.read())
        copied += 1
    log(f"Copied {copied} PNG textures")


def ensure_master_material():
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER_MAT_PATH):
        material = unreal.load_asset(MASTER_MAT_PATH + "." + MASTER_MAT_PATH.split("/")[-1])
        log("Reusing existing M_EmilyUnlit master material")
        return material

    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_EmilyUnlit",
        CONTENT_BASE,
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    tex_param = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionTextureSampleParameter2D,
        -300,
        0,
    )
    tex_param.set_editor_property("parameter_name", TEXTURE_PARAM_NAME)
    tex_param.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(
        tex_param, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    log("Created M_EmilyUnlit master material")
    return material


def import_fbx():
    if not os.path.isfile(FBX_PATH):
        raise FileNotFoundError(f"FBX not found: {FBX_PATH}")

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX_PATH)
    task.set_editor_property("destination_path", CONTENT_BASE)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("automated_import_should_detect_type", False)
    task.set_editor_property("options", options)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = task.get_editor_property("imported_object_paths")
    log(f"FBX imported: {paths}")


def import_textures():
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    imported = 0
    for filename in sorted(os.listdir(TEXTURES_DISK)):
        if not filename.lower().endswith(".png"):
            continue
        full_path = os.path.join(TEXTURES_DISK, filename)
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", full_path)
        task.set_editor_property("destination_path", TEXTURES_CONTENT)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)
        task.set_editor_property("replace_existing", True)
        asset_tools.import_asset_tasks([task])
        imported += 1
    log(f"Imported {imported} textures")


def fix_all_materials(master_material):
    fixed = 0
    for mat_name, tex_name in MATERIAL_TEXTURE_MAP.items():
        material = unreal.load_asset(f"{CONTENT_BASE}/{mat_name}.{mat_name}")
        texture = unreal.load_asset(f"{TEXTURES_CONTENT}/{tex_name}.{tex_name}")
        if not material:
            unreal.log_warning(f"Missing material: {mat_name}")
            continue
        if not texture:
            unreal.log_warning(f"Missing texture: {tex_name}")
            continue

        unreal.MaterialEditingLibrary.set_material_instance_parent(material, master_material)
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            material, TEXTURE_PARAM_NAME, texture
        )
        unreal.MaterialEditingLibrary.update_material_instance(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
        fixed += 1
        log(f"Fixed {mat_name} -> {tex_name}")

    return fixed


log("=== Emily full reimport start ===")
delete_emily_assets()
copy_textures_to_disk()
master = ensure_master_material()
import_fbx()
import_textures()
fixed_count = fix_all_materials(master)
log(f"=== Emily full reimport done: {fixed_count}/15 materials ===")
