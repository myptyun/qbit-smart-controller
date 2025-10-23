#!/usr/bin/env python3
"""
验证服务名称匹配工具
检查Lucky API返回的服务名称与service_control.json中的键名是否完全匹配
"""

import json
import urllib.request
import urllib.error
from pathlib import Path

def load_service_control_config():
    """加载服务控制配置"""
    service_control_file = Path("data/config/service_control.json")
    if not service_control_file.exists():
        print("ERROR: service_control.json not found")
        return {}
    
    with open(service_control_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_lucky_api_url():
    """获取Lucky API URL"""
    config_file = Path("config/config.yaml")
    if not config_file.exists():
        print("ERROR: config.yaml not found")
        return None
    
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    for line in lines:
        if 'api_url:' in line:
            api_url = line.split('api_url:')[1].strip().strip('"')
            return api_url
    
    return None

def fetch_lucky_api_data():
    """获取Lucky API数据"""
    api_url = get_lucky_api_url()
    if not api_url:
        print("ERROR: Could not find Lucky API URL in config")
        return None
    
    print(f"Fetching data from: {api_url}")
    
    try:
        with urllib.request.urlopen(api_url, timeout=10) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
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

def extract_service_keys_from_lucky_data(lucky_data):
    """从Lucky API数据中提取服务键名"""
    service_keys = set()
    
    if not lucky_data:
        return service_keys
    
    # 从ProxyList提取
    if "ProxyList" in lucky_data and isinstance(lucky_data["ProxyList"], list):
        for proxy in lucky_data["ProxyList"]:
            key = proxy.get("Key", "")
            if key:
                service_keys.add(key)
                print(f"  Found in ProxyList: '{key}'")
    
    # 从statistics提取
    if "statistics" in lucky_data and isinstance(lucky_data["statistics"], dict):
        for key in lucky_data["statistics"].keys():
            service_keys.add(key)
            print(f"  Found in statistics: '{key}'")
    
    # 从ruleList提取
    if "ruleList" in lucky_data and isinstance(lucky_data["ruleList"], list):
        for rule in lucky_data["ruleList"]:
            # 提取RuleName
            rule_name = rule.get("RuleName", "")
            if rule_name:
                service_keys.add(rule_name)
                print(f"  Found in ruleList.RuleName: '{rule_name}'")
            
            # 提取RuleKey
            rule_key = rule.get("RuleKey", "")
            if rule_key:
                service_keys.add(rule_key)
                print(f"  Found in ruleList.RuleKey: '{rule_key}'")
            
            # 从ProxyList中提取
            if "ProxyList" in rule and isinstance(rule["ProxyList"], list):
                for proxy in rule["ProxyList"]:
                    key = proxy.get("Key", "")
                    if key:
                        service_keys.add(key)
                        print(f"  Found in ruleList.ProxyList: '{key}'")
    
    return service_keys

def verify_service_matching():
    """验证服务名称匹配"""
    print("=" * 80)
    print("SERVICE NAME MATCHING VERIFICATION")
    print("=" * 80)
    
    # 1. 加载服务控制配置
    print("\n1. Loading service control configuration...")
    service_control = load_service_control_config()
    
    if not service_control:
        print("ERROR: No service control configuration found")
        return
    
    print("Current service control configuration:")
    for service_key, enabled in service_control.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"  '{service_key}': {status}")
    
    # 2. 获取Lucky API数据
    print("\n2. Fetching Lucky API data...")
    lucky_data = fetch_lucky_api_data()
    
    if not lucky_data:
        print("ERROR: Could not fetch Lucky API data")
        print("This could be due to:")
        print("  - Lucky device not running")
        print("  - Incorrect API URL")
        print("  - Network connectivity issues")
        print("  - Invalid API token")
        return
    
    # 保存原始数据用于分析
    debug_file = Path("lucky_api_debug.json")
    with open(debug_file, 'w', encoding='utf-8') as f:
        json.dump(lucky_data, f, indent=2, ensure_ascii=False)
    print(f"Lucky API data saved to: {debug_file}")
    
    # 3. 提取Lucky API中的服务键名
    print("\n3. Extracting service keys from Lucky API data...")
    lucky_service_keys = extract_service_keys_from_lucky_data(lucky_data)
    
    print(f"\nLucky API service keys found:")
    for key in sorted(lucky_service_keys):
        print(f"  '{key}'")
    
    # 4. 比较配置键名和Lucky API键名
    print("\n4. Comparing configuration keys with Lucky API keys...")
    config_keys = set(service_control.keys())
    
    print(f"\nConfiguration keys: {sorted(config_keys)}")
    print(f"Lucky API keys: {sorted(lucky_service_keys)}")
    
    # 5. 分析匹配情况
    print("\n5. Matching analysis:")
    
    # 完全匹配的键
    exact_matches = config_keys & lucky_service_keys
    print(f"\nExact matches ({len(exact_matches)}):")
    for key in sorted(exact_matches):
        status = "ENABLED" if service_control[key] else "DISABLED"
        print(f"  '{key}': {status} ✓")
    
    # 配置中存在但Lucky API中不存在的键
    config_only = config_keys - lucky_service_keys
    print(f"\nIn config but NOT in Lucky API ({len(config_only)}):")
    for key in sorted(config_only):
        status = "ENABLED" if service_control[key] else "DISABLED"
        print(f"  '{key}': {status} ❌ (NOT FOUND in Lucky API)")
    
    # Lucky API中存在但配置中不存在的键
    lucky_only = lucky_service_keys - config_keys
    print(f"\nIn Lucky API but NOT in config ({len(lucky_only)}):")
    for key in sorted(lucky_only):
        print(f"  '{key}': ❌ (NOT CONFIGURED - will be default DISABLED)")
    
    # 6. 生成修复建议
    print("\n6. Fix recommendations:")
    
    if config_only:
        print(f"\n⚠️  MISMATCH DETECTED:")
        print(f"   The following services are configured but not found in Lucky API:")
        for key in sorted(config_only):
            print(f"     - '{key}'")
        print(f"   These services will be ignored (treated as disabled)")
    
    if lucky_only:
        print(f"\n🆕 NEW SERVICES DETECTED:")
        print(f"   The following services are in Lucky API but not configured:")
        for key in sorted(lucky_only):
            print(f"     - '{key}'")
        print(f"   These services will be automatically added to config as DISABLED")
    
    if not exact_matches:
        print(f"\n❌ CRITICAL ISSUE:")
        print(f"   NO services match between config and Lucky API!")
        print(f"   This means ALL services will be treated as disabled")
        print(f"   Check service names carefully for typos or case differences")
    
    # 7. 生成修复后的配置
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
    
    # 8. 保存修复后的配置
    if corrected_config != service_control:
        print(f"\n8. Saving corrected configuration...")
        backup_file = Path("data/config/service_control.json.backup")
        
        # 备份原配置
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(service_control, f, indent=2, ensure_ascii=False)
        print(f"Original config backed up to: {backup_file}")
        
        # 保存修复后的配置
        with open(Path("data/config/service_control.json"), 'w', encoding='utf-8') as f:
            json.dump(corrected_config, f, indent=2, ensure_ascii=False)
        print(f"Corrected config saved to: data/config/service_control.json")
        
        print(f"\n✅ Configuration has been corrected!")
        print(f"   - Removed {len(config_only)} mismatched services")
        print(f"   - Added {len(lucky_only)} new services (default disabled)")
        print(f"   - Kept {len(exact_matches)} matching services")
    else:
        print(f"\n✅ Configuration is already correct!")

def main():
    """主函数"""
    verify_service_matching()
    
    print("\n" + "=" * 80)
    print("IMPORTANT NOTES:")
    print("=" * 80)
    print("1. Service names must match EXACTLY (case sensitive)")
    print("2. Lucky API 'Key' field must match config key names")
    print("3. New services are automatically added as DISABLED")
    print("4. Mismatched services are ignored (treated as disabled)")
    print("5. Check the debug file 'lucky_api_debug.json' for detailed API response")

if __name__ == "__main__":
    main()
