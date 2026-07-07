"""Unit tests for the Leuze scan payload parser."""

import pytest

from production_control.opcua.protocol import parse_scan


@pytest.mark.parametrize(
    "payload,expected",
    [
        ("https://pc.potlilium.serraict.me/potting-lots/scan/27246", 27246),
        ("http://pc.localhost/potting-lots/scan/1", 1),
        ("https://pc.potlilium.serraict.me/potting-lots/scan/27246/", 27246),
        ("/potting-lots/scan/27246", 27246),
        # Bulb-picklist labels carry the same potting-lot id (observed
        # on-site 2026-07-07: kratten are labeled from the bulb picklist).
        ("https://pc.potlilium.serraict.me/bulb-picking/scan/27978", 27978),
        ("/bulb-picking/scan/27978", 27978),
    ],
)
def test_parses_valid_scan_urls(payload, expected):
    assert parse_scan(payload) == expected


@pytest.mark.parametrize(
    "payload",
    [
        None,
        "",
        "not a url",
        "https://pc.potlilium.serraict.me/other/path",
        "https://pc.potlilium.serraict.me/potting-lots/scan/",  # missing id
        "https://pc.potlilium.serraict.me/potting-lots/scan/abc",  # non-int
        "https://pc.potlilium.serraict.me/potting-lots/scan/27246/extra",
        "https://pc.potlilium.serraict.me/bulb-picking/scan/",  # missing id
        "https://pc.potlilium.serraict.me/bulb-picking/scan/abc",  # non-int
    ],
)
def test_rejects_unparseable_payloads(payload):
    assert parse_scan(payload) is None
