import unreal

MAIN_MAP = "/Game/Main"
STANDING_DIR = "/Game/Characters/Nami/Standing"
CONTENT = "/Game/Characters/Nami"

UNWANTED = ("tongue", "teeth", "terrain", "placeholder")

STANDING_PARTS = [
    ("body", "Nami_Body"),
    ("belt", "Nami_belt"),
    ("cutehair", "Nami_cutehair"),
    ("eyelashes", "Nami_eyelashes"),
    ("hat", "Nami_hat"),
    ("jean", "Nami_jean"),
    ("katana", "Nami_katana"),
    ("L_eyes", "Nami_L_eyes"),
    ("R_eyes", "Nami_R_eyes"),
    ("sport_boot", "Nami_sport_boot"),
    ("sport_shirt", "Nami_sport_shirt"),
]


def log(msg):
    unreal.log(f"[NamiMainClean] {msg}")


def mesh_name_from_comp(comp):
    if isinstance(comp, unreal.StaticMeshComponent):
        mesh = comp.get_editor_property("static_mesh")
        return mesh.get_name() if mesh else ""
    if isinstance(comp, unreal.SkeletalMeshComponent):
        mesh = comp.get_skeletal_mesh_asset()
        return mesh.get_name() if mesh else ""
    return ""


def should_remove(actor):
    label = actor.get_actor_label().lower()
    if any(k in label for k in UNWANTED):
        return True
    for comp in actor.get_components_by_class(unreal.MeshComponent):
        name = mesh_name_from_comp(comp).lower()
        if any(k in name for k in UNWANTED):
            return True
    return False


def spawn_standing_at(location):
    root = None
    rot = unreal.Rotator(0, 0, 0)
    for mesh_name, label in STANDING_PARTS:
        path = f"{STANDING_DIR}/{mesh_name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            continue
        mesh = unreal.load_asset(f"{path}.{mesh_name}")
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, location, rot
        )
        actor.set_actor_label(label)
        actor.get_component_by_class(unreal.StaticMeshComponent).set_static_mesh(mesh)
        if root is None and mesh_name == "body":
            root = actor
        elif root:
            actor.attach_to_actor(
                root, "",
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                False,
            )


if not unreal.EditorAssetLibrary.does_asset_exist(MAIN_MAP):
    log("Main map not found")
else:
    unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    removed = []
    nami_locations = []
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if should_remove(actor):
            removed.append(actor.get_actor_label())
            unreal.EditorLevelLibrary.destroy_actor(actor)
            continue
        label = actor.get_actor_label()
        if label.startswith("Nami_"):
            nami_locations.append(actor.get_actor_location())
            unreal.EditorLevelLibrary.destroy_actor(actor)

    if nami_locations:
        loc = nami_locations[0]
    else:
        loc = unreal.Vector(0, 0, 0)

    spawn_standing_at(loc)
    unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), MAIN_MAP
    )
    log(f"Removed {len(removed)} junk actors: {removed}")
    log(f"Replaced old Nami with standing static assembly at {loc}")
