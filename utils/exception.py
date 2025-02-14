#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pydantic.errors import PydanticUserError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from uvicorn.protocols.http.h11_impl import STATUS_PHRASES
import logging
from app.utils.response import CustomResponseCode, StandardResponseCode
from app.utils.response import APIResponse
from app.utils.schema import (
    CUSTOM_USAGE_ERROR_MESSAGES,
    CUSTOM_VALIDATION_ERROR_MESSAGES,
)
from app.core.conf import settings
from app.utils.serializers import JsonResponse
from fastapi import HTTPException
from starlette.background import BackgroundTask


class BaseExceptionMixin(Exception):
    code: int

    def __init__(self, *, msg: str = None, data: Any = None, background: BackgroundTask | None = None):
        self.msg = msg
        self.data = data
        # The original background task: https://www.starlette.io/background/
        self.background = background


class HTTPError(HTTPException):
    def __init__(self, *, code: int, msg: Any = None, headers: dict[str, Any] | None = None):
        super().__init__(status_code=code, detail=msg, headers=headers)


class RequestError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_400

    def __init__(self, *, msg: str = 'Bad Request', data: Any = None, background: BackgroundTask | None = None):
        super().__init__(msg=msg, data=data, background=background)


class ForbiddenError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_403

    def __init__(self, *, msg: str = 'Forbidden', data: Any = None, background: BackgroundTask | None = None):
        super().__init__(msg=msg, data=data, background=background)


class NotFoundError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_404

    def __init__(self, *, msg: str = 'Not Found', data: Any = None, background: BackgroundTask | None = None):
        super().__init__(msg=msg, data=data, background=background)


class ServerError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_500

    def __init__(
            self, *, msg: str = 'Internal Server Error', data: Any = None, background: BackgroundTask | None = None
    ):
        super().__init__(msg=msg, data=data, background=background)


class GatewayError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_502

    def __init__(self, *, msg: str = 'Bad Gateway', data: Any = None, background: BackgroundTask | None = None):
        super().__init__(msg=msg, data=data, background=background)


class AuthorizationError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_401

    def __init__(self, *, msg: str = 'Permission Denied', data: Any = None, background: BackgroundTask | None = None):
        super().__init__(msg=msg, data=data, background=background)


class TokenError(HTTPError):
    code = StandardResponseCode.HTTP_401

    def __init__(self, *, msg: str = 'Not Authenticated', headers: dict[str, Any] | None = None):
        super().__init__(code=self.code, msg=msg, headers=headers or {'WWW-Authenticate': 'Bearer'})


def _get_exception_code(status_code: int):
    """
    获取返回状态码, OpenAPI, Uvicorn... 可用状态码基于 RFC 定义, 详细代码见下方链接

    `python 状态码标准支持 <https://github.com/python/cpython/blob/6e3cc72afeaee2532b4327776501eb8234ac787b/Lib/http
    /__init__.py#L7>`__

    `IANA 状态码注册表 <https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml>`__

    :param status_code:
    :return:
    """
    try:
        STATUS_PHRASES[status_code]
    except Exception:
        code = StandardResponseCode.HTTP_400
    else:
        code = status_code
    return code


async def _validation_exception_handler(request: Request, e: RequestValidationError | ValidationError):
    """
    数据验证异常处理

    :param e:
    :return:
    """
    errors = []
    for error in e.errors():
        custom_message = CUSTOM_VALIDATION_ERROR_MESSAGES.get(error['type'])
        if custom_message:
            ctx = error.get('ctx')
            if not ctx:
                error['msg'] = custom_message
            else:
                error['msg'] = custom_message.format(**ctx)
                ctx_error = ctx.get('error')
                if ctx_error:
                    error['ctx']['error'] = (
                        ctx_error.__str__().replace("'", '"') if isinstance(ctx_error, Exception) else None
                    )
        errors.append(error)
    error = errors[0]
    if error.get('type') == 'json_invalid':
        message = 'json解析失败'
    else:
        error_input = error.get('input')
        field = str(error.get('loc')[-1])
        error_msg = error.get('msg')
        message = f'{error_msg}{field}，输入：{error_input}' if settings.ENVIRONMENT == 'dev' else error_msg
    msg = f'请求参数非法: {message}'
    data = {'errors': errors} if settings.ENVIRONMENT == 'dev' else None
    content = {
        'code': StandardResponseCode.HTTP_422,
        'msg': msg,
        'data': data,
    }
    request.state.__request_validation_exception__ = content  # 用于在中间件中获取异常信息
    return JsonResponse(status_code=422, content=content)


