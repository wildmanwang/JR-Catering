from db.db_base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, column_property, aliased, declared_attr
from sqlalchemy import String, DECIMAL, Integer, Boolean, DateTime, select, and_, func, JSON, text
from datetime import datetime
from apps.vadmin.system.models.branch import Branch


class DishKitchen(BaseModel):
    __tablename__ = "dish_kitchen"
    __table_args__ = ({'comment': '厨部表'})
    
    name_unique: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="名称")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可用")


class DishKitchenBranch(BaseModel):
    __tablename__ = "dish_kitchen_branch"
    __table_args__ = ({'comment': '厨部店铺表'})
    
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="店铺")
    dish_kitchen_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="厨部")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")


class DishTag(BaseModel):
    __tablename__ = "dish_tag"
    __table_args__ = ({'comment': '标签表'})
    
    name_unique: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="名称")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可用")


class DishTagging(BaseModel):
    __tablename__ = "dish_tagging"
    __table_args__ = ({'comment': '菜品标签表'})
    
    dish_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="菜品")
    dish_tag_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="标签")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")


class DishImage(BaseModel):
    __tablename__ = "dish_image"
    __table_args__ = ({'comment': '产品图片表'})

    product_type: Mapped[int] = mapped_column(Integer, comment="类型 1/单品;2/套餐")
    product_id: Mapped[int] = mapped_column(Integer, comment="产品")
    img_platform: Mapped[str] = mapped_column(String(50), nullable=False, default="default", comment="图片平台")
    img_url: Mapped[str] = mapped_column(String(255), comment="图片地址")
    is_first: Mapped[bool] = mapped_column(Boolean, comment="是否首图")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")


class Dish(BaseModel):
    __tablename__ = "dish"
    __table_args__ = ({'comment': '菜品表'})

    name_unique: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="名称")
    kitchen_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="厨部")
    name_display: Mapped[str | None] = mapped_column(String(255), comment="显示名称")
    name_english: Mapped[str | None] = mapped_column(String(255), comment="英文名称")
    spec: Mapped[str | None] = mapped_column(String(255), comment="规格")
    unit: Mapped[str | None] = mapped_column(String(50), comment="单位")
    price: Mapped[float | None] = mapped_column(DECIMAL(12, 2), comment="价格")
    time_on: Mapped[datetime | None] = mapped_column(DateTime, comment="上架时间")
    time_off: Mapped[datetime | None] = mapped_column(DateTime, comment="下架时间")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")
    status: Mapped[int] = mapped_column(Integer, nullable=False, comment="0:草稿;2:已发布;9:已下线")
    description: Mapped[str | None] = mapped_column(String(255), comment="简介")
    description_english: Mapped[str | None] = mapped_column(String(255), comment="英文简介")
    
    kitchen_name_unique = column_property(
        select(DishKitchen.name_unique)
        .where(DishKitchen.id == kitchen_id)
        .correlate_except(DishKitchen)
        .scalar_subquery())

    @declared_attr.directive
    def dish_images(cls):
        dish_image_alias = aliased(DishImage)
        return column_property(
            select(func.coalesce(
                func.json_arrayagg(
                    func.concat(
                        func.ifnull(dish_image_alias.order_number, '00'),
                        text("'-'"),
                        dish_image_alias.img_url
                    )
                ),
                text("'[]'")
            ))
            .select_from(dish_image_alias)
            .where(
                and_(
                    dish_image_alias.product_type == 1,
                    dish_image_alias.product_id == cls.id))
            .order_by(
                dish_image_alias.is_first.desc(),
                dish_image_alias.order_number.asc()
            )
            .scalar_subquery()
            .cast(JSON)
        )


class DishBom(BaseModel):
    __tablename__ = "dish_bom"
    __table_args__ = ({'comment': '菜品BOM表'})
    
    product_type: Mapped[int] = mapped_column(Integer, comment="类型 1/单品;2/套餐")
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="产品")
    material_type: Mapped[int] = mapped_column(Integer, comment="类型 1/食材;2/耗材")
    material_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="物料")
    spec: Mapped[str | None] = mapped_column(String(255), comment="规格")
    unit: Mapped[str | None] = mapped_column(String(50), comment="单位")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="数量")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")


class DishBranch(BaseModel):
    __tablename__ = "dish_branch"
    __table_args__ = ({'comment': '菜品店铺表'})
    
    dish_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="菜品")
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="店铺")
    name_display: Mapped[str | None] = mapped_column(String(255), comment="显示名称")
    name_english: Mapped[str | None] = mapped_column(String(255), comment="英文名称")
    price: Mapped[float | None] = mapped_column(DECIMAL(12, 2), comment="价格")
    cost_price: Mapped[float | None] = mapped_column(DECIMAL(12, 2), comment="成本价")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")
    status: Mapped[int] = mapped_column(Integer, nullable=False, comment="0:草稿;1:已上传;2:已发布;3:库存不足;9:已下线")
    description: Mapped[str | None] = mapped_column(String(255), comment="简介")
    description_english: Mapped[str | None] = mapped_column(String(255), comment="英文简介")

    dish_name_unique = column_property(
        select(Dish.name_unique)
        .where(Dish.id == dish_id)
        .correlate_except(Dish)
        .scalar_subquery())
    branch_name_unique = column_property(
        select(Branch.name_unique)
        .where(Branch.id == branch_id)
        .correlate_except(Branch)
        .scalar_subquery())
