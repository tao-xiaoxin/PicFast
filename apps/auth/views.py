"""
认证视图
Created by: tao-xiaoxin
Created time: 2025-02-19 01:39:04
"""

from typing import List
from fastapi import Request, Header, Depends, Body
from core.engine import CurrentSession
from apps.auth.schemas import (
    AccessKeyCreate,
    AccessKeyInfo
)
from apps.auth.services import AuthService
from utils.token_manager import token_manager
from utils.responses import APIResponse, ResponseModel


async def create_access_key(
        request: Request,
        data: AccessKeyCreate,
        db: CurrentSession
) -> ResponseModel:
    """
    创建新的访问密钥

    Args:
        request: 请求对象
        data: 访问密钥创建数据
        db: 数据库会话

    Returns:
        新创建的访问密钥信息，包含一次性的 secret_key
    """
    data = await AuthService.create_access_key(db, data)
    return APIResponse.success(data=data)


async def list_access_keys(
        request: Request,
        db: CurrentSession,
) -> ResponseModel:
    """
    获取访问密钥列表

    Args:
        request: 请求对象
        db: 数据库会话

    Returns:
        访问密钥列表
    """
    data = await AuthService.list_access_keys(db)
    return APIResponse.success(data=data)


async def issue_token(
        request: Request,
        db: CurrentSession,
        x_access_key: str = Body(..., description="访问密钥", ),
        x_secret_key: str = Body(..., description="密钥", )
) -> ResponseModel:
    """
    签发访问令牌

    Args:
        request: 请求对象
        db: 数据库会话
        x_access_key: 访问密钥（从请求头获取）
        x_secret_key: 密钥（从请求头获取）

    Returns:
        TokenResponse: 包含访问令牌和刷新令牌的响应
    """
    data = await AuthService.issue_token(
        request,
        db,
        x_access_key,
        x_secret_key
    )
    return APIResponse.success(data=data)


async def refresh_token(
        request: Request,
        db: CurrentSession,
        x_refresh_token: str = Body(..., description="刷新令牌", embed=True),
) -> ResponseModel:
    """
    刷新访问令牌

    Args:
        request: 请求对象
        db: 数据库会话
        x_refresh_token: 刷新令牌

    Returns:
        TokenResponse: 包含新的访问令牌和刷新令牌的响应
    """
    data = await AuthService.refresh_credentials(
        request=request,
        db=db,
        refresh_token=x_refresh_token
    )
    return APIResponse.success(data=data)


async def revoke_token(
        request: Request,
        db: CurrentSession,
        current_key: dict = Depends(token_manager.verify_request)
) -> dict:
    """
    撤销访问令牌

    Args:
        request: 请求对象
        db: 数据库会话
        current_key: 当前访问密钥信息

    Returns:
        dict: 撤销结果
    """
    return await AuthService.revoke_credentials(
        request,
        db,
        current_key
    )


async def verify_token(
        request: Request,
        db: CurrentSession,
        current_key: dict = Depends(token_manager.verify_request)
) -> dict:
    """
    验证访问令牌

    Args:
        request: 请求对象
        db: 数据库会话
        current_key: 当前访问密钥信息

    Returns:
        dict: 令牌验证结果
    """
    return {
        "valid": True,
        "key_info": {
            "key_id": current_key.get("kid"),
            "name": current_key.get("name"),
            "access_key": current_key.get("key")
        }
    }
