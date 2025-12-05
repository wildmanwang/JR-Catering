#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:33
# @File           : dish_group.py
# @IDE            : PyCharm
# @desc           : 菜品分组

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class DishGroupParams(QueryParams):
    def __init__(self, params: Paging = Depends()):
        super().__init__(params)
