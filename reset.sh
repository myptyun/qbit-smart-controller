#!/bin/bash

###############################################################################
# qBit Smart Controller - 完全重置脚本
# 停止、清理、拉取最新代码、重新构建
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

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
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

print_header "🔄 qBit Smart Controller 完全重置"
print_warning "此操作将："
echo "  1. 停止并删除所有容器"
echo "  2. 删除 Docker 镜像"
echo "  3. 清理未使用的容器和网络"
echo "  4. 备份配置文件"
echo "  5. 拉取最新代码"
echo "  6. 重新构建并启动"
echo ""

read -p "确认继续？(y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_info "已取消操作"
    exit 0
fi

# 步骤1：备份配置
print_header "💾 步骤 1/6: 备份配置文件"
if [ -f "config/config.yaml" ]; then
    backup_file="config/config.yaml.backup.$(date +%Y%m%d_%H%M%S)"
    cp config/config.yaml "$backup_file"
    print_success "配置文件已备份到: $backup_file"
else
    print_warning "未找到配置文件"
fi

# 步骤2：停止并删除容器
print_header "🛑 步骤 2/6: 停止并删除容器"
docker compose down
print_success "容器已停止并删除"

# 步骤3：删除镜像
print_header "🗑️ 步骤 3/6: 删除旧镜像"
if docker images | grep -q "qbit-smart-controller"; then
    docker rmi qbit-smart-controller-qbit-controller || true
    print_success "旧镜像已删除"
else
    print_warning "未找到旧镜像"
fi

# 步骤4：清理 Docker
print_header "🧹 步骤 4/6: 清理 Docker 资源"
print_info "清理未使用的容器..."
docker container prune -f
print_info "清理未使用的网络..."
docker network prune -f
print_success "Docker 资源清理完成"

# 步骤5：拉取最新代码
print_header "📥 步骤 5/6: 拉取最新代码"
print_info "正在拉取最新代码..."
git fetch origin
git reset --hard origin/main
print_success "代码已更新到最新版本"
git log -1 --oneline

# 步骤6：重新构建并启动
print_header "🏗️ 步骤 6/6: 重新构建并启动"
print_info "正在构建 Docker 镜像..."
docker compose build --no-cache

print_info "正在启动服务..."
docker compose up -d

# 等待服务启动
print_info "等待服务启动..."
sleep 5

# 检查状态
print_header "📊 服务状态"
if docker compose ps | grep -q "Up"; then
    print_success "✅ 服务启动成功！"
    echo ""
    docker compose ps
    echo ""
    print_info "查看日志：docker compose logs -f"
else
    print_error "❌ 服务启动失败"
    print_info "查看错误日志：docker logs qbit-smart-controller"
    exit 1
fi

print_success "🎉 重置完成！"


