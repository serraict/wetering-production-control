"""Vloerplan data models."""

from datetime import date
from math import isnan
from typing import Optional

from sqlalchemy import Column, Integer
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, SQLModel

from ..data.repository import DateFromTimestamp


class _IntFromDouble(TypeDecorator):
    """Reads a Dremio DOUBLE column and returns Python int (NaN -> None)."""

    impl = Integer
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, float) and isnan(value):
            return None
        return int(value)


class Vloerplan19cm(SQLModel, table=True):
    """Model representing a vloerplan record for 19cm pots from vloerplan_19cm view."""

    __tablename__ = "vloerplan_19cm"
    __table_args__ = {"schema": "Productie.Plan"}

    id: int = Field(
        primary_key=True,
        title="ID",
        description="Regel identifier",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    product_naam: Optional[str] = Field(
        default=None,
        title="Product",
        description="Productnaam",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    productgroep_naam: Optional[str] = Field(
        default=None,
        title="Productgroep",
        description="Productgroepnaam",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    klant_code: Optional[str] = Field(
        default=None,
        title="Klant",
        description="Klantcode",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    tuin_nr_plan: Optional[int] = Field(
        default=None,
        title="Tuin plan",
        description="Geplande tuin",
        sa_column=Column("tuin_nr_plan", _IntFromDouble(), info={"ui_sortable": True}),
    )

    tuin_nr_olsthoorn: Optional[int] = Field(
        default=None,
        title="Tuin Olsthoorn",
        description="Tuinnummer Olsthoorn",
        sa_column=Column("tuin_nr_olsthoorn", _IntFromDouble(), info={"ui_sortable": True}),
    )

    datum_oppot_plan: Optional[date] = Field(
        default=None,
        title="Oppotdatum",
        description="Geplande oppotdatum",
        sa_column=Column("datum_oppot_plan", DateFromTimestamp(), info={"ui_sortable": True}),
    )

    datum_uit_cel_plan_opm: Optional[date] = Field(
        default=None,
        title="Uit Cel",
        description="Geplande datum uit cel",
        sa_column=Column("datum_uit_cel_plan_opm", DateFromTimestamp(), info={"ui_sortable": True}),
    )

    opmerking: Optional[str] = Field(
        default=None,
        title="Opmerking",
        description="Opmerking",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )
