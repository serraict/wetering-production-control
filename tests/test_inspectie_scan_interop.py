"""Verify scan-view changes and inspectie page share the same storage."""

from datetime import date
from unittest.mock import patch

from production_control.inspectie.changes import STORAGE_KEY, apply_delta
from production_control.web.pages.inspectie import get_pending_commands


def test_apply_delta_entries_are_visible_to_inspectie_page():
    """A change written via apply_delta surfaces in get_pending_commands.

    Ensures the scan view (which calls apply_delta directly) and the
    inspectie page see the same pending changes.
    """
    storage: dict = {}
    apply_delta(storage, "27014", current_afwijking=0, current_datum=date(2025, 10, 10), delta=1)
    apply_delta(storage, "27014", current_afwijking=0, current_datum=date(2025, 10, 10), delta=1)

    assert STORAGE_KEY in storage
    assert storage[STORAGE_KEY]["27014"]["new_afwijking"] == 2
    assert storage[STORAGE_KEY]["27014"]["new_datum"] == "2025-10-12"

    with patch("production_control.web.pages.inspectie.get_storage", return_value=storage):
        commands = get_pending_commands()

    assert len(commands) == 1
    cmd = commands[0]
    assert cmd.code == "27014"
    assert cmd.new_afwijking == 2
    assert cmd.new_datum_afleveren == date(2025, 10, 12)
