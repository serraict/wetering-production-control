"""Tests for spacing command models."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from production_control.spacing.models import WijderzetRegistratie
from production_control.spacing.commands import CorrectSpacingRecord


def create_test_record() -> WijderzetRegistratie:
    """Create a test record with default values."""
    return WijderzetRegistratie(
        partij_code="TEST123",
        product_naam="Test Plant",
        productgroep_naam="Test Group",
        aantal_tafels_totaal=10,
        aantal_tafels_na_wdz1=15,
        aantal_tafels_na_wdz2=20,
        aantal_tafels_oppotten_plan=Decimal("10.0"),
        aantal_planten_gerealiseerd=100,
        datum_wdz1_real=date(2023, 1, 1),
        datum_wdz2_real=date(2023, 1, 1),
        datum_oppotten_real=date(2023, 1, 1),
        datum_uit_cel_real=date(2023, 1, 1),
        dichtheid_oppotten_plan=100,
        dichtheid_wz1_plan=50,
        dichtheid_wz2_plan=25.0,
        wijderzet_registratie_fout=False,
    )


def test_create_command_from_record() -> None:
    """Test creating a command from a WijderzetRegistratie."""
    record = create_test_record()
    command = CorrectSpacingRecord.from_record(record)
    assert command.partij_code == "TEST123"
    assert command.aantal_tafels_na_wdz1 == 15
    assert command.aantal_tafels_na_wdz2 == 20


def test_validate_wz1_greater_than_zero() -> None:
    """Test that aantal_tafels_na_wdz1 must be greater than zero."""
    record = create_test_record()
    with pytest.raises(ValidationError, match="greater than 0"):
        CorrectSpacingRecord(
            partij_code=record.partij_code,
            aantal_tafels_na_wdz1=0,
            aantal_tafels_na_wdz2=None,
        )


def test_validate_wz2_requires_wz1() -> None:
    """Test that aantal_tafels_na_wdz2 cannot be set if wz1 is None."""
    record = create_test_record()
    with pytest.raises(ValidationError, match="WZ2.*WZ1 leeg"):
        CorrectSpacingRecord(
            partij_code=record.partij_code,
            aantal_tafels_na_wdz1=None,
            aantal_tafels_na_wdz2=20,
        )


def test_validate_wz2_greater_than_wz1() -> None:
    """Test that aantal_tafels_na_wdz2 must be greater than wz1."""
    record = create_test_record()
    with pytest.raises(ValidationError, match="WZ2.*groter.*WZ1"):
        CorrectSpacingRecord(
            partij_code=record.partij_code,
            aantal_tafels_na_wdz1=20,
            aantal_tafels_na_wdz2=15,
        )


def test_allow_null_values() -> None:
    """Test that null values are allowed for both fields."""
    record = create_test_record()
    command = CorrectSpacingRecord(
        partij_code=record.partij_code,
        aantal_tafels_na_wdz1=None,
        aantal_tafels_na_wdz2=None,
    )
    assert command.aantal_tafels_na_wdz1 is None
    assert command.aantal_tafels_na_wdz2 is None


def test_allow_wz1_without_wz2() -> None:
    """Test that wz1 can be set without wz2."""
    record = create_test_record()
    command = CorrectSpacingRecord(
        partij_code=record.partij_code,
        aantal_tafels_na_wdz1=15,
        aantal_tafels_na_wdz2=None,
    )
    assert command.aantal_tafels_na_wdz1 == 15
    assert command.aantal_tafels_na_wdz2 is None
