"""
图片CRUD操作
Created by: tao-xiaoxin
Created time: 2025-02-17 02:01:19
"""

from typing import List, Optional, Sequence
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import desc
from sqlalchemy.dialects.mysql import insert as mysql_insert
from apps.image.models import ImageModels
from apps.image.schemas import ImageCreate, ImageUpdate
from utils.log import log


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

    @staticmethod
    async def create_or_update_by_key(
            db: AsyncSession,
            image: ImageCreate,
            increment_view: bool = True
    ) -> ImageModels:
        """
        创建或更新图片记录（通过key判断）

        如果具有相同key的记录存在则更新并增加浏览次数，否则创建新记录

        Args:
            db: 数据库会话
            image: 图片创建模型
            increment_view: 是否增加浏览次数，默认为True

        Returns:
            ImageModels: 创建或更新后的图片记录

        Raises:
            Exception: 数据库操作失败时抛出异常
        """
        try:
            # 查找是否存在相同key的记录
            existing_image = await ImageCRUD.get_image_by_key(db, image.key)

            if existing_image:
                # 如果存在，更新记录
                update_data = image.model_dump(exclude={"id"})

                # 处理浏览次数
                if increment_view:
                    # 如果需要增加浏览次数，手动加1
                    update_data["view_count"] = existing_image.view_count + 1
                else:
                    # 如果不需要增加浏览次数，保持原有值
                    update_data["view_count"] = existing_image.view_count

                # 更新其他字段
                for key, value in update_data.items():
                    setattr(existing_image, key, value)

                await db.commit()
                await db.refresh(existing_image)

                log.info(
                    f"Updated image record - Key: {image.key}, "
                    f"View Count: {existing_image.view_count}"
                )

                return existing_image
            else:
                # 如果不存在，创建新记录（view_count 默认为 0）
                new_image = await ImageCRUD.create_image(db, image)

                log.info(
                    f"Created new image record - Key: {image.key}, "
                    f"View Count: {new_image.view_count}"
                )

                return new_image

        except Exception as e:
            await db.rollback()
            log.error(f"Failed to create or update image: {str(e)}")
            raise

    @staticmethod
    async def upsert_image(
            db: AsyncSession,
            image: ImageCreate
    ) -> ImageModels:
        """
        创建或更新图片记录（使用MySQL的INSERT ... ON DUPLICATE KEY UPDATE）

        使用单个查询执行创建或更新操作，性能更好

        Args:
            db: 数据库会话
            image: 图片创建模型

        Returns:
            ImageModels: 创建或更新后的图片记录
        """
        try:
            # 准备插入或更新的数据
            insert_data = image.model_dump(exclude={"id"})

            # 构建 INSERT ... ON DUPLICATE KEY UPDATE 语句
            stmt = mysql_insert(ImageModels).values(insert_data)

            # 指定在发生冲突时要更新的字段
            update_dict = {
                k: v for k, v in insert_data.items()
                if k != "key"  # 不更新key字段
            }

            # 添加自动更新的字段
            update_dict["updated_at"] = ImageModels.updated_at

            # 执行upsert操作
            stmt = stmt.on_duplicate_key_update(**update_dict)
            result = await db.execute(stmt)
            await db.commit()

            # 获取创建或更新后的记录
            image_id = result.lastrowid
            return await ImageCRUD.get_image_by_id(db, image_id)

        except Exception as e:
            await db.rollback()
            log.error(f"Failed to upsert image: {str(e)}")
            raise

    @staticmethod
    async def bulk_create_or_update(
            db: AsyncSession,
            images: List[ImageCreate]
    ) -> List[ImageModels]:
        """
        批量创建或更新图片记录

        Args:
            db: 数据库会话
            images: 图片创建模型列表

        Returns:
            List[ImageModels]: 创建或更新后的图片记录列表
        """
        try:
            result_images = []

            # 获取所有的key
            keys = [image.key for image in images]

            # 查询已存在的记录
            query = select(ImageModels).where(ImageModels.key.in_(keys))
            result = await db.execute(query)
            existing_images = {img.key: img for img in result.scalars().all()}

            for image in images:
                if image.key in existing_images:
                    # 更新已存在的记录
                    existing_image = existing_images[image.key]
                    update_data = image.model_dump(exclude={"id"})
                    for key, value in update_data.items():
                        setattr(existing_image, key, value)
                    result_images.append(existing_image)
                else:
                    # 创建新记录
                    new_image = ImageModels(**image.model_dump())
                    db.add(new_image)
                    result_images.append(new_image)

            await db.commit()

            # 刷新所有记录以获取数据库生成的值
            for image in result_images:
                await db.refresh(image)

            return result_images

        except Exception as e:
            await db.rollback()
            log.error(f"Failed to bulk create or update images: {str(e)}")
            raise
