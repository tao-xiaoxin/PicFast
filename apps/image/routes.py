"""
路由文件: 定义API路由
Created by: tao-xiaoxin
Created time: 2025-02-14 06:08:30
"""

from fastapi import APIRouter
from apps.image.views import upload_image, get_image

image_router = APIRouter()

# 图片上传路由
image_router.route('/image/upload', methods=['POST'])(upload_image)

# 图片获取路由
image_router.route('/image/{md5_key}', methods=['GET'])(get_image)