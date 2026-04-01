#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate-seedance.py — 从分析JSON生成Seedance 2.0专属提示词
平衡策略：保留关键视觉细节，删除分析性描述，用@素材替代冗长文字
"""

import json
import argparse
import re
from pathlib import Path
from utils import ensure_utf8_output, load_env_file

ensure_utf8_output()
load_env_file()


def load_analysis(path):
    """加载分析JSON"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_visual_action(text):
    """提取纯视觉动作，删除情绪分析和非视觉描述"""
    # 删除情绪描述
    text = re.sub(r'传达出.*?[。，]', '', text)
    text = re.sub(r'表现出.*?[。，]', '', text)
    text = re.sub(r'情绪.*?[。，]', '', text)

    # 保留音效描述（真实数据显示70%的提示词包含音效，高优先级）
    # 删除重复的光影描述（光影在开头总述一次即可）
    text = re.sub(r'光线.*?[。，]', '', text)
    text = re.sub(r'色调.*?[。，]', '', text)

    return text.strip()


def simplify_camera_movement(camera_desc):
    """简化运镜描述为单一动作"""
    if '推进' in camera_desc or 'Dolly in' in camera_desc or '推近' in camera_desc:
        return '镜头推进'
    elif '拉远' in camera_desc or 'Dolly out' in camera_desc:
        return '镜头拉远'
    elif '震动' in camera_desc or 'shake' in camera_desc.lower():
        return '镜头震动'
    elif '俯视' in camera_desc or '俯拍' in camera_desc:
        return '镜头俯视'
    elif '仰视' in camera_desc or '仰拍' in camera_desc:
        return '镜头仰视'
    elif '跟随' in camera_desc or 'tracking' in camera_desc.lower():
        return '镜头跟随'
    elif '旋转' in camera_desc or '环绕' in camera_desc:
        return '镜头旋转'
    else:
        return '固定镜头'


def generate_segment_prompt(seg):
    """为单个segment生成Seedance提示词（整合场景+动作+特效）"""
    time_range = seg.get('time_range', '0-1秒')
    camera = simplify_camera_movement(seg.get('camera_movement', ''))
    scene = seg.get('scene', '')
    action = seg.get('character_action', '')
    effects = seg.get('effects', '')

    # 提取场景描述：第一句（环境上下文）+ 战斗元素句（如有）
    scene_info = ''
    if scene:
        sentences = [s.strip() for s in scene.split('。') if s.strip()]
        env_sentence = sentences[0] if sentences else ''
        battle_sentence = ''
        if '小怪' in scene or '鱼人' in scene or '敌人' in scene or 'Boss' in scene:
            for s in sentences[1:]:
                if '小怪' in s or '鱼人' in s or 'Boss' in s or '敌人' in s:
                    battle_sentence = s
                    break
        scene_info = env_sentence + '。'
        if battle_sentence:
            scene_info += battle_sentence + '。'

    # 组合：运镜 + 场景描述 + 动作 + 特效
    parts = [camera]
    if scene_info:
        parts.append(scene_info)
    if action:
        parts.append(action)
    if effects:
        parts.append(effects)

    return f"**{time_range}：** {' '.join(parts)}"


def generate_first_frame_prompt(segments, hand_desc, scene_desc):
    """生成首帧绘图提示词"""
    if not segments:
        return ""

    # 使用Gemini分析的真实手部状态（修复：不再硬编码）
    natural_state = hand_desc.get('natural_state', '白皙纤细的女性手部')
    magic_ball = hand_desc.get('magic_ball', '乒乓球大小的魔法球')

    # 优先从当前segments第一段提取场景（适配多星座各自场景）
    # fallback到顶层scene_description
    first_seg_scene = segments[0].get('scene', '')
    if first_seg_scene:
        # 只取第一句，避免把人物动作/特效描述混入环境
        scene_env = first_seg_scene.split('。')[0]
    else:
        scene_env = scene_desc if scene_desc else "神秘的魔法环境"

    # 确保末尾有标点，避免与后续文字直接拼接（修复：补充分隔符）
    if scene_env and scene_env[-1] not in '。，,.':
        scene_env += '。'

    prompt = (
        f"电影级写实摄影，真实拍摄质感。第一人称POV视角，画面中央是{natural_state}，"
        f"手掌托举{magic_ball}。场景：{scene_env}"
        f"ARRI Alexa Mini LF拍摄，浅景深，手部清晰背景虚化，4K超高清画质。\n\n"
        f"禁止出现：CG动画、3D渲染、卡通化、动画风格、文字、字幕、LOGO、水印。"
    )

    return prompt


