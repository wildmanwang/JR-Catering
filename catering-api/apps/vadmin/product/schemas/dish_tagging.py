#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 10:57
# @File           : dish_tagging.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr


class DishTagging(BaseModel):
    dish_id: int = Field(..., title="菜品")
    dish_tag_id: int = Field(..., title="标签")
    order_number: int | None = Field(None, title="排序号")


class DishTaggingSimpleOut(DishTagging):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
