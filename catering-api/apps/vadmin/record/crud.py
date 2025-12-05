#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2021/10/18 22:18
# @File           : crud.py
# @IDE            : PyCharm
# @desc           : 数据库 增删改查操作

import random
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
from core.crud import DalBase


class SMSSendRecordDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(SMSSendRecordDal, self).__init__()
        self.db = db
        self.model = models.VadminSMSSendRecord
        self.schema = schemas.SMSSendRecordSimpleOut


class OperationRecordDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(OperationRecordDal, self).__init__()
        self.db = db
        self.model = models.VadminOperationRecord
        self.schema = schemas.OperationRecordSimpleOut
