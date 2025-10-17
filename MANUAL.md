# qBittorrent 智能控制器 - 完整手册

## 📋 目录

1. [项目简介](#项目简介)
2. [系统要求](#系统要求)
3. [快速开始](#快速开始)
4. [详细配置](#详细配置)
5. [部署指南](#部署指南)
6. [故障排除](#故障排除)
7. [安全配置](#安全配置)
8. [维护管理](#维护管理)
9. [更新升级](#更新升级)

---

## 🚀 项目简介

qBittorrent 智能控制器是一个基于 Lucky 设备状态的智能限速控制系统，能够自动监控网络连接并根据设备活跃状态动态调整 qBittorrent 的下载/上传速度。

### 主要功能

- **智能限速**: 根据 Lucky 设备连接数自动调整 qBittorrent 速度
- **多实例支持**: 同时管理多个 qBittorrent 实例
- **连接韧性**: 自动重试和错误恢复机制
- **Web 界面**: 友好的 Web 管理界面
- **Docker 部署**: 容器化部署，易于管理

### 工作原理

1. 定期采集 Lucky 设备的连接数
2. 根据连接数阈值触发限速或恢复全速
3. 支持延迟触发，避免频繁切换
4. 提供详细的监控和日志记录

---

## 💻 系统要求

### 硬件要求
- **CPU**: 1 核心以上
- **内存**: 最少 512MB，推荐 1GB+
- **存储**: 最少 2GB 可用空间
- **网络**: 能够访问 qBittorrent 和 Lucky 设备

### 软件要求
- **操作系统**: Debian 11+ 或 Ubuntu 20.04+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

---

## ⚡ 快速开始

### 1. 安装依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 启动 Docker
sudo systemctl enable docker
sudo systemctl start docker

# 添加用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker
```

### 2. 部署项目

```bash
# 下载项目
git clone <repository-url>
cd qbit-smart-controller

# 运行部署脚本
chmod +x deploy.sh
./deploy.sh init

# 编辑配置
sudo nano /opt/qbit-smart-controller/config/config.yaml

# 重启服务
./deploy.sh restart
```

### 3. 访问界面

打开浏览器访问：`http://localhost:5000`

---

## ⚙️ 详细配置

### 配置文件结构

```yaml
# 智能 qBittorrent 限速控制器配置

# Lucky 设备配置
lucky_devices:
  - name: "我的Lucky设备"
    api_url: "http://192.168.1.100:16601/api/webservice/rules?openToken=YOUR_LUCKY_OPEN_TOKEN_HERE"
    weight: 5.0
    enabled: true
    description: "主要监控设备"

# qBittorrent 实例配置
qbittorrent_instances:
  - name: "我的QB实例"
    host: "http://192.168.1.101:8080"
    username: "admin"
    password: "adminadmin"
    enabled: true
    description: "qBittorrent测试"

# 控制器设置
controller_settings:
  poll_interval: 2        # 轮询间隔（秒）
  limit_on_delay: 5       # 限速触发延迟（秒）
  limit_off_delay: 30     # 恢复延迟（秒）
  retry_interval: 10      # 重试间隔（秒）
  limited_download: 1024  # 限速时下载速度（KB/s）
  limited_upload: 512     # 限速时上传速度（KB/s）
  normal_download: 0      # 正常时下载速度（0=不限速）
  normal_upload: 0        # 正常时上传速度（0=不限速）

# Web 服务配置
web_settings:
  host: "0.0.0.0"
  port: 5000
```

### 配置说明

#### Lucky 设备配置
- `api_url`: Lucky 设备的 API 地址和访问令牌
- `weight`: 权重系数，用于多设备加权计算
- `enabled`: 是否启用该设备监控

#### qBittorrent 实例配置
- `host`: qBittorrent Web UI 地址
- `username`: 登录用户名
- `password`: 登录密码
- `enabled`: 是否启用该实例

#### 控制器设置
- `poll_interval`: 数据采集间隔，建议 2-5 秒
- `limit_on_delay`: 检测到连接后多久开始限速
- `limit_off_delay`: 无连接后多久恢复全速
- `limited_download/upload`: 限速时的速度限制
- `normal_download/upload`: 正常时的速度限制（0=不限速）

---

## 🐳 部署指南

### Docker 部署

#### 1. 目录结构
```
/opt/qbit-smart-controller/
├── config/
│   └── config.yaml              # 配置文件
├── data/
│   ├── logs/                    # 日志文件
│   └── config/                  # 运行时配置
├── app/                         # 应用代码
├── docker-compose.yml           # Docker 编排
└── Dockerfile                   # 镜像构建
```

#### 2. 卷映射配置
```yaml
volumes:
  - ./config:/app/config:ro      # 配置文件（只读）
  - ./data:/app/data             # 数据目录（读写）
```

#### 3. 网络配置
```yaml
# 如果在同一机器上
host: "http://172.17.0.1:8080"  # Docker 默认网关

# 如果在不同机器上
host: "http://192.168.1.101:8080"  # 实际 IP 地址
```

### 系统服务配置

```bash
# 创建系统服务
sudo nano /etc/systemd/system/qbit-controller.service
```

```ini
[Unit]
Description=qBittorrent Smart Controller
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/qbit-smart-controller
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable qbit-controller
sudo systemctl start qbit-controller
```

---

## 🔧 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 查看详细日志
docker-compose logs

# 检查配置文件语法
docker-compose config

# 重新构建镜像
docker-compose build --no-cache
```

#### 2. 网络连接问题
```bash
# 测试网络连通性
docker-compose exec qbit-controller ping 192.168.1.101

# 检查端口开放
telnet 192.168.1.101 8080

# 检查 DNS 解析
docker-compose exec qbit-controller nslookup 192.168.1.101
```

#### 3. 连接重置错误
```bash
# 重置连接会话
curl -X POST http://localhost:5000/api/controller/reset-connections

# 检查连接健康状态
curl http://localhost:5000/api/controller/connection-health
```

#### 4. 权限问题
```bash
# 检查文件权限
ls -la /opt/qbit-smart-controller/

# 重新设置权限
sudo chown -R $USER:$USER /opt/qbit-smart-controller/
sudo chmod -R 755 /opt/qbit-smart-controller/
```

### 调试命令

```bash
# 进入容器调试
docker-compose exec qbit-controller bash

# 查看实时日志
docker-compose logs -f

# 查看应用日志
tail -f /opt/qbit-smart-controller/data/logs/controller.log

# 查看错误日志
tail -f /opt/qbit-smart-controller/data/logs/error.log
```

### 完全重置

```bash
# 停止并删除容器
docker-compose down
docker-compose rm -f

# 删除镜像（可选）
docker rmi qbit-smart-controller_qbit-controller

# 重新构建和启动
docker-compose up -d --build
```

---

## 🔒 安全配置

### 密码安全

⚠️ **重要**: 修改所有默认密码！

```yaml
# 修改 qBittorrent 密码
qbittorrent_instances:
  - name: "我的QB实例"
    username: "your_username"
    password: "your_strong_password"  # 使用强密码

# 修改 Lucky API Token
lucky_devices:
  - name: "我的Lucky设备"
    api_url: "http://192.168.1.100:16601/api/webservice/rules?openToken=YOUR_ACTUAL_TOKEN"
```

### 文件权限

```bash
# 设置配置文件权限
chmod 600 /opt/qbit-smart-controller/config/config.yaml
chown $USER:$USER /opt/qbit-smart-controller/config/config.yaml
```

### 网络安全

```bash
# 配置防火墙
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 5000/tcp

# 限制访问来源（可选）
sudo ufw allow from 192.168.1.0/24 to any port 5000
```

### 环境变量配置（推荐）

```bash
# 创建环境变量文件
nano /opt/qbit-smart-controller/.env
```

```bash
QB_HOST=http://192.168.1.101:8080
QB_USERNAME=admin
QB_PASSWORD=your_actual_password
LUCKY_TOKEN=your_actual_token
```

---

## 📊 维护管理

### 日志管理

```bash
# 查看应用日志
tail -f /opt/qbit-smart-controller/data/logs/controller.log

# 查看错误日志
tail -f /opt/qbit-smart-controller/data/logs/error.log

# 清理旧日志
find /opt/qbit-smart-controller/data/logs -name "*.log" -mtime +7 -delete
```

### 数据备份

```bash
# 创建备份脚本
cat > /opt/qbit-smart-controller/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/qbit-controller"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C /opt/qbit-smart-controller config/

# 备份日志
tar -czf $BACKUP_DIR/data_$DATE.tar.gz -C /opt/qbit-smart-controller data/

# 清理旧备份（保留最近7天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR"
EOF

chmod +x /opt/qbit-smart-controller/backup.sh
```

### 自动备份

```bash
# 添加到 crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /opt/qbit-smart-controller/backup.sh
```

### 监控脚本

```bash
# 创建监控脚本
cat > /opt/qbit-smart-controller/monitor.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "$(date): qBittorrent Controller is down, restarting..." >> /var/log/qbit-controller-monitor.log
    cd /opt/qbit-smart-controller
    docker-compose restart
fi
EOF

chmod +x /opt/qbit-smart-controller/monitor.sh

# 每5分钟检查一次
# */5 * * * * /opt/qbit-smart-controller/monitor.sh
```

---

## 🔄 更新升级

### 更新代码

```bash
# 备份当前配置
./deploy.sh backup

# 更新代码
git pull origin main

# 重新部署
./deploy.sh update

# 验证更新
./deploy.sh status
```

### 版本管理

```bash
# 查看当前版本
curl http://localhost:5000/api/status

# 查看更新日志
cat CHANGELOG.md
```

### 回滚操作

```bash
# 停止服务
docker-compose down

# 恢复备份
./deploy.sh restore backup_file.tar.gz

# 重启服务
docker-compose up -d
```

---

## 📞 技术支持

### 获取帮助

1. **查看日志**: 首先检查应用日志和错误日志
2. **健康检查**: 使用 `/health` 和 `/api/controller/connection-health` 端点
3. **重置连接**: 使用 `/api/controller/reset-connections` 端点
4. **联系支持**: 提供详细的错误信息和日志

### 有用的 API 端点

- `GET /health` - 服务健康检查
- `GET /api/status` - 服务状态信息
- `GET /api/config` - 配置信息
- `GET /api/controller/state` - 控制器状态
- `GET /api/controller/connection-health` - 连接健康状态
- `POST /api/controller/reset-connections` - 重置连接
- `GET /api/lucky/status` - Lucky 设备状态
- `GET /api/qbit/status` - qBittorrent 状态

---

## 📝 更新日志

### v2.0.0 (当前版本)
- ✅ 增强的连接韧性机制
- ✅ 智能重试和错误恢复
- ✅ 改进的日志记录
- ✅ 连接健康监控
- ✅ Debian/Ubuntu 优化
- ✅ 综合文档手册

### v1.x.x (历史版本)
- 基础功能实现
- Docker 部署支持
- Web 管理界面

---

**注意**: 本手册涵盖了所有必要的配置、部署、维护和故障排除信息。如有问题，请参考相应的章节或联系技术支持。
