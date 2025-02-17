"""
图片CRUD操作
Created by: tao-xiaoxin
Created time: 2025-02-17 02:01:19
"""

from typing import List, Optional, Sequence
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import desc
from apps.image.models import ImageModels
from apps.image.schemas import ImageCreate, ImageUpdate


class ImageCRUD:
    """图片CRUD操作类"""

    @staticmethod
    async def create_image(db: AsyncSession, image: ImageCreate) -> ImageModels:
        """
        创建图片记录

        Args:
            db: 数据库会话
            image: 图片创建模型

        Returns:
            ImageModels: 创建的图片记录
        """
        db_image = ImageModels(**image.model_dump())
        db.add(db_image)
        await db.commit()
        await db.refresh(db_image)
        return db_image

    @staticmethod
    async def get_image_by_id(db: AsyncSession, image_id: int) -> Optional[ImageModels]:
        """
        根据ID获取图片

        Args:
            db: 数据库会话
            image_id: 图片ID

        Returns:
            Optional[ImageModels]: 图片记录
        """
        query = select(ImageModels).where(ImageModels.id == image_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_image_by_key(db: AsyncSession, key: str) -> Optional[ImageModels]:
        """
        根据key获取图片

        Args:
            db: 数据库会话
            key: 图片唯一标识

        Returns:
            Optional[ImageModels]: 图片记录
        """
        query = select(ImageModels).where(ImageModels.key == key)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_images(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[ImageModels]:
        """
        获取图片列表

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            List[ImageModels]: 图片记录列表
        """
        query = select(ImageModels).offset(skip).limit(limit).order_by(desc(ImageModels.created_at))
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_image(
            db: AsyncSession,
            image_id: int,
            image_update: ImageUpdate
    ) -> Optional[ImageModels]:
        """
        更新图片记录

        Args:
            db: 数据库会话
            image_id: 图片ID
            image_update: 更新数据

        Returns:
            Optional[ImageModels]: 更新后的图片记录
        """
        update_data = image_update.model_dump(exclude_unset=True)
        if not update_data:
            return None

        query = update(ImageModels).where(
            ImageModels.id == image_id
        ).values(**update_data).returning(ImageModels)

        result = await db.execute(query)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_image(db: AsyncSession, image_id: int) -> bool:
        """
        删除图片记录

        Args:
            db: 数据库会话
            image_id: 图片ID

        Returns:
            bool: 是否删除成功
        """
        image = await ImageCRUD.get_image_by_id(db, image_id)
        if not image:
            return False

        await db.delete(image)
        await db.commit()
        return True