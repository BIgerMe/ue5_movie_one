"""Import the apartment + three girls into 模型使用 and assemble a living-room level.

Blender already did meshes / rigs / the walk clip.  This script only does UE work:
scene, lighting, placement, and playing the walk.
"""
import os
import unreal

CONTENT = "/Game/ApartmentScene"
MAP_PATH = CONTENT + "/L_ApartmentLiving"
EXPORTS = r"E:\game\scene_build\exports"

# Blender metres -> UE cm.  Axis: Blender Y-forward walk becomes UE -X after the
# FBX -Z forward / Y up export used for this project.
SEAT = (unreal.Vector(202.0, 1215.0, 0.0), unreal.Rotator(0.0, 90.0, 0.0))
STAND = (unreal.Vector(330.0, 1330.0, 0.0), unreal.Rotator(0.0, -48.0, 0.0))
WALK0 = (unreal.Vector(455.0, 1270.0, 0.0), unreal.Rotator(0.0, -14.7, 0.0))

CHAR_JOBS = [
    ("Cute", os.path.join(EXPORTS, "Cute_Walk.fbx"), True),
    ("Rosemary", os.path.join(EXPORTS, "Rosemary_Sit.fbx"), True),
    ("Ayane", os.path.join(EXPORTS, "Ayane_Stand.fbx"), True),
]


def log(msg):
    unreal.log(f"[Apartment] {msg}")


def ensure_dir(path):
    unreal.EditorAssetLibrary.make_directory(path)


def import_fbx(path, dest, skeletal, combine=False):
    ensure_dir(dest)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", path)
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)

    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", True)
    opts.set_editor_property("import_materials", True)
    opts.set_editor_property("import_textures", True)
    opts.set_editor_property("import_as_skeletal", skeletal)
    opts.set_editor_property("import_animations", skeletal)
    if skeletal:
        opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
        sk = opts.get_editor_property("skeletal_mesh_import_data")
        try:
            sk.set_editor_property("import_morph_targets", True)
            sk.set_editor_property("use_t0_as_ref_pose", False)
            sk.set_editor_property("convert_scene", True)
            sk.set_editor_property("convert_scene_unit", True)
            sk.set_editor_property("force_front_x_axis", False)
        except Exception as e:
            log(f"skeletal import data: {e}")
    else:
        opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
        st = opts.get_editor_property("static_mesh_import_data")
        st.set_editor_property("combine_meshes", combine)
        st.set_editor_property("auto_generate_collision", False)
        st.set_editor_property("generate_lightmap_u_vs", False)
        try:
            st.set_editor_property("convert_scene", True)
            st.set_editor_property("convert_scene_unit", True)
            st.set_editor_property("build_nanite", True)
        except Exception as e:
            log(f"static import data: {e}")

    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    log(f"Imported {os.path.basename(path)} -> {len(paths)} assets")
    return paths


def assets_of_class(paths, cls):
    out = []
    for p in paths:
        name = p.rsplit("/", 1)[-1]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, cls):
            out.append(obj)
    return out


def pick_body(meshes):
    if not meshes:
        return None
    for key in ("body", "Body", "upbody"):
        for m in meshes:
            if m.get_name().lower() == key.lower() or m.get_name().lower().startswith(key.lower()):
                return m
    meshes = sorted(meshes, key=lambda m: -len(m.get_imported_bounds().box_extent.to_tuple()) if hasattr(m, "get_imported_bounds") else 0)
    return meshes[0]


