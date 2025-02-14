# -*- coding: utf-8 -*-
import os.path
from functools import lru_cache
from typing import Literal, List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.path_conf import BASE_DIR


class Settings(BaseSettings):
    """Global Settings"""
    os.environ['GRADIO_ANALYTICS_ENABLED'] = '0'

    model_config = SettingsConfigDict(env_file=f'{BASE_DIR}/.env', env_file_encoding='utf-8', extra='ignore')

    # Env Config
    ENVIRONMENT: Literal['dev', 'pro',"test"]

    # Env Token
    TOKEN_SECRET_KEY: str  # 密钥 secrets.token_urlsafe(32)

    # Env Opera Log
    OPERA_LOG_ENCRYPT_SECRET_KEY: str  # 密钥 os.urandom(32), 需使用 bytes.hex() 方法转换为 str

    # 服务器配置
    HOST: str = '0.0.0.0'
    PORT: int = 8099
    WORKERS: int = 1
    RELOAD: bool = True
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "pro")
    DEBUG: bool = False

    # FastAPI
    API_V1_STR: str = '/v1'
    PROJECT_NAME: str = "AI-Tools"
    PROJECT_VERSION: str = "0.2.1"
    DESCRIPTION: str = 'AI 能力集成平台'
    DOCS_URL: str | None = f'{API_V1_STR}/docs'
    REDOCS_URL: str | None = f'{API_V1_STR}/redocs'
    OPENAPI_URL: str | None = f'{API_V1_STR}/openapi'

    # Middleware
    MIDDLEWARE_CORS: bool = True
    MIDDLEWARE_ACCESS: bool = True

    @model_validator(mode='before')
    @classmethod
    def validate_openapi_url(cls, values):
        if values['ENVIRONMENT'] == 'pro':
            values['OPENAPI_URL'] = None
        return values

    # Static Server
    STATIC_FILES: bool = True

    # Location Parse
    LOCATION_PARSE: Literal['online', 'offline', 'false'] = 'offline'

    # Limiter
    # LIMITER_REDIS_PREFIX: str = 'limiter'

    # DateTime
    DATETIME_TIMEZONE: str = 'Asia/Shanghai'
    DATETIME_FORMAT: str = '%Y-%m-%d %H:%M:%S'

    # # Token
    # TOKEN_ALGORITHM: str = 'HS256'  # 算法
    # TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 1  # 过期时间，单位：秒
    # TOKEN_REFRESH_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7  # 刷新过期时间，单位：秒
    # TOKEN_REDIS_PREFIX: str = 'token'
    # TOKEN_REFRESH_REDIS_PREFIX: str = 'token:refresh'
    # TOKEN_EXCLUDE: list[str] = [  # JWT / RBAC 白名单
    #     f'{API_V1_STR}/auth/login',
    # ]

    # Log
    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "process:{process} | thread:{thread} | "
        "<level>{message}</level>"
    )
    LOG_STDOUT_FILENAME: str = 'access.log'
    LOG_STDERR_FILENAME: str = 'error.log'

    # AI Models Path
    models_dir: str = "/data/ai_models"
    TEXT_MODEL_PATH: str = os.path.join(models_dir, "text_models")
    IMAGE_MODEL_PATH: str = os.path.join(models_dir, "image_models")
    AUDIO_MODEL_PATH: str = os.path.join(models_dir, "audio_models")
    VIDEO_MODEL_PATH: str = os.path.join(models_dir, "video_models")

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500 MB
    ALLOWED_AUDIO_EXTENSIONS: List[str] = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
    ALLOWED_VIDEO_EXTENSIONS: List[str] = ['.mp4', '.avi', '.mov', '.wmv', '.flv']

    # 媒体文件存储路径
    if ENVIRONMENT == "dev":
        MEDIA_ROOT: str = os.path.join(BASE_DIR, "media")
    else:
        MEDIA_ROOT: str = "/gwm-tmp/ai_data/media"

    # 指定显卡设备
    DEVICE1: str = os.getenv("DEVICE1", "cuda:3")
    DEVICE2: str = os.getenv("DEVICE2", "cuda:3")
    DEVICE3: str = os.getenv("DEVICE3", "cuda:3")

    UPLOADS_DIR: str = os.path.join(MEDIA_ROOT, "uploads")
    PROCESSED_DIR: str = os.path.join(MEDIA_ROOT, "processed")

    # 上传目录
    AUDIO_UPLOADS_DIR: str = os.path.join(UPLOADS_DIR, "audio")
    VIDEO_UPLOADS_DIR: str = os.path.join(UPLOADS_DIR, "video")
    DOCUMENTS_DIR: str = os.path.join(UPLOADS_DIR, "documents")
    IMAGES_UPLOADS_DIR: str = os.path.join(UPLOADS_DIR, "images")

    # 处理后的输出目录
    AUDIO_PROCESSED_DIR: str = os.path.join(PROCESSED_DIR, "audio")
    VIDEO_PROCESSED_DIR: str = os.path.join(PROCESSED_DIR, "video")
    DOCUMENTS_PROCESSED_DIR: str = os.path.join(PROCESSED_DIR, "documents")
    IMAGES_PROCESSED_DIR: str = os.path.join(PROCESSED_DIR, "images")

    # 文件解密相关配置
    FILE_DECRYPT_APP_KEY: str = os.getenv("FILE_DECRYPT_APP_KEY", "BMBSXX1T0TXX")
    FILE_DECRYPT_APP_SECRET: str = os.getenv("FILE_DECRYPT_APP_SECRET", "f72ca82420664f589c2bee55b1680364")
    FILE_DECRYPT_API_URL: str = os.getenv("FILE_DECRYPT_API_URL", "https://gwapi.gwm.cn/rest/sec/cdg/file_decrypt")

    # OSS 配置
    OSS_ACCESS_KEY_ID: str = "2498EtVmPG3jZ2R1"
    OSS_ACCESS_KEY_SECRET: str = "KKhnSHakXosPEFVX2PgGQF91rO4DJP"
    OSS_BUCKET: str = "ailib-prod"
    OSS_ENDPOINT: str = "http://oss0c83-cn-baoding-gwmcloud-d01-a.ops.cloud.gwm.cn"
    OSS_BUSINESS_MEDIA_PATH: str = "aitools/media/"

    def create_media_dirs(self):
        """创建必要的媒体目录"""
        dirs_to_create = [
            self.MEDIA_ROOT,
            self.UPLOADS_DIR,
            self.PROCESSED_DIR,
        ]
        for dir_path in dirs_to_create:
            os.makedirs(dir_path, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """
    获取全局配置,懒加载
    :return:
    """
    return Settings()


# 创建配置实例
settings = get_settings()
settings.create_media_dirs()
