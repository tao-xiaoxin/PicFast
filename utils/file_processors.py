"""
文件处理工具类
Created by: tao-xiaoxin
Created time: 2025-02-17 06:35:40
"""

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


def get_file_info(file_path: str) -> Tuple[str, str, int]:
    """
    获取文件信息，包括扩展名、MIME类型和文件大小

    Args:
        file_path: 文件路径

    Returns:
        Tuple[str, str, int]: 包含扩展名、MIME类型和文件大小的元组

    Raises:
        FileNotFoundError: 当文件不存在时
        IOError: 当无法访问文件时
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 获取文件扩展名
        extension = get_file_extension(file_path)

        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)

        # 获取文件大小
        file_size = os.path.getsize(file_path)

        return extension or "", mime_type or "application/octet-stream", file_size

    except Exception as e:
        logger.error(f"Failed to get file info: {str(e)}")
        raise


# 初始化MIME类型映射
mimetypes.init()

# 添加常见的文件扩展名映射
COMMON_EXTENSIONS = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/svg+xml': '.svg',
    'application/pdf': '.pdf',
    'text/plain': '.txt',
    'text/html': '.html',
    'application/json': '.json',
    'application/xml': '.xml'
}

for mime_type, ext in COMMON_EXTENSIONS.items():
    mimetypes.add_type(mime_type, ext)