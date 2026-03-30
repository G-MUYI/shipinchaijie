#!/usr/bin/env python3
"""
generate-prompts.py — 从分析JSON生成AI视频提示词
用法: python bin/generate-prompts.py <analysis.json> --output <output.md>
"""

import json
import argparse
from pathlib import Path

from utils import ensure_utf8_output, load_env_file


ensure_utf8_output()
load_env_file()


def load_analysis(path):
    """加载分析JSON"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_first_frame_prompt(data):
    """生成首帧AI绘画提示词"""
    hand = data.get('hand_description', {})
    scene = data.get('scene_description', '')
    lighting = data.get('lighting_texture', {})

    natural_state = hand.get('natural_state', '手部自然状态')
    magic_ball = hand.get('magic_ball', '魔法球')

    prompt = f"""电影级写实摄影，真实拍摄质感。{natural_state}。{magic_ball}。{scene}。"""
    prompt += f"""{lighting.get('light_type', '自然光')}，{lighting.get('texture', '清晰质感')}。"""
    prompt += """次表面散射的真实皮肤，物理正确的光影，全局光照，体积光穿透空气，HDR高动态范围。照片级写实，避免3D渲染感、CG动画风格、卡通化效果。"""

    return prompt


def generate_overview_section(data):
    """生成总述区"""
    char = data.get('character_description', '')
    scene = data.get('scene_description', '')
    visual = data.get('visual_style', {})
    lighting = data.get('lighting_texture', {})
    realism = data.get('realism_quality', {})
    camera = data.get('overall_camera', '')
    sound = data.get('overall_sound', {})

    overview = f"""**核心主题**：{data.get('summary', '视频核心内容')[:100]}

**角色设定**：{char}

**环境**：{scene}

**视觉风格与色调**：电影实拍质感，真实摄影机拍摄。{realism.get('rendering_style', '照片级写实')}。{visual.get('color_tone', '自然色调')}。照片级写实，避免3D渲染感。

**光线与质感**：{lighting.get('light_type', '自然光')}。次表面散射的真实皮肤材质，物理正确的布料褶皱纹理，真实金属菲涅尔反射。电影实拍质感，全局光照柔和弹射，体积光穿透空气微粒，HDR高动态范围明暗层次。照片级写实渲染，避免塑料质感和过度光滑的3D感。

**特效概述**：{visual.get('effects_style', '能量特效')}。特效具有真实的光照衰减与散射，能量光源真实照亮周围环境和人物面部，符合物理规律的光影交互。避免廉价发光效果，采用克制的自然Bloom溢出。

**镜头运动**：{camera}

**音频设计**：背景音乐：{sound.get('music', '无')}；环境音：{sound.get('ambient', '无')}；音效：{sound.get('effects', '无')}
"""
    return overview


def generate_timeline_section(data):
    """生成时间线区"""
    segments = data.get('segments', [])
    timeline = []

    hand_desc = data.get('hand_description', {})
    effect_onset = hand_desc.get('effect_onset_time', '')

    for idx, seg in enumerate(segments, 1):
        time_range = seg.get('time_range', '0-1s')

        # 根据时间段推断手部状态（简化逻辑）
        if '特效' in seg.get('effects', '') or '能量' in seg.get('effects', ''):
            hand_state = f"{seg.get('character_action', '').split('，')[0] if seg.get('character_action') else '手部'}，{seg.get('effects', '特效状态')}"
        else:
            hand_state = seg.get('character_action', '自然状态')

        # 生成段落主题标签（从动作中提取关键词）
        action = seg.get('character_action', '')
        if '站立' in action or '静止' in action:
            tag = '静立'
        elif '准备' in action or '蓄力' in action:
            tag = '准备'
        elif '触发' in action or '激活' in action or '爆发' in action:
            tag = '激活'
        elif '蔓延' in action or '扩散' in action:
            tag = '蔓延'
        elif '完成' in action or '持续' in action:
            tag = '持续'
        else:
            tag = f'动作{idx}'

        section = f"""{time_range} · {tag}