def register_exception(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        全局HTTP异常处理

        :param request:
        :param exc:
        :return:
        """
        if settings.ENVIRONMENT == 'dev':
            content = {
                'code': exc.status_code,
                'msg': exc.detail,
                'data': None,
            }
        else:
            res = APIResponse.error(res=CustomResponseCode.HTTP_400)
            content = res.model_dump()
        request.state.__request_http_exception__ = content  # 用于在中间件中获取异常信息
        return JsonResponse(
            status_code=_get_exception_code(exc.status_code),
            content=content,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def fastapi_validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        fastapi 数据验证异常处理

        :param request:
        :param exc:
        :return:
        """
        return await _validation_exception_handler(request, exc)

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """
        pydantic 数据验证异常处理

        :param request:
        :param exc:
        :return:
        """
        return await _validation_exception_handler(request, exc)

    @app.exception_handler(PydanticUserError)
    async def pydantic_user_error_handler(request: Request, exc: PydanticUserError):
        """
        Pydantic 用户异常处理

        :param request:
        :param exc:
        :return:
        """
        return JsonResponse(
            status_code=StandardResponseCode.HTTP_500,
            content={
                'code': StandardResponseCode.HTTP_500,
                'msg': CUSTOM_USAGE_ERROR_MESSAGES.get(exc.code),
                'data': None,
            },
        )

    @app.exception_handler(AssertionError)
    async def assertion_error_handler(request: Request, exc: AssertionError):
        """
        断言错误处理

        :param request:
        :param exc:
        :return:
        """
        if settings.ENVIRONMENT == 'dev':
            content = {
                'code': StandardResponseCode.HTTP_500,
                'msg': str(''.join(exc.args) if exc.args else exc.__doc__),
                'data': None,
            }
        else:
            res = APIResponse.error(res=CustomResponseCode.HTTP_500)
            content = res.model_dump()
        return JsonResponse(
            status_code=StandardResponseCode.HTTP_500,
            content=content,
        )

    @app.exception_handler(Exception)
    async def all_exception_handler(request: Request, exc: Exception):
        """
        全局异常处理

        :param request:
        :param exc:
        :return:
        """
        if isinstance(exc, BaseExceptionMixin):
            return JsonResponse(
                status_code=_get_exception_code(exc.code),
                content={
                    'code': exc.code,
                    'msg': str(exc.msg),
                    'data': exc.data if exc.data else None,
                },
                background=exc.background,
            )
        else:
            import traceback

            logging.error(f'未知异常: {exc}')
            logging.error(traceback.format_exc())
            if settings.ENVIRONMENT == 'dev':
                content = {
                    'code': StandardResponseCode.HTTP_500,
                    'msg': str(exc),
                    'data': None,
                }
            else:
                res = APIResponse.error(res=CustomResponseCode.HTTP_500)
                content = res.model_dump()
            return JsonResponse(status_code=StandardResponseCode.HTTP_500, content=content)

    if settings.MIDDLEWARE_CORS:

        @app.exception_handler(StandardResponseCode.HTTP_500)
        async def cors_status_code_500_exception_handler(request, exc):
            """
            跨域 500 异常处理

            `Related issue <https://github.com/encode/starlette/issues/1175>`_

            :param request:
            :param exc:
            :return:
            """
            if isinstance(exc, BaseExceptionMixin):
                content = {
                    'code': exc.code,
                    'msg': exc.msg,
                    'data': exc.data,
                }
            else:
                if settings.ENVIRONMENT == 'dev':
                    content = {
                        'code': StandardResponseCode.HTTP_500,
                        'msg': str(exc),
                        'data': None,
                    }
                else:
                    res = APIResponse.error(res=CustomResponseCode.HTTP_500)
                    content = res.model_dump()
            response = JsonResponse(
                status_code=exc.code if isinstance(exc, BaseExceptionMixin) else StandardResponseCode.HTTP_500,
                content=content,
                background=exc.background if isinstance(exc, BaseExceptionMixin) else None,
            )
            origin = request.headers.get('origin')
            if origin:
                cors = CORSMiddleware(
                    app=app,
                    allow_origins=['*'],
                    allow_credentials=True,
                    allow_methods=['*'],
                    allow_headers=['*'],
                )
                response.headers.update(cors.simple_headers)
                has_cookie = 'cookie' in request.headers
                if cors.allow_all_origins and has_cookie:
                    response.headers['Access-Control-Allow-Origin'] = origin
                elif not cors.allow_all_origins and cors.is_allowed_origin(origin=origin):
                    response.headers['Access-Control-Allow-Origin'] = origin
                    response.headers.add_vary_header('Origin')
            return response
