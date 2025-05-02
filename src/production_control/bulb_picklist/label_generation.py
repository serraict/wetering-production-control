"""Label generation for bulb picklist."""

import os
import tempfile
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import qrcode
from weasyprint import HTML

from ..bulb_picklist.models import BulbPickList


class LabelGenerator:
    """Generate PDF labels for bulb picklist items."""

    def __init__(self):
        """Initialize the label generator."""
        self.template_dir = Path(__file__).parent / "templates"
        self.template_path = self.template_dir / "label.html"

    def generate_qr_code(self, record: BulbPickList, base_url: Optional[str] = None) -> str:
        """
        Generate a QR code for a BulbPickList record.

        The QR code encodes a URL to the detail page for the record.
        Returns a base64 encoded data URL for embedding in HTML.

        Args:
            record: The BulbPickList record to generate a QR code for
            base_url: Optional base URL to use for the QR code. If not provided,
                      a relative URL will be used.
        """
        # Create the URL path
        path = f"/bulb-picking/{record.id}"

        # If a base URL is provided, create a full URL
        if base_url:
            url = urljoin(base_url, path)
        else:
            url = path
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Create an image from the QR code
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert the image to a base64 encoded string
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Return as a data URL
        return f"data:image/png;base64,{img_str}"

    def generate_label_html(self, record: BulbPickList, base_url: Optional[str] = None) -> str:
        """
        Generate HTML for a label from a BulbPickList record.

        Args:
            record: The BulbPickList record to generate a label for
            base_url: Optional base URL to use for the QR code. If not provided,
                      a relative URL will be used.
        """
        with open(self.template_path, "r") as f:
            template = f.read()

        # Generate QR code
        qr_code_data = self.generate_qr_code(record, base_url)

        # Replace template variables with record values
        html = template.replace("{{ ras }}", record.ras)
        html = html.replace("{{ bollen_code }}", str(record.bollen_code))
        html = html.replace("{{ id }}", str(record.id))
        html = html.replace("{{ locatie }}", record.locatie)
        html = html.replace("{{ aantal_bakken }}", str(int(record.aantal_bakken)))
        html = html.replace("{{ qr_code }}", qr_code_data)

        return html

    def generate_pdf(
        self,
        record: BulbPickList,
        output_path: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> str:
        """
        Generate a PDF label for a BulbPickList record.

        Args:
            record: The BulbPickList record to generate a label for
            output_path: Optional path to save the PDF to. If not provided,
                         a temporary file will be created.

        Returns:
            The path to the generated PDF file
        """
        html_content = self.generate_label_html(record, base_url)

        # Create a temporary file if no output path is provided
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)

        # Generate PDF from HTML
        HTML(string=html_content).write_pdf(output_path)

        return output_path
