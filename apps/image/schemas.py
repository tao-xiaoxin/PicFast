"""
数据模型
Created by: tao-xiaoxin
Created time: 2025-02-14 06:06:29
"""

from pydantic import BaseModel, HttpUrl

class ImageResponse(BaseModel):
    """图片上传响应模型"""
    key: str  # 图片的MD5值
    url: HttpUrl  # 图片的访问URL

class ErrorResponse(BaseModel):
    """错误响应模型"""
    detail: str