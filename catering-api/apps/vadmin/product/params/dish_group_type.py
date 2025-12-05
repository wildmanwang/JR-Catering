#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:33
# @File           : dish_group_type.py
# @IDE            : PyCharm
# @desc           : 菜品分组类型

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class DishGroupTypeParams(QueryParams):
    def __init__(self, params: Paging = Depends()):
        super().__init__(params)
