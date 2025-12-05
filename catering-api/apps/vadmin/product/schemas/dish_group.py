#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:33
# @File           : dish_group.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr
from enum import Enum


class DishGroupStatusEnum(int, Enum):
    NEW = -1
    DRAFT = 0
    UPLOADED = 1
    PUBLISHED = 2


class DishGroup(BaseModel):
    name_unique: str = Field(..., title="名称")
    name_display: str | None = Field(None, title="显示名称")
    name_english: str | None = Field(None, title="英文名称")
    dish_group_type_id: int = Field(..., title="菜品组类型")
    stype: int = Field(..., title="类型 0/可选;2/必选")
    order_number: int | None = Field(None, title="排序号")
    is_active: bool = Field(True, title="是否可用")


class DishGroupSimpleOut(DishGroup):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
