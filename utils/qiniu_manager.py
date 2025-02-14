"""
七牛云存储管理器
Created by: tao-xiaoxin
Created time: 2025-02-14 05:16:31
https://developer.qiniu.com/kodo/1242/python
"""

import os
import time
from datetime import datetime
from typing import List, Union, Tuple
import logging
from qiniu import Auth, put_file, put_data, BucketManager
from core.conf import settings

logger = logging.getLogger(__name__)


class QiniuManager:
    def __init__(self,
                 access_key: str = settings.QINIU_ACCESS_KEY,
                 secret_key: str = settings.QINIU_SECRET_KEY,
                 bucket_name: str = settings.QINIU_BUCKET_NAME,
                 domain: str = settings.QINIU_DOMAIN,
                 base_path: str = settings.QINIU_BUSINESS_MEDIA_PATH):
        """
        初始化七牛云管理器
        :param access_key: 七牛云 AccessKey
        :param secret_key: 七牛云 SecretKey
        :param bucket_name: 存储空间名称
        :param domain: 访问域名
        :param base_path: 基础存储路径
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.domain = domain.rstrip('/')  # 确保域名结尾没有斜杠
        self.base_path = base_path
        self.auth = Auth(self.access_key, self.secret_key)
        self.bucket_manager = BucketManager(self.auth)
        logger.info(f"QiniuManager initialized for bucket: {bucket_name}")

    @staticmethod
    def _get_file_category(file_extension: str) -> str:
        """
        根据文件扩展名确定文件类别
        :param file_extension: 文件扩展名
        :return: 文件类别
        """
        audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a'}
        video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
        pdf_extensions = {'.pdf'}
        word_extensions = {'.doc', '.docx', '.odt', '.rtf'}
        txt_extensions = {'.txt', '.log', '.csv', '.xml', '.md', '.json'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}

        extension = file_extension.lower()
        if extension in audio_extensions:
            return "audio"
        elif extension in video_extensions:
            return "video"
        elif extension in pdf_extensions:
            return "documents/pdf"
        elif extension in word_extensions:
            return "documents/word"
        elif extension in txt_extensions:
            return "documents/txt"
        elif extension in image_extensions:
            return "images"
        else:
            return "other"

    def _get_full_key(self, file_path: str) -> str:
        """
        获取完整的存储键值，包括日期归档
        :param file_path: 文件路径
        :return: 完整的存储键值
        """
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1].lower()
        category = self._get_file_category(file_extension)
        date_folder = datetime.now().strftime("%Y%m%d")
        return f"{self.base_path}{category}/{date_folder}/{file_name}"

    def get_upload_token(self, key: str, expires: int = 3600) -> str:
        """
        获取上传凭证
        :param key: 文件键值
        :param expires: 凭证有效期（秒）
        :return: 上传凭证
        """
        return self.auth.upload_token(self.bucket_name, key, expires)

    def upload_file(self, local_file_path: str, qiniu_key: str = None) -> Tuple[bool, str]:
        """
        上传文件到七牛云
        :param local_file_path: 本地文件路径
        :param qiniu_key: 七牛云存储键值（可选）
        :return: (是否成功, 文件访问URL)
        """
        if qiniu_key is None:
            qiniu_key = self._get_full_key(local_file_path)

        try:
            token = self.get_upload_token(qiniu_key)
            ret, info = put_file(token, qiniu_key, local_file_path)

            if info.status_code == 200:
                file_url = f"{self.domain}/{qiniu_key}"
                logger.info(f"File uploaded successfully: {qiniu_key}")
                return True, file_url
            else:
                logger.error(f"Failed to upload file {local_file_path}: {info}")
                return False, ""
        except Exception as e:
            logger.error(f"Error uploading file {local_file_path}: {str(e)}")
            return False, ""

    def upload_bytes(self, file_bytes: bytes, qiniu_key: str) -> str:
        """
        将字节数据上传到七牛云
        :param file_bytes: 字节数据
        :param qiniu_key: 存储键值
        :return: 文件访问URL
        """
        try:
            token = self.get_upload_token(qiniu_key)
            ret, info = put_data(token, qiniu_key, file_bytes)

            if info.status_code == 200:
                file_url = f"{self.domain}/{qiniu_key}"
                logger.info(f"Bytes uploaded successfully: {qiniu_key}")
                return file_url
            else:
                logger.error(f"Failed to upload bytes: {info}")
                return ""
        except Exception as e:
            logger.error(f"Error uploading bytes: {str(e)}")
            return ""

    def delete_file(self, qiniu_key: str) -> bool:
        """
        删除七牛云上的文件
        :param qiniu_key: 存储键值
        :return: 是否删除成功
        """
        try:
            ret, info = self.bucket_manager.delete(self.bucket_name, qiniu_key)
            if info.status_code == 200:
                logger.info(f"File deleted successfully: {qiniu_key}")
                return True
            else:
                logger.error(f"Failed to delete file {qiniu_key}: {info}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {qiniu_key}: {str(e)}")
            return False

    def upload_with_retry(self, local_file_path: str, qiniu_key: str = None, max_retries: int = 3) -> str:
        """
        带重试机制的文件上传
        :param local_file_path: 本地文件路径
        :param qiniu_key: 存储键值（可选）
        :param max_retries: 最大重试次数
        :return: 文件访问URL
        """
        attempt = 1
        while attempt <= max_retries:
            try:
                success, url = self.upload_file(local_file_path, qiniu_key)
                if success:
                    logger.info(f"File uploaded successfully on attempt {attempt}")
                    return url
                logger.warning(f"Upload failed on attempt {attempt}")
            except Exception as e:
                logger.error(f"Error on attempt {attempt}: {str(e)}")

            attempt += 1
            if attempt <= max_retries:
                time.sleep(1)  # 重试前等待1秒

        logger.error(f"Failed to upload file after {max_retries} attempts")
        return ""

    def list_files(self, prefix: str = '', limit: int = 100) -> List[str]:
        """
        列出指定前缀的文件
        :param prefix: 前缀
        :param limit: 返回数量限制
        :return: 文件键值列表
        """
        try:
            marker = None
            files = []
            _, file_info = self.bucket_manager.list(self.bucket_name, prefix=prefix, limit=limit, marker=marker)
            if file_info.status_code == 200:
                for item in file_info.get('items', []):
                    files.append(item['key'])
            return files
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []


qiniu_manager = QiniuManager()
