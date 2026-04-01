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

    # 提取场景中的关键战斗元素
    scene_info = ''
    if '小怪' in scene or '鱼人' in scene or '敌人' in scene or 'Boss' in scene:
        # 提取包含敌人信息的句子
        sentences = scene.split('。')
        for s in sentences[1:]:  # 跳过第一句环境描述
            if s.strip() and ('小怪' in s or '鱼人' in s or 'Boss' in s or '敌人' in s):
                scene_info = s.strip() + '。'
                break

    # 组合：运镜 + 场景战斗元素 + 动作 + 特效
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

    first_seg = segments[0]
    action = first_seg.get('character_action', '')
    seg_scene = first_seg.get('scene', '')

    # 从 segment 的 scene 中提取完整环境描述
    scene_env = ""
    if seg_scene and '背景' in seg_scene:
        bg_start = seg_scene.find('背景')
        if bg_start != -1:
            # 提取"背景"之后到场景描述结束的所有内容
            bg_text = seg_scene[bg_start:].replace('背景', '').strip()
            # 移除开头的"虚化为"等连接词
            bg_text = re.sub(r'^(虚化为|是|为)', '', bg_text).strip()
            scene_env = bg_text

    # 如果没有提取到，使用顶层 scene_description
    if not scene_env:
        scene_env = scene_desc if scene_desc else "神秘的魔法环境"

    # 简化：只保留手部外观
    hand_visual = "一只白皙纤细的女性手部"
    if '指甲' in action or '美甲' in action:
        nail_match = re.search(r'(指甲|美甲)[^。，]*', action)
        if nail_match:
            hand_visual = f"一只白皙纤细的女性手部，{nail_match.group()}"

    prompt = f"电影级写实摄影，真实拍摄质感。第一人称POV视角，画面中央是{hand_visual}，手掌托举一颗乒乓球大小的魔法球。场景：{scene_env}ARRI Alexa Mini LF拍摄，浅景深，手部清晰背景虚化，4K超高清画质。\n\n禁止出现：CG动画、3D渲染、卡通化、动画风格、文字、字幕、LOGO、水印。"

    return prompt


def generate_video_prompt(segments, visual_style):
    """生成视频提示词（包含7阶段战斗编排）"""
    if not segments:
        return ""

    first_scene = segments[0].get('scene', '')
    scene_short = first_scene.split('。')[0] if '。' in first_scene else first_scene[:80]

    prompt = f"@图片1为首帧参考。第一人称POV视角，{scene_short}\n\n"
    prompt += "## 完整Boss战流程（7阶段）\n\n"

    # 定义战斗阶段映射
    stage_map = {
        0: "【阶段1：魔法球展示】",
        1: "【阶段2：捏爆激活+小怪冲击】",
        2: "【阶段3：AOE清场】",
        3: "【阶段4：Boss攻击+闪避反击】",
        4: "【阶段5：终极大招释放】"
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


def split_segments_by_zodiac(segments):
    """根据时间范围拆分多星座视频的segments"""
    # 根据实际视频的星座切换时间点（每个星座约15秒）
    zodiac_boundaries = [
        (0, 15),      # 双鱼座: 0-15秒
        (15, 30),     # 天秤座: 15-30秒
        (30, 45),     # 天蝎座: 30-45秒
        (45, 60),     # 白羊座: 45-60秒
        (60, 75),     # 摩羯座: 60-75秒
        (75, 999)     # 处女座: 75秒-结束
    ]

    zodiac_segments = [[] for _ in range(6)]

    for seg in segments:
        time_range = seg.get('time_range', '00:00.000-00:01.000')
        start_time = parse_time(time_range.split('-')[0])

        # 找到对应的星座索引
        for idx, (start, end) in enumerate(zodiac_boundaries):
            if start <= start_time < end:
                zodiac_segments[idx].append(seg)
                break

    return zodiac_segments


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

    # 检查是否多星座（根据zodiac_sign字段判断）
    zodiac_names = ['双鱼座', '天秤座', '天蝎座', '白羊座', '摩羯座', '处女座']

    # 只有当zodiac_sign包含多个星座时才拆分
    is_multi_zodiac = '、' in zodiac_signs or '，' in zodiac_signs

    if is_multi_zodiac:
        # 多星座视频，拆分
        print(f"检测到多星座视频，自动拆分为{len(zodiac_names)}个文件")
        zodiac_segments = split_segments_by_zodiac(segments)

        for idx, (name, segs) in enumerate(zip(zodiac_names, zodiac_segments)):
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


