"""Tests for spacing correction CLI commands."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from production_control.__cli__ import app
from production_control.spacing.models import WijderzetRegistratie
from production_control.spacing.optech import OpTechConnectionError, OpTechResponseError


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_record():
    """Create a mock spacing record."""
    return WijderzetRegistratie(
        id=uuid4(),
        partij_code="TEST-001",
        product_naam="Test Product",
        productgroep_naam="Test Group",
        aantal_planten_gerealiseerd=100,
        aantal_tafels_totaal=10,
        aantal_tafels_na_wdz1=15,
        aantal_tafels_na_wdz2=20,
        aantal_tafels_oppotten_plan=Decimal("10.0"),
        dichtheid_oppotten_plan=100,
        dichtheid_wz1_plan=50,
        datum_oppotten_real=date(2024, 1, 1),
        wijderzet_registratie_fout="Test error message",
    )


@pytest.mark.integration
def test_correct_spacing_requires_partij_code(cli_runner):
    """Test that correct-spacing command requires partij_code."""
    result = cli_runner.invoke(app, ["correct-spacing"])
    assert result.exit_code == 2  # Typer's error exit code
    assert "Missing argument 'PARTIJ_CODE'" in result.stdout


def test_correct_spacing_dry_run(cli_runner, mock_record):
    """Test correct-spacing command in dry-run mode."""
    # Mock the repository to return our test record
    mock_repo = MagicMock()
    mock_repo.get_by_partij_code.return_value = mock_record

    with patch("production_control.__cli__.SpacingRepository", return_value=mock_repo):
        result = cli_runner.invoke(app, ["correct-spacing", "TEST-001", "--wdz1", "25"])

        assert result.exit_code == 0
        assert "[DRY RUN]" in result.stdout
        assert "TEST-001" in result.stdout
        assert "would update" in result.stdout.lower()
        # Verify no actual correction was attempted
        mock_repo.update.assert_not_called()


@pytest.mark.integration
def test_correct_spacing_invalid_partij(cli_runner):
    """Test correct-spacing command with invalid partij code."""
    mock_repo = MagicMock()
    mock_repo.get_by_partij_code.return_value = None

    with patch("production_control.__cli__.SpacingRepository", return_value=mock_repo):
        result = cli_runner.invoke(app, ["correct-spacing", "INVALID", "--wdz1", "25"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()


def test_correct_spacing_no_changes(cli_runner, mock_record):
    """Test correct-spacing command when no changes are specified."""
    mock_repo = MagicMock()
    mock_repo.get_by_partij_code.return_value = mock_record

    with patch("production_control.__cli__.SpacingRepository", return_value=mock_repo):
        result = cli_runner.invoke(app, ["correct-spacing", "TEST-001"])

        assert result.exit_code == 0
        assert "No changes specified" in result.stdout


@pytest.mark.integration
def test_correct_spacing_negative_tables(cli_runner, mock_record):
    """Test correct-spacing command with negative table counts."""
    mock_repo = MagicMock()
    mock_repo.get_by_partij_code.return_value = mock_record

    with patch("production_control.__cli__.SpacingRepository", return_value=mock_repo):
        result = cli_runner.invoke(app, ["correct-spacing", "TEST-001", "--wdz1", "-5"])

        assert result.exit_code == 1
        assert "must be positive" in result.stdout.lower()


@pytest.mark.integration
def test_correct_spacing_wdz2_requires_wdz1(cli_runner, mock_record):
    """Test that setting wdz2 requires wdz1 to be set."""
    mock_repo = MagicMock()
    mock_repo.get_by_partij_code.return_value = mock_record

    with patch("production_control.__cli__.SpacingRepository", return_value=mock_repo):
        result = cli_runner.invoke(app, ["correct-spacing", "TEST-001", "--wdz2", "30"])

        assert result.exit_code == 1
        assert "wdz1 must be set" in result.stdout.lower()


def test_correct_spacing_actual_correction(cli_runner, mock_record):
    """Test actual spacing correction (non-dry-run mode)."""
    mock_repo = MagicMock()
    mock_repo.get_by_partij_code.return_value = mock_record

    mock_optech = MagicMock()
    mock_optech.send_correction.return_value.success = True
    mock_optech.send_correction.return_value.message = "Successfully updated"

    with (
        patch("production_control.__cli__.SpacingRepository", return_value=mock_repo),
        patch("production_control.__cli__.OpTechClient", return_value=mock_optech),
    ):
        result = cli_runner.invoke(
            app, ["correct-spacing", "TEST-001", "--wdz1", "25", "--no-dry-run"]
        )

        assert result.exit_code == 0
        assert "Successfully updated" in result.stdout
        assert mock_optech.send_correction.called


@pytest.mark.integration
def test_correct_spacing_api_error(cli_runner, mock_record):
    """Test handling of API errors during correction."""
    mock_repo = MagicMock()
    mock_repo.get_by_partij_code.return_value = mock_record

    mock_optech = MagicMock()
    mock_optech.send_correction.side_effect = OpTechResponseError(400, "Invalid data")

    with (
        patch("production_control.__cli__.SpacingRepository", return_value=mock_repo),
        patch("production_control.__cli__.OpTechClient", return_value=mock_optech),
    ):
        result = cli_runner.invoke(
            app, ["correct-spacing", "TEST-001", "--wdz1", "25", "--no-dry-run"]
        )

        assert result.exit_code == 1
        assert "Failed to update" in result.stdout
        assert "Invalid data" in result.stdout


@pytest.mark.integration
def test_correct_spacing_connection_error(cli_runner, mock_record):
    """Test handling of connection errors during correction."""
    mock_repo = MagicMock()
    mock_repo.get_by_partij_code.return_value = mock_record

    mock_optech = MagicMock()
    mock_optech.send_correction.side_effect = OpTechConnectionError(
        "Connection failed", "http://optech.test"
    )

    with (
        patch("production_control.__cli__.SpacingRepository", return_value=mock_repo),
        patch("production_control.__cli__.OpTechClient", return_value=mock_optech),
    ):
        result = cli_runner.invoke(
            app, ["correct-spacing", "TEST-001", "--wdz1", "25", "--no-dry-run"]
        )

        assert result.exit_code == 1
        assert "Failed to connect" in result.stdout
        assert "Connection failed" in result.stdout
