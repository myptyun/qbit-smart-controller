#!/usr/bin/env python3
"""
自动版本管理模块
基于Git提交信息自动生成版本号
"""

import subprocess
import os
from datetime import datetime

def get_git_version():
    """获取基于Git的版本信息"""
    try:
        # 获取最新的提交hash（短版本）
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        # 获取提交数量
        commit_count = subprocess.check_output(
            ['git', 'rev-list', '--count', 'HEAD'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        # 获取最新提交的时间
        commit_date = subprocess.check_output(
            ['git', 'log', '-1', '--format=%cd', '--date=short'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        return {
            'commit_hash': commit_hash,
            'commit_count': int(commit_count),
            'commit_date': commit_date,
            'version': f"2.{commit_count}.{commit_hash}",
            'build_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        # 如果Git不可用，返回默认版本
        return {
            'commit_hash': 'unknown',
            'commit_count': 0,
            'commit_date': 'unknown',
            'version': '2.0.0-dev',
            'build_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def get_version_string():
    """获取完整的版本字符串"""
    version_info = get_git_version()
    return f"v{version_info['version']} (Build: {version_info['build_time']})"

def get_version_info():
    """获取版本信息字典"""
    return get_git_version()

if __name__ == "__main__":
    # 测试版本信息
    print("版本信息:")
    version_info = get_version_info()
    for key, value in version_info.items():
        print(f"  {key}: {value}")
    print(f"\n完整版本字符串: {get_version_string()}")
