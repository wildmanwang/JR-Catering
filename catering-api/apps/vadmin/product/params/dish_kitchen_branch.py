#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 10:56
# @File           : dish_kitchen_branch.py
# @IDE            : PyCharm
# @desc           : 厨部店铺

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class DishKitchenBranchParams(QueryParams):
    def __init__(self, params: Paging = Depends()):
        super().__init__(params)
