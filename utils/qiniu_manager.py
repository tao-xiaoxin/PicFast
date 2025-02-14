import os
import time

import oss2
from typing import List, Union, Tuple
from app.core.conf import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OSSManager:
    def __init__(self, access_key_id: str = settings.OSS_ACCESS_KEY_ID,
                 access_key_secret: str = settings.OSS_ACCESS_KEY_SECRET, endpoint: str = settings.OSS_ENDPOINT,
                 bucket_name: str = settings.OSS_BUCKET, base_path: str = settings.OSS_BUSINESS_MEDIA_PATH):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
        self.base_path = base_path
        logger.info(f"OSSManager initialized for bucket: {bucket_name}")

    @staticmethod
    def _get_file_category(file_extension: str) -> str:
        """
        根据文件扩展名确定文件类别
        """
        audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a', '.aiff', '.ape', '.mid', '.midi']
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.mpeg', '.mpg', '.m4v', '.3gp',
                            '.rmvb']
        pdf_extensions = ['.pdf']
        word_extensions = ['.doc', '.docx', '.odt', '.rtf']
        txt_extensions = ['.txt', '.log', '.ini', '.csv', '.xml', '.md', '.json', '.yaml', '.yml']
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.raw', '.heic']
        spreadsheet_extensions = ['.xls', '.xlsx', '.ods', '.csv']
        presentation_extensions = ['.ppt', '.pptx', '.odp', '.key']
        compressed_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']
        executable_extensions = ['.exe', '.msi', '.app', '.dmg', '.sh', '.bat', '.cmd']

        if file_extension in audio_extensions:
            return "audio"
        elif file_extension in video_extensions:
            return "video"
        elif file_extension in pdf_extensions:
            return "documents/pdf"
        elif file_extension in word_extensions:
            return "documents/word"
        elif file_extension in txt_extensions:
            return "documents/txt"
        elif file_extension in image_extensions:
            return "images"
        elif file_extension in spreadsheet_extensions:
            return "documents/spreadsheets"
        elif file_extension in presentation_extensions:
            return "documents/presentations"
        elif file_extension in compressed_extensions:
            return "compressed"
        elif file_extension in executable_extensions:
            return "executables"
        else:
            return "other"

    def _get_full_oss_path(self, file_path: str) -> str:
        """
        获取完整的OSS文件路径，包括日期归档
        """
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1].lower()
        category = self._get_file_category(file_extension)
        date_folder = datetime.now().strftime("%Y%m%d")
        return f"{self.base_path}{category}/{date_folder}/{file_name}"

    def upload_file(self, local_file_path: str, oss_file_name: str = None) -> Tuple[bool, str]:
        """
        上传文件到OSS，自动分类和日期归档，成功后删除本地文件
        :param local_file_path: 本地文件路径
        :param oss_file_name: OSS上的文件名（可选，默认使用本地文件名）
        :return: 元组 (上传是否成功, 文件的长期访问URL)
        """
        if oss_file_name is None:
            oss_file_name = os.path.basename(local_file_path)
        full_oss_path = self._get_full_oss_path(oss_file_name)
        try:
            with open(oss2.to_unicode(local_file_path), 'rb') as file_obj:
                self.bucket.put_object(full_oss_path, file_obj)
            # 生成文件的长期访问URL
            long_term_url = self.get_file_url(full_oss_path)
            return True, long_term_url
        except Exception as e:
            logger.error(f"Failed to upload file {local_file_path}: {str(e)}")
            return False, ""

    def upload_bytes_file(self, file_bytes: bytes, oss_file_name: str) -> str:
        """
        将字节数据直接上传到OSS
        :param file_bytes: 要上传的字节数据
        :param oss_file_name: OSS上的文件名
        :return: 元组 (上传是否成功, 文件的长期访问URL)
        """
        full_oss_path = self._get_full_oss_path(oss_file_name)
        try:
            # 直接上传字节数据
            self.bucket.put_object(full_oss_path, file_bytes)

            logger.info(f"Byte data uploaded successfully as: {oss_file_name} -> {full_oss_path}")

            # 生成文件的长期访问URL
            long_term_url = self.get_file_url(full_oss_path)

            return long_term_url
        except Exception as e:
            logger.error(f"Failed to upload byte data as {oss_file_name}: {str(e)}")
            return ""

    def download_file(self, oss_file_path: str, local_file_path: str) -> bool:
        """
        从OSS下载文件
        :param oss_file_path: OSS上的文件路径
        :param local_file_path: 本地文件保存路径
        :return: 下载是否成功
        """
        try:
            self.bucket.get_object_to_file(oss_file_path, local_file_path)
            logger.info(f"File downloaded successfully: {oss_file_path} -> {local_file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download file {oss_file_path}: {str(e)}")
            return False

    def list_files(self, prefix: str = '', max_keys: int = 100) -> List[str]:
        """
        列出OSS中的文件
        :param prefix: 文件前缀
        :param max_keys: 最大返回数量
        :return: 文件名列表
        """
        try:
            files = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix, max_keys=max_keys):
                files.append(obj.key)
            return files
        except Exception as e:
            logger.error(f"Failed to list files with prefix {prefix}: {str(e)}")
            return []

    def delete_file(self, oss_file_path: str) -> bool:
        """
        删除OSS中的文件
        :param oss_file_path: OSS上的文件路径
        :return: 删除是否成功
        """
        try:
            self.bucket.delete_object(oss_file_path)
            logger.info(f"File deleted successfully: {oss_file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {oss_file_path}: {str(e)}")
            return False

    def get_file_url(self, oss_file_path: str, expires: int = 315360000) -> str:
        """
        获取文件的长期访问URL
        :param oss_file_path: OSS上的文件路径
        :param expires: URL的有效期（秒），默认为10年 (315360000秒)
        :return: 长期访问URL
        """
        try:
            url = self.bucket.sign_url('GET', oss_file_path, expires)
            logger.info(f"Generated long-term URL for {oss_file_path}")
            return url
        except Exception as e:
            logger.error(f"Failed to generate URL for {oss_file_path}: {str(e)}")
            return ""

    def upload_with_retry(self, local_file_path: str, oss_file_name: str = None, max_retries: int = 100) -> str:
        """
        尝试上传文件到OSS,失败时最多重试指定次数
        :param local_file_path: 本地文件路径
        :param oss_file_name: OSS上的文件名（可选,默认使用本地文件名）
        :param max_retries: 最大重试次数,默认100次
        :return: 成功返回URL字符串,失败返回None
        """
        attempt = 1
        while attempt <= max_retries:
            try:
                success, url = self.upload_file(local_file_path, oss_file_name)
                if success:
                    logger.info(f"File uploaded successfully on attempt {attempt}")
                    return url
                logger.warning(f"Upload failed on attempt {attempt}")
            except Exception as e:
                logger.error(f"Error on attempt {attempt}: {str(e)}")
            attempt += 1
            time.sleep(0.3)

        logger.error(f"Failed to upload file after {max_retries} attempts")
        return ""

    def get_file_bytes(self, file_url: str) -> Union[bytes, None]:
        """
        获取OSS中的文件字节数据
        :param file_url: OSS上的文件url 路径
        :return: 文件字节数据或None
        """
        try:
            return self.bucket.get_object_with_url(file_url).read()
        except Exception as e:
            logger.error(f"获取文件内容失败，文件地址：{file_url}，错误原因{str(e)}")
            return None


oss_manager = OSSManager()
