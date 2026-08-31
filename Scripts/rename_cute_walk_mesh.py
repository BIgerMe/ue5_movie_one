import unreal
OLD = "/Game/ApartmentScene/Cute/Cute_Walk_Mesh"
NEW = "/Game/ApartmentScene/Cute/Cute_Walk"
if unreal.EditorAssetLibrary.does_asset_exist(OLD):
    ok = unreal.EditorAssetLibrary.rename_asset(OLD, NEW)
    print(f"rename {OLD} -> {NEW} ok={ok}")
else:
    print(f"{OLD} missing, Cute_Walk exists={unreal.EditorAssetLibrary.does_asset_exist(NEW)}")
