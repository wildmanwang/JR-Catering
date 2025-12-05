#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:33
# @File           : dish_group_detail.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr, DecimalType


class DishGroupDetail(BaseModel):
    dish_group_id: int = Field(..., title="菜品组")
    dish_id: int = Field(..., title="菜品")
    additional_price: DecimalType = Field(None, title="加价")
    order_number: int | None = Field(None, title="排序号")


class DishGroupDetailSimpleOut(DishGroupDetail):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
