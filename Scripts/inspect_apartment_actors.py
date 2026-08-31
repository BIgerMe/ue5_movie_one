"""Dump apartment actors so poses can be snapped to furniture."""
import unreal

MAP_PATH = "/Game/ApartmentScene/L_ApartmentLiving"


def log(msg):
    print(f"[Inspect] {msg}")
    unreal.log(f"[Inspect] {msg}")


def actors():
    try:
        return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    except Exception:
        return list(unreal.EditorLevelLibrary.get_all_level_actors())


unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
want = (
    "cute", "rosemary", "ayane", "chair", "sofa", "couch", "ashanti",
    "playerstart", "table", "apt_",
)
for a in actors():
    label = a.get_actor_label()
    low = label.lower()
    cls = a.get_class().get_name()
    if not any(k in low or k in cls.lower() for k in want):
        if not isinstance(a, (unreal.SkeletalMeshActor, unreal.Character, unreal.PlayerStart)):
            continue
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    log(
        f"{label:28s} {cls:22s} "
        f"loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) "
        f"rot=({rot.pitch:.1f},{rot.yaw:.1f},{rot.roll:.1f})"
    )
log("DONE")
