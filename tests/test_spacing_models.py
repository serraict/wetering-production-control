"""Tests for spacing models."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from sqlmodel import create_engine
from production_control.spacing.repositories import SpacingRepository
from production_control.spacing.models import WijderzetRegistratie


@pytest.fixture
def mock_engine():
    """Create a mock database engine."""
    engine = create_engine("dremio+flight://mock:32010/dremio")
    return engine


def test_wijderzet_registratie_model():
    """Test creating a WijderzetRegistratie model."""
    # Arrange
    test_date = date(2023, 1, 1)

    # Act
    registratie = WijderzetRegistratie(
        partij_code="TEST123",
        product_naam="Test Plant",
        productgroep_naam="Test Group",
        aantal_tafels_totaal=10,
        aantal_tafels_na_wdz1=15,
        aantal_tafels_na_wdz2=20,
        aantal_tafels_oppotten_plan=Decimal("10.0"),
        aantal_planten_gerealiseerd=100,
        datum_wdz1_real=test_date,
        datum_wdz2_real=test_date,
        datum_oppotten_real=test_date,
        datum_uit_cel_real=test_date,
        dichtheid_oppotten_plan=100,
        dichtheid_wz1_plan=50,
        dichtheid_wz2_plan=25.0,
        wijderzet_registratie_fout=False,
    )

    # Assert
    assert registratie.partij_code == "TEST123"
    assert registratie.product_naam == "Test Plant"
    assert registratie.productgroep_naam == "Test Group"
    assert registratie.datum_oppotten_real == test_date
    assert registratie.datum_uit_cel_real == test_date
    assert registratie.datum_wdz1_real == test_date
    assert registratie.datum_wdz2_real == test_date
    assert registratie.aantal_planten_gerealiseerd == 100
    assert registratie.aantal_tafels_totaal == 10
    assert registratie.aantal_tafels_na_wdz1 == 15
    assert registratie.aantal_tafels_na_wdz2 == 20
    assert registratie.aantal_tafels_oppotten_plan == Decimal("10.0")
    assert registratie.dichtheid_oppotten_plan == 100
    assert registratie.dichtheid_wz1_plan == 50
    assert registratie.dichtheid_wz2_plan == 25.0
    assert registratie.wijderzet_registratie_fout is False


def test_wijderzet_registratie_warning_emoji():
    """Test the warning emoji property."""
    # Test with error
    registratie_with_error = WijderzetRegistratie(
        partij_code="TEST123",
        wijderzet_registratie_fout="Some error",
    )
    assert registratie_with_error.warning_emoji == "⚠️"

    # Test without error
    registratie_without_error = WijderzetRegistratie(
        partij_code="TEST123",
        wijderzet_registratie_fout=None,
    )
    assert registratie_without_error.warning_emoji == ""


@patch("production_control.spacing.repositories.Session")
def test_spacing_repository_get_paginated(mock_session_class, mock_engine):
    """Test paginated retrieval of spacing records."""
    # Arrange
    repository = SpacingRepository(mock_engine)
    session = mock_session_class.return_value.__enter__.return_value

    # Mock count query
    count_result = MagicMock()
    count_result.one.return_value = 1

    # Mock data query
    test_date = date(2023, 1, 1)
    test_record = WijderzetRegistratie(
        partij_code="TEST123",
        product_naam="Test Plant",
        productgroep_naam="Test Group",
        datum_oppotten_real=test_date,
        datum_uit_cel_real=test_date,
        datum_wdz1_real=test_date,
        datum_wdz2_real=test_date,
        aantal_planten_gerealiseerd=100,
        aantal_tafels_totaal=10,
        aantal_tafels_na_wdz1=15,
        aantal_tafels_na_wdz2=20,
        aantal_tafels_oppotten_plan=Decimal("10.0"),
        dichtheid_oppotten_plan=100,
        dichtheid_wz1_plan=50,
        dichtheid_wz2_plan=25.0,
        wijderzet_registratie_fout=False,
    )
    session.exec.side_effect = [count_result, [test_record]]

    # Act
    registraties, total = repository.get_paginated(
        page=1,
        items_per_page=10,
    )

    # Assert
    assert isinstance(registraties, list)
    assert isinstance(total, int)
    assert len(registraties) <= 10
    for reg in registraties:
        assert isinstance(reg, WijderzetRegistratie)


@pytest.mark.parametrize(
    "plan_value,expected_rounded",
    [
        (Decimal("10.0"), 10),  # Whole number
        (Decimal("10.2"), 10),  # Round down
        (Decimal("10.5"), 11),  # Round half up
        (Decimal("10.7"), 11),  # Round up
        (Decimal("0.4"), 0),    # Small number round down
        (Decimal("0.5"), 1),    # Small number round half up
        (Decimal("0.6"), 1),    # Small number round up
    ],
)
def test_rounded_aantal_tafels_oppotten_plan(plan_value: Decimal, expected_rounded: int):
    """Test rounding of aantal_tafels_oppotten_plan."""
    record = WijderzetRegistratie(
        partij_code="TEST-001",
        product_naam="Test Product",
        productgroep_naam="Test Group",
        aantal_planten_gerealiseerd=100,
        aantal_tafels_totaal=10,
        aantal_tafels_oppotten_plan=plan_value,
    )
    assert record.rounded_aantal_tafels_oppotten_plan == expected_rounded
