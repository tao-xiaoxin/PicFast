"""
服务文件: 处理业务逻辑
Created by: tao-xiaoxin
Created time: 2025-02-14 06:06:29
"""

from typing import Dict, Optional
from fastapi import UploadFile
from utils.qiniu_manager import qiniu_manager
from utils.file_processors import get_file_md5


class ImageService:
    """图片服务类"""

    @staticmethod
    async def upload_image(file: UploadFile) -> Dict[str, str]:
        """
        上传图片并返回访问信息
        :param file: 上传的图片文件
        :return: 包含上传结果的字典
        """
        try:
            # 读取文件内容
            content = await file.read()

            # 计算MD5值作为key
            key = get_file_md5(content)

            # 使用七牛云管理器上传图片
            url = qiniu_manager.upload_bytes(content, f"images/{key}")

            if url:
                return {
                    "success": True,
                    "key": key,
                    "url": url
                }
            return {
                "success": False,
                "error": "Failed to upload to qiniu"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    async def get_image(md5_key: str) -> Optional[bytes]:
        """
        获取图片内容
        :param md5_key: 图片的MD5值
        :return: 图片字节数据或None
        """
        try:
            # 构建完整的文件路径
            file_key = f"images/{md5_key}"

            # 从七牛云获取图片内容
            content = qiniu_manager.get_file_bytes(file_key)
            return content
        except Exception as e:
            return None
