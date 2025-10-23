#!/usr/bin/env python3
"""
Service Mapping Explanation - How Lucky API service names are linked to control switches
"""

import json
from pathlib import Path

def explain_service_mapping():
    """Explain how service mapping works"""
    print("=" * 80)
    print("LUCKY API SERVICE NAME TO CONFIG KEY MAPPING EXPLANATION")
    print("=" * 80)
    
    print("\n1. DATA FLOW OVERVIEW")
    print("-" * 50)
    print("Lucky API -> Parse Service Info -> Service Discovery -> State Control -> Connection Count")
    print("    |              |               |              |              |")
    print("Raw Data    Detailed Connections  New Service   Enable/Disable  Total Count")
    print("            Info                  Detection     Switch          Calculation")
    
    print("\n2. LUCKY API DATA STRUCTURES")
    print("-" * 50)
    print("Lucky API can return different data structures:")
    
    print("\nStructure 1: ProxyList")
    print("""
{
  "ProxyList": [
    {
      "Key": "Proxmox",           # Service identifier
      "Connections": 5,           # Connection count
      "WebServiceType": "proxy",  # Service type
      "Enable": true,             # Enable status in Lucky
      "Locations": ["/path1"]     # Path information
    }
  ]
}
""")
    
    print("Structure 2: statistics")
    print("""
{
  "statistics": {
    "Proxmox": {
      "Connections": 5,
      "DownloadBytes": 1024,
      "UploadBytes": 512
    }
  }
}
""")
    
    print("\n3. SERVICE NAME EXTRACTION LOGIC")
    print("-" * 50)
    print("How the system extracts service names from Lucky API:")
    print("""
# In _parse_detailed_connections method:
for proxy in data["ProxyList"]:
    service_key = proxy.get("Key", "")  # Extract Key field as service identifier
    connections_info.append({
        "rule_name": service_key,  # Use Key as rule_name
        "key": service_key,        # Also save as key
        "connections": connections,
        ...
    })
""")
    
    print("\n4. SERVICE DISCOVERY MECHANISM")
    print("-" * 50)
    print("How new services are discovered and initialized:")
    print("""
# In discover_and_initialize_services method:
for service in detected_services:
    service_key = service.get("rule_name") or service.get("key", "")
    if service_key and service_key not in self._service_control_state:
        # New services default to DISABLED (to avoid accidental speed limiting)
        self._service_control_state[service_key] = False
        new_services.append(service_key)
""")
    
    print("\n5. STATE CONTROL ASSOCIATION")
    print("-" * 50)
    print("How service control states are stored and retrieved:")
    print("""
# Storage location: data/config/service_control.json
{
  "Proxmox": false,  # Disabled state
  "hzun": true,      # Enabled state
  "hzik": true       # Enabled state
}

# Retrieval logic:
def get_service_control_status(self, service_key: str) -> bool:
    if service_key in self._service_control_state:
        return self._service_control_state[service_key]
    return False  # New services default to disabled
""")
    
    print("\n6. CONNECTION COUNT CALCULATION ASSOCIATION")
    print("-" * 50)
    print("How services are linked during connection count calculation:")
    print("""
# In _collect_total_connections method:
for conn in detailed_connections:
    service_key = conn.get("rule_name", "")      # Get from Lucky API data
    service_key_alt = conn.get("key", "")
    service_name = service_key or service_key_alt
    
    # Query control state using service key
    is_service_enabled = self.config_manager.get_service_control_status(service_key or service_key_alt)
    
    if is_service_enabled:
        device_connections += conn.get("connections", 0)  # Include in total
    else:
        # Ignore this service's connection count
""")

def demonstrate_mapping_examples():
    """Demonstrate mapping examples"""
    print("\n7. PRACTICAL MAPPING EXAMPLES")
    print("-" * 50)
    
    # Simulate Lucky API data
    lucky_api_data = {
        "ProxyList": [
            {"Key": "Proxmox", "Connections": 5},
            {"Key": "hzun", "Connections": 3},
            {"Key": "hzik", "Connections": 2},
            {"Key": "NewService", "Connections": 1}  # New service
        ]
    }
    
    # Current service control configuration
    service_control = {
        "Proxmox": False,  # Disabled
        "hzun": True,      # Enabled
        "hzik": True,      # Enabled
        # "NewService" not in config, will be default disabled
    }
    
    print("Lucky API returned data:")
    for proxy in lucky_api_data["ProxyList"]:
        print(f"  {proxy['Key']}: {proxy['Connections']} connections")
    
    print(f"\nCurrent service control configuration:")
    for service_key, enabled in service_control.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"  {service_key}: {status}")
    
    print(f"\nConnection count calculation process:")
    total_connections = 0.0
    
    for proxy in lucky_api_data["ProxyList"]:
        service_key = proxy["Key"]
        connections = proxy["Connections"]
        
        # Check service control state
        is_enabled = service_control.get(service_key, False)  # New services default False
        
        if is_enabled:
            total_connections += connections
            print(f"  [INCLUDED] {service_key}: {connections} connections")
        else:
            print(f"  [EXCLUDED] {service_key}: {connections} connections")
    
    print(f"\nTotal connections: {total_connections}")

