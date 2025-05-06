"""Label generation for bulb picklist."""

import os
import tempfile
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import qrcode
from PIL import Image
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

        The QR code encodes a URL to the scan landing page for the record.
        Returns a base64 encoded data URL for embedding in HTML.

        Args:
            record: The BulbPickList record to generate a QR code for
            base_url: Optional base URL to use for the QR code. If not provided,
                      a relative URL will be used.
        """
        # Create the URL path
        path = f"/bulb-picking/scan/{record.id}"

        # If a base URL is provided, create a full URL
        if base_url:
            url = urljoin(base_url, path)
        else:
            url = path

        # Use higher error correction to allow for the logo overlay
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Higher error correction
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Create an image from the QR code
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

        # Load the Serra icon
        icon_path = Path(__file__).parent.parent / "assets" / "favicon" / "64x64.png"
        icon = Image.open(icon_path).convert("RGBA")

        # Calculate position to center the icon
        qr_width, qr_height = qr_img.size

        # Resize icon to be about 1/5 of the QR code size
        icon_size = qr_width // 5
        icon = icon.resize((icon_size, icon_size), Image.LANCZOS)
        icon_width, icon_height = icon.size

        # Create a white circle background for the icon
        # Create a new image with a white background
        background_size = int(icon_size * 1.5)  # Make the background larger than the icon
        background = Image.new("RGBA", (background_size, background_size), (255, 255, 255, 255))

        # Calculate position to center the icon on the background
        icon_position = ((background_size - icon_width) // 2, (background_size - icon_height) // 2)

        # Paste the icon onto the white background
        background.paste(icon, icon_position, icon)

        # Calculate position to center the background with icon on the QR code
        position = ((qr_width - background_size) // 2, (qr_height - background_size) // 2)

        # Paste the background with icon onto the QR code
        qr_img.paste(background, position, background)

        # Convert the image to a base64 encoded string
        buffered = BytesIO()
        qr_img.save(buffered, format="PNG")
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

        # Create the URL path for display
        path = f"/bulb-picking/scan/{record.id}"
        display_url = path
        if base_url:
            display_url = urljoin(base_url, path)

        # Replace template variables with record values
        html = template.replace("{{ ras }}", record.ras)
        html = html.replace("{{ bollen_code }}", str(record.bollen_code))
        html = html.replace("{{ id }}", str(record.id))
        html = html.replace("{{ locatie }}", record.locatie)
        html = html.replace("{{ aantal_bakken }}", str(int(record.aantal_bakken)))
        html = html.replace("{{ qr_code }}", qr_code_data)
        html = html.replace("{{ scan_url }}", display_url)

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
