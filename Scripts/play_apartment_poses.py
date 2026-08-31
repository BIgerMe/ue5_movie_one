"""Make the three pose clips actually play in PIE.

Editor play_animation() does not persist.  This:
1. Rebinds each clip to the mesh skeleton
2. Writes AnimationSingleNode + AnimToPlay onto the placed actors
3. Adds LS_ApartmentPoses (auto-play, no loop) so Play starts the 2s transition
"""
import unreal

CONTENT = "/Game/ApartmentScene"
MAP_PATH = CONTENT + "/L_ApartmentLiving"
SEQ_PATH = CONTENT + "/LS_ApartmentPoses"
FPS = 24
END_FRAME = 96

CLIPS = {
    "Cute": "/Game/ApartmentScene/Cute/Cute_SitChair.Cute_SitChair",
    "Rosemary": "/Game/ApartmentScene/Rosemary/Rosemary_LieSofa.Rosemary_LieSofa",
    "Ayane": "/Game/ApartmentScene/Ayane/Ayane_LegsUp.Ayane_LegsUp",
}


def log(msg):
    print(f"[PlayPose] {msg}")
    unreal.log(f"[PlayPose] {msg}")


def actors():
    try:
        return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    except Exception:
        return list(unreal.EditorLevelLibrary.get_all_level_actors())


def load_anim(path):
    obj = unreal.load_asset(path)
    if obj:
        return obj
    folder, name = path.rsplit("/", 1)
    folder = folder.rsplit("/", 1)[0] if "." in name else folder
    short = name.split(".")[0]
    if unreal.EditorAssetLibrary.does_directory_exist(folder):
        for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
            if short.lower() in p.rsplit("/", 1)[-1].lower() and "skeleton" not in p.lower():
                a = unreal.load_asset(p if "." in p.rsplit("/", 1)[-1] else p + "." + p.rsplit("/", 1)[-1])
                if isinstance(a, unreal.AnimSequence):
                    return a
    return None


def mesh_of(actor):
    return getattr(actor, "skeletal_mesh_component", None) or getattr(actor, "mesh", None)


def inspect_anim(anim):
    if not anim:
        log("anim=None")
        return
    sk = None
    length = None
    try:
        sk = anim.get_editor_property("skeleton")
    except Exception:
        pass
    try:
        length = anim.get_editor_property("sequence_length")
    except Exception:
        try:
            length = float(anim.get_play_length())
        except Exception:
            pass
    log(f"anim {anim.get_name()} sk={sk.get_name() if sk else None} len={length}")


def bind_and_play(comp, anim):
    if not comp or not anim:
        return False
    sk_mesh = None
    try:
        sk_asset = comp.skeletal_mesh
        sk_mesh = sk_asset.get_editor_property("skeleton") if sk_asset else None
    except Exception:
        pass
    try:
        sk_anim = anim.get_editor_property("skeleton")
        if sk_mesh and sk_anim != sk_mesh:
            anim.set_editor_property("skeleton", sk_mesh)
            unreal.EditorAssetLibrary.save_loaded_asset(anim)
            log(f"rebound {anim.get_name()} -> {sk_mesh.get_name()}")
    except Exception as e:
        log(f"rebind: {e}")
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    ok = False
    try:
        data = unreal.SingleAnimationPlayData()
        data.set_editor_property("anim_to_play", anim)
        data.set_editor_property("saved_looping", False)
        data.set_editor_property("saved_playing", True)
        try:
            data.set_editor_property("saved_position", 0.0)
        except Exception:
            pass
        comp.set_editor_property("animation_data", data)
        ok = True
    except Exception as e:
        log(f"animation_data: {e}")
    try:
        comp.override_animation_data(anim, False, True, 0.0, 1.0)
        ok = True
    except Exception:
        pass
    try:
        comp.play_animation(anim, False)
        ok = True
    except Exception as e:
        log(f"play_animation: {e}")
    return ok


def add_anim_track(seq, actor, anim, frames):
    binding = seq.add_possessable(actor)
    track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    sec = track.add_section()
    try:
        sec.set_range(0, frames)
    except Exception:
        sec.set_start_frame(0)
        sec.set_end_frame(frames)
    try:
        params = sec.get_editor_property("params")
        params.set_editor_property("animation", anim)
        try:
            params.set_editor_property("slot_name", "DefaultSlot")
        except Exception:
            pass
    except Exception:
        try:
            sec.set_editor_property("animation", anim)
        except Exception as e:
            log(f"set animation: {e}")
    for prop, val in (("loop", False), ("force_custom_mode", False)):
        try:
            sec.set_editor_property(prop, val)
        except Exception:
            pass
    log(f"seq track {actor.get_actor_label()} -> {anim.get_name()}")
    return binding


def build_sequence(bindings):
    if unreal.EditorAssetLibrary.does_asset_exist(SEQ_PATH):
        unreal.EditorAssetLibrary.delete_asset(SEQ_PATH)
    factory = unreal.LevelSequenceFactoryNew()
    seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "LS_ApartmentPoses", CONTENT, unreal.LevelSequence, factory
    )
    try:
        seq.set_display_rate(unreal.FrameRate(FPS, 1))
        seq.set_playback_start(0)
        seq.set_playback_end(END_FRAME)
    except Exception as e:
        log(f"range: {e}")
    for actor, anim in bindings:
        try:
            add_anim_track(seq, actor, anim, END_FRAME)
        except Exception as e:
            log(f"track {actor.get_actor_label()}: {e}")
    unreal.EditorAssetLibrary.save_loaded_asset(seq)

    for a in list(actors()):
        if a.get_actor_label() in ("Apt_PoseSeq", "Apt_CutePatrol"):
            unreal.EditorLevelLibrary.destroy_actor(a)
    lsa = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.LevelSequenceActor, unreal.Vector(0, 0, 0), unreal.Rotator()
    )
    lsa.set_actor_label("Apt_PoseSeq")
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
        try:
            ps.set_editor_property("play_rate", 1.0)
        except Exception:
            pass
        lsa.set_editor_property("playback_settings", ps)
    except Exception as e:
        log(f"playback_settings: {e}")
    for prop, val in (("auto_play", True), ("autoplay", True)):
        try:
            lsa.set_editor_property(prop, val)
        except Exception:
            pass
    log("spawned Apt_PoseSeq auto_play")
    return seq


log("=== force pose playback ===")
unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)

found = {}
for a in actors():
    label = a.get_actor_label()
    if label in CLIPS:
        found[label] = a
        log(f"found {label} {a.get_class().get_name()}")

bindings = []
for label, path in CLIPS.items():
    anim = load_anim(path)
    inspect_anim(anim)
    actor = found.get(label)
    if not actor:
        log(f"MISSING actor {label}")
        continue
    if not anim:
        log(f"MISSING anim {path}")
        continue
    ok = bind_and_play(mesh_of(actor), anim)
    log(f"bound {label} ok={ok}")
    bindings.append((actor, anim))

if bindings:
    build_sequence(bindings)

ok = unreal.EditorLoadingAndSavingUtils.save_map(
    unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
)
log(f"=== Done saved={ok} ===")
