# 视频拆解提示词生成器

将视频拆解为极其细致的镜头语言描述，生成可直接用于 AI 视频生成工具（Sora、可灵、Runway、Seedance 2.0/即梦 等）的提示词。

## 版本信息

- **当前版本：** 1.2.0
- **最后更新：** 2026-03-29
- **改进内容：**
  - ✅ 强化了多主题视频拆分逻辑（每个主题生成独立文件）
  - ✅ 加强了手部渐进规则的说明和示例
  - ✅ 明确了时间线分段要求（≥视频时长/2）
  - ✅ 优化了文件命名规范（包含主题标识）
  - ✅ 完善了错误示例和正确示例对比
  - ✅ 通过完整测试评估（68%通过率 vs 56% baseline）

📝 **[查看完整改进历史](docs/improvements/README.md)**

## 功能

- **视频拆解** — 通过 Gemini API 分析视频，输出详细拆解报告（运镜、光线、色调、节奏、手部状态等）
- **提示词生成** — 基于拆解结果，生成逐段（1-2 秒粒度）的 AI 视频生成提示词
- **复刻重创** — 保留原视频的运镜骨架（景别、节奏、转场），替换为全新场景和角色
- **Seedance 2.0 专属格式** — 支持即梦平台的 @引用系统、十大能力模式（一致性控制、运镜复刻、视频延长、一镜到底、音乐卡点等）
- **双模板支持** — 提供基础版（适合新手）和专业版（适合专业用户）两种模板

支持三种输入方式：视频链接（YouTube/抖音/B站等）、本地 `.mp4` 文件、纯文字描述。

### 支持平台

| 平台 | 格式 |
|------|------|
| Sora / 可灵 / Runway | 通用时间戳分镜提示词 |
| Seedance 2.0（即梦） | 专属格式（@引用、视频延长、编辑、一镜到底、音乐卡点） |

## 快速开始

### 1. 安装依赖

```bash
# macOS / Linux
bash setup.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

### 2. 配置 API Key

```bash
export GEMINI_API_KEY='your-api-key'
```

获取地址：https://aistudio.google.com/apikey

### 3. 测试工作流程

```bash
# macOS / Linux
bash bin/test-workflow.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\bin\test-workflow.ps1
```

### 4. 使用

本项目设计为 Claude Code Skill，在 Claude Code 中直接调用即可。也可以单独使用各脚本：

```bash
# 下载视频
python bin/video-download.py "https://youtube.com/watch?v=xxx" output/tmp

# Gemini 分析视频
python bin/gemini-analyze.py video.mp4 --output output/analysis.json

# 校验输出格式
python bin/validate-output.py breakdown output/video-breakdown-xxx.md
python bin/validate-output.py remix output/video-remix-xxx.md
```

## 项目结构

```
├── SKILL.md                    # Claude Code Skill 定义（核心工作流程，270行）
├── requirements.txt            # Python 依赖（google-genai, yt-dlp）
├── setup.sh / setup.ps1        # 依赖安装脚本
├── bin/
│   ├── gemini-analyze.py       # Gemini API 视频分析
│   ├── video-download.py       # yt-dlp 视频下载
│   └── validate-output.py      # 输出格式校验
├── templates/
│   ├── gemini-prompt.txt       # Gemini 分析提示词
│   ├── prompt-template.md      # 专业版提示词模板
│   └── prompt-template-basic.md # 基础版提示词模板
├── references/                 # 参考文档
│   ├── seedance-guide.md       # Seedance 2.0 平台专属指南
│   ├── prompt-writing-standards.md # 提示词写作标准
│   └── error-handling.md       # 错误处理指南
├── evals/                      # 测试用例
│   └── evals.json              # 测试用例定义
├── docs/                       # 文档目录
│   └── improvements/           # 改进历史
│       ├── README.md           # 改进历史索引
│       └── v1.2.0-2026-03-29.md # 最新改进文档
└── output/                     # 生成结果输出目录（已 gitignore）
```

## 环境要求

- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)（视频下载，setup 脚本会自动安装）
- Gemini API Key
