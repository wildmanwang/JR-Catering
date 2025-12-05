# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2021/10/24 16:44
# @File           : views.py
# @IDE            : PyCharm
# @desc           : 主要接口文件
from core.dependencies import IdList
from redis.asyncio import Redis
from apps.vadmin.system.utils.current import AllUserAuth
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, crud, schemas, params
from application.settings import ALIYUN_OSS
from utils.file.file_manage import FileManage
from apps.vadmin.system.utils.current import AllUserAuth, FullAdminAuth, OpenAuth
from apps.vadmin.system import crud as vadmin_auth_crud
from apps.vadmin.system.utils.validation.auth import Auth
from utils.response import SuccessResponse, ErrorResponse
from utils.sms.code import CodeSMS
from utils.file.aliyun_oss import AliyunOSS, BucketConf
from apps.vadmin.system.utils.validation.auth import Auth
from .params import RoleParams, DeptParams, DictDetailParams, UserParams, DictTypeParams
from core.database import redis_getter, db_getter
from sqlalchemy.orm import joinedload
from fastapi import UploadFile, Depends, APIRouter, Form, Request, Body

app = APIRouter()


###########################################################
#    系统字典
###########################################################
@app.get("/dict/genderoptions")
async def get_options_gender():
    datas = [{"label": "男", "value": schemas.GenderEnum.MALE},
        {"label": "女", "value": schemas.GenderEnum.FEMALE},
        {"label": "未知", "value": schemas.GenderEnum.UNKNOW}]
    return SuccessResponse(datas)


###########################################################
#    用户管理
###########################################################
@app.get("/users", summary="获取用户列表")
async def get_users(
        params: UserParams = Depends(),
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.user.list"]))
):
    model = models.VadminUser
    options = [joinedload(model.roles), joinedload(model.depts)]
    schema = schemas.UserOut
    datas, count = await crud.UserDal(auth.db).get_datas(
        **params.dict(),
        v_options=options,
        v_schema=schema,
        v_return_count=True
    )
    return SuccessResponse(datas, count=count)


@app.post("/users", summary="创建用户")
async def create_user(data: schemas.UserIn, auth: Auth = Depends(FullAdminAuth(permissions=["auth.user.create"]))):
    return SuccessResponse(await crud.UserDal(auth.db).create_data(data=data))


@app.delete("/users", summary="批量删除用户", description="软删除，删除后清空所关联的角色")
async def delete_users(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["auth.user.delete"]))):
    if auth.user.id in ids.ids:
        return ErrorResponse("不能删除当前登录用户")
    elif 1 in ids.ids:
        return ErrorResponse("不能删除超级管理员用户")
    await crud.UserDal(auth.db).delete_datas(ids=ids.ids, v_soft=True, is_active=False)
    return SuccessResponse("删除成功")


@app.put("/users/{data_id}", summary="更新用户信息")
async def put_user(
        data_id: int,
        data: schemas.UserUpdate,
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.user.update"]))
):
    return SuccessResponse(await crud.UserDal(auth.db).put_data(data_id, data))


@app.get("/users/{data_id}", summary="获取用户信息")
async def get_user(
        data_id: int,
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.user.view", "auth.user.update"]))
):
    model = models.VadminUser
    options = [joinedload(model.roles), joinedload(model.depts)]
    schema = schemas.UserOut
    return SuccessResponse(await crud.UserDal(auth.db).get_data(data_id, v_options=options, v_schema=schema))


@app.post("/user/current/reset/password", summary="重置当前用户密码")
async def user_current_reset_password(data: schemas.ResetPwd, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.UserDal(auth.db).reset_current_password(auth.user, data))


@app.post("/user/current/update/info", summary="更新当前用户基本信息")
async def post_user_current_update_info(data: schemas.UserUpdateBaseInfo, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.UserDal(auth.db).update_current_info(auth.user, data))


@app.post("/user/current/update/avatar", summary="更新当前用户头像")
async def post_user_current_update_avatar(file: UploadFile, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.UserDal(auth.db).update_current_avatar(auth.user, file))


