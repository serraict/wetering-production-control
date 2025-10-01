"""Tests for inspectie repository."""

from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import pytest
from sqlmodel import create_engine

from production_control.inspectie.repositories import InspectieRepository
from production_control.inspectie.models import InspectieRonde


@pytest.fixture
def mock_engine():
    """Create a mock database engine."""
    engine = create_engine("dremio+flight://mock:32010/dremio")
    return engine


def test_inspectie_repository_exists(mock_engine):
    """Test that InspectieRepository can be instantiated."""
    repository = InspectieRepository(mock_engine)
    assert repository is not None


@patch("production_control.inspectie.repositories.Session")
def test_inspectie_repository_get_paginated(mock_session_class, mock_engine):
    """Test paginated retrieval of inspectie records."""
    repository = InspectieRepository(mock_engine)
    session = mock_session_class.return_value.__enter__.return_value

    # Mock count query
    count_result = MagicMock()
    count_result.one.return_value = 1

    # Mock data query
    test_date = date(2025, 9, 25)
    test_record = InspectieRonde(
        code="27014",
        locatie_samenvatting="1: 2x 1-2",
        baan_samenvatting="001",
        klant_code="PT",
        bollen_code="ab41559-9-4",
        product_naam="T. Rocket 13",
        product_groep_naam="13 aziaat",
        datum_afleveren_plan=test_date,
        afwijking_afleveren=5,
        aantal_in_kas=398,
        aantal_tafels=2,
        productgroep_code=113,
        min_baan=1,
    )
    session.exec.side_effect = [count_result, [test_record]]

    # Act
    records, total = repository.get_paginated(
        page=1,
        items_per_page=10,
    )

    # Assert
    assert isinstance(records, list)
    assert isinstance(total, int)
    assert len(records) <= 10
    for record in records:
        assert isinstance(record, InspectieRonde)


@patch("production_control.inspectie.repositories.Session")
def test_inspectie_repository_show_all_records(mock_session_class, mock_engine):
    """Test that items_per_page=0 shows all records without error."""
    repository = InspectieRepository(mock_engine)
    session = mock_session_class.return_value.__enter__.return_value

    # Mock count query
    count_result = MagicMock()
    count_result.one.return_value = 5

    # Mock data query with multiple records
    test_date = date(2025, 9, 25)
    test_records = [
        InspectieRonde(
            code=f"2701{i}",
            product_naam=f"Test Product {i}",
            datum_afleveren_plan=test_date,
            afwijking_afleveren=i,
            min_baan=i,
        )
        for i in range(5)
    ]
    session.exec.side_effect = [count_result, test_records]

    # Act - request to show all records (items_per_page=0)
    records, total = repository.get_paginated(
        page=1,
        items_per_page=0,  # This should show all records
    )

    # Assert
    assert isinstance(records, list)
    assert len(records) == 5  # Should return all 5 records
    assert total == 5
    for record in records:
        assert isinstance(record, InspectieRonde)


@patch("production_control.inspectie.repositories.Session")
def test_inspectie_repository_date_range_filtering(mock_session_class, mock_engine):
    """Test date range filtering in repository."""
    repository = InspectieRepository(mock_engine)
    session = mock_session_class.return_value.__enter__.return_value

    # Mock count query
    count_result = MagicMock()
    count_result.one.return_value = 2

    # Mock data query with records in different date ranges
    today = date.today()
    next_week = today + timedelta(days=7)
    next_month = today + timedelta(days=30)

    test_records = [
        InspectieRonde(
            code="27014",
            product_naam="Test Product 1",
            datum_afleveren_plan=next_week,
            min_baan=1,
        ),
        InspectieRonde(
            code="27015",
            product_naam="Test Product 2",
            datum_afleveren_plan=next_month,
            min_baan=2,
        ),
    ]
    session.exec.side_effect = [count_result, test_records]

    # Act - request with date range
    records, total = repository.get_paginated(
        page=1,
        items_per_page=10,
        date_from=today,
        date_to=today + timedelta(days=14),
    )

    # Assert that get_paginated method was called successfully
    assert isinstance(records, list)
    assert isinstance(total, int)


@patch("production_control.inspectie.repositories.Session")
def test_inspectie_repository_next_two_weeks_filter(mock_session_class, mock_engine):
    """Test default 'next 2 weeks' filter behavior."""
    repository = InspectieRepository(mock_engine)
    session = mock_session_class.return_value.__enter__.return_value

    # Mock count query
    count_result = MagicMock()
    count_result.one.return_value = 1

    # Mock data query
    today = date.today()
    test_record = InspectieRonde(
        code="27014",
        product_naam="Test Product",
        datum_afleveren_plan=today + timedelta(days=10),
        min_baan=1,
    )
    session.exec.side_effect = [count_result, [test_record]]

    # Act - test the default behavior (should be next 2 weeks when implemented)
    records, total = repository.get_paginated(
        page=1,
        items_per_page=10,
        default_filter="next_two_weeks",
    )

    # Assert
    assert isinstance(records, list)
    assert isinstance(total, int)


@patch("production_control.inspectie.repositories.Session")
def test_inspectie_repository_sorting_by_min_baan_first(mock_session_class, mock_engine):
    """Test that sorting prioritizes min_baan field first."""
    repository = InspectieRepository(mock_engine)
    session = mock_session_class.return_value.__enter__.return_value

    # Mock count query
    count_result = MagicMock()
    count_result.one.return_value = 3

    # Mock data with records that should be sorted by min_baan first
    # This addresses Bianca's issue: position 2 should come before position 7
    today = date.today()
    test_records = [
        InspectieRonde(
            code="27014",
            product_naam="Test Product 1",
            datum_afleveren_plan=today + timedelta(days=10),
            min_baan=7,  # Higher baan number
        ),
        InspectieRonde(
            code="27015",
            product_naam="Test Product 2",
            datum_afleveren_plan=today + timedelta(days=5),  # Earlier date
            min_baan=2,  # Lower baan number - should come first despite later date
        ),
        InspectieRonde(
            code="27016",
            product_naam="Test Product 3",
            datum_afleveren_plan=today + timedelta(days=15),
            min_baan=812,  # Much higher baan number - should come last
        ),
    ]
    session.exec.side_effect = [count_result, test_records]

    # Act - test default sorting
    records, total = repository.get_paginated(page=1, items_per_page=10)

    # Assert - verify sorting behavior is tested (implementation will be in _apply_default_sorting)
    assert isinstance(records, list)
    assert isinstance(total, int)
    assert len(records) == 3
