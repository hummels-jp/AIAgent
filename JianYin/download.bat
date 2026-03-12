@echo off
echo 开始下载剪映Windows安装程序...
echo.

set "DOWNLOAD_URL=https://lf3-package.vlabstatic.com/obj/faceu-packages/Jianying_6_3_0_12011_jianyingpro_0_creatortool.exe"
set "OUTPUT_FILE=CapCut_Setup.exe"

echo 下载链接: %DOWNLOAD_URL%
echo 保存到: %OUTPUT_FILE%
echo.

REM 使用bitsadmin下载（Windows内置工具）
echo 正在下载，请稍候...
bitsadmin /transfer "CapCutDownload" %DOWNLOAD_URL% "%OUTPUT_FILE%"

if exist "%OUTPUT_FILE%" (
    echo ✅ 下载完成！
    echo.
    for %%F in ("%OUTPUT_FILE%") do (
        echo 文件信息:
        echo   名称: %%~nxF
        echo   大小: %%~zF 字节
        set /a filesize=%%~zF/1048576
        echo        约 !filesize! MB
        echo   路径: %%~dpF%%~nxF
    )
    echo.
    echo 下一步操作:
    echo 1. 双击 "%OUTPUT_FILE%" 运行安装程序
    echo 2. 按照安装向导完成安装
    echo 3. 安装后可在开始菜单找到剪映
) else (
    echo ❌ 下载失败！
    echo.
    echo 备用方案:
    echo 1. 手动访问剪映官网: https://www.capcut.cn/
    echo 2. 点击"立即下载"按钮
    echo 3. 选择Windows版本下载
)

echo.
pause