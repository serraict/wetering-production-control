"""Parse a Leuze scan payload into a partij ID.

The scanner publishes a string like:
    https://pc.potlilium.serraict.me/potting-lots/scan/27246

We accept any URL (or path) whose path component matches
`.../potting-lots/scan/<int>` and return the trailing integer. Anything
else returns None — the caller logs and drops.
"""

from __future__ import annotations

from urllib.parse import urlparse

_PATH_MARKER = "/potting-lots/scan/"


def parse_scan(payload: str | None) -> int | None:
    if not payload:
        return None
    try:
        path = urlparse(payload).path or payload
    except ValueError:
        return None
    idx = path.find(_PATH_MARKER)
    if idx < 0:
        return None
    tail = path[idx + len(_PATH_MARKER) :].strip("/")
    if not tail or "/" in tail:
        return None
    try:
        return int(tail)
    except ValueError:
        return None
