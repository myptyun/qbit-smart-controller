#!/bin/bash

# 快速修复配置问题脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CONTAINER_NAME="qbit-smart-controller"
IMAGE_NAME="qbit-controller"
CONFIG_DIR="/home/myptyun/config"
DATA_DIR="/home/myptyun/data"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔧 配置问题快速修复工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. 备份现有配置
backup_config() {
    log_info "步骤 1/7: 备份现有配置"
    
    if [ -f "$CONFIG_DIR/config.yaml" ]; then
        BACKUP_FILE="$CONFIG_DIR/config.yaml.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CONFIG_DIR/config.yaml" "$BACKUP_FILE"
        log_success "配置已备份到: $BACKUP_FILE"
    else
        log_warning "配置文件不存在，跳过备份"
    fi
    echo ""
}

# 2. 停止容器
stop_container() {
    log_info "步骤 2/7: 停止现有容器"
    
    if docker ps -q -f name=$CONTAINER_NAME > /dev/null 2>&1; then
        docker stop $CONTAINER_NAME
        log_success "容器已停止"
    else
        log_warning "容器未运行"
    fi
    echo ""
}

# 3. 删除容器
remove_container() {
    log_info "步骤 3/7: 删除现有容器"
    
    if docker ps -aq -f name=$CONTAINER_NAME > /dev/null 2>&1; then
        docker rm $CONTAINER_NAME
        log_success "容器已删除"
    else
        log_warning "容器不存在"
    fi
    echo ""
}

# 4. 确保目录存在
ensure_directories() {
    log_info "步骤 4/7: 确保目录存在并设置权限"
    
    mkdir -p "$CONFIG_DIR" "$DATA_DIR/logs"
    chmod -R 755 "$CONFIG_DIR" "$DATA_DIR"
    log_success "目录已创建并设置权限"
    echo ""
}

# 5. 创建或验证配置文件
verify_config() {
    log_info "步骤 5/7: 验证配置文件"
    
    if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
        log_warning "配置文件不存在，创建默认配置"
        cat > "$CONFIG_DIR/config.yaml" << 'EOF'
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
    description: "qBittorrent实例"

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
        log_success "默认配置文件已创建"
    else
        log_success "配置文件已存在"
    fi
    
    # 显示配置文件信息
    log_info "配置文件信息:"
    ls -lh "$CONFIG_DIR/config.yaml" | awk '{print "   权限:", $1, "大小:", $5}'
    echo ""
}

# 6. 启动容器（使用正确的挂载方式）
start_container() {
    log_info "步骤 6/7: 启动容器（使用读写模式）"
    
    log_warning "使用以下命令启动容器:"
    echo ""
    echo -e "${BLUE}docker run -d \\${NC}"
    echo -e "${BLUE}  --name $CONTAINER_NAME \\${NC}"
    echo -e "${BLUE}  --restart unless-stopped \\${NC}"
    echo -e "${BLUE}  --log-driver json-file \\${NC}"
    echo -e "${BLUE}  --log-opt max-size=50m \\${NC}"
    echo -e "${BLUE}  --log-opt max-file=5 \\${NC}"
    echo -e "${BLUE}  -p 5000:5000 \\${NC}"
    echo -e "${BLUE}  -v $CONFIG_DIR:/app/config \\${NC}"
    echo -e "${BLUE}  -v $DATA_DIR:/app/data \\${NC}"
    echo -e "${BLUE}  -e TZ=Asia/Shanghai \\${NC}"
    echo -e "${BLUE}  -e PYTHONUNBUFFERED=1 \\${NC}"
    echo -e "${BLUE}  -e LOG_LEVEL=INFO \\${NC}"
    echo -e "${BLUE}  $IMAGE_NAME${NC}"
    echo ""
    
    read -p "是否现在启动容器？(Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        docker run -d \
            --name $CONTAINER_NAME \
            --restart unless-stopped \
            --log-driver json-file \
            --log-opt max-size=50m \
            --log-opt max-file=5 \
            -p 5000:5000 \
            -v $CONFIG_DIR:/app/config \
            -v $DATA_DIR:/app/data \
            -e TZ=Asia/Shanghai \
            -e PYTHONUNBUFFERED=1 \
            -e LOG_LEVEL=INFO \
            $IMAGE_NAME
        
        log_success "容器已启动"
    else
        log_info "跳过启动，您可以稍后手动启动"
    fi
    echo ""
}

# 7. 验证修复
verify_fix() {
    log_info "步骤 7/7: 验证修复"
    
    sleep 5
    
    if docker ps -q -f name=$CONTAINER_NAME > /dev/null 2>&1; then
        log_success "容器正在运行"
        
        # 检查挂载
        log_info "检查挂载点:"
        docker inspect $CONTAINER_NAME --format='{{range .Mounts}}  {{if eq .Destination "/app/config"}}Config: {{.Source}} -> {{.Destination}} ({{if .RW}}读写✅{{else}}只读❌{{end}}){{end}}{{end}}' 2>/dev/null
        echo ""
        
        # 检查容器内配置文件
        if docker exec $CONTAINER_NAME test -f /app/config/config.yaml 2>/dev/null; then
            log_success "容器内可以访问配置文件"
        else
            log_error "容器内无法访问配置文件"
        fi
        
        # 测试健康检查
        log_info "等待服务启动..."
        sleep 3
        
        if curl -f http://localhost:5000/health > /dev/null 2>&1; then
            log_success "服务健康检查通过"
        else
            log_warning "服务健康检查失败，查看日志:"
            docker logs --tail 10 $CONTAINER_NAME
        fi
    else
        log_error "容器未运行"
    fi
    echo ""
}

# 显示下一步
show_next_steps() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ 修复完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}📝 下一步操作:${NC}"
    echo ""
    echo -e "1. 编辑配置文件，更新您的实际信息:"
    echo -e "   ${BLUE}nano $CONFIG_DIR/config.yaml${NC}"
    echo ""
    echo -e "2. 重启容器使配置生效:"
    echo -e "   ${BLUE}docker restart $CONTAINER_NAME${NC}"
    echo ""
    echo -e "3. 访问 Web 界面:"
    echo -e "   ${BLUE}http://localhost:5000${NC}"
    echo ""
    echo -e "4. 查看日志:"
    echo -e "   ${BLUE}docker logs -f $CONTAINER_NAME${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  提示:${NC}"
    echo -e "   - 现在配置目录是读写模式，可以在 Web 界面中保存配置"
    echo -e "   - 请更新配置文件中的 qBittorrent 用户名和密码"
    echo -e "   - 请更新 Lucky 设备的 API URL 和 Token"
    echo ""
}

# 主函数
main() {
    backup_config
    stop_container
    remove_container
    ensure_directories
    verify_config
    start_container
    verify_fix
    show_next_steps
}

# 执行主函数
main

