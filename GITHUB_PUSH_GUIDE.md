# 📤 GitHub 推送完整指南

## 快速开始（3步走）

### ✨ 使用自动化脚本（最简单）

#### Windows 用户：
```bash
# 双击运行
push_to_github.bat

# 或者在命令行中运行
.\push_to_github.bat
```

#### Linux/Mac 用户：
```bash
# 添加执行权限
chmod +x push_to_github.sh

# 运行脚本
./push_to_github.sh
```

---

## 📖 详细步骤

### 第一步：在 GitHub 创建仓库

1. **登录 GitHub**：https://github.com
   
2. **创建新仓库**：
   - 点击右上角 "+" → "New repository"
   - 仓库名称：`qbit-smart-controller`
   - 描述：`智能 qBittorrent 限速控制器 - 基于Lucky设备状态的自动限速系统`
   - 选择：**Public**（公开）或 **Private**（私有）
   - ⚠️ **不要勾选**以下选项：
     - ❌ Add a README file
     - ❌ Add .gitignore
     - ❌ Choose a license
   
3. **点击 "Create repository"**

4. **复制仓库地址**：
   - HTTPS: `https://github.com/YOUR_USERNAME/qbit-smart-controller.git`
   - SSH: `git@github.com:YOUR_USERNAME/qbit-smart-controller.git`

---

### 第二步：配置 Git（首次使用需要）

```bash
# 设置用户名（替换为你的 GitHub 用户名）
git config --global user.name "YourUsername"

# 设置邮箱（替换为你的 GitHub 邮箱）
git config --global user.email "your.email@example.com"

# 查看配置
git config --global --list
```

---

### 第三步：推送代码

#### 方法A：如果是新项目（推荐）

```bash
# 1. 进入项目目录
cd c:\Users\P52\qbit-smart-controller

# 2. 初始化 Git 仓库（如果还没有）
git init

# 3. 添加所有文件
git add .

# 4. 提交更改
git commit -m "feat: v2.0 完整重构优化

✨ 核心功能
- 实现自动限速控制循环
- Lucky设备监控
- qBittorrent速度控制

🔧 代码优化
- 清理重复代码
- 完善日志系统
- 资源管理优化

📖 文档完善
- 完整的README
- 使用指南
- 故障排查

🐳 Docker优化
- 健康检查
- 环境变量支持
- 日志管理"

# 5. 连接到 GitHub 仓库（替换为你的仓库地址）
git remote add origin https://github.com/YOUR_USERNAME/qbit-smart-controller.git

# 6. 设置主分支为 main
git branch -M main

# 7. 推送代码
git push -u origin main
```

#### 方法B：如果已经有 Git 仓库

```bash
# 1. 查看状态
git status

# 2. 添加更改
git add .

# 3. 提交
git commit -m "feat: v2.0 完整重构优化"

# 4. 推送
git push origin main
```

---

## 🔐 认证设置

### 选项1：使用 Personal Access Token（推荐新手）

#### 创建 Token：

1. GitHub 右上角头像 → **Settings**
2. 左侧最底部 → **Developer settings**
3. 左侧 → **Personal access tokens** → **Tokens (classic)**
4. 点击 **Generate new token** → **Generate new token (classic)**
5. 设置：
   - Note: `qbit-controller-token`
   - Expiration: `90 days`（或自定义）
   - 勾选权限：
     - ✅ **repo**（完整仓库权限）
6. 点击 **Generate token**
7. ⚠️ **立即复制 Token**（只显示一次！）

#### 使用 Token：

```bash
# 推送时会要求输入凭据：
Username: 你的GitHub用户名
Password: 粘贴你的Token（不是GitHub密码！）

# Windows: Token 会被保存，下次不用再输入
# Linux/Mac: 可以配置凭据缓存
git config --global credential.helper cache
# 或永久保存（不太安全）
git config --global credential.helper store
```

---

### 选项2：使用 SSH 密钥（推荐老手）

#### Windows 用户：

```powershell
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your.email@example.com"
# 按3次回车（使用默认路径，不设置密码）

# 2. 启动 ssh-agent
Get-Service ssh-agent | Set-Service -StartupType Manual
Start-Service ssh-agent

# 3. 添加密钥
ssh-add $env:USERPROFILE\.ssh\id_ed25519

# 4. 复制公钥
type $env:USERPROFILE\.ssh\id_ed25519.pub | clip
```

#### Linux/Mac 用户：

```bash
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your.email@example.com"
# 按3次回车

# 2. 启动 ssh-agent
eval "$(ssh-agent -s)"

# 3. 添加密钥
ssh-add ~/.ssh/id_ed25519

# 4. 复制公钥（Mac）
pbcopy < ~/.ssh/id_ed25519.pub

# 或者（Linux）
cat ~/.ssh/id_ed25519.pub
# 然后手动复制输出
```

#### 在 GitHub 添加 SSH Key：

