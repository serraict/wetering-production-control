"""Topic-name derivation for lot conversations."""

from typing import Any


def topic_name_for(lot: Any) -> str:
    """Return the Zulip topic name for a potting lot.

    The topic name is the lot id rendered as a string — deterministic, never
    changes, no mapping table.
    """
    return str(lot.id)
