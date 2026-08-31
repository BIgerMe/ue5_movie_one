import unreal

MAP_PATH = "/Game/Characters/Nami/Nami_Showcase"
CONTENT = "/Game/Characters/Nami"
SPAWN_LOCATION = unreal.Vector(0.0, 0.0, 0.0)
SPAWN_ROTATION = unreal.Rotator(0.0, 0.0, 0.0)

ROOT_MESH = "body1"
PART_MESHES = [
    "cutehair1",
    "jean1",
    "hat1",
    "sport_shirt",
    "sport_boot",
    "belt1",
    "katana",
    "eyelashes",
    "L_eyes",
    "R_eyes",
]


def log(msg):
    unreal.log(f"[NamiAssemble] {msg}")


def load_mesh(name):
    path = f"{CONTENT}/{name}.{name}"
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{CONTENT}/{name}"):
        return None
    return unreal.load_asset(path)


def spawn_skeletal(name, label):
    mesh = load_mesh(name)
    if not mesh:
        log(f"Skip missing mesh: {name}")
        return None, None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkeletalMeshActor, SPAWN_LOCATION, SPAWN_ROTATION
    )
    actor.set_actor_label(label)
    actor.set_actor_location(SPAWN_LOCATION, False, False)
    actor.set_actor_rotation(SPAWN_ROTATION, False)
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    comp.set_skeletal_mesh(mesh)
    comp.set_visibility(True, True)
    return actor, comp


def add_simple_lighting():
    sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(-45, 45, 0)
    )
    sun.set_actor_label("Nami_Sun")
    sun_comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if sun_comp:
        sun_comp.set_intensity(6.0)

    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0, 0, 600), unreal.Rotator(0, 0, 0)
    )
    sky.set_actor_label("Nami_SkyLight")
    sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
    if sky_comp:
        sky_comp.set_intensity(1.2)
        sky_comp.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)


def assemble_scene():
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
        log(f"Loaded existing map: {MAP_PATH}")
    else:
        unreal.EditorLoadingAndSavingUtils.new_blank_map(True)
        log("Created new blank map")

    # Clear previously spawned Nami actors if re-running on same map
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if label.startswith("Nami_"):
            unreal.EditorLevelLibrary.destroy_actor(actor)

    body_actor, body_comp = spawn_skeletal(ROOT_MESH, "Nami_Body")
    if not body_actor or not body_comp:
        raise RuntimeError("Root mesh body1 not found")

    attached = 0
    for mesh_name in PART_MESHES:
        part_actor, part_comp = spawn_skeletal(mesh_name, f"Nami_{mesh_name}")
        if not part_actor or not part_comp:
            continue
        part_comp.set_leader_pose_component(body_comp, True)
        part_actor.attach_to_actor(
            body_actor,
            "",
            unreal.AttachmentRule.SNAP_TO_TARGET,
            unreal.AttachmentRule.SNAP_TO_TARGET,
            unreal.AttachmentRule.SNAP_TO_TARGET,
            False,
        )
        attached += 1

    saved = unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
    )
    log(f"Assembled {attached + 1} meshes, map saved={saved}: {MAP_PATH}")


log("=== Nami scene assemble start ===")
assemble_scene()
log("=== Done ===")
