#!/usr/bin/env python3
"""
qBittorrent 简单测试脚本 (使用requests库)
这个脚本更接近curl命令的行为
"""

import requests
import sys

# 配置信息
QB_HOST = "http://192.168.2.21:8080"
QB_USERNAME = "admin"
QB_PASSWORD = "t8766332p"

def test_qb_simple():
    """简单测试qBittorrent连接"""
    print("=" * 60)
    print("qBittorrent 简单连接测试 (requests)")
    print("=" * 60)
    print(f"目标地址: {QB_HOST}")
    print(f"用户名: {QB_USERNAME}")
    print(f"密码: {'*' * len(QB_PASSWORD)}")
    print("=" * 60)
    print()
    
    # 禁用代理
    proxies = {
        'http': None,
        'https': None,
    }
    
    # 测试1: 基本连接
    print("📡 测试1: 基本连接")
    print("-" * 60)
    try:
        response = requests.get(QB_HOST, timeout=10, proxies=proxies)
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 服务器可访问")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    print()
    
    # 测试2: 登录
    print("📡 测试2: 登录测试")
    print("-" * 60)
    try:
        login_url = f"{QB_HOST}/api/v2/auth/login"
        print(f"🔑 登录URL: {login_url}")
        
        # 方式1: 使用data参数（字典）
        login_data = {
            "username": QB_USERNAME,
            "password": QB_PASSWORD
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        print(f"🔑 请求头: {headers}")
        print(f"🔑 请求数据: username={QB_USERNAME}&password={'*' * len(QB_PASSWORD)}")
        print()
        
        # 发送登录请求
        session = requests.Session()
        response = session.post(
            login_url, 
            data=login_data, 
            headers=headers,
            proxies=proxies,
            timeout=10
        )
        
        print(f"📥 响应状态: {response.status_code}")
        print(f"📥 响应内容: {response.text}")
        print(f"📥 响应头: {dict(response.headers)}")
        print(f"🍪 Session Cookies: {dict(session.cookies)}")
        print(f"🍪 Response Cookies: {dict(response.cookies)}")
        print()
        
        if response.status_code == 200:
            # 检查Cookie
            if 'SID' in session.cookies:
                sid = session.cookies.get('SID')
                print(f"✅ 登录成功！获取到 SID: {sid}")
                
                # 测试3: 使用Cookie访问API
                print()
                print("📡 测试3: 使用Cookie访问传输信息")
                print("-" * 60)
                transfer_url = f"{QB_HOST}/api/v2/transfer/info"
                transfer_response = session.get(transfer_url, proxies=proxies, timeout=10)
                
                print(f"📥 传输信息状态: {transfer_response.status_code}")
                print(f"📥 传输信息内容: {transfer_response.text[:200]}")
                
                if transfer_response.status_code == 200:
                    print(f"✅ API访问成功！")
                    print()
                    print("=" * 60)
                    print("✅ 所有测试通过！qBittorrent连接正常")
                    print("=" * 60)
                    return True
                else:
                    print(f"❌ API访问失败")
                    return False
            else:
                print(f"⚠️ 登录返回200但未获取到SID Cookie")
                print(f"⚠️ 可能的原因：")
                print(f"   1. qBittorrent的Web UI设置问题")
                print(f"   2. 用户名或密码错误")
                print(f"   3. qBittorrent版本问题")
                return False
        else:
            print(f"❌ 登录失败，状态码: {response.status_code}")
            if response.status_code == 401:
                print(f"⚠️ 401错误：用户名或密码错误")
            elif response.status_code == 403:
                print(f"⚠️ 403错误：访问被禁止，可能是IP白名单限制")
            return False
            
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "🔧 " * 20)
    print("qBittorrent 独立连接测试工具 (requests)")
    print("🔧 " * 20 + "\n")
    
    try:
        result = test_qb_simple()
        if result:
            sys.exit(0)
        else:
            print()
            print("=" * 60)
            print("❌ 测试失败")
            print("=" * 60)
            print()
            print("💡 建议检查项：")
            print("   1. qBittorrent是否运行在 http://192.168.2.21:8080")
            print("   2. 用户名密码是否正确 (admin / t8766332p)")
            print("   3. qBittorrent Web UI设置 > 启用Web用户界面")
            print("   4. qBittorrent Web UI设置 > 绕过本地主机身份验证 (如果勾选)")
            print("   5. qBittorrent Web UI设置 > IP白名单设置")
            print()
            print("💡 可以在qBittorrent机器上手动测试：")
            print(f'   curl -i -X POST -d "username={QB_USERNAME}&password={QB_PASSWORD}" {QB_HOST}/api/v2/auth/login')
            print()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)

