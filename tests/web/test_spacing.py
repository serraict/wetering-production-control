"""Tests for spacing web interface."""

from nicegui.testing import User


async def test_spacing_page_exists(user: User) -> None:
    """Test that spacing page exists and shows header."""
    # When
    await user.open("/spacing")

    # Then
    await user.should_see("Spacing Overview")
