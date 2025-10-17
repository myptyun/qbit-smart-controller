# 自定义路径部署指南

## 📁 您的实际路径配置

根据您的需求，系统将使用以下路径：

- **配置文件**: `/home/myptyun/config/config.yaml`
- **数据目录**: `/home/myptyun/data/`
- **日志文件**: `/home/myptyun/data/logs/`

## 🚀 部署方式

### 方式一：使用 Docker Compose（推荐）

```bash
# 1. 添加执行权限
chmod +x deploy_custom_path.sh

# 2. 初始化部署
./deploy_custom_path.sh init

# 3. 编辑配置文件
nano /home/myptyun/config/config.yaml

# 4. 重启服务
./deploy_custom_path.sh restart
```

### 方式二：直接使用 Docker 命令

```bash
# 1. 添加执行权限
chmod +x deploy_docker_cmd.sh

# 2. 初始化部署
./deploy_docker_cmd.sh init

# 3. 编辑配置文件
nano /home/myptyun/config/config.yaml

# 4. 重启服务
./deploy_docker_cmd.sh restart
```

## 🔧 手动部署命令

如果您想手动执行，可以使用以下命令：

### 1. 创建目录

```bash
mkdir -p /home/myptyun/config
mkdir -p /home/myptyun/data/logs
```

### 2. 创建配置文件

```bash
cat > /home/myptyun/config/config.yaml << 'EOF'
# 智能 qBittorrent 限速控制器配置

lucky_devices:
  - name: "我的Lucky设备"
    api_url: "http://192.168.1.100:16601/api/webservice/rules?openToken=YOUR_LUCKY_OPEN_TOKEN_HERE"
    weight: 5.0
    enabled: true
    description: "主要监控设备"

qbittorrent_instances:
  - name: "我的QB实例"
    host: "http://192.168.1.101:8080"
    username: "admin"
    password: "adminadmin"
    enabled: true
    description: "qBittorrent测试"

controller_settings:
  poll_interval: 2
  limit_on_delay: 5
  limit_off_delay: 30
  retry_interval: 10
  limited_download: 1024
  limited_upload: 512
  normal_download: 0
  normal_upload: 0

web_settings:
  host: "0.0.0.0"
  port: 5000
EOF
```

### 3. 构建并运行容器

#### 使用 Docker Compose：

```bash
# 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  qbit-controller:
    build: .
    container_name: qbit-smart-controller
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - /home/myptyun/config:/app/config:ro
      - /home/myptyun/data:/app/data
    environment:
      - TZ=Asia/Shanghai
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO

networks:
  default:
    driver: bridge
EOF

# 启动服务
docker-compose up -d --build
```

#### 直接使用 Docker 命令：

```bash
# 构建镜像
docker build -t qbit-controller .

# 运行容器
docker run -d \
  --name qbit-smart-controller \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /home/myptyun/config:/app/config:ro \
  -v /home/myptyun/data:/app/data \
  -e TZ=Asia/Shanghai \
  -e PYTHONUNBUFFERED=1 \
  -e LOG_LEVEL=INFO \
  qbit-controller
```

## 📋 常用命令

### 查看状态

```bash
# 检查容器状态
docker ps -f name=qbit-smart-controller

# 查看日志
docker logs -f qbit-smart-controller

# 检查健康状态
curl http://localhost:5000/health
```

### 管理容器

```bash
# 重启容器
docker restart qbit-smart-controller

# 停止容器
docker stop qbit-smart-controller

# 删除容器
docker rm qbit-smart-controller

# 重新构建镜像
docker build -t qbit-controller .
```

### 使用脚本管理

```bash
# 使用 Docker Compose 脚本
./deploy_custom_path.sh restart
./deploy_custom_path.sh logs
./deploy_custom_path.sh status

# 使用 Docker 命令脚本
./deploy_docker_cmd.sh restart
./deploy_docker_cmd.sh logs
./deploy_docker_cmd.sh status
```

## 📝 配置文件说明

配置文件位置：`/home/myptyun/config/config.yaml`

### 重要配置项

1. **Lucky 设备配置**：
   ```yaml
   lucky_devices:
     - name: "我的Lucky设备"
       api_url: "http://YOUR_LUCKY_IP:16601/api/webservice/rules?openToken=YOUR_TOKEN"
       weight: 5.0
       enabled: true
   ```

2. **qBittorrent 实例配置**：
   ```yaml
   qbittorrent_instances:
     - name: "我的QB实例"
       host: "http://YOUR_QB_IP:8080"
       username: "your_username"
       password: "your_password"
       enabled: true
   ```

### 编辑配置文件

```bash
# 使用 nano 编辑器
nano /home/myptyun/config/config.yaml

# 使用 vim 编辑器
vim /home/myptyun/config/config.yaml

# 使用其他编辑器
code /home/myptyun/config/config.yaml  # VS Code
```

## 🔍 故障排除

### 1. 容器启动失败

```bash
# 查看详细日志
docker logs qbit-smart-controller

# 检查配置文件语法
cat /home/myptyun/config/config.yaml

# 检查目录权限
ls -la /home/myptyun/config/
ls -la /home/myptyun/data/
```

### 2. 配置文件不生效

```bash
# 检查挂载是否正确
docker inspect qbit-smart-controller | grep -A 10 "Mounts"

# 重启容器使配置生效
docker restart qbit-smart-controller
```

### 3. 权限问题

```bash
# 重新设置目录权限
sudo chown -R $USER:$USER /home/myptyun/config
sudo chown -R $USER:$USER /home/myptyun/data
sudo chmod -R 755 /home/myptyun/config
sudo chmod -R 755 /home/myptyun/data
```

## 📊 访问服务

- **Web 界面**: http://localhost:5000
- **健康检查**: http://localhost:5000/health
- **API 状态**: http://localhost:5000/api/status

## 🔄 更新部署

```bash
# 停止容器
docker stop qbit-smart-controller
docker rm qbit-smart-controller

# 重新构建镜像
docker build -t qbit-controller .

# 重新启动
docker run -d \
  --name qbit-smart-controller \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /home/myptyun/config:/app/config:ro \
  -v /home/myptyun/data:/app/data \
  -e TZ=Asia/Shanghai \
  -e PYTHONUNBUFFERED=1 \
  -e LOG_LEVEL=INFO \
  qbit-controller
```

---

**注意**: 配置文件和数据目录现在使用您的实际路径 `/home/myptyun/config` 和 `/home/myptyun/data`，确保数据持久化和配置管理。
