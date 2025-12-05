from pydantic import BaseModel, ConfigDict, Field, constr, conint
from core.data_types import DatetimeStr, DecimalType
from datetime import datetime
from typing import List, Annotated
from enum import Enum


class DishStatusEnum(int, Enum):
    NEW = -1
    DRAFT = 0
    UPLOADED = 1
    PUBLISHED = 2
    OUTOFSTOCK = 3
    TAKEDOWN = 9


class Dish(BaseModel):
    name_unique: Annotated[str, Field(max_length=10)]
    kitchen_id: int
    name_display: str
    name_english: str | None = None
    spec: str | None = None
    unit: str | None = None
    price: DecimalType = None
    time_on: DatetimeStr | None = None
    time_off: DatetimeStr | None = None
    order_number: int | None = None
    status: int
    description: str | None = None
    description_english: str | None = None


class DishIn(Dish):
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        validate_assignment=True)

    id: int | None = None
    dish_images: List[str] = Field(default_factory=list)


class DishOut(Dish):
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        validate_assignment=True)

    id: int | None = None
    create_datetime: DatetimeStr | None = None
    update_datetime: DatetimeStr | None = None

    dish_kitchen_name_unique: str = Field(None, alias="dish_kitchen_name_unique", title="所属厨部")

    dish_images: List[str] = Field(default_factory=list)
