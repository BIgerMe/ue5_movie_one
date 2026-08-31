"""Make the living room visible without baked lighting, and keep walk posing in editor.

SM5 has no Lumen, so an indoor mesh lit only by a distant sun is black.
Fill lights are Movable so the 'rebuild lighting' warning does not matter.
"""
import unreal

MAP_PATH = "/Game/ApartmentScene/L_ApartmentLiving"

LIVING = unreal.Vector(360.0, -1240.0, 0.0)


def log(msg):
    unreal.log(f"[AptLight] {msg}")


def all_actors():
    try:
        return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    except Exception:
        return list(unreal.EditorLevelLibrary.get_all_level_actors())


def destroy_labeled(prefix):
    for a in list(all_actors()):
        if a.get_actor_label().startswith(prefix):
            unreal.EditorLevelLibrary.destroy_actor(a)


def movable(comp):
    try:
        comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    except Exception:
        pass


def spawn_point(label, loc, intensity, radius, color=(1.0, 0.95, 0.88)):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight, loc, unreal.Rotator()
    )
    actor.set_actor_label(label)
    c = actor.get_component_by_class(unreal.PointLightComponent)
    movable(c)
    c.set_intensity(intensity)
    c.set_light_color(unreal.LinearColor(color[0], color[1], color[2], 1.0))
    try:
        c.set_editor_property("attenuation_radius", radius)
        c.set_editor_property("cast_shadows", False)
        c.set_editor_property("use_inverse_squared_falloff", True)
        c.set_editor_property("indirect_lighting_intensity", 0.0)
    except Exception as e:
        log(f"{label} extras: {e}")
    return actor


unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)

# drop previous fill lights so re-runs stay clean
destroy_labeled("Apt_Fill")
destroy_labeled("Apt_Post")
destroy_labeled("Apt_PlayerStart")
destroy_labeled("Apt_CineCam")

# existing sun / sky -> movable, indoor-friendly
for a in all_actors():
    label = a.get_actor_label()
    if label == "Apt_Sun":
        c = a.get_component_by_class(unreal.DirectionalLightComponent)
        if c:
            movable(c)
            c.set_intensity(2.0)
            a.set_actor_rotation(unreal.Rotator(pitch=-50.0, yaw=40.0, roll=0.0), False)
    if label == "Apt_SkyLight":
        c = a.get_component_by_class(unreal.SkyLightComponent)
        if c:
            movable(c)
            c.set_intensity(0.6)
            try:
                c.set_editor_property("real_time_capture", True)
                c.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
            except Exception:
                pass

# unitless falloff, living-room bulb range — previous 12k-18k candela was a flashbang
def spawn_soft(label, loc, intensity, radius):
    actor = spawn_point(label, loc, intensity, radius)
    c = actor.get_component_by_class(unreal.PointLightComponent)
    try:
        c.set_editor_property("use_inverse_squared_falloff", False)
        c.set_intensity(intensity)
        c.set_editor_property("cast_shadows", False)
    except Exception:
        pass
    return actor

spawn_soft("Apt_Fill_Sofa", unreal.Vector(240.0, -1220.0, 220.0), 6.0, 450.0)
spawn_soft("Apt_Fill_Walk", unreal.Vector(480.0, -1180.0, 220.0), 5.0, 400.0)
spawn_soft("Apt_Fill_Center", unreal.Vector(400.0, -1080.0, 240.0), 4.0, 500.0)

# unbounded post so auto-exposure does not crush a dark first frame
post = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.PostProcessVolume, LIVING, unreal.Rotator()
)
post.set_actor_label("Apt_Post")
try:
    post.set_editor_property("unbound", True)
    settings = post.get_editor_property("settings")
    settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM)
    settings.set_editor_property("auto_exposure_bias", -1.0)
    try:
        settings.set_editor_property("override_auto_exposure_method", True)
        settings.set_editor_property("override_auto_exposure_bias", True)
        settings.set_editor_property("auto_exposure_min_brightness", 0.4)
        settings.set_editor_property("auto_exposure_max_brightness", 1.2)
        settings.set_editor_property("override_auto_exposure_min_brightness", True)
        settings.set_editor_property("override_auto_exposure_max_brightness", True)
        settings.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
        settings.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
    except Exception:
        pass
    post.set_editor_property("settings", settings)
except Exception as e:
    log(f"post: {e}")

# PIE spawn in the living room, not at the world origin
ps = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.PlayerStart, unreal.Vector(520.0, -980.0, 90.0),
    unreal.Rotator(pitch=0.0, yaw=-150.0, roll=0.0),
)
ps.set_actor_label("Apt_PlayerStart")

cam_loc = unreal.Vector(620.0, -900.0, 160.0)
cam_rot = unreal.Rotator(pitch=-8.0, yaw=-145.0, roll=0.0)
cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CineCameraActor, cam_loc, cam_rot
)
cam.set_actor_label("Apt_CineCam")
try:
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam_loc, cam_rot)
except Exception as e:
    log(f"viewport cam: {e}")

# keep walk posing in the editor viewport (no need to PIE)
for a in all_actors():
    if not a.get_actor_label().startswith(("Cute", "Rosemary", "Ayane")):
        continue
    comp = a.get_component_by_class(unreal.SkeletalMeshComponent)
    if not comp:
        continue
    try:
        comp.set_editor_property("visibility_based_anim_tick_option",
                                 unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    except Exception:
        pass
    if a.get_actor_label() == "Cute":
        anim = unreal.load_asset("/Game/ApartmentScene/Cute/Cute_Walk_Anim.Cute_Walk_Anim")
        if anim:
            comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            comp.play_animation(anim, True)
            log("Cute walk looping")

ok = unreal.EditorLoadingAndSavingUtils.save_map(
    unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH
)
log(f"saved={ok}")
log("DONE")
