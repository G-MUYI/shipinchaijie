# 错误处理指南

本文档定义了在视频拆解流程中可能遇到的错误及其处理方式。

## API 相关错误

### Gemini API Key 未设置

**错误表现：**
- 环境检查输出 `NO_API_KEY`
- Python 脚本报错 `API key not found`

**解决方案：**
告诉用户：
```
请先设置 Gemini API Key：

# macOS / Linux
export GEMINI_API_KEY='your-api-key'

# Windows PowerShell
$env:GEMINI_API_KEY='your-api-key'

获取地址：https://aistudio.google.com/apikey
```

### Gemini API 调用失败

**可能原因：**
1. API Key 无效或过期
2. 网络连接问题
3. API 配额用尽
4. 视频文件过大

**解决方案：**
1. 检查 API Key 是否正确
2. 检查网络连接（可能需要代理）
3. 检查 API 配额：https://aistudio.google.com/
4. 如果视频过大，建议用户：
   - 压缩视频文件
   - 或使用文字描述模式跳过 Gemini 分析

**友好提示：**
```
Gemini API 调用失败。可能的原因：
1. API Key 无效 — 请检查 https://aistudio.google.com/apikey
2. 网络问题 — 请检查网络连接
3. 视频文件过大 — 建议压缩后重试

你也可以选择使用"文字描述"模式，跳过视频分析直接生成提示词。
```

## 依赖安装错误

### Python 未安装

**错误表现：**
- 环境检查输出 `NO_PYTHON`

**解决方案：**
```
请先安装 Python 3.8+：
- Windows: https://www.python.org/downloads/
- macOS: brew install python3
- Linux: sudo apt install python3
```

### google-genai 包未安装

**错误表现：**
- 环境检查输出 `NO_GENAI`
- Python 报错 `ModuleNotFoundError: No module named 'google.genai'`

**解决方案：**
```
请运行依赖安装脚本：

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\setup.ps1

# macOS / Linux
bash setup.sh
```

### yt-dlp 未安装

**错误表现：**
- 环境检查输出 `NO_YTDLP`
- 下载视频时报错 `command not found: yt-dlp`

**解决方案：**
```
请运行依赖安装脚本（会自动安装 yt-dlp）：

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\setup.ps1

# macOS / Linux
bash setup.sh
```

## 视频下载错误

### 视频链接无效

**错误表现：**
- yt-dlp 报错 `ERROR: Unable to download webpage`
- 或 `ERROR: Video unavailable`

**解决方案：**
1. 检查链接是否正确
2. 检查视频是否被删除或设为私密
3. 某些平台可能需要登录，建议用户下载后使用本地文件模式

**友好提示：**
```
视频下载失败。可能的原因：
1. 链接无效或视频已被删除
2. 视频设为私密，无法公开访问
3. 平台限制（需要登录）

建议：
- 检查链接是否正确
- 或手动下载视频后使用"本地文件"模式
```

### 网络连接问题

**错误表现：**
- yt-dlp 报错 `ERROR: Unable to connect`
- 或超时错误

**解决方案：**
```
网络连接失败。请检查：
1. 网络连接是否正常
2. 是否需要配置代理
3. 防火墙是否阻止了连接

建议：手动下载视频后使用"本地文件"模式
```

## 文件相关错误

### 本地文件不存在

**错误表现：**
- 文件验证失败
- 报错 `ERROR: 文件不存在`

**解决方案：**
```
找不到指定的视频文件。请检查：
1. 文件路径是否正确
2. 文件是否存在
3. 是否有读取权限

当前路径：[显示用户提供的路径]
```

### 文件格式不支持

**错误表现：**
- Gemini API 报错不支持的文件格式

**解决方案：**
```
视频格式不支持。Gemini API 支持的格式：
- MP4 (推荐)
- MOV
- AVI
- WebM

建议：使用 ffmpeg 转换为 MP4 格式
```

### 文件过大

**错误表现：**
- Gemini API 报错文件大小超限

**解决方案：**
```
视频文件过大。建议：
1. 压缩视频（降低分辨率或码率）
2. 或使用"文字描述"模式跳过视频分析
```

## 输出校验错误

### 拆解报告格式不完整

**错误表现：**
- validate-output.py 报错缺少必需字段

**解决方案：**
自动补全缺失的部分，然后重新保存。

### 提示词格式不符合标准

**错误表现：**
- validate-output.py 报错格式问题

**解决方案：**
根据 prompt-writing-standards.md 修正格式。

## 权限相关错误

### 无法写入 output 目录

**错误表现：**
- 报错 `Permission denied`

**解决方案：**
```
无法写入输出目录。请检查：
1. output 目录是否存在
2. 是否有写入权限

尝试手动创建目录：
mkdir -p output
```

### 无法执行脚本

**错误表现：**
- bash 报错 `Permission denied`

**解决方案：**
```
脚本没有执行权限。请运行：

# macOS / Linux
chmod +x bin/*.py
chmod +x bin/*.sh

# Windows PowerShell
# 通常不需要额外权限，如果遇到问题：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 通用错误处理原则

1. **友好的错误信息** — 不要直接抛出技术错误，要翻译成用户能理解的语言
2. **提供解决方案** — 每个错误都给出明确的解决步骤
3. **提供替代方案** — 如果某个功能失败，提供其他可行的方式
4. **保存进度** — 即使出错，也要保存已完成的部分
5. **日志记录** — 将详细错误信息记录到日志文件，方便调试

## 降级策略

当某些功能不可用时，提供降级方案：

1. **Gemini API 不可用** → 使用文字描述模式
2. **视频下载失败** → 使用本地文件模式
3. **网络问题** → 离线模式（仅处理本地文件）
4. **依赖缺失** → 提供手动安装指南

## 用户反馈

遇到错误时，始终：
1. 说明发生了什么
2. 解释为什么会发生
3. 提供解决方案
4. 询问用户想如何继续
