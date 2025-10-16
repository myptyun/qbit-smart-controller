#!/bin/bash

###############################################################################
# qBit Smart Controller - 一键更新脚本
# 用于在 Debian 服务器上快速更新和重启项目
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    print_error "错误：未找到 docker-compose.yml 文件"
    print_error "请在项目根目录运行此脚本"
    exit 1
fi

print_header "🚀 qBit Smart Controller 一键更新"

# 步骤1：显示当前状态
print_info "当前分支信息："
git branch --show-current
print_info "当前提交："
git log -1 --oneline

# 步骤2：停止正在运行的容器
print_header "🛑 步骤 1/5: 停止正在运行的容器"
if docker compose ps | grep -q "Up"; then
    print_info "正在停止容器..."
    docker compose down
    print_success "容器已停止"
else
    print_warning "没有正在运行的容器"
fi

# 步骤3：备份配置文件
print_header "💾 步骤 2/5: 备份配置文件"
if [ -f "config/config.yaml" ]; then
    backup_file="config/config.yaml.backup.$(date +%Y%m%d_%H%M%S)"
    cp config/config.yaml "$backup_file"
    print_success "配置文件已备份到: $backup_file"
else
    print_warning "未找到配置文件，跳过备份"
fi

# 步骤4：拉取最新代码
print_header "📥 步骤 3/5: 拉取最新代码"
print_info "正在从 GitHub 拉取最新代码..."

# 保存本地修改（如果有）
if ! git diff-index --quiet HEAD --; then
    print_warning "检测到本地修改，正在保存..."
    git stash save "Auto stash before update at $(date)"
    print_success "本地修改已保存到 stash"
fi

# 拉取最新代码
git fetch origin
git pull origin main

print_success "代码已更新到最新版本"
print_info "最新提交："
git log -1 --oneline

# 步骤5：重新构建并启动
print_header "🏗️ 步骤 4/5: 重新构建 Docker 镜像"
print_info "正在构建 Docker 镜像..."
docker compose build --no-cache

print_success "Docker 镜像构建完成"

print_header "🚀 步骤 5/5: 启动服务"
print_info "正在启动容器..."
docker compose up -d

# 等待服务启动
print_info "等待服务启动..."
sleep 5

# 检查容器状态
print_header "📊 服务状态检查"
if docker compose ps | grep -q "Up"; then
    print_success "✅ 服务启动成功！"
    echo ""
    docker compose ps
    echo ""
else
    print_error "❌ 服务启动失败，请查看日志："
    print_info "docker logs qbit-smart-controller"
    exit 1
fi

# 显示日志
print_header "📝 实时日志（按 Ctrl+C 退出）"
print_info "正在显示实时日志..."
echo ""
docker compose logs -f --tail=50


