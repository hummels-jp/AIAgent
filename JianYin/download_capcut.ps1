# 剪映下载脚本
Write-Host "正在下载剪映专业版..."

# 尝试从官方源下载（这是一个示例链接，实际需要正确的官方链接）
$url = "https://lf16-capcut.faceulv.com/obj/capcutpc-packages-us/packages/CapCut_1_0_0_0_capcutpc_0_creatortool.exe"
$output = "D:\huqianqian_git\AIAgent\JianYin\CapCut_Setup.exe"

try {
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $url -OutFile $output -ErrorAction Stop
    if (Test-Path $output) {
        $fileSize = (Get-Item $output).Length / 1MB
        Write-Host "下载成功！文件大小: $($fileSize.ToString('F2')) MB"
        Write-Host "文件保存到: $output"
    } else {
        Write-Host "下载失败，文件不存在"
    }
} catch {
    Write-Host "下载失败: $_"
}

Write-Host ""
Write-Host "备用方案："
Write-Host "1. 手动访问剪映官网: https://www.capcut.cn/"
Write-Host "2. 点击'立即下载'按钮"
Write-Host "3. 下载后手动安装到指定目录"