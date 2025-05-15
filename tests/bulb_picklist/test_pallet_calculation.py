"""Tests for pallet calculation functionality."""

from production_control.bulb_picklist.models import BulbPickList


def test_pallet_count_property():
    """Test the pallet_count property on BulbPickList."""
    # Test basic cases
    assert BulbPickList(aantal_bakken=25).pallet_count == 1  # Exactly one full pallet
    assert BulbPickList(aantal_bakken=26).pallet_count == 2  # One full + one partial
    assert BulbPickList(aantal_bakken=50).pallet_count == 2  # Two full pallets
    assert BulbPickList(aantal_bakken=51).pallet_count == 3  # Two full + one partial
    assert BulbPickList(aantal_bakken=68).pallet_count == 3  # Two full + one partial
