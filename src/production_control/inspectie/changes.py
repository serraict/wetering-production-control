"""Pending afwijking/afleverdatum changes stored in browser session.

Shared between the inspectieronde page and the scan view so both screens
see the same pending state and commit through the same endpoint.
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional, Tuple


STORAGE_KEY = "inspectie_changes"


def parse_date(value: Any) -> Optional[date]:
    """Parse a stored value into a date, returning None if unparseable."""
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def apply_delta(
    storage: Dict[str, Any],
    code: str,
    current_afwijking: int,
    current_datum: date,
    delta: int,
) -> Tuple[int, date]:
    """Apply +/- delta to the pending afwijking and afleverdatum for code.

    Writes into storage[STORAGE_KEY][code], creating the entry on first use
    and updating new_afwijking/new_datum on subsequent calls. Returns the
    new (afwijking, datum) after applying the delta.
    """
    storage.setdefault(STORAGE_KEY, {})
    change = storage[STORAGE_KEY].get(code)

    if change is None:
        new_afwijking = current_afwijking + delta
        new_datum = current_datum + timedelta(days=delta)
        storage[STORAGE_KEY][code] = {
            "original_afwijking": current_afwijking,
            "new_afwijking": new_afwijking,
            "original_datum": current_datum.isoformat(),
            "new_datum": new_datum.isoformat(),
        }
        return new_afwijking, new_datum

    new_afwijking = change["new_afwijking"] + delta
    base_datum = (
        parse_date(change.get("new_datum"))
        or parse_date(change.get("original_datum"))
        or current_datum
    )
    new_datum = base_datum + timedelta(days=delta)
    change["new_afwijking"] = new_afwijking
    change["new_datum"] = new_datum.isoformat()
    return new_afwijking, new_datum


def get_pending_change(storage: Dict[str, Any], code: str) -> Optional[Dict[str, Any]]:
    """Return the pending change dict for code, or None when absent/invalid."""
    change = storage.get(STORAGE_KEY, {}).get(code)
    if isinstance(change, dict) and "new_afwijking" in change:
        return change
    return None
