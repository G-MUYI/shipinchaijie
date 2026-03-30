#!/usr/bin/env python3
"""
video-download.py — 使用 yt-dlp 下载视频（跨平台）
用法: python video-download.py <URL> [输出目录]
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from utils import ensure_utf8_output, load_env_file, setup_proxy


ensure_utf8_output()


def format_file_size(size_bytes):
    """格式化文件大小"""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.1f}{units[unit_index]}"


def sanitize_title(title):
    """清理标题中的特殊字符，保留中文"""
    safe = re.sub(r"[^\w\u4e00-\u9fff\u3400-\u4dbf\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af-]", "_", title).strip("_")
    if not safe:
        safe = "video"
    return safe[:100]


def main():
    # 加载.env文件中的配置
    load_env_file()

    parser = argparse.ArgumentParser(description="使用 yt-dlp 下载视频")
    parser.add_argument("url", help="视频 URL")
    parser.add_argument("output_dir", nargs="?", default=None, help="输出目录")
    parser.add_argument("--proxy", default=None, help="代理服务器 (例如: http://127.0.0.1:7890)")
    args = parser.parse_args()

    # 立即设置代理，确保所有网络操作都使用代理
    # 优先级：命令行参数 > .env文件中的PROXY_URL
    proxy = args.proxy or setup_proxy()

    # 确定输出目录
    output_dir = args.output_dir or tempfile.gettempdir()
    os.makedirs(output_dir, exist_ok=True)

    # 检查 yt-dlp
    ytdlp_cmd = ["python", "-m", "yt_dlp"]
    try:
        subprocess.run(ytdlp_cmd + ["--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        if not shutil.which("yt-dlp"):
            print("ERROR: yt-dlp 未安装。请运行 setup.sh 或 setup.ps1 安装依赖。")
            sys.exit(1)
        ytdlp_cmd = ["yt-dlp"]

    # 获取视频标题
    print("正在解析视频信息...")
    title = ""
    proxy_args = ["--proxy", proxy] if proxy else []
    try:
        result = subprocess.run(
            ytdlp_cmd + ["--get-title"] + proxy_args + [args.url],
            capture_output=True,
            text=True,
            timeout=30,
            env=os.environ.copy(),  # 【改进2】确保子进程继承代理环境变量
        )
        if result.returncode == 0 and result.stdout.strip():
            title = result.stdout.strip().split("\n")[0]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    if not title:
        print("WARNING: 无法获取视频标题，使用默认名称。")
        title = "video"

    safe_title = sanitize_title(title)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    basename = f"{safe_title}_{timestamp}_{os.getpid()}"
    output_file = os.path.join(output_dir, f"{basename}.mp4")

    print(f"正在下载视频: {title}")
    print(f"保存到: {output_file}")

    # 下载视频
    download_args = ytdlp_cmd + [
        "-f",
        "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        "--merge-output-format",
        "mp4",
        "-o",
        output_file,
        "--no-playlist",
        "--socket-timeout",
        "30",
        "--retries",
        "3",
    ]
    if proxy:
        download_args.extend(["--proxy", proxy])
    download_args.append(args.url)

    try:
        subprocess.run(download_args, check=True, env=os.environ.copy())  # 【改进3】确保下载时也使用代理环境变量
    except subprocess.CalledProcessError:
        print("ERROR: 视频下载失败。请检查:")
        print("  - URL 是否有效")
        print("  - 网络连接是否正常")
        if proxy:
            print(f"  - 代理 {proxy} 是否可用")
        else:
            print("  - 是否需要配置代理（在 .env 文件中设置 PROXY_URL）")
        print("  - 视频是否需要登录/付费")
        sys.exit(1)

    # 查找输出文件（yt-dlp 可能自动调整扩展名）
    resolved_file = None
    if os.path.isfile(output_file):
        resolved_file = output_file
    else:
        for f in Path(output_dir).iterdir():
            if f.name.startswith(basename) and f.is_file():
                resolved_file = str(f)
                break

    if not resolved_file:
        print("ERROR: 下载似乎成功但未找到输出文件。")
        sys.exit(1)

    file_size = os.path.getsize(resolved_file)
    if file_size == 0:
        os.remove(resolved_file)
        print("ERROR: 下载的文件为空（0字节），可能下载失败。")
        sys.exit(1)

    print(f"下载完成! 文件大小: {format_file_size(file_size)}")
    print(f"FILE_PATH={resolved_file}")


if __name__ == "__main__":
    main()
