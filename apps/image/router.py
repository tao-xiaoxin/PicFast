"""
图片路由
Created by: tao-xiaoxin
Created time: 2025-02-17 06:04:32
"""

from fastapi import APIRouter
from apps.image.views import upload_image, get_image

# 创建图片路由器
image_router = APIRouter(
    prefix="/image",
    tags=["image"],
    responses={404: {"description": "Not found"}}
)

# 定义路由
image_router.add_api_route(
    path="/upload",
    endpoint=upload_image,
    methods=["POST"],
    summary="上传图片",
    description="上传图片文件并返回处理结果",
    response_description="上传成功返回图片信息"
)

image_router.add_api_route(
    path="/{md5_key}",
    endpoint=get_image,
    methods=["GET"],
    summary="获取图片",
    description="通过MD5键获取图片",
    response_description="返回图片文件"
)
