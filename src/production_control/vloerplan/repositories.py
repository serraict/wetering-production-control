"""Vloerplan repositories."""

from typing import List, Optional, Tuple, Union

from sqlalchemy import Engine, Select, func, text
from sqlmodel import Session, select

from ..data import Pagination
from ..data.repository import DremioRepository
from .models import Vloerplan19cm


class Vloerplan19cmRepository(DremioRepository[Vloerplan19cm]):
    """Repository for vloerplan 19cm records."""

    search_fields = [
        "id",
        "product_naam",
        "productgroep_naam",
        "klant_code",
        "opmerking",
    ]

    def __init__(self, connection: Optional[Union[str, Engine]] = None):
        super().__init__(Vloerplan19cm, connection)

    def _apply_default_sorting(self, query: Select) -> Select:
        return query.order_by(
            self.model.datum_uit_cel_plan_opm.desc(),
            self.model.id,
        )

    def get_paginated(
        self,
        page: int = 1,
        items_per_page: int = 10,
        sort_by: Optional[str] = None,
        descending: bool = False,
        filter_text: Optional[str] = None,
        pagination: Optional[Pagination] = None,
    ) -> Tuple[List[Vloerplan19cm], int]:
        page, items_per_page, sort_by, descending = self._validate_pagination(
            page, items_per_page, sort_by, descending, pagination
        )

        with Session(self.engine) as session:
            base_query = select(Vloerplan19cm)
            count_stmt = select(func.count(Vloerplan19cm.id))

            return self._execute_paginated_query(
                session,
                base_query,
                count_stmt,
                page,
                items_per_page,
                filter_text,
                self.search_fields,
                sort_by,
                descending,
            )

    def get_by_id(self, id: int) -> Optional[Vloerplan19cm]:
        with Session(self.engine) as session:
            # text() because Dremio Flight doesn't support parameterized queries
            return session.exec(
                select(Vloerplan19cm).where(text(f"id = {id}"))
            ).first()
