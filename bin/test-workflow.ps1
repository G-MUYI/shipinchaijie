# 快速测试整个工作流程 (Windows PowerShell)

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_DIR = Split-Path -Parent $SCRIPT_DIR

Write-Host "=== 视频拆解提示词工作流程测试 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Python
Write-Host "[1/5] 检查 Python..."
$py = if (Get-Command py -ErrorAction SilentlyContinue) { @('py', '-3') }
      elseif (Get-Command python -ErrorAction SilentlyContinue) { @('python') }
      else { @() }

if ($py.Count -eq 0) {
    Write-Host "ERROR: 未找到 Python" -ForegroundColor Red
    exit 1
}
$version = & $py[0] $(if ($py.Count -gt 1) { $py[1] }) --version
Write-Host "✓ Python: $version" -ForegroundColor Green

# 2. 检查依赖
Write-Host ""
Write-Host "[2/5] 检查依赖..."
& $py[0] $(if ($py.Count -gt 1) { $py[1] }) -c "from google import genai" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ google-genai" -ForegroundColor Green
} else {
    Write-Host "✗ google-genai 未安装" -ForegroundColor Yellow
}

if (Get-Command yt-dlp -ErrorAction SilentlyContinue) {
    Write-Host "✓ yt-dlp" -ForegroundColor Green
} else {
    Write-Host "✗ yt-dlp 未安装" -ForegroundColor Yellow
}

# 3. 检查 API Key
Write-Host ""
Write-Host "[3/5] 检查 API Key..."
if ($env:GEMINI_API_KEY) {
    Write-Host "✓ GEMINI_API_KEY 已设置" -ForegroundColor Green
} else {
    Write-Host "✗ GEMINI_API_KEY 未设置" -ForegroundColor Yellow
}

# 4. 测试校验脚本
Write-Host ""
Write-Host "[4/5] 测试校验脚本..."
Write-Host "测试新格式检测..."

$testContent = @"
# 视频拆解报告
## 详细拆解分析
### 基础信息
### 视觉风格与色调分析
### 光线与质感
### 运镜方式
### 主角描述
### 手部状态
### 场景描述
### 关键动作与节奏分析
### 音频与字幕元素
### 制作参考建议
### Timeline
## AI 视频生成提示词

**核心主题**：测试
**角色设定**：测试
**镜头运动**：测试
运镜：测试
特效：测试

禁止出现文字、字幕、LOGO或水印。
"@

$testFile = "$env:TEMP\test-new-format.md"
$testContent | Out-File -FilePath $testFile -Encoding UTF8

& $py[0] $(if ($py.Count -gt 1) { $py[1] }) "$PROJECT_DIR\bin\validate-output.py" breakdown $testFile 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 新格式校验通过" -ForegroundColor Green
} else {
    Write-Host "✗ 新格式校验失败" -ForegroundColor Red
}
Remove-Item $testFile -ErrorAction SilentlyContinue

# 5. 检查模板文件
Write-Host ""
Write-Host "[5/5] 检查模板文件..."
if (Test-Path "$PROJECT_DIR\templates\prompt-template.md") {
    Write-Host "✓ 专业版模板" -ForegroundColor Green
} else {
    Write-Host "✗ 专业版模板缺失" -ForegroundColor Red
}

if (Test-Path "$PROJECT_DIR\templates\prompt-template-basic.md") {
    Write-Host "✓ 基础版模板" -ForegroundColor Green
} else {
    Write-Host "✗ 基础版模板缺失" -ForegroundColor Red
}

if (Test-Path "$PROJECT_DIR\templates\gemini-prompt.txt") {
    Write-Host "✓ Gemini 提示词" -ForegroundColor Green
} else {
    Write-Host "✗ Gemini 提示词缺失" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 测试完成 ===" -ForegroundColor Cyan
