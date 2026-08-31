import unreal

CONTENT = "/Game/Characters/Nami"
RIG_DIR = f"{CONTENT}/Rig"
CR_PATH = f"{RIG_DIR}/CR_Nami"
ABP_PATH = f"{RIG_DIR}/ABP_Nami"
BP_PATH = f"{CONTENT}/BP_Nami"
BODY_MESH = f"{CONTENT}/body1"
RIGGED_FBX = r"E:\game\epic_assets_other\nami\Nami_rigged_all.fbx"
RIGGED_PREFIX = "Nami_rigged_all"

PART_MESHES = [
    ("cutehair1", "Nami_cutehair1"),
    ("jean1", "Nami_jean1"),
    ("hat1", "Nami_hat1"),
    ("sport_shirt", "Nami_sport_shirt"),
    ("sport_boot", "Nami_sport_boot"),
    ("belt1", "Nami_belt1"),
    ("katana", "Nami_katana"),
    ("eyelashes", "Nami_eyelashes"),
    ("L_eyes", "Nami_L_eyes"),
    ("R_eyes", "Nami_R_eyes"),
]

SRC_POST_ABP = "/Game/Free_Magic/Demo/Characters/Mannequins/Rigs/ABP_Manny_PostProcess.ABP_Manny_PostProcess"


def log(msg):
    unreal.log(f"[NamiCR] {msg}")


def ensure_dir(path):
    unreal.EditorAssetLibrary.make_directory(path)


def import_rigged_body():
    ensure_dir(RIG_DIR)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", RIGGED_FBX)
    task.set_editor_property("destination_path", CONTENT)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", True)
    opts.set_editor_property("import_as_skeletal", True)
    opts.set_editor_property("import_animations", True)
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    skel_data = opts.get_editor_property("skeletal_mesh_import_data")
    skel_data.set_editor_property("import_morph_targets", False)
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = task.get_editor_property("imported_object_paths")
    log(f"Imported rigged FBX: {paths}")
    return paths


def find_body_mesh():
    for name in ("Nami_rigged_all", "body", "body1"):
        p = f"{CONTENT}/{name}"
        if unreal.EditorAssetLibrary.does_asset_exist(p):
            return unreal.load_asset(f"{p}.{name}")
    return unreal.load_asset(f"{BODY_MESH}.body1")


def bind_body_material(mesh):
    mi_path = f"{CONTENT}/body"
    if not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        return
    mi = unreal.load_asset(f"{mi_path}.body")
    if not mi:
        return
    mats = mesh.get_editor_property("materials")
    if not mats:
        return
    entry = mats[0]
    entry.set_editor_property("material_interface", mi)
    mats[0] = entry
    mesh.set_editor_property("materials", mats)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    log("Applied body material")


def find_part_meshes(skeleton):
    """Find imported part meshes sharing the rigged skeleton."""
    parts = {}
    names_wanted = [n for n, _ in PART_MESHES]
    for asset in unreal.EditorAssetLibrary.list_assets(CONTENT, recursive=False):
        name = asset.split("/")[-1]
        if name.endswith("_Skeleton") or name.startswith("M_"):
            continue
        part_mesh = unreal.load_asset(f"{asset}.{name}")
        if not isinstance(part_mesh, unreal.SkeletalMesh):
            continue
        if part_mesh.get_editor_property("skeleton") != skeleton:
            continue
        for want in names_wanted:
            key = want.replace("1", "")
            if key in name.lower() or name.lower() in want.lower():
                parts[want] = part_mesh
                break
    return parts


def create_or_load_cr(mesh):
    ensure_dir(RIG_DIR)
    if unreal.EditorAssetLibrary.does_asset_exist(CR_PATH):
        cr = unreal.load_asset(f"{CR_PATH}.CR_Nami")
        log("Loaded existing CR_Nami")
        return cr

    factory = unreal.ControlRigBlueprintFactory()
    cr = factory.create_control_rig_from_skeletal_mesh_or_skeleton(mesh, False)
    if not cr:
        raise RuntimeError("Failed to create Control Rig")

    # Move/rename to Rig folder
    src = cr.get_path_name().split(".")[0]
    if src != CR_PATH:
        unreal.EditorAssetLibrary.rename_asset(src, CR_PATH)
        cr = unreal.load_asset(f"{CR_PATH}.CR_Nami")

    unreal.ControlRigBlueprintLibrary.set_preview_mesh(cr, mesh)

    hierarchy = cr.hierarchy
    hc = hierarchy.get_controller()
    keys = hierarchy.get_all_keys()
    if len(keys) <= 1:
        imported = hc.import_bones_from_asset(mesh.get_path_name(), "", True, True, False)
        log(f"Imported bones: {len(imported) if imported else 0}")

    # Add root control if missing
    controls = [k for k in hierarchy.get_all_keys() if k.type == unreal.RigElementType.CONTROL]
    if not controls:
        bone = None
        for k in hierarchy.get_all_keys():
            if k.type == unreal.RigElementType.BONE:
                bone = k
                break
        settings = unreal.RigControlSettings()
        settings.control_type = unreal.RigControlType.EULER_TRANSFORM
        hc.add_control("C_Root", bone or unreal.RigElementKey(), settings, unreal.RigControlValue(), True)
        log("Added C_Root control")

    unreal.EditorAssetLibrary.save_loaded_asset(cr)
    log(f"Created CR_Nami at {CR_PATH}")
    return cr


