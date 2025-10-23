#!/usr/bin/env python3
"""
测试API端点的服务控制功能
"""

import json
import requests
import time
from pathlib import Path

def test_service_control_api():
    """测试服务控制API"""
    base_url = "http://localhost:5000"
    
    print("Testing Service Control API Endpoints")
    print("=" * 50)
    
    # 1. 测试获取服务控制状态
    print("\n1. Testing GET /api/lucky/service-control")
    try:
        response = requests.get(f"{base_url}/api/lucky/service-control", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("  SUCCESS: Retrieved service control status")
            service_control = data.get("service_control", {})
            print(f"  Services configured: {len(service_control)}")
            for service_key, enabled in service_control.items():
                status = "ENABLED" if enabled else "DISABLED"
                print(f"    {service_key}: {status}")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")
    
    # 2. 测试设置服务控制状态
    print("\n2. Testing POST /api/lucky/service-control")
    try:
        # 启用 Proxmox 服务
        payload = {
            "service_key": "Proxmox",
            "enabled": True
        }
        response = requests.post(f"{base_url}/api/lucky/service-control", 
                               json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("  SUCCESS: Set Proxmox to ENABLED")
            print(f"  Message: {data.get('message', '')}")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")
    
    # 3. 再次获取状态验证
    print("\n3. Verifying status change")
    try:
        response = requests.get(f"{base_url}/api/lucky/service-control", timeout=5)
        if response.status_code == 200:
            data = response.json()
            service_control = data.get("service_control", {})
            proxmox_status = service_control.get("Proxmox", False)
            status = "ENABLED" if proxmox_status else "DISABLED"
            print(f"  Proxmox status: {status}")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")
    
    # 4. 测试批量设置
    print("\n4. Testing batch service control")
    try:
        payload = {
            "service_controls": {
                "hzun": True,
                "hzik": True
            }
        }
        response = requests.put(f"{base_url}/api/lucky/service-control/batch", 
                              json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("  SUCCESS: Batch update completed")
            print(f"  Message: {data.get('message', '')}")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")
    
    # 5. 最终状态检查
    print("\n5. Final status check")
    try:
        response = requests.get(f"{base_url}/api/lucky/service-control", timeout=5)
        if response.status_code == 200:
            data = response.json()
            service_control = data.get("service_control", {})
            print("  Final service control status:")
            for service_key, enabled in service_control.items():
                status = "ENABLED" if enabled else "DISABLED"
                print(f"    {service_key}: {status}")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")

def test_controller_state():
    """测试控制器状态"""
    base_url = "http://localhost:5000"
    
    print("\n" + "=" * 50)
    print("Testing Controller State")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/controller/state", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("  SUCCESS: Retrieved controller state")
            print(f"  Running: {data.get('running', False)}")
            print(f"  Limited: {data.get('is_limited', False)}")
            print(f"  Total connections: {data.get('total_connections', 0)}")
            print(f"  Status: {data.get('status', 'Unknown')}")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")

def test_lucky_connections():
    """测试Lucky连接信息"""
    base_url = "http://localhost:5000"
    
    print("\n" + "=" * 50)
    print("Testing Lucky Connections")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/lucky/connections", timeout=10)
        if response.status_code == 200:
            data = response.json()
            devices = data.get("devices", [])
            print(f"  SUCCESS: Retrieved {len(devices)} device(s)")
            
            for device in devices:
                device_name = device.get("device_name", "Unknown")
                success = device.get("success", False)
                connections = device.get("connections", [])
                total_connections = device.get("total_connections", 0)
                
                print(f"    Device: {device_name}")
                print(f"    Success: {success}")
                print(f"    Total connections: {total_connections}")
                print(f"    Services: {len(connections)}")
                
                for conn in connections:
                    service_name = conn.get("rule_name", "Unknown")
                    conn_count = conn.get("connections", 0)
                    print(f"      {service_name}: {conn_count} connections")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")

def main():
    """主函数"""
    print("API Endpoint Test Tool")
    print("=" * 50)
    
    # 检查服务器是否运行
    try:
        response = requests.get("http://localhost:5000/health", timeout=3)
        if response.status_code == 200:
            print("Server is running, starting tests...")
        else:
            print("Server responded but with error status")
    except requests.exceptions.RequestException:
        print("ERROR: Server is not running or not accessible")
        print("Please start the server first with: python -m uvicorn app.main:app --host 0.0.0.0 --port 5000")
        return
    
    # 运行测试
    test_service_control_api()
    test_controller_state()
    test_lucky_connections()
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main()

