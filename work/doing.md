# Doing

In this document we describe what we are working on now.

## Add Warning Message Filter to Spacing Page

Add a filter toggle to display only records with warning messages on the spacing page.

### Context

- The spacing page currently shows all spacing records with pagination and search functionality
- Records can have warning messages in the `wijderzet_registratie_fout` field
- Records with warnings show a ⚠️ emoji via the `warning_emoji` computed field
- This feature will help Paul (lead production operator) quickly identify records that need attention

### Implementation Plan

1. Add Warning Filter UI
   - Add a toggle switch next to the existing search input
   - Label: "Toon alleen waarschuwingen" (following Dutch UI convention)
   - Update table state to track warning filter state

2. Update Backend Filtering
   - Modify SpacingRepository to support filtering by warning presence
   - Add warning filter parameter to get_paginated method
   - Update SQL query to handle warning filtering

3. Connect UI to Backend
   - Update handle_filter to consider both search text and warning filter
   - Ensure proper state management for combined filters
   - Maintain existing date range functionality

4. Test-First Development Steps

   a. First Test: Warning Filter State
   ```python
   def test_warning_filter_state():
       # Verify warning filter can be toggled and affects table state
   ```

   b. Second Test: Repository Warning Filter
   ```python
   def test_repository_warning_filter():
       # Verify repository correctly filters records with warnings
   ```

   c. Third Test: UI Integration
   ```python
   def test_warning_filter_ui():
       # Verify UI updates when warning filter is toggled
   ```

   d. Fourth Test: Combined Filtering
   ```python
   def test_combined_search_and_warning_filter():
       # Verify search and warning filter work together
   ```

5. Documentation Updates
   - Update CHANGELOG.md
   - Add docstrings for new functionality
   - Update any relevant UI documentation

### Files to Modify

1. src/production_control/web/pages/spacing.py
   - Add warning filter UI component
   - Update filter handling logic

2. src/production_control/spacing/repositories.py
   - Enhance filtering capabilities

3. tests/web/test_spacing.py
   - Add new test cases

4. tests/spacing/test_repository.py
   - Add repository filter tests

### Git Commits

Plan to make atomic commits following conventional commits:

1. feat(spacing): add warning filter UI component
2. feat(repo): add warning filter to spacing repository
3. feat(spacing): integrate warning filter with search
4. test(spacing): add warning filter tests
5. docs: update changelog for warning filter feature

### Definition of Done

- Warning filter toggle is visible and functional
- Records are correctly filtered when toggle is active
- Search and date filters work in combination with warning filter
- All tests pass
- Code follows project's Python style
- Documentation is updated
- Changes are committed with clear messages
