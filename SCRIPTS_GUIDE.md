# 脚本使用指南

本项目提供了多个自动化脚本，方便在不同平台上管理和更新项目。

## 📋 目录

- [Windows 脚本](#windows-脚本)
- [Linux/Debian 脚本](#linuxdebian-脚本)
- [使用场景](#使用场景)

---

## 💻 Windows 脚本

### `push.bat` - 一键推送到 GitHub

**功能**：
- 自动添加所有更改
- 提交代码（支持自定义提交信息）
- 推送到 GitHub
- 失败时可重试

**使用方法**：
```cmd
# 双击运行，或在命令行中：
push.bat
```

### `start.bat` - 启动 Docker 项目（Windows）

**功能**：
- 构建 Docker 镜像
- 启动服务

**使用方法**：
```cmd
start.bat
```

---

## 🐧 Linux/Debian 脚本

### `update.sh` - 完整更新（推荐）⭐

**功能**：
1. 停止正在运行的容器
2. 备份配置文件
3. 拉取最新代码
4. 重新构建 Docker 镜像
5. 启动服务
6. 显示实时日志

**适用场景**：
- 有重大代码更新
- 依赖包变更
- Dockerfile 修改
- 首次更新

**使用方法**：
```bash
cd ~/qbit-smart-controller
chmod +x update.sh
./update.sh
```

**预计时间**：2-5 分钟

---

### `quick_update.sh` - 快速更新

**功能**：
1. 拉取最新代码
2. 重启容器（不重新构建）

**适用场景**：
- Python 代码修改
- 前端页面更新
- 配置文件更新
- 小修复

**使用方法**：
```bash
cd ~/qbit-smart-controller
chmod +x quick_update.sh
./quick_update.sh
```

**预计时间**：10-30 秒

---

### `reset.sh` - 完全重置

**功能**：
1. 备份配置
2. 停止并删除容器
3. 删除 Docker 镜像
4. 清理 Docker 资源
5. 拉取最新代码
6. 重新构建并启动

**适用场景**：
- 遇到严重问题
- Docker 缓存问题
- 需要完全重新开始

**使用方法**：
```bash
cd ~/qbit-smart-controller
chmod +x reset.sh
./reset.sh
```

**预计时间**：3-8 分钟

⚠️ **注意**：此脚本会提示确认，因为会删除容器和镜像

---

### `deploy_debian.sh` - 首次部署

**功能**：
1. 安装 Docker 和 Docker Compose
2. 克隆项目
3. 配置并启动

**适用场景**：
- 首次在 Debian 服务器上部署

**使用方法**：
```bash
wget https://raw.githubusercontent.com/myptyun/qbit-smart-controller/main/deploy_debian.sh
chmod +x deploy_debian.sh
sudo ./deploy_debian.sh
```

---

### `start.sh` - 启动项目（Linux）

**功能**：
- 构建并启动 Docker 服务

**使用方法**：
```bash
./start.sh
```

---

## 🎯 使用场景

### 场景1：每天查看 GitHub 有更新

```bash
# 在 Debian 服务器上运行
cd ~/qbit-smart-controller
./quick_update.sh
```

**原因**：快速，只需要重启容器

---

### 场景2：GitHub 显示有 Dockerfile 或依赖更新

```bash
# 在 Debian 服务器上运行
cd ~/qbit-smart-controller
./update.sh
```

**原因**：需要重新构建镜像

---

### 场景3：服务出现异常或无法启动

```bash
# 在 Debian 服务器上运行
cd ~/qbit-smart-controller
./reset.sh
```

**原因**：完全清理并重新开始

---

### 场景4：在 Windows 上修改代码后推送

```cmd
# 双击运行
push.bat

# 输入提交信息（或直接回车使用默认）
```

---

### 场景5：首次在新服务器上部署

```bash
# 下载并运行部署脚本
wget https://raw.githubusercontent.com/myptyun/qbit-smart-controller/main/deploy_debian.sh
chmod +x deploy_debian.sh
sudo ./deploy_debian.sh
```

---

## 📊 脚本对比

| 脚本 | 平台 | 时间 | 重新构建 | 适用场景 |
|------|------|------|----------|----------|
| `quick_update.sh` | Linux | 10-30秒 | ❌ | 代码小改动 |
| `update.sh` | Linux | 2-5分钟 | ✅ | 重大更新 |
| `reset.sh` | Linux | 3-8分钟 | ✅ | 解决问题 |
| `deploy_debian.sh` | Linux | 5-15分钟 | ✅ | 首次部署 |
| `push.bat` | Windows | <1分钟 | - | 推送代码 |
| `start.bat` | Windows | 2-3分钟 | ✅ | 启动服务 |

---

## 🔧 高级用法

### 组合使用

在 Windows 开发，推送后在 Debian 更新：

```bash
# 1. Windows 上修改代码
# 编辑代码...

# 2. Windows 上推送
push.bat

# 3. Debian 上更新
ssh user@debian
cd ~/qbit-smart-controller
./quick_update.sh  # 或 ./update.sh
```

---

### 自动化更新（可选）

在 Debian 上设置定时更新：

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨3点自动更新
0 3 * * * cd ~/qbit-smart-controller && ./quick_update.sh >> ~/qbit-update.log 2>&1
```

---

## 🐛 故障排除

### 脚本权限错误

```bash
# 赋予执行权限
chmod +x *.sh
```

### Git 冲突

```bash
# 保存本地修改
git stash

# 拉取更新
git pull origin main

# 恢复本地修改
git stash pop
```

### Docker 容器名冲突

```bash
# 停止并删除旧容器
docker compose down
docker container prune -f

# 重新启动
./update.sh
```

---

## 📚 相关文档

- [更新指南](UPDATE_GUIDE.md) - 详细的更新说明
- [README](README.md) - 项目总览
- [部署指南](deploy_debian.sh) - 首次部署
- [GitHub 推送指南](GITHUB_PUSH_GUIDE.md) - Git 相关

---

## 💡 最佳实践

1. **定期更新**：每周至少运行一次 `quick_update.sh`
2. **查看日志**：更新后检查日志确保正常运行
3. **备份配置**：修改配置前先备份
4. **测试连接**：更新后测试 Lucky 和 qBittorrent 连接
5. **使用脚本**：不要手动执行多个命令，使用提供的脚本

---

**祝使用愉快！** 🎉

