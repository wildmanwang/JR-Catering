#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 10:54
# @File           : dish_kitchen.py
# @IDE            : PyCharm
# @desc           : 厨部

from fastapi import Depends, Query
from core.dependencies import Paging, QueryParams


class DishKitchenParams(QueryParams):
    def __init__(
        self,
        is_active: bool | None = Query(None, title="是否可用"),
        params: Paging = Depends()
    ):
        super().__init__(params)
        self.is_active = is_active
