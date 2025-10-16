import os
import uvicorn
import yaml
import logging
import aiohttp
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
import json

print("🚀 开始启动智能 qBittorrent 限速控制器...")

# 设置完善的日志系统
from logging.handlers import RotatingFileHandler
import sys

# 创建日志目录
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

# 配置日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# 创建根日志器
logger = logging.getLogger("qbit-controller")
logger.setLevel(logging.INFO)

# 清除现有的处理器
logger.handlers.clear()

# 1. 控制台处理器（彩色输出）
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(log_format, date_format)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# 2. 文件处理器（所有日志）
file_handler = RotatingFileHandler(
    log_dir / "controller.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(log_format, date_format)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# 3. 错误日志处理器
error_handler = RotatingFileHandler(
    log_dir / "error.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=3,
    encoding='utf-8'
)
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter(log_format, date_format)
error_handler.setFormatter(error_formatter)
logger.addHandler(error_handler)

# 防止日志传播到根日志器
logger.propagate = False

logger.info("=" * 60)
logger.info("🚀 智能 qBittorrent 限速控制器 v2.0 启动中...")
logger.info("=" * 60)

app = FastAPI(
    title="智能 qBittorrent 限速控制器",
    description="基于Lucky设备状态的智能限速控制",
    version="2.0.0"
)

# 创建必要的目录
os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)

# 挂载静态文件
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    templates = Jinja2Templates(directory="app/templates")
    print("✅ 静态文件设置成功")
except Exception as e:
    print(f"⚠️ 静态文件设置警告: {e}")

class ConfigManager:
    def __init__(self):
        self.config_file = Path("config/config.yaml")
        self.default_config = {
            "lucky_devices": [
                {
                    "name": "我的Lucky设备",
                    "api_url": "http://192.168.2.3:16601/api/webservice/rules?openToken=S9SXzQAAg03myzAfUsLkiQmTBUUUr3Yn",
                    "weight": 1.0,
                    "enabled": True,
                    "description": "主要监控设备"
                }
            ],
            "qbittorrent_instances": [
                {
                    "name": "我的QB实例",
                    "host": "http://192.168.2.21:8080",
                    "username": "admin",
                    "password": "adminadmin",
                    "enabled": True,
                    "description": "qBittorrent实例"
                }
            ],
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
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """确保配置文件存在"""
        if not self.config_file.exists():
            print("📁 配置文件不存在，创建默认配置...")
            self.save_config(self.default_config)
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                print("✅ 配置文件加载成功")
                return config
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            return self.default_config
    
    def save_config(self, config):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, indent=2)
            print("✅ 配置文件保存成功")
            return True
        except Exception as e:
            print(f"❌ 配置文件保存失败: {e}")
            return False

