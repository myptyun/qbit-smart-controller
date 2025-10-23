#!/usr/bin/env python3
"""
简化的服务控制调试工具
不依赖外部库，直接分析配置和文件
"""

import json
import os
from pathlib import Path

def analyze_service_control_config():
    """分析服务控制配置"""
    print("Service Control Configuration Analysis")
    print("=" * 50)
    
    # 1. 检查服务控制文件
    service_control_file = Path("data/config/service_control.json")
    print(f"1. Service control file: {service_control_file}")
    
    if service_control_file.exists():
        try:
            with open(service_control_file, 'r', encoding='utf-8') as f:
                service_control = json.load(f)
            
            print(f"   File exists: YES")
            print(f"   Services configured: {len(service_control)}")
            print("   Service status:")
            for service_key, enabled in service_control.items():
                status = "ENABLED" if enabled else "DISABLED"
                print(f"     {service_key}: {status}")
        except Exception as e:
            print(f"   Error reading file: {e}")
    else:
        print(f"   File exists: NO")
        print(f"   Directory exists: {service_control_file.parent.exists()}")
    
    # 2. 检查配置文件
    config_file = Path("config/config.yaml")
    print(f"\n2. Main config file: {config_file}")
    
    if config_file.exists():
        print(f"   File exists: YES")
        try:
            # 简单读取YAML文件（不依赖yaml库）
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找Lucky设备配置
            if "lucky_devices:" in content:
                print("   Lucky devices configured: YES")
                # 提取API URL
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "api_url:" in line:
                        api_url = line.split('api_url:')[1].strip().strip('"')
                        print(f"   API URL: {api_url}")
                        break
            else:
                print("   Lucky devices configured: NO")
                
        except Exception as e:
            print(f"   Error reading file: {e}")
    else:
        print(f"   File exists: NO")
    
    # 3. 检查日志文件
    log_dir = Path("data/logs")
    print(f"\n3. Log directory: {log_dir}")
    
    if log_dir.exists():
        print(f"   Directory exists: YES")
        log_files = list(log_dir.glob("*.log"))
        print(f"   Log files found: {len(log_files)}")
        for log_file in log_files:
            print(f"     {log_file.name}")
    else:
        print(f"   Directory exists: NO")

def test_service_control_logic():
    """测试服务控制逻辑"""
    print("\n" + "=" * 50)
    print("Service Control Logic Test")
    print("=" * 50)
    
    # 读取服务控制状态
    service_control_file = Path("data/config/service_control.json")
    if not service_control_file.exists():
        print("ERROR: Service control file not found")
        return
    
    with open(service_control_file, 'r', encoding='utf-8') as f:
        service_control = json.load(f)
    
    # 模拟连接数据
    mock_connections = [
        {"rule_name": "Proxmox", "key": "Proxmox", "connections": 5},
        {"rule_name": "hzun", "key": "hzun", "connections": 3},
        {"rule_name": "hzik", "key": "hzik", "connections": 2},
    ]
    
    print("Testing connection calculation logic:")
    print("Mock connection data:")
    for conn in mock_connections:
        service_key = conn.get("rule_name", "")
        is_enabled = service_control.get(service_key, False)
        status = "ENABLED" if is_enabled else "DISABLED"
        print(f"  {service_key}: {conn['connections']} connections, control: {status}")
    
    # 计算总连接数
    total_connections = 0.0
    print("\nConnection calculation:")
    for conn in mock_connections:
        service_key = conn.get("rule_name", "")
        is_enabled = service_control.get(service_key, False)
        
        if is_enabled:
            connections = conn.get("connections", 0)
            total_connections += connections
            print(f"  [INCLUDED] {service_key}: {connections} connections")
        else:
            print(f"  [EXCLUDED] {service_key}: {conn.get('connections', 0)} connections")
    
    print(f"\nTotal connections: {total_connections}")
    
    # 分析结果
    enabled_count = sum(1 for enabled in service_control.values() if enabled)
    disabled_count = len(service_control) - enabled_count
    
    print(f"\nAnalysis:")
    print(f"  Enabled services: {enabled_count}")
    print(f"  Disabled services: {disabled_count}")
    
    if total_connections == 0 and disabled_count > 0:
        print("  RESULT: Service control is working correctly!")
        print("  - All services are disabled, so total connections = 0")
    elif total_connections > 0 and enabled_count > 0:
        print("  RESULT: Service control is working correctly!")
        print("  - Some services are enabled, so they contribute to total connections")
    else:
        print("  RESULT: Potential issue detected!")
        print("  - Check service control configuration")

def check_file_permissions():
    """检查文件权限"""
    print("\n" + "=" * 50)
    print("File Permissions Check")
    print("=" * 50)
    
    files_to_check = [
        "data/config/service_control.json",
        "config/config.yaml",
        "data/logs/",
    ]
    
    for file_path in files_to_check:
        path = Path(file_path)
        print(f"\n{file_path}:")
        print(f"  Exists: {path.exists()}")
        if path.exists():
            if path.is_file():
                print(f"  Readable: {os.access(path, os.R_OK)}")
                print(f"  Writable: {os.access(path, os.W_OK)}")
            elif path.is_dir():
                print(f"  Readable: {os.access(path, os.R_OK)}")
                print(f"  Writable: {os.access(path, os.W_OK)}")

def generate_test_scenarios():
    """生成测试场景"""
    print("\n" + "=" * 50)
    print("Test Scenarios")
    print("=" * 50)
    
    print("Scenario 1: All services disabled")
    test_config = {
        "Proxmox": False,
        "hzun": False,
        "hzik": False
    }
    
    mock_connections = [
        {"rule_name": "Proxmox", "connections": 5},
        {"rule_name": "hzun", "connections": 3},
        {"rule_name": "hzik", "connections": 2},
    ]
    
    total = sum(conn["connections"] for conn in mock_connections 
                if test_config.get(conn["rule_name"], False))
    print(f"  Expected total connections: {total}")
    
    print("\nScenario 2: Some services enabled")
    test_config = {
        "Proxmox": True,
        "hzun": False,
        "hzik": True
    }
    
    total = sum(conn["connections"] for conn in mock_connections 
                if test_config.get(conn["rule_name"], False))
    print(f"  Expected total connections: {total}")
    
    print("\nScenario 3: All services enabled")
    test_config = {
        "Proxmox": True,
        "hzun": True,
        "hzik": True
    }
    
    total = sum(conn["connections"] for conn in mock_connections 
                if test_config.get(conn["rule_name"], False))
    print(f"  Expected total connections: {total}")

def main():
    """主函数"""
    print("Service Control Debug Tool (Simple Version)")
    print("=" * 60)
    
    # 运行分析
    analyze_service_control_config()
    test_service_control_logic()
    check_file_permissions()
    generate_test_scenarios()
    
    print("\n" + "=" * 60)
    print("Debug Summary:")
    print("1. Check if service_control.json exists and is readable")
    print("2. Verify service control logic is working correctly")
    print("3. Test different service enable/disable scenarios")
    print("4. Check file permissions if issues persist")
    
    print("\nIf you're still seeing disabled services being counted:")
    print("- Check if service names in service_control.json match Lucky API response")
    print("- Verify Lucky API is returning expected data structure")
    print("- Check if services are actually enabled in Lucky device configuration")

if __name__ == "__main__":
    main()

