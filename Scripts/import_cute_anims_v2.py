"""Import all Cute v2 animations, update LS_CuteSolo, bind default pose."""
import os
import unreal

CONTENT = "/Game/ApartmentScene"
MAP = CONTENT + "/L_ApartmentCute"
SEQ = CONTENT + "/LS_CuteSolo"
EXPORTS = r"E:\game\scene_build\exports"
FPS = 24

# New names (v2). Old assets removed after import.
CLIPS = (
    ("Cute_Idle", "Cute_Idle_Anim.fbx"),
    ("Cute_Walk", "Cute_Walk_Anim.fbx"),
    ("Cute_Stand_Open", "Cute_Stand_Open.fbx"),
    ("Cute_Sit_Chair", "Cute_Sit_Chair.fbx"),
    ("Cute_Sit_LeanBack", "Cute_Sit_LeanBack.fbx"),
)
OLD = (
    CONTENT + "/Cute/Cute_IdleStand",
    CONTENT + "/Cute/Cute_SitDown",
    CONTENT + "/Cute/Cute_SitOpen",
)
WALK = CONTENT + "/Cute/Cute_Walk_Anim.Cute_Walk_Anim"


def log(msg):
    print(f"[ImportV2] {msg}")
    unreal.log(f"[ImportV2] {msg}")


def find_sk():
    for p in unreal.EditorAssetLibrary.list_assets(CONTENT + "/Cute", recursive=True):
        if "Skeleton" in p or p.endswith("Cute_Walk_Skeleton"):
            obj = unreal.load_asset(p)
            if isinstance(obj, unreal.Skeleton):
                return obj
    for p in unreal.EditorAssetLibrary.list_assets(CONTENT + "/Cute", recursive=True):
        name = p.rsplit("/", 1)[-1]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, unreal.Skeleton):
            return obj
    return None


def import_fbx(fbx, skel, anim_only=False):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path", CONTENT + "/Cute")
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    opts.set_editor_property("import_as_skeletal", True)
    opts.set_editor_property("import_animations", True)
    if anim_only:
        opts.set_editor_property("import_mesh", False)
        opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    else:
        opts.set_editor_property("import_mesh", True)
        opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
        try:
            sk = opts.get_editor_property("skeletal_mesh_import_data")
            sk.set_editor_property("import_morph_targets", True)
            sk.set_editor_property("use_t0_as_ref_pose", False)
        except Exception:
            pass
    try:
        opts.set_editor_property("skeleton", skel)
    except Exception:
        pass
    try:
        ad = opts.get_editor_property("anim_sequence_import_data")
        ad.set_editor_property("import_bone_tracks", True)
    except Exception:
        pass
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])


def pick_anim(keyword):
    for p in unreal.EditorAssetLibrary.list_assets(CONTENT + "/Cute", recursive=True):
        if keyword.lower() in p.lower():
            name = p.rsplit("/", 1)[-1]
            obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
            if isinstance(obj, unreal.AnimSequence):
                return obj
    return None


def bind(comp, anim, loop=True):
    if not comp or not anim:
        return
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    try:
        d = unreal.SingleAnimationPlayData()
        d.set_editor_property("anim_to_play", anim)
        d.set_editor_property("saved_looping", loop)
        d.set_editor_property("saved_playing", True)
        comp.set_editor_property("animation_data", d)
    except Exception:
        pass
    try:
        comp.play_animation(anim, loop)
    except Exception:
        pass


log("start")
skel = find_sk()
if not skel:
    raise RuntimeError("skeleton missing")

for _name, fname in CLIPS:
    fbx = os.path.join(EXPORTS, fname)
    if os.path.isfile(fbx):
        anim_only = fname not in ("Cute_Idle_Anim.fbx", "Cute_Walk_Anim.fbx")
        import_fbx(fbx, skel, anim_only=anim_only)
        log(f"imported {fname}")
    else:
        log(f"missing {fbx}")

for old in OLD:
    if unreal.EditorAssetLibrary.does_asset_exist(old):
        unreal.EditorAssetLibrary.delete_asset(old)
        log(f"deleted old {old}")

stand = pick_anim("Stand_Open")
sit = pick_anim("Sit_Chair")
lean = pick_anim("Sit_LeanBack")
walk = unreal.load_asset(WALK)
log(f"anims stand={stand} sit={sit} lean={lean} walk={walk}")

world = unreal.EditorLevelLibrary.get_editor_world()
if "L_ApartmentCute" not in str(world.get_path_name()):
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)

try:
    acts = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
except Exception:
    acts = list(unreal.EditorLevelLibrary.get_all_level_actors())

cute = None
for a in acts:
    if a.get_actor_label() == "Cute":
        cute = a
        mesh = getattr(a, "mesh", None) or getattr(a, "skeletal_mesh_component", None)
        bind(mesh, stand or pick_anim("Idle"), True)
        log("Cute default = Stand_Open")
        break

if cute and stand and sit and lean and walk:
    if unreal.EditorAssetLibrary.does_asset_exist(SEQ):
        unreal.EditorAssetLibrary.delete_asset(SEQ)
    seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "LS_CuteSolo", CONTENT, unreal.LevelSequence, unreal.LevelSequenceFactoryNew()
    )
    shots = ((walk, 0, 48, True), (sit, 48, 120, False), (lean, 120, 168, True))
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
            sec.set_editor_property("animation", anim)
        try:
            sec.set_editor_property("loop", looping)
        except Exception:
            pass
    unreal.EditorAssetLibrary.save_loaded_asset(seq)
    for a in list(acts):
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
        lsa.set_editor_property("playback_settings", ps)
    except Exception:
        pass
    log("LS_CuteSolo updated")

unreal.EditorLoadingAndSavingUtils.save_current_level()
log("done")
