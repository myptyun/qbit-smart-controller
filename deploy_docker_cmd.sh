#!/bin/bash

# 直接使用 Docker 命令部署脚本
# 适配您的实际路径：/home/myptyun/config 和 /home/myptyun/data

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
CONTAINER_NAME="qbit-smart-controller"
IMAGE_NAME="qbit-controller"
CONFIG_DIR="/home/myptyun/config"
DATA_DIR="/home/myptyun/data"
PORT="5000"

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

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    log_success "Docker 已安装: $(docker --version)"
}

# 创建目录和配置文件
setup_directories() {
    log_info "创建目录和配置文件..."
    
    # 创建目录
    sudo mkdir -p "$CONFIG_DIR" "$DATA_DIR"/logs
    sudo chown -R $USER:$USER "$CONFIG_DIR" "$DATA_DIR"
    
    # 创建配置文件
    if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
        cat > "$CONFIG_DIR/config.yaml" << 'EOF'
# 智能 qBittorrent 限速控制器配置

lucky_devices:
  - name: "我的Lucky设备"
    api_url: "http://192.168.1.100:16601/api/webservice/rules?openToken=YOUR_LUCKY_OPEN_TOKEN_HERE"
    weight: 5.0
    enabled: true
    description: "主要监控设备"

# 更新为您的实际qBittorrent地址
qbittorrent_instances:
  - name: "我的QB实例"
    host: "http://192.168.1.101:8080"  # 改为您实际的QB地址
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

# Web 服务配置
web_settings:
  host: "0.0.0.0"
  port: 5000
EOF
        log_success "配置文件已创建: $CONFIG_DIR/config.yaml"
        log_warning "请编辑配置文件，更新您的实际信息"
    else
        log_info "配置文件已存在"
    fi
}

# 构建镜像
build_image() {
    log_info "构建 Docker 镜像..."
    
    # 检查 Dockerfile 是否存在
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile 不存在，请确保在项目根目录运行此脚本"
        exit 1
    fi
    
    # 构建镜像
    docker build -t "$IMAGE_NAME" .
    
    log_success "镜像构建完成"
}

# 停止现有容器
stop_container() {
    log_info "停止现有容器..."
    
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        docker stop "$CONTAINER_NAME"
        log_success "容器已停止"
    fi
    
    if docker ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
        docker rm "$CONTAINER_NAME"
        log_success "容器已删除"
    fi
}

# 启动容器
start_container() {
    log_info "启动容器..."
    
    # 使用您之前的命令格式，但适配您的实际路径
    # 注意：配置目录不使用 :ro (只读)，以便在 Web 界面中保存配置
    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart unless-stopped \
        -p "$PORT:5000" \
        -v "$CONFIG_DIR:/app/config" \
        -v "$DATA_DIR:/app/data" \
        -e TZ=Asia/Shanghai \
        -e PYTHONUNBUFFERED=1 \
        -e LOG_LEVEL=INFO \
        "$IMAGE_NAME"
    
    log_success "容器启动完成"
}

# 检查容器状态
check_status() {
    log_info "检查容器状态..."
    
    # 等待容器启动
    sleep 5
    
    # 检查容器是否运行
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        log_success "容器运行正常"
    else
        log_error "容器启动失败"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
    
    # 检查健康状态
    if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
        log_success "服务健康检查通过"
    else
        log_warning "服务健康检查失败，请检查日志"
    fi
}

# 显示日志
show_logs() {
    log_info "查看容器日志..."
    docker logs -f "$CONTAINER_NAME"
}

# 重启容器
restart_container() {
    log_info "重启容器..."
    docker restart "$CONTAINER_NAME"
    check_status
    log_success "容器重启完成"
}

# 显示帮助信息
show_help() {
    cat << EOF
qBittorrent 智能控制器 - Docker 命令部署脚本

使用方法: $0 <命令>

命令:
  init     初始化部署（首次部署时使用）
  restart  重启容器
  stop     停止容器
  logs     查看日志
  status   检查容器状态
  help     显示帮助信息

配置:
  容器名称: $CONTAINER_NAME
  镜像名称: $IMAGE_NAME
  端口映射: $PORT:5000
  配置文件: $CONFIG_DIR/config.yaml
  数据目录: $DATA_DIR/

示例:
  $0 init                    # 首次部署
  $0 restart                 # 重启容器
  $0 logs                    # 查看日志

EOF
}

# 主函数
main() {
    case "${1:-help}" in
        init)
            log_info "开始初始化部署..."
            log_info "使用您的自定义路径:"
            log_info "  配置文件: $CONFIG_DIR/config.yaml"
            log_info "  数据目录: $DATA_DIR/"
            echo ""
            
            check_dependencies
            setup_directories
            build_image
            stop_container
            start_container
            check_status
            
            log_success "初始化部署完成！"
            log_info "请编辑配置文件: $CONFIG_DIR/config.yaml"
            log_info "然后运行: $0 restart"
            echo ""
            log_info "访问地址: http://localhost:$PORT"
            ;;
        restart)
            restart_container
            ;;
        stop)
            log_info "停止容器..."
            docker stop "$CONTAINER_NAME"
            log_success "容器已停止"
            ;;
        logs)
            show_logs
            ;;
        status)
            check_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
