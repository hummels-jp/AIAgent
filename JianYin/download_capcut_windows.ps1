# 剪映Windows版下载脚本
Write-Host "开始下载剪映Windows安装程序..." -ForegroundColor Green
Write-Host "========================================"

# 设置参数
$downloadUrl = "https://lf3-package.vlabstatic.com/obj/faceu-packages/Jianying_4_0_0_9015_jianyingpro_0_creatortool.exe"
$outputFile = "D:\huqianqian_git\AIAgent\JianYin\CapCut_Setup.exe"

# 备选下载链接（如果主链接失败）
$backupUrls = @(
    "https://lf16-capcut.faceulv.com/obj/capcutpc-packages-us/packages/CapCut_1_0_0_0_capcutpc_0_creatortool.exe",
    "https://lf3-cappackage.bytetos.com/obj/capcutpc-packages-us/packages/CapCut_1_2_0_0_capcutpc_0_creatortool.exe"
)

# 创建下载函数
function Download-File {
    param([string]$Url, [string]$Output)
    
    try {
        Write-Host "尝试从链接下载: $Url" -ForegroundColor Yellow
        $ProgressPreference = 'SilentlyContinue'
        
        # 设置超时和重试
        $client = New-Object System.Net.WebClient
        $client.DownloadFile($Url, $Output)
        
        if (Test-Path $Output) {
            $fileSize = (Get-Item $Output).Length / 1MB
            Write-Host "✅ 下载成功！" -ForegroundColor Green
            Write-Host "文件大小: $($fileSize.ToString('F2')) MB" -ForegroundColor Cyan
            Write-Host "保存路径: $Output" -ForegroundColor Cyan
            return $true
        } else {
            Write-Host "❌ 下载失败：文件未创建" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ 下载失败: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 清理可能存在的旧文件
if (Test-Path $outputFile) {
    Remove-Item $outputFile -Force -ErrorAction SilentlyContinue
    Write-Host "已清理旧文件" -ForegroundColor Yellow
}

# 尝试主链接下载
Write-Host "`n尝试主链接下载..." -ForegroundColor Cyan
$success = Download-File -Url $downloadUrl -Output $outputFile

# 如果主链接失败，尝试备选链接
if (-not $success) {
    Write-Host "`n主链接下载失败，尝试备选链接..." -ForegroundColor Yellow
    
    $index = 1
    foreach ($backupUrl in $backupUrls) {
        Write-Host "`n尝试备选链接 #$index..." -ForegroundColor Yellow
        $success = Download-File -Url $backupUrl -Output $outputFile
        
        if ($success) {
            break
        }
        $index++
    }
}

# 显示最终结果
Write-Host "`n========================================" -ForegroundColor Green
if ($success) {
    Write-Host "✅ 剪映Windows安装程序下载完成！" -ForegroundColor Green
    
    # 显示文件信息
    $fileInfo = Get-Item $outputFile
    Write-Host "文件信息:" -ForegroundColor Cyan
    Write-Host "  名称: $($fileInfo.Name)"
    Write-Host "  大小: $([math]::Round($fileInfo.Length / 1MB, 2)) MB"
    Write-Host "  修改时间: $($fileInfo.LastWriteTime)"
    Write-Host "  完整路径: $outputFile"
    
    Write-Host "`n下一步操作:" -ForegroundColor Yellow
    Write-Host "1. 双击 '$($fileInfo.Name)' 运行安装程序"
    Write-Host "2. 按照安装向导完成安装"
    Write-Host "3. 安装后可在开始菜单找到剪映"
} else {
    Write-Host "❌ 所有下载尝试都失败了" -ForegroundColor Red
    Write-Host "`n备用方案:" -ForegroundColor Yellow
    Write-Host "1. 手动访问剪映官网: https://www.capcut.cn/"
    Write-Host "2. 点击'立即下载'按钮"
    Write-Host "3. 选择Windows版本下载"
    Write-Host "4. 下载后手动安装"
}

# 保持窗口打开（如果是直接运行的话）
if ($Host.Name -eq 'ConsoleHost') {
    Write-Host "`n按任意键继续..."
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}