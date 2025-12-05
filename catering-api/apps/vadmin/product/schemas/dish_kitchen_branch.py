#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 10:56
# @File           : dish_kitchen_branch.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr


class DishKitchenBranch(BaseModel):
    branch_id: int = Field(..., title="店铺")
    dish_kitchen_id: int = Field(..., title="厨部")
    order_number: int | None = Field(None, title="排序号")


class DishKitchenBranchSimpleOut(DishKitchenBranch):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
