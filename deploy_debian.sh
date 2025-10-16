#!/bin/bash

# Debian 13 一键部署脚本
# 用途：在 Debian 系统上自动部署 qBit Smart Controller

set -e  # 遇到错误立即退出

echo "========================================"
echo "🐧 Debian 13 部署脚本"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为 root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}⚠️  请不要使用 root 用户运行此脚本${NC}"
    echo "建议使用普通用户，脚本会在需要时提示输入 sudo 密码"
    exit 1
fi

# 检查网络连接
echo "🔍 检查网络连接..."
if ping -c 1 github.com &> /dev/null; then
    echo -e "${GREEN}✅ 网络连接正常${NC}"
else
    echo -e "${RED}❌ 无法连接到 GitHub，请检查网络${NC}"
    exit 1
fi

# 安装 Docker
echo ""
echo "🐳 检查 Docker 安装..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker 已安装: $(docker --version)${NC}"
else
    echo "📦 开始安装 Docker..."
    
    # 更新软件包
    sudo apt update
    
    # 安装依赖
    sudo apt install -y ca-certificates curl gnupg lsb-release
    
    # 添加 Docker GPG 密钥
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    
    # 设置 Docker 仓库
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装 Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # 启动 Docker
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # 添加用户到 docker 组
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}✅ Docker 安装完成${NC}"
    echo -e "${YELLOW}⚠️  请注销并重新登录以应用 docker 组权限${NC}"
fi

# 检查 Docker Compose
echo ""
echo "🔧 检查 Docker Compose..."
if docker compose version &> /dev/null; then
    echo -e "${GREEN}✅ Docker Compose 已安装: $(docker compose version)${NC}"
else
    echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker${NC}"
    exit 1
fi

# 安装 Git
echo ""
echo "📦 检查 Git 安装..."
if command -v git &> /dev/null; then
    echo -e "${GREEN}✅ Git 已安装: $(git --version)${NC}"
else
    echo "正在安装 Git..."
    sudo apt install -y git
    echo -e "${GREEN}✅ Git 安装完成${NC}"
fi

# 克隆项目
echo ""
echo "📥 克隆项目..."
PROJECT_DIR="$HOME/qbit-smart-controller"

if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠️  项目目录已存在: $PROJECT_DIR${NC}"
    read -p "是否删除并重新克隆？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_DIR"
        git clone https://github.com/myptyun/qbit-smart-controller.git "$PROJECT_DIR"
        echo -e "${GREEN}✅ 项目克隆完成${NC}"
    else
        echo "使用现有项目目录"
    fi
else
    git clone https://github.com/myptyun/qbit-smart-controller.git "$PROJECT_DIR"
    echo -e "${GREEN}✅ 项目克隆完成${NC}"
fi

# 进入项目目录
cd "$PROJECT_DIR"

# 创建配置文件
echo ""
echo "⚙️  配置项目..."
mkdir -p config data/logs

if [ ! -f "config/config.yaml" ]; then
    if [ -f "data/config/config.example.yaml" ]; then
        cp data/config/config.example.yaml config/config.yaml
        echo -e "${GREEN}✅ 配置文件已创建: config/config.yaml${NC}"
        echo -e "${YELLOW}⚠️  请编辑配置文件填写你的 Lucky 和 qBittorrent 信息${NC}"
        echo ""
        read -p "是否现在编辑配置文件？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} config/config.yaml
        fi
    else
        echo -e "${RED}❌ 找不到示例配置文件${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 配置文件已存在${NC}"
fi

# 构建并启动
echo ""
echo "🚀 构建并启动服务..."
docker compose down 2>/dev/null || true
docker compose up -d --build

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 检查服务状态..."
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ 服务启动成功！${NC}"
    echo ""
    echo "=========================================="
    echo "🎉 部署完成！"
    echo "=========================================="
    echo ""
    echo "📍 访问地址:"
    echo "   http://localhost:5000"
    echo "   http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "📝 常用命令:"
    echo "   查看日志: docker compose logs -f"
    echo "   停止服务: docker compose down"
    echo "   重启服务: docker compose restart"
    echo "   更新代码: git pull && docker compose up -d --build"
    echo ""
    echo "📖 配置文件: $PROJECT_DIR/config/config.yaml"
    echo "📊 日志文件: $PROJECT_DIR/data/logs/"
    echo ""
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    echo ""
    echo "查看日志排查问题:"
    echo "  docker compose logs"
    exit 1
fi

