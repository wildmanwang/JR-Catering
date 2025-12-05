#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:36
# @File           : dish_combo_detail.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr


class DishComboDetail(BaseModel):
    dish_combo_id: int = Field(..., title="菜品套餐")
    dish_group_id: int = Field(..., title="菜品组")
    name_display: str | None = Field(None, title="显示名称")
    name_english: str | None = Field(None, title="英文名称")
    choose_number: int = Field(..., title="可选数量")
    order_number: int | None = Field(None, title="排序号")


class DishComboDetailSimpleOut(DishComboDetail):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
