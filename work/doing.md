# Doing

In this document we describe what we are working on now.

## Fix Week Number Display for Year-End Dates

**Issue**: The year of week is not printed correctly for dates like 2024-12-30. In week number notation, this should be 25w01-1, but it is displayed as 24w01-1.

**Analysis**:

- The issue exists in two places in the codebase:
  1. `src/production_control/spacing/models.py`: The `WijderzetRegistratie.__str__` method uses `strftime("%yw%V-%u")`
  2. `src/production_control/web/components/table_utils.py`: The `DATE_FORMAT` constant uses `"%gw%V-%u"`

- The key difference is the use of `%y` vs `%g`:
  - `%y`: gives the year without century (24)
  - `%g`: gives the ISO 8601 year without century for the week number (25 for 2024-12-30 since it belongs to week 1 of 2025)

**Plan**:

1. Update the date format in `models.py` to use `%g` instead of `%y` to match the ISO week year
2. Add a test case in `test_date_formatting.py` specifically for dates at year boundaries
