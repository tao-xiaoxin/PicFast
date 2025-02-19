"""
认证相关数据库操作
Created by: tao-xiaoxin
Created time: 2025-02-19 09:11:38
"""
from typing import Optional, List, Tuple, Any, Sequence
from sqlalchemy import select, and_, or_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from apps.auth.models import AccessKey
from apps.auth.schemas import AccessKeyCreate, AccessKeyUpdate
from utils.security import (
    generate_access_key,
    generate_secret_key,
    hash_secret_key,
    verify_secret_key
)
from utils.timezone import timezone
from utils.log import log


class AccessKeyCRUD:
    """访问密钥CRUD操作"""

    @staticmethod
    async def create(
            db: AsyncSession,
            data: AccessKeyCreate
    ) -> Optional[Tuple[AccessKey, str]]:
        """
        创建新的访问密钥

        Args:
            db: 数据库会话
            data: 创建数据

        Returns:
            Optional[Tuple[AccessKey, str]]: (访问密钥记录, 原始密钥)
            注意：原始密钥只在创建时返回一次，之后将无法获取
        """
        try:
            # 生成访问密钥和密钥
            access_key = generate_access_key()
            plain_secret_key = generate_secret_key()

            # 对密钥进行哈希加密
            hashed_secret_key = hash_secret_key(plain_secret_key)

            access_key_obj = AccessKey(
                name=data.name,
                description=data.description,
                access_key=access_key,
                secret_key=hashed_secret_key,  # 存储加密后的密钥
                expires_at=data.expires_at
            )

            db.add(access_key_obj)
            await db.commit()
            await db.refresh(access_key_obj)

            # 返回访问密钥记录和原始密钥
            return access_key_obj, plain_secret_key

        except Exception as e:
            await db.rollback()
            log.error(f"Failed to create access key: {str(e)}")
            return None

    @staticmethod
    async def get_by_id(
            db: AsyncSession,
            key_id: int
    ) -> Optional[AccessKey]:
        """
        通过ID获取访问密钥

        Args:
            db: 数据库会话
            key_id: 密钥ID

        Returns:
            Optional[AccessKey]: 访问密钥记录
        """
        try:
            result = await db.execute(
                select(AccessKey).where(AccessKey.id == key_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            log.error(f"Failed to get access key by ID: {str(e)}")
            return None

    @staticmethod
    async def get_by_access_key(
            db: AsyncSession,
            access_key: str
    ) -> Optional[AccessKey]:
        """
        通过access_key获取访问密钥

        Args:
            db: 数据库会话
            access_key: 访问密钥

        Returns:
            Optional[AccessKey]: 访问密钥记录
        """
        try:
            result = await db.execute(
                select(AccessKey).where(AccessKey.access_key == access_key)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            log.error(f"Failed to get access key: {str(e)}")
            return None

    @staticmethod
    async def get_active_keys(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[AccessKey] | list[Any]:
        """
        获取激活状态的访问密钥列表

        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 限制数量

        Returns:
            List[AccessKey]: 访问密钥记录列表
        """
        try:
            result = await db.execute(
                select(AccessKey)
                .where(
                    and_(
                        AccessKey.is_enabled == True,
                        or_(
                            AccessKey.expires_at == None,
                            AccessKey.expires_at > timezone.now()
                        )
                    )
                )
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()

        except Exception as e:
            log.error(f"Failed to get active access keys: {str(e)}")
            return []

    @staticmethod
    async def update(
            db: AsyncSession,
            key_id: int,
            data: AccessKeyUpdate
    ) -> Optional[AccessKey]:
        """
        更新访问密钥信息

        Args:
            db: 数据库会话
            key_id: 密钥ID
            data: 更新数据

        Returns:
            Optional[AccessKey]: 更新后的访问密钥记录
        """
        try:
            # 构建更新数据
            update_data = data.model_dump(exclude_unset=True)

            if update_data:
                await db.execute(
                    update(AccessKey)
                    .where(AccessKey.id == key_id)
                    .values(**update_data)
                )
                await db.commit()

            return await AccessKeyCRUD.get_by_id(db, key_id)

        except Exception as e:
            await db.rollback()
            log.error(f"Failed to update access key: {str(e)}")
            return None

    @staticmethod
    async def validate_credentials(
            db: AsyncSession,
            access_key: str,
            secret_key: str
    ) -> Optional[AccessKey]:
        """
        验证访问凭证

        Args:
            db: 数据库会话
            access_key: 访问密钥
            secret_key: 原始密钥

        Returns:
            Optional[AccessKey]: 验证通过返回访问密钥记录，否则返回None
        """
        try:
            result = await db.execute(
                select(AccessKey).where(
                    and_(
                        AccessKey.access_key == access_key,
                        AccessKey.is_enabled == True,
                        or_(
                            AccessKey.expires_at == None,
                            AccessKey.expires_at > timezone.now
                        )
                    )
                )
            )
            access_key_obj = result.scalar_one_or_none()

            if not access_key_obj:
                return None

            # 验证密钥
            if not verify_secret_key(secret_key, access_key_obj.secret_key):
                return None

            return access_key_obj

        except Exception as e:
            log.error(f"Failed to validate credentials: {str(e)}")
            return None

    @staticmethod
    async def update_last_used(
            db: AsyncSession,
            access_key: str
    ) -> bool:
        """
        更新访问密钥的最后使用时间

        Args:
            db: 数据库会话
            access_key: 访问密钥

        Returns:
            bool: 更新是否成功
        """
        try:
            result = await db.execute(
                update(AccessKey)
                .where(AccessKey.access_key == access_key)
                .values(last_used_at=timezone.now)
            )
            await db.commit()
            return result.rowcount > 0

        except Exception as e:
            await db.rollback()
            log.error(f"Failed to update last used time: {str(e)}")
            return False

    @staticmethod
    async def disable(
            db: AsyncSession,
            access_key: str
    ) -> bool:
        """
        禁用访问密钥

        Args:
            db: 数据库会话
            access_key: 访问密钥

        Returns:
            bool: 禁用是否成功
        """
        try:
            result = await db.execute(
                update(AccessKey)
                .where(AccessKey.access_key == access_key)
                .values(is_enabled=False)
            )
            await db.commit()
            return result.rowcount > 0

        except Exception as e:
            await db.rollback()
            log.error(f"Failed to disable access key: {str(e)}")
            return False

    @staticmethod
    async def get_access_keys(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 10,
            name: Optional[str] = None,
            is_enabled: Optional[bool] = None,
            order_by: str = "created_at",
            order: str = "desc"
    ) -> Tuple[Sequence[AccessKey], int]:
        """
        获取访问密钥列表

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            name: 密钥名称过滤
            is_enabled: 是否启用状态过滤
            order_by: 排序字段
            order: 排序方向 (asc/desc)

        Returns:
            Tuple[Sequence[AccessKey], int]: (访问密钥列表, 总记录数)
        """
        try:
            # 构建查询条件
            conditions = []
            if name:
                conditions.append(AccessKey.name.ilike(f"%{name}%"))
            if is_enabled is not None:
                conditions.append(AccessKey.is_enabled == is_enabled)

            # 构建查询语句
            query = select(AccessKey)
            if conditions:
                query = query.where(and_(*conditions))

            # 添加排序
            if order_by:
                # 获取排序字段
                sort_field = getattr(AccessKey, order_by, AccessKey.created_at)
                # 设置排序方向
                if order.lower() == "desc":
                    sort_field = sort_field.desc()
                else:
                    sort_field = sort_field.asc()
                query = query.order_by(sort_field)

            # 获取总数
            total_query = select(func.count()).select_from(query.subquery())
            total = await db.scalar(total_query) or 0

            # 添加分页
            query = query.offset(skip).limit(limit)

            # 执行查询
            result = await db.execute(query)
            keys = result.scalars().all()

            return keys, total

        except Exception as e:
            log.error(f"Failed to get access keys: {str(e)}")
            return [], 0

    @staticmethod
    async def get_access_key_by_access_key(
            db: AsyncSession,
            access_key: str
    ) -> Optional[AccessKey]:
        """
        通过access_key获取访问密钥详细信息

        Args:
            db: 数据库会话
            access_key: 访问密钥

        Returns:
            Optional[AccessKey]: 访问密钥记录，如果不存在则返回None
        """
        try:
            result = await db.execute(
                select(AccessKey)
                .where(
                    and_(
                        AccessKey.access_key == access_key,
                        AccessKey.is_enabled == True,  # 只返回启用状态的密钥
                        or_(
                            AccessKey.expires_at == None,
                            AccessKey.expires_at > timezone.now
                        )
                    )
                )
            )
            return result.scalar_one_or_none()

        except Exception as e:
            log.error(f"Failed to get access key by access_key {access_key}: {str(e)}")
            return None

    @staticmethod
    async def disable_access_key(
            db: AsyncSession,
            access_key: str
    ) -> bool:
        """
        禁用指定的访问密钥

        Args:
            db: 数据库会话
            access_key: 要禁用的访问密钥

        Returns:
            bool: 是否成功禁用访问密钥
        """
        try:
            result = await db.execute(
                update(AccessKey)
                .where(AccessKey.access_key == access_key)
                .values(
                    is_enabled=False,
                    last_used_at=timezone.now
                )
            )
            await db.commit()

            if result.rowcount > 0:
                log.success(f"Successfully disabled access key: {access_key}")
                return True
            else:
                log.warning(f"Access key not found: {access_key}")
                return False

        except Exception as e:
            await db.rollback()
            log.error(f"Failed to disable access key {access_key}: {str(e)}")
            return False
