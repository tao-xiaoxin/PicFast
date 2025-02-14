"""
视图文件: 处理请求和响应的具体逻辑
Created by: tao-xiaoxin
Created time: 2025-02-14 06:25:20
"""

from fastapi import HTTPException, UploadFile, File, Request
from utils.responses import APIResponse, ResponseModel
from apps.image.services import ImageService


async def upload_image(
        request: Request,
        file: UploadFile = File(..., description="要上传的图片文件")
) -> ResponseModel:
    """
    处理图片上传

    上传图片并返回图片访问URL和MD5值

    Args:
        request: FastAPI请求对象
        file: 要上传的图片文件

    Returns:
        ResponseModel: 标准响应对象，包含图片访问信息

    Raises:
        HTTPException: 上传失败时抛出异常
    """
    try:
        result = await ImageService.upload_image(file)
        if result.get('success'):
            return APIResponse.success(
                data={
                    'key': result['key'],
                    'url': result['url']
                },
                msg="图片上传成功"
            )
        return APIResponse.error(
            msg="图片上传失败",
            code=500
        )
    except Exception as e:
        return APIResponse.error(
            msg=f"图片上传异常：{str(e)}",
            code=500
        )


async def get_image(
        request: Request,
        md5_key: str
) -> ResponseModel:
    """
    处理图片获取

    通过MD5值获取图片内容

    Args:
        request: FastAPI请求对象
        md5_key: 图片的MD5值

    Returns:
        ResponseModel: 图片二进制内容或错误信息

    Raises:
        HTTPException: 获取失败时抛出异常
    """
    try:
        image_data = await ImageService.get_image(md5_key)
        if image_data:
            # 对于二进制文件，直接返回内容
            return APIResponse.content(
                content=image_data,
                headers={'Content-Type': 'image/jpeg'}
            )
        return APIResponse.error(
            msg="图片不存在",
            code=404
        )
    except Exception as e:
        return APIResponse.error(
            msg=f"获取图片异常：{str(e)}",
            code=500
        )
