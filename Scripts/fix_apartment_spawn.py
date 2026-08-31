"""Spawn characters and patrol sequence using assets already imported by Interchange.

UE 5.8 Interchange does not fill AssetImportTask.imported_object_paths, so the
previous pass imported FBXs but spawned nothing.  This does not reimport.
"""
import unreal

CONTENT = "/Game/ApartmentScene"
MAP_PATH = CONTENT + "/L_ApartmentLiving"
SEQ_PATH = CONTENT + "/LS_CutePatrol"

WAYPOINTS = [
    (unreal.Vector(455.0, -1270.0, 0.0), 165.3),
    (unreal.Vector(580.0, -1180.0, 0.0), 110.0),
    (unreal.Vector(550.0, -980.0, 0.0), 20.0),
    (unreal.Vector(360.0, -1020.0, 0.0), -70.0),
    (unreal.Vector(340.0, -1280.0, 0.0), -170.0),
    (unreal.Vector(455.0, -1270.0, 0.0), 165.3),
]
WALK_SPEED = 92.0
FPS = 24
SEAT = (unreal.Vector(202.0, -1215.0, 0.0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
STAND = (unreal.Vector(330.0, -1330.0, 0.0), unreal.Rotator(pitch=0.0, yaw=132.0, roll=0.0))
WALK0 = (WAYPOINTS[0][0], unreal.Rotator(pitch=0.0, yaw=WAYPOINTS[0][1], roll=0.0))


def log(msg):
    print(f"[AptWalk] {msg}")
    unreal.log(f"[AptWalk] {msg}")


def actors():
    try:
        return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    except Exception:
        return list(unreal.EditorLevelLibrary.get_all_level_actors())


def destroy_labeled(prefixes):
    n = 0
    for a in list(actors()):
        label = a.get_actor_label()
        if any(label == p or label.startswith(p) for p in prefixes):
            unreal.EditorLevelLibrary.destroy_actor(a)
            n += 1
    log(f"destroyed {n} actors {prefixes}")


def find_assets(folder, cls, name_substr=""):
    out = []
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        log(f"missing dir {folder}")
        return out
    for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        name = p.rsplit("/", 1)[-1]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, cls) and name_substr.lower() in obj.get_name().lower():
            out.append(obj)
    return out


def pick_sk(meshes, prefer):
    if not meshes:
        return None
    for key in prefer:
        for m in meshes:
            if key.lower() in m.get_name().lower():
                return m
    return meshes[0]


def pick_anim(anims, prefer, avoid=()):
    if not anims:
        return None
    for key in prefer:
        for a in anims:
            n = a.get_name().lower()
            if key.lower() in n and not any(x.lower() in n for x in avoid):
                return a
    for a in anims:
        n = a.get_name().lower()
        if not any(x.lower() in n for x in avoid):
            return a
    return anims[0]


def spawn_character(label, mesh, anim, location, rotation):
    if not mesh:
        log(f"{label}: NO MESH")
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkeletalMeshActor, location, rotation
    )
    actor.set_actor_label(label)
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(rotation, False)
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    try:
        comp.set_skeletal_mesh_asset(mesh)
    except Exception:
        comp.set_skeletal_mesh(mesh)
    if anim:
        skel_mesh = mesh.get_editor_property("skeleton")
        skel_anim = anim.get_editor_property("skeleton")
        if skel_anim != skel_mesh:
            log(f"{label} skeleton mismatch mesh={skel_mesh.get_name() if skel_mesh else None} "
                f"anim={skel_anim.get_name() if skel_anim else None} — trying rebind")
            try:
                anim.set_editor_property("skeleton", skel_mesh)
                unreal.EditorAssetLibrary.save_loaded_asset(anim)
            except Exception as e:
                log(f"rebind failed: {e}")
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.play_animation(anim, True)
        log(f"{label} mesh={mesh.get_name()} anim={anim.get_name()}")
    else:
        log(f"{label} mesh={mesh.get_name()} NO ANIM")
    return actor


def path_keys():
    keys = []
    t = 0.0
    loc, yaw = WAYPOINTS[0]
    keys.append((0.0, loc, yaw))
    for i in range(1, len(WAYPOINTS)):
        nxt, nyaw = WAYPOINTS[i]
        dist = (nxt - loc).length()
        t += dist / WALK_SPEED
        keys.append((t, nxt, nyaw))
        loc, yaw = nxt, nyaw
    return keys


def _add_float_key(channel, frame, value):
    fn = unreal.FrameNumber(int(round(frame)))
    for name in ("add_key", "add_key_at_frame"):
        fn_attr = getattr(channel, name, None)
        if fn_attr is None:
            continue
        try:
            fn_attr(fn, float(value))
            return True
        except Exception:
            try:
                fn_attr(unreal.FrameTime(fn), float(value))
                return True
            except Exception:
                pass
    try:
        channel.add_key(fn, float(value), 1.0, unreal.MovieSceneKeyInterpolation.AUTO)
        return True
    except Exception as e:
        log(f"add_key fail: {e}")
        return False


