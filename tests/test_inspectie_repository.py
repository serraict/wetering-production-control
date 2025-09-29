"""Tests for inspectie repository."""

from datetime import date
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


def test_inspectie_repository_exists():
    """Test that InspectieRepository can be instantiated."""
    repository = InspectieRepository()
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
