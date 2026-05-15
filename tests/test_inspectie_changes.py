"""Tests for the shared inspectie pending-change helpers."""

from datetime import date

from production_control.inspectie.changes import (
    STORAGE_KEY,
    apply_delta,
    get_pending_change,
    parse_date,
)


def test_apply_delta_creates_entry_on_first_call():
    storage: dict = {}
    new_afw, new_datum = apply_delta(
        storage, "27014", current_afwijking=0, current_datum=date(2025, 10, 10), delta=1
    )

    assert new_afw == 1
    assert new_datum == date(2025, 10, 11)

    entry = storage[STORAGE_KEY]["27014"]
    assert entry == {
        "original_afwijking": 0,
        "new_afwijking": 1,
        "original_datum": "2025-10-10",
        "new_datum": "2025-10-11",
    }


def test_apply_delta_accumulates_on_subsequent_calls():
    storage: dict = {}
    apply_delta(storage, "27014", 0, date(2025, 10, 10), 1)
    new_afw, new_datum = apply_delta(storage, "27014", 0, date(2025, 10, 10), 1)

    assert new_afw == 2
    assert new_datum == date(2025, 10, 12)

    entry = storage[STORAGE_KEY]["27014"]
    assert entry["original_afwijking"] == 0
    assert entry["original_datum"] == "2025-10-10"
    assert entry["new_afwijking"] == 2
    assert entry["new_datum"] == "2025-10-12"


def test_apply_delta_handles_negative_delta():
    storage: dict = {}
    new_afw, new_datum = apply_delta(storage, "27014", 0, date(2025, 10, 10), -1)

    assert new_afw == -1
    assert new_datum == date(2025, 10, 9)


def test_apply_delta_uses_current_datum_when_stored_datum_missing():
    storage: dict = {
        STORAGE_KEY: {
            "27014": {
                "original_afwijking": 0,
                "new_afwijking": 0,
            }
        }
    }
    new_afw, new_datum = apply_delta(storage, "27014", 0, date(2025, 10, 10), 1)
    assert new_afw == 1
    assert new_datum == date(2025, 10, 11)


def test_apply_delta_uses_original_datum_when_new_datum_missing():
    storage: dict = {
        STORAGE_KEY: {
            "27014": {
                "original_afwijking": 0,
                "new_afwijking": 0,
                "original_datum": "2025-10-10",
            }
        }
    }
    new_afw, new_datum = apply_delta(storage, "27014", 0, date(2025, 10, 11), 1)
    assert new_afw == 1
    assert new_datum == date(2025, 10, 11)


def test_get_pending_change_returns_entry_when_present():
    storage: dict = {}
    apply_delta(storage, "27014", 0, date(2025, 10, 10), 1)
    change = get_pending_change(storage, "27014")
    assert change is not None
    assert change["new_afwijking"] == 1


def test_get_pending_change_returns_none_when_absent():
    assert get_pending_change({}, "27014") is None
    assert get_pending_change({STORAGE_KEY: {}}, "27014") is None


def test_get_pending_change_ignores_malformed_entry():
    storage = {STORAGE_KEY: {"27014": "not-a-dict"}}
    assert get_pending_change(storage, "27014") is None

    storage = {STORAGE_KEY: {"27014": {"original_afwijking": 0}}}
    assert get_pending_change(storage, "27014") is None


def test_parse_date_accepts_date_string_and_invalid():
    assert parse_date(date(2025, 10, 10)) == date(2025, 10, 10)
    assert parse_date("2025-10-10") == date(2025, 10, 10)
    assert parse_date("not-a-date") is None
    assert parse_date(None) is None
    assert parse_date(123) is None
