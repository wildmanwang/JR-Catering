# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2021/10/19 15:47
# @File           : exception.py
# @IDE            : PyCharm
# @desc           : 全局异常处理

from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from starlette import status
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI
from core.logger import logger
from application.settings import DEBUG


class CustomException(Exception):

    def __init__(
            self,
            msg: str,
            code: int = status.HTTP_400_BAD_REQUEST,
            status_code: int = status.HTTP_200_OK,
            desc: str = None
    ):
        self.msg = msg
        self.code = code
        self.status_code = status_code
        self.desc = desc


def register_exception(app: FastAPI):
    """
    异常捕捉
    """

    @app.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        """
        自定义异常
        """
        if DEBUG:
            print("请求地址", request.url.__str__())
            print("捕捉到重写CustomException异常异常：custom_exception_handler")
            print(exc.desc)
            print(exc.msg)
        # 打印栈信息，方便追踪排查异常
        logger.exception(exc)
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.msg, "code": exc.code},
        )

    @app.exception_handler(StarletteHTTPException)
    async def unicorn_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        重写HTTPException异常处理器
        """
        if DEBUG:
            print("请求地址", request.url.__str__())
            print("捕捉到重写HTTPException异常异常：unicorn_exception_handler")
            print(exc.detail)
        # 打印栈信息，方便追踪排查异常
        logger.exception(exc)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail,
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        重写请求验证异常处理器
        """
        if DEBUG:
            print("请求地址", request.url.__str__())
            print("捕捉到重写请求验证异常异常：validation_exception_handler")
            print(exc.errors())
        # 打印栈信息，方便追踪排查异常
        logger.exception(exc)
        msg = exc.errors()[0].get("msg")
        if msg == "field required":
            msg = "请求失败，缺少必填项！"
        elif msg == "value is not a valid list":
            print(exc.errors())
            msg = f"类型错误，提交参数应该为列表！"
        elif msg == "value is not a valid int":
            msg = f"类型错误，提交参数应该为整数！"
        elif msg == "value could not be parsed to a boolean":
            msg = f"类型错误，提交参数应该为布尔值！"
        elif msg == "Input should be a valid list":
            msg = f"类型错误，输入应该是一个有效的列表！"
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {
                    "message": msg,
                    "body": exc.body,
                    "code": status.HTTP_400_BAD_REQUEST
                }
            ),
        )

    @app.exception_handler(ValueError)
    async def value_exception_handler(request: Request, exc: ValueError):
        """
        捕获值异常
        """
        if DEBUG:
            print("请求地址", request.url.__str__())
            print("捕捉到值异常：value_exception_handler")
            print(exc.__str__())
        # 打印栈信息，方便追踪排查异常
        logger.exception(exc)
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {
                    "message": exc.__str__(),
                    "code": status.HTTP_400_BAD_REQUEST
                }
            ),
        )

    @app.exception_handler(Exception)
    async def all_exception_handler(request: Request, exc: Exception):
        """
        捕获全部未处理的异常
        
        此处理器会捕获所有未被其他异常处理器处理的异常，并返回统一的错误响应格式。
        返回实际的异常消息，方便前端显示详细的错误信息。
        
        :param request: FastAPI 请求对象
        :param exc: 捕获的异常对象
        :return: JSONResponse 包含错误信息和状态码
        """
        if DEBUG:
            print("请求地址", request.url.__str__())
            print("捕捉到全局异常：all_exception_handler")
            print(exc.__str__())
        
        # 打印栈信息，方便追踪排查异常
        logger.exception(exc)
        
        # 提取实际的异常消息，如果异常对象为空则使用默认消息
        exception_message = str(exc) if exc else "接口异常！"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(
                {
                    "message": exception_message,
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR
                }
            ),
        )
