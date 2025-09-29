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


def test_potting_lot_repository_initialization(mock_engine):
    """Test initializing the PottingLotRepository."""
    repository = PottingLotRepository(mock_engine)
    assert repository is not None


def test_potting_lot_repository_with_connection(mock_engine):
    """Test initializing the PottingLotRepository with a connection."""
    repository = PottingLotRepository(mock_engine)
    assert repository is not None


def test_potting_lot_repository_default_sorting(mock_engine):
    """Test the default sorting behavior of the repository."""
    repository = PottingLotRepository(mock_engine)
    # We can verify the repository has the expected search fields
    assert "id" in repository.search_fields
    assert "bollen_code" in repository.search_fields
    assert "naam" in repository.search_fields
    assert "oppot_datum" in repository.search_fields
    assert "opmerking" in repository.search_fields

    # We call _apply_default_sorting but don't need to use the result
    # This at least verifies the method doesn't raise exceptions
    repository._apply_default_sorting(select(PottingLot))


def test_potting_lot_repository_filtering(mock_engine):
    """Test the filtering behavior of the repository."""
    # This test verifies that the repository has the correct search fields
    # for filtering potting lot records
    repository = PottingLotRepository(mock_engine)
    assert len(repository.search_fields) == 8
    assert "id" in repository.search_fields
    assert "bollen_code" in repository.search_fields
    assert "naam" in repository.search_fields
    assert "oppot_datum" in repository.search_fields
    assert "opmerking" in repository.search_fields
    assert "product_groep" in repository.search_fields
    assert "klant_code" in repository.search_fields
    assert "oppot_week" in repository.search_fields


@pytest.mark.integration
def test_get_top_lots_integration():
    """Integration test for get_top_lots method with actual Dremio connection."""
    repository = PottingLotRepository()

    # Test with default limit (50)
    top_lots = repository.get_top_lots()

    # Verify we got results (assuming there are potting lots in the database)
    assert isinstance(top_lots, list)
    # We should get up to 50 results
    assert len(top_lots) <= 50

    # If we have results, verify they are PottingLot objects
    if top_lots:
        assert isinstance(top_lots[0], PottingLot)

        # Verify ordering - results should be ordered by oppot_datum DESC, id DESC
        if len(top_lots) > 1:
            for i in range(len(top_lots) - 1):
                current_lot = top_lots[i]
                next_lot = top_lots[i + 1]

                # If both have oppot_datum, check ordering
                if current_lot.oppot_datum is not None and next_lot.oppot_datum is not None:
                    # Current should be >= next (DESC order)
                    assert current_lot.oppot_datum >= next_lot.oppot_datum
                    # If dates are equal, IDs should be in DESC order
                    if current_lot.oppot_datum == next_lot.oppot_datum:
                        assert current_lot.id >= next_lot.id


@pytest.mark.integration
def test_get_top_lots_with_custom_limit():
    """Integration test for get_top_lots with custom limit."""
    repository = PottingLotRepository()

    # Test with smaller limit
    top_lots = repository.get_top_lots(limit=5)

    assert isinstance(top_lots, list)
    # We should get at most 5 results
    assert len(top_lots) <= 5

    # Test with limit of 1
    single_lot = repository.get_top_lots(limit=1)
    assert isinstance(single_lot, list)
    assert len(single_lot) <= 1

    if single_lot:
        assert isinstance(single_lot[0], PottingLot)
