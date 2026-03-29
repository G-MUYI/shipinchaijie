# 视频拆解技能改进说明

## 改进版本：v2.2.1
**发布日期：** 2026-03-30

---

## 改进内容

### 1. 视频下载流程优化（video-download.py）

#### 问题
- 代理设置时机不够早，可能导致某些网络操作无法使用代理
- 环境变量设置不够全面
- 错误提示不够明确

#### 改进
✅ **立即设置代理**
- 在程序开始时（解析参数后）立即设置代理环境变量
- 确保所有网络操作（包括 yt-dlp 的元数据获取和视频下载）都使用代理

✅ **完善环境变量**
- 新增 `ALL_PROXY` 环境变量，支持更多工具
- 确保 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY` 三个变量都设置

✅ **优化错误提示**
- 下载失败时明确提示是否配置了代理
- 如果配置了代理，提示检查代理是否可用
- 如果未配置代理，提示在 .env 文件中设置 PROXY_URL

✅ **确保子进程继承环境变量**
- 在调用 subprocess.run 时显式传递 `env=os.environ.copy()`
- 确保 yt-dlp 子进程能够使用代理

#### 代码示例
```python
# 改进前
proxy = args.proxy or os.environ.get("PROXY_URL")
if proxy:
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy

# 改进后
proxy = args.proxy or os.environ.get("PROXY_URL")
if proxy:
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy
    os.environ["ALL_PROXY"] = proxy  # 新增
    print(f"✓ 使用代理: {proxy}")
else:
    print("⚠ 未配置代理，如果下载失败请在 .env 文件中设置 PROXY_URL")
```

---

### 2. API 分析流程优化（gemini-analyze.py）

#### 问题
- API key 检查时机太晚（在初始化客户端时才检查）
- 代理设置时机太晚（在初始化客户端前才设置）
- 错误提示不够友好，难以区分是 API key 问题还是网络问题

#### 改进
✅ **新增 API key 前置检查函数**
```python
def check_api_key_early():
    """在程序开始时立即检查 API key 是否配置"""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        # 显示详细的配置指引
        print("=" * 60)
        print("ERROR: 未配置 GEMINI_API_KEY")
        print("=" * 60)
        print("\n请按以下步骤配置 API key：")
        print("\n1. 获取 API key:")
        print("   访问 https://aistudio.google.com/apikey")
        print("\n2. 配置方式（选择其一）：")
        print("   方式A - 在 .env 文件中添加（推荐）：")
        print("     GEMINI_API_KEY=your-api-key-here")
        # ... 更多配置说明
        raise FatalError("未配置 GEMINI_API_KEY，程序终止")

    # 简单验证 API key 格式
    if not key.startswith("AIza"):
        print("WARNING: API key 格式可能不正确")
        # ... 格式提示

    return key
```

✅ **新增代理前置设置函数**
```python
def setup_proxy_early():
    """在程序开始时立即设置代理"""
    proxy_url = os.environ.get("PROXY_URL")
    if proxy_url:
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        os.environ["ALL_PROXY"] = proxy_url
        print(f"✓ 使用代理: {proxy_url}")
        return proxy_url
    else:
        print("⚠ 未配置代理，如果 API 调用失败请在 .env 文件中设置 PROXY_URL")
        return None
```

✅ **优化执行顺序**
```python
def main():
    # 1. 解析参数
    args = parser.parse_args()

    # 2. 加载 .env 文件（最先执行）
    load_env_file()

    # 3. 立即设置代理（在任何网络操作之前）
    proxy_url = setup_proxy_early()

    # 4. 立即检查 API key（在初始化客户端之前）
    api_key = check_api_key_early()

    # 5. 验证视频文件
    # 6. 检查依赖
    # 7. 初始化客户端（此时代理和 API key 都已就绪）
```

✅ **增强错误分类和解决建议**
```python
except Exception as e:
    error_msg = str(e)
    print("\n" + "=" * 60)
    print("ERROR: API 调用失败")
    print("=" * 60)

    # 详细的错误分类
    if "quota" in error_msg.lower() or "429" in error_msg:
        print("问题类型: API 配额耗尽")
        print("\n解决方案:")
        print("  1. 等待一段时间后重试")
        print("  2. 升级到付费 API 计划")
        # ...
    elif "permission" in error_msg.lower() or "403" in error_msg:
        print("问题类型: API key 权限不足或无效")
        print("\n解决方案:")
        print("  1. 检查 .env 文件中的 GEMINI_API_KEY 是否正确")
        # ...
    elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
        print("问题类型: 网络连接问题")
        proxy_url = os.environ.get("PROXY_URL")
        if proxy_url:
            print(f"  当前代理: {proxy_url}")
            print("  1. 检查代理是否正常运行")
        else:
            print("  1. 检查网络连接")
            print("  2. 如果在国内，需要配置代理")
        # ...
