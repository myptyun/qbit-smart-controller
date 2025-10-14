import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

class LuckyMonitor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.session = None
    
    async def get_session(self):
        """获取aiohttp会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def test_lucky_connection(self, api_url: str) -> Dict[str, Any]:
        """测试Lucky设备连接"""
        try:
            session = await self.get_session()
            async with session.get(api_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "status": "connected",
                        "data": data,
                        "message": "连接成功"
                    }
                else:
                    return {
                        "success": False,
                        "status": "error",
                        "message": f"HTTP错误: {response.status}"
                    }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "status": "timeout",
                "message": "连接超时"
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"连接失败: {str(e)}"
            }
    
    async def get_device_connections(self, device_config: Dict[str, Any]) -> Dict[str, Any]:
        """获取设备连接数"""
        try:
            session = await self.get_session()
            api_url = device_config["api_url"]
            
            async with session.get(api_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 解析Lucky API响应，提取连接数
                    # 这里需要根据实际的Lucky API响应结构进行调整
                    connections = self._parse_connections(data, device_config)
                    weighted_connections = connections * device_config.get("weight", 1.0)
                    
                    return {
                        "success": True,
                        "device_name": device_config["name"],
                        "connections": connections,
                        "weighted_connections": weighted_connections,
                        "last_update": datetime.now().isoformat(),
                        "raw_data": data
                    }
                else:
                    return {
                        "success": False,
                        "device_name": device_config["name"],
                        "connections": 0,
                        "weighted_connections": 0,
                        "error": f"HTTP {response.status}",
                        "last_update": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "success": False,
                "device_name": device_config["name"],
                "connections": 0,
                "weighted_connections": 0,
                "error": str(e),
                "last_update": datetime.now().isoformat()
            }
    
    def _parse_connections(self, data: Dict, device_config: Dict) -> int:
        """解析Lucky API响应，提取连接数"""
        # 根据您提供的Lucky API实际响应结构来实现
        # 这里是一个示例实现，您需要根据实际情况调整
        try:
            # 假设响应中有rules字段，每个rule可能有连接数
            if "rules" in data:
                total_connections = 0
                for rule in data["rules"]:
                    # 根据实际API响应结构调整这个解析逻辑
                    if "connections" in rule:
                        total_connections += rule["connections"]
                return total_connections
            return 0
        except:
            return 0
    
    async def collect_all_devices_status(self) -> List[Dict]:
        """收集所有设备状态"""
        config = self.config_manager.load_config()
        tasks = []
        
        for device in config.get("lucky_devices", []):
            if device.get("enabled", True):
                tasks.append(self.get_device_connections(device))
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()