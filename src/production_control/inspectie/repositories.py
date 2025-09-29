"""Inspectie repository for data access."""

from typing import List, Optional, Tuple, Union

from sqlalchemy import Engine, Select, func, text
from sqlmodel import Session, select

from ..data import Pagination
from ..data.repository import DremioRepository
from .models import InspectieRonde


class InspectieRepository(DremioRepository[InspectieRonde]):
    """Repository for accessing inspectie ronde data from Dremio."""

    # Fields to search when filtering inspectie records
    search_fields = ["code", "product_naam", "product_groep_naam", "klant_code"]

    def __init__(self, connection: Optional[Union[str, Engine]] = None):
        """Initialize the repository with InspectieRonde model."""
        super().__init__(InspectieRonde, connection)

    def _apply_default_sorting(self, query: Select) -> Select:
        """Apply default sorting to query."""
        return query.order_by(
            InspectieRonde.datum_afleveren_plan,
            self.model.product_naam,
            self.model.code,
        )

    def get_paginated(
        self,
        page: int = 1,
        items_per_page: int = 10,
        sort_by: Optional[str] = None,
        descending: bool = False,
        filter_text: Optional[str] = None,
        pagination: Optional[Pagination] = None,
    ) -> Tuple[List[InspectieRonde], int]:
        """Get paginated inspectie records from the data source."""
        page, items_per_page, sort_by, descending = self._validate_pagination(
            page, items_per_page, sort_by, descending, pagination
        )

        with Session(self.engine) as session:
            # Create base queries
            base_query = select(InspectieRonde)
            count_stmt = select(func.count(InspectieRonde.code))

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

    def get_by_id(self, code: str) -> Optional[InspectieRonde]:
        """Get an inspectie record by its code."""
        with Session(self.engine) as session:
            # Using text() since Dremio Flight doesn't support parameterized queries
            return session.exec(select(InspectieRonde).where(text(f"code = '{code}'"))).first()
