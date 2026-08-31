"""Make M_Transparent actually translucent, and put the cute girl back in the map."""
import os
import sys
import unreal

MAT_DIR = "/Game/Material"
MAT_PATH = MAT_DIR + "/M_Transparent"
MI_PATH = MAT_DIR + "/MI_HidePart"
MAP_PATH = "/Game/ApartmentScene/L_ApartmentLiving"
BP_PATH = "/Game/ApartmentScene/BP_CuteGirl"
GM_PATH = "/Game/ApartmentScene/BP_AptGameMode"
MESH_PATH = "/Game/ApartmentScene/Cute/Cute_Walk.Cute_Walk"
IDLE_PATH = "/Game/ApartmentScene/Cute/Cute_Idle_Anim.Cute_Idle_Anim"

WALK0 = unreal.Vector(455.0, -1270.0, 92.0)
WALK_YAW = 165.3


def log(msg):
    print(f"[Transp] {msg}")
    unreal.log(f"[Transp] {msg}")


def actors():
    try:
        return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    except Exception:
        return list(unreal.EditorLevelLibrary.get_all_level_actors())


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def load_or_create_material():
    ensure_dir(MAT_DIR)
    if unreal.EditorAssetLibrary.does_asset_exist(MAT_PATH):
        mat = unreal.load_asset(MAT_PATH + ".M_Transparent")
        log("loaded existing M_Transparent")
    else:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_Transparent", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew()
        )
        log("created M_Transparent")
    return mat


def rebuild_transparent_material(mat):
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("two_sided", True)
    try:
        mat.set_editor_property(
            "translucency_lighting_mode",
            unreal.TranslucencyLightingMode.TLM_VOLUMETRIC_NON_DIRECTIONAL,
        )
    except Exception:
        pass

    color = mel.create_material_expression(
        mat, unreal.MaterialExpressionVectorParameter, -420, 0
    )
    color.set_editor_property("parameter_name", "Color")
    color.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    mel.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)

    opacity = mel.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, -420, 220
    )
    opacity.set_editor_property("parameter_name", "Opacity")
    # Glassy in the Content Browser sphere; 0 = fully hidden via MI_HidePart.
    opacity.set_editor_property("default_value", 0.35)
    mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)

    rough = mel.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -420, 400
    )
    rough.set_editor_property("r", 0.85)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    spec = mel.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -420, 500
    )
    spec.set_editor_property("r", 0.05)
    mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)

    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    log("M_Transparent blend=Translucent two_sided Opacity param default=0.35")
    return mat


def ensure_hide_instance(parent):
    mel = unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(MI_PATH):
        mi = unreal.load_asset(MI_PATH + ".MI_HidePart")
        log("loaded existing MI_HidePart")
    else:
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "MI_HidePart",
            MAT_DIR,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew(),
        )
        log("created MI_HidePart")
    mel.set_material_instance_parent(mi, parent)
    mel.set_material_instance_scalar_parameter_value(mi, "Opacity", 0.0)
    mel.set_material_instance_vector_parameter_value(
        mi, "Color", unreal.LinearColor(1.0, 1.0, 1.0, 0.0)
    )
    mel.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    log("MI_HidePart Opacity=0 (assign this to shirt/jean slots to hide them)")
    return mi


def log_mesh_slots():
    mesh = unreal.load_asset(MESH_PATH)
    if not mesh:
        log("Cute_Walk mesh missing")
        return []
    names = []
    try:
        slots = mesh.get_editor_property("materials")
    except Exception:
        slots = []
    for i, slot in enumerate(slots or []):
        try:
            slot_name = str(slot.get_editor_property("material_slot_name"))
        except Exception:
            slot_name = "?"
        try:
            mat = slot.get_editor_property("material")
            mat_name = mat.get_name() if mat else None
        except Exception:
            mat_name = None
        names.append((i, slot_name, mat_name))
        log(f"Cute_Walk slot[{i}] {slot_name} -> {mat_name}")
    return names


def restore_cute_in_level():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    bp = unreal.load_asset(BP_PATH + ".BP_CuteGirl")
    if not bp or not bp.generated_class():
        raise RuntimeError("BP_CuteGirl missing")
    rot = unreal.Rotator(pitch=0.0, yaw=WALK_YAW, roll=0.0)
    existing = None
    for a in actors():
        label = a.get_actor_label()
        cls_name = a.get_class().get_name()
        if label == "Cute" or "CuteGirl" in cls_name:
            existing = a
            break
    if existing:
        existing.set_actor_location(WALK0, False, False)
        existing.set_actor_rotation(rot, False)
        pawn = existing
        log(f"reused placed pawn {pawn.get_actor_label()}")
    else:
        pawn = unreal.EditorLevelLibrary.spawn_actor_from_class(
            bp.generated_class(), WALK0, rot
        )
        pawn.set_actor_label("Cute")
        log("spawned BP_CuteGirl as Cute")
    try:
        pawn.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
    except Exception as e:
        log(f"auto possess: {e}")
    idle = unreal.load_asset(IDLE_PATH)
    if idle and pawn.mesh:
        try:
            pawn.mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            pawn.mesh.play_animation(idle, True)
        except Exception as e:
            log(f"idle: {e}")
    for a in actors():
        if isinstance(a, unreal.PlayerStart) or a.get_actor_label().startswith("Apt_PlayerStart"):
            a.set_actor_location(WALK0, False, False)
            a.set_actor_rotation(rot, False)
            log("PlayerStart synced")
            break
    return pawn


def patch_game_mode_no_second_pawn():
    gm = unreal.load_asset(GM_PATH + ".BP_AptGameMode")
    if not gm:
        log("BP_AptGameMode missing")
        return
    unreal.BlueprintEditorLibrary.compile_blueprint(gm)
    cdo = unreal.get_default_object(gm.generated_class())
    # Placed Cute auto-possesses. Do not spawn a second pawn at PlayerStart.
    try:
        cdo.set_editor_property("default_pawn_class", None)
        log("GameMode default pawn=None (use placed Cute)")
    except Exception as e:
        log(f"default_pawn None failed ({e}), keeping BP_CuteGirl")
    unreal.EditorAssetLibrary.save_loaded_asset(gm)
    py_dir = os.path.join(unreal.Paths.project_content_dir(), "Python")
    if py_dir not in sys.path:
        sys.path.insert(0, py_dir)
    import cute_apartment_character as cac
    cac.patch_game_mode()


log("=== transparent material + restore cute ===")
mat = rebuild_transparent_material(load_or_create_material())
ensure_hide_instance(mat)
log_mesh_slots()
restore_cute_in_level()
patch_game_mode_no_second_pawn()
ok = unreal.EditorLoadingAndSavingUtils.save_map(
    unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
)
log(f"=== Done map_saved={ok} ===")
