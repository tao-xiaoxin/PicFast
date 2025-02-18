"""
服务文件: 处理业务逻辑
Created by: tao-xiaoxin
Created time: 2025-02-14 06:06:29
"""
import json
from typing import Dict, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from utils.qiniu_manager import qiniu
from core.engine import redis_client
from core.conf import settings
from utils.file_processors import get_file_size_mb, get_file_md5, get_file_extension
from apps.image.schemas import ImageCreate
from apps.image.crud import ImageCRUD
from utils.log import log


class ImageService:
    """图片服务类"""

    # 图片缓存配置
    CACHE_SIZE_LIMIT_MB = 3  # 缓存大小限制（MB）
    CACHE_EXPIRE_DAYS = 7  # 缓存过期时间（天）
    CACHE_KEY_PREFIX = settings.REDIS_KEY_PREFIX  # 缓存键前缀

    @staticmethod
    async def _cache_image(
            file_key: str,
            content: bytes,
            mime_type: str
    ) -> bool:
        """
        将图片缓存到Redis

        Args:
            file_key: 文件唯一标识
            content: 文件内容
            mime_type: MIME类型

        Returns:
            bool: 是否成功缓存
        """
        try:
            # 构建缓存键
            cache_key = f"{ImageService.CACHE_KEY_PREFIX}{file_key}"

            # 构建缓存数据
            cache_data = {
                "content": content.hex(),  # 将二进制转为十六进制字符串
                "mime_type": mime_type
            }

            # 使用JSON序列化
            cache_value = json.dumps(cache_data)

            # 设置缓存，过期时间为7天
            return await redis_client.set_key(
                cache_key,
                cache_value,
                expire=ImageService.CACHE_EXPIRE_DAYS * 24 * 3600
            )

        except Exception as e:
            log.error(f"Failed to cache image: {str(e)}")
            return False

    @staticmethod
    async def _get_cached_image(file_key: str) -> Optional[Dict]:
        """
        从Redis获取缓存的图片

        Args:
            file_key: 文件唯一标识

        Returns:
            Optional[Dict]: 缓存的图片数据，如果不存在返回None
        """
        try:
            cache_key = f"{ImageService.CACHE_KEY_PREFIX}{file_key}"
            cached_data = await redis_client.get_key(cache_key)

            if not cached_data:
                return None

            # 解析JSON数据
            data = json.loads(cached_data)

            # 将十六进制字符串转回二进制
            data["content"] = bytes.fromhex(data["content"])

            return data

        except Exception as e:
            log.error(f"Failed to get cached image: {str(e)}")
            return None

    @staticmethod
    async def upload_image(
            file: UploadFile,
            db: AsyncSession
    ) -> Dict[str, str]:
        """
        上传图片并返回访问信息

        包含文件上传到七牛云和数据库记录的创建/更新，
        对于小于3MB的文件会缓存到Redis

        Args:
            file: 上传的图片文件
            db: 数据库会话

        Returns:
            Dict[str, str]: 包含上传结果的字典

        Raises:
            HTTPException: 当上传失败时抛出异常
        """
        try:
            # 读取文件内容
            content = await file.read()

            # 获取文件信息
            file_size = get_file_size_mb(len(content))
            file_key = get_file_md5(content)
            file_extension = get_file_extension(file.filename)

            if not file_extension:
                raise ValueError("Invalid file type!")

            new_file_name = f"{file_key}.{file_extension}"

            # 上传到七牛云
            storage_path = qiniu.upload_bytes(content, new_file_name)
            mime_type = qiniu.get_mime_type(storage_path)

            if not storage_path:
                raise ValueError("Upload Failed!")

            try:
                # 创建数据库记录
                image_data = ImageCreate(
                    key=file_key,
                    original_name=file.filename,
                    size=file_size,
                    mime_type=mime_type,
                    storage_path=storage_path,
                    view_count=0
                )

                # 创建或更新数据库记录
                db_image = await ImageCRUD.create_or_update_by_key(
                    db,
                    image_data,
                    increment_view=False
                )

                if not db_image:
                    raise ValueError("Failed to create database record")

                # 如果文件小于3MB，缓存到Redis
                if file_size < ImageService.CACHE_SIZE_LIMIT_MB:
                    await ImageService._cache_image(file_key, content, mime_type)

                return {
                    "success": True,
                    "file_key": file_key,
                }

            except Exception as db_error:
                raise db_error

        except ValueError as ve:
            log.error(f"Validation error: {str(ve)}")
            raise HTTPException(
                status_code=400,
                detail=str(ve)
            )
        except Exception as e:
            log.error(f"Failed to upload image: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error during upload"
            )

    @staticmethod
    async def get_image(
            md5_key: str,
            db: AsyncSession
    ) -> Optional[Dict]:
        """
        获取图片信息和内容

        首先尝试从Redis缓存获取，如果没有再从存储获取

        Args:
            md5_key: 图片的MD5值
            db: 数据库会话

        Returns:
            Optional[Dict]: 图片信息和内容

        Raises:
            HTTPException: 当图片不存在或获取失败时抛出异常
        """
        try:
            # 首先尝试从缓存获取
            cached_data = await ImageService._get_cached_image(md5_key)
            if cached_data:
                # 更新访问计数
                await ImageService._update_view_count(md5_key, db)
                return cached_data

            # 从数据库获取图片记录
            db_image = await ImageCRUD.get_image_by_key(db, md5_key)

            if not db_image:
                return None

            # 更新浏览次数
            db_image.view_count += 1
            await db.commit()

            # 从存储获取内容
            success, result = qiniu.get_file_bytes(db_image.storage_path)

            if not success:
                raise HTTPException(
                    status_code=404,
                    detail="Image content not found"
                )

            # 构建返回数据
            content = result["content"]

            # 如果文件小于3MB，加入缓存
            if db_image.size < ImageService.CACHE_SIZE_LIMIT_MB:
                await ImageService._cache_image(
                    md5_key,
                    content,
                    db_image.mime_type
                )

            return {
                "content": content,
                "mime_type": db_image.mime_type,
                "original_name": db_image.original_name,
            }

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Failed to get image: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error while retrieving image"
            )

    @staticmethod
    async def _update_view_count(md5_key: str, db: AsyncSession) -> None:
        """
        更新图片访问次数

        Args:
            md5_key: 图片的MD5值
            db: 数据库会话
        """
        try:
            db_image = await ImageCRUD.get_image_by_key(db, md5_key)
            if db_image:
                db_image.view_count += 1
                await db.commit()
        except Exception as e:
            log.error(f"Failed to update view count: {str(e)}")
