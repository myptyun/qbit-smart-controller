#!/usr/bin/env python3
"""
检查服务名称匹配的简单工具
"""

import json
from pathlib import Path

def check_current_config():
    """检查当前配置"""
    print("CURRENT SERVICE CONTROL CONFIGURATION")
    print("=" * 50)
    
    service_control_file = Path("data/config/service_control.json")
    if not service_control_file.exists():
        print("ERROR: service_control.json not found")
        return
    
    with open(service_control_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("Service names in your configuration:")
    for service_name, enabled in config.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"  '{service_name}': {status}")
    
    print(f"\nTotal services configured: {len(config)}")
    enabled_count = sum(1 for enabled in config.values() if enabled)
    disabled_count = len(config) - enabled_count
    print(f"Enabled services: {enabled_count}")
    print(f"Disabled services: {disabled_count}")

def explain_matching_requirement():
    """解释匹配要求"""
    print("\n" + "=" * 50)
    print("SERVICE NAME MATCHING REQUIREMENT")
    print("=" * 50)
    
    print("For service control to work properly:")
    print("\n1. Lucky API must return data like this:")
    print("""
{
  "ProxyList": [
    {
      "Key": "Proxmox",     # This field name must match your config
      "Connections": 5,
      "WebServiceType": "proxy"
    }
  ]
}
""")
    
    print("2. Your config must have matching keys:")
    print("""
{
  "Proxmox": false,  # Must match Lucky API "Key" field exactly
  "hzun": true,      # Must match Lucky API "Key" field exactly
  "hzik": true       # Must match Lucky API "Key" field exactly
}
""")
    
    print("3. Matching rules:")
    print("   - Names must match EXACTLY (case sensitive)")
    print("   - No extra spaces, hyphens, or characters")
    print("   - 'Proxmox' matches 'Proxmox' [YES]")
    print("   - 'Proxmox' does NOT match 'proxmox' [NO]")
    print("   - 'Proxmox' does NOT match 'Proxmox-Proxy' [NO]")

def show_common_problems():
    """显示常见问题"""
    print("\n" + "=" * 50)
    print("COMMON MATCHING PROBLEMS")
    print("=" * 50)
    
    problems = [
        {
            "config_name": "Proxmox",
            "lucky_api_name": "proxmox",
            "issue": "Case mismatch (uppercase vs lowercase)"
        },
        {
            "config_name": "Proxmox",
            "lucky_api_name": "Proxmox-Proxy",
            "issue": "Extra suffix in Lucky API"
        },
        {
            "config_name": "Proxmox",
            "lucky_api_name": "Proxmox ",
            "issue": "Trailing space in Lucky API"
        },
        {
            "config_name": "Proxmox",
            "lucky_api_name": "proxmox-proxy",
            "issue": "Case mismatch + extra suffix"
        }
    ]
    
    for i, problem in enumerate(problems, 1):
        print(f"{i}. Config: '{problem['config_name']}'")
        print(f"   Lucky API: '{problem['lucky_api_name']}'")
        print(f"   Issue: {problem['issue']}")
        print(f"   Result: Service will be treated as DISABLED")
        print()

def provide_solution_steps():
    """提供解决步骤"""
    print("=" * 50)
    print("HOW TO FIX MATCHING ISSUES")
    print("=" * 50)
    
    print("Step 1: Check your Lucky device")
    print("  - Access your Lucky device web interface")
    print("  - Go to the services/proxies section")
    print("  - Note the exact service names shown there")
    
    print("\nStep 2: Compare with your config")
    print("  - Compare Lucky device service names with your config")
    print("  - Look for case differences, extra characters, etc.")
    
    print("\nStep 3: Update your configuration")
    print("  - Edit data/config/service_control.json")
    print("  - Make sure key names match Lucky device exactly")
    print("  - Save the file")
    
    print("\nStep 4: Test the changes")
    print("  - Restart your application")
    print("  - Check if disabled services are now properly excluded")
    
    print("\nStep 5: Verify with debug tools")
    print("  - Run: python verify_service_matching.py")
    print("  - Check the debug output for any remaining mismatches")

def main():
    """主函数"""
    check_current_config()
    explain_matching_requirement()
    show_common_problems()
    provide_solution_steps()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print("The key issue is that service names in your config file")
    print("must match the 'Key' field from Lucky API response EXACTLY.")
    print("\nIf they don't match, the system can't find the control setting")
    print("and will treat the service as disabled (which is correct behavior).")
    print("\nBut if you're seeing disabled services still being counted,")
    print("it means the names don't match, so the system can't apply")
    print("the disable setting properly.")

if __name__ == "__main__":
    main()
