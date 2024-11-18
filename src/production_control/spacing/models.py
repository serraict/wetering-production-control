"""Spacing data models."""

import os
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy import (
    Engine,
    func,
    Integer,
    bindparam,
    text,
    distinct,
    desc,
    create_engine,
    nulls_last,
)
from sqlmodel import Field, Session, SQLModel, select


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
    wijderzet_registratie_fout: Optional[bool] = Field(
        default=None,
        title="Fout",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 16}},
    )


class SpacingRepository:
    """Read-only repository for spacing data access."""

    def __init__(self, connection: Optional[Union[str, Engine]] = None):
        """Initialize repository with optional connection string or engine."""
        if isinstance(connection, Engine):
            self.engine = connection
        else:
            conn_str = os.getenv("VINEAPP_DB_CONNECTION", "dremio+flight://localhost:32010/dremio")
            self.engine = create_engine(conn_str)

    def get_paginated(
        self,
        page: int = 1,
        items_per_page: int = 10,
        sort_by: Optional[str] = None,
        descending: bool = False,
        filter_text: Optional[str] = None,
    ) -> Tuple[List[WijderzetRegistratie], int]:
        """Get paginated spacing records from the data source.

        Args:
            page: The page number (1-based)
            items_per_page: Number of items per page
            sort_by: Column name to sort by
            descending: Sort in descending order if True
            filter_text: Optional text to filter records by (case-insensitive)

        Returns:
            Tuple containing list of spacing records for the requested page and total count
        """
        with Session(self.engine) as session:
            # Create base query
            base_query = select(WijderzetRegistratie)

            # Apply filter if provided
            if filter_text:
                # Note: Using string interpolation because Dremio Flight doesn't support parameters
                pattern = f"%{filter_text}%"
                filter_expr = text(
                    f"lower(partij_code) LIKE lower('{pattern}') OR "
                    f"lower(product_naam) LIKE lower('{pattern}') OR "
                    f"lower(productgroep_naam) LIKE lower('{pattern}')"
                )
                base_query = base_query.where(filter_expr)

            # Get total count using the same filter
            count_stmt = select(func.count(distinct(WijderzetRegistratie.id)))
            if filter_text:
                count_stmt = count_stmt.where(filter_expr)
            total = session.exec(count_stmt).one()

            # Calculate offset
            offset = (page - 1) * items_per_page

            # Apply sorting
            if sort_by:
                column = getattr(WijderzetRegistratie, sort_by)
                if descending:
                    base_query = base_query.order_by(nulls_last(desc(column)))
                else:
                    base_query = base_query.order_by(nulls_last(column))
            else:
                # Default sorting
                base_query = base_query.order_by(
                    WijderzetRegistratie.productgroep_naam, WijderzetRegistratie.partij_code
                )

            # Apply pagination
            query = base_query.limit(
                bindparam("limit", type_=Integer, literal_execute=True)
            ).offset(bindparam("offset", type_=Integer, literal_execute=True))

            # Execute with bound parameters
            result = session.exec(
                query,
                params={
                    "limit": items_per_page,
                    "offset": offset,
                },
            )
            registraties = list(result)

            return registraties, total
