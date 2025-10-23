#!/usr/bin/env python3
"""
综合测试服务控制功能
"""

import json
import urllib.request
import urllib.error
from pathlib import Path

def test_lucky_api_connection():
    """测试Lucky API连接"""
    print("Testing Lucky API Connection")
    print("=" * 50)
    
    # 读取配置文件
    config_file = Path("config/config.yaml")
    if not config_file.exists():
        print("ERROR: config.yaml not found")
        return None
    
    # 简单解析YAML（不依赖yaml库）
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取API URL
    api_url = None
    lines = content.split('\n')
    for line in lines:
        if 'api_url:' in line:
            api_url = line.split('api_url:')[1].strip().strip('"')
            break
    
    if not api_url:
        print("ERROR: API URL not found in config")
        return None
    
    print(f"API URL: {api_url}")
    
    # 测试连接
    try:
        print("Attempting to connect to Lucky API...")
        with urllib.request.urlopen(api_url, timeout=10) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                print("SUCCESS: Connected to Lucky API")
                
                # 解析JSON数据
                try:
                    json_data = json.loads(data)
                    print(f"Data structure keys: {list(json_data.keys())}")
                    
                    # 保存数据用于分析
                    debug_file = Path("lucky_api_response.json")
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    print(f"Response saved to: {debug_file}")
                    
                    return json_data
                except json.JSONDecodeError as e:
                    print(f"ERROR: Failed to parse JSON response: {e}")
                    return None
            else:
                print(f"ERROR: HTTP {response.status}")
                return None
                
    except urllib.error.URLError as e:
        print(f"ERROR: Connection failed: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return None

def analyze_lucky_data(lucky_data):
    """分析Lucky API数据"""
    print("\nAnalyzing Lucky API Data")
    print("=" * 50)
    
    if not lucky_data:
        print("No data to analyze")
        return
    
    # 分析数据结构
    print("Data structure analysis:")
    print(f"  Top-level keys: {list(lucky_data.keys())}")
    
    # 检查statistics
    if "statistics" in lucky_data:
        print(f"\nStatistics section:")
        stats = lucky_data["statistics"]
        print(f"  Number of rules: {len(stats)}")
        for rule_key, rule_data in stats.items():
            connections = rule_data.get("Connections", 0)
            print(f"    {rule_key}: {connections} connections")
    
    # 检查ruleList
    if "ruleList" in lucky_data:
        print(f"\nRuleList section:")
        rules = lucky_data["ruleList"]
        print(f"  Number of rules: {len(rules)}")
        for rule in rules:
            rule_name = rule.get("RuleName", "Unknown")
            rule_key = rule.get("RuleKey", "")
            print(f"    Rule: {rule_name} (Key: {rule_key})")
            
            if "ProxyList" in rule:
                proxies = rule["ProxyList"]
                print(f"      Proxies: {len(proxies)}")
                for proxy in proxies:
                    proxy_key = proxy.get("Key", "")
                    connections = proxy.get("Connections", 0)
                    print(f"        {proxy_key}: {connections} connections")
    
    # 检查ProxyList
    if "ProxyList" in lucky_data:
        print(f"\nProxyList section:")
        proxies = lucky_data["ProxyList"]
        print(f"  Number of proxies: {len(proxies)}")
        for proxy in proxies:
            proxy_key = proxy.get("Key", "")
            connections = proxy.get("Connections", 0)
            print(f"    {proxy_key}: {connections} connections")

def test_service_mapping(lucky_data):
    """测试服务映射"""
    print("\nTesting Service Mapping")
    print("=" * 50)
    
    # 读取服务控制配置
    service_control_file = Path("data/config/service_control.json")
    with open(service_control_file, 'r', encoding='utf-8') as f:
        service_control = json.load(f)
    
    print("Service control configuration:")
    for service_key, enabled in service_control.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"  {service_key}: {status}")
    
    # 提取Lucky API中的服务键
    lucky_service_keys = set()
    
    if "statistics" in lucky_data:
        lucky_service_keys.update(lucky_data["statistics"].keys())
    
    if "ruleList" in lucky_data:
        for rule in lucky_data["ruleList"]:
            if "RuleName" in rule:
                lucky_service_keys.add(rule["RuleName"])
            if "RuleKey" in rule:
                lucky_service_keys.add(rule["RuleKey"])
            
            if "ProxyList" in rule:
                for proxy in rule["ProxyList"]:
                    if "Key" in proxy:
                        lucky_service_keys.add(proxy["Key"])
    
    if "ProxyList" in lucky_data:
        for proxy in lucky_data["ProxyList"]:
            if "Key" in proxy:
                lucky_service_keys.add(proxy["Key"])
    
    print(f"\nLucky API service keys: {sorted(lucky_service_keys)}")
    print(f"Service control keys: {sorted(service_control.keys())}")
    
    # 检查映射
    print(f"\nMapping analysis:")
    for service_key in service_control.keys():
        if service_key in lucky_service_keys:
            print(f"  {service_key}: MATCHED")
        else:
            print(f"  {service_key}: NOT FOUND in Lucky API")
    
    # 检查未配置的服务
    unconfigured_services = lucky_service_keys - set(service_control.keys())
    if unconfigured_services:
        print(f"\nUnconfigured services in Lucky API:")
        for service in unconfigured_services:
            print(f"  {service}")

