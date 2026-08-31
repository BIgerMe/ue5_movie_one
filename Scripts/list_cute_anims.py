import unreal
CONTENT = "/Game/ApartmentScene/Cute"
for p in unreal.EditorAssetLibrary.list_assets(CONTENT, recursive=True):
    name = p.rsplit("/", 1)[-1]
    obj = unreal.load_asset(p if "." in name else f"{p}.{name}")
    if isinstance(obj, unreal.AnimSequence):
        print(p, obj.get_play_length())
