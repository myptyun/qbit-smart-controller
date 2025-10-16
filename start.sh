#!/bin/bash

echo "🚀 智能 qBittorrent 限速控制器 - 启动脚本"
echo "=========================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未安装 Docker"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: 未安装 Docker Compose"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# 检查配置文件
if [ ! -f "config/config.yaml" ]; then
    echo "⚠️  警告: 未找到配置文件 config/config.yaml"
    if [ -f "data/config/config.example.yaml" ]; then
        echo "📋 复制示例配置文件..."
        cp data/config/config.example.yaml config/config.yaml
        echo "✅ 已创建配置文件，请编辑 config/config.yaml 后重新启动"
        exit 0
    else
        echo "❌ 错误: 未找到示例配置文件"
        exit 1
    fi
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data/logs data/config config

# 停止旧容器
echo "🛑 停止旧容器..."
docker-compose down

# 构建并启动
echo "🔨 构建并启动容器..."
docker-compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ 服务启动成功！"
    echo ""
    echo "📊 访问 Web 界面: http://localhost:5000"
    echo "📝 查看日志: docker-compose logs -f"
    echo "🛑 停止服务: docker-compose down"
    echo ""
    echo "查看实时日志请运行: docker-compose logs -f"
else
    echo ""
    echo "❌ 服务启动失败"
    echo "请查看日志: docker-compose logs"
    exit 1
fi

