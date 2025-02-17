"""
七牛云存储管理器
Created by: tao-xiaoxin
Created time: 2025-02-14 05:16:31
https://developer.qiniu.com/kodo/1242/python
"""

import os
from typing import List, Union, Tuple
import logging
from qiniu import Auth, put_file, put_data, BucketManager
from core.conf import settings
from utils.timezone import timezone

logger = logging.getLogger(__name__)


class QiniuManager:
    def __init__(self,
                 access_key: str = settings.QINIU_ACCESS_KEY,
                 secret_key: str = settings.QINIU_SECRET_KEY,
                 bucket_name: str = settings.QINIU_BUCKET_NAME,
                 domain: str = settings.QINIU_DOMAIN,
                 base_path: str = settings.QINIU_BUSINESS_MEDIA_PATH
                 ):
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

    def _get_full_key(self, file_path: str) -> str:
        """
        获取完整的存储键值，包括日期归档
        :param file_path: 文件路径
        :return: 完整的存储键值
        """
        file_name = os.path.basename(file_path)
        date_folder = timezone.now.strftime("%Y/%m")
        return f"{self.base_path}/{date_folder}/{file_name}"

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
        full_key = self._get_full_key(qiniu_key)
        try:
            token = self.get_upload_token(qiniu_key)
            ret, info = put_data(token, full_key, file_bytes)

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


qiniu_manager = QiniuManager()
