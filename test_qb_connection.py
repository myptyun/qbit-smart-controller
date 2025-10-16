#!/usr/bin/env python3
"""
qBittorrent 连接测试脚本
用于诊断登录和Cookie问题
"""

import aiohttp
import asyncio
import sys

# 配置信息
QB_HOST = "http://192.168.2.21:8080"
QB_USERNAME = "admin"
QB_PASSWORD = "t8766332p"

async def test_qb_connection():
    """测试qBittorrent连接"""
    print("=" * 60)
    print("qBittorrent 连接测试")
    print("=" * 60)
    print(f"目标地址: {QB_HOST}")
    print(f"用户名: {QB_USERNAME}")
    print(f"密码: {'*' * len(QB_PASSWORD)}")
    print("=" * 60)
    print()
    
    # 创建会话（禁用代理）
    timeout = aiohttp.ClientTimeout(total=15, connect=5, sock_read=10)
    connector = aiohttp.TCPConnector(verify_ssl=False)
    
    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        trust_env=False  # 禁用代理
    ) as session:
        
        # 测试1: 基本连接
        print("📡 测试1: 基本连接")
        print("-" * 60)
        try:
            async with session.get(QB_HOST, timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"✅ 状态码: {response.status}")
                print(f"✅ 服务器可访问")
                content = await response.text()
                print(f"✅ 响应长度: {len(content)} 字节")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            print(f"❌ 错误类型: {type(e).__name__}")
            return False
        print()
        
        # 测试2: 登录（方法1 - 使用data参数）
        print("📡 测试2: 登录测试 (方法1 - data参数)")
        print("-" * 60)
        try:
            login_url = f"{QB_HOST}/api/v2/auth/login"
            print(f"🔑 登录URL: {login_url}")
            
            login_data = {
                "username": QB_USERNAME,
                "password": QB_PASSWORD
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            print(f"🔑 请求头: {headers}")
            print(f"🔑 请求数据: username={QB_USERNAME}&password={'*' * len(QB_PASSWORD)}")
            
            async with session.post(login_url, data=login_data, headers=headers) as response:
                status = response.status
                content = await response.text()
                cookies = response.cookies
                response_headers = dict(response.headers)
                
                print(f"📥 响应状态: {status}")
                print(f"📥 响应内容: {content}")
                print(f"📥 响应头: {response_headers}")
                print(f"🍪 Cookie数量: {len(cookies)}")
                
                for cookie in cookies:
                    print(f"🍪 Cookie: {cookie.key} = {cookie.value}")
                
                if status == 200:
                    sid_cookie = cookies.get('SID')
                    if sid_cookie:
                        print(f"✅ 登录成功！获取到 SID: {sid_cookie.value}")
                        
                        # 测试3: 使用Cookie访问API
                        print()
                        print("📡 测试3: 使用Cookie访问传输信息")
                        print("-" * 60)
                        transfer_url = f"{QB_HOST}/api/v2/transfer/info"
                        async with session.get(transfer_url, cookies=cookies) as transfer_response:
                            transfer_status = transfer_response.status
                            transfer_content = await transfer_response.text()
                            print(f"📥 传输信息状态: {transfer_status}")
                            print(f"📥 传输信息内容: {transfer_content[:200]}")
                            
                            if transfer_status == 200:
                                print(f"✅ API访问成功！")
                                return True
                            else:
                                print(f"❌ API访问失败")
                                return False
                    else:
                        print(f"⚠️ 登录返回200但未获取到SID Cookie")
                        print(f"⚠️ 检查Set-Cookie头...")
                        set_cookie = response_headers.get('Set-Cookie', '')
                        print(f"🍪 Set-Cookie头: {set_cookie}")
                        return False
                else:
                    print(f"❌ 登录失败，状态码: {status}")
                    return False
                    
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            print(f"❌ 错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
        print()
        
        # 测试4: 登录（方法2 - 手动构建表单字符串）
        print("📡 测试4: 登录测试 (方法2 - 手动构建表单)")
        print("-" * 60)
        try:
            login_url = f"{QB_HOST}/api/v2/auth/login"
            
            # 手动构建表单字符串
            form_data = f"username={QB_USERNAME}&password={QB_PASSWORD}"
            
            headers2 = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': str(len(form_data))
            }
            
            print(f"🔑 登录URL: {login_url}")
            print(f"🔑 请求头: {headers2}")
            print(f"🔑 请求体: {form_data.replace(QB_PASSWORD, '*' * len(QB_PASSWORD))}")
            
            async with session.post(login_url, data=form_data, headers=headers2) as response:
                status = response.status
                content = await response.text()
                cookies = response.cookies
                
                print(f"📥 响应状态: {status}")
                print(f"📥 响应内容: {content}")
                print(f"🍪 Cookie数量: {len(cookies)}")
                
                for cookie in cookies:
                    print(f"🍪 Cookie: {cookie.key} = {cookie.value}")
                
                if status == 200:
                    sid_cookie = cookies.get('SID')
                    if sid_cookie:
                        print(f"✅ 登录成功！获取到 SID: {sid_cookie.value}")
                        return True
                    else:
                        print(f"⚠️ 登录返回200但未获取到SID Cookie")
                        return False
                else:
                    print(f"❌ 登录失败，状态码: {status}")
                    return False
                    
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """主函数"""
    try:
        result = await test_qb_connection()
        print()
        print("=" * 60)
        if result:
            print("✅ 所有测试通过！qBittorrent连接正常")
            sys.exit(0)
        else:
            print("❌ 测试失败，请检查上面的错误信息")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("\n" + "🔧 " * 20)
    print("qBittorrent 独立连接测试工具")
    print("🔧 " * 20 + "\n")
    
    asyncio.run(main())

