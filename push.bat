@echo off
chcp 65001 >nul
echo ========================================
echo   一键推送到 GitHub
echo ========================================
echo.

echo [1/3] 添加所有更改...
git add .
if %errorlevel% neq 0 (
    echo 错误：git add 失败
    pause
    exit /b 1
)
echo ✓ 文件已添加

echo.
echo [2/3] 提交更改...
set /p commit_msg="请输入提交信息（直接回车使用默认）: "
if "%commit_msg%"=="" set commit_msg=Update: 更新代码

git commit -m "%commit_msg%"
if %errorlevel% neq 0 (
    echo 注意：没有需要提交的更改，或提交失败
)

echo.
echo [3/3] 推送到 GitHub...
:retry
git push origin main
if %errorlevel% neq 0 (
    echo.
    echo 推送失败！可能的原因：
    echo 1. 网络连接问题
    echo 2. 认证失败
    echo 3. 远程仓库问题
    echo.
    choice /C YN /M "是否重试"
    if errorlevel 2 goto end
    if errorlevel 1 goto retry
)

echo.
echo ========================================
echo   ✓ 推送成功！
echo ========================================
echo.
echo 仓库地址: https://github.com/myptyun/qbit-smart-controller
echo.

:end
pause