@app.get("/user/admin/current/info", summary="获取当前管理员信息")
async def get_user_admin_current_info(auth: Auth = Depends(FullAdminAuth())):
    result = schemas.UserOut.model_validate(auth.user).model_dump()
    result["permissions"] = list(FullAdminAuth.get_user_permissions(auth.user))
    return SuccessResponse(result)


@app.post("/user/export/query/list/to/excel", summary="导出用户查询列表为excel")
async def post_user_export_query_list(
        header: list = Body(..., title="表头与对应字段"),
        params: UserParams = Depends(),
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.user.export"]))
):
    return SuccessResponse(await crud.UserDal(auth.db).export_query_list(header, params))


@app.get("/user/download/import/template", summary="下载最新批量导入用户模板")
async def get_user_download_new_import_template(auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.UserDal(auth.db).download_import_template())


@app.post("/import/users", summary="批量导入用户")
async def post_import_users(file: UploadFile, auth: Auth = Depends(FullAdminAuth(permissions=["auth.user.import"]))):
    return SuccessResponse(await crud.UserDal(auth.db).import_users(file))


@app.post("/users/init/password/send/sms", summary="初始化所选用户密码并发送通知短信")
async def post_users_init_password(
        request: Request,
        ids: IdList = Depends(),
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.user.reset"])),
        rd: Redis = Depends(redis_getter)
):
    return SuccessResponse(await crud.UserDal(auth.db).init_password_send_sms(ids.ids, rd))


@app.post("/users/init/password/send/email", summary="初始化所选用户密码并发送通知邮件")
async def post_users_init_password_send_email(
        request: Request,
        ids: IdList = Depends(),
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.user.reset"])),
        rd: Redis = Depends(redis_getter)
):
    return SuccessResponse(await crud.UserDal(auth.db).init_password_send_email(ids.ids, rd))


@app.put("/users/wx/server/openid", summary="更新当前用户服务端微信平台openid")
async def put_user_wx_server_openid(code: str, auth: Auth = Depends(AllUserAuth()), rd: Redis = Depends(redis_getter)):
    result = await crud.UserDal(auth.db).update_wx_server_openid(code, auth.user, rd)
    return SuccessResponse(result)


