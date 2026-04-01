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
    """提取纯视觉动作，删除情绪分析但保留视觉相关描述"""
    # 只删除纯情绪/心理分析描述
    text = re.sub(r'传达出.*?[。，]', '', text)
    text = re.sub(r'表现出.*?[。，]', '', text)
    text = re.sub(r'情绪.*?[。，]', '', text)
    # 保留光线和色调描述（Seedance高频元素，出现率65%）
    # 保留音效描述（真实数据显示70%的提示词包含音效，高优先级）
    return text.strip()


def simplify_camera_movement(camera_desc):
    """简化运镜描述为单一动作，保留速度和幅度信息"""
    if not camera_desc:
        return '固定镜头'

    # 提取速度修饰词
    speed = ''
    for s in ['缓慢', '缓缓', '慢慢', '快速', '骤然', '猛然', '迅速', '急速', '轻微', '微微', '小幅', '大幅']:
        if s in camera_desc:
            speed = s
            break

    # 提取景别轨迹（如"从中景到特写"）
    trajectory = ''
    traj_match = re.search(r'从(.{1,6}?)(到|至|切换到|过渡到)(.{1,6})', camera_desc)
    if traj_match:
        trajectory = f'，从{traj_match.group(1)}到{traj_match.group(3)}'

    # 确定运镜类型
    movement = '固定镜头'
    if '推进' in camera_desc or '推近' in camera_desc or 'Dolly in' in camera_desc:
        movement = '推进'
    elif '拉远' in camera_desc or 'Dolly out' in camera_desc:
        movement = '拉远'
    elif '震动' in camera_desc or 'shake' in camera_desc.lower():
        movement = '震动'
    elif '俯视' in camera_desc or '俯拍' in camera_desc:
        movement = '俯拍'
    elif '仰视' in camera_desc or '仰拍' in camera_desc:
        movement = '仰拍'
    elif '跟随' in camera_desc or 'tracking' in camera_desc.lower() or '跟拍' in camera_desc:
        movement = '跟拍'
    elif '旋转' in camera_desc or '环绕' in camera_desc:
        movement = '环绕'
    elif '横移' in camera_desc or '侧移' in camera_desc:
        movement = '横移'
    elif '手持' in camera_desc:
        movement = '手持跟拍'
    elif '航拍' in camera_desc or 'FPV' in camera_desc:
        movement = '航拍'
    elif '希区柯克' in camera_desc:
        movement = '希区柯克变焦'

    # 组合：速度 + 运镜类型 + 轨迹
    result = f'镜头{speed}{movement}' if speed else f'镜头{movement}'
    result += trajectory
    return result


def detect_content_type(data):
    """从Gemini分析数据中判断内容类型"""
    segments = data.get('segments', [])
    overall_style = data.get('basic_info', {}).get('overall_style', '')
    summary = data.get('summary', '')
    all_text = overall_style + summary

    # 合并所有segments文本用于关键词检测
    seg_text = ''
    for seg in segments:
        seg_text += seg.get('scene', '') + seg.get('character_action', '') + seg.get('effects', '')

    combined = all_text + seg_text

    # 按优先级判断内容类型
    battle_keywords = ['Boss', 'boss', '小怪', '敌人', '攻击', '闪避', '战斗', '打斗', '格斗',
                       '挥剑', '拳击', '技能释放', '对抗', '击中', '冲击波']
    dance_keywords = ['舞蹈', '跳舞', 'MV', '卡点', 'BPM', '节拍', '编舞', '舞步']
    wedding_keywords = ['婚礼', '新郎', '新娘', '婚纱', '教堂', '戒指', '誓言']
    horror_keywords = ['恐怖', '悬疑', '惊悚', '黑暗', '阴森', '鬼', '僵尸']
    scifi_keywords = ['赛博朋克', '科幻', '机械', '霓虹', '全息', '机甲', '太空']
    animal_keywords = ['动物', '拟人', '猫', '狗', 'ASMR', '萌宠']
    nature_keywords = ['风光', '自然', '日出', '日落', '山', '海', '森林', '草原']

    if any(k in combined for k in battle_keywords):
        return 'battle'
    elif any(k in combined for k in dance_keywords):
        return 'dance'
    elif any(k in combined for k in wedding_keywords):
        return 'wedding'
    elif any(k in combined for k in horror_keywords):
        return 'horror'
    elif any(k in combined for k in scifi_keywords):
        return 'scifi'
    elif any(k in combined for k in animal_keywords):
        return 'animal'
    elif any(k in combined for k in nature_keywords):
        return 'nature'
    else:
        return 'general'


