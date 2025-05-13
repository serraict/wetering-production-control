"""Potting lots repositories."""

from typing import List, Optional, Tuple

from sqlalchemy import Engine, Select, distinct, func, text
from sqlmodel import Session, select

from ..data import Pagination
from ..data.repository import DremioRepository
from .models import PottingLot


class PottingLotRepository(DremioRepository[PottingLot]):
    """Repository for potting lot records."""

    # Fields to search when filtering potting lot records
    search_fields = [
        "id",
        "bollen_code",
        "naam",
        "oppot_datum",
        "opmerking",
        "product_groep",
        "klant_code",
        "oppot_week",
    ]

    def __init__(self, connection: Optional[Engine] = None):
        """Initialize repository with optional connection."""
        super().__init__(PottingLot, connection)

    def _apply_default_sorting(self, query: Select) -> Select:
        """Apply default sorting to query.

        Sort by oppot_datum (descending) and id as default.
        """
        return query.order_by(
            self.model.oppot_datum.desc(),
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
    ) -> Tuple[List[PottingLot], int]:
        """Get paginated potting lot records from the data source."""
        page, items_per_page, sort_by, descending = self._validate_pagination(
            page, items_per_page, sort_by, descending, pagination
        )

        with Session(self.engine) as session:
            # Create base queries
            base_query = select(PottingLot)
            count_stmt = select(func.count(distinct(PottingLot.id)))

            # Execute paginated query
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

    def get_by_id(self, id: int) -> Optional[PottingLot]:
        """Get a potting lot record by its id."""
        with Session(self.engine) as session:
            # Using text() since Dremio Flight doesn't support parameterized queries
            return session.exec(select(PottingLot).where(text(f"id = {id}"))).first()
