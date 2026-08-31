"""Collision for the apartment + WASD-possessed cute girl.

Replaces the patrol sequence with a Character (capsule + CharacterMovement).
Room mesh uses complex-as-simple collision so walls/sofa/floor block the pawn.
"""
import os
import sys
import unreal

CONTENT = "/Game/ApartmentScene"
MAP_PATH = CONTENT + "/L_ApartmentLiving"
GM_PATH = CONTENT + "/BP_AptGameMode"

WALK0 = unreal.Vector(455.0, -1270.0, 92.0)
WALK_YAW = 165.3
SEAT = (unreal.Vector(202.0, -1215.0, 0.0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
STAND = (unreal.Vector(330.0, -1330.0, 0.0), unreal.Rotator(pitch=0.0, yaw=132.0, roll=0.0))

CAP_RADIUS = 28.0
CAP_HALF = 86.0


def log(msg):
    print(f"[AptWASD] {msg}")
    unreal.log(f"[AptWASD] {msg}")


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
    log(f"destroyed {n} {prefixes}")


def ensure_python_character():
    py_dir = os.path.join(unreal.Paths.project_content_dir(), "Python")
    if py_dir not in sys.path:
        sys.path.insert(0, py_dir)
    import cute_apartment_character as cac
    cac.patch_game_mode()
    log("patched AptPlayerController onto GameMode")
    return unreal.Character


def enable_room_collision():
    """Skip mutating Apartment_Room.uasset — rebuilding it wants ~26GB.

    Collision comes from invisible blocking volumes + actor collision profiles.
    """
    log("skip room-mesh rebuild; using Apt_Col_* volumes")
    return 0


def spawn_box(label, loc, scale):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    if not cube:
        log("Engine Cube missing")
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, loc, unreal.Rotator()
    )
    actor.set_actor_label(label)
    actor.set_actor_location(loc, False, False)
    actor.set_actor_scale3d(scale)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_static_mesh(cube)
    try:
        comp.set_visibility(False, True)
        comp.set_hidden_in_game(True)
        comp.set_cast_shadow(False)
    except Exception:
        pass
    comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    comp.set_collision_profile_name("BlockAll")
    try:
        comp.set_collision_object_type(unreal.CollisionChannel.ECC_WORLD_STATIC)
    except Exception:
        pass
    log(f"blocker {label} loc={loc} scale={scale}")
    return actor


def spawn_collision_volumes():
    """Invisible boxes: floor, outer walls, sofa. Cube is 100cm."""
    # Apartment AABB from the imported combined mesh (cm).
    cx, cy = 540.0, -1245.0
    hx, hy = 672.0, 1182.0
    wall_t = 0.40   # 40cm thick
    wall_h = 3.20   # 320cm tall
    # Floor: top at z=0
    spawn_box("Apt_Col_Floor", unreal.Vector(cx, cy, -15.0), unreal.Vector(hx / 50.0, hy / 50.0, 0.30))
    # Four outer walls (scale is multiples of 100cm)
    spawn_box(
        "Apt_Col_WallXMin",
        unreal.Vector(cx - hx, cy, 160.0),
        unreal.Vector(wall_t, hy / 50.0, wall_h),
    )
    spawn_box(
        "Apt_Col_WallXMax",
        unreal.Vector(cx + hx, cy, 160.0),
        unreal.Vector(wall_t, hy / 50.0, wall_h),
    )
    spawn_box(
        "Apt_Col_WallYMin",
        unreal.Vector(cx, cy - hy, 160.0),
        unreal.Vector(hx / 50.0, wall_t, wall_h),
    )
    spawn_box(
        "Apt_Col_WallYMax",
        unreal.Vector(cx, cy + hy, 160.0),
        unreal.Vector(hx / 50.0, wall_t, wall_h),
    )
    # Sofa / seat block (Rosemary sits here)
    spawn_box("Apt_Col_Sofa", unreal.Vector(220.0, -1210.0, 40.0), unreal.Vector(1.10, 3.50, 0.80))
    # Low coffee-table-ish block in front of sofa
    spawn_box("Apt_Col_Table", unreal.Vector(340.0, -1210.0, 20.0), unreal.Vector(0.80, 1.60, 0.40))



def harden_static_mesh_actors():
    n = 0
    for a in actors():
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if not comp:
            continue
        try:
            comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            comp.set_collision_profile_name("BlockAll")
            try:
                comp.set_collision_object_type(unreal.CollisionChannel.ECC_WORLD_STATIC)
            except Exception:
                pass
            n += 1
        except Exception as e:
            log(f"sm actor {a.get_actor_label()}: {e}")
    log(f"hardened {n} static mesh actors")


def spawn_floor_blocker():
    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    if not cube:
        log("Engine Cube missing — skip backup floor")
        return
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(540.0, -1245.0, -12.0), unreal.Rotator()
    )
    actor.set_actor_label("Apt_FloorCollision")
    actor.set_actor_scale3d(unreal.Vector(50.0, 50.0, 0.24))  # 5m? Cube=100cm → 50x=50m, 24cm thick
    actor.set_actor_location(unreal.Vector(540.0, -1245.0, -12.0), False, False)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_static_mesh(cube)
    comp.set_visibility(False, True)
    try:
        comp.set_hidden_in_game(True)
        comp.set_cast_shadow(False)
    except Exception:
        pass
    comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    comp.set_collision_profile_name("BlockAll")
    log("spawned Apt_FloorCollision")


def add_npc_capsule(actor, z_center):
    """Native actors cannot add_component_by_class here; drop an invisible box."""
    loc = actor.get_actor_location()
    spawn_box(
        f"Apt_Col_{actor.get_actor_label()}",
        unreal.Vector(loc.x, loc.y, loc.z + z_center),
        unreal.Vector(0.55, 0.55, 1.72),
    )


