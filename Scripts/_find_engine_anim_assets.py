import unreal

hits = []
for root in ["/Engine", "/Game"]:
    try:
        for a in unreal.EditorAssetLibrary.list_assets(root, recursive=True):
            low = a.lower()
            if "abp_" in low or "cr_" in low or "ctrlrig" in low or "mann" in low:
                if "nami" not in low:
                    hits.append(a)
    except Exception:
        pass
unreal.log(f"Sample anim assets ({len(hits)}):")
for a in hits[:40]:
    unreal.log(a)
