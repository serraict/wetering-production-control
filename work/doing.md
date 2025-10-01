# Doing

## Goal: Bianca can easily view and edit the inspectie_ronde details

Bianca walks around the greenhouse and inspects the crop.
She does this based on the data in the `inspectie_ronde` view.
For each lot in the view, she inspects the crops and administrates
if the lot will be ready for sales at hte expected date or earlier (+1) or later (-1)

## Current Status

First deploy done, received feedback from Bianca:

> Hoi Marijn,
>
> Ik kan hem niet met mijn mobiel openen.
>
> Wel met de computer.
>
> Als ik op + druk, verandert er alleen niets.
>
> Ook krijg ik de volgorde niet lekker.
>
> Net als vroeger zet hij een partij die in 2 en 7 staan in de volgorde op positie 7 en niet op 2.
>
> En je kan geen selectie maken van de komende 2 weken.
>
> Partijen waarvan een deel al over de baan naar het inpakken gaan en die daardoor ook een baannummer van bijvoorbeeld 812 en 813 hebben en ook nog een laag nummer, die staan helemaal onderaan de lijst denk ik als ik hem uitprint en ik had alleen de eerste 3 pagina’s uitgeprint, dus die miste ik in het rondje lopen.
>
> Met vriendelijke groet,
>
> Bianca van de Wetering

## Acceptance criteria

✅ View data with inline edit controls

- ✅ There is an overview page with all the inspectieronde ("Verkoop.inspectie_ronde") columns (similar to wijderzetten page)
- ✅ We can show all record on this page
- ✅ There is a +1 and -1 button on each row
- ✅ Printing
  - ✅ There is a print button that prints the current page
  - ✅ Printing shows all the columns

✅ Edit data pleasantly

- ✅ The buttons +1 and -1 are implemented and show user feedback
- ✅ Create modification command for each record that was edited (ready for implementation)

🔄 Smart filtering and sorting - NEXT**

- ⏳ Add date range filtering with "next 2 weeks" default and "show all" toggle
- ⏳ Fix sorting order to prioritize min_baan field (addresses position 2 vs 7 issue)
- ⏳ Ensure items with multiple baan numbers appear at correct position based on min_baan

🔄 Persist the data - IN PROGRESS

- ⏳ For each command, update the backing database (note this is not Dremio, but the Olsthoorn Firebird database)

## Design

### Data Model

Based on the `Verkoop.inspectie_ronde` view in Dremio, we need to create:

- `InspectieRonde` model with fields matching the view structure
- Primary key will be a combination of `code` and other identifying fields
- `afwijking_afleveren` field for the +1/-1 adjustments

### Architecture

Following the existing patterns in the codebase:

- Model in `src/production_control/inspectie/models.py`
- Repository in `src/production_control/inspectie/repositories.py`
- Commands in `src/production_control/inspectie/commands.py`
- Web page in `src/production_control/web/pages/inspectie.py`

### UI Components

Reuse existing components:

- `model_list_page` for the overview table
- `data_table` for displaying the data
- Custom row actions for +1/-1 buttons
- Print functionality using browser print

## Implementation plan

### ✅ Phase 1: Model and Repository (Test-Driven) - COMPLETED

### ✅ Phase 2: Basic Web Interface (Test-Driven) - COMPLETED

### 🔄 Phase 3: Commands and Data Persistence (Test-Driven) - NEXT

#### ✅ Step 3.1: Create command for afwijking updates - COMPLETED

#### ✅ Step 3.2: Wire up UI with browser storage tracking - COMPLETED

#### ⏳ Step 3.3: Implement Firebird database updates

- **Test**: Test database connection and update queries (using mocks initially)
- **Code**: Implement command execution with Firebird database updates
- **Test**: Integration test with actual database (if available in test environment)

### 🔄 Phase 4: Smart Filtering and Sorting (Test-Driven) - PLANNED

#### Step 4.1: Enhanced Repository Filtering

- **Test**: Add test for date range filtering in `InspectieRepository`
- **Code**: Extend `get_paginated()` method to accept `date_from` and `date_to` parameters
- **Code**: Implement filtering logic using `datum_afleveren_plan` field
- **Test**: Test default "next 2 weeks" filter behavior

#### Step 4.2: Fix Sorting Order

- **Test**: Add test for proper sorting by `min_baan` first, then `datum_afleveren_plan`
- **Code**: Update `_apply_default_sorting()` method in `InspectieRepository`
- **Code**: Change sort order to: `min_baan ASC, datum_afleveren_plan ASC, product_naam ASC`
- **Test**: Verify items with multiple baan numbers (812, 813) appear at correct position

#### Step 4.3: Enhanced UI Controls

- **Test**: Add test for filter toggle functionality
- **Code**: Add "Next 2 weeks" / "Show all" toggle button to UI
- **Code**: Implement button state management and page refresh on toggle
- **Test**: Test filter state persistence in browser storage

#### ~~Step 4.4: Improved Button Feedback~~

#### Step 4.5: Integration Testing

- **Test**: End-to-end test of filtering + sorting + button actions
- **Test**: Performance test with large datasets (> 1000 records)
- **Code**: Optimize queries if needed based on performance results

### Testing Strategy

- Follow single-test-at-a-time approach from CONTRIBUTING_AI_PROMPT.md
- Start with basic existence tests
- Progress to functionality tests
- End with edge cases and error conditions
- Mock external dependencies (Dremio, Firebird) in unit tests
- Create integration tests for database operations
