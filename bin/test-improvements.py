#!/usr/bin/env python3
"""
测试脚本 - 验证代理和API key检查的改进
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_env_loading():
    """测试 .env 文件加载"""
    print("=" * 60)
    print("测试 1: .env 文件加载")
    print("=" * 60)

    # 导入 load_env_file 函数
    if os.path.exists("video-download.py"):
        import importlib.util
        spec = importlib.util.spec_from_file_location("video_download", "video-download.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        module.load_env_file()

        # 检查环境变量
        api_key = os.environ.get("GEMINI_API_KEY")
        proxy_url = os.environ.get("PROXY_URL")
        model = os.environ.get("GEMINI_MODEL")

        print(f"✓ GEMINI_API_KEY: {'已配置' if api_key else '未配置'}")
        if api_key:
            print(f"  值: {api_key[:10]}...")

        print(f"✓ PROXY_URL: {'已配置' if proxy_url else '未配置'}")
        if proxy_url:
            print(f"  值: {proxy_url}")

        print(f"✓ GEMINI_MODEL: {model or '使用默认值'}")
        print()

        return api_key, proxy_url
    else:
        print("ERROR: 找不到 video-download.py")
        return None, None

def test_api_key_check():
    """测试 API key 前置检查"""
    print("=" * 60)
    print("测试 2: API key 前置检查")
    print("=" * 60)

    # 临时保存原始 API key
    original_key = os.environ.get("GEMINI_API_KEY")

    # 测试未配置的情况
    print("\n场景 A: 未配置 API key")
    os.environ.pop("GEMINI_API_KEY", None)

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("gemini_analyze", "gemini-analyze.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        module.check_api_key_early()
        print("✗ 应该抛出错误但没有")
    except Exception as e:
        print(f"✓ 正确捕获错误: {type(e).__name__}")

    # 恢复 API key
    if original_key:
        os.environ["GEMINI_API_KEY"] = original_key

    # 测试已配置的情况
    print("\n场景 B: 已配置 API key")
    if original_key:
        try:
            key = module.check_api_key_early()
            print(f"✓ API key 检查通过: {key[:10]}...")
        except Exception as e:
            print(f"✗ 检查失败: {e}")
    else:
        print("⚠ 跳过测试（.env 中未配置 API key）")

    print()

def test_proxy_setup():
    """测试代理设置"""
    print("=" * 60)
    print("测试 3: 代理设置")
    print("=" * 60)

    proxy_url = os.environ.get("PROXY_URL")

    if proxy_url:
        print(f"✓ PROXY_URL 已配置: {proxy_url}")

        # 检查环境变量是否设置
        http_proxy = os.environ.get("HTTP_PROXY")
        https_proxy = os.environ.get("HTTPS_PROXY")
        all_proxy = os.environ.get("ALL_PROXY")

        print(f"  HTTP_PROXY: {http_proxy or '未设置'}")
        print(f"  HTTPS_PROXY: {https_proxy or '未设置'}")
        print(f"  ALL_PROXY: {all_proxy or '未设置'}")

        if http_proxy and https_proxy:
            print("✓ 代理环境变量设置正确")
        else:
            print("⚠ 代理环境变量未完全设置")
    else:
        print("⚠ PROXY_URL 未配置")

    print()

def main():
    print("\n" + "=" * 60)
    print("视频拆解技能 - 改进功能测试")
    print("=" * 60 + "\n")

    # 切换到脚本所在目录
    os.chdir(Path(__file__).parent)

    # 运行测试
    api_key, proxy_url = test_env_loading()
    test_api_key_check()
    test_proxy_setup()

    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"API key 配置: {'✓ 已配置' if api_key else '✗ 未配置'}")
    print(f"代理配置: {'✓ 已配置' if proxy_url else '⚠ 未配置（可选）'}")
    print("\n如果所有测试通过，改进功能已正常工作！")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
