# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2021/10/24 16:44
# @File           : views.py
# @IDE            : PyCharm
# @desc           : 主要接口文件

from fastapi import APIRouter, Depends
from utils.response import SuccessResponse
from . import crud
from apps.vadmin.system.utils.current import AllUserAuth
from apps.vadmin.system.utils.validation.auth import Auth
from .params import OperationParams, SMSParams
from core.database import db_getter

app = APIRouter()


###########################################################
#    日志管理
###########################################################
@app.get("/operations", summary="获取操作日志列表")
async def get_record_operation(
        p: OperationParams = Depends(),
        db = Depends(db_getter),
        auth: Auth = Depends(AllUserAuth())
):
    datas, count = await crud.OperationRecordDal(db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.get("/sms/send/list", summary="获取短信发送列表")
async def get_sms_send_list(p: SMSParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.SMSSendRecordDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


