"""Command models for spacing operations."""

from typing import Optional
from pydantic import BaseModel, model_validator, Field

from .models import WijderzetRegistratie


class CorrectSpacingRecord(BaseModel):
    """Command to correct the number of tables after spacing operations."""

    partij_code: str = Field(..., description="Code van de partij")
    aantal_tafels_na_wdz1: Optional[int] = Field(
        None,
        description="Aantal tafels na wijderzet 1",
        gt=0,
    )
    aantal_tafels_na_wdz2: Optional[int] = Field(
        None,
        description="Aantal tafels na wijderzet 2",
    )

    @model_validator(mode="after")
    def validate_wz2_after_wz1(self) -> "CorrectSpacingRecord":
        """Validate that WZ2 is only set if WZ1 is set and is greater than WZ1."""
        wz1 = self.aantal_tafels_na_wdz1
        wz2 = self.aantal_tafels_na_wdz2

        if wz2 is not None:
            if wz1 is None:
                msg = "Aantal tafels na WZ2 kan niet ingevuld worden als WZ1 leeg is"
                raise ValueError(msg)
            if wz2 <= wz1:
                msg = "Aantal tafels na WZ2 moet groter zijn dan aantal tafels na WZ1"
                raise ValueError(msg)

        return self

    @classmethod
    def from_record(cls, record: WijderzetRegistratie) -> "CorrectSpacingRecord":
        """Create a command from a WijderzetRegistratie record."""
        return cls(
            partij_code=record.partij_code,
            aantal_tafels_na_wdz1=record.aantal_tafels_na_wdz1,
            aantal_tafels_na_wdz2=record.aantal_tafels_na_wdz2,
        )
