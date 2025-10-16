#!/bin/bash

###############################################################################
# qBit Smart Controller - 快速更新脚本
# 只更新代码和重启容器，不重新构建镜像（适合小改动）
###############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

if [ ! -f "docker-compose.yml" ]; then
    print_error "请在项目根目录运行此脚本"
    exit 1
fi

print_header "⚡ qBit Smart Controller 快速更新"

# 拉取代码
print_info "正在拉取最新代码..."
git pull origin main

# 重启容器
print_info "正在重启容器..."
docker compose restart

# 检查状态
sleep 3
if docker compose ps | grep -q "Up"; then
    print_success "✅ 服务重启成功！"
    docker compose ps
else
    print_error "❌ 服务重启失败"
    exit 1
fi

print_info "查看日志：docker compose logs -f"


