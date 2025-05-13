"""Label generation for potting lots."""

from pathlib import Path

from ..potting_lots.models import PottingLot
from ..data.label_generation import BaseLabelGenerator


class LabelGenerator(BaseLabelGenerator[PottingLot]):
    """Generate PDF labels for potting lot items."""

    def __init__(self):
        """Initialize the label generator."""
        template_dir = Path(__file__).parent / "templates"
        super().__init__(template_dir)

    def get_scan_path(self, record: PottingLot) -> str:
        return f"/potting-lots/scan/{record.id}"
