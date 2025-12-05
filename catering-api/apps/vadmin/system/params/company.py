#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/26 18:04
# @File           : company.py
# @IDE            : PyCharm
# @desc           : 公司

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class CompanyParams(QueryParams):
    def __init__(self, params: Paging = Depends()):
        super().__init__(params)
