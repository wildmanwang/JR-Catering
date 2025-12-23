from db.db_base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean


class Company(BaseModel):
    __tablename__ = "company"
    __table_args__ = ({'comment': '公司'})

    name_unique: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="名称")
    busi_type: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="0:总部;1:分公司")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可用")


class Branch(BaseModel):
    __tablename__ = "branch"
    __table_args__ = ({'comment': '店铺'})

    name_unique: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="名称")
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="所属公司")
    web_site: Mapped[str] = mapped_column(String(255), nullable=True, comment="主页")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可用")
