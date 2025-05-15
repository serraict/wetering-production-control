# Doing

## Print as many labels as required

Print the appropriate number of pallet labels based on the number of boxes:

- Each pallet can hold a maximum of 25 boxes
- Number of pallets needed = ceiling(total_boxes / 25)

Example test cases:
1. Basic cases:
   - 25 boxes -> 1 pallet (exactly one full pallet)
   - 26 boxes -> 2 pallets (one full + one partial)
   - 50 boxes -> 2 pallets (two full pallets)
   - 51 boxes -> 3 pallets (two full + one partial)
   - 68 boxes -> 3 pallets (two full + one partial)

2. Edge cases:
   - 0 boxes -> 0 pallets (invalid input)
   - 1 box -> 1 pallet (minimum case)
   - 24 boxes -> 1 pallet (partial pallet)
   - 999 boxes -> 40 pallets (large number)

3. Special considerations:
   - Each pallet label should indicate:
     - Total number of boxes
     - Which pallet number this is (e.g. "Pallet 1 of 3")

## Implementation Plan

1. Calculate Number of Pallets
   - Add test_calculate_pallets() for basic pallet calculation
   - Implement calculate_pallets() function (box count -> pallet count)
   - Test basic case (26 boxes -> 2 pallets)

2. Handle Edge Cases
   - Add test_calculate_pallets_edge_cases()
   - Test 0 boxes, 1 box, large numbers
   - Update calculate_pallets() to handle these cases

3. Generate Multiple Labels
   - Add test_generate_multiple_labels()
   - Extend BulbPickList model for pallet numbering
   - Test generating labels for multiple pallets

4. Implementation Structure:
   ```python
   def calculate_pallets(box_count: int) -> int:
       """Calculate number of pallets needed for given box count."""
       if box_count <= 0:
           return 0
       return (box_count + 24) // 25  # ceiling division by 25

   def generate_pallet_labels(record: BulbPickList) -> List[str]:
       """Generate labels for all pallets needed."""
       pallet_count = calculate_pallets(record.box_count)
       labels = []
       for pallet_num in range(1, pallet_count + 1):
           label_data = {
               **record.dict(),
               "pallet_number": pallet_num,
               "total_pallets": pallet_count
           }
           labels.append(generate_label(label_data))
       return labels
   ```

5. Template Updates:
   - Update Jinja2 template with pallet information
   - Add "Pallet X of Y" to label layout
   - Show total box count on each label

6. Integration:
   - Update web interface for multiple label generation
   - Ensure PDF generation works with multiple labels
   - Add validation for box count input

7. Testing Strategy:
   - Unit tests for pallet calculation
   - Integration tests for label generation
   - UI tests for web interface updates
