"""
工具函数模块
提供各种辅助功能
"""

import os
import re
import socket
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin


def normalize_path(path: str) -> Path:
    """
    标准化路径

    Args:
        path: 路径字符串

    Returns:
        Path对象(绝对路径)
    """
    p = Path(path)
    return p.expanduser().resolve()


def ensure_dir(path: str) -> Path:
    """
    确保目录存在,不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path对象
    """
    p = normalize_path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_relative_path(file_path: Path, base_path: Path) -> Path:
    """
    获取相对路径

    Args:
        file_path: 文件路径
        base_path: 基准路径

    Returns:
        相对路径
    """
    try:
        return file_path.relative_to(base_path)
    except ValueError:
        # 如果不在同一路径树下,返回文件名
        return Path(file_path.name)


def build_output_path(
    html_path: Path,
    input_dir: Path,
    output_dir: Path,
    keep_structure: bool = True
) -> Path:
    """
    构建输出PDF路径

    Args:
        html_path: HTML文件路径
        input_dir: 输入根目录
        output_dir: 输出根目录
        keep_structure: 是否保持目录结构

    Returns:
        PDF文件路径
    """
    if keep_structure:
        # 保持目录结构
        rel_path = get_relative_path(html_path, input_dir)
        pdf_path = output_dir / rel_path.with_suffix('.pdf')
    else:
        # 平铺在输出目录
        pdf_path = output_dir / html_path.with_suffix('.pdf').name

    # 确保父目录存在
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    return pdf_path


def build_file_url(file_path: Path, base_url: str) -> str:
    """
    构建文件的HTTP URL

    Args:
        file_path: 文件路径(绝对路径)
        base_url: 基础URL(如 http://localhost:8000)

    Returns:
        完整URL
    """
    # 将Windows路径转换为URL格式
    path_str = str(file_path).replace('\\', '/')

    # 如果base_url以/结尾,去掉
    base_url = base_url.rstrip('/')

    # 构建URL
    url = urljoin(base_url + '/', path_str)

    return url


def sanitize_filename(filename: str) -> str:
    """
    清洗文件名,移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清洗后的文件名
    """
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # 移除控制字符
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)

    # 限制长度
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:195] + ext

    return filename


def format_size(size_bytes: int) -> str:
    """
    格式化字节大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的字符串(如 "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """
    格式化时长

    Args:
        seconds: 秒数

    Returns:
        格式化后的字符串(如 "1h 23m 45s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> Optional[int]:
    """
    查找可用端口

    Args:
        start_port: 起始端口
        max_attempts: 最大尝试次数

    Returns:
        可用端口,如果找不到返回None
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None


def is_port_in_use(port: int, host: str = 'localhost') -> bool:
    """
    检查端口是否被占用

    Args:
        port: 端口号
        host: 主机地址

    Returns:
        是否被占用
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return False
    except OSError:
        return True


def truncate_string(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


if __name__ == "__main__":
    # 测试代码
    print("测试工具函数...")

    # 测试路径处理
    html_path = Path("/home/user/docs/tools/sqltools.html")
    input_dir = Path("/home/user/docs")
    output_dir = Path("/home/user/output")

    pdf_path = build_output_path(html_path, input_dir, output_dir, keep_structure=True)
    print(f"输出路径: {pdf_path}")

    # 测试大小格式化
    print(f"1024 bytes = {format_size(1024)}")
    print(f"1048576 bytes = {format_size(1048576)}")

    # 测试时长格式化
    print(f"45秒 = {format_duration(45)}")
    print(f"125秒 = {format_duration(125)}")
    print(f"3725秒 = {format_duration(3725)}")

    # 测试端口查找
    port = find_available_port(8000)
    print(f"找到可用端口: {port}")

    # 测试文件名清洗
    dirty_name = "test<file>:name?.html"
    clean_name = sanitize_filename(dirty_name)
    print(f"清洗文件名: {dirty_name} -> {clean_name}")

    print("\n工具函数测试完成!")
