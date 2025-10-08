"""FastAPI endpoints for Firebird database operations."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..inspectie.commands import UpdateAfwijkingCommand
from .connection import execute_firebird_command

router = APIRouter(prefix="/api/firebird", tags=["firebird"])


class ApiResponse(BaseModel):
    """Standard API response."""

    success: bool
    message: str | None = None
    error: str | None = None


@router.post("/update-afwijking", response_model=ApiResponse)
async def update_afwijking(command: UpdateAfwijkingCommand) -> ApiResponse:
    """Update afwijking_afleveren value in Firebird database.

    Args:
        command: UpdateAfwijkingCommand with code and new_afwijking value

    Returns:
        ApiResponse indicating success or failure

    Raises:
        HTTPException: If the update fails
    """
    # Build SQL UPDATE statement with parameterized query to prevent SQL injection
    # Note: VOLGNR is the primary key, code is stored in TEELTNR field
    sql = "UPDATE TEELTPL SET AFW_AFLEV = ? WHERE TEELTNR = ?"
    params = (command.new_afwijking, command.code)

    result = execute_firebird_command(sql, params)

    if result["success"]:
        return ApiResponse(
            success=True,
            message=f"Updated afwijking for code {command.code} to {command.new_afwijking}",
        )
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "firebird-api"}
