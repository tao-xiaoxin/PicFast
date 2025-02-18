import os
import logging
from typing import Dict, Optional, Tuple
from qiniu import Auth, put_file, put_data, BucketManager
from core.conf import settings
from utils.timezone import timezone

logger = logging.getLogger(__name__)


class QiniuManager:
    def __init__(
            self,
            access_key: str = settings.QINIU_ACCESS_KEY,
            secret_key: str = settings.QINIU_SECRET_KEY,
            bucket_name: str = settings.QINIU_BUCKET_NAME,
            domain: str = settings.QINIU_DOMAIN,
            base_path: str = settings.QINIU_BUSINESS_MEDIA_PATH
    ):
        """
        初始化七牛云管理器
        
        Args:
            access_key: 七牛云 AccessKey
            secret_key: 七牛云 SecretKey
            bucket_name: 存储空间名称
            domain: 访问域名
            base_path: 基础存储路径
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
        
        Args:
            file_path: 文件路径或文件名
            
        Returns:
            str: 完整的存储键值
        """
        file_name = os.path.basename(file_path)
        date_folder = timezone.now.strftime("%Y/%m")
        return f"{self.base_path}/{date_folder}/{file_name}"

    def get_upload_token(self, key: str, expires: int = 3600) -> str:
        """
        获取上传凭证
        
        Args:
            key: 文件键值
            expires: 凭证有效期（秒）
            
        Returns:
            str: 上传凭证
        """
        return self.auth.upload_token(self.bucket_name, key, expires)

    def upload_bytes(
            self,
            file_bytes: bytes,
            file_name: str,
            expires: int = 3600
    ) -> bool | str:
        """
        将字节数据上传到七牛云
        
        Args:
            file_bytes: 要上传的字节数据
            file_name: 文件名（用于生成存储路径）
            expires: 上传凭证的有效期（秒）
            
        Returns:
            bool| str : (是否成功, 结果信息)
                成功时返回: 存储键值
                失败时返回: False
        """
        try:
            # 生成存储键值
            qiniu_key = self._get_full_key(file_name)

            # 获取上传凭证
            token = self.get_upload_token(qiniu_key, expires)

            # 上传文件
            ret, info = put_data(token, qiniu_key, file_bytes)

            if info.status_code == 200:
                # 上传成功
                logger.info(f"File uploaded successfully: {qiniu_key}")
                return qiniu_key
            else:
                # 上传失败
                error_msg = f"Upload failed: {info.error}"
                logger.error(error_msg)
                return False

        except Exception as e:
            error_msg = f"Error uploading file: {str(e)}"
            logger.error(error_msg)
            return False

    def get_file_url(self, key: str, expires: Optional[int] = None) -> str:
        """
        获取文件访问URL
        
        Args:
            key: 文件存储键值
            expires: 链接有效期（秒），不设置则永久有效
            
        Returns:
            str: 文件访问URL
        """
        if expires:
            # 生成私有下载链接
            return self.auth.private_download_url(
                f"{self.domain}/{key}",
                expires=expires
            )
        # 生成公开访问链接
        return f"{self.domain}/{key}"


# 创建全局实例
qiniu = QiniuManager()
