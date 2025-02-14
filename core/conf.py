# -*- coding: utf-8 -*-
import os.path
from functools import lru_cache
from typing import Literal, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from core.path_conf import BASE_DIR


class Settings(BaseSettings):
    """Global Settings"""

    model_config = SettingsConfigDict(env_file=f'{BASE_DIR}/.env', env_file_encoding='utf-8', extra='ignore')

    # Env Config
    ENVIRONMENT: Literal['dev', 'pro', "test"]

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
    # API版本
    API_V1_STR: str = "/api/v1"  # 注意这里添加了前导斜杠

    # 项目信息
    PROJECT_NAME: str = "PicFast"
    PROJECT_VERSION: str = "0.1.0"
    DESCRIPTION: str = "PicFast 是一款高效、快速的图片缓存服务"

    # API文档
    DOCS_URL: Optional[str] = f"{API_V1_STR}/docs"
    REDOCS_URL: Optional[str] = f"{API_V1_STR}/redocs"
    OPENAPI_URL: Optional[str] = f"{API_V1_STR}/openapi"

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

    # Limiter
    # LIMITER_REDIS_PREFIX: str = 'limiter'

    # DateTime
    DATETIME_TIMEZONE: str = 'Asia/Shanghai'
    DATETIME_FORMAT: str = '%Y-%m-%d %H:%M:%S'

    """Redis配置"""
    # Redis连接配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Redis缓存配置
    REDIS_KEY_PREFIX: str = os.getenv("REDIS_KEY_PREFIX", "picfast:")
    REDIS_DEFAULT_EXPIRE: int = int(os.getenv("REDIS_DEFAULT_EXPIRE", "86400"))  # 默认1天

    """MySQL配置"""
    # MySQL连接配置
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "picfast")

    # MySQL连接池配置
    MYSQL_POOL_SIZE: int = int(os.getenv("MYSQL_POOL_SIZE", "5"))
    MYSQL_POOL_RECYCLE: int = int(os.getenv("MYSQL_POOL_RECYCLE", "3600"))
    MYSQL_MAX_OVERFLOW: int = int(os.getenv("MYSQL_MAX_OVERFLOW", "10"))

    # MySQL连接特性配置
    MYSQL_CHARSET: str = os.getenv("MYSQL_CHARSET", "utf8mb4")

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

    # 媒体文件存储路径
    MEDIA_ROOT: str = os.path.join(BASE_DIR, "media")

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

    # 七牛云配置
    QINIU_ACCESS_KEY: str = os.getenv("QINIU_ACCESS_KEY", "")
    QINIU_SECRET_KEY: str = os.getenv("QINIU_SECRET_KEY", "")
    QINIU_BUCKET_NAME: str = os.getenv("QINIU_BUCKET_NAME", "")
    QINIU_DOMAIN: str = os.getenv("QINIU_DOMAIN", "")
    QINIU_BUSINESS_MEDIA_PATH: str = os.getenv("QINIU_BUSINESS_MEDIA_PATH", "")

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
