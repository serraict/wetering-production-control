"""Tests for bulb picklist scan landing page."""

from datetime import date
from unittest.mock import patch, MagicMock

from nicegui.testing import User

from production_control.bulb_picklist.models import BulbPickList


async def test_bulb_picklist_scan_page_exists(user: User) -> None:
    """Test that the bulb picklist scan landing page exists."""
    with patch(
        "production_control.web.pages.bulb_picklist.BulbPickListRepository"
    ) as mock_repo_class:
        # Given
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        test_date = date(2023, 1, 2)
        test_record = BulbPickList(
            id=1001,
            bollen_code=12345,
            ras="Tulipa Test",
            locatie="A01-01",
            aantal_bakken=10.0,
            aantal_bollen=100.0,
            oppot_datum=test_date,
        )
        mock_repo.get_by_id.return_value = test_record

        # When
        await user.open("/bulb-picking/scan/1001")

        # Then
        # Verify that the page title is displayed
        title = user.find(content="Bollen Picklist Scan").elements.pop()
        assert "Bollen Picklist Scan" in title.text

        # Verify that the record details are displayed
        content = user.find(content="Tulipa Test").elements.pop()
        assert "Tulipa Test" in content.text
        assert "12345" in content.text
