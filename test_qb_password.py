#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试 qBittorrent 用户名和密码
在修改配置前先验证密码是否正确
"""

import requests
import sys
import os

# 设置 UTF-8 编码输出（Windows 兼容）
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# 禁用代理（避免代理干扰本地网络连接）
session = requests.Session()
session.trust_env = False  # 不使用环境变量中的代理设置

def test_qbit_login(host, username, password):
    """测试 qBittorrent 登录"""
    print("=" * 60)
    print("qBittorrent 登录测试")
    print("=" * 60)
    
    # 测试基本连接
    print(f"\n[1/3] 测试基本连接...")
    print(f"   URL: {host}")
    
    try:
        response = session.get(host, timeout=5)
        print(f"   [OK] 连接成功: HTTP {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] 连接失败: {e}")
        return False
    
    # 测试版本 API（不需要认证）
    print(f"\n[2/3] 测试版本 API...")
    version_url = f"{host}/api/v2/app/version"
    print(f"   URL: {version_url}")
    
    try:
        response = session.get(version_url, timeout=5)
        if response.status_code == 200:
            version = response.text.strip()
            print(f"   [OK] qBittorrent 版本: {version}")
        else:
            print(f"   [WARN] 状态码: {response.status_code}")
    except Exception as e:
        print(f"   [WARN] 无法获取版本: {e}")
    
    # 测试登录
    print(f"\n[3/3] 测试登录认证...")
    login_url = f"{host}/api/v2/auth/login"
    print(f"   URL: {login_url}")
    print(f"   用户名: {username}")
    print(f"   密码: {'*' * len(password)}")
    
    try:
        login_data = {
            'username': username,
            'password': password
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = session.post(
            login_url,
            data=login_data,
            headers=headers,
            timeout=5
        )
        
        result = response.text.strip()
        print(f"   响应: {result}")
        print(f"   状态码: {response.status_code}")
        
        # 检查 Cookie
        cookies = response.cookies
        print(f"   收到的 Cookie: {len(cookies)} 个")
        
        for cookie in cookies:
            print(f"      - {cookie.name} = {cookie.value[:20]}...")
        
        # 判断结果
        print("\n" + "=" * 60)
        if result == "Ok.":
            print("[SUCCESS] 登录成功！用户名和密码正确")
            print("=" * 60)
            print("\n你可以在 config/config.yaml 中使用这些凭据:")
            print(f"""
qbittorrent_instances:
  - name: "我的QB实例"
    host: "{host}"
    username: "{username}"
    password: "{password}"
    enabled: true
""")
            return True
        elif result == "Fails.":
            print("[FAIL] 登录失败！用户名或密码错误")
            print("=" * 60)
            print("\n请检查:")
            print("1. 在 qBittorrent Web UI 中确认用户名和密码")
            print("   路径: 工具 -> 选项 -> Web UI")
            print("2. 确保没有输入错误（注意大小写）")
            print("3. 尝试重新设置密码")
            return False
        else:
            print(f"[WARN] 意外的响应: {result}")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"   [FAIL] 请求失败: {e}")
        return False

def main():
    """主函数"""
    print("\nqBittorrent 密码验证工具\n")
    
    # 从命令行参数或交互式输入获取信息
    if len(sys.argv) == 4:
        host = sys.argv[1]
        username = sys.argv[2]
        password = sys.argv[3]
    else:
        print("请输入 qBittorrent 连接信息:\n")
        host = input("主机地址 (如 http://192.168.2.21:8080): ").strip()
        username = input("用户名 (默认 admin): ").strip() or "admin"
        password = input("密码: ").strip()
    
    # 移除末尾的斜杠
    host = host.rstrip('/')
    
    # 执行测试
    success = test_qbit_login(host, username, password)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

