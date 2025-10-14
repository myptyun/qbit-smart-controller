import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

class QBittorrentManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.sessions = {}  # 存储每个实例的会话
    
    async def get_session(self, instance_name: str) -> Optional[aiohttp.ClientSession]:
        """获取指定实例的会话"""
        if instance_name not in self.sessions:
            self.sessions[instance_name] = aiohttp.ClientSession()
        return self.sessions[instance_name]
    
    async def test_qbit_connection(self, instance_config: Dict[str, Any]) -> Dict[str, Any]:
        """测试qBittorrent连接"""
        try:
            session = aiohttp.ClientSession()
            
            # 登录
            login_data = {
                "username": instance_config["username"],
                "password": instance_config["password"]
            }
            
            login_url = f"{instance_config['host']}/api/v2/auth/login"
            async with session.post(login_url, data=login_data, timeout=10) as response:
                if response.status == 200:
                    # 获取传输信息测试
                    transfer_url = f"{instance_config['host']}/api/v2/transfer/info"
                    async with session.get(transfer_url, timeout=10) as transfer_response:
                        if transfer_response.status == 200:
                            result = {
                                "success": True,
                                "status": "connected",
                                "message": "连接成功"
                            }
                        else:
                            result = {
                                "success": False,
                                "status": "error",
                                "message": f"传输信息获取失败: {transfer_response.status}"
                            }
                else:
                    result = {
                        "success": False,
                        "status": "auth_failed",
                        "message": f"认证失败: {response.status}"
                    }
            
            await session.close()
            return result
            
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"连接测试失败: {str(e)}"
            }
    
    async def get_qbit_status(self, instance_config: Dict[str, Any]) -> Dict[str, Any]:
        """获取qBittorrent实例状态"""
        try:
            session = aiohttp.ClientSession()
            
            # 登录
            login_data = {
                "username": instance_config["username"],
                "password": instance_config["password"]
            }
            
            login_url = f"{instance_config['host']}/api/v2/auth/login"
            async with session.post(login_url, data=login_data, timeout=10) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "instance_name": instance_config["name"],
                        "status": "auth_failed",
                        "last_online": None,
                        "error": "认证失败"
                    }
                
                # 获取传输信息
                transfer_url = f"{instance_config['host']}/api/v2/transfer/info"
                async with session.get(transfer_url, timeout=10) as transfer_response:
                    if transfer_response.status == 200:
                        transfer_info = await transfer_response.json()
                        
                        # 获取torrent列表
                        torrents_url = f"{instance_config['host']}/api/v2/torrents/info"
                        async with session.get(torrents_url, timeout=10) as torrents_response:
                            torrents_info = await torrents_response.json() if torrents_response.status == 200 else []
                        
                        await session.close()
                        
                        return {
                            "success": True,
                            "instance_name": instance_config["name"],
                            "status": "online",
                            "download_speed": transfer_info.get("dl_info_speed", 0),
                            "upload_speed": transfer_info.get("up_info_speed", 0),
                            "active_downloads": len([t for t in torrents_info if t["state"] == "downloading"]),
                            "active_seeds": len([t for t in torrents_info if t["state"] == "uploading"]),
                            "total_torrents": len(torrents_info),
                            "last_online": datetime.now().isoformat()
                        }
                    else:
                        await session.close()
                        return {
                            "success": False,
                            "instance_name": instance_config["name"],
                            "status": "error",
                            "last_online": None,
                            "error": f"数据传输失败: {transfer_response.status}"
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "instance_name": instance_config["name"],
                "status": "error",
                "last_online": None,
                "error": str(e)
            }
    
    async def set_speed_limits(self, instance_config: Dict[str, Any], download_limit: int, upload_limit: int) -> bool:
        """设置速度限制"""
        try:
            session = aiohttp.ClientSession()
            
            # 登录
            login_data = {
                "username": instance_config["username"],
                "password": instance_config["password"]
            }
            
            login_url = f"{instance_config['host']}/api/v2/auth/login"
            async with session.post(login_url, data=login_data, timeout=10) as response:
                if response.status != 200:
                    return False
                
                # 设置速度限制
                limits_url = f"{instance_config['host']}/api/v2/transfer/setSpeedLimits"
                limits_data = {
                    "dl_limit": download_limit * 1024,  # 转换为bytes
                    "up_limit": upload_limit * 1024     # 转换为bytes
                }
                
                async with session.post(limits_url, data=limits_data, timeout=10) as limits_response:
                    success = limits_response.status == 200
                
                await session.close()
                return success
                
        except Exception:
            return False
    
    async def collect_all_instances_status(self) -> List[Dict]:
        """收集所有实例状态"""
        config = self.config_manager.load_config()
        tasks = []
        
        for instance in config.get("qbittorrent_instances", []):
            if instance.get("enabled", True):
                tasks.append(self.get_qbit_status(instance))
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def close_all_sessions(self):
        """关闭所有会话"""
        for session in self.sessions.values():
            await session.close()
        self.sessions.clear()