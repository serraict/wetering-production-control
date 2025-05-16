#!/usr/bin/env python
"""
Create test data for performance testing.

This script creates test data with a variety of pallet counts,
similar to what we would expect in the real data.
"""

import json
import random
from pathlib import Path
from datetime import date, timedelta


# Create test data
def create_test_data(num_records=50):
    """
    Create test data with a variety of pallet counts.

    Args:
        num_records: Number of records to create

    Returns:
        List of dictionaries with test data
    """
    test_data = []

    # Create records with varying pallet counts
    for i in range(num_records):
        # Randomly choose aantal_bakken to get different pallet counts
        # 1 pallet = 1-25 boxes
        # 2 pallets = 26-50 boxes
        # 3 pallets = 51-75 boxes
        # etc.
        aantal_bakken = random.randint(1, 125)

        # Calculate pallet count (not used in the record, but useful for debugging)
        _ = (aantal_bakken + 24) // 25  # Ceiling division

        # Generate random date in the past year
        random_date = date.today() - timedelta(days=random.randint(0, 365))

        # Create record
        record = {
            "id": i + 1,
            "bollen_code": 10000 + i,
            "ras": f"Variety {i + 1}",
            "locatie": f"Location {(i % 10) + 1}",
            "aantal_bakken": aantal_bakken,
            "aantal_bollen": aantal_bakken * 40,  # 40 bulbs per box
            "oppot_datum": random_date.isoformat(),
            "oppot_week": f"{random_date.isocalendar()[1]}",
            "artikel": f"Article {(i % 5) + 1}",
        }

        test_data.append(record)

    return test_data


if __name__ == "__main__":
    # Create test data
    test_data = create_test_data(50)

    # Print summary
    pallet_counts = {}
    for record in test_data:
        pallet_count = (record["aantal_bakken"] + 24) // 25
        pallet_counts[pallet_count] = pallet_counts.get(pallet_count, 0) + 1

    print("Pallet count distribution:")
    for pallet_count, count in sorted(pallet_counts.items()):
        print(f"  {pallet_count} pallets: {count} records")

    # Save to JSON file
    output_path = Path("work/performance_testing/data/test_data.json")
    with open(output_path, "w") as f:
        json.dump(test_data, f, indent=2)

    print(f"Saved {len(test_data)} records to {output_path}")
