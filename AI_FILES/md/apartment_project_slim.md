# 公寓项目精简说明

## 当前结构（`Content/`）

```
ApartmentScene/          ← 唯一工作区（~600MB，原 ~1.7GB）
  L_ApartmentCute.umap   ← 默认启动关卡（白衣女孩 + 房间）
  LS_CuteSolo.uasset     ← 演示序列 walk→sit→open
  BP_AptGameMode.uasset
  BP_CuteGirl.uasset
  Cute/                  ← 角色网格 + 动画
  Room/                  ← 公寓静态场景（Apartment_Room ~309MB）

Material/                ← 透明/隐藏材质（MI_HidePart 等）
Python/                  ← 运行时 init_unreal + cute_apartment_character
```

## 已移出 Content（`_ArchiveContent/`）

以下文件夹已从 `Content/` 移到项目根 `_ArchiveContent/`，**不参与资源扫描**，需要时可整包移回：

- `Characters/`（Nami、Emily）
- `Fishermans_Cabin/`、`Free_Magic/`、`ArrowTrail/`、`TorchFire/`、`_SplineVFX/`、`Magma_Material/`

## 已删除（公寓内）

- `Ayane/`、`Rosemary/`、`CuteBody/`
- `L_ApartmentLiving`（三角色旧关卡）
- `LS_ApartmentPoses`、`LS_CutePatrol`
- `Cute_SitChair`（旧坏姿势）

## 启动配置

`Config/DefaultEngine.ini` 已设置：

- 编辑器启动 → `L_ApartmentCute`
- 游戏默认地图 → `L_ApartmentCute`
- GameMode → `BP_AptGameMode`

## 插件

已关闭 Virtual Production / nDisplay / PixelStreaming 等 20+ 插件，并移除 `WindowsEngine.ini` 里的 DisplayCluster 引擎类，缩短冷启动时间。

## 日常维护

| 任务 | 脚本 |
|------|------|
| 重导白衣动画 | `Scripts/reimport_cute_solo_anims.py` |
| 重建 solo 关卡 | `Scripts/setup_cute_solo_level.py` |
| 再次精简 | `Scripts/cleanup_apartment_project.py` |

改 Content 前关编辑器，用 `UnrealEditor-Cmd -ExecutePythonScript=...` 执行。

## 仍占体积的大头

- `Room/Apartment_Room.uasset`（~309MB）— 不要重建 complex collision
- `Cute/body_*` 贴图 — 后续可压到 2K
