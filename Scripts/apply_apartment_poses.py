"""Import pose clips, place the three girls, hide Rosemary clothes."""
import os
import sys
import unreal

CONTENT = "/Game/ApartmentScene"
MAP_PATH = CONTENT + "/L_ApartmentLiving"
EXPORTS = r"E:\game\scene_build\exports"
HIDE = "/Game/Material/MI_HidePart.MI_HidePart"

CUTE_LOC = unreal.Vector(365.0, -1300.0, 92.0)
CUTE_ROT = unreal.Rotator(pitch=0.0, yaw=45.3, roll=0.0)
ROSE_LOC = unreal.Vector(215.0, -1208.0, 6.0)
ROSE_ROT = unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
AYANE_LOC = unreal.Vector(400.0, -1160.0, 2.0)
AYANE_ROT = unreal.Rotator(pitch=0.0, yaw=-165.0, roll=0.0)


def log(msg):
    print(f"[PoseUE] {msg}")
    unreal.log(f"[PoseUE] {msg}")


def actors():
    try:
        return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    except Exception:
        return list(unreal.EditorLevelLibrary.get_all_level_actors())


def find_assets(folder, cls, *keys):
    out = []
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        return out
    for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        name = p.rsplit("/", 1)[-1]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, cls):
            out.append(obj)
    picked = []
    for k in keys:
        for i in out:
            if k.lower() in i.get_name().lower():
                picked.append(i)
                break
    return picked or out


def import_anim(fbx, dest, skeleton):
    if not os.path.isfile(fbx):
        raise RuntimeError("missing " + fbx)
    if not unreal.EditorAssetLibrary.does_directory_exist(dest):
        unreal.EditorAssetLibrary.make_directory(dest)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path", dest)
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
        opts.set_editor_property("skeleton", skeleton)
    except Exception as e:
        log(f"skeleton: {e}")
    try:
        ad = opts.get_editor_property("anim_sequence_import_data")
        ad.set_editor_property("import_bone_tracks", True)
    except Exception:
        pass
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    log(f"imported {os.path.basename(fbx)}")
    return find_assets(dest, unreal.AnimSequence, os.path.splitext(os.path.basename(fbx))[0])


def play_on_mesh(mesh, anim):
    if not mesh or not anim:
        return
    mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    try:
        mesh.play_animation(anim, False)
    except Exception:
        try:
            mesh.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            data = mesh.get_editor_property("animation_data")
            data.set_editor_property("anim_to_play", anim)
            data.set_editor_property("saved_looping", False)
            data.set_editor_property("saved_playing", True)
            mesh.set_editor_property("animation_data", data)
        except Exception as e:
            log(f"play: {e}")


def hide_rose_clothes(mesh_comp):
    hide = unreal.load_asset(HIDE)
    if not hide or not mesh_comp:
        log("no MI_HidePart or mesh")
        return
    count = 0
    try:
        mats = list(mesh_comp.get_materials() or [])
    except Exception:
        mats = []
    for i, mat in enumerate(mats):
        name = ""
        try:
            name = str(mesh_comp.get_material_slot_names()[i])
        except Exception:
            name = mat.get_name() if mat else ""
        low = name.lower()
        if any(k in low for k in ("shirt", "t-shirt", "t_shirt", "jean", "top", "cloth")) and "sock" not in low:
            mesh_comp.set_material(i, hide)
            count += 1
            log(f"Rosemary slot[{i}] {name} -> MI_HidePart")
    if count == 0:
        # fallback: slots  by typical import order
        for i, key in enumerate(("eyes", "body", "hair", "jean", "t-shirt", "sock")):
            if key in ("jean", "t-shirt"):
                try:
                    mesh_comp.set_material(i, hide)
                    log(f"Rosemary fallback slot {i} {key}")
                    count += 1
                except Exception:
                    pass
    log(f"hidden slots={count}")


def place_actor(label, loc, rot, anim):
    found = None
    for a in actors():
        if a.get_actor_label() == label:
            found = a
            break
    if not found:
        log(f"missing {label}")
        return
    found.set_actor_location(loc, False, False)
    found.set_actor_rotation(rot, False)
    mesh = getattr(found, "skeletal_mesh_component", None) or getattr(found, "mesh", None)
    play_on_mesh(mesh, anim)
    if label == "Rosemary":
        hide_rose_clothes(mesh)
    log(f"placed {label} at ({loc.x:.0f},{loc.y:.0f},{loc.z:.0f})")
    return found


log("=== apply poses ===")
unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)

cute_sk = find_assets(CONTENT + "/Cute", unreal.Skeleton, "Walk", "Cute")[0]
rose_sk = find_assets(CONTENT + "/Rosemary", unreal.Skeleton, "Sit", "Rosemary")[0]
ayane_sk = find_assets(CONTENT + "/Ayane", unreal.Skeleton, "Stand", "Ayane")[0]
log(f"skels cute={cute_sk.get_name()} rose={rose_sk.get_name()} ayane={ayane_sk.get_name()}")

cute_anims = import_anim(os.path.join(EXPORTS, "Cute_SitChair.fbx"), CONTENT + "/Cute", cute_sk)
rose_anims = import_anim(os.path.join(EXPORTS, "Rosemary_LieSofa.fbx"), CONTENT + "/Rosemary", rose_sk)
ayane_anims = import_anim(os.path.join(EXPORTS, "Ayane_LegsUp.fbx"), CONTENT + "/Ayane", ayane_sk)
cute_anim = next((a for a in cute_anims if "sit" in a.get_name().lower()), cute_anims[0] if cute_anims else None)
rose_anim = next((a for a in rose_anims if "lie" in a.get_name().lower()), rose_anims[0] if rose_anims else None)
ayane_anim = next((a for a in ayane_anims if "leg" in a.get_name().lower()), ayane_anims[0] if ayane_anims else None)
log(f"anims cute={cute_anim} rose={rose_anim} ayane={ayane_anim}")

place_actor("Cute", CUTE_LOC, CUTE_ROT, cute_anim)
place_actor("Rosemary", ROSE_LOC, ROSE_ROT, rose_anim)
place_actor("Ayane", AYANE_LOC, AYANE_ROT, ayane_anim)

py_dir = os.path.join(unreal.Paths.project_content_dir(), "Python")
if py_dir not in sys.path:
    sys.path.insert(0, py_dir)
try:
    import cute_apartment_character as cac
    cac.POSE_LOCK_ANIM = cute_anim
except Exception as e:
    log(f"pc hook: {e}")

ok = unreal.EditorLoadingAndSavingUtils.save_map(
    unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
)
log(f"=== Done saved={ok} ===")
