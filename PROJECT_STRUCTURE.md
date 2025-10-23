# qbit-smart-controller 项目结构

## 📁 核心目录
- `app/` - 主应用程序代码
- `config/` - 配置文件
- `data/` - 数据文件（日志、服务控制状态等）

## 📄 核心文件
- `app/main.py` - 主应用程序（FastAPI应用）
- `requirements.txt` - Python依赖
- `Dockerfile` - Docker镜像构建文件
- `docker-compose.yml` - Docker Compose配置
- `version.py` - 版本信息

## 🚀 部署脚本
- `deploy.sh` - 标准部署脚本
- `deploy_docker_cmd.sh` - Docker命令部署
- `deploy_custom_path.sh` - 自定义路径部署
- `package_for_deployment.py` - 创建部署包
- `deploy_to_remote.py` - 远程部署脚本
- `git_deploy.py` - Git部署脚本

## ⚙️ 配置管理
- `init_config.sh` - 初始化配置
- `fix_config.sh` - 修复配置
- `reset.sh` - 重置应用
- `update.sh` - 更新应用

## 📚 文档
- `README.md` - 项目说明
- `MANUAL.md` - 使用手册
- `FAQ.md` - 常见问题
- `CUSTOM_PATH_DEPLOYMENT.md` - 自定义部署说明

## 🔧 工具脚本
- `test_qb_connection.sh` - 测试qBittorrent连接
- `diagnose.sh` - 诊断脚本
- `quick_update.sh` - 快速更新
- `redeploy.sh` - 重新部署