def generate_segment_prompt(seg):
    """为单个segment生成Seedance提示词（保留完整视觉细节）"""
    time_range = seg.get('time_range', '0-1秒')
    camera = simplify_camera_movement(seg.get('camera_movement', ''))
    scene = seg.get('scene', '')
    action = seg.get('character_action', '')
    effects = seg.get('effects', '')
    sound = seg.get('sound', '')
    shot_size = seg.get('shot_size', '')

    # 保留完整的场景描述（不再只取第一句），但清理冗余
    scene_info = extract_visual_action(scene) if scene else ''

    # 组合：运镜 + 景别 + 场景描述 + 动作 + 特效
    parts = [camera]
    if shot_size:
        parts.append(shot_size)
    if scene_info:
        parts.append(scene_info)
    if action:
        parts.append(extract_visual_action(action))
    if effects:
        parts.append(effects)

    prompt = f"**{time_range}：** {'，'.join(parts)}"

    # 音效描述（Seedance高优先级，出现率70%）
    if sound:
        prompt += f"。音效：{sound}"

    return prompt


def generate_first_frame_prompt(segments, hand_desc, scene_desc, perspective='POV'):
    """生成首帧绘图提示词，支持不同视角"""
    if not segments:
        return ""

    # 使用Gemini分析的真实手部状态
    natural_state = hand_desc.get('natural_state', '白皙纤细的女性手部')
    magic_ball = hand_desc.get('magic_ball', '乒乓球大小的魔法球')

    # 优先从当前segments第一段提取场景（适配多星座各自场景）
    first_seg_scene = segments[0].get('scene', '')
    if first_seg_scene:
        # 提取环境相关的句子（排除人物动作/特效描述），保留更多层次
        sentences = [s.strip() for s in first_seg_scene.split('。') if s.strip()]
        env_sentences = []
        for s in sentences:
            # 保留场景/环境/光线相关描述，跳过纯动作描述
            if any(k in s for k in ['背景', '场景', '环境', '地面', '天空', '光',
                                     '建筑', '石柱', '神殿', '森林', '街道', '城市',
                                     '远处', '周围', '氛围', '雾', '雨', '雪',
                                     '前景', '中景', '火把', '符文']):
                env_sentences.append(s)
        if env_sentences:
            scene_env = '。'.join(env_sentences[:3])  # 最多保留3句环境描述
        else:
            scene_env = sentences[0] if sentences else ''
    else:
        scene_env = scene_desc if scene_desc else "神秘的魔法环境"

    # 确保末尾有标点
    if scene_env and scene_env[-1] not in '。，,.':
        scene_env += '。'

    # 根据视角类型生成不同的首帧提示词
    if perspective == 'POV':
        prompt = (
            f"电影级写实摄影，真实拍摄质感。第一人称POV视角，画面中央是{natural_state}，"
            f"手掌托举{magic_ball}。场景：{scene_env}"
            f"ARRI Alexa Mini LF拍摄，浅景深，手部清晰背景虚化，4K超高清画质。\n\n"
            f"排除：模糊，低清，噪点，扭曲，变形，CG动画，3D渲染，卡通化，动画风格，文字，字幕，LOGO，水印。"
        )
    elif perspective == 'third_person':
        prompt = (
            f"电影级写实摄影，真实拍摄质感。第三人称视角，展示角色全身姿态。"
            f"场景：{scene_env}"
            f"ARRI Alexa Mini LF拍摄，中景构图，角色位于画面中央偏左，4K超高清画质。\n\n"
            f"排除：模糊，低清，噪点，扭曲，变形，CG动画，3D渲染，卡通化，动画风格，文字，字幕，LOGO，水印。"
        )
    else:  # mixed
        prompt = (
            f"电影级写实摄影，真实拍摄质感。{scene_env}"
            f"ARRI Alexa Mini LF拍摄，4K超高清画质。\n\n"
            f"排除：模糊，低清，噪点，扭曲，变形，CG动画，3D渲染，卡通化，动画风格，文字，字幕，LOGO，水印。"
        )

    return prompt


