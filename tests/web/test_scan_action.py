"""Tests for the `create_scan_action` row-action helper.

Locks in two contracts callers depend on:
1. The action dict has the shape `server_side_paginated_table` expects
   (`{"icon", "handler"}`).
2. The handler maps `e.args["key"]` (the row's primary-key value)
   through the caller-supplied URL builder and navigates there — so a
   caller wiring `scan_url_for=lambda id: router.url_path_for(...)`
   gets the right URL even if the route prefix changes.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from production_control.web.components.model_detail_page import create_scan_action


def _fake_event(key):
    e = MagicMock()
    e.args = {"key": key}
    return e


def test_create_scan_action_returns_icon_and_handler() -> None:
    action = create_scan_action(scan_url_for=lambda _id: "/anywhere")
    assert action["icon"] == "qr_code_scanner"
    assert callable(action["handler"])


def test_handler_navigates_to_scan_url_for_row_key() -> None:
    seen_ids: list[int] = []

    def scan_url_for(id_value):
        seen_ids.append(id_value)
        return f"/potting-lots/scan/{id_value}"

    action = create_scan_action(scan_url_for=scan_url_for)

    with patch("production_control.web.components.model_detail_page.ui.navigate.to") as navigate_to:
        action["handler"](_fake_event(27246))

    assert seen_ids == [27246]
    navigate_to.assert_called_once_with("/potting-lots/scan/27246")


def test_view_batch_route_name_matches_url_path_for() -> None:
    """Every list page's scan action resolves through `view_batch` on
    the scan router (potting_lots, inspectie, bulb_picklist, spacing,
    uitrijden — they're all potting lots under the hood). In-app
    navigation skips the canonical `/potting-lots/scan/{id}` entry
    point — that route is a server-side redirect for external barcode
    scans, and routing through it pollutes browser history with the
    intermediate URL. If `view_batch` is renamed without updating each
    caller, the list pages will 500 on click. Fail here first."""
    from production_control.web.pages.scan import router

    assert router.url_path_for("view_batch", id=27246) == "/scan/view/27246"