运镜：{seg.get('camera_movement', '固定镜头')}；
画面描述：{seg.get('scene', '画面内容')}；
光线与色调：{seg.get('scene', '').split('，')[0] if '光' in seg.get('scene', '') else '自然光线'}；
人物动作：{seg.get('character_action', '无')}；
手部状态：{hand_state}；
人物情绪：{seg.get('character_emotion', '平静')}；
特效：{seg.get('effects', '无')}；
台词（{seg.get('dialogue_tone', '平静')}）："{seg.get('dialogue', '无')}"；
声音：{seg.get('sound', '环境音')}；
转场：{seg.get('transition', '无')}
"""
        timeline.append(section)

    return '\n'.join(timeline)


def generate_phase_section(data):
    """生成关键动作与节奏分析"""
    phases = data.get('key_phases', [])
    if not phases:
        return "无"

    sections = []
    for phase in phases:
        sections.append(
            f"""#### {phase.get('phase_name', '未命名阶段')}（{phase.get('time_range', '时间未知')}）

动作：{phase.get('action_description', '无')}
节奏：{phase.get('rhythm', '无')}
参考建议：{phase.get('reference_suggestion', '无')}
"""
        )

    return '\n'.join(sections).strip()


def generate_detailed_report(data):
    """生成可通过项目校验器的详细拆解报告。"""
    basic = data.get('basic_info', {})
    visual = data.get('visual_style', {})
    lighting = data.get('lighting_texture', {})
    hand = data.get('hand_description', {})
    subtitle_audio = data.get('subtitle_audio', {})
    suggestions = data.get('production_suggestions', {})
    zodiac = data.get('zodiac_sign', '未知星座')

    return f"""# 视频拆解报告

## 详细拆解分析

### 基础信息
- 星座：{zodiac}
- 时长：{basic.get('duration', '未知')}
- 分辨率：{basic.get('resolution', '未知')}
- 画幅比例：{basic.get('aspect_ratio', '未知')}
- 整体风格：{basic.get('overall_style', '未知')}
- 综合总结：{data.get('summary', '无')}

### 视觉风格与色调分析
整体色调：{visual.get('color_tone', '无')}
环境设定：{visual.get('environment', '无')}
特效风格：{visual.get('effects_style', '无')}

### 光线与质感
光线类型：{lighting.get('light_type', '无')}
色调：{lighting.get('color_tone', '无')}
画面质感：{lighting.get('texture', '无')}
特殊光影效果：{lighting.get('special_effects', '无')}

### 运镜方式
{data.get('overall_camera', '无')}

### 主角描述
{data.get('character_description', '无')}

### 手部状态
- 自然状态：{hand.get('natural_state', '无')}
- 魔法球描述：{hand.get('magic_ball', '无')}
- 星座手势/结印：{hand.get('zodiac_gesture', '无')}
- 捏爆动作：{hand.get('crush_action', '无')}
- 特效触发时间：{hand.get('effect_onset_time', '无')}
- 特效蔓延过程：{hand.get('effect_progression', '无')}
- 特效持续性：{hand.get('effect_persistence', '无')}

### 场景描述
{data.get('scene_description', '无')}

### 关键动作与节奏分析
{generate_phase_section(data)}

### 音频与字幕元素
字幕：{subtitle_audio.get('subtitles', '无')}
标题：{subtitle_audio.get('titles', '无')}
音频推测：{subtitle_audio.get('audio_estimate', '无')}

### 制作参考建议
视角：{suggestions.get('perspective', '无')}
环境：{suggestions.get('environment_keys', '无')}
核心视觉元素：{suggestions.get('core_visual_elements', '无')}
角色互动：{suggestions.get('interaction_design', '无')}
高潮：{suggestions.get('climax_design', '无')}

### Timeline
{generate_timeline_section(data)}
"""


def generate_prompt(data):
    """生成完整提示词"""
    zodiac = data.get('zodiac_sign', '未知星座')

    output = f"""{generate_detailed_report(data)}

## AI 视频生成提示词

### 标题
{zodiac}专属魔法球

### 首帧AI绘画提示词
{generate_first_frame_prompt(data)}

### 视频生成提示词
{generate_overview_section(data)}

### 时间线
{generate_timeline_section(data)}

禁止出现文字、字幕、LOGO或水印。
"""
    return output


def main():
    parser = argparse.ArgumentParser(description='从分析JSON生成AI视频提示词')
    parser.add_argument('analysis_json', help='分析JSON文件路径')
    parser.add_argument('--output', required=True, help='输出Markdown文件路径')
    args = parser.parse_args()

    data = load_analysis(args.analysis_json)
    prompt = generate_prompt(data)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt, encoding='utf-8')

    print(f"[OK] 提示词已生成: {output_path}")


if __name__ == '__main__':
    main()
