#!/bin/bash

# 自定义路径部署脚本
# 适配用户的实际宿主机路径：/home/myptyun/config 和 /home/myptyun/data

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="qbit-smart-controller"
USER_HOME="/home/myptyun"
CONFIG_DIR="$USER_HOME/config"
DATA_DIR="$USER_HOME/data"
PROJECT_DIR="$USER_HOME/$PROJECT_NAME"

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

# 检查是否为 root
if [ "$EUID" -eq 0 ]; then 
    log_warning "请不要使用 root 用户运行此脚本"
    log_info "建议使用普通用户，脚本会在需要时提示输入 sudo 密码"
    exit 1
fi

# 检查 Docker 和 Docker Compose
check_dependencies() {
    log_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 创建目录结构
create_directories() {
    log_info "创建目录结构..."
    
    # 创建用户主目录下的项目目录
    sudo mkdir -p "$PROJECT_DIR"/{config,data/{logs,config},app}
    
    # 创建您的自定义配置和数据目录
    sudo mkdir -p "$CONFIG_DIR" "$DATA_DIR"/logs
    
    # 设置权限
    sudo chown -R $USER:$USER "$PROJECT_DIR"
    sudo chown -R $USER:$USER "$CONFIG_DIR"
    sudo chown -R $USER:$USER "$DATA_DIR"
    
    log_success "目录结构创建完成"
}

# 初始化配置文件
init_config() {
    log_info "初始化配置文件..."
    
    # 在您的自定义路径创建配置文件
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
        log_success "默认配置文件已创建: $CONFIG_DIR/config.yaml"
        log_warning "请编辑配置文件，更新您的 qBittorrent 和 Lucky 设备信息"
    else
        log_info "配置文件已存在，跳过创建"
    fi
}

# 复制项目文件
copy_project_files() {
    log_info "复制项目文件..."
    
    # 获取脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # 复制必要的文件到项目目录
    cp -f "$SCRIPT_DIR/docker-compose.yml" "$PROJECT_DIR/"
    cp -f "$SCRIPT_DIR/Dockerfile" "$PROJECT_DIR/"
    cp -f "$SCRIPT_DIR/requirements.txt" "$PROJECT_DIR/"
    cp -f "$SCRIPT_DIR/version.py" "$PROJECT_DIR/"
    
    # 复制应用代码
    cp -rf "$SCRIPT_DIR/app" "$PROJECT_DIR/"
    
    log_success "项目文件复制完成"
}

# 创建自定义的 docker-compose.yml
create_custom_compose() {
    log_info "创建自定义 docker-compose.yml..."
    
    cat > "$PROJECT_DIR/docker-compose.yml" << EOF
version: '3.8'

services:
  qbit-controller:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: qbit-smart-controller
    restart: unless-stopped
    
    # 端口映射
    ports:
      - "5000:5000"
    
    # 卷映射 - 使用您的自定义路径
    volumes:
      # 配置文件映射（只读）- 使用您的实际路径
      - $CONFIG_DIR:/app/config:ro
      # 数据目录映射（读写）- 使用您的实际路径
      - $DATA_DIR:/app/data
    
    # 环境变量
    environment:
      - TZ=Asia/Shanghai
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
      - LOG_LEVEL=INFO
    
    # 网络配置
    networks:
      - qbit-network
    
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    
    # 日志配置
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
    
    # 资源限制（可选）
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

# 网络配置
networks:
  qbit-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
EOF
    
    log_success "自定义 docker-compose.yml 创建完成"
}

# 构建和启动容器
deploy_container() {
    log_info "构建和启动容器..."
    
    cd "$PROJECT_DIR"
    
    # 停止现有容器
    docker-compose down 2>/dev/null || true
    
    # 构建并启动
    docker-compose up -d --build
    
    log_success "容器部署完成"
}

# 检查服务状态
check_status() {
    log_info "检查服务状态..."
    
    cd "$PROJECT_DIR"
    
    # 等待服务启动
    sleep 10
    
    # 检查容器状态
    if docker-compose ps | grep -q "Up"; then
        log_success "容器运行正常"
    else
        log_error "容器启动失败"
        docker-compose logs
        exit 1
    fi
    
    # 检查健康状态
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        log_success "服务健康检查通过"
    else
        log_warning "服务健康检查失败，请检查日志"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
qBittorrent 智能控制器 - 自定义路径部署脚本

使用方法: $0 <命令> [参数]

命令:
  init     初始化部署（首次部署时使用）
  restart  重启服务
  stop     停止服务
  logs     查看日志
  status   检查服务状态
  help     显示帮助信息

路径配置:
  配置文件: $CONFIG_DIR/config.yaml
  数据目录: $DATA_DIR/
  项目目录: $PROJECT_DIR/

示例:
  $0 init                    # 首次部署
  $0 restart                 # 重启服务
  $0 logs                    # 查看日志

EOF
}

# 显示日志
show_logs() {
    log_info "查看容器日志..."
    cd "$PROJECT_DIR"
    docker-compose logs -f
}

# 停止服务
stop_service() {
    log_info "停止服务..."
    cd "$PROJECT_DIR"
    docker-compose down
    log_success "服务已停止"
}

# 主函数
main() {
    case "${1:-help}" in
        init)
            log_info "开始初始化部署..."
            log_info "使用自定义路径:"
            log_info "  配置文件: $CONFIG_DIR/config.yaml"
            log_info "  数据目录: $DATA_DIR/"
            log_info "  项目目录: $PROJECT_DIR/"
            echo ""
            
            check_dependencies
            create_directories
            init_config
            copy_project_files
            create_custom_compose
            deploy_container
            check_status
            
            log_success "初始化部署完成！"
            log_info "请编辑配置文件: $CONFIG_DIR/config.yaml"
            log_info "然后运行: $0 restart"
            echo ""
            log_info "访问地址: http://localhost:5000"
            ;;
        restart)
            log_info "重启服务..."
            cd "$PROJECT_DIR"
            docker-compose restart
            check_status
            log_success "服务重启完成！"
            ;;
        stop)
            stop_service
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
