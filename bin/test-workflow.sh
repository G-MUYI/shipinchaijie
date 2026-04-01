#!/bin/bash
# 快速测试整个工作流程

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 视频拆解提示词工作流程测试 ==="
echo ""

# 1. 检查 Python
echo "[1/5] 检查 Python..."
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "ERROR: 未找到 Python"
    exit 1
fi
echo "✓ Python: $($PY_CMD --version)"

# 2. 检查依赖
echo ""
echo "[2/5] 检查依赖..."
$PY_CMD -c "from google import genai" 2>/dev/null && echo "✓ google-genai" || echo "✗ google-genai 未安装"
command -v yt-dlp >/dev/null 2>&1 && echo "✓ yt-dlp" || echo "✗ yt-dlp 未安装"

# 3. 检查 API Key
echo ""
echo "[3/5] 检查 API Key..."
if [ -n "${GEMINI_API_KEY:-}" ]; then
    echo "✓ GEMINI_API_KEY 已设置"
else
    echo "✗ GEMINI_API_KEY 未设置"
fi

# 4. 测试校验脚本
echo ""
echo "[4/5] 测试校验脚本..."
echo "测试新格式检测..."
cat > /tmp/test-new-format.md << 'EOF'
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
EOF

$PY_CMD "$PROJECT_DIR/bin/validate-output.py" breakdown /tmp/test-new-format.md && echo "✓ 新格式校验通过" || echo "✗ 新格式校验失败"
rm /tmp/test-new-format.md

# 5. 检查模板文件
echo ""
echo "[5/5] 检查模板文件..."
[ -f "$PROJECT_DIR/templates/prompt-template.md" ] && echo "✓ 专业版模板" || echo "✗ 专业版模板缺失"
[ -f "$PROJECT_DIR/templates/gemini-prompt-v2.txt" ] && echo "✓ Gemini 提示词 (v2)" || echo "✗ Gemini 提示词缺失"

echo ""
echo "=== 测试完成 ==="
