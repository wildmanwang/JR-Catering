#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:36
# @File           : dish_combo_detail.py
# @IDE            : PyCharm
# @desc           : 菜品套餐详情

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class DishComboDetailParams(QueryParams):
    def __init__(self, params: Paging = Depends()):
        super().__init__(params)
