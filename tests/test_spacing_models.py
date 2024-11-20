"""Tests for spacing models."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from sqlmodel import create_engine
from production_control.spacing.models import WijderzetRegistratie, SpacingRepository


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


@patch("production_control.spacing.models.Session")
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
