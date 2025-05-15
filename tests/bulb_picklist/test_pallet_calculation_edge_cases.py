"""Tests for pallet calculation edge cases."""

from production_control.bulb_picklist.models import BulbPickList


def test_pallet_count_edge_cases():
    """Test edge cases for the pallet_count property."""
    # Test edge cases
    assert BulbPickList(aantal_bakken=0).pallet_count == 0  # Zero boxes
    assert BulbPickList(aantal_bakken=-5).pallet_count == 0  # Negative boxes
    assert BulbPickList(aantal_bakken=1).pallet_count == 1  # Minimum case
    assert BulbPickList(aantal_bakken=24).pallet_count == 1  # Partial pallet
    assert BulbPickList(aantal_bakken=999).pallet_count == 40  # Large number
