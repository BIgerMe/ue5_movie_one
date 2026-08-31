"""Slim apartment project: clean L_ApartmentCute, delete unused ApartmentScene assets, set startup map."""
import unreal

CONTENT = "/Game/ApartmentScene"
MAP = CONTENT + "/L_ApartmentCute"

# Level actors to remove (solo level does not need these).
REMOVE_LABELS = {
    "Rosemary", "Ayane",
    "Apt_Col_Rosemary", "Apt_Col_Ayane",
    "Apt_PoseSeq", "Apt_CutePatrol",
    "Apt_FloorCollision",
}

# Whole folders / loose assets safe to delete for Cute-solo workflow.
DELETE_DIRS = (
    CONTENT + "/Ayane",
    CONTENT + "/Rosemary",
    CONTENT + "/CuteBody",
)

DELETE_ASSETS = (
    CONTENT + "/L_ApartmentLiving",
    CONTENT + "/LS_ApartmentPoses",
    CONTENT + "/LS_CutePatrol",
    CONTENT + "/Cute/Cute_SitChair",
)


def log(msg):
    print(f"[Cleanup] {msg}")
    unreal.log(f"[Cleanup] {msg}")


def actors():
    try:
        return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    except Exception:
        return list(unreal.EditorLevelLibrary.get_all_level_actors())


def delete_asset(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        ok = unreal.EditorAssetLibrary.delete_asset(path)
        log(f"delete asset {path} ok={ok}")
        return ok
    return False


def delete_tree(folder):
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        log(f"skip missing {folder}")
        return
    assets = sorted(unreal.EditorAssetLibrary.list_assets(folder, recursive=True), key=len, reverse=True)
    n = 0
    for p in assets:
        if not unreal.EditorAssetLibrary.does_asset_exist(p):
            continue
        try:
            if unreal.EditorAssetLibrary.delete_asset(p):
                n += 1
        except Exception as exc:
            log(f"skip delete {p}: {exc}")
    try:
        unreal.EditorAssetLibrary.delete_directory(folder)
    except Exception as exc:
        log(f"delete_directory {folder}: {exc}")
    log(f"removed {folder} ({n} assets)")


log("=== apartment cleanup ===")

for folder in DELETE_DIRS:
    delete_tree(folder)
for asset in DELETE_ASSETS:
    delete_asset(asset)

world = unreal.EditorLevelLibrary.get_editor_world()
cur = str(world.get_path_name()) if world else ""
if MAP.split("/")[-1] not in cur:
    log(f"load {MAP} (was {cur})")
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)

removed = 0
for a in list(actors()):
    label = a.get_actor_label()
    if label in REMOVE_LABELS:
        unreal.EditorLevelLibrary.destroy_actor(a)
        log(f"removed actor {label}")
        removed += 1

# Keep a single demo sequence driver.
seq_count = 0
for a in actors():
    if a.get_actor_label() == "Apt_CuteSolo":
        seq_count += 1
        if seq_count > 1:
            unreal.EditorLevelLibrary.destroy_actor(a)
            log("removed duplicate Apt_CuteSolo")

ok = unreal.EditorLoadingAndSavingUtils.save_current_level()
log(f"level saved={ok} actors_removed={removed}")

# Drop registry caches so deleted assets are not rescanned from stale refs.
try:
    unreal.EditorAssetLibrary.consolidate_assets([], [])
except Exception:
    pass

log("=== done ===")
