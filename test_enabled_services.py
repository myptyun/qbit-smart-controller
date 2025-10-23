#!/usr/bin/env python3
"""
测试启用服务的情况
"""

import json
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
                print(f"Loaded {len(persisted_state)} service control states")
            else:
                print("Service control file does not exist")
        except Exception as e:
            print(f"Failed to load service control state: {e}")
    
    def _save_persisted_service_control(self):
        """保存服务控制状态到文件"""
        try:
            self.service_control_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.service_control_file, 'w', encoding='utf-8') as f:
                json.dump(self._service_control_state, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save service control state: {e}")
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

def test_enabled_services():
    """测试启用服务的情况"""
    print("Testing enabled services scenario...")
    
    # 初始化配置管理器
    config_manager = SimpleConfigManager()
    
    # 启用所有服务
    print("\nEnabling all services...")
    config_manager.set_service_control_status("Proxmox", True)
    config_manager.set_service_control_status("hzun", True)
    config_manager.set_service_control_status("hzik", True)
    
    # 检查状态
    print("\nCurrent service control status:")
    service_control = config_manager.get_all_service_control_status()
    for service_key, enabled in service_control.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"  {service_key}: {status}")
    
    # 模拟服务连接数据
    print("\nMock service connection data:")
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
        status = "ENABLED" if is_enabled else "DISABLED"
        print(f"  {service_key}: {conn['connections']} connections, control status: {status}")
    
    # 测试连接数计算逻辑
    print("\nTesting connection calculation logic:")
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
            print(f"  [INCLUDED] {service_name}: {connections} connections")
        else:
            print(f"  [EXCLUDED] {service_name}: {conn.get('connections', 0)} connections")
    
    print(f"\nTotal connections calculated: {total_connections}")
    
    # 现在禁用一个服务
    print("\nDisabling Proxmox service...")
    config_manager.set_service_control_status("Proxmox", False)
    
    # 重新计算
    print("\nRecalculating after disabling Proxmox:")
    total_connections_after = 0.0
    
    for conn in mock_detailed_connections:
        service_key = conn.get("rule_name", "")
        service_key_alt = conn.get("key", "")
        service_name = service_key or service_key_alt
        
        is_service_enabled = config_manager.get_service_control_status(service_key or service_key_alt)
        
        if is_service_enabled:
            connections = conn.get("connections", 0)
            total_connections_after += connections
            print(f"  [INCLUDED] {service_name}: {connections} connections")
        else:
            print(f"  [EXCLUDED] {service_name}: {conn.get('connections', 0)} connections")
    
    print(f"\nTotal connections after disabling Proxmox: {total_connections_after}")
    print(f"Connection change: {total_connections} -> {total_connections_after} (reduced by {total_connections - total_connections_after})")
    
    return total_connections, total_connections_after

def main():
    """主函数"""
    print("Enabled Services Test")
    print("=" * 40)
    
    # 运行测试
    total_before, total_after = test_enabled_services()
    
    print("\n" + "=" * 40)
    print("Test Results Summary:")
    print(f"  Total connections before: {total_before}")
    print(f"  Total connections after: {total_after}")
    print(f"  Connections reduced: {total_before - total_after}")
    
    if total_before > total_after:
        print("  SUCCESS: Service control logic works correctly!")
        print("  - Enabled services are properly included")
        print("  - Disabled services are properly excluded")
    else:
        print("  ISSUE: Service control logic may have problems")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()

