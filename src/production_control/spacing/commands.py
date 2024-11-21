"""Command models for spacing operations."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from .models import WijderzetRegistratie


class CorrectSpacingRecord(BaseModel):
    """Command to correct the number of tables after spacing operations."""

    # Editable fields
    aantal_tafels_na_wdz1: Optional[int] = Field(
        None,
        description="Aantal tafels na wijderzet 1",
        json_schema_extra={"ui_editable": True, "minimum": 0},
    )
    aantal_tafels_na_wdz2: Optional[int] = Field(
        None,
        description="Aantal tafels na wijderzet 2",
        json_schema_extra={"ui_editable": True, "minimum": 0},
    )

    # Read-only fields
    partij_code: str = Field(..., description="Code van de partij")
    product_naam: str = Field(..., description="Naam van het product")
    productgroep_naam: str = Field(..., description="Naam van de productgroep")
    aantal_tafels_oppotten_plan: Decimal = Field(
        ..., description="Aantal tafels volgens oppot plan"
    )
    aantal_planten_gerealiseerd: int = Field(..., description="Aantal gerealiseerde planten")
    datum_oppotten_real: date = Field(..., description="Datum van oppotten")
    datum_wdz1_real: Optional[date] = Field(None, description="Datum van wijderzet 1")
    datum_wdz2_real: Optional[date] = Field(None, description="Datum van wijderzet 2")

    @classmethod
    def from_record(cls, record: WijderzetRegistratie) -> "CorrectSpacingRecord":
        """Create a command from a WijderzetRegistratie record."""
        return cls(
            partij_code=record.partij_code,
            product_naam=record.product_naam,
            productgroep_naam=record.productgroep_naam,
            aantal_tafels_oppotten_plan=record.aantal_tafels_oppotten_plan,
            aantal_planten_gerealiseerd=record.aantal_planten_gerealiseerd,
            datum_oppotten_real=record.datum_oppotten_real,
            datum_wdz1_real=record.datum_wdz1_real,
            datum_wdz2_real=record.datum_wdz2_real,
            aantal_tafels_na_wdz1=record.aantal_tafels_na_wdz1,
            aantal_tafels_na_wdz2=record.aantal_tafels_na_wdz2,
        )

    def get_editable_fields(self) -> list[str]:
        """Get list of editable field names."""
        return [
            name
            for name, field in self.model_fields.items()
            if field.json_schema_extra and field.json_schema_extra.get("ui_editable", False)
        ]

    def get_readonly_fields(self) -> list[str]:
        """Get list of read-only field names."""
        return [
            name
            for name, field in self.model_fields.items()
            if not (field.json_schema_extra and field.json_schema_extra.get("ui_editable", False))
        ]
