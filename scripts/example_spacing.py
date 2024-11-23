"""Example script to demonstrate retrieving spacing data from Dremio."""

import os
from production_control.spacing.repository import SpacingRepository


def main():
    """Main function to demonstrate spacing data retrieval."""
    # Get connection string from environment variable
    conn_str = os.getenv(
        "VINEAPP_DB_CONNECTION", "dremio+flight://localhost:32010/dremio?UseEncryption=false"
    )

    # Create repository
    repository = SpacingRepository(conn_str)

    try:
        # Get first page of spacing records
        registraties, total = repository.get_paginated(page=1, items_per_page=50)

        print(f"\nFound {total} spacing records. Showing first {len(registraties)}:")
        for reg in registraties:
            print(f"\nBatch {reg.partij_code} - {reg.product_naam}:")
            print(f"  Plants realized: {reg.aantal_planten_gerealiseerd}")
            print(f"  Total tables: {reg.aantal_tafels_totaal}")
            print(f"  Tables after spacing 1: {reg.aantal_tafels_na_wdz1}")
            print(f"  Tables after spacing 2: {reg.aantal_tafels_na_wdz2}")
            print(f"  Spacing error: {'Yes' if reg.wijderzet_registratie_fout else 'No'}")

        # Try filtering
        print("\nFiltering records with 'TEST':")
        filtered, total = repository.get_paginated(page=1, items_per_page=5, filter_text="TEST")
        print(f"Found {total} matching records")
        for reg in filtered:
            print(f"- {reg.partij_code}: {reg.product_naam}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
