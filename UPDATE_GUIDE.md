# qBit Smart Controller - 更新指南

本文档说明如何在 Debian 服务器上快速更新和管理项目。

## 📋 目录

- [更新脚本说明](#更新脚本说明)
- [使用方法](#使用方法)
- [故障排除](#故障排除)

---

## 🛠️ 更新脚本说明

### 1. `update.sh` - 完整更新（推荐）

**用途**：停止容器 → 备份配置 → 拉取代码 → 重新构建 → 启动服务

**适用场景**：
- 有重大代码更新
- 依赖包有变化（requirements.txt）
- Dockerfile 有修改
- 首次更新或长时间未更新

**执行时间**：约 2-5 分钟

```bash
cd ~/qbit-smart-controller
chmod +x update.sh
./update.sh
```

### 2. `quick_update.sh` - 快速更新

**用途**：拉取代码 → 重启容器（不重新构建）

**适用场景**：
- 只有 Python 代码修改
- 配置文件更新
- 前端页面更新
- 小修复和优化

**执行时间**：约 10-30 秒

```bash
cd ~/qbit-smart-controller
chmod +x quick_update.sh
./quick_update.sh
```

### 3. `reset.sh` - 完全重置

**用途**：停止 → 删除容器和镜像 → 清理资源 → 拉取代码 → 重新构建

**适用场景**：
- 遇到严重问题需要完全重置
- Docker 缓存问题
- 配置混乱需要重新开始

**执行时间**：约 3-8 分钟

```bash
cd ~/qbit-smart-controller
chmod +x reset.sh
./reset.sh
```

---

## 📖 使用方法

### 首次设置

```bash
# 1. 进入项目目录
cd ~/qbit-smart-controller

# 2. 赋予脚本执行权限
chmod +x update.sh quick_update.sh reset.sh

# 3. 执行完整更新
./update.sh
```

### 日常更新流程

#### 场景1：GitHub 有新代码 → 快速更新

```bash
cd ~/qbit-smart-controller
./quick_update.sh
```

#### 场景2：有 Docker 相关更新 → 完整更新

```bash
cd ~/qbit-smart-controller
./update.sh
```

#### 场景3：遇到问题 → 完全重置

```bash
cd ~/qbit-smart-controller
./reset.sh
```

---

## 🔧 手动操作（高级）

如果你想手动控制每一步：

### 停止服务

```bash
cd ~/qbit-smart-controller
docker compose down
```

### 拉取最新代码

```bash
git pull origin main
```

### 重新构建并启动

```bash
# 完全重新构建
docker compose up -d --build

# 或者只重启
docker compose restart
```

### 查看日志

```bash
# 实时日志
docker compose logs -f

# 只看最近50行
docker compose logs -f --tail=50

# 查看错误日志
docker logs qbit-smart-controller 2>&1 | grep -i error
```

### 查看服务状态

```bash
docker compose ps
```

### 进入容器

```bash
docker exec -it qbit-smart-controller bash
```

---

## 🐛 故障排除

### 问题1：权限错误

```bash
# 错误：Permission denied
# 解决：
chmod +x update.sh quick_update.sh reset.sh
```

### 问题2：容器名冲突

```bash
# 错误：Container name already in use
# 解决：
docker compose down
docker container prune -f
./update.sh
```

### 问题3：镜像构建失败

```bash
# 错误：Build failed
# 解决：清理并重新构建
docker compose down
docker rmi qbit-smart-controller-qbit-controller
docker compose build --no-cache
docker compose up -d
```

### 问题4：服务无法启动

```bash
# 1. 查看详细日志
docker logs qbit-smart-controller

# 2. 检查配置文件
cat config/config.yaml

# 3. 检查端口占用
netstat -tulpn | grep 5000

# 4. 如果端口被占用，修改 docker-compose.yml
# 将 "5000:5000" 改为 "8080:5000"
```

### 问题5：配置文件丢失

```bash
# 检查备份文件
ls -la config/*.backup.*

# 恢复最新备份
cp config/config.yaml.backup.YYYYMMDD_HHMMSS config/config.yaml
```

### 问题6：Git 冲突

```bash
# 如果有本地修改冲突
git stash  # 保存本地修改
git pull origin main  # 拉取更新
git stash pop  # 恢复本地修改（可能需要手动解决冲突）

# 或者强制覆盖本地修改
git reset --hard origin/main
```

---

## 📝 更新日志查看

```bash
# 查看最近5次提交
git log -5 --oneline

# 查看详细变更
git log -5

# 查看某个文件的变更历史
git log -p app/main.py
```

---

## 🎯 最佳实践

1. **定期更新**：每周至少运行一次 `quick_update.sh`
2. **更新前备份**：重要配置更改前先备份
3. **查看日志**：更新后检查日志确保正常运行
4. **测试连接**：更新后测试 Lucky 和 qBittorrent 连接
5. **保持简洁**：不要在生产环境手动修改代码

---

## 📞 获取帮助

如果遇到无法解决的问题：

1. **查看完整日志**：
   ```bash
   docker logs qbit-smart-controller > error.log
   cat error.log
   ```

2. **检查系统资源**：
   ```bash
   free -h  # 内存
   df -h    # 磁盘
   docker stats  # Docker 资源使用
   ```

3. **重启 Docker 服务**（慎用）：
   ```bash
   sudo systemctl restart docker
   ```

---

## 🚀 快速参考

| 命令 | 用途 | 时间 |
|------|------|------|
| `./quick_update.sh` | 快速更新代码和重启 | 10-30秒 |
| `./update.sh` | 完整更新和重新构建 | 2-5分钟 |
| `./reset.sh` | 完全重置项目 | 3-8分钟 |
| `docker compose logs -f` | 查看实时日志 | - |
| `docker compose restart` | 重启服务 | 5-10秒 |
| `docker compose down` | 停止服务 | 2-5秒 |
| `docker compose up -d` | 启动服务 | 5-15秒 |

---

**更新愉快！** 🎉

