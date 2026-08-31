import unreal

CONTENT = "/Game/Characters/Nami"
MESHES = ["body1", "cutehair1", "jean1", "hat1", "sport_shirt", "sport_boot", "belt1", "katana"]


def log(msg):
    unreal.log(f"[NamiRigInspect] {msg}")


def bone_names_for_skeleton(sk):
    try:
        pose = sk.get_reference_pose()
        if pose:
            return [str(n) for n in pose.get_bone_names()]
    except Exception as exc:
        log(f"get_reference_pose failed: {exc}")
    return []


for name in MESHES:
    mesh = unreal.load_asset(f"{CONTENT}/{name}.{name}")
    if not mesh:
        log(f"MISSING {name}")
        continue
    sk = mesh.get_editor_property("skeleton")
    if not sk:
        log(f"{name}: no skeleton")
        continue
    names = bone_names_for_skeleton(sk)
    log(f"{name}: sk={sk.get_name()} bones={len(names)} first20={names[:20]}")
