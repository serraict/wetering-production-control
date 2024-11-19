"""Tests for base repository."""

import pytest

from production_control.data.repository import RepositoryError, InvalidParameterError


def test_repository_error():
    """Test RepositoryError can be raised."""
    with pytest.raises(RepositoryError) as exc_info:
        raise RepositoryError("Test error")
    assert str(exc_info.value) == "Test error"


def test_invalid_parameter_error():
    """Test InvalidParameterError can be raised and inherits from RepositoryError."""
    with pytest.raises(InvalidParameterError) as exc_info:
        raise InvalidParameterError("Invalid parameter")
    assert str(exc_info.value) == "Invalid parameter"
    assert isinstance(exc_info.value, RepositoryError)