def generate_video_prompt(segments, visual_style):
    """生成视频提示词（包含7阶段战斗编排）"""
    if not segments:
        return ""

    first_scene = segments[0].get('scene', '')
    scene_short = first_scene.split('。')[0] if '。' in first_scene else first_scene[:80]

    prompt = f"@图片1为首帧参考。第一人称POV视角，{scene_short}\n\n"
    prompt += "## 完整Boss战流程（7阶段）\n\n"

    # 定义战斗阶段映射（对齐模板7阶段）
    stage_map = {
        0: "【阶段1：小怪清场】",
        1: "【阶段2：Boss登场】",
        2: "【阶段3：Boss首次攻击】",
        3: "【阶段4：主角闪避】",
        4: "【阶段5：主角反击准备】",
        5: "【阶段6：终极大招释放】",
        6: "【阶段7：Boss受击与结束】",
    }

    for idx, seg in enumerate(segments):
        # 添加阶段标注
        if idx in stage_map:
            prompt += f"{stage_map[idx]}\n"

        seg_text = generate_segment_prompt(seg)
        prompt += seg_text + "\n\n"

    prompt += "电影级写实摄影，ARRI Alexa Mini LF，手持微晃动，运动模糊，4K超高清。\n"
    prompt += "禁止出现文字、字幕、LOGO或水印。"

    return prompt


def parse_zodiac_names(zodiac_sign_str):
    """从zodiac_sign字段解析实际星座名称列表，支持、，, 和空格分隔"""
    if not zodiac_sign_str:
        return []
    names = re.split(r'[、，,\s]+', zodiac_sign_str.strip())
    return [n.strip() for n in names if n.strip()]


def split_segments_by_zodiac(segments, zodiac_names):
    """将segments按星座数量均分（动态边界，不依赖硬编码时间）"""
    n = len(zodiac_names)
    if n == 0 or not segments:
        return [[] for _ in zodiac_names]

    chunk_size = len(segments) / n
    result = []
    for i in range(n):
        start = int(i * chunk_size)
        end = int((i + 1) * chunk_size) if i < n - 1 else len(segments)
        result.append(segments[start:end])
    return result


def parse_time(time_str):
    """解析时间字符串为秒数"""
    time_str = time_str.strip()
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(time_str.replace('秒', ''))


def main():
    parser = argparse.ArgumentParser(description='从分析JSON生成Seedance 2.0专属提示词')
    parser.add_argument('analysis_json', help='分析JSON文件路径')
    parser.add_argument('--output-dir', required=True, help='输出目录')
    args = parser.parse_args()

    data = load_analysis(args.analysis_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    segments = data.get('segments', [])
    hand_desc = data.get('hand_description', {})
    visual_style = data.get('visual_style', {})
    zodiac_signs = data.get('zodiac_sign', '')
    scene_desc = data.get('scene_description', '')

    # 解析实际星座名称（修复：不再硬编码，支持、，, 和空格分隔）
    zodiac_names = parse_zodiac_names(zodiac_signs)
    is_multi_zodiac = len(zodiac_names) > 1

    if is_multi_zodiac:
        # 多星座视频，按实际星座名称拆分
        print(f"检测到多星座视频（{zodiac_signs}），自动拆分为{len(zodiac_names)}个文件")
        zodiac_segments = split_segments_by_zodiac(segments, zodiac_names)

        for name, segs in zip(zodiac_names, zodiac_segments):
            if not segs:
                continue

            output_file = output_dir / f'seedance-{name}.md'
            first_frame = generate_first_frame_prompt(segs, hand_desc, scene_desc)
            video_prompt = generate_video_prompt(segs, visual_style)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f'# Seedance 2.0 提示词 - {name}\n\n')
                f.write('## 首帧绘图提示词\n\n')
                f.write(first_frame + '\n\n')
                f.write('---\n\n')
                f.write('## 视频生成提示词\n\n')
                f.write(video_prompt)

            print(f"[OK] {name}提示词已生成: {output_file}")
    else:
        # 单一主题
        output_file = output_dir / 'seedance-prompt.md'
        first_frame = generate_first_frame_prompt(segments, hand_desc, scene_desc)
        video_prompt = generate_video_prompt(segments, visual_style)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('# Seedance 2.0 提示词\n\n')
            f.write('## 首帧绘图提示词\n\n')
            f.write(first_frame + '\n\n')
            f.write('---\n\n')
            f.write('## 视频生成提示词\n\n')
            f.write(video_prompt)

        print(f"[OK] Seedance提示词已生成: {output_file}")


if __name__ == '__main__':
    main()


