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

Second deploy done, feedback:

> Het is fijn dat de afwijkingen er meteen bij staan.
> Alleen door je selectie van 2 weken pakt hij niet meer de partijen met een ideale rijpdatum voor vandaag, maar die er nog wel staan.
> Die wil ik ook nog graag kunnen zien. Vandaag is het 40-4, maar een partij die op 40-3 stond, kan ik best verkeerd ingeschat hebben en alsnog naar 40-5 moeten.
> Kun je dan ook een week ervoor tot 2 weken erna als selectieperiode zetten?

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

✅ Smart filtering and sorting

🔄 Persist the data - moved to the backlog

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

### ✅ Phase 4: Smart Filtering and Sorting - COMPLETED

### ✅ Phase 5: Mobile-Friendly Improvements - COMPLETED

- ✅ Refactored mobile view implementation:
  - Replaced `mobile_view` and `mobile_fields` parameters with single optional `columns` parameter
  - Simplified API across all table components (table_utils, data_table, model_list_page)
  - Renamed "Mobile/Desktop" toggle to "Compact/Volledig" view
  - Compact view shows: product_naam, datum_afleveren_plan, afwijking_afleveren, baan_samenvatting
- ✅ Added view details button to inspection page row actions
- ✅ TODO: Collapse top bar menu into burger menu on small screens

### Testing Strategy

- Follow single-test-at-a-time approach from CONTRIBUTING_AI_PROMPT.md
- Start with basic existence tests
- Progress to functionality tests
- End with edge cases and error conditions
- Mock external dependencies (Dremio, Firebird) in unit tests
- Create integration tests for database operations
