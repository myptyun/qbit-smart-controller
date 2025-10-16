@echo off
chcp 65001 >nul
echo 🚀 智能 qBittorrent 限速控制器 - 启动脚本
echo ==========================================

REM 检查 Docker 是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Docker 未运行
    echo 请先启动 Docker Desktop
    pause
    exit /b 1
)

REM 检查配置文件
if not exist "config\config.yaml" (
    echo ⚠️  警告: 未找到配置文件 config\config.yaml
    if exist "data\config\config.example.yaml" (
        echo 📋 复制示例配置文件...
        if not exist "config" mkdir config
        copy "data\config\config.example.yaml" "config\config.yaml"
        echo ✅ 已创建配置文件，请编辑 config\config.yaml 后重新启动
        pause
        exit /b 0
    ) else (
        echo ❌ 错误: 未找到示例配置文件
        pause
        exit /b 1
    )
)

REM 创建必要的目录
echo 📁 创建必要的目录...
if not exist "data\logs" mkdir data\logs
if not exist "data\config" mkdir data\config
if not exist "config" mkdir config

REM 停止旧容器
echo 🛑 停止旧容器...
docker-compose down

REM 构建并启动
echo 🔨 构建并启动容器...
docker-compose up -d --build

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 5 /nobreak >nul

REM 检查服务状态
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo.
    echo ❌ 服务启动失败
    echo 请查看日志: docker-compose logs
    pause
    exit /b 1
) else (
    echo.
    echo ✅ 服务启动成功！
    echo.
    echo 📊 访问 Web 界面: http://localhost:5000
    echo 📝 查看日志: docker-compose logs -f
    echo 🛑 停止服务: docker-compose down
    echo.
    echo 按任意键退出...
    pause >nul
)

