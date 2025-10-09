"""Tests for Firebird API endpoints."""

from datetime import date
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from production_control.inspectie.commands import UpdateAfwijkingCommand
from production_control.firebird.api import update_afwijking, health_check


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint returns ok status."""
    response = await health_check()

    assert response == {"status": "ok", "service": "firebird-api"}


@pytest.mark.asyncio
@patch("production_control.firebird.api.execute_firebird_command")
async def test_update_afwijking_success(mock_execute):
    """Test successful afwijking update."""
    mock_execute.return_value = {"success": True, "message": "Command executed successfully"}

    command = UpdateAfwijkingCommand(code="24096", new_afwijking=10)
    response = await update_afwijking(command)

    assert response.success is True
    assert "24096" in response.message
    assert "10" in response.message
    assert response.error is None

    # Verify parameterized query was used
    mock_execute.assert_called_once_with(
        "UPDATE TEELTPL SET AFW_AFLEV = ? WHERE TEELTNR = ?", (10, "24096")
    )


@pytest.mark.asyncio
@patch("production_control.firebird.api.execute_firebird_command")
async def test_update_afwijking_database_error(mock_execute):
    """Test afwijking update with database error."""
    mock_execute.return_value = {"success": False, "error": "Database connection failed"}

    command = UpdateAfwijkingCommand(code="24096", new_afwijking=10)

    with pytest.raises(HTTPException) as exc_info:
        await update_afwijking(command)

    assert exc_info.value.status_code == 500
    assert "Database connection failed" in exc_info.value.detail


@pytest.mark.asyncio
@patch("production_control.firebird.api.execute_firebird_command")
async def test_update_afwijking_with_negative_value(mock_execute):
    """Test afwijking update with negative value."""
    mock_execute.return_value = {"success": True, "message": "Command executed successfully"}

    command = UpdateAfwijkingCommand(code="24097", new_afwijking=-5)
    response = await update_afwijking(command)

    assert response.success is True
    mock_execute.assert_called_once_with(
        "UPDATE TEELTPL SET AFW_AFLEV = ? WHERE TEELTNR = ?", (-5, "24097")
    )


@pytest.mark.asyncio
@patch("production_control.firebird.api.execute_firebird_command")
async def test_update_afwijking_with_zero(mock_execute):
    """Test afwijking update with zero value."""
    mock_execute.return_value = {"success": True, "message": "Command executed successfully"}

    command = UpdateAfwijkingCommand(code="24098", new_afwijking=0)
    response = await update_afwijking(command)

    assert response.success is True
    mock_execute.assert_called_once_with(
        "UPDATE TEELTPL SET AFW_AFLEV = ? WHERE TEELTNR = ?", (0, "24098")
    )


@pytest.mark.asyncio
@patch("production_control.firebird.api.execute_firebird_command")
async def test_update_afwijking_prevents_sql_injection(mock_execute):
    """Test that SQL injection attempts are prevented by parameterization."""
    mock_execute.return_value = {"success": True, "message": "Command executed successfully"}

    # Attempt SQL injection in code field
    malicious_code = "24096'; DROP TABLE TEELTPL; --"
    command = UpdateAfwijkingCommand(code=malicious_code, new_afwijking=10)
    response = await update_afwijking(command)

    # The malicious code should be treated as a literal string parameter
    assert response.success is True
    mock_execute.assert_called_once_with(
        "UPDATE TEELTPL SET AFW_AFLEV = ? WHERE TEELTNR = ?", (10, malicious_code)
    )


@pytest.mark.asyncio
@patch("production_control.firebird.api.execute_firebird_command")
async def test_update_afwijking_with_date(mock_execute):
    """Test afwijking update with delivery date."""
    mock_execute.return_value = {"success": True, "message": "Command executed successfully"}

    test_date = date(2025, 10, 15)
    command = UpdateAfwijkingCommand(code="24096", new_afwijking=10, new_datum_afleveren=test_date)
    response = await update_afwijking(command)

    assert response.success is True
    assert "24096" in response.message
    assert "2025-10-15" in response.message

    # Verify parameterized query updates both fields
    mock_execute.assert_called_once_with(
        "UPDATE TEELTPL SET AFW_AFLEV = ?, DAT_AFLEV_PLAN = ? WHERE TEELTNR = ?",
        (10, test_date, "24096"),
    )
