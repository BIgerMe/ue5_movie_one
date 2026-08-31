# Cute 动画 v2 调整说明

## 已完成的修改

| 原名称 | 新名称 | 调整内容 |
|--------|--------|----------|
| Cute_Idle_Anim | 保持 | 手臂外展约 14°，自然垂于身体两侧，避免手穿进臀部 |
| Cute_IdleStand | **Cute_Stand_Open** | 适度开腿朝前（-Y），非一字马 |
| Cute_SitDown | **Cute_Sit_Chair** | 站→坐椅→适度开腿；导出时剔除眼骨曲线，修复白眼 |
| Cute_SitOpen | **Cute_Sit_LeanBack** | 保留上身后仰；翘臀、朝后开；同样修复眼珠 |
| Cute_Walk_Anim | 保持 | 手臂外展减内八；spine 轻微乳摇 |

旧资产 `Cute_IdleStand` / `Cute_SitDown` / `Cute_SitOpen` 已在导入时删除。

## 测试方法

1. 打开项目 `模型使用.uproject`，进入关卡 **L_ApartmentCute**。
2. 选中场景中的 **Cute**，在 Details → Mesh → Animation 中逐个预览：
   - `Cute_Stand_Open`（默认开局站姿）
   - `Cute_Idle_Anim`
   - `Cute_Walk_Anim`
   - `Cute_Sit_Chair`
   - `Cute_Sit_LeanBack`
3. 播放 Sequencer：**Apt_CuteSolo**（Walk → Sit_Chair → Sit_LeanBack）。
4. PIE 运行：WASD 移动应切换 Walk/Idle；开局为 Stand_Open 开放站姿。

## 重新导出（如需微调）

```powershell
# Blender
blender --background --python E:\game\scene_build\scripts\stage2c_cute.py
blender --background --python E:\game\scene_build\scripts\export_ue_characters.py -- Cute_Idle Cute_Walk
blender --background --python E:\game\scene_build\scripts\stage5_cute_solo.py

# UE（先关闭编辑器）
UnrealEditor-Cmd.exe "G:\app\UE_5.8\assets\模型使用\模型使用.uproject" ^
  -ExecutePythonScript="G:\app\UE_5.8\assets\模型使用\Scripts\import_cute_anims_v2.py" -stdout -unattended -nosplash

# 若仅 Idle/Walk 需重导：
# -ExecutePythonScript="...\Scripts\reimport_idle_walk.py"
```

## 源文件

- Idle/Walk：`E:\game\scene_build\scripts\stage2c_cute.py`
- 站姿/坐姿：`E:\game\scene_build\scripts\stage5_cute_solo.py`
- UE 导入：`Scripts/import_cute_anims_v2.py`
