@echo off
chcp 65001 >nul
title Stock Dashboard API Server

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║         Stock Dashboard API 服务器                   ║
echo ╚══════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0server"

echo [1/2] 检查 Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 未安装 Node.js！
    echo.
    echo 请访问 https://nodejs.org/ 下载安装
    echo.
    pause
    exit /b 1
)
echo [OK] Node.js 已就绪
echo.

echo [2/2] 安装依赖...
call npm install >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 重新安装依赖...
    call npm install
)
echo [OK] 依赖已就绪
echo.
echo ════════════════════════════════════════════════════════
echo.
echo    启动中...
echo.
echo    打开浏览器访问: index.html
echo.
echo ════════════════════════════════════════════════════════
echo.

npm start

pause
