"""Runtime controller: WASD / stick, third-person view target, idle-walk.

Camera lives on BP_CuteGirl (SpringArm + Camera).  This PC only possesses,
moves, and looks.  Keyboard is polled every tick so Enhanced Input cannot
swallow WASD.
"""
import unreal

MESH_PATH = "/Game/ApartmentScene/Cute/Cute_Walk.Cute_Walk"
IDLE_PATH = "/Game/ApartmentScene/Cute/Cute_Idle_Anim.Cute_Idle_Anim"
WALK_PATH = "/Game/ApartmentScene/Cute/Cute_Walk_Anim.Cute_Walk_Anim"
STAND_PATH = "/Game/ApartmentScene/Cute/Cute_Stand_Open.Cute_Stand_Open"
GM_PATH = "/Game/ApartmentScene/BP_AptGameMode.BP_AptGameMode"
CUTE_BP_PATH = "/Game/ApartmentScene/BP_CuteGirl.BP_CuteGirl"

WALK_CLIP_SPEED = 92.0
WALK_THRESHOLD = 18.0
CAM_ARM = 340.0
CAM_HEIGHT = 70.0
LOOK_SENS = 1.4
POSE_LOCK_ANIM = None
POSE_CLIPS = {}


def _load(path):
    obj = unreal.load_asset(path)
    if obj:
        return obj
    short = path.rsplit("/", 1)[-1].split(".")[0]
    folder = "/Game/ApartmentScene/Cute"
    if unreal.EditorAssetLibrary.does_directory_exist(folder):
        for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
            name = p.rsplit("/", 1)[-1]
            if name.split(".")[0] == short:
                return unreal.load_asset(p if "." in name else f"{p}.{name}")
    return None


