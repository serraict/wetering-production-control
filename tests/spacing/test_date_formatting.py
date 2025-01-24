"""Tests for spacing date formatting."""

from datetime import date
from uuid import UUID

from production_control.spacing.models import WijderzetRegistratie


def test_wijderzet_date_str():
    """Test date fields format as strings in ISO week format."""
    # Given
    record = WijderzetRegistratie(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        partij_code="TEST123",
        product_naam="Test Plant",
        productgroep_naam="Test Group",
        datum_oppotten_real=date(2024, 1, 16),  # Tuesday of week 3
        datum_uit_cel_real=None,  # Test None handling
        datum_wdz1_real=date(2024, 1, 1),  # Monday of week 1
        datum_wdz2_real=date(2023, 12, 31),  # Sunday of week 52, 2023
    )

    # Then
    assert str(record) == "TEST123 (24w03-2)"  # Format includes batch code and potting date


def test_wijderzet_date_str_year_boundary():
    """Test date formatting at year boundaries follows ISO week numbering."""
    # Given
    record = WijderzetRegistratie(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        partij_code="TEST123",
        product_naam="Test Plant",
        productgroep_naam="Test Group",
        datum_oppotten_real=date(2024, 12, 30),  # Monday of week 1, 2025
        datum_uit_cel_real=None,
        datum_wdz1_real=None,
        datum_wdz2_real=None,
    )

    # Then
    assert str(record) == "TEST123 (25w01-1)"  # Should show 2025's week 1, not 2024's
