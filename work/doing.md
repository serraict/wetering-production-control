# Doing

## Goal: The user can print labels so that he can efficiently pick the crates with bulbs

Details: there is a table in `Productie.Oppotten` with the bulb picklist.

We need a screen that show the records in this table, sorted descending order by oppot week and location.

In this list, the user can select rows and then generate a pdf document with labels.

## High level design

Based on data exploration, we'll implement the following:

### Data Model

We'll create a `BulbPickList` model that maps to the `Productie.Oppotten."bollen_pick_lijst"` table with the following fields:
- `oppot_datum`: Date - The planting date
- `oppot_week`: Integer (computed) - The week number extracted from oppot_datum
- `ras`: String - The bulb variety name
- `bollen_code`: Integer - The bulb code
- `locatie`: String - The storage location
- `aantal_bakken`: Float - Number of trays
- `aantal_bollen`: Float - Number of bulbs
- Additional fields as needed

### Web Interface

We'll create a new page at `/bulb-picking` that displays:
- A table showing the bulb pick list data
- Sorting by oppot week (descending) and location
- Row selection functionality
- A "Select All" button
- A "Print Labels" button that generates PDF labels for selected rows

### Label Generation

The pick labels will include:
- Plant name (ras)
- QR code linking to a detail page
- Batch codes (bollen_code)
- Location (locatie)
- Number of trays (aantal_bakken)

The PDF will be formatted for 6x4" labels to be printed on a Zebra printer.

## Implementation Plan

Following our test-first development approach, we'll implement this feature in small, focused steps:

### 0. Preparation

- [x] Explore the data in Dremio
- [x] Update this document with findings if necessary (esp high level design).

### 1. Model and Repository

- [ ] Create test for `BulbPickList` model existence
- [ ] Implement basic `BulbPickList` model
- [ ] Test model fields and validation
- [ ] Complete model implementation
- [ ] Test repository initialization
- [ ] Implement repository class
- [ ] Test data retrieval with pagination
- [ ] Implement data retrieval methods
- [ ] Test filtering and sorting
- [ ] Implement filtering and sorting

### 2. Web Interface

- [ ] Test bulb picking page rendering
- [ ] Create basic page structure
- [ ] Test table component with selection
- [ ] Implement table with row selection
- [ ] Test "Select All" functionality
- [ ] Implement "Select All" button

### 3. Label Generation

- [ ] Research PDF and QR code generation options
- [ ] Test PDF generation
- [ ] Implement PDF generation for labels
- [ ] Test QR code generation
- [ ] Implement QR code integration
- [ ] Test complete label generation
- [ ] Implement "Print Labels" button

### 4. Integration

- [ ] Test end-to-end workflow
- [ ] Fix any integration issues
- [ ] Update application startup to include new module
- [ ] Update menu to include new page
- [ ] Update CHANGELOG.md

### 5. Quality Assurance

- [ ] Run `make test` to verify all tests pass
- [ ] Run `make format` for code formatting
- [ ] Run `make quality` for linting
- [ ] Verify changes meet project standards
