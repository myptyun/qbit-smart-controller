#!/bin/bash

# qBittorrent 智能控制器 Docker 部署脚本
# 使用方法: ./deploy.sh [init|update|restart|backup|restore]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="qbit-smart-controller"
PROJECT_DIR="/opt/$PROJECT_NAME"
BACKUP_DIR="/opt/backups/$PROJECT_NAME"

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

# 检查 Docker 和 Docker Compose
check_dependencies() {
    log_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 创建目录结构
create_directories() {
    log_info "创建目录结构..."
    
    sudo mkdir -p "$PROJECT_DIR"/{config,data/{logs,config},app}
    sudo mkdir -p "$BACKUP_DIR"
    
    # 设置权限
    sudo chown -R $USER:$USER "$PROJECT_DIR"
    sudo chown -R $USER:$USER "$BACKUP_DIR"
    chmod -R 755 "$PROJECT_DIR"
    
    log_success "目录结构创建完成"
}

# 初始化配置文件
init_config() {
    log_info "初始化配置文件..."
    
    # 创建默认配置文件
    if [ ! -f "$PROJECT_DIR/config/config.yaml" ]; then
        cat > "$PROJECT_DIR/config/config.yaml" << 'EOF'
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
        log_success "默认配置文件已创建: $PROJECT_DIR/config/config.yaml"
        log_warning "请编辑配置文件，更新您的 qBittorrent 和 Lucky 设备信息"
    else
        log_info "配置文件已存在，跳过创建"
    fi
    
    # 创建环境配置文件
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        cat > "$PROJECT_DIR/.env" << 'EOF'
# 时区设置
TZ=Asia/Shanghai

# Python 设置
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# 日志级别
LOG_LEVEL=INFO
EOF
        log_success "环境配置文件已创建: $PROJECT_DIR/.env"
    fi
}

# 复制项目文件
copy_project_files() {
    log_info "复制项目文件..."
    
    # 获取脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # 复制必要的文件
    cp -f "$SCRIPT_DIR/docker-compose.yml" "$PROJECT_DIR/"
    cp -f "$SCRIPT_DIR/Dockerfile" "$PROJECT_DIR/"
    cp -f "$SCRIPT_DIR/requirements.txt" "$PROJECT_DIR/"
    cp -f "$SCRIPT_DIR/version.py" "$PROJECT_DIR/"
    
    # 复制应用代码
    cp -rf "$SCRIPT_DIR/app" "$PROJECT_DIR/"
    
    log_success "项目文件复制完成"
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

# 备份数据
backup_data() {
    log_info "备份数据..."
    
    DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"
    
    # 创建备份
    tar -czf "$BACKUP_FILE" -C "$PROJECT_DIR" config data
    
    # 清理旧备份（保留最近7天）
    find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true
    
    log_success "备份完成: $BACKUP_FILE"
}

# 恢复数据
restore_data() {
    if [ -z "$2" ]; then
        log_error "请指定备份文件路径"
        log_info "可用的备份文件："
        ls -la "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null || log_info "没有找到备份文件"
        exit 1
    fi
    
    BACKUP_FILE="$2"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "备份文件不存在: $BACKUP_FILE"
        exit 1
    fi
    
    log_info "恢复数据从: $BACKUP_FILE"
    
    # 停止容器
    cd "$PROJECT_DIR"
    docker-compose down
    
    # 恢复数据
    tar -xzf "$BACKUP_FILE" -C "$PROJECT_DIR"
    
    # 重启容器
    docker-compose up -d
    
    log_success "数据恢复完成"
}

# 显示帮助信息
show_help() {
    cat << EOF
qBittorrent 智能控制器 Docker 部署脚本

使用方法: $0 <命令> [参数]

命令:
  init     初始化部署（首次部署时使用）
  update   更新部署（代码更新后使用）
  restart  重启服务
  backup   备份数据
  restore  恢复数据
  status   检查服务状态
  logs     查看日志
  help     显示帮助信息

示例:
  $0 init                    # 首次部署
  $0 update                  # 更新部署
  $0 backup                  # 备份数据
  $0 restore /path/to/backup.tar.gz  # 恢复数据
  $0 logs                    # 查看日志

EOF
}

# 查看日志
show_logs() {
    log_info "查看容器日志..."
    cd "$PROJECT_DIR"
    docker-compose logs -f
}

# 主函数
main() {
    case "${1:-help}" in
        init)
            log_info "开始初始化部署..."
            check_dependencies
            create_directories
            init_config
            copy_project_files
            deploy_container
            check_status
            log_success "初始化部署完成！"
            log_info "请编辑配置文件: $PROJECT_DIR/config/config.yaml"
            log_info "然后运行: $0 restart"
            ;;
        update)
            log_info "开始更新部署..."
            backup_data
            copy_project_files
            deploy_container
            check_status
            log_success "更新部署完成！"
            ;;
        restart)
            log_info "重启服务..."
            cd "$PROJECT_DIR"
            docker-compose restart
            check_status
            log_success "服务重启完成！"
            ;;
        backup)
            backup_data
            ;;
        restore)
            restore_data "$@"
            ;;
        status)
            check_status
            ;;
        logs)
            show_logs
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
