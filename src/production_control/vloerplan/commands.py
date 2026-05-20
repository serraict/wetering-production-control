"""Commands for vloerplan operations."""

from pydantic import BaseModel, Field


class UpdateTuinNrCommand(BaseModel):
    """Command to overwrite TEELTPL.TUINNUMMER with the planned tuin number."""

    teeltnr: int = Field(..., description="TEELTPL.TEELTNR (equals vloerplan_19cm.id)")
    new_tuinnummer: int = Field(..., gt=0, description="The planned tuin number to write")