def explain_key_matching():
    """Explain key matching mechanism"""
    print("\n8. KEY MATCHING MECHANISM")
    print("-" * 50)
    
    print("Key matching points:")
    print("1. Lucky API 'Key' field -> Service control config key name")
    print("2. Must match exactly (case sensitive)")
    print("3. New services are automatically added to config, default disabled")
    
    print("\nMatching examples:")
    examples = [
        {
            "lucky_key": "Proxmox",
            "config_key": "Proxmox",
            "match": True,
            "note": "Exact match"
        },
        {
            "lucky_key": "proxmox",
            "config_key": "Proxmox",
            "match": False,
            "note": "Case mismatch"
        },
        {
            "lucky_key": "Proxmox-Proxy",
            "config_key": "Proxmox",
            "match": False,
            "note": "Name mismatch"
        },
        {
            "lucky_key": "NewService",
            "config_key": None,
            "match": False,
            "note": "New service, not in config, default disabled"
        }
    ]
    
    for example in examples:
        print(f"  Lucky Key: '{example['lucky_key']}'")
        print(f"  Config Key: '{example['config_key']}'")
        print(f"  Match: {example['match']} - {example['note']}")
        print()

def explain_troubleshooting():
    """Explain troubleshooting"""
    print("\n9. COMMON ISSUES AND SOLUTIONS")
    print("-" * 50)
    
    problems = [
        {
            "problem": "Disabled services still being counted in connection total",
            "causes": [
                "Service names from Lucky API don't match config key names",
                "Service control config not saved properly",
                "Application cache issues",
                "Multiple application instances running"
            ],
            "solutions": [
                "Check actual service names returned by Lucky API",
                "Ensure key names in config file match exactly",
                "Restart application to clear cache",
                "Check if multiple instances are running"
            ]
        },
        {
            "problem": "New services not being auto-discovered",
            "causes": [
                "Lucky API connection failure",
                "Data parsing errors",
                "Service discovery logic not executed"
            ],
            "solutions": [
                "Check Lucky API connection status",
                "Check application logs for error messages",
                "Manually add new services to config"
            ]
        }
    ]
    
    for i, problem in enumerate(problems, 1):
        print(f"{i}. {problem['problem']}")
        print("   Possible causes:")
        for cause in problem['causes']:
            print(f"     - {cause}")
        print("   Solutions:")
        for solution in problem['solutions']:
            print(f"     - {solution}")
        print()

def show_current_config():
    """Show current configuration"""
    print("\n10. CURRENT CONFIGURATION STATUS")
    print("-" * 50)
    
    service_control_file = Path("data/config/service_control.json")
    if service_control_file.exists():
        with open(service_control_file, 'r', encoding='utf-8') as f:
            service_control = json.load(f)
        
        print("Current service control configuration:")
        for service_key, enabled in service_control.items():
            status = "ENABLED" if enabled else "DISABLED"
            print(f"  {service_key}: {status}")
        
        enabled_count = sum(1 for enabled in service_control.values() if enabled)
        disabled_count = len(service_control) - enabled_count
        
        print(f"\nSummary:")
        print(f"  Total services: {len(service_control)}")
        print(f"  Enabled services: {enabled_count}")
        print(f"  Disabled services: {disabled_count}")
    else:
        print("Service control file not found")

def main():
    """Main function"""
    explain_service_mapping()
    demonstrate_mapping_examples()
    explain_key_matching()
    explain_troubleshooting()
    show_current_config()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("Service name to config key association works through these steps:")
    print("1. Lucky API returns service data with 'Key' field")
    print("2. System extracts 'Key' field as service identifier")
    print("3. New services automatically added to control config, default disabled")
    print("4. During connection count calculation, control state queried by service identifier")
    print("5. Only enabled services contribute to total connection count")
    print("\nKey point: Service names must match exactly (case sensitive)")

if __name__ == "__main__":
    main()
