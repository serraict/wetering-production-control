# Doing

## Update label layouts

All labels:

- 2mm padding around label
- top row: 50%, middle row: 30%, bottom row: 20%
- default size: 104x77 mm
- remove the url
- add 2px solid black border around label
- add 1px border around cells

Bulb picking:

- add article group next to bulb number
- add locatie2 and locatie3 (update in view)
- QR code 30x30mm

Potting lot:

- add certification nr to bottom ro
- add bolmaat to bottom row

## Implementation Plan

Implementation order:

1. General Label Changes: ✅

   - Update label_styles.html.jinja2:
     - Add 2mm padding around label ✅
     - Set grid rows to 50/30/20 ✅
     - Set label size to 104x77mm (this is already configurable, but change the default label size) ✅
     - Set QR code to 30x30mm ✅
     - Scale bottom row font to 80% ✅
     - Add 2px solid black border around label ✅
     - Add 1px border around cells ✅
   - The url-text class is kept for backward compatibility but will be removed from templates

1. Bulb Picking Label: ✅

   - Update labels.html.jinja2:
     - Add artikel to middle-left section ✅
     - Remove url-text from header ✅
   - Update bottom-left with locatie2 and locatie3 -> handled by backend

1. Potting Lot Label: ✅

   - Update labels.html.jinja2:
     - Split bottom-full into bottom-left and bottom-right ✅
     - Add cert_nr and bolmaat to bottom-right ✅
     - Remove url-text from header ✅

## Progress

- ✅ Updated label_styles.html.jinja2 with new grid layout, padding, QR code size, borders around label and cells
- ✅ Updated default label dimensions in LabelConfig class to 104x77mm
- ✅ Fixed page break issues in labels_base.html.jinja2
- ✅ Made middle row font size match header (120%, bold)
- ✅ Added artikel field to BulbPickList model
- ✅ Updated bulb picking label template to show artikel and remove URL text
- ✅ Added cert_nr field to PottingLot model
- ✅ Updated potting lot label template to show bolmaat and cert_nr, and remove URL text
