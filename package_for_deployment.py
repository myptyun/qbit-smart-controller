#!/usr/bin/env python3
"""
项目打包脚本 - 为远程部署准备文件
"""
import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

def create_deployment_package():
    """创建部署包"""
    print("📦 开始创建部署包...")
    
    # 创建临时目录
    temp_dir = Path("deployment_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    # 需要包含的文件和目录
    include_items = [
        "app/",
        "config/",
        "data/",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "version.py",
        "README.md",
        "MANUAL.md"
    ]
    
    # 需要排除的文件
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        "*.log",
        "*.tmp",
        "test_*.py",
        "debug_*.py",
        "check_*.py",
        "analyze_*.py",
        "simple_*.py",
        "comprehensive_*.py",
        "final_*.py",
        "simulation_*.py",
        "verify_*.py",
        "explain_*.py",
        "service_mapping_*.py",
        "service_matching_*.py",
        "remote_*.py",
        "ssh_*.py",
        "diagnose_*.py",
        "lucky_api_response.json",
        "deployment_temp/",
        ".git/"
    ]
    
    # 复制文件
    for item in include_items:
        src = Path(item)
        if src.exists():
            dst = temp_dir / item
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*exclude_patterns))
                print(f"✅ 复制目录: {item}")
            else:
                shutil.copy2(src, dst)
                print(f"✅ 复制文件: {item}")
        else:
            print(f"⚠️ 文件不存在: {item}")
    
    # 创建部署脚本
    create_deployment_scripts(temp_dir)
    
    # 创建压缩包
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"qbit-smart-controller-{timestamp}.zip"
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ 部署包创建完成: {zip_name}")
    
    # 清理临时目录
    shutil.rmtree(temp_dir)
    
    return zip_name

def create_deployment_scripts(temp_dir):
    """创建部署脚本"""
    
    # 远程部署脚本
    deploy_script = """#!/bin/bash
# 远程部署脚本
set -e

echo "🚀 开始部署 qbit-smart-controller..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 停止现有容器
echo "🛑 停止现有容器..."
docker stop qbit-smart-controller 2>/dev/null || true
docker rm qbit-smart-controller 2>/dev/null || true

# 备份现有数据
echo "💾 备份现有数据..."
if [ -d "data" ]; then
    cp -r data data_backup_$(date +%Y%m%d_%H%M%S)
fi

# 构建新镜像
echo "🔨 构建新镜像..."
docker build -t qbit-smart-controller:latest .

# 启动新容器
echo "🚀 启动新容器..."
docker run -d \\
    --name qbit-smart-controller \\
    --restart unless-stopped \\
    -p 5000:5000 \\
    -v $(pwd)/config:/app/config \\
    -v $(pwd)/data:/app/data \\
    qbit-smart-controller:latest

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -f http://localhost:5000/api/controller/state > /dev/null 2>&1; then
    echo "✅ 部署成功！服务正在运行"
    echo "🌐 Web界面: http://$(hostname -I | awk '{print $1}'):5000"
else
    echo "❌ 部署失败，请检查日志"
    docker logs qbit-smart-controller
    exit 1
fi

echo "🎉 部署完成！"
"""
    
    with open(temp_dir / "deploy_remote.sh", "w", encoding="utf-8") as f:
        f.write(deploy_script)
    
    # 设置执行权限
    os.chmod(temp_dir / "deploy_remote.sh", 0o755)
    
    # 快速更新脚本
    update_script = """#!/bin/bash
# 快速更新脚本
set -e

echo "🔄 开始快速更新..."

# 停止容器
docker stop qbit-smart-controller

# 重新构建镜像
docker build -t qbit-smart-controller:latest .

# 启动容器
docker start qbit-smart-controller

echo "✅ 更新完成！"
"""
    
    with open(temp_dir / "quick_update.sh", "w", encoding="utf-8") as f:
        f.write(update_script)
    
    os.chmod(temp_dir / "quick_update.sh", 0o755)

if __name__ == "__main__":
    package_name = create_deployment_package()
    print(f"\n🎉 部署包已创建: {package_name}")
    print("\n📋 部署步骤:")
    print("1. 将部署包上传到远程服务器")
    print("2. 解压部署包")
    print("3. 运行 ./deploy_remote.sh")
