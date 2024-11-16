"""Test configuration and fixtures."""

from typing import Generator
import pytest
from nicegui.testing import User


@pytest.fixture
def user(user: User) -> Generator[User, None, None]:
    """Initialize NiceGUI for testing."""
    from production_control.web.startup import startup

    startup()
    yield user
