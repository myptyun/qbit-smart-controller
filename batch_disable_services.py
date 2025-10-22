#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量禁用服务的实用脚本
"""

import json
import os
import sys

def batch_disable_services():
    """批量禁用所有服务"""
    print("批量禁用服务工具")
    print("=" * 50)
    
    # 配置文件路径
    config_file = "data/config/service_control.json"
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"配置文件不存在: {config_file}")
        return False
    
    # 读取当前配置
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            current_config = json.load(f)
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return False
    
    print("当前配置:")
    for service, status in current_config.items():
        status_text = "启用" if status else "禁用"
        print(f"  {service}: {status_text}")
    
    # 获取所有服务列表
    all_services = list(current_config.keys())
    
    if not all_services:
        print("没有找到任何服务")
        return False
    
    print(f"\n找到 {len(all_services)} 个服务")
    
    # 询问用户确认
    print("\n选项:")
    print("1. 禁用所有服务")
    print("2. 启用所有服务")
    print("3. 选择性禁用（保留重要服务）")
    print("4. 退出")
    
    choice = input("\n请选择操作 (1-4): ").strip()
    
    if choice == "1":
        # 禁用所有服务
        new_config = {}
        for service in all_services:
            new_config[service] = False
        
        print("\n将禁用所有服务:")
        for service in new_config:
            print(f"  {service}: 禁用")
        
        confirm = input("\n确认执行吗? (y/N): ").strip().lower()
        if confirm == 'y':
            return save_config(config_file, new_config)
        else:
            print("操作已取消")
            return False
            
    elif choice == "2":
        # 启用所有服务
        new_config = {}
        for service in all_services:
            new_config[service] = True
        
        print("\n将启用所有服务:")
        for service in new_config:
            print(f"  {service}: 启用")
        
        confirm = input("\n确认执行吗? (y/N): ").strip().lower()
        if confirm == 'y':
            return save_config(config_file, new_config)
        else:
            print("操作已取消")
            return False
            
    elif choice == "3":
        # 选择性禁用
        print("\n请输入要保留启用的重要服务名称（用逗号分隔）:")
        print("例如: 数据库服务,缓存服务,监控服务")
        important_services_input = input("重要服务: ").strip()
        
        if important_services_input:
            important_services = [s.strip() for s in important_services_input.split(',')]
        else:
            important_services = []
        
        new_config = {}
        for service in all_services:
            if service in important_services:
                new_config[service] = True
            else:
                new_config[service] = False
        
        print("\n选择性禁用配置:")
        for service, status in new_config.items():
            status_text = "启用" if status else "禁用"
            print(f"  {service}: {status_text}")
        
        confirm = input("\n确认执行吗? (y/N): ").strip().lower()
        if confirm == 'y':
            return save_config(config_file, new_config)
        else:
            print("操作已取消")
            return False
            
    elif choice == "4":
        print("退出")
        return False
    else:
        print("无效选择")
        return False

def save_config(config_file, new_config):
    """保存配置到文件"""
    try:
        # 创建备份
        backup_file = config_file + ".backup"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(backup_content)
            print(f"已创建备份文件: {backup_file}")
        
        # 保存新配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
        
        print(f"配置已保存到: {config_file}")
        return True
        
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False

if __name__ == "__main__":
    success = batch_disable_services()
    if success:
        print("\n操作完成！")
    else:
        print("\n操作失败或已取消")
        sys.exit(1)
