# GitHub 仓库搭建指南（模型使用 UE 项目）

## 重要安全说明

**请不要在 Cursor 对话里发送 GitHub 密码。** GitHub 已不支持用账号密码推送代码。

推荐认证方式（任选其一）：

1. **Cursor / VS Code 内置 GitHub 登录**（最简单）
2. **Personal Access Token (PAT)**：GitHub → Settings → Developer settings → Tokens
3. **SSH 密钥**：`ssh-keygen` 后把公钥加到 GitHub

---

## 仓库范围

只提交 **`G:\app\UE_5.8\assets\模型使用`** 这个 UE 项目目录，**不要**把整个 `UE_5.8` 引擎目录提交上去。

已自动忽略：

| 目录 | 原因 |
|------|------|
| `Saved/` `Intermediate/` `DerivedDataCache/` | 本地缓存，每台电脑会重新生成 |
| `Content/_ArchiveContent/` | ~3.7GB 归档，不必同步 |
| `.env` 等 | 密钥文件 |

大资源（`.uasset` / `.umap` 等）走 **Git LFS**（项目根目录已有 `.gitattributes`）。

---

## 一、在本机初始化并首次提交

在项目目录打开终端（PowerShell）：

```powershell
cd "G:\app\UE_5.8\assets\模型使用"

git init -b main
git lfs install
git lfs track

git add .gitignore .gitattributes
git add Config Content Scripts AI_FILES "*.uproject"
git status   # 确认没有 Saved/Intermediate/_ArchiveContent

git commit -m "Initial commit: Apartment Cute UE project"
```

首次 `git add` 可能较慢（LFS 扫描大文件）。

---

## 二、在 GitHub 新建空仓库

1. 打开 https://github.com/new
2. 仓库名建议：`ue-apartment-cute`（可自定）
3. **不要**勾选 “Add a README” / “Add .gitignore”（本地已有）
4. 创建后记下地址，例如：`https://github.com/你的用户名/ue-apartment-cute.git`

---

## 三、关联远程并推送

```powershell
git remote add origin https://github.com/你的用户名/ue-apartment-cute.git
git push -u origin main
```

推送时 Cursor/终端会弹出 **GitHub 登录** 或要求输入 **PAT**（不是密码）。

---

## 四、另一台电脑拉取继续开发

### 环境要求

- 安装 **Git** + **Git LFS**
- 安装 **Unreal Engine 5.8**（路径可以不同）
- （可选）Blender、`E:\game\scene_build\` 脚本——项目内 `Scripts/` 已有一份 UE 导入脚本

### 克隆

```powershell
git lfs install
git clone https://github.com/你的用户名/ue-apartment-cute.git
cd ue-apartment-cute
git lfs pull
```

### 打开项目

1. 双击 `模型使用.uproject`（或在 UE 里 Open Project）
2. 首次打开会编译 Shader / 生成 `Saved`、`Intermediate`，属正常现象
3. 默认关卡：`L_ApartmentCute`（见 `Config/DefaultEngine.ini`）

---

## Cursor 能做什么？

| 能力 | 说明 |
|------|------|
| 帮你写 `.gitignore`、跑 `git` 命令 | 可以（Agent 模式） |
| 在 Cursor 里提交 / 推送 | 可以，用左侧 **Source Control** 或让我执行命令 |
| 自动替你输入 GitHub 密码 | **不可以**，也不安全 |
| 代你在 GitHub 网页建仓库 | 需你浏览器登录一次，或安装 `gh` CLI |

你的 Cursor **已连接 GitHub 账号**（可用于 PR 等功能）；推送代码仍需本机 Git 完成一次认证。

---

## 常见问题

**Q: 推送失败 `file exceeds 100MB`？**  
A: 确认已 `git lfs install` 且 `.gitattributes` 已提交；大文件应用 LFS 跟踪后再 commit。

**Q: LFS 流量/配额？**  
A: GitHub 免费账号 LFS 约 1GB 存储 + 1GB/月带宽；本项目 Content ~570MB，一般够用。

**Q: Blender 脚本在哪？**  
A: UE 侧在 `Scripts/`；Blender 源脚本在 `E:\game\scene_build\scripts\`，另一台机器需自行拷贝或再建一个仓库。

---

## 可选：安装 GitHub CLI（以后一条命令建仓库）

```powershell
winget install GitHub.cli
gh auth login
gh repo create ue-apartment-cute --private --source=. --remote=origin --push
```
