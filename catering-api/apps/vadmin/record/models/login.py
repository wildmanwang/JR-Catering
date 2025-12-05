#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2022/7/7 13:41
# @File           : login.py
# @IDE            : PyCharm
# @desc           : 登录记录模型
import json

from sqlalchemy.orm import Mapped, mapped_column

from application.settings import LOGIN_LOG_RECORD
from apps.vadmin.system.utils.validation import LoginForm, WXLoginForm
from utils.ip_manage import IPManage
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from starlette.requests import Request as StarletteRequest
from user_agents import parse
from apps.vadmin.record.models.operation import VadminOperationRecord


class VadminLoginRecord:
    """
    登录记录类（已废弃，登录日志已并入操作日志）
    保留此类仅用于兼容性，实际记录已写入操作日志表
    """

    @classmethod
    async def create_login_record(
            cls,
            db: AsyncSession,
            data: LoginForm | WXLoginForm,
            status: bool,
            req: Request | StarletteRequest,
            resp: dict,
            user_id: int | None = None,
            user_name: str | None = None
    ):
        """
        创建登录记录（写入操作日志表）
        :param db: 数据库会话
        :param data: 登录表单数据
        :param status: 是否登录成功
        :param req: 请求对象
        :param resp: 响应数据
        :param user_id: 用户ID（登录成功时提供）
        :param user_name: 用户名（登录成功时提供）
        :return:
        """
        if not LOGIN_LOG_RECORD:
            return None
        
        # 获取请求信息
        header = {}
        for k, v in req.headers.items():
            header[k] = v
        if isinstance(req, StarletteRequest):
            form = (await req.form()).multi_items()
            request_params = json.dumps({"form": form, "headers": header})
        else:
            try:
                body = json.loads((await req.body()).decode())
                request_params = json.dumps({"body": body, "headers": header})
            except:
                request_params = json.dumps({"headers": header})
        
        # 解析用户代理信息
        user_agent = parse(req.headers.get("user-agent", ""))
        system = f"{user_agent.os.family} {user_agent.os.version_string}" if user_agent.os.family else None
        browser = f"{user_agent.browser.family} {user_agent.browser.version_string}" if user_agent.browser.family else None
        
        # 获取IP地址信息
        client_ip = req.client.host if req.client else None
        
        # 确定操作内容
        operation_content = "登录" if status else "登录失败"
        
        # 构建操作日志数据
        operation_data = {
            "telephone": data.telephone if hasattr(data, 'telephone') and data.telephone else (data.code if hasattr(data, 'code') else None),
            "user_id": user_id,
            "user_name": user_name,
            "status_code": 200 if status else 401,
            "client_ip": client_ip,
            "request_method": "POST",
            "api_path": req.url.path if hasattr(req, 'url') else None,
            "request_api": str(req.url) if hasattr(req, 'url') else None,
            "system": system,
            "browser": browser,
            "summary": "用户登录",
            "route_name": "login" if hasattr(data, 'method') and data.method != "2" else "wx_login",
            "description": f"用户通过{'密码' if hasattr(data, 'method') and data.method == '0' else '短信' if hasattr(data, 'method') and data.method == '1' else '微信'}方式登录",
            "tags": ["登录"],
            "operation_content": operation_content,
            "params": request_params
        }
        
        # 写入操作日志表
        obj = VadminOperationRecord(**operation_data)
        db.add(obj)
        await db.flush()
