"""Spacing data models."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from pydantic import computed_field
from sqlmodel import Field, SQLModel


class WijderzetRegistratie(SQLModel, table=True):
    """Model representing a spacing record from registratie_controle view."""

    __tablename__ = "registratie_controle"
    __table_args__ = {"schema": "Productie.Controle"}

    # Primary key
    partij_code: str = Field(
        primary_key=True,
        title="Partij",
        description="Code van de partij",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    product_naam: str = Field(
        title="Product",
        description="Naam van het product",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    # Plant amounts
    aantal_planten_gerealiseerd: int = Field(
        title="Planten",
        description="Aantal gerealiseerde planten",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    # Table amounts
    aantal_tafels_oppotten_plan: Decimal = Field(
        title="#oppepot",
        sa_column_kwargs={"info": {"ui_sortable": True, "decimals": 1}},
    )
    aantal_tafels_na_wdz1: int = Field(
        title="#WZ1",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )
    aantal_tafels_na_wdz2: int = Field(
        title="#WZ2",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )
    aantal_tafels_totaal: int = Field(
        title="#Nu",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    # Important dates
    datum_wdz1_real: Optional[date] = Field(
        default=None,
        title="Wijderzet 1",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )
    datum_wdz2_real: Optional[date] = Field(
        default=None,
        title="Wijderzet 2",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )
    datum_oppotten_real: Optional[date] = Field(
        default=None,
        title="Oppotdatum",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    # Hidden fields
    productgroep_naam: str = Field(
        title="Productgroep",
        description="Naam van de productgroep",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )
    datum_laatste_wdz: Optional[date] = Field(
        default=None,
        title="Laatste wijderzet",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )
    datum_uit_cel_real: Optional[date] = Field(
        default=None,
        title="Uit cel",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )
    dichtheid_oppotten_plan: int = Field(
        title="Dichtheid oppotten",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )
    dichtheid_wz1_plan: int = Field(
        title="Dichtheid WZ1",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )
    dichtheid_wz2_plan: Optional[float] = Field(
        default=None,
        title="Dichtheid WZ2",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )
    wijderzet_registratie_fout: Optional[str] = Field(
        default=None,
        title="Fout",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    # Calculated fields
    @computed_field(return_type=Optional[str])
    @property
    def warning_emoji(self) -> str:
        """Return a warning emoji if there's an error, empty string otherwise."""
        return "⚠️" if self.wijderzet_registratie_fout else ""

    @computed_field(return_type=int)
    @property
    def rounded_aantal_tafels_oppotten_plan(self) -> int:
        """Return the rounded number of tables from the plan."""
        return int(self.aantal_tafels_oppotten_plan.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def __str__(self) -> str:
        """Format record as string with batch code and potting date."""
        if self.datum_oppotten_real:
            date_str = self.datum_oppotten_real.strftime("%gw%V-%u")
            return f"{self.partij_code} ({date_str})"
        return self.partij_code
