#!/usr/bin/env python3
"""
gemini-analyze.py — 使用 Google Gemini API 分析视频内容
用法: python gemini-analyze.py <视频文件路径> [--prompt-file <prompt文件路径>]
输出: JSON 格式的视频拆解分析结果
"""

import sys
import os
import json
import time
import re
import argparse
from pathlib import Path


class FatalError(Exception):
    """Raised when the program encounters an unrecoverable error."""


def load_env_file():
    """从 .env 文件加载环境变量"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, "..", ".env")
    if os.path.isfile(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def check_dependencies():
    """检查必要依赖是否安装"""
    try:
        from google import genai  # noqa: F401
    except ImportError:
        raise FatalError(
            "google-genai 未安装。请运行:\n"
            "  pip install google-genai\n"
            "  或运行 setup.sh / setup.ps1 安装所有依赖。"
        )


def get_api_key():
    """获取 Gemini API key"""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise FatalError(
            "未设置 GEMINI_API_KEY 环境变量。\n"
            "请通过以下方式设置:\n"
            "  export GEMINI_API_KEY='your-api-key'\n"
            "  或 PowerShell: $env:GEMINI_API_KEY='your-api-key'\n"
            "  或在 Claude Code settings.json 中配置 env.GEMINI_API_KEY\n\n"
            "获取 API key: https://aistudio.google.com/apikey"
        )
    return key


def get_model_name():
    """获取 Gemini 模型名称，支持环境变量覆盖"""
    # 默认使用 gemini-2.5-flash，可通过 GEMINI_MODEL 环境变量覆盖
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def upload_video(client, video_path):
    """上传视频文件到 Gemini Files API"""
    file_size = os.path.getsize(video_path)
    file_size_mb = file_size / (1024 * 1024)

    if file_size_mb > 2048:
        raise FatalError(f"文件大小 {file_size_mb:.1f}MB 超过 2GB 限制。")

    print(f"正在上传视频 ({file_size_mb:.1f}MB)...")

    try:
        uploaded_file = client.files.upload(file=video_path)
        print(f"上传完成! 文件ID: {uploaded_file.name}")
        return uploaded_file
    except Exception as e:
        raise FatalError(
            f"视频上传失败 — {e}\n"
            "请检查:\n"
            "  - API key 是否有效\n"
            "  - 网络连接是否正常\n"
            "  - API 配额是否充足"
        ) from e


def wait_for_processing(client, uploaded_file, timeout=600):
    """等待视频处理完成，带进度显示"""
    print("等待 Gemini 处理视频...")
    start_time = time.time()
    poll_count = 0
    consecutive_errors = 0
    is_tty = sys.stdout.isatty()

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print(f"ERROR: 视频处理超时（{timeout}秒）。")
            print("大文件可能需要更长时间，请稍后重试。")
            raise RuntimeError("视频处理超时")

        try:
            file_info = client.files.get(name=uploaded_file.name)
            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            if consecutive_errors >= 5:
                print(f"ERROR: 连续 {consecutive_errors} 次查询失败，放弃重试。最后错误: {e}")
                raise RuntimeError(f"查询处理状态连续失败: {e}")
            print(f"WARNING: 查询处理状态失败 — {e}，正在重试 ({consecutive_errors}/5)...")
            time.sleep(5)
            continue

        state = file_info.state.name if hasattr(file_info.state, 'name') else str(file_info.state)

        if state == "ACTIVE":
            print(f"视频处理完成! (耗时 {elapsed:.0f}秒)")
            return file_info
        elif state == "FAILED":
            print("ERROR: 视频处理失败。可能原因:")
            print("  - 视频格式不支持")
            print("  - 视频内容无法解析")
            raise RuntimeError("视频处理失败")

        poll_count += 1
        if is_tty:
            dots = "." * (poll_count % 4 + 1)
            print(f"  处理中{dots} ({elapsed:.0f}秒)", end="\r")
        elif poll_count % 6 == 0:  # 非终端每30秒输出一次
            print(f"  处理中... ({elapsed:.0f}秒)")
        time.sleep(5)


def analyze_video(client, uploaded_file, prompt_text, model_name, timeout=600):
    """发送分析请求并获取结果（使用流式响应避免代理超时）"""
    print(f"正在分析视频内容（模型: {model_name}，这可能需要1-3分钟）...")

    try:
        chunks = []
        start_time = time.time()
        chunk_count = 0
        for chunk in client.models.generate_content_stream(
            model=model_name,
            contents=[uploaded_file, prompt_text],
        ):
            if time.time() - start_time > timeout:
                raise RuntimeError(f"分析超时（{timeout}秒），已收到部分结果")
            if chunk.text:
                chunks.append(chunk.text)
                chunk_count += 1
                if chunk_count % 5 == 0:
                    sys.stdout.write(".")
                    sys.stdout.flush()
        print()  # 换行

        full_text = "".join(chunks)
        if not full_text:
            raise RuntimeError("Gemini 返回了空结果")

        print("分析完成!")
        return full_text

    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print("ERROR: API 配额耗尽。请稍后重试或升级 API 计划。")
        elif "permission" in error_msg.lower() or "403" in error_msg:
            print("ERROR: API key 权限不足。请检查 key 是否有效。")
        elif "not found" in error_msg.lower() or "404" in error_msg:
            print("ERROR: 模型不可用。请检查 API 版本。")
        else:
            print(f"ERROR: 分析失败 — {e}")
        raise


def cleanup_file(client, uploaded_file):
    """清理上传的文件"""
    try:
        client.files.delete(name=uploaded_file.name)
        print("已清理临时文件。")
    except Exception as e:
        print(f"WARNING: 临时文件清理失败（不影响结果）— {e}")


REQUIRED_TOP_LEVEL_SCHEMA = {
    "basic_info": dict,
    "summary": str,
    "zodiac_sign": str,
    "visual_style": dict,
    "lighting_texture": dict,
    "cg_realism": dict,
    "overall_camera": str,
    "overall_sound": dict,
    "character_description": str,
    "hand_description": dict,
    "scene_description": str,
    "key_phases": list,
    "subtitle_audio": dict,
    "production_suggestions": dict,
    "segments": list,
    "additional_notes": str,
}

REQUIRED_NESTED_SCHEMA = {
    "basic_info": {
        "duration": str,
        "resolution": str,
        "aspect_ratio": str,
        "overall_style": str,
    },
    "visual_style": {
        "color_tone": str,
        "environment": str,
        "effects_style": str,
    },
    "lighting_texture": {
        "light_type": str,
        "color_tone": str,
        "texture": str,
        "special_effects": str,
    },
    "cg_realism": {
        "rendering_style": str,
        "material_detail": str,
        "lighting_system": str,
        "effects_physics": str,
        "lens_feel": str,
        "post_atmosphere": str,
    },
    "overall_sound": {
        "ambient": str,
        "music": str,
        "effects": str,
    },
    "hand_description": {
        "natural_state": str,
        "magic_ball": str,
        "effect_onset_time": str,
        "effect_progression": str,
        "effect_persistence": str,
    },
    "subtitle_audio": {
        "subtitles": str,
        "titles": str,
        "audio_estimate": str,
    },
    "production_suggestions": {
        "perspective": str,
        "environment_keys": str,
        "core_visual_elements": str,
        "interaction_design": str,
        "climax_design": str,
    },
}

SEGMENT_REQUIRED_FIELDS = {
    "time_range": str,
    "camera_movement": str,
    "shot_size": str,
    "scene": str,
    "character_action": str,
    "character_emotion": str,
    "dialogue": str,
    "dialogue_tone": str,
    "sound": str,
    "effects": str,
    "rhythm": str,
    "transition": str,
}

KEY_PHASE_REQUIRED_FIELDS = {
    "phase_name": str,
    "time_range": str,
    "action_description": str,
    "rhythm": str,
    "reference_suggestion": str,
}


def extract_json_payload(text):
    """从 Gemini 响应中提取 JSON 文本"""
    stripped = text.strip()

    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)

    raise ValueError("Gemini 返回结果不是有效 JSON，请重试。")


def validate_dict_fields(name, data, expected_fields):
    """校验 dict 中的必需字段与类型"""
    errors = []
    for key, expected_type in expected_fields.items():
        if key not in data:
            errors.append(f"{name}.{key} 缺失")
        elif not isinstance(data[key], expected_type):
            actual_type = type(data[key]).__name__
            errors.append(f"{name}.{key} 类型错误（期望 {expected_type.__name__}，实际 {actual_type}）")
    return errors


def validate_analysis_schema(raw):
    """严格校验 Gemini 分析 JSON schema"""
    if not isinstance(raw, dict):
        raise ValueError(f"分析结果根节点必须是对象，实际为 {type(raw).__name__}")

    errors = validate_dict_fields("root", raw, REQUIRED_TOP_LEVEL_SCHEMA)

    for section_name, fields in REQUIRED_NESTED_SCHEMA.items():
        section = raw.get(section_name)
        if isinstance(section, dict):
            errors.extend(validate_dict_fields(section_name, section, fields))

    key_phases = raw.get("key_phases")
    if isinstance(key_phases, list):
        if not key_phases:
            errors.append("key_phases 不能为空")
        for index, phase in enumerate(key_phases, start=1):
            if not isinstance(phase, dict):
                errors.append(f"key_phases[{index}] 必须是对象")
                continue
            errors.extend(validate_dict_fields(f"key_phases[{index}]", phase, KEY_PHASE_REQUIRED_FIELDS))

    segments = raw.get("segments")
    if isinstance(segments, list):
        if not segments:
            errors.append("segments 不能为空")
        for index, segment in enumerate(segments, start=1):
            if not isinstance(segment, dict):
                errors.append(f"segments[{index}] 必须是对象")
                continue
            errors.extend(validate_dict_fields(f"segments[{index}]", segment, SEGMENT_REQUIRED_FIELDS))

    if errors:
        raise ValueError("分析结果缺少必需字段:\n- " + "\n- ".join(errors))


def parse_json_response(text):
    """从 Gemini 响应中提取 JSON 并做严格 schema 验证"""
    payload = extract_json_payload(text)

    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini 返回了无法解析的 JSON：{e}") from e

    validate_analysis_schema(raw)
    return raw


def main():
    parser = argparse.ArgumentParser(description="使用 Gemini API 分析视频")
    parser.add_argument("video_path", help="视频文件路径")
    parser.add_argument(
        "--prompt-file",
        default=None,
        help="分析提示词文件路径（默认使用 templates/gemini-prompt.txt）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出JSON文件路径（默认输出到stdout）",
    )
    args = parser.parse_args()

    # 加载 .env 环境变量
    load_env_file()

    # 验证视频文件
    if not os.path.isfile(args.video_path):
        raise FatalError(f"视频文件不存在: {args.video_path}")

    # 检查依赖
    check_dependencies()
    from google import genai

    # 获取 API key 和模型名
    api_key = get_api_key()
    model_name = get_model_name()

    # 读取分析 prompt
    prompt_file = args.prompt_file
    if not prompt_file:
        # 默认路径：相对于脚本所在目录的 ../templates/gemini-prompt.txt
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_file = os.path.join(script_dir, "..", "templates", "gemini-prompt.txt")

    if not os.path.isfile(prompt_file):
        raise FatalError(f"提示词文件不存在: {prompt_file}")

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    # 初始化 Gemini 客户端
    print("初始化 Gemini API...")

    # 配置代理（如果设置了PROXY_URL环境变量）
    proxy_url = os.environ.get("PROXY_URL")
    if proxy_url:
        print(f"使用代理: {proxy_url}")
        # 设置环境变量供httpx使用
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url

    client = genai.Client(api_key=api_key)

    # 上传视频
    uploaded_file = upload_video(client, args.video_path)

    try:
        # 等待处理
        processed_file = wait_for_processing(client, uploaded_file)

        # 分析视频
        result_text = analyze_video(client, processed_file, prompt_text, model_name)

        # 解析结果
        result = parse_json_response(result_text)

        # 输出结果
        output_json = json.dumps(result, ensure_ascii=False, indent=2)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_json)
            print(f"分析结果已保存到: {output_path}")
        else:
            print("---ANALYSIS_RESULT_START---")
            print(output_json)
            print("---ANALYSIS_RESULT_END---")

    finally:
        # 清理上传的文件
        cleanup_file(client, uploaded_file)


if __name__ == "__main__":
    try:
        main()
    except FatalError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
