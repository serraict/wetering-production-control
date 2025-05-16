#!/usr/bin/env python
"""
Run performance tests for label generation.

This script loads the saved table state and runs performance tests
for different parts of the label generation process.
"""

import os
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Callable
import cProfile
import pstats
from functools import wraps

from production_control.bulb_picklist.models import BulbPickList
from production_control.bulb_picklist.label_generation import LabelGenerator


def timing_decorator(func):
    """Decorator to measure execution time of a function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result, execution_time

    return wrapper


@timing_decorator
def convert_rows_to_records(rows: List[Dict[str, Any]]) -> List[BulbPickList]:
    """Convert row dictionaries to BulbPickList objects."""
    return [BulbPickList(**row) for row in rows]


@timing_decorator
def generate_qr_codes(records: List[BulbPickList]) -> List[str]:
    """Generate QR codes for records."""
    label_generator = LabelGenerator()
    return [label_generator.generate_qr_code(record) for record in records]


@timing_decorator
def prepare_record_data(records: List[BulbPickList]) -> List[Dict[str, Any]]:
    """Prepare record data for template rendering."""
    label_generator = LabelGenerator()
    return [label_generator._prepare_record_data(record) for record in records]


@timing_decorator
def generate_labels_html(records: List[BulbPickList]) -> str:
    """Generate HTML for labels."""
    label_generator = LabelGenerator()
    return label_generator.generate_labels_html(records)


@timing_decorator
def generate_pdf(records: List[BulbPickList], output_dir: Path = None) -> str:
    """
    Generate PDF for labels.

    Args:
        records: List of records to generate labels for
        output_dir: Optional directory to save the PDF to

    Returns:
        Path to the generated PDF file
    """
    # This matches exactly what happens in the UI
    label_generator = LabelGenerator()

    # Create a descriptive filename
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        batch_size = len(records) if isinstance(records, list) else 1
        output_path = output_dir / f"labels_batch_{batch_size}.pdf"
        return label_generator.generate_pdf(records, output_path=str(output_path))
    else:
        return label_generator.generate_pdf(records)


def profile_function(func: Callable, *args, **kwargs) -> pstats.Stats:
    """Profile a function and return stats."""
    profile = cProfile.Profile()
    profile.enable()
    func(*args, **kwargs)
    profile.disable()
    return pstats.Stats(profile)


def run_tests(
    rows: List[Dict[str, Any]], batch_sizes: List[int] = None, save_pdfs: bool = True
) -> None:
    """
    Run performance tests for different batch sizes.

    Args:
        rows: List of row dictionaries from table state
        batch_sizes: List of batch sizes to test (default: [1, 10, 25, 50])
    """
    if batch_sizes is None:
        batch_sizes = [1, 10, 25, 50]

    # Ensure we have enough rows for the largest batch size
    max_batch_size = max(batch_sizes)
    if len(rows) < max_batch_size:
        print(f"Warning: Not enough rows ({len(rows)}) for largest batch size ({max_batch_size})")
        batch_sizes = [size for size in batch_sizes if size <= len(rows)]

    # Convert all rows to records first - this matches what happens in handle_print_all
    all_records, _ = convert_rows_to_records(rows)

    # Print information about the records
    total_pallets = sum(record.pallet_count for record in all_records)
    print(f"Total records: {len(all_records)}")
    print(f"Total pallets: {total_pallets}")
    print(
        f"Average pallets per record: {total_pallets / len(all_records) if all_records else 0:.2f}"
    )

    # Print pallet distribution
    pallet_counts = {}
    for record in all_records:
        pallet_counts[record.pallet_count] = pallet_counts.get(record.pallet_count, 0) + 1

    print("Pallet count distribution:")
    for pallet_count, count in sorted(pallet_counts.items()):
        print(f"  {pallet_count} pallets: {count} records")

    # Run tests for each batch size
    results = {}
    for batch_size in batch_sizes:
        print(f"\n=== Testing with batch size: {batch_size} ===")

        # Select a random subset of records
        batch_records = random.sample(all_records, batch_size)

        # Test each component
        _, qr_time = generate_qr_codes(batch_records)
        _, prepare_time = prepare_record_data(batch_records)
        _, html_time = generate_labels_html(batch_records)

        # Test full PDF generation
        output_dir = Path("work/performance_testing/output") if save_pdfs else None

        try:
            _, pdf_time = generate_pdf(batch_records, output_dir)

            # Store results
            results[batch_size] = {
                "qr_code_time": qr_time,
                "prepare_data_time": prepare_time,
                "html_time": html_time,
                "pdf_time": pdf_time,
                "total_time": qr_time + prepare_time + html_time + pdf_time,
                "time_per_record": (qr_time + prepare_time + html_time + pdf_time) / batch_size,
            }
        except Exception as e:
            print(f"Error generating PDF: {e}")

    # Print summary
    print("\n=== Summary ===")
    print(
        f"{'Batch Size':<10} {'QR Code':<10} {'Prepare':<10} {'HTML':<10} {'PDF':<10} {'Total':<10} {'Per Record':<10}"
    )
    for batch_size, result in sorted(results.items()):
        print(
            f"{batch_size:<10} "
            f"{result['qr_code_time']:.4f}s    "
            f"{result['prepare_data_time']:.4f}s    "
            f"{result['html_time']:.4f}s    "
            f"{result['pdf_time']:.4f}s    "
            f"{result['total_time']:.4f}s    "
            f"{result['time_per_record']:.4f}s"
        )

    # Profile the slowest component for the largest batch size
    if results:
        largest_batch = max(results.keys())
        result = results[largest_batch]
        slowest_component = max(
            ["qr_code_time", "prepare_data_time", "html_time", "pdf_time"], key=lambda k: result[k]
        )

        print(
            f"\n=== Profiling the slowest component ({slowest_component}) for batch size {largest_batch} ==="
        )

        if slowest_component == "qr_code_time":
            stats = profile_function(generate_qr_codes, all_records[:largest_batch])
        elif slowest_component == "prepare_data_time":
            stats = profile_function(prepare_record_data, all_records[:largest_batch])
        elif slowest_component == "html_time":
            stats = profile_function(generate_labels_html, all_records[:largest_batch])
        else:  # pdf_time
            stats = profile_function(generate_pdf, all_records[:largest_batch])

        # Print top 10 time-consuming functions
        stats.strip_dirs().sort_stats("cumulative").print_stats(10)


def load_test_data(path: Path) -> List[Dict[str, Any]]:
    """
    Load test data from JSON file.

    Args:
        path: Path to the JSON file

    Returns:
        List of row dictionaries
    """
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading test data: {e}")
        return []


if __name__ == "__main__":
    # Load the test data
    data_path = Path("work/performance_testing/data/test_data.json")

    if not data_path.exists():
        print(f"Error: {data_path} does not exist.")
        print("Please run create_test_data.py first to create test data.")
        exit(1)

    # Load the test data
    rows = load_test_data(data_path)

    print(f"Loaded {len(rows)} rows from {data_path}")

    # Create output directory
    output_dir = Path("work/performance_testing/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"PDFs will be saved to {output_dir.absolute()}")

    # Run tests
    run_tests(rows, save_pdfs=True)
