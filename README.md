
# 🚀 SpeedHiveHome

基于 Lucky 软路由设备状态的智能 qBittorrent 限速控制系统。当 Lucky 检测到网络活动时，自动限制 qBittorrent 的上传/下载速度，确保不影响正常上网体验。

## ✨ 核心功能

### 🎯 自动限速控制
- **智能检测**：实时监控 Lucky 设备的网络连接数
- **延迟触发**：支持限速触发延迟和恢复延迟，避免频繁切换
- **加权计算**：支持多设备加权监控，灵活适应不同场景
- **平滑切换**：状态机设计，确保限速切换平稳可靠

### 📊 实时监控
- **多设备支持**：可同时监控多个 Lucky 设备
- **多实例管理**：支持控制多个 qBittorrent 实例
- **Web 界面**：现代化的实时监控仪表板
- **状态可视化**：直观显示限速状态、连接数、速度等信息

### 🔧 配置管理
- **YAML 配置**：简单直观的配置文件格式
- **灵活控制**：每个设备和实例可独立启用/禁用
- **参数调整**：轮询间隔、延迟时间、速度限制等全部可配置

### 📝 日志系统
- **多级日志**：控制台 + 文件日志
- **自动轮转**：日志文件大小控制和自动备份
- **错误追踪**：单独的错误日志文件便于排查问题

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web 控制面板                          │
│              (实时监控 + 状态显示)                        │
└─────────────────────────────────────────────────────────┘
                          ↕ API
┌─────────────────────────────────────────────────────────┐
│              SpeedController (核心控制器)                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │  状态机：正常 ⟷ 限速中                           │    │
│  │  - 检测连接数                                    │    │
│  │  - 倒计时控制                                    │    │
│  │  - 自动切换限速                                  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
         ↓ 监控                    ↓ 控制
┌──────────────────┐      ┌──────────────────┐
│  Lucky Monitor   │      │  qBit Manager    │
│  - API 轮询       │      │  - 速度限制       │
│  - 连接数解析     │      │  - 状态查询       │
│  - 加权计算       │      │  - 会话管理       │
└──────────────────┘      └──────────────────┘
         ↓                         ↓
┌──────────────────┐      ┌──────────────────┐
│  Lucky 设备      │      │  qBittorrent     │
│  (软路由)        │      │  (下载客户端)     │
└──────────────────┘      └──────────────────┘
```

## 📚 项目结构

```
qbit-smart-controller/
├── app/                    # 应用核心
│   ├── main.py            # 主程序
│   └── templates/
│       └── index.html     # Web界面
├── config/
│   └── config.yaml        # 主配置文件
├── data/                  # 数据目录
│   ├── config/            # 配置数据
│   └── logs/              # 日志目录
├── deploy.sh              # 标准部署脚本
├── diagnose.sh            # 诊断工具
├── docker-compose.yml     # Docker编排
├── Dockerfile             # Docker镜像
├── init_config.sh         # 配置初始化
├── test_qb_connection.sh  # 连接测试
├── update.sh              # 更新脚本
└── version.py             # 版本信息
```

## 🛠️ 实用工具脚本

- **`init_config.sh`** - 初始化配置文件和目录
- **`diagnose.sh`** - 诊断容器和配置问题
- **`fix_config.sh`** - 快速修复配置问题
- **`test_qb_connection.sh`** - 测试 qBittorrent 连接和认证
- **`deploy.sh`** - 标准部署脚本
- **`update.sh`** - 项目更新脚本

## 🚀 快速开始

### 前置要求

- Docker 和 Docker Compose
- Lucky 软路由（支持 API 访问）
- qBittorrent（支持 Web API）

### 1. 克隆项目

```bash
git clone https://github.com/myptyun/qbit-smart-controller.git
cd qbit-smart-controller
```

### 2. 配置文件

编辑 `config/config.yaml`：

```yaml
# Lucky 设备配置
lucky_devices:
  - name: "我的Lucky设备"
    api_url: "http://192.168.1.100:16601/api/webservice/rules?openToken=YOUR_LUCKY_TOKEN"
    weight: 1.0  # 权重：1.0=正常，0.5=减半影响，2.0=加倍影响
    enabled: true
    description: "主要监控设备"
  
  # 示例：多设备配置（注释掉，需要时取消注释）
  # - name: "次要Lucky设备"
  #   api_url: "http://192.168.1.101:16601/api/webservice/rules?openToken=YOUR_SECOND_TOKEN"
  #   weight: 0.5  # 权重减半，影响较小
  #   enabled: false
  #   description: "次要监控设备"

