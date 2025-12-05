#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2025/11/28 10:54
# @File           : crud.py
# @IDE            : PyCharm
# @desc           : 数据访问层
from core.crud import DalBase
from . import models, schemas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, outerjoin, func, and_, BinaryExpression



class DishKitchenDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishKitchenDal, self).__init__()
        self.db = db
        self.model = models.DishKitchen
        self.schema = schemas.DishKitchenSimpleOut


class DishKitchenBranchDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishKitchenBranchDal, self).__init__()
        self.db = db
        self.model = models.DishKitchenBranch
        self.schema = schemas.DishKitchenBranchSimpleOut


class DishTagDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishTagDal, self).__init__()
        self.db = db
        self.model = models.DishTag
        self.schema = schemas.DishTagSimpleOut


class DishTaggingDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishTaggingDal, self).__init__()
        self.db = db
        self.model = models.DishTagging
        self.schema = schemas.DishTaggingSimpleOut


class DishImageDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishImageDal, self).__init__()
        self.db = db
        self.model = models.DishImage
        self.schema = schemas.DishImageSimpleOut


class DishDal(DalBase):
    import_headers = [
        {"label": "名称", "field": "name_unique", "required": True},
        {"label": "厨部", "field": "kitchen_id", "required": True},
        {"label": "显示名称", "field": "name_display", "required": False},
        {"label": "英文名称", "field": "name_english", "required": False},
        {"label": "规格", "field": "spec", "required": False},
        {"label": "单位", "field": "unit", "required": False},
        {"label": "价格", "field": "price", "required": False},
        {"label": "上架时间", "field": "time_on", "required": False},
        {"label": "下架时间", "field": "time_off", "required": False},
        {"label": "排序号", "field": "order_number", "required": False},
        {"label": "状态", "field": "status", "required": True},
        {"label": "简介", "field": "description", "required": False},
        {"label": "英文简介", "field": "description_english", "required": False}
    ]

    def __init__(self, db: AsyncSession):
        super(DishDal, self).__init__()
        self.db = db
        self.model = models.Dish
        self.schema = schemas.DishOut
    
    async def update_image(self, data_id: int, oper_url: list[str]) -> models.Dish:
        '''
        产品图片处理
        '''
        dish = await self.get_data(data_id)
        if not dish:
            raise Exception('菜品id无效：{dish_id}', dish_id=data_id)
        dishImage = DishImageDal(db=self.db)
        order_number = 0
        bFirst = 0
        for oper_str in oper_url:
            oper_type = oper_str.split('?')[1]
            url = oper_str.split('?')[0]
            if not url:
                raise Exception('菜品图片地址无效')
            order_number += 10
            if oper_type == 'add':
                if order_number == 10:
                    bFirst = 1
                else:
                    bFirst = 0
                oper_image = models.DishImage(product_type=1, product_id=data_id, img_platform='default', img_url=url, is_first=bFirst, order_number=order_number)
                self.db.add(oper_image)
            elif oper_type == 'delete':
                order_number -= 10
                stmt = select(models.DishImage).where(models.DishImage.img_url == url)
                result = await dishImage.db.execute(stmt)
                oper_image = result.scalars().first()
                await dishImage.db.delete(oper_image)
            elif oper_type == 'update':
                stmt = select(models.DishImage).where(models.DishImage.img_url == url)
                result = await dishImage.db.execute(stmt)
                oper_image = result.scalars().first()
                oper_image.order_number = order_number
                if order_number == 10 and oper_image.is_first != 1:
                    oper_image.is_first = 1
                elif order_number > 10 and oper_image.is_first == 1:
                    oper_image.is_first = 0
            elif oper_type == 'original':
                stmt = select(models.DishImage).where(models.DishImage.img_url == url)
                result = await dishImage.db.execute(stmt)
                oper_image = result.scalars().first()
                if oper_image.order_number != order_number:
                    oper_image.order_number = order_number
                if order_number == 10 and oper_image.is_first != 1:
                    oper_image.is_first = 1
                elif order_number > 10 and oper_image.is_first == 1:
                    oper_image.is_first = 0
            else:
                raise Exception('菜品图片操作失败：无效的操作类型：{oper_type}', oper_type=oper_type)
        await self.db.refresh(dish)
        return dish

    async def upload(
            self,
            dish: models.Dish
    ) -> dict:
        """
        菜品上传
        :param dish:
        :return
        {
            "result": bool,
            "data_number": float,
            "data_str": str,
            "msg": str,
            "data_list": []
        }
        """
        rtn = {
            "result": False,
            "msg": ""
        }

        if not dish:
            rtn["msg"] = "菜品无效"
        
        return rtn
    
    async def online(
            self,
            dish: models.Dish
    ) -> dict:
        """
        菜品上线
        :param dish
        :return
        {
            "result": bool,
            "data_number": float,
            "data_str": str,
            "msg": str,
            "data_list": []
        }
        """
        rtn = {
            "result": False,
            "msg": ""
        }

        if not dish:
            rtn["msg"] = "菜品无效"
        
        return rtn

    async def offline(
            self,
            dish: models.Dish
    ) -> dict:
        """
        菜品下线
        :param dish
        :return
        {
            "result": bool,
            "data_number": float,
            "data_str": str,
            "msg": str,
            "data_list": []
        }
        """
        rtn = {
            "result": False,
            "msg": ""
        }

        if not dish:
            rtn["msg"] = "菜品无效"
        
        return rtn


class DishBomDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishBomDal, self).__init__()
        self.db = db
        self.model = models.DishBom
        self.schema = schemas.DishBomSimpleOut


class DishBranchDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishBranchDal, self).__init__()
        self.db = db
        self.model = models.DishBranch
        self.schema = schemas.DishBranchSimpleOut


class DishGroupTypeDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishGroupTypeDal, self).__init__()
        self.db = db
        self.model = models.DishGroupType
        self.schema = schemas.DishGroupTypeSimpleOut


class DishGroupDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishGroupDal, self).__init__()
        self.db = db
        self.model = models.DishGroup
        self.schema = schemas.DishGroupSimpleOut


class DishGroupDetailDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishGroupDetailDal, self).__init__()
        self.db = db
        self.model = models.DishGroupDetail
        self.schema = schemas.DishGroupDetailSimpleOut


class DishComboSeriesDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishComboSeriesDal, self).__init__()
        self.db = db
        self.model = models.DishComboSeries
        self.schema = schemas.DishComboSeriesSimpleOut


class DishComboDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishComboDal, self).__init__()
        self.db = db
        self.model = models.DishCombo
        self.schema = schemas.DishComboSimpleOut


class DishComboDetailDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(DishComboDetailDal, self).__init__()
        self.db = db
        self.model = models.DishComboDetail
        self.schema = schemas.DishComboDetailSimpleOut
