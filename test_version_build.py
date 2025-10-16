#!/usr/bin/env python3
"""
测试版本信息生成
模拟 Docker 构建过程中的版本信息生成
"""

import json
import os
import sys

print("=" * 60)
print("🔍 测试版本信息生成")
print("=" * 60)

try:
    # 导入版本模块
    from version import get_version_info
    
    # 获取版本信息
    version_info = get_version_info()
    
    print("\n✅ 版本信息获取成功:")
    print(f"   版本号: {version_info['version']}")
    print(f"   提交哈希: {version_info['commit_hash']}")
    print(f"   提交数量: {version_info['commit_count']}")
    print(f"   提交日期: {version_info['commit_date']}")
    print(f"   构建时间: {version_info['build_time']}")
    
    # 生成 JSON 文件（模拟 Docker 构建过程）
    json_file = "version_info.json"
    with open(json_file, 'w') as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 版本信息文件生成成功: {json_file}")
    
    # 读取并验证
    with open(json_file, 'r') as f:
        loaded_info = json.load(f)
    
    print("\n✅ 验证 JSON 文件内容:")
    print(json.dumps(loaded_info, indent=2, ensure_ascii=False))
    
    # 检查是否是开发版本
    if version_info['version'] == '2.0.0-dev':
        print("\n⚠️  警告: 当前版本是开发版本 (2.0.0-dev)")
        print("   这意味着:")
        print("   1. Git 可能不可用")
        print("   2. 或者不在 Git 仓库中")
        print("   3. 或者 .git 目录不存在")
    else:
        print(f"\n🎉 成功! 版本号: {version_info['version']}")
    
    # 清理测试文件
    if os.path.exists(json_file):
        response = input(f"\n是否删除测试文件 {json_file}? (y/n): ").lower()
        if response == 'y':
            os.remove(json_file)
            print(f"✅ 已删除 {json_file}")
    
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

