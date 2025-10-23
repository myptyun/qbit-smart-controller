#!/usr/bin/env python3
"""
简化的服务状态控制测试
不依赖完整应用启动，直接测试核心逻辑
"""

import json
import os
from pathlib import Path

class SimpleConfigManager:
    """简化的配置管理器，用于测试"""
    def __init__(self):
        self.service_control_file = Path("data/config/service_control.json")
        # 动态服务控制状态 - 内存存储
        self._service_control_state = {}
        self._load_persisted_service_control()
    
    def _load_persisted_service_control(self):
        """加载持久化的服务控制状态"""
        try:
            if self.service_control_file.exists():
                with open(self.service_control_file, 'r', encoding='utf-8') as f:
                    persisted_state = json.load(f)
                self._service_control_state.update(persisted_state)
                print(f"✅ 加载了 {len(persisted_state)} 个已保存的服务控制状态")
            else:
                print("📝 服务控制文件不存在，使用空状态")
        except Exception as e:
            print(f"❌ 加载服务控制状态失败: {e}")
    
    def _save_persisted_service_control(self):
        """保存服务控制状态到文件"""
        try:
            self.service_control_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.service_control_file, 'w', encoding='utf-8') as f:
                json.dump(self._service_control_state, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 保存服务控制状态失败: {e}")
            return False
    
    def get_service_control_status(self, service_key: str) -> bool:
        """获取服务控制状态 - 动态处理"""
        # 如果服务在内存状态中，使用保存的状态
        if service_key in self._service_control_state:
            return self._service_control_state[service_key]
        # 新服务默认禁用（避免意外触发限速）
        return False
    
    def set_service_control_status(self, service_key: str, enabled: bool):
        """设置服务控制状态 - 动态处理"""
        # 更新内存状态
        self._service_control_state[service_key] = enabled
        # 持久化到文件
        return self._save_persisted_service_control()
    
    def get_all_service_control_status(self):
        """获取所有服务控制状态"""
        return self._service_control_state.copy()
    
    def discover_and_initialize_services(self, detected_services):
        """发现并初始化新服务"""
        new_services = []
        for service in detected_services:
            service_key = service.get("rule_name") or service.get("key", "")
            if service_key and service_key not in self._service_control_state:
                # 新服务默认禁用（避免意外触发限速）
                self._service_control_state[service_key] = False
                new_services.append(service_key)
        
        if new_services:
            print(f"🆕 发现 {len(new_services)} 个新服务: {', '.join(new_services)} (默认禁用)")
            # 保存新发现的服务状态
            self._save_persisted_service_control()
        
        return new_services

def test_connection_calculation_logic():
    """测试连接数计算逻辑"""
    print("🧪 测试连接数计算逻辑...")
    
    # 初始化配置管理器
    config_manager = SimpleConfigManager()
    
    # 1. 检查当前服务控制状态
    print("\n📋 当前服务控制状态:")
    service_control = config_manager.get_all_service_control_status()
    if service_control:
        for service_key, enabled in service_control.items():
            status = "✅ 启用" if enabled else "❌ 禁用"
            print(f"  {service_key}: {status}")
    else:
        print("  没有配置的服务控制状态")
    
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
    
    # 3. 测试连接数计算逻辑（模拟_collect_total_connections方法）
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
    
    return total_connections, total_connections_after

def analyze_current_service_control():
    """分析当前的服务控制状态"""
    print("\n🔍 分析当前服务控制状态...")
    
    service_control_file = Path("data/config/service_control.json")
    if not service_control_file.exists():
        print("  ⚠️ 服务控制文件不存在")
        return
    
    with open(service_control_file, 'r', encoding='utf-8') as f:
        service_control = json.load(f)
    
    print(f"  📄 服务控制文件: {service_control_file}")
    print(f"  📊 配置的服务数量: {len(service_control)}")
    
    enabled_count = sum(1 for enabled in service_control.values() if enabled)
    disabled_count = len(service_control) - enabled_count
    
    print(f"  ✅ 启用的服务: {enabled_count}")
    print(f"  ❌ 禁用的服务: {disabled_count}")
    
    print("\n  详细状态:")
    for service_key, enabled in service_control.items():
        status = "✅ 启用" if enabled else "❌ 禁用"
        print(f"    {service_key}: {status}")

def main():
    """主函数"""
    print("服务状态控制测试工具 (简化版)")
    print("=" * 60)
    
    # 分析当前状态
    analyze_current_service_control()
    
    # 运行测试
    total_before, total_after = test_connection_calculation_logic()
    
    print("\n" + "=" * 60)
    print("📋 测试结果总结:")
    print(f"  • 禁用前总连接数: {total_before}")
    print(f"  • 禁用后总连接数: {total_after}")
    print(f"  • 连接数减少: {total_before - total_after}")
    
    if total_before > total_after:
        print("  ✅ 服务控制逻辑工作正常 - 禁用状态的服务被正确排除")
    else:
        print("  ❌ 服务控制逻辑可能有问题 - 禁用状态的服务仍被计入")
    
    print("\n✅ 测试完成!")

if __name__ == "__main__":
    main()
