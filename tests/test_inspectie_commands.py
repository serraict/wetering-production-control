"""Tests for inspectie commands."""

from datetime import date

import pytest
from pydantic import ValidationError

from production_control.inspectie.commands import UpdateAfwijkingCommand


def test_update_afwijking_command_exists():
    """Test that UpdateAfwijkingCommand can be instantiated."""
    command = UpdateAfwijkingCommand(
        code="27014", new_afwijking=1, new_datum_afleveren=date(2025, 10, 10)
    )
    assert command is not None


def test_update_afwijking_command_with_plus_one():
    """Test command with +1 value."""
    command = UpdateAfwijkingCommand(
        code="27014", new_afwijking=1, new_datum_afleveren=date(2025, 10, 10)
    )
    assert command.code == "27014"
    assert command.new_afwijking == 1


def test_update_afwijking_command_with_minus_one():
    """Test command with -1 value."""
    command = UpdateAfwijkingCommand(
        code="27014", new_afwijking=-1, new_datum_afleveren=date(2025, 10, 10)
    )
    assert command.code == "27014"
    assert command.new_afwijking == -1


def test_update_afwijking_command_validation_empty_code():
    """Test command validation fails for empty code."""
    with pytest.raises(ValidationError):
        UpdateAfwijkingCommand(code="", new_afwijking=1, new_datum_afleveren=date(2025, 10, 10))


def test_update_afwijking_command_validation_none_code():
    """Test command validation fails for None code."""
    with pytest.raises(ValidationError):
        UpdateAfwijkingCommand(code=None, new_afwijking=1, new_datum_afleveren=date(2025, 10, 10))


def test_update_afwijking_command_validation_zero_afwijking():
    """Test command allows zero afwijking value."""
    command = UpdateAfwijkingCommand(
        code="27014", new_afwijking=0, new_datum_afleveren=date(2025, 10, 10)
    )
    assert command.new_afwijking == 0


def test_update_afwijking_command_validation_large_values():
    """Test command handles large positive and negative values."""
    default_date = date(2025, 10, 10)
    command_pos = UpdateAfwijkingCommand(
        code="27014", new_afwijking=100, new_datum_afleveren=default_date
    )
    command_neg = UpdateAfwijkingCommand(
        code="27014", new_afwijking=-100, new_datum_afleveren=default_date
    )
    assert command_pos.new_afwijking == 100
    assert command_neg.new_afwijking == -100


def test_update_afwijking_command_requires_date():
    """Test command validation fails when new_datum_afleveren is missing."""
    with pytest.raises(ValidationError):
        UpdateAfwijkingCommand(code="27014", new_afwijking=1)
