#!/usr/bin/env python3
"""
服务名称匹配演示工具
演示Lucky API服务名称与配置键名匹配的重要性
"""

import json
from pathlib import Path

def load_current_config():
    """加载当前配置"""
    service_control_file = Path("data/config/service_control.json")
    with open(service_control_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def demonstrate_matching_problems():
    """演示匹配问题"""
    print("=" * 80)
    print("SERVICE NAME MATCHING PROBLEMS DEMONSTRATION")
    print("=" * 80)
    
    # 当前配置
    current_config = load_current_config()
    print("\n1. Current service control configuration:")
    for service_key, enabled in current_config.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"  '{service_key}': {status}")
    
    # 模拟不同的Lucky API响应场景
    scenarios = [
        {
            "name": "Scenario 1: Perfect Match",
            "description": "Lucky API返回的服务名称与配置完全匹配",
            "lucky_data": {
                "ProxyList": [
                    {"Key": "Proxmox", "Connections": 5},
                    {"Key": "hzun", "Connections": 3},
                    {"Key": "hzik", "Connections": 2}
                ]
            }
        },
        {
            "name": "Scenario 2: Case Mismatch",
            "description": "Lucky API返回的服务名称大小写不匹配",
            "lucky_data": {
                "ProxyList": [
                    {"Key": "proxmox", "Connections": 5},  # 小写
                    {"Key": "Hzun", "Connections": 3},     # 首字母大写
                    {"Key": "HZIK", "Connections": 2}      # 全大写
                ]
            }
        },
        {
            "name": "Scenario 3: Name Mismatch",
            "description": "Lucky API返回的服务名称与配置不完全匹配",
            "lucky_data": {
                "ProxyList": [
                    {"Key": "Proxmox-Proxy", "Connections": 5},
                    {"Key": "hzun-service", "Connections": 3},
                    {"Key": "hzik-proxy", "Connections": 2}
                ]
            }
        },
        {
            "name": "Scenario 4: Mixed Issues",
            "description": "混合问题：部分匹配，部分不匹配",
            "lucky_data": {
                "ProxyList": [
                    {"Key": "Proxmox", "Connections": 5},    # 匹配
                    {"Key": "hzun", "Connections": 3},       # 匹配
                    {"Key": "NewService", "Connections": 2}  # 新服务
                ]
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print("-" * 60)
        print(f"Description: {scenario['description']}")
        
        # 提取Lucky API中的服务键名
        lucky_keys = set()
        for proxy in scenario['lucky_data']['ProxyList']:
            lucky_keys.add(proxy['Key'])
        
        print(f"\nLucky API service keys:")
        for key in sorted(lucky_keys):
            print(f"  '{key}'")
        
        # 分析匹配情况
        config_keys = set(current_config.keys())
        exact_matches = config_keys & lucky_keys
        config_only = config_keys - lucky_keys
        lucky_only = lucky_keys - config_keys
        
        print(f"\nMatching analysis:")
        print(f"  Exact matches: {len(exact_matches)}")
        for key in sorted(exact_matches):
            status = "ENABLED" if current_config[key] else "DISABLED"
            print(f"    '{key}': {status} [MATCH]")
        
        print(f"  In config but not in Lucky API: {len(config_only)}")
        for key in sorted(config_only):
            status = "ENABLED" if current_config[key] else "DISABLED"
            print(f"    '{key}': {status} [NOT FOUND]")
        
        print(f"  In Lucky API but not in config: {len(lucky_only)}")
        for key in sorted(lucky_only):
            print(f"    '{key}': [NOT CONFIGURED - default DISABLED]")
        
        # 计算实际会参与连接数计算的服务
        print(f"\nConnection count calculation:")
        total_connections = 0.0
        for proxy in scenario['lucky_data']['ProxyList']:
            service_key = proxy['Key']
            connections = proxy['Connections']
            
            # 检查是否在配置中且启用
            is_configured = service_key in current_config
            is_enabled = current_config.get(service_key, False)
            
            if is_configured and is_enabled:
                total_connections += connections
                print(f"  [INCLUDED] '{service_key}': {connections} connections")
            else:
                reason = "NOT CONFIGURED" if not is_configured else "DISABLED"
                print(f"  [EXCLUDED] '{service_key}': {connections} connections ({reason})")
        
        print(f"  Total connections: {total_connections}")

def show_correct_matching_example():
    """显示正确匹配的示例"""
    print(f"\n" + "=" * 80)
    print("CORRECT MATCHING EXAMPLE")
    print("=" * 80)
    
    print("For proper service control to work, the following must match EXACTLY:")
    print("\n1. Lucky API response:")
    print("""
{
  "ProxyList": [
    {
      "Key": "Proxmox",     # ← This must match config key
      "Connections": 5,
      "WebServiceType": "proxy"
    },
    {
      "Key": "hzun",        # ← This must match config key
      "Connections": 3,
      "WebServiceType": "proxy"
    }
  ]
}
""")
    
    print("2. Service control configuration:")
    print("""
{
  "Proxmox": false,  # ← Must match Lucky API "Key" field exactly
  "hzun": true,      # ← Must match Lucky API "Key" field exactly
  "hzik": true       # ← Must match Lucky API "Key" field exactly
}
""")
    
    print("3. Result:")
    print("  - 'Proxmox': DISABLED → 5 connections EXCLUDED")
    print("  - 'hzun': ENABLED → 3 connections INCLUDED")
    print("  - 'hzik': ENABLED → 0 connections (not in API) → EXCLUDED")
    print("  - Total connections: 3")

def provide_troubleshooting_guide():
    """提供故障排除指南"""
    print(f"\n" + "=" * 80)
    print("TROUBLESHOOTING GUIDE")
    print("=" * 80)
    
    print("If disabled services are still being counted, check these:")
    
    print("\n1. Verify Lucky API response format:")
    print("   - Check if Lucky API is returning expected data structure")
    print("   - Look for 'Key' field in ProxyList or statistics")
    print("   - Ensure service names are consistent")
    
    print("\n2. Check service name matching:")
    print("   - Service names must match EXACTLY (case sensitive)")
    print("   - No extra spaces, hyphens, or special characters")
    print("   - Compare Lucky API 'Key' field with config key names")
    
    print("\n3. Common mismatches:")
    print("   - 'Proxmox' vs 'proxmox' (case difference)")
    print("   - 'Proxmox' vs 'Proxmox-Proxy' (extra suffix)")
    print("   - 'Proxmox' vs 'Proxmox ' (trailing space)")
    print("   - 'Proxmox' vs 'proxmox-proxy' (case + suffix)")
    
    print("\n4. Debug steps:")
    print("   - Run: python verify_service_matching.py")
    print("   - Check lucky_api_debug.json for actual API response")
    print("   - Compare service names character by character")
    print("   - Test with a known working Lucky API endpoint")
    
    print("\n5. Fix methods:")
    print("   - Update service_control.json to match Lucky API exactly")
    print("   - Or update Lucky device service names to match config")
    print("   - Restart application after making changes")

def main():
    """主函数"""
    demonstrate_matching_problems()
    show_correct_matching_example()
    provide_troubleshooting_guide()
    
    print(f"\n" + "=" * 80)
    print("KEY TAKEAWAY")
    print("=" * 80)
    print("The service names in data/config/service_control.json MUST match")
    print("the 'Key' field values from Lucky API response EXACTLY.")
    print("Any mismatch will cause the service to be treated as disabled.")
    print("\nThis is why you might see disabled services still being counted -")
    print("the names don't match, so the system can't find the control setting!")

if __name__ == "__main__":
    main()
