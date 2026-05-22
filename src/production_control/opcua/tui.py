"""Textual TUI over the PLC monitor: live view of PLC + Leuze nodes,
each pane fed by the same supervised connect loops as the headless
JSONL monitor.

Run:
    uv run python -m production_control.opcua.tui

Quits on `q`. Skips the Leuze pane if VINEAPP_OPCUA_LEUZE_URL is unset.

Independent of `production_control.opcua.monitor`'s stdout JSONL stream
(this slice is TUI-only; file logging is v4).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Static

from .monitor import run_plc, supervise

logger = logging.getLogger("opcua_tui")


@dataclass
class Row:
    name: str
    value: Any = None
    server_ts: datetime | None = None
    status: str | None = None
    received_at: datetime | None = None


class StateHandler:
    """asyncua subscription handler that mirrors notifications into a shared
    dict instead of writing JSONL. The TUI reads from the dict on a timer."""

    def __init__(self, source: str, state: dict[tuple[str, str], Row]) -> None:
        self._source = source
        self._state = state
        self._names: dict[str, str] = {}

    def register(self, node, name: str) -> None:
        node_id = node.nodeid.to_string()
        self._names[node_id] = name
        self._state.setdefault((self._source, node_id), Row(name=name))

    def datachange_notification(self, node, val, data) -> None:
        node_id = node.nodeid.to_string()
        monitored = data.monitored_item.Value
        self._state[(self._source, node_id)] = Row(
            name=self._names.get(node_id, node_id),
            value=val,
            server_ts=monitored.ServerTimestamp,
            status=str(monitored.StatusCode.name) if monitored.StatusCode else None,
            received_at=datetime.now(timezone.utc),
        )

    def status_change_notification(self, status) -> None:  # noqa: D401
        logger.info("status: %s", status)

    def event_notification(self, event) -> None:  # noqa: D401
        pass


def _ago(received: datetime | None, now: datetime) -> str:
    if received is None:
        return "—"
    secs = (now - received).total_seconds()
    if secs < 60:
        return f"{secs:.0f}s ago"
    if secs < 3600:
        return f"{secs / 60:.0f}m ago"
    return f"{secs / 3600:.0f}h ago"


def _value_str(v: Any) -> str:
    if v is None:
        return "—"
    return str(v)


class MonitorApp(App):
    """Two-pane live view of the PLC and Leuze subscriptions."""

    BINDINGS = [("q", "quit", "Quit")]
    CSS = """
    Static.source-header {
        padding: 0 1;
        background: $accent 20%;
        color: $text;
    }
    DataTable {
        height: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.state: dict[tuple[str, str], Row] = {}
        self._tasks: list[asyncio.Task] = []
        self._leuze_enabled = bool(os.environ.get("VINEAPP_OPCUA_LEUZE_URL"))

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield Static("PLC — connecting…", id="plc_header", classes="source-header")
            yield DataTable(id="plc_table", zebra_stripes=True)
            if self._leuze_enabled:
                yield Static("Leuze — connecting…", id="leuze_header", classes="source-header")
                yield DataTable(id="leuze_table", zebra_stripes=True)
        yield Footer()

    async def on_mount(self) -> None:
        table_ids = ["plc_table"] + (["leuze_table"] if self._leuze_enabled else [])
        for tbl_id in table_ids:
            tbl = self.query_one(f"#{tbl_id}", DataTable)
            tbl.add_columns("Node", "Value", "Updated")
            tbl.cursor_type = "row"

        plc_handler = StateHandler("plc", self.state)
        self._tasks.append(
            asyncio.create_task(supervise("plc", partial(run_plc, plc_handler)), name="plc")
        )

        if self._leuze_enabled:
            from .leuze import run_leuze  # lazy: triggers cert monkey-patch

            leuze_handler = StateHandler("leuze", self.state)
            self._tasks.append(
                asyncio.create_task(
                    supervise("leuze", partial(run_leuze, leuze_handler)), name="leuze"
                )
            )

        self.set_interval(0.25, self._refresh)

    async def on_unmount(self) -> None:
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass

    def _refresh(self) -> None:
        now = datetime.now(timezone.utc)
        self._refresh_pane("plc", "PLC (10.0.0.190)", header_keys=("Mode", "ErrorStatus"), now=now)
        if self._leuze_enabled:
            self._refresh_pane("leuze", "Leuze (10.0.0.191)", header_keys=(), now=now)

    def _refresh_pane(
        self, source: str, label: str, header_keys: tuple[str, ...], now: datetime
    ) -> None:
        rows = sorted(
            (r for (src, _), r in self.state.items() if src == source),
            key=lambda r: r.name,
        )

        header = self.query_one(f"#{source}_header", Static)
        if not rows:
            header.update(f"{label} — connecting…")
        else:
            latest = max((r.received_at for r in rows if r.received_at), default=None)
            parts = [label, f"upd {_ago(latest, now)}"]
            for key in header_keys:
                hit = next((r for r in rows if r.name == key), None)
                if hit is not None:
                    parts.append(f"{key}: {_value_str(hit.value)}")
            header.update("  ·  ".join(parts))

        tbl = self.query_one(f"#{source}_table", DataTable)
        tbl.clear()
        for row in rows:
            tbl.add_row(row.name, _value_str(row.value), _ago(row.received_at, now))


def cli() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    MonitorApp().run()


if __name__ == "__main__":
    cli()
