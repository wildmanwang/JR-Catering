#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:36
# @File           : dish_combo.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr, DecimalType
from datetime import datetime
from enum import Enum


class DishComboStatusEnum(int, Enum):
    NEW = -1
    DRAFT = 0
    UPLOADED = 1
    PUBLISHED = 2
    OUTOFSTOCK = 3
    TAKEDOWN = 9


class DishCombo(BaseModel):
    name_unique: str = Field(..., title="名称")
    name_display: str | None = Field(None, title="显示名称")
    name_english: str | None = Field(None, title="英文名称")
    dish_combo_series_id: int = Field(..., title="菜品套餐系列")
    person_number: int = Field(..., title="人数")
    price: DecimalType = Field(None, title="价格")
    cost_price: DecimalType = Field(None, title="成本价")
    time_on: datetime | None = Field(None, title="上架时间")
    time_off: datetime | None = Field(None, title="下架时间")
    order_number: int | None = Field(None, title="排序号")
    status: int = Field(..., title="0:草稿;1:已上传;2:已发布;9:已下线")
    description: str | None = Field(None, title="简介")
    description_english: str | None = Field(None, title="英文简介")


class DishComboSimpleOut(DishCombo):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
