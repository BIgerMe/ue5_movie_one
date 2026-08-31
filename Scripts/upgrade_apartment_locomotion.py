"""Reimport improved character anims and let the white-shirt girl stroll the living room.

Does not reimport the apartment mesh.  Close the editor before running.
"""
import math
import os
import unreal

CONTENT = "/Game/ApartmentScene"
MAP_PATH = CONTENT + "/L_ApartmentLiving"
EXPORTS = r"E:\game\scene_build\exports"
SEQ_PATH = CONTENT + "/LS_CutePatrol"

# Blender metres * 100, Y flipped.  Loop in front of the sofa, not through it.
# Walk clip is 0.92 m/s in-place; duration is matched to path length so feet don't skate.
WAYPOINTS = [
    (unreal.Vector(455.0, -1270.0, 0.0), 165.3),
    (unreal.Vector(580.0, -1180.0, 0.0), 110.0),
    (unreal.Vector(550.0, -980.0, 0.0), 20.0),
    (unreal.Vector(360.0, -1020.0, 0.0), -70.0),
    (unreal.Vector(340.0, -1280.0, 0.0), -170.0),
    (unreal.Vector(455.0, -1270.0, 0.0), 165.3),
]
WALK_SPEED = 92.0  # cm/s
TURN_TIME = 0.35
FPS = 24

SEAT = (unreal.Vector(202.0, -1215.0, 0.0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
STAND = (unreal.Vector(330.0, -1330.0, 0.0), unreal.Rotator(pitch=0.0, yaw=132.0, roll=0.0))
WALK0 = (WAYPOINTS[0][0], unreal.Rotator(pitch=0.0, yaw=WAYPOINTS[0][1], roll=0.0))


def log(msg):
    unreal.log(f"[AptWalk] {msg}")


def ensure_dir(path):
    unreal.EditorAssetLibrary.make_directory(path)


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
    return n


def import_fbx(path, dest, skeletal, skeleton=None, mesh=True, anim=True):
    ensure_dir(dest)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", path)
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)

    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", mesh)
    opts.set_editor_property("import_materials", mesh)
    opts.set_editor_property("import_textures", mesh)
    opts.set_editor_property("import_as_skeletal", skeletal)
    opts.set_editor_property("import_animations", anim and skeletal)
    if skeletal:
        opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
        if skeleton is not None:
            try:
                opts.set_editor_property("skeleton", skeleton)
            except Exception as e:
                log(f"skeleton assign: {e}")
        sk = opts.get_editor_property("skeletal_mesh_import_data")
        try:
            sk.set_editor_property("import_morph_targets", True)
            sk.set_editor_property("use_t0_as_ref_pose", False)
            sk.set_editor_property("convert_scene", True)
            sk.set_editor_property("convert_scene_unit", True)
        except Exception as e:
            log(f"sk data: {e}")
        try:
            ad = opts.get_editor_property("anim_sequence_import_data")
            ad.set_editor_property("import_bone_tracks", True)
        except Exception:
            pass
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    log(f"Imported {os.path.basename(path)} -> {len(paths)} assets")
    return paths


def load_imported(paths, cls):
    out = []
    for p in paths:
        name = p.rsplit("/", 1)[-1]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, cls):
            out.append(obj)
    return out


def find_assets(folder, cls, name_substr=""):
    out = []
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        return out
    for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        name = p.rsplit("/", 1)[-1]
        obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
        if isinstance(obj, cls) and name_substr.lower() in obj.get_name().lower():
            out.append(obj)
    return out


def pick_body(meshes):
    if not meshes:
        return None
    for key in ("body", "Body"):
        for m in meshes:
            if m.get_name().lower() == key.lower() or m.get_name().lower().startswith(key.lower()):
                return m
    return meshes[0]


