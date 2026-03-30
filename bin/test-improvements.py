#!/usr/bin/env python3
"""
测试脚本 - 验证代理和API key检查的改进
"""

import importlib.util
import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from utils import ensure_utf8_output


ensure_utf8_output()


def load_module(module_name, filename):
    """从 bin 目录按文件名加载模块。"""
    path = Path(__file__).parent / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_env_loading():
    """测试 .env 文件加载"""
    print("=" * 60)
    print("测试 1: .env 文件加载")
    print("=" * 60)

    load_module("video_download", "video-download.py").load_env_file()

    api_key = os.environ.get("GEMINI_API_KEY")
    proxy_url = os.environ.get("PROXY_URL")
    model = os.environ.get("GEMINI_MODEL")

    print(f"[OK] GEMINI_API_KEY: {'已配置' if api_key else '未配置'}")
    if api_key:
        print(f"  值: {api_key[:10]}...")

    print(f"[OK] PROXY_URL: {'已配置' if proxy_url else '未配置'}")
    if proxy_url:
        print(f"  值: {proxy_url}")

    print(f"[OK] GEMINI_MODEL: {model or '使用默认值'}")
    print()

    return api_key, proxy_url, 0

def test_api_key_check():
    """测试 API key 前置检查"""
    print("=" * 60)
    print("测试 2: API key 前置检查")
    print("=" * 60)

    failures = 0
    module = load_module("gemini_analyze", "gemini-analyze.py")

    # 临时保存原始 API key
    original_key = os.environ.get("GEMINI_API_KEY")

    # 测试未配置的情况
    print("\n场景 A: 未配置 API key")
    os.environ.pop("GEMINI_API_KEY", None)

    try:
        module.check_api_key()
        print("[FAIL] 应该抛出错误但没有")
        failures += 1
    except module.FatalError:
        print("[OK] 未配置时正确抛出 FatalError")
    except Exception as exc:
        print(f"[FAIL] 抛出了意外异常: {type(exc).__name__}: {exc}")
        failures += 1

    # 恢复 API key
    if original_key:
        os.environ["GEMINI_API_KEY"] = original_key

    # 测试已配置的情况
    print("\n场景 B: 已配置 API key")
    if original_key:
        try:
            key = module.check_api_key()
            print(f"[OK] API key 检查通过: {key[:10]}...")
        except Exception as exc:
            print(f"[FAIL] 检查失败: {exc}")
            failures += 1
    else:
        print("[SKIP] 跳过测试（.env 中未配置 API key）")

    print()
    return failures

def test_proxy_setup():
    """测试代理设置"""
    print("=" * 60)
    print("测试 3: 代理设置")
    print("=" * 60)

    failures = 0
    proxy_url = os.environ.get("PROXY_URL")

    if proxy_url:
        load_module("video_download_for_proxy", "video-download.py").load_env_file()
        load_module("utils_for_proxy", "utils.py").setup_proxy()
        print(f"[OK] PROXY_URL 已配置: {proxy_url}")

        # 检查环境变量是否设置
        http_proxy = os.environ.get("HTTP_PROXY")
        https_proxy = os.environ.get("HTTPS_PROXY")
        all_proxy = os.environ.get("ALL_PROXY")

        print(f"  HTTP_PROXY: {http_proxy or '未设置'}")
        print(f"  HTTPS_PROXY: {https_proxy or '未设置'}")
        print(f"  ALL_PROXY: {all_proxy or '未设置'}")

        if http_proxy and https_proxy and all_proxy:
            print("[OK] 代理环境变量设置正确")
        else:
            print("[FAIL] 代理环境变量未完全设置")
            failures += 1
    else:
        print("[SKIP] PROXY_URL 未配置")

    print()
    return failures

def main():
    print("\n" + "=" * 60)
    print("视频拆解技能 - 改进功能测试")
    print("=" * 60 + "\n")

    # 运行测试
    api_key, proxy_url, failures = test_env_loading()
    failures += test_api_key_check()
    failures += test_proxy_setup()

    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"API key 配置: {'[OK] 已配置' if api_key else '[WARN] 未配置'}")
    print(f"代理配置: {'[OK] 已配置' if proxy_url else '[SKIP] 未配置（可选）'}")
    print(f"失败数: {failures}")
    print("\n如果失败数为 0，说明改进功能工作正常。")
    print("=" * 60 + "\n")

    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
