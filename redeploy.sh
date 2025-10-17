#!/bin/bash

# 快速重新部署脚本 - 修复配置只读和代码bug

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
echo -e "${BLUE}🚀 快速重新部署${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. 停止并删除容器
log_info "停止现有容器..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true
log_success "容器已清理"
echo ""

# 2. 重新构建镜像
log_info "重新构建镜像（包含代码修复）..."
docker build -t $IMAGE_NAME .
log_success "镜像构建完成"
echo ""

# 3. 启动容器（不使用 :ro 标志）
log_info "启动容器（配置目录使用读写模式）..."
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
    --health-cmd="curl -f http://localhost:5000/health || exit 1" \
    --health-interval=30s \
    --health-timeout=10s \
    --health-retries=3 \
    $IMAGE_NAME

log_success "容器已启动"
echo ""

# 4. 等待服务启动
log_info "等待服务启动..."
sleep 5

# 5. 验证部署
log_info "验证部署..."
echo ""

# 检查容器状态
if docker ps -q -f name=$CONTAINER_NAME > /dev/null 2>&1; then
    log_success "✅ 容器正在运行"
    docker ps -f name=$CONTAINER_NAME --format "   {{.Names}}: {{.Status}}"
    echo ""
else
    log_error "❌ 容器未运行"
    exit 1
fi

# 检查挂载点
log_info "检查挂载点:"
MOUNT_INFO=$(docker inspect $CONTAINER_NAME --format='{{range .Mounts}}{{if eq .Destination "/app/config"}}{{.Source}} -> {{.Destination}} ({{if .RW}}读写✅{{else}}只读❌{{end}}){{end}}{{end}}')
echo -e "   Config: $MOUNT_INFO"
echo ""

# 检查健康状态
log_info "等待健康检查..."
sleep 5

if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    log_success "✅ 健康检查通过"
    echo ""
else
    log_error "❌ 健康检查失败"
    echo ""
    log_info "查看最近日志:"
    docker logs --tail 20 $CONTAINER_NAME
    exit 1
fi

# 6. 显示结果
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 重新部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📋 修复内容:${NC}"
echo -e "   ✅ 修复了 Cookie 处理的代码 bug"
echo -e "   ✅ 配置目录现在是读写模式"
echo -e "   ✅ 可以在 Web 界面保存配置"
echo ""
echo -e "${YELLOW}🌐 访问地址:${NC}"
echo -e "   http://localhost:5000"
echo ""
echo -e "${YELLOW}📝 查看日志:${NC}"
echo -e "   ${BLUE}docker logs -f $CONTAINER_NAME${NC}"
echo ""
echo -e "${YELLOW}🔍 再次诊断:${NC}"
echo -e "   ${BLUE}./diagnose.sh${NC}"
echo ""

