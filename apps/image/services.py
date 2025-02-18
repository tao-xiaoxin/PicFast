"""
服务文件: 处理业务逻辑
Created by: tao-xiaoxin
Created time: 2025-02-14 06:06:29
"""

from typing import Dict, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from apps.image.crud import ImageCRUD
from apps.image.schemas import ImageCreate
from core.conf import settings
from utils.qiniu_manager import qiniu
from utils.file_processors import get_file_md5, get_file_extension, get_file_size_mb
from utils.log import log


class ImageService:
    """图片服务类"""

    @staticmethod
    async def upload_image(
            file: UploadFile,
            db: AsyncSession
    ) -> Dict[str, str]:
        """
        上传图片并返回访问信息

        包含文件上传到七牛云和数据库记录的创建/更新

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

            if not storage_path:
                raise ValueError("upload Failed ！")

            try:
                # 创建数据库记录
                image_data = ImageCreate(
                    key=file_key,
                    original_name=file.filename,
                    size=file_size,
                    mime_type=file_extension,
                    storage_path=storage_path,
                    view_count=0  # 创建时默认为0
                )

                # # 创建或更新数据库记录
                db_image = await ImageCRUD.create_or_update_by_key(
                    db,
                    image_data,
                    increment_view=False
                )

                if not db_image:
                    raise ValueError("Failed to create database record")

                return {
                    "success": True,
                    "key": file_key,
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
    ) -> Optional[Dict[str, any]]:
        """
        获取图片信息和内容

        Args:
            md5_key: 图片的MD5值
            db: 数据库会话

        Returns:
            Optional[Dict[str, any]]: 图片信息和内容

        Raises:
            HTTPException: 当图片不存在或获取失败时抛出异常
        """
        try:
            # 从数据库获取图片记录
            db_image = await ImageCRUD.get_image_by_key(db, md5_key)

            if not db_image:
                raise HTTPException(
                    status_code=404,
                    detail="Image not found"
                )

            # 更新浏览次数
            db_image.view_count += 1
            await db.commit()

            # 从七牛云获取图片内容
            content = qiniu_manager.get_file_bytes(db_image.storage_path)

            if not content:
                raise HTTPException(
                    status_code=404,
                    detail="Image content not found"
                )

            return {
                "content": content,
                "mime_type": db_image.mime_type,
                "size": db_image.size,
                "original_name": db_image.original_name,
                "view_count": db_image.view_count,
                "created_at": db_image.created_at,
                "updated_at": db_image.updated_at
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
    async def delete_image(
            md5_key: str,
            db: AsyncSession
    ) -> bool:
        """
        删除图片及其记录

        同时删除七牛云存储的文件和数据库记录

        Args:
            md5_key: 图片的MD5值
            db: 数据库会话

        Returns:
            bool: 删除是否成功

        Raises:
            HTTPException: 当删除操作失败时抛出异常
        """
        try:
            # 获取图片记录
            db_image = await ImageCRUD.get_image_by_key(db, md5_key)

            if not db_image:
                raise HTTPException(
                    status_code=404,
                    detail="Image not found"
                )

            # 删除七牛云文件
            qiniu_manager.delete_file(db_image.storage_path)

            # 删除数据库记录
            success = await ImageCRUD.delete_image(db, db_image.id)

            if not success:
                raise ValueError("Failed to delete database record")

            return True

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Failed to delete image: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error while deleting image"
            )
