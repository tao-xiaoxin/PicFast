# -*- coding: utf-8 -*-
"""
应用注册器
Created by: tao-xiaoxin
Created time: 2025-02-18 10:59:29
"""

import os
from fastapi import FastAPI
from core.conf import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from core.engine import mysql_manager
from core.path_conf import STATIC_DIR
from middleware.access_middleware import AccessMiddleware
from utils.exception import register_exception
from utils.log import set_customize_logfile, setup_logging
from utils.serializers import JsonResponse
from core.router import routers as main_router


@asynccontextmanager
async def register_init(app: FastAPI):
    """
    启动初始化处理器

    在应用启动时初始化必要的服务，在应用关闭时清理资源

    Args:
        app: FastAPI 应用实例
    """
    # 初始化数据库连接
    await mysql_manager.init_database()

    # 创建数据库表
    # await create_table()

    # 连接 redis
    # await redis_client.open()

    # 初始化 limiter
    # await FastAPILimiter.init(
    #     redis_client,
    #     prefix=settings.LIMITER_REDIS_PREFIX,
    #     http_callback=http_limit_callback
    # )

    yield  # 应用运行时

    # 关闭数据库连接
    await mysql_manager.close_database()

    # 关闭 redis 连接
    # await redis_client.close()


def register_app():
    """
    注册应用

    初始化 FastAPI 应用并配置所有必要的组件

    Returns:
        FastAPI: 配置完成的 FastAPI 应用实例
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.DESCRIPTION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOCS_URL,
        openapi_url=settings.OPENAPI_URL,
        default_response_class=JsonResponse,
        lifespan=register_init  # 使用异步上下文管理器管理应用生命周期
    )

    # 注册日志
    register_logger()

    # 注册静态文件
    register_static_file(app)

    # 注册中间件
    register_middleware(app)

    # 注册路由
    register_router(app)

    # 注册全局异常处理
    register_exception(app)

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
