"""Build a saveable third-person Character BP and use it as the default pawn."""
import os
import sys
import unreal

CONTENT = "/Game/ApartmentScene"
MAP_PATH = CONTENT + "/L_ApartmentLiving"
BP_PATH = CONTENT + "/BP_CuteGirl"
GM_PATH = CONTENT + "/BP_AptGameMode"

WALK0 = unreal.Vector(455.0, -1270.0, 92.0)
WALK_YAW = 165.3
CAP_RADIUS = 28.0
CAP_HALF = 86.0
CAM_ARM = 340.0
CAM_Z = 62.0
MAX_WALK = 160.0


def log(msg):
    print(f"[TPS] {msg}")
    unreal.log(f"[TPS] {msg}")


def actors():
    try:
        return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    except Exception:
        return list(unreal.EditorLevelLibrary.get_all_level_actors())


def find_asset(folder, cls, *keys):
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


def bp_handles(bp):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    return sds.k2_gather_subobject_data_for_blueprint(bp), sds


def find_handle(handles, pred):
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in handles:
        data = lib.get_data(h)
        if pred(lib, data, lib.get_associated_object(data)):
            return h, lib.get_associated_object(data)
    return None, None


def dump_handles(bp):
    handles, sds = bp_handles(bp)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    log(f"subobjects={len(handles)}")
    for i, h in enumerate(handles):
        data = lib.get_data(h)
        assoc = lib.get_associated_object(data)
        log(
            f"  [{i}] actor={lib.is_actor(data)} root={lib.is_root_component(data)} "
            f"assoc={assoc} cls={assoc.get_class().get_name() if assoc else None}"
        )
    return handles, sds, lib


def add_bp_comp(bp, component_type, name, parent_cls=None):
    handles, sds, lib = dump_handles(bp)
    parent_handle = None
    actor_handle = None
    root_handle = None
    for h in handles:
        data = lib.get_data(h)
        assoc = lib.get_associated_object(data)
        if lib.is_actor(data):
            actor_handle = h
        if lib.is_root_component(data):
            root_handle = h
        if parent_cls and assoc and isinstance(assoc, parent_cls):
            parent_handle = h
    candidates = [h for h in (parent_handle, root_handle, actor_handle) if h]
    if handles and not candidates:
        candidates = [handles[0]]
    last_err = ""
    for base in candidates:
        params = unreal.AddNewSubobjectParams(base, component_type, bp)
        new_handle, err = sds.add_new_subobject(params)
        err_text = str(err) if err is not None else ""
        try:
            if hasattr(err, "is_empty") and err.is_empty():
                err_text = ""
        except Exception:
            pass
        log(f"add {name} handle={new_handle} err='{err_text}'")
        if new_handle and not err_text.strip():
            sds.rename_subobject(handle=new_handle, new_name=unreal.Text(name))
            unreal.BlueprintEditorLibrary.compile_blueprint(bp)
            data = lib.get_data(new_handle)
            obj = lib.get_associated_object(data)
            log(f"add {name} ok obj={obj}")
            return obj
        last_err = err_text
    log(f"add {name} failed last_err={last_err}")
    return None


