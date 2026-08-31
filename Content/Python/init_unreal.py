"""Project Python startup — registers AptPlayerController and patches the apartment GameMode."""
try:
    import unreal
    import cute_apartment_character as cac

    cac.patch_game_mode()
    _accum = {"t": 1.0}

    def _keep_game_mode_patched(delta_seconds):
        _accum["t"] += float(delta_seconds or 0.0)
        if _accum["t"] < 0.5:
            return
        _accum["t"] = 0.0
        cac.patch_game_mode()

    unreal.register_slate_post_tick_callback(_keep_game_mode_patched)
except Exception as exc:
    print("[init_unreal] cute_apartment_character:", exc)
