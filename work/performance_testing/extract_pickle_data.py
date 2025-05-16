#!/usr/bin/env python
"""
Extract data from pickle file.

This script extracts data from the pickle file and saves it in a format
that's easier to work with for performance testing.
"""

import sys
import json
from pathlib import Path


def extract_data():
    """Extract data from pickle file."""
    pickle_path = Path("work/performance_testing/data/bulb_picklist_table_state.pkl")
    json_path = Path("work/performance_testing/data/bulb_picklist_data.json")

    if not pickle_path.exists():
        print(f"Error: {pickle_path} does not exist.")
        return

    # Read the pickle file as binary
    with open(pickle_path, "rb") as f:
        data = f.read()

    # Convert to hex for inspection
    hex_data = data.hex()
    print(f"Pickle file size: {len(data)} bytes")
    print(f"First 100 bytes (hex): {hex_data[:200]}")

    # Look for JSON-like structures in the data
    try:
        # Convert to string for inspection
        str_data = data.decode("latin1", errors="ignore")
        
        # Look for patterns that might indicate the start of record data
        print("\nSearching for record data patterns...")
        
        # Print some sample of the string data
        print(f"Sample of string data: {str_data[:1000]}")
        
        # Save the string data to a file for manual inspection
        with open(json_path.with_suffix(".txt"), "w") as f:
            f.write(str_data)
        
        print(f"Saved string data to {json_path.with_suffix('.txt')} for manual inspection")
    except Exception as e:
        print(f"Error extracting data: {e}")


if __name__ == "__main__":
    extract_data()