def spawn_character(label, meshes, anim, location, rotation):
    body = pick_body(meshes)
    if not body:
        log(f"{label}: no skeletal mesh")
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkeletalMeshActor, location, rotation
    )
    actor.set_actor_label(label)
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(rotation, False)
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    try:
        comp.set_skeletal_mesh_asset(body)
    except Exception:
        comp.set_skeletal_mesh(body)
    if anim:
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.play_animation(anim, True)
        log(f"{label} playing {anim.get_name()}")
    skel = body.get_editor_property("skeleton")
    attached = 0
    for mesh in meshes:
        if mesh == body:
            continue
        if mesh.get_editor_property("skeleton") != skel:
            continue
        part = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkeletalMeshActor, location, rotation
        )
        part.set_actor_label(f"{label}_{mesh.get_name()}")
        pc = part.get_component_by_class(unreal.SkeletalMeshComponent)
        try:
            pc.set_skeletal_mesh_asset(mesh)
        except Exception:
            pc.set_skeletal_mesh(mesh)
        try:
            pc.set_leader_pose_component(comp, True)
        except Exception:
            pass
        part.attach_to_actor(
            actor, "",
            unreal.AttachmentRule.SNAP_TO_TARGET,
            unreal.AttachmentRule.SNAP_TO_TARGET,
            unreal.AttachmentRule.SNAP_TO_TARGET,
            False,
        )
        attached += 1
    log(f"{label} body={body.get_name()} parts={attached}")
    return actor


def add_lighting():
    sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(400, 800, 600), unreal.Rotator(-40, 35, 0)
    )
    sun.set_actor_label("Apt_Sun")
    sc = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if sc:
        sc.set_intensity(8.0)
        try:
            sc.set_editor_property("atmosphere_sun_light", True)
        except Exception:
            pass

    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(400, 800, 700), unreal.Rotator()
    )
    sky.set_actor_label("Apt_SkyLight")
    skc = sky.get_component_by_class(unreal.SkyLightComponent)
    if skc:
        skc.set_intensity(1.4)
        skc.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)

    try:
        sky_atm = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator()
        )
        sky_atm.set_actor_label("Apt_SkyAtmosphere")
    except Exception:
        pass


def spawn_static_from_paths(paths):
    n = 0
    for mesh in assets_of_class(paths, unreal.StaticMesh):
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator()
        )
        actor.set_actor_label(mesh.get_name())
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_static_mesh(mesh)
        n += 1
    log(f"Spawned {n} apartment meshes")
    return n


def world_bounds():
    mn = [1e9, 1e9, 1e9]
    mx = [-1e9, -1e9, -1e9]
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        origin, extent = actor.get_actor_bounds(False)
        for i, v in enumerate((origin.x, origin.y, origin.z)):
            e = (extent.x, extent.y, extent.z)[i]
            mn[i] = min(mn[i], v - e)
            mx[i] = max(mx[i], v + e)
    log(f"Apartment bounds min={mn} max={mx}")
    return mn, mx


def open_map():
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
        for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
            label = actor.get_actor_label()
            if label.startswith(("Cute", "Rosemary", "Ayane", "Apt_", "Group", "Shape", "Object", "BoConcept", "William", "Blanket", "Box")):
                unreal.EditorLevelLibrary.destroy_actor(actor)
        log(f"Loaded {MAP_PATH}")
    else:
        unreal.EditorLoadingAndSavingUtils.new_blank_map(True)
        log("New blank map")


def save_map():
    ensure_dir(CONTENT)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
    )
    log(f"Saved map {MAP_PATH} ok={ok}")


log("=== Apartment scene assemble ===")
open_map()

apt_paths = import_fbx(os.path.join(EXPORTS, "Apartment_Room.fbx"), CONTENT + "/Room", False, combine=True)
spawn_static_from_paths(apt_paths)
world_bounds()

chars = {}
for name, fbx, skel in CHAR_JOBS:
    paths = import_fbx(fbx, CONTENT + "/" + name, skel)
    meshes = assets_of_class(paths, unreal.SkeletalMesh)
    anims = assets_of_class(paths, unreal.AnimSequence)
    log(f"{name}: meshes={[m.get_name() for m in meshes]} anims={[a.get_name() for a in anims]}")
    chars[name] = (meshes, anims[0] if anims else None)

spawn_character("Cute", *chars["Cute"], *WALK0)
spawn_character("Rosemary", *chars["Rosemary"], *SEAT)
spawn_character("Ayane", *chars["Ayane"], *STAND)
add_lighting()
save_map()
log("=== Done ===")
