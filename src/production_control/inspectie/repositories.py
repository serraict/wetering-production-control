"""Inspectie repository for data access."""

from datetime import date, timedelta
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
        """Apply default sorting to query.

        Sorts by min_baan first (to address position 2 vs 7 issue),
        then by datum_afleveren_plan, then by product_naam, then by code.
        """
        return query.order_by(
            self.model.min_baan,
            InspectieRonde.datum_afleveren_plan,
            self.model.product_naam,
            self.model.code,
        )

    def _apply_date_filter(
        self,
        query: Select,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        default_filter: Optional[str] = None,
    ) -> Select:
        """Apply date range filtering to query.

        Args:
            query: The base query to filter
            date_from: Start date for filtering
            date_to: End date for filtering
            default_filter: Named filter like 'next_two_weeks'

        Returns:
            Query with date filter applied
        """
        # Handle default filter presets
        if default_filter == "next_two_weeks":
            today = date.today()
            date_from = today - timedelta(days=7)  # 1 week before today
            date_to = today + timedelta(days=14)  # 2 weeks after today

        # Apply date range filtering if provided
        if date_from is not None:
            query = query.where(text(f"datum_afleveren_plan >= '{date_from}'"))

        if date_to is not None:
            query = query.where(text(f"datum_afleveren_plan <= '{date_to}'"))

        return query

    def get_paginated(
        self,
        page: int = 1,
        items_per_page: int = 10,
        sort_by: Optional[str] = None,
        descending: bool = False,
        filter_text: Optional[str] = None,
        pagination: Optional[Pagination] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        default_filter: Optional[str] = None,
    ) -> Tuple[List[InspectieRonde], int]:
        """Get paginated inspectie records from the data source."""
        page, items_per_page, sort_by, descending = self._validate_pagination(
            page, items_per_page, sort_by, descending, pagination
        )

        with Session(self.engine) as session:
            # Create base queries
            base_query = select(InspectieRonde)
            count_stmt = select(func.count(InspectieRonde.code))

            # Apply date filtering
            base_query = self._apply_date_filter(base_query, date_from, date_to, default_filter)
            count_stmt = self._apply_date_filter(count_stmt, date_from, date_to, default_filter)

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
