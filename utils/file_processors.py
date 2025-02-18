"""
文件处理工具类
Created by: tao-xiaoxin
Created time: 2025-02-17 06:35:40
"""
import math
import os
import base64
import hashlib
import mimetypes
from typing import Union, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def get_file_md5(file_content: Union[bytes, str]) -> str:
    """
    计算文件内容的MD5值

    Args:
        file_content: 文件内容（字节数据）或文件路径

    Returns:
        str: 文件内容的MD5哈希值

    Raises:
        FileNotFoundError: 当提供的文件路径不存在时
        IOError: 当读取文件失败时
    """
    try:
        if isinstance(file_content, str):
            with open(file_content, "rb") as f:
                file_content = f.read()
        return hashlib.md5(file_content).hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate MD5: {str(e)}")
        raise


def convert_size(size_bytes: int) -> Union[float, str]:
    """
    将字节大小转换为合适的单位

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        Union[float, str]: 转换后的大小，保留两位小数

    Examples:
        >>> convert_size(1234)
        '1.21 KB'
        >>> convert_size(1234567)
        '1.18 MB'
    """
    if size_bytes == 0:
        return "0 B"

    # 定义单位
    size_units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")

    # 计算单位的幂
    power = int(math.log(size_bytes, 1024))

    # 确保不超过最大单位
    power = min(power, len(size_units) - 1)

    # 计算最终大小
    size = size_bytes / (1024 ** power)

    # 返回格式化的字符串，保留两位小数
    return f"{size:.2f} {size_units[power]}"


def to_base64(file_content: Union[bytes, str]) -> str:
    """
    将文件内容转换为base64字符串

    Args:
        file_content: 文件内容（字节数据）或文件路径

    Returns:
        str: base64编码的字符串

    Raises:
        FileNotFoundError: 当提供的文件路径不存在时
        IOError: 当读取文件失败时
    """
    try:
        if isinstance(file_content, str):
            with open(file_content, "rb") as f:
                file_content = f.read()
        return base64.b64encode(file_content).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to encode to base64: {str(e)}")
        raise


def from_base64(base64_str: str) -> bytes:
    """
    将base64字符串转换为字节数据

    Args:
        base64_str: base64编码的字符串

    Returns:
        bytes: 解码后的字节数据

    Raises:
        ValueError: 当base64字符串格式无效时
    """
    try:
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        return base64.b64decode(base64_str)
    except Exception as e:
        logger.error(f"Failed to decode base64: {str(e)}")
        raise


def get_file_extension(filename: str = None, mime_type: str = None) -> Optional[str]:
    """
    获取文件扩展名

    可以通过文件名或MIME类型获取文件扩展名。
    如果同时提供了文件名和MIME类型，优先使用文件名。

    Args:
        filename: 文件名（可选）
        mime_type: MIME类型（可选）

    Returns:
        Optional[str]: 文件扩展名（不包含点号），如果无法确定则返回None

    Examples:
        >>> get_file_extension("image.jpg")
        'jpg'
        >>> get_file_extension(mime_type="image/jpeg")
        'jpg'
        >>> get_file_extension("test")
        None
    """
    try:
        if filename:
            # 从文件名获取扩展名
            ext = os.path.splitext(filename)[1]
            if ext:
                return ext[1:].lower()  # 移除点号并转换为小写

        if mime_type:
            # 从MIME类型获取扩展名
            ext = mimetypes.guess_extension(mime_type)
            if ext:
                return ext[1:].lower()  # 移除点号并转换为小写

        return None

    except Exception as e:
        logger.error(f"Failed to get file extension: {str(e)}")
        return None


def get_file_info(file_path: str) -> Tuple[str, str]:
    """
    获取文件信息，包括扩展名、MIME类型和文件大小（带单位）

    Args:
        file_path: 文件路径

    Returns:
        Tuple[str, str]: 包含扩展名、文件大小（带单位）的元组

    Raises:
        FileNotFoundError: 当文件不存在时
        IOError: 当无法访问文件时

    Examples:
        >>> get_file_info("example.jpg")
        ('jpg', '1.25 MB')
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 获取文件扩展名
        extension = get_file_extension(file_path)

        # 获取文件大小并转换为合适的单位
        file_size = os.path.getsize(file_path)
        formatted_size = convert_size(file_size)

        return extension, formatted_size

    except Exception as e:
        logger.error(f"Failed to get file info: {str(e)}")
        raise


def get_file_size_mb(size_bytes: int, decimal_places: int = 2) -> float:
    """
    将字节大小转换为MB单位

    Args:
        size_bytes: 文件大小（字节）
        decimal_places: 保留小数位数，默认为2

    Returns:
        float: MB为单位的文件大小

    Examples:
        >>> get_file_size_mb(1048576)  # 1MB
        1.0
        >>> get_file_size_mb(2097152)  # 2MB
        2.0
    """
    return round(size_bytes / (1024 * 1024), decimal_places)
