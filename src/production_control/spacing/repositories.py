from ..data import Pagination
from ..data.repository import DremioRepository
from .models import WijderzetRegistratie


from sqlalchemy import Engine, Select, distinct, func, text
from sqlmodel import Session, select


from typing import List, Optional, Tuple


class SpacingRepository(DremioRepository[WijderzetRegistratie]):
    """Read-only repository for spacing data access."""

    # Fields to search when filtering spacing records
    search_fields = ["partij_code", "product_naam", "productgroep_naam"]

    def __init__(self, connection: Optional[Engine] = None):
        """Initialize repository with optional connection."""
        super().__init__(WijderzetRegistratie, connection)

    def _apply_default_sorting(self, query: Select) -> Select:
        """Apply default sorting to query."""
        return query.order_by(
            WijderzetRegistratie.datum_laatste_wdz.desc(),
            self.model.productgroep_naam,
            self.model.partij_code,
        )

    def get_paginated(
        self,
        page: int = 1,
        items_per_page: int = 10,
        sort_by: Optional[str] = None,
        descending: bool = False,
        filter_text: Optional[str] = None,
        pagination: Optional[Pagination] = None,
    ) -> Tuple[List[WijderzetRegistratie], int]:
        """Get paginated spacing records from the data source."""
        page, items_per_page, sort_by, descending = self._validate_pagination(
            page, items_per_page, sort_by, descending, pagination
        )

        with Session(self.engine) as session:
            # Create base queries
            base_query = select(WijderzetRegistratie).where(
                WijderzetRegistratie.datum_laatste_wdz.is_not(None)
            )
            count_stmt = select(func.count(distinct(WijderzetRegistratie.partij_code))).where(
                WijderzetRegistratie.datum_laatste_wdz.is_not(None)
            )

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

    def get_error_records(self) -> List[WijderzetRegistratie]:
        """Get all spacing records that have errors."""
        with Session(self.engine) as session:
            query = (
                select(WijderzetRegistratie)
                .where(WijderzetRegistratie.wijderzet_registratie_fout.is_not(None))
                .order_by(WijderzetRegistratie.productgroep_naam, self.model.partij_code)
            )
            return list(session.exec(query))

    def get_by_id(self, partij_code: str) -> Optional[WijderzetRegistratie]:
        """Get a spacing record by its partij_code."""
        with Session(self.engine) as session:
            # Using text() since Dremio Flight doesn't support parameterized queries
            return session.exec(
                select(WijderzetRegistratie).where(text(f"partij_code = '{partij_code}'"))
            ).first()

    def get_by_partij_code(self, partij_code: str) -> Optional[WijderzetRegistratie]:
        """Get a spacing record by its partij_code.
        
        This is an alias for get_by_id, since partij_code is our primary identifier.
        """
        return self.get_by_id(partij_code)