@unreal.uclass()
class AptPlayerController(unreal.PlayerController):
    @unreal.ufunction(override=True)
    def receive_begin_play(self):
        self._gait = "none"
        self._follow_cam = None
        self._pose_age = 0.0
        try:
            tick = self.primary_actor_tick
            tick.set_editor_property("can_ever_tick", True)
            tick.set_editor_property("start_with_tick_enabled", True)
        except Exception:
            pass
        self.set_actor_tick_enabled(True)
        try:
            self.set_show_mouse_cursor(False)
            self.set_input_mode_game_only()
        except Exception:
            pass
        pawn = self._ensure_pawn()
        if pawn:
            try:
                if self.get_pawn() != pawn:
                    self.possess(pawn)
            except Exception as e:
                unreal.log(f"[CutePC] possess: {e}")
            try:
                self.set_view_target_with_blend(pawn, 0.0)
            except Exception:
                try:
                    self.set_view_target(pawn)
                except Exception:
                    pass
            self._prep_anim(pawn)
            self._ensure_tps_camera(pawn)
        self._kick_all_poses()
        unreal.log("[CutePC] begin play pawn=%s" % (pawn.get_actor_label() if pawn else None))

    @unreal.ufunction(override=True)
    def receive_tick(self, delta_seconds):
        self._poll_move()
        self._poll_look()
        self._update_follow_cam()
        if getattr(self, "_gait", "") != "walk":
            t = float(delta_seconds or 0.0)
            self._pose_age = getattr(self, "_pose_age", 0.0) + t
            if self._pose_age < 0.35:
                self._kick_all_poses()
        self._update_gait()

    def _ensure_pawn(self):
        pawn = self.get_pawn()
        if isinstance(pawn, unreal.Character):
            return pawn
        found = []
        try:
            found = list(unreal.GameplayStatics.get_all_actors_of_class(self, unreal.Character))
        except Exception:
            pass
        for a in found:
            label = a.get_actor_label()
            if label.startswith("Cute") or "CuteGirl" in a.get_class().get_name():
                return a
        return found[0] if found else None

    def _cam_alive(self):
        cam = getattr(self, "_follow_cam", None)
        if not cam:
            return False
        try:
            return bool(cam.is_valid())
        except Exception:
            try:
                cam.get_actor_location()
                return True
            except Exception:
                return False

    def _ensure_tps_camera(self, pawn):
        if not pawn:
            return
        try:
            pcm = self.player_camera_manager
            if pcm:
                pcm.view_pitch_min = -45.0
                pcm.view_pitch_max = 35.0
        except Exception:
            pass
        boom = pawn.get_component_by_class(unreal.SpringArmComponent)
        built_in = pawn.get_component_by_class(unreal.CameraComponent)
        if boom:
            try:
                boom.target_arm_length = CAM_ARM
                boom.set_editor_property("use_pawn_control_rotation", True)
                boom.set_editor_property("collision_test", True)
                boom.set_relative_location(unreal.Vector(0.0, 0.0, CAM_HEIGHT), False, False)
            except TypeError:
                boom.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, CAM_HEIGHT))
            except Exception as e:
                unreal.log(f"[CutePC] boom setup: {e}")
        if built_in:
            try:
                built_in.set_editor_property("use_pawn_control_rotation", False)
            except Exception:
                pass
            self._follow_cam = None
            try:
                self.set_view_target_with_blend(pawn, 0.0)
            except Exception:
                pass
            unreal.log("[CutePC] using pawn SpringArm+Camera boom=%s" % (boom is not None))
            return
        trans = unreal.Transform()
        try:
            trans.set_editor_property("translation", pawn.get_actor_location())
            trans.set_editor_property("rotation", self.get_control_rotation())
        except Exception:
            pass
        cam = None
        try:
            cam = unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(
                pawn,
                unreal.CameraActor.static_class(),
                trans,
                unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,
            )
            if cam:
                cam = unreal.GameplayStatics.finish_spawning_actor(cam, trans)
        except Exception as e:
            unreal.log(f"[CutePC] spawn CameraActor: {e}")
            cam = None
        if cam:
            try:
                cam.set_actor_label("Apt_FollowCam")
            except Exception:
                pass
            self._follow_cam = cam
            try:
                self.set_view_target_with_blend(cam, 0.0)
            except Exception:
                try:
                    self.set_view_target(cam)
                except Exception:
                    pass
            unreal.log("[CutePC] spawned follow CameraActor")
        else:
            unreal.log("[CutePC] CameraActor spawn failed")

    def _update_follow_cam(self):
        pawn = self.get_pawn()
        if not pawn:
            return
        if pawn.get_component_by_class(unreal.CameraComponent):
            try:
                self.set_view_target_with_blend(pawn, 0.0)
            except Exception:
                pass
            return
        if not self._cam_alive():
            self._ensure_tps_camera(pawn)
        cam = getattr(self, "_follow_cam", None)
        if not cam:
            return
        cr = self.get_control_rotation()
        look = unreal.Rotator(pitch=cr.pitch, yaw=cr.yaw, roll=0.0)
        fwd = unreal.MathLibrary.get_forward_vector(look)
        loc = pawn.get_actor_location() + unreal.Vector(0.0, 0.0, CAM_HEIGHT) - fwd * CAM_ARM
        try:
            cam.set_actor_location(loc, False, False)
            cam.set_actor_rotation(look, False)
        except TypeError:
            cam.set_actor_location(loc, False)
            cam.set_actor_rotation(look)
        try:
            self.set_view_target_with_blend(cam, 0.0)
        except Exception:
            pass

    def _kick_all_poses(self):
        try:
            wname = str(self.get_world().get_name())
        except Exception:
            wname = ""
        if "ApartmentCute" in wname:
            return
        world = self
        for label, path in POSE_CLIPS.items():
            anim = POSE_LOCK_ANIM if label == "Cute" and POSE_LOCK_ANIM else _load(path)
            if not anim:
                continue
            actor = None
            try:
                for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
                    if a.get_actor_label() == label:
                        actor = a
                        break
            except Exception:
                pass
            if actor is None:
                continue
            mesh = getattr(actor, "skeletal_mesh_component", None) or getattr(actor, "mesh", None)
            if not mesh:
                continue
            try:
                mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
                mesh.play_animation(anim, False)
            except Exception as e:
                unreal.log(f"[CutePC] play {label}: {e}")
        self._gait = "pose"

    def _prep_anim(self, ch):
        mesh = ch.mesh
        if not mesh:
            return
        pose = _load(STAND_PATH) or _load(IDLE_PATH)
        if pose:
            mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            mesh.play_animation(pose, True)
            self._gait = "idle"
            return
        idle = _load(IDLE_PATH)
        if idle:
            mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            mesh.play_animation(idle, True)
            self._gait = "idle"

    def _key(self, name):
        try:
            if self.is_input_key_down(unreal.Key(name)):
                return 1.0
        except Exception:
            pass
        pi = getattr(self, "player_input", None)
        if pi:
            try:
                return float(pi.get_key_value(unreal.Key(name)))
            except Exception:
                pass
        try:
            return float(self.get_input_analog_key_state(unreal.Key(name)))
        except Exception:
            return 0.0

    def _poll_move(self):
        pawn = self.get_pawn()
        if not pawn:
            return
        fwd = self._key("W") - self._key("S") + self._key("Up") - self._key("Down")
        fwd += self._key("Gamepad_LeftY")
        right = self._key("D") - self._key("A") + self._key("Right") - self._key("Left")
        right += self._key("Gamepad_LeftX")
        if abs(fwd) < 0.02 and abs(right) < 0.02:
            return
        yaw = self.get_control_rotation().yaw
        if abs(fwd) >= 0.02:
            axis = unreal.MathLibrary.get_forward_vector(unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
            pawn.add_movement_input(axis, max(-1.0, min(1.0, fwd)), False)
        if abs(right) >= 0.02:
            axis = unreal.MathLibrary.get_right_vector(unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
            pawn.add_movement_input(axis, max(-1.0, min(1.0, right)), False)

    def _poll_look(self):
        mx = self._key("MouseX")
        my = self._key("MouseY")
        mx += self._key("Gamepad_RightX")
        my += self._key("Gamepad_RightY")
        if abs(mx) > 0.0001:
            try:
                self.add_yaw_input(mx * LOOK_SENS)
            except Exception:
                self.add_controller_yaw_input(mx * LOOK_SENS)
        if abs(my) > 0.0001:
            try:
                self.add_pitch_input(-my * LOOK_SENS)
            except Exception:
                self.add_controller_pitch_input(-my * LOOK_SENS)

    def _update_gait(self):
        pawn = self.get_pawn()
        if not isinstance(pawn, unreal.Character) or not pawn.mesh:
            return
        speed = pawn.get_velocity().size()
        if getattr(self, "_gait", "") == "pose" and speed < WALK_THRESHOLD:
            return
        want = "walk" if speed > WALK_THRESHOLD else "idle"
        if want != getattr(self, "_gait", "none"):
            asset = _load(WALK_PATH if want == "walk" else IDLE_PATH)
            if asset:
                pawn.mesh.play_animation(asset, True)
            self._gait = want
        if want == "walk":
            inst = None
            try:
                inst = pawn.mesh.get_single_node_instance()
            except Exception:
                inst = pawn.mesh.get_anim_instance()
            if inst:
                rate = max(0.35, min(2.4, speed / WALK_CLIP_SPEED))
                try:
                    inst.set_play_rate(rate)
                except Exception:
                    pass


def patch_game_mode():
    try:
        if not unreal.EditorAssetLibrary.does_asset_exist("/Game/ApartmentScene/BP_AptGameMode"):
            return
        bp = unreal.load_asset(GM_PATH)
        if not bp:
            return
        gen = bp.generated_class()
        if not gen:
            return
        cdo = unreal.get_default_object(gen)
        pawn_cls = None
        if unreal.EditorAssetLibrary.does_asset_exist("/Game/ApartmentScene/BP_CuteGirl"):
            cute_bp = unreal.load_asset(CUTE_BP_PATH)
            if cute_bp and cute_bp.generated_class():
                pawn_cls = cute_bp.generated_class()
        changed = False
        cur_pc = cdo.get_editor_property("player_controller_class")
        if "AptPlayerController" not in str(cur_pc):
            cdo.set_editor_property("player_controller_class", AptPlayerController)
            changed = True
        cur_pawn = cdo.get_editor_property("default_pawn_class")
        cur_name = str(cur_pawn) if cur_pawn else ""
        # None = placed Cute in the map. Only replace Spectator/DefaultPawn (first-person bug).
        if pawn_cls and cur_pawn and (
            "Spectator" in cur_name or cur_name.endswith("DefaultPawn")
        ):
            cdo.set_editor_property("default_pawn_class", pawn_cls)
            changed = True
        if changed:
            unreal.log("[CutePC] patched GameMode PC + pawn=%s" % (cur_name or pawn_cls.get_name()))
    except Exception as e:
        unreal.log(f"[CutePC] patch_game_mode: {e}")
