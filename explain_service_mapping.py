#!/usr/bin/env python3
"""
详细解释Lucky API服务名称与配置键名的关联机制
"""

import json
from pathlib import Path

def explain_service_mapping_mechanism():
    """解释服务映射机制"""
    print("=" * 80)
    print("LUCKY API 服务名称与配置键名关联机制详解")
    print("=" * 80)
    
    print("\n1. 数据流程概述")
    print("-" * 50)
    print("Lucky API -> 解析服务信息 -> 服务发现 -> 状态控制 -> 连接数计算")
    print("    ↓              ↓           ↓         ↓         ↓")
    print("原始数据      详细连接信息    新服务检测   启用/禁用   总连接数")
    
    print("\n2. Lucky API 数据结构")
    print("-" * 50)
    print("Lucky API 可能返回以下数据结构之一：")
    print("\n结构1: ProxyList")
    print("""
{
  "ProxyList": [
    {
      "Key": "Proxmox",           # 服务标识符
      "Connections": 5,           # 连接数
      "WebServiceType": "proxy",  # 服务类型
      "Enable": true,             # Lucky中的启用状态
      "Locations": ["/path1"]     # 路径信息
    },
    {
      "Key": "hzun",
      "Connections": 3,
      "WebServiceType": "proxy",
      "Enable": true,
      "Locations": ["/path2"]
    }
  ]
}
""")
    
    print("结构2: statistics")
    print("""
{
  "statistics": {
    "Proxmox": {
      "Connections": 5,
      "DownloadBytes": 1024,
      "UploadBytes": 512
    },
    "hzun": {
      "Connections": 3,
      "DownloadBytes": 2048,
      "UploadBytes": 1024
    }
  }
}
""")
    
    print("结构3: ruleList")
    print("""
{
  "ruleList": [
    {
      "RuleName": "Proxmox",      # 规则名称
      "RuleKey": "Proxmox",       # 规则键
      "Connections": 5,
      "ProxyList": [
        {
          "Key": "Proxmox",
          "Connections": 5
        }
      ]
    }
  ]
}
""")
    
    print("\n3. 服务名称提取逻辑")
    print("-" * 50)
    print("代码中的服务名称提取逻辑：")
    print("""
# 在 _parse_detailed_connections 方法中：
for proxy in data["ProxyList"]:
    service_key = proxy.get("Key", "")  # 提取 Key 字段作为服务标识符
    connections_info.append({
        "rule_name": service_key,  # 使用 Key 作为 rule_name
        "key": service_key,        # 同时保存为 key
        "connections": connections,
        ...
    })
""")
    
    print("\n4. 服务发现机制")
    print("-" * 50)
    print("当检测到新服务时的处理逻辑：")
    print("""
# 在 discover_and_initialize_services 方法中：
for service in detected_services:
    service_key = service.get("rule_name") or service.get("key", "")
    if service_key and service_key not in self._service_control_state:
        # 新服务默认禁用（避免意外触发限速）
        self._service_control_state[service_key] = False
        new_services.append(service_key)
""")
    
    print("\n5. 状态控制关联")
    print("-" * 50)
    print("服务控制状态的存储和检索：")
    print("""
# 存储位置：data/config/service_control.json
{
  "Proxmox": false,  # 禁用状态
  "hzun": true,      # 启用状态
  "hzik": true       # 启用状态
}

# 检索逻辑：
def get_service_control_status(self, service_key: str) -> bool:
    if service_key in self._service_control_state:
        return self._service_control_state[service_key]
    return False  # 新服务默认禁用
""")
    
    print("\n6. 连接数计算中的关联")
    print("-" * 50)
    print("在计算总连接数时的关联逻辑：")
    print("""
# 在 _collect_total_connections 方法中：
for conn in detailed_connections:
    service_key = conn.get("rule_name", "")      # 从Lucky API数据中获取
    service_key_alt = conn.get("key", "")
    service_name = service_key or service_key_alt
    
    # 使用服务键名查询控制状态
    is_service_enabled = self.config_manager.get_service_control_status(service_key or service_key_alt)
    
    if is_service_enabled:
        device_connections += conn.get("connections", 0)  # 计入总连接数
    else:
        # 忽略该服务的连接数
""")

