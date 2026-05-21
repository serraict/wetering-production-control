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
    ],
)
def test_rejects_unparseable_payloads(payload):
    assert parse_scan(payload) is None
