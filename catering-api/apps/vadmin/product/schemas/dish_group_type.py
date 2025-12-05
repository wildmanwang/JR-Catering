#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:33
# @File           : dish_group_type.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr


class DishGroupType(BaseModel):
    name_unique: str = Field(..., title="名称")
    order_number: int | None = Field(None, title="排序号")
    is_active: bool = Field(True, title="是否可用")


class DishGroupTypeSimpleOut(DishGroupType):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
