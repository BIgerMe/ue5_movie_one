"""Reimport Cute solo clips and rebind IdleStand on L_ApartmentCute. No map rebuild."""
import os
import unreal

CONTENT = "/Game/ApartmentScene"
MAP = CONTENT + "/L_ApartmentCute"
EXPORTS = r"E:\game\scene_build\exports"
CLIPS = (
    os.path.join(EXPORTS, "Cute_IdleStand.fbx"),
    os.path.join(EXPORTS, "Cute_SitDown.fbx"),
    os.path.join(EXPORTS, "Cute_SitOpen.fbx"),
)


def log(msg):
    print(f"[Reimport] {msg}")
    unreal.log(f"[Reimport] {msg}")


def find_first(folder, cls, *keys):
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        return None
    items = []
    for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        name = p.rsplit("/", 1)[-1]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, cls):
            items.append(obj)
    for k in keys:
        for i in items:
            if k.lower() in i.get_name().lower():
                return i
    return items[0] if items else None


log("start")
skel = find_first(CONTENT + "/Cute", unreal.Skeleton, "Walk", "Cute")
if not skel:
    raise RuntimeError("Cute skeleton missing")
for fbx in CLIPS:
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path", CONTENT + "/Cute")
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", False)
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    opts.set_editor_property("import_as_skeletal", True)
    opts.set_editor_property("import_animations", True)
    opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    try:
        opts.set_editor_property("skeleton", skel)
    except Exception:
        pass
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    log(f"imported {os.path.basename(fbx)}")

idle = find_first(CONTENT + "/Cute", unreal.AnimSequence, "IdleStand")
world = unreal.EditorLevelLibrary.get_editor_world()
cur = str(world.get_path_name()) if world else ""
if "L_ApartmentCute" not in cur and unreal.EditorAssetLibrary.does_asset_exist(MAP):
    log(f"loading {MAP} (was {cur})")
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)

try:
    acts = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
except Exception:
    acts = list(unreal.EditorLevelLibrary.get_all_level_actors())
for a in acts:
    if a.get_actor_label() != "Cute":
        continue
    mesh = getattr(a, "mesh", None) or getattr(a, "skeletal_mesh_component", None)
    if not mesh or not idle:
        continue
    mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    try:
        data = unreal.SingleAnimationPlayData()
        data.set_editor_property("anim_to_play", idle)
        data.set_editor_property("saved_looping", True)
        data.set_editor_property("saved_playing", True)
        mesh.set_editor_property("animation_data", data)
    except Exception:
        pass
    try:
        mesh.play_animation(idle, True)
    except Exception:
        pass
    log("Cute rebound to IdleStand")
    break

ok = unreal.EditorLoadingAndSavingUtils.save_current_level()
log(f"done saved={ok} idle={idle}")
