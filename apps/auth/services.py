"""
认证服务
Created by: tao-xiaoxin
Created time: 2025-02-19 01:09:15
"""

from typing import Dict, Optional, Any, Tuple
from datetime import datetime
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from apps.auth.crud import AccessKeyCRUD
from apps.auth.models import AccessKey
from apps.auth.schemas import AccessKeyCreate
from core.engine import CurrentSession
from utils.token_manager import token_manager as token
from utils.timezone import timezone
from utils.log import log


class AuthService:
    """认证服务类"""

    @staticmethod
    async def create_access_key(
            db: AsyncSession,
            data: AccessKeyCreate
    ) -> Dict:
        """
        创建新的访问密钥

        Args:
            db: 数据库会话
            data: 创建数据

        Returns:
            Dict: 包含访问密钥信息的响应数据

        Raises:
            HTTPException: 创建失败时抛出异常
        """
        try:
            result = await AccessKeyCRUD.create(db, data)
            if not result:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create access key"
                )

            access_key_obj, plain_secret_key = result

            return {
                "name": access_key_obj.name,
                "access_key": access_key_obj.access_key,
                "secret_key": plain_secret_key,  # 只在创建时返回原始密钥
                "expires_at": timezone.format(access_key_obj.expires_at) if access_key_obj.expires_at else None,
                "created_at": timezone.format(access_key_obj.created_at) if access_key_obj.created_at else None,
                "description": access_key_obj.description
            }

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Failed to create access key: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

    @staticmethod
    async def list_access_keys(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 10,
            name: Optional[str] = None,
            is_enabled: Optional[bool] = None,
            order_by: str = "created_at",
            order: str = "desc"
    ) -> Dict[str, Any]:
        """
        获取访问密钥列表

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            name: 密钥名称过滤
            is_enabled: 是否启用状态过滤
            order_by: 排序字段 (created_at, last_used_at, expires_at)
            order: 排序方向 (asc, desc)

        Returns:
            Dict: 包含密钥列表和总数的响应数据

        Raises:
            HTTPException: 查询失败时抛出异常
        """
        try:
            # 获取密钥列表和总数
            keys, total = await AccessKeyCRUD.get_access_keys(
                db,
                skip=skip,
                limit=limit,
                name=name,
                is_enabled=is_enabled,
                order_by=order_by,
                order=order
            )

            # 格式化返回数据
            return {
                "total": total,
                "items": [
                    {
                        "id": key.id,
                        "name": key.name,
                        "access_key": key.access_key,
                        "description": key.description,
                        "is_enabled": key.is_enabled,
                        "expires_at": timezone.format(key.expires_at) if key.expires_at else None,
                        "last_used_at": timezone.format(key.last_used_at) if key.last_used_at else None,
                        "created_at": timezone.format(key.created_at) if key.created_at else None
                    }
                    for key in keys
                ]
            }

        except Exception as e:
            log.error(f"Failed to list access keys: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve access keys"
            )

    async def issue_token(
            self,
            request: Request,
            db: AsyncSession,
            access_key: str,
            secret_key: str
    ) -> Dict:
        """
        签发访问令牌

        Args:
            request: 请求对象
            db: 数据库会话
            access_key: 访问密钥
            secret_key: 密钥

        Returns:
            Dict: 包含令牌的响应数据

        Raises:
            HTTPException: 签发失败时抛出异常
        """
        try:
            # 验证访问密钥
            key_info = await AccessKeyCRUD.validate_credentials(
                db,
                access_key,
                secret_key
            )
            access_token, refresh_token = await self._validate_and_generate_tokens(key_info, db, access_key)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": token.access_expires,
                "refresh_expires_in": token.refresh_expires
            }

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Token issuance failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to issue token"
            )

    @staticmethod
    async def _validate_and_generate_tokens(
            key_info: Optional[AccessKey],
            db: CurrentSession,
            access_key: str,
    ) -> Tuple[str, str]:
        """
        验证密钥状态并生成令牌对

        Args:
            key_info: 访问密钥信息对象，可能为 None
            access_key: 访问密钥字符串

        Returns:
            Tuple[str, str]: (访问令牌, 刷新令牌)

        Raises:
            HTTPException: 当密钥不存在、过期或状态无效时抛出异常
        """
        # 1. 验证密钥是否存在
        if not key_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        # 2. 验证密钥状态
        if not key_info.is_enabled:
            raise HTTPException(
                status_code=403,
                detail="Access key is disabled"
            )

        # 3. 验证过期时间
        if key_info.expires_at and timezone.f_datetime(key_info.expires_at) < timezone.now:
            raise HTTPException(
                status_code=403,
                detail="Access key has expired"
            )

        # 4. 生成令牌数据
        token_data = {
            "kid": key_info.id,
            "name": key_info.name,
            "key": access_key
        }

        # 5. 更新最后使用时间
        await AccessKeyCRUD.update_last_used(db, access_key)

        # 6. 生成令牌对
        return await token.generate_token_pair(
            access_key,
            token_data
        )

    async def refresh_credentials(
            self,
            request: Request,
            db: AsyncSession,
            refresh_token: str,
    ) -> Dict:
        """
        刷新访问凭证

        流程：
        1. 验证刷新令牌的有效性
        2. 从令牌中获取访问密钥信息
        3. 验证访问密钥的状态
        4. 生成新的令牌对
        5. 更新最后使用时间

        Args:
            request: 请求对象
            db: 数据库会话
            refresh_token: 刷新令牌

        Returns:
            Dict: 新的令牌信息

        Raises:
            HTTPException: 刷新失败时抛出异常
        """
        try:
            # 1. 验证刷新令牌
            refresh_payload = await token.verify_token(
                refresh_token,
                token_type="refresh"
            )

            # 2. 从令牌中获取访问密钥信息
            access_key = refresh_payload.get("key")
            if not access_key:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid refresh token"
                )

            # 3. 验证访问密钥状态
            key_info = await AccessKeyCRUD.get_access_key_by_access_key(db, access_key)

            access_token, new_refresh_token = await self._validate_and_generate_tokens(key_info, db, access_key)

            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "expires_in": token.access_expires,
                "refresh_expires_in": token.refresh_expires
            }

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Credential refresh failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to refresh credentials"
            )

    @staticmethod
    async def revoke_credentials(
            request: Request,
            db: AsyncSession,
            current_key: Dict
    ) -> Dict:
        """
        撤销访问凭证

        Args:
            request: 请求对象
            db: 数据库会话
            current_key: 当前密钥信息

        Returns:
            Dict: 撤销结果
        """
        try:
            # 撤销令牌
            await token.revoke_tokens(current_key["key"])

            # 更新密钥状态
            await AccessKeyCRUD.disable_access_key(db, current_key["key"])

            return {
                "message": "Credentials successfully revoked",
                "key": current_key["key"]
            }

        except Exception as e:
            log.error(f"Credential revocation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to revoke credentials"
            )
