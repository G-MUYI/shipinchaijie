#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享工具函数 — 供 bin/ 下各脚本复用
"""

import os
import socket
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


def check_proxy_available(host, port, timeout=2):
    """检测代理端口是否可用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def find_available_proxy():
    """自动检测可用的代理端口"""
    common_ports = [7890, 7897, 1080, 10809, 10808, 8080, 8118]

    for port in common_ports:
        if check_proxy_available("127.0.0.1", port):
            return f"http://127.0.0.1:{port}"

    return None


def setup_proxy():
    """设置代理环境变量，返回代理 URL 或 None"""
    proxy_url = os.environ.get("PROXY_URL")

    if proxy_url:
        # 检测配置的代理是否可用
        try:
            if "://" in proxy_url:
                host_port = proxy_url.split("://")[1]
            else:
                host_port = proxy_url

            host, port = host_port.split(":")
            port = int(port)

            if check_proxy_available(host, port):
                os.environ["HTTP_PROXY"] = proxy_url
                os.environ["HTTPS_PROXY"] = proxy_url
                os.environ["ALL_PROXY"] = proxy_url
                print(f"[OK] 使用配置的代理: {proxy_url}")
                return proxy_url
            else:
                print(f"[WARNING] 配置的代理 {proxy_url} 不可用，尝试自动检测...")
        except Exception:
            print(f"[WARNING] 代理配置格式错误: {proxy_url}，尝试自动检测...")

    # 自动检测可用代理
    auto_proxy = find_available_proxy()
    if auto_proxy:
        os.environ["HTTP_PROXY"] = auto_proxy
        os.environ["HTTPS_PROXY"] = auto_proxy
        os.environ["ALL_PROXY"] = auto_proxy
        print(f"[OK] 自动检测到可用代理: {auto_proxy}")
        return auto_proxy

    print("[WARNING] 未找到可用代理，如果 API 调用失败请检查代理设置")
    return None
