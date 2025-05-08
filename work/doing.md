# Doing

Add potted week field to bulb picking. name is oppot_week in database.

## Implementation Plan

1. **Update the BulbPickList model**

   - Add the `oppot_week` field to the `BulbPickList` model in `src/production_control/bulb_picklist/models.py`
   - The field should be an string representing the iso week (e.g. 22w07)
   - Add appropriate field metadata (title, description, UI sortable)

1. **Update the repository for search functionality**

   - Add `oppot_week` to the `search_fields` list in `BulbPickListRepository` in `src/production_control/bulb_picklist/repositories.py`

1. **Update the label generation**

   - Modify the `_prepare_record_data` method in `LabelGenerator` to include the `oppot_week` field
   - Update the label template to display the week number next to the potting ID

1. **Write tests**

   - Update `test_bulb_picklist_model_attributes` in `tests/test_bulb_picklist_models.py` to include the new field
   - Update label generation tests to verify the week number appears on the label

1. **Verify changes**

   - Run tests to ensure all functionality works correctly
   - Manually verify the field appears in the UI and on generated labels

## Progress

- [x] Update BulbPickList model
- [x] Update BulbPickListRepository search fields
- [x] Update label generation
- [x] Update tests
- [x] Verify changes
