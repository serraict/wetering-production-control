"""Tests for spacing fix commands."""

from decimal import Decimal
from typing import Optional

import pytest

from production_control.spacing.commands import FixMissingWdz2DateCommand


@pytest.mark.parametrize(
    "wdz1,wdz2,plan,can_fix",
    [
        (10, 20, Decimal("10.0"), True),  # WDZ1 equals rounded plan
        (10, 20, Decimal("10.4"), True),  # WDZ1 equals rounded plan (round down)
        (20, 20, Decimal("10.4"), True),  # WDZ1=WDZ2, plan doesn't matter
        (12, 20, Decimal("10.6"), False),  # WDZ1 doesn't equal rounded plan (10.6 rounds to 11)
        (10, None, Decimal("10.0"), False),  # No WDZ2 count
    ],
)
def test_fix_missing_wdz2_date_can_fix(
    wdz1: int, wdz2: Optional[int], plan: Decimal, can_fix: bool
):
    """Test identification of records that can be fixed automatically."""
    command = FixMissingWdz2DateCommand(
        partij_code="TEST123",
        aantal_tafels_oppotten_plan=plan,
        aantal_tafels_na_wdz1=wdz1,
        aantal_tafels_na_wdz2=wdz2,
    )
    assert command.can_fix_automatically() == can_fix


def test_fix_missing_wdz2_date_get_correction():
    """Test generating correction command for fixable record."""
    # Arrange
    command = FixMissingWdz2DateCommand(
        partij_code="TEST123",
        aantal_tafels_oppotten_plan=Decimal("10.0"),
        aantal_tafels_na_wdz1=10,  # Equals rounded plan
        aantal_tafels_na_wdz2=20,
    )

    # Act
    correction = command.get_correction()

    # Assert
    assert correction is not None
    assert correction.partij_code == "TEST123"
    assert correction.aantal_tafels_na_wdz1 == 20  # WDZ2 count moved to WDZ1
    assert correction.aantal_tafels_na_wdz2 == 0  # WDZ2 count cleared


def test_fix_missing_wdz2_date_no_correction_for_manual_review():
    """Test that no correction is generated for records needing manual review."""
    # Arrange
    command = FixMissingWdz2DateCommand(
        partij_code="TEST123",
        aantal_tafels_oppotten_plan=Decimal("10.0"),
        aantal_tafels_na_wdz1=15,  # Doesn't equal rounded plan
        aantal_tafels_na_wdz2=20,
    )

    # Act
    correction = command.get_correction()

    # Assert
    assert correction is None
