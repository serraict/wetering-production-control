"""Tests for vloerplan commands."""

import pytest
from pydantic import ValidationError

from production_control.vloerplan.commands import UpdateTuinNrCommand


def test_update_tuin_nr_command_rejects_null_tuinnummer() -> None:
    with pytest.raises(ValidationError):
        UpdateTuinNrCommand(teeltnr=27515, new_tuinnummer=None)


def test_update_tuin_nr_command_rejects_zero_tuinnummer() -> None:
    with pytest.raises(ValidationError):
        UpdateTuinNrCommand(teeltnr=27515, new_tuinnummer=0)
