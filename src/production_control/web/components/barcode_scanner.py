"""Barcode scanner component for potting lot activation."""

import logging
from typing import Callable

from nicegui import ui
from nicegui_scanner import BarcodeScanner

logger = logging.getLogger(__name__)


def create_barcode_scanner_ui(on_scan: Callable[[str], None]) -> ui.column:
    with ui.column() as container:

        def on_scanner_event(event):
            barcode_text = event.args
            logger.info(f"Barcode scanned: {barcode_text}")
            on_scan(barcode_text)

        scanner = BarcodeScanner(on_scan=on_scanner_event)
        scanner.create_control_buttons()

    return container
