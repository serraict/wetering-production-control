"""Common label generation functionality."""

import os
import tempfile
import base64
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, TypeVar, Generic
from urllib.parse import urljoin

import jinja2
import qrcode
from PIL import Image
from weasyprint import HTML
from nicegui import ui

# Generic type for record models
T = TypeVar('T')


class LabelConfig:
    """Configuration for label generation."""

    # Default dimensions
    DEFAULT_WIDTH = "151mm"
    DEFAULT_HEIGHT = "101mm"

    def __init__(
        self,
        width: str = DEFAULT_WIDTH,
        height: str = DEFAULT_HEIGHT,
        base_url: str = "",
    ):
        """
        Initialize label configuration.

        Args:
            width: Width of the label
            height: Height of the label
            base_url: Base URL for QR codes
        """
        self.width = width
        self.height = height
        self.base_url = base_url

    @classmethod
    def from_env(cls) -> "LabelConfig":
        """
        Create a LabelConfig from environment variables.

        Uses the following environment variables:
        - LABEL_WIDTH: Width of the label (default: 151mm)
        - LABEL_HEIGHT: Height of the label (default: 101mm)
        - QR_CODE_BASE_URL: Base URL for QR codes (default: "")

        Returns:
            LabelConfig instance with values from environment variables
        """
        return cls(
            width=os.environ.get("LABEL_WIDTH", cls.DEFAULT_WIDTH),
            height=os.environ.get("LABEL_HEIGHT", cls.DEFAULT_HEIGHT),
            base_url=os.environ.get("QR_CODE_BASE_URL", ""),
        )


class BaseLabelGenerator(Generic[T]):
    """Base class for generating PDF labels."""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the label generator.

        Args:
            template_dir: Optional directory containing templates. If not provided,
                          subclasses must override this.
        """
        self.template_dir = template_dir

        # Initialize Jinja2 environment if template_dir is provided
        if self.template_dir:
            self.jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(self.template_dir),
                autoescape=jinja2.select_autoescape(["html", "xml"]),
            )

    def get_scan_path(self, record: T) -> str:
        """
        Get the scan path for a record.

        Args:
            record: The record to get the scan path for

        Returns:
            The scan path for the record

        Note:
            This method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement get_scan_path")

    def generate_qr_code(self, record: T, base_url: str = "") -> str:
        """
        Generate a QR code for a record.

        The QR code encodes a URL to the scan landing page for the record.
        Returns a base64 encoded data URL for embedding in HTML.

        Args:
            record: The record to generate a QR code for
            base_url: Optional base URL to use for the QR code. If not provided,
                      a relative URL will be used.
        """
        # Create the URL path
        path = self.get_scan_path(record)

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

    def _prepare_record_data(self, record: T, base_url: str = "") -> Dict[str, Any]:
        """
        Prepare record data for template rendering.

        Args:
            record: The record to prepare data for
            base_url: Optional base URL to use for the QR code

        Returns:
            Dictionary with record data ready for template rendering

        Note:
            This method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _prepare_record_data")

    def generate_labels_html(
        self,
        records: Union[T, List[T]],
        config: Optional[LabelConfig] = None,
    ) -> str:
        """
        Generate HTML for one or more labels.

        Args:
            records: A single record or a list of records
            config: Label configuration (dimensions and base URL)

        Returns:
            HTML string containing all labels
        """
        # Use default config if none provided
        if config is None:
            config = LabelConfig()

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
            )

        # Prepare data for all records
        records_data = [self._prepare_record_data(record, config.base_url) for record in records]

        # Use the provided dimensions
        page_size = f"{config.width} {config.height}"

        # Render template with Jinja2
        template = self.jinja_env.get_template("labels.html.jinja2")
        html = template.render(
            records=records_data,
            labels=records_data,  # For backward compatibility
            page_size=page_size,
            label_width=config.width,
            label_height=config.height,
        )

        return html

    def generate_pdf(
        self,
        records: Union[T, List[T]],
        config: Optional[LabelConfig] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate a PDF with one or more labels.

        Args:
            records: A single record or a list of records
            config: Label configuration (dimensions and base URL)
            output_path: Optional path to save the PDF to. If not provided,
                         a temporary file will be created.

        Returns:
            The path to the generated PDF file
        """
        # Use default config if none provided
        if config is None:
            config = LabelConfig()

        html_content = self.generate_labels_html(records, config)

        # Create a temporary file if no output path is provided
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)

        # Generate PDF from HTML
        HTML(string=html_content).write_pdf(output_path)

        return output_path

    def cleanup_pdf(self, pdf_path: str, delay: int = 5) -> None:
        """
        Schedule cleanup of a temporary PDF file.

        Args:
            pdf_path: Path to the PDF file to clean up
            delay: Delay in seconds before cleanup (default: 5)
        """

        def cleanup():
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        ui.timer(delay, cleanup, once=True)
