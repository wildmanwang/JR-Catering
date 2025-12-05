from db.db_base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, column_property, aliased, declared_attr
from sqlalchemy import String, DECIMAL, Integer, Boolean, DateTime, select, and_, func, JSON, text
from datetime import datetime
from apps.vadmin.product.models.dish import DishImage


class DishComboSeries(BaseModel):
    __tablename__ = "dish_combo_series"
    __table_args__ = ({'comment': '菜品套餐系列表'})
    
    name_unique: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="名称")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可用")


class DishCombo(BaseModel):
    __tablename__ = "dish_combo"
    __table_args__ = ({'comment': '菜品套餐表'})
    
    name_unique: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="名称")
    name_display: Mapped[str | None] = mapped_column(String(255), comment="显示名称")
    name_english: Mapped[str | None] = mapped_column(String(255), comment="英文名称")
    dish_combo_series_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="菜品套餐系列")
    person_number: Mapped[int] = mapped_column(Integer, nullable=False, comment="人数")
    price: Mapped[float | None] = mapped_column(DECIMAL(12, 2), comment="价格")
    cost_price: Mapped[float | None] = mapped_column(DECIMAL(12, 2), comment="成本价")
    time_on: Mapped[datetime | None] = mapped_column(DateTime, comment="上架时间")
    time_off: Mapped[datetime | None] = mapped_column(DateTime, comment="下架时间")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")
    status: Mapped[int] = mapped_column(Integer, nullable=False, comment="0:草稿;1:已上传;2:已发布;9:已下线")
    description: Mapped[str | None] = mapped_column(String(255), comment="简介")
    description_english: Mapped[str | None] = mapped_column(String(255), comment="英文简介")

    dish_combo_series_name_unique = column_property(
        select(DishComboSeries.name_unique)
        .where(DishComboSeries.id == dish_combo_series_id)
        .correlate_except(DishComboSeries)
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
                    dish_image_alias.product_type == 2,
                    dish_image_alias.product_id == cls.id))
            .order_by(
                dish_image_alias.is_first.desc(),
                dish_image_alias.order_number.asc()
            )
            .scalar_subquery()
            .cast(JSON)
        )


class DishComboDetail(BaseModel):
    __tablename__ = "dish_combo_detail"
    __table_args__ = ({'comment': '菜品套餐详情表'})
    
    dish_combo_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="菜品套餐")
    dish_group_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="菜品组")
    name_display: Mapped[str | None] = mapped_column(String(255), comment="显示名称")
    name_english: Mapped[str | None] = mapped_column(String(255), comment="英文名称")
    choose_number: Mapped[int] = mapped_column(Integer, nullable=False, comment="可选数量")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")
