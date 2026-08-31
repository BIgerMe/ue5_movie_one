import unreal

CONTENT = "/Game/Characters/Nami"
RIGGED_MESH = f"{CONTENT}/Nami_rigged_all"
SHOWCASE = f"{CONTENT}/Nami_Showcase"

# material slot keyword -> material instance asset name
SLOT_TO_MAT = [
    ("eyes_lashes", "eyes_lashes"),
    ("eyelash", "eyes_lashes"),
    ("cutehair", "cutehair"),
    ("sport", "sport"),
    ("sword", "sword"),
    ("katana", "sword"),
    ("jean", "jean"),
    ("boot", "jean"),
    ("belt", "belt"),
    ("hat", "hat"),
    ("body", "body"),
    ("eyes", "eyes"),
    ("eye", "eyes"),
]


def log(msg):
    unreal.log(f"[NamiFix] {msg}")


def resolve_mat(slot_name):
    s = slot_name.lower()
    for key, mat_name in SLOT_TO_MAT:
        if key in s:
            path = f"{CONTENT}/{mat_name}"
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                return unreal.load_asset(f"{path}.{mat_name}")
    return None


def bind_all_materials(mesh):
    mats = mesh.get_editor_property("materials")
    changed = 0
    for i, entry in enumerate(mats):
        slot = str(entry.get_editor_property("material_slot_name"))
        mi = resolve_mat(slot)
        if not mi:
            # fallback: try slot basename
            base = slot.split(".")[-1]
            mi = resolve_mat(base)
        if mi:
            entry.set_editor_property("material_interface", mi)
            mats[i] = entry
            changed += 1
            log(f"Slot[{i}] {slot} -> {mi.get_name()}")
        else:
            log(f"Slot[{i}] {slot} -> NO MATCH")
    mesh.set_editor_property("materials", mats)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return changed


def find_anims():
    idle = walk = None
    for asset in unreal.EditorAssetLibrary.list_assets(CONTENT, recursive=True):
        name = asset.split("/")[-1]
        obj = unreal.load_asset(f"{asset}.{name}")
        if not isinstance(obj, unreal.AnimSequence):
            continue
        low = name.lower()
        if "idle" in low or "stand" in low:
            idle = obj
        elif "walk" in low:
            walk = obj
    # fallback names from import
    for name, var in [("Nami_Idle", "idle"), ("Nami_Walk", "walk"), ("Nami_rigged_all_Anim", "walk")]:
        p = f"{CONTENT}/{name}"
        if unreal.EditorAssetLibrary.does_asset_exist(p):
            obj = unreal.load_asset(f"{p}.{name}")
            if isinstance(obj, unreal.AnimSequence):
                if var == "idle" and not idle:
                    idle = obj
                if var == "walk" and not walk:
                    walk = obj
    return idle, walk


def refresh_showcase(mesh, idle):
    if not unreal.EditorAssetLibrary.does_asset_exist(SHOWCASE):
        return
    unreal.EditorLoadingAndSavingUtils.load_map(SHOWCASE)
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if not actor.get_actor_label().startswith("Nami_"):
            continue
        comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
        if not comp:
            continue
        comp.set_skeletal_mesh(mesh)
        if idle:
            comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            comp.play_animation(idle, True)
    unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), SHOWCASE
    )
    log("Showcase updated with materials mesh + idle anim")


log("=== Nami fix colors + idle ===")
mesh = unreal.load_asset(f"{RIGGED_MESH}.Nami_rigged_all")
if not mesh:
    raise RuntimeError("Nami_rigged_all not found")

n = bind_all_materials(mesh)
log(f"Bound {n} material slots")

idle, walk = find_anims()
log(f"Anims idle={idle.get_name() if idle else None} walk={walk.get_name() if walk else None}")

if idle:
    refresh_showcase(mesh, idle)
log("=== Done ===")
