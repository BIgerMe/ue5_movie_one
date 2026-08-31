"""Reimport Cute_Walk mesh (rest pose) and restore shirt/jean original materials."""
import os
import unreal

CONTENT = "/Game/ApartmentScene"
MAP = CONTENT + "/L_ApartmentCute"
MESH_PATH = CONTENT + "/Cute/Cute_Walk.Cute_Walk"
STAND = CONTENT + "/Cute/Cute_Stand_Open.Cute_Stand_Open"
BP = CONTENT + "/BP_CuteGirl.BP_CuteGirl"
FBX = r"E:\game\scene_build\exports\Cute_Walk_Mesh.fbx"

# Slot name fragment -> original material in /Cute
MAT_MAP = (
    ("body", CONTENT + "/Cute/body.body"),
    ("shirt", CONTENT + "/Cute/shirt.shirt"),
    ("jean", CONTENT + "/Cute/jean.jean"),
    ("hair", CONTENT + "/Cute/hair.hair"),
    ("eye", CONTENT + "/Cute/eyes.eyes"),
    ("teeth", CONTENT + "/Cute/teeth.teeth"),
    ("tongue", CONTENT + "/Cute/teeth.teeth"),
)


def log(msg):
    print(f"[FixCute] {msg}")
    unreal.log(f"[FixCute] {msg}")


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
    opts.set_editor_property("import_materials", True)
    opts.set_editor_property("import_textures", True)
    opts.set_editor_property("import_as_skeletal", True)
    opts.set_editor_property("import_animations", False)
    opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    opts.set_editor_property("skeleton", skel)
    try:
        sk = opts.get_editor_property("skeletal_mesh_import_data")
        sk.set_editor_property("import_morph_targets", True)
        sk.set_editor_property("use_t0_as_ref_pose", False)
        sk.set_editor_property("convert_scene", True)
        sk.set_editor_property("convert_scene_unit", True)
    except Exception:
        pass
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    log(f"import -> {paths}")
    for p in paths:
        name = p.rsplit("/", 1)[-1].split(".")[0]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, unreal.SkeletalMesh):
            if name != "Cute_Walk" and unreal.EditorAssetLibrary.does_asset_exist(p.rsplit(".", 1)[0] if "." in p else p):
                base = p.rsplit("/", 1)[0]
                if unreal.EditorAssetLibrary.does_asset_exist(CONTENT + "/Cute/Cute_Walk"):
                    unreal.EditorAssetLibrary.delete_asset(CONTENT + "/Cute/Cute_Walk")
                unreal.EditorAssetLibrary.rename_asset(
                    p.rsplit(".", 1)[0] if "." in p.rsplit("/", 1)[-1] else p,
                    CONTENT + "/Cute/Cute_Walk",
                )
                return unreal.load_asset(MESH_PATH)
            return obj
    return unreal.load_asset(MESH_PATH)


def restore_materials(mesh):
    if not mesh:
        return 0
    slots = list(mesh.get_editor_property("materials") or [])
    n = 0
    for i, slot in enumerate(slots):
        try:
            sname = str(slot.get_editor_property("material_slot_name")).lower()
        except Exception:
            sname = ""
        chosen = None
        for key, path in MAT_MAP:
            if key in sname:
                chosen = unreal.load_asset(path)
                break
        if not chosen:
            log(f"  slot[{i}] {sname} keep import mat")
            continue
        slot.set_editor_property("material_interface", chosen)
        slots[i] = slot
        n += 1
        log(f"  slot[{i}] {sname} -> {chosen.get_name()}")
    mesh.set_editor_property("materials", slots)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return n


def restore_component_materials(comp, mesh):
    if not comp or not mesh:
        return
    try:
        names = [str(n).lower() for n in (comp.get_material_slot_names() or [])]
    except Exception:
        names = []
    for i, sname in enumerate(names):
        chosen = None
        for key, path in MAT_MAP:
            if key in sname:
                chosen = unreal.load_asset(path)
                break
        if chosen:
            try:
                comp.set_material(i, chosen)
            except Exception:
                pass


def bind(comp, mesh, anim):
    if not comp:
        return
    if mesh:
        try:
            comp.set_skinned_asset_and_update(mesh)
        except Exception:
            comp.set_skeletal_mesh(mesh)
    restore_component_materials(comp, mesh)
    if anim:
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        try:
            comp.play_animation(anim, True)
        except Exception:
            pass


log("start")
if not os.path.isfile(FBX):
    raise RuntimeError(f"missing {FBX}")
skel = find_sk()
if not skel:
    raise RuntimeError("skeleton missing")

mesh = import_mesh(FBX, skel)
if not mesh:
    raise RuntimeError("mesh import failed")
log(f"mesh={mesh.get_name()}")
restore_materials(mesh)

bp = unreal.load_asset(BP)
if bp:
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo and cdo.mesh:
        bind(cdo.mesh, mesh, None)
        log("BP mesh restored")
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
        log("level Cute rebound")
        break

unreal.EditorLoadingAndSavingUtils.save_current_level()
log("done")
