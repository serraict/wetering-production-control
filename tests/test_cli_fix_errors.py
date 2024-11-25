"""Tests for CLI fix-spacing-errors command."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

import pytest
from typer.testing import CliRunner

from production_control.__cli__ import app
from production_control.spacing.models import WijderzetRegistratie
from production_control.spacing.optech import OpTechError, CorrectionResponse


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_records():
    """Create mock spacing records with various error types."""
    return [
        # Type 1 error - can fix automatically
        WijderzetRegistratie(
            partij_code="TEST-001",
            product_naam="Test Plant 1",
            productgroep_naam="Test Group",
            aantal_tafels_oppotten_plan=Decimal("10.0"),
            aantal_tafels_na_wdz1=10,  # Matches rounded plan
            aantal_tafels_na_wdz2=20,
            datum_oppotten_real=date(2024, 1, 1),
            wijderzet_registratie_fout="Geen wdz2 datum maar wel tafel aantal na wdz 2",
            aantal_planten_gerealiseerd=1000,
            rounded_aantal_tafels_oppotten_plan=10,
        ),
        # Type 1 error - needs manual review
        WijderzetRegistratie(
            partij_code="TEST-002",
            product_naam="Test Plant 2",
            productgroep_naam="Test Group",
            aantal_tafels_oppotten_plan=Decimal("10.0"),
            aantal_tafels_na_wdz1=15,  # Doesn't match rounded plan
            aantal_tafels_na_wdz2=20,
            datum_oppotten_real=date(2024, 1, 1),
            wijderzet_registratie_fout="Geen wdz2 datum maar wel tafel aantal na wdz 2",
            aantal_planten_gerealiseerd=1000,
            rounded_aantal_tafels_oppotten_plan=10,
        ),
    ]


@pytest.fixture
def mock_repo(mock_records):
    """Create a mock repository with test records."""
    mock = MagicMock()
    mock.get_error_records.return_value = mock_records
    return mock


def test_fix_spacing_errors_dry_run(cli_runner, mock_repo):
    """Test fix-spacing-errors command in dry-run mode."""
    with patch("production_control.__cli__.SpacingRepository", return_value=mock_repo):
        # Run command
        result = cli_runner.invoke(
            app, ["fix-spacing-errors", "--error", "Geen wdz2 datum"]
        )

        # Verify output
        assert result.exit_code == 0
        assert "[DRY RUN]" in result.stdout
        assert "Would fix: 1" in result.stdout
        assert "Manual review needed: 1" in result.stdout
        # TEST-001 should be fixed automatically
        assert "Move WDZ2 count (20) to WDZ1" in result.stdout


def test_fix_spacing_errors_with_logging(cli_runner, mock_repo):
    """Test fix-spacing-errors command with log file."""
    with patch("production_control.__cli__.SpacingRepository", return_value=mock_repo), \
         tempfile.NamedTemporaryFile(suffix=".log", delete=False) as temp_log:
        # Run command with log file
        result = cli_runner.invoke(
            app,
            ["fix-spacing-errors", "--error", "Geen wdz2 datum", "--log", temp_log.name]
        )

        # Verify output
        assert result.exit_code == 0
        assert "Manual review needed: 1" in result.stdout
        assert temp_log.name in result.stdout

        # Verify log file
        with open(temp_log.name) as f:
            log_content = f.read()
            assert "TEST-002" in log_content
            assert "WDZ1 count (15) doesn't match rounded plan (10)" in log_content

        # Clean up
        Path(temp_log.name).unlink()


def test_fix_spacing_errors_actual_fix(cli_runner, mock_repo):
    """Test fix-spacing-errors command with actual fixes."""
    with patch("production_control.__cli__.SpacingRepository", return_value=mock_repo), \
         patch("production_control.__cli__.OpTechClient") as mock_client_class:
        # Set up mock client
        mock_client = MagicMock()
        mock_client.send_correction.return_value = CorrectionResponse(
            success=True,
            message="Successfully updated spacing data for partij TEST-001"
        )
        mock_client_class.return_value = mock_client

        # Run command without dry-run
        result = cli_runner.invoke(
            app,
            ["fix-spacing-errors", "--error", "Geen wdz2 datum", "--no-dry-run"]
        )

        # Verify output
        assert result.exit_code == 0
        assert "Successfully updated" in result.stdout
        assert "Fixed: 1" in result.stdout
        assert "Manual review needed: 1" in result.stdout

        # Verify API call
        mock_client.send_correction.assert_called_once()
        correction = mock_client.send_correction.call_args[0][0]
        assert correction.partij_code == "TEST-001"
        assert correction.aantal_tafels_na_wdz1 == 20
        assert correction.aantal_tafels_na_wdz2 == 0  # Should be 0 for API compatibility


def test_fix_spacing_errors_api_error(cli_runner, mock_repo):
    """Test fix-spacing-errors command handling API errors."""
    with patch("production_control.__cli__.SpacingRepository", return_value=mock_repo), \
         patch("production_control.__cli__.OpTechClient") as mock_client_class, \
         tempfile.NamedTemporaryFile(suffix=".log", delete=False) as temp_log:
        # Set up mock client to raise an error
        mock_client = MagicMock()
        error_msg = "API Error: Invalid request"
        mock_client.send_correction.side_effect = OpTechError(error_msg)
        mock_client_class.return_value = mock_client

        # Run command
        result = cli_runner.invoke(
            app,
            [
                "fix-spacing-errors",
                "--error", "Geen wdz2 datum",
                "--no-dry-run",
                "--log", temp_log.name,
            ]
        )

        # Verify output
        assert result.exit_code == 0
        assert "Failed to update" in result.stdout
        assert "Manual review needed: 2" in result.stdout  # Original + failed fix

        # Verify log file
        with open(temp_log.name) as f:
            log_content = f.read()
            assert f"Failed to update partij TEST-001: {error_msg}" in log_content

        # Clean up
        Path(temp_log.name).unlink()
