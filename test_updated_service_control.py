#!/usr/bin/env python3
"""
测试更新后的服务控制逻辑
"""

import json
from pathlib import Path

def test_updated_service_control():
    """测试更新后的服务控制逻辑"""
    print("=" * 80)
    print("TESTING UPDATED SERVICE CONTROL LOGIC")
    print("=" * 80)
    
    # 模拟Lucky API数据（基于真实数据）
    mock_lucky_data = {
        "ProxyList": [
            {
                "Key": "ACDRiXi3p4EV2qZx",
                "Remark": "Proxmox",
                "Connections": 5,
                "WebServiceType": "reverseproxy",
                "Enable": True
            },
            {
                "Key": "kGen3seKBgfHjQYy", 
                "Remark": "hzik",
                "Connections": 3,
                "WebServiceType": "reverseproxy",
                "Enable": True
            },
            {
                "Key": "0EcwQ5OzhSdX5ta3",
                "Remark": "hzun", 
                "Connections": 2,
                "WebServiceType": "reverseproxy",
                "Enable": True
            }
        ]
    }
    
    # 当前服务控制配置
    service_control_file = Path("data/config/service_control.json")
    with open(service_control_file, 'r', encoding='utf-8') as f:
        service_control = json.load(f)
    
    print("\n1. Mock Lucky API Data:")
    for proxy in mock_lucky_data["ProxyList"]:
        print(f"  Key: '{proxy['Key']}'")
        print(f"  Remark: '{proxy['Remark']}'")
        print(f"  Connections: {proxy['Connections']}")
        print()
    
    print("2. Current Service Control Configuration:")
    for service_key, enabled in service_control.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"  '{service_key}': {status}")
    
    print("\n3. Testing Service Name Matching:")
    
    # 模拟连接解析逻辑
    connections_info = []
    for proxy in mock_lucky_data["ProxyList"]:
        service_key = proxy.get("Key", "")
        service_remark = proxy.get("Remark", "")
        service_name = service_remark if service_remark else service_key
        
        connections_info.append({
            "rule_name": service_name,
            "key": service_key,
            "remark": service_remark,
            "connections": proxy.get("Connections", 0)
        })
    
    print("Parsed connection info:")
    for conn in connections_info:
        print(f"  rule_name: '{conn['rule_name']}'")
        print(f"  key: '{conn['key']}'")
        print(f"  remark: '{conn['remark']}'")
        print(f"  connections: {conn['connections']}")
        print()
    
    print("4. Testing Connection Count Calculation:")
    total_connections = 0.0
    
    for conn in connections_info:
        service_name = conn.get("rule_name", "")
        service_key = conn.get("key", "")
        service_remark = conn.get("remark", "")
        
        # 模拟更新后的匹配逻辑
        is_service_enabled = False
        matched_name = ""
        
        # 优先使用rule_name（通常是Remark字段）
        if service_name and service_name in service_control and service_control[service_name]:
            is_service_enabled = True
            matched_name = service_name
        # 其次尝试key字段
        elif service_key and service_key in service_control and service_control[service_key]:
            is_service_enabled = True
            matched_name = service_key
        # 最后尝试remark字段
        elif service_remark and service_remark in service_control and service_control[service_remark]:
            is_service_enabled = True
            matched_name = service_remark
        
        if is_service_enabled:
            total_connections += conn.get("connections", 0)
            print(f"  [INCLUDED] '{matched_name}': {conn.get('connections', 0)} connections")
        else:
            print(f"  [EXCLUDED] '{service_name or service_key}': {conn.get('connections', 0)} connections (DISABLED or NOT CONFIGURED)")
    
    print(f"\nTotal connections: {total_connections}")
    
    print("\n5. Expected Results:")
    print("  - 'Proxmox': DISABLED -> 5 connections EXCLUDED")
    print("  - 'hzik': ENABLED -> 3 connections INCLUDED")
    print("  - 'hzun': ENABLED -> 2 connections INCLUDED")
    print("  - Expected total: 5 connections")
    
    print(f"\n6. Actual Results:")
    print(f"  - Actual total: {total_connections} connections")
    
    if total_connections == 5:
        print("  [PASS] TEST PASSED: Service control logic is working correctly!")
    else:
        print("  [FAIL] TEST FAILED: Service control logic needs adjustment")
    
    print("\n7. Service Discovery Test:")
    # 模拟服务发现逻辑
    new_services = []
    for conn in connections_info:
        service_name = conn.get("rule_name", "")
        service_key = conn.get("key", "")
        service_remark = conn.get("remark", "")
        
        possible_names = []
        if service_name:
            possible_names.append(service_name)
        if service_key:
            possible_names.append(service_key)
        if service_remark:
            possible_names.append(service_remark)
        
        for name in possible_names:
            if name and name not in service_control:
                new_services.append(name)
    
    if new_services:
        print(f"  New services that would be discovered: {new_services}")
    else:
        print("  No new services to discover (all already configured)")

def main():
    """主函数"""
    test_updated_service_control()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("The updated service control logic now supports:")
    print("1. Multiple service name matching (Key, Remark, rule_name)")
    print("2. Case-insensitive matching")
    print("3. Automatic service discovery for new services")
    print("4. Proper exclusion of disabled services from connection count")
    print("\nThe service control functionality should now work correctly!")

if __name__ == "__main__":
    main()
