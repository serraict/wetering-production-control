# Doing

## Print duplicate labels for potting lots

For each potting lot, we need to print two identical labels:
- One label to attach to the first pot of the lot
- One label to attach to the last pot of the lot

This helps operators quickly identify where each lot begins and ends in the greenhouse.

### Files to Modify

1. src/production_control/potting_lots/label_generation.py
   ```python
   class LabelGenerator(BaseLabelGenerator[PottingLot]):
       def generate_labels_html(self, records: Union[PottingLot, List[PottingLot]], ...) -> str:
           # Duplicate each record to generate two identical labels
           duplicated_records = [r for r in records for _ in range(2)]
           return super().generate_labels_html(duplicated_records, ...)
   ```

2. tests/potting_lots/test_label_generation.py
   ```python
   def test_generate_duplicate_labels():
       # Test that each potting lot gets two identical labels
       ...

   def test_generate_multiple_duplicate_labels():
       # Test with multiple records
       ...
   ```

3. src/production_control/web/pages/potting_lots.py
   ```python
   def generate_and_download_pdf(...):
       # Update tooltip to indicate duplicate labels
       ...
   ```

### Implementation Steps

1. Test-First Development:
   - Create tests in test_label_generation.py
   - Verify tests fail appropriately

2. Implementation:
   - Modify LabelGenerator to duplicate records
   - Update UI tooltip text

3. Quality Checks:
   - Run tests
   - Check code formatting
   - Verify changes

### Definition of Done

- [x] Tests written in test_label_generation.py
- [x] Implementation in potting_lots/label_generation.py
- [x] UI updates in pages/potting_lots.py
- [x] Fixed display of None values for klant_code in template
- [x] All tests passing
- [x] Code formatted
- [x] Changes reviewed
- [x] CHANGELOG.md updated

### Commit Plan

1. test: Add tests for duplicate potting lot labels
2. feat: Implement duplicate label generation
3. docs: Update documentation and changelog
