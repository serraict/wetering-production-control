# Doing

In this document we describe what we are working on now.

## Goal: User can track spacing process segment

- Create functionality to record spacing operations (new and historical)
- Enable correction of ~200 lots with incorrect spacing data from January 2023
- Must be completed this week
- Critical for accurate cost determination per lot
- Impacts greenhouse space utilization tracking

Completed work:

- Created data model and repository for spacing records with SQLModel
- Built web interface for viewing and correcting spacing records
- Implemented OpTech API integration for applying corrections
- Added CLI functionality:
  - List and filter spacing errors
  - Preview corrections with dry-run support
  - Apply corrections with validation
  - Proper logging and error handling
  - Comprehensive test coverage

Remaining Work:

- Create batch-fix for common errors:
  `production_control correct-spacing --error "Geen wdz2 datum"  ` # issue a correction for each record with an error. 

### Error Analysis and Fix Strategy

We have identified three types of errors in the spacing records:

1. Missing WDZ2 Date (180 records)
   ```
   Error: "Geen wdz2 datum maar wel tafel aantal na wdz 2"
   Fix Strategy:
   - Check if WDZ1 count equals rounded aantal_tafels_oppotten_plan
   - If true:
     * Set WDZ1 count to current WDZ2 count
     * Clear WDZ2 count (set to null)
   - If false:
     * Log for manual review
   ```

2. Greenhouse Count Mismatch (4 records)
   ```
   Error: "Meer tafels in de kas dan geregistreerd bij wijderzetten"
   Fix Strategy:
   - Log records for manual follow-up
   - Requires physical verification of actual table count
   ```

3. Invalid Double Spacing (32 records)
   ```
   Error: "Partij is 2x wdz maar het tafelaantal is niet juis geregistreerd"
   Fix Strategy:
   - Log records for manual review
   - Requires user verification of correct counts
   ```

### Implementation Plan

1. Enhance SpacingRepository:
   - Add method to get records by error type (we already have this, because we can display err by name, right?)
   - Add method to get rounded aantal_tafels_oppotten_plan

2. Create error-specific correction commands:
   - AutomaticSpacingCorrection for type 1 errors
   - LoggedSpacingError for types 2 and 3

3. Update CLI:
   - Add --fix flag to correct-spacing command
   - Add --log-only flag for manual review cases
   - Add error type specific handling

4. Add logging:
   - Create log file for manual review cases
   - Include all relevant record details
   - Add timestamp and correction attempts

## Design

### System Architecture

```mermaid
graph TD
    subgraph Production Control App
        WebApp[Web Application]
        SQLModel[SQLModel Layer]
        SpacingPages[Spacing Pages]
        SpacingModel[Spacing Model]
        OpTechClient[OpTech Client]
    end
    
    subgraph Data Sources
        Dremio[Dremio Instance]
        DremioView[registratie_controle view]
    end
    
    subgraph Spacing Control
        Technison[Technison Application]
        OpTech[OpTech API]
    end

    WebApp --> SpacingPages
    SpacingPages --> SpacingModel
    SpacingPages --> OpTechClient
    SpacingModel --> SQLModel
    OpTechClient --> OpTech
    SQLModel --> DremioView
    DremioView --> Dremio
    OpTech --> Technison

    style WebApp fill:#f9f,stroke:#333
    style SQLModel fill:#bbf,stroke:#333
    style SpacingPages fill:#f9f,stroke:#333
    style SpacingModel fill:#bbf,stroke:#333
    style OpTechClient fill:#fbf,stroke:#333
    style Dremio fill:#bfb,stroke:#333
    style Technison fill:#fbb,stroke:#333
    style OpTech fill:#fbf,stroke:#333