def spawn_character(label, meshes, anim, location, rotation, skip_parts=()):
    body = pick_body(meshes)
    if not body:
        log(f"{label}: no skeletal mesh")
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkeletalMeshActor, location, rotation
    )
    actor.set_actor_label(label)
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(rotation, False)
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    try:
        comp.set_skeletal_mesh_asset(body)
    except Exception:
        comp.set_skeletal_mesh(body)
    if anim:
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.play_animation(anim, True)
        log(f"{label} playing {anim.get_name()}")
    skel = body.get_editor_property("skeleton")
    skip = {n.lower() for n in skip_parts}
    attached = 0
    for mesh in meshes:
        if mesh == body or mesh.get_name().lower() in skip:
            continue
        if mesh.get_editor_property("skeleton") != skel:
            continue
        part = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkeletalMeshActor, location, rotation
        )
        part.set_actor_label(f"{label}_{mesh.get_name()}")
        pc = part.get_component_by_class(unreal.SkeletalMeshComponent)
        try:
            pc.set_skeletal_mesh_asset(mesh)
        except Exception:
            pc.set_skeletal_mesh(mesh)
        try:
            pc.set_leader_pose_component(comp, True)
        except Exception:
            pass
        if anim:
            pc.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            try:
                pc.set_leader_pose_component(comp, True)
            except Exception:
                pc.play_animation(anim, True)
        part.attach_to_actor(
            actor, "",
            unreal.AttachmentRule.SNAP_TO_TARGET,
            unreal.AttachmentRule.SNAP_TO_TARGET,
            unreal.AttachmentRule.SNAP_TO_TARGET,
            False,
        )
        attached += 1
    log(f"{label} body={body.get_name()} parts={attached}")
    return actor


def room_complex_collision():
    meshes = find_assets(CONTENT + "/Room", unreal.StaticMesh)
    n = 0
    for mesh in meshes:
        try:
            mesh.set_editor_property(
                "collision_complexity",
                unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE,
            )
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
            n += 1
            log(f"collision complex-as-simple: {mesh.get_name()}")
        except Exception as e:
            log(f"collision {mesh.get_name()}: {e}")
    return n


def path_keys():
    """(time_sec, loc, yaw_deg). Yaw interpolates across each leg so she faces the path."""
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
    try:
        seq.set_display_rate(unreal.FrameRate(FPS, 1))
        seq.set_playback_start(0)
        seq.set_playback_end(total_frames)
    except Exception:
        try:
            unreal.MovieSceneSequenceExtensions.set_playback_start(seq, 0)
            unreal.MovieSceneSequenceExtensions.set_playback_end(seq, total_frames)
        except Exception as e:
            log(f"playback range: {e}")

    binding = seq.add_possessable(cute)
    log(f"sequence possess {cute.get_actor_label()} keys={len(keys)} duration={total_sec:.2f}s")

    # animation
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
            try:
                anim_sec.set_editor_property("animation", walk_anim)
            except Exception as e:
                log(f"anim params: {e}")
        try:
            anim_sec.set_editor_property("loop", True)
        except Exception:
            pass
        log("added skeletal animation track")
    except Exception as e:
        log(f"anim track: {e}")

    # transform
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
        if not channels:
            log("no transform channels")
        else:
            log(f"transform channels={len(channels)} {[getattr(c,'get_name',lambda:type(c))() for c in channels[:9]]}")
            # Expected: loc X Y Z, rot roll pitch yaw (or pitch yaw roll), scale
            # We key loc xyz and yaw; leave others at actor defaults.
            for t, loc, yaw in keys:
                fr = t * FPS
                # loc
                if len(channels) >= 3:
                    _add_float_key(channels[0], fr, loc.x)
                    _add_float_key(channels[1], fr, loc.y)
                    _add_float_key(channels[2], fr, loc.z)
                # rotation: UE rotator stored as (roll, pitch, yaw) or (pitch, yaw, roll)
                # MovieScene 3D transform typically: Roll, Pitch, Yaw at indices 3,4,5
                if len(channels) >= 6:
                    _add_float_key(channels[3], fr, 0.0)
                    _add_float_key(channels[4], fr, 0.0)
                    _add_float_key(channels[5], fr, yaw)
        log("added transform track")
    except Exception as e:
        log(f"transform track: {e}")

    unreal.EditorAssetLibrary.save_loaded_asset(seq)

    # LevelSequenceActor auto-plays in PIE
    for a in list(actors()):
        if a.get_actor_label() == "Apt_CutePatrol":
            unreal.EditorLevelLibrary.destroy_actor(a)
    lsa = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.LevelSequenceActor, unreal.Vector(0, 0, 0), unreal.Rotator()
    )
    lsa.set_actor_label("Apt_CutePatrol")
    try:
        lsa.set_sequence(seq)
    except Exception:
        try:
            lsa.set_editor_property("sequence", seq)
        except Exception as e:
            log(f"set_sequence: {e}")
    for prop, val in (
        ("auto_play", True),
        ("looping", True),
        ("autoplay", True),
    ):
        try:
            lsa.set_editor_property(prop, val)
        except Exception:
            pass
    try:
        ps = lsa.get_editor_property("playback_settings")
        ps.set_editor_property("auto_play", True)
        ps.set_editor_property("loop_count", unreal.MovieSceneSequenceLoopCount(-1))
        lsa.set_editor_property("playback_settings", ps)
    except Exception as e:
        log(f"playback_settings: {e}")
    log(f"spawned Apt_CutePatrol {SEQ_PATH}")
    return seq


