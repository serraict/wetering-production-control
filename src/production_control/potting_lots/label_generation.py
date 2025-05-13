"""Label generation for potting lots."""

from pathlib import Path
from typing import Union, List

from ..potting_lots.models import PottingLot
from ..data.label_generation import BaseLabelGenerator, LabelConfig


class LabelGenerator(BaseLabelGenerator[PottingLot]):
    """Generate PDF labels for potting lot items."""

    def __init__(self):
        """Initialize the label generator."""
        template_dir = Path(__file__).parent / "templates"
        super().__init__(template_dir)

    def get_scan_path(self, record: PottingLot) -> str:
        return f"/potting-lots/scan/{record.id}"

    def generate_labels_html(
        self,
        records: Union[PottingLot, List[PottingLot]],
        config: LabelConfig = None,
    ) -> str:
        """
        Generate HTML for one or more labels, duplicating each record.

        For each potting lot, two identical labels are generated:
        - One for the first pot of the lot
        - One for the last pot of the lot

        Args:
            records: A single record or a list of records
            config: Label configuration (dimensions and base URL)

        Returns:
            HTML string containing all labels
        """
        # Handle single record case
        if not isinstance(records, list):
            records = [records]

        # Duplicate each record to generate two identical labels
        duplicated_records = []
        for record in records:
            # Add the record twice
            duplicated_records.append(record)
            duplicated_records.append(record)

        # Call the parent class method with the duplicated records
        return super().generate_labels_html(duplicated_records, config)
