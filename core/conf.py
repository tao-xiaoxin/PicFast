# -*- coding: utf-8 -*-
import os.path
from functools import lru_cache
from typing import Literal, Optional, List
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

    @classmethod
    def validate_openapi_url(cls, values):
        if values['ENVIRONMENT'] == 'pro':
            values['OPENAPI_URL'] = None
        return values

    # Static Server
    STATIC_FILES: bool = True

    # DateTime
    DATETIME_TIMEZONE: str = 'Asia/Shanghai'
    DATETIME_FORMAT: str = '%Y-%m-%d %H:%M:%S'

    """Redis配置"""
    # Redis连接配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", '')
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_TIMEOUT: int = int(os.getenv("REDIS_TIMEOUT", "3600"))

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

    # 数据库连接池配置
    MYSQL_POOL_SIZE: int = os.getenv("MYSQL_POOL_SIZE", 5)  # 连接池大小
    MYSQL_MAX_OVERFLOW: int = os.getenv("MYSQL_MAX_OVERFLOW", 10)  # 最大溢出连接数
    MYSQL_ECHO: bool = os.getenv("MYSQL_ECHO", False)  # 是否打印SQL语句

    # MySQL连接特性配置
    MYSQL_CHARSET: str = os.getenv("MYSQL_CHARSET", "utf8mb4")

    # Token
    TOKEN_ALGORITHM: str = 'HS256'  # 算法
    TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 1  # 过期时间，单位：秒
    TOKEN_REFRESH_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7  # 刷新过期时间，单位：秒
    TOKEN_REDIS_PREFIX: str = 'pf:token'
    TOKEN_REFRESH_REDIS_PREFIX: str = 'pf:token:refresh'

    @property
    def AUTH_EXCLUDE_PATHS(self) -> List[str]:
        """
        JWT / RBAC 白名单
        使用 property 替代可变默认值

        包含：
        1. 认证相关接口
        2. 图片获取接口

        Returns:
            List[str]: 白名单路径列表
        """
        return [
            # 认证相关
            f"{self.API_V1_STR}/auth/token",
            # 图片相关 - 使用占位符表示动态路径
            f"{self.API_V1_STR}/image/{{md5_key}}",  # 使用双大括号来转义
        ]

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

    # 媒体文件存储路径
    MEDIA_ROOT: str = os.path.join(BASE_DIR, "media")
    UPLOADS_DIR: str = os.path.join(MEDIA_ROOT, "uploads")
    PROCESSED_DIR: str = os.path.join(MEDIA_ROOT, "processed")

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
