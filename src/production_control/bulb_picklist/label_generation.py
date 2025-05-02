"""Label generation for bulb picklist."""

import os
import tempfile
from pathlib import Path
from typing import Optional

from weasyprint import HTML

from ..bulb_picklist.models import BulbPickList


class LabelGenerator:
    """Generate PDF labels for bulb picklist items."""

    def __init__(self):
        """Initialize the label generator."""
        self.template_dir = Path(__file__).parent / "templates"
        self.template_path = self.template_dir / "label.html"

    def generate_label_html(self, record: BulbPickList) -> str:
        """Generate HTML for a label from a BulbPickList record."""
        with open(self.template_path, "r") as f:
            template = f.read()

        # Replace template variables with record values
        html = template.replace("{{ ras }}", record.ras)
        html = html.replace("{{ bollen_code }}", str(record.bollen_code))
        html = html.replace("{{ id }}", str(record.id))
        html = html.replace("{{ locatie }}", record.locatie)
        html = html.replace("{{ aantal_bakken }}", str(int(record.aantal_bakken)))

        return html

    def generate_pdf(self, record: BulbPickList, output_path: Optional[str] = None) -> str:
        """
        Generate a PDF label for a BulbPickList record.

        Args:
            record: The BulbPickList record to generate a label for
            output_path: Optional path to save the PDF to. If not provided,
                         a temporary file will be created.

        Returns:
            The path to the generated PDF file
        """
        html_content = self.generate_label_html(record)

        # Create a temporary file if no output path is provided
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)

        # Generate PDF from HTML
        HTML(string=html_content).write_pdf(output_path)

        return output_path
