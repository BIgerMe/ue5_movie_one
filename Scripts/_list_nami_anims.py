import unreal
CONTENT = "/Game/Characters/Nami"
for asset in unreal.EditorAssetLibrary.list_assets(CONTENT, recursive=True):
    name = asset.split("/")[-1]
    obj = unreal.load_asset(f"{asset}.{name}")
    if isinstance(obj, unreal.AnimSequence):
        sk = obj.get_editor_property("skeleton")
        log_name = f"{name} frames={obj.get_number_of_frames()} sk={sk.get_name() if sk else None}"
        unreal.log(log_name)
