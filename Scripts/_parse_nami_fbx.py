import re
path = r"E:\game\epic_assets_other\nami\Nami+OP.fbx"
with open(path, "rb") as f:
    data = f.read()
text = data.decode("utf-8", errors="ignore")
mats = re.findall(r"Material::\s*([^\x00\n\"]+)", text)
mats2 = list(dict.fromkeys([m.strip() for m in mats if m.strip()]))
print("Materials found:", len(mats2))
for m in mats2:
    print(m)
