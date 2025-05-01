"""Repository for bulb picklist data access."""

from typing import List, Optional, Tuple

from sqlalchemy import Engine, Select, distinct, func, text
from sqlmodel import Session, select

from ..data import Pagination
from ..data.repository import DremioRepository
from .models import BulbPickList


class BulbPickListRepository(DremioRepository[BulbPickList]):
    """Read-only repository for bulb picklist data access."""

    # Fields to search when filtering bulb picklist records
    search_fields = ["bollen_code", "ras", "locatie"]

    def __init__(self, connection: Optional[Engine] = None):
        """Initialize repository with optional connection."""
        super().__init__(BulbPickList, connection)

    def _apply_default_sorting(self, query: Select) -> Select:
        """Apply default sorting to query.

        Sort by oppot_datum (descending) and location as specified in the requirements.
        """
        return query.order_by(
            self.model.oppot_datum.desc(),
            self.model.locatie,
        )

    def get_paginated(
        self,
        page: int = 1,
        items_per_page: int = 10,
        sort_by: Optional[str] = None,
        descending: bool = False,
        filter_text: Optional[str] = None,
        pagination: Optional[Pagination] = None,
    ) -> Tuple[List[BulbPickList], int]:
        """Get paginated bulb picklist records from the data source."""
        page, items_per_page, sort_by, descending = self._validate_pagination(
            page, items_per_page, sort_by, descending, pagination
        )

        with Session(self.engine) as session:
            # Create base queries
            base_query = select(BulbPickList)
            count_stmt = select(func.count(distinct(BulbPickList.bollen_code)))

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

    def get_by_id(self, bollen_code: int) -> Optional[BulbPickList]:
        """Get a bulb picklist record by its bollen_code."""
        with Session(self.engine) as session:
            # Using text() since Dremio Flight doesn't support parameterized queries
            return session.exec(
                select(BulbPickList).where(text(f"bollen_code = {bollen_code}"))
            ).first()
