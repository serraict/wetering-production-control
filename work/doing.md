# Doing

## Print labels for visible bulb lots

User Story:
As a grower
I want to print labels for all currently visible bulb lots in one go
So that I can efficiently prepare labels for upcoming production

Implementation Plan:

1. Setup & Dependencies:

   - Add Jinja2 to project dependencies
   - Update requirements and pyproject.toml

1. Template Implementation:

   - Create base.html.jinja2 with common layout and styles
   - Create labels.html.jinja2 for unified label rendering
   - Convert existing styles to Jinja2 format
   - Ensure proper page breaks and layout
   - At this stage, the single label functionality should work with the new template.

1. Label Generator Updates:

   - Refactor LabelGenerator to use Jinja2
   - Implement unified generate_pdf method for any number of records
   - Maintain QR code generation functionality
   - Add PDF file cleanup

1. Web Interface:

   - Add "Print Labels" button (Dutch: "Labels Afdrukken")
   - Use table state to get currently visible records
   - Implement direct PDF download in browser

Test Strategy:

1. Unit Tests:

   - Test generate_pdf with single record (existing behavior)
   - Test generate_pdf with multiple records
   - Test multiple record selection
   - Test template rendering
   - Test QR code generation

1. Integration Tests:

   - Test PDF generation end-to-end
   - Verify PDF structure and content
   - Test download functionality
   - Verify browser behavior

1. Edge Cases:

   - Test empty record list
   - Test very long text fields
   - Test special characters in data

Definition of Done:

- All tests pass
- Code follows project style (black, flake8)
- Dutch used in UI, English in code/comments
- Changes documented in CHANGELOG.md
- `make quality` passes
- `make releasable` passes
