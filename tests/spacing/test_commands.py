"""Tests for spacing command models."""

from datetime import date
from decimal import Decimal

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
    assert command.product_naam == "Test Plant"
    assert command.productgroep_naam == "Test Group"
    assert command.aantal_tafels_oppotten_plan == Decimal("10.0")
    assert command.aantal_planten_gerealiseerd == 100
    assert command.datum_oppotten_real == date(2023, 1, 1)
    assert command.datum_wdz1_real == date(2023, 1, 1)
    assert command.datum_wdz2_real == date(2023, 1, 1)


def test_allow_null_values() -> None:
    """Test that null values are allowed for both fields."""
    record = create_test_record()
    command = CorrectSpacingRecord(
        partij_code=record.partij_code,
        product_naam=record.product_naam,
        productgroep_naam=record.productgroep_naam,
        aantal_tafels_oppotten_plan=record.aantal_tafels_oppotten_plan,
        aantal_planten_gerealiseerd=record.aantal_planten_gerealiseerd,
        datum_oppotten_real=record.datum_oppotten_real,
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
        product_naam=record.product_naam,
        productgroep_naam=record.productgroep_naam,
        aantal_tafels_oppotten_plan=record.aantal_tafels_oppotten_plan,
        aantal_planten_gerealiseerd=record.aantal_planten_gerealiseerd,
        datum_oppotten_real=record.datum_oppotten_real,
        aantal_tafels_na_wdz1=15,
        aantal_tafels_na_wdz2=None,
    )
    assert command.aantal_tafels_na_wdz1 == 15
    assert command.aantal_tafels_na_wdz2 is None


def test_get_editable_fields() -> None:
    """Test getting list of editable fields."""
    record = create_test_record()
    command = CorrectSpacingRecord.from_record(record)
    editable = command.get_editable_fields()
    assert editable == ["aantal_tafels_na_wdz1", "aantal_tafels_na_wdz2"]


def test_get_readonly_fields() -> None:
    """Test getting list of read-only fields."""
    record = create_test_record()
    command = CorrectSpacingRecord.from_record(record)
    readonly = command.get_readonly_fields()
    assert "partij_code" in readonly
    assert "product_naam" in readonly
    assert "productgroep_naam" in readonly
    assert "aantal_tafels_oppotten_plan" in readonly
    assert "aantal_planten_gerealiseerd" in readonly
    assert "datum_oppotten_real" in readonly
    assert "datum_wdz1_real" in readonly
    assert "datum_wdz2_real" in readonly
