#!/usr/bin/env python3
"""
validate-output.py — 校验生成的拆解/复刻 Markdown 是否符合项目约束

用法:
  python bin/validate-output.py breakdown output/video-breakdown-xxxx.md
  python bin/validate-output.py remix output/video-remix-xxxx.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


BREAKDOWN_HEADINGS = [
    "# 视频拆解报告",
    "## 详细拆解分析",
    "### 基础信息",
    "### 视觉风格与色调分析",
    "### 光线与质感",
    "### 运镜方式",
    "### 主角描述",
    "### 手部状态",
    "### 场景描述",
    "### 关键动作与节奏分析",
    "### 音频与字幕元素",
    "### 制作参考建议",
    "### Timeline",
    "## AI 视频生成提示词",
]

FORBIDDEN_HAND_EFFECTS = [
    "发光",
    "缠绕",
    "能量",
    "流动",
    "纹路",
    "火焰",
    "冰焰",
    "龙鳞",
    "符文",
    "水银",
    "丝带",
    "翅膀",
    "甲片",
    "覆盖",
    "裂纹",
    "光效",
    "活体膜",
]

PROMPT_ENDING = "禁止出现文字、字幕、LOGO或水印。"


class ValidationError(Exception):
    """Raised when a generated markdown file violates project constraints."""


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"{path} 不是有效的 UTF-8 文本: {exc}") from exc


def validate_breakdown(path: Path, text: str) -> None:
    for heading in BREAKDOWN_HEADINGS:
        ensure(heading in text, f"缺少必须章节: {heading}")

    # 检测新格式（总述区 + 时间线区）或旧格式
    has_new_format = "**核心主题**：" in text or "**总述区" in text
    has_old_format = not has_new_format

    if has_new_format:
        # 新格式校验：总述区必需字段
        ensure("**核心主题**：" in text or "核心主题" in text, "新格式缺少 核心主题")
        ensure("**角色设定**：" in text or "角色设定" in text, "新格式缺少 角色设定")
        ensure("**镜头运动**：" in text or "镜头运动" in text, "新格式缺少 镜头运动")
        # 时间线区字段（可选检查，因为格式灵活）
        ensure("运镜：" in text or "运镜" in text, "新格式时间线区缺少运镜描述")
        ensure("特效：" in text or "特效" in text, "新格式时间线区缺少特效描述")
    else:
        # 旧格式校验
        ensure("标题：" in text, "缺少 标题 字段，无法保留字幕/标题分析结果")
        ensure("人物情绪：" in text or "人物情绪/表情" in text, "提示词部分缺少人物情绪字段")
        ensure("转场：" in text, "提示词部分缺少转场字段")

    ensure(text.count(PROMPT_ENDING) >= 1, f"缺少固定结尾: {PROMPT_ENDING}")


def iter_prompt_sections(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"^##\s+\d+/\d+\s+[—-]\s+.+$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: list[tuple[str, str]] = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        title = match.group(0)
        sections.append((title, text[start:end]))

    return sections


def validate_opening_hand_line(section_title: str, section_text: str) -> None:
    opening_match = re.search(r"^主角仅露出双手【图片1】.*$", section_text, re.MULTILINE)
    ensure(opening_match is not None, f"{section_title} 缺少开头的手部总述")

    opening_line = opening_match.group(0)
    bad_keywords = [keyword for keyword in FORBIDDEN_HAND_EFFECTS if keyword in opening_line]
    ensure(
        not bad_keywords,
        f"{section_title} 的开头手部总述提前出现特效描述: {', '.join(bad_keywords)}",
    )


def validate_remix(path: Path, text: str) -> None:
    ensure(text.startswith("# 视频复刻提示词"), "缺少复刻报告标题")
    ensure("## 骨架来源" in text, "缺少 骨架来源 章节")

    prompt_sections = iter_prompt_sections(text)
    ensure(prompt_sections, "未找到独立提示词章节（格式应为 ## 1/6 - 标题）")

    for title, section_text in prompt_sections:
        validate_opening_hand_line(title, section_text)
        ensure(
            PROMPT_ENDING in section_text,
            f"{title} 缺少固定结尾: {PROMPT_ENDING}",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="校验生成的 Markdown 输出")
    parser.add_argument("kind", choices=["breakdown", "remix"], help="输出类型")
    parser.add_argument("path", help="待校验的 Markdown 文件路径")
    args = parser.parse_args()

    path = Path(args.path)
    ensure(path.is_file(), f"文件不存在: {path}")
    text = read_text(path)

    if args.kind == "breakdown":
        validate_breakdown(path, text)
    else:
        validate_remix(path, text)

    print(f"OK: {args.kind} 输出结构通过校验 -> {path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
