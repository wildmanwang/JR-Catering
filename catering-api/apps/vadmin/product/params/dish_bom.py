#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:25
# @File           : dish_bom.py
# @IDE            : PyCharm
# @desc           : 成本卡

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class DishBomParams(QueryParams):
    def __init__(self, params: Paging = Depends()):
        super().__init__(params)
