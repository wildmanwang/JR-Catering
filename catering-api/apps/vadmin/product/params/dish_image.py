#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 11:01
# @File           : dish_image.py
# @IDE            : PyCharm
# @desc           : 产品图片

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class DishImageParams(QueryParams):
    def __init__(self, params: Paging = Depends()):
        super().__init__(params)
