"""Bulb picklist data models."""

import math
from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class BulbPickList(SQLModel, table=True):
    """Model representing a bulb pick list record from bollen_pick_lijst table."""

    __tablename__ = "bollen_pick_lijst"
    __table_args__ = {"schema": "Productie.Oppotten"}

    id: int = Field(
        primary_key=True,
        title="ID",
        description="The potting lot identifier",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    bollen_code: int = Field(
        title="Bollen Code",
        description="The bulb code",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    # Basic fields
    ras: str = Field(
        title="Ras",
        description="The bulb variety name",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    locatie: str = Field(
        title="Locatie",
        description="The storage location",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    aantal_bakken: float = Field(
        title="Aantal Bakken",
        description="Number of trays",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    aantal_bollen: float = Field(
        title="Aantal Bollen",
        description="Number of bulbs",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    oppot_datum: Optional[date] = Field(
        default=None,
        title="Oppot Datum",
        description="The planting date",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    oppot_week: Optional[str] = Field(
        default=None,
        title="Oppot Week",
        description="The planting week",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    @property
    def pallet_count(self) -> int:
        """
        Calculate the number of pallets needed for the boxes.

        Each pallet can hold a maximum of 25 boxes.
        Returns 0 if aantal_bakken is 0 or negative.

        Returns:
            int: Number of pallets needed
        """
        if self.aantal_bakken <= 0:
            return 0
        return math.ceil(self.aantal_bakken / 25)
