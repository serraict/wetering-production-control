#!/usr/bin/env python
"""
Optimized label generator for performance testing.

This script provides an optimized version of the label generator
with various performance improvements.
"""

import os
import tempfile
import base64
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from functools import lru_cache
import time
import concurrent.futures
import threading

import qrcode
from weasyprint import HTML
# No need for these imports since we're using the parent class's Jinja environment

from production_control.bulb_picklist.models import BulbPickList
from production_control.bulb_picklist.label_generation import LabelGenerator
from production_control.data.label_generation import LabelConfig


class OptimizedLabelGenerator(LabelGenerator):
    """Optimized label generator with performance improvements."""

    def __init__(self):
        """Initialize the optimized label generator."""
        super().__init__()
        # Thread-local storage for QR code generation
        self._thread_local = threading.local()
        # We'll use the parent class's Jinja environment which is already properly configured
        # with both module-specific and common templates
        self._labels_template = self.jinja_env.get_template("labels.html.jinja2")

    @lru_cache(maxsize=128)
    def generate_qr_code(self, record_id: int, base_url: str = "") -> str:
        """
        Generate a QR code for a record with caching.

        Args:
            record_id: The ID of the record to generate a QR code for
            base_url: Optional base URL to use for the QR code

        Returns:
            Base64 encoded data URL for the QR code
        """
        # Get or create QR code generator
        if not hasattr(self._thread_local, "qr"):
            self._thread_local.qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

        # Generate QR code
        qr = self._thread_local.qr
        qr.clear()
        qr.add_data(f"{base_url}/bulb-picking/scan/{record_id}")
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def _prepare_record_data_parallel(
        self, records: List[BulbPickList], base_url: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Prepare record data for template rendering in parallel.

        Args:
            records: The records to prepare data for
            base_url: Optional base URL to use for the QR code

        Returns:
            List of dictionaries with record data ready for template rendering
        """
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Generate QR codes in parallel
            qr_codes = list(
                executor.map(
                    lambda record: self.generate_qr_code(record.id, base_url),
                    records
                )
            )

        # Prepare record data
        all_record_data = []
        for i, record in enumerate(records):
            # Calculate pallet count
            pallet_count = record.pallet_count

            # Create a record for each pallet
            for pallet_number in range(1, pallet_count + 1):
                record_data = {
                    "id": record.id,
                    "bollen_code": record.bollen_code,
                    "ras": record.ras,
                    "locatie": record.locatie,
                    "aantal_bakken": record.aantal_bakken,
                    "aantal_bollen": record.aantal_bollen,
                    "oppot_datum": record.oppot_datum,
                    "oppot_week": record.oppot_week,
                    "artikel": record.artikel,
                    "qr_code": qr_codes[i],
                    "pallet_number": pallet_number,
                    "total_pallets": pallet_count,
                    "pallet_info": f"Pallet {pallet_number}/{pallet_count}",
                }
                all_record_data.append(record_data)

        return all_record_data

    def generate_labels_html(
        self,
        records: Union[BulbPickList, List[BulbPickList]],
        config=None,
    ) -> str:
        """
        Generate HTML for one or more labels with optimized template rendering.

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
            return ""

        # Prepare record data in parallel
        all_record_data = self._prepare_record_data_parallel(records, config.base_url)

        # Render template directly with Jinja2
        html = self._labels_template.render(
            records=all_record_data,
            labels=all_record_data,  # For backward compatibility
            page_size=f"{config.width} {config.height}",
            label_width=config.width,
            label_height=config.height,
            title="Labels",
        )

        return html

    def generate_pdf(
        self,
        records: Union[BulbPickList, List[BulbPickList]],
        config: Optional[LabelConfig] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate a PDF with one or more labels with optimized batch processing.

        Args:
            records: A single record or a list of records
            config: Label configuration (dimensions and base URL)
            output_path: Optional path to save the PDF to

        Returns:
            The path to the generated PDF file
        """
        # Use default config if none provided
        if config is None:
            config = self._default_config

        # Generate HTML content
        html_content = self.generate_labels_html(records, config)

        # Create a temporary file if no output path is provided
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)

        # Generate PDF from HTML with optimized settings
        HTML(string=html_content).write_pdf(
            output_path,
            # Use optimized settings for WeasyPrint
            presentational_hints=True,
            optimize_size=('fonts', 'images'),
        )

        return output_path


def run_performance_comparison(records: List[BulbPickList], batch_sizes: List[int] = None):
    """
    Run a performance comparison between the original and optimized label generators.

    Args:
        records: List of records to test with
        batch_sizes: List of batch sizes to test (default: [1, 10, 25, 50])
    """
    if batch_sizes is None:
        batch_sizes = [1, 10, 25, 50]

    # Ensure we have enough records for the largest batch size
    max_batch_size = max(batch_sizes)
    if len(records) < max_batch_size:
        print(f"Warning: Not enough records ({len(records)}) for largest batch size ({max_batch_size})")
        batch_sizes = [size for size in batch_sizes if size <= len(records)]

    # Create generators
    original_generator = LabelGenerator()
    optimized_generator = OptimizedLabelGenerator()

    # Create output directory
    output_dir = Path("work/performance_testing/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run tests for each batch size
    results = {}
    for batch_size in batch_sizes:
        print(f"\n=== Testing with batch size: {batch_size} ===")

        # Select a subset of records
        batch_records = records[:batch_size]

        # Test original generator
        print("\nOriginal Generator:")
        start_time = time.time()
        original_path = output_dir / f"original_batch_{batch_size}.pdf"
        original_generator.generate_pdf(batch_records, output_path=str(original_path))
        original_time = time.time() - start_time
        print(f"Total time: {original_time:.4f} seconds")
        print(f"PDF saved to: {original_path}")

        # Test optimized generator
        print("\nOptimized Generator:")
        start_time = time.time()
        optimized_path = output_dir / f"optimized_batch_{batch_size}.pdf"
        optimized_generator.generate_pdf(batch_records, output_path=str(optimized_path))
        optimized_time = time.time() - start_time
        print(f"Total time: {optimized_time:.4f} seconds")
        print(f"PDF saved to: {optimized_path}")

        # Calculate improvement
        improvement = (original_time - optimized_time) / original_time * 100
        print(f"Improvement: {improvement:.1f}%")

        # Store results
        results[batch_size] = {
            "original": original_time,
            "optimized": optimized_time,
            "improvement": improvement,
        }

    # Print summary
    print("\n=== Summary ===")
    print(f"{'Batch Size':<10} {'Original':<10} {'Optimized':<10} {'Improvement':<10}")
    for batch_size, result in sorted(results.items()):
        print(
            f"{batch_size:<10} "
            f"{result['original']:.4f}s    "
            f"{result['optimized']:.4f}s    "
            f"{result['improvement']:.1f}%"
        )


if __name__ == "__main__":
    # Import here to avoid circular imports
    import json
    from production_control.bulb_picklist.models import BulbPickList

    # Load test data
    data_path = Path("work/performance_testing/data/test_data.json")
    if not data_path.exists():
        print(f"Error: {data_path} does not exist.")
        print("Please run create_test_data.py first to create test data.")
        exit(1)

    # Load the test data
    with open(data_path, "r") as f:
        rows = json.load(f)

    # Convert to records
    records = [BulbPickList(**row) for row in rows]

    # Run performance comparison
    run_performance_comparison(records)
