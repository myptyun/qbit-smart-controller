#!/usr/bin/env python3
"""
测试服务状态控制功能
验证禁用状态的服务是否仍被计入总连接数
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.main import ConfigManager, LuckyMonitor, SpeedController, QBittorrentManager

async def test_service_control_logic():
    """测试服务控制逻辑"""
    print("🧪 开始测试服务状态控制逻辑...")
    
    # 初始化管理器
    config_manager = ConfigManager()
    lucky_monitor = LuckyMonitor(config_manager)
    qbit_manager = QBittorrentManager(config_manager)
    speed_controller = SpeedController(config_manager, lucky_monitor, qbit_manager)
    
    # 1. 检查当前服务控制状态
    print("\n📋 当前服务控制状态:")
    service_control = config_manager.get_all_service_control_status()
    for service_key, enabled in service_control.items():
        status = "✅ 启用" if enabled else "❌ 禁用"
        print(f"  {service_key}: {status}")
    
    # 2. 模拟一些服务数据
    print("\n🔍 模拟服务连接数据:")
    mock_detailed_connections = [
        {
            "rule_name": "Proxmox",
            "key": "Proxmox", 
            "connections": 5,
            "service_type": "proxy",
            "enabled": True
        },
        {
            "rule_name": "hzun",
            "key": "hzun",
            "connections": 3,
            "service_type": "proxy", 
            "enabled": True
        },
        {
            "rule_name": "hzik",
            "key": "hzik",
            "connections": 2,
            "service_type": "proxy",
            "enabled": True
        }
    ]
    
    # 显示模拟数据
    for conn in mock_detailed_connections:
        service_key = conn.get("rule_name", "")
        is_enabled = config_manager.get_service_control_status(service_key)
        status = "✅ 启用" if is_enabled else "❌ 禁用"
        print(f"  {service_key}: {conn['connections']} 个连接, 控制状态: {status}")
    
    # 3. 测试连接数计算逻辑
    print("\n🧮 测试连接数计算逻辑:")
    total_connections = 0.0
    
    for conn in mock_detailed_connections:
        service_key = conn.get("rule_name", "")
        service_key_alt = conn.get("key", "")
        service_name = service_key or service_key_alt
        
        # 使用动态服务控制状态
        is_service_enabled = config_manager.get_service_control_status(service_key or service_key_alt)
        
        if is_service_enabled:
            connections = conn.get("connections", 0)
            total_connections += connections
            print(f"  ✅ {service_name}: {connections} 个连接 (已计入总数)")
        else:
            print(f"  ❌ {service_name}: {conn.get('connections', 0)} 个连接 (已忽略)")
    
    print(f"\n📊 总连接数计算结果: {total_connections}")
    
    # 4. 测试设置服务控制状态
    print("\n🔧 测试设置服务控制状态:")
    
    # 禁用 Proxmox 服务
    print("  禁用 Proxmox 服务...")
    config_manager.set_service_control_status("Proxmox", False)
    
    # 重新计算连接数
    print("\n🧮 重新计算连接数 (Proxmox 已禁用):")
    total_connections_after = 0.0
    
    for conn in mock_detailed_connections:
        service_key = conn.get("rule_name", "")
        service_key_alt = conn.get("key", "")
        service_name = service_key or service_key_alt
        
        is_service_enabled = config_manager.get_service_control_status(service_key or service_key_alt)
        
        if is_service_enabled:
            connections = conn.get("connections", 0)
            total_connections_after += connections
            print(f"  ✅ {service_name}: {connections} 个连接 (已计入总数)")
        else:
            print(f"  ❌ {service_name}: {conn.get('connections', 0)} 个连接 (已忽略)")
    
    print(f"\n📊 禁用后总连接数: {total_connections_after}")
    print(f"📊 连接数变化: {total_connections} -> {total_connections_after} (减少 {total_connections - total_connections_after})")
    
    # 5. 验证服务控制状态持久化
    print("\n💾 验证服务控制状态持久化:")
    current_state = config_manager.get_all_service_control_status()
    print("  当前内存状态:")
    for service_key, enabled in current_state.items():
        status = "✅ 启用" if enabled else "❌ 禁用"
        print(f"    {service_key}: {status}")
    
    # 检查文件状态
    service_control_file = Path("data/config/service_control.json")
    if service_control_file.exists():
        with open(service_control_file, 'r', encoding='utf-8') as f:
            file_state = json.load(f)
        print("  文件保存状态:")
        for service_key, enabled in file_state.items():
            status = "✅ 启用" if enabled else "❌ 禁用"
            print(f"    {service_key}: {status}")
    else:
        print("  ⚠️ 服务控制文件不存在")
    
    # 6. 测试新服务发现逻辑
    print("\n🆕 测试新服务发现逻辑:")
    new_services = [
        {"rule_name": "NewService1", "key": "NewService1", "connections": 1},
        {"rule_name": "NewService2", "key": "NewService2", "connections": 2}
    ]
    
    discovered = config_manager.discover_and_initialize_services(new_services)
    print(f"  发现新服务: {discovered}")
    
    # 检查新服务的默认状态
    for service in new_services:
        service_key = service.get("rule_name", "")
        is_enabled = config_manager.get_service_control_status(service_key)
        status = "✅ 启用" if is_enabled else "❌ 禁用"
        print(f"    {service_key}: {status} (默认状态)")
    
    print("\n✅ 服务状态控制测试完成!")
    
    # 清理资源
    await lucky_monitor.close()
    await qbit_manager.close()

async def test_real_api_calls():
    """测试真实的API调用"""
    print("\n🌐 测试真实API调用...")
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # 检查是否有配置的Lucky设备
    lucky_devices = config.get("lucky_devices", [])
    if not lucky_devices:
        print("  ⚠️ 没有配置Lucky设备，跳过真实API测试")
        return
    
    lucky_monitor = LuckyMonitor(config_manager)
    
    try:
        for device in lucky_devices:
            if not device.get("enabled", True):
                print(f"  ⏭️ 跳过禁用的设备: {device['name']}")
                continue
                
            print(f"  🔍 测试设备: {device['name']}")
            result = await lucky_monitor.get_device_connections(device)
            
            if result.get("success"):
                detailed_connections = result.get("detailed_connections", [])
                print(f"    📊 获取到 {len(detailed_connections)} 个服务")
                
                # 分析每个服务的控制状态
                for conn in detailed_connections:
                    service_key = conn.get("rule_name", "")
                    service_key_alt = conn.get("key", "")
                    service_name = service_key or service_key_alt
                    
                    is_enabled = config_manager.get_service_control_status(service_key or service_key_alt)
                    connections = conn.get("connections", 0)
                    
                    status = "✅ 启用" if is_enabled else "❌ 禁用"
                    print(f"      {service_name}: {connections} 个连接, 控制状态: {status}")
            else:
                print(f"    ❌ 设备连接失败: {result.get('error', '未知错误')}")
                
    except Exception as e:
        print(f"  ❌ API测试异常: {e}")
    finally:
        await lucky_monitor.close()

def main():
    """主函数"""
    print("🚀 服务状态控制测试工具")
    print("=" * 50)
    
    # 运行测试
    asyncio.run(test_service_control_logic())
    asyncio.run(test_real_api_calls())
    
    print("\n" + "=" * 50)
    print("✅ 所有测试完成!")

if __name__ == "__main__":
    main()
