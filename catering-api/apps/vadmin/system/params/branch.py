#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/26 18:32
# @File           : branch.py
# @IDE            : PyCharm
# @desc           : 店铺

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class BranchParams(QueryParams):
    def __init__(self, params: Paging = Depends()):
        super().__init__(params)
