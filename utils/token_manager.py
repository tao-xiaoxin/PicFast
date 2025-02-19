"""
Token管理器
Created by: tao-xiaoxin
Created time: 2025-02-19 09:49:25
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import BaseModel

from core.conf import settings
from core.engine import redis_client
from utils.timezone import timezone
from utils.log import log
from utils.security import hash_password, verify_password


class NewTokenPair(BaseModel):
    """新令牌对模型"""
    access_token: str
    refresh_token: str
    access_token_expires: datetime
    refresh_token_expires: datetime


class TokenManager:
    """Token管理器"""

    def __init__(self):
        """初始化Token管理器"""
        # JWT配置
        self.algorithm = settings.TOKEN_ALGORITHM
        self.access_expires = settings.TOKEN_EXPIRE_SECONDS
        self.refresh_expires = settings.TOKEN_REFRESH_EXPIRE_SECONDS

        # Bearer token认证
        self.security = HTTPBearer()

    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用哈希算法加密密码

        Args:
            password: 原始密码

        Returns:
            str: 加密后的密码
        """
        return hash_password(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码

        Args:
            plain_password: 要验证的密码
            hashed_password: 要比较的哈希密码

        Returns:
            bool: 验证是否通过
        """
        return verify_password(plain_password, hashed_password)

    async def _store_token_in_redis(
            self,
            to_encode: Dict[str, Any],
            subject: str,
            expire_seconds: int,
            multi_login: bool,
            is_refresh: bool = False
    ) -> Tuple[str, datetime]:
        """
        生成token并存储到Redis

        Args:
            to_encode: 要编码的数据
            subject: JWT的主题/用户ID
            expire_seconds: 过期秒数
            multi_login: 是否允许多端登录
            is_refresh: 是否为刷新令牌

        Returns:
            Tuple[str, datetime]: (token, 过期时间)
        """
        try:
            # 选择密钥
            secret_key = (settings.TOKEN_SECRET_KEY if is_refresh
                          else settings.TOKEN_SECRET_KEY)

            # 选择Redis前缀
            redis_prefix = (settings.TOKEN_REFRESH_REDIS_PREFIX if is_refresh
                            else settings.TOKEN_REDIS_PREFIX)

            # 生成token
            token = jwt.encode(
                to_encode,
                secret_key,
                algorithm=self.algorithm
            )

            # 处理单一登录
            if multi_login is False:
                key_prefix = f'{redis_prefix}:{subject}'
                await redis_client.delete_prefix(key_prefix)

            # 存储到Redis
            key = f'{redis_prefix}:{subject}:{token}'
            await redis_client.setex(key, expire_seconds, token)

            return token, to_encode['exp']

        except Exception as e:
            log.error(f"Failed to store token in Redis: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Could not store token"
            )

    async def create_access_token(
            self,
            subject: str,
            expires_delta: Optional[timedelta] = None,
            **extra_data
    ) -> Tuple[str, datetime]:
        """
        生成访问令牌

        Args:
            subject: JWT的主题/用户ID
            expires_delta: 增加的过期时间
            **extra_data: 额外的数据

        Returns:
            Tuple[str, datetime]: (访问令牌, 过期时间)
        """
        try:
            if expires_delta:
                expire = timezone.now + expires_delta
                expire_seconds = int(expires_delta.total_seconds())
            else:
                expire = timezone.now + timedelta(seconds=self.access_expires)
                expire_seconds = self.access_expires

            # 处理多端登录
            multi_login = extra_data.pop('multi_login', True)

            # 编码数据
            to_encode = {
                'exp': expire,
                'sub': subject,
                'type': 'access',
                **extra_data
            }

            return await self._store_token_in_redis(
                to_encode=to_encode,
                subject=subject,
                expire_seconds=expire_seconds,
                multi_login=multi_login,
                is_refresh=False
            )

        except Exception as e:
            log.error(f"Failed to create access token: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Could not create access token"
            )

    async def create_refresh_token(
            self,
            subject: str,
            expire_time: Optional[datetime] = None,
            **extra_data
    ) -> Tuple[str, datetime]:
        """
        生成刷新令牌

        Args:
            subject: JWT的主题/用户ID
            expire_time: 过期时间
            **extra_data: 额外的数据

        Returns:
            Tuple[str, datetime]: (刷新令牌, 过期时间)
        """
        try:
            if expire_time:
                expire = expire_time + timedelta(seconds=self.refresh_expires)
                expire_datetime = timezone.f_datetime(expire_time)
                current_datetime = timezone.now
                if expire_datetime < current_datetime:
                    raise HTTPException(
                        status_code=401,
                        detail="Refresh token has expired"
                    )
                expire_seconds = int((expire_datetime - current_datetime).total_seconds())
            else:
                expire = timezone.now + timedelta(seconds=self.refresh_expires)
                expire_seconds = self.refresh_expires

            # 处理多端登录
            multi_login = extra_data.pop('multi_login', True)

            # 编码数据
            to_encode = {
                'exp': expire,
                'sub': subject,
                'type': 'refresh',
                **extra_data
            }

            return await self._store_token_in_redis(
                to_encode=to_encode,
                subject=subject,
                expire_seconds=expire_seconds,
                multi_login=multi_login,
                is_refresh=True
            )

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Failed to create refresh token: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Could not create refresh token"
            )

    async def generate_token_pair(
            self,
            subject: str,
            data: Dict[str, Any],
            expire_time: Optional[datetime] = None,
    ) -> Tuple[str, str]:
        """
        生成令牌对（访问令牌和刷新令牌）

        Args:
            subject: JWT的主题（通常是access_key）
            data: 要包含在令牌中的额外数据字典
            expire_time: 过期时间（可选）

        Returns:
            Tuple[str, str]: (访问令牌, 刷新令牌)
        """
        try:
            # 生成访问令牌
            access_token, _ = await self.create_access_token(
                subject=subject,
                **data  # 解包额外数据
            )

            # 生成刷新令牌
            refresh_token, _ = await self.create_refresh_token(
                subject=subject,
                expire_time=expire_time,
                **data  # 解包额外数据
            )

            return access_token, refresh_token

        except Exception as e:
            log.error(f"Failed to generate token pair: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Could not generate token pair"
            )

    async def refresh_tokens(
            self,
            subject: str,
            token: str,
            refresh_token: str,
            **extra_data
    ) -> tuple[str, str]:
        """
        刷新令牌对

        Args:
            subject: JWT的主题/用户ID
            token: 当前访问令牌
            refresh_token: 当前刷新令牌
            **extra_data: 额外的数据

        Returns:
            NewTokenPair: 新的令牌对
        """
        # 验证刷新令牌
        redis_refresh_token = await redis_client.get(
            f'{settings.TOKEN_REFRESH_REDIS_PREFIX}:{subject}:{refresh_token}'
        )
        if not redis_refresh_token or redis_refresh_token != refresh_token:
            raise HTTPException(
                status_code=401,
                detail="Refresh token has expired"
            )

        # 生成新的令牌对
        new_tokens = await self.generate_token_pair(subject, **extra_data)

        # 删除旧的令牌
        token_key = f'{settings.TOKEN_REDIS_PREFIX}:{subject}:{token}'
        refresh_token_key = f'{settings.TOKEN_REFRESH_REDIS_PREFIX}:{subject}:{refresh_token}'
        await redis_client.delete(token_key)
        await redis_client.delete(refresh_token_key)

        return new_tokens

    def decode_token(self, token: str) -> Dict:
        """
        解码Token

        Args:
            token: JWT Token

        Returns:
            Dict: Token中的数据

        Raises:
            HTTPException: Token无效或已过期
        """
        try:
            payload = jwt.decode(
                token,
                settings.TOKEN_SECRET_KEY,
                algorithms=[self.algorithm]
            )
            subject = payload.get('sub')
            if not subject:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token"
                )
            return payload

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate token"
            )
        except Exception as e:
            log.error(f"Failed to decode token: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Could not decode token"
            )

    async def verify_token(
            self,
            token: str,
            token_type: str = "access"
    ) -> Dict:
        """
        验证Token

        Args:
            token: JWT Token
            token_type: Token类型 ("access" 或 "refresh")

        Returns:
            Dict: Token中的数据
        """
        payload = self.decode_token(token)

        # 验证Token类型
        if payload.get('type') != token_type:
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )

        # 验证Redis中的Token
        subject = payload['sub']
        redis_prefix = (settings.TOKEN_REDIS_PREFIX if token_type == "access"
                        else settings.TOKEN_REFRESH_REDIS_PREFIX)
        key = f'{redis_prefix}:{subject}:{token}'

        redis_token = await redis_client.get(key)
        if not redis_token or redis_token != token:
            raise HTTPException(
                status_code=401,
                detail="Token is invalid or expired"
            )

        return payload

    @staticmethod
    async def get_token_from_request(request: Request) -> str:
        """
        从请求头获取Token

        Args:
            request: FastAPI请求对象

        Returns:
            str: Token字符串
        """
        authorization = request.headers.get('Authorization')
        scheme, token = get_authorization_scheme_param(authorization)

        if not authorization or scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization scheme"
            )

        return token

    async def verify_request(
            self,
            request: Request,
            credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> Dict:
        """
        验证请求中的Token

        Args:
            request: FastAPI请求对象
            credentials: Bearer Token凭证

        Returns:
            Dict: Token中的数据
        """
        if request.url.path in settings.TOKEN_EXCLUDE_PATHS:
            return {}

        return await self.verify_token(credentials.credentials, "access")

    @staticmethod
    async def revoke_tokens(access_key: str) -> bool:
        """
        撤销指定 access_key 的所有令牌（包括访问令牌和刷新令牌）

        Args:
            access_key: 要撤销的 access_key

        Returns:
            bool: 撤销是否成功

        Raises:
            HTTPException: 撤销失败时抛出异常
        """
        try:
            # 使用 delete_prefix 删除所有访问令牌和刷新令牌
            await redis_client.delete_prefix(f"{settings.TOKEN_REDIS_PREFIX}:{access_key}")
            await redis_client.delete_prefix(f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{access_key}")

            return True

        except Exception as e:
            log.error(f"Failed to revoke tokens for access_key {access_key}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to revoke tokens"
            )


# 创建全局Token管理器实例
token_manager = TokenManager()
