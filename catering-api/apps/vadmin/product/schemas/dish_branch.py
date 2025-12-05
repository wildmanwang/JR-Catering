#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:30
# @File           : dish_branch.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr, DecimalType


class DishBranch(BaseModel):
    dish_id: int = Field(..., title="菜品")
    branch_id: int = Field(..., title="店铺")
    name_display: str | None = Field(None, title="显示名称")
    name_english: str | None = Field(None, title="英文名称")
    price: DecimalType = Field(None, title="价格")
    cost_price: DecimalType = Field(None, title="成本价")
    order_number: int | None = Field(None, title="排序号")
    status: int = Field(..., title="0:草稿;1:已上传;2:已发布;3:库存不足;9:已下线")
    description: str | None = Field(None, title="简介")
    description_english: str | None = Field(None, title="英文简介")


class DishBranchSimpleOut(DishBranch):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
