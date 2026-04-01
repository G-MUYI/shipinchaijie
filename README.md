# 视频拆解提示词生成器

将视频拆解为极其细致的镜头语言描述，生成可直接用于 AI 视频生成工具（Sora、可灵、Runway、Seedance 2.0/即梦 等）的提示词。

## 版本信息

- **当前版本：** 2.3.1
- **最后更新：** 2026-04-01
- **改进内容：**
  - ✅ Seedance 2.0 平台专属优化：提示词长度控制、单运镜原则、禁止文学化描述、素材与文字分工策略
  - ✅ 一镜到底转场遮挡物标注（6种遮挡物类型，防止硬切）
  - ✅ 背景微动态维度（8种场景类型微动态元素表，防止死水背景）
  - ✅ 材质交互规则描述法（5维度交互模板，5种常见材质速查）
  - ✅ 强化了多主题视频拆分逻辑（每个主题生成独立文件）

📝 **[查看完整改进历史](docs/changelog/README.md)**

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
# 复制模板文件
cp .env.example .env

# 编辑 .env，填入你的 API Key
# GEMINI_API_KEY=your-actual-api-key
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

# 生成 Seedance 2.0 专属提示词
python bin/generate-seedance.py output/analysis.json --output-dir output

# 校验输出格式
python bin/validate-output.py breakdown output/video-breakdown-xxx.md
python bin/validate-output.py remix output/video-remix-xxx.md
```

## 项目结构

```
├── SKILL.md                    # Claude Code Skill 定义（核心工作流程）
├── requirements.txt            # Python 依赖（google-genai, yt-dlp）
├── setup.sh / setup.ps1        # 依赖安装脚本
├── .env.example                # 环境变量模板（复制为 .env 后填入 API Key）
├── bin/
│   ├── gemini-analyze.py       # Gemini API 视频分析
│   ├── video-download.py       # yt-dlp 视频下载
│   ├── validate-output.py      # 输出格式校验
│   ├── generate-prompts.py     # 通用提示词生成工具
│   ├── generate-seedance.py    # Seedance 2.0 专属提示词生成工具
│   └── utils.py                # 共享工具函数
├── templates/
│   ├── gemini-prompt.txt       # Gemini 分析提示词
│   ├── prompt-template.md      # 专业版提示词模板
│   └── prompt-template-basic.md # 基础版提示词模板
├── references/                 # 参考文档
│   ├── prompt-writing-standards.md  # 提示词写作标准
│   ├── combat-choreography-guide.md # 战斗动作编排指南
│   ├── seedance-guide.md       # Seedance 2.0 平台专属指南
│   ├── error-handling.md       # 错误处理指南
│   └── zodiac-gestures.md      # 星座手势定义
├── evals/                      # 测试用例
│   └── evals.json              # 测试用例定义
├── docs/                       # 文档目录
│   ├── changelog/              # 版本变更历史
│   ├── reports/                # 项目报告
│   ├── guides/                 # 快速入门指南
│   └── archive/                # 归档文档
└── output/                     # 生成结果输出目录（已 gitignore）
```

## 环境要求

- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)（视频下载，setup 脚本会自动安装）
- Gemini API Key

## 版本历史

### v2.3.0 (2026-03-31)

**主要改进：**
1. Seedance 2.0 平台专属优化（提示词长度控制、单运镜原则、禁止文学化描述、素材与文字分工）
2. 一镜到底转场遮挡物标注（6种遮挡物类型）
3. 背景微动态维度（8种场景类型微动态元素表）
4. 材质交互规则描述法（5维度交互模板）

### v2.2.0 (2026-03-29)

**主要改进：**
1. 新增战斗动作编排指南 - 系统性解决一镜到底连贯性问题
2. 完善Boss对战完整流程（7阶段，缺一不可）
3. 强化物理逻辑细节（重力、惯性、力的传递、环境反馈）
4. 优化第一人称POV战斗描述

### v2.1.0 (2026-03-29)

**主要改进：**
1. 首帧绘图提示词强化真实感风格 - 移除CG动画渲染等词汇
2. 明确禁用词汇清单 - 避免3D渲染感、CG动画风格、卡通化效果
3. 首帧提示词格式规范 - 必须以"电影级写实摄影，真实拍摄质感"开头

### v2.0.0 (2026-03-29)

**主要改进：**
1. 视角选择功能 - 支持第一人称POV/第三人称/混合视角
2. 首帧AI绘图提示词生成 - 支持垫图，提升角色一致性
3. 复刻重创功能优化 - 在拆解完成后询问，通过7个引导性问题帮助构思创意
4. 动作连贯性与物理逻辑 - 新增完整的动作编排规则和物理逻辑检查

**详细改进：**
- 调整复刻询问时机（从开始移到拆解完成后）
- 添加7个引导性问题（主题/角色/能力/场景/氛围/色调/特殊要求）
- 新增动作连贯性章节（约200行，包含8个子章节）
- 优化工作流程（12个步骤）
- 更新核心原则和重要提醒

### v1.0.0 (2026-03-24)

初始版本，支持基础的视频拆解和提示词生成功能。

## 文档

- [技能定义](SKILL.md) - 完整的技能说明和工作流程
- [提示词写作标准](references/prompt-writing-standards.md) - 详细的写作规范
- [战斗动作编排](references/combat-choreography-guide.md) - Boss战完整流程
- [改进历史](docs/changelog/README.md) - 版本改进详情
- [项目报告](docs/reports/README.md) - 审查报告、评估报告等

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

- GitHub: [@G-MUYI](https://github.com/G-MUYI)
- 原 shipinchaijie 仓库: https://github.com/G-MUYI/shipinchaijie.git