def spawn_npc(label, mesh, anim, loc, rot):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkeletalMeshActor, loc, rot
    )
    actor.set_actor_label(label)
    actor.set_actor_location(loc, False, False)
    actor.set_actor_rotation(rot, False)
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    try:
        comp.set_skeletal_mesh_asset(mesh)
    except Exception:
        comp.set_skeletal_mesh(mesh)
    if anim:
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.play_animation(anim, True)
    add_npc_capsule(actor, CAP_HALF)
    return actor


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


def pick(items, keys):
    if not items:
        return None
    for k in keys:
        for i in items:
            if k.lower() in i.get_name().lower():
                return i
    return items[0]


def ensure_game_mode(pawn_cls):
    if unreal.EditorAssetLibrary.does_asset_exist(GM_PATH):
        bp = unreal.load_asset(GM_PATH + ".BP_AptGameMode")
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.GameModeBase)
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "BP_AptGameMode", CONTENT, unreal.Blueprint, factory
        )
        log("created BP_AptGameMode")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    gen = bp.generated_class()
    if gen:
        cdo = unreal.get_default_object(gen)
        try:
            # Placed Cute pawn auto-possesses; do not spawn a second DefaultPawn.
            cdo.set_editor_property("default_pawn_class", unreal.SpectatorPawn)
            log("GameMode default pawn=SpectatorPawn (Cute actor auto-possesses Player0)")
        except Exception as e:
            log(f"default_pawn_class: {e}")
        try:
            cdo.set_editor_property("player_controller_class", unreal.PlayerController)
        except Exception:
            pass
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        try:
            import cute_apartment_character as cac
            cac.patch_game_mode()
        except Exception as e:
            log(f"runtime PC patch: {e}")
    world = None
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    except Exception:
        world = unreal.EditorLevelLibrary.get_editor_world()
    ws = world.get_world_settings()
    if gen:
        try:
            ws.set_editor_property("default_game_mode", gen)
            log("world DefaultGameMode = BP_AptGameMode")
        except Exception as e:
            log(f"world game mode: {e}")
    return bp


def place_player_start():
    ps = None
    for a in actors():
        if isinstance(a, unreal.PlayerStart) or a.get_actor_label().startswith("Apt_PlayerStart"):
            ps = a
            break
    rot = unreal.Rotator(pitch=0.0, yaw=WALK_YAW, roll=0.0)
    if ps is None:
        ps = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, WALK0, rot)
        ps.set_actor_label("Apt_PlayerStart")
    ps.set_actor_location(WALK0, False, False)
    ps.set_actor_rotation(rot, False)
    log(f"PlayerStart at {WALK0}")


def spawn_player(cls):
    rot = unreal.Rotator(pitch=0.0, yaw=WALK_YAW, roll=0.0)
    pawn = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.Character, WALK0, rot)
    pawn.set_actor_label("Cute")
    pawn.set_actor_location(WALK0, False, False)
    pawn.set_actor_rotation(rot, False)
    try:
        pawn.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
    except Exception as e:
        log(f"auto possess: {e}")
    cap = pawn.capsule_component
    if cap:
        cap.set_capsule_size(CAP_RADIUS, CAP_HALF)
        try:
            cap.set_collision_profile_name("Pawn")
            cap.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        except Exception:
            pass
    mv = pawn.character_movement
    if mv:
        mv.max_walk_speed = 160.0
        try:
            mv.set_editor_property("orient_rotation_to_movement", True)
        except Exception:
            pass
    mesh = pawn.mesh
    sks = find_assets(CONTENT + "/Cute", unreal.SkeletalMesh, "Walk")
    if mesh and sks:
        try:
            mesh.set_skeletal_mesh_asset(sks[0])
        except Exception:
            mesh.set_skeletal_mesh(sks[0])
        mesh.set_relative_location(unreal.Vector(0.0, 0.0, -CAP_HALF), False, False)
        mesh.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        anims = find_assets(CONTENT + "/Cute", unreal.AnimSequence, "Idle")
        if anims:
            mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            mesh.play_animation(anims[0], True)
    log(f"spawned native Character Cute at {WALK0}")
    return pawn


log("=== WASD + collision ===")
unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)

cls = ensure_python_character()

destroy_labeled(("Cute", "Apt_CutePatrol", "Apt_FloorCollision", "Apt_Col_", "Rosemary", "Ayane"))

nmesh = enable_room_collision()
log(f"updated {nmesh} room meshes")
harden_static_mesh_actors()
spawn_collision_volumes()

rs_mesh = pick(find_assets(CONTENT + "/Rosemary", unreal.SkeletalMesh), ("Sit", "body", "Rosemary"))
ay_mesh = pick(find_assets(CONTENT + "/Ayane", unreal.SkeletalMesh), ("Stand", "body", "Ayane"))
rs_anim = pick(find_assets(CONTENT + "/Rosemary", unreal.AnimSequence), ("Sit", "Rosemary"))
ay_anim = pick(find_assets(CONTENT + "/Ayane", unreal.AnimSequence), ("Stand", "Ayane"))
if rs_mesh:
    spawn_npc("Rosemary", rs_mesh, rs_anim, *SEAT)
if ay_mesh:
    spawn_npc("Ayane", ay_mesh, ay_anim, *STAND)

ensure_game_mode(cls)
place_player_start()
spawn_player(cls)

ok = unreal.EditorLoadingAndSavingUtils.save_map(
    unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
)
try:
    if unreal.EditorAssetLibrary.does_asset_exist(GM_PATH):
        unreal.EditorAssetLibrary.save_asset(GM_PATH)
except Exception as e:
    log(f"save GM: {e}")
log(f"saved map ok={ok}")
log("=== Done ===")
