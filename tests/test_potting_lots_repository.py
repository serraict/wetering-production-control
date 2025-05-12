"""Tests for potting lots repository."""

import pytest
from sqlmodel import create_engine, select
from production_control.potting_lots.models import PottingLot
from production_control.potting_lots.repositories import PottingLotRepository


@pytest.fixture
def mock_engine():
    """Create a mock database engine."""
    engine = create_engine("dremio+flight://mock:32010/dremio")
    return engine


def test_potting_lot_repository_initialization():
    """Test initializing the PottingLotRepository."""
    repository = PottingLotRepository()
    assert repository is not None


def test_potting_lot_repository_with_connection(mock_engine):
    """Test initializing the PottingLotRepository with a connection."""
    repository = PottingLotRepository(mock_engine)
    assert repository is not None


def test_potting_lot_repository_default_sorting():
    """Test the default sorting behavior of the repository."""
    repository = PottingLotRepository()
    # We can verify the repository has the expected search fields
    assert "id" in repository.search_fields
    assert "bollen_code" in repository.search_fields
    assert "naam" in repository.search_fields
    assert "oppot_datum" in repository.search_fields
    assert "opmerking" in repository.search_fields

    # We call _apply_default_sorting but don't need to use the result
    # This at least verifies the method doesn't raise exceptions
    repository._apply_default_sorting(select(PottingLot))


def test_potting_lot_repository_filtering():
    """Test the filtering behavior of the repository."""
    # This test verifies that the repository has the correct search fields
    # for filtering potting lot records
    repository = PottingLotRepository()
    assert len(repository.search_fields) == 5
    assert "id" in repository.search_fields
    assert "bollen_code" in repository.search_fields
    assert "naam" in repository.search_fields
    assert "oppot_datum" in repository.search_fields
    assert "opmerking" in repository.search_fields