# qBittorrent 实例配置
qbittorrent_instances:
  - name: "我的QB实例"
    host: "http://192.168.1.200:8080"  # 改为您实际的QB地址
    username: "admin"
    password: "your_password"
    enabled: true
    description: "主下载服务器"

# 控制器设置
controller_settings:
  poll_interval: 1  # 减少到1秒，提高响应速度
  limit_on_delay: 5
  limit_off_delay: 30
  retry_interval: 10
  limited_download: 1024
  limited_upload: 512
  normal_download: 0
  normal_upload: 0

# Web服务器设置
web_settings:
  host: "0.0.0.0"  # 绑定到所有网络接口，允许外部访问
  port: 5000       # 服务端口
```

### 3. 启动服务

```bash
# 使用 Docker Compose 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 4. 访问界面

打开浏览器访问：`http://localhost:5000`

## 🔄 更新项目

### 标准更新

适用于日常代码更新：

```bash
cd ~/qbit-smart-controller
./update.sh
```

### 重新部署

遇到问题时使用：

```bash
cd ~/qbit-smart-controller
./deploy.sh
```

### 诊断问题

```bash
cd ~/qbit-smart-controller
./diagnose.sh
```

## 📖 详细说明

### 配置参数详解

#### Lucky 设备配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `name` | 设备名称（自定义） | 必填 |
| `api_url` | Lucky API 地址（包含 token） | 必填 |
| `weight` | 权重系数（用于多设备加权） | 1.0 |
| `enabled` | 是否启用此设备 | true |
| `description` | 设备描述 | 可选 |

**获取 Lucky API Token：**
1. 登录 Lucky 管理界面
2. 进入「系统设置」→「API 管理」
3. 生成或查看 Open Token
4. API 地址格式：`http://YOUR_LUCKY_IP:16601/api/webservice/rules?openToken=YOUR_LUCKY_TOKEN`

#### qBittorrent 配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `name` | 实例名称（自定义） | 必填 |
| `host` | qBittorrent Web UI 地址 | 必填 |
| `username` | Web UI 用户名 | 必填 |
| `password` | Web UI 密码 | 必填 |
| `enabled` | 是否启用此实例 | true |
| `description` | 实例描述 | 可选 |

**qBittorrent 配置要求：**
1. 启用 Web UI：「工具」→「选项」→「Web UI」
2. 允许远程连接
3. 记录用户名和密码
4. 默认端口：8080（可在 qBittorrent 中修改）

#### 控制器设置

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `poll_interval` | 状态采集频率（秒） | 2-5 |
| `limit_on_delay` | 限速触发延迟（秒） | 5-10 |
| `limit_off_delay` | 恢复全速延迟（秒） | 30-60 |
| `retry_interval` | 连接失败重试间隔（秒） | 10 |
| `limited_download` | 限速时下载速度（KB/s） | 1024 |
| `limited_upload` | 限速时上传速度（KB/s） | 512 |
| `normal_download` | 正常时下载速度（KB/s，0=不限速） | 0 |
| `normal_upload` | 正常时上传速度（KB/s，0=不限速） | 0 |

### 工作原理

```
1. Lucky 检测到网络连接
   ↓
2. 累积加权连接数 > 0
   ↓
3. 等待 limit_on_delay 秒
   ↓
4. 触发限速：设置为 limited_download/upload
   ↓
5. Lucky 连接消失
   ↓
6. 等待 limit_off_delay 秒
   ↓
7. 恢复全速：设置为 normal_download/upload
```

### 多设备权重计算

如果配置了多个 Lucky 设备，系统会计算加权总连接数：

```
总加权连接数 = Σ(设备连接数 × 设备权重)
```

**示例：**
- 设备A：3个连接，权重 1.0 → 贡献 3.0
- 设备B：2个连接，权重 0.5 → 贡献 1.0
- **总计：4.0 个加权连接**

### 前端显示说明

Web界面会智能显示连接数信息：

- **单设备场景**：显示"X个加权连接"（权重为1.0时与原始连接数相同）
- **多设备场景**：显示"X个加权连接"并显示原始连接数对比
- **限速状态**：实时显示加权连接数和倒计时信息

## 🔌 API 接口

### 状态查询

```bash
# 服务状态
GET /api/status

# 配置信息
GET /api/config

# Lucky 设备状态
GET /api/lucky/status

# qBittorrent 状态
GET /api/qbit/status

# 控制器状态
GET /api/controller/state

# 健康检查
GET /health
```

### 连接测试

