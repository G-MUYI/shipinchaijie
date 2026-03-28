# 视频拆解 Skills

这是一个用于视频拆解和AI视频提示词生成的技能集合。

## 项目结构

```
视频拆解skills/
├── shipinchaijie/              # 视频拆解技能主目录
│   ├── SKILL.md               # 技能定义文件
│   ├── bin/                   # 可执行脚本
│   ├── references/            # 参考文档
│   ├── templates/             # 提示词模板
│   └── output/                # 输出目录
└── shipinchaijie-workspace/   # 工作区（测试、评估等）
```

## 主要功能

### shipinchaijie (v2.0.0)

视频拆解提示词生成器 — 将视频拆解为极其细致的镜头语言描述，生成可直接用于 AI 视频生成工具的专业提示词。

**核心功能：**
- ✅ 视角选择（第一人称POV/第三人称上帝视角/混合视角）
- ✅ 首帧AI绘图提示词生成（支持垫图，提升角色一致性）
- ✅ 复刻重创功能（通过7个引导性问题帮助构思创意）
- ✅ 动作连贯性与物理逻辑优化
- ✅ 多主题视频自动拆分
- ✅ 支持多平台格式（通用/Seedance 2.0）

**支持的输入方式：**
- 视频链接（YouTube、抖音、B站、快手等）
- 本地视频文件（.mp4、.mov、.avi等）
- 文字描述

**支持的AI视频生成平台：**
- Sora
- 可灵 (Kling)
- Runway
- Seedance 2.0（即梦）
- Luma
- Pika

## 快速开始

### 环境要求

- Python 3.8+
- Gemini API Key（用于视频分析）
- yt-dlp（用于视频下载）

### 安装依赖

```bash
# 安装 Python 依赖
pip install google-generativeai yt-dlp

# 设置 Gemini API Key
export GEMINI_API_KEY="your-api-key-here"
```

### 使用方法

在 Claude Code 中调用技能：

```
/video-breakdown
```

或者直接描述需求：

```
帮我拆解这个视频：[视频链接]
```

## 版本历史

### v2.0.0 (2024-03-29)

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

### v1.0.0 (2024-03-24)

初始版本，支持基础的视频拆解和提示词生成功能。

## 文档

- [技能定义](shipinchaijie/SKILL.md) - 完整的技能说明和工作流程
- [提示词写作标准](shipinchaijie/references/prompt-writing-standards.md) - 详细的写作规范
- [改进总结](shipinchaijie-workspace/v2.0.0-improvement-summary-final.md) - v2.0.0 改进详情

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

- GitHub: [@G-MUYI](https://github.com/G-MUYI)
- 原 shipinchaijie 仓库: https://github.com/G-MUYI/shipinchaijie.git
