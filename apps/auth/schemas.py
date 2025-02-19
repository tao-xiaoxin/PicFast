"""
认证相关的数据模型
Created by: tao-xiaoxin
Created time: 2025-02-19 09:11:38
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class AccessKeyBase(BaseModel):
    """访问密钥基础模型"""
    name: str = Field(..., min_length=1, max_length=50, description="密钥名称")
    description: Optional[str] = Field(None, max_length=200, description="密钥描述或者备注")
    expires_at: Optional[datetime] = Field(None, description="过期时间，不设置则永不过期")


class AccessKeyUpdate(AccessKeyBase):
    """更新访问密钥请求模型"""
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class AccessKeyInfo(AccessKeyBase):
    """访问密钥信息响应模型"""
    id: int = Field(..., description="密钥ID")
    access_key: str = Field(..., description="访问密钥")
    is_enabled: bool = Field(..., description="是否启用")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class AccessKeyCreate(AccessKeyBase):
    """创建访问密钥请求模型"""
    pass


class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="访问令牌过期时间(秒)")
    refresh_expires_in: int = Field(..., description="刷新令牌过期时间(秒)")


class CurrentUserModel(BaseModel):
    """当前用户模型"""

    id: int
    username: str
    email: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    roles: List[str] = []
    permissions: List[str] = []

    class Config:
        from_attributes = True
