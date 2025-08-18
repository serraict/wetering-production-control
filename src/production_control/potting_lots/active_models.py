"""Active potting lot models."""

from pydantic import BaseModel, field_validator

from .models import PottingLot


class ActivePottingLot(BaseModel):
    """Runtime state for tracking active potting lots per line."""

    line: int  # Potting line number (1 or 2)
    potting_lot_id: int  # ID of the active potting lot
    potting_lot: PottingLot  # Full potting lot details for display

    @field_validator("line")
    @classmethod
    def validate_line(cls, v: int) -> int:
        """Validate that line number is 1 or 2."""
        if v not in [1, 2]:
            raise ValueError("Line must be 1 or 2")
        return v
