#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:25
# @File           : dish_bom.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr


class DishBom(BaseModel):
    product_type: int = Field(..., title="类型 1/单品;2/套餐")
    product_id: int = Field(..., title="产品")
    material_type: int = Field(..., title="类型 1/食材;2/耗材")
    material_id: int = Field(..., title="物料")
    spec: str | None = Field(None, title="规格")
    unit: str | None = Field(None, title="单位")
    quantity: int = Field(..., title="数量")
    order_number: int | None = Field(None, title="排序号")


class DishBomSimpleOut(DishBom):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
