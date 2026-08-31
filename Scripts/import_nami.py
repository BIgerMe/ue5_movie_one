import os
import re
import unreal

CONTENT_BASE = "/Game/Characters/Nami"
TEXTURES_CONTENT = CONTENT_BASE + "/Textures"
FBX_PATH = r"E:\game\epic_assets_other\nami\Nami+OP.fbx"
TEXTURE_SRC = r"E:\game\epic_assets_other\nami\textures\textures"

MASTER_PBR = CONTENT_BASE + "/M_NamiPBR"
MASTER_TRANSLUCENT = CONTENT_BASE + "/M_NamiTranslucent"

P_TEX = {
    "base": "BaseColorTex",
    "normal": "NormalTex",
    "rough": "RoughnessTex",
    "metal": "MetallicTex",
}

# FBX material slot keyword -> texture filename prefix
SLOT_TO_PREFIX = [
    ("tattoo", "body__tattoo"),
    ("body", "body"),
    ("belt", "belt"),
    ("hair", "cutehair"),
    ("cutehair", "cutehair"),
    ("eyelash", "eyelashes"),
    ("eye", "Eye_brown"),
    ("hat", "Hat"),
    ("jean", "jean"),
    ("sport", "Sport"),
    ("sword", "sword"),
    ("teeth", "teeth"),
]

TRANSLUCENT_PREFIXES = {"cutehair", "eyelashes"}


def log(msg):
    unreal.log(f"[NamiImport] {msg}")


def scan_textures():
    groups = {}
    for fn in os.listdir(TEXTURE_SRC):
        lower = fn.lower()
        if not lower.endswith((".png", ".jpg", ".tga")):
            continue
        base = fn.rsplit(".", 1)[0]
        kind = None
        prefix = base
        for suffix, key in [
            ("_basecolor_opacity", "base"),
            ("_basecolor", "base"),
            ("_BaseColor", "base"),
            ("_normal", "normal"),
            ("_Normal", "normal"),
            ("_roughness", "rough"),
            ("_Roughness", "rough"),
            ("_metallic", "metal"),
            ("_Metalness", "metal"),
            ("_specular", "rough"),  # fallback roughness channel
        ]:
            if base.lower().endswith(suffix.lower()):
                kind = key
                prefix = base[: -len(suffix)]
                break
        if kind is None:
            continue
        groups.setdefault(prefix, {})[kind] = fn
    return groups


def resolve_prefix(slot_name):
    s = slot_name.lower()
    for keyword, prefix in SLOT_TO_PREFIX:
        if keyword in s:
            return prefix
    # fallback: first word
    token = re.split(r"[^a-zA-Z0-9]+", slot_name)[0].lower()
    return token or slot_name


def import_textures():
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    unreal.EditorAssetLibrary.make_directory(TEXTURES_CONTENT)
    count = 0
    for fn in sorted(os.listdir(TEXTURE_SRC)):
        if not fn.lower().endswith((".png", ".jpg", ".tga")):
            continue
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", os.path.join(TEXTURE_SRC, fn))
        task.set_editor_property("destination_path", TEXTURES_CONTENT)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)
        task.set_editor_property("replace_existing", True)
        asset_tools.import_asset_tasks([task])
        count += 1
    log(f"Imported {count} textures")


def import_fbx():
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
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    log(f"FBX imported: {task.get_editor_property('imported_object_paths')}")


