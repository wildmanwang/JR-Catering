from db.db_base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, column_property, aliased, declared_attr
from sqlalchemy import String, DECIMAL, Integer, Boolean, DateTime, select, and_, func, JSON, text
from datetime import datetime
from apps.vadmin.system.models.branch import Branch


class DishGroupType(BaseModel):
    __tablename__ = "dish_group_type"
    __table_args__ = ({'comment': '菜品组类型表'})
    
    name_unique: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="名称")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可用")


class DishGroup(BaseModel):
    __tablename__ = "dish_group"
    __table_args__ = ({'comment': '菜品组表'})
    
    name_unique: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="名称")
    name_display: Mapped[str | None] = mapped_column(String(255), comment="显示名称")
    name_english: Mapped[str | None] = mapped_column(String(255), comment="英文名称")
    dish_group_type_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="菜品组类型")
    stype: Mapped[int] = mapped_column(Integer, nullable=False, comment="类型 0/可选;2/必选")
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="门店")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可用")


class DishGroupDetail(BaseModel):
    __tablename__ = "dish_group_detail"
    __table_args__ = ({'comment': '菜品组详情表'})
    
    dish_group_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="菜品组")
    dish_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="菜品")
    additional_price: Mapped[float | None] = mapped_column(DECIMAL(12, 2), comment="加价")
    order_number: Mapped[int | None] = mapped_column(Integer, comment="排序号")
