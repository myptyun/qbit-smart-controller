#!/usr/bin/env python3
"""
深度调试服务控制逻辑
"""

import json
import sys
import os
from pathlib import Path

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def debug_config_manager():
    """调试配置管理器"""
    print("=" * 80)
    print("DEBUGGING CONFIG MANAGER")
    print("=" * 80)
    
    # 模拟ConfigManager的核心逻辑
    class DebugConfigManager:
        def __init__(self):
            self._service_control_state = {}
            self._load_persisted_service_control()
        
        def _load_persisted_service_control(self):
            """加载持久化的服务控制状态"""
            service_control_file = Path("data/config/service_control.json")
            if service_control_file.exists():
                with open(service_control_file, 'r', encoding='utf-8') as f:
                    self._service_control_state = json.load(f)
                print(f"[OK] Loaded {len(self._service_control_state)} services from config")
                print("Service control state:")
                for service, enabled in self._service_control_state.items():
                    status = "ENABLED" if enabled else "DISABLED"
                    print(f"  {service}: {status}")
            else:
                print("[ERROR] No service control config found")
        
        def get_service_control_status(self, service_key: str) -> bool:
            """获取服务控制状态 - 详细调试版本"""
            print(f"\n[CHECK] Checking service control status for: '{service_key}'")
            
            # 直接匹配
            if service_key in self._service_control_state:
                status = self._service_control_state[service_key]
                print(f"  [OK] Direct match found: {status}")
                return status
            
            # 大小写不敏感匹配
            service_key_lower = service_key.lower()
            for stored_key, status in self._service_control_state.items():
                if stored_key.lower() == service_key_lower:
                    print(f"  [OK] Case-insensitive match found: '{stored_key}' -> {status}")
                    return status
            
            # 没有匹配
            print(f"  [NO] No match found, defaulting to DISABLED")
            return False
        
        def get_all_service_control_status(self):
            """获取所有服务控制状态"""
            return self._service_control_state.copy()
    
    return DebugConfigManager()

def debug_lucky_api_parsing():
    """调试Lucky API解析逻辑"""
    print("\n" + "=" * 80)
    print("DEBUGGING LUCKY API PARSING")
    print("=" * 80)
    
    # 使用真实的Lucky API数据
    lucky_file = Path("lucky_api_response.json")
    if not lucky_file.exists():
        print("❌ Lucky API response file not found")
        return []
    
    with open(lucky_file, 'r', encoding='utf-8-sig') as f:
        lucky_data = json.load(f)
    
    print("✅ Loaded Lucky API data")
    
    # 模拟_parse_detailed_connections逻辑
    connections_info = []
    
    if "ruleList" in lucky_data and isinstance(lucky_data["ruleList"], list):
        for rule in lucky_data["ruleList"]:
            if "ProxyList" in rule and isinstance(rule["ProxyList"], list):
                for proxy in rule["ProxyList"]:
                    service_key = proxy.get("Key", "")
                    service_remark = proxy.get("Remark", "")
                    connections = proxy.get("Connections", 0)
                    service_type = proxy.get("WebServiceType", "unknown")
                    enabled = proxy.get("Enable", True)
                    
                    # 优先使用Remark字段作为服务名称
                    service_name = service_remark if service_remark else service_key
                    
                    connection_info = {
                        "rule_name": service_name,
                        "key": service_key,
                        "remark": service_remark,
                        "connections": connections,
                        "service_type": service_type,
                        "enabled": enabled,
                        "status": "active" if connections > 0 else "inactive"
                    }
                    
                    connections_info.append(connection_info)
                    
                    print(f"📡 Service: {service_name}")
                    print(f"    Key: {service_key}")
                    print(f"    Remark: {service_remark}")
                    print(f"    Connections: {connections}")
                    print(f"    Type: {service_type}")
                    print(f"    Enabled in Lucky: {enabled}")
                    print()
    
    print(f"✅ Parsed {len(connections_info)} services from Lucky API")
    return connections_info

