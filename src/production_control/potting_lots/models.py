"""Potting lots data models."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class PottingLot(SQLModel, table=True):
    """Model representing a potting lot record from oppotlijst table."""

    __tablename__ = "oppotlijst"
    __table_args__ = {"schema": "Productie.Oppotten"}

    # Primary key
    id: int = Field(
        primary_key=True,
        title="ID",
        description="The potting lot identifier",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    # Basic info
    naam: str = Field(
        title="Artikel",
        description="The plant variety name",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    bollen_code: int = Field(
        title="Bollen Code",
        description="The bulb code",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    oppot_datum: Optional[date] = Field(
        default=None,
        title="Oppot Datum",
        description="The planting date",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    # Additional fields (some hidden in list view but all shown in detail view)
    productgroep_code: Optional[int] = Field(
        default=None,
        title="Productgroep Code",
        description="The product group code",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    bolmaat: Optional[float] = Field(
        default=None,
        title="Bolmaat",
        description="The bulb size",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    bol_per_pot: Optional[float] = Field(
        default=None,
        title="Bollen per Pot",
        description="Number of bulbs per pot",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    rij_cont: Optional[int] = Field(
        default=None,
        title="Rijen per Container",
        description="Rows per container",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    olsthoorn_bollen_code: Optional[str] = Field(
        default=None,
        title="Olsthoorn Bollen Code",
        description="Olsthoorn bulb code",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    aantal_pot: Optional[int] = Field(
        default=None,
        title="Aantal Potten",
        description="Number of pots",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    aantal_bol: Optional[int] = Field(
        default=None,
        title="Aantal Bollen",
        description="Number of bulbs",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    aantal_containers_oppotten: Optional[Decimal] = Field(
        default=None,
        title="Aantal Containers",
        description="Number of containers",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    water: Optional[str] = Field(
        default=None,
        title="Water",
        description="Water information",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    fust: Optional[str] = Field(
        default=None,
        title="Fust",
        description="Container type",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    opmerking: Optional[str] = Field(
        default=None,
        title="Opmerking",
        description="Remarks",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    # New fields found in the database
    product_groep: Optional[str] = Field(
        default=None,
        title="Product Groep",
        description="Product group",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": False}},
    )

    klant_code: Optional[str] = Field(
        default=None,
        title="Klant Code",
        description="Customer code",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": False}},
    )

    oppot_week: Optional[str] = Field(
        default=None,
        title="Oppotweek",
        description="Week van oppotten",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )
