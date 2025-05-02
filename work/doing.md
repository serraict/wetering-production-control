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

- [x] Create test for `BulbPickList` model existence
- [x] Implement basic `BulbPickList` model
- [x] Test model fields and validation
- [x] Complete model implementation
- [x] Test repository initialization
- [x] Implement repository class
- [x] Test data retrieval with pagination
- [x] Implement data retrieval methods
- [x] Test filtering and sorting
- [x] Implement filtering and sorting

### 2. Web Interface

- [x] Test bulb picking page rendering
- [x] Create basic page structure
- [x] Update BulbPickList model to use potting lot code (id) as primary key
  - [x] Identify the potting lot code field in the database (found 'id' field is most suitable)
  - [x] Update model changes:
  - Add 'id' field as primary key
  - Remove primary key from bollen_code but keep as regular field
  - Keep all other fields unchanged
  - [x] Update repository changes:
  - Update get_by_id method to use 'id' instead of bollen_code
  - Update \_apply_default_sorting to keep same sorting logic
  - Update get_paginated to use 'id' in count query
  - [x] Update UI changes:
  - Update view handler to use 'id' instead of bollen_code
  - Update detail page route to use 'id'
  - [x] Update tests:
  - Update test_bulb_picklist_models.py for new primary key
  - Update test_bulb_picklist_repository.py to use 'id'
  - Update test_web_bulb_picklist.py to use 'id' in test data

### 3. Label Generation

Add a button each row to generate a label for that row.

- [x] add button
- [x] add popup dialog that show the label
- [x] add print button to the popup
- [ ] Research PDF generation
- [ ] Implement PDF generation for a single label
- [ ] Test PDF generation
- [ ] Implement "Print Label" button

### 3a. Add QR Code to label

- [ ] Research QR code generation options
- [ ] Test QR code generation
- [ ] Implement QR code integration

### 3b. Generate labels for selected records

- [ ] Test table component with selection. We ran into problem with this earlier.
  Before starting, we have to analyze hove server side paging works, and document it.
  Then we have to find out how to include selection, leveraging nicegui as good as possible.
  We have to be careful when storing selection state.
- [ ] Implement table with row selection
- [ ] Test "Select All" functionality
- [ ] Implement "Select All" button
- [ ] Exploratory tests by user.
  - collect results and determine actions
  - ask questions based on usage

### 4. Integration

- [ ] Test end-to-end workflow
- [ ] Fix any integration issues
- [x] Update application startup to include new module
- [x] Update menu to include new page
- [x] Update CHANGELOG.md

### 5. Quality Assurance

Run these everytime we check a box in this document, and one final time before the complete task as done:

- [ ] Run `make test` to verify all tests pass
- [ ] Run `make format` for code formatting
- [ ] Run `make quality` for linting
- [ ] Verify changes meet project standards
- [ ] Remove ORM mapping tests from other models (focus on behavior, not implementation details)

### 6. Refactoring

- [ ] Create generic components for model detail pages and view actions
- [ ] Refactor bulb_picklist.py to use these components
- [ ] Refactor other pages (products.py, spacing.py) to use the same components
- [ ] Update tests to reflect the new structure