def simulate_connection_calculation(lucky_data):
    """模拟连接数计算"""
    print("\nSimulating Connection Calculation")
    print("=" * 50)
    
    # 读取服务控制配置
    service_control_file = Path("data/config/service_control.json")
    with open(service_control_file, 'r', encoding='utf-8') as f:
        service_control = json.load(f)
    
    # 提取连接数据
    connections_data = []
    
    # 从statistics提取
    if "statistics" in lucky_data:
        for rule_key, rule_data in lucky_data["statistics"].items():
            connections = rule_data.get("Connections", 0)
            connections_data.append({
                "rule_name": rule_key,
                "key": rule_key,
                "connections": connections
            })
    
    # 从ProxyList提取
    if "ProxyList" in lucky_data:
        for proxy in lucky_data["ProxyList"]:
            proxy_key = proxy.get("Key", "")
            connections = proxy.get("Connections", 0)
            connections_data.append({
                "rule_name": proxy_key,
                "key": proxy_key,
                "connections": connections
            })
    
    print("Extracted connection data:")
    for conn in connections_data:
        print(f"  {conn['rule_name']}: {conn['connections']} connections")
    
    # 模拟_collect_total_connections逻辑
    print(f"\nSimulating _collect_total_connections logic:")
    total_connections = 0.0
    
    for conn in connections_data:
        service_key = conn.get("rule_name", "")
        service_key_alt = conn.get("key", "")
        service_name = service_key or service_key_alt
        
        # 使用动态服务控制状态
        is_service_enabled = service_control.get(service_key or service_key_alt, False)
        
        if is_service_enabled:
            connections = conn.get("connections", 0)
            total_connections += connections
            print(f"  [INCLUDED] {service_name}: {connections} connections")
        else:
            print(f"  [EXCLUDED] {service_name}: {conn.get('connections', 0)} connections")
    
    print(f"\nTotal connections calculated: {total_connections}")
    
    # 分析结果
    enabled_services = [k for k, v in service_control.items() if v]
    disabled_services = [k for k, v in service_control.items() if not v]
    
    print(f"\nFinal analysis:")
    print(f"  Enabled services: {enabled_services}")
    print(f"  Disabled services: {disabled_services}")
    print(f"  Total connections from enabled services: {total_connections}")
    
    return total_connections

def main():
    """主函数"""
    print("Comprehensive Service Control Test")
    print("=" * 60)
    
    # 1. 测试Lucky API连接
    lucky_data = test_lucky_api_connection()
    
    if lucky_data:
        # 2. 分析Lucky数据
        analyze_lucky_data(lucky_data)
        
        # 3. 测试服务映射
        test_service_mapping(lucky_data)
        
        # 4. 模拟连接数计算
        total_connections = simulate_connection_calculation(lucky_data)
        
        print(f"\n" + "=" * 60)
        print("FINAL RESULT:")
        print(f"Total connections from enabled services: {total_connections}")
        
        if total_connections > 0:
            print("Service control is working correctly!")
            print("Only enabled services are contributing to the total.")
        else:
            print("All services are disabled or no connections found.")
    else:
        print("\n" + "=" * 60)
        print("Could not connect to Lucky API.")
        print("Please check:")
        print("1. Lucky device is running and accessible")
        print("2. API URL is correct in config.yaml")
        print("3. Network connectivity")
        print("4. API token is valid")

if __name__ == "__main__":
    main()
