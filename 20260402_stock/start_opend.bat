@echo off
chcp 65001 >nul
title Futu OpenD with API

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║         启动富途 OpenD 并启用 API 服务               ║
echo ╚══════════════════════════════════════════════════════╝
echo.

REM 查找 OpenD 安装路径
set "OPEND_PATH="

if exist "C:\Program Files\FutuOpenD\FutuOpenD.exe" (
    set "OPEND_PATH=C:\Program Files\FutuOpenD\FutuOpenD.exe"
) else if exist "C:\Program Files (x86)\FutuOpenD\FutuOpenD.exe" (
    set "OPEND_PATH=C:\Program Files (x86)\FutuOpenD\FutuOpenD.exe"
) else (
    echo 请手动输入 FutuOpenD.exe 的路径：
    set /p OPEND_PATH=
)

if not exist "%OPEND_PATH%" (
    echo.
    echo [错误] 找不到 FutuOpenD.exe
    echo 请确认 OpenD 已正确安装
    pause
    exit /b 1
)

echo [信息] OpenD 路径: %OPEND_PATH%
echo.
echo [提示] 正在启动 OpenD 并启用 API 服务...
echo [提示] 请确保已登录富途账户
echo.

REM 启动 OpenD 并启用 WebSocket API
start "" "%OPEND_PATH%" -websocket -websocket_port 11111

echo [信息] OpenD 已启动
echo [信息] API 端口: 11111
echo.
echo 请等待 OpenD 完全启动后，再启动 API 服务器
echo.

pause