###########################################################
#    角色管理
###########################################################
@app.get("/roles", summary="获取角色列表")
async def get_roles(
        params: RoleParams = Depends(),
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.role.list"]))
):
    datas, count = await crud.RoleDal(auth.db).get_datas(**params.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/roles", summary="创建角色信息")
async def create_role(role: schemas.RoleIn, auth: Auth = Depends(FullAdminAuth(permissions=["auth.role.create"]))):
    return SuccessResponse(await crud.RoleDal(auth.db).create_data(data=role))


@app.delete("/roles", summary="批量删除角色", description="硬删除, 如果存在用户关联则无法删除")
async def delete_roles(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["auth.role.delete"]))):
    if 1 in ids.ids:
        return ErrorResponse("不能删除管理员角色")
    await crud.RoleDal(auth.db).delete_datas(ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/roles/{data_id}", summary="更新角色信息")
async def put_role(
        data_id: int,
        data: schemas.RoleIn,
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.role.update"]))
):
    if 1 == data_id:
        return ErrorResponse("不能修改管理员角色")
    return SuccessResponse(await crud.RoleDal(auth.db).put_data(data_id, data))


@app.get("/roles/options", summary="获取角色选择项")
async def get_role_options(auth: Auth = Depends(FullAdminAuth(permissions=["auth.user.create", "auth.user.update"]))):
    return SuccessResponse(await crud.RoleDal(auth.db).get_select_datas())


@app.get("/roles/{data_id}", summary="获取角色信息")
async def get_role(
        data_id: int,
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.role.view", "auth.role.update"]))
):
    model = models.VadminRole
    options = [joinedload(model.menus), joinedload(model.depts)]
    schema = schemas.RoleOut
    return SuccessResponse(await crud.RoleDal(auth.db).get_data(data_id, v_options=options, v_schema=schema))


###########################################################
#    菜单管理
###########################################################
@app.get("/menus", summary="获取菜单列表")
async def get_menus(auth: Auth = Depends(FullAdminAuth(permissions=["auth.menu.list"]))):
    datas = await crud.MenuDal(auth.db).get_tree_list(mode=1)
    return SuccessResponse(datas)


@app.get("/menus/tree/options", summary="获取菜单树选择项，添加/修改菜单时使用")
async def get_menus_options(auth: Auth = Depends(FullAdminAuth(permissions=["auth.menu.create", "auth.menu.update"]))):
    datas = await crud.MenuDal(auth.db).get_tree_list(mode=2)
    return SuccessResponse(datas)


@app.get("/menus/role/tree/options", summary="获取菜单列表树信息，角色权限使用")
async def get_menus_treeselect(
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.role.create", "auth.role.update"]))
):
    return SuccessResponse(await crud.MenuDal(auth.db).get_tree_list(mode=3))


@app.post("/menus", summary="创建菜单信息")
async def create_menu(menu: schemas.Menu, auth: Auth = Depends(FullAdminAuth(permissions=["auth.menu.create"]))):
    if menu.parent_id:
        menu.alwaysShow = False
    return SuccessResponse(await crud.MenuDal(auth.db).create_data(data=menu))


@app.delete("/menus", summary="批量删除菜单", description="硬删除, 如果存在角色关联则无法删除")
async def delete_menus(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth(permissions=["auth.menu.delete"]))):
    await crud.MenuDal(auth.db).delete_datas(ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/menus/{data_id}", summary="更新菜单信息")
async def put_menus(
        data_id: int,
        data: schemas.Menu, auth: Auth = Depends(FullAdminAuth(permissions=["auth.menu.update"]))
):
    return SuccessResponse(await crud.MenuDal(auth.db).put_data(data_id, data))


@app.get("/menus/{data_id}", summary="获取菜单信息")
async def get_menus(
        data_id: int,
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.menu.view", "auth.menu.update"]))
):
    schema = schemas.MenuSimpleOut
    return SuccessResponse(await crud.MenuDal(auth.db).get_data(data_id, v_schema=schema))


@app.get("/role/menus/tree/{role_id}", summary="获取菜单列表树信息以及角色菜单权限ID，角色权限使用")
async def get_role_menu_tree(
        role_id: int,
        auth: Auth = Depends(FullAdminAuth(permissions=["auth.role.create", "auth.role.update"]))
):
    tree_data = await crud.MenuDal(auth.db).get_tree_list(mode=3)
    role_menu_tree = await crud.RoleDal(auth.db).get_role_menu_tree(role_id)
    return SuccessResponse({"role_menu_tree": role_menu_tree, "menus": tree_data})


###########################################################
#    部门管理
###########################################################
@app.get("/depts", summary="获取部门列表")
async def get_depts(
        params: DeptParams = Depends(),
        auth: Auth = Depends(FullAdminAuth())
):
    datas = await crud.DeptDal(auth.db).get_tree_list(1)
    return SuccessResponse(datas)


@app.get("/dept/tree/options", summary="获取部门树选择项，添加/修改部门时使用")
async def get_dept_options(auth: Auth = Depends(FullAdminAuth())):
    datas = await crud.DeptDal(auth.db).get_tree_list(mode=2)
    return SuccessResponse(datas)


@app.get("/dept/user/tree/options", summary="获取部门树选择项，添加/修改用户时使用")
async def get_dept_treeselect(auth: Auth = Depends(FullAdminAuth())):
    return SuccessResponse(await crud.DeptDal(auth.db).get_tree_list(mode=3))


@app.post("/depts", summary="创建部门信息")
async def create_dept(data: schemas.Dept, auth: Auth = Depends(FullAdminAuth())):
    return SuccessResponse(await crud.DeptDal(auth.db).create_data(data=data))


@app.delete("/depts", summary="批量删除部门", description="硬删除, 如果存在用户关联则无法删除")
async def delete_depts(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth())):
    await crud.DeptDal(auth.db).delete_datas(ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/depts/{data_id}", summary="更新部门信息")
async def put_dept(
        data_id: int,
        data: schemas.Dept,
        auth: Auth = Depends(FullAdminAuth())
):
    return SuccessResponse(await crud.DeptDal(auth.db).put_data(data_id, data))


###########################################################
#    字典类型管理
###########################################################
@app.get("/dict/types", summary="获取字典类型列表")
async def get_dict_types(p: DictTypeParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.DictTypeDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/dict/types", summary="创建字典类型")
async def create_dict_types(data: schemas.DictType, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DictTypeDal(auth.db).create_data(data=data))


@app.delete("/dict/types", summary="批量删除字典类型")
async def delete_dict_types(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.DictTypeDal(auth.db).delete_datas(ids=ids.ids)
    return SuccessResponse("删除成功")


@app.post("/dict/types/details", summary="获取多个字典类型下的字典元素列表")
async def post_dicts_details(
        auth: Auth = Depends(AllUserAuth()),
        dict_types: list[str] = Body(None, title="字典元素列表", description="查询字典元素列表")
):
    datas = await crud.DictTypeDal(auth.db).get_dicts_details(dict_types)
    return SuccessResponse(datas)


@app.get("/dict/types/options", summary="获取字典类型选择项")
async def get_dicts_options(auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DictTypeDal(auth.db).get_select_datas())


@app.put("/dict/types/{data_id}", summary="更新字典类型")
async def put_dict_types(data_id: int, data: schemas.DictType, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DictTypeDal(auth.db).put_data(data_id, data))


@app.get("/dict/types/{data_id}", summary="获取字典类型详细")
async def get_dict_type(data_id: int, auth: Auth = Depends(AllUserAuth())):
    schema = schemas.DictTypeSimpleOut
    return SuccessResponse(await crud.DictTypeDal(auth.db).get_data(data_id, v_schema=schema))


###########################################################
#    字典元素管理
###########################################################
@app.post("/dict/details", summary="创建字典元素")
async def create_dict_details(data: schemas.DictDetails, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DictDetailsDal(auth.db).create_data(data=data))


@app.get("/dict/details", summary="获取单个字典类型下的字典元素列表，分页")
async def get_dict_details(params: DictDetailParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.DictDetailsDal(auth.db).get_datas(**params.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.delete("/dict/details", summary="批量删除字典元素", description="硬删除")
async def delete_dict_details(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.DictDetailsDal(auth.db).delete_datas(ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/dict/details/{data_id}", summary="更新字典元素")
async def put_dict_details(data_id: int, data: schemas.DictDetails, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.DictDetailsDal(auth.db).put_data(data_id, data))


@app.get("/dict/details/{data_id}", summary="获取字典元素详情")
async def get_dict_detail(data_id: int, auth: Auth = Depends(AllUserAuth())):
    schema = schemas.DictDetailsSimpleOut
    return SuccessResponse(await crud.DictDetailsDal(auth.db).get_data(data_id, v_schema=schema))


###########################################################
#    文件上传管理
###########################################################
@app.post("/upload/image/to/oss", summary="上传图片到阿里云OSS")
async def upload_image_to_oss(file: UploadFile, path: str = Form(...)):
    result = await AliyunOSS(BucketConf(**ALIYUN_OSS)).upload_image(path, file)
    return SuccessResponse(result)


@app.post("/upload/video/to/oss", summary="上传视频到阿里云OSS")
async def upload_video_to_oss(file: UploadFile, path: str = Form(...)):
    result = await AliyunOSS(BucketConf(**ALIYUN_OSS)).upload_video(path, file)
    return SuccessResponse(result)


@app.post("/upload/file/to/oss", summary="上传文件到阿里云OSS")
async def upload_file_to_oss(file: UploadFile, path: str = Form(...)):
    result = await AliyunOSS(BucketConf(**ALIYUN_OSS)).upload_file(path, file)
    return SuccessResponse(result)


@app.post("/upload/image/to/local", summary="上传图片到本地")
async def upload_image_to_local(file: UploadFile, path: str = Form(...)):
    manage = FileManage(file, path)
    path = await manage.save_image_local()
    return SuccessResponse(path)


###########################################################
#    短信服务管理
###########################################################
@app.post("/sms/send", summary="发送短信验证码（阿里云服务）")
async def sms_send(telephone: str, rd: Redis = Depends(redis_getter), auth: Auth = Depends(OpenAuth())):
    user = await vadmin_auth_crud.UserDal(auth.db).get_data(telephone=telephone, v_return_none=True)
    if not user:
        return ErrorResponse("手机号不存在！")
    sms = CodeSMS(telephone, rd)
    return SuccessResponse(await sms.main_async())


###########################################################
#    系统配置管理
###########################################################
@app.post("/settings/tabs", summary="获取系统配置标签列表")
async def get_settings_tabs(classifys: list[str] = Body(...), auth: Auth = Depends(FullAdminAuth())):
    return SuccessResponse(await crud.SettingsTabDal(auth.db).get_datas(limit=0, classify=("in", classifys)))


@app.get("/settings/tabs/values", summary="获取系统配置标签下的信息")
async def get_settings_tabs_values(tab_id: int, auth: Auth = Depends(FullAdminAuth())):
    return SuccessResponse(await crud.SettingsDal(auth.db).get_tab_values(tab_id=tab_id))


@app.put("/settings/tabs/values", summary="更新系统配置信息")
async def put_settings_tabs_values(
        request: Request,
        datas: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth())
):
    return SuccessResponse(await crud.SettingsDal(auth.db).update_datas(datas, request))


@app.get("/settings/base/config", summary="获取系统基础配置", description="每次进入系统中时使用")
async def get_setting_base_config(db: AsyncSession = Depends(db_getter)):
    return SuccessResponse(await crud.SettingsDal(db).get_base_config())


@app.get("/settings/privacy", summary="获取隐私协议")
async def get_settings_privacy(auth: Auth = Depends(OpenAuth())):
    return SuccessResponse((await crud.SettingsDal(auth.db).get_data(config_key="web_privacy")).config_value)


@app.get("/settings/agreement", summary="获取用户协议")
async def get_settings_agreement(auth: Auth = Depends(OpenAuth())):
    return SuccessResponse((await crud.SettingsDal(auth.db).get_data(config_key="web_agreement")).config_value)


###########################################################
#    公司
###########################################################
@app.get("/company", summary="获取公司列表", tags=["公司"])
async def get_company_list(p: params.CompanyParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.CompanyDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/company", summary="创建公司", tags=["公司"])
async def create_company(data: schemas.Company, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.CompanyDal(auth.db).create_data(data=data))


@app.delete("/company", summary="删除公司", description="硬删除", tags=["公司"])
async def delete_company_list(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.CompanyDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/company/{data_id}", summary="更新公司", tags=["公司"])
async def put_company(data_id: int, data: schemas.Company, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.CompanyDal(auth.db).put_data(data_id, data))


@app.get("/company/{data_id}", summary="获取公司信息", tags=["公司"])
async def get_company(data_id: int, db: AsyncSession = Depends(db_getter)):
    schema = schemas.CompanySimpleOut
    return SuccessResponse(await crud.CompanyDal(db).get_data(data_id, v_schema=schema))


###########################################################
#    店铺
###########################################################
@app.get("/branch", summary="获取店铺列表", tags=["店铺"])
async def get_branch_list(p: params.BranchParams = Depends(), auth: Auth = Depends(AllUserAuth())):
    datas, count = await crud.BranchDal(auth.db).get_datas(**p.dict(), v_return_count=True)
    return SuccessResponse(datas, count=count)


@app.post("/branch", summary="创建店铺", tags=["店铺"])
async def create_branch(data: schemas.Branch, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.BranchDal(auth.db).create_data(data=data))


@app.delete("/branch", summary="删除店铺", description="硬删除", tags=["店铺"])
async def delete_branch_list(ids: IdList = Depends(), auth: Auth = Depends(AllUserAuth())):
    await crud.BranchDal(auth.db).delete_datas(ids=ids.ids, v_soft=False)
    return SuccessResponse("删除成功")


@app.put("/branch/{data_id}", summary="更新店铺", tags=["店铺"])
async def put_branch(data_id: int, data: schemas.Branch, auth: Auth = Depends(AllUserAuth())):
    return SuccessResponse(await crud.BranchDal(auth.db).put_data(data_id, data))


@app.get("/branch/{data_id}", summary="获取店铺信息", tags=["店铺"])
async def get_branch(data_id: int, db: AsyncSession = Depends(db_getter)):
    schema = schemas.BranchSimpleOut
    return SuccessResponse(await crud.BranchDal(db).get_data(data_id, v_schema=schema))