def spawn_body_preview(meshes, anim):
    """Put the unclothed cute-girl SK a step aside so clothing removal is visible."""
    if not meshes:
        return
    loc = unreal.Vector(620.0, -1400.0, 0.0)
    rot = unreal.Rotator(pitch=0.0, yaw=165.0, roll=0.0)
    spawn_character("Cute_NoCloth", meshes, anim, loc, rot)


log("=== upgrade apartment locomotion ===")
unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
destroy_labeled(("Cute", "Rosemary", "Ayane", "Apt_CutePatrol"))

room_complex_collision()

# --- Cute: walk FBX is the SK, idle is animation-only onto that skeleton ---
walk_paths = import_fbx(os.path.join(EXPORTS, "Cute_Walk.fbx"), CONTENT + "/Cute", True)
cute_meshes = load_imported(walk_paths, unreal.SkeletalMesh)
walk_anims = [a for a in load_imported(walk_paths, unreal.AnimSequence) if "idle" not in a.get_name().lower()]
if not walk_anims:
    walk_anims = load_imported(walk_paths, unreal.AnimSequence)
walk_anim = walk_anims[0] if walk_anims else None
skel = cute_meshes[0].get_editor_property("skeleton") if cute_meshes else None
log(f"Cute meshes={[m.get_name() for m in cute_meshes]} walk={walk_anim.get_name() if walk_anim else None}")

idle_paths = import_fbx(
    os.path.join(EXPORTS, "Cute_Idle.fbx"), CONTENT + "/Cute", True,
    skeleton=skel, mesh=False, anim=True,
)
idle_anims = load_imported(idle_paths, unreal.AnimSequence)
if not idle_anims:
    idle_anims = find_assets(CONTENT + "/Cute", unreal.AnimSequence, "idle")
idle_anim = idle_anims[0] if idle_anims else None
log(f"Cute idle={idle_anim.get_name() if idle_anim else None}")

body_paths = import_fbx(os.path.join(EXPORTS, "Cute_Body.fbx"), CONTENT + "/CuteBody", True)
body_meshes = load_imported(body_paths, unreal.SkeletalMesh)
body_anims = load_imported(body_paths, unreal.AnimSequence)
log(f"CuteBody meshes={[m.get_name() for m in body_meshes]}")

# --- others ---
rs_paths = import_fbx(os.path.join(EXPORTS, "Rosemary_Sit.fbx"), CONTENT + "/Rosemary", True)
ay_paths = import_fbx(os.path.join(EXPORTS, "Ayane_Stand.fbx"), CONTENT + "/Ayane", True)
rs_meshes = load_imported(rs_paths, unreal.SkeletalMesh)
ay_meshes = load_imported(ay_paths, unreal.SkeletalMesh)
rs_anim = (load_imported(rs_paths, unreal.AnimSequence) or [None])[0]
ay_anim = (load_imported(ay_paths, unreal.AnimSequence) or [None])[0]

cute = spawn_character("Cute", cute_meshes, idle_anim or walk_anim, *WALK0)
spawn_character("Rosemary", rs_meshes, rs_anim, *SEAT)
spawn_character("Ayane", ay_meshes, ay_anim, *STAND)
# Cute_Body.fbx is imported under /Game/ApartmentScene/CuteBody (no shirt/jean).
# Not spawned in the living room — drag it in if you want the unclothed mesh.

if cute and walk_anim:
    build_sequence(cute, walk_anim)

ok = unreal.EditorLoadingAndSavingUtils.save_map(
    unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
)
unreal.EditorAssetLibrary.save_directory(CONTENT, True, True)
log(f"saved map ok={ok}")
log("=== Done ===")
