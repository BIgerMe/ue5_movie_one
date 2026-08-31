import unreal

STANDING_FBX = r"E:\game\epic_assets_other\nami\exports\Nami_ue_bake.fbx"
CONTENT = "/Game/Characters/Nami"
STANDING_DIR = CONTENT + "/Standing"
SHOWCASE_MAP = f"{CONTENT}/Nami_Showcase"
MAIN_MAP = "/Game/Main"

SPAWN_LOCATION = unreal.Vector(0.0, 0.0, 0.0)
SPAWN_ROTATION = unreal.Rotator(0.0, 0.0, 0.0)

# mesh asset name -> (actor label, material instance name)
STANDING_PARTS = [
    ("body", "Nami_Body", "body"),
    ("belt", "Nami_belt", "belt"),
    ("cutehair", "Nami_cutehair", "cutehair"),
    ("eyelashes", "Nami_eyelashes", "eyes_lashes"),
    ("hat", "Nami_hat", "hat"),
    ("jean", "Nami_jean", "jean"),
    ("katana", "Nami_katana", "sword"),
    ("L_eyes", "Nami_L_eyes", "eyes"),
    ("R_eyes", "Nami_R_eyes", "eyes"),
    ("sport_boot", "Nami_sport_boot", "jean"),
    ("sport_shirt", "Nami_sport_shirt", "sport"),
]

UNWANTED_MESH_KEYWORDS = (
    "tongue",
    "teeth",
    "terrain",
    "placeholder",
    "floor",
    "plane",
)

UNWANTED_ACTOR_LABELS = (
    "Nami_Floor",
    "Nami_Sun",
    "Nami_SkyLight",
    "Nami_tongue",
    "Nami_teeth_lower",
    "Nami_teeth_upper",
    "Nami_teeth",
    "Nami_terrain",
)


def log(msg):
    unreal.log(f"[NamiStanding] {msg}")


def import_standing_fbx():
    unreal.EditorAssetLibrary.make_directory(STANDING_DIR)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", STANDING_FBX)
    task.set_editor_property("destination_path", STANDING_DIR)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    static_data = options.get_editor_property("static_mesh_import_data")
    static_data.set_editor_property("combine_meshes", False)
    static_data.set_editor_property("generate_lightmap_u_vs", True)
    static_data.set_editor_property("auto_generate_collision", False)
    task.set_editor_property("options", options)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = task.get_editor_property("imported_object_paths")
    log(f"Imported standing FBX -> {len(paths)} assets")
    return paths


def load_static_mesh(name):
    path = f"{STANDING_DIR}/{name}"
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return None
    return unreal.load_asset(f"{path}.{name}")


def load_material(mat_name):
    path = f"{CONTENT}/{mat_name}"
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return None
    return unreal.load_asset(f"{path}.{mat_name}")


def bind_standing_materials():
    bound = 0
    for mesh_name, _, mat_name in STANDING_PARTS:
        mesh = load_static_mesh(mesh_name)
        mi = load_material(mat_name)
        if not mesh or not mi:
            log(f"Skip bind {mesh_name}: mesh={bool(mesh)} mat={bool(mi)}")
            continue
        slot_count = max(1, len(mesh.get_editor_property("static_materials")))
        for i in range(slot_count):
            mesh.set_material(i, mi)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        bound += 1
        log(f"Bound {mesh_name} -> {mat_name}")
    return bound


def actor_uses_unwanted_mesh(actor):
    for comp in actor.get_components_by_class(unreal.MeshComponent):
        mesh = None
        if isinstance(comp, unreal.StaticMeshComponent):
            mesh = comp.get_editor_property("static_mesh")
        elif isinstance(comp, unreal.SkeletalMeshComponent):
            mesh = comp.get_skeletal_mesh_asset()
        if not mesh:
            continue
        name = mesh.get_name().lower()
        if any(k in name for k in UNWANTED_MESH_KEYWORDS):
            return True
    return False


def clean_map(map_path):
    if not unreal.EditorAssetLibrary.does_asset_exist(map_path):
        log(f"Map not found: {map_path}")
        return 0

    unreal.EditorLoadingAndSavingUtils.load_map(map_path)
    removed = 0
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        label = actor.get_actor_label()
        if label in UNWANTED_ACTOR_LABELS:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            removed += 1
            continue
        lower = label.lower()
        if any(k in lower for k in UNWANTED_MESH_KEYWORDS):
            unreal.EditorLevelLibrary.destroy_actor(actor)
            removed += 1
            continue
        if actor_uses_unwanted_mesh(actor):
            unreal.EditorLevelLibrary.destroy_actor(actor)
            removed += 1

    unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), map_path
    )
    log(f"Cleaned {map_path}: removed {removed} unwanted actors")
    return removed


def clear_old_nami_actors():
    removed = 0
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        label = actor.get_actor_label()
        if label.startswith("Nami_"):
            unreal.EditorLevelLibrary.destroy_actor(actor)
            removed += 1
    log(f"Cleared {removed} old Nami_* actors from current map")
    return removed


def assemble_standing_showcase():
    if unreal.EditorAssetLibrary.does_asset_exist(SHOWCASE_MAP):
        unreal.EditorLoadingAndSavingUtils.load_map(SHOWCASE_MAP)
    else:
        unreal.EditorLoadingAndSavingUtils.new_blank_map(True)

    clear_old_nami_actors()

    root_actor = None
    spawned = 0
    for mesh_name, label, _ in STANDING_PARTS:
        mesh = load_static_mesh(mesh_name)
        if not mesh:
            log(f"Missing standing mesh: {mesh_name}")
            continue
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, SPAWN_LOCATION, SPAWN_ROTATION
        )
        actor.set_actor_label(label)
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_static_mesh(mesh)
        comp.set_visibility(True, True)
        if root_actor is None and mesh_name == "body":
            root_actor = actor
        elif root_actor:
            actor.attach_to_actor(
                root_actor,
                "",
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                False,
            )
        spawned += 1

    saved = unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), SHOWCASE_MAP
    )
    log(f"Assembled standing Nami ({spawned} parts), saved={saved}")


log("=== Nami standing import start ===")
import_standing_fbx()
bind_standing_materials()
clean_map(SHOWCASE_MAP)
clean_map(MAIN_MAP)
assemble_standing_showcase()
log("=== Done ===")
