"""Tests for OpTech API client."""

from datetime import date
from decimal import Decimal
import logging

from production_control.spacing.models import WijderzetRegistratie
from production_control.spacing.commands import CorrectSpacingRecord
from production_control.spacing.optech import OpTechClient


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


def test_send_correction_logs_command(caplog) -> None:
    """Test that sending a correction logs the command details."""
    # Given
    caplog.set_level(logging.INFO)
    record = create_test_record()
    command = CorrectSpacingRecord.from_record(record)

    # When
    client = OpTechClient()
    client.send_correction(command)

    # Then
    assert "Sending correction" in caplog.text
    assert "TEST123" in caplog.text
    assert "15" in caplog.text
    assert "20" in caplog.text
