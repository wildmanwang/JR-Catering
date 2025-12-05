#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/26 18:04
# @File           : company.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr


class Company(BaseModel):
    name_unique: str = Field(..., title="名称")
    busi_type: int = Field(1, title="0:总部;1:分公司")
    is_active: bool = Field(True, title="是否可用")


class CompanySimpleOut(Company):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
