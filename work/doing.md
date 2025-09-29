# Doing

## Goal: Bianca can easily view and edit the inspectie_ronde details

Bianca walks around the greenhouse and inspects the crop.
She does this based on the data in the `inspectie_ronde` view.
For each lot in the view, she inspects the crops and administrates
if the lot will be ready for sales at hte expected date or earlier (+1) or later (-1)

## Current Status

**✅ PHASES 1 & 2 COMPLETED** - Basic functionality is working!

- **Model & Repository**: Full `InspectieRonde` model with all 13 fields from Dremio view
- **Web Interface**: Complete page at `/inspectie` with table showing correct columns:
  - `Code`, `banen`, `klant_code`, `product`, `product_groep_naam`, `datum`, `aantal_in_kas`, `aantal_tafels`, `1e baan`, `teeltafwijking`, Actions
- **UI Controls**: +1/-1 buttons on each row (currently show notifications)
- **Navigation**: "Inspectie Ronde" menu item added
- **Print**: Print button using browser's native print
- **Tests**: Comprehensive test coverage (87% models, 90% repository)
- **Quality**: All quality checks passing, follows project conventions

**🔄 NEXT: Phase 3** - Implement actual database persistence for +1/-1 commands

## Acceptance criteria

✅ **Phase 1: view data with inline edit controls - COMPLETED**

- ✅ There is an overview page with all the inspectieronde ("Verkoop.inspectie_ronde") columns (similar to wijderzetten page)
- ✅ We can show all record on this page
- ✅ There is a +1 and -1 button on each row
- ⏳ Printing
  - ✅ There is a print button that prints the current page
  - ⏳ Printing shows all the columns

✅ **Phase 2: edit data pleasantly - COMPLETED**

- ✅ The buttons +1 and -1 are implemented and show user feedback
- ⏳ Create modification command for each record that was edited (ready for implementation)

🔄 **Phase 3: persist the data - NOT STARTED**

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

#### ✅ Step 2.1: Create overview page

#### ✅ Step 2.2: Add inline edit controls (+1/-1 buttons)

#### ⏳ Step 2.3: Add print functionality

- ✅ **Test**: Test print button exists and triggers browser print
- ✅ **Code**: Add print button using JavaScript window.print()
- ⏳ Print all the columns

### 🔄 Phase 3: Commands and Data Persistence (Test-Driven) - NEXT

#### ⏳ Step 3.1: Create command for afwijking updates

- **Test**: `tests/test_inspectie_commands.py` - test command creation and validation
- **Code**: `src/production_control/inspectie/commands.py` - create UpdateAfwijkingCommand
- **Test**: Test command with +1 and -1 values
- **Test**: Test command validation

#### ⏳ Step 3.2: Implement Firebird database updates

- **Test**: Test database connection and update queries (using mocks initially)
- **Code**: Implement command execution with Firebird database updates
- **Test**: Integration test with actual database (if available in test environment)

#### ⏳ Step 3.3: Wire up UI to commands

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
