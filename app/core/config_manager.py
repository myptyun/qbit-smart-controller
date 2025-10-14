import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    def __init__(self, config_dir: str = "data/config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "settings.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 默认配置结构
        self.default_config = {
            "lucky_devices": [],
            "qbittorrent_instances": [],
            "controller_settings": {
                "poll_interval": 2,
                "limit_on_delay": 5,
                "limit_off_delay": 30,
                "retry_interval": 10,
                "limited_download": 1024,
                "limited_upload": 512,
                "normal_download": 0,
                "normal_upload": 0
            }
        }
        
        self._ensure_config_file()
    
    def _ensure_config_file(self):
        """确保配置文件存在"""
        if not self.config_file.exists():
            self.save_config(self.default_config)
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置文件"""
        try:
            # 创建备份
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.json.bak')
                with open(self.config_file, 'r') as src, open(backup_file, 'w') as dst:
                    dst.write(src.read())
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"配置文件保存失败: {e}")
            return False
    
    def add_lucky_device(self, device_config: Dict[str, Any]) -> bool:
        """添加Lucky设备配置"""
        config = self.load_config()
        config["lucky_devices"].append(device_config)
        return self.save_config(config)
    
    def update_lucky_device(self, index: int, device_config: Dict[str, Any]) -> bool:
        """更新Lucky设备配置"""
        config = self.load_config()
        if 0 <= index < len(config["lucky_devices"]):
            config["lucky_devices"][index] = device_config
            return self.save_config(config)
        return False
    
    def delete_lucky_device(self, index: int) -> bool:
        """删除Lucky设备配置"""
        config = self.load_config()
        if 0 <= index < len(config["lucky_devices"]):
            config["lucky_devices"].pop(index)
            return self.save_config(config)
        return False
    
    def add_qbit_instance(self, instance_config: Dict[str, Any]) -> bool:
        """添加qBittorrent实例配置"""
        config = self.load_config()
        config["qbittorrent_instances"].append(instance_config)
        return self.save_config(config)
    
    def update_qbit_instance(self, index: int, instance_config: Dict[str, Any]) -> bool:
        """更新qBittorrent实例配置"""
        config = self.load_config()
        if 0 <= index < len(config["qbittorrent_instances"]):
            config["qbittorrent_instances"][index] = instance_config
            return self.save_config(config)
        return False
    
    def delete_qbit_instance(self, index: int) -> bool:
        """删除qBittorrent实例配置"""
        config = self.load_config()
        if 0 <= index < len(config["qbittorrent_instances"]):
            config["qbittorrent_instances"].pop(index)
            return self.save_config(config)
        return False
    
    def update_controller_settings(self, settings: Dict[str, Any]) -> bool:
        """更新控制器设置"""
        config = self.load_config()
        config["controller_settings"].update(settings)
        return self.save_config(config)