"""URL parsing utilities for potting lot activation."""

import re
from typing import Optional


def extract_lot_id_from_barcode(barcode_text: str) -> Optional[int]:
    """
    Extract potting lot ID from scanned barcode text.

    This function handles various formats:
    1. Full URLs: https://example.com/potting-lots/scan/12345 → 12345
    2. Relative paths: /potting-lots/scan/12345 → 12345
    3. Direct IDs: 12345 → 12345

    Args:
        barcode_text: The scanned barcode content

    Returns:
        The extracted lot ID as integer, or None if not found/invalid
    """
    if not barcode_text or not isinstance(barcode_text, str):
        return None

    barcode_text = barcode_text.strip()
    if not barcode_text:
        return None

    # Try to extract from URL pattern: /potting-lots/scan/{id}
    # Handle query params, fragments, and additional path segments
    url_match = re.search(r"/potting-lots/scan/(\d+)(?:[/?#].*)?$", barcode_text)
    if url_match:
        try:
            lot_id = int(url_match.group(1))
            return lot_id if lot_id >= 0 else None  # Reject negative IDs
        except ValueError:
            return None

    # Fallback: try to parse as direct numeric ID
    try:
        lot_id = int(barcode_text)
        return lot_id if lot_id >= 0 else None  # Reject negative IDs
    except ValueError:
        return None


def is_potting_lot_url(url: str) -> bool:
    """
    Check if a URL is a potting lot scan URL.

    Args:
        url: URL to check

    Returns:
        True if the URL matches the potting lot scan pattern
    """
    if not url or not isinstance(url, str):
        return False

    return bool(re.search(r"/potting-lots/scan/\d+(?:[/?#].*)?$", url.strip()))
