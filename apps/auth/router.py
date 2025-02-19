"""
认证路由
Created by: tao-xiaoxin
Created time: 2025-02-19 09:40:16
"""

from fastapi import APIRouter
from apps.auth.views import (
    create_access_key,
    list_access_keys,
    issue_token,
    refresh_token,
    revoke_token,
)

# 创建认证路由器
auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"}
    }
)

# 访问密钥管理路由
auth_router.add_api_route(
    path="/keys",
    endpoint=create_access_key,
    methods=["POST"],
    summary="创建访问密钥",
    description="创建新的API访问密钥对。注意：secret_key 只会在创建时返回一次，请妥善保管。",
    response_description="返回新创建的访问密钥信息"
)

auth_router.add_api_route(
    path="/keys",
    endpoint=list_access_keys,
    methods=["GET"],
    summary="获取访问密钥列表",
    description="获取当前所有可用的访问密钥列表",
    response_description="返回访问密钥列表"
)

# Token管理路由
auth_router.add_api_route(
    path="/token",
    endpoint=issue_token,
    methods=["POST"],
    summary="签发访问令牌",
    description="使用 Access Key 和 Secret Key 获取访问令牌",
    response_description="返回访问令牌和刷新令牌"
)

auth_router.add_api_route(
    path="/token/refresh",
    endpoint=refresh_token,
    methods=["POST"],
    summary="刷新访问令牌",
    description="使用刷新令牌获取新的访问令牌",
    response_description="返回新的访问令牌和刷新令牌"
)

auth_router.add_api_route(
    path="/token/revoke",
    endpoint=revoke_token,
    methods=["POST"],
    summary="撤销访问令牌",
    description="撤销当前的访问凭证",
    response_description="返回撤销结果"
)
