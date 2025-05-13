"""Label generation for bulb picklist."""

from pathlib import Path

from ..bulb_picklist.models import BulbPickList
from ..data.label_generation import BaseLabelGenerator


class LabelGenerator(BaseLabelGenerator[BulbPickList]):
    """Generate PDF labels for bulb pick list items."""

    def __init__(self):
        """Initialize the label generator."""
        template_dir = Path(__file__).parent / "templates"
        super().__init__(template_dir)

    def get_scan_path(self, record: BulbPickList) -> str:
        return f"/bulb-picking/scan/{record.id}"
