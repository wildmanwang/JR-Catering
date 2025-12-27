#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/26 18:32
# @File           : branch.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr


class Branch(BaseModel):
    name_unique: str = Field(..., title="名称")
    company_id: int = Field(..., title="所属公司")
    web_site: str | None = Field(None, title="主页")
    is_active: bool = Field(True, title="是否可用")


class BranchSimpleOut(Branch):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