def ensure_cute_bp():
    mesh_asset = find_asset(CONTENT + "/Cute", unreal.SkeletalMesh, "Walk", "body")
    if not mesh_asset:
        raise RuntimeError("Cute_Walk skeletal mesh missing")
    if unreal.EditorAssetLibrary.does_asset_exist(BP_PATH):
        bp = unreal.load_asset(BP_PATH + ".BP_CuteGirl")
        log("loaded existing BP_CuteGirl")
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Character)
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "BP_CuteGirl", CONTENT, unreal.Blueprint, factory
        )
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        log("created BP_CuteGirl")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())

    cap = cdo.capsule_component
    if cap:
        cap.set_capsule_size(CAP_RADIUS, CAP_HALF)
        try:
            cap.set_collision_profile_name("Pawn")
            cap.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        except Exception:
            pass

    mv = cdo.character_movement
    if mv:
        mv.max_walk_speed = MAX_WALK
        mv.max_acceleration = 1400.0
        mv.braking_deceleration_walking = 900.0
        try:
            mv.rotation_rate = unreal.Rotator(0.0, 540.0, 0.0)
            mv.set_editor_property("orient_rotation_to_movement", True)
        except Exception:
            pass

    try:
        cdo.set_editor_property("use_controller_rotation_yaw", False)
        cdo.set_editor_property("use_controller_rotation_pitch", False)
        cdo.set_editor_property("use_controller_rotation_roll", False)
        cdo.set_editor_property("base_eye_height", 64.0)
    except Exception:
        pass

    mesh = cdo.mesh
    if mesh:
        try:
            mesh.set_skeletal_mesh_asset(mesh_asset)
        except Exception:
            mesh.set_skeletal_mesh(mesh_asset)
        try:
            mesh.set_relative_location(unreal.Vector(0.0, 0.0, -CAP_HALF), False, False)
        except TypeError:
            mesh.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, -CAP_HALF))
        try:
            mesh.set_relative_rotation(unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0), False, False)
        except TypeError:
            mesh.set_editor_property("relative_rotation", unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
        mesh.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        idle = find_asset(CONTENT + "/Cute", unreal.AnimSequence, "Idle")
        if idle:
            mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            try:
                mesh.set_editor_property("animation_data", idle)  # may fail
            except Exception:
                pass
            try:
                mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
                mesh.play_animation(idle, True)
            except Exception:
                pass

    boom = cdo.get_component_by_class(unreal.SpringArmComponent)
    if boom is None:
        boom = add_bp_comp(bp, unreal.SpringArmComponent, "CameraBoom", unreal.CapsuleComponent)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        cdo = unreal.get_default_object(bp.generated_class())
        if boom is None:
            boom = cdo.get_component_by_class(unreal.SpringArmComponent)
        log(f"added CameraBoom={boom}")
    if boom:
        try:
            boom.set_relative_location(unreal.Vector(0.0, 0.0, CAM_Z), False, False)
        except TypeError:
            boom.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, CAM_Z))
        boom.target_arm_length = CAM_ARM
        try:
            boom.set_editor_property("use_pawn_control_rotation", True)
            boom.set_editor_property("collision_test", True)
            boom.set_editor_property("probe_size", 12.0)
            boom.set_editor_property("camera_lag_speed", 8.0)
            boom.set_editor_property("enable_camera_lag", True)
        except Exception as e:
            log(f"boom props: {e}")

    cam = cdo.get_component_by_class(unreal.CameraComponent)
    if cam is None:
        cam = add_bp_comp(bp, unreal.CameraComponent, "FollowCam", unreal.SpringArmComponent)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        cdo = unreal.get_default_object(bp.generated_class())
        if boom is None:
            boom = cdo.get_component_by_class(unreal.SpringArmComponent)
        if cam is None:
            cam = cdo.get_component_by_class(unreal.CameraComponent)
        log(f"added FollowCam={cam}")
    if cam:
        try:
            cam.set_editor_property("use_pawn_control_rotation", False)
            cam.set_field_of_view(80.0)
        except Exception as e:
            log(f"cam props: {e}")
    if boom is None or cam is None:
        log(f"WARNING camera missing boom={boom} cam={cam} (runtime follow cam will be used)")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    log(f"BP_CuteGirl ready mesh={mesh_asset.get_name()} boom={boom is not None} cam={cam is not None}")
    return bp


def patch_game_mode(cute_bp):
    if not unreal.EditorAssetLibrary.does_asset_exist(GM_PATH):
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.GameModeBase)
        gm = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "BP_AptGameMode", CONTENT, unreal.Blueprint, factory
        )
        log("created BP_AptGameMode")
    else:
        gm = unreal.load_asset(GM_PATH + ".BP_AptGameMode")
    unreal.BlueprintEditorLibrary.compile_blueprint(gm)
    gen = gm.generated_class()
    cdo = unreal.get_default_object(gen)
    cdo.set_editor_property("default_pawn_class", cute_bp.generated_class())
    try:
        cdo.set_editor_property("player_controller_class", unreal.PlayerController)
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(gm)
    py_dir = os.path.join(unreal.Paths.project_content_dir(), "Python")
    if py_dir not in sys.path:
        sys.path.insert(0, py_dir)
    import cute_apartment_character as cac
    cac.patch_game_mode()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ws = world.get_world_settings()
    ws.set_editor_property("default_game_mode", gen)
    log("GameMode default pawn=BP_CuteGirl")
    return gm


def place_in_level(cute_bp):
    """Do not leave a second pawn in the map. GameMode spawns BP_CuteGirl at PlayerStart."""
    for a in list(actors()):
        label = a.get_actor_label()
        if label == "Cute" or label.startswith("BP_CuteGirl") or isinstance(a, unreal.Character):
            if a.get_actor_label() in ("Cute",) or "CuteGirl" in a.get_class().get_name():
                unreal.EditorLevelLibrary.destroy_actor(a)
                log(f"removed extra pawn {label}")
    rot = unreal.Rotator(pitch=0.0, yaw=WALK_YAW, roll=0.0)
    placed = False
    for a in actors():
        if isinstance(a, unreal.PlayerStart) or a.get_actor_label().startswith("Apt_PlayerStart"):
            a.set_actor_location(WALK0, False, False)
            a.set_actor_rotation(rot, False)
            placed = True
            log("PlayerStart updated")
            break
    if not placed:
        ps = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, WALK0, rot)
        ps.set_actor_label("Apt_PlayerStart")
        log("spawned PlayerStart")
    ok = unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
    )
    log(f"map saved={ok} (pawn comes from GameMode+PlayerStart)")
    return ok


log("=== third person ===")
unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
bp = ensure_cute_bp()
patch_game_mode(bp)
ok = place_in_level(bp)
log(f"=== Done saved={ok} ===")
