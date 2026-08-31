"""Reimport Cute_Idle / Cute_Walk with skeletal-mesh pipeline (fixes Interchange anim-only failure)."""
import os
import unreal

CONTENT = "/Game/ApartmentScene"
EXPORTS = r"E:\game\scene_build\exports"
JOBS = (
    ("Cute_Idle_Anim.fbx", "Idle"),
    ("Cute_Walk_Anim.fbx", "Walk"),
)


def log(msg):
    print(f"[IdleWalk] {msg}")
    unreal.log(f"[IdleWalk] {msg}")


def find_sk():
    for p in unreal.EditorAssetLibrary.list_assets(CONTENT + "/Cute", recursive=True):
        name = p.rsplit("/", 1)[-1]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, unreal.Skeleton):
            return obj
    return None


def import_fbx(fbx, skel):
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
    opts.set_editor_property("skeleton", skel)
    try:
        ad = opts.get_editor_property("anim_sequence_import_data")
        ad.set_editor_property("import_bone_tracks", True)
    except Exception:
        pass
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    log(f"{os.path.basename(fbx)} -> {paths}")
    return paths


log("start")
skel = find_sk()
if not skel:
    raise RuntimeError("skeleton missing")
# Never delete Cute_Walk — it is the character skeletal mesh used by BP_CuteGirl.
for fname, _tag in JOBS:
    fbx = os.path.join(EXPORTS, fname)
    if os.path.isfile(fbx):
        import_fbx(fbx, skel)
    else:
        log(f"missing {fbx}")
log("done")
