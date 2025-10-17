#!/bin/bash

# 配置文件初始化脚本
# 用于在使用 docker run 命令前初始化配置文件和目录

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置路径
CONFIG_DIR="/home/myptyun/config"
DATA_DIR="/home/myptyun/data"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}配置文件初始化脚本${NC}"
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

# 创建目录
create_directories() {
    log_info "创建目录结构..."
    
    # 创建配置目录
    if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR"
        log_success "创建配置目录: $CONFIG_DIR"
    else
        log_info "配置目录已存在: $CONFIG_DIR"
    fi
    
    # 创建数据目录
    if [ ! -d "$DATA_DIR" ]; then
        mkdir -p "$DATA_DIR/logs"
        log_success "创建数据目录: $DATA_DIR"
    else
        log_info "数据目录已存在: $DATA_DIR"
    fi
    
    # 设置权限
    chmod -R 755 "$CONFIG_DIR" "$DATA_DIR"
    log_success "目录权限设置完成"
}

# 创建配置文件
create_config() {
    log_info "检查配置文件..."
    
    CONFIG_FILE="$CONFIG_DIR/config.yaml"
    
    if [ -f "$CONFIG_FILE" ]; then
        log_warning "配置文件已存在: $CONFIG_FILE"
        read -p "是否覆盖现有配置文件？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "保留现有配置文件"
            return
        fi
    fi
    
    log_info "创建默认配置文件..."
    
    cat > "$CONFIG_FILE" << 'EOF'
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

# Web 服务配置
web_settings:
  host: "0.0.0.0"
  port: 5000
EOF
    
    log_success "配置文件创建成功: $CONFIG_FILE"
    log_warning "请编辑配置文件，更新您的实际信息"
}

# 显示下一步操作
show_next_steps() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ 初始化完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}📝 下一步操作：${NC}"
    echo ""
    echo -e "1. 编辑配置文件："
    echo -e "   ${BLUE}nano $CONFIG_DIR/config.yaml${NC}"
    echo ""
    echo -e "2. 更新配置项："
    echo -e "   - Lucky API URL 和 Token"
    echo -e "   - qBittorrent 地址、用户名和密码"
    echo ""
    echo -e "3. 启动容器（注意：移除 :ro 标志）："
    echo -e "   ${BLUE}docker run -d \\${NC}"
    echo -e "   ${BLUE}  --name qbit-smart-controller \\${NC}"
    echo -e "   ${BLUE}  --restart unless-stopped \\${NC}"
    echo -e "   ${BLUE}  -p 5000:5000 \\${NC}"
    echo -e "   ${BLUE}  -v $CONFIG_DIR:/app/config \\${NC}"
    echo -e "   ${BLUE}  -v $DATA_DIR:/app/data \\${NC}"
    echo -e "   ${BLUE}  -e TZ=Asia/Shanghai \\${NC}"
    echo -e "   ${BLUE}  -e PYTHONUNBUFFERED=1 \\${NC}"
    echo -e "   ${BLUE}  qbit-controller${NC}"
    echo ""
    echo -e "4. 或者使用部署脚本："
    echo -e "   ${BLUE}./deploy_docker_cmd.sh init${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  重要提示：${NC}"
    echo -e "   - 配置目录不要使用 :ro (只读) 标志"
    echo -e "   - 这样才能在 Web 界面中保存配置修改"
    echo ""
}

# 主函数
main() {
    create_directories
    create_config
    show_next_steps
}

# 执行主函数
main

