"""Command models for spacing operations."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
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
            for name, field in self.__class__.model_fields.items()
            if field.json_schema_extra and field.json_schema_extra.get("ui_editable", False)
        ]

    def get_readonly_fields(self) -> list[str]:
        """Get list of read-only field names."""
        return [
            name
            for name, field in self.__class__.model_fields.items()
            if not (field.json_schema_extra and field.json_schema_extra.get("ui_editable", False))
        ]


class FixMissingWdz2DateCommand(BaseModel):
    """Command to fix records with missing WDZ2 date but having table count."""

    # Record details
    partij_code: str = Field(..., description="Code van de partij")
    aantal_tafels_oppotten_plan: Decimal = Field(
        ..., description="Aantal tafels volgens oppot plan"
    )
    aantal_tafels_na_wdz1: int = Field(..., description="Aantal tafels na wijderzet 1")
    aantal_tafels_na_wdz2: Optional[int] = Field(None, description="Aantal tafels na wijderzet 2")

    @classmethod
    def from_record(cls, record: WijderzetRegistratie) -> "FixMissingWdz2DateCommand":
        """Create a command from a WijderzetRegistratie record."""
        return cls(
            partij_code=record.partij_code,
            aantal_tafels_oppotten_plan=record.aantal_tafels_oppotten_plan,
            aantal_tafels_na_wdz1=record.aantal_tafels_na_wdz1,
            aantal_tafels_na_wdz2=record.aantal_tafels_na_wdz2,
        )

    def can_fix_automatically(self) -> bool:
        """Check if the record can be fixed automatically.

        A record can be fixed automatically if:
        1. WDZ1 count equals rounded aantal_tafels_oppotten_plan
        2. WDZ2 count is present
        """
        if self.aantal_tafels_na_wdz2 is None:
            return False

        rounded_plan = int(
            self.aantal_tafels_oppotten_plan.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        if self.aantal_tafels_na_wdz1 == rounded_plan:
            return True

        if self.aantal_tafels_na_wdz1 == self.aantal_tafels_na_wdz2:
            return True

        return False

    def get_correction(self) -> Optional[CorrectSpacingRecord]:
        """Get correction command if the record can be fixed automatically."""
        if not self.can_fix_automatically():
            return None

        return CorrectSpacingRecord(
            partij_code=self.partij_code,
            aantal_tafels_na_wdz1=self.aantal_tafels_na_wdz2,  # Move WDZ2 count to WDZ1
            aantal_tafels_na_wdz2=0,  # Set WDZ2 count to 0 for API compatibility
            # Required fields for CorrectSpacingRecord
            product_naam="",  # Not needed for correction
            productgroep_naam="",  # Not needed for correction
            aantal_tafels_oppotten_plan=self.aantal_tafels_oppotten_plan,
            aantal_planten_gerealiseerd=0,  # Not needed for correction
            datum_oppotten_real=date.today(),  # Not needed for correction
        )
