#!/usr/bin/env python3
"""
Git部署脚本 - 通过Git同步代码到远程服务器
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description=""):
    """运行命令并显示结果"""
    if description:
        print(f"🔧 {description}")
    
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 成功")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ 失败")
        if result.stderr:
            print(result.stderr)
        return False
    
    return True

def git_deploy():
    """通过Git部署"""
    print("🚀 开始Git部署...")
    
    remote_host = "192.168.2.9"
    remote_user = "root"
    remote_path = "/root/qbit-smart-controller"
    
    # 1. 提交本地更改
    print("\n📝 步骤1: 提交本地更改")
    if not run_command("git add .", "添加文件到Git"):
        return False
    
    if not run_command('git commit -m "Update: 重构代码并修复服务控制逻辑"', "提交更改"):
        print("⚠️ 没有新的更改需要提交")
    
    # 2. 推送到远程仓库
    print("\n📤 步骤2: 推送到远程仓库")
    if not run_command("git push origin main", "推送到远程仓库"):
        return False
    
    # 3. 在远程服务器上拉取并部署
    print("\n🚀 步骤3: 远程拉取并部署")
    remote_commands = f"""
    cd {remote_path} &&
    git pull origin main &&
    docker stop qbit-smart-controller 2>/dev/null || true &&
    docker rm qbit-smart-controller 2>/dev/null || true &&
    docker build -t qbit-smart-controller:latest . &&
    docker run -d \\
        --name qbit-smart-controller \\
        --restart unless-stopped \\
        -p 5000:5000 \\
        -v $(pwd)/config:/app/config \\
        -v $(pwd)/data:/app/data \\
        qbit-smart-controller:latest
    """
    
    ssh_cmd = f'ssh {remote_user}@{remote_host} "{remote_commands}"'
    if not run_command(ssh_cmd, "执行远程部署"):
        return False
    
    # 4. 验证部署
    print("\n🔍 步骤4: 验证部署")
    verify_cmd = f'ssh {remote_user}@{remote_host} "curl -f http://localhost:5000/api/controller/state"'
    if run_command(verify_cmd, "验证服务状态"):
        print("🎉 Git部署成功！")
        print(f"🌐 Web界面: http://{remote_host}:5000")
    else:
        print("⚠️ 部署可能有问题，请检查远程服务器日志")

def setup_git_remote():
    """设置Git远程仓库"""
    print("🔧 设置Git远程仓库...")
    
    # 检查是否已有远程仓库
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if "origin" in result.stdout:
        print("✅ 远程仓库已存在")
        return True
    
    # 创建新的Git仓库
    if not run_command("git init", "初始化Git仓库"):
        return False
    
    # 添加所有文件
    if not run_command("git add .", "添加文件"):
        return False
    
    # 初始提交
    if not run_command('git commit -m "Initial commit: qbit-smart-controller"', "初始提交"):
        return False
    
    print("✅ Git仓库设置完成")
    print("💡 请手动添加远程仓库:")
    print("   git remote add origin <your-repo-url>")
    print("   git push -u origin main")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_git_remote()
    else:
        git_deploy()
