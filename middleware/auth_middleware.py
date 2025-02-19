#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证中间件
Created by: tao-xiaoxin
Created time: 2025-02-19 11:16:02
"""
import re
from typing import Any
from fastapi import Request, Response
from fastapi import Request, HTTPException
from jose import JWTError
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic_core import from_json
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError
from starlette.requests import HTTPConnection

from core.conf import settings
from utils.token_manager import token_manager as jwt
from utils.log import log
from backend.app.admin.schema.user import CurrentUserIns
from backend.common.exception.errors import TokenError


from backend.database.db_mysql import async_db_session
from core.conf import settings
from core.engine import redis_client
from backend.utils.serializers import MsgSpecJSONResponse, select_as_dict

from typing import Optional, Tuple, Any
from fastapi import Request
from starlette.authentication import (
    AuthenticationBackend,
    AuthenticationError,
    AuthCredentials,
    BaseUser
)
from starlette.requests import HTTPConnection
from starlette.responses import Response
from fastapi.security.utils import get_authorization_scheme_param

from core.conf import settings
from core.engine import redis_client, async_db_session
from utils.token_manager import token_manager
from schemas.user import CurrentUserModel
from utils.json import from_json
from utils.responses import CustomJSONResponse
from utils.log import log


class _AuthenticationError(AuthenticationError):
    """重写内部认证错误类"""

    def __init__(self, *, code: int = None, msg: str = None, headers: dict[str, Any] | None = None):
        self.code = code
        self.msg = msg
        self.headers = headers


class JwtAuthMiddleware(AuthenticationBackend):
    """JWT 认证中间件"""

    @staticmethod
    def auth_exception_handler(conn: HTTPConnection, exc: _AuthenticationError) -> Response:
        """覆盖内部认证错误处理"""
        return MsgSpecJSONResponse(content={'code': exc.code, 'msg': exc.msg, 'data': None}, status_code=exc.code)

    async def authenticate(self, request: Request) -> tuple[AuthCredentials, CurrentUserIns] | None:
        token = request.headers.get('Authorization')
        if not token:
            return

        if request.url.path in settings.TOKEN_EXCLUDE:
            return

        scheme, token = get_authorization_scheme_param(token)
        if scheme.lower() != 'bearer':
            return

        try:
            sub = await jwt.jwt_authentication(token)
            cache_user = await redis_client.get(f'{settings.USER_REDIS_PREFIX}:{sub}')
            if not cache_user:
                async with async_db_session() as db:
                    current_user = await jwt.get_current_user(db, sub)
                    user = CurrentUserIns(**select_as_dict(current_user))
                    await redis_client.setex(
                        f'{settings.USER_REDIS_PREFIX}:{sub}',
                        settings.USER_REDIS_EXPIRE_SECONDS,
                        user.model_dump_json(),
                    )
            else:
                # TODO: 在恰当的时机，应替换为使用 model_validate_json
                # https://docs.pydantic.dev/latest/concepts/json/#partial-json-parsing
                user = CurrentUserIns.model_validate(from_json(cache_user, allow_partial=True))
        except TokenError as exc:
            raise _AuthenticationError(code=exc.code, msg=exc.detail, headers=exc.headers)
        except Exception as e:
            log.exception(e)
            raise _AuthenticationError(code=getattr(e, 'code', 500), msg=getattr(e, 'msg', 'Internal Server Error'))

        # 请注意，此返回使用非标准模式，所以在认证通过时，将丢失某些标准特性
        # 标准返回模式请查看：https://www.starlette.io/authentication/
        return AuthCredentials(['authenticated']), user


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""

    async def dispatch(
            self,
            request: Request,
            call_next
    ) -> Response:
        """
        处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            Response: 响应对象

        Raises:
            HTTPException: Token验证失败时抛出
        """
        try:
            # 检查是否在白名单中
            if self._is_path_whitelisted(request.url.path):
                return await call_next(request)

            # 获取并验证 Token
            token = await self._get_token(request)
            if not token:
                raise HTTPException(
                    status_code=401,
                    detail="Missing token"
                )

            # 验证 Token
            payload = await token_manager.verify_token(token)

            # 将用户信息添加到请求状态中
            request.state.user = payload

            # 继续处理请求
            return await call_next(request)

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Authentication failed"
            )

    def _is_path_whitelisted(self, path: str) -> bool:
        """
        检查路径是否在白名单中

        Args:
            path: 请求路径

        Returns:
            bool: 是否在白名单中
        """
        for pattern in settings.TOKEN_EXCLUDE:
            # 将路径模式转换为正则表达式
            regex_pattern = pattern.replace(
                "{md5_key}",
                "[a-fA-F0-9]{32}"
            )
            regex_pattern = f"^{regex_pattern}$"

            if re.match(regex_pattern, path):
                return True

        return False

    async def _get_token(self, request: Request) -> str:
        """
        从请求头获取Token

        Args:
            request: 请求对象

        Returns:
            str: Token字符串

        Raises:
            HTTPException: Token格式无效时抛出
        """
        authorization = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)

        if not authorization or scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization scheme"
            )

        return token


class CustomAuthenticationError(AuthenticationError):
    """自定义认证错误类"""

    def __init__(
            self,
            *,
            code: int = None,
            msg: str = None,
            headers: dict[str, Any] | None = None
    ):
        self.code = code or 401
        self.msg = msg or "Authentication failed"
        self.headers = headers


class JWTAuthBackend(AuthenticationBackend):
    """JWT认证后端"""

    @staticmethod
    def auth_exception_handler(
            conn: HTTPConnection,
            exc: CustomAuthenticationError
    ) -> Response:
        """
        自定义认证错误处理器

        Args:
            conn: HTTP连接
            exc: 认证错误异常

        Returns:
            Response: 自定义响应
        """
        return CustomJSONResponse(
            content={
                'code': exc.code,
                'msg': exc.msg,
                'data': None
            },
            status_code=exc.code
        )

    async def authenticate(
            self,
            request: Request
    ) -> Optional[Tuple[AuthCredentials, CurrentUserModel]]:
        """
        认证处理

        Args:
            request: 请求对象

        Returns:
            Optional[Tuple[AuthCredentials, CurrentUserModel]]:
                认证凭证和当前用户信息的元组，或None表示认证失败

        Raises:
            CustomAuthenticationError: 认证失败时抛出
        """
        try:
            # 获取认证头
            authorization = request.headers.get('Authorization')
            if not authorization:
                return None

            # 检查白名单
            if request.url.path in settings.TOKEN_EXCLUDE:
                return None

            # 验证token格式
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() != 'bearer':
                return None

            # 验证token
            try:
                payload = await token_manager.verify_token(token)
                user_id = payload.get('sub')
            except Exception as e:
                log.error(f"Token verification failed: {str(e)}")
                raise CustomAuthenticationError(
                    code=401,
                    msg="Invalid or expired token"
                )

            # 尝试从缓存获取用户信息
            cache_key = f"{settings.USER_REDIS_PREFIX}:{user_id}"
            cached_user = await redis_client.get(cache_key)

            if cached_user:
                # 从缓存恢复用户信息
                user = CurrentUserModel.model_validate(
                    from_json(cached_user, allow_partial=True)
                )
            else:
                # 从数据库获取用户信息
                async with async_db_session() as db:
                    user_data = await token_manager.get_current_user(db, user_id)
                    if not user_data:
                        raise CustomAuthenticationError(
                            code=401,
                            msg="User not found"
                        )

                    # 创建用户模型实例
                    user = CurrentUserModel.model_validate(user_data)

                    # 缓存用户信息
                    await redis_client.setex(
                        cache_key,
                        settings.USER_REDIS_EXPIRE_SECONDS,
                        user.model_dump_json()
                    )

            # 返回认证凭证和用户信息
            return AuthCredentials(['authenticated']), user

        except CustomAuthenticationError:
            raise
        except Exception as e:
            log.exception(e)
            raise CustomAuthenticationError(
                code=getattr(e, 'code', 500),
                msg=getattr(e, 'msg', 'Internal Server Error')
            )
