"""Script to analyze spacing error types."""

from production_control.spacing.repositories import SpacingRepository


def main():
    """Analyze error types in spacing records."""
    repository = SpacingRepository()
    error_records = repository.get_error_records()

    # Collect unique error messages
    error_types = set()
    for record in error_records:
        if record.wijderzet_registratie_fout:
            error_types.add(record.wijderzet_registratie_fout.strip())

    # Print error types with counts
    print("\nUnique error types found:")
    print("-" * 80)
    for error in sorted(error_types):
        count = sum(
            1
            for r in error_records
            if r.wijderzet_registratie_fout and r.wijderzet_registratie_fout.strip() == error
        )
        print(f"\nError ({count} occurrences):")
        print(error)


if __name__ == "__main__":
    main()