def build_sequence(cute, walk_anim):
    if unreal.EditorAssetLibrary.does_asset_exist(SEQ_PATH):
        unreal.EditorAssetLibrary.delete_asset(SEQ_PATH)
    factory = unreal.LevelSequenceFactoryNew()
    seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "LS_CutePatrol", CONTENT, unreal.LevelSequence, factory
    )
    keys = path_keys()
    total_sec = keys[-1][0]
    total_frames = int(round(total_sec * FPS)) + 1
    log(f"sequence duration={total_sec:.2f}s frames={total_frames} keys={len(keys)}")
    try:
        seq.set_display_rate(unreal.FrameRate(FPS, 1))
        seq.set_playback_start(0)
        seq.set_playback_end(total_frames)
    except Exception as e:
        log(f"playback range: {e}")

    binding = seq.add_possessable(cute)

    try:
        anim_track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
        anim_sec = anim_track.add_section()
        try:
            anim_sec.set_range(0, total_frames)
        except Exception:
            anim_sec.set_start_frame(0)
            anim_sec.set_end_frame(total_frames)
        try:
            params = anim_sec.get_editor_property("params")
            params.set_editor_property("animation", walk_anim)
        except Exception:
            anim_sec.set_editor_property("animation", walk_anim)
        try:
            anim_sec.set_editor_property("loop", True)
        except Exception:
            pass
        log("anim track ok")
    except Exception as e:
        log(f"anim track: {e}")

    try:
        tf_track = binding.add_track(unreal.MovieScene3DTransformTrack)
        tf_sec = tf_track.add_section()
        try:
            tf_sec.set_range(0, total_frames)
        except Exception:
            tf_sec.set_start_frame(0)
            tf_sec.set_end_frame(total_frames)
        channels = None
        for getter in ("get_all_channels", "get_channels"):
            if hasattr(tf_sec, getter):
                try:
                    channels = list(getattr(tf_sec, getter)())
                    break
                except Exception:
                    pass
        if channels:
            log(f"transform nchannels={len(channels)}")
            for t, loc, yaw in keys:
                fr = t * FPS
                if len(channels) >= 3:
                    _add_float_key(channels[0], fr, loc.x)
                    _add_float_key(channels[1], fr, loc.y)
                    _add_float_key(channels[2], fr, loc.z)
                if len(channels) >= 6:
                    _add_float_key(channels[3], fr, 0.0)
                    _add_float_key(channels[4], fr, 0.0)
                    _add_float_key(channels[5], fr, yaw)
        else:
            log("no transform channels")
    except Exception as e:
        log(f"transform track: {e}")

    unreal.EditorAssetLibrary.save_loaded_asset(seq)

    lsa = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.LevelSequenceActor, unreal.Vector(0, 0, 0), unreal.Rotator()
    )
    lsa.set_actor_label("Apt_CutePatrol")
    try:
        lsa.set_sequence(seq)
    except Exception:
        lsa.set_editor_property("sequence", seq)
    try:
        ps = lsa.get_editor_property("playback_settings")
        ps.set_editor_property("auto_play", True)
        try:
            ps.set_editor_property("loop_count", unreal.MovieSceneSequenceLoopCount(-1))
        except Exception:
            pass
        lsa.set_editor_property("playback_settings", ps)
    except Exception as e:
        log(f"playback_settings: {e}")
    log(f"spawned Apt_CutePatrol")
    return seq


log("=== fix spawn ===")
unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
destroy_labeled(("Cute", "Rosemary", "Ayane", "Apt_CutePatrol"))

cute_sks = find_assets(CONTENT + "/Cute", unreal.SkeletalMesh)
cute_anims = find_assets(CONTENT + "/Cute", unreal.AnimSequence)
log(f"Cute SK={[m.get_name() for m in cute_sks]} anim={[a.get_name() for a in cute_anims]}")

walk_mesh = pick_sk(cute_sks, ("Walk", "body"))
idle_mesh = pick_sk(cute_sks, ("Idle",))
walk_anim = pick_anim(cute_anims, ("Walk",), avoid=("Idle", "Body"))
idle_anim = pick_anim(cute_anims, ("Idle",), avoid=("Walk",))
default_anim = idle_anim or walk_anim
if idle_anim and walk_mesh:
    if idle_anim.get_editor_property("skeleton") != walk_mesh.get_editor_property("skeleton"):
        log("idle/walk different skeletons — default to walk anim on walk mesh")
        default_anim = walk_anim

rs_sks = find_assets(CONTENT + "/Rosemary", unreal.SkeletalMesh)
rs_anims = find_assets(CONTENT + "/Rosemary", unreal.AnimSequence)
ay_sks = find_assets(CONTENT + "/Ayane", unreal.SkeletalMesh)
ay_anims = find_assets(CONTENT + "/Ayane", unreal.AnimSequence)
log(f"Rosemary SK={[m.get_name() for m in rs_sks]} Ayane SK={[m.get_name() for m in ay_sks]}")

cute = spawn_character("Cute", walk_mesh, default_anim, *WALK0)
spawn_character("Rosemary", pick_sk(rs_sks, ("body", "Sit", "Rosemary")), pick_anim(rs_anims, ("Sit", "Rosemary")), *SEAT)
spawn_character("Ayane", pick_sk(ay_sks, ("body", "Stand", "Ayane")), pick_anim(ay_anims, ("Stand", "Ayane")), *STAND)

body_sks = find_assets(CONTENT + "/CuteBody", unreal.SkeletalMesh)
log(f"CuteBody (no clothes) SK={[m.get_name() for m in body_sks]} — not spawned")

if cute and walk_anim:
    build_sequence(cute, walk_anim)
else:
    log("SKIP sequence (missing cute or walk anim)")

ok = unreal.EditorLoadingAndSavingUtils.save_map(
    unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
)
unreal.EditorAssetLibrary.save_directory(CONTENT, True, True)
log(f"saved map ok={ok}")
log("=== Done ===")
