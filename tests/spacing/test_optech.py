"""Tests for the OpTech API client."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

import httpx
import pytest

from production_control.spacing.commands import CorrectSpacingRecord
from production_control.spacing.optech import (
    CorrectionResponse,
    OpTechClient,
    OpTechConnectionError,
    OpTechResponseError,
)


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up test environment variables."""
    monkeypatch.setenv("VINEAPP_OPTECH_API_URL", "http://optech.test")


@pytest.fixture
def test_command() -> CorrectSpacingRecord:
    """Create a test correction command."""
    return CorrectSpacingRecord(
        partij_code="TEST123",
        product_naam="Test Plant",
        productgroep_naam="Test Group",
        aantal_tafels_oppotten_plan=Decimal("10.0"),
        aantal_planten_gerealiseerd=100,
        datum_oppotten_real=date(2024, 1, 1),
        datum_wdz1_real=date(2024, 1, 15),
        datum_wdz2_real=None,
        aantal_tafels_na_wdz1=15,
        aantal_tafels_na_wdz2=None,
    )


def test_client_requires_base_url() -> None:
    """Test that client requires VINEAPP_OPTECH_API_URL to be set."""
    with pytest.raises(ValueError, match="VINEAPP_OPTECH_API_URL.*not set"):
        OpTechClient()


def test_client_validates_url_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that client validates URL format."""
    monkeypatch.setenv("VINEAPP_OPTECH_API_URL", "invalid-url")
    with pytest.raises(ValueError, match="Invalid VINEAPP_OPTECH_API_URL"):
        OpTechClient()


def test_send_correction_success(
    mock_env: None,
    test_command: CorrectSpacingRecord,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test successful spacing correction."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"

    mock_http_client = MagicMock()
    mock_http_client.put.return_value = mock_response

    mock_client_class = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_http_client
    mock_client_class.return_value.__exit__.return_value = None

    with patch("httpx.Client", return_value=mock_client_class.return_value):
        client = OpTechClient()
        result = client.send_correction(test_command)

        assert isinstance(result, CorrectionResponse)
        assert result.success is True
        assert "Successfully updated" in result.message
        assert test_command.partij_code in result.message

        # Verify API call uses the correct field names
        mock_http_client.put.assert_called_once_with(
            "http://optech.test/api/partij/TEST123/wijderzet",
            json={
                "aantal_wijderzet_1": test_command.aantal_tafels_na_wdz1,
                "aantal_wijderzet_2": test_command.aantal_tafels_na_wdz2,
            },
            timeout=25.0,
        )


def test_send_correction_api_error(
    mock_env: None,
    test_command: CorrectSpacingRecord,
) -> None:
    """Test handling of API error responses."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Invalid data"
    mock_response.json.return_value = {"detail": "Invalid data"}

    mock_http_client = MagicMock()
    mock_http_client.put.return_value = mock_response

    mock_client_class = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_http_client
    mock_client_class.return_value.__exit__.return_value = None

    with patch("httpx.Client", return_value=mock_client_class.return_value):
        client = OpTechClient()
        with pytest.raises(OpTechResponseError) as exc_info:
            client.send_correction(test_command)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid data"


def test_send_correction_connection_error(
    mock_env: None,
    test_command: CorrectSpacingRecord,
) -> None:
    """Test handling of connection errors."""
    mock_http_client = MagicMock()
    mock_http_client.put.side_effect = httpx.RequestError("Connection failed")

    mock_client_class = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_http_client
    mock_client_class.return_value.__exit__.return_value = None

    with patch("httpx.Client", return_value=mock_client_class.return_value):
        client = OpTechClient()
        with pytest.raises(OpTechConnectionError) as exc_info:
            client.send_correction(test_command)

        assert "Failed to connect to OpTech API" in str(exc_info.value)
        assert "Connection failed" in str(exc_info.value)
        assert "Please verify the VINEAPP_OPTECH_API_URL configuration" in str(exc_info.value)
        assert "http://optech.test/api/partij/TEST123/wijderzet" in str(exc_info.value)


def test_send_correction_timeout(
    mock_env: None,
    test_command: CorrectSpacingRecord,
) -> None:
    """Test handling of timeout errors."""
    mock_http_client = MagicMock()
    mock_http_client.put.side_effect = httpx.ReadTimeout("Request timed out")

    mock_client_class = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_http_client
    mock_client_class.return_value.__exit__.return_value = None

    with patch("httpx.Client", return_value=mock_client_class.return_value):
        client = OpTechClient()
        with pytest.raises(OpTechConnectionError) as exc_info:
            client.send_correction(test_command)

        assert "Failed to connect to OpTech API" in str(exc_info.value)
        assert "Request timed out" in str(exc_info.value)
        assert "Please verify the VINEAPP_OPTECH_API_URL configuration" in str(exc_info.value)
        assert "http://optech.test/api/partij/TEST123/wijderzet" in str(exc_info.value)