def demonstrate_mapping_examples():
    """演示映射示例"""
    print("\n7. 实际映射示例")
    print("-" * 50)
    
    # 模拟Lucky API数据
    lucky_api_data = {
        "ProxyList": [
            {"Key": "Proxmox", "Connections": 5},
            {"Key": "hzun", "Connections": 3},
            {"Key": "hzik", "Connections": 2},
            {"Key": "NewService", "Connections": 1}  # 新服务
        ]
    }
    
    # 当前服务控制配置
    service_control = {
        "Proxmox": False,  # 禁用
        "hzun": True,      # 启用
        "hzik": True,      # 启用
        # "NewService" 不在配置中，将被默认禁用
    }
    
    print("Lucky API 返回的数据：")
    for proxy in lucky_api_data["ProxyList"]:
        print(f"  {proxy['Key']}: {proxy['Connections']} connections")
    
    print(f"\n当前服务控制配置：")
    for service_key, enabled in service_control.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"  {service_key}: {status}")
    
    print(f"\n连接数计算过程：")
    total_connections = 0.0
    
    for proxy in lucky_api_data["ProxyList"]:
        service_key = proxy["Key"]
        connections = proxy["Connections"]
        
        # 检查服务控制状态
        is_enabled = service_control.get(service_key, False)  # 新服务默认False
        
        if is_enabled:
            total_connections += connections
            print(f"  [INCLUDED] {service_key}: {connections} connections")
        else:
            print(f"  [EXCLUDED] {service_key}: {connections} connections")
    
    print(f"\n总连接数: {total_connections}")

def explain_key_matching():
    """解释键名匹配机制"""
    print("\n8. 键名匹配机制详解")
    print("-" * 50)
    
    print("关键匹配点：")
    print("1. Lucky API 的 'Key' 字段 -> 服务控制配置的键名")
    print("2. 必须完全匹配（区分大小写）")
    print("3. 新服务会自动添加到配置中，默认禁用")
    
    print("\n匹配示例：")
    examples = [
        {
            "lucky_key": "Proxmox",
            "config_key": "Proxmox",
            "match": True,
            "note": "完全匹配"
        },
        {
            "lucky_key": "proxmox",
            "config_key": "Proxmox",
            "match": False,
            "note": "大小写不匹配"
        },
        {
            "lucky_key": "Proxmox-Proxy",
            "config_key": "Proxmox",
            "match": False,
            "note": "名称不匹配"
        },
        {
            "lucky_key": "NewService",
            "config_key": None,
            "match": False,
            "note": "新服务，不在配置中，默认禁用"
        }
    ]
    
    for example in examples:
        print(f"  Lucky Key: '{example['lucky_key']}'")
        print(f"  Config Key: '{example['config_key']}'")
        print(f"  Match: {example['match']} - {example['note']}")
        print()

def explain_troubleshooting():
    """解释故障排除"""
    print("\n9. 常见问题及解决方案")
    print("-" * 50)
    
    problems = [
        {
            "problem": "禁用状态的服务仍被计入连接数",
            "causes": [
                "Lucky API返回的服务名称与配置中的键名不匹配",
                "服务控制配置没有正确保存",
                "应用缓存问题",
                "多个应用实例运行"
            ],
            "solutions": [
                "检查Lucky API返回的实际服务名称",
                "确保配置文件中键名完全匹配",
                "重启应用清除缓存",
                "检查是否有多个实例在运行"
            ]
        },
        {
            "problem": "新服务没有被自动发现",
            "causes": [
                "Lucky API连接失败",
                "数据解析错误",
                "服务发现逻辑未执行"
            ],
            "solutions": [
                "检查Lucky API连接状态",
                "查看应用日志中的错误信息",
                "手动添加新服务到配置"
            ]
        }
    ]
    
    for i, problem in enumerate(problems, 1):
        print(f"{i}. {problem['problem']}")
        print("   可能原因：")
        for cause in problem['causes']:
            print(f"     - {cause}")
        print("   解决方案：")
        for solution in problem['solutions']:
            print(f"     - {solution}")
        print()

def main():
    """主函数"""
    explain_service_mapping_mechanism()
    demonstrate_mapping_examples()
    explain_key_matching()
    explain_troubleshooting()
    
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    print("服务名称与配置键名的关联是通过以下步骤实现的：")
    print("1. Lucky API返回服务数据，包含'Key'字段")
    print("2. 系统提取'Key'字段作为服务标识符")
    print("3. 新服务自动添加到服务控制配置，默认禁用")
    print("4. 连接数计算时，通过服务标识符查询控制状态")
    print("5. 只有启用状态的服务才会计入总连接数")
    print("\n关键点：服务名称必须完全匹配（区分大小写）")

if __name__ == "__main__":
    main()