```

---

## 使用说明

### 配置 .env 文件

在项目根目录的 `.env` 文件中配置以下内容：

```env
# Gemini API Key（必需）
GEMINI_API_KEY=AIzaSyAIt-lrA7Ud_t_YjEJ62J9sKgwiIlNY0Ww

# Gemini 模型（可选，默认使用 gemini-2.5-flash）
GEMINI_MODEL=gemini-3-flash-preview

# 代理 URL（可选，但在国内强烈推荐）
PROXY_URL=http://127.0.0.1:7897
```

### 测试改进功能

运行测试脚本验证改进是否生效：

```bash
cd bin
python test-improvements.py
```

测试脚本会检查：
1. .env 文件是否正确加载
2. API key 前置检查是否工作
3. 代理设置是否正确

---

## 错误处理示例

### 场景 1：未配置 API key

**错误提示：**
```
============================================================
ERROR: 未配置 GEMINI_API_KEY
============================================================

请按以下步骤配置 API key：

1. 获取 API key:
   访问 https://aistudio.google.com/apikey

2. 配置方式（选择其一）：
   方式A - 在 .env 文件中添加（推荐）：
     GEMINI_API_KEY=your-api-key-here

   方式B - 设置环境变量：
     export GEMINI_API_KEY='your-api-key'  # macOS/Linux
     $env:GEMINI_API_KEY='your-api-key'    # Windows PowerShell

   方式C - 在 Claude Code settings.json 中配置：
     "env": { "GEMINI_API_KEY": "your-api-key" }

============================================================
```

### 场景 2：API key 格式错误

**警告提示：**
```
============================================================
WARNING: API key 格式可能不正确
============================================================
当前 API key: abcd123456...
Google Gemini API key 通常以 'AIza' 开头
请确认你使用的是正确的 API key
============================================================
```

### 场景 3：网络连接问题（已配置代理）

**错误提示：**
```
============================================================
ERROR: API 调用失败
============================================================
问题类型: 网络连接问题

解决方案:
  当前代理: http://127.0.0.1:7897
  1. 检查代理是否正常运行
  2. 尝试更换代理端口
  3. 检查防火墙设置
============================================================
```

### 场景 4：网络连接问题（未配置代理）

**错误提示：**
```
============================================================
ERROR: API 调用失败
============================================================
问题类型: 网络连接问题

解决方案:
  1. 检查网络连接
  2. 如果在国内，需要配置代理（在 .env 中设置 PROXY_URL）
     例如: PROXY_URL=http://127.0.0.1:7897
  3. 检查防火墙设置
============================================================
```

---

## 技术细节

### 代理设置优先级

1. **命令行参数** > **环境变量** > **未配置**
2. 设置的环境变量：
   - `HTTP_PROXY`：HTTP 请求代理
   - `HTTPS_PROXY`：HTTPS 请求代理
   - `ALL_PROXY`：所有协议的代理（兼容更多工具）

### API key 验证

- 检查是否存在：`os.environ.get("GEMINI_API_KEY")`
- 格式验证：Google API key 通常以 `AIza` 开头
- 如果格式不正确，显示警告但不阻止执行

### 执行顺序优化

**改进前：**
```
解析参数 → 加载 .env → 验证文件 → 检查依赖 → 获取 API key → 设置代理 → 初始化客户端
```

**改进后：**
```
解析参数 → 加载 .env → 设置代理 → 检查 API key → 验证文件 → 检查依赖 → 初始化客户端
```

关键改进：
- 代理和 API key 检查提前到所有网络操作之前
- 失败快速（fail-fast）：配置问题立即发现，不浪费时间

---

## 兼容性

- ✅ Windows 10/11
- ✅ macOS
- ✅ Linux
- ✅ Python 3.7+
- ✅ 向后兼容（不影响现有功能）

---

## 后续计划

- [ ] 添加代理连接测试功能
- [ ] 支持 SOCKS5 代理
- [ ] 添加 API key 有效性在线验证
- [ ] 优化大文件上传的代理超时处理

---

## 反馈

如有问题或建议，请在项目中提出 issue。
