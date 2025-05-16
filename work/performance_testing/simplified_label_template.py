#!/usr/bin/env python
"""
Simplified label template for performance testing.

This script tests the impact of simplifying the HTML/CSS layout
on label generation performance.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

from weasyprint import HTML
import jinja2

from production_control.bulb_picklist.models import BulbPickList
from production_control.bulb_picklist.label_generation import LabelGenerator
from production_control.data.label_generation import LabelConfig


# Simplified template without flexbox, borders, or QR codes
SIMPLIFIED_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        @page {
            size: {{ page_size }};
            margin: 0;
            padding: 0;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }
        .label {
            width: {{ label_width }};
            height: {{ label_height }};
            padding: 5mm;
            box-sizing: border-box;
            page-break-after: always;
        }
        .label-content {
            width: 100%;
            height: 100%;
        }
        .label-header {
            font-size: 14pt;
            font-weight: bold;
            margin-bottom: 5mm;
        }
        .label-info {
            font-size: 12pt;
            margin-bottom: 3mm;
        }
        .label-footer {
            font-size: 10pt;
            margin-top: 5mm;
        }
    </style>
</head>
<body>
    {% for record in records %}
    <div class="label">
        <div class="label-content">
            <div class="label-header">
                {{ record.bollen_code }} - {{ record.ras }}
            </div>
            <div class="label-info">
                Locatie: {{ record.locatie }}
            </div>
            <div class="label-info">
                Aantal bakken: {{ record.aantal_bakken }}
            </div>
            <div class="label-info">
                Aantal bollen: {{ record.aantal_bollen }}
            </div>
            <div class="label-info">
                Oppot datum: {{ record.oppot_datum }}
            </div>
            <div class="label-info">
                Oppot week: {{ record.oppot_week }}
            </div>
            <div class="label-info">
                Artikel: {{ record.artikel }}
            </div>
            <div class="label-footer">
                {{ record.pallet_info }}
            </div>
        </div>
    </div>
    {% endfor %}
</body>
</html>
"""


class SimplifiedLabelGenerator(LabelGenerator):
    """Label generator with simplified template."""

    def __init__(self):
        """Initialize the simplified label generator."""
        super().__init__()
        # Create a template environment with the simplified template
        self._template_env = jinja2.Environment(autoescape=True)
        self._template = self._template_env.from_string(SIMPLIFIED_TEMPLATE)

    def generate_labels_html(
        self,
        records: Union[BulbPickList, List[BulbPickList]],
        config=None,
    ) -> str:
        """
        Generate HTML for one or more labels with simplified template.

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

        # Prepare record data (without QR codes)
        all_record_data = []
        for record in records:
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
                    "pallet_number": pallet_number,
                    "total_pallets": pallet_count,
                    "pallet_info": f"Pallet {pallet_number}/{pallet_count}",
                }
                all_record_data.append(record_data)

        # Render template
        html = self._template.render(
            records=all_record_data,
            page_size=f"{config.width} {config.height}",
            label_width=config.width,
            label_height=config.height,
            title="Simplified Labels",
        )

        return html

    def generate_pdf(
        self,
        records: Union[BulbPickList, List[BulbPickList]],
        config: Optional[LabelConfig] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate a PDF with one or more labels with simplified template.

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

        # Generate PDF from HTML
        HTML(string=html_content).write_pdf(output_path)

        return output_path


def run_simplified_template_test(records: List[BulbPickList], batch_sizes: List[int] = None):
    """
    Run a performance test with simplified template.

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
    simplified_generator = SimplifiedLabelGenerator()

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

        # Test simplified generator
        print("\nSimplified Generator:")
        start_time = time.time()
        simplified_path = output_dir / f"simplified_batch_{batch_size}.pdf"
        simplified_generator.generate_pdf(batch_records, output_path=str(simplified_path))
        simplified_time = time.time() - start_time
        print(f"Total time: {simplified_time:.4f} seconds")
        print(f"PDF saved to: {simplified_path}")

        # Calculate improvement
        improvement = (original_time - simplified_time) / original_time * 100
        print(f"Improvement: {improvement:.1f}%")

        # Store results
        results[batch_size] = {
            "original": original_time,
            "simplified": simplified_time,
            "improvement": improvement,
        }

    # Print summary
    print("\n=== Summary ===")
    print(f"{'Batch Size':<10} {'Original':<10} {'Simplified':<10} {'Improvement':<10}")
    for batch_size, result in sorted(results.items()):
        print(
            f"{batch_size:<10} "
            f"{result['original']:.4f}s    "
            f"{result['simplified']:.4f}s    "
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

    # Run performance test with simplified template
    run_simplified_template_test(records)
