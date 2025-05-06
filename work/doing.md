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
- [x] Research PDF generation
- [x] Implement PDF generation for a single label
- [x] Test PDF generation
- [x] Implement "Print Label" button

### 3a. Add QR Code to label

- [x] Add qrcode\[pil\] dependency to pyproject.toml
- [x] Test QR code generation:
  - Add test for QR code generation method in test_pdf_label_generation.py
  - Test QR code content (should encode `/bulb-picking/{record.id}`)
  - Test QR code image generation (base64 format for HTML embedding)
  - Test QR code integration with label HTML
- [x] Implement QR code generation:
  - Add generate_qr_code method to LabelGenerator class
  - Generate QR code as base64 image (~25mm square size)
  - Position QR code in bottom right of label template
  - Update generate_label_html to include QR code
  - Ensure proper sizing and contrast (black on white)
- [x] base url should be configurable and/or retrieved from nicegui context
  - verify that the app works

### 3b Pretty and smooth qr code usage experience

- [x] Create a landing page for pick label scans
  - scanning the qr code should bring us to this page
  - base url should be configurable
- [x] Add logo to center of qr code so people know it is a serra link
  - move the qr code to the top-right of the label
  - add a small, gray, readable url below the label title
  - there should be a serra icon in the center of the qr code
- [x] The print button in the list should not opene a popup but instead print the label to pdf immediately

### 4. Integration

- [x] Test end-to-end workflow
- [x] Fix any integration issues
- [x] Update application startup to include new module
- [x] Update menu to include new page
- [x] Update CHANGELOG.md

### 5. Quality Assurance

Run these everytime we check a box in this document, and one final time before the complete task as done:

- [x] Run `make test` to verify all tests pass
- [x] Run `make format` for code formatting
- [x] Run `make quality` for linting
- [x] Verify changes meet project standards
- [x] Remove ORM mapping tests from other models (focus on behavior, not implementation details)

### 6. Refactoring

- [x] Create generic components for model detail pages and view actions
  - [x] Create model_detail_page.py component
  - [x] Create model_list_page.py component
- [x] Refactor products.py to use these components
  - [x] Update products list page to use model_list_page.py
  - [x] Update product detail page to use model_detail_page.py
  - [x] Update tests to reflect the new structure
- [ ] Refactor bulb_picklist.py to use these components
  - [ ] Refactor to use model_detail_page.py for the detail pages
  - [ ] Refactor to use model_list_page.py for the list page
  - [ ] Update the view and label actions to use the generic components
- [ ] Refactor spacing.py to use these components
  - [ ] Refactor to use model_detail_page.py for the detail pages
  - [ ] Refactor to use model_list_page.py for the list page
  - [ ] Update the view and edit actions to use the generic components
