import unreal

CONTENT = "/Game/Characters/Nami"
IDLE_FBX = r"E:\game\epic_assets_other\nami\Nami_idle.fbx"
WALK_FBX = r"E:\game\epic_assets_other\nami\Nami_walk.fbx"
SHOWCASE = f"{CONTENT}/Nami_Showcase"

SLOT_TO_MAT = [
    ("eyes_lashes", "eyes_lashes"),
    ("cutehair", "cutehair"),
    ("sport", "sport"),
    ("sword", "sword"),
    ("jean", "jean"),
    ("belt", "belt"),
    ("hat", "hat"),
    ("body", "body"),
    ("eyes", "eyes"),
]


def log(msg):
    unreal.log(f"[NamiFix] {msg}")


def import_fbx(path, import_mesh=False, skeleton=None):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", path)
    task.set_editor_property("destination_path", CONTENT)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", import_mesh)
    opts.set_editor_property("import_as_skeletal", import_mesh)
    opts.set_editor_property("import_animations", True)
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    if import_mesh:
        opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    elif skeleton:
        opts.set_editor_property("skeleton", skeleton)
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = task.get_editor_property("imported_object_paths") or []
    log(f"Imported {path} (mesh={import_mesh}): {paths}")
    return paths


def import_all():
    idle_paths = import_fbx(IDLE_FBX, import_mesh=True)
    sk = unreal.load_asset(f"{CONTENT}/Nami_idle_Skeleton.Nami_idle_Skeleton")

    walk_paths = import_fbx(WALK_FBX, import_mesh=False, skeleton=sk)
    if not walk_paths:
        log("Anim-only walk import empty; retry with mesh+anim")
        walk_paths = import_fbx(WALK_FBX, import_mesh=True)

    anims = []
    for p in idle_paths + walk_paths:
        name = p.rsplit("/", 1)[-1]
        obj = unreal.load_asset(f"{p}.{name}" if "." not in name else p)
        if isinstance(obj, unreal.AnimSequence):
            anims.append(obj.get_name())
    log(f"Anim sequences: {anims}")
    return sk


def resolve_mat(slot_name):
    s = slot_name.lower()
    for key, mat_name in SLOT_TO_MAT:
        if key in s:
            p = f"{CONTENT}/{mat_name}"
            if unreal.EditorAssetLibrary.does_asset_exist(p):
                return unreal.load_asset(f"{p}.{mat_name}")
    return None


def bind_materials(mesh):
    mats = mesh.get_editor_property("materials")
    bound = 0
    for i, entry in enumerate(mats):
        slot = str(entry.get_editor_property("material_slot_name"))
        mi = resolve_mat(slot)
        if mi:
            entry.set_editor_property("material_interface", mi)
            mats[i] = entry
            bound += 1
            log(f"{slot} -> {mi.get_name()}")
        else:
            log(f"{slot} -> NO MATCH")
    mesh.set_editor_property("materials", mats)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return bound


def pick_anim(prefer_idle=True):
    names = (
        ["Nami_idle_Anim", "Nami_Idle_Anim"]
        if prefer_idle
        else ["Nami_walk_Anim", "Nami_Walk_Anim", "Nami_rigged_all_Anim"]
    )
    for name in names:
        p = f"{CONTENT}/{name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(p):
            continue
        obj = unreal.load_asset(f"{p}.{name}")
        if isinstance(obj, unreal.AnimSequence):
            return obj

    keyword = "idle" if prefer_idle else "walk"
    for asset in unreal.EditorAssetLibrary.list_assets(CONTENT, recursive=True):
        base = asset.split("/")[-1]
        if keyword not in base.lower():
            continue
        obj = unreal.load_asset(f"{asset}.{base}")
        if isinstance(obj, unreal.AnimSequence):
            return obj
    return None


def update_showcase(mesh, anim):
    if not unreal.EditorAssetLibrary.does_asset_exist(SHOWCASE):
        unreal.EditorLoadingAndSavingUtils.new_blank_map(True)
    else:
        unreal.EditorLoadingAndSavingUtils.load_map(SHOWCASE)

    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if actor.get_actor_label().startswith("Nami_"):
            unreal.EditorLevelLibrary.destroy_actor(actor)

    loc = unreal.Vector(0, 0, 0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkeletalMeshActor, loc, unreal.Rotator(0, 0, 0)
    )
    actor.set_actor_label("Nami_Body")
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    comp.set_skinned_asset_and_update(mesh)
    if anim:
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.play_animation(anim, True)
        log(f"Playing {anim.get_name()}")

    unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), SHOWCASE
    )


log("=== Reimport + fix Nami ===")
import_all()

mesh = unreal.load_asset(f"{CONTENT}/Nami_idle.Nami_idle")
if not mesh:
    mesh = unreal.load_asset(f"{CONTENT}/Nami_rigged_all.Nami_rigged_all")
if not mesh:
    raise RuntimeError("No rigged mesh found")

bound = bind_materials(mesh)
log(f"Bound {bound} material slots")

idle = pick_anim(True)
walk = pick_anim(False)
log(f"idle={idle.get_name() if idle else None} walk={walk.get_name() if walk else None}")

update_showcase(mesh, walk or idle)
log("=== Done ===")
