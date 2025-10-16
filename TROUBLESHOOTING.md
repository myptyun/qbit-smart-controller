# 故障排除指南

## 问题 1: 版本号显示 v2.0.0-dev

### 原因
Docker 容器使用的是旧镜像，没有包含新的版本信息生成逻辑。

### 解决步骤

#### 1. 本地测试版本信息生成
```bash
# Windows PowerShell
python test_version_build.py

# Linux/Mac
python3 test_version_build.py
```

如果显示真实版本号（如 v2.42.e471e7b），说明版本生成正常。

#### 2. 重新构建 Docker 镜像

**在 Debian 服务器上执行：**

```bash
# 进入项目目录
cd ~/qbit-smart-controller

# 拉取最新代码
git pull origin main

# 停止并删除旧容器
docker-compose down

# 删除旧镜像（重要！）
docker rmi qbit-smart-controller:latest

# 重新构建镜像（不使用缓存）
docker-compose build --no-cache

# 启动新容器
docker-compose up -d

# 查看日志确认版本
docker-compose logs -f
```

#### 3. 验证版本信息

访问网页后，检查：
- 导航栏右上角的版本号
- 浏览器控制台是否有错误
- API 端点：`http://你的IP:5000/api/status`

**预期响应：**
```json
{
  "status": "running",
  "version": "2.42.e471e7b",
  "version_string": "v2.42.e471e7b (Build: 2025-10-16 ...)",
  "commit_hash": "e471e7b",
  "build_time": "2025-10-16 ..."
}
```

---

## 问题 2: qBittorrent 连接失败

### 常见原因

1. **网络不通**
   - qBittorrent 未运行
   - IP/端口配置错误
   - 防火墙阻止

2. **认证失败**
   - 用户名/密码错误
   - qBittorrent 开启了旁路认证白名单

3. **配置问题**
   - config.yaml 配置错误

### 诊断步骤

#### 1. 检查配置文件

```bash
# 查看配置
cat config/config.yaml
```

确认以下内容正确：
```yaml
qbittorrent_instances:
  - name: "我的QB实例"
    host: "http://192.168.2.21:8080"  # 注意：http 还是 https
    username: "admin"
    password: "adminadmin"
    enabled: true
```

#### 2. 测试网络连接

**从 Docker 容器内测试：**

```bash
# 进入容器
docker-compose exec app bash

# 测试网络连接
curl -v http://192.168.2.21:8080/api/v2/app/version

# 测试登录
curl -i -X POST \
  -d "username=admin&password=adminadmin" \
  http://192.168.2.21:8080/api/v2/auth/login

# 退出容器
exit
```

#### 3. 检查 qBittorrent 设置

在 qBittorrent Web UI 中：

1. **工具 → 选项 → Web UI**
   - 确认端口号（默认 8080）
   - 确认用户名和密码
   
2. **旁路本地主机认证**
   - 如果勾选了"对本地主机上的客户端跳过身份验证"
   - 需要确保容器和 qBittorrent 在同一网络

3. **IP 地址白名单**
   - 如果启用了白名单，添加容器 IP
   - 或者禁用白名单

#### 4. 使用调试 API

访问调试端点获取详细错误信息：

```bash
# 浏览器或 curl
curl http://你的IP:5000/api/debug/qbit/0
```

这会返回详细的连接诊断信息。

#### 5. 查看容器日志

```bash
# 实时查看日志
docker-compose logs -f app

# 查看最后 50 行
docker-compose logs --tail=50 app
```

查找以下关键词：
- `❌` 错误标记
- `QB连接异常`
- `登录失败`
- `403` 或 `401` HTTP 状态码

### 常见解决方案

#### 方案 1: qBittorrent 在同一主机上

如果 qBittorrent 和容器在同一台机器：

```yaml
qbittorrent_instances:
  - host: "http://host.docker.internal:8080"  # Windows/Mac
  # 或
  - host: "http://172.17.0.1:8080"  # Linux (Docker 默认网关)
```

#### 方案 2: 网络模式调整

在 `docker-compose.yml` 中使用主机网络：

```yaml
services:
  app:
    network_mode: "host"
```

⚠️ 注意：使用 host 网络后，端口映射会失效。

#### 方案 3: 禁用认证（仅测试）

临时在 qBittorrent 中禁用认证进行测试：
- 勾选"对本地主机上的客户端跳过身份验证"
- 确认容器能否连接

---

## 快速诊断命令

在 Debian 服务器上运行：

```bash
#!/bin/bash
echo "=== qBittorrent 连接诊断 ==="

# 1. 检查容器状态
echo -e "\n[1/5] 容器状态:"
docker-compose ps

# 2. 检查网络连接
echo -e "\n[2/5] 网络测试:"
docker-compose exec app curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://192.168.2.21:8080/

# 3. 测试 qBittorrent API
echo -e "\n[3/5] qBittorrent API 测试:"
docker-compose exec app curl -s http://192.168.2.21:8080/api/v2/app/version

# 4. 查看最近日志
echo -e "\n[4/5] 最近日志:"
docker-compose logs --tail=20 app | grep -i "qb\|error"

# 5. 检查配置
echo -e "\n[5/5] 配置文件:"
cat config/config.yaml | grep -A 6 "qbittorrent_instances"

echo -e "\n=== 诊断完成 ==="
```

保存为 `diagnose.sh` 并运行：
```bash
chmod +x diagnose.sh
./diagnose.sh
```

---

## 需要帮助？

如果以上步骤无法解决问题，请提供：

1. Docker 容器日志：`docker-compose logs --tail=100 app > logs.txt`
2. 配置文件（隐藏密码）：`cat config/config.yaml`
3. 网络测试结果
4. qBittorrent 版本和设置截图

## 成功标志

当一切正常时，你会看到：

✅ 版本号显示真实版本（如 v2.42.e471e7b）  
✅ qBittorrent 状态卡片显示绿色"已连接"  
✅ 可以看到下载/上传速度  
✅ 日志中没有错误信息

