#!/usr/bin/env python3
"""
generate-prompts.py — 从分析JSON生成AI视频提示词
用法: python bin/generate-prompts.py <analysis.json> --output <output.md>
"""

import json
import sys
import argparse
from pathlib import Path


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
    prompt += """次表面散射的真实皮肤，物理正确的光影，全局光照，体积光穿透空气，HDR高动态范围。照片级写实，电影实拍质感，避免3D渲染感。"""

    return prompt


def generate_overview_section(data):
    """生成总述区"""
    char = data.get('character_description', '')
    scene = data.get('scene_description', '')
    visual = data.get('visual_style', {})
    lighting = data.get('lighting_texture', {})
    cg = data.get('cg_realism', {})
    camera = data.get('overall_camera', '')
    sound = data.get('overall_sound', {})

    overview = f"""**核心主题**：{data.get('summary', '视频核心内容')[:100]}

**角色设定**：{char}

**环境**：{scene}

**视觉风格与色调**：电影实拍质感，真实摄影机拍摄。{cg.get('rendering_style', '照片级写实')}。{visual.get('color_tone', '自然色调')}。照片级写实，避免3D渲染感。

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

    for seg in segments:
        time_range = seg.get('time_range', '0-1s')
        section = f"""{time_range}

运镜：{seg.get('camera_movement', '固定镜头')}；
画面描述：{seg.get('scene', '画面内容')}；
人物动作：{seg.get('character_action', '无')}；
手部状态：{seg.get('effects', '自然状态')}；
人物情绪：{seg.get('character_emotion', '平静')}；
特效：{seg.get('effects', '无')}；
台词（{seg.get('dialogue_tone', '平静')}）："{seg.get('dialogue', '无')}"；
声音：{seg.get('sound', '环境音')}；
转场：{seg.get('transition', '无')}
"""
        timeline.append(section)

    return '\n'.join(timeline)


def generate_prompt(data):
    """生成完整提示词"""
    zodiac = data.get('zodiac_sign', '未知星座')

    output = f"""# {zodiac}专属魔法球

## 首帧AI绘画提示词

{generate_first_frame_prompt(data)}

---

## 视频生成提示词

{generate_overview_section(data)}

---

## 时间线

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

    print(f"✓ 提示词已生成: {output_path}")


if __name__ == '__main__':
    main()
