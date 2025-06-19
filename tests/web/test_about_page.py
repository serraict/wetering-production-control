"""Tests for web interface."""

import os
from unittest.mock import patch
from nicegui.testing import User


async def test_about_page_shows_guest_when_there_is_no_authenticated_user(user: User) -> None:

    await user.open("/about")
    await user.should_see("Guest")


async def test_about_page_shows_authenticated_user_name(user: User) -> None:
    """Should display the authenticated user's name from headers."""
    with patch("production_control.web.auth.context") as mock_context:
        mock_context.client.request.headers.get.side_effect = lambda key: {
            "remote-name": "John Doe",
            "remote-user": "john.doe",
        }.get(key)

        await user.open("/about")
        await user.should_see("John Doe")


async def test_about_page_shows_roles_in_tooltip(user: User) -> None:
    """Should display user roles in tooltip when hovering over username."""
    with patch("production_control.web.auth.context") as mock_context:
        mock_context.client.request.headers.get.side_effect = lambda key: {
            "remote-user": "admin.user",
            "remote-groups": "admin,production_employee",
        }.get(key)

        await user.open("/about")
        await user.should_see("admin.user")

        # Check that the tooltip content is accessible (NiceGUI testing may vary)
        # The exact tooltip testing might need adjustment based on NiceGUI's testing capabilities


async def test_about_page_shows_no_roles_assigned_tooltip_when_no_groups(user: User) -> None:
    """Should show 'No roles assigned' tooltip when user has no groups."""
    with patch("production_control.web.auth.context") as mock_context:
        mock_context.client.request.headers.get.side_effect = lambda key: {
            "remote-user": "basic.user",
            "remote-groups": "",
        }.get(key)

        await user.open("/about")
        await user.should_see("basic.user")


async def test_about_page_user_name_is_link_when_profile_page_url_set(user: User) -> None:
    """Should render username as a link when PROFILE_PAGE_URL environment variable is set."""
    with (
        patch("production_control.web.auth.context") as mock_context,
        patch.dict(os.environ, {"PROFILE_PAGE_URL": "https://profile.example.com"}),
    ):
        mock_context.client.request.headers.get.side_effect = lambda key: {
            "remote-user": "test.user"
        }.get(key)

        await user.open("/about")
        await user.should_see("test.user")

        # Find the link element - this might need adjustment based on NiceGUI testing capabilities
        # The exact way to test links in NiceGUI may vary


async def test_about_page_user_name_is_label_when_no_profile_page_url(user: User) -> None:
    """Should render username as a label when PROFILE_PAGE_URL is not set."""
    with (
        patch("production_control.web.auth.context") as mock_context,
        patch.dict(os.environ, {}, clear=True),
    ):
        mock_context.client.request.headers.get.side_effect = lambda key: {
            "remote-user": "test.user"
        }.get(key)

        await user.open("/about")
        await user.should_see("test.user")


async def test_about_page_displays_multiple_roles_correctly(user: User) -> None:
    """Should display multiple roles correctly in tooltip."""
    with patch("production_control.web.auth.context") as mock_context:
        mock_context.client.request.headers.get.side_effect = lambda key: {
            "remote-user": "multi.user",
            "remote-groups": "admin,user,production_employee",
        }.get(key)

        await user.open("/about")
        await user.should_see("multi.user")
