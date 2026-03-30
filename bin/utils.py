#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享工具函数 — 供 bin/ 下各脚本复用
"""

import os
import sys
from pathlib import Path


def ensure_utf8_output():
    """在 Windows 控制台下尽量统一为 UTF-8 输出。"""
    if sys.platform != "win32":
        return

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        try:
            stream.reconfigure(encoding="utf-8")
            continue
        except (AttributeError, ValueError):
            pass

        buffer = getattr(stream, "buffer", None)
        if buffer is None:
            continue

        import codecs

        setattr(sys, stream_name, codecs.getwriter("utf-8")(buffer, "strict"))


def load_env_file():
    """从项目根目录的 .env 文件加载环境变量"""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.is_file():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def setup_proxy():
    """设置代理环境变量，返回代理 URL 或 None"""
    proxy_url = os.environ.get("PROXY_URL")
    if proxy_url:
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        os.environ["ALL_PROXY"] = proxy_url
        print(f"[OK] 使用代理: {proxy_url}")
        return proxy_url
    else:
        print("[WARNING] 未配置代理，如果 API 调用失败请在 .env 文件中设置 PROXY_URL")
        return None
