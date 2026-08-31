import unreal

CONTENT_BASE = "/Game/Characters/Emily"
DRESS_MAT = "F00_002_03_Tops_01_CLOTH"
DRESS_TEX = "F00_002_03_Tops_01"
MASTER_TRANSLUCENT = CONTENT_BASE + "/M_EmilyTranslucent"

TINT_PARAM = "TintColor"
TEX_PARAM = "BaseColorTex"
OPACITY_PARAM = "OpacityScale"


def log(msg):
    unreal.log(f"[EmilyDress] {msg}")


def rebuild_translucent_master():
    """Opacity = texture alpha * OpacityScale, for semi-sheer lace."""
    mel = unreal.MaterialEditingLibrary
    material = unreal.load_asset(f"{MASTER_TRANSLUCENT}.{MASTER_TRANSLUCENT.split('/')[-1]}")
    if not material:
        raise RuntimeError("M_EmilyTranslucent not found")

    mel.delete_all_material_expressions(material)

    tex = mel.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -600, 0
    )
    tex.set_editor_property("parameter_name", TEX_PARAM)
    tex.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)

    tint = mel.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -600, 220
    )
    tint.set_editor_property("parameter_name", TINT_PARAM)
    tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))

    color_mul = mel.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -320, 80
    )
    mel.connect_material_expressions(tex, "", color_mul, "A")
    mel.connect_material_expressions(tint, "", color_mul, "B")
    mel.connect_material_property(color_mul, "", unreal.MaterialProperty.MP_BASE_COLOR)

    opacity_scale = mel.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -600, 420
    )
    opacity_scale.set_editor_property("parameter_name", OPACITY_PARAM)
    opacity_scale.set_editor_property("default_value", 1.0)

    opacity_mul = mel.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -320, 360
    )
    mel.connect_material_expressions(tex, "A", opacity_mul, "A")
    mel.connect_material_expressions(opacity_scale, "", opacity_mul, "B")
    mel.connect_material_property(opacity_mul, "", unreal.MaterialProperty.MP_OPACITY)

    rough = mel.create_material_expression(
        material, unreal.MaterialExpressionConstant, -320, 520
    )
    rough.set_editor_property("r", 0.9)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    spec = mel.create_material_expression(
        material, unreal.MaterialExpressionConstant, -320, 620
    )
    spec.set_editor_property("r", 0.05)
    mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)

    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    log("Updated M_EmilyTranslucent with OpacityScale")


def fix_dress_texture_alpha():
    tex_path = f"{CONTENT_BASE}/Textures/{DRESS_TEX}.{DRESS_TEX}"
    texture = unreal.load_asset(tex_path)
    if not texture:
        unreal.log_warning(f"Texture not found: {tex_path}")
        return
    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_BC7)
    texture.set_editor_property("srgb", True)
    texture.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    log("Set dress texture to BC7 (preserve alpha)")


def apply_dress_material():
    mat_path = f"{CONTENT_BASE}/{DRESS_MAT}.{DRESS_MAT}"
    tex_path = f"{CONTENT_BASE}/Textures/{DRESS_TEX}.{DRESS_TEX}"
    material = unreal.load_asset(mat_path)
    texture = unreal.load_asset(tex_path)
    master = unreal.load_asset(f"{MASTER_TRANSLUCENT}.{MASTER_TRANSLUCENT.split('/')[-1]}")
    if not all([material, texture, master]):
        raise RuntimeError("Dress material/texture/master missing")

    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_parent(material, master)
    mel.set_material_instance_texture_parameter_value(material, TEX_PARAM, texture)
    # Slightly brighter than 0.8 so lace fabric is not pure black
    mel.set_material_instance_vector_parameter_value(
        material, TINT_PARAM, unreal.LinearColor(1.0, 1.0, 1.0, 1.0)
    )
    # 1.0 = use texture alpha as-is; lower = more see-through overall
    mel.set_material_instance_scalar_parameter_value(material, OPACITY_PARAM, 0.95)

    overrides = material.get_editor_property("base_property_overrides")
    overrides.set_editor_property("override_two_sided", True)
    overrides.set_editor_property("two_sided", True)
    material.set_editor_property("base_property_overrides", overrides)

    mel.update_material_instance(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    log("Dress -> Translucent, OpacityScale=0.95, Tint=1.0")


log("=== Emily dress transparency fix ===")
fix_dress_texture_alpha()
rebuild_translucent_master()
apply_dress_material()
log("=== Done ===")
