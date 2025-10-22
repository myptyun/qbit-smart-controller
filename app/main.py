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

# 导入版本管理模块
try:
    from version import get_version_info, get_version_string
    VERSION_INFO = get_version_info()
    VERSION_STRING = get_version_string()
except ImportError:
    # 如果version.py不存在，使用默认版本
    VERSION_INFO = {
        'version': '2.0.0-dev',
        'build_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'commit_hash': 'unknown'
    }
    VERSION_STRING = f"v{VERSION_INFO['version']} (Build: {VERSION_INFO['build_time']})"

print("🚀 开始启动 SpeedHiveHome...")

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
logger.info(f"🚀 SpeedHiveHome {VERSION_STRING} 启动中...")
logger.info("=" * 60)

app = FastAPI(
    title="SpeedHiveHome",
    description="基于Lucky设备状态的智能限速控制",
    version=VERSION_INFO['version']
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
        self.service_control_file = Path("data/config/service_control.json")
        self.default_config = {
            "lucky_devices": [
                {
                    "name": "我的Lucky设备",
                    "api_url": "http://192.168.1.100:16601/api/webservice/rules?openToken=YOUR_LUCKY_OPEN_TOKEN_HERE",
                    "weight": 1.0,
                    "enabled": True,
                    "description": "主要监控设备"
                }
            ],
            "qbittorrent_instances": [
                {
                    "name": "我的QB实例",
                    "host": "http://192.168.1.101:8080",
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
                "normal_upload": 0,
            }
        }
        self._ensure_config_exists()
        self._ensure_service_control_exists()
    
    def _ensure_config_exists(self):
        """确保配置文件存在"""
        if not self.config_file.exists():
            print("📁 配置文件不存在，创建默认配置...")
            self.save_config(self.default_config)
    
    def _ensure_service_control_exists(self):
        """确保服务控制状态文件存在"""
        if not self.service_control_file.exists():
            print("📁 服务控制状态文件不存在，创建默认配置...")
            self.service_control_file.parent.mkdir(parents=True, exist_ok=True)
            self.save_service_control({})
    
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
    
    def load_service_control(self):
        """加载服务控制状态"""
        try:
            if not self.service_control_file.exists():
                return {}
            with open(self.service_control_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 服务控制状态加载失败: {e}")
            return {}
    
    def save_service_control(self, service_control):
        """保存服务控制状态"""
        try:
            self.service_control_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.service_control_file, 'w', encoding='utf-8') as f:
                json.dump(service_control, f, ensure_ascii=False, indent=2)
            print("✅ 服务控制状态保存成功")
            return True
        except Exception as e:
            print(f"❌ 服务控制状态保存失败: {e}")
            return False
    
    def set_service_control_status(self, service_key: str, enabled: bool):
        """设置单个服务的控制状态"""
        service_control = self.load_service_control()
        service_control[service_key] = enabled
        return self.save_service_control(service_control)
    
    def get_service_control_status(self, service_key: str) -> bool:
        """获取单个服务的控制状态，默认为True（启用）"""
        service_control = self.load_service_control()
        return service_control.get(service_key, True)

class LuckyMonitor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.session = None
        self._session_created = False
    
    async def get_session(self):
        """获取或创建 HTTP 会话（连接池复用）"""
        if self.session is None or self.session.closed:
            # 配置连接池和超时 - 增强连接韧性
            timeout = aiohttp.ClientTimeout(
                total=20,           # 总超时增加到20秒
                connect=8,          # 连接超时增加到8秒
                sock_read=12,       # 读取超时增加到12秒
                sock_connect=8      # 套接字连接超时
            )
            connector = aiohttp.TCPConnector(
                verify_ssl=False,
                limit=15,           # 连接池大小增加到15
                limit_per_host=8,   # 每个主机的连接数增加到8
                ttl_dns_cache=300,  # DNS 缓存时间（秒）
                force_close=False,  # 复用连接
                enable_cleanup_closed=True,
                keepalive_timeout=60,  # Keep-Alive 超时
                family=0,  # 允许IPv4和IPv6
                use_dns_cache=True
            )
            # 禁用代理，避免代理问题影响Lucky设备连接
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                raise_for_status=False,
                trust_env=False,  # 不信任环境变量中的代理设置
                headers={'Connection': 'keep-alive', 'User-Agent': 'SpeedHiveHome/2.0'}
            )
            self._session_created = True
            logger.debug("✅ Lucky Monitor HTTP 会话已创建（已禁用代理，增强连接韧性）")
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
    
    async def get_device_connections(self, device_config: dict, max_retries: int = 3):
        """获取Lucky设备连接数 - 带重试机制"""
        for attempt in range(max_retries):
            try:
                session = await self.get_session()
                api_url = device_config["api_url"]
                
                if attempt > 0:
                    logger.info(f"🔄 {device_config['name']} - 重试采集数据 (尝试 {attempt + 1}/{max_retries})")
                    await asyncio.sleep(2 * attempt)  # 指数退避
                else:
                    print(f"🔍 采集Lucky数据: {device_config['name']}")
                
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        connections = self._parse_connections(data)
                        weighted_connections = connections * device_config.get("weight", 1.0)
                        
                        print(f"📊 {device_config['name']} - 连接数: {connections}, 加权: {weighted_connections}")
                        
                        # 解析详细的连接信息和服务信息
                        detailed_connections = self._parse_detailed_connections(data)
                        services_info = self._parse_lucky_services(data)
                        total_download_bytes = sum(conn.get("download_bytes", 0) for conn in detailed_connections)
                        total_upload_bytes = sum(conn.get("upload_bytes", 0) for conn in detailed_connections)
                        
                        return {
                            "success": True,
                            "device_name": device_config["name"],
                            "connections": connections,
                            "weighted_connections": weighted_connections,
                            "status": "online",
                            "last_update": datetime.now().isoformat(),
                            "raw_data": data,
                            "api_url": api_url,
                            "download_bytes": total_download_bytes,
                            "upload_bytes": total_upload_bytes,
                            "detailed_connections": detailed_connections,
                            "services": services_info,
                            "attempt": attempt + 1
                        }
                    else:
                        error_msg = f"HTTP {response.status}"
                        if attempt == max_retries - 1:  # 最后一次尝试
                            print(f"❌ {device_config['name']} - {error_msg} (已重试{max_retries}次)")
                        return {
                            "success": False,
                            "device_name": device_config["name"],
                            "connections": 0,
                            "weighted_connections": 0,
                            "status": "error",
                            "error": error_msg,
                            "last_update": datetime.now().isoformat(),
                            "attempt": attempt + 1
                        }
            except (aiohttp.ClientConnectorError, aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError) as e:
                error_msg = str(e)
                error_type = type(e).__name__
                
                if attempt == max_retries - 1:  # 最后一次尝试
                    logger.error(f"❌ {device_config['name']} - 采集异常 ({error_type}): {error_msg} (已重试{max_retries}次)")
                    return {
                        "success": False,
                        "device_name": device_config["name"],
                        "connections": 0,
                        "weighted_connections": 0,
                        "status": "error",
                        "error": f"{error_type}: {error_msg}",
                        "error_type": error_type,
                        "last_update": datetime.now().isoformat(),
                        "attempt": attempt + 1
                    }
                else:
                    logger.warning(f"⚠️ {device_config['name']} - 连接错误 ({error_type}): {error_msg}, 将在 {2 * (attempt + 1)} 秒后重试")
                    # 如果是连接重置错误，强制重新创建会话
                    if "Connection reset" in error_msg or "104" in error_msg:
                        logger.info(f"🔄 {device_config['name']} - 检测到连接重置，重新创建HTTP会话")
                        await self.close()
                        await asyncio.sleep(1)
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ {device_config['name']} - 未知异常: {error_msg}")
                return {
                    "success": False,
                    "device_name": device_config["name"],
                    "connections": 0,
                    "weighted_connections": 0,
                    "status": "error",
                    "error": error_msg,
                    "error_type": "Unknown",
                    "last_update": datetime.now().isoformat(),
                    "attempt": attempt + 1
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
                            "key": rule_key,  # 添加key字段，用于状态控制匹配
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
                        "key": rule_name,  # 添加key字段，用于状态控制匹配
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

    def _parse_lucky_services(self, data: dict) -> list:
        """解析Lucky API响应，提取服务信息"""
        try:
            print("🔍 开始解析Lucky服务数据...")
            services_info = []
            
            # 从ruleList中提取服务信息
            if "ruleList" in data and isinstance(data["ruleList"], list):
                for rule in data["ruleList"]:
                    rule_key = rule.get("RuleKey", "")
                    print(f"📋 处理规则: {rule.get('RuleName', 'Unknown')} (Key: {rule_key})")
                    
                    # 从ProxyList中提取每个代理服务
                    proxy_list = rule.get("ProxyList", [])
                    if isinstance(proxy_list, list):
                        print(f"  📡 找到 {len(proxy_list)} 个代理服务")
                        
                        for proxy in proxy_list:
                            service_info = {
                                "key": proxy.get("Key", ""),
                                "service_type": proxy.get("WebServiceType", "unknown"),
                                "enabled": proxy.get("Enable", False),
                                "locations": proxy.get("Locations", []),
                                "domains": proxy.get("Domains", []),
                                "Remark": proxy.get("Remark", ""),  # 保持原始字段名
                                "last_error": proxy.get("LastErrMsg", ""),
                                "cache_enabled": proxy.get("CacheEnabled", False),
                                "cache_size": proxy.get("CaCheTotalSize", 0),
                                "cache_files": proxy.get("CacheFilesTotal", 0),
                                "display_in_frontend": proxy.get("DisplayInFrontendList", True),
                                "coraza_waf": proxy.get("CorazaWAF", False),
                                "safe_ip_mode": proxy.get("SafeIPMode", ""),
                                "safe_user_agent_mode": proxy.get("SafeUserAgentMode", ""),
                                "basic_auth_enabled": proxy.get("EnableBasicAuth", False),
                                "basic_auth_users": proxy.get("BasicAuthUserList", ""),
                                "custom_output": proxy.get("CustomOutputText", "")
                            }
                            
                            # 只显示启用的服务（不限制display_in_frontend）
                            if service_info["enabled"]:
                                services_info.append(service_info)
                                print(f"    ✅ 服务 {service_info['Remark']}: {service_info['service_type']}")
                            else:
                                print(f"    ❌ 服务 {service_info['Remark']}: 已禁用")
                    else:
                        print(f"  ⚠️ ProxyList 不是数组: {type(proxy_list)}")
            
            print(f"📊 解析到 {len(services_info)} 个启用的服务信息")
            return services_info
            
        except Exception as e:
            print(f"❌ 解析服务信息失败: {e}")
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
            
            # 简化限速逻辑：总连接数 > 0 即触发限速
            has_connections = self.total_connections > 0
            
            # 详细日志显示限速判断条件
            logger.info(f"🔍 限速判断: 总连接数={self.total_connections:.1f} -> 触发限速={has_connections}")
            
            # 2. 状态机逻辑
            if has_connections and not self.is_limited:
                # 检测到连接，开始限速倒计时
                self.limit_timer += poll_interval
                self.normal_timer = 0
                
                logger.info(f"⚠️ 检测到 {self.total_connections:.1f} 个连接，限速倒计时: {self.limit_timer}/{limit_on_delay}秒")
                
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
        """采集所有设备的总连接数（禁用设备连接数+0，启用设备连接数正常累加）"""
        devices = config.get("lucky_devices", [])
        total = 0.0
        
        for device in devices:
            # 检查设备是否启用控制
            device_enabled = device.get("enabled", True)
            
            try:
                result = await self.lucky_monitor.get_device_connections(device)
                if result.get("success"):
                    # 获取详细连接信息
                    detailed_connections = result.get("detailed_connections", [])
                    device_connections = 0.0
                    
                    if device_enabled:
                        # 设备启用：只累加启用控制的服务连接数
                        service_control = self.config_manager.load_service_control()
                        for conn in detailed_connections:
                            service_key = conn.get("rule_name", "")
                            service_key_alt = conn.get("key", "")
                            
                            # 检查服务是否被禁用
                            is_service_disabled = (
                                (service_key in service_control and service_control[service_key] == False) or
                                (service_key_alt in service_control and service_control[service_key_alt] == False)
                            )
                            
                            if not is_service_disabled:
                                device_connections += conn.get("connections", 0)
                                logger.debug(f"📊 {device.get('name')} - 服务 {service_key or service_key_alt} 启用，连接数: {conn.get('connections', 0)}")
                            else:
                                logger.debug(f"📊 {device.get('name')} - 服务 {service_key or service_key_alt} 禁用，连接数: 0")
                        
                        logger.info(f"📊 {device.get('name')} - 设备启用，总连接数: {device_connections}")
                    else:
                        # 设备禁用：连接数+0
                        device_connections = 0.0
                        logger.info(f"📊 {device.get('name')} - 设备禁用，连接数: 0")
                    
                    total += device_connections
                    
            except Exception as e:
                logger.error(f"❌ 采集设备 {device.get('name')} 失败: {e}")
        
        logger.info(f"📊 总连接数: {total:.1f}")
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
        failed_instances = []
        
        for instance in instances:
            if not instance.get("enabled", True):
                continue
                
            # 尝试恢复，带重试机制
            success = await self._restore_instance_with_retry(instance, download_limit, upload_limit)
            
            if success:
                success_count += 1
                logger.info(f"✅ {instance['name']} 恢复全速成功")
            else:
                failed_instances.append(instance)
                logger.error(f"❌ {instance['name']} 恢复全速失败")
        
        self.last_action_time = datetime.now()
        logger.info(f"📊 全速恢复完成: {success_count}/{len(instances)} 个实例成功")
        
        # 如果有失败的实例，记录并尝试降级处理
        if failed_instances:
            await self._handle_failed_instances(failed_instances, download_limit, upload_limit)
    
    async def _restore_instance_with_retry(self, instance: dict, download_limit: int, upload_limit: int, max_retries: int = 3) -> bool:
        """带重试机制的实例恢复"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 {instance['name']} - 恢复尝试 {attempt + 1}/{max_retries}")
                
                # 如果是重试，先清除可能的过期缓存
                if attempt > 0:
                    instance_key = f"{instance['host']}_{instance['username']}"
                    if instance_key in self.qbit_manager.cookies:
                        del self.qbit_manager.cookies[instance_key]
                    if instance_key in self.qbit_manager.sid_cache:
                        del self.qbit_manager.sid_cache[instance_key]
                    logger.info(f"🔄 {instance['name']} - 已清除缓存，准备重新认证")
                    
                    # 等待一段时间再重试
                    await asyncio.sleep(2 * attempt)
                
                success = await self.qbit_manager.set_speed_limits(instance, download_limit, upload_limit)
                
                if success:
                    logger.info(f"✅ {instance['name']} - 恢复成功 (尝试 {attempt + 1})")
                    return True
                else:
                    logger.warning(f"⚠️ {instance['name']} - 恢复失败 (尝试 {attempt + 1})")
                    
            except Exception as e:
                logger.error(f"❌ {instance['name']} - 恢复异常 (尝试 {attempt + 1}): {e}")
        
        logger.error(f"❌ {instance['name']} - 所有重试均失败")
        return False
    
    async def _handle_failed_instances(self, failed_instances: list, download_limit: int, upload_limit: int):
        """处理恢复失败的实例"""
        logger.warning(f"🚨 {len(failed_instances)} 个实例恢复失败，开始降级处理")
        
        for instance in failed_instances:
            instance_name = instance['name']
            logger.warning(f"🔧 开始处理失败实例: {instance_name}")
            
            # 1. 尝试重新连接测试
            try:
                test_result = await self.qbit_manager.test_connection(instance)
                if test_result.get("success"):
                    logger.info(f"✅ {instance_name} - 连接测试成功，尝试最后一次恢复")
                    # 最后一次尝试
                    success = await self.qbit_manager.set_speed_limits(instance, download_limit, upload_limit)
                    if success:
                        logger.info(f"✅ {instance_name} - 最终恢复成功")
                        continue
                else:
                    logger.error(f"❌ {instance_name} - 连接测试失败: {test_result.get('message', '未知错误')}")
            except Exception as e:
                logger.error(f"❌ {instance_name} - 连接测试异常: {e}")
            
            # 2. 记录失败实例到文件，供后续手动处理
            await self._record_failed_instance(instance, download_limit, upload_limit)
            
            # 3. 发送告警（如果有配置）
            await self._send_failure_alert(instance)
    
    async def _record_failed_instance(self, instance: dict, download_limit: int, upload_limit: int):
        """记录失败的实例到文件"""
        try:
            failed_file = Path("data/logs/failed_instances.json")
            failed_file.parent.mkdir(parents=True, exist_ok=True)
            
            failure_record = {
                "timestamp": datetime.now().isoformat(),
                "instance": instance,
                "target_limits": {
                    "download": download_limit,
                    "upload": upload_limit
                },
                "action": "restore_normal_speed",
                "status": "failed"
            }
            
            # 读取现有记录
            existing_records = []
            if failed_file.exists():
                try:
                    with open(failed_file, 'r', encoding='utf-8') as f:
                        existing_records = json.load(f)
                except:
                    existing_records = []
            
            # 添加新记录
            existing_records.append(failure_record)
            
            # 只保留最近50条记录
            if len(existing_records) > 50:
                existing_records = existing_records[-50:]
            
            # 写入文件
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(existing_records, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📝 {instance['name']} - 失败记录已保存到 {failed_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存失败记录异常: {e}")
    
    async def _send_failure_alert(self, instance: dict):
        """发送失败告警（预留接口）"""
        # 这里可以扩展为发送邮件、微信通知等
        logger.warning(f"🚨 告警: {instance['name']} 恢复全速失败，需要手动处理")
    
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
        self.cookies = {}  # 存储每个实例的认证 Cookie (持久化缓存)
        self.sid_cache = {}  # SID缓存: {instance_key: {'sid': xxx, 'timestamp': xxx}}
        self.sid_lifetime = 3600  # SID 生命周期（秒），默认1小时
    
    async def get_session(self):
        """获取或创建 HTTP 会话（连接池复用）"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(
                total=15,           # 总超时增加到15秒
                connect=8,          # 连接超时增加到8秒
                sock_read=10,       # 读取超时增加到10秒
                sock_connect=8      # 套接字连接超时
            )
            connector = aiohttp.TCPConnector(
                verify_ssl=False,
                limit=25,           # 连接池大小增加到25
                limit_per_host=12,  # 每个主机的连接数增加到12
                ttl_dns_cache=300,
                force_close=False,
                enable_cleanup_closed=True,
                keepalive_timeout=60,  # Keep-Alive 超时
                family=0,  # 允许IPv4和IPv6
                use_dns_cache=True
            )
            # 禁用代理，避免代理问题影响qBittorrent连接
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                raise_for_status=False,
                trust_env=False,  # 不信任环境变量中的代理设置
                headers={'Connection': 'keep-alive', 'User-Agent': 'SpeedHiveHome/2.0'}
            )
            self._session_created = True
            logger.debug("✅ qBittorrent Manager HTTP 会话已创建（已禁用代理，增强连接韧性）")
        return self.session
    
    def _is_sid_valid(self, instance_key: str) -> bool:
        """检查缓存的SID是否仍然有效"""
        if instance_key not in self.sid_cache:
            return False
        
        cache_entry = self.sid_cache[instance_key]
        import time
        age = time.time() - cache_entry.get('timestamp', 0)
        
        # 如果SID超过生命周期，视为过期
        if age > self.sid_lifetime:
            logger.debug(f"SID已过期 ({age:.0f}秒 > {self.sid_lifetime}秒)")
            return False
        
        return True
    
    async def get_valid_cookies(self, instance_config: dict):
        """获取有效的认证Cookie，如果缓存的SID有效则直接返回，否则重新登录
        
        这个方法确保了：
        1. 首次请求时自动登录
        2. 后续请求使用缓存的SID（1小时内有效）
        3. SID过期后自动重新登录
        """
        instance_key = f"{instance_config['host']}_{instance_config['username']}"
        
        # 检查是否有有效的缓存SID
        if self._is_sid_valid(instance_key):
            logger.debug(f"✓ 使用缓存的SID（跳过登录）: {instance_config['name']}")
            return self.cookies.get(instance_key)
        
        # SID无效或不存在，需要重新登录
        logger.info(f"⟳ SID无效或不存在，执行登录: {instance_config['name']}")
        login_success = await self.login_to_qbit(instance_config)
        
        if login_success:
            return self.cookies.get(instance_key)
        else:
            return None
    
    async def login_to_qbit(self, instance_config: dict) -> bool:
        """登录到 qBittorrent 并保存 Cookie"""
        try:
            session = await self.get_session()
            instance_key = f"{instance_config['host']}_{instance_config['username']}"
            
            # 登录 - 使用表单格式 (application/x-www-form-urlencoded)
            login_data = {
                "username": instance_config["username"],
                "password": instance_config["password"]
            }
            
            login_url = f"{instance_config['host']}/api/v2/auth/login"
            print(f"🔑 登录 qBittorrent: {login_url}")
            print(f"🔑 用户名: {instance_config['username']}")
            print(f"🔑 请求数据: username={instance_config['username']}&password=***")
            
            # 显式设置 Content-Type 为 application/x-www-form-urlencoded
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # 使用 data 参数发送表单数据
            async with session.post(login_url, data=login_data, headers=headers) as response:
                login_content = await response.text()
                print(f"🔑 登录响应状态: {response.status}")
                print(f"🔑 登录响应内容: {login_content}")
                print(f"🔑 响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    # 提取 Cookie，特别是 SID
                    cookies = response.cookies
                    
                    # 打印所有 Cookie
                    print(f"🍪 收到 Cookie 数量: {len(cookies)}")
                    for name, cookie in cookies.items():
                        print(f"🍪 Cookie: {name} = {cookie.value}")
                    
                    # 检查是否有 SID Cookie
                    sid_cookie = cookies.get('SID')
                    if sid_cookie:
                        self.cookies[instance_key] = cookies
                        # 缓存SID和时间戳
                        import time
                        self.sid_cache[instance_key] = {
                            'sid': sid_cookie.value,
                            'timestamp': time.time()
                        }
                        print(f"✅ 登录成功，SID已缓存: {sid_cookie.value[:20]}...")
                        logger.info(f"✅ {instance_config['name']} - 登录成功，SID已缓存")
                        return True
                    else:
                        # 检查 Set-Cookie 头
                        set_cookie_header = response.headers.get('Set-Cookie', '')
                        print(f"🍪 Set-Cookie 头: {set_cookie_header}")
                        
                        if 'SID=' in set_cookie_header:
                            # 手动解析 SID
                            import re
                            sid_match = re.search(r'SID=([^;]+)', set_cookie_header)
                            if sid_match:
                                sid_value = sid_match.group(1)
                                print(f"✅ 从 Set-Cookie 头提取 SID: {sid_value[:20]}...")
                                # 创建包含 SID 的 Cookie 对象
                                from aiohttp import CookieJar
                                jar = CookieJar()
                                jar.update_cookies({'SID': sid_value})
                                self.cookies[instance_key] = jar
                                # 缓存SID和时间戳
                                import time
                                self.sid_cache[instance_key] = {
                                    'sid': sid_value,
                                    'timestamp': time.time()
                                }
                                logger.info(f"✅ {instance_config['name']} - 登录成功，SID已缓存（从头部提取）")
                                return True
                        
                        # 即使没有明确的 SID，如果登录成功也保存 Cookie
                        self.cookies[instance_key] = cookies
                        print(f"⚠️ 登录成功但未找到 SID Cookie，保存所有 Cookie")
                        return True
                else:
                    # 详细的错误处理
                    error_msg = f"登录失败 (HTTP {response.status})"
                    
                    if response.status == 403:
                        if "封禁" in login_content or "banned" in login_content.lower():
                            error_msg = f"❌ IP地址已被封禁！原因：{login_content}"
                            print(error_msg)
                            print("💡 解决方法：")
                            print("   1. 在qBittorrent中解除IP封禁")
                            print("   2. 或重启qBittorrent服务清除封禁列表")
                            print("   3. 检查用户名密码是否正确")
                        else:
                            error_msg = f"❌ 访问被禁止 (403)：{login_content}"
                            print(error_msg)
                            print("💡 可能原因：IP白名单限制或权限不足")
                    elif response.status == 401:
                        error_msg = f"❌ 认证失败 (401)：用户名或密码错误"
                        print(error_msg)
                        print(f"💡 当前用户名: {instance_config['username']}")
                        print("💡 请检查用户名和密码是否正确")
                    else:
                        print(f"❌ 登录失败: HTTP {response.status}")
                        print(f"❌ 响应内容: {login_content}")
                    
                    return False
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            print(f"❌ 异常类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_connection(self, instance_config: dict):
        """测试qBittorrent连接"""
        try:
            print(f"🔍 测试QB连接: {instance_config['host']}")
            
            session = await self.get_session()
            
            # 使用缓存机制获取有效的 Cookie（只在需要时才登录）
            cookies = await self.get_valid_cookies(instance_config)
            if not cookies:
                return {
                    "success": False,
                    "status": "auth_failed",
                    "message": "登录失败，请查看上方的详细错误信息"
                }
            
            # 使用 Cookie 测试传输信息
            transfer_url = f"{instance_config['host']}/api/v2/transfer/info"
            print(f"📊 测试传输信息: {transfer_url}")
            
            async with session.get(transfer_url, cookies=cookies) as transfer_response:
                transfer_content = await transfer_response.text()
                print(f"📊 传输响应: {transfer_response.status} - {transfer_content[:200]}...")
                
                if transfer_response.status == 200:
                    return {
                        "success": True,
                        "status": "connected",
                        "message": "连接成功"
                    }
                elif transfer_response.status == 403:
                    # Cookie 可能过期，清除并重试
                    del self.cookies[instance_key]
                    return {
                        "success": False,
                        "status": "forbidden",
                        "message": f"403 禁止访问 - Cookie 可能过期，请重试"
                    }
                else:
                    return {
                        "success": False,
                        "status": "error", 
                        "message": f"数据传输失败: {transfer_response.status} - {transfer_content}"
                    }
        except Exception as e:
            error_msg = f"连接失败: {str(e)}"
            print(f"❌ QB连接异常: {error_msg}")
            return {
                "success": False,
                "status": "error",
                "message": error_msg
            }
    
    async def get_instance_status(self, instance_config: dict, max_retries: int = 3):
        """获取qBittorrent实例状态 - 带重试机制"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"🔄 {instance_config['name']} - 重试获取状态 (尝试 {attempt + 1}/{max_retries})")
                    await asyncio.sleep(2 * attempt)  # 指数退避
                else:
                    logger.debug(f"🔍 采集QB状态: {instance_config['name']}")
                
                session = await self.get_session()
                
                # 使用缓存机制获取有效的 Cookie
                cookies = await self.get_valid_cookies(instance_config)
                if not cookies:
                    return {
                        "success": False,
                        "instance_name": instance_config["name"],
                        "status": "offline",
                        "error": "认证失败",
                        "download_speed": 0,
                        "upload_speed": 0,
                        "active_downloads": 0,
                        "active_seeds": 0,
                        "total_torrents": 0,
                        "connection_status": "disconnected",
                        "last_update": datetime.now().isoformat(),
                        "attempt": attempt + 1
                    }
                
                # 获取传输信息 - 使用更长的超时时间
                transfer_url = f"{instance_config['host']}/api/v2/transfer/info"
                try:
                    async with session.get(transfer_url, cookies=cookies, timeout=aiohttp.ClientTimeout(total=10)) as transfer_response:
                        if transfer_response.status == 200:
                            transfer_info = await transfer_response.json()
                            
                            # 获取种子列表
                            torrents_url = f"{instance_config['host']}/api/v2/torrents/info"
                            try:
                                async with session.get(torrents_url, cookies=cookies, timeout=aiohttp.ClientTimeout(total=10)) as torrents_response:
                                    torrents_info = await torrents_response.json() if torrents_response.status == 200 else []
                            except Exception:
                                # 种子列表获取失败，使用空列表
                                torrents_info = []
                            
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
                                "connection_status": transfer_info.get("connection_status", "unknown"),
                                "last_update": datetime.now().isoformat(),
                                "attempt": attempt + 1
                            }
                            
                            logger.debug(f"✅ {instance_config['name']} - 在线, 下载: {status_data['download_speed']} B/s, 上传: {status_data['upload_speed']} B/s")
                            return status_data
                        elif transfer_response.status == 403:
                            # Cookie 过期，清除缓存和Cookie
                            instance_key = f"{instance_config['host']}_{instance_config['username']}"
                            if instance_key in self.cookies:
                                del self.cookies[instance_key]
                            if instance_key in self.sid_cache:
                                del self.sid_cache[instance_key]
                            logger.warning(f"⚠️ {instance_config['name']} - Cookie已过期，已清除缓存")
                            return {
                                "success": False,
                                "instance_name": instance_config["name"],
                                "status": "offline",
                                "error": "认证过期",
                                "download_speed": 0,
                                "upload_speed": 0,
                                "active_downloads": 0,
                                "active_seeds": 0,
                                "total_torrents": 0,
                                "connection_status": "disconnected",
                                "last_update": datetime.now().isoformat(),
                                "attempt": attempt + 1
                            }
                        else:
                            if attempt == max_retries - 1:
                                logger.warning(f"⚠️ {instance_config['name']} - HTTP {transfer_response.status} (已重试{max_retries}次)")
                            return {
                                "success": False,
                                "instance_name": instance_config["name"],
                                "status": "offline",
                                "error": f"服务异常 (HTTP {transfer_response.status})",
                                "download_speed": 0,
                                "upload_speed": 0,
                                "active_downloads": 0,
                                "active_seeds": 0,
                                "total_torrents": 0,
                                "connection_status": "disconnected",
                                "last_update": datetime.now().isoformat(),
                                "attempt": attempt + 1
                            }
                except (aiohttp.ClientConnectorError, aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError) as e:
                    error_msg = str(e)
                    error_type = type(e).__name__
                    
                    if attempt == max_retries - 1:
                        logger.error(f"❌ {instance_config['name']} - 连接异常 ({error_type}): {error_msg} (已重试{max_retries}次)")
                        return {
                            "success": False,
                            "instance_name": instance_config["name"],
                            "status": "offline",
                            "error": f"{error_type}: {error_msg}",
                            "error_type": error_type,
                            "download_speed": 0,
                            "upload_speed": 0,
                            "active_downloads": 0,
                            "active_seeds": 0,
                            "total_torrents": 0,
                            "connection_status": "disconnected",
                            "last_update": datetime.now().isoformat(),
                            "attempt": attempt + 1
                        }
                    else:
                        logger.warning(f"⚠️ {instance_config['name']} - 连接错误 ({error_type}): {error_msg}, 将在 {2 * (attempt + 1)} 秒后重试")
                        # 如果是连接重置错误，清除认证缓存
                        if "Connection reset" in error_msg or "104" in error_msg:
                            logger.info(f"🔄 {instance_config['name']} - 检测到连接重置，清除认证缓存")
                            instance_key = f"{instance_config['host']}_{instance_config['username']}"
                            if instance_key in self.cookies:
                                del self.cookies[instance_key]
                            if instance_key in self.sid_cache:
                                del self.sid_cache[instance_key]
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ {instance_config['name']} - 未知异常: {error_msg}")
                return {
                    "success": False,
                    "instance_name": instance_config["name"],
                    "status": "offline",
                    "error": error_msg,
                    "error_type": "Unknown",
                    "download_speed": 0,
                    "upload_speed": 0,
                    "active_downloads": 0,
                    "active_seeds": 0,
                    "total_torrents": 0,
                    "connection_status": "disconnected",
                    "last_update": datetime.now().isoformat(),
                    "attempt": attempt + 1
                }
    
    async def set_speed_limits(self, instance_config: dict, download_limit: int, upload_limit: int, max_retries: int = 3) -> bool:
        """设置速度限制（KB/s） - 带重试机制"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"🔄 {instance_config['name']} - 重试设置速度限制 (尝试 {attempt + 1}/{max_retries})")
                    await asyncio.sleep(2 * attempt)  # 指数退避
                else:
                    logger.info(f"🎚️ 设置速度限制: {instance_config['name']} - 下载: {download_limit} KB/s, 上传: {upload_limit} KB/s")
                
                session = await self.get_session()
                instance_key = f"{instance_config['host']}_{instance_config['username']}"
                
                # 使用缓存机制获取有效的 Cookie
                cookies = await self.get_valid_cookies(instance_config)
                if not cookies:
                    logger.error(f"❌ {instance_config['name']} - 无法获取有效Cookie")
                    return False
                
                # 设置全局下载限制
                dl_limit_url = f"{instance_config['host']}/api/v2/transfer/setDownloadLimit"
                dl_limit_data = {"limit": download_limit * 1024}  # 转换为 bytes/s
                
                dl_success = False
                dl_error = ""
                try:
                    async with session.post(dl_limit_url, data=dl_limit_data, cookies=cookies, timeout=aiohttp.ClientTimeout(total=10)) as dl_response:
                        dl_success = dl_response.status == 200
                        if not dl_success:
                            dl_error = f"HTTP {dl_response.status}"
                            response_text = await dl_response.text()
                            if attempt == max_retries - 1:
                                logger.error(f"❌ {instance_config['name']} - 下载限制设置失败: {dl_error}, 响应: {response_text}")
                except (aiohttp.ClientConnectorError, aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError) as e:
                    dl_error = f"{type(e).__name__}: {str(e)}"
                    if attempt == max_retries - 1:
                        logger.error(f"❌ {instance_config['name']} - 下载限制请求异常: {e}")
                except Exception as e:
                    dl_error = f"请求异常: {str(e)}"
                    if attempt == max_retries - 1:
                        logger.error(f"❌ {instance_config['name']} - 下载限制请求异常: {e}")
                
                # 设置全局上传限制
                up_limit_url = f"{instance_config['host']}/api/v2/transfer/setUploadLimit"
                up_limit_data = {"limit": upload_limit * 1024}  # 转换为 bytes/s
                
                up_success = False
                up_error = ""
                try:
                    async with session.post(up_limit_url, data=up_limit_data, cookies=cookies, timeout=aiohttp.ClientTimeout(total=10)) as up_response:
                        up_success = up_response.status == 200
                        if not up_success:
                            up_error = f"HTTP {up_response.status}"
                            response_text = await up_response.text()
                            if attempt == max_retries - 1:
                                logger.error(f"❌ {instance_config['name']} - 上传限制设置失败: {up_error}, 响应: {response_text}")
                except (aiohttp.ClientConnectorError, aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError) as e:
                    up_error = f"{type(e).__name__}: {str(e)}"
                    if attempt == max_retries - 1:
                        logger.error(f"❌ {instance_config['name']} - 上传限制请求异常: {e}")
                except Exception as e:
                    up_error = f"请求异常: {str(e)}"
                    if attempt == max_retries - 1:
                        logger.error(f"❌ {instance_config['name']} - 上传限制请求异常: {e}")
                
                success = dl_success and up_success
                if success:
                    logger.info(f"✅ {instance_config['name']} - 速度限制设置成功 (尝试 {attempt + 1})")
                    return True
                else:
                    # 检查是否是连接重置错误
                    if any("Connection reset" in err or "104" in err for err in [dl_error, up_error]):
                        logger.warning(f"⚠️ {instance_config['name']} - 检测到连接重置，清除认证缓存")
                        if instance_key in self.cookies:
                            del self.cookies[instance_key]
                        if instance_key in self.sid_cache:
                            del self.sid_cache[instance_key]
                    
                    # 如果失败，可能是 Cookie 过期，清除缓存
                    if any("403" in err for err in [dl_error, up_error]):
                        if instance_key in self.cookies:
                            del self.cookies[instance_key]
                        if instance_key in self.sid_cache:
                            del self.sid_cache[instance_key]
                        logger.warning(f"⚠️ {instance_config['name']} - Cookie已过期，已清除缓存")
                    
                    if attempt == max_retries - 1:
                        error_details = []
                        if not dl_success:
                            error_details.append(f"下载: {dl_error}")
                        if not up_success:
                            error_details.append(f"上传: {up_error}")
                        logger.error(f"❌ {instance_config['name']} - 速度限制设置失败 (已重试{max_retries}次) - {', '.join(error_details)}")
                    else:
                        logger.warning(f"⚠️ {instance_config['name']} - 速度限制设置失败，将在 {2 * (attempt + 1)} 秒后重试")
                        
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"❌ {instance_config['name']} - 设置速度限制异常: {e}")
                    import traceback
                    logger.error(f"❌ 异常详情: {traceback.format_exc()}")
                else:
                    logger.warning(f"⚠️ {instance_config['name']} - 设置速度限制异常，将在 {2 * (attempt + 1)} 秒后重试: {e}")
        
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
        "message": "SpeedHiveHome 服务已启动",
        "version": VERSION_INFO['version'],
        "version_string": VERSION_STRING,
        "commit_hash": VERSION_INFO['commit_hash'],
        "build_time": VERSION_INFO['build_time'],
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
        "tests": [],
        "cookies_stored": len(qbit_manager.cookies)
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
                    cookies = response.cookies
                    debug_info["tests"].append({
                        "test": "登录认证",
                        "url": login_url,
                        "status": response.status,
                        "success": response.status == 200,
                        "message": f"HTTP {response.status} - {content[:100]}",
                        "cookies_received": len(cookies),
                        "cookie_names": list(cookies.keys()),
                        "response_headers": dict(response.headers)
                    })
                    
                    # 如果登录成功，测试带 Cookie 的请求
                    if response.status == 200 and cookies:
                        transfer_url = f"{instance['host']}/api/v2/transfer/info"
                        async with session.get(transfer_url, cookies=cookies, timeout=10) as transfer_response:
                            transfer_content = await transfer_response.text()
                            debug_info["tests"].append({
                                "test": "带Cookie的传输信息",
                                "url": transfer_url,
                                "status": transfer_response.status,
                                "success": transfer_response.status == 200,
                                "message": f"HTTP {transfer_response.status} - {transfer_content[:100]}",
                                "response_headers": dict(transfer_response.headers)
                            })
            except Exception as e:
                debug_info["tests"].append({
                    "test": "登录认证",
                    "url": login_url,
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

@app.get("/api/test/connection")
async def test_connection():
    """测试连接 - 简单测试"""
    return {
        "success": True,
        "message": "API 连接正常",
        "timestamp": datetime.now().isoformat()
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

@app.post("/api/controller/restore/{instance_index}")
async def manual_restore_instance(instance_index: int):
    """手动恢复指定实例的全速"""
    try:
        config = config_manager.load_config()
        instances = config.get("qbittorrent_instances", [])
        
        if instance_index < 0 or instance_index >= len(instances):
            raise HTTPException(status_code=404, detail="实例不存在")
        
        instance = instances[instance_index]
        settings = config.get("controller_settings", {})
        download_limit = settings.get("normal_download", 0)
        upload_limit = settings.get("normal_upload", 0)
        
        logger.info(f"🔧 手动恢复实例: {instance['name']}")
        
        # 使用重试机制恢复
        success = await speed_controller._restore_instance_with_retry(
            instance, download_limit, upload_limit, max_retries=5
        )
        
        if success:
            return {
                "message": f"实例 {instance['name']} 恢复成功",
                "status": "success",
                "instance": instance['name'],
                "limits": {
                    "download": download_limit,
                    "upload": upload_limit
                }
            }
        else:
            return {
                "message": f"实例 {instance['name']} 恢复失败",
                "status": "failed",
                "instance": instance['name'],
                "suggestion": "请检查实例连接状态或手动重启qBittorrent"
            }
            
    except Exception as e:
        logger.error(f"手动恢复实例异常: {e}")
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")

@app.post("/api/controller/restore-all")
async def manual_restore_all_instances():
    """手动恢复所有实例的全速"""
    try:
        config = config_manager.load_config()
        settings = config.get("controller_settings", {})
        download_limit = settings.get("normal_download", 0)
        upload_limit = settings.get("normal_upload", 0)
        
        logger.info("🔧 手动恢复所有实例")
        
        # 直接调用恢复方法
        await speed_controller._apply_normal_mode(settings)
        
        return {
            "message": "所有实例恢复操作已完成",
            "status": "success",
            "limits": {
                "download": download_limit,
                "upload": upload_limit
            }
        }
        
    except Exception as e:
        logger.error(f"手动恢复所有实例异常: {e}")
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")

@app.get("/api/controller/failed-instances")
async def get_failed_instances():
    """获取失败的实例记录"""
    try:
        failed_file = Path("data/logs/failed_instances.json")
        
        if not failed_file.exists():
            return {
                "message": "没有失败记录",
                "failed_instances": []
            }
        
        with open(failed_file, 'r', encoding='utf-8') as f:
            failed_records = json.load(f)
        
        # 只返回最近10条记录
        recent_records = failed_records[-10:] if len(failed_records) > 10 else failed_records
        
        return {
            "message": f"找到 {len(failed_records)} 条失败记录",
            "failed_instances": recent_records,
            "total_count": len(failed_records)
        }
        
    except Exception as e:
        logger.error(f"获取失败记录异常: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败记录失败: {str(e)}")

@app.post("/api/controller/reset-connections")
async def reset_all_connections():
    """重置所有连接会话 - 解决连接重置问题"""
    try:
        logger.info("🔄 开始重置所有连接会话...")
        
        # 重置 Lucky Monitor 会话
        await lucky_monitor.close()
        logger.info("✅ Lucky Monitor 会话已重置")
        
        # 重置 qBittorrent Manager 会话
        await qbit_manager.close()
        logger.info("✅ qBittorrent Manager 会话已重置")
        
        # 清除所有认证缓存
        qbit_manager.cookies.clear()
        qbit_manager.sid_cache.clear()
        logger.info("✅ 认证缓存已清除")
        
        return {
            "message": "所有连接会话已重置",
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "actions": [
                "Lucky Monitor 会话已重置",
                "qBittorrent Manager 会话已重置", 
                "认证缓存已清除"
            ]
        }
        
    except Exception as e:
        logger.error(f"重置连接会话异常: {e}")
        raise HTTPException(status_code=500, detail=f"重置连接失败: {str(e)}")

@app.get("/api/controller/connection-health")
async def get_connection_health():
    """获取连接健康状态"""
    try:
        config = config_manager.load_config()
        
        # 检查 Lucky 设备连接
        lucky_devices = config.get("lucky_devices", [])
        lucky_health = []
        for device in lucky_devices:
            if device.get("enabled", True):
                try:
                    result = await lucky_monitor.test_connection(device["api_url"])
                    lucky_health.append({
                        "device_name": device["name"],
                        "status": "healthy" if result.get("success") else "unhealthy",
                        "details": result
                    })
                except Exception as e:
                    lucky_health.append({
                        "device_name": device["name"],
                        "status": "error",
                        "details": {"error": str(e)}
                    })
        
        # 检查 qBittorrent 实例连接
        qbit_instances = config.get("qbittorrent_instances", [])
        qbit_health = []
        for instance in qbit_instances:
            if instance.get("enabled", True):
                try:
                    result = await qbit_manager.test_connection(instance)
                    qbit_health.append({
                        "instance_name": instance["name"],
                        "status": "healthy" if result.get("success") else "unhealthy",
                        "details": result
                    })
                except Exception as e:
                    qbit_health.append({
                        "instance_name": instance["name"],
                        "status": "error",
                        "details": {"error": str(e)}
                    })
        
        # 统计连接状态
        total_lucky = len(lucky_health)
        healthy_lucky = len([h for h in lucky_health if h["status"] == "healthy"])
        total_qbit = len(qbit_health)
        healthy_qbit = len([h for h in qbit_health if h["status"] == "healthy"])
        
        overall_status = "healthy" if (healthy_lucky == total_lucky and healthy_qbit == total_qbit) else "degraded"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "lucky_devices": {
                "total": total_lucky,
                "healthy": healthy_lucky,
                "unhealthy": total_lucky - healthy_lucky,
                "details": lucky_health
            },
            "qbittorrent_instances": {
                "total": total_qbit,
                "healthy": healthy_qbit,
                "unhealthy": total_qbit - healthy_qbit,
                "details": qbit_health
            },
            "connection_pools": {
                "lucky_session_active": lucky_monitor.session is not None and not lucky_monitor.session.closed,
                "qbit_session_active": qbit_manager.session is not None and not qbit_manager.session.closed,
                "qbit_cookies_cached": len(qbit_manager.cookies),
                "qbit_sid_cached": len(qbit_manager.sid_cache)
            }
        }
        
    except Exception as e:
        logger.error(f"获取连接健康状态异常: {e}")
        raise HTTPException(status_code=500, detail=f"获取连接健康状态失败: {str(e)}")

@app.get("/api/lucky/service-control")
async def get_service_control_status():
    """获取所有服务的控制状态"""
    try:
        service_control = config_manager.load_service_control()
        return {
            "service_control": service_control,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取服务控制状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务控制状态失败: {str(e)}")

@app.post("/api/lucky/service-control")
async def set_service_control_status(request: Request):
    """设置服务控制状态"""
    try:
        data = await request.json()
        service_key = data.get("service_key")
        enabled = data.get("enabled", True)
        
        if not service_key:
            raise HTTPException(status_code=400, detail="缺少service_key参数")
        
        success = config_manager.set_service_control_status(service_key, enabled)
        
        if success:
            logger.info(f"✅ 服务控制状态已更新: {service_key} = {enabled}")
            return {
                "message": f"服务 {service_key} 控制状态已设置为 {'启用' if enabled else '禁用'}",
                "status": "success",
                "service_key": service_key,
                "enabled": enabled,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="保存服务控制状态失败")
            
    except Exception as e:
        logger.error(f"设置服务控制状态失败: {e}")
        raise HTTPException(status_code=400, detail=f"设置服务控制状态失败: {str(e)}")

@app.put("/api/lucky/service-control/batch")
async def batch_set_service_control_status(request: Request):
    """批量设置服务控制状态"""
    try:
        data = await request.json()
        service_controls = data.get("service_controls", {})
        
        if not isinstance(service_controls, dict):
            raise HTTPException(status_code=400, detail="service_controls必须是字典格式")
        
        # 加载现有状态
        current_control = config_manager.load_service_control()
        
        # 更新状态
        current_control.update(service_controls)
        
        # 保存状态
        success = config_manager.save_service_control(current_control)
        
        if success:
            logger.info(f"✅ 批量更新服务控制状态: {len(service_controls)} 个服务")
            return {
                "message": f"已批量更新 {len(service_controls)} 个服务的控制状态",
                "status": "success",
                "updated_count": len(service_controls),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="批量保存服务控制状态失败")
            
    except Exception as e:
        logger.error(f"批量设置服务控制状态失败: {e}")
        raise HTTPException(status_code=400, detail=f"批量设置服务控制状态失败: {str(e)}")

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
    
    print("=" * 60)
    print(f"🚀 智能 qBittorrent 限速控制器 {VERSION_STRING}")
    print("=" * 60)
    print("✅ 所有依赖加载成功，启动 Web 服务器...")
    print(f"📊 服务地址: http://{host}:{port}")
    print(f"🔖 版本信息: {VERSION_INFO['commit_hash']} ({VERSION_INFO['build_time']})")
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
    print("=" * 60)
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info",
        access_log=True
    )
