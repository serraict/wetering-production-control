"""Label generation for bulb picklist."""

from pathlib import Path
from typing import Dict, Any, List, Union

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

    def _prepare_record_data(
        self, record: BulbPickList, base_url: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Prepare record data for template rendering, creating multiple records for pallets if needed.

        Args:
            record: The record to prepare data for
            base_url: Optional base URL to use for the QR code

        Returns:
            List of dictionaries with record data ready for template rendering
        """
        # Calculate number of pallets needed
        pallet_count = record.pallet_count

        if pallet_count <= 0:
            return []

        # Create a record for each pallet
        result = []
        for pallet_num in range(1, pallet_count + 1):
            # Get base record data from parent class
            record_dict = super()._prepare_record_data(record, base_url)

            # Add pallet information
            record_dict["pallet_number"] = pallet_num
            record_dict["total_pallets"] = pallet_count
            record_dict["pallet_info"] = f"Pallet {pallet_num}/{pallet_count}"

            result.append(record_dict)

        return result

    def generate_labels_html(
        self,
        records: Union[BulbPickList, List[BulbPickList]],
        config=None,
    ) -> str:
        """
        Generate HTML for one or more labels, with support for multiple pallets.

        Args:
            records: A single record or a list of records
            config: Label configuration (dimensions and base URL)

        Returns:
            HTML string containing all labels
        """
        # Use default config if none provided
        if config is None:
            config = self._default_config

        # Handle single record case
        if not isinstance(records, list):
            records = [records]

        if not records:
            # Return empty template if no records
            template = self.jinja_env.get_template("labels.html.jinja2")
            return template.render(
                records=[],
                labels=[],  # For backward compatibility
                page_size=f"{config.width} {config.height}",
                label_width=config.width,
                label_height=config.height,
                title="Labels",
            )

        # Prepare data for all records, expanding for multiple pallets
        all_records_data = []
        for record in records:
            all_records_data.extend(self._prepare_record_data(record, config.base_url))

        # Use the provided dimensions
        page_size = f"{config.width} {config.height}"

        # Render template with Jinja2
        template = self.jinja_env.get_template("labels.html.jinja2")
        html = template.render(
            records=all_records_data,
            labels=all_records_data,  # For backward compatibility
            page_size=page_size,
            label_width=config.width,
            label_height=config.height,
            title="Labels",
        )

        return html
