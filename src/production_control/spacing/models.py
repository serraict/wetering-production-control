"""Spacing data models."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, distinct, Select, Engine
from sqlmodel import Field, Session, SQLModel, select

from ..data import Pagination
from ..data.repository import DremioRepository


class WijderzetRegistratie(SQLModel, table=True):
    """Model representing a spacing record from registratie_controle view."""

    __tablename__ = "registratie_controle"
    __table_args__ = {"schema": "Productie.Controle"}

    # Primary key
    id: UUID = Field(
        primary_key=True,
        title="ID",
        sa_column_kwargs={"info": {"ui_hidden": True}},
    )

    # Batch information
    partij_code: str = Field(
        title="Partij",
        description="Code van de partij",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 1}},
    )
    product_naam: str = Field(
        title="Product",
        description="Naam van het product",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 2}},
    )
    productgroep_naam: str = Field(
        title="Productgroep",
        description="Naam van de productgroep",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 3}},
    )

    # Realization dates
    datum_oppotten_real: Optional[date] = Field(
        default=None,
        title="Oppotdatum",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 4}},
    )
    datum_uit_cel_real: Optional[date] = Field(
        default=None,
        title="Uit cel",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 5}},
    )
    datum_wdz1_real: Optional[date] = Field(
        default=None,
        title="Wijderzet 1",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 6}},
    )
    datum_wdz2_real: Optional[date] = Field(
        default=None,
        title="Wijderzet 2",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 7}},
    )

    # Plant amounts
    aantal_planten_gerealiseerd: int = Field(
        title="Planten",
        description="Aantal gerealiseerde planten",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 8}},
    )

    # Table amounts
    aantal_tafels_totaal: int = Field(
        title="Tafels totaal",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 9}},
    )
    aantal_tafels_na_wdz1: int = Field(
        title="Tafels na WZ1",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 10}},
    )
    aantal_tafels_na_wdz2: int = Field(
        title="Tafels na WZ2",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 11}},
    )
    aantal_tafels_oppotten_plan: Decimal = Field(
        title="Tafels plan",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 12}},
    )

    # Density information
    dichtheid_oppotten_plan: int = Field(
        title="Dichtheid oppotten",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 13}},
    )
    dichtheid_wz1_plan: int = Field(
        title="Dichtheid WZ1",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 14}},
    )
    dichtheid_wz2_plan: Optional[float] = Field(
        default=None,
        title="Dichtheid WZ2",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 15}},
    )

    # Error tracking
    wijderzet_registratie_fout: Optional[str] = Field(
        default=None,
        title="Fout",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 16}},
    )

    def __str__(self) -> str:
        """Format record as string with batch code and potting date."""
        if self.datum_oppotten_real:
            date_str = self.datum_oppotten_real.strftime("%yw%V-%u").replace("y", "")
            return f"{self.partij_code} ({date_str})"
        return self.partij_code


class SpacingRepository(DremioRepository[WijderzetRegistratie]):
    """Read-only repository for spacing data access."""

    # Fields to search when filtering spacing records
    search_fields = ["partij_code", "product_naam", "productgroep_naam"]

    def __init__(self, connection: Optional[Engine] = None):
        """Initialize repository with optional connection."""
        super().__init__(WijderzetRegistratie, connection)

    def _apply_default_sorting(self, query: Select) -> Select:
        """Apply default sorting to query."""
        return query.order_by(self.model.productgroep_naam, self.model.partij_code)

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
            base_query = select(WijderzetRegistratie)
            count_stmt = select(func.count(distinct(WijderzetRegistratie.id)))

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
                .order_by(WijderzetRegistratie.productgroep_naam, WijderzetRegistratie.partij_code)
            )
            return list(session.exec(query))
