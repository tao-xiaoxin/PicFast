"""
视图文件: 处理请求和响应的具体逻辑
Created by: tao-xiaoxin
Created time: 2025-02-14 06:25:20
"""
import os

from fastapi import APIRouter, File, UploadFile, Request

from core.conf import settings
from core.engine import CurrentSession
from apps.image.services import ImageService
from utils.responses import APIResponse, ResponseModel
from apps.image.schemas import ImageResponse
from fastapi.responses import FileResponse, Response


async def upload_image(
        request: Request,
        db: CurrentSession,  # 使用 CurrentSession 类型注解
        file: UploadFile = File(..., description="要上传的图片文件"),
) -> ResponseModel:
    """
    处理图片上传

    上传图片并返回图片访问URL和MD5值

    Args:
        request: FastAPI请求对象
        db : 数据库连接对象
        file: 要上传的图片文件

    Returns:
        ResponseModel: 标准响应对象，包含图片访问信息

    Raises:
        HTTPException: 上传失败时抛出异常
    """

    try:
        result = await ImageService.upload_image(file, db)

        if result["success"]:
            return APIResponse.success(
                data=ImageResponse(**result),
            )

        return APIResponse.error(
            msg="Upload failed！",
            code=400
        )

    except Exception as e:
        return APIResponse.error(
            msg=f"Upload failed: {str(e)}",
            code=500
        )


async def get_image(
        request: Request,
        db: CurrentSession,
        md5_key: str
):
    """
    获取图片

    通过MD5值直接返回图片文件

    Args:
        request: FastAPI请求对象
        db: 数据库连接对象
        md5_key: 图片的MD5值

    Returns:
        FileResponse: 直接返回图片文件
        APIResponse: 出错时返回错误信息
    """
    try:
        # 获取图片信息
        image_data = await ImageService.get_image(md5_key, db)

        if not image_data:
            return APIResponse.error(
                msg="not found！",
                code=404,
                status_code=404
            )
        # 使用七牛云内容返回
        return Response(
            content=image_data["content"],
            media_type=image_data["mime_type"],
            headers={
                "Content-Disposition": f'inline; filename="{image_data["original_name"]}"'
            }
        )

        # return APIResponse.success()
        # # 构建完整的文件路径
        # file_path = os.path.join(settings.BASE_DIR, image_data["file_path"].lstrip("/"))
        #
        # if not os.path.exists(file_path):
        #     return APIResponse.error(
        #         msg="Image file not found",
        #         code=404
        #     )
        #
        # # 直接返回文件
        # return FileResponse(
        #     path=file_path,
        #     media_type=image_data["mime_type"],
        #     filename=image_data["original_name"]
        # )

    except Exception as e:
        return APIResponse.error(
            msg=f"Error getting image: {str(e)}",
            code=500
        )
