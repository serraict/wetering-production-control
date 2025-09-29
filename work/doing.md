# Doing

## Goal: Bianca can easily view and edit the inspectie_ronde details

Bianca walks around the greenhouse and inspects the crop.
She does this based on the data in the `inspectie_ronde` view.
For each lot in the view, she inspects the crops and administrates
if the lot will be ready for sales at hte expected date or earlier (+1) or later (-1)

## Acceptance criteria

Phase 1: view data with inline edit controls

- There is an overview page with all the inspectieronde ("Verkoop.inspectie_ronde") columns (similar to wijderzetten page)
- We can show all record on this page
- There is a +1 and -1 button on each row
- There is a print button tah prints the current page

Phase 2: edit data pleasantly

- The buttons +1 and -1 create a command to change `afwijking_afleveren` field
- create a modifciation command for each record that was edited

Phase 3: persist the data

- For each command, update the backing database (note this is not Dremio, but the Olsthoorn Firebird database)

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

### Phase 1: Model and Repository (Test-Driven)

#### Step 1.1: Create InspectieRonde model

- **Test**: `tests/test_inspectie_models.py` - test model creation with sample data
- **Code**: `src/production_control/inspectie/models.py` - create SQLModel for inspectie_ronde view
- **Test**: Verify all fields from Dremio view are mapped correctly
- **Test**: Test computed fields if needed

#### Step 1.2: Create repository for data access

- **Test**: `tests/test_inspectie_repository.py` - test paginated data retrieval
- **Code**: `src/production_control/inspectie/repositories.py` - extend DremioRepository
- **Test**: Test filtering and sorting functionality
- **Test**: Test get_by_id functionality

### Phase 2: Basic Web Interface (Test-Driven)

#### Step 2.1: Create overview page

- **Test**: `tests/web/test_inspectie.py` - test page renders without errors
- **Code**: `src/production_control/web/pages/inspectie.py` - create basic list page
- **Test**: Test table displays data correctly
- **Test**: Test pagination works

#### Step 2.2: Add inline edit controls (+1/-1 buttons)

- **Test**: Test buttons are rendered for each row
- **Code**: Create custom row actions for +1/-1 buttons
- **Test**: Test button click handlers (mock the actual updates)

#### Step 2.3: Add print functionality

- **Test**: Test print button exists and triggers browser print
- **Code**: Add print button using JavaScript window.print()

### Phase 3: Commands and Data Persistence (Test-Driven)

#### Step 3.1: Create command for afwijking updates

- **Test**: `tests/test_inspectie_commands.py` - test command creation and validation
- **Code**: `src/production_control/inspectie/commands.py` - create UpdateAfwijkingCommand
- **Test**: Test command with +1 and -1 values
- **Test**: Test command validation

#### Step 3.2: Implement Firebird database updates

- **Test**: Test database connection and update queries (using mocks initially)
- **Code**: Implement command execution with Firebird database updates
- **Test**: Integration test with actual database (if available in test environment)

#### Step 3.3: Wire up UI to commands

- **Test**: Test end-to-end flow from button click to database update
- **Code**: Connect +1/-1 buttons to command execution
- **Test**: Test error handling and user feedback

### Testing Strategy

- Follow single-test-at-a-time approach from CONTRIBUTING_AI_PROMPT.md
- Start with basic existence tests
- Progress to functionality tests
- End with edge cases and error conditions
- Mock external dependencies (Dremio, Firebird) in unit tests
- Create integration tests for database operations
