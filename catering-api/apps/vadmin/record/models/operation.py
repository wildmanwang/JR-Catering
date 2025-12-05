#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2021/10/18 22:19
# @File           : operation.py
# @IDE            : PyCharm
# @desc           : 操作记录模型

from sqlalchemy.orm import Mapped, mapped_column
from db.db_base import BaseModel
from sqlalchemy import String, Integer, Float, Text, JSON


class VadminOperationRecord(BaseModel):
    __tablename__ = "vadmin_record_operation"
    __table_args__ = ({'comment': '操作记录表'})

    telephone: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True, comment="手机号")
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True, comment="用户ID")
    user_name: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="用户名")
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="状态码")
    client_ip: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="客户端IP")
    request_method: Mapped[str | None] = mapped_column(String(10), index=True, nullable=True, comment="请求方法")
    api_path: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="API路径")
    request_api: Mapped[str | None] = mapped_column(Text, nullable=True, comment="完整请求API")
    system: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="操作系统")
    browser: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="浏览器")
    summary: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="接口摘要")
    route_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="路由名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="接口描述")
    tags: Mapped[str | None] = mapped_column(JSON, nullable=True, comment="标签列表")
    operation_content: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="操作内容")
    process_time: Mapped[float | None] = mapped_column(Float, nullable=True, comment="处理时间(秒)")
    content_length: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="响应内容长度")
    params: Mapped[str | None] = mapped_column(Text, nullable=True, comment="请求参数(JSON字符串)")