class LuckyMonitor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.session = None
        self._session_created = False
    
    async def get_session(self):
        """获取或创建 HTTP 会话（连接池复用）"""
        if self.session is None or self.session.closed:
            # 配置连接池和超时
            timeout = aiohttp.ClientTimeout(
                total=15,           # 总超时
                connect=5,          # 连接超时
                sock_read=10        # 读取超时
            )
            connector = aiohttp.TCPConnector(
                verify_ssl=False,
                limit=10,           # 连接池大小
                limit_per_host=5,   # 每个主机的连接数
                ttl_dns_cache=300,  # DNS 缓存时间（秒）
                force_close=False,  # 复用连接
                enable_cleanup_closed=True
            )
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                raise_for_status=False
            )
            self._session_created = True
            logger.debug("✅ Lucky Monitor HTTP 会话已创建")
        return self.session
    
    async def test_connection(self, api_url: str):
        """测试Lucky设备连接"""
        try:
            print(f"🔍 测试Lucky连接: {api_url}")
            session = await self.get_session()
            async with session.get(api_url) as response:
                content = await response.text()
                print(f"📡 Lucky响应状态: {response.status}")
                print(f"📡 Lucky响应内容: {content[:500]}...")
                
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
                        "message": f"HTTP错误: {response.status}",
                        "response_content": content
                    }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "status": "timeout",
                "message": "连接超时 (15秒)"
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"连接失败: {str(e)}"
            }
    
    async def get_device_connections(self, device_config: dict):
        """获取Lucky设备连接数"""
        try:
            session = await self.get_session()
            api_url = device_config["api_url"]
            
            print(f"🔍 采集Lucky数据: {device_config['name']}")
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    connections = self._parse_connections(data)
                    weighted_connections = connections * device_config.get("weight", 1.0)
                    
                    print(f"📊 {device_config['name']} - 连接数: {connections}, 加权: {weighted_connections}")
                    
                    return {
                        "success": True,
                        "device_name": device_config["name"],
                        "connections": connections,
                        "weighted_connections": weighted_connections,
                        "status": "online",
                        "last_update": datetime.now().isoformat(),
                        "raw_data": data
                    }
                else:
                    error_msg = f"HTTP {response.status}"
                    print(f"❌ {device_config['name']} - {error_msg}")
                    return {
                        "success": False,
                        "device_name": device_config["name"],
                        "connections": 0,
                        "weighted_connections": 0,
                        "status": "error",
                        "error": error_msg,
                        "last_update": datetime.now().isoformat()
                    }
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {device_config['name']} - 采集异常: {error_msg}")
            return {
                "success": False,
                "device_name": device_config["name"],
                "connections": 0,
                "weighted_connections": 0,
                "status": "error",
                "error": error_msg,
                "last_update": datetime.now().isoformat()
            }
    
    def _parse_connections(self, data: dict) -> int:
        """解析Lucky API响应，提取连接数"""
        try:
            print("🔍 开始解析Lucky连接数据...")
            print(f"📦 API响应数据结构: {list(data.keys())}")
            
            # 方法1: 从statistics中提取（优先，最准确）
            if "statistics" in data and data["statistics"]:
                total_connections = 0
                for rule_key, rule_stats in data["statistics"].items():
                    # 尝试多种可能的连接数字段名
                    connections = (
                        rule_stats.get("Connections", 0) or 
                        rule_stats.get("connections", 0) or
                        rule_stats.get("ConnCount", 0) or
                        rule_stats.get("ActiveConnections", 0)
                    )
                    
                    if connections > 0:
                        total_connections += connections
                        print(f"  📡 规则 {rule_key}: {connections} 个连接")
                
                if total_connections > 0:
                    print(f"📊 总连接数 (statistics): {total_connections}")
                    return total_connections
            
            # 方法2: 从ruleList中提取每个规则的连接信息
            if "ruleList" in data and isinstance(data["ruleList"], list):
                total_connections = 0
                for rule in data["ruleList"]:
                    rule_name = rule.get("RuleName", "未知规则")
                    
                    # 尝试从规则本身提取连接数
                    connections = (
                        rule.get("Connections", 0) or 
                        rule.get("connections", 0) or
                        rule.get("ConnCount", 0) or
                        rule.get("CurrentConnections", 0)
                    )
                    
                    if connections > 0:
                        total_connections += connections
                        print(f"  📡 规则 {rule_name}: {connections} 个连接")
                
                if total_connections > 0:
                    print(f"📊 总连接数 (ruleList): {total_connections}")
                    return total_connections
                else:
                    print(f"⚠️ 规则列表中未找到连接数，规则数量: {len(data['ruleList'])}")
            
            # 方法3: 直接从顶层提取总连接数
            if "totalConnections" in data:
                total = data["totalConnections"]
                print(f"📊 总连接数 (直接): {total}")
                return total
            
            # 如果所有方法都失败，记录完整结构以便调试
            print("⚠️ 未找到连接数据，完整数据结构:")
            print(f"  {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            
            return 0
        except Exception as e:
            print(f"❌ 连接数解析错误: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _parse_detailed_connections(self, data: dict) -> list:
        """解析Lucky API响应，提取详细的连接信息"""
        try:
            print("🔍 开始解析Lucky详细连接数据...")
            connections_info = []
            
            # 方法1: 从statistics中提取详细信息
            if "statistics" in data and data["statistics"]:
                for rule_key, rule_stats in data["statistics"].items():
                    connections = (
                        rule_stats.get("Connections", 0) or 
                        rule_stats.get("connections", 0) or
                        rule_stats.get("ConnCount", 0) or
                        rule_stats.get("ActiveConnections", 0)
                    )
                    
                    if connections > 0:
                        connections_info.append({
                            "rule_name": rule_key,
                            "connections": connections,
                            "download_bytes": rule_stats.get("DownloadBytes", 0),
                            "upload_bytes": rule_stats.get("UploadBytes", 0),
                            "download_speed": rule_stats.get("DownloadSpeed", 0),
                            "upload_speed": rule_stats.get("UploadSpeed", 0),
                            "last_activity": rule_stats.get("LastActivity", ""),
                            "status": "active" if connections > 0 else "inactive"
                        })
                        print(f"  📡 规则 {rule_key}: {connections} 个连接")
            
            # 方法2: 从ruleList中提取详细信息
            elif "ruleList" in data and isinstance(data["ruleList"], list):
                for rule in data["ruleList"]:
                    rule_name = rule.get("RuleName", "未知规则")
                    connections = (
                        rule.get("Connections", 0) or 
                        rule.get("connections", 0) or
                        rule.get("ConnCount", 0) or
                        rule.get("CurrentConnections", 0)
                    )
                    
                    connections_info.append({
                        "rule_name": rule_name,
                        "connections": connections,
                        "download_bytes": rule.get("DownloadBytes", 0),
                        "upload_bytes": rule.get("UploadBytes", 0),
                        "download_speed": rule.get("DownloadSpeed", 0),
                        "upload_speed": rule.get("UploadSpeed", 0),
                        "last_activity": rule.get("LastActivity", ""),
                        "status": "active" if connections > 0 else "inactive",
                        "rule_type": rule.get("RuleType", "unknown"),
                        "target": rule.get("Target", ""),
                        "source": rule.get("Source", "")
                    })
                    print(f"  📡 规则 {rule_name}: {connections} 个连接")
            
            print(f"📊 解析到 {len(connections_info)} 个连接规则")
            return connections_info
            
        except Exception as e:
            print(f"❌ 详细连接解析错误: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def close(self):
        """关闭会话并释放资源"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("🔒 Lucky Monitor HTTP 会话已关闭")
        self.session = None
        self._session_created = False

class SpeedController:
    """智能限速控制器 - 核心控制逻辑"""
    def __init__(self, config_manager, lucky_monitor, qbit_manager):
        self.config_manager = config_manager
        self.lucky_monitor = lucky_monitor
        self.qbit_manager = qbit_manager
        self.is_limited = False
        self.limit_timer = 0
        self.normal_timer = 0
        self.total_connections = 0
        self.running = False
        self.last_action_time = None
        logger.info("🎮 速度控制器初始化完成")
    
    async def start(self):
        """启动控制循环"""
        if self.running:
            logger.warning("控制器已在运行")
            return
        
        self.running = True
        logger.info("🚀 启动自动限速控制循环...")
        
        try:
            while self.running:
                await self._control_cycle()
        except Exception as e:
            logger.error(f"❌ 控制循环异常: {e}", exc_info=True)
            self.running = False
    
    async def stop(self):
        """停止控制循环"""
        logger.info("⏹️ 停止控制循环...")
        self.running = False
    
    async def _control_cycle(self):
        """单次控制周期"""
        try:
            config = self.config_manager.load_config()
            settings = config.get("controller_settings", {})
            
            poll_interval = settings.get("poll_interval", 2)
            limit_on_delay = settings.get("limit_on_delay", 5)
            limit_off_delay = settings.get("limit_off_delay", 30)
            
            # 1. 采集所有 Lucky 设备的连接数
            self.total_connections = await self._collect_total_connections(config)
            
            has_connections = self.total_connections > 0
            
            # 2. 状态机逻辑
            if has_connections and not self.is_limited:
                # 检测到连接，开始限速倒计时
                self.limit_timer += poll_interval
                self.normal_timer = 0
                
                logger.info(f"⚠️ 检测到 {self.total_connections:.1f} 个加权连接，限速倒计时: {self.limit_timer}/{limit_on_delay}秒")
                
                if self.limit_timer >= limit_on_delay:
                    # 触发限速
                    await self._apply_limited_mode(settings)
                    self.is_limited = True
                    self.limit_timer = 0
                    
            elif not has_connections and self.is_limited:
                # 无连接，开始恢复倒计时
                self.normal_timer += poll_interval
                self.limit_timer = 0
                
                logger.info(f"✅ 无活跃连接，恢复倒计时: {self.normal_timer}/{limit_off_delay}秒")
                
                if self.normal_timer >= limit_off_delay:
                    # 恢复全速
                    await self._apply_normal_mode(settings)
                    self.is_limited = False
                    self.normal_timer = 0
                    
            elif has_connections and self.is_limited:
                # 保持限速状态，重置恢复计时器
                self.normal_timer = 0
                logger.debug(f"🔒 保持限速状态，当前连接: {self.total_connections:.1f}")
                
            else:
                # 保持正常状态，重置限速计时器
                self.limit_timer = 0
                logger.debug(f"✨ 保持正常状态，无活跃连接")
            
            # 3. 等待下次轮询
            await asyncio.sleep(poll_interval)
            
        except Exception as e:
            logger.error(f"❌ 控制周期执行失败: {e}", exc_info=True)
            await asyncio.sleep(5)  # 出错后等待5秒再重试
    
    async def _collect_total_connections(self, config: dict) -> float:
        """采集所有设备的总加权连接数"""
        devices = config.get("lucky_devices", [])
        total = 0.0
        
        for device in devices:
            if not device.get("enabled", True):
                continue
                
            try:
                result = await self.lucky_monitor.get_device_connections(device)
                if result.get("success"):
                    total += result.get("weighted_connections", 0)
            except Exception as e:
                logger.error(f"❌ 采集设备 {device.get('name')} 失败: {e}")
        
        return total
    
    async def _apply_limited_mode(self, settings: dict):
        """应用限速模式"""
        download_limit = settings.get("limited_download", 1024)
        upload_limit = settings.get("limited_upload", 512)
        
        logger.warning(f"🚨 进入限速模式 - 下载: {download_limit} KB/s, 上传: {upload_limit} KB/s")
        
        config = self.config_manager.load_config()
        instances = config.get("qbittorrent_instances", [])
        
        success_count = 0
        for instance in instances:
            if not instance.get("enabled", True):
                continue
                
            try:
                success = await self.qbit_manager.set_speed_limits(
                    instance, download_limit, upload_limit
                )
                if success:
                    success_count += 1
                    logger.info(f"✅ {instance['name']} 限速设置成功")
                else:
                    logger.error(f"❌ {instance['name']} 限速设置失败")
            except Exception as e:
                logger.error(f"❌ {instance['name']} 限速设置异常: {e}")
        
        self.last_action_time = datetime.now()
        logger.info(f"📊 限速应用完成: {success_count}/{len(instances)} 个实例成功")
    
    async def _apply_normal_mode(self, settings: dict):
        """应用正常模式（全速）"""
        download_limit = settings.get("normal_download", 0)
        upload_limit = settings.get("normal_upload", 0)
        
        logger.info(f"🎉 恢复全速模式 - 下载: {'不限速' if download_limit == 0 else str(download_limit) + ' KB/s'}, 上传: {'不限速' if upload_limit == 0 else str(upload_limit) + ' KB/s'}")
        
        config = self.config_manager.load_config()
        instances = config.get("qbittorrent_instances", [])
        
        success_count = 0
        for instance in instances:
            if not instance.get("enabled", True):
                continue
                
            try:
                success = await self.qbit_manager.set_speed_limits(
                    instance, download_limit, upload_limit
                )
                if success:
                    success_count += 1
                    logger.info(f"✅ {instance['name']} 恢复全速成功")
                else:
                    logger.error(f"❌ {instance['name']} 恢复全速失败")
            except Exception as e:
                logger.error(f"❌ {instance['name']} 恢复全速异常: {e}")
        
        self.last_action_time = datetime.now()
        logger.info(f"📊 全速恢复完成: {success_count}/{len(instances)} 个实例成功")
    
    def get_controller_state(self) -> dict:
        """获取控制器状态"""
        return {
            "running": self.running,
            "is_limited": self.is_limited,
            "total_connections": self.total_connections,
            "limit_timer": self.limit_timer,
            "normal_timer": self.normal_timer,
            "last_action_time": self.last_action_time.isoformat() if self.last_action_time else None,
            "status": "限速中" if self.is_limited else "正常运行"
        }

class QBittorrentManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.session = None
        self._session_created = False
    
    async def get_session(self):
        """获取或创建 HTTP 会话（连接池复用）"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(
                total=10,
                connect=5,
                sock_read=8
            )
            connector = aiohttp.TCPConnector(
                verify_ssl=False,
                limit=20,
                limit_per_host=10,
                ttl_dns_cache=300,
                force_close=False,
                enable_cleanup_closed=True
            )
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                raise_for_status=False
            )
            self._session_created = True
            logger.debug("✅ qBittorrent Manager HTTP 会话已创建")
        return self.session
    
    async def test_connection(self, instance_config: dict):
        """测试qBittorrent连接"""
        try:
            print(f"🔍 测试QB连接: {instance_config['host']}")
            
            session = await self.get_session()
            
            # 登录
            login_data = {
                "username": instance_config["username"],
                "password": instance_config["password"]
            }
            
            login_url = f"{instance_config['host']}/api/v2/auth/login"
            print(f"🔑 尝试登录: {login_url}")
            print(f"🔑 用户名: {instance_config['username']}")
            
            async with session.post(login_url, data=login_data) as response:
                login_content = await response.text()
                print(f"🔑 登录响应: {response.status} - {login_content}")
                
                if response.status == 200:
                    # 获取传输信息测试连接
                    transfer_url = f"{instance_config['host']}/api/v2/transfer/info"
                    print(f"📊 测试传输信息: {transfer_url}")
                    
                    async with session.get(transfer_url) as transfer_response:
                        transfer_content = await transfer_response.text()
                        print(f"📊 传输响应: {transfer_response.status} - {transfer_content[:200]}...")
                        
                        if transfer_response.status == 200:
                            return {
                                "success": True,
                                "status": "connected",
                                "message": "连接成功"
                            }
                        elif transfer_response.status == 403:
                            return {
                                "success": False,
                                "status": "forbidden",
                                "message": f"403 禁止访问 - 可能原因：1)IP被限制 2)权限不足 3)需要重新登录。响应: {transfer_content}"
                            }
                        else:
                            return {
                                "success": False,
                                "status": "error", 
                                "message": f"数据传输失败: {transfer_response.status} - {transfer_content}"
                            }
                elif response.status == 403:
                    return {
                        "success": False,
                        "status": "auth_forbidden",
                        "message": f"403 认证被禁止 - 可能原因：1)用户名密码错误 2)IP被限制 3)Web UI未启用。响应: {login_content}"
                    }
                elif response.status == 401:
                    return {
                        "success": False,
                        "status": "auth_failed",
                        "message": f"401 认证失败 - 用户名或密码错误。响应: {login_content}"
                    }
                else:
                    return {
                        "success": False,
                        "status": "auth_failed",
                        "message": f"认证失败: {response.status} - {login_content}"
                    }
        except Exception as e:
            error_msg = f"连接失败: {str(e)}"
            print(f"❌ QB连接异常: {error_msg}")
            return {
                "success": False,
                "status": "error",
                "message": error_msg
            }
    
    async def get_instance_status(self, instance_config: dict):
        """获取qBittorrent实例状态"""
        try:
            print(f"🔍 采集QB状态: {instance_config['name']}")
            
            session = await self.get_session()
            
            # 登录
            login_data = {
                "username": instance_config["username"],
                "password": instance_config["password"]
            }
            
            login_url = f"{instance_config['host']}/api/v2/auth/login"
            async with session.post(login_url, data=login_data) as response:
                if response.status != 200:
                    error_msg = f"认证失败: {response.status}"
                    print(f"❌ {instance_config['name']} - {error_msg}")
                    return {
                        "success": False,
                        "instance_name": instance_config["name"],
                        "status": "auth_failed",
                        "error": error_msg
                    }
                
                # 获取传输信息
                transfer_url = f"{instance_config['host']}/api/v2/transfer/info"
                async with session.get(transfer_url) as transfer_response:
                    if transfer_response.status == 200:
                        transfer_info = await transfer_response.json()
                        
                        # 获取种子列表
                        torrents_url = f"{instance_config['host']}/api/v2/torrents/info"
                        async with session.get(torrents_url) as torrents_response:
                            torrents_info = await torrents_response.json() if torrents_response.status == 200 else []
                        
                        active_downloads = len([t for t in torrents_info if t.get("state") == "downloading"])
                        active_seeds = len([t for t in torrents_info if t.get("state") == "uploading"])
                        
                        status_data = {
                            "success": True,
                            "instance_name": instance_config["name"],
                            "status": "online",
                            "download_speed": transfer_info.get("dl_info_speed", 0),
                            "upload_speed": transfer_info.get("up_info_speed", 0),
                            "active_downloads": active_downloads,
                            "active_seeds": active_seeds,
                            "total_torrents": len(torrents_info),
                            "last_update": datetime.now().isoformat()
                        }
                        
                        print(f"✅ {instance_config['name']} - 在线, 下载: {status_data['download_speed']} B/s, 上传: {status_data['upload_speed']} B/s")
                        return status_data
                    else:
                        error_msg = f"数据传输失败: {transfer_response.status}"
                        print(f"❌ {instance_config['name']} - {error_msg}")
                        return {
                            "success": False,
                            "instance_name": instance_config["name"],
                            "status": "error",
                            "error": error_msg
                        }
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {instance_config['name']} - 采集异常: {error_msg}")
            return {
                "success": False,
                "instance_name": instance_config["name"],
                "status": "error", 
                "error": error_msg
            }
    
    async def set_speed_limits(self, instance_config: dict, download_limit: int, upload_limit: int) -> bool:
        """设置速度限制（KB/s）"""
        try:
            print(f"🎚️ 设置速度限制: {instance_config['name']} - 下载: {download_limit} KB/s, 上传: {upload_limit} KB/s")
            
            session = await self.get_session()
            
            # 登录
            login_data = {
                "username": instance_config["username"],
                "password": instance_config["password"]
            }
            
            login_url = f"{instance_config['host']}/api/v2/auth/login"
            async with session.post(login_url, data=login_data) as response:
                if response.status != 200:
                    print(f"❌ {instance_config['name']} - 登录失败")
                    return False
                
                # 设置全局下载限制
                dl_limit_url = f"{instance_config['host']}/api/v2/transfer/setDownloadLimit"
                dl_limit_data = {"limit": download_limit * 1024}  # 转换为 bytes/s
                async with session.post(dl_limit_url, data=dl_limit_data) as dl_response:
                    dl_success = dl_response.status == 200
                
                # 设置全局上传限制
                up_limit_url = f"{instance_config['host']}/api/v2/transfer/setUploadLimit"
                up_limit_data = {"limit": upload_limit * 1024}  # 转换为 bytes/s
                async with session.post(up_limit_url, data=up_limit_data) as up_response:
                    up_success = up_response.status == 200
                
                success = dl_success and up_success
                if success:
                    print(f"✅ {instance_config['name']} - 速度限制设置成功")
                else:
                    print(f"❌ {instance_config['name']} - 速度限制设置失败")
                
                return success
        except Exception as e:
            print(f"❌ {instance_config['name']} - 设置速度限制异常: {e}")
            return False
    
    async def close(self):
        """关闭会话并释放资源"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("🔒 qBittorrent Manager HTTP 会话已关闭")
        self.session = None
        self._session_created = False

# 初始化管理器
config_manager = ConfigManager()
lucky_monitor = LuckyMonitor(config_manager)
qbit_manager = QBittorrentManager(config_manager)
speed_controller = SpeedController(config_manager, lucky_monitor, qbit_manager)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """主页面"""
    try:
        config = config_manager.load_config()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "config": config
        })
    except Exception as e:
        logger.error(f"页面渲染失败: {e}")
        return HTMLResponse(f"""
        <html>
            <head><title>错误</title></head>
            <body>
                <h1>页面加载错误</h1>
                <p>{str(e)}</p>
            </body>
        </html>
        """)

@app.get("/api/status")
async def get_status():
    """服务状态"""
    config = config_manager.load_config()
    return {
        "status": "running", 
        "message": "智能 qBittorrent 限速控制器服务已启动",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "config_file": str(config_manager.config_file)
    }

@app.get("/api/config")
async def get_config():
    """获取配置信息"""
    return config_manager.load_config()

@app.post("/api/config")
async def update_config(request: Request):
    """更新整个配置"""
    try:
        config_data = await request.json()
        if config_manager.save_config(config_data):
            logger.info("📝 配置已更新")
            return {"message": "配置保存成功", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="配置保存失败")
    except Exception as e:
        logger.error(f"配置更新失败: {e}")
        raise HTTPException(status_code=400, detail=f"配置更新失败: {str(e)}")

@app.put("/api/config/controller")
async def update_controller_settings(request: Request):
    """更新控制器设置"""
    try:
        settings = await request.json()
        config = config_manager.load_config()
        config["controller_settings"].update(settings)
        
        if config_manager.save_config(config):
            logger.info(f"⚙️ 控制器设置已更新: {settings}")
            return {"message": "控制器设置保存成功", "status": "success", "settings": config["controller_settings"]}
        else:
            raise HTTPException(status_code=500, detail="设置保存失败")
    except Exception as e:
        logger.error(f"控制器设置更新失败: {e}")
        raise HTTPException(status_code=400, detail=f"设置更新失败: {str(e)}")

@app.get("/api/lucky/status")
async def get_lucky_status():
    """Lucky设备状态 - 真实API调用"""
    print("🔄 开始采集Lucky设备状态...")
    config = config_manager.load_config()
    devices = config.get("lucky_devices", [])
    
    status_data = []
    for device in devices:
        if device.get("enabled", True):
            device_status = await lucky_monitor.get_device_connections(device)
            status_data.append(device_status)
        else:
            status_data.append({
                "success": False,
                "device_name": device["name"],
                "connections": 0,
                "weighted_connections": 0,
                "status": "disabled",
                "error": "设备已禁用",
                "last_update": datetime.now().isoformat()
            })
    
    print(f"✅ Lucky状态采集完成: {len(status_data)} 个设备")
    return {"devices": status_data}

@app.get("/api/lucky/connections")
async def get_lucky_connections():
    """获取Lucky设备的详细连接信息"""
    print("🔍 获取Lucky详细连接信息...")
    config = config_manager.load_config()
    devices = config.get("lucky_devices", [])
    
    detailed_data = []
    for device in devices:
        if device.get("enabled", True):
            try:
                session = await lucky_monitor.get_session()
                api_url = device["api_url"]
                
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 解析详细的连接信息
                        connections_info = lucky_monitor._parse_detailed_connections(data)
                        
                        detailed_data.append({
                            "success": True,
                            "device_name": device["name"],
                            "device_info": {
                                "api_url": api_url,
                                "weight": device.get("weight", 1.0),
                                "description": device.get("description", "")
                            },
                            "connections": connections_info,
                            "total_connections": sum(conn.get("connections", 0) for conn in connections_info),
                            "last_update": datetime.now().isoformat(),
                            "raw_data": data
                        })
                    else:
                        detailed_data.append({
                            "success": False,
                            "device_name": device["name"],
                            "error": f"HTTP {response.status}",
                            "last_update": datetime.now().isoformat()
                        })
            except Exception as e:
                detailed_data.append({
                    "success": False,
                    "device_name": device["name"],
                    "error": str(e),
                    "last_update": datetime.now().isoformat()
                })
        else:
            detailed_data.append({
                "success": False,
                "device_name": device["name"],
                "status": "disabled",
                "error": "设备已禁用",
                "last_update": datetime.now().isoformat()
            })
    
    return {"devices": detailed_data}

@app.get("/api/qbit/status")
async def get_qbit_status():
    """qBittorrent状态 - 真实API调用"""
    print("🔄 开始采集QB状态...")
    config = config_manager.load_config()
    instances = config.get("qbittorrent_instances", [])
    
    status_data = []
    for instance in instances:
        if instance.get("enabled", True):
            instance_status = await qbit_manager.get_instance_status(instance)
            status_data.append(instance_status)
        else:
            status_data.append({
                "success": False,
                "instance_name": instance["name"],
                "status": "disabled",
                "error": "实例已禁用",
                "last_update": datetime.now().isoformat()
            })
    
    print(f"✅ QB状态采集完成: {len(status_data)} 个实例")
    return {"instances": status_data}

@app.get("/api/test/lucky/{device_index}")
async def test_lucky_connection(device_index: int):
    """测试Lucky设备连接"""
    print(f"🧪 测试Lucky设备连接: {device_index}")
    config = config_manager.load_config()
    devices = config.get("lucky_devices", [])
    
    if device_index < 0 or device_index >= len(devices):
        raise HTTPException(status_code=404, detail="设备不存在")
    
    device = devices[device_index]
    result = await lucky_monitor.test_connection(device["api_url"])
    return result

@app.get("/api/test/qbit/{instance_index}")
async def test_qbit_connection(instance_index: int):
    """测试qBittorrent连接"""
    print(f"🧪 测试QB连接: {instance_index}")
    config = config_manager.load_config()
    instances = config.get("qbittorrent_instances", [])
    
    if instance_index < 0 or instance_index >= len(instances):
        raise HTTPException(status_code=404, detail="实例不存在")
    
    instance = instances[instance_index]
    result = await qbit_manager.test_connection(instance)
    return result

@app.get("/api/debug/qbit/{instance_index}")
async def debug_qbit_connection(instance_index: int):
    """调试qBittorrent连接 - 详细诊断"""
    print(f"🔧 调试QB连接: {instance_index}")
    config = config_manager.load_config()
    instances = config.get("qbittorrent_instances", [])
    
    if instance_index < 0 or instance_index >= len(instances):
        raise HTTPException(status_code=404, detail="实例不存在")
    
    instance = instances[instance_index]
    debug_info = {
        "instance_config": {
            "name": instance["name"],
            "host": instance["host"],
            "username": instance["username"],
            "password": "***"  # 隐藏密码
        },
        "tests": []
    }
    
    try:
        # 测试1: 基本连接
        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(instance["host"], timeout=5) as response:
                    debug_info["tests"].append({
                        "test": "基本连接",
                        "url": instance["host"],
                        "status": response.status,
                        "success": response.status == 200,
                        "message": f"HTTP {response.status}"
                    })
            except Exception as e:
                debug_info["tests"].append({
                    "test": "基本连接",
                    "url": instance["host"],
                    "status": "error",
                    "success": False,
                    "message": str(e)
                })
            
            # 测试2: 登录
            try:
                login_data = {
                    "username": instance["username"],
                    "password": instance["password"]
                }
                login_url = f"{instance['host']}/api/v2/auth/login"
                async with session.post(login_url, data=login_data, timeout=10) as response:
                    content = await response.text()
                    debug_info["tests"].append({
                        "test": "登录认证",
                        "url": login_url,
                        "status": response.status,
                        "success": response.status == 200,
                        "message": f"HTTP {response.status} - {content[:100]}",
                        "response_headers": dict(response.headers)
                    })
            except Exception as e:
                debug_info["tests"].append({
                    "test": "登录认证",
                    "url": login_url,
                    "status": "error",
                    "success": False,
                    "message": str(e)
                })
            
            # 测试3: 传输信息
            try:
                transfer_url = f"{instance['host']}/api/v2/transfer/info"
                async with session.get(transfer_url, timeout=10) as response:
                    content = await response.text()
                    debug_info["tests"].append({
                        "test": "传输信息",
                        "url": transfer_url,
                        "status": response.status,
                        "success": response.status == 200,
                        "message": f"HTTP {response.status} - {content[:100]}",
                        "response_headers": dict(response.headers)
                    })
            except Exception as e:
                debug_info["tests"].append({
                    "test": "传输信息",
                    "url": transfer_url,
                    "status": "error",
                    "success": False,
                    "message": str(e)
                })
    
    except Exception as e:
        debug_info["error"] = str(e)
    
    return debug_info

@app.get("/api/debug/config")
async def debug_config():
    """调试配置信息"""
    config = config_manager.load_config()
    return {
        "config": config,
        "config_file": str(config_manager.config_file),
        "file_exists": config_manager.config_file.exists()
    }

@app.get("/api/controller/state")
async def get_controller_state():
    """获取控制器状态"""
    return speed_controller.get_controller_state()

@app.post("/api/controller/start")
async def start_controller():
    """手动启动控制器"""
    if speed_controller.running:
        return {"message": "控制器已在运行", "status": "running"}
    
    asyncio.create_task(speed_controller.start())
    return {"message": "控制器启动成功", "status": "started"}

@app.post("/api/controller/stop")
async def stop_controller():
    """手动停止控制器"""
    await speed_controller.stop()
    return {"message": "控制器已停止", "status": "stopped"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "qbit-smart-controller",
        "controller_running": speed_controller.running
    }

@app.on_event("startup")
async def startup_event():
    """应用启动时启动控制器"""
    logger.info("🚀 应用启动，初始化控制器...")
    # 启动控制循环
    asyncio.create_task(speed_controller.start())
    logger.info("✅ 控制器已启动")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("⏹️ 应用关闭，清理资源...")
    await speed_controller.stop()
    await lucky_monitor.close()
    await qbit_manager.close()
    logger.info("✅ 资源清理完成")

if __name__ == "__main__":
    config = config_manager.load_config()
    web_settings = config.get("web_settings", {})
    
    host = web_settings.get("host", "0.0.0.0")
    port = web_settings.get("port", 5000)
    
    print("=" * 50)
    print("🚀 智能 qBittorrent 限速控制器 v2.0.0")
    print("=" * 50)
    print("✅ 所有依赖加载成功，启动 Web 服务器...")
    print(f"📊 服务地址: http://{host}:{port}")
    print("🔧 可用端点:")
    print("   /              - Web 界面")
    print("   /api/status    - 服务状态") 
    print("   /api/config    - 配置信息")
    print("   /api/lucky/status - Lucky设备状态")
    print("   /api/qbit/status  - qBittorrent状态")
    print("   /api/test/lucky/{index} - 测试Lucky连接")
    print("   /api/test/qbit/{index} - 测试QB连接")
    print("   /api/debug/config - 调试配置")
    print("   /health        - 健康检查")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info",
        access_log=True
    )
