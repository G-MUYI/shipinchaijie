# 参考文档索引

本目录包含技能使用的所有参考文档。

## 核心标准（必读）

### [prompt-writing-standards.md](./prompt-writing-standards.md)
**提示词写作标准** — 生成AI视频提示词时必须遵循的写作标准和质量要求

**核心内容：**
- ⭐ 手部描述渐进规则（五阶段模型）
- 总述区与时间线区结构要求
- 真实感渲染描述规范
- 禁用词汇清单与推荐词汇
- 动作连贯性与物理逻辑要求

**适用场景：** 所有视频提示词生成

---

### [combat-choreography-guide.md](./combat-choreography-guide.md)
**战斗动作编排指南** — 战斗类视频的动作编排专项指南

**核心内容：**
- 一镜到底战斗场景的连贯性原则
- Boss对战完整流程（7阶段）
- 物理逻辑细节清单（重力、惯性、力的传递）
- 第一人称POV战斗特殊处理
- 常见问题与解决方案

**适用场景：** 战斗类、动作类视频提示词生成

---

## 平台适配

### [seedance-guide.md](./seedance-guide.md)
**Seedance 2.0平台专属格式指南**

**核心内容：**
- Seedance平台十大能力类型
- @引用系统（@图片1、@视频1、@音频1）
- 时长处理策略
- 自然流畅的中文描述要求
- 多版本输出建议

**适用场景：** 目标平台为Seedance（即梦）时使用

---

## 辅助文档

### [error-handling.md](./error-handling.md)
**错误处理指南** — 常见错误的友好提示和解决方案

**核心内容：**
- API错误处理（Gemini API、网络错误）
- 依赖安装错误（Python、yt-dlp、google-genai）
- 视频下载错误（URL无效、平台限制）
- 文件错误（路径不存在、权限问题）

**适用场景：** 遇到错误时查阅

---

### [zodiac-gestures.md](./zodiac-gestures.md)
**星座手势参考** — 十二星座专属手势/结印设计（可选扩展）

**核心内容：**
- 每个星座的独立提示词生成规则
- 首帧AI绘画提示词格式
- 避免CG动画关键词的规范
- 星座识别与手势设计

**适用场景：** 特定主题视频（星座魔法、元素法师等）

**注意：** 本功能为可选扩展，不是所有视频都需要星座概念

---

## 使用建议

### 新手用户
1. 先阅读 [prompt-writing-standards.md](./prompt-writing-standards.md)
2. 了解手部描述五阶段规则（最重要）
3. 根据目标平台选择对应的格式指南

### 进阶用户
1. 战斗类视频必读 [combat-choreography-guide.md](./combat-choreography-guide.md)
2. Seedance平台用户必读 [seedance-guide.md](./seedance-guide.md)
3. 遇到问题查阅 [error-handling.md](./error-handling.md)

### 特殊主题
- 星座/魔法主题视频可参考 [zodiac-gestures.md](./zodiac-gestures.md)

---

## 文档更新历史

| 日期 | 文档 | 变更内容 |
|------|------|---------|
| 2026-03-29 | prompt-writing-standards.md | 三阶段扩展为五阶段模型 |
| 2026-03-29 | combat-choreography-guide.md | 新增战斗编排指南 |
| 2026-03-29 | zodiac-gestures.md | 从docs/移动到references/ |

---

## 快速链接

- [返回项目主页](../README.md)
- [查看技能定义](../SKILL.md)
- [查看版本更新历史](../docs/changelog/)
- [查看项目报告](../docs/reports/)
