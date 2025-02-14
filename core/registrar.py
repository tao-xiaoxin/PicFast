# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI
from app.core.conf import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.path_conf import STATIC_DIR
from app.middleware.access_middleware import AccessMiddleware
from app.utils.exception import register_exception
from app.utils.log import set_customize_logfile, setup_logging
from app.utils.serializers import JsonResponse
from app.core.router import routers as main_router
from app.core.model_registrar import initialize_models


def register_app():
    """
    启动初始化
    :return:
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.DESCRIPTION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOCS_URL,
        openapi_url=settings.OPENAPI_URL,
        default_response_class=JsonResponse,
    )

    # 日志
    register_logger()

    # 静态文件
    register_static_file(app)

    # 中间件
    register_middleware(app)

    # 路由
    register_router(app)

    # 全局异常处理
    register_exception(app)

    # 初始化模型
    initialize_models()

    return app


def register_logger() -> None:
    """
    系统日志

    :return:
    """
    setup_logging()
    set_customize_logfile()


def register_static_file(app: FastAPI):
    """
    静态文件交互开发模式, 生产使用 nginx 静态资源服务

    :param app:
    :return:
    """
    if settings.STATIC_FILES:
        if not os.path.exists(STATIC_DIR):
            os.mkdir(STATIC_DIR)
        app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')
        app.mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media")


#
#
def register_middleware(app: FastAPI):
    """
    中间件，执行顺序从下往上

    :param app:
    :return:
    """
    # Access log
    if settings.MIDDLEWARE_ACCESS:
        app.add_middleware(AccessMiddleware)
    # CORS: Always at the end
    if settings.MIDDLEWARE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )


def register_router(app: FastAPI):
    """
    路由

    :param app: FastAPI
    :return:
    """

    app.include_router(main_router)
