#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2022/2/14 21:11 
# @File           : __init__.py.py
# @IDE            : PyCharm
# @desc           : xpath例子


from .login import VadminLoginRecord  # 保留用于登录记录写入操作日志
from .sms import VadminSMSSendRecord
from .operation import VadminOperationRecord