def setup_post_process_abp(mesh):
    ensure_dir(RIG_DIR)
    if unreal.EditorAssetLibrary.does_asset_exist(ABP_PATH):
        return unreal.load_asset(f"{ABP_PATH}.ABP_Nami")

    if unreal.EditorAssetLibrary.does_asset_exist(SRC_POST_ABP):
        unreal.EditorAssetLibrary.duplicate_asset(SRC_POST_ABP, ABP_PATH)
        abp = unreal.load_asset(f"{ABP_PATH}.ABP_Nami")
        log("Duplicated ABP_Manny_PostProcess -> ABP_Nami")
    else:
        factory = unreal.AnimBlueprintFactory()
        factory.set_editor_property("target_skeleton", mesh.get_editor_property("skeleton"))
        factory.set_editor_property("preview_skeletal_mesh", mesh)
        factory.set_editor_property("parent_class", unreal.AnimInstance)
        abp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "ABP_Nami", RIG_DIR, unreal.AnimBlueprint, factory
        )
        log("Created empty ABP_Nami")

    unreal.EditorAssetLibrary.save_loaded_asset(abp)
    return abp


def bind_mesh_rig(mesh, cr, abp):
    rig_class = cr.generated_class()
    if rig_class:
        mesh.set_editor_property("default_animating_rig", rig_class)
    if abp:
        gen = abp.generated_class()
        if gen:
            mesh.set_editor_property("post_process_anim_blueprint", gen)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    log("Bound default_animating_rig + post process ABP on body mesh")


def find_anim_sequences():
    anims = {}
    for asset in unreal.EditorAssetLibrary.list_assets(CONTENT, recursive=True):
        name = asset.split("/")[-1]
        obj = unreal.load_asset(f"{asset}.{name}")
        if not isinstance(obj, unreal.AnimSequence):
            continue
        low = name.lower()
        if "walk" in low or "rigged" in low:
            anims["walk"] = obj
        if "idle" in low or "stand" in low:
            anims["idle"] = obj
    if "idle" not in anims and "walk" in anims:
        anims["idle"] = anims["walk"]
    return anims


def create_character_blueprint(mesh, anims):
    """Create minimal Character BP; full component setup can be done in editor."""
    ensure_dir(CONTENT)
    if unreal.EditorAssetLibrary.does_asset_exist(BP_PATH):
        log(f"BP exists: {BP_PATH}")
        return unreal.load_asset(f"{BP_PATH}.BP_Nami")
    try:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Character)
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "BP_Nami", CONTENT, unreal.Blueprint, factory
        )
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        log(f"Created empty {BP_PATH} — assign mesh/anim in editor")
        return bp
    except Exception as exc:
        log(f"Skip BP create: {exc}")
        return None


def spawn_preview(mesh):
    map_path = f"{CONTENT}/Nami_Showcase"
    if unreal.EditorAssetLibrary.does_asset_exist(map_path):
        unreal.EditorLoadingAndSavingUtils.load_map(map_path)
    else:
        unreal.EditorLoadingAndSavingUtils.new_blank_map(True)

    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if actor.get_actor_label().startswith("Nami_"):
            unreal.EditorLevelLibrary.destroy_actor(actor)

    loc = unreal.Vector(0, 0, 0)
    skel = mesh.get_editor_property("skeleton")
    rig_parts = find_part_meshes(skel)

    body_name = mesh.get_name()
    body_label = "Nami_Body" if "body" in body_name.lower() else f"Nami_{body_name}"
    body_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkeletalMeshActor, loc, unreal.Rotator(0, 0, 0)
    )
    body_actor.set_actor_label(body_label)
    body_comp = body_actor.get_component_by_class(unreal.SkeletalMeshComponent)
    body_comp.set_skeletal_mesh(mesh)
    anims = find_anim_sequences()
    idle = anims.get("idle") or anims.get("walk")
    if idle:
        body_comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        body_comp.play_animation(idle, True)

    for mesh_name, label in PART_MESHES:
        part_mesh = rig_parts.get(mesh_name)
        if not part_mesh:
            part_mesh = unreal.load_asset(f"{CONTENT}/{mesh_name}.{mesh_name}")
        if not part_mesh or part_mesh == mesh:
            continue
        part = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkeletalMeshActor, loc, unreal.Rotator(0, 0, 0)
        )
        part.set_actor_label(label)
        pc = part.get_component_by_class(unreal.SkeletalMeshComponent)
        pc.set_skeletal_mesh(part_mesh)
        try:
            pc.set_leader_pose_component(body_comp, True)
        except Exception:
            pass
        part.attach_to_actor(body_actor, "", unreal.AttachmentRule.SNAP_TO_TARGET,
                             unreal.AttachmentRule.SNAP_TO_TARGET,
                             unreal.AttachmentRule.SNAP_TO_TARGET, False)

    unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), map_path
    )
    log(f"Spawned preview: body={body_name}, rig_parts={len(rig_parts)}, anims={list(anims.keys())}")


log("=== Nami Control Rig setup ===")
if unreal.Paths.file_exists(RIGGED_FBX):
    import_rigged_body()
else:
    log(f"Skip FBX import, not found: {RIGGED_FBX}")

mesh = find_body_mesh()
bind_body_material(mesh)
cr = create_or_load_cr(mesh)
abp = setup_post_process_abp(mesh)
bind_mesh_rig(mesh, cr, abp)
anims = find_anim_sequences()
create_character_blueprint(mesh, anims)
spawn_preview(mesh)
log("=== Done ===")