def _build_pbr_master(path, blend_mode, use_opacity_alpha=False):
    name = path.split("/")[-1]
    mel = unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(f"{path}.{name}")
    else:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, CONTENT_BASE, unreal.Material, unreal.MaterialFactoryNew()
        )

    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("blend_mode", blend_mode)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)

    tex = mel.create_material_expression(
        mat, unreal.MaterialExpressionTextureSampleParameter2D, -800, 0
    )
    tex.set_editor_property("parameter_name", P_TEX["base"])
    tex.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)

    nrm = mel.create_material_expression(
        mat, unreal.MaterialExpressionTextureSampleParameter2D, -800, 200
    )
    nrm.set_editor_property("parameter_name", P_TEX["normal"])
    nrm.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)

    rough = mel.create_material_expression(
        mat, unreal.MaterialExpressionTextureSampleParameter2D, -800, 400
    )
    rough.set_editor_property("parameter_name", P_TEX["rough"])
    rough.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)

    metal = mel.create_material_expression(
        mat, unreal.MaterialExpressionTextureSampleParameter2D, -800, 600
    )
    metal.set_editor_property("parameter_name", P_TEX["metal"])
    metal.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)

    mel.connect_material_property(tex, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(nrm, "", unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(rough, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "R", unreal.MaterialProperty.MP_METALLIC)

    if use_opacity_alpha:
        mel.connect_material_property(tex, "A", unreal.MaterialProperty.MP_OPACITY)

    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def ensure_masters():
    pbr = _build_pbr_master(MASTER_PBR, unreal.BlendMode.BLEND_OPAQUE, False)
    trans = _build_pbr_master(MASTER_TRANSLUCENT, unreal.BlendMode.BLEND_TRANSLUCENT, True)
    log("Master materials ready")
    return pbr, trans


def load_tex(prefix, kind, tex_groups):
    files = tex_groups.get(prefix, {})
    fn = files.get(kind)
    if not fn:
        return None
    stem = fn.rsplit(".", 1)[0]
    return unreal.load_asset(f"{TEXTURES_CONTENT}/{stem}.{stem}")


def apply_pbr_to_instance(material, prefix, tex_groups, master_opaque, master_trans):
    mel = unreal.MaterialEditingLibrary
    is_trans = prefix in TRANSLUCENT_PREFIXES
    master = master_trans if is_trans else master_opaque
    mel.set_material_instance_parent(material, master)

    base = load_tex(prefix, "base", tex_groups)
    normal = load_tex(prefix, "normal", tex_groups)
    rough = load_tex(prefix, "rough", tex_groups)
    metal = load_tex(prefix, "metal", tex_groups)

    if base:
        mel.set_material_instance_texture_parameter_value(material, P_TEX["base"], base)
    if normal:
        mel.set_material_instance_texture_parameter_value(material, P_TEX["normal"], normal)
    if rough:
        mel.set_material_instance_texture_parameter_value(material, P_TEX["rough"], rough)
    if metal:
        mel.set_material_instance_texture_parameter_value(material, P_TEX["metal"], metal)

    if prefix in {"body", "body__tattoo", "Eye_brown", "teeth", "Hat"}:
        overrides = material.get_editor_property("base_property_overrides")
        overrides.set_editor_property("override_two_sided", True)
        overrides.set_editor_property("two_sided", True)
        material.set_editor_property("base_property_overrides", overrides)

    mel.update_material_instance(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return bool(base)


def fix_materials(tex_groups):
    fixed = 0
    for asset_path in unreal.EditorAssetLibrary.list_assets(CONTENT_BASE, recursive=False):
        if not asset_path.startswith(CONTENT_BASE + "/"):
            continue
        name = asset_path.split("/")[-1]
        if name.startswith("M_") or name in ("Nami", "Nami_Skeleton", "Nami_PhysicsAsset"):
            continue
        if not name.endswith("_SKIN") and "_EYE" not in name and not any(
            k in name.lower() for k in ("body", "belt", "hair", "hat", "jean", "sport", "sword", "teeth", "tattoo", "eye", "sport")
        ):
            # still try all material instances
            pass
        material = unreal.load_asset(f"{asset_path}.{name}")
        if not material or not isinstance(material, unreal.MaterialInstanceConstant):
            continue
        prefix = resolve_prefix(name)
        # try exact prefix keys from tex_groups
        if prefix not in tex_groups:
            for p in tex_groups:
                if p.lower() in name.lower() or name.lower() in p.lower():
                    prefix = p
                    break
        master_opaque, master_trans = ensure_masters()
        if apply_pbr_to_instance(material, prefix, tex_groups, master_opaque, master_trans):
            fixed += 1
            log(f"Material {name} -> prefix '{prefix}'")
        else:
            unreal.log_warning(f"No base texture for {name} (prefix={prefix})")
    return fixed


log("=== Nami import start ===")
tex_groups = scan_textures()
log(f"Texture groups: {list(tex_groups.keys())}")
import_fbx()
import_textures()
ensure_masters()
fixed = fix_materials(tex_groups)
log(f"=== Nami import done: {fixed} materials configured ===")
