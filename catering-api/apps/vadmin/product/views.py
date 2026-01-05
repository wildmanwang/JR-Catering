#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 10:54
# @File           : views.py
# @IDE            : PyCharm
# @desc           : 路由，视图文件
from apps.vadmin.system.utils.current import FullAdminAuth, AllUserAuth
from fastapi import Depends, APIRouter
from apps.vadmin.system.utils.validation.auth import Auth
from . import crud, models, params, schemas
from core.dependencies import IdList
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import db_getter
from utils.response import SuccessResponse



app = APIRouter()


###########################################################
#    厨部
###########################################################
@app.get("/kitchen", summary="获取厨部列表", tags=["厨部"])
async def get_dish_kitchen_list(p: params.DishKitchenParams = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dishkitchen.list"]))):
    datas, count = await crud.DishKitchenDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/kitchen", summary="创建厨部", tags=["厨部"])
async def create_dish_kitchen(data: schemas.DishKitchen, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishkitchen.create"]))):
    return SuccessResponse(await crud.DishKitchenDal(auth.db).create_data(data=data))


@app.delete("/kitchen", summary="删除厨部", description="硬删除", tags=["厨部"])
async def delete_dish_kitchen_list(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dishkitchen.delete"]))):
    await crud.DishKitchenDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/kitchen/{data_id}", summary="更新厨部", tags=["厨部"])
async def put_dish_kitchen(data_id: int, data: schemas.DishKitchen, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishkitchen.update"]))):
    return SuccessResponse(await crud.DishKitchenDal(auth.db).put_data(data_id, data))


@app.get("/kitchen/{data_id}", summary="获取厨部信息", tags=["厨部"])
async def get_dish_kitchen(data_id: int, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishkitchen.view"]))):
    schema = schemas.DishKitchenSimpleOut
    return SuccessResponse(await crud.DishKitchenDal(auth.db).get_data(data_id, v_schema=schema))




###########################################################
#    厨部店铺
###########################################################
@app.get("/kitchenbranch", summary="获取店铺厨部列表", tags=["店铺厨部"])
async def get_dish_kitchen_branch_list(p: params.DishKitchenBranchParams = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dishkitchenbranch.list"]))):
    datas, count = await crud.DishKitchenBranchDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/kitchenbranch", summary="创建店铺厨部", tags=["店铺厨部"])
async def create_dish_kitchen_branch(data: schemas.DishKitchenBranch, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishkitchenbranch.create"]))):
    return SuccessResponse(await crud.DishKitchenBranchDal(auth.db).create_data(data=data))


@app.delete("/kitchenbranch", summary="删除店铺厨部", description="硬删除", tags=["店铺厨部"])
async def delete_dish_kitchen_branch_list(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dishkitchenbranch.delete"]))):
    await crud.DishKitchenBranchDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/kitchenbranch/{data_id}", summary="更新店铺厨部", tags=["店铺厨部"])
async def put_dish_kitchen_branch(data_id: int, data: schemas.DishKitchenBranch, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishkitchenbranch.update"]))):
    return SuccessResponse(await crud.DishKitchenBranchDal(auth.db).put_data(data_id, data))


@app.get("/kitchenbranch/{data_id}", summary="获取店铺厨部信息", tags=["店铺厨部"])
async def get_dish_kitchen_branch(data_id: int, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishkitchenbranch.view"]))):
    schema = schemas.DishKitchenBranchSimpleOut
    return SuccessResponse(await crud.DishKitchenBranchDal(auth.db).get_data(data_id, v_schema=schema))




###########################################################
#    标签
###########################################################
@app.get("/tag", summary="获取标签列表", tags=["标签"])
async def get_dish_tag_list(p: params.DishTagParams = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dishtag.list"]))):
    datas, count = await crud.DishTagDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/tag", summary="创建标签", tags=["标签"])
async def create_dish_tag(data: schemas.DishTag, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishtag.create"]))):
    return SuccessResponse(await crud.DishTagDal(auth.db).create_data(data=data))


@app.delete("/tag", summary="删除标签", description="硬删除", tags=["标签"])
async def delete_dish_tag_list(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dishtag.delete"]))):
    await crud.DishTagDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/tag/{data_id}", summary="更新标签", tags=["标签"])
async def put_dish_tag(data_id: int, data: schemas.DishTag, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishtag.update"]))):
    return SuccessResponse(await crud.DishTagDal(auth.db).put_data(data_id, data))


@app.get("/tag/{data_id}", summary="获取标签信息", tags=["标签"])
async def get_dish_tag(data_id: int, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishtag.view"]))):
    schema = schemas.DishTagSimpleOut
    return SuccessResponse(await crud.DishTagDal(auth.db).get_data(data_id, v_schema=schema))




###########################################################
#    菜品标签
###########################################################
@app.get("/tagging", summary="获取菜品标签列表", tags=["菜品标签"])
async def get_dish_tagging_list(p: params.DishTaggingParams = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dishtagging.list"]))):
    datas, count = await crud.DishTaggingDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/tagging", summary="创建菜品标签", tags=["菜品标签"])
async def create_dish_tagging(data: schemas.DishTagging, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishtagging.create"]))):
    return SuccessResponse(await crud.DishTaggingDal(auth.db).create_data(data=data))


@app.delete("/tagging", summary="删除菜品标签", description="硬删除", tags=["菜品标签"])
async def delete_dish_tagging_list(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dishtagging.delete"]))):
    await crud.DishTaggingDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/tagging/{data_id}", summary="更新菜品标签", tags=["菜品标签"])
async def put_dish_tagging(data_id: int, data: schemas.DishTagging, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishtagging.update"]))):
    return SuccessResponse(await crud.DishTaggingDal(auth.db).put_data(data_id, data))


@app.get("/tagging/{data_id}", summary="获取菜品标签信息", tags=["菜品标签"])
async def get_dish_tagging(data_id: int, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishtagging.view"]))):
    schema = schemas.DishTaggingSimpleOut
    return SuccessResponse(await crud.DishTaggingDal(auth.db).get_data(data_id, v_schema=schema))




###########################################################
#    产品图片
###########################################################
@app.get("/image", summary="获取产品图片列表", tags=["产品图片"])
async def get_dish_image_list(p: params.DishImageParams = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dishimage.list"]))):
    datas, count = await crud.DishImageDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/image", summary="创建产品图片", tags=["产品图片"])
async def create_dish_image(data: schemas.DishImage, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishimage.create"]))):
    return SuccessResponse(await crud.DishImageDal(auth.db).create_data(data=data))


@app.delete("/image", summary="删除产品图片", description="硬删除", tags=["产品图片"])
async def delete_dish_image_list(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dishimage.delete"]))):
    await crud.DishImageDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/image/{data_id}", summary="更新产品图片", tags=["产品图片"])
async def put_dish_image(data_id: int, data: schemas.DishImage, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishimage.update"]))):
    return SuccessResponse(await crud.DishImageDal(auth.db).put_data(data_id, data))


@app.get("/image/{data_id}", summary="获取产品图片信息", tags=["产品图片"])
async def get_dish_image(data_id: int, auth: Auth = Depends(FullAdminAuth(permissions=["product.dishimage.view"]))):
    schema = schemas.DishImageSimpleOut
    return SuccessResponse(await crud.DishImageDal(auth.db).get_data(data_id, v_schema=schema))




###########################################################
#    菜品
###########################################################
@app.get("/dishstatusoptions")
async def get_options_dishstatus():
    datas = [{"label": "新建", "value": schemas.DishStatusEnum.NEW},
        {"label": "草稿", "value": schemas.DishStatusEnum.DRAFT},
        {"label": "已上传", "value": schemas.DishStatusEnum.UPLOADED},
        {"label": "已发布", "value": schemas.DishStatusEnum.PUBLISHED},
        {"label": "缺货", "value": schemas.DishStatusEnum.OUTOFSTOCK},
        {"label": "已下架", "value": schemas.DishStatusEnum.TAKEDOWN}]
    return SuccessResponse(datas)


@app.get("/dish", summary="获取菜品列表")
async def get_dishs(
    params: params.DishParams = Depends(),
    auth: Auth = Depends(FullAdminAuth(permissions=["product.dish.list"]))
):
    datas, count = await crud.DishDal(auth.db).get_datas(
        **params.dict(),
        v_schema=schemas.DishOut,
        v_return_count=True
    )
    return SuccessResponse(datas, count=count)


@app.post("/dish", summary="创建菜品")
async def create_dish(data: schemas.DishIn, auth: Auth = Depends(FullAdminAuth(permissions=["product.dish.create"]))):
    res = SuccessResponse(await crud.DishDal(auth.db).create_data(data=data))
    if res.data['code'] == 200:
        await crud.DishDal(auth.db).update_image(res.data['data']['id'], data.dish_images)
    return res


@app.delete("/dish", summary="批量删除菜品")
async def delete_dishs(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["product.dish.delete"]))):
    await crud.DishDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功！")


@app.put("/dish/{data_id}", summary="更新菜品信息")
async def put_dish(
    data_id: int,
    data: schemas.DishIn,
    auth: Auth = Depends(FullAdminAuth(permissions=["product.dish.update"]))
):
    res = SuccessResponse(await crud.DishDal(auth.db).put_data(data_id, data))
    if res.data['code'] == 200:
        print(data.dish_images)
        await crud.DishDal(auth.db).update_image(data_id, data.dish_images)
    return res


@app.get("/dish/{data_id}", summary="获取菜品信息")
async def get_dish(
    data_id: int,
    auth: Auth = Depends(FullAdminAuth(permissions=["product.dish.view"]))
):
    model = models.Dish
    schema = schemas.DishOut
    return SuccessResponse(await crud.DishDal(auth.db).get_data(data_id, v_options=None, v_schema=schema))




###########################################################
#    成本卡
###########################################################
@app.get("/dishbom", summary="获取成本卡列表", tags=["成本卡"])
async def get_dish_bom_list(p: params.DishBomParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.DishBomDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/dishbom", summary="创建成本卡", tags=["成本卡"])
async def create_dish_bom(data: schemas.DishBom, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishBomDal(auth.db).create_data(data=data))


@app.delete("/dishbom", summary="删除成本卡", description="硬删除", tags=["成本卡"])
async def delete_dish_bom_list(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.DishBomDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/dishbom/{data_id}", summary="更新成本卡", tags=["成本卡"])
async def put_dish_bom(data_id: int, data: schemas.DishBom, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishBomDal(auth.db).put_data(data_id, data))


@app.get("/dishbom/{data_id}", summary="获取成本卡信息", tags=["成本卡"])
async def get_dish_bom(data_id: int, db: AsyncSession = Depends(db_getter)):
    schema = schemas.DishBomSimpleOut
    return SuccessResponse(await crud.DishBomDal(db).get_data(data_id, v_schema=schema))




###########################################################
#    菜品店铺
###########################################################
@app.get("/branchdish", summary="获取菜品店铺列表", tags=["菜品店铺"])
async def get_dish_branch_list(p: params.DishBranchParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.DishBranchDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/branchdish", summary="创建菜品店铺", tags=["菜品店铺"])
async def create_dish_branch(data: schemas.DishBranch, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishBranchDal(auth.db).create_data(data=data))


@app.delete("/branchdish", summary="删除菜品店铺", description="硬删除", tags=["菜品店铺"])
async def delete_dish_branch_list(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.DishBranchDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/branchdish/{data_id}", summary="更新菜品店铺", tags=["菜品店铺"])
async def put_dish_branch(data_id: int, data: schemas.DishBranch, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishBranchDal(auth.db).put_data(data_id, data))


@app.get("/branchdish/{data_id}", summary="获取菜品店铺信息", tags=["菜品店铺"])
async def get_dish_branch(data_id: int, db: AsyncSession = Depends(db_getter)):
    schema = schemas.DishBranchSimpleOut
    return SuccessResponse(await crud.DishBranchDal(db).get_data(data_id, v_schema=schema))




###########################################################
#    菜品分组类型
###########################################################
@app.get("/dishgroupstypeoptions")
async def get_options_dishgroupstype():
    datas = [{"label": "固定", "value": 2},
        {"label": "必选", "value": 1},
        {"label": "可选", "value": 0}]
    return SuccessResponse(datas)

@app.get("/dishgrouptype", summary="获取菜品分组类型列表", tags=["菜品分组类型"])
async def get_dish_group_type_list(p: params.DishGroupTypeParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.DishGroupTypeDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/dishgrouptype", summary="创建菜品分组类型", tags=["菜品分组类型"])
async def create_dish_group_type(data: schemas.DishGroupType, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishGroupTypeDal(auth.db).create_data(data=data))


@app.delete("/dishgrouptype", summary="删除菜品分组类型", description="硬删除", tags=["菜品分组类型"])
async def delete_dish_group_type_list(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.DishGroupTypeDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/dishgrouptype/{data_id}", summary="更新菜品分组类型", tags=["菜品分组类型"])
async def put_dish_group_type(data_id: int, data: schemas.DishGroupType, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishGroupTypeDal(auth.db).put_data(data_id, data))


@app.get("/dishgrouptype/{data_id}", summary="获取菜品分组类型信息", tags=["菜品分组类型"])
async def get_dish_group_type(data_id: int, db: AsyncSession = Depends(db_getter)):
    schema = schemas.DishGroupTypeSimpleOut
    return SuccessResponse(await crud.DishGroupTypeDal(db).get_data(data_id, v_schema=schema))




###########################################################
#    菜品分组
###########################################################
@app.get("/dishgroupstatusoptions")
async def get_options_dishgroupstatus():
    datas = [{"label": "新建", "value": schemas.DishGroupStatusEnum.NEW},
        {"label": "草稿", "value": schemas.DishGroupStatusEnum.DRAFT},
        {"label": "已上传", "value": schemas.DishGroupStatusEnum.UPLOADED},
        {"label": "已发布", "value": schemas.DishGroupStatusEnum.PUBLISHED}]
    return SuccessResponse(datas)


@app.get("/dishgroup", summary="获取菜品分组列表", tags=["菜品分组"])
async def get_dish_group_list(p: params.DishGroupParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.DishGroupDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/dishgroup", summary="创建菜品分组", tags=["菜品分组"])
async def create_dish_group(data: schemas.DishGroup, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishGroupDal(auth.db).create_data(data=data))


@app.delete("/dishgroup", summary="删除菜品分组", description="硬删除", tags=["菜品分组"])
async def delete_dish_group_list(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.DishGroupDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/dishgroup/{data_id}", summary="更新菜品分组", tags=["菜品分组"])
async def put_dish_group(data_id: int, data: schemas.DishGroup, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishGroupDal(auth.db).put_data(data_id, data))


@app.get("/dishgroup/{data_id}", summary="获取菜品分组信息", tags=["菜品分组"])
async def get_dish_group(data_id: int, db: AsyncSession = Depends(db_getter)):
    schema = schemas.DishGroupSimpleOut
    return SuccessResponse(await crud.DishGroupDal(db).get_data(data_id, v_schema=schema))




###########################################################
#    菜品分组明细
###########################################################
@app.get("/dishgroupdetail", summary="获取菜品分组明细列表", tags=["菜品分组明细"])
async def get_dish_group_detail_list(p: params.DishGroupDetailParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.DishGroupDetailDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/dishgroupdetail", summary="创建菜品分组明细", tags=["菜品分组明细"])
async def create_dish_group_detail(data: schemas.DishGroupDetail, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishGroupDetailDal(auth.db).create_data(data=data))


@app.delete("/dishgroupdetail", summary="删除菜品分组明细", description="硬删除", tags=["菜品分组明细"])
async def delete_dish_group_detail_list(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.DishGroupDetailDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/dishgroupdetail/{data_id}", summary="更新菜品分组明细", tags=["菜品分组明细"])
async def put_dish_group_detail(data_id: int, data: schemas.DishGroupDetail, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishGroupDetailDal(auth.db).put_data(data_id, data))


@app.get("/dishgroupdetail/{data_id}", summary="获取菜品分组明细信息", tags=["菜品分组明细"])
async def get_dish_group_detail(data_id: int, db: AsyncSession = Depends(db_getter)):
    schema = schemas.DishGroupDetailSimpleOut
    return SuccessResponse(await crud.DishGroupDetailDal(db).get_data(data_id, v_schema=schema))




###########################################################
#    菜品套餐系列
###########################################################
@app.get("/dishcomboseries", summary="获取菜品套餐系列列表", tags=["菜品套餐系列"])
async def get_dish_combo_series_list(p: params.DishComboSeriesParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.DishComboSeriesDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/dishcomboseries", summary="创建菜品套餐系列", tags=["菜品套餐系列"])
async def create_dish_combo_series(data: schemas.DishComboSeries, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishComboSeriesDal(auth.db).create_data(data=data))


@app.delete("/dishcomboseries", summary="删除菜品套餐系列", description="硬删除", tags=["菜品套餐系列"])
async def delete_dish_combo_series_list(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.DishComboSeriesDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/dishcomboseries/{data_id}", summary="更新菜品套餐系列", tags=["菜品套餐系列"])
async def put_dish_combo_series(data_id: int, data: schemas.DishComboSeries, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishComboSeriesDal(auth.db).put_data(data_id, data))


@app.get("/dishcomboseries/{data_id}", summary="获取菜品套餐系列信息", tags=["菜品套餐系列"])
async def get_dish_combo_series(data_id: int, db: AsyncSession = Depends(db_getter)):
    schema = schemas.DishComboSeriesSimpleOut
    return SuccessResponse(await crud.DishComboSeriesDal(db).get_data(data_id, v_schema=schema))




###########################################################
#    菜品套餐
###########################################################
@app.get("/dishcombostatusoptions")
async def get_options_dishcombostatus():
  datas = [{"label": "新建", "value": schemas.DishComboStatusEnum.NEW},
           {"label": "草稿", "value": schemas.DishComboStatusEnum.DRAFT},
           {"label": "已上传", "value": schemas.DishComboStatusEnum.UPLOADED},
           {"label": "已发布", "value": schemas.DishComboStatusEnum.PUBLISHED},
           {"label": "缺货", "value": schemas.DishComboStatusEnum.OUTOFSTOCK},
           {"label": "已下架", "value": schemas.DishComboStatusEnum.TAKEDOWN}]
  return SuccessResponse(datas)


@app.get("/dishcombo", summary="获取菜品套餐列表", tags=["菜品套餐"])
async def get_dish_combo_list(p: params.DishComboParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.DishComboDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/dishcombo", summary="创建菜品套餐", tags=["菜品套餐"])
async def create_dish_combo(data: schemas.DishCombo, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishComboDal(auth.db).create_data(data=data))


@app.delete("/dishcombo", summary="删除菜品套餐", description="硬删除", tags=["菜品套餐"])
async def delete_dish_combo_list(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.DishComboDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/dishcombo/{data_id}", summary="更新菜品套餐", tags=["菜品套餐"])
async def put_dish_combo(data_id: int, data: schemas.DishCombo, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishComboDal(auth.db).put_data(data_id, data))


@app.get("/dishcombo/{data_id}", summary="获取菜品套餐信息", tags=["菜品套餐"])
async def get_dish_combo(data_id: int, db: AsyncSession = Depends(db_getter)):
    schema = schemas.DishComboSimpleOut
    return SuccessResponse(await crud.DishComboDal(db).get_data(data_id, v_schema=schema))




###########################################################
#    菜品套餐详情
###########################################################
@app.get("/dishcombodetail", summary="获取菜品套餐详情列表", tags=["菜品套餐详情"])
async def get_dish_combo_detail_list(p: params.DishComboDetailParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.DishComboDetailDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/dishcombodetail", summary="创建菜品套餐详情", tags=["菜品套餐详情"])
async def create_dish_combo_detail(data: schemas.DishComboDetail, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishComboDetailDal(auth.db).create_data(data=data))


@app.delete("/dishcombodetail", summary="删除菜品套餐详情", description="硬删除", tags=["菜品套餐详情"])
async def delete_dish_combo_detail_list(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.DishComboDetailDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/dishcombodetail/{data_id}", summary="更新菜品套餐详情", tags=["菜品套餐详情"])
async def put_dish_combo_detail(data_id: int, data: schemas.DishComboDetail, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DishComboDetailDal(auth.db).put_data(data_id, data))


@app.get("/dishcombodetail/{data_id}", summary="获取菜品套餐详情信息", tags=["菜品套餐详情"])
async def get_dish_combo_detail(data_id: int, db: AsyncSession = Depends(db_getter)):
    schema = schemas.DishComboDetailSimpleOut
    return SuccessResponse(await crud.DishComboDetailDal(db).get_data(data_id, v_schema=schema))
