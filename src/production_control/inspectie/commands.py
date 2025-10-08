"""Commands for inspectie operations."""

from pydantic import BaseModel, Field, field_validator


class UpdateAfwijkingCommand(BaseModel):
    """Command to update the afwijking_afleveren for an inspectieronde."""

    code: str = Field(..., min_length=1, description="The unique code of the inspectieronde")
    new_afwijking: int = Field(
        ..., description="The new afwijking value (can be positive, negative, or zero)"
    )

    @field_validator("code")
    @classmethod
    def code_must_not_be_empty(cls, v):
        """Validate that code is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Code must not be empty")
        return v.strip()