def generate_video_prompt(segments, visual_style, content_type='general'):
    """生成视频提示词，根据内容类型选择不同结构"""
    if not segments:
        return ""

    first_scene = segments[0].get('scene', '')
    scene_short = first_scene.split('。')[0] if '。' in first_scene else first_scene[:80]

    prompt = f"@图片1为首帧参考。{scene_short}\n\n"

    # 根据内容类型选择不同的结构框架
    if content_type == 'battle':
        prompt += _generate_battle_prompt(segments)
    elif content_type == 'dance':
        prompt += _generate_dance_prompt(segments)
    elif content_type == 'wedding':
        prompt += _generate_emotional_prompt(segments)
    elif content_type == 'horror':
        prompt += _generate_horror_prompt(segments)
    else:
        prompt += _generate_general_prompt(segments)

    # 摄影参数和负向提示
    prompt += "\n\n电影级写实摄影，ARRI Alexa Mini LF，4K超高清。\n"
    prompt += "排除：模糊，低清，噪点，扭曲，变形，五官崩坏，动作僵硬，画面抖动，比例失调。\n"
    prompt += "禁止出现文字、字幕、LOGO或水印。"

    return prompt


def _generate_battle_prompt(segments):
    """战斗类内容：使用7阶段Boss战结构"""
    prompt = "## 完整战斗流程\n\n"

    # 动态分配阶段（根据实际段数，而非硬编码索引）
    total = len(segments)
    if total >= 7:
        # 有足够段数，按比例分配7阶段
        stage_boundaries = [
            (0, max(1, total // 5)),                          # 阶段1：小怪清场
            (max(1, total // 5), max(2, total * 2 // 7)),     # 阶段2：Boss登场
            (max(2, total * 2 // 7), max(3, total * 3 // 7)), # 阶段3：Boss攻击
            (max(3, total * 3 // 7), max(4, total * 4 // 7)), # 阶段4：闪避
            (max(4, total * 4 // 7), max(5, total * 5 // 7)), # 阶段5：反击准备
            (max(5, total * 5 // 7), max(6, total * 6 // 7)), # 阶段6：大招释放
            (max(6, total * 6 // 7), total),                  # 阶段7：结束
        ]
        stage_names = [
            "【阶段1：小怪清场】", "【阶段2：Boss登场】", "【阶段3：Boss首次攻击】",
            "【阶段4：主角闪避】", "【阶段5：主角反击准备】", "【阶段6：终极大招释放】",
            "【阶段7：Boss受击与结束】",
        ]
        for stage_idx, (start, end) in enumerate(stage_boundaries):
            prompt += f"{stage_names[stage_idx]}\n"
            for seg in segments[start:end]:
                prompt += generate_segment_prompt(seg) + "\n\n"
    else:
        # 段数不足7，直接按顺序输出
        for seg in segments:
            prompt += generate_segment_prompt(seg) + "\n\n"

    return prompt


def _generate_dance_prompt(segments):
    """舞蹈/MV类内容：强调节拍卡点"""
    prompt = ""
    for seg in segments:
        prompt += generate_segment_prompt(seg) + "\n\n"
    return prompt


def _generate_emotional_prompt(segments):
    """婚礼/情感类内容：强调情绪和光效"""
    prompt = ""
    for seg in segments:
        prompt += generate_segment_prompt(seg) + "\n\n"
    return prompt


def _generate_horror_prompt(segments):
    """恐怖/悬疑类内容：强调静默和渐进"""
    prompt = ""
    for seg in segments:
        prompt += generate_segment_prompt(seg) + "\n\n"
    return prompt


def _generate_general_prompt(segments):
    """通用内容：时间轴分镜式"""
    prompt = ""
    for seg in segments:
        prompt += generate_segment_prompt(seg) + "\n\n"
    return prompt


def parse_zodiac_names(zodiac_sign_str):
    """从zodiac_sign字段解析实际星座名称列表，支持、，, 和空格分隔"""
    if not zodiac_sign_str:
        return []
    names = re.split(r'[、，,\s]+', zodiac_sign_str.strip())
    return [n.strip() for n in names if n.strip()]


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


def get_segment_start_time(seg):
    """从segment的time_range中提取开始时间（秒）"""
    time_range = seg.get('time_range', '00:00.000-00:01.000')
    start_str = time_range.split('-')[0].strip()
    try:
        return parse_time(start_str)
    except (ValueError, IndexError):
        return 0.0


def split_segments_by_zodiac(segments, zodiac_names):
    """将segments按星座拆分，基于时间范围而非段数均分"""
    n = len(zodiac_names)
    if n == 0 or not segments:
        return [[] for _ in zodiac_names]

    # 计算总时长
    if len(segments) < 2:
        return [segments] + [[] for _ in range(n - 1)]

    # 获取最后一段的结束时间
    last_range = segments[-1].get('time_range', '00:00.000-00:01.000')
    try:
        end_str = last_range.split('-')[1].strip()
        total_duration = parse_time(end_str)
    except (ValueError, IndexError):
        total_duration = len(segments) * 2.0  # fallback：假设每段2秒

    # 按时间均分边界
    time_per_zodiac = total_duration / n

    result = []
    seg_idx = 0
    for i in range(n):
        boundary = (i + 1) * time_per_zodiac
        group = []
        while seg_idx < len(segments):
            start_time = get_segment_start_time(segments[seg_idx])
            # 最后一组收集所有剩余段
            if i == n - 1:
                group.append(segments[seg_idx])
                seg_idx += 1
            elif start_time < boundary:
                group.append(segments[seg_idx])
                seg_idx += 1
            else:
                break
        result.append(group)

    return result


def generate_sound_section(segments):
    """从所有segments中提取音效信息，生成统一的音效描述段"""
    sounds = []
    for seg in segments:
        sound = seg.get('sound', '')
        if sound and sound not in sounds:
            sounds.append(sound)

    if not sounds:
        return ""

    # 去重并组合
    return "音效：" + "；".join(sounds[:5]) + "。"


def main():
    parser = argparse.ArgumentParser(description='从分析JSON生成Seedance 2.0专属提示词')
    parser.add_argument('analysis_json', help='分析JSON文件路径')
    parser.add_argument('--output-dir', required=True, help='输出目录')
    parser.add_argument('--perspective', default='POV', choices=['POV', 'third_person', 'mixed'],
                        help='视角类型（默认POV）')
    args = parser.parse_args()

    data = load_analysis(args.analysis_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    segments = data.get('segments', [])
    hand_desc = data.get('hand_description', {})
    visual_style = data.get('visual_style', {})
    zodiac_signs_list = data.get('zodiac_signs', [])
    zodiac_signs = '、'.join(zodiac_signs_list) if zodiac_signs_list else ''
    scene_desc = data.get('scene_description', '')

    # 检测内容类型
    content_type = detect_content_type(data)
    print(f"检测到内容类型：{content_type}")

    # 解析实际星座名称
    zodiac_names = parse_zodiac_names(zodiac_signs)
    is_multi_zodiac = len(zodiac_names) > 1

    if is_multi_zodiac:
        # 多星座视频，按时间范围拆分
        print(f"检测到多星座视频（{zodiac_signs}），自动拆分为{len(zodiac_names)}个文件")
        zodiac_segments = split_segments_by_zodiac(segments, zodiac_names)

        for name, segs in zip(zodiac_names, zodiac_segments):
            if not segs:
                continue

            output_file = output_dir / f'seedance-{name}.md'
            first_frame = generate_first_frame_prompt(segs, hand_desc, scene_desc, args.perspective)
            video_prompt = generate_video_prompt(segs, visual_style, content_type)
            sound_section = generate_sound_section(segs)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f'# Seedance 2.0 提示词 - {name}\n\n')
                f.write('## 首帧绘图提示词\n\n')
                f.write(first_frame + '\n\n')
                f.write('---\n\n')
                f.write('## 视频生成提示词\n\n')
                f.write(video_prompt)
                if sound_section:
                    f.write('\n\n' + sound_section)

            print(f"[OK] {name}提示词已生成: {output_file}")
    else:
        # 单一主题
        output_file = output_dir / 'seedance-prompt.md'
        first_frame = generate_first_frame_prompt(segments, hand_desc, scene_desc, args.perspective)
        video_prompt = generate_video_prompt(segments, visual_style, content_type)
        sound_section = generate_sound_section(segments)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('# Seedance 2.0 提示词\n\n')
            f.write('## 首帧绘图提示词\n\n')
            f.write(first_frame + '\n\n')
            f.write('---\n\n')
            f.write('## 视频生成提示词\n\n')
            f.write(video_prompt)
            if sound_section:
                f.write('\n\n' + sound_section)

        print(f"[OK] Seedance提示词已生成: {output_file}")


if __name__ == '__main__':
    main()
