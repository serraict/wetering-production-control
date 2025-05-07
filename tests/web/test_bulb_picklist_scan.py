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
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        test_record = BulbPickList(
            id=1001,
            bollen_code=12345,
            ras="Tulipa Test",
            locatie="A01-01",
            aantal_bakken=10.0,
            aantal_bollen=100.0,
            oppot_datum=date(2023, 1, 2),
        )
        mock_repo.get_by_id.return_value = test_record

        await user.open("/bulb-picking/scan/1001")
        await user.should_see("Bollen Picklist")
        await user.should_see("Tulipa Test")
