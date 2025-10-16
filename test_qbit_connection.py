#!/usr/bin/env python3
"""
测试 qBittorrent 连接脚本
用于验证 Cookie 认证机制是否正常工作
"""

import asyncio
import aiohttp
import json

async def test_qbit_connection():
    """测试 qBittorrent 连接"""
    
    # 你的 qBittorrent 配置
    qbit_config = {
        "host": "http://192.168.2.21:8080",
        "username": "admin", 
        "password": "t8766332p"
    }
    
    print(f"🔍 测试 qBittorrent 连接: {qbit_config['host']}")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 步骤1: 登录获取 Cookie
            print("\n📝 步骤1: 登录获取 Cookie")
            login_data = {
                "username": qbit_config["username"],
                "password": qbit_config["password"]
            }
            
            login_url = f"{qbit_config['host']}/api/v2/auth/login"
            print(f"🔑 登录URL: {login_url}")
            
            async with session.post(login_url, data=login_data) as response:
                login_content = await response.text()
                cookies = response.cookies
                
                print(f"🔑 登录响应: HTTP {response.status}")
                print(f"🔑 响应内容: {login_content}")
                print(f"🍪 收到Cookie数量: {len(cookies)}")
                
                for cookie in cookies:
                    print(f"🍪 Cookie: {cookie.key} = {cookie.value[:20]}...")
                
                if response.status == 200:
                    print("✅ 登录成功！")
                    
                    # 步骤2: 使用 Cookie 测试传输信息
                    print("\n📊 步骤2: 测试传输信息")
                    transfer_url = f"{qbit_config['host']}/api/v2/transfer/info"
                    
                    async with session.get(transfer_url, cookies=cookies) as transfer_response:
                        transfer_content = await transfer_response.text()
                        
                        print(f"📊 传输信息响应: HTTP {transfer_response.status}")
                        
                        if transfer_response.status == 200:
                            try:
                                transfer_data = json.loads(transfer_content)
                                print("✅ 传输信息获取成功！")
                                print(f"📥 下载速度: {transfer_data.get('dl_info_speed', 0)} B/s")
                                print(f"📤 上传速度: {transfer_data.get('up_info_speed', 0)} B/s")
                                print(f"📊 下载数据: {transfer_data.get('dl_info_data', 0)} bytes")
                                print(f"📊 上传数据: {transfer_data.get('up_info_data', 0)} bytes")
                            except json.JSONDecodeError:
                                print(f"❌ JSON解析失败: {transfer_content[:200]}")
                        else:
                            print(f"❌ 传输信息获取失败: {transfer_content}")
                    
                    # 步骤3: 测试种子列表
                    print("\n🌱 步骤3: 测试种子列表")
                    torrents_url = f"{qbit_config['host']}/api/v2/torrents/info"
                    
                    async with session.get(torrents_url, cookies=cookies) as torrents_response:
                        torrents_content = await torrents_response.text()
                        
                        print(f"🌱 种子列表响应: HTTP {torrents_response.status}")
                        
                        if torrents_response.status == 200:
                            try:
                                torrents_data = json.loads(torrents_content)
                                print(f"✅ 种子列表获取成功！共 {len(torrents_data)} 个种子")
                                
                                # 统计状态
                                states = {}
                                for torrent in torrents_data:
                                    state = torrent.get('state', 'unknown')
                                    states[state] = states.get(state, 0) + 1
                                
                                print("📊 种子状态统计:")
                                for state, count in states.items():
                                    print(f"  {state}: {count} 个")
                                    
                            except json.JSONDecodeError:
                                print(f"❌ JSON解析失败: {torrents_content[:200]}")
                        else:
                            print(f"❌ 种子列表获取失败: {torrents_content}")
                    
                    # 步骤4: 测试速度限制设置
                    print("\n🎚️ 步骤4: 测试速度限制设置")
                    
                    # 设置下载限制为 1000 KB/s
                    dl_limit_url = f"{qbit_config['host']}/api/v2/transfer/setDownloadLimit"
                    dl_limit_data = {"limit": 1000 * 1024}  # 1000 KB/s = 1024000 bytes/s
                    
                    async with session.post(dl_limit_url, data=dl_limit_data, cookies=cookies) as dl_response:
                        print(f"🎚️ 下载限制设置: HTTP {dl_response.status}")
                        if dl_response.status == 200:
                            print("✅ 下载限制设置成功")
                        else:
                            print(f"❌ 下载限制设置失败: {await dl_response.text()}")
                    
                    # 设置上传限制为 500 KB/s
                    up_limit_url = f"{qbit_config['host']}/api/v2/transfer/setUploadLimit"
                    up_limit_data = {"limit": 500 * 1024}  # 500 KB/s = 512000 bytes/s
                    
                    async with session.post(up_limit_url, data=up_limit_data, cookies=cookies) as up_response:
                        print(f"🎚️ 上传限制设置: HTTP {up_response.status}")
                        if up_response.status == 200:
                            print("✅ 上传限制设置成功")
                        else:
                            print(f"❌ 上传限制设置失败: {await up_response.text()}")
                    
                else:
                    print(f"❌ 登录失败: {login_content}")
                    
        except Exception as e:
            print(f"❌ 连接异常: {e}")

if __name__ == "__main__":
    print("🚀 开始测试 qBittorrent 连接...")
    asyncio.run(test_qbit_connection())
    print("\n🏁 测试完成！")
