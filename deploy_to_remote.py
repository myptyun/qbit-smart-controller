#!/usr/bin/env python3
"""
SSH远程部署脚本
"""
import os
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

def deploy_to_remote():
    """部署到远程服务器"""
    print("🚀 开始远程部署...")
    
    # 远程服务器信息
    remote_host = "192.168.2.9"
    remote_user = "root"
    remote_path = "/root/qbit-smart-controller"
    
    print(f"目标服务器: {remote_user}@{remote_host}")
    print(f"部署路径: {remote_path}")
    
    # 1. 创建部署包
    print("\n📦 步骤1: 创建部署包")
    if not run_command("python package_for_deployment.py", "创建部署包"):
        return False
    
    # 获取最新的部署包文件名
    zip_files = list(Path(".").glob("qbit-smart-controller-*.zip"))
    if not zip_files:
        print("❌ 未找到部署包")
        return False
    
    latest_zip = max(zip_files, key=lambda x: x.stat().st_mtime)
    print(f"📦 部署包: {latest_zip}")
    
    # 2. 上传到远程服务器
    print(f"\n📤 步骤2: 上传到远程服务器")
    upload_cmd = f"scp {latest_zip} {remote_user}@{remote_host}:/tmp/"
    if not run_command(upload_cmd, "上传部署包"):
        return False
    
    # 3. 在远程服务器上部署
    print(f"\n🚀 步骤3: 远程部署")
    remote_commands = f"""
    cd /tmp &&
    unzip -o {latest_zip.name} &&
    cd qbit-smart-controller-* &&
    chmod +x deploy_remote.sh &&
    ./deploy_remote.sh
    """
    
    ssh_cmd = f'ssh {remote_user}@{remote_host} "{remote_commands}"'
    if not run_command(ssh_cmd, "执行远程部署"):
        return False
    
    # 4. 验证部署
    print(f"\n🔍 步骤4: 验证部署")
    verify_cmd = f'ssh {remote_user}@{remote_host} "curl -f http://localhost:5000/api/controller/state"'
    if run_command(verify_cmd, "验证服务状态"):
        print("🎉 部署成功！")
        print(f"🌐 Web界面: http://{remote_host}:5000")
    else:
        print("⚠️ 部署可能有问题，请检查远程服务器日志")
    
    # 5. 清理
    print(f"\n🧹 步骤5: 清理临时文件")
    cleanup_cmd = f'ssh {remote_user}@{remote_host} "rm -f /tmp/{latest_zip.name}"'
    run_command(cleanup_cmd, "清理远程临时文件")
    
    # 删除本地部署包
    latest_zip.unlink()
    print("✅ 清理完成")

def quick_update():
    """快速更新（不重新打包）"""
    print("🔄 开始快速更新...")
    
    remote_host = "192.168.2.9"
    remote_user = "root"
    
    # 直接上传关键文件
    files_to_upload = [
        "app/main.py",
        "requirements.txt",
        "Dockerfile"
    ]
    
    for file_path in files_to_upload:
        if Path(file_path).exists():
            upload_cmd = f"scp {file_path} {remote_user}@{remote_host}:/root/qbit-smart-controller/"
            run_command(upload_cmd, f"上传 {file_path}")
    
    # 在远程服务器上快速更新
    update_commands = """
    cd /root/qbit-smart-controller &&
    docker stop qbit-smart-controller &&
    docker build -t qbit-smart-controller:latest . &&
    docker start qbit-smart-controller
    """
    
    ssh_cmd = f'ssh {remote_user}@{remote_host} "{update_commands}"'
    if run_command(ssh_cmd, "执行快速更新"):
        print("✅ 快速更新完成！")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_update()
    else:
        deploy_to_remote()
