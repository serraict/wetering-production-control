"""Tests for spacing repository functionality."""

from datetime import date
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest
from sqlmodel import create_engine, Session

from production_control.spacing.repositories import SpacingRepository
from production_control.spacing.models import WijderzetRegistratie


@pytest.fixture
def mock_engine():
    """Create a mock database engine."""
    engine = create_engine("dremio+flight://mock:32010/dremio")
    return engine


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_records():
    """Create mock spacing records."""
    return [
        WijderzetRegistratie(
            id=uuid4(),
            partij_code="TEST-001",
            product_naam="Test Product",
            productgroep_naam="Test Group",
            aantal_planten_gerealiseerd=100,
            aantal_tafels_totaal=10,
            aantal_tafels_na_wdz1=15,
            aantal_tafels_na_wdz2=20,
            aantal_tafels_oppotten_plan=10,
            dichtheid_oppotten_plan=100,
            dichtheid_wz1_plan=50,
            datum_oppotten_real=date(2024, 1, 1),
            wijderzet_registratie_fout=True,
        ),
        WijderzetRegistratie(
            id=uuid4(),
            partij_code="TEST-002",
            product_naam="Test Product",
            productgroep_naam="Test Group",
            aantal_planten_gerealiseerd=100,
            aantal_tafels_totaal=10,
            aantal_tafels_na_wdz1=15,
            aantal_tafels_na_wdz2=20,
            aantal_tafels_oppotten_plan=10,
            dichtheid_oppotten_plan=100,
            dichtheid_wz1_plan=50,
            datum_oppotten_real=date(2024, 1, 1),
            wijderzet_registratie_fout=False,
        ),
    ]


@pytest.fixture
def repository(mock_engine):
    """Create a repository instance with a mock engine."""
    return SpacingRepository(mock_engine)


@patch("production_control.spacing.repositories.Session")
def test_get_error_records(mock_session_class, repository, mock_records):
    """Verify get_error_records returns only records with errors."""
    # Setup mock
    session = mock_session_class.return_value.__enter__.return_value
    session.exec.return_value = [mock_records[0]]  # Only return the error record

    # Execute
    error_records = repository.get_error_records()

    # Verify
    assert len(error_records) == 1
    assert error_records[0].partij_code == "TEST-001"
    assert error_records[0].wijderzet_registratie_fout is True
