#!/usr/bin/env bash
# setup.sh — 安装视频拆解提示词 Skill 的依赖
# 用法: bash setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "  视频拆解提示词 Skill — 依赖安装"
echo "=========================================="
echo ""

ERRORS=0

# 1. 检查 Python
echo "[1/3] 检查 Python..."
PY_CMD=""
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
fi

if [ -n "$PY_CMD" ]; then
    PY_VER=$($PY_CMD --version 2>&1)
    echo "  已安装: $PY_VER"
    # 检查 Python 版本 >= 3.8
    PY_MAJOR=$($PY_CMD -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "0")
    PY_MINOR=$($PY_CMD -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "0")
    if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]; }; then
        echo "  WARNING: Python 版本过低（需要 3.8+，当前 ${PY_MAJOR}.${PY_MINOR}）"
        echo "  请升级 Python: https://www.python.org/downloads/"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  ERROR: 未找到 Python。请安装 Python 3.8+。"
    echo "  下载: https://www.python.org/downloads/"
    ERRORS=$((ERRORS + 1))
fi

PIP_CMD=()
if [ -n "$PY_CMD" ]; then
    PIP_CMD=("$PY_CMD" -m pip)
fi

# 2. 安装 google-genai SDK
echo ""
echo "[2/3] 安装 Python 依赖..."
REQ_FILE="$SCRIPT_DIR/requirements.txt"
if [ -f "$REQ_FILE" ]; then
    if [ "${#PIP_CMD[@]}" -gt 0 ] && "${PIP_CMD[@]}" install --user -r "$REQ_FILE" --quiet 2>&1; then
        echo "  依赖安装成功!"
    else
        echo "  ERROR: 无法安装依赖。请手动运行:"
        echo "    $PY_CMD -m pip install -r requirements.txt"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  WARNING: requirements.txt 未找到，尝试单独安装..."
    if [ "${#PIP_CMD[@]}" -gt 0 ] && "${PIP_CMD[@]}" install --user google-genai --quiet 2>&1; then
        echo "  google-genai 安装成功!"
    else
        echo "  ERROR: 无法安装 google-genai。请手动运行:"
        echo "    $PY_CMD -m pip install google-genai"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 3. 检查/安装 yt-dlp
echo ""
echo "[3/3] 检查 yt-dlp..."
if command -v yt-dlp &>/dev/null; then
    YT_VER=$(yt-dlp --version 2>&1)
    echo "  已安装: yt-dlp $YT_VER"
else
    echo "  yt-dlp 未安装，正在安装..."
    if [ "${#PIP_CMD[@]}" -gt 0 ] && "${PIP_CMD[@]}" install --user yt-dlp --quiet 2>&1; then
        echo "  yt-dlp 安装成功!"
    else
        echo "  ERROR: 无法安装 yt-dlp。请手动运行:"
        echo "    $PY_CMD -m pip install yt-dlp"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 设置脚本可执行权限
echo ""
echo "设置脚本权限..."
chmod +x "$SCRIPT_DIR/bin/video-download.py" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/bin/gemini-analyze.py" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/bin/validate-output.py" 2>/dev/null || true

# 结果汇总
echo ""
echo "=========================================="
if [ "$ERRORS" -eq 0 ]; then
    echo "  所有依赖安装完成!"
    echo ""
    echo "  下一步: 设置 Gemini API Key"
    echo "  export GEMINI_API_KEY='your-api-key'"
    echo ""
    echo "  获取 API key: https://aistudio.google.com/apikey"
else
    echo "  安装完成，但有 $ERRORS 个错误需要处理。"
    echo "  请查看上方的 ERROR 信息并手动修复。"
fi
echo "=========================================="
