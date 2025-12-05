from fastapi import Depends, Query
from core.dependencies import Paging, QueryParams


class DishParams(QueryParams):
    def __init__(
            self,
            kitchen_id: int | None = Query(None, title="厨部"),
            status: int | None = Query(None, title="状态"),
            name_unique: str | None = Query(None, title="名称"),
            name_display: str | None = Query(None, title="显示名称"),
            name_english: str | None = Query(None, title="英文名称"),
            fuzzy_query_str: str | None = Query(None, title="模糊查询"),
            params: Paging = Depends()
    ):
        super().__init__(params)
        self.kitchen_id = kitchen_id
        self.status = status
        self.name_unique = ("like", name_unique)
        self.name_display = ("like", name_display)
        self.name_english = ("like", name_english)
        # fuzzy_query_str 不在这里处理，由 crud.get_datas() 统一处理
        self.fuzzy_query_str = fuzzy_query_str
