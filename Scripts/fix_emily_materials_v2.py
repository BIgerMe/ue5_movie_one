import unreal

CONTENT_BASE = "/Game/Characters/Emily"
TEXTURES_CONTENT = CONTENT_BASE + "/Textures"

TINT_PARAM = "TintColor"
TEX_PARAM = "BaseColorTex"

MASTER_LIT = CONTENT_BASE + "/M_EmilyLit"
MASTER_TRANSLUCENT = CONTENT_BASE + "/M_EmilyTranslucent"
MASTER_MASKED = CONTENT_BASE + "/M_EmilyMasked"

# Unity _Color tint + blend mode from source .mat files
MATERIAL_CONFIG = {
    "F00_000_00_Face_00_SKIN": {"tex": "F00_000_Face_00", "master": "lit", "tint": (0.8, 0.8, 0.8, 1.0)},
    "F00_002_02_Body_00_SKIN": {"tex": "F00_002_02_Body_00", "master": "lit", "tint": (0.8, 0.8, 0.8, 1.0)},
    "F00_000_Hair_00_HAIR_01": {"tex": "F00_000_Hair_00_01", "master": "lit", "tint": (1.0, 0.68, 1.0, 1.0), "two_sided": True},
    "F00_000_HairBack_00_HAIR": {"tex": "F00_000_HairBack_00", "master": "masked", "tint": (1.0, 0.60, 1.0, 1.0), "two_sided": True},
    "F00_000_Hair_00_HAIR_02": {"tex": "F00_000_Hair_00_02", "master": "translucent", "tint": (0.95, 0.65, 1.0, 1.0), "two_sided": True},
    "F00_002_03_Tops_01_CLOTH": {"tex": "F00_002_03_Tops_01", "master": "translucent", "tint": (1.0, 1.0, 1.0, 1.0), "two_sided": True, "opacity_scale": 0.95},
    "F00_004_01_Shoes_01_CLOTH": {"tex": "F00_004_01_Shoes_01", "master": "masked", "tint": (0.8, 0.8, 0.8, 1.0)},
    "F00_000_00_FaceEyeline_00_FACE": {"tex": "F00_000_FaceEyeline_00", "master": "translucent", "tint": (0.0, 0.0, 0.0, 1.0)},
    "F00_000_00_FaceEyelash_00_FACE": {"tex": "F00_000_FaceEyelash_00", "master": "translucent", "tint": (0.0, 0.0, 0.0, 1.0)},
    "F00_000_00_FaceBrow_00_FACE": {"tex": "F00_000_FaceBrow_00", "master": "translucent", "tint": (0.769, 0.282, 0.868, 1.0)},
    "F00_000_00_FaceMouth_00_FACE": {"tex": "F00_000_FaceMouth_00", "master": "lit", "tint": (0.8, 0.8, 0.8, 1.0)},
    "F00_000_00_EyeIris_00_EYE": {"tex": "F00_000_EyeIris_00", "master": "translucent", "tint": (0.8, 0.8, 0.8, 1.0)},
    "F00_000_00_EyeHighlight_00_EYE": {"tex": "F00_000_EyeHighlight_00", "master": "translucent", "tint": (0.8, 0.8, 0.8, 1.0)},
    "F00_000_00_EyeWhite_00_EYE": {"tex": "F00_000_EyeWhite_00", "master": "lit", "tint": (0.8, 0.8, 0.8, 1.0)},
    "F00_000_00_EyeExtra_01_EYE": {"tex": "F00_000_00_EyeExtra_01", "master": "lit", "tint": (0.8, 0.8, 0.8, 1.0)},
}


def log(msg):
    unreal.log(f"[EmilyMatV2] {msg}")


def _connect_tinted_texture(material, use_alpha_as_opacity=False):
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)

    tex = mel.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -500, 0
    )
    tex.set_editor_property("parameter_name", TEX_PARAM)
    tex.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)

    tint = mel.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -500, 220
    )
    tint.set_editor_property("parameter_name", TINT_PARAM)
    tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))

    multiply = mel.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -250, 80
    )
    mel.connect_material_expressions(tex, "", multiply, "A")
    mel.connect_material_expressions(tint, "", multiply, "B")
    mel.connect_material_property(multiply, "", unreal.MaterialProperty.MP_BASE_COLOR)

    rough = mel.create_material_expression(
        material, unreal.MaterialExpressionConstant, -250, 300
    )
    rough.set_editor_property("r", 0.85)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    spec = mel.create_material_expression(
        material, unreal.MaterialExpressionConstant, -250, 400
    )
    spec.set_editor_property("r", 0.1)
    mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)

    if use_alpha_as_opacity:
        mel.connect_material_property(tex, "A", unreal.MaterialProperty.MP_OPACITY)


def ensure_master_material(asset_path, blend_mode, use_alpha):
    asset_name = asset_path.split("/")[-1]
    material = None
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        material = unreal.load_asset(f"{asset_path}.{asset_name}")
        log(f"Updating master material {asset_name}")
    else:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name, CONTENT_BASE, unreal.Material, unreal.MaterialFactoryNew()
        )
        log(f"Created master material {asset_name}")

    material.set_editor_property("blend_mode", blend_mode)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    _connect_tinted_texture(material, use_alpha_as_opacity=use_alpha)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def ensure_masters():
    masters = {
        "lit": ensure_master_material(
            MASTER_LIT, unreal.BlendMode.BLEND_OPAQUE, use_alpha=False
        ),
        "translucent": ensure_master_material(
            MASTER_TRANSLUCENT, unreal.BlendMode.BLEND_TRANSLUCENT, use_alpha=True
        ),
        "masked": ensure_master_material(
            MASTER_MASKED, unreal.BlendMode.BLEND_MASKED, use_alpha=True
        ),
    }
    return masters


def apply_material_instance(mat_name, cfg, masters):
    material = unreal.load_asset(f"{CONTENT_BASE}/{mat_name}.{mat_name}")
    texture = unreal.load_asset(f"{TEXTURES_CONTENT}/{cfg['tex']}.{cfg['tex']}")
    if not material or not texture:
        unreal.log_warning(f"Skip missing: mat={mat_name} tex={cfg.get('tex')}")
        return False

    master = masters[cfg["master"]]
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_parent(material, master)
    mel.set_material_instance_texture_parameter_value(material, TEX_PARAM, texture)
    tint = unreal.LinearColor(cfg["tint"][0], cfg["tint"][1], cfg["tint"][2], cfg["tint"][3])
    mel.set_material_instance_vector_parameter_value(material, TINT_PARAM, tint)

    if cfg.get("two_sided"):
        overrides = material.get_editor_property("base_property_overrides")
        overrides.set_editor_property("override_two_sided", True)
        overrides.set_editor_property("two_sided", True)
        material.set_editor_property("base_property_overrides", overrides)

    mel.update_material_instance(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return True


# Remove old emissive-only master that washed out colors
old_unlit = CONTENT_BASE + "/M_EmilyUnlit"
if unreal.EditorAssetLibrary.does_asset_exist(old_unlit):
    unreal.EditorAssetLibrary.delete_asset(old_unlit)
    log("Removed old M_EmilyUnlit")

log("=== Emily material v2 fix start ===")
master_materials = ensure_masters()
fixed = 0
for mat_name, cfg in MATERIAL_CONFIG.items():
    if apply_material_instance(mat_name, cfg, master_materials):
        fixed += 1
        log(f"Applied {mat_name} ({cfg['master']}) tint={cfg['tint'][:3]}")

log(f"=== Emily material v2 fix done: {fixed}/{len(MATERIAL_CONFIG)} ===")
