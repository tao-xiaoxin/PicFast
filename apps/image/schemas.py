"""
图片模型验证
Created by: tao-xiaoxin
Created time: 2025-02-17 02:01:19
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ImageCreate(BaseModel):
    """创建图片模型"""
    key: str
    original_name: Optional[str] = None
    size: float
    mime_type: str
    storage_path: str
    view_count: Optional[int] = 0


class ImageUpdate(BaseModel):
    """更新图片模型"""
    original_name: Optional[str] = None
    storage_path: Optional[str] = None
    view_count: Optional[int] = 0


class ImageResponse(BaseModel):
    """图片响应模型"""
    success: bool
    file_key: str

    class Config:
        from_attributes = True
