#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:30
# @File           : dish_branch.py
# @IDE            : PyCharm
# @desc           : 菜品店铺

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class DishBranchParams(QueryParams):
    def __init__(self, params: Paging = Depends()):
        super().__init__(params)
