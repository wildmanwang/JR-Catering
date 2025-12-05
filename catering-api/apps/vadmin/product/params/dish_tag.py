#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 10:57
# @File           : dish_tag.py
# @IDE            : PyCharm
# @desc           : 标签

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class DishTagParams(QueryParams):
    def __init__(self, params: Paging = Depends()):
        super().__init__(params)
