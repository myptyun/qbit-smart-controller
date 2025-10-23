#!/usr/bin/env python3
"""
项目清理脚本 - 移除测试和调试文件
"""
import os
from pathlib import Path

def cleanup_project():
    """清理项目文件"""
    print("[CLEANUP] 开始清理项目文件...")
    
    # 需要删除的测试和调试文件
    files_to_remove = [
        # 测试文件
        "test_*.py",
        "check_*.py", 
        "debug_*.py",
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
        "batch_disable_services.py",
        
        # 临时文件
        "lucky_api_response.json",
        "remote_commands.txt",
        "docker_restart_guide.md",
        
        # 清理脚本本身
        "cleanup_project.py"
    ]
    
    # 需要保留的重要文件
    keep_files = [
        "app/",
        "config/",
        "data/",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "version.py",
        "README.md",
        "MANUAL.md",
        "FAQ.md",
        "CUSTOM_PATH_DEPLOYMENT.md",
        "deploy_*.sh",
        "init_config.sh",
        "fix_config.sh",
        "reset.sh",
        "update.sh",
        "redeploy.sh",
        "quick_update.sh",
        "test_qb_connection.sh",
        "diagnose.sh",
        "package_for_deployment.py",
        "deploy_to_remote.py",
        "git_deploy.py"
    ]
    
    removed_count = 0
    
    # 删除文件
    for pattern in files_to_remove:
        for file_path in Path(".").glob(pattern):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    print(f"[DELETE] 删除: {file_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"[ERROR] 删除失败 {file_path}: {e}")
    
    print(f"[SUCCESS] 清理完成，删除了 {removed_count} 个文件")
    
    # 创建 .gitignore
    create_gitignore()
    
    # 创建项目结构说明
    create_project_structure()

def create_gitignore():
    """创建 .gitignore 文件"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
*.bak
*.backup

# Test files
test_*.py
debug_*.py
check_*.py
analyze_*.py
simple_*.py
comprehensive_*.py
final_*.py
simulation_*.py
verify_*.py
explain_*.py
service_mapping_*.py
service_matching_*.py
remote_*.py
ssh_*.py
diagnose_*.py

# API responses
lucky_api_response.json

# Deployment temp
deployment_temp/
*.zip

# OS
.DS_Store
Thumbs.db
"""
    
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    
    print("[SUCCESS] 创建 .gitignore 文件")

def create_project_structure():
    """创建项目结构说明"""
    structure_content = """# qbit-smart-controller 项目结构

## 📁 核心目录
- `app/` - 主应用程序代码
- `config/` - 配置文件
- `data/` - 数据文件（日志、服务控制状态等）

## 📄 核心文件
- `app/main.py` - 主应用程序（FastAPI应用）
- `requirements.txt` - Python依赖
- `Dockerfile` - Docker镜像构建文件
- `docker-compose.yml` - Docker Compose配置
- `version.py` - 版本信息

## 🚀 部署脚本
- `deploy.sh` - 标准部署脚本
- `deploy_docker_cmd.sh` - Docker命令部署
- `deploy_custom_path.sh` - 自定义路径部署
- `package_for_deployment.py` - 创建部署包
- `deploy_to_remote.py` - 远程部署脚本
- `git_deploy.py` - Git部署脚本

## ⚙️ 配置管理
- `init_config.sh` - 初始化配置
- `fix_config.sh` - 修复配置
- `reset.sh` - 重置应用
- `update.sh` - 更新应用

## 📚 文档
- `README.md` - 项目说明
- `MANUAL.md` - 使用手册
- `FAQ.md` - 常见问题
- `CUSTOM_PATH_DEPLOYMENT.md` - 自定义部署说明

## 🔧 工具脚本
- `test_qb_connection.sh` - 测试qBittorrent连接
- `diagnose.sh` - 诊断脚本
- `quick_update.sh` - 快速更新
- `redeploy.sh` - 重新部署
"""
    
    with open("PROJECT_STRUCTURE.md", "w", encoding="utf-8") as f:
        f.write(structure_content)
    
    print("[SUCCESS] 创建项目结构说明")

if __name__ == "__main__":
    cleanup_project()
