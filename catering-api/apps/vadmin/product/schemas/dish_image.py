#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:01
# @File           : dish_image.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作

from pydantic import BaseModel, Field, ConfigDict
from core.data_types import DatetimeStr


class DishImage(BaseModel):
    product_type: int = Field(..., title="类型 1/单品;2/套餐")
    product_id: int = Field(..., title="产品")
    img_platform: str = Field("default", title="图片平台")
    img_url: str = Field(..., title="图片地址")
    is_first: bool = Field(..., title="是否首图")
    order_number: int | None = Field(None, title="排序号")


class DishImageSimpleOut(DishImage):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="编号")
    create_datetime: DatetimeStr = Field(..., title="创建时间")
    update_datetime: DatetimeStr = Field(..., title="更新时间")
