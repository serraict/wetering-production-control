"""Tests for web components."""

from pydantic import BaseModel, HttpUrl, computed_field
from nicegui import ui
from nicegui.testing import User

from production_control.web.components.model_card import display_model_card
from production_control.web.components.message import message, show_error
from production_control.web.components.menu import menu


class AViewModel(BaseModel):
    """Test model with URL field."""

    name: str
    website: HttpUrl

    @computed_field(return_type=HttpUrl)
    def api_url(self) -> str:
        """Get API URL."""
        base = str(self.website).rstrip("/")
        return f"{base}/api"


async def test_model_card_renders_url_as_link(user: User) -> None:
    """Test that model_card renders URL fields as clickable links."""
    # Given
    test_url = "https://example.com"
    model = AViewModel(
        name="Test Name",
        website=test_url,
    )

    # When
    @ui.page("/test")
    def test_page():
        display_model_card(model)

    await user.open("/test")

    # Then
    await user.should_see("Test Name")  # Regular field should be visible
    await user.should_see("Website")  # Field label should be visible
    await user.should_see("Api Url")  # Computed field label should be visible

    # Verify URLs are rendered as links
    await user.should_see("https://example.com/")  # URL should be visible
    await user.should_see("https://example.com/api")  # Computed URL should be visible
    await user.should_see(kind=ui.link)  # Both URLs should be links


async def test_message_shows_notification(user: User) -> None:
    """Test that message() shows a notification."""

    # When
    @ui.page("/test")
    def test_page():
        message("Test message", type="info")

    await user.open("/test")

    # Then
    await user.should_see("Test message")


async def test_show_error_shows_negative_notification(user: User) -> None:
    """Test that show_error() shows a negative notification."""

    # When
    @ui.page("/test")
    def test_page():
        show_error("Test error")

    await user.open("/test")

    # Then
    await user.should_see("Test error")


async def test_menu_shows_navigation_links(user: User) -> None:
    """Test that menu shows navigation links."""

    # When
    @ui.page("/test")
    def test_page():
        menu()

    await user.open("/test")

    # Then - verify menu button is present
    menu_button = user.find(ui.button)
    assert menu_button.elements  # Menu button should exist

    # Verify menu items exist (they're in the DOM, just not visible until clicked)
    menu_items = user.find(ui.menu_item).elements
    assert len(menu_items) == 6
