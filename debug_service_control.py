#!/usr/bin/env python3
"""
调试服务控制问题的工具
"""

import json
import asyncio
import aiohttp
from pathlib import Path

async def debug_lucky_api_data():
    """调试Lucky API返回的数据结构"""
    print("Debugging Lucky API Data Structure")
    print("=" * 50)
    
    # 读取配置
    config_file = Path("config/config.yaml")
    if not config_file.exists():
        print("ERROR: config.yaml not found")
        return
    
    import yaml
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    lucky_devices = config.get("lucky_devices", [])
    if not lucky_devices:
        print("ERROR: No Lucky devices configured")
        return
    
    device = lucky_devices[0]
    api_url = device["api_url"]
    
    print(f"Testing device: {device['name']}")
    print(f"API URL: {api_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    print("\nSUCCESS: Retrieved Lucky API data")
                    
                    # 分析数据结构
                    print("\nData structure analysis:")
                    print(f"  Top-level keys: {list(data.keys())}")
                    
                    # 检查 statistics
                    if "statistics" in data:
                        print(f"  Statistics keys: {list(data['statistics'].keys())}")
                        for rule_key, rule_stats in data["statistics"].items():
                            print(f"    Rule: {rule_key}")
                            print(f"      Keys: {list(rule_stats.keys())}")
                            connections = rule_stats.get("Connections", 0)
                            print(f"      Connections: {connections}")
                    
                    # 检查 ruleList
                    if "ruleList" in data:
                        print(f"  RuleList count: {len(data['ruleList'])}")
                        for i, rule in enumerate(data["ruleList"][:3]):  # 只显示前3个
                            print(f"    Rule {i}: {rule.get('RuleName', 'Unknown')}")
                            print(f"      Keys: {list(rule.keys())}")
                            if "ProxyList" in rule:
                                print(f"      ProxyList count: {len(rule['ProxyList'])}")
                                for j, proxy in enumerate(rule["ProxyList"][:2]):  # 只显示前2个
                                    print(f"        Proxy {j}: {proxy.get('Key', 'Unknown')}")
                                    print(f"          Keys: {list(proxy.keys())}")
                                    print(f"          Connections: {proxy.get('Connections', 0)}")
                    
                    # 检查 ProxyList
                    if "ProxyList" in data:
                        print(f"  ProxyList count: {len(data['ProxyList'])}")
                        for i, proxy in enumerate(data["ProxyList"][:3]):  # 只显示前3个
                            print(f"    Proxy {i}: {proxy.get('Key', 'Unknown')}")
                            print(f"      Keys: {list(proxy.keys())}")
                            print(f"      Connections: {proxy.get('Connections', 0)}")
                    
                    # 保存完整数据用于分析
                    debug_file = Path("debug_lucky_data.json")
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"\nFull data saved to: {debug_file}")
                    
                else:
                    print(f"ERROR: HTTP {response.status}")
                    content = await response.text()
                    print(f"Response: {content[:200]}...")
                    
    except Exception as e:
        print(f"ERROR: {e}")

def debug_service_control_mapping():
    """调试服务控制映射"""
    print("\n" + "=" * 50)
    print("Debugging Service Control Mapping")
    print("=" * 50)
    
    # 读取服务控制状态
    service_control_file = Path("data/config/service_control.json")
    if service_control_file.exists():
        with open(service_control_file, 'r', encoding='utf-8') as f:
            service_control = json.load(f)
        
        print("Current service control configuration:")
        for service_key, enabled in service_control.items():
            status = "ENABLED" if enabled else "DISABLED"
            print(f"  {service_key}: {status}")
    else:
        print("Service control file not found")
    
    # 读取Lucky数据（如果存在）
    debug_file = Path("debug_lucky_data.json")
    if debug_file.exists():
        with open(debug_file, 'r', encoding='utf-8') as f:
            lucky_data = json.load(f)
        
        print("\nLucky API service keys:")
        
        # 从 statistics 提取
        if "statistics" in lucky_data:
            print("  From statistics:")
            for rule_key in lucky_data["statistics"].keys():
                print(f"    {rule_key}")
        
        # 从 ruleList 提取
        if "ruleList" in lucky_data:
            print("  From ruleList:")
            for rule in lucky_data["ruleList"]:
                rule_name = rule.get("RuleName", "Unknown")
                rule_key = rule.get("RuleKey", "")
                print(f"    RuleName: {rule_name}, RuleKey: {rule_key}")
                
                if "ProxyList" in rule:
                    for proxy in rule["ProxyList"]:
                        proxy_key = proxy.get("Key", "")
                        print(f"      Proxy Key: {proxy_key}")
        
        # 从 ProxyList 提取
        if "ProxyList" in lucky_data:
            print("  From ProxyList:")
            for proxy in lucky_data["ProxyList"]:
                proxy_key = proxy.get("Key", "")
                print(f"    {proxy_key}")
        
        print("\nMapping analysis:")
        print("  Service control keys vs Lucky API keys:")
        for service_key in service_control.keys():
            found = False
            # 检查是否在Lucky数据中找到匹配的键
            if "statistics" in lucky_data and service_key in lucky_data["statistics"]:
                found = True
                print(f"    {service_key}: FOUND in statistics")
            elif "ruleList" in lucky_data:
                for rule in lucky_data["ruleList"]:
                    if (rule.get("RuleName") == service_key or 
                        rule.get("RuleKey") == service_key):
                        found = True
                        print(f"    {service_key}: FOUND in ruleList")
                        break
            elif "ProxyList" in lucky_data:
                for proxy in lucky_data["ProxyList"]:
                    if proxy.get("Key") == service_key:
                        found = True
                        print(f"    {service_key}: FOUND in ProxyList")
                        break
            
            if not found:
                print(f"    {service_key}: NOT FOUND in Lucky API data")

def main():
    """主函数"""
    print("Service Control Debug Tool")
    print("=" * 50)
    
    # 运行调试
    asyncio.run(debug_lucky_api_data())
    debug_service_control_mapping()
    
    print("\n" + "=" * 50)
    print("Debug completed!")
    print("\nRecommendations:")
    print("1. Check if service keys in service_control.json match Lucky API keys")
    print("2. Verify that Lucky API is returning expected data structure")
    print("3. Check if services are actually enabled in Lucky device")
    print("4. Review the debug_lucky_data.json file for detailed analysis")

if __name__ == "__main__":
    main()
