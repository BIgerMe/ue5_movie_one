"""Restore deleted Cute_Walk skeletal mesh and rebind BP + L_ApartmentCute Cute actor."""
import os
import unreal

CONTENT = "/Game/ApartmentScene"
MAP = CONTENT + "/L_ApartmentCute"
MESH_PATH = CONTENT + "/Cute/Cute_Walk.Cute_Walk"
STAND = CONTENT + "/Cute/Cute_Stand_Open.Cute_Stand_Open"
BP = CONTENT + "/BP_CuteGirl.BP_CuteGirl"
FBX = r"E:\game\scene_build\exports\Cute_Walk_Mesh.fbx"


def log(msg):
    print(f"[RestoreMesh] {msg}")
    unreal.log(f"[RestoreMesh] {msg}")


def find_sk():
    for p in unreal.EditorAssetLibrary.list_assets(CONTENT + "/Cute", recursive=True):
        name = p.rsplit("/", 1)[-1]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, unreal.Skeleton):
            return obj
    return None


def import_mesh(fbx, skel):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path", CONTENT + "/Cute")
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", True)
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    opts.set_editor_property("import_as_skeletal", True)
    opts.set_editor_property("import_animations", False)
    opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    opts.set_editor_property("skeleton", skel)
    try:
        sk = opts.get_editor_property("skeletal_mesh_import_data")
        sk.set_editor_property("import_morph_targets", True)
        sk.set_editor_property("use_t0_as_ref_pose", True)
        sk.set_editor_property("convert_scene", True)
        sk.set_editor_property("convert_scene_unit", True)
    except Exception:
        pass
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    log(f"imported {os.path.basename(fbx)} -> {paths}")
    for p in paths:
        name = p.rsplit("/", 1)[-1].split(".")[0]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, unreal.SkeletalMesh):
            return obj
    mesh = unreal.load_asset(MESH_PATH)
    if mesh:
        return mesh
    alt = unreal.load_asset(CONTENT + "/Cute/Cute_Walk_Mesh.Cute_Walk_Mesh")
    if alt and unreal.EditorAssetLibrary.does_asset_exist(CONTENT + "/Cute/Cute_Walk_Mesh"):
        unreal.EditorAssetLibrary.rename_asset(CONTENT + "/Cute/Cute_Walk_Mesh", CONTENT + "/Cute/Cute_Walk")
        log("renamed Cute_Walk_Mesh -> Cute_Walk")
        return unreal.load_asset(MESH_PATH)
    return alt


def bind(comp, mesh, anim):
    if not comp:
        return
    if mesh:
        comp.set_skeletal_mesh(mesh)
    if anim:
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        try:
            comp.play_animation(anim, True)
        except Exception:
            pass


log("start")
if not os.path.isfile(FBX):
    raise RuntimeError(f"missing {FBX} — run export_cute_mesh_only.py in Blender first")
skel = find_sk()
if not skel:
    raise RuntimeError("Cute_Walk_Skeleton missing")
mesh = import_mesh(FBX, skel)
if not mesh:
    raise RuntimeError("Cute_Walk mesh import failed")
log(f"mesh={mesh.get_name()}")

bp = unreal.load_asset(BP)
if bp:
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo and cdo.mesh:
        cdo.mesh.set_skeletal_mesh(mesh)
        log("BP_CuteGirl CDO mesh restored")
    unreal.EditorAssetLibrary.save_loaded_asset(bp)

world = unreal.EditorLevelLibrary.get_editor_world()
if "L_ApartmentCute" not in str(world.get_path_name()):
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)

stand = unreal.load_asset(STAND)
try:
    acts = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
except Exception:
    acts = list(unreal.EditorLevelLibrary.get_all_level_actors())
for a in acts:
    if a.get_actor_label() == "Cute":
        m = getattr(a, "mesh", None) or getattr(a, "skeletal_mesh_component", None)
        bind(m, mesh, stand)
        log("level Cute actor rebound")
        break

unreal.EditorLoadingAndSavingUtils.save_current_level()
log("done")