def debug_connection_calculation(config_manager, connections_info):
    """调试连接数计算逻辑"""
    print("\n" + "=" * 80)
    print("DEBUGGING CONNECTION CALCULATION")
    print("=" * 80)
    
    total_connections = 0.0
    
    for i, conn in enumerate(connections_info):
        print(f"\n🔍 Processing connection {i+1}:")
        print(f"  rule_name: '{conn.get('rule_name', '')}'")
        print(f"  key: '{conn.get('key', '')}'")
        print(f"  remark: '{conn.get('remark', '')}'")
        print(f"  connections: {conn.get('connections', 0)}")
        
        service_name = conn.get("rule_name", "")
        service_key = conn.get("key", "")
        service_remark = conn.get("remark", "")
        
        # 测试服务控制状态查询
        is_service_enabled = False
        matched_name = ""
        
        print(f"\n  🔍 Checking service control status:")
        
        # 优先使用rule_name（通常是Remark字段）
        if service_name:
            print(f"    Checking rule_name: '{service_name}'")
            if config_manager.get_service_control_status(service_name):
                is_service_enabled = True
                matched_name = service_name
                print(f"    ✅ rule_name match: ENABLED")
            else:
                print(f"    ❌ rule_name match: DISABLED")
        
        # 其次尝试key字段
        if not is_service_enabled and service_key:
            print(f"    Checking key: '{service_key}'")
            if config_manager.get_service_control_status(service_key):
                is_service_enabled = True
                matched_name = service_key
                print(f"    ✅ key match: ENABLED")
            else:
                print(f"    ❌ key match: DISABLED")
        
        # 最后尝试remark字段
        if not is_service_enabled and service_remark:
            print(f"    Checking remark: '{service_remark}'")
            if config_manager.get_service_control_status(service_remark):
                is_service_enabled = True
                matched_name = service_remark
                print(f"    ✅ remark match: ENABLED")
            else:
                print(f"    ❌ remark match: DISABLED")
        
        # 计算连接数
        if is_service_enabled:
            total_connections += conn.get("connections", 0)
            print(f"  ✅ [INCLUDED] '{matched_name}': {conn.get('connections', 0)} connections")
        else:
            print(f"  ❌ [EXCLUDED] '{service_name or service_key}': {conn.get('connections', 0)} connections (DISABLED)")
    
    print(f"\n📊 Total connections: {total_connections}")
    return total_connections

def debug_specific_services(config_manager, connections_info):
    """调试特定服务"""
    print("\n" + "=" * 80)
    print("DEBUGGING SPECIFIC SERVICES")
    print("=" * 80)
    
    # 重点检查Proxmox服务
    proxmox_services = []
    for conn in connections_info:
        if "proxmox" in conn.get("rule_name", "").lower() or "proxmox" in conn.get("remark", "").lower():
            proxmox_services.append(conn)
    
    print(f"🔍 Found {len(proxmox_services)} Proxmox-related services:")
    for i, service in enumerate(proxmox_services):
        print(f"\n  Proxmox service {i+1}:")
        print(f"    rule_name: '{service.get('rule_name', '')}'")
        print(f"    key: '{service.get('key', '')}'")
        print(f"    remark: '{service.get('remark', '')}'")
        print(f"    connections: {service.get('connections', 0)}")
        
        # 检查配置中的状态
        service_name = service.get("rule_name", "")
        service_key = service.get("key", "")
        service_remark = service.get("remark", "")
        
        print(f"    Configuration status:")
        if service_name:
            status = config_manager.get_service_control_status(service_name)
            print(f"      rule_name '{service_name}': {'ENABLED' if status else 'DISABLED'}")
        if service_key:
            status = config_manager.get_service_control_status(service_key)
            print(f"      key '{service_key}': {'ENABLED' if status else 'DISABLED'}")
        if service_remark:
            status = config_manager.get_service_control_status(service_remark)
            print(f"      remark '{service_remark}': {'ENABLED' if status else 'DISABLED'}")

def main():
    """主函数"""
    print("DEEP DEBUGGING SERVICE CONTROL LOGIC")
    print("=" * 80)
    
    # 1. 调试配置管理器
    config_manager = debug_config_manager()
    
    # 2. 调试Lucky API解析
    connections_info = debug_lucky_api_parsing()
    
    # 3. 调试连接数计算
    total_connections = debug_connection_calculation(config_manager, connections_info)
    
    # 4. 调试特定服务
    debug_specific_services(config_manager, connections_info)
    
    # 5. 总结
    print("\n" + "=" * 80)
    print("DEBUGGING SUMMARY")
    print("=" * 80)
    
    print(f"Total connections calculated: {total_connections}")
    
    # 检查是否有问题
    issues_found = []
    
    # 检查Proxmox服务
    for conn in connections_info:
        if "proxmox" in conn.get("rule_name", "").lower():
            service_name = conn.get("rule_name", "")
            if config_manager.get_service_control_status(service_name):
                issues_found.append(f"Proxmox service '{service_name}' is ENABLED but should be DISABLED")
    
    if issues_found:
        print("\n❌ ISSUES FOUND:")
        for issue in issues_found:
            print(f"  - {issue}")
    else:
        print("\n✅ No issues found in service control logic")
        print("✅ Proxmox service should be correctly excluded")
    
    print("\n🔍 If you're still seeing issues, the problem might be:")
    print("1. Application not restarted with new code")
    print("2. Application using cached configuration")
    print("3. Multiple application instances running")
    print("4. Application not using the updated service control logic")

if __name__ == "__main__":
    main()
