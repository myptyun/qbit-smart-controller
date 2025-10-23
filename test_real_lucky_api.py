#!/usr/bin/env python3
"""
使用真实的Lucky API测试服务名称匹配
"""

import json
import urllib.request
import urllib.error
from pathlib import Path

def fetch_lucky_api_data():
    """获取真实的Lucky API数据"""
    api_url = "http://192.168.2.3:16601/api/webservice/rules?openToken=S9SXzQAAg03myzAfUsLkiQmTBUUUr3Yn"
    
    print(f"Fetching data from Lucky API...")
    print(f"URL: {api_url}")
    
    try:
        with urllib.request.urlopen(api_url, timeout=10) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                print("SUCCESS: Connected to Lucky API")
                return json.loads(data)
            else:
                print(f"ERROR: HTTP {response.status}")
                return None
    except urllib.error.URLError as e:
        print(f"ERROR: Connection failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return None

def load_service_control_config():
    """加载服务控制配置"""
    service_control_file = Path("data/config/service_control.json")
    with open(service_control_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_service_keys_from_lucky_data(lucky_data):
    """从Lucky API数据中提取服务键名"""
    service_keys = set()
    
    print("\nExtracting service keys from Lucky API data...")
    
    # 从ProxyList提取
    if "ProxyList" in lucky_data and isinstance(lucky_data["ProxyList"], list):
        print(f"Found ProxyList with {len(lucky_data['ProxyList'])} services:")
        for proxy in lucky_data["ProxyList"]:
            key = proxy.get("Key", "")
            connections = proxy.get("Connections", 0)
            if key:
                service_keys.add(key)
                print(f"  '{key}': {connections} connections")
    
    # 从statistics提取
    if "statistics" in lucky_data and isinstance(lucky_data["statistics"], dict):
        print(f"Found statistics with {len(lucky_data['statistics'])} services:")
        for key, stats in lucky_data["statistics"].items():
            connections = stats.get("Connections", 0)
            service_keys.add(key)
            print(f"  '{key}': {connections} connections")
    
    # 从ruleList提取
    if "ruleList" in lucky_data and isinstance(lucky_data["ruleList"], list):
        print(f"Found ruleList with {len(lucky_data['ruleList'])} rules:")
        for rule in lucky_data["ruleList"]:
            rule_name = rule.get("RuleName", "")
            rule_key = rule.get("RuleKey", "")
            
            if rule_name:
                service_keys.add(rule_name)
                print(f"  RuleName: '{rule_name}'")
            
            if rule_key:
                service_keys.add(rule_key)
                print(f"  RuleKey: '{rule_key}'")
            
            # 从ProxyList中提取
            if "ProxyList" in rule and isinstance(rule["ProxyList"], list):
                for proxy in rule["ProxyList"]:
                    key = proxy.get("Key", "")
                    connections = proxy.get("Connections", 0)
                    if key:
                        service_keys.add(key)
                        print(f"    Proxy Key: '{key}': {connections} connections")
    
    return service_keys

def analyze_service_matching():
    """分析服务名称匹配"""
    print("=" * 80)
    print("REAL LUCKY API SERVICE NAME MATCHING ANALYSIS")
    print("=" * 80)
    
    # 1. 获取Lucky API数据
    print("\n1. Fetching Lucky API data...")
    lucky_data = fetch_lucky_api_data()
    
    if not lucky_data:
        print("ERROR: Could not fetch Lucky API data")
        return
    
    # 保存原始数据用于分析
    debug_file = Path("real_lucky_api_response.json")
    with open(debug_file, 'w', encoding='utf-8') as f:
        json.dump(lucky_data, f, indent=2, ensure_ascii=False)
    print(f"Lucky API response saved to: {debug_file}")
    
    # 2. 提取服务键名
    print("\n2. Extracting service keys from Lucky API...")
    lucky_service_keys = extract_service_keys_from_lucky_data(lucky_data)
    
    print(f"\nAll Lucky API service keys found:")
    for key in sorted(lucky_service_keys):
        print(f"  '{key}'")
    
    # 3. 加载当前配置
    print("\n3. Loading current service control configuration...")
    service_control = load_service_control_config()
    
    print("Current service control configuration:")
    for service_key, enabled in service_control.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"  '{service_key}': {status}")
    
    # 4. 分析匹配情况
    print("\n4. Analyzing service name matching...")
    config_keys = set(service_control.keys())
    
    # 完全匹配的键
    exact_matches = config_keys & lucky_service_keys
    print(f"\nExact matches ({len(exact_matches)}):")
    for key in sorted(exact_matches):
        status = "ENABLED" if service_control[key] else "DISABLED"
        print(f"  '{key}': {status} [MATCH]")
    
    # 配置中存在但Lucky API中不存在的键
    config_only = config_keys - lucky_service_keys
    print(f"\nIn config but NOT in Lucky API ({len(config_only)}):")
    for key in sorted(config_only):
        status = "ENABLED" if service_control[key] else "DISABLED"
        print(f"  '{key}': {status} [NOT FOUND in Lucky API]")
    
    # Lucky API中存在但配置中不存在的键
    lucky_only = lucky_service_keys - config_keys
    print(f"\nIn Lucky API but NOT in config ({len(lucky_only)}):")
    for key in sorted(lucky_only):
        print(f"  '{key}': [NOT CONFIGURED - will be default DISABLED]")
    
    # 5. 模拟连接数计算
    print("\n5. Simulating connection count calculation...")
    
    # 从Lucky API数据中提取连接信息
    connections_data = []
    
    # 从ProxyList提取
    if "ProxyList" in lucky_data:
        for proxy in lucky_data["ProxyList"]:
            key = proxy.get("Key", "")
            connections = proxy.get("Connections", 0)
            if key:
                connections_data.append({"rule_name": key, "connections": connections})
    
    # 从statistics提取
    if "statistics" in lucky_data:
        for key, stats in lucky_data["statistics"].items():
            connections = stats.get("Connections", 0)
            connections_data.append({"rule_name": key, "connections": connections})
    
    print("Connection count calculation:")
    total_connections = 0.0
    
    for conn in connections_data:
        service_key = conn["rule_name"]
        connections = conn["connections"]
        
        # 检查服务控制状态
        is_enabled = service_control.get(service_key, False)
        
        if is_enabled:
            total_connections += connections
            print(f"  [INCLUDED] '{service_key}': {connections} connections")
        else:
            print(f"  [EXCLUDED] '{service_key}': {connections} connections (DISABLED or NOT CONFIGURED)")
    
    print(f"\nTotal connections: {total_connections}")
    
    # 6. 生成修复建议
    print("\n6. Fix recommendations:")
    
    if config_only:
        print(f"\nWARNING: MISMATCH DETECTED!")
        print(f"The following services are configured but not found in Lucky API:")
        for key in sorted(config_only):
            print(f"  - '{key}'")
        print(f"These services will be ignored (treated as disabled)")
    
    if lucky_only:
        print(f"\nNEW SERVICES DETECTED:")
        print(f"The following services are in Lucky API but not configured:")
        for key in sorted(lucky_only):
            print(f"  - '{key}'")
        print(f"These services will be automatically added to config as DISABLED")
    
    if not exact_matches:
        print(f"\nCRITICAL ISSUE:")
        print(f"NO services match between config and Lucky API!")
        print(f"This means ALL services will be treated as disabled")
        print(f"Check service names carefully for typos or case differences")
    
    # 7. 生成修复后的配置
    if config_only or lucky_only:
        print("\n7. Generating corrected configuration...")
        
        corrected_config = {}
        
        # 保留匹配的服务配置
        for key in exact_matches:
            corrected_config[key] = service_control[key]
        
        # 添加新服务（默认禁用）
        for key in lucky_only:
            corrected_config[key] = False
        
        print("Corrected service control configuration:")
        for service_key, enabled in corrected_config.items():
            status = "ENABLED" if enabled else "DISABLED"
            source = "EXISTING" if service_key in exact_matches else "NEW"
            print(f"  '{service_key}': {status} ({source})")
        
        # 保存修复后的配置
        backup_file = Path("data/config/service_control.json.backup")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(service_control, f, indent=2, ensure_ascii=False)
        print(f"\nOriginal config backed up to: {backup_file}")
        
        with open(Path("data/config/service_control.json"), 'w', encoding='utf-8') as f:
            json.dump(corrected_config, f, indent=2, ensure_ascii=False)
        print(f"Corrected config saved to: data/config/service_control.json")
        
        print(f"\nConfiguration has been corrected!")
        print(f"  - Removed {len(config_only)} mismatched services")
        print(f"  - Added {len(lucky_only)} new services (default disabled)")
        print(f"  - Kept {len(exact_matches)} matching services")
    else:
        print(f"\nConfiguration is already correct!")

def main():
    """主函数"""
    analyze_service_matching()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("Check the following files for detailed information:")
    print("  - real_lucky_api_response.json: Full Lucky API response")
    print("  - data/config/service_control.json: Updated configuration")
    print("  - data/config/service_control.json.backup: Original configuration backup")

if __name__ == "__main__":
    main()
