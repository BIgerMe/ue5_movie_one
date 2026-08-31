"""Create L_ApartmentCute: room only + white-shirt girl, reusable pose clips."""
import os
import unreal

CONTENT = "/Game/ApartmentScene"
SRC_MAP = CONTENT + "/L_ApartmentLiving"
NEW_MAP = CONTENT + "/L_ApartmentCute"
SEQ_PATH = CONTENT + "/LS_CuteSolo"
EXPORTS = r"E:\game\scene_build\exports"
FPS = 24

CLIPS = [
    ("Cute_IdleStand", os.path.join(EXPORTS, "Cute_IdleStand.fbx"), 48),
    ("Cute_SitDown", os.path.join(EXPORTS, "Cute_SitDown.fbx"), 72),
    ("Cute_SitOpen", os.path.join(EXPORTS, "Cute_SitOpen.fbx"), 48),
]

CUTE_LOC = unreal.Vector(365.0, -1300.0, 92.0)
CUTE_ROT = unreal.Rotator(pitch=0.0, yaw=45.3, roll=0.0)
WALK = "/Game/ApartmentScene/Cute/Cute_Walk_Anim.Cute_Walk_Anim"


def log(msg):
    print(f"[CuteSolo] {msg}")
    unreal.log(f"[CuteSolo] {msg}")


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
    except Exception:
        pass
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    log(f"imported {os.path.basename(fbx)}")


def pick_anim(name):
    items = find_assets(CONTENT + "/Cute", unreal.AnimSequence, name)
    return items[0] if items else None


def bind_mesh(comp, anim, looping=False):
    if not comp or not anim:
        return
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    try:
        data = unreal.SingleAnimationPlayData()
        data.set_editor_property("anim_to_play", anim)
        data.set_editor_property("saved_looping", looping)
        data.set_editor_property("saved_playing", True)
        comp.set_editor_property("animation_data", data)
    except Exception:
        pass
    try:
        comp.play_animation(anim, looping)
    except Exception:
        pass


def add_anim_section(seq, actor, anim, start, end, looping=False):
    binding = seq.add_possessable(actor)
    track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    sec = track.add_section()
    try:
        sec.set_range(start, end)
    except Exception:
        sec.set_start_frame(start)
        sec.set_end_frame(end)
    try:
        params = sec.get_editor_property("params")
        params.set_editor_property("animation", anim)
    except Exception:
        try:
            sec.set_editor_property("animation", anim)
        except Exception as e:
            log(f"anim section: {e}")
    try:
        sec.set_editor_property("loop", looping)
    except Exception:
        pass
    log(f"seq {start}-{end} {anim.get_name()}")
    return binding


log("=== cute solo level ===")
skels = find_assets(CONTENT + "/Cute", unreal.Skeleton, "Walk", "Cute")
skel = skels[0] if skels else None
if not skel:
    raise RuntimeError("Cute skeleton missing")
for name, fbx, _n in CLIPS:
    if os.path.isfile(fbx):
        import_anim(fbx, CONTENT + "/Cute", skel)
    else:
        log(f"missing fbx {fbx}")

world = unreal.EditorLevelLibrary.get_editor_world()
cur = ""
try:
    cur = str(world.get_path_name())
except Exception:
    pass
# One map load max. Prefer the living source; Save-As writes L_ApartmentCute.
if "L_ApartmentLiving" not in cur and "L_ApartmentCute" not in cur:
    log(f"loading living source (current={cur})")
    unreal.EditorLoadingAndSavingUtils.load_map(SRC_MAP)
else:
    log(f"reuse open map {cur}")

remove = (
    "Rosemary", "Ayane", "Apt_Col_Rosemary", "Apt_Col_Ayane",
    "Apt_PoseSeq", "Apt_CutePatrol",
)
for a in list(actors()):
    if a.get_actor_label() in remove:
        unreal.EditorLevelLibrary.destroy_actor(a)
        log(f"removed {a.get_actor_label()}")

idle = pick_anim("IdleStand")
sit = pick_anim("SitDown")
openp = pick_anim("SitOpen")
walk = unreal.load_asset(WALK)
log(f"clips idle={idle} sit={sit} open={openp} walk={walk}")

cute = None
for a in actors():
    if a.get_actor_label() == "Cute":
        cute = a
        break
if cute:
    cute.set_actor_location(CUTE_LOC, False, False)
    cute.set_actor_rotation(CUTE_ROT, False)
    mesh = getattr(cute, "mesh", None) or getattr(cute, "skeletal_mesh_component", None)
    bind_mesh(mesh, idle or walk, looping=True)
    log("Cute default = IdleStand")
else:
    log("Cute actor missing in new map")

if cute and walk and sit and openp:
    if unreal.EditorAssetLibrary.does_asset_exist(SEQ_PATH):
        unreal.EditorAssetLibrary.delete_asset(SEQ_PATH)
    factory = unreal.LevelSequenceFactoryNew()
    seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "LS_CuteSolo", CONTENT, unreal.LevelSequence, factory
    )
    # walk 48 + sit 72 + open 48 = 168 frames (~7s)
    shots = ((walk, 0, 48, True), (sit, 48, 120, False), (openp, 120, 168, True))
    try:
        seq.set_display_rate(unreal.FrameRate(FPS, 1))
        seq.set_playback_start(0)
        seq.set_playback_end(168)
    except Exception:
        pass
    binding = seq.add_possessable(cute)
    track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    for anim, start, end, looping in shots:
        sec = track.add_section()
        try:
            sec.set_range(start, end)
        except Exception:
            sec.set_start_frame(start)
            sec.set_end_frame(end)
        try:
            params = sec.get_editor_property("params")
            params.set_editor_property("animation", anim)
        except Exception:
            try:
                sec.set_editor_property("animation", anim)
            except Exception as e:
                log(f"anim section: {e}")
        try:
            sec.set_editor_property("loop", looping)
        except Exception:
            pass
        log(f"seq {start}-{end} {anim.get_name()}")
    unreal.EditorAssetLibrary.save_loaded_asset(seq)

    for a in list(actors()):
        if a.get_actor_label() == "Apt_CuteSolo":
            unreal.EditorLevelLibrary.destroy_actor(a)
    lsa = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.LevelSequenceActor, unreal.Vector(0, 0, 0), unreal.Rotator()
    )
    lsa.set_actor_label("Apt_CuteSolo")
    try:
        lsa.set_sequence(seq)
    except Exception:
        lsa.set_editor_property("level_sequence_asset", seq)
    try:
        ps = lsa.get_editor_property("playback_settings")
        ps.set_editor_property("auto_play", True)
        try:
            ps.set_editor_property("loop_count", unreal.MovieSceneSequenceLoopCount(0))
        except Exception:
            pass
        lsa.set_editor_property("playback_settings", ps)
    except Exception as e:
        log(f"playback: {e}")
    log("Apt_CuteSolo auto-play sequence ready")

ok = unreal.EditorLoadingAndSavingUtils.save_map(
    unreal.EditorLevelLibrary.get_editor_world(), NEW_MAP
)
log(f"=== Done saved={ok} map={NEW_MAP} ===")
