# Doing

## Context

Crop in the greenhouse is placed on rolling benches.
The Potlilium batches span multiple benches and are marked with labels with a QR code.
The QR code is a URL that ends with the identifier of the batch (e.g., `/potting-lots/scan/12345`).
The codes are generated on the potting list page.

**Current implementation:**

- Scan route already exists: `/potting-lots/scan/{id}` → redirects to detail page
- Barcode scanner component exists using `nicegui-scanner`
- Detail page shows lot information but is optimized for desktop, not mobile

## Goal

Paul can scan batch labels from his smartphone and quickly view batch information while working in the greenhouse.

## Acceptance criteria

- [ ] Paul can access a dedicated scanning page from his smartphone browser
- [ ] Paul can scan the QR code label using his phone's camera
- [ ] After scanning, the system displays:
  - Lot code (bollen_code)
  - Article name (naam)
  - Other relevant batch details
- [ ] The display is mobile-optimized and easy to read on a smartphone
- [ ] The scanner works reliably on mobile browsers (iOS Safari, Android Chrome)
- [ ] Paul can scan multiple batches in sequence without navigation issues

## Technical requirements

- Mobile-responsive UI optimized for smartphone screens
- Camera access permission handling
- Fast scan-to-display performance (< 2 seconds)
- Clear error messages if QR code is invalid or batch not found

## Implementation steps

- [x] Create new dedicated scanning page route: `/scan` (separate from existing `/potting-lots/scan/{id}`)
  - [x] should be a new page in web/pages
- [x] Implement camera scanner UI on the page using existing `barcode_scanner` component
- [x] Configure scanner to handle scanned URLs and extract lot ID using existing `url_parser`
- [x] On successful scan, redirect to mobile-optimized view of batch info
- [x] Create mobile-optimized batch info display (or enhance existing detail page for mobile)
  - [x] Show lot code (bollen_code)
  - [x] Show article name (naam)
  - [ ] Show other key fields (oppot_datum, bolmaat, klant_code, etc.)
- [x] Add error handling for:
  - [x] Invalid QR codes
  - [x] Batch not found
  - [x] Camera access denied
- [ ] Add "Scan another" button for sequential scanning
- [ ] Test on mobile devices (iOS Safari and Android Chrome)
- [ ] Add navigation link to scanning page from main menu

## Notes

- For now, assume Paul is the only person using the scanner (no multi-user considerations needed)
- Location tracking is not available in the current data model - deferred to future enhancement
- Existing scan route `/potting-lots/scan/{id}` can remain as-is for QR code link compatibility
- New `/scan` route will provide the camera scanning interface
- Future enhancement: Consider adding batch action capabilities after viewing
