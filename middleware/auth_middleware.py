#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证中间件
Created by: tao-xiaoxin
Created time: 2025-02-19 11:16:02
"""
from typing import Any, Coroutine

from fastapi import Request, Response, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError
from starlette.requests import HTTPConnection

from apps.auth.crud import AccessKeyCRUD
from core.conf import settings
from core.engine import mysql_manager
from utils.token_manager import token_manager as token
from utils.exception import TokenError
from utils.log import log
from utils.responses import APIResponse

get_db = mysql_manager.get_db


class _AuthenticationError(AuthenticationError):
    """自定义认证错误"""

    def __init__(
            self,
            code: int = 401,
            message: str = "Authentication failed",
            headers: dict[str, Any] | None = None
    ):
        self.code = code
        self.message = message
        self.headers = headers or {}


class AccessKeyUser:
    """访问密钥用户类"""

    def __init__(self, access_key: str, token_data: dict):
        self.access_key = access_key
        self.token_data = token_data
        self.is_authenticated = True

    @property
    def identity(self) -> str:
        return self.access_key

    @property
    def display_name(self) -> str:
        return self.token_data.get("name", self.access_key)


class AuthMiddleware(AuthenticationBackend):
    """认证中间件"""

    @staticmethod
    def auth_exception_handler(conn: HTTPConnection, exc: _AuthenticationError) -> Response:
        """
        认证异常处理器

        Args:
            conn: HTTP连接对象
            exc: 认证异常

        Returns:
            Response: JSON响应
        """
        return APIResponse.error(
            code=exc.code,
            msg=exc.message,
            headers=exc.headers
        )

    async def authenticate(self, request: Request) -> tuple[AuthCredentials, AccessKeyUser] | None:
        """
        认证处理

        Args:
            request: 请求对象

        Returns:
            tuple[AuthCredentials, AccessKeyUser] | None: 认证凭证和用户对象或None

        Raises:
            _AuthenticationError: 认证失败时抛出
        """
        # 1. 检查是否为免认证路径
        if request.url.path in settings.AUTH_EXCLUDE_PATHS:
            return None

        # 2. 对于非免认证路径，必须提供认证头
        auth_header = request.headers.get("Authorization")
        token_type = request.headers.get("X-Token-Type")
        if not auth_header:
            raise _AuthenticationError(
                code=401,
                message="Authentication required"
            )
        if not token_type:
            raise _AuthenticationError(
                code=401,
                message="Token type required"
            )

        # 3. 验证认证方案
        scheme, credentials = get_authorization_scheme_param(auth_header)
        if scheme.lower() != "bearer":
            raise _AuthenticationError(
                code=401,
                message="Invalid authentication scheme"
            )

        try:
            # 4. 验证令牌
            token_data = await token.verify_token(credentials, token_type=token_type)
            if not token_data:
                raise _AuthenticationError(
                    code=401,
                    message="Invalid token"
                )

            # 5. 获取访问密钥
            access_key = token_data.get("key")
            if not access_key:
                raise _AuthenticationError(
                    code=401,
                    message="Invalid token payload"
                )

            # 6. 验证访问密钥状态
            if not await self._verify_access_key(access_key):
                raise _AuthenticationError(
                    code=403,
                    message="Access key is disabled or expired"
                )

            # 7. 创建用户对象
            user = AccessKeyUser(
                access_key=access_key,
                token_data=token_data
            )

            return AuthCredentials(["authenticated"]), user
        except TokenError as e:
            raise _AuthenticationError(
                code=e.code,
                message=e.detail,
                headers=e.headers
            )
        except HTTPException as e:
            raise _AuthenticationError(
                message=e.detail,
                headers=e.headers
            )
        except Exception as e:
            # 处理其他未预期的异常
            log.error(f"Authentication failed: {str(e)}")
            raise _AuthenticationError(
                code=getattr(e, "code", 500),
                message=getattr(e, "message", e)
            )

    @staticmethod
    async def _verify_access_key(access_key: str) -> bool | None:
        """
        验证访问密钥状态

        Args:
            access_key: 访问密钥

        Returns:
            bool: 访问密钥是否有效
        """
        try:
            async for db in get_db():
                # 获取并验证访问密钥
                key_info = await AccessKeyCRUD.get_access_key_by_access_key(db, access_key)
                if not key_info:
                    return False

                # 更新最后使用时间
                await AccessKeyCRUD.update_last_used(db, access_key)
                return True

        except Exception as e:
            log.error(f"Access key verification failed: {str(e)}")
            return False
