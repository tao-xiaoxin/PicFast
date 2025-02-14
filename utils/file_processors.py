"""
文件处理工具类
Created by: tao-xiaoxin
Created time: 2025-02-14 06:17:20
"""
import base64
import hashlib
from typing import Union
import logging

logger = logging.getLogger(__name__)


def get_file_md5(file_content: bytes | str) -> str:
    """Calculate MD5 hash of file content"""
    if type(file_content) is str:
        with open(file_content, "rb") as f:
            file_content = f.read()
    return hashlib.md5(file_content).hexdigest()


def to_base64(file_content: Union[bytes, str]) -> str:
    """
    将文件内容转换为base64字符串

    Args:
        file_content: 文件内容（字节数据）或文件路径

    Returns:
        str: base64编码的字符串
    """
    if isinstance(file_content, str):
        with open(file_content, "rb") as f:
            file_content = f.read()
    return base64.b64encode(file_content).decode('utf-8')


def from_base64(base64_str: str) -> bytes:
    """
    将base64字符串转换为字节数据

    Args:
        base64_str: base64编码的字符串

    Returns:
        bytes: 解码后的字节数据
    """
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    return base64.b64decode(base64_str)
