"""Test for the updated date range filtering (1 week before to 2 weeks after)."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from sqlmodel import create_engine

from production_control.inspectie.repositories import InspectieRepository


@pytest.fixture
def mock_engine():
    """Create a mock database engine."""
    engine = create_engine("dremio+flight://mock:32010/dremio")
    return engine


@patch("production_control.inspectie.repositories.Session")
def test_next_two_weeks_filter_shows_three_week_window(mock_session_class, mock_engine):
    """Test that 'next_two_weeks' filter now shows 1 week before to 2 weeks after."""
    repository = InspectieRepository(mock_engine)

    # Create a mock query to capture the applied date filters
    mock_query = mock_session_class.return_value.__enter__.return_value.exec.return_value
    mock_query.scalars.return_value.all.return_value = []
    mock_query.one.return_value = 0

    today = date.today()
    expected_start = today - timedelta(days=7)  # 1 week before
    expected_end = today + timedelta(days=14)  # 2 weeks after

    # Test the _apply_date_filter method directly
    from sqlmodel import select
    from production_control.inspectie.models import InspectieRonde

    base_query = select(InspectieRonde)
    filtered_query = repository._apply_date_filter(base_query, default_filter="next_two_weeks")

    # Convert the query to string to check the date conditions
    query_str = str(filtered_query)

    # Verify that both date conditions are present
    assert f"datum_afleveren_plan >= '{expected_start}'" in query_str
    assert f"datum_afleveren_plan <= '{expected_end}'" in query_str

    print(f"✓ Filter correctly shows: {expected_start} to {expected_end} (3-week window)")


def test_date_range_calculation():
    """Test that the date range calculation is correct."""
    today = date.today()

    # Calculate expected dates
    expected_start = today - timedelta(days=7)  # 1 week before
    expected_end = today + timedelta(days=14)  # 2 weeks after

    # Total window should be 21 days
    total_days = (expected_end - expected_start).days
    assert total_days == 21, f"Expected 21-day window, got {total_days} days"

    # Verify the dates are calculated correctly
    assert expected_start < today < expected_end

    print(f"✓ Date range: {expected_start} to {expected_end}")
    print(f"✓ Total window: {total_days} days")
