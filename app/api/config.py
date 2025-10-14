from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.core.config_manager import ConfigManager

router = APIRouter(prefix="/api/config", tags=["config"])

# 请求模型
class LuckyDeviceConfig(BaseModel):
    name: str
    api_url: str
    weight: float = 1.0
    enabled: bool = True
    description: Optional[str] = None

class QBittorrentConfig(BaseModel):
    name: str
    host: str
    username: str
    password: str
    enabled: bool = True
    description: Optional[str] = None

class ControllerSettings(BaseModel):
    poll_interval: int = 2
    limit_on_delay: int = 5
    limit_off_delay: int = 30
    retry_interval: int = 10
    limited_download: int = 1024
    limited_upload: int = 512
    normal_download: int = 0
    normal_upload: int = 0

# 初始化配置管理器
config_manager = ConfigManager()

@router.get("/")
async def get_config():
    """获取完整配置"""
    return config_manager.load_config()

@router.get("/lucky-devices")
async def get_lucky_devices():
    """获取Lucky设备列表"""
    config = config_manager.load_config()
    return config.get("lucky_devices", [])

@router.post("/lucky-devices")
async def add_lucky_device(device: LuckyDeviceConfig):
    """添加Lucky设备"""
    success = config_manager.add_lucky_device(device.dict())
    if not success:
        raise HTTPException(status_code=500, detail="添加设备失败")
    return {"message": "设备添加成功"}

@router.put("/lucky-devices/{index}")
async def update_lucky_device(index: int, device: LuckyDeviceConfig):
    """更新Lucky设备"""
    success = config_manager.update_lucky_device(index, device.dict())
    if not success:
        raise HTTPException(status_code=500, detail="更新设备失败")
    return {"message": "设备更新成功"}

@router.delete("/lucky-devices/{index}")
async def delete_lucky_device(index: int):
    """删除Lucky设备"""
    success = config_manager.delete_lucky_device(index)
    if not success:
        raise HTTPException(status_code=500, detail="删除设备失败")
    return {"message": "设备删除成功"}

@router.get("/qbit-instances")
async def get_qbit_instances():
    """获取qBittorrent实例列表"""
    config = config_manager.load_config()
    return config.get("qbittorrent_instances", [])

@router.post("/qbit-instances")
async def add_qbit_instance(instance: QBittorrentConfig):
    """添加qBittorrent实例"""
    success = config_manager.add_qbit_instance(instance.dict())
    if not success:
        raise HTTPException(status_code=500, detail="添加实例失败")
    return {"message": "实例添加成功"}

@router.put("/qbit-instances/{index}")
async def update_qbit_instance(index: int, instance: QBittorrentConfig):
    """更新qBittorrent实例"""
    success = config_manager.update_qbit_instance(index, instance.dict())
    if not success:
        raise HTTPException(status_code=500, detail="更新实例失败")
    return {"message": "实例更新成功"}

@router.delete("/qbit-instances/{index}")
async def delete_qbit_instance(index: int):
    """删除qBittorrent实例"""
    success = config_manager.delete_qbit_instance(index)
    if not success:
        raise HTTPException(status_code=500, detail="删除实例失败")
    return {"message": "实例删除成功"}

@router.get("/controller-settings")
async def get_controller_settings():
    """获取控制器设置"""
    config = config_manager.load_config()
    return config.get("controller_settings", {})

@router.put("/controller-settings")
async def update_controller_settings(settings: ControllerSettings):
    """更新控制器设置"""
    success = config_manager.update_controller_settings(settings.dict())
    if not success:
        raise HTTPException(status_code=500, detail="更新设置失败")
    return {"message": "设置更新成功"}