```bash
# 测试 Lucky 连接
GET /api/test/lucky/{device_index}

# 测试 qBittorrent 连接
GET /api/test/qbit/{instance_index}
```

### 控制器管理

```bash
# 启动控制器
POST /api/controller/start

# 停止控制器
POST /api/controller/stop
```

### 服务控制

```bash
# 获取所有服务控制状态
GET /api/services/control

# 更新服务控制状态
POST /api/services/control
Content-Type: application/json
{
  "service_name": "服务名称",
  "enabled": true/false
}
```

## 📊 日志管理

### 日志位置

```
data/logs/
├── controller.log      # 主日志（10MB，保留5份）
├── error.log          # 错误日志（10MB，保留3份）
└── failed_instances.json  # 失败实例记录
```

### 查看日志

```bash
# 实时查看容器日志
docker-compose logs -f

# 查看文件日志
tail -f data/logs/controller.log

# 查看错误日志
tail -f data/logs/error.log

# 在容器内查看日志
docker exec -it qbit-smart-controller bash
tail -f /app/data/logs/controller.log
```

## 🐛 故障排查

### 1. Lucky 连接失败

**症状：** Web 界面显示 Lucky 设备离线或错误

**排查步骤：**
1. 检查 Lucky API 地址是否正确
2. 测试 API 访问：
   ```bash
   curl "http://YOUR_LUCKY_IP:16601/api/webservice/rules?openToken=YOUR_LUCKY_TOKEN"
   ```
3. 检查网络连通性
4. 验证 Token 是否过期
5. 查看日志：`grep "Lucky" data/logs/controller.log`

### 2. qBittorrent 连接失败

**症状：** Web 界面显示 QB 实例离线

**排查步骤：**
1. 确认 qBittorrent Web UI 已启用
2. 测试登录：
   ```bash
   curl -X POST "http://YOUR_QB_IP:8080/api/v2/auth/login" \
     -d "username=admin&password=your_password"
   ```
3. 检查用户名密码是否正确
4. 确认允许远程连接
5. 查看日志：`grep "QB" data/logs/controller.log`

### 3. 限速不生效

**症状：** 检测到连接但 qBittorrent 速度未改变

**排查步骤：**
1. 检查控制器状态：访问 `/api/controller/state`
2. 查看日志中的限速日志：
   ```bash
   grep "限速" data/logs/controller.log
   ```
3. 确认 qBittorrent 没有设置全局最大速度限制（会覆盖 API 设置）
4. 检查 qBittorrent 替代限速设置

### 4. 频繁切换限速状态

**症状：** 限速状态反复切换

**解决方案：**
1. 增加 `limit_on_delay` 和 `limit_off_delay`
2. 调整 Lucky 设备权重
3. 检查 Lucky 连接数是否稳定

## 🔧 高级配置

### 环境变量

在 `docker-compose.yml` 中可配置环境变量：

```yaml
environment:
  - TZ=Asia/Shanghai          # 时区
  - LOG_LEVEL=INFO            # 日志级别：DEBUG/INFO/WARNING/ERROR
  - PYTHONUNBUFFERED=1        # Python 输出不缓冲
```

### 自定义端口

修改 `docker-compose.yml`：

```yaml
ports:
  - "5000:5000"  # 改为你想要的端口，如 "8888:5000"
```

### 持久化数据

项目使用 Docker 卷持久化数据：

```yaml
volumes:
  - ./config:/app/config      # 配置文件
  - ./data:/app/data          # 日志和数据
```

## 📈 性能优化

### 资源占用

- CPU：< 1%（轻量级监控）
- 内存：< 50MB
- 磁盘：日志文件约 50MB（自动轮转）

### 优化建议

1. **轮询间隔**：根据实际需求调整 `poll_interval`
   - 高实时性要求：1-2秒
   - 普通场景：2-5秒
   - 低频检查：5-10秒

2. **延迟设置**：避免频繁切换
   - `limit_on_delay`：建议 5-10秒
   - `limit_off_delay`：建议 30-60秒

3. **多设备权重**：根据重要性分配权重
   - 主要设备：1.0
   - 次要设备：0.5-0.8

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [qBittorrent](https://www.qbittorrent.org/) - 优秀的 BT 客户端
- [Lucky](https://lucky666.cn/) - 强大的软路由工具

## 📞 支持

- 问题反馈：[GitHub Issues](https://github.com/myptyun/qbit-smart-controller/issues)
- 使用文档：[Wiki](https://github.com/myptyun/qbit-smart-controller/wiki)

---

**祝你使用愉快！如果觉得有用，请给个 ⭐ Star 吧！**

