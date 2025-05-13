"""Label generation for bulb picklist."""

from pathlib import Path
from typing import Dict, Any

from ..bulb_picklist.models import BulbPickList
from ..data.label_generation import BaseLabelGenerator, LabelConfig


# Re-export LabelConfig for backward compatibility
LabelConfig = LabelConfig


class LabelGenerator(BaseLabelGenerator[BulbPickList]):
    """Generate PDF labels for bulb pick list items."""

    def __init__(self):
        """Initialize the label generator."""
        template_dir = Path(__file__).parent / "templates"
        super().__init__(template_dir)

    def get_scan_path(self, record: BulbPickList) -> str:
        """
        Get the scan path for a BulbPickList record.

        Args:
            record: The BulbPickList record to get the scan path for

        Returns:
            The scan path for the record
        """
        return f"/bulb-picking/scan/{record.id}"

    def _prepare_record_data(self, record: BulbPickList, base_url: str = "") -> Dict[str, Any]:
        """
        Prepare record data for template rendering.

        Args:
            record: The BulbPickList record to prepare data for
            base_url: Optional base URL to use for the QR code

        Returns:
            Dictionary with record data ready for template rendering
        """
        # Generate QR code
        qr_code_data = self.generate_qr_code(record, base_url)

        # Create the URL path for display
        display_url = self.get_scan_path(record)
        if base_url:
            from urllib.parse import urljoin

            display_url = urljoin(base_url, display_url)

        # Prepare record data for template
        return {
            "id": record.id,
            "bollen_code": record.bollen_code,
            "ras": record.ras,
            "locatie": record.locatie,
            "aantal_bakken": int(record.aantal_bakken),
            "qr_code": qr_code_data,
            "scan_url": display_url,
            "oppot_week": record.oppot_week,
        }
