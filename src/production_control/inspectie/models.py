"""Inspectieronde data models."""

from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class InspectieRonde(SQLModel, table=True):
    """Model representing an inspection round record from inspectie_ronde view."""

    __tablename__ = "inspectie_ronde"
    __table_args__ = {"schema": "Verkoop"}

    # Primary key - using code as the main identifier
    code: str = Field(
        primary_key=True,
        title="Code",
        description="Code van de inspectieronde",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    locatie_samenvatting: Optional[str] = Field(
        default=None,
        title="Locatie",
        description="Samenvatting van locaties",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    baan_samenvatting: Optional[str] = Field(
        default=None,
        title="banen",
        description="Samenvatting van banen",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    klant_code: Optional[str] = Field(
        default=None,
        title="klant",
        description="Code van de klant",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    bollen_code: Optional[str] = Field(
        default=None,
        title="Bollen",
        description="Code van de bollen",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    product_naam: Optional[str] = Field(
        default=None,
        title="product",
        description="Naam van het product",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    product_groep_naam: Optional[str] = Field(
        default=None,
        title="product_groep_naam",
        description="Naam van de productgroep",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    datum_afleveren_plan: Optional[date] = Field(
        default=None,
        title="datum",
        description="Geplande afleverdatum",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    aantal_in_kas: Optional[int] = Field(
        default=None,
        title="#plt",
        description="Aantal in kas",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    aantal_tafels: Optional[int] = Field(
        default=None,
        title="#cont",
        description="Aantal tafels",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    min_baan: Optional[int] = Field(
        default=None,
        title="1e baan",
        description="Minimum baan nummer",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    afwijking_afleveren: Optional[int] = Field(
        default=None,
        title="afw.",
        description="Afwijking in dagen voor aflevering",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    productgroep_code: Optional[int] = Field(
        default=None,
        title="PG Code",
        description="Code van de productgroep",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    def __str__(self) -> str:
        """Format record as string with code and product name."""
        if self.product_naam:
            return f"{self.code} - {self.product_naam}"
        return self.code
