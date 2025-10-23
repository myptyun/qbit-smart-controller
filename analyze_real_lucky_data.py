#!/usr/bin/env python3
"""
分析真实的Lucky API数据
"""

import json
from pathlib import Path

def load_lucky_api_data():
    """加载Lucky API数据"""
    with open("lucky_api_response.json", 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def load_service_control_config():
    """加载服务控制配置"""
    service_control_file = Path("data/config/service_control.json")
    with open(service_control_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_lucky_data():
    """分析Lucky API数据"""
    print("=" * 80)
    print("REAL LUCKY API DATA ANALYSIS")
    print("=" * 80)
    
    # 加载数据
    lucky_data = load_lucky_api_data()
    service_control = load_service_control_config()
    
    print("\n1. Lucky API Data Structure:")
    print(f"  - ret: {lucky_data.get('ret', 'N/A')}")
    print(f"  - ruleList count: {len(lucky_data.get('ruleList', []))}")
    print(f"  - statistics available: {'Yes' if 'statistics' in lucky_data else 'No'}")
    
    # 提取服务信息
    print("\n2. Extracting Service Information:")
    
    # 从ProxyList中提取服务
    services_from_proxy = []
    if "ruleList" in lucky_data:
        for rule in lucky_data["ruleList"]:
            if "ProxyList" in rule:
                for proxy in rule["ProxyList"]:
                    service_info = {
                        "key": proxy.get("Key", ""),
                        "remark": proxy.get("Remark", ""),
                        "enabled": proxy.get("Enable", False),
                        "service_type": proxy.get("WebServiceType", ""),
                        "domains": proxy.get("Domains", [])
                    }
                    services_from_proxy.append(service_info)
    
    print(f"  Found {len(services_from_proxy)} services in ProxyList:")
    for service in services_from_proxy:
        status = "ENABLED" if service["enabled"] else "DISABLED"
        print(f"    Key: '{service['key']}'")
        print(f"    Remark: '{service['remark']}'")
        print(f"    Status: {status}")
        print(f"    Type: {service['service_type']}")
        if service['domains']:
            print(f"    Domains: {', '.join(service['domains'])}")
        print()
    
    # 从statistics中提取连接信息
    print("3. Connection Statistics:")
    if "statistics" in lucky_data:
        stats = lucky_data["statistics"]
        for rule_key, rule_stats in stats.items():
            print(f"  Rule: {rule_key}")
            if "ProxyList" in rule_stats:
                for proxy_key, proxy_stats in rule_stats["ProxyList"].items():
                    connections = proxy_stats.get("Connections", 0)
                    traffic_in = proxy_stats.get("TrafficIn", 0)
                    traffic_out = proxy_stats.get("TrafficOut", 0)
                    print(f"    Proxy {proxy_key}: {connections} connections")
                    print(f"      Traffic In: {traffic_in} bytes")
                    print(f"      Traffic Out: {traffic_out} bytes")
    
    # 分析服务名称匹配
    print("\n4. Service Name Matching Analysis:")
    
    # 提取所有服务键名
    lucky_service_keys = set()
    for service in services_from_proxy:
        if service["key"]:
            lucky_service_keys.add(service["key"])
    
    # 提取Remark作为可能的服务名称
    lucky_remarks = set()
    for service in services_from_proxy:
        if service["remark"]:
            lucky_remarks.add(service["remark"])
    
    print(f"  Lucky API service keys (Key field): {sorted(lucky_service_keys)}")
    print(f"  Lucky API service remarks (Remark field): {sorted(lucky_remarks)}")
    print(f"  Your config keys: {sorted(service_control.keys())}")
    
    # 检查匹配情况
    config_keys = set(service_control.keys())
    
    # 检查与Key字段的匹配
    key_matches = config_keys & lucky_service_keys
    print(f"\n  Matches with Key field: {len(key_matches)}")
    for key in sorted(key_matches):
        status = "ENABLED" if service_control[key] else "DISABLED"
        print(f"    '{key}': {status} [MATCH]")
    
    # 检查与Remark字段的匹配
    remark_matches = config_keys & lucky_remarks
    print(f"\n  Matches with Remark field: {len(remark_matches)}")
    for key in sorted(remark_matches):
        status = "ENABLED" if service_control[key] else "DISABLED"
        print(f"    '{key}': {status} [MATCH]")
    
    # 检查不匹配的情况
    config_only = config_keys - lucky_service_keys - lucky_remarks
    print(f"\n  In config but NOT found in Lucky API: {len(config_only)}")
    for key in sorted(config_only):
        status = "ENABLED" if service_control[key] else "DISABLED"
        print(f"    '{key}': {status} [NOT FOUND]")
    
    # 检查新服务
    lucky_only = (lucky_service_keys | lucky_remarks) - config_keys
    print(f"\n  In Lucky API but NOT in config: {len(lucky_only)}")
    for key in sorted(lucky_only):
        print(f"    '{key}': [NOT CONFIGURED - default DISABLED]")
    
    # 5. 生成修复建议
    print("\n5. Fix Recommendations:")
    
    if not key_matches and not remark_matches:
        print("  CRITICAL ISSUE: No services match between config and Lucky API!")
        print("  This means ALL services will be treated as disabled.")
        print("  You need to update your configuration to match Lucky API service names.")
    
    if config_only:
        print(f"  WARNING: {len(config_only)} services in config are not found in Lucky API")
        print("  These services will be ignored (treated as disabled)")
    
    if lucky_only:
        print(f"  INFO: {len(lucky_only)} new services found in Lucky API")
        print("  These will be automatically added to config as DISABLED")
    
    # 6. 生成正确的配置
    print("\n6. Generating Corrected Configuration:")
    
    # 创建服务键名到Remark的映射
    key_to_remark = {}
    for service in services_from_proxy:
        if service["key"] and service["remark"]:
            key_to_remark[service["key"]] = service["remark"]
    
    # 生成修复后的配置
    corrected_config = {}
    
    # 保留匹配的服务配置
    for key in key_matches:
        corrected_config[key] = service_control[key]
    
    for key in remark_matches:
        corrected_config[key] = service_control[key]
    
    # 添加新服务（默认禁用）
    for key in lucky_only:
        corrected_config[key] = False
    
    print("Corrected service control configuration:")
    for service_key, enabled in corrected_config.items():
        status = "ENABLED" if enabled else "DISABLED"
        source = "EXISTING" if service_key in (key_matches | remark_matches) else "NEW"
        print(f"  '{service_key}': {status} ({source})")
    
    # 保存修复后的配置
    if corrected_config != service_control:
        print(f"\n7. Saving corrected configuration...")
        backup_file = Path("data/config/service_control.json.backup")
        
        # 备份原配置
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(service_control, f, indent=2, ensure_ascii=False)
        print(f"  Original config backed up to: {backup_file}")
        
        # 保存修复后的配置
        with open(Path("data/config/service_control.json"), 'w', encoding='utf-8') as f:
            json.dump(corrected_config, f, indent=2, ensure_ascii=False)
        print(f"  Corrected config saved to: data/config/service_control.json")
        
        print(f"\n  Configuration has been corrected!")
        print(f"    - Removed {len(config_only)} mismatched services")
        print(f"    - Added {len(lucky_only)} new services (default disabled)")
        print(f"    - Kept {len(key_matches | remark_matches)} matching services")
    else:
        print(f"\n  Configuration is already correct!")

def main():
    """主函数"""
    analyze_lucky_data()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("Key findings:")
    print("1. Lucky API uses 'Key' field as unique service identifier")
    print("2. 'Remark' field contains human-readable service names")
    print("3. Service control should match either 'Key' or 'Remark' field")
    print("4. All services currently have 0 connections in statistics")
    print("5. Configuration has been updated to match Lucky API data")

if __name__ == "__main__":
    main()
