"""Fix character placement: Blender Y becomes -Y in this FBX->UE import."""
import unreal

MAP_PATH = "/Game/ApartmentScene/L_ApartmentLiving"

# Blender metres * 100, with Y flipped to match Apartment_Room bounds
# (Y in UE is about -2427 .. -63).
SEAT = (unreal.Vector(202.0, -1215.0, 0.0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
STAND = (unreal.Vector(330.0, -1330.0, 0.0), unreal.Rotator(pitch=0.0, yaw=132.0, roll=0.0))
WALK0 = (unreal.Vector(455.0, -1270.0, 0.0), unreal.Rotator(pitch=0.0, yaw=165.3, roll=0.0))

PLACES = {"Rosemary": SEAT, "Ayane": STAND, "Cute": WALK0}


def log(msg):
    unreal.log(f"[AptFix] {msg}")


def actors():
    try:
        subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        return list(subsys.get_all_level_actors())
    except Exception:
        return list(unreal.EditorLevelLibrary.get_all_level_actors())


unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)

room = None
for a in actors():
    if a.get_actor_label() == "Apartment_Room" or (
        isinstance(a, unreal.StaticMeshActor) and "Apartment_Room" in a.get_actor_label()
    ):
        room = a
        origin, extent = a.get_actor_bounds(False)
        log(f"Room origin={origin} extent={extent}")

moved = 0
for a in actors():
    label = a.get_actor_label()
    key = label.split("_")[0]
    if key not in PLACES:
        continue
    loc, rot = PLACES[key]
    a.set_actor_location(loc, False, False)
    a.set_actor_rotation(rot, False)
    log(f"Moved {label} -> {loc} {rot}")
    moved += 1

# cine camera aimed at the sofa group
cam_loc = unreal.Vector(530.0, -830.0, 155.0)
cam_look = unreal.Vector(260.0, -1230.0, 105.0)
delta = cam_look - cam_loc
yaw = unreal.MathLibrary.make_rot_from_x(delta)
for a in list(actors()):
    if a.get_actor_label() == "Apt_CineCam":
        a.destroy_actor()
cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CineCameraActor, cam_loc, unreal.Rotator(pitch=0.0, yaw=yaw.yaw, roll=0.0)
)
cam.set_actor_label("Apt_CineCam")
try:
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam_loc, yaw)
except Exception:
    pass

ok = unreal.EditorLoadingAndSavingUtils.save_map(
    unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
)
log(f"moved={moved} saved={ok}")
log("DONE")
