"""Parse a Leuze scan payload into a partij ID.

The scanner publishes a string like:
    https://pc.potlilium.serraict.me/potting-lots/scan/27246
    https://pc.potlilium.serraict.me/bulb-picking/scan/27978

Kratten on the ontstapelaar line carry bulb-picklist labels, and
bulb-picklist rows ARE potting lots (same id), so both scan paths
resolve to the same partij number.

We accept any URL (or path) whose path component matches one of the
markers followed by `<int>` and return the trailing integer. Anything
else returns None — the caller logs and drops.
"""

from __future__ import annotations

from urllib.parse import urlparse

_PATH_MARKERS = ("/potting-lots/scan/", "/bulb-picking/scan/")


def parse_scan(payload: str | None) -> int | None:
    if not payload:
        return None
    try:
        path = urlparse(payload).path or payload
    except ValueError:
        return None
    for marker in _PATH_MARKERS:
        idx = path.find(marker)
        if idx >= 0:
            tail = path[idx + len(marker) :].strip("/")
            break
    else:
        return None
    if not tail or "/" in tail:
        return None
    try:
        return int(tail)
    except ValueError:
        return None