1. GitHub 右上角头像 → **Settings**
2. 左侧 → **SSH and GPG keys**
3. 点击 **New SSH key**
4. Title: `My Computer`
5. Key: 粘贴刚才复制的公钥
6. 点击 **Add SSH key**

#### 使用 SSH 推送：

```bash
# 使用 SSH 地址添加远程仓库
git remote add origin git@github.com:YOUR_USERNAME/qbit-smart-controller.git

# 或者修改现有的远程地址
git remote set-url origin git@github.com:YOUR_USERNAME/qbit-smart-controller.git

# 测试连接
ssh -T git@github.com
# 应该看到: Hi username! You've successfully authenticated...

# 推送
git push -u origin main
```

---

## 🚨 常见问题

### 1. 推送被拒绝：`! [rejected] main -> main (fetch first)`

**原因**：远程仓库有本地没有的提交

**解决**：
```bash
# 拉取远程更改
git pull origin main --rebase

# 再次推送
git push origin main
```

---

### 2. 认证失败：`Authentication failed`

**检查清单**：
- [ ] Token 是否正确复制（没有多余空格）
- [ ] Token 权限是否包含 `repo`
- [ ] Token 是否过期
- [ ] 用户名是否正确

**重新输入凭据**（Windows）：
```bash
# 打开凭据管理器
control /name Microsoft.CredentialManager

# 删除 git:https://github.com 凭据
# 再次推送时会要求重新输入
```

---

### 3. 文件太大：`file size exceeds 100MB`

GitHub 单文件限制 100MB

**解决**：
```bash
# 查看大文件
find . -type f -size +100M

# 如果是不需要的文件，添加到 .gitignore
echo "big-file.zip" >> .gitignore
git rm --cached big-file.zip
git commit -m "Remove large file"
```

---

### 4. 分支名称不匹配

有些仓库默认分支是 `master`，有些是 `main`

**查看当前分支**：
```bash
git branch
```

**推送到正确的分支**：
```bash
# 如果是 master
git push origin master

# 如果是 main
git push origin main

# 重命名本地分支
git branch -M main  # 改为 main
git branch -M master  # 改为 master
```

---

### 5. 远程仓库不存在

**错误信息**：`Repository not found`

**检查**：
- [ ] 仓库地址是否正确
- [ ] 用户名是否正确
- [ ] 是否有权限访问该仓库

**查看远程地址**：
```bash
git remote -v
```

**修改远程地址**：
```bash
git remote set-url origin https://github.com/CORRECT_USERNAME/qbit-smart-controller.git
```

---

## 📝 后续更新代码

以后修改代码后推送：

```bash
# 1. 查看修改了哪些文件
git status

# 2. 添加要提交的文件
git add .                    # 添加所有文件
# 或
git add app/main.py          # 添加特定文件

# 3. 提交
git commit -m "fix: 修复某个bug"

# 4. 推送
git push

# 一行命令（不推荐新手）
git add . && git commit -m "update" && git push
```

---

## 📊 提交信息规范（可选）

建议使用语义化提交信息：

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加邮件通知功能` |
| `fix` | 修复 bug | `fix: 修复连接超时问题` |
| `docs` | 文档更新 | `docs: 更新README安装说明` |
| `style` | 代码格式 | `style: 格式化代码` |
| `refactor` | 重构 | `refactor: 重构日志模块` |
| `perf` | 性能优化 | `perf: 优化数据库查询` |
| `test` | 测试 | `test: 添加单元测试` |
| `chore` | 构建/工具 | `chore: 更新依赖` |

---

## 🎉 成功推送后

1. **访问你的仓库**：
   ```
   https://github.com/YOUR_USERNAME/qbit-smart-controller
   ```

2. **查看代码**：应该能看到所有文件

3. **检查 README**：GitHub 会自动显示 README.md

4. **添加 Topics**（可选）：
   - 点击仓库顶部的 ⚙️（设置齿轮）
   - 添加标签：`qbittorrent`, `lucky`, `automation`, `docker`, `fastapi`

5. **设置 About**（可选）：
   - 描述：`智能 qBittorrent 限速控制器`
   - Website：你的项目网站或文档
   - Topics：添加相关标签

6. **启用 Issues**（接收反馈）：
   - Settings → Features → Issues ✅

---

## 🔗 快速链接

- **GitHub 官方文档**：https://docs.github.com/
- **Git 教程**：https://git-scm.com/book/zh/v2
- **GitHub Desktop**：https://desktop.github.com/
- **VS Code Git 教程**：https://code.visualstudio.com/docs/sourcecontrol/overview

---

## 🆘 需要帮助？

如果遇到其他问题：

1. **查看错误信息**：仔细阅读 Git 输出的错误信息
2. **搜索解决方案**：复制错误信息到 Google/百度
3. **查看 Git 状态**：`git status` 查看当前状态
4. **查看日志**：`git log --oneline` 查看提交历史

---

**祝你推送成功！🎉**